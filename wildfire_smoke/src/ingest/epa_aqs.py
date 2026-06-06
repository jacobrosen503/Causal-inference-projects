"""Build county-year PM2.5 panel from EPA AQS daily monitor data.

Aggregates daily monitor readings to annual county-level averages.
County is the geographic unit because:
  - EPA regulates PM2.5 at the county/air basin level
  - Avoids complex IDW spatial join to district centroids
  - County FIPS links cleanly to SEDA via CCD crosswalk

Input:  data/raw/epa_aqs/pm25_daily_{state}_{year}.csv
Output: data/processed/pm25_county_year.parquet

Usage:
    python src/ingest/epa_aqs.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR  = PROJECT_ROOT / "data" / "raw" / "epa_aqs"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WESTERN_STATE_FIPS = {
    "06","41","53","30","16","56","08","32","04","35","49"
}


def load_all_aqs() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("pm25_daily_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No AQS files in {RAW_DIR}.\n"
            "Run: python scripts/download_epa_aqs.py --email EMAIL --key bluekit86"
        )
    print(f"Loading {len(files)} AQS files...")
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
            dfs.append(df)
        except Exception as e:
            print(f"  Warning: {f.name} — {e}")
    combined = pd.concat(dfs, ignore_index=True)
    print(f"  Combined: {len(combined):,} rows")
    return combined


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize AQS column names which vary slightly by API version."""
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    rename = {
        "arithmetic_mean":        "pm25",
        "daily_mean_pm2.5_concentration": "pm25",
        "sample_measurement":     "pm25",
        "state_code":             "state_fips",
        "county_code":            "county_fips_3digit",
        "date_local":             "date",
        "local_site_name":        "site_name",
    }
    return df.rename(columns={k: v for k, v in rename.items() if k in df.columns})


def build_county_year_panel(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)

    # Parse date and extract year
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year

    # Build 5-digit county FIPS
    if "state_fips" in df.columns and "county_fips_3digit" in df.columns:
        df["county_fips"] = (
            df["state_fips"].astype(str).str.zfill(2) +
            df["county_fips_3digit"].astype(str).str.zfill(3)
        )
    elif "county_code" in df.columns and "state_code" in df.columns:
        df["county_fips"] = (
            df["state_code"].astype(str).str.zfill(2) +
            df["county_code"].astype(str).str.zfill(3)
        )
    else:
        raise KeyError(f"Cannot build county FIPS. Columns: {list(df.columns[:15])}")

    # Filter to western states
    df = df[df["county_fips"].str[:2].isin(WESTERN_STATE_FIPS)]

    # Clean PM2.5 values
    if "pm25" not in df.columns:
        pm_col = next((c for c in df.columns if "mean" in c or "pm" in c.lower()), None)
        if pm_col:
            df = df.rename(columns={pm_col: "pm25"})
        else:
            raise KeyError(f"Cannot find PM2.5 column. Available: {list(df.columns)}")

    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
    df = df[df["pm25"].between(0, 500)]   # drop impossible values

    # Aggregate to county x year
    panel = (
        df.groupby(["county_fips", "year"])
        .agg(
            pm25_annual_mean   =("pm25", "mean"),
            pm25_annual_median =("pm25", "median"),
            pm25_days_gt35     =("pm25", lambda x: (x > 35).sum()),   # unhealthy days
            n_monitor_days     =("pm25", "count"),
            n_monitors         =("county_fips", "count"),
        )
        .reset_index()
    )
    panel["log_pm25"] = np.log(panel["pm25_annual_mean"].clip(lower=0.1))

    print(f"County-year PM2.5 panel: {panel.shape}")
    print(f"  Counties: {panel['county_fips'].nunique():,}")
    print(f"  Years: {sorted(panel['year'].unique())}")
    print(f"  PM2.5 range: {panel['pm25_annual_mean'].min():.1f} - {panel['pm25_annual_mean'].max():.1f} μg/m³")

    out = OUT_DIR / "pm25_county_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    df = load_all_aqs()
    build_county_year_panel(df)
