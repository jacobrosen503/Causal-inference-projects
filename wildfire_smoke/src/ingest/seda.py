"""Load and clean Stanford SEDA district test score data.

Input:  data/raw/seda/seda_district_long.csv
Output: data/processed/seda_district_year.parquet

Usage:
    python src/ingest/seda.py
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_SEDA = PROJECT_ROOT / "data" / "raw" / "seda" / "seda_district_long.csv"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_seda() -> pd.DataFrame:
    if not RAW_SEDA.exists():
        raise FileNotFoundError(
            f"{RAW_SEDA} not found.\n"
            "Download from https://edopportunity.org/get-the-data/seda-archive-downloads/\n"
            "Then run: python scripts/download_seda.py  (for instructions)"
        )

    print(f"Loading SEDA: {RAW_SEDA}")
    df = pd.read_csv(RAW_SEDA, low_memory=False)
    df.columns = [c.lower().strip() for c in df.columns]
    print(f"  Raw shape: {df.shape}")
    return df


def build_panel(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize common column name variants across SEDA versions
    rename = {
        "sedalea":    "leaid",
        "lea_id":     "leaid",
        "stateabb":   "state",
        "mn_avg_ol":  "test_score_mean",
        "cs_mn_avg_ol": "test_score_mean",
        "mn_avg_ol_se": "test_score_se",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Filter: math scores, grades 3-8, western states
    WESTERN = ["CA", "OR", "WA", "MT", "ID", "WY", "CO", "NV", "AZ", "NM", "UT"]
    if "subject" in df.columns:
        df = df[df["subject"] == "math"]
    if "state" in df.columns:
        df = df[df["state"].isin(WESTERN)]
    if "grade" in df.columns:
        df = df[df["grade"].between(3, 8)]

    # Pool grades: average test score across grades per district-year
    group_cols = ["leaid", "year"]
    if "state" in df.columns:
        group_cols.append("state")

    panel = (
        df.groupby(group_cols)
        .agg(
            test_score_mean=("test_score_mean", "mean"),
            test_score_se=("test_score_se", "mean") if "test_score_se" in df.columns else ("test_score_mean", "std"),
            n_grades=("test_score_mean", "count"),
        )
        .reset_index()
    )

    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")
    panel = panel.dropna(subset=["leaid", "year", "test_score_mean"])

    print(f"SEDA panel: {panel.shape} | districts: {panel['leaid'].nunique()} | years: {sorted(panel['year'].dropna().unique())}")

    out = OUT_DIR / "seda_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    df = load_seda()
    build_panel(df)
