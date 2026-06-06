"""Merge all data sources into the final district-year analysis panel.

District-level merge using NCES EDGE geocode crosswalk:
  SEDA test scores (district x year)
  + EPA AQS PM2.5 (district x year, IDW from monitors)
  + HMS smoke instrument (district x year, centroid point-in-polygon)
  + SEDA covariates (district x year, poverty/income/demographics)

Input:
  data/processed/seda_district_year.parquet
  data/processed/pm25_district_year.parquet
  data/processed/smoke_instrument_district_year.parquet
  data/crosswalks/district_centroids_edge.csv
  data/raw/seda/seda_covariates.csv   (optional — controls)

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
XWALK     = PROJECT_ROOT / "data" / "crosswalks" / "district_centroids_edge.csv"
COV_FILE  = PROJECT_ROOT / "data" / "raw" / "seda" / "seda_covariates.csv"
OUT       = PROC / "analysis_panel.parquet"


def load_required(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{name} not found: {path}\n"
            f"Run the corresponding ingest script first."
        )
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, low_memory=False)


def load_seda_covariates() -> pd.DataFrame | None:
    if not COV_FILE.exists():
        print(f"Note: SEDA covariates not found — running without demographic controls")
        print(f"      Save seda_cov_geodist_long_4_1.csv as data/raw/seda/seda_covariates.csv")
        return None

    df = pd.read_csv(COV_FILE, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df["leaid"] = df["sedalea"].astype(str).str.strip().str.zfill(7)
    df["year"]  = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    cols = ["leaid","year","povertyall","sesall","lninc50all","perecd","perblk","perhsp","totenrl"]
    avail = [c for c in cols if c in df.columns]

    pooled = (
        df[avail].groupby(["leaid","year"])
        .mean(numeric_only=True)
        .reset_index()
    )
    pooled["year"] = pooled["year"].astype(int)
    print(f"SEDA covariates: {pooled.shape} | Controls: {[c for c in avail if c not in ['leaid','year']]}")
    return pooled


def build_panel() -> pd.DataFrame:
    seda  = load_required(PROC / "seda_district_year.parquet",           "SEDA scores")
    pm25  = load_required(PROC / "pm25_district_year.parquet",           "PM2.5 panel")
    smoke = load_required(PROC / "smoke_instrument_district_year.parquet","Smoke instrument")
    xwalk = pd.read_csv(XWALK)

    print(f"SEDA:      {seda.shape}")
    print(f"PM2.5:     {pm25.shape}")
    print(f"Smoke:     {smoke.shape}")
    print(f"Crosswalk: {xwalk.shape}")

    # Normalize LEAIDs everywhere
    for df in [seda, pm25, smoke, xwalk]:
        df["leaid"] = df["leaid"].astype(str).str.zfill(7)

    # Normalize year
    seda["year"]  = seda["year"].astype(int)
    pm25["year"]  = pm25["year"].astype(int)
    smoke["year"] = smoke["year"].astype(int)

    # Add county_fips, locale, lat/lon from crosswalk
    geo_cols = ["leaid","county_fips","lat","lon","locale"]
    geo_cols = [c for c in geo_cols if c in xwalk.columns]
    seda = seda.merge(xwalk[geo_cols].drop_duplicates("leaid"), on="leaid", how="left")

    # Merge PM2.5 and smoke at district x year
    panel = (
        seda
        .merge(pm25[["leaid","year","pm25_annual_mean","log_pm25","n_monitors"]],
               on=["leaid","year"], how="left")
        .merge(smoke[["leaid","year","smoke_days","smoke_days_heavy","smoke_days_pct"]],
               on=["leaid","year"], how="left")
    )

    # Covariates
    cov = load_seda_covariates()
    if cov is not None:
        panel = panel.merge(cov, on=["leaid","year"], how="left")

    # Flags
    panel["camp_fire_county"] = (
        panel.get("county_fips", pd.Series(dtype=str)) == "06007"
    ) & (panel["year"] == 2018)

    panel = panel.sort_values(["leaid","year"]).reset_index(drop=True)

    complete = panel.dropna(subset=["test_score_mean","pm25_annual_mean","smoke_days"])
    print(f"\nAnalysis panel:  {panel.shape}")
    print(f"Complete cases:  {len(complete):,} (score + PM2.5 + smoke)")
    print(f"Districts:       {panel['leaid'].nunique():,}")
    print(f"Years:           {sorted(panel['year'].unique())}")

    panel.to_parquet(OUT, index=False)
    print(f"Written: {OUT}")
    return panel


if __name__ == "__main__":
    build_panel()
