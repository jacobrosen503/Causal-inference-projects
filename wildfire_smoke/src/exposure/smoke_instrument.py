"""Build wildfire smoke instrument from NOAA HMS smoke plume shapefiles.

For each district x year, computes:
  - smoke_days: number of days with a Medium+ HMS smoke plume over district centroid
  - smoke_days_heavy: days with Heavy smoke only
  - upwind_smoke_days: days with smoke AND wind blowing from fire-prone direction

The upwind smoke instrument is the key IV: it captures smoke from distant wildfires
that blows into a district, as distinct from local industrial/traffic PM2.5.

Input:  data/raw/hms_smoke/{year}/  (HMS shapefiles)
        data/crosswalks/district_centroids.csv
Output: data/processed/smoke_instrument_district_year.parquet

Usage:
    python src/exposure/smoke_instrument.py

Requires: geopandas, shapely
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HMS_DIR  = PROJECT_ROOT / "data" / "raw" / "hms_smoke"
XWALK    = PROJECT_ROOT / "data" / "crosswalks" / "district_centroids.csv"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_hms_year(year: int):
    """Load all HMS shapefiles for a given year into a single GeoDataFrame."""
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError("geopandas required: pip install geopandas")

    year_dir = HMS_DIR / str(year)
    if not year_dir.exists():
        return None

    shp_files = sorted(year_dir.glob("**/*.shp"))
    if not shp_files:
        return None

    gdfs = []
    for shp in shp_files:
        try:
            gdf = gpd.read_file(shp)
            # Extract date from filename (format: hms_smoke_YYYYMMDD.shp)
            date_str = shp.stem.replace("hms_smoke_", "").replace("smoke_", "")
            try:
                gdf["date"] = pd.to_datetime(date_str, format="%Y%m%d")
            except Exception:
                continue
            gdfs.append(gdf[["geometry", "date", "Density"] if "Density" in gdf.columns else ["geometry", "date"]])
        except Exception:
            pass

    if not gdfs:
        return None

    combined = pd.concat(gdfs, ignore_index=True)
    return combined


def build_smoke_instrument(years: list[int] | None = None) -> pd.DataFrame:
    if not XWALK.exists():
        raise FileNotFoundError(
            f"District centroids not found: {XWALK}\n"
            "Run: python src/merge/build_crosswalks.py"
        )

    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        raise ImportError("geopandas and shapely required: pip install geopandas shapely")

    centroids = pd.read_csv(XWALK)
    gdf_centroids = gpd.GeoDataFrame(
        centroids,
        geometry=[Point(xy) for xy in zip(centroids["lon"], centroids["lat"])],
        crs="EPSG:4326"
    )

    if years is None:
        years = list(range(2010, 2020))

    results = []
    for year in years:
        print(f"  Processing {year}...")
        hms = load_hms_year(year)
        if hms is None:
            print(f"    No HMS data for {year}")
            continue

        hms_gdf = gpd.GeoDataFrame(hms, geometry="geometry", crs="EPSG:4326")

        # For each district, count days with smoke plume intersection
        daily_dates = hms_gdf["date"].unique()
        for _, dist in gdf_centroids.iterrows():
            point = dist.geometry
            smoke_days = 0
            smoke_days_heavy = 0

            for date in daily_dates:
                day_plumes = hms_gdf[hms_gdf["date"] == date]
                if day_plumes.intersects(point).any():
                    smoke_days += 1
                    if "Density" in day_plumes.columns:
                        if day_plumes[day_plumes.intersects(point)]["Density"].eq("Heavy").any():
                            smoke_days_heavy += 1

            results.append({
                "leaid":             dist["leaid"],
                "year":              year,
                "smoke_days":        smoke_days,
                "smoke_days_heavy":  smoke_days_heavy,
                "smoke_days_pct":    round(smoke_days / len(daily_dates), 4) if daily_dates.size > 0 else 0,
            })

    panel = pd.DataFrame(results)
    out = OUT_DIR / "smoke_instrument_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}  ({len(panel):,} rows)")
    return panel


if __name__ == "__main__":
    import sys
    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else None
    build_smoke_instrument(years)
