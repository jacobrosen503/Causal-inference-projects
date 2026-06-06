# Wildfire Smoke & Student Achievement

Does air pollution hurt student test scores? Naive regressions are nearly useless here — poor districts have both worse air quality and worse schools. This project uses wind-driven wildfire smoke as an instrument for PM2.5 exposure, complemented by regression discontinuity at EPA AQI thresholds and a Camp Fire event study.

This is the technical showpiece of a three-project causal inference portfolio. It combines the most complex data pipeline (EPA AQS, NOAA HMS, Stanford SEDA, Census ACS) with the most demanding identification strategy (IV/2SLS).

---

## Causal question

What is the causal effect of PM2.5 air pollution on standardized test score performance in western US school districts?

| Estimand | Method |
|----------|--------|
| LATE (PM2.5 effect via smoke channel) | IV/2SLS — smoke days instruments PM2.5 |
| Reduced form | Smoke days -> test scores directly |
| Local ATE at AQI = 100 | RDD at EPA threshold |
| CATE by income/urbanicity | CausalForest DML |
| Dynamic effect of extreme smoke | Event study: Camp Fire 2018 |

---

## Data pipeline

```
EPA AQS API          -> PM2.5 daily monitor readings   (treatment)
NOAA HMS shapefiles  -> Smoke plume days per district  (instrument)
Stanford SEDA        -> District test scores 2010-2019 (outcome)
Census ACS           -> District demographics          (controls)
```

**Download and build:**

```bash
# 1. EPA AQS (sign up for free key at aqs.epa.gov/data/api/signup)
python scripts/download_epa_aqs.py --email YOUR@EMAIL --key YOUR_KEY

# 2. NOAA HMS smoke plumes (~500MB for 2010-2019)
python scripts/download_hms_smoke.py

# 3. Stanford SEDA (manual registration at edopportunity.org, then download)
python scripts/download_seda.py   # prints instructions

# 4. Build crosswalks (district centroids)
python src/merge/build_crosswalks.py

# 5. Build all processed panels
python src/ingest/epa_aqs.py
python src/ingest/seda.py
python src/exposure/smoke_instrument.py
python src/merge/build_panel.py
```

---

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `00_data_audit` | Verify panel completeness, describe distributions |
| `01_smoke_exposure_pipeline` | Document instrument construction, validate |
| `02_merge_panel` | Descriptives, raw correlation, DAG |
| `03_ols_biased_baseline` | Naive OLS — show confounding direction |
| `04_iv_first_stage` | Smoke -> PM2.5 (relevance check, F-stat) |
| `05_iv_2sls_main` | Main 2SLS estimate + reduced form |
| `06_iv_diagnostics` | Hausman test, alternative instruments, robustness |
| `07_rdd_aqi100` | RDD at AQI=100 — complementary design |
| `08_dml_heterogeneity` | CausalForest: CATE by poverty, urbanicity |
| `09_event_study_camp_fire` | Camp Fire 2018 — dynamic DiD |
| `99_robustness` | Drop 2018, drop CA, alternative instruments |

---

## Identification

See [METHODOLOGY.md](METHODOLOGY.md) for the full write-up.

**Core IV logic:** Wildfire smoke blowing into a school district increases PM2.5 but is driven by upwind fire conditions, not local economic activity. Smoke days is a valid instrument if:
1. Relevance: smoke predicts PM2.5 at monitors near affected districts (test: first-stage F > 10)
2. Exclusion: smoke affects test scores only through air quality — not through evacuations, school closures, or other channels (discuss and test)

**RDD:** Schools in counties that just exceeded AQI = 100 on testing days vs those that just missed — a regression discontinuity on an institutional threshold. Complementary to IV because it uses a completely different source of variation.

---

## Stack

```
pandas, numpy, pyarrow, geopandas, shapely, statsmodels, linearmodels, econml, matplotlib, seaborn
```

---

## Related

Part of a three-project causal inference portfolio. See the [repo root](../) for the full index.
