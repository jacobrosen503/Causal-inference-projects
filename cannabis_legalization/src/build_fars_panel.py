"""Build state-year traffic fatality panel from raw NHTSA FARS data.

Merges FARS fatality counts with Census population estimates and
state legalization dates to produce the main analysis panel.

Usage:
    python src/build_fars_panel.py
    python src/build_fars_panel.py --source accident_files  # raw crash-level CSVs

Output: data/processed/fars_state_year.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR  = PROJECT_ROOT / "data" / "raw"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CODEBOOK = PROJECT_ROOT / "data" / "codebooks" / "state_legalization_dates.csv"


def load_legalization_dates() -> pd.DataFrame:
    df = pd.read_csv(CODEBOOK)
    df = df[df["retail_sales_year"].notna()].copy()
    df["retail_sales_year"] = df["retail_sales_year"].astype(int)
    return df[["state", "state_abbr", "fips", "retail_sales_year", "law_passed_year"]]


def load_fars_prebuilt() -> pd.DataFrame:
    """Load pre-aggregated FARS file (from NHTSA query tool export)."""
    candidates = [
        RAW_DIR / "fars" / "fars_state_year_raw.csv",
        RAW_DIR / "fars" / "fars_api_raw.json",
    ]
    for path in candidates:
        if path.exists():
            print(f"Loading: {path}")
            if path.suffix == ".json":
                return pd.read_json(path)
            return pd.read_csv(path)
    raise FileNotFoundError(
        "No FARS data found in data/raw/fars/. "
        "Run: python scripts/download_fars.py"
    )


def load_population() -> pd.DataFrame:
    """Load Census state population estimates."""
    pop_path = RAW_DIR / "census" / "state_population_2010_2022.csv"
    if not pop_path.exists():
        raise FileNotFoundError(
            "Census population file not found at data/raw/census/state_population_2010_2022.csv. "
            "Download from: https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html"
        )
    return pd.read_csv(pop_path)


def build_panel() -> pd.DataFrame:
    fars = load_fars_prebuilt()
    print(f"FARS raw: {fars.shape}")

    # Normalize column names (NHTSA exports vary)
    fars.columns = [c.lower().strip().replace(" ", "_") for c in fars.columns]

    # Expected columns after normalization — adjust to match your export
    rename_map = {
        "state_name": "state",
        "statename":  "state",
        "fatalities":           "total_fatalities",
        "drunk_driving_fatalities": "alcohol_fatalities",
        "drug_impaired_driving_fatalities": "drug_fatalities",
    }
    fars = fars.rename(columns={k: v for k, v in rename_map.items() if k in fars.columns})

    if "year" not in fars.columns:
        raise KeyError("Could not find 'year' column in FARS data. Check column names.")
    if "state" not in fars.columns:
        raise KeyError("Could not find 'state' column in FARS data. Check column names.")

    fars["year"] = pd.to_numeric(fars["year"], errors="coerce").astype("Int64")
    fars["total_fatalities"] = pd.to_numeric(fars.get("total_fatalities", np.nan), errors="coerce")

    # Merge population
    try:
        pop = load_population()
        pop.columns = [c.lower().strip() for c in pop.columns]
        panel = fars.merge(pop, on=["state", "year"], how="left")
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Skipping per-100k normalization — add population data for rates.")
        panel = fars.copy()
        panel["population"] = np.nan

    # Merge legalization dates
    leg = load_legalization_dates()
    panel = panel.merge(leg[["state", "retail_sales_year"]], on="state", how="left")

    # Treatment indicators
    panel["treated"] = panel["retail_sales_year"].notna()
    panel["post"]    = (
        panel["treated"] &
        (panel["year"] >= panel["retail_sales_year"])
    )
    panel["years_since_legalization"] = np.where(
        panel["treated"],
        panel["year"] - panel["retail_sales_year"],
        np.nan
    )

    # Per-100k rates
    if panel["population"].notna().any():
        for col in ["total_fatalities", "alcohol_fatalities", "drug_fatalities"]:
            if col in panel.columns:
                panel[f"{col}_per_100k"] = panel[col] / panel["population"] * 100_000

    panel = panel.sort_values(["state", "year"]).reset_index(drop=True)
    print(f"Panel: {panel.shape}  |  States: {panel['state'].nunique()}  |  Years: {sorted(panel['year'].dropna().unique())}")

    out = OUT_DIR / "fars_state_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    build_panel()
