"""Download EPA AQS annual summary PM2.5 data for western US states.

Uses the EPA AQS API "annualData" endpoint which returns one record
per monitor per year — already aggregated. Much smaller than daily files.

Total download: ~20-30MB for all 11 states × 10 years.
Compare to daily files: ~400MB+

Usage:
    python scripts/download_epa_aqs.py --email YOUR@EMAIL --key bluekit86
    python scripts/download_epa_aqs.py --email YOUR@EMAIL --key bluekit86 --years 2015 2016

Output: data/raw/epa_aqs/pm25_annual_{state}_{year}.csv

After downloading:
    python src/ingest/epa_aqs.py
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "epa_aqs"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Western US: state FIPS codes
STATES = {
    "CA": "06", "OR": "41", "WA": "53", "MT": "30",
    "ID": "16", "WY": "56", "CO": "08", "NV": "32",
    "AZ": "04", "NM": "35", "UT": "49",
}

PM25_PARAM = "88101"   # PM2.5 FRM/FEM Mass
BASE_URL   = "https://aqs.epa.gov/data/api"


def download_annual(state_abbr: str, state_fips: str, year: int,
                    email: str, key: str) -> bool:
    import requests, json

    out = RAW_DIR / f"pm25_annual_{state_abbr}_{year}.csv"
    if out.exists():
        print(f"    [skip] {out.name}")
        return True

    url = (
        f"{BASE_URL}/annualData/byState"
        f"?email={email}&key={key}"
        f"&param={PM25_PARAM}"
        f"&bdate={year}0101&edate={year}1231"
        f"&state={state_fips}"
    )

    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()

        header = data.get("Header", [{}])[0]
        if header.get("status") == "No data matched your selection":
            print(f"    [no data] {state_abbr} {year}")
            out.write_text("")   # empty file so we skip next time
            return True

        rows = data.get("Data", [])
        if not rows:
            print(f"    [empty] {state_abbr} {year}")
            return True

        import csv, io
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        out.write_text(buf.getvalue())

        size_kb = out.stat().st_size / 1024
        print(f"    [ok] {out.name}  ({len(rows)} monitors, {size_kb:.0f} KB)")
        return True

    except Exception as e:
        print(f"    [fail] {state_abbr} {year}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--key",   required=True)
    parser.add_argument("--years", nargs="+", type=int,
                        default=list(range(2010, 2020)))
    parser.add_argument("--states", nargs="+",
                        default=list(STATES.keys()),
                        choices=list(STATES.keys()))
    args = parser.parse_args()

    total = ok = 0
    for state_abbr in args.states:
        state_fips = STATES[state_abbr]
        print(f"\n{state_abbr}")
        for year in args.years:
            total += 1
            if download_annual(state_abbr, state_fips, year,
                               args.email, args.key):
                ok += 1
            time.sleep(0.5)   # be polite to EPA API

    print(f"\nDownloaded {ok}/{total} state-year files")
    print(f"Output directory: {RAW_DIR}")
    print(f"Next step: python src/ingest/epa_aqs.py")


if __name__ == "__main__":
    main()
