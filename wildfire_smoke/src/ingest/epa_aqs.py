"""Build district-year PM2.5 panel from EPA AQS annual summary data.

Reads pre-aggregated annual monitor files (one row per monitor per year)
and IDW-averages to district centroids within 100km.

Input:  data/raw/epa_aqs/pm25_annual_{state}_{year}.csv
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
RAW_DIR  = PROJECT_ROOT / "data" / "raw" / "epa_aqs"
XWALK    = PROJECT_ROOT / "data" / "crosswalks" / "district_centroids_edge.csv"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_DIST_KM = 100


def haversine_km(lat1, lon1, lat2_arr, lon2_arr):
    R = 6371.0
    dlat = np.radians(lat2_arr - lat1)
    dlon = np.radians(lon2_arr - lon1)
    a = (np.sin(dlat/2)**2
         + np.cos(np.radians(lat1))
         * np.cos(np.radians(lat2_arr))
         * np.sin(dlon/2)**2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def load_annual_files() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("pm25_annual_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No annual files in {RAW_DIR}.\n"
            "Run: python scripts/download_epa_aqs.py --email EMAIL --key bluekit86"
        )

    dfs = []
    for f in files:
        if f.stat().st_size == 0:
            continue
        try:
            dfs.append(pd.read_csv(f, low_memory=False))
        except Exception as e:
            print(f"  Warning: {f.name} — {e}")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(files)} files — {len(combined):,} monitor-year records")
    return combined


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize EPA annual summary column names."""
    df.columns = [c.lower().strip().replace(" ","_") for c in df.columns]

    # Annual summary key columns
    rename = {
        "arithmetic_mean":          "pm25_mean",
        "observation_percent":      "obs_pct",
        "year":                     "year",
        "latitude":                 "lat",
        "longitude":                "lon",
        "state_code":               "state_fips",
        "county_code":              "county_fips_3",
        "site_num":                 "site_num",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    df["pm25_mean"] = pd.to_numeric(df.get("pm25_mean", np.nan), errors="coerce")
    df["lat"]       = pd.to_numeric(df.get("lat", np.nan), errors="coerce")
    df["lon"]       = pd.to_numeric(df.get("lon", np.nan), errors="coerce")
    df["year"]      = pd.to_numeric(df.get("year", np.nan), errors="coerce").astype("Int64")

    # Drop bad values
    df = df.dropna(subset=["pm25_mean","lat","lon","year"])
    df = df[df["pm25_mean"].between(0, 200)]

    return df


def idw_to_districts(monitors: pd.DataFrame,
                     districts: pd.DataFrame) -> pd.DataFrame:
    mon_lats = monitors["lat"].values
    mon_lons = monitors["lon"].values
    mon_pm   = monitors["pm25_mean"].values

    results = []
    for _, dist in districts.iterrows():
        dists_km = haversine_km(dist["lat"], dist["lon"], mon_lats, mon_lons)
        nearby   = dists_km <= MAX_DIST_KM

        if not nearby.any():
            continue

        d  = dists_km[nearby]
        pm = mon_pm[nearby]
        w  = 1.0 / (d**2 + 1e-6)
        results.append({
            "leaid":            dist["leaid"],
            "year":             dist["_year"],
            "pm25_annual_mean": round(float((pm * w).sum() / w.sum()), 3),
            "n_monitors":       int(nearby.sum()),
        })
    return pd.DataFrame(results)


def build_panel() -> pd.DataFrame:
    raw       = load_annual_files()
    monitors  = normalize(raw)
    districts = pd.read_csv(XWALK)
    districts["leaid"] = districts["leaid"].astype(str).str.zfill(7)

    years = sorted(monitors["year"].dropna().unique())
    print(f"Years: {[int(y) for y in years]}")
    print(f"Districts: {len(districts):,}")
    print(f"\nRunning IDW ({len(districts):,} districts × {len(years)} years)...")
    print("Expected time: 5-15 minutes")

    all_results = []
    for year in years:
        yr_mon = monitors[monitors["year"] == year].copy()
        if yr_mon.empty:
            continue
        # Attach year to districts for the IDW function
        districts["_year"] = int(year)
        yr_results = idw_to_districts(yr_mon, districts)
        all_results.append(yr_results)
        print(f"  {int(year)}: {len(yr_results):,} districts matched")

    panel = pd.concat(all_results, ignore_index=True)
    panel["log_pm25"] = np.log(panel["pm25_annual_mean"].clip(lower=0.1))

    print(f"\nPM2.5 panel: {panel.shape}")
    print(f"PM2.5 range: {panel['pm25_annual_mean'].min():.1f} — {panel['pm25_annual_mean'].max():.1f} μg/m³")

    out = OUT_DIR / "pm25_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")
    return panel


if __name__ == "__main__":
    build_panel()
