"""Download CDC WONDER drug overdose death data by state and year.

CDC WONDER provides underlying cause of death statistics. We need drug and
opioid overdose deaths by state-year for 2010-2022.

Manual download (required — CDC WONDER does not have a public bulk API):
    1. Go to: https://wonder.cdc.gov/ucd-icd10-expanded.html
    2. Group results by: State, Year
    3. Filter cause of death:
         ICD-10 codes X40-X44 (accidental drug poisoning)
         + X60-X64 (intentional self-poisoning)
         + X85 (assault by drugs)
         + Y10-Y14 (undetermined intent)
       This is the standard "drug overdose" definition used in the literature.
    4. For opioid-specific deaths, also filter:
         T40.0-T40.4, T40.6 (opioid-related codes as contributing cause)
    5. Select years: 2010-2022
    6. Export as tab-delimited text
    7. Save to: data/raw/cdc/cdc_overdose_deaths_raw.txt

Notes:
    - Cells with fewer than 10 deaths are suppressed ("Suppressed") by CDC.
      Handle these as missing in build_cdc_panel.py.
    - Population denominators are included in the WONDER export.

After downloading:
    python scripts/build_cdc_panel.py
"""

INSTRUCTIONS = """
CDC WONDER Download Instructions
=================================

1. Visit: https://wonder.cdc.gov/ucd-icd10-expanded.html
   (Use "Underlying Cause of Death, Expanded" for 2018+ or standard for pre-2018)

2. Section 1 — Group Results By:
   State, Year

3. Section 2 — Select years:
   2010 through 2022

4. Section 3 — Select cause of death (ICD-10):
   Drug overdose (all intents):
     X40-X44, X60-X64, X85, Y10-Y14

5. Click Send -> Export Results as Tab Delimited (.txt)
   Save as: data/raw/cdc/cdc_overdose_deaths_raw.txt

6. Repeat for opioid-specific deaths:
   Add T40.0-T40.4, T40.6 as contributing cause filters
   Save as: data/raw/cdc/cdc_opioid_deaths_raw.txt

7. Run: python scripts/build_cdc_panel.py

Expected columns in output (data/processed/cdc_state_year.parquet):
    state, year, overdose_deaths, opioid_deaths, population,
    overdose_deaths_per_100k, opioid_deaths_per_100k
"""

if __name__ == "__main__":
    print(INSTRUCTIONS)
