# Blog Draft

**Working title:** "Wildfire Smoke Is Lowering Test Scores — And We Can Prove It (With IV, RDD, and ML)"

**Target length:** 2,000-2,500 words
**Audience:** Data scientists and policy-minded readers

---

## Hook — Climate and Kids

Every fall, parents in California, Oregon, and Washington watch air quality apps as wildfire smoke settles over their cities. Schools close. Kids stay inside. But the acute closures are only part of the story. What about the months of degraded air quality before and after the acute events? What does chronic PM2.5 exposure do to kids learning math?

This is a hard causal question. The naive regression is nearly useless.

---

## Why Naive Regression Fails

A simple cross-sectional regression of district test scores on PM2.5 shows almost nothing — or even a positive relationship. That is not because pollution is good for kids. It is because the districts with the worst industrial and traffic-related air quality are also the districts with the fewest resources, the most economically stressed families, and the worst baseline school outcomes. PM2.5 and poverty are tangled together.

Panel fixed effects help. District fixed effects remove the time-invariant poverty story — the fact that Fresno has always had worse air and worse schools than Marin. What is left is within-district variation: when does a district's air quality worsen, and does that correspond to worse test scores that year?

Better, but not solved. Time-varying economic shocks — a factory closing, a highway expansion — can simultaneously worsen air quality and school outcomes. The FE estimator is still confounded.

---

## The Instrument: Smoke From Upwind Wildfires

The key insight: wildfire smoke blowing from hundreds of miles away raises PM2.5 but has nothing to do with the local economy. A fire burning in the Sierra Nevada in August does not care whether Sacramento has high or low unemployment. When wind carries smoke toward Sacramento Valley school districts, PM2.5 spikes — and that variation is plausibly exogenous to local conditions.

We operationalize this using NOAA's Hazard Mapping System (HMS), which provides daily satellite-derived smoke plume polygons classified as Light, Medium, or Heavy. For each school district x year, we count the number of days with a Medium or Heavy smoke plume over the district centroid. This is the instrument.

**Two-stage logic:**
- First stage: smoke days -> PM2.5 (test: F-statistic on instrument, want F > 10)
- Second stage: instrumented PM2.5 -> test scores

Include Figure 1: first-stage scatter (smoke days vs PM2.5, binned, within-district demeaned). Strong upward slope = relevant instrument.

---

## Main Result

2SLS estimate: a 1 μg/m³ increase in annual PM2.5 reduces test scores by [X] standard deviations (95% CI: [X, X]).

Reduced form (smoke days -> test scores directly, bypassing PM2.5): [X] SD per additional smoke day.

The reduced form is more credible if someone questions whether PM2.5 is the true channel — it only requires that smoke affects scores through some air quality pathway, not necessarily specifically PM2.5.

Compare to OLS and FE: the IV estimate is more negative than FE, consistent with the poverty confound biasing FE toward zero (poor districts have high industrial PM2.5 AND low scores, making OLS look like pollution has a small or zero effect).

---

## A Second Design: Regression Discontinuity at AQI = 100

The EPA's Air Quality Index has a threshold at 100 — the boundary between "Moderate" and "Unhealthy for Sensitive Groups." At this level, EPA recommends reducing outdoor activity for children. Schools often respond: canceling recess, keeping kids inside.

We use this threshold as a natural discontinuity. Districts whose testing-season AQI was just above 100 are compared to those just below. If assignment near the threshold is approximately random, the gap in test scores at AQI = 100 is causal.

Include Figure 2: RDD plot with binned scatter and fitted lines on each side. Gap visible at threshold.

This is a completely different design from the IV — different source of variation, different estimand (local to the AQI = 100 boundary), different data. If both designs point in the same direction, that is unusually strong evidence.

---

## Who Is Most Affected? DML and Environmental Justice

CausalForest DML estimates heterogeneous treatment effects by district poverty level. The environmental justice question: do low-income districts bear a larger educational burden from air pollution?

If high-poverty districts show larger negative CATEs, the mechanism could be: worse building air filtration, more outdoor activity exposure, less ability to compensate with tutoring or enrichment, or baseline health vulnerabilities amplifying the effect.

This analysis requires ACS district demographic data merged with the panel. The DML results [describe findings from notebook 08 once data is available].

---

## Camp Fire Case Study

The Camp Fire (November 8, 2018) was the most destructive wildfire in California history. It burned 153,000 acres and produced smoke that blanketed the Sacramento Valley and Bay Area for weeks. AQI in Sacramento exceeded 200 for more than a week. Many schools closed.

The event study estimates test score effects in high-smoke districts in 2018 versus their pre-2018 trends, using low-smoke districts as controls. Pre-period coefficients (2013-2017) test whether parallel trends held before the fire. Post-period coefficient (2018) estimates the Camp Fire's educational impact.

Include Figure 3: Camp Fire event study.

---

## Exclusion Restriction Concerns

The main threat to the IV is school closures: during extreme smoke events, schools close, which directly affects test scores (through lost instruction days) independently of chronic PM2.5 exposure. We address this by:

1. Using annual smoke days (cumulative chronic exposure) rather than acute event indicators
2. Dropping 2018 in robustness checks (Camp Fire year)
3. Focusing on districts far from fire origins where closures are less common

We cannot fully rule this out. The reduced form (smoke -> scores) is more robust to this concern than the 2SLS estimate.

---

## Limits

Western US sample only — generalization to other regions is uncertain. SEDA scores are estimates with their own measurement error. ACS district-level controls are imprecise. The exclusion restriction cannot be proven, only made credible.

---

## Reproduce It

```bash
# EPA AQS key: sign up at https://aqs.epa.gov/data/api/signup
python scripts/download_epa_aqs.py --email EMAIL --key KEY
python scripts/download_hms_smoke.py
# SEDA: register at https://edopportunity.org then download
python src/merge/build_panel.py
jupyter lab
```

Full pipeline: `Causal-inference-projects/wildfire_smoke/`
