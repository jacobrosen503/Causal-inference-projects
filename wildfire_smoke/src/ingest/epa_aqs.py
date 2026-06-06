"""Build district-year PM2.5 panel from EPA AQS daily monitor data.

Uses inverse-distance weighting (IDW) from EPA monitor locations to
district centroids (from NCES EDGE geocode file). Districts within
100km of at least one monitor get a weighted average PM2.5 estimate.

Input:  data/raw/epa_aqs/pm25_daily_{state}_{year}.csv
        data/crosswalks/district_centroids_edge.csv
Output: data/processed/pm25_district_year.parquet

Usage:
    python src/ingest/epa_aqs.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR   = PROJECT_ROOT / "data" / "raw" / "epa_aqs"
XWALK     = PROJECT_ROOT / "data" / "crosswalks" / "district_centroids_edge.csv"
OUT_DIR   = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_DIST_KM = 100   # max monitor-to-district distance for IDW


def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorized haversine distance in km."""
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat/2)**2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2)
    return R * 2 * np.arcsin(np.sqrt(a))


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
            dfs.append(pd.read_csv(f, low_memory=False))
        except Exception as e:
            print(f"  Warning: {f.name} — {e}")
    combined = pd.concat(dfs, ignore_index=True)
    print(f"  Combined: {len(combined):,} monitor-days")
    return combined


def aggregate_monitors(aqs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily monitor readings to annual monitor-level means."""
    aqs.columns = [c.lower().strip().replace(" ","_") for c in aqs.columns]

    # Find key columns
    date_col = next((c for c in aqs.columns if "date" in c), None)
    pm_col   = next((c for c in aqs.columns if "arithmetic_mean" in c or "daily_mean" in c), None)
    lat_col  = "latitude"
    lon_col  = "longitude"

    if not all(c in aqs.columns for c in [lat_col, lon_col]):
        raise KeyError(f"lat/lon columns missing. Available: {list(aqs.columns[:15])}")

    aqs["year"] = pd.to_datetime(aqs[date_col], errors="coerce").dt.year
    aqs[pm_col] = pd.to_numeric(aqs[pm_col], errors="coerce")
    aqs = aqs[aqs[pm_col].between(0, 500)]

    monitor_annual = (
        aqs.groupby([lat_col, lon_col, "year"])
        .agg(pm25_mean=(pm_col, "mean"), n_days=(pm_col, "count"))
        .reset_index()
    )
    print(f"  Annual monitor records: {len(monitor_annual):,}")
    return monitor_annual


def idw_to_districts(monitors: pd.DataFrame, districts: pd.DataFrame) -> pd.DataFrame:
    """IDW from monitors to district centroids, within MAX_DIST_KM."""
    results = []
    years = sorted(monitors["year"].dropna().unique())

    for year in years:
        yr_monitors = monitors[monitors["year"] == year].dropna(
            subset=["latitude","longitude","pm25_mean"]
        )
        if yr_monitors.empty:
            continue

        mon_lats = yr_monitors["latitude"].values
        mon_lons = yr_monitors["longitude"].values
        mon_pm   = yr_monitors["pm25_mean"].values

        for _, dist in districts.iterrows():
            dists_km = haversine_km(dist["lat"], dist["lon"], mon_lats, mon_lons)
            nearby = dists_km <= MAX_DIST_KM

            if not nearby.any():
                continue

            d = dists_km[nearby]
            pm = mon_pm[nearby]
            w  = 1 / (d**2 + 1e-6)
            pm25_idw = (pm * w).sum() / w.sum()

            results.append({
                "leaid":           dist["leaid"],
                "year":            int(year),
                "pm25_annual_mean": round(pm25_idw, 3),
                "n_monitors":       int(nearby.sum()),
            })

    panel = pd.DataFrame(results)
    panel["log_pm25"] = np.log(panel["pm25_annual_mean"].clip(lower=0.1))
    print(f"District-year PM2.5 panel: {panel.shape}")
    print(f"  Districts with coverage: {panel['leaid'].nunique():,}")
    print(f"  PM2.5 range: {panel['pm25_annual_mean'].min():.1f}-{panel['pm25_annual_mean'].max():.1f} μg/m³")
    return panel


def build_panel() -> pd.DataFrame:
    aqs       = load_all_aqs()
    monitors  = aggregate_monitors(aqs)
    districts = pd.read_csv(XWALK)
    districts["leaid"] = districts["leaid"].astype(str).str.zfill(7)

    print(f"\nRunning IDW for {districts.shape[0]:,} districts × {monitors['year'].nunique()} years...")
    print("(This may take 10-20 minutes depending on hardware)")

    panel = idw_to_districts(monitors, districts)

    out = OUT_DIR / "pm25_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    build_panel()
