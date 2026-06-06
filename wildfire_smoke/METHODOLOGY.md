# Methodology

## Research Question

What is the causal effect of PM2.5 air pollution on standardized test score performance in western US school districts from 2010-2019?

---

## Why OLS Fails

The naive regression of test scores on PM2.5 is confounded by district poverty:

```
District poverty -> PM2.5 (industrial, traffic sources)
District poverty -> Test scores (resources, teacher quality, stability)
```

Poor districts have higher PM2.5 from local industrial and traffic sources AND lower test scores from resource constraints. OLS conflates the causal effect of air pollution with the selection effect of poverty. The estimated coefficient on PM2.5 is biased toward zero or positive — the opposite of the true causal direction.

Panel fixed effects (district + year FEs) remove time-invariant poverty effects but leave time-varying confounders: a factory closing or economic shock simultaneously affects local air quality and school quality.

---

## Instrumental Variables Strategy

### Instrument: Wildfire Smoke Days

For each district x year, we count the number of days with a NOAA HMS Medium or Heavy smoke plume over the district centroid. This measures exposure to smoke from distant wildfires driven by wind patterns, not local economic conditions.

**Why smoke is a valid instrument:**

**Relevance (first stage):** Smoke plumes drive PM2.5 at monitors in affected areas. When a wildfire burns upwind of a school district and wind carries smoke overhead, PM2.5 spikes at local monitors. The first-stage regression tests this: F-statistic on smoke_days in a PM2.5 regression should exceed 10.

**Exclusion restriction:** Wildfire smoke blowing from hundreds of miles away affects test scores only through the air quality channel, conditional on district-level controls. This rules out local economic activity as a driver. The main threats:

1. School closures during extreme smoke events (direct effect not through chronic PM2.5). Mitigation: use annual smoke days (cumulative exposure), not acute events; drop extreme-event years in robustness checks.

2. Evacuation disruption near fire origin. Mitigation: drop districts in counties with major fire events; the Camp Fire event study treats this separately.

3. Teacher absenteeism or anxiety effects independent of PM2.5 concentration. Mitigation: focus on smoke from distant fires (>50km from district centroid), where local disruption effects are minimal.

### LATE Interpretation

2SLS identifies the Local Average Treatment Effect (LATE) for districts whose PM2.5 is affected by wildfire smoke — districts with meaningful wildfire smoke exposure. This is the policy-relevant population for western US school districts.

---

## Regression Discontinuity Design

### Running Variable: AQI During Testing Window

States administer standardized tests in spring (roughly March-May). We compute the mean AQI for each district during the testing window using EPA monitor data. The running variable is: AQI_testing_window - 100.

**Why AQI = 100 is a natural threshold:** It is the boundary between "Moderate" and "Unhealthy for Sensitive Groups" — the first level at which EPA recommends reducing outdoor activity for children. Schools may change recess policies or air filtration responses at this level.

**Identification:** Districts that just barely exceed AQI = 100 on testing days are compared to those that just barely miss. If assignment to the "above 100" group is approximately random conditional on being near the threshold, the discontinuity identifies a causal effect.

**Threats:**
- Manipulation: districts could request make-up testing days if air quality is bad. The McCrary density test checks for bunching below the threshold.
- Donut RDD: if schools respond to the threshold in ways that affect outcomes, we test robustness to donut bandwidths that exclude observations very close to the cutoff.

---

## Double Machine Learning (DML)

CausalForest DML flexibly controls for observable confounders (district income, urbanicity, baseline test score level) and estimates heterogeneous treatment effects. It uses cross-fitting to avoid overfitting bias and returns CATE estimates at the individual district-year level.

The environmental justice angle: do low-income districts experience larger causal effects of PM2.5 on test scores? This could reflect worse baseline health, lower air filtration in school buildings, or more outdoor activity.

---

## Identification Conditions

| Condition | What it requires | How we test it |
|-----------|-----------------|----------------|
| IV Relevance | smoke_days predicts PM2.5 | First stage F-statistic |
| IV Exclusion | smoke affects scores only via PM2.5 | Robustness: drop school-closure years, drop near-fire districts |
| RDD Continuity | density of running variable is smooth at AQI=100 | McCrary density test |
| RDD No manipulation | districts cannot sort below threshold | McCrary; examine school scheduling data |
| SUTVA | no spillovers between districts | Plausible; districts take tests independently |

---

## DAG

```
Wildfire activity ──→ Smoke plumes ──→ PM2.5 at monitors ──→ Test scores
                                              ↑                     ↑
District poverty ────────────────────────────┘                     │
                │                                                   │
                └───────────────────────────────────────────────────┘
```

The smoke instrument blocks the backdoor path through district poverty by providing variation in PM2.5 that is orthogonal to local economic conditions.

---

## Sample and Panel

- **Geography:** Western US states (CA, OR, WA, MT, ID, WY, CO, NV, AZ, NM, UT)
- **Unit:** School district x year
- **Years:** 2010-2019 (exclude 2020+ due to COVID disruption of testing and air quality patterns)
- **Outcome:** SEDA mean test score estimate (math, grades 3-8, pooled)
- **Treatment:** Annual mean PM2.5 at district centroid (IDW-averaged from monitors within 100km)
- **Instrument:** Count of days with HMS Medium/Heavy smoke plume over district centroid
