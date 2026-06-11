# Returns to Schooling: Numerically Verifying the Mechanics of OLS

**The claim this project makes:** Every result that OLS regression is credited with — bias removal, standard error behavior, fixed effects identification — has a precise algebraic mechanism. This project verifies those mechanisms on real data, to floating-point precision, not just states them.

**The question:** What is the causal return to an additional year of schooling? Naive OLS says ~6%. Holding the demographic and experience controls fixed, the model *without* an ability measure gives 6.5%; adding IQ drops it to 5.4%. That 1.1-percentage-point gap is ability bias — and we calculate it exactly from three separate regressions using the Omitted Variable Bias formula, verifying it matches to ten decimal places.

**What makes this unusual:** Most observational datasets don't include a direct measure of cognitive ability. `wage2` does. That one feature turns what would be a qualitative claim ("there's probably ability bias") into a numerical verification that would otherwise only be possible with simulated data. The same principle runs through the entire project: we don't just apply methods, we verify the theorems behind them.

**Data:** Wooldridge (1993) NLS-Y wage panel, 935 young men, United States. Available through the `wooldridge` Python package (`pip install wooldridge`). No download or registration required.

---

## Why This Project Exists

Most causal inference demos show that adding controls changes an estimate. This project asks the harder question: *why?* The answer is the **Frisch-Waugh-Lovell (FWL) theorem** — a result from 1933 that most practitioners have never seen verified on real data.

FWL says that multivariate OLS can be decomposed into three steps: (1) regress the treatment on the controls and save residuals, (2) regress the outcome on the controls and save residuals, (3) regress the outcome residuals on the treatment residuals. The coefficient from step 3 is algebraically identical to the one from the full regression — same point estimate, same standard error, same p-value. This is a theorem, not an approximation.

Verifying this on real data, to five decimal places, is the clearest possible demonstration of what regression is doing: it is *physically orthogonalizing* the treatment with respect to the controls. The residualized treatment is the variation in schooling that is unexplained by IQ, experience, and demographics — as close to "randomly assigned schooling" as observational data can get.

This dataset is especially useful because it includes **IQ scores** — a direct proxy for the key confound. Having a measured ability variable lets us apply the OVB formula numerically, something that is usually only possible with simulated data.

---

## Concepts Demonstrated

| Concept | Notebook |
|---------|---------|
| Naive OLS and the direction of confounding bias | 01 |
| Progressive control addition and the diminishing returns | 01 |
| Omitted variable bias formula — algebraic derivation and numerical verification | 01 |
| The Frisch-Waugh-Lovell theorem: three-step decomposition | 02 |
| Debiasing step: why residualizing the treatment removes confounding | 02 |
| Denoising step: why residualizing the outcome reduces variance, not bias | 02 |
| Coefficient identity across all three FWL steps (SE matches after the df correction) | 02 |
| SE formula σ(ε̂) / (σ(T̃)√(n−df)) — derived and verified numerically | 02 |
| Why log wages? Level vs. proportional treatment effects | 03 |
| Nonlinear treatment response: the Mincer experience quadratic | 03 |
| Neutral controls: variables that reduce SE without inducing bias | 03 |
| Noise-inducing controls: variables that inflate SE by absorbing treatment variance | 03 |
| Bias-variance trade-off in control selection | 03 |
| Fixed effects via de-meaning: algebraic equivalence to dummy variables | 04 |
| Saturated model: one slope per group | 04 |
| Regression as a variance-weighted (not sample-size-weighted) average | 04 |
| Why variance-weighting matters for DiD (foreshadowing Goodman-Bacon) | 04 |

---

## Notebooks

| Notebook | Topic | Key Punchline |
|---------|-------|---------------|
| [`01_naive_ols_and_confounding`](notebooks/01_naive_ols_and_confounding.ipynb) | OVB formula | Including IQ drops the return to schooling from 6.5% → 5.4%. The OVB formula recovers that 1.1-point gap exactly. |
| [`02_fwl_orthogonalization`](notebooks/02_fwl_orthogonalization.ipynb) | FWL theorem | All three approaches give identical coefficients to five decimal places. The standard error matches only after the degrees-of-freedom correction — verified via the closed-form SE formula. |
| [`03_nonlinearities_and_controls`](notebooks/03_nonlinearities_and_controls.ipynb) | Control selection | Adding siblings *widens* the CI on schooling even though siblings barely affect wages. Adding IQ *tightens* it — same magnitude of confound, opposite effect on variance. |
| [`04_fixed_effects_and_weighted_average`](notebooks/04_fixed_effects_and_weighted_average.ipynb) | FE and weighting | OLS with group dummies gives a variance-weighted average of within-group effects — not a sample-size-weighted average. The group with more education variance gets more weight. |

---

## Quick Start

```bash
pip install -r requirements.txt
jupyter lab   # open notebooks/ in order
```

No data download needed. Each notebook calls `woo.dataWoo('wage2')` directly.

