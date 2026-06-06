"""Build county-year wildfire smoke instrument from NOAA HMS shapefiles.

For each county x year: counts days with HMS Medium/Heavy smoke plume
over the county centroid. This is the IV for PM2.5 exposure.

Uses committed county_centroids.csv — no district lat/lon needed.

Input:  data/raw/hms_smoke/{year}/  (HMS shapefiles)
        data/crosswalks/county_centroids.csv
Output: data/processed/smoke_instrument_county_year.parquet

Usage:
    python src/exposure/smoke_instrument.py
    python src/exposure/smoke_instrument.py 2015 2016 2017   # specific years
"""
from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HMS_DIR   = PROJECT_ROOT / "data" / "raw" / "hms_smoke"
CENTROIDS = PROJECT_ROOT / "data" / "crosswalks" / "county_centroids.csv"
OUT_DIR   = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Western US county FIPS prefixes (state FIPS)
WESTERN_STATE_FIPS = {"06","41","53","30","16","56","08","32","04","35","49"}


def load_county_centroids() -> pd.DataFrame:
    if not CENTROIDS.exists():
        raise FileNotFoundError(f"County centroids not found: {CENTROIDS}")
    cent = pd.read_csv(CENTROIDS)
    cent["county_fips"] = cent["fips"].astype(str).str.zfill(5)
    cent = cent[["county_fips","clat10","clon10"]].rename(
        columns={"clat10":"lat","clon10":"lon"}
    )
    # Filter to western states
    cent = cent[cent["county_fips"].str[:2].isin(WESTERN_STATE_FIPS)]
    print(f"County centroids loaded: {len(cent):,} western counties")
    return cent


def load_hms_year(year: int):
    """Load all HMS shapefiles for a year into one GeoDataFrame."""
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
            # Extract date from filename
            stem = shp.stem
            date_part = "".join(filter(str.isdigit, stem))[:8]
            if len(date_part) == 8:
                gdf["date"] = pd.to_datetime(date_part, format="%Y%m%d", errors="coerce")
            else:
                continue
            density_col = next((c for c in gdf.columns if "dens" in c.lower()), None)
            keep = ["geometry","date"]
            if density_col:
                keep.append(density_col)
                gdf = gdf.rename(columns={density_col:"Density"})
            gdfs.append(gdf[keep] if density_col else gdf[["geometry","date"]])
        except Exception:
            pass

    if not gdfs:
        return None
    return pd.concat(gdfs, ignore_index=True)


def build_smoke_instrument(years: list[int] | None = None) -> pd.DataFrame:
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        raise ImportError("pip install geopandas shapely")

    centroids = load_county_centroids()
    gdf_cent = gpd.GeoDataFrame(
        centroids,
        geometry=[Point(lon, lat) for lon, lat in zip(centroids["lon"], centroids["lat"])],
        crs="EPSG:4326"
    )

    if years is None:
        years = list(range(2010, 2020))

    results = []
    for year in years:
        print(f"  Processing HMS {year}...")
        hms = load_hms_year(year)
        if hms is None:
            print(f"    No data for {year} — run scripts/download_hms_smoke.py")
            continue

        hms_gdf = gpd.GeoDataFrame(hms, geometry="geometry", crs="EPSG:4326")
        daily_dates = hms_gdf["date"].dropna().unique()
        print(f"    {len(daily_dates)} smoke days in {year}")

        # For each county centroid, count days with smoke plume intersection
        for _, county in gdf_cent.iterrows():
            smoke_days = 0
            smoke_days_heavy = 0
            for date in daily_dates:
                day = hms_gdf[hms_gdf["date"] == date]
                if day.intersects(county.geometry).any():
                    smoke_days += 1
                    if "Density" in day.columns:
                        if day[day.intersects(county.geometry)]["Density"].eq("Heavy").any():
                            smoke_days_heavy += 1
            results.append({
                "county_fips":       county["county_fips"],
                "year":              year,
                "smoke_days":        smoke_days,
                "smoke_days_heavy":  smoke_days_heavy,
                "smoke_days_pct":    round(smoke_days / max(len(daily_dates), 1), 4),
            })

    panel = pd.DataFrame(results)
    out = OUT_DIR / "smoke_instrument_county_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}  ({len(panel):,} rows)")
    return panel


if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else None
    build_smoke_instrument(years)
