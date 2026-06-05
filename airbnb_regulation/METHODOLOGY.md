# Methodology

## Research Question

What is the causal effect of short-term rental regulation on Airbnb market outcomes (listing counts, prices, availability, room-type composition)?

---

## Target Trial Emulation

| Component | Definition |
|-----------|-----------|
| Eligibility | All active Airbnb listings in study cities during the panel window (2021-2024) |
| Intervention | City adopts a binding STR registration or permit requirement |
| Comparator | Cities without equivalent regulation in the same window |
| Time zero | Month of regulatory enforcement (not announcement) |
| Outcomes | log_listings, mean_price_usd, availability_rate, entire_home_share |
| Effect measure | ATT — average effect on listing market in treated cities |

---

## Identification Conditions

### 1. Parallel Trends

Pre-regulation trends in outcomes must be similar between treated and control cities, conditional on city and time fixed effects. We test this with pre-period event study coefficients. NYC's tourist market is distinct from European cities — this is the weakest assumption and the most important one to scrutinize.

Mitigants: synthetic control (which reweights control cities to match NYC's pre-period trajectory); multiple control cities; visual inspection of pre-trends across all four outcomes.

### 2. No Anticipation

Outcomes should not respond to the regulation before enforcement date. NYC LL18 was announced and debated months before September 2023 — some hosts may have de-listed in anticipation. We handle this by:
- Testing pre-trend coefficients in the event study
- Shifting the effective treatment date earlier as a robustness check
- Discussing the interpretation if pre-period coefficients are non-zero

### 3. Positivity

Both treated and control cities should have observations in all relevant time periods. The panel is unbalanced across cities (Inside Airbnb scrapes cities at different frequencies), so we interpolate or restrict to common windows where needed.

### 4. SUTVA

We assume regulation in NYC does not affect listing counts in Amsterdam or Lisbon. This is plausible given distinct tourist markets. Less plausible for European cities relative to each other — we check robustness by dropping one control city at a time.

### 5. Exclusion (for Synthetic Control)

The synthetic control assumes that the donor pool cities are not themselves affected by NYC's regulation. Reasonable: cross-city spillovers in STR markets are minimal.

---

## Natural Experiments

### NYC Local Law 18 (September 2023)

The clearest quasi-experiment in the STR regulatory literature. Key features:
- Hard enforcement date: September 5, 2023
- Airbnb automatically de-listed non-registered hosts
- Effect was immediate and visible in platform data within weeks
- Pre-treatment market: ~22,000 active listings; post: ~4,000
- Political process driving enforcement was largely independent of market trends

The abruptness makes this unusually clean. Most STR regulation is gradual and contested; LL18 had a bright-line compliance mechanism.

### Florence Historic Centre Ban (October 2023)

The Florence UNESCO zone ban restricts new STR permits in the historic centre. Less abrupt than NYC — existing permits were grandfathered — so the effect builds more slowly. Better suited for synthetic control than a sharp DiD.

---

## Estimation Ladder

| Design | Estimand | Key Assumption |
|--------|----------|----------------|
| Two-period DiD (NYC) | ATT post-Sep 2023 | Parallel trends vs control cities |
| Event study (NYC) | Dynamic ATT by month | Parallel trends + no anticipation |
| Callaway-Sant'Anna | Cohort-specific ATTs (NYC + Florence) | Parallel trends by cohort |
| TWFE comparison | Pooled DiD | Parallel trends + homogeneous effects |
| Synthetic control (Florence) | ATT vs reweighted donor | Pre-period fit |

**On TWFE:** We include TWFE for comparison but note that with staggered adoption, TWFE can be biased when treatment effects are heterogeneous across cohorts. Callaway-Sant'Anna is the preferred estimator for the multi-city analysis.

---

## DAG

```
City characteristics (tourism market, housing stock) -> STR listing count -> Price
City characteristics -> Regulation adoption
Time trends (pandemic recovery, platform growth) -> STR listing count
Regulation -> STR listing count (causal path of interest)
Regulation -> Price (via supply reduction)
```

City and time fixed effects block the backdoor paths through city characteristics and common time trends. The residual identification threat is city-specific time-varying confounders: a city might adopt regulation *because* its STR market was already contracting (reverse causality) or *because* of a simultaneous housing policy shock.

---

## Robustness Checks

| Check | Purpose |
|-------|---------|
| Drop one control city at a time | Sensitivity to control group composition |
| Alternative outcomes (log_listings vs levels) | Functional form |
| Shift NYC treatment date -3 months | Anticipation effects |
| Restrict to entire-home listings only | Heterogeneity by listing type |
| Placebo treatment dates (pre-period) | Spurious pre-trends |
| Placebo treated cities (assign treatment to controls) | False positives |
