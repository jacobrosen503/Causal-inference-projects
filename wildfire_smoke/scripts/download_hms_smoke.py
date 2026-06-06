"""Download NOAA HMS (Hazard Mapping System) smoke plume shapefiles.

HMS provides daily smoke plume polygons classified as Light/Medium/Heavy.
We use these to construct the smoke instrument (upwind wildfire smoke
exposure at each school district).

Source: https://www.ospo.noaa.gov/Products/land/hms.html
Direct archive: https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile/

Usage:
    python scripts/download_hms_smoke.py
    python scripts/download_hms_smoke.py --years 2015 2016 2017

Output: data/raw/hms_smoke/hms_smoke_{year}/  (shapefiles by year)

After downloading:
    python src/exposure/smoke_instrument.py

Note: Files are ~50MB/year compressed. Total for 2010-2019: ~500MB.
"""
from __future__ import annotations

import argparse
import time
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "hms_smoke"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile"


def download_year(year: int) -> bool:
    try:
        import requests
    except ImportError:
        print("requests not installed: pip install requests")
        return False

    year_dir = RAW_DIR / str(year)
    if year_dir.exists() and any(year_dir.glob("*.shp")):
        print(f"  [skip] {year} already downloaded")
        return True

    year_dir.mkdir(exist_ok=True)
    ok_count = 0

    # HMS shapefiles are organized by year/month
    for month in range(1, 13):
        url = f"{BASE_URL}/{year}/{year}{month:02d}_smoke.zip"
        dest = year_dir / f"{year}{month:02d}_smoke.zip"

        try:
            r = requests.get(url, stream=True, timeout=60)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            with zipfile.ZipFile(dest, "r") as z:
                z.extractall(year_dir)
            dest.unlink()
            ok_count += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"    [fail] {year}-{month:02d}: {e}")

    print(f"  {year}: {ok_count}/12 months downloaded")
    return ok_count > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int,
                        default=list(range(2010, 2020)))
    args = parser.parse_args()

    print(f"Downloading HMS smoke plumes for {args.years}")
    for year in args.years:
        download_year(year)

    print("\nNext: python src/exposure/smoke_instrument.py")


if __name__ == "__main__":
    main()