**View rendered notebooks on nbviewer** (no local setup required):
- [01 — Naive OLS and OVB Formula](https://nbviewer.org/github/jacobrosen503/Causal-inference-projects/blob/main/returns_to_schooling/notebooks/01_naive_ols_and_confounding.ipynb)
- [02 — Frisch-Waugh-Lovell Theorem](https://nbviewer.org/github/jacobrosen503/Causal-inference-projects/blob/main/returns_to_schooling/notebooks/02_fwl_orthogonalization.ipynb)
- [03 — Nonlinearities and Control Selection](https://nbviewer.org/github/jacobrosen503/Causal-inference-projects/blob/main/returns_to_schooling/notebooks/03_nonlinearities_and_controls.ipynb)
- [04 — Fixed Effects and Variance-Weighted Average](https://nbviewer.org/github/jacobrosen503/Causal-inference-projects/blob/main/returns_to_schooling/notebooks/04_fixed_effects_and_weighted_average.ipynb)

---

## Identification Strategy

See [METHODOLOGY.md](METHODOLOGY.md) for the full technical write-up.

Short version:

1. **Naive OLS** overstates the return to schooling because ability (proxied by IQ) drives both more schooling and higher wages. The OVB formula quantifies this: bias = (IQ coefficient in wage regression) × (IQ~educ regression coefficient).

2. **Controlled OLS** adds work experience, demographics, and IQ. The FWL theorem explains *why* this removes confounding: OLS residualizes education on the controls, producing a "debiased" version of the treatment. We verify the three-step decomposition numerically.

3. **Nonlinear specification** captures log-linear wage effects and the concave experience profile (experience²). Notebook 03 works through how to linearize a nonlinear treatment before applying FWL.

4. **Fixed effects** via de-meaning show that controlling for group membership is algebraically equivalent to subtracting within-group means. Notebook 04 demonstrates this and connects it to variance-weighted averaging — the same issue that causes TWFE DiD to fail with heterogeneous treatment timing.

---

## Talking About This in Interviews

> "Most people learn OLS as a prediction tool. I used it as a debiasing tool, following Facure's framing. The wage-schooling dataset is particularly instructive because it has IQ scores — so I could apply the OVB formula numerically instead of just citing it. The FWL orthogonalization notebook verifies that all three decomposition steps give the exact same coefficient and SE on real data. That kind of ground-truth verification is what I look for when I'm confident a method is working correctly."

**"What was the most interesting finding?"** → "The OVB decomposition. There's a ~1.1 percentage-point gap between the with-ability and without-ability OLS estimates. The OVB formula says this gap equals the IQ wage premium (δ) times the education-IQ correlation (γ). We calculated both from separate regressions and their product matches the actual gap to ten decimal places. That's normally only verifiable with simulated data — having IQ scores in an observational dataset is what makes it possible here. There's also a puzzle: Card (1995)'s IV estimate is *higher* than our OLS, not lower, suggesting measurement error attenuation may be offsetting the upward ability bias in this sample."

**"Isn't this just adding controls?"** → "Adding controls is the result. FWL is the mechanism. When you add IQ, OLS residualizes schooling on IQ — it removes the variation in education that's explained by ability, leaving a 'purified' treatment that's orthogonal to all the confounders. That residualized treatment is what gets regressed on wages. The two are numerically equivalent, but FWL tells you exactly what you're conditioning on. It also explains why noise-inducing controls hurt: anything that predicts the treatment absorbs residual variation and inflates your standard error."

**"Is this causal?"** → "Conditional on CIA holding, yes. But CIA requires all common causes of schooling and wages to be in the controls. IQ helps a lot, but non-cognitive skills and school quality remain uncontrolled. A fully credible estimate needs a quasi-experimental design — Card (1995)'s proximity-to-college IV is the canonical approach, and it motivates the IV design in the wildfire_smoke project in this repository."

---

## Repository Layout

```
returns_to_schooling/
├── README.md
├── DATA_DICTIONARY.md
├── METHODOLOGY.md
├── requirements.txt
├── notebooks/
│   ├── 01_naive_ols_and_confounding.ipynb
│   ├── 02_fwl_orthogonalization.ipynb
│   ├── 03_nonlinearities_and_controls.ipynb
│   └── 04_fixed_effects_and_weighted_average.ipynb
└── outputs/          # figures written here when notebooks are run (gitignored — use nbviewer links above)
```

---

## Blog Post Angles

Three natural posts from this project, each with a different audience:

**1. "What OLS is actually doing when it 'controls for' something"** *(general data science audience)*
The FWL three-panel visualization (Notebook 02) is the centerpiece: watching IQ-quartile color offsets physically disappear as the treatment is orthogonalized. Most practitioners have never seen regression explained this way. The pitch: "you've been told OLS holds variables constant — it doesn't, it residualizes them, and here's what that looks like."

**2. "I found the exact amount my regression lies to me"** *(technical, shareable)*
The OVB numerical verification (Notebook 01). Omitting IQ inflates the return to schooling by exactly 1.10 percentage points (6.5% → 5.4%). We know it's exactly that because we calculated δ × γ from three regressions and it matches to ten decimal places. Raises the IV puzzle at the end: if OLS is biased upward by ability, why is Card's IV estimate higher?

**3. "Why your DiD regression might have the wrong sign"** *(applied econometrics audience, topical)*
The Goodman-Bacon thread from Notebook 04. Start with variance-weighting (a property of OLS most practitioners don't know), build to TWFE, show the staggered DiD simulation where the contaminated 2×2 comparison pulls the estimate down. Closes with Callaway-Sant'Anna as the fix. This bridges OLS fundamentals to a live debate in applied econometrics.

## Connection to Other Projects

This project establishes the **OLS fundamentals** that underpin every other method in this repository:

- **cruise_cabin_causal** uses panel fixed effects (which are exactly the de-meaned OLS from Notebook 04) and CausalForestDML (which extends FWL to nonparametric models)
- **cannabis_legalization** uses DiD, where the variance-weighted average property of OLS (Notebook 04) is what causes TWFE to fail with heterogeneous treatment timing (Goodman-Bacon 2021)
- **wildfire_smoke** uses IV/2SLS, which is a two-stage application of OLS where FWL appears in both stages

---

## License

MIT
