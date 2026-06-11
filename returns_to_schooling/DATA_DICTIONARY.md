# Data Dictionary — Returns to Schooling

**Source:** Wooldridge (1993), *Introductory Econometrics*, `wage2` dataset.  
National Longitudinal Survey of Youth (NLS-Y), young men, United States.  
**N = 935 observations** (857 with non-missing IQ score).  
**Access:** `pip install wooldridge` → `import wooldridge as woo; df = woo.dataWoo('wage2')`

---

## Variables

| Variable | Type | Description | Notes |
|----------|------|-------------|-------|
| `wage` | continuous | Monthly earnings (USD) | Range: 115–3,078; mean ≈ $957 |
| `lwage` | continuous | Natural log of monthly earnings | Pre-computed; equals `np.log(wage)` |
| `educ` | integer | Years of completed schooling | Range: 9–18; mean ≈ 13.5 |
| `exper` | integer | Years of work experience | Range: 1–23; constructed as age − educ − 6 |
| `tenure` | integer | Years with current employer | Range: 0–23 |
| `IQ` | integer | IQ test score | Range: 50–145; mean ≈ 101; **78 missing** |
| `KWW` | integer | Knowledge of World of Work score | Occupational aptitude proxy; range 12–56 |
| `married` | binary | 1 if currently married | — |
| `black` | binary | 1 if Black | — |
| `south` | binary | 1 if lives in southern US | — |
| `urban` | binary | 1 if lives in urban area | — |
| `sibs` | integer | Number of siblings | Range: 0–14; used as noise-inducing control demo |
| `brthord` | integer | Birth order | — |
| `meduc` | integer | Mother's years of education | ~197 missing |
| `feduc` | integer | Father's years of education | ~196 missing |
| `age` | integer | Age in years | Range: 28–38; sample is "young men" |

---

## Key Relationships

**The identification challenge:** Higher-ability individuals both pursue more schooling and earn higher wages. IQ is a partial proxy for ability. Including IQ in the wage regression reduces the measured return to schooling — demonstrating the upward bias in naive OLS.

**Why IQ is unusual:** Most real-world observational datasets do not include any measure of cognitive ability. Having IQ in the data allows us to apply the Omitted Variable Bias (OVB) formula numerically and verify that the bias equals exactly what the formula predicts. This is rare, and it's why `wage2` is a particularly instructive dataset for demonstrating OLS confounding mechanics.

**Treatment:** `educ` — years of completed schooling (continuous)  
**Outcome:** `lwage` or `np.log(wage)` — log monthly earnings  
**Key confounders:** `IQ`, `exper`, `tenure`, demographics  
**Noise-inducing control demo:** `sibs` — predicts education but has weak direct effect on wages
