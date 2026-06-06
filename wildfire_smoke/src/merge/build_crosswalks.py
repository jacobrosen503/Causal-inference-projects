"""Build district-to-county crosswalk and attach county centroids.

Pivots to county-level geographic matching instead of district lat/lon,
which avoids needing NCES EDGE shapefiles. Most air quality papers use
county-level PM2.5 aggregation anyway.

Pipeline:
  1. Load CCD directory file -> extract LEAID + county FIPS (CONUM)
  2. Load committed county_centroids.csv -> county FIPS + lat/lon
  3. Join: LEAID -> county FIPS -> lat/lon
  4. Output: district_crosswalk.csv (used by epa_aqs.py and smoke_instrument.py)

Inputs:
  data/raw/nces/ccd_district_directory.csv   (the file you downloaded)
  data/crosswalks/county_centroids.csv       (committed — no download needed)

Output:
  data/crosswalks/district_crosswalk.csv

Usage:
    python src/merge/build_crosswalks.py
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CCD_FILE      = PROJECT_ROOT / "data" / "raw" / "nces" / "ccd_district_directory.csv"
CENTROIDS     = PROJECT_ROOT / "data" / "crosswalks" / "county_centroids.csv"
OUT_FILE      = PROJECT_ROOT / "data" / "crosswalks" / "district_crosswalk.csv"

WESTERN_STATES = ["CA","OR","WA","MT","ID","WY","CO","NV","AZ","NM","UT"]


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first candidate column name that exists in df (case-insensitive)."""
    upper = {c.upper(): c for c in df.columns}
    for cand in candidates:
        if cand.upper() in upper:
            return upper[cand.upper()]
    return None


def load_ccd(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    print(f"  CCD columns: {list(df.columns[:15])} ...")
    print(f"  CCD shape: {df.shape}")

    # Find LEAID column
    leaid_col = find_column(df, ["LEAID","LEA_ID","leaid"])
    if not leaid_col:
        raise KeyError(f"Cannot find LEAID column. Available: {list(df.columns)}")

    # Find county FIPS column — CCD uses CONUM (5-digit county FIPS)
    county_col = find_column(df, ["CONUM","CNTY","COUNTY","LCOUNTY","FIPSCNTY","county_fips"])
    if not county_col:
        print(f"  Warning: no county FIPS column found. Columns: {list(df.columns)}")
        print("  Will proceed without county FIPS — check column names above")

    # Find state column
    state_col = find_column(df, ["STABBR","STATE","LSTATE","stateabb"])

    # Find district name
    name_col = find_column(df, ["NAME","LEANM","DISTNAME","district_name"])

    keep = {leaid_col: "leaid"}
    if county_col: keep[county_col] = "county_fips"
    if state_col:  keep[state_col]  = "state"
    if name_col:   keep[name_col]   = "district_name"

    out = df[list(keep.keys())].rename(columns=keep)
    out["leaid"] = out["leaid"].astype(str).str.strip().str.zfill(7)

    if "county_fips" in out.columns:
        # Normalize to 5-digit string
        out["county_fips"] = (
            out["county_fips"].astype(str).str.strip()
            .str.replace(r"\.0$","",regex=True)
            .str.zfill(5)
        )

    if "state" in out.columns and WESTERN_STATES:
        out = out[out["state"].isin(WESTERN_STATES)]
        print(f"  After western filter: {len(out):,} districts")

    return out


def build_crosswalk() -> pd.DataFrame:
    if not CCD_FILE.exists():
        raise FileNotFoundError(f"CCD file not found: {CCD_FILE}")
    if not CENTROIDS.exists():
        raise FileNotFoundError(f"County centroids not found: {CENTROIDS}")

    print(f"Loading CCD: {CCD_FILE.name}")
    ccd = load_ccd(CCD_FILE)

    print(f"\nLoading county centroids: {CENTROIDS.name}")
    cent = pd.read_csv(CENTROIDS)
    # Use 2010 centroids; normalize FIPS to 5-digit string
    cent["county_fips"] = cent["fips"].astype(str).str.zfill(5)
    cent = cent[["county_fips","clat10","clon10"]].rename(
        columns={"clat10":"lat","clon10":"lon"}
    )
    print(f"  {len(cent):,} counties with centroids")

    if "county_fips" not in ccd.columns:
        raise ValueError(
            "county_fips not found in CCD file.\n"
            f"Available columns: {list(ccd.columns)}\n"
            "Look for the county FIPS column above and update find_column() candidates."
        )

    # Join
    crosswalk = ccd.merge(cent, on="county_fips", how="left")
    n_matched = crosswalk["lat"].notna().sum()
    print(f"\nMatched {n_matched:,} / {len(crosswalk):,} districts to county centroids")

    crosswalk.to_csv(OUT_FILE, index=False)
    print(f"Written: {OUT_FILE}")
    print(crosswalk.head(3).to_string())
    return crosswalk


if __name__ == "__main__":
    build_crosswalk()
