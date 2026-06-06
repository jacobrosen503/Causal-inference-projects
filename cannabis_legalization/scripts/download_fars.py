"""Download NHTSA FARS (Fatality Analysis Reporting System) state-year data.

FARS provides annual counts of traffic fatalities by state going back to 1975.
We need state-level annual files for 2010-2022.

Manual download (recommended for first-time setup):
    1. Go to: https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars
    2. Click "FARS Data" -> "Annual File"
    3. Download the SAS or CSV versions for each year 2010-2022
    4. The key file in each year's ZIP is: ACCIDENT.csv (one row per fatal crash)

Alternatively, NHTSA provides a query tool at:
    https://cdan.dot.gov/query

Recommended query:
    - Variables: State, Year, Total Fatalities, Alcohol Impaired, Drug Impaired
    - Years: 2010-2022
    - Group by: State x Year
    - Export as CSV -> save to data/raw/fars/

After downloading, run:
    python scripts/build_fars_panel.py

Expected output: data/processed/fars_state_year.parquet
    Columns: state_fips, state, year, total_fatalities, alcohol_fatalities,
             drug_fatalities, population, fatalities_per_100k, etc.

Usage:
    python scripts/download_fars.py          # prints download instructions
    python scripts/download_fars.py --auto   # attempts automated download via NHTSA API
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "fars"
RAW_DIR.mkdir(parents=True, exist_ok=True)


INSTRUCTIONS = """
FARS Data Download Instructions
================================

Option A — NHTSA Query Tool (easiest, pre-aggregated)
------------------------------------------------------
1. Visit: https://cdan.dot.gov/query
2. Select: Crash-level data
3. Filter: Years 2010-2022
4. Group by: State, Year
5. Include: Total fatalities, alcohol-impaired fatalities, drug-impaired fatalities
6. Export as CSV
7. Save to: data/raw/fars/fars_state_year_raw.csv

Option B — Annual ZIP files (raw crash-level)
---------------------------------------------
1. Visit: https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars
2. Under "FARS Data" -> "Annual File", download ZIP for each year 2010-2022
3. Extract ACCIDENT.CSV from each ZIP
4. Save to: data/raw/fars/accident_{year}.csv
5. Run: python scripts/build_fars_panel.py --source accident_files

Option C — NHTSA Open Data API (automated below)
-------------------------------------------------
Run: python scripts/download_fars.py --auto

Population data (needed for per-100k rates)
-------------------------------------------
Download Census state population estimates 2010-2022:
    https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html
Save to: data/raw/census/state_population_2010_2022.csv

After all files are downloaded:
    python scripts/build_fars_panel.py
"""


def try_auto_download():
    """Attempt to download pre-aggregated FARS data via NHTSA's open data API."""
    try:
        import requests
    except ImportError:
        print("requests not installed. Run: pip install requests")
        return False

    # NHTSA does expose some data via Socrata at data.transportation.gov
    # State-year fatality counts
    url = (
        "https://data.transportation.gov/resource/pb7k-p4f4.json"
        "?$limit=50000"
        "&$where=year between 2010 and 2022"
        "&$select=state_name,year,fatalities,drunk_driving_fatalities"
    )
    print(f"Trying: {url}")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data:
            import json
            out = RAW_DIR / "fars_api_raw.json"
            with open(out, "w") as f:
                json.dump(data, f)
            print(f"Downloaded {len(data)} records -> {out}")
            return True
        else:
            print("API returned empty response.")
            return False
    except Exception as e:
        print(f"Auto-download failed: {e}")
        print("Use manual Option A or B above.")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Attempt automated API download")
    args = parser.parse_args()

    print(INSTRUCTIONS)
    print(f"Target directory: {RAW_DIR}\n")

    if args.auto:
        print("Attempting automated download...")
        success = try_auto_download()
        if success:
            print("\nNext step: python scripts/build_fars_panel.py")
    else:
        print("Run with --auto to attempt automated download, or follow manual steps above.")


if __name__ == "__main__":
    main()
