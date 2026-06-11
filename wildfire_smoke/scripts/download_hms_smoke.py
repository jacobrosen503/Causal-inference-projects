"""Download NOAA HMS (Hazard Mapping System) smoke plume shapefiles.

HMS provides daily smoke plume polygons classified as Light/Medium/Heavy.
We use these to construct the smoke instrument (upwind wildfire smoke
exposure at each school district).

Source: https://www.ospo.noaa.gov/Products/land/hms.html
Direct archive: https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile/

Directory structure on server:
  {BASE_URL}/{year}/{month:02d}/hms_smoke{YYYYMMDD}.zip

Usage:
    python scripts/download_hms_smoke.py
    python scripts/download_hms_smoke.py --years 2015 2016 2017

Output: data/raw/hms_smoke/{year}/  (shapefiles extracted by year)

After downloading:
    python src/exposure/smoke_instrument.py

Note: Files are ~50MB/year compressed. Total for 2010-2019: ~500MB.
"""
from __future__ import annotations

import argparse
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "hms_smoke"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile"


def iter_dates(year: int):
    """Yield every date in the given year."""
    d = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    while d < end:
        yield d
        d += timedelta(days=1)


def download_year(year: int, session) -> int:
    year_dir = RAW_DIR / str(year)

    # Check if already fully downloaded (rough check: at least 300 shapefiles)
    existing_shp = list(year_dir.glob("*.shp")) if year_dir.exists() else []
    if len(existing_shp) >= 300:
        print(f"  [skip] {year} already downloaded ({len(existing_shp)} shapefiles)")
        return len(existing_shp)

    year_dir.mkdir(exist_ok=True)
    ok_count = 0
    fail_count = 0

    for d in iter_dates(year):
        date_str = d.strftime("%Y%m%d")
        shp_file = year_dir / f"hms_smoke{date_str}.shp"
        if shp_file.exists():
            ok_count += 1
            continue

        url = f"{BASE_URL}/{year}/{d.month:02d}/hms_smoke{date_str}.zip"
        dest = year_dir / f"hms_smoke{date_str}.zip"

        try:
            r = session.get(url, stream=True, timeout=60)
            if r.status_code == 404:
                # Some days have no smoke — that's normal
                continue
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            with zipfile.ZipFile(dest, "r") as z:
                z.extractall(year_dir)
            dest.unlink()
            ok_count += 1
            time.sleep(0.1)
        except Exception as e:
            fail_count += 1
            if fail_count <= 5:
                print(f"    [fail] {date_str}: {e}")

    print(f"  {year}: {ok_count} days downloaded ({fail_count} errors)")
    return ok_count


def main():
    try:
        import requests
    except ImportError:
        print("requests not installed: pip install requests")
        return

    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int,
                        default=list(range(2010, 2020)))
    args = parser.parse_args()

    print(f"Downloading HMS smoke plumes for {args.years}")
    session = requests.Session()
    for year in args.years:
        download_year(year, session)

    print("\nNext: python src/exposure/smoke_instrument.py")


if __name__ == "__main__":
    main()
