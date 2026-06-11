# Causal Inference Projects

I'm a data scientist with six years of analytics experience, currently working on the forecasting team at a hotel revenue management company. My day-to-day involves building models on production hospitality data at scale, and I've gotten increasingly interested in moving past predictive modeling toward answering questions about causation.

This repo is where I'm building that out. Each project applies causal inference methods to a public dataset, working through the full pipeline from naive correlation to a defensible identification strategy. The structure is the same across projects: start with a business or policy question, show why simple regressions fail, then design around the confounding.

Background: M.S. Data Science (Drexel), B.A. Political Science and Statistics (UT Austin). I work primarily in Python and SQL.

---

## Projects

### `returns_to_schooling/` -- The Mechanics of OLS (Foundations)

What is regression *actually doing* when it "controls for" a confounder? This project answers that on real data — Wooldridge's NLS wage panel, which uniquely includes IQ scores — by verifying the theorems behind OLS numerically rather than just citing them. The omitted-variable-bias formula reproduces the ability-bias gap to ten decimal places; the Frisch-Waugh-Lovell theorem shows that "controlling for IQ" means physically orthogonalizing schooling against it (and that the third-stage standard error is wrong until you correct the degrees of freedom). Fixed effects are then derived as de-meaning, and OLS as a variance-weighted average — the property that makes staggered-timing TWFE fail. This is the foundation the other four projects build on.

Methods: OLS, omitted variable bias, Frisch-Waugh-Lovell orthogonalization, fixed effects as de-meaning, variance-weighted averaging (→ Goodman-Bacon)

Data: Wooldridge NLS `wage2` (via the `wooldridge` package — no download, no registration)

[returns_to_schooling/](returns_to_schooling/)

---

### `cruise_cabin_causal/` -- Cabin Mix and Revenue (Semi-Synthetic Demo)

> All data are simulated. No real cruise operator or booking records are described.

Does expanding inventory complexity causally increase revenue, or do we just observe that larger operators have both? The raw correlation is 0.88 and almost entirely selection. This project uses a documented data-generating process with known ground truth (true beta = 0.06 per category) and works through the full estimation ladder.

Methods: OLS, panel fixed effects, CausalForest DML, Oster bounds, event study

[cruise_cabin_causal/](cruise_cabin_causal/)

---

### `cannabis_legalization/` -- Cannabis Legalization and Traffic Fatalities

Does recreational cannabis legalization reduce traffic fatalities? Using NHTSA FARS data and 15+ staggered state legalization cohorts (2014-2022), this project implements Callaway-Sant'Anna staggered DiD and compares it to naive TWFE to show where the bias comes from.

A second component uses NYC Open Data and NY cannabis license records to estimate the effect of dispensary openings on neighborhood 311 complaint patterns -- a within-city event study design.

Methods: TWFE DiD, Callaway-Sant'Anna staggered DiD, event study, within-city dispensary event study

Data: NHTSA FARS (committed), Census population (committed), NYC 311, NY cannabis licenses

[cannabis_legalization/](cannabis_legalization/)

---

### `airbnb_regulation/` -- Airbnb Regulation Impact Study

Does restricting short-term rentals reduce listings — and what's the effect on prices and availability? NYC's Local Law 18 (September 2023) cut active Airbnb listings by ~81% within weeks of enforcement. This project uses that abrupt shock, plus a concurrent Florence historic-centre ban, to estimate treatment effects with staggered DiD and synthetic control.

> Note: Inside Airbnb removed historical snapshots from public access in 2025. The panel uses simulated data replicating the documented LL18 impact; the causal design is unchanged.

Methods: Two-period DiD, event study, Callaway-Sant'Anna staggered DiD, synthetic control (Abadie weights), placebo tests

[airbnb_regulation/](airbnb_regulation/)

---

### `wildfire_smoke/` -- Wildfire Smoke and Student Achievement (Showpiece)

Does air pollution hurt student test scores? Naive regressions are nearly useless here because poor districts have both worse air quality and worse schools. This project uses wind-driven wildfire smoke as an instrument for PM2.5 exposure, complemented by RDD at EPA AQI thresholds and a Camp Fire event study. The instrument's first stage is strong and clean; the writeup is candid that the second stage does *not* identify a credible effect at annual/district resolution — a deliberate exercise in showing where an IV earns its keep and where it doesn't.

The most complex data pipeline in the repo: EPA AQS monitors, NOAA HMS smoke plumes, Stanford SEDA test scores, and Census ACS demographics, merged via spatial joins at the school district level.

Methods: IV/2SLS, RDD, CausalForest DML, event study (Camp Fire 2018)

Data: EPA AQS (API), NOAA HMS shapefiles, Stanford SEDA (registration required), Census ACS

[wildfire_smoke/](wildfire_smoke/)

---

## Stack

```
pandas, numpy, pyarrow, statsmodels, linearmodels, econml, scikit-learn,
geopandas, shapely, matplotlib, seaborn, wooldridge
```

---

"Causal inference for hospitality and public policy -- DiD, IV, RDD, DML."
