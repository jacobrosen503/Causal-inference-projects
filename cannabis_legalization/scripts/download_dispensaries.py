"""Download NY State licensed cannabis dispensary locations and opening dates.

Source: NY State Office of Cannabis Management
URL: https://cannabis.ny.gov/dispensary-location-verification

The OCM publishes a list of licensed adult-use retail dispensaries with:
  - Business name
  - Address (street, city, zip, county)
  - License type
  - License status
  - Issue date (proxy for opening date)

This data is also available on NY Open Data:
  https://data.ny.gov/Economic-Development/Active-Licensee-Map/ems6-2xvk

Download instructions:
    1. Visit: https://data.ny.gov/Economic-Development/Active-Licensee-Map/ems6-2xvk
    2. Filter: License Type = "Adult-Use Retail Dispensary" (AURD)
    3. Export as CSV
    4. Save to: data/raw/dispensaries/ny_cannabis_licenses.csv

Or run: python scripts/download_dispensaries.py --auto

After downloading:
    python scripts/build_dispensary_events.py

Expected output: data/processed/nyc_dispensary_events.parquet
    Columns: license_id, business_name, address, zip, borough, latitude, longitude,
             license_issue_date, first_full_month
"""
from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "dispensaries"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_ny_open_data():
    try:
        import requests
    except ImportError:
        print("requests not installed: pip install requests")
        return

    # NY Open Data Socrata API for cannabis licenses
    url = (
        "https://data.ny.gov/resource/ems6-2xvk.json"
        "?$limit=5000"
        "&$where=license_type_name='Adult-Use Retail Dispensary' AND license_status='Active'"
        "&$select=lic_num,dba_name,premise_address_1,premise_city,premise_zip,"
        "county,license_type_name,license_status,lic_effective_date,longitude,latitude"
    )

    print(f"Querying NY Open Data...")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        records = r.json()
        if not records:
            print("No records returned — check URL or filter")
            return

        import csv
        out = RAW_DIR / "ny_cannabis_licenses.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

        print(f"Downloaded {len(records)} licenses -> {out}")
        print("Next step: python scripts/build_dispensary_events.py")
    except Exception as e:
        print(f"Download failed: {e}")
        print("Try manual download from https://data.ny.gov/Economic-Development/Active-Licensee-Map/ems6-2xvk")


def main():
    print(__doc__)
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()
    if args.auto:
        download_ny_open_data()


if __name__ == "__main__":
    main()
