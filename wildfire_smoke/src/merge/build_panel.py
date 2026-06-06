"""Merge all data sources into the final district-year analysis panel.

Geographic matching is at the county level:
  SEDA district scores -> CCD crosswalk -> county FIPS
  county FIPS -> county PM2.5 (EPA AQS aggregated by county)
  county FIPS -> county smoke days (HMS plumes at county centroid)

Inputs:
  data/processed/seda_district_year.parquet
  data/processed/pm25_county_year.parquet
  data/processed/smoke_instrument_county_year.parquet
  data/crosswalks/district_crosswalk.csv   (LEAID -> county_fips)
  data/raw/seda/seda_covariates.csv        (SEDA covariate file)

Output:
  data/processed/analysis_panel.parquet

Usage:
    python src/merge/build_panel.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROC      = PROJECT_ROOT / "data" / "processed"
XWALK     = PROJECT_ROOT / "data" / "crosswalks" / "district_crosswalk.csv"
COV_FILE  = PROJECT_ROOT / "data" / "raw" / "seda" / "seda_covariates.csv"
OUT       = PROC / "analysis_panel.parquet"

WESTERN = ["CA","OR","WA","MT","ID","WY","CO","NV","AZ","NM","UT"]


def load_required(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")
    ext = path.suffix
    if ext == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, low_memory=False)


def load_seda_covariates() -> pd.DataFrame | None:
    if not COV_FILE.exists():
        print(f"Note: SEDA covariates not found at {COV_FILE} — running without demographic controls")
        return None
    print(f"Loading SEDA covariates: {COV_FILE.name}")
    df = pd.read_csv(COV_FILE, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # Pool to district x year (average across grades)
    df["leaid"] = df["sedalea"].astype(str).str.strip().str.zfill(7)
    df["year"]  = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Key control variables
    control_cols = ["leaid","year","povertyall","sesall","lninc50all","perecd","perblk","perhsp","totenrl"]
    available    = [c for c in control_cols if c in df.columns]

    pooled = (
        df[available].groupby(["leaid","year"])
        .mean(numeric_only=True)
        .reset_index()
    )
    print(f"  Covariates: {pooled.shape} | Controls: {[c for c in available if c not in ['leaid','year']]}")
    return pooled


def build_panel() -> pd.DataFrame:
    seda  = load_required(PROC / "seda_district_year.parquet",          "SEDA scores")
    pm25  = load_required(PROC / "pm25_county_year.parquet",            "PM2.5 panel")
    smoke = load_required(PROC / "smoke_instrument_county_year.parquet","Smoke instrument")
    xwalk = load_required(XWALK,                                         "District crosswalk")

    print(f"\nSEDA:     {seda.shape}")
    print(f"PM2.5:    {pm25.shape}")
    print(f"Smoke:    {smoke.shape}")
    print(f"Crosswalk:{xwalk.shape}")

    # Normalize LEAIDs
    seda["leaid"]  = seda["leaid"].astype(str).str.strip().str.zfill(7)
    xwalk["leaid"] = xwalk["leaid"].astype(str).str.strip().str.zfill(7)

    # Join crosswalk to get county_fips for each district
    seda = seda.merge(xwalk[["leaid","county_fips","lat","lon"]].drop_duplicates("leaid"),
                      on="leaid", how="left")
    print(f"\nDistricts with county FIPS: {seda['county_fips'].notna().sum():,} / {len(seda):,}")

    # Join PM2.5 and smoke at county x year
    pm25["year"]  = pm25["year"].astype(int)
    smoke["year"] = smoke["year"].astype(int)
    seda["year"]  = seda["year"].astype(int)

    panel = (
        seda
        .merge(pm25[["county_fips","year","pm25_annual_mean","log_pm25","pm25_days_gt35"]],
               on=["county_fips","year"], how="left")
        .merge(smoke[["county_fips","year","smoke_days","smoke_days_heavy","smoke_days_pct"]],
               on=["county_fips","year"], how="left")
    )

    # SEDA covariates (optional)
    cov = load_seda_covariates()
    if cov is not None:
        cov["year"] = cov["year"].astype(int)
        panel = panel.merge(cov, on=["leaid","year"], how="left")

    # Camp Fire flag (Butte County CA = 06007, 2018)
    panel["camp_fire_county"] = (panel["county_fips"] == "06007") & (panel["year"] == 2018)

    # Summary
    complete = panel.dropna(subset=["test_score_mean","pm25_annual_mean","smoke_days"])
    print(f"\nAnalysis panel: {panel.shape}")
    print(f"Complete cases (score + PM2.5 + smoke): {len(complete):,}")
    print(f"Districts: {panel['leaid'].nunique():,} | Counties: {panel['county_fips'].nunique():,} | Years: {sorted(panel['year'].unique())}")

    panel = panel.sort_values(["leaid","year"]).reset_index(drop=True)
    panel.to_parquet(OUT, index=False)
    print(f"Written: {OUT}")
    return panel


if __name__ == "__main__":
    build_panel()
