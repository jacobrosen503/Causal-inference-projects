# Blog Draft — Medium Article

**Working title:** "Does Adding Cabin Categories Raise Yield? A Causal Inference Demo on Simulated Cruise Data"

**Target length:** 1,800–2,500 words  
**Figures:** 3–4 (scatter, event study, estimator comparison)

---

## Hook — Revenue Managers Expand SKU Complexity. Does It Pay Off?

Open with the intuitive business question: when a ship refits its cabin configuration and adds a new category tier (suite, balcony, oceanview-plus), does revenue per berth actually rise? The raw data says yes — emphatically. But the raw data always says yes on this kind of question. This post is about why that answer is almost entirely wrong, and what you have to do to get an honest one.

**Disclaimer paragraph (required, first screen):** All data in this post are simulated using a documented Python data-generating process. No cruise operator, ship, or booking record is described. The causal structure (inventory complexity → revenue, scale confounding) is inspired by real inventory management problems; the numbers and identities are not.

---

## The Naive Result — And Why It's Misleading

Show Figure 1: cross-sectional scatter of mean cabin categories vs mean log revenue per berth across 800 simulated ships. Correlation ≈ 0.88. OLS slope ≈ 0.19 per category.

This looks like a strong signal. It isn't.

The problem: ships that offer more cabin category tiers are also larger, more sophisticated operators with higher baseline yield. They'd have higher revenue *even without* the additional categories. This is the classic selection problem.

Key line: **"We're not measuring the effect of cabin complexity on revenue. We're measuring the effect of being a large, sophisticated ship."**

---

## DAG — One Figure Shows the Problem

Include an identification diagram:

```
Ship Scale ──→ Cabin Category Count ──→ log Revenue per Berth
     │                                          ↑
     └──────────────────────────────────────────┘
```

Ship scale drives both. Any cross-sectional regression confounds the causal path with the backdoor path through scale. Observable proxies (brand tier, berth capacity) capture some of the scale variation but not all.

---

## Panel Fixed Effects — The Within-Ship Story

If we can't compare ships to each other, can we compare the *same ship to itself* over time?

Explain two-way FE: ship fixed effects remove all time-invariant ship characteristics (scale, operator quality, route). Month fixed effects remove common industry trends. What's left is within-ship variation in category count.

For 18% of ships in the panel: they refitted and expanded their cabin mix at some point in the observation window. Before the refit: fewer categories. After: more. The FE estimator uses this timing variation.

Result: **TWFE β = 0.060** (vs OLS β = 0.189). Selection accounts for ~68% of the raw association; within-ship effect is ~32%.

Caveats to mention:
- Strict exogeneity required: no time-varying confounders correlated with refit timing
- Does the refit coincide with a pricing strategy overhaul? (In real data: yes, possibly)

---

## Event Study — Validating with Timing

The event study makes the parallel trends assumption transparent. Instead of a single post-indicator, we estimate the treatment effect at each month relative to the refit date: τ_{-12}, τ_{-11}, ..., τ_{-1}, τ_{+1}, ..., τ_{+12}.

**The pre-trend test:** if parallel trends holds, τ_{-k} ≈ 0 for all pre-periods. If we see a rise in the pre-period, ships that refitted were already on a different trajectory before the refit — and our estimate is confounded.

Show Figure 2: the event study plot. Pre-period coefficients near zero. Jump at t=0. Stable post-period effect. This is what a clean quasi-experiment looks like on simulated data.

Post-period average ≈ **0.085** — consistent with β × average Δ categories (1.48 categories on average, expected effect = 0.06 × 1.48 = 0.089).

---

## Reproduce It

The entire pipeline is on GitHub: `cruise-cabin-mix-causal`.

```bash
pip install -r requirements.txt
python scripts/generate_data.py   # regenerate the DGP
jupyter lab                        # run notebooks in order
```

DGP parameters (including the true β) are in `config/sim_params.yaml`. The point is to show you can execute and defend the design — and that on simulated data, you can verify you're getting it right.

---

## Honest Limits

1. **This is a simulation.** The DGP is designed to make panel FE work perfectly. Real data doesn't have a known ground truth.
2. **Homogeneous effects by design.** The DGP has no true heterogeneity; CausalForest finds noise. Real heterogeneity would need to be built into the DGP.
3. **SUTVA.** Ships don't compete in the simulation. Real ships do.
4. **No anticipation by construction.** Real refits are planned and marketed in advance.

---

## LinkedIn Version

"3 things that look like causal effects but aren't:

1. Cross-sectional correlation (selection)
2. Before-after comparison without controls (time trends)
3. OLS with observables when the key confounder is unobserved

This is why we use panel fixed effects and event studies. Full demo on simulated cruise data → [GitHub link]"

---

## Figure list

1. `02a_cross_sectional_scatter.png` — the misleading picture
2. `08_event_study.png` — the honest picture  
3. `10_estimator_comparison.png` — OLS vs FE vs ES vs truth

---

*Related:* Private production analysis on multi-property hotel inventory (same design; thousands of properties; no public data).
