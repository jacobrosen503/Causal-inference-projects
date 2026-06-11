"""Build wildfire smoke instrument from NOAA HMS smoke plume shapefiles.

For each district x year, computes:
  - smoke_days: number of days with a Medium+ HMS smoke plume over district centroid
  - smoke_days_heavy: days with Heavy smoke only
  - smoke_days_medium: days with Medium smoke only

The smoke_days instrument is the key IV: it captures smoke from distant wildfires
that blows into a district, as distinct from local industrial/traffic PM2.5.

Input:  data/raw/hms_smoke/{year}/  (HMS shapefiles)
        data/crosswalks/district_crosswalk.csv
Output: data/processed/smoke_instrument_district_year.parquet

Usage:
    python src/exposure/smoke_instrument.py
    python src/exposure/smoke_instrument.py 2010 2011 2012

Requires: geopandas, shapely
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HMS_DIR  = PROJECT_ROOT / "data" / "raw" / "hms_smoke"
XWALK    = PROJECT_ROOT / "data" / "crosswalks" / "district_crosswalk.csv"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_centroids_gdf():
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        raise ImportError("geopandas and shapely required: pip install geopandas shapely")

    if not XWALK.exists():
        raise FileNotFoundError(
            f"District crosswalk not found: {XWALK}\n"
            "Run: python src/merge/build_crosswalks.py"
        )

    centroids = pd.read_csv(XWALK).dropna(subset=["lat", "lon"])
    gdf = gpd.GeoDataFrame(
        centroids[["leaid", "lat", "lon"]],
        geometry=gpd.points_from_xy(centroids["lon"], centroids["lat"]),
        crs="EPSG:4326",
    )
    return gdf


def load_hms_year(year: int):
    """Load all HMS shapefiles for a given year into a single GeoDataFrame."""
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError("geopandas required: pip install geopandas")

    year_dir = HMS_DIR / str(year)
    if not year_dir.exists():
        return None

    shp_files = sorted(year_dir.glob("*.shp"))
    if not shp_files:
        return None

    gdfs = []
    for shp in shp_files:
        try:
            gdf = gpd.read_file(shp)
            # Filename format: hms_smoke20100101.shp  (no underscore before date)
            stem = shp.stem  # e.g. "hms_smoke20100101"
            date_str = stem[-8:]  # last 8 chars = YYYYMMDD
            gdf["date"] = pd.to_datetime(date_str, format="%Y%m%d", errors="coerce")
            if gdf["date"].isna().all():
                continue
            keep_cols = ["geometry", "date"]
            if "Density" in gdf.columns:
                keep_cols.append("Density")
            gdfs.append(gdf[keep_cols])
        except Exception:
            pass

    if not gdfs:
        return None

    return pd.concat(gdfs, ignore_index=True)


def build_smoke_instrument(years: list[int] | None = None) -> pd.DataFrame:
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError("geopandas and shapely required: pip install geopandas shapely")

    gdf_centroids = load_centroids_gdf()
    print(f"Loaded {len(gdf_centroids):,} district centroids")

    if years is None:
        years = [y for y in range(2010, 2020) if (HMS_DIR / str(y)).exists()]

    all_results = []
    for year in years:
        print(f"  Processing {year}...")
        hms_raw = load_hms_year(year)
        if hms_raw is None:
            print(f"    No HMS data for {year}")
            continue

        hms_gdf = gpd.GeoDataFrame(hms_raw, geometry="geometry", crs="EPSG:4326")

        # Spatial join: each day, find which district centroids fall inside a smoke plume
        # Then count days per district
        dates = sorted(hms_gdf["date"].dropna().unique())
        print(f"    {len(dates)} smoke-plume days loaded")

        # Initialize counters
        smoke_count = {leaid: 0 for leaid in gdf_centroids["leaid"]}
        heavy_count = {leaid: 0 for leaid in gdf_centroids["leaid"]}
        medium_count = {leaid: 0 for leaid in gdf_centroids["leaid"]}

        for date in dates:
            day_plumes = hms_gdf[hms_gdf["date"] == date].copy()
            if day_plumes.empty:
                continue

            # Spatial join: points in polygons
            joined = gpd.sjoin(gdf_centroids, day_plumes, how="inner", predicate="within")
            for leaid in joined["leaid"].unique():
                smoke_count[leaid] = smoke_count.get(leaid, 0) + 1
                if "Density" in joined.columns:
                    rows = joined[joined["leaid"] == leaid]["Density"]
                    if rows.eq("Heavy").any():
                        heavy_count[leaid] = heavy_count.get(leaid, 0) + 1
                    elif rows.eq("Medium").any():
                        medium_count[leaid] = medium_count.get(leaid, 0) + 1

        for leaid in gdf_centroids["leaid"]:
            all_results.append({
                "leaid":              leaid,
                "year":               year,
                "smoke_days":         smoke_count.get(leaid, 0),
                "smoke_days_heavy":   heavy_count.get(leaid, 0),
                "smoke_days_medium":  medium_count.get(leaid, 0),
            })

        print(f"    Done: {sum(1 for v in smoke_count.values() if v > 0):,} districts had smoke days")

    panel = pd.DataFrame(all_results)
    out = OUT_DIR / "smoke_instrument_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"\nWritten: {out}  ({len(panel):,} rows)")
    return panel


if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else None
    build_smoke_instrument(years)
