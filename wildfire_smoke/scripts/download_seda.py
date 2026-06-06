"""Download Stanford SEDA district-level test score data.

SEDA (Stanford Education Data Archive) provides standardized test score
estimates for US school districts from 2009-2019.

Download: https://edopportunity.org/get-the-data/seda-archive-downloads/
  -> SEDA Version 4.1 (or latest)
  -> "District-level Estimates" (main file)
  -> Download the "Long" format CSV

Save to: data/raw/seda/seda_district_long.csv

Key columns we use:
  - sedacounty: county FIPS
  - sedalea: district LEAID
  - year: school year end year (e.g. 2015 = 2014-15)
  - subject: math, rla (reading/language arts)
  - grade: gr3-gr8
  - mn_avg_ol: mean score (our primary outcome)
  - mn_avg_ol_se: standard error

After downloading:
    python src/ingest/seda.py

Note: SEDA data requires registration at https://edopportunity.org/
Registration is free and instant.
"""

INSTRUCTIONS = """
SEDA Download Instructions
===========================

1. Go to: https://edopportunity.org/get-the-data/seda-archive-downloads/

2. Find SEDA Version 4.1 (or most recent available)

3. Download: "District Achievement Data (Long Format)"
   File will be named something like: seda_county_long_gcs_v41.csv
   or: SEDA_district_poolsub_gcs_4.1.0.csv

4. Save to: data/raw/seda/seda_district_long.csv

5. Also download the "Geodata" file which has district lat/lon:
   Save to: data/raw/seda/seda_geodata.csv

6. Run: python src/ingest/seda.py

The data is free for research use. Registration required at edopportunity.org.
"""

if __name__ == "__main__":
    print(INSTRUCTIONS)
