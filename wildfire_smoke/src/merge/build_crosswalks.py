"""Build district centroid crosswalk from NCES CCD directory file.

Joins CCD lat/lon to SEDA district IDs to enable spatial joins
with EPA monitors and HMS smoke plumes.

Input:  data/raw/nces/ccd_district_directory.csv
Output: data/crosswalks/district_centroids.csv

Download CCD directory:
    https://nces.ed.gov/ccd/pubagency.asp
    -> Select most recent year -> Download CSV ("Directory" file)
    -> Save to data/raw/nces/ccd_district_directory.csv

Usage:
    python src/merge/build_crosswalks.py
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CCD_FILE  = PROJECT_ROOT / "data" / "raw" / "nces" / "ccd_district_directory.csv"
OUT_FILE  = PROJECT_ROOT / "data" / "crosswalks" / "district_centroids.csv"
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Western US states we need
WESTERN_STATES = ["CA","OR","WA","MT","ID","WY","CO","NV","AZ","NM","UT"]


def load_ccd(path: Path) -> pd.DataFrame:
    # CCD column names vary slightly by year — normalize
    df = pd.read_csv(path, low_memory=False, encoding="latin-1")
    df.columns = [c.strip().upper() for c in df.columns]

    rename = {
        "LEAID":   "leaid",
        "LATCOD":  "lat",
        "LONCOD":  "lon",
        "CNTY":    "county_fips",
        "STABBR":  "state",
        "NAME":    "district_name",
        "LEANM":   "district_name",
        # Some years use these variants
        "LAT1516": "lat",
        "LON1516": "lon",
        "LAT1718": "lat",
        "LON1718": "lon",
        "LAT1920": "lat",
        "LON1920": "lon",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # If lat/lon still not found, look for any LAT/LON column
    if "lat" not in df.columns:
        lat_cols = [c for c in df.columns if c.startswith("LAT")]
        lon_cols = [c for c in df.columns if c.startswith("LON")]
        if lat_cols:
            df = df.rename(columns={lat_cols[0]: "lat", lon_cols[0]: "lon"})
            print(f"  Using lat/lon columns: {lat_cols[0]}, {lon_cols[0]}")

    return df


def build_crosswalk() -> pd.DataFrame:
    if not CCD_FILE.exists():
        raise FileNotFoundError(
            f"{CCD_FILE} not found.\n"
            "Download from: https://nces.ed.gov/ccd/pubagency.asp\n"
            "  -> Most recent year -> CSV Directory file\n"
            "  -> Save to data/raw/nces/ccd_district_directory.csv"
        )

    print(f"Loading CCD: {CCD_FILE}")
    ccd = load_ccd(CCD_FILE)
    print(f"  Raw: {ccd.shape} | Columns found: {[c for c in ['leaid','lat','lon','county_fips','state'] if c in ccd.columns]}")

    # Filter to western states if state column available
    if "state" in ccd.columns:
        ccd = ccd[ccd["state"].isin(WESTERN_STATES)]
        print(f"  After western state filter: {len(ccd):,} districts")

    # Keep only what we need
    keep = ["leaid","lat","lon","county_fips","state","district_name"]
    keep = [c for c in keep if c in ccd.columns]
    crosswalk = ccd[keep].copy()

    # Clean coordinates
    crosswalk["lat"] = pd.to_numeric(crosswalk["lat"], errors="coerce")
    crosswalk["lon"] = pd.to_numeric(crosswalk["lon"], errors="coerce")

    # Drop missing coords
    n_before = len(crosswalk)
    crosswalk = crosswalk.dropna(subset=["lat","lon"])
    crosswalk = crosswalk[crosswalk["lat"].between(-90, 90)]
    crosswalk = crosswalk[crosswalk["lon"].between(-180, 0)]
    print(f"  Valid coordinates: {len(crosswalk):,} / {n_before:,} districts")

    # Normalize LEAID to string
    crosswalk["leaid"] = crosswalk["leaid"].astype(str).str.strip()

    crosswalk.to_csv(OUT_FILE, index=False)
    print(f"Written: {OUT_FILE}")

    # Sample
    print(crosswalk.head(3).to_string())
    return crosswalk


if __name__ == "__main__":
    build_crosswalk()
