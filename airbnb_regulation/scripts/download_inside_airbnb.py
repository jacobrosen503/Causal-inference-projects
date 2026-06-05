"""Download real Inside Airbnb listing snapshots for all study cities.

Run this locally in Cursor (insideairbnb.com is not accessible in all environments).
Downloads listings.csv.gz for each city-snapshot and saves to data/raw/.

Estimated download: ~500MB total across all cities and snapshots.
After downloading, run: python scripts/build_real_panel.py

Usage:
    python scripts/download_inside_airbnb.py
    python scripts/download_inside_airbnb.py --cities nyc florence  # subset
"""
from __future__ import annotations

import argparse
import gzip
import shutil
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Inside Airbnb snapshot URLs
# Format: http://data.insideairbnb.com/{country}/{region}/{city}/{date}/data/listings.csv.gz
# Dates confirmed available as of May 2026 — update if new snapshots released.

SNAPSHOTS = {
    "nyc": {
        "label": "New York City",
        "urls": [
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2021-07-11/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2022-03-06/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2022-09-07/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2023-03-06/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2023-06-05/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2023-09-05/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2023-12-04/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2024-03-04/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2024-06-02/data/listings.csv.gz",
            "http://data.insideairbnb.com/united-states/ny/new-york-city/2024-09-05/data/listings.csv.gz",
        ],
    },
    "florence": {
        "label": "Florence",
        "urls": [
            "http://data.insideairbnb.com/italy/toscana/florence/2022-03-12/data/listings.csv.gz",
            "http://data.insideairbnb.com/italy/toscana/florence/2022-09-16/data/listings.csv.gz",
            "http://data.insideairbnb.com/italy/toscana/florence/2023-03-16/data/listings.csv.gz",
            "http://data.insideairbnb.com/italy/toscana/florence/2023-09-16/data/listings.csv.gz",
            "http://data.insideairbnb.com/italy/toscana/florence/2023-12-16/data/listings.csv.gz",
            "http://data.insideairbnb.com/italy/toscana/florence/2024-03-20/data/listings.csv.gz",
            "http://data.insideairbnb.com/italy/toscana/florence/2024-06-15/data/listings.csv.gz",
        ],
    },
    "amsterdam": {
        "label": "Amsterdam",
        "urls": [
            "http://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2021-12-05/data/listings.csv.gz",
            "http://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2022-06-05/data/listings.csv.gz",
            "http://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2022-12-05/data/listings.csv.gz",
            "http://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2023-06-05/data/listings.csv.gz",
            "http://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2023-12-05/data/listings.csv.gz",
            "http://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2024-06-05/data/listings.csv.gz",
        ],
    },
    "lisbon": {
        "label": "Lisbon",
        "urls": [
            "http://data.insideairbnb.com/portugal/lisbon/lisbon/2021-10-27/data/listings.csv.gz",
            "http://data.insideairbnb.com/portugal/lisbon/lisbon/2022-09-14/data/listings.csv.gz",
            "http://data.insideairbnb.com/portugal/lisbon/lisbon/2023-03-21/data/listings.csv.gz",
            "http://data.insideairbnb.com/portugal/lisbon/lisbon/2023-09-14/data/listings.csv.gz",
            "http://data.insideairbnb.com/portugal/lisbon/lisbon/2024-03-20/data/listings.csv.gz",
            "http://data.insideairbnb.com/portugal/lisbon/lisbon/2024-09-14/data/listings.csv.gz",
        ],
    },
    "vienna": {
        "label": "Vienna",
        "urls": [
            "http://data.insideairbnb.com/austria/vienna/vienna/2021-11-04/data/listings.csv.gz",
            "http://data.insideairbnb.com/austria/vienna/vienna/2022-09-09/data/listings.csv.gz",
            "http://data.insideairbnb.com/austria/vienna/vienna/2023-06-12/data/listings.csv.gz",
            "http://data.insideairbnb.com/austria/vienna/vienna/2023-12-24/data/listings.csv.gz",
            "http://data.insideairbnb.com/austria/vienna/vienna/2024-06-18/data/listings.csv.gz",
        ],
    },
    "barcelona": {
        "label": "Barcelona",
        "urls": [
            "http://data.insideairbnb.com/spain/catalonia/barcelona/2021-11-07/data/listings.csv.gz",
            "http://data.insideairbnb.com/spain/catalonia/barcelona/2022-09-12/data/listings.csv.gz",
            "http://data.insideairbnb.com/spain/catalonia/barcelona/2023-03-15/data/listings.csv.gz",
            "http://data.insideairbnb.com/spain/catalonia/barcelona/2023-09-04/data/listings.csv.gz",
            "http://data.insideairbnb.com/spain/catalonia/barcelona/2024-03-12/data/listings.csv.gz",
            "http://data.insideairbnb.com/spain/catalonia/barcelona/2024-09-04/data/listings.csv.gz",
        ],
    },
}


def download_file(url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"    [skip] {dest.name} already exists")
        return True
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        size_mb = dest.stat().st_size / 1e6
        print(f"    [ok]   {dest.name}  ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"    [fail] {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cities", nargs="+", choices=list(SNAPSHOTS.keys()),
                        default=list(SNAPSHOTS.keys()))
    args = parser.parse_args()

    total = ok = fail = 0
    for city_key in args.cities:
        city = SNAPSHOTS[city_key]
        print(f"\n{city['label']}")
        city_dir = RAW_DIR / city_key
        city_dir.mkdir(exist_ok=True)

        for url in city["urls"]:
            snapshot_date = url.split("/")[-4]
            dest = city_dir / f"{city_key}_{snapshot_date}_listings.csv.gz"
            total += 1
            if download_file(url, dest):
                ok += 1
            else:
                fail += 1
            time.sleep(0.5)

    print(f"\nDownloaded {ok}/{total} files ({fail} failed)")
    if ok > 0:
        print("Next step: python scripts/build_real_panel.py")


if __name__ == "__main__":
    main()
