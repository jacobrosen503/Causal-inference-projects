# Blog Draft

**Working title:** "Does Legalizing Cannabis Save Lives? What Staggered DiD Actually Shows"

**Target length:** 1,800-2,500 words
**Hook:** policy stakes + common naive analysis failures

---

## Hook — A Policy With Measurable Predictions

Recreational cannabis legalization is one of the cleanest policy experiments in recent US history. Starting with Colorado and Washington in 2014, states have been legalizing at staggered intervals for a decade. The timing is driven by ballot initiatives and legislative calendars — not by concurrent trends in traffic safety or drug overdose rates. That makes it unusually tractable for causal inference.

Two specific hypotheses are measurable: does legalization reduce drunk driving (substitution of alcohol for cannabis)? Does it reduce opioid overdose deaths (substitution of opioids for cannabis as a pain management option)? Both have active policy debates. Both are empirical questions.

---

## Why Naive Analysis Fails

The obvious approach: compare traffic fatalities before and after legalization in Colorado and Washington. Both outcomes improved after 2014. But so did traffic safety across the entire country — airbags, AEB systems, and slower speed trends. A before/after comparison in treated states confounds the policy effect with national trends.

The second attempt: compare legalized vs non-legalized states. But states that legalized tend to be more liberal, more urban, and have different baseline safety cultures than states that haven't. A cross-sectional comparison just measures political geography.

Difference-in-differences combines both: compare the *change* in treated states to the *change* in control states. This cancels out both the national trend (affecting everyone) and the time-invariant state differences (always present).

---

## The Staggered Timing Problem

With 15+ treatment cohorts from 2014 to 2023, standard TWFE difference-in-differences has a bias problem. When effects are heterogeneous across cohorts — if early adopters see different effects than late adopters — TWFE uses already-treated states as implicit controls for later-treated ones. Early Colorado/Washington become comparison states for 2022 New Jersey. If Colorado's effect changed over time, that comparison is invalid.

The fix (Callaway-Sant'Anna, 2021): for each cohort, compare only to never-treated or not-yet-treated states. Estimate cohort-specific ATTs separately, then aggregate. No already-treated contamination.

---

## Main Results

**Traffic fatalities:** The headline TWFE estimate is [result]. The Callaway-Sant'Anna aggregated ATT is [result]. Cohort-specific ATTs range from [range] — variation across cohorts is [interpretation].

**Opioid overdose deaths:** [result from notebook 09]. The substitution hypothesis finds [support/limited support/no support] in this data.

**Event study pre-trends:** [interpretation of pre-period coefficients]. Parallel trends looks [credible/questionable] for this analysis.

---

## What This Does Not Prove

Cannabis legalization is a bundle of interventions: retail access, reduced criminalization, price and quality regulation, tax revenues, marketing restrictions. We cannot separately identify which component drives any measured effect.

The opioid crisis was accelerating throughout 2010-2022 independent of cannabis policy. COVID (2020-2021) dramatically changed both driving patterns and overdose rates. Robust specs drop 2020-2021 entirely.

Generalizability: states that legalized first (CO, WA) may be fundamentally different from states that have not legalized at all. The ATT measures the effect *in states that chose to legalize* — not the effect that would occur if a politically opposed state were forced to legalize.

---

## NYC Dispensary Appendix

A shorter section on the within-NYC event study: do new dispensaries change 311 complaint patterns? Results from notebook 07: [findings]. The pre-trend plot: [interpretation]. This is a more speculative analysis but illustrates how the same design logic scales from state-year to zip-month.

---

## Reproduce It

```bash
# FARS data: https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars
python scripts/download_fars.py
python src/build_fars_panel.py

# CDC WONDER: https://wonder.cdc.gov/ucd-icd10-expanded.html (manual query)
python src/build_cdc_panel.py

# NYC 311 + dispensaries
python scripts/download_311.py --auto
python scripts/download_dispensaries.py --auto
python src/build_311_panel.py

# Run notebooks in order
jupyter lab
```

Full repo: `Causal-inference-projects/cannabis_legalization/`
