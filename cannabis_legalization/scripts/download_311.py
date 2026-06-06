"""Download NYC 311 Service Request data for cannabis-relevant complaint types.

NYC Open Data hosts 311 data from 2010 to present via the Socrata API.
Full dataset is ~35GB; we filter to relevant complaint types and date range.

Dataset: 311 Service Requests from 2010 to Present
URL: https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9
API endpoint: https://data.cityofnewyork.us/resource/erm2-nwe9.json

Complaint types we want:
    - Drug Activity
    - Noise - Residential
    - Noise - Street/Sidewalk
    - Illegal Parking
    - Disorderly Youth

Date range: 2020-01-01 to 2024-12-31
    (pre-period before first NYC dispensary Dec 2022; post-period through 2024)

Option A — NYC Open Data web export (easiest)
---------------------------------------------
1. Go to: https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9
2. Click Filter -> Add a New Filter Condition:
   - created_date is between 2020-01-01 and 2024-12-31
   - complaint_type in (Drug Activity, Noise - Residential, Noise - Street/Sidewalk, Illegal Parking, Disorderly Youth)
3. Export -> CSV for Spreadsheets
4. Save to: data/raw/nyc_311/nyc_311_cannabis_relevant.csv

Option B — Automated API download (script below)
-------------------------------------------------
Run: python scripts/download_311.py --auto

This uses the Socrata API with pagination. Expect ~500K-2M rows.
Estimated download time: 10-30 minutes.

After downloading:
    python scripts/build_311_panel.py
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "nyc_311"
RAW_DIR.mkdir(parents=True, exist_ok=True)

COMPLAINT_TYPES = [
    "Drug Activity",
    "Noise - Residential",
    "Noise - Street/Sidewalk",
    "Illegal Parking",
    "Disorderly Youth",
]

START_DATE = "2020-01-01T00:00:00"
END_DATE   = "2024-12-31T23:59:59"
ENDPOINT   = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
PAGE_SIZE  = 50000


def build_query(offset: int) -> str:
    types = ", ".join(f"'{t}'" for t in COMPLAINT_TYPES)
    where = (
        f"created_date >= '{START_DATE}' "
        f"AND created_date <= '{END_DATE}' "
        f"AND complaint_type in({types})"
    )
    select = "unique_key,created_date,complaint_type,incident_zip,borough,latitude,longitude,community_board"
    return (
        f"{ENDPOINT}"
        f"?$where={where}"
        f"&$select={select}"
        f"&$limit={PAGE_SIZE}"
        f"&$offset={offset}"
        f"&$order=created_date ASC"
    )


def download_all():
    try:
        import requests
        import csv
        import json
    except ImportError:
        print("requests not installed: pip install requests")
        return

    out_path = RAW_DIR / "nyc_311_cannabis_relevant.csv"
    total = 0
    offset = 0
    first = True

    print(f"Downloading NYC 311 data to {out_path}")
    print(f"Complaint types: {COMPLAINT_TYPES}")
    print(f"Date range: {START_DATE} to {END_DATE}\n")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = None
        while True:
            url = build_query(offset)
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                records = r.json()
            except Exception as e:
                print(f"Error at offset {offset}: {e}")
                break

            if not records:
                break

            if writer is None:
                fieldnames = list(records[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

            writer.writerows(records)
            total += len(records)
            offset += PAGE_SIZE
            print(f"  Downloaded {total:,} rows...")

            if len(records) < PAGE_SIZE:
                break

            time.sleep(0.5)

    print(f"\nDone: {total:,} rows saved to {out_path}")
    print("Next step: python scripts/build_311_panel.py")


def main():
    print(__doc__)
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Download via Socrata API")
    args = parser.parse_args()
    if args.auto:
        download_all()


if __name__ == "__main__":
    main()
