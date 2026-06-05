"""Build a city-month panel from real Inside Airbnb snapshot CSVs.

Run after: python scripts/download_inside_airbnb.py

Aggregates listing-level snapshots to city-month:
  - log_listings: log count of active listings
  - mean_price_usd: mean nightly price
  - availability_rate: mean availability_365 / 365
  - entire_home_share: share of entire home/apt listings

Output: data/processed/city_month_panel_real.parquet
        (same schema as synthetic panel; swap into notebooks by changing DATA_FILE)
"""
from __future__ import annotations

import gzip
import re
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
OUT_DIR      = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CITY_META = {
    "nyc":       {"label": "New York City", "country": "USA"},
    "florence":  {"label": "Florence",      "country": "Italy"},
    "amsterdam": {"label": "Amsterdam",     "country": "Netherlands"},
    "lisbon":    {"label": "Lisbon",        "country": "Portugal"},
    "vienna":    {"label": "Vienna",        "country": "Austria"},
    "barcelona": {"label": "Barcelona",     "country": "Spain"},
}

NYC_TREAT    = pd.Timestamp("2023-09-01")
FLORENCE_TREAT = pd.Timestamp("2023-10-01")


def parse_price(s) -> float:
    if pd.isna(s):
        return np.nan
    return float(re.sub(r"[^0-9.]", "", str(s)))


def load_snapshot(path: Path) -> pd.DataFrame:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        df = pd.read_csv(f, low_memory=False)
    return df


def aggregate_snapshot(df: pd.DataFrame, snapshot_date: pd.Timestamp) -> dict:
    df = df.copy()
    df["price_clean"] = df["price"].apply(parse_price)

    # Active listing = has a price and availability > 0
    active = df[df["price_clean"].notna() & (df["price_clean"] > 0)].copy()

    n = len(active)
    mean_price = active["price_clean"].median()  # median more robust than mean

    # Availability: use availability_365 if present, else availability_30
    avail_col = "availability_365" if "availability_365" in active.columns else "availability_30"
    avail_denom = 365 if avail_col == "availability_365" else 30
    availability = active[avail_col].mean() / avail_denom if avail_col in active.columns else np.nan

    # Entire home share
    eh_share = (active["room_type"] == "Entire home/apt").mean() if "room_type" in active.columns else np.nan

    return {
        "snapshot_date": snapshot_date,
        "n_listings":    n,
        "log_listings":  np.log(max(n, 1)),
        "mean_price_usd": mean_price,
        "log_price":     np.log(max(mean_price, 1)) if not np.isnan(mean_price) else np.nan,
        "availability_rate": availability,
        "entire_home_share": eh_share,
    }


def build_city_series(city_key: str) -> pd.DataFrame:
    city_dir = RAW_DIR / city_key
    if not city_dir.exists():
        print(f"  [{city_key}] no raw data — skipping")
        return pd.DataFrame()

    files = sorted(city_dir.glob("*.csv.gz"))
    if not files:
        print(f"  [{city_key}] no files in {city_dir}")
        return pd.DataFrame()

    rows = []
    for f in files:
        # Extract date from filename: citykey_YYYY-MM-DD_listings.csv.gz
        match = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        if not match:
            continue
        snap_date = pd.Timestamp(match.group(1))
        # Snap to month start
        month = snap_date.to_period("M").to_timestamp()

        print(f"  [{city_key}] {f.name}")
        df = load_snapshot(f)
        agg = aggregate_snapshot(df, snap_date)
        agg["month"] = month
        rows.append(agg)

    if not rows:
        return pd.DataFrame()

    series = pd.DataFrame(rows).sort_values("month").drop_duplicates("month")

    meta = CITY_META[city_key]
    series["city"]    = meta["label"]
    series["country"] = meta["country"]

    # Post-treatment indicators
    series["is_treated_city"] = city_key in ("nyc", "florence")
    series["post"] = False
    if city_key == "nyc":
        series["post"] = series["month"] >= NYC_TREAT
        series["treat_col"] = "treat_nyc"
    elif city_key == "florence":
        series["post"] = series["month"] >= FLORENCE_TREAT
        series["treat_col"] = "treat_florence"
    else:
        series["treat_col"] = ""

    series["is_simulated"] = False
    return series


def main():
    all_series = []
    for city_key in CITY_META:
        s = build_city_series(city_key)
        if not s.empty:
            all_series.append(s)

    if not all_series:
        print("No data found. Run download_inside_airbnb.py first.")
        return

    panel = pd.concat(all_series, ignore_index=True)
    panel = panel.sort_values(["city", "month"]).reset_index(drop=True)
    panel["year_month"] = panel["month"].dt.strftime("%Y-%m")
    panel["month_idx"]  = panel.groupby("city")["month"].transform(
        lambda s: (s.dt.to_period("M") - s.min().to_period("M")).apply(lambda x: x.n)
    )

    out = OUT_DIR / "city_month_panel_real.parquet"
    panel.to_parquet(out, index=False)
    print(f"\nWritten: {out}")
    print(f"  Cities : {panel['city'].nunique()}")
    print(f"  Rows   : {len(panel):,}")
    print(f"\nTo use in notebooks: set DATA_FILE = 'city_month_panel_real.parquet'")


if __name__ == "__main__":
    main()
