"""Build district-year PM2.5 panel from EPA AQS annual summary data.

Aggregates annual monitor readings to district-level averages using
inverse-distance weighting from monitor locations to district centroids.

Input:  data/raw/epa_aqs/pm25_annual_{state}_{year}.csv
        data/crosswalks/district_crosswalk.csv
Output: data/processed/pm25_district_year.parquet

Usage:
    python src/ingest/epa_aqs.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR  = PROJECT_ROOT / "data" / "raw" / "epa_aqs"
# district_crosswalk.csv has columns: leaid, lat, lon (built by build_crosswalks.py)
XWALK    = PROJECT_ROOT / "data" / "crosswalks" / "district_crosswalk.csv"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_all_aqs() -> pd.DataFrame:
    # Support both annual summary files (pm25_annual_*) and daily files (pm25_daily_*)
    files = sorted(RAW_DIR.glob("pm25_annual_*.csv")) or sorted(RAW_DIR.glob("pm25_daily_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No AQS files found in {RAW_DIR}. "
            "Run: python scripts/download_epa_aqs.py --email EMAIL --key KEY"
        )
    print(f"Loading {len(files)} AQS files...")
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
            dfs.append(df)
        except Exception as e:
            print(f"  Warning: {f.name} — {e}")
    return pd.concat(dfs, ignore_index=True)


def aggregate_to_district_year(aqs: pd.DataFrame, centroids: pd.DataFrame) -> pd.DataFrame:
    """
    Inverse-distance weighting from monitors to district centroids.
    For each district x year: weighted average PM2.5 from monitors within 100km.
    """
    # Normalize AQS columns
    aqs.columns = [c.lower().strip().replace(" ", "_") for c in aqs.columns]

    pm_col  = next((c for c in aqs.columns if "arithmetic_mean" in c or "daily_mean" in c), None)
    lat_col = next((c for c in aqs.columns if c == "latitude"), None)
    lon_col = next((c for c in aqs.columns if c == "longitude"), None)

    if not all([pm_col, lat_col, lon_col]):
        raise KeyError(f"Missing expected columns. Found: {list(aqs.columns[:10])}")

    # Use 'year' column if present (annual files), else parse from date column
    if "year" not in aqs.columns:
        date_col = next((c for c in aqs.columns if "date" in c), None)
        if date_col:
            aqs["year"] = pd.to_datetime(aqs[date_col], errors="coerce").dt.year
        else:
            raise KeyError("Cannot determine year from AQS data")

    aqs[pm_col] = pd.to_numeric(aqs[pm_col], errors="coerce")
    # For annual files, filter to the 24-hour daily mean standard (one row per monitor-year)
    if "pollutant_standard" in aqs.columns:
        mask = aqs["pollutant_standard"].str.contains("24-hour|24 hour|Annual", case=False, na=False)
        aqs = aqs[mask].drop_duplicates(subset=[lat_col, lon_col, "year"])

    # Annual monitor averages (for annual files this is a no-op groupby)
    monitor_annual = (
        aqs.groupby([lat_col, lon_col, "year"])
        .agg(pm25_mean=(pm_col, "mean"), pm25_days=(pm_col, "count"))
        .reset_index()
    )

    if not XWALK.exists():
        raise FileNotFoundError(
            f"District crosswalk not found at {XWALK}. "
            "Run: python src/merge/build_crosswalks.py"
        )

    districts = pd.read_csv(XWALK)
    # Keep only rows with valid lat/lon
    districts = districts.dropna(subset=["lat", "lon"])

    # For each district x year, find monitors within 100km and IDW-average
    results = []
    for _, dist in districts.iterrows():
        for year, grp in monitor_annual.groupby("year"):
            # Haversine distance (approximate)
            dlat = np.radians(grp[lat_col] - dist["lat"])
            dlon = np.radians(grp[lon_col] - dist["lon"])
            a = np.sin(dlat/2)**2 + np.cos(np.radians(dist["lat"])) * np.cos(np.radians(grp[lat_col])) * np.sin(dlon/2)**2
            dist_km = 6371 * 2 * np.arcsin(np.sqrt(a))

            nearby = grp[dist_km <= 100].copy()
            if nearby.empty:
                continue

            nearby["dist_km"] = dist_km[dist_km <= 100].values
            nearby["weight"] = 1 / (nearby["dist_km"] ** 2 + 1e-6)
            pm25_idw = (nearby["pm25_mean"] * nearby["weight"]).sum() / nearby["weight"].sum()

            results.append({
                "leaid":  dist["leaid"],
                "year":   year,
                "pm25_annual_mean": round(pm25_idw, 3),
                "n_monitors": len(nearby),
            })

    panel = pd.DataFrame(results)
    print(f"PM2.5 panel: {panel.shape} | districts: {panel['leaid'].nunique()}")
    out = OUT_DIR / "pm25_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    aqs      = load_all_aqs()
    centroids = pd.read_csv(XWALK) if XWALK.exists() else pd.DataFrame()
    if centroids.empty:
        print("District centroids missing — run src/merge/build_crosswalks.py first")
    else:
        aggregate_to_district_year(aqs, centroids)
