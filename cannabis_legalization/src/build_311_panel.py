"""Build NYC neighborhood-month panel from 311 complaint data.

Aggregates raw 311 CSV to zip code x month counts by complaint type.
Merges dispensary opening events.

Usage:
    python src/build_311_panel.py

Output: data/processed/nyc_311_zip_month.parquet
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_311  = PROJECT_ROOT / "data" / "raw" / "nyc_311" / "nyc_311_cannabis_relevant.csv"
RAW_DISP = PROJECT_ROOT / "data" / "raw" / "dispensaries" / "ny_cannabis_licenses.csv"
OUT_DIR  = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


COMPLAINT_TYPES = [
    "Drug Activity",
    "Noise - Residential",
    "Noise - Street/Sidewalk",
    "Illegal Parking",
    "Disorderly Youth",
]


def load_311() -> pd.DataFrame:
    if not RAW_311.exists():
        raise FileNotFoundError(
            f"{RAW_311} not found. "
            "Run: python scripts/download_311.py --auto  (or manual export from NYC Open Data)"
        )
    print(f"Loading 311 data from {RAW_311} ...")
    df = pd.read_csv(RAW_311, low_memory=False, parse_dates=["created_date"])
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    print(f"  Loaded {len(df):,} rows")
    return df


def load_dispensaries() -> pd.DataFrame:
    if not RAW_DISP.exists():
        raise FileNotFoundError(
            f"{RAW_DISP} not found. "
            "Run: python scripts/download_dispensaries.py --auto"
        )
    df = pd.read_csv(RAW_DISP, low_memory=False)
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    return df


def build_311_panel(df_311: pd.DataFrame) -> pd.DataFrame:
    """Aggregate 311 complaints to zip_code x month x complaint_type."""
    df = df_311.copy()

    # Normalize date
    if "created_date" not in df.columns:
        raise KeyError("Expected 'created_date' column in 311 data")
    df["month"] = df["created_date"].dt.to_period("M").dt.to_timestamp()

    # Normalize zip
    zip_col = next((c for c in df.columns if "zip" in c), None)
    if zip_col:
        df["zip"] = df[zip_col].astype(str).str.strip().str[:5]
    else:
        raise KeyError("No zip code column found in 311 data")

    # Filter to relevant complaint types
    if "complaint_type" in df.columns:
        df = df[df["complaint_type"].isin(COMPLAINT_TYPES)]

    # Aggregate
    panel = (
        df.groupby(["zip", "month", "complaint_type"])
        .size()
        .reset_index(name="n_complaints")
    )

    # Also build a total complaints column
    total = (
        df.groupby(["zip", "month"])
        .size()
        .reset_index(name="total_complaints")
    )

    panel = panel.pivot_table(
        index=["zip", "month"],
        columns="complaint_type",
        values="n_complaints",
        fill_value=0
    ).reset_index()
    panel.columns = [
        c if c in ("zip", "month") else f"n_{c.lower().replace(' - ', '_').replace(' ', '_')}"
        for c in panel.columns
    ]
    panel = panel.merge(total, on=["zip", "month"], how="left")
    panel["log_total_complaints"] = np.log1p(panel["total_complaints"])
    return panel


def build_dispensary_events(disp_df: pd.DataFrame) -> pd.DataFrame:
    """Extract NYC dispensary locations and opening months."""
    # Filter to NYC (by zip prefix or borough)
    nyc_zips = set(range(10001, 10283)) | set(range(11001, 11697))

    # Normalize columns
    zip_col  = next((c for c in disp_df.columns if "zip" in c), None)
    date_col = next((c for c in disp_df.columns if "effective" in c or "issue" in c or "date" in c), None)
    lat_col  = next((c for c in disp_df.columns if "lat" in c), None)
    lon_col  = next((c for c in disp_df.columns if "lon" in c or "lng" in c), None)

    disp_df = disp_df.copy()
    if zip_col:
        disp_df["zip"] = disp_df[zip_col].astype(str).str.strip().str[:5]
        disp_df = disp_df[pd.to_numeric(disp_df["zip"], errors="coerce").between(10001, 11697)]

    if date_col:
        disp_df["open_month"] = pd.to_datetime(disp_df[date_col], errors="coerce").dt.to_period("M").dt.to_timestamp()
    else:
        disp_df["open_month"] = pd.NaT

    cols = ["zip", "open_month"]
    if lat_col: cols.append(lat_col)
    if lon_col: cols.append(lon_col)

    return disp_df[[c for c in cols if c in disp_df.columns]].dropna(subset=["zip", "open_month"])


def build_panel():
    df_311  = load_311()
    panel   = build_311_panel(df_311)

    try:
        disp_df = load_dispensaries()
        events  = build_dispensary_events(disp_df)
        events.to_parquet(OUT_DIR / "nyc_dispensary_events.parquet", index=False)
        print(f"Written: nyc_dispensary_events.parquet  ({len(events)} dispensaries)")
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Proceeding without dispensary event file.")

    out = OUT_DIR / "nyc_311_zip_month.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}  ({len(panel):,} rows, {panel['zip'].nunique()} zip codes)")
    return panel


if __name__ == "__main__":
    build_panel()
