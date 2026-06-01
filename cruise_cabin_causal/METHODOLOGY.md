# Methodology

## Research Question

Does expanding the number of **cabin categories** (inventory mix complexity) causally increase **revenue per berth**, or is the association driven by latent ship/operator scale?

This is an inventory-complexity-to-revenue problem: larger, more sophisticated ships have both more cabin configurations and higher baseline revenue — making naive cross-sectional comparisons nearly useless for causal inference.

---

## Causal Estimand

### Target Trial Emulation

| Component | Definition |
|-----------|-----------|
| Eligibility | Ships active for all 48 panel months |
| Time zero | First month with new (expanded) cabin category count after a refit event |
| Treatment | Sustained increase in `cabin_category_count` (≥1 month with new count) |
| Comparator | Ships that never receive a refit during the panel |
| Outcome | `log_revenue_per_berth` at 1–12 months post-event |
| Effect measure | ATT — average effect among ships that actually refitted |

### Potential Outcomes

Let *Y_it(d)* be the log revenue per berth for ship *i* at month *t* had category count been *d*. The within-ship effect of expanding by Δ categories is:

> τ = E[Y_it(d + Δ) − Y_it(d) | treated]

The DGP encodes a true linear effect: τ = β × Δ, where **β = 0.06** (per category, log scale).

---

## Identification Conditions

### 1. Consistency
The refit event maps to a clean, sustained change in `cabin_category_count`. There is no ambiguity about what "receiving treatment" means in the simulated DGP. In real hospitality data, consistency is more fragile: a "room type count change" might reflect a PMS migration rather than a genuine inventory expansion.

### 2. Exchangeability (Parallel Trends for Event Study)
The core identifying assumption for the event study: ships that refitted and ships that didn't would have followed the same revenue trajectory *had the refit not occurred*, conditional on ship and calendar-month fixed effects.

We test this assumption by estimating leads (pre-refit coefficients) in the event study. If pre-trend coefficients are near zero, parallel trends is plausible.

**Threats in real data:** Large-scale refits may be scheduled anticipating strong demand — violating no-anticipation. Refit timing may correlate with market conditions.

### 3. Positivity
Refit events are spread across months 12–36 and across brand tiers and regions. We verify sufficient treated observations in each event-study window.

**Check:** Event-study cells with fewer than 5 ships per relative-month bin are flagged.

### 4. No Anticipation
Revenue should not respond to a planned refit before the refit occurs. We test this by checking that τ_{-k} ≈ 0 for k = 1, 2, 3 pre-periods.

**Note:** In the simulated DGP, there is no anticipation by construction. In real data, marketing of newly refitted cabins could start pre-refit.

### 5. SUTVA (Stable Unit Treatment Value Assumption)
We assume no spillover between ships: a refit on one ship does not affect revenue on another. This is reasonable in the simulation; more questionable in real deployment where ships compete for same itineraries and routes.

---

## Data Generating Process (Known Ground Truth)

The DGP is fully documented in `src/simulate_panel.py` and parameterized via `config/sim_params.yaml`. Key structural equations:

**Latent scale** (ship-level):

> ship_scale_i ~ N(0, 1)

**Ship fixed effect on log revenue** (confounding path):

> FE_i = 4.2 + 0.35 × ship_scale_i + ε_i

**Baseline cabin categories** (also driven by scale — this is the confound):

> base_categories_i = round(6 + 2.2 × ship_scale_i + Poisson(1))

**Outcome** (ship i, month t):

> log_rpb_it = FE_i + month_FE_t + 0.06 × cabin_category_count_it + ε_it

This makes the cross-sectional OLS biased upward: larger ships have both more categories *and* higher FEs.

**Treatment assignment:** 18% of ships receive a random refit at a random month in [12, 36], adding +1 or +2 cabin categories.

---

## Estimation Ladder

| Design | Estimand | Key Assumption | Expected Bias vs True β |
|--------|----------|----------------|------------------------|
| Naive OLS | Associational | Conditional ignorability (fails) | Strong upward |
| OLS + controls | Partial adjustment | Observables capture confounding | Partial attenuation |
| Panel FE (ship + month) | Within-ship ATT | Strict exogeneity of time-varying shocks | Near zero — close to β |
| Event Study / DiD | ATT at changers | Parallel trends, no anticipation | Should align with FE |
| CausalForest DML | CATE | Overlap, no unobserved confounding given X | Varies by subgroup |

**Expected result:** OLS coefficient >> 0.06; FE and event study converge toward 0.06.

---

## DAG

```
Ship Scale ──→ Cabin Category Count ──→ log Revenue per Berth
     │                                          ↑
     └──────────────────────────────────────────┘
           (direct path through ship FE)
```

Observable partial proxies for scale: `brand_tier`, `berth_capacity`, `sailing_region`.  
Ship fixed effects block the backdoor path through scale. The event study uses timing variation to identify the causal path.

---

## Robustness Checks

| Check | What it tests |
|-------|--------------|
| Restrict to δ=1 vs δ=2 events | Whether effect scales linearly with Δ categories |
| Placebo event dates (shift ± 6 months) | Spurious pre-trends or artifactual patterns |
| Leave-one-region-out | Whether a single region drives results |
| Alternative event window (±6 vs ±12 months) | Sensitivity to window choice |
| Brand tier subgroups | Heterogeneity in the causal effect |

---

## What This Demonstrates

This repo is a methods reference. In a technical screen, the goal is to:

1. Articulate *why* cross-sectional OLS fails (scale confounding; show the DAG)
2. Explain *what* panel FE buys (removes time-invariant heterogeneity via within-ship variation)
3. Defend parallel trends as an assumption (not a fact), and explain how the event study pre-trend plot tests it
4. Know the limits: SUTVA violations, anticipation effects, what IV would require to go further

The known true β = 0.06 is a pedagogical device: it lets you verify that the pipeline recovers the right answer before applying the same design to real data where you don't know the truth.
