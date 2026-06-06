# Data Dictionary

## `analysis_panel.parquet` (primary analysis file)

District x year panel merging all data sources.

| Column | Source | Description |
|--------|--------|-------------|
| `leaid` | SEDA | NCES Local Education Agency ID |
| `year` | All | School year end year (e.g. 2015 = 2014-15) |
| `state` | SEDA | State abbreviation |
| `test_score_mean` | SEDA | Mean standardized test score (math, grades 3-8, pooled) |
| `test_score_se` | SEDA | Standard error of mean score estimate |
| `pm25_annual_mean` | EPA AQS | Annual mean PM2.5 (μg/m³), IDW-averaged from monitors within 100km |
| `log_pm25` | Derived | log(pm25_annual_mean) |
| `n_monitors` | EPA AQS | Number of monitors contributing to IDW average |
| `smoke_days` | NOAA HMS | Days with Medium+ smoke plume over district centroid |
| `smoke_days_heavy` | NOAA HMS | Days with Heavy smoke plume only |
| `smoke_days_pct` | Derived | smoke_days / 365 |
| `poverty_rate` | ACS | District poverty rate (5-year estimate) |
| `median_income` | ACS | Median household income |
| `urban_pct` | ACS | Share of population in urban areas |
| `camp_fire_affected` | Derived | True for CA districts in 2018 (proxy for Camp Fire exposure) |

## `pm25_district_year.parquet`

| Column | Description |
|--------|-------------|
| `leaid` | District LEAID |
| `year` | Year |
| `pm25_annual_mean` | IDW-averaged annual PM2.5 (μg/m³) |
| `n_monitors` | Monitors contributing to average |

## `smoke_instrument_district_year.parquet`

| Column | Description |
|--------|-------------|
| `leaid` | District LEAID |
| `year` | Year |
| `smoke_days` | Days with HMS Medium/Heavy smoke plume over centroid |
| `smoke_days_heavy` | Days with HMS Heavy smoke only |
| `smoke_days_pct` | Fraction of year with smoke exposure |

## `seda_district_year.parquet`

| Column | Description |
|--------|-------------|
| `leaid` | District LEAID |
| `year` | School year end year |
| `state` | State abbreviation |
| `test_score_mean` | Mean score (standardized, math, grades 3-8 pooled) |
| `test_score_se` | Standard error |
| `n_grades` | Number of grade-subject cells averaged |

## `data/crosswalks/district_centroids.csv`

| Column | Description |
|--------|-------------|
| `leaid` | District LEAID |
| `lat` | Centroid latitude |
| `lon` | Centroid longitude |
| `state` | State abbreviation |
| `name` | District name |

## Data sources

| Source | URL | Access |
|--------|-----|--------|
| EPA AQS | https://aqs.epa.gov/data/api | Free API key |
| NOAA HMS | https://www.ospo.noaa.gov/Products/land/hms.html | Public download |
| Stanford SEDA | https://edopportunity.org | Free registration |
| Census ACS | https://data.census.gov | Public API |

## Key variables for IV analysis

- **Outcome (Y):** `test_score_mean` — standardized, so effects are in SD units
- **Treatment (T):** `pm25_annual_mean` — endogenous, instrumented by smoke
- **Instrument (Z):** `smoke_days` — days with wildfire smoke plume
- **Controls (X):** `poverty_rate`, `urban_pct`, `median_income`, district FE, year FE
