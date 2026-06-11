# Methodology — Returns to Schooling

## Identification Assumption

This project uses **conditional independence** (also called unconfoundedness or selection-on-observables):

> Conditional on observed covariates X, years of schooling is as good as randomly assigned:
> (Y₀, Y₁) ⊥ T | X

In the wage regression context, this requires that all common causes of schooling and earnings are captured in X. The baseline control set includes IQ, work experience, tenure, marital status, race, region, and urbanicity.

**Is this plausible?** Partially. IQ captures one major confound (cognitive ability), and experience/tenure capture accumulated labor market skills. What remains uncontrolled — family networks, non-cognitive skills, institutional quality of schools attended — continues to bias the estimate upward. The project is honest about this limitation, using the IQ inclusion as a demonstration of *how* regression removes bias, not as a claim that the resulting estimate is fully causal.

---

## Estimands

**Parameter of interest:** The average return to an additional year of schooling in log wages, interpreted as an approximate percentage effect:

∂E[log(wage) | educ, X] / ∂educ = β₁

Under CIA, β₁ equals the Average Treatment Effect (ATE) of one additional year of schooling on log monthly earnings, holding X fixed.

**Why log wages?** The Mincer (1974) earnings equation models log wages as a linear function of schooling, experience, and experience². This specification captures the empirically observed proportional (not level) returns to education and the concave experience profile. See Notebook 03 for the distributional justification and the nonlinear experience treatment.

---

## The OVB Formula

If the true model is:

log(wage) = τ·educ + δ·IQ + θX + ε

but we estimate the short model omitting IQ:

log(wage) = α·educ + θX + u

then the OLS estimator for α satisfies:

α = τ + δ · γ

where γ is the coefficient from the auxiliary regression IQ ~ educ + X. The term δ·γ is the **omitted variable bias** — positive here because IQ raises wages (δ > 0) and IQ is positively correlated with education even after partialling out X (γ > 0).

This project verifies the formula algebraically by computing τ, δ, and γ from separate regressions and confirming their sum equals α. The match is exact (to floating-point precision), not approximate.

---

## The Frisch-Waugh-Lovell Theorem

The FWL theorem (Frisch & Waugh 1933; Lovell 1963) states that in the model:

Y = β₁T + β₂X + ε

the OLS estimate of β₁ is numerically identical to the estimate obtained by the following three-step procedure:

1. **Debiasing:** Regress T on X; compute residuals T̃ = T − X(X'X)⁻¹X'T
2. **Denoising:** Regress Y on X; compute residuals Ỹ = Y − X(X'X)⁻¹X'Y
3. **Final model:** Regress Ỹ on T̃

The equivalence holds for both the coefficient estimate and the standard error. This is not an approximation — it is a theorem. Verifying it numerically on real data (to five decimal places) demonstrates that regression removes confounding by physically orthogonalizing the treatment with respect to the controls, not by "holding them constant" in any abstract sense.

**Practical implication:** FWL separates the debiasing step from the impact estimation step. The residualized treatment T̃ is the version of the treatment that is orthogonal to all controls — as good as randomly assigned, conditional on X. Any downstream analysis can be performed on T̃ directly.

**Denoising vs. debiasing:** The debiasing step (step 1 alone) produces the same point estimate as the full three-step procedure. The denoising step (step 2) adds no further bias reduction; its only function is to reduce the variance of the error term in the final model, producing tighter standard errors. This is verified numerically in Notebook 02.

---

## Standard Error Formula

The SE of β₁ in the multivariate regression is:

SE(β̂₁) = σ(ε̂) / (σ(T̃) · √(n − df))

where ε̂ are the residuals from the full model, T̃ are the treatment residuals from the debiasing step, and df is the number of parameters estimated. This formula is verified numerically in Notebook 02.

The formula reveals two levers on precision:
- **Better outcome prediction** (smaller σ(ε̂)) tightens the SE — this is what the denoising step delivers
- **More treatment variation** (larger σ(T̃)) also tightens the SE — controlling for strong predictors of the treatment reduces T̃ variance and therefore inflates the SE

---

## Bias-Variance Trade-Off in Control Selection

Not all controls are equal. A covariate that:
- **Causes Y but not T** → neutral control; reduces SE without inducing bias (include it)
- **Causes T but not Y** → noise-inducing control; reduces σ(T̃), inflating SE (omit it)
- **Causes both T and Y** → confounder; must be included to remove bias, even though it also reduces σ(T̃)

In the wage regression:
- `IQ` causes both wages and education → confound; include despite SE cost
- `sibs` (number of siblings) strongly predicts education level but has very weak direct effect on wages → noise-inducing; including it inflates SE on education coefficient with minimal bias reduction

Notebook 03 demonstrates this empirically by comparing SE and coefficient across five control specifications.

---

## Fixed Effects and De-Meaning

The Frisch-Waugh-Lovell theorem extends directly to categorical covariates. Including group dummies G in the model:

log(wage) = β₁·educ + β₂·G + ε

is algebraically equivalent to:

1. Subtracting the within-group mean from both educ and log(wage) (de-meaning)
2. Running the regression on the de-meaned variables

This is the **within-group transformation** (or within estimator), which removes all time-invariant group-level confounding. It is the foundation of panel fixed effects, which appears in the cruise_cabin_causal project. Notebook 04 establishes the equivalence numerically and connects it to the idea of regression as a **variance-weighted** (not sample-size-weighted) average of within-group effects.

---

## Limitations

1. **CIA is not fully plausible.** Unobserved ability components, family networks, and school quality remain uncontrolled. The estimated ~4.5% return per year should be interpreted as an *upper bound* on the true causal effect under selection-on-observables.

2. **Sample is restricted.** The NLS-Y `wage2` data covers only young men in the United States. Estimates do not generalize to women, older workers, or other countries.

3. **IQ as an ability proxy.** IQ is a partial and imperfect measure of the cognitive ability that confounds the schooling-wages relationship. Including it reduces bias but does not eliminate it.

4. **No quasi-experimental design.** This project makes no claim of quasi-experimental identification (no instrument, no RDD, no DiD). The goal is to demonstrate the mechanics of OLS-based debiasing, not to produce a publication-quality causal estimate. For instrumental variables approaches to the returns-to-schooling problem, see Card (1995) — proximity to a college as an instrument — which motivates the wildfire_smoke IV project in this repository.
