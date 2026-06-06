"""Build state-year overdose death panel from CDC WONDER tab-delimited export.

Usage:
    python src/build_cdc_panel.py

Output: data/processed/cdc_state_year.parquet
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR  = PROJECT_ROOT / "data" / "raw" / "cdc"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CODEBOOK = PROJECT_ROOT / "data" / "codebooks" / "state_legalization_dates.csv"


def load_wonder_export(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. "
            "Run: python scripts/download_cdc.py  (and follow manual instructions)"
        )

    # CDC WONDER exports are tab-delimited with a notes section at the bottom
    # Read lines until we hit the notes separator
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    data_lines = []
    for line in lines:
        if line.startswith("---") or line.startswith("\"Notes\""):
            break
        data_lines.append(line)

    from io import StringIO
    df = pd.read_csv(StringIO("\n".join(data_lines)), sep="\t", low_memory=False)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def clean_wonder(df: pd.DataFrame, death_col: str) -> pd.DataFrame:
    """Normalize a CDC WONDER export to state x year with death counts."""
    # Rename common column variations
    rename = {
        "state": "state",
        "state_code": "state_fips",
        "year": "year",
        "deaths": death_col,
        "population": "population",
        "crude_rate": "crude_rate",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Drop suppressed / unreliable rows
    if death_col in df.columns:
        df = df[~df[death_col].astype(str).str.contains("Suppressed|Unreliable|Missing", na=False)]
        df[death_col] = pd.to_numeric(df[death_col], errors="coerce")

    df["year"] = pd.to_numeric(df.get("year", np.nan), errors="coerce").astype("Int64")
    df["population"] = pd.to_numeric(df.get("population", np.nan), errors="coerce")

    return df[["state", "year", "population", death_col]].dropna(subset=["state", "year"])


def build_panel() -> pd.DataFrame:
    overdose = clean_wonder(
        load_wonder_export("cdc_overdose_deaths_raw.txt"),
        "overdose_deaths"
    )
    try:
        opioid = clean_wonder(
            load_wonder_export("cdc_opioid_deaths_raw.txt"),
            "opioid_deaths"
        )
        panel = overdose.merge(opioid[["state", "year", "opioid_deaths"]], on=["state", "year"], how="left")
    except FileNotFoundError:
        print("Opioid-specific file not found — proceeding with overdose deaths only.")
        panel = overdose.copy()
        panel["opioid_deaths"] = np.nan

    # Per-100k rates
    for col in ["overdose_deaths", "opioid_deaths"]:
        if col in panel.columns:
            panel[f"{col}_per_100k"] = panel[col] / panel["population"] * 100_000

    # Merge legalization dates
    leg = pd.read_csv(CODEBOOK)
    leg["retail_sales_year"] = pd.to_numeric(leg["retail_sales_year"], errors="coerce").astype("Int64")
    panel = panel.merge(leg[["state", "retail_sales_year"]], on="state", how="left")
    panel["treated"] = panel["retail_sales_year"].notna()
    panel["post"]    = panel["treated"] & (panel["year"] >= panel["retail_sales_year"])

    panel = panel.sort_values(["state", "year"]).reset_index(drop=True)
    out = OUT_DIR / "cdc_state_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}  ({len(panel):,} rows)")
    return panel


if __name__ == "__main__":
    build_panel()
