"""Build district crosswalk from NCES EDGE geocode shapefile.

Extracts LEAID, lat/lon, county FIPS, and locale from the NCES EDGE
geocode shapefile and saves a clean CSV for spatial joins.

Input:  data/raw/nces/EDGE_GEOCODE_PUBLICLEA_1819.shp  (or committed CSV)
Output: data/crosswalks/district_centroids_edge.csv

The committed CSV (western US only) is already in the repo.
Re-run this script only if you need to update or expand the crosswalk.

Usage:
    python src/merge/build_crosswalks.py
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHP_FILE  = PROJECT_ROOT / "data" / "raw" / "nces" / "EDGE_GEOCODE_PUBLICLEA_1819.shp"
OUT_FILE  = PROJECT_ROOT / "data" / "crosswalks" / "district_centroids_edge.csv"
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

WESTERN = {"CA","OR","WA","MT","ID","WY","CO","NV","AZ","NM","UT"}


def build_crosswalk() -> pd.DataFrame:
    # Use committed CSV if shapefile not available
    if not SHP_FILE.exists():
        if OUT_FILE.exists():
            print(f"Using committed crosswalk: {OUT_FILE}")
            return pd.read_csv(OUT_FILE)
        raise FileNotFoundError(
            f"Neither shapefile nor committed CSV found.\n"
            f"Download: https://nces.ed.gov/programs/edge/data/EDGE_GEOCODE_PUBLICLEA_1819.zip"
        )

    import geopandas as gpd
    print(f"Reading shapefile: {SHP_FILE.name}")
    gdf = gpd.read_file(SHP_FILE)

    crosswalk = gdf[["LEAID","NAME","STATE","STFIP","CNTY","NMCNTY","LAT","LON","LOCALE"]].copy()
    crosswalk.columns = ["leaid","district_name","state","state_fips","county_fips","county_name","lat","lon","locale"]
    crosswalk["leaid"]       = crosswalk["leaid"].astype(str).str.zfill(7)
    crosswalk["county_fips"] = crosswalk["county_fips"].astype(str).str.zfill(5)

    west = crosswalk[crosswalk["state"].isin(WESTERN)].copy()
    west.to_csv(OUT_FILE, index=False)
    print(f"Written: {OUT_FILE}  ({len(west):,} western districts)")
    return west


if __name__ == "__main__":
    df = build_crosswalk()
    print(df.head(3).to_string())
