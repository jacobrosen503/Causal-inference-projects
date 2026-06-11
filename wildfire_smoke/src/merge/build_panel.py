"""Merge all data sources into the final district-year analysis panel.

Joins:
  - SEDA test scores (outcome)
  - EPA AQS PM2.5 (treatment/exposure)
  - HMS smoke instrument (IV)
  - ACS demographics (controls)

Input:  data/processed/seda_district_year.parquet
        data/processed/pm25_district_year.parquet
        data/processed/smoke_instrument_district_year.parquet
        data/raw/acs/acs_district_controls.csv  (optional)

Output: data/processed/analysis_panel.parquet

Usage:
    python src/merge/build_panel.py
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROC = PROJECT_ROOT / "data" / "processed"
ACS  = PROJECT_ROOT / "data" / "raw" / "acs" / "acs_district_controls.csv"
OUT  = PROC / "analysis_panel.parquet"


def load_required(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{name} not found at {path}.\n"
            "Run the corresponding ingest script first."
        )
    return pd.read_parquet(path)


def build_panel() -> pd.DataFrame:
    seda  = load_required(PROC / "seda_district_year.parquet",  "SEDA scores")
    pm25  = load_required(PROC / "pm25_district_year.parquet",  "PM2.5 panel")
    smoke = load_required(PROC / "smoke_instrument_district_year.parquet", "Smoke instrument")

    print(f"SEDA:  {seda.shape}")
    print(f"PM2.5: {pm25.shape}")
    print(f"Smoke: {smoke.shape}")

    # Normalize leaid to zero-padded string across all sources
    for df in [seda, pm25, smoke]:
        df["leaid"] = df["leaid"].astype(str).str.strip().str.zfill(7)

    # Merge on district x year
    panel = (
        seda
        .merge(pm25,  on=["leaid", "year"], how="left")
        .merge(smoke, on=["leaid", "year"], how="left")
    )

    # ACS controls (optional)
    if ACS.exists():
        acs = pd.read_csv(ACS)
        acs.columns = [c.lower().strip() for c in acs.columns]
        panel = panel.merge(acs, on="leaid", how="left")
        print(f"ACS controls merged: {acs.shape[1]-1} variables")
    else:
        print(f"Note: ACS controls not found at {ACS}. Analysis will run without demographic controls.")
        print("      Download from Census API or data.census.gov for district-level ACS estimates.")

    # Log transforms
    panel["log_pm25"] = np.log(panel["pm25_annual_mean"].clip(lower=0.1))

    # Flag Camp Fire districts (Butte County CA, 2018)
    if "leaid" in panel.columns:
        panel["camp_fire_affected"] = (
            panel["leaid"].astype(str).str.startswith("0600")  # CA districts
        ) & (panel["year"] == 2018)

    panel = panel.sort_values(["leaid", "year"]).reset_index(drop=True)

    panel.to_parquet(OUT, index=False)
    print(f"\nAnalysis panel: {panel.shape}")
    print(f"Written: {OUT}")
    return panel


if __name__ == "__main__":
    build_panel()
