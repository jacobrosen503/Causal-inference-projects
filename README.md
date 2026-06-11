# Causal Inference Projects

I'm a data scientist with six years of analytics experience, currently working on the forecasting team at a hotel revenue management company. My day-to-day involves building models on production hospitality data at scale, and I've gotten increasingly interested in moving past predictive modeling toward answering questions about causation.

This repo is where I'm building that out. Each project applies causal inference methods to a real public dataset, working through the full pipeline from naive correlation to a defensible identification strategy. The structure is the same across projects: start with a business or policy question, show why simple regressions fail, then design around the confounding.

Background: M.S. Data Science (Drexel), B.A. Political Science and Statistics (UT Austin). I work primarily in Python and SQL.

---

## Projects

### `returns_to_schooling/` -- OLS, Confounding, and the Frisch-Waugh-Lovell Theorem

What is the causal return to an additional year of schooling — and what is OLS *actually doing* when it removes confounding bias? Using Wooldridge's NLS-Y `wage2` dataset (935 young men, IQ scores included), this project demonstrates every concept from Facure Ch. 4 on real data: the OVB formula verified to floating-point precision, the FWL three-step decomposition with coefficient and SE identity confirmed, control selection bias-variance tradeoffs, and regression as a variance-weighted average of within-group effects.

The differentiating angle: most demos show that adding controls changes an estimate. This project shows *why* — by orthogonalizing the treatment on real data and watching the IQ quartile offsets physically disappear.

Methods: OLS, Omitted Variable Bias formula, Frisch-Waugh-Lovell decomposition, log transformation, Mincer earnings equation, fixed effects via de-meaning, variance-weighted averaging

Data: Wooldridge `wage2` via `pip install wooldridge` (no download required)

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

### `wildfire_smoke/` -- Wildfire Smoke and Student Achievement (Showpiece)

Does air pollution hurt student test scores? Naive regressions are nearly useless here because poor districts have both worse air quality and worse schools. This project uses wind-driven wildfire smoke as an instrument for PM2.5 exposure, complemented by RDD at EPA AQI thresholds and a Camp Fire event study.

The most complex data pipeline of the three: EPA AQS monitors, NOAA HMS smoke plumes, Stanford SEDA test scores, and Census ACS demographics, merged via spatial joins at the school district level.

Methods: IV/2SLS, RDD, CausalForest DML, event study (Camp Fire 2018)

Data: EPA AQS (API), NOAA HMS shapefiles, Stanford SEDA (registration required), Census ACS

[wildfire_smoke/](wildfire_smoke/)

---

## Stack

```
pandas, numpy, pyarrow, statsmodels, linearmodels, econml, scikit-learn,
geopandas, shapely, matplotlib, seaborn
```

---

"Causal inference for hospitality and public policy -- DiD, IV, RDD, DML."
