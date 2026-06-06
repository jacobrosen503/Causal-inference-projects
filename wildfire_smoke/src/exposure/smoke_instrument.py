"""Build district-year wildfire smoke instrument from NOAA HMS shapefiles.

For each district x year: counts days with HMS Medium/Heavy smoke plume
over the district centroid (from NCES EDGE geocode file).

Input:  data/raw/hms_smoke/{year}/  (HMS shapefiles)
        data/crosswalks/district_centroids_edge.csv
Output: data/processed/smoke_instrument_district_year.parquet

Usage:
    python src/exposure/smoke_instrument.py
    python src/exposure/smoke_instrument.py 2015 2016   # specific years
"""
from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HMS_DIR   = PROJECT_ROOT / "data" / "raw" / "hms_smoke"
XWALK     = PROJECT_ROOT / "data" / "crosswalks" / "district_centroids_edge.csv"
OUT_DIR   = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_district_centroids() -> "gpd.GeoDataFrame":
    import geopandas as gpd
    from shapely.geometry import Point

    districts = pd.read_csv(XWALK)
    districts["leaid"] = districts["leaid"].astype(str).str.zfill(7)

    gdf = gpd.GeoDataFrame(
        districts,
        geometry=[Point(lon, lat) for lon, lat in zip(districts["lon"], districts["lat"])],
        crs="EPSG:4326"
    )
    print(f"District centroids loaded: {len(gdf):,} western districts")
    return gdf


def load_hms_year(year: int) -> "pd.DataFrame | None":
    import geopandas as gpd

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
            date_part = "".join(filter(str.isdigit, shp.stem))[:8]
            if len(date_part) == 8:
                gdf["date"] = pd.to_datetime(date_part, format="%Y%m%d", errors="coerce")
                density_col = next((c for c in gdf.columns if "dens" in c.lower()), None)
                if density_col:
                    gdf = gdf.rename(columns={density_col: "Density"})
                keep = ["geometry","date"] + (["Density"] if "Density" in gdf.columns else [])
                gdfs.append(gdf[keep])
        except Exception:
            pass

    return pd.concat(gdfs, ignore_index=True) if gdfs else None


def build_smoke_instrument(years: list[int] | None = None) -> pd.DataFrame:
    import geopandas as gpd

    districts = load_district_centroids()

    if years is None:
        years = list(range(2010, 2020))

    results = []
    for year in years:
        print(f"  Processing HMS {year}...")
        hms = load_hms_year(year)
        if hms is None:
            print(f"    No HMS data — run scripts/download_hms_smoke.py")
            continue

        hms_gdf = gpd.GeoDataFrame(hms, geometry="geometry", crs="EPSG:4326")
        daily_dates = hms_gdf["date"].dropna().unique()
        print(f"    {len(daily_dates)} days with smoke data")

        for _, dist in districts.iterrows():
            smoke_days = 0
            smoke_days_heavy = 0
            for date in daily_dates:
                day = hms_gdf[hms_gdf["date"] == date]
                if day.intersects(dist.geometry).any():
                    smoke_days += 1
                    if "Density" in day.columns:
                        if day[day.intersects(dist.geometry)]["Density"].eq("Heavy").any():
                            smoke_days_heavy += 1

            results.append({
                "leaid":            dist["leaid"],
                "year":             year,
                "smoke_days":       smoke_days,
                "smoke_days_heavy": smoke_days_heavy,
                "smoke_days_pct":   round(smoke_days / max(len(daily_dates), 1), 4),
            })

    panel = pd.DataFrame(results)
    out = OUT_DIR / "smoke_instrument_district_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}  ({len(panel):,} rows)")
    return panel


if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else None
    build_smoke_instrument(years)
