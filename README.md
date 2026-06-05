# Causal Inference Projects

Causal inference portfolio — DiD, synthetic control, IV, RDD, DML.

Each subfolder is a standalone project with its own data pipeline, numbered notebooks, and methodology write-up.

---

## Projects

### `cruise_cabin_causal/` — Cruise Cabin Mix & Revenue (Semi-Synthetic Demo)

> Public methods reference. All data are simulated.

The same causal structure as my private hotel inventory work: does expanding product complexity (cabin categories / room types) causally increase revenue per berth, or is the association driven by operator scale confounding?

**Methods:** Naive OLS → Panel FE → CausalForest DML → Oster bounds → Event study  
**Known ground truth:** β = 0.06 per category (simulated DGP)  
**Key finding:** Raw cross-sectional correlation ≈ 0.88; TWFE recovers true β ≈ 0.06  

→ [`cruise_cabin_causal/`](cruise_cabin_causal/)

---

### `airbnb_regulation/` — STR Regulation Impact *(coming)*

Effect of short-term rental regulations (NYC Local Law 18, Florence, London) on listings, prices, and availability.

**Methods:** Two-period DiD, Callaway–Sant'Anna staggered DiD, synthetic control, event study  
**Data:** Inside Airbnb public snapshots  

---

### `wildfire_smoke/` — Wildfire Smoke & Student Achievement *(coming)*

Effect of PM2.5 exposure on standardized test scores using wind-driven wildfire smoke as an instrument.

**Methods:** IV/2SLS, RDD at EPA AQI thresholds, CausalForest DML  
**Data:** EPA AQS, Stanford SEDA, NOAA HMS smoke plumes  

---

## Stack

```
pandas · numpy · pyarrow · statsmodels · linearmodels · econml · scikit-learn · matplotlib · seaborn
```

## Profile

> "Causal inference for hospitality & public policy — DiD, IV, RDD, DML."
