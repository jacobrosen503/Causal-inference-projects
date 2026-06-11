# Cannabis Legalization Causal Study

Two linked causal designs studying the effects of recreational cannabis policy using public data.

**Part 1 — State-level staggered DiD:** Does recreational cannabis legalization reduce traffic fatalities and opioid overdose deaths? Using NHTSA FARS and CDC WONDER data across 15+ staggered legalization cohorts from Colorado and Washington (2014) through Maryland and Missouri (2023).

**Part 2 — Within-NYC event study:** Do cannabis dispensary openings affect neighborhood 311 complaint patterns? Using NYC Open Data and NY Office of Cannabis Management license records.

---

## Causal questions

**Part 1:** What is the ATT of recreational cannabis legalization on traffic fatality rates and drug overdose mortality, using staggered state-level legalization dates as treatment?

**Part 2:** Does a new cannabis dispensary opening in a zip code change the volume or composition of 311 complaints in the months around opening?

---

## Data

**Download and build (run in Cursor):**

```bash
# Part 1 — State-level
python scripts/download_fars.py       # NHTSA FARS instructions + optional auto-download
python scripts/download_cdc.py        # CDC WONDER instructions (manual query required)
python src/build_fars_panel.py        # builds data/processed/fars_state_year.parquet
python src/build_cdc_panel.py         # builds data/processed/cdc_state_year.parquet

# Part 2 — NYC
python scripts/download_311.py --auto            # ~1M rows, ~15 min
python scripts/download_dispensaries.py --auto   # NY cannabis license data
python src/build_311_panel.py                    # builds nyc_311_zip_month.parquet
```

**Already committed (no download needed):**

```
data/codebooks/state_legalization_dates.csv   # retail sales start years by state
data/processed/fars_state_year.parquet        # NHTSA FARS 2010-2022 (real data)
```

**Note on data availability:**
- NHTSA FARS (traffic fatalities): real data, committed to repo
- CDC WONDER (opioid overdoses, notebook 09): real data, 2010–2017, 51 states. Downloaded from CDC WONDER "Underlying Cause of Death" (drug overdose ICD codes). Committed to repo.
- NYC 311 + dispensary events (notebook 07): real data. 4.6M 311 service requests (2020–2025, filtered to cannabis-relevant complaint types) from NYC Open Data Socrata API; 51 NYC dispensary opening dates from NY Office of Cannabis Management retail license records. Panel covers Jan 2022–Jun 2025 (235 zip codes × 42 months).

---

## Notebooks

| Notebook | Design | Purpose |
|----------|--------|---------|
| `00_data_audit` | Both | Load panels, check structure, verify treatment coding |
| `02_descriptive` | State | Pre-legalization fatality trends by treatment status |
| `03_naive_ols` | State | Biased baseline — why simple comparisons fail |
| `04_twfe_did` | State | TWFE DiD — standard estimator + its limitations |
| `05_callaway_santanna` | State | C-S staggered DiD — preferred estimator |
| `06_event_study_legalization` | State | Dynamic effects around retail sales start |
| `07_nyc_dispensary_event_study` | NYC | 311 complaints around dispensary opening dates |
| `08_heterogeneity` | State | Early vs late adopters; alcohol vs drug fatalities |
| `09_opioid_overdose` | State | Substitution hypothesis — CDC WONDER overdose data |
| `99_robustness` | State | Anticipation, control group sensitivity, exclusions |

---

## Identification

See [METHODOLOGY.md](METHODOLOGY.md) for the full write-up.

**State-level (Part 1):**
Retail cannabis legalization dates vary across states for reasons largely unrelated to short-term trends in traffic safety. The staggered timing (2014-2023) allows Callaway-Sant'Anna estimation with cohort-specific ATTs, avoiding the TWFE bias that arises when treatment effects are heterogeneous across cohorts.

**Within-NYC (Part 2):**
Dispensary opening dates are driven by NY State licensing timelines, not by local 311 complaint patterns. We use event study leads and lags around opening dates to test for pre-trends and estimate dynamic effects.

---

## Treatment codebook

State recreational cannabis retail sales start years are in `data/codebooks/state_legalization_dates.csv`, compiled from public sources. Use `retail_sales_year` as the treatment year (when retail purchases became legal), not `law_passed_year` (when voters approved).

---

## Stack

```
pandas, numpy, pyarrow, statsmodels, linearmodels, econml, matplotlib, seaborn
```

---

## Related

Part of a five-project causal inference portfolio. See the [repo root](../) for the full index.
