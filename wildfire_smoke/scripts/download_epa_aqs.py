"""Download EPA AQS daily PM2.5 monitor data for western US states.

Source: EPA Air Quality System (AQS) API
API docs: https://aqs.epa.gov/aqsweb/documents/data_api.html
Sign up for free API key: https://aqs.epa.gov/data/api/signup?email=YOUR_EMAIL

Usage:
    python scripts/download_epa_aqs.py --email your@email.com --key YOUR_KEY
    python scripts/download_epa_aqs.py --email your@email.com --key YOUR_KEY --years 2015 2016

Output: data/raw/epa_aqs/pm25_daily_{state}_{year}.csv

After downloading:
    python src/ingest/epa_aqs.py  (builds district-year PM2.5 panel)
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "epa_aqs"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Western US state FIPS codes
STATES = {
    "CA": "06", "OR": "41", "WA": "53", "MT": "30",
    "ID": "16", "WY": "56", "CO": "08", "NV": "32",
    "AZ": "04", "NM": "35", "UT": "49",
}

BASE_URL = "https://aqs.epa.gov/data/api"


def download_state_year(state_fips: str, state_abbr: str, year: int, email: str, key: str) -> bool:
    try:
        import requests
    except ImportError:
        print("requests not installed: pip install requests")
        return False

    out = RAW_DIR / f"pm25_daily_{state_abbr}_{year}.csv"
    if out.exists():
        print(f"    [skip] {out.name}")
        return True

    url = (
        f"{BASE_URL}/dailyData/byState"
        f"?email={email}&key={key}"
        f"&param=88101"
        f"&bdate={year}0101&edate={year}1231"
        f"&state={state_fips}"
    )

    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
        if data.get("Header", [{}])[0].get("status") == "No data matched your selection":
            print(f"    [no data] {state_abbr} {year}")
            return True
        rows = data.get("Data", [])
        if not rows:
            return True
        import csv, io
        out.write_text("\n".join([",".join(rows[0].keys())] + [",".join(str(v) for v in r.values()) for r in rows]))
        print(f"    [ok] {out.name}  ({len(rows)} records)")
        return True
    except Exception as e:
        print(f"    [fail] {state_abbr} {year}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="EPA AQS registered email")
    parser.add_argument("--key",   required=True, help="EPA AQS API key")
    parser.add_argument("--years", nargs="+", type=int,
                        default=list(range(2010, 2020)),
                        help="Years to download (default: 2010-2019)")
    args = parser.parse_args()

    total = ok = 0
    for state_abbr, state_fips in STATES.items():
        print(f"\n{state_abbr}")
        for year in args.years:
            total += 1
            if download_state_year(state_fips, state_abbr, year, args.email, args.key):
                ok += 1
            time.sleep(0.5)

    print(f"\nDownloaded {ok}/{total}")
    print("Next: python src/ingest/epa_aqs.py")


if __name__ == "__main__":
    main()
