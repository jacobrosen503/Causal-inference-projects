# Blog Draft

**Working title:** "What Happened to Airbnb When New York Cracked Down? A Causal Inference Tour"

**Target length:** 1,800-2,500 words
**Target:** Medium + LinkedIn teaser

---

## Hook — NYC listings headlines; the policy debate

Open with the numbers: in August 2023, New York City had roughly 22,000 active Airbnb listings. By October 2023, there were fewer than 4,000. That is not a gradual market shift. That is a policy.

Local Law 18, which took effect September 5, 2023, required all short-term rental hosts to register with the city, complete an in-person appointment, and be present during any guest stay. Airbnb was required to de-list any host who had not registered. The law had been debated for years and was driven by a genuine housing shortage — the argument being that short-term rentals were removing long-term housing stock from an already constrained market.

This post is not about whether the policy was right. It is about whether we can measure what it actually did, and how.

---

## Why not just compare before and after?

The naive approach: compare NYC listings in August 2023 to October 2023. Listings dropped ~80%. Done?

Not quite. The problem is that other things were also happening in late 2023. Post-pandemic travel patterns were still shifting. Airbnb was changing its fee structure platform-wide. The broader rental market was moving. Any of these could affect listing counts independent of LL18.

The "before and after" comparison confounds the policy effect with everything else that changed at the same time.

---

## The DiD fix: comparing NYC to cities that did not regulate

What we need is a counterfactual — what would NYC's listing count have looked like in October 2023 if LL18 had not passed? We cannot observe this directly. But we can approximate it using cities that had no comparable regulation in the same window.

DiD logic: if Amsterdam, Lisbon, Vienna, and Barcelona were all following similar trends to NYC before September 2023, we can use their post-September 2023 trajectory as a stand-in for what NYC's would have been absent the policy.

Estimated effect on log_listings: around -1.65 (roughly -80% in levels). The price effect is positive — supply dropped, and the remaining listings command higher nightly rates.

---

## Event study — making the assumption visible

DiD requires parallel trends: that treated and control cities were on similar trajectories before the policy. We do not have to just assume this. We can plot it.

The event study estimates the treatment effect at each month relative to the enforcement date, rather than a single pre/post average. The key check: pre-period coefficients (months before September 2023) should be near zero if parallel trends holds. Post-period coefficients show the dynamic treatment path.

Include Figure 1: event study plot. Pre-period near flat. Sharp break at t=0. Stable negative post-period. This is what a clean natural experiment looks like.

Note on anticipation: there is some evidence that NYC listings were already declining in the months before September 2023 as hosts anticipated the deadline. This means our estimate may be a lower bound on the full effect. We discuss this as a violation of no-anticipation and test sensitivity to shifting the effective date earlier.

---

## Synthetic control — Florence as a single treated unit

NYC's effect is so large that the DiD result is hard to miss. Florence is a different story. The historic centre STR ban was partial (new permits only, existing ones grandfathered), the effect builds slowly, and Florence is harder to match to a control group because no other city in the panel is quite like it — a small, high-density, UNESCO-listed historic centre with extreme tourism concentration.

For single treated units with a limited control pool, Abadie's synthetic control is the better tool. Instead of using all control cities equally, it finds a weighted combination that best matches Florence's pre-treatment outcome trajectory. The estimated effect is then the gap between Florence's actual post-treatment path and the synthetic control's path.

Include Figure 2: Florence actual vs synthetic control on log_listings. Pre-period: close fit. Post-period: Florence diverges below the synthetic.

Robustness: in-space placebo tests apply the same synthetic control method to control cities that were never treated. If Florence's post-treatment gap is larger than all placebo gaps, that is evidence the effect is real and not just noise.

---

## Staggered DiD — combining NYC and Florence

With two treated cities at different dates (NYC in September, Florence in October 2023), we can use a modern staggered DiD estimator. The standard TWFE regression is biased in this setting when treatment effects are heterogeneous — treated units in earlier cohorts can act as implicit controls for later-treated units, contaminating the estimates.

Callaway-Sant'Anna handles this by estimating cohort-specific ATTs separately and then aggregating them. We compare TWFE vs C-S and note where they diverge.

Include Figure 3: C-S ATT estimates by cohort vs TWFE pooled estimate.

---

## Limitations

The control group is imperfect. Amsterdam, Lisbon, Vienna, and Barcelona are not NYC. Tourist markets differ, housing supply dynamics differ, platform penetration differs. Parallel trends is an assumption we can test in the pre-period but not prove.

The data is scraped. Inside Airbnb captures listings available for booking on a given day. It does not capture off-platform rentals, VRBO/HomeAway, or hosts who moved to longer-term rental platforms. Some of the measured "decline" in Airbnb listings may represent migration to other platforms rather than genuine housing stock returning to long-term rental.

LL18 is a bundle. Registration, in-person appointment, and host presence requirements came together. We cannot separately identify the effect of each component.

---

## Reproduce it

Full pipeline on GitHub: `Causal-inference-projects/airbnb_regulation/`

```bash
python scripts/download_inside_airbnb.py  # get real data
python scripts/build_real_panel.py        # build city-month panel
jupyter lab                               # run notebooks in order
```

---

## LinkedIn teaser

"3 ways economists construct a counterfactual when you cannot run an experiment:

1. Difference-in-differences: find cities that did not pass the law and compare trends
2. Synthetic control: build a weighted composite that matches pre-treatment history
3. Staggered DiD: stack multiple treated cities with different timing and recover cohort-specific effects

NYC Local Law 18 gives a rare case where the effect is so sharp you can almost see it raw. The methods are still worth doing — because the next policy shock will not be this clean."
