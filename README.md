# Causal Inference Projects

I'm a data scientist with six years of analytics experience, currently working on the forecasting team at a hotel revenue management company. My day-to-day involves building models on production hospitality data at scale, and I've gotten increasingly interested in moving past predictive modeling toward answering questions about causation.

This repo is where I'm building that out. The projects here apply causal inference methods to real and simulated datasets, working through the full pipeline from naive OLS to quasi-experimental designs. Each project is structured the same way: start with a business question, show why simple correlations fail, then build toward an identification strategy that can actually support a causal claim.

Background: M.S. Data Science (Drexel), B.A. Political Science and Statistics (UT Austin). I work primarily in Python and SQL.

---

## Projects

### cruise_cabin_causal -- Cabin Mix and Revenue (Semi-Synthetic Demo)

> All data are simulated. No real cruise operator or booking records are described.

The causal question mirrors a problem I work on with real hotel data: does expanding product complexity (more room types, more cabin categories) actually drive higher revenue, or do we just observe that larger, more sophisticated operators have both? The raw correlation is strong and almost entirely selection.

This project uses a documented data-generating process with a known ground truth (true beta = 0.06 per category) and works through the full estimation ladder: naive OLS overstates the effect by roughly 3x, two-way fixed effects recovers the true parameter, and an event study using refit timing as quasi-experimental variation validates the design.

Methods: OLS, panel fixed effects, CausalForest DML, Oster bounds, event study

[cruise_cabin_causal/](cruise_cabin_causal/)

---

### airbnb_regulation -- Short-Term Rental Regulation Impact (coming)

When cities restrict short-term rentals, what actually happens to listings, prices, and availability? This project uses public Airbnb data and staggered regulatory shocks across cities (NYC Local Law 18, Florence, London) to estimate treatment effects with modern DiD methods.

Methods: two-period DiD, Callaway-Sant'Anna staggered DiD, synthetic control, event study

---

### wildfire_smoke -- Air Pollution and Student Achievement (coming)

Does wildfire smoke lower test scores? Naive regressions are hopeless here because poor districts have both worse air quality and worse school outcomes. This project uses wind-driven wildfire smoke as an instrument for PM2.5 exposure, complemented by regression discontinuity at EPA air quality thresholds.

Methods: IV/2SLS, RDD, CausalForest DML

Data: EPA AQS, Stanford SEDA, NOAA HMS smoke plumes

---

## Stack

Python, pandas, statsmodels, linearmodels, econml, scikit-learn, matplotlib, seaborn, pyarrow
