# Data Dictionary

## `fars_state_year.parquet`

State x year panel of traffic fatalities. Built from NHTSA FARS + Census population.

| Column | Description |
|--------|-------------|
| `state` | State name |
| `state_abbr` | Two-letter abbreviation |
| `fips` | State FIPS code |
| `year` | Calendar year |
| `total_fatalities` | Total fatal crash victims |
| `alcohol_fatalities` | Alcohol-impaired driver fatalities |
| `drug_fatalities` | Drug-impaired driver fatalities |
| `population` | State population (Census estimate) |
| `total_fatalities_per_100k` | Total / population * 100,000 |
| `alcohol_fatalities_per_100k` | Alcohol / population * 100,000 |
| `drug_fatalities_per_100k` | Drug / population * 100,000 |
| `retail_sales_year` | Year retail cannabis sales began (null = never treated) |
| `treated` | True if state ever legalized |
| `post` | True if year >= retail_sales_year |
| `years_since_legalization` | year - retail_sales_year (null for never-treated) |

## `cdc_state_year.parquet`

State x year panel of drug overdose deaths. Built from CDC WONDER.

| Column | Description |
|--------|-------------|
| `state` | State name |
| `year` | Calendar year |
| `overdose_deaths` | All-cause drug overdose deaths (ICD-10: X40-X44, X60-X64, X85, Y10-Y14) |
| `opioid_deaths` | Opioid-specific overdose deaths |
| `population` | State population |
| `overdose_deaths_per_100k` | Per 100k population rate |
| `opioid_deaths_per_100k` | Per 100k population rate |
| `retail_sales_year` | Year retail cannabis sales began |
| `treated` | True if state ever legalized |
| `post` | True if year >= retail_sales_year |

## `nyc_311_zip_month.parquet`

NYC zip code x month panel of 311 complaint counts.

| Column | Description |
|--------|-------------|
| `zip` | 5-digit zip code |
| `month` | Month start date |
| `total_complaints` | Total 311 complaints of all tracked types |
| `log_total_complaints` | log(1 + total_complaints) |
| `n_drug_activity` | Drug Activity complaints |
| `n_noise_residential` | Noise - Residential complaints |
| `n_noise_street_sidewalk` | Noise - Street/Sidewalk complaints |
| `n_illegal_parking` | Illegal Parking complaints |
| `n_disorderly_youth` | Disorderly Youth complaints |
| `has_dispensary` | True if zip ever gets a dispensary in study window |
| `first_open_month` | Month of first dispensary opening in zip |
| `post_open` | True if month >= first_open_month |
| `rel_month` | Months since first dispensary opening (null for never-treated zips) |

## `nyc_dispensary_events.parquet`

Licensed adult-use retail dispensaries in NYC with opening dates.

| Column | Description |
|--------|-------------|
| `zip` | 5-digit zip code |
| `open_month` | Month of license issue (proxy for opening) |
| `latitude`, `longitude` | Coordinates (from NY Open Data) |

## `data/codebooks/state_legalization_dates.csv`

Manually compiled from public records. Use `retail_sales_year` (not `law_passed_year`) as the treatment date.

| Column | Description |
|--------|-------------|
| `state` | Full state name |
| `state_abbr` | Two-letter code |
| `fips` | FIPS numeric code |
| `law_passed_year` | Year ballot measure or legislation passed |
| `retail_sales_year` | Year retail sales to adults legally began |
| `law_name` | Name of legislation or ballot measure |
| `notes` | Context and caveats |
