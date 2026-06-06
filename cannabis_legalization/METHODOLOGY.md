# Methodology

## Research Questions

**Part 1:** What is the causal effect of recreational cannabis legalization on traffic fatality rates and opioid overdose mortality?

**Part 2:** Does the opening of a licensed cannabis dispensary change 311 complaint patterns in the surrounding neighborhood?

---

## Part 1 — State-Level Staggered DiD

### Target Trial Emulation

| Component | Definition |
|-----------|-----------|
| Eligibility | All US states (excl. DC) with FARS and population data |
| Intervention | State legalizes recreational cannabis retail sales |
| Comparator | States that have not legalized in the same year |
| Time zero | First year of legal retail sales |
| Outcome | Annual traffic fatalities per 100k; drug overdose deaths per 100k |
| Effect measure | ATT — average effect on legalizing states |

### Identification Conditions

**Parallel trends:** Pre-legalization fatality and overdose trends should be similar across treated and never-treated states, conditional on state and year fixed effects. We test this with pre-period event study coefficients. This is the most important and most debated assumption — states that legalized cannabis early (CO, WA) may have had different safety cultures than never-legalizing states.

**No anticipation:** Fatality rates should not respond to legalization before retail sales begin. Legal cannabis bills are often debated publicly for 1-2 years before implementation. We test sensitivity by shifting treatment dates one year earlier.

**Exclusion of spillovers (SUTVA):** We assume legalization in Colorado does not affect fatality rates in Kansas. Border-state effects are possible if residents cross state lines to purchase cannabis. We test robustness by comparing border vs non-border control states.

**Exogeneity of timing:** The staggered timing of legalization (2014-2023) should not be driven by concurrent trends in traffic safety or drug overdose rates. States legalized based on ballot initiatives and legislative processes, which are largely independent of short-term safety trends. This is more credible than policies targeting safety outcomes directly.

### Why TWFE Is Biased Here

With 15+ treatment cohorts, standard TWFE uses already-treated states as implicit controls for not-yet-treated states. If the effect of legalization grows over time (e.g., as the cannabis market matures), early adopters can act as "bad controls" for later cohorts — pulling their estimated effects toward zero or reversing the sign.

Callaway-Sant'Anna (2021) addresses this by:
1. Estimating a separate ATT for each (cohort, time) cell
2. Using only never-treated or not-yet-treated states as controls
3. Aggregating to an overall ATT that is robust to heterogeneous effects

### Competing Hypotheses

**Traffic fatalities:**
- Substitution: cannabis substitutes for alcohol driving → fewer alcohol-impaired fatalities
- Complementarity: cannabis + alcohol driving increases → more fatalities
- Impaired driving channel: cannabis impairs driving directly → more drug-impaired fatalities
- Net effect: empirical question; literature is mixed but leans slightly negative (small reduction)

**Opioid overdoses:**
- Substitution hypothesis: legal cannabis provides a safer alternative to opioids for pain management → fewer opioid deaths
- This is one of the most debated causal claims in health policy; some studies find evidence, others don't

### Known Confounders

- Opioid epidemic was accelerating throughout 2010-2022, independent of cannabis policy
- Traffic safety was improving over time due to vehicle safety features (Tesla Autopilot, etc.)
- COVID (2020-2021) dramatically changed both driving patterns and overdose rates
- Robust specs restrict to 2010-2019 or add COVID-year indicators

---

## Part 2 — Within-NYC Dispensary Event Study

### Design

New York's first licensed adult-use cannabis dispensary opened December 29, 2022. Licensing has been staggered since then based on NY State OCM review timelines. This provides variation in the *timing* of dispensary openings across NYC zip codes — a natural event study design.

**Unit:** NYC zip code x month
**Treatment:** First licensed dispensary opening in the zip code
**Outcome:** Log count of 311 complaints (total and by type)
**Window:** 12 months pre-opening to 12 months post-opening

### Identification

The key assumption is that NYS licensing timelines are not correlated with pre-existing trends in 311 complaint rates at the zip code level. Licensing delays are driven by OCM processing times, not by neighborhood characteristics. We test this with pre-trend coefficients.

**Plausible effects:**
- Increased foot traffic near dispensaries → more noise, parking complaints
- Displacement of illegal dealers → fewer drug activity complaints
- Gentrification signal → changes in quality-of-life complaint types

**Threats:**
- Dispensaries may be sited in neighborhoods already changing (anticipation of gentrification)
- NYS was prioritizing Social Equity applicants, which could correlate with neighborhood type
- 311 complaint behavior itself is endogenous (awareness effects)

---

## DAG (Part 1)

```
State political culture ──→ Legalization timing ──→ Cannabis availability
State political culture ──→ Traffic safety culture ──→ Fatality rate
                                                            ↑
Cannabis availability ──────────────────────────────────────┘

State + year FE block the backdoor path through political culture.
Staggered timing provides quasi-random variation in exposure year.
```
