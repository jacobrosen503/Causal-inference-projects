"""Load and clean Stanford SEDA 4.1 district test score data.

Input:  data/raw/seda/seda_district_long.csv
        (file: seda_geodist_long_cs_4.1.csv, renamed on save)
Output: data/processed/seda_district_year.parquet

Columns in SEDA 4.1 scores file:
    fips, stateabb, sedalea, sedaleaname, subject, grade, year,
    cs_mn_all, cs_mnse_all, totgyb_all, [subgroup columns...]

Usage:
    python src/ingest/seda.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "seda" / "seda_district_long.csv"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Western US states
WESTERN = ["CA","OR","WA","MT","ID","WY","CO","NV","AZ","NM","UT"]

# Study window (stop before COVID)
YEAR_MIN, YEAR_MAX = 2010, 2019


def load_seda() -> pd.DataFrame:
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"{RAW_FILE} not found.\n"
            "Save seda_geodist_long_cs_4.1.csv as:\n"
            "  data/raw/seda/seda_district_long.csv"
        )
    print(f"Loading SEDA: {RAW_FILE}")
    # Large file — load in chunks if needed
    df = pd.read_csv(RAW_FILE, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    print(f"  Raw: {df.shape}")
    return df


def build_panel(df: pd.DataFrame) -> pd.DataFrame:
    # Filter: math only, western states, study window, grades 3-8
    df = df[df["subject"] == "mth"].copy()
    df = df[df["stateabb"].isin(WESTERN)]
    df = df[df["year"].between(YEAR_MIN, YEAR_MAX)]
    df = df[df["grade"].between(3, 8)]
    print(f"  After filters (math, western, {YEAR_MIN}-{YEAR_MAX}, gr3-8): {df.shape}")

    # Pool grades: average cs_mn_all across grades per district-year
    panel = (
        df.groupby(["sedalea", "stateabb", "year"])
        .agg(
            test_score_mean=("cs_mn_all",  "mean"),
            test_score_se  =("cs_mnse_all","mean"),
            n_grades       =("grade",      "count"),
            n_students     =("totgyb_all", "sum"),
        )
        .reset_index()
    )

    panel = panel.rename(columns={"sedalea": "leaid", "stateabb": "state"})
    panel["leaid"] = panel["leaid"].astype(str).str.strip()
    panel["year"]  = panel["year"].astype(int)

    panel = panel.dropna(subset=["test_score_mean"])
    panel = panel.sort_values(["leaid","year"]).reset_index(drop=True)

    print(f"  Panel: {panel.shape} | Districts: {panel['leaid'].nunique():,} | Years: {sorted(panel['year'].unique())}")

    out = OUT_DIR / "seda_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    df = load_seda()
    build_panel(df)
