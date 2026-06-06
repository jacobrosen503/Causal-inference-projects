"""Build state-year traffic fatality panel from CDAN query export + Census population.

Inputs:
  data/raw/fars/fars_state_year_raw.csv        — CDAN wide export (state x year fatality counts)
  data/raw/census/state_population_2010_2022.csv — merged from NST-EST Census files

Usage:
    python src/build_fars_panel.py

Output: data/processed/fars_state_year.parquet

Download instructions:
  FARS:   https://cdan.dot.gov/query  (State x Year, 2010-2022, export CSV)
  Census: see scripts/download_census.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FARS  = PROJECT_ROOT / "data/raw/fars/fars_state_year_raw.csv"
RAW_POP   = PROJECT_ROOT / "data/raw/census/state_population_2010_2022.csv"
CODEBOOK  = PROJECT_ROOT / "data/codebooks/state_legalization_dates.csv"
OUT_DIR   = PROJECT_ROOT / "data/processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_cdan_wide(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=0)
    raw.columns = ["state"] + [str(c) for c in raw.columns[1:]]
    raw = raw[[c for c in raw.columns if c != "Total"]]
    panel = raw.melt(id_vars="state", var_name="year", value_name="total_fatalities")
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")
    panel["total_fatalities"] = (
        panel["total_fatalities"].astype(str)
        .str.replace(",", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    return panel.dropna(subset=["state", "year", "total_fatalities"])


def build_panel() -> pd.DataFrame:
    if not RAW_FARS.exists():
        raise FileNotFoundError(
            f"{RAW_FARS} not found.\n"
            "Download from https://cdan.dot.gov/query — State x Year, 2010-2022"
        )

    print(f"Loading FARS: {RAW_FARS}")
    panel = load_cdan_wide(RAW_FARS)
    panel["year"] = panel["year"].astype(int)
    print(f"  {len(panel):,} rows | {panel['state'].nunique()} states")

    # Population
    if RAW_POP.exists():
        pop = pd.read_csv(RAW_POP)
        pop["year"] = pop["year"].astype(int)
        panel = panel.merge(pop, on=["state", "year"], how="left")
        panel["total_fatalities_per_100k"] = (
            panel["total_fatalities"] / panel["population"] * 100_000
        ).round(3)
        print(f"  Population merged. Per-100k rates computed.")
    else:
        panel["population"] = np.nan
        panel["total_fatalities_per_100k"] = np.nan
        print(f"  Note: Census population not found at {RAW_POP}. Per-100k rates skipped.")

    # Legalization dates
    leg = pd.read_csv(CODEBOOK)
    leg["retail_sales_year"] = pd.to_numeric(leg["retail_sales_year"], errors="coerce")
    panel = panel.merge(leg[["state", "state_abbr", "fips", "retail_sales_year"]], on="state", how="left")

    panel["treated"] = panel["retail_sales_year"].notna()
    panel["post"]    = panel["treated"] & (panel["year"] >= panel["retail_sales_year"])
    panel["years_since_legalization"] = np.where(
        panel["treated"], panel["year"] - panel["retail_sales_year"], np.nan
    )

    panel = panel.sort_values(["state", "year"]).reset_index(drop=True)
    out = OUT_DIR / "fars_state_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    build_panel()
