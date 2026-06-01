# Cruise Cabin Mix & Revenue — Semi-Synthetic Causal Demo

> **All data are simulated.** This repo does not describe any real cruise operator, ship, or booking system.

**Question:** Does expanding the number of **cabin categories** (inventory complexity) causally increase **revenue per berth** — or is the positive association driven by operator/ship scale confounding?

This project demonstrates a full causal inference pipeline — naive OLS → panel fixed effects → event study → CausalForest DML → sensitivity analysis — on a reproducible semi-synthetic panel with known ground truth.

## Why this exists

My primary causal work is on proprietary multi-property hotel inventory data at scale (room-type complexity, ADR, RevPAR). This public repo has the same causal structure — inventory complexity drives revenue, but scale confounds the raw association — with the domain changed so nothing is mistaken for client data. The identification story is real; the ships aren't.

## Quick start

```bash
pip install -r requirements.txt
python scripts/generate_data.py   # writes data/processed/
jupyter lab                       # open notebooks/ in order
```

## Causal question

When a ship expands its cabin category mix after a refit, does revenue per berth rise — holding ship fixed effects and calendar-month effects constant?

- **Treatment:** Sustained increase in `cabin_category_count` at a refit event
- **Outcome:** `log_revenue_per_berth`
- **Unit:** Ship × month
- **True effect (DGP):** β = 0.06 per category (log scale)
- **Raw association:** corr ≈ 0.88 (confounded by ship scale)

The point is to recover β ≈ 0.06 via design, while showing *why* naive OLS fails.

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `00_data_audit` | Load data, verify simulated flag, describe panel |
| `02_descriptive` | Cross-sectional scatter — show spurious strength |
| `03_naive_ols` | Inflated OLS coefficient — document bias direction |
| `04_panel_fe` | Two-way FE (ship + month) — attenuated, closer to truth |
| `05_causal_forest_dml` | Heterogeneous effects by brand tier / berth capacity |
| `06_oster_sensitivity` | How strong would unobserved confounding need to be? |
| `08_event_study` | Dynamic DiD: leads/lags around refit events |
| `10_compare_estimators` | Table: OLS vs FE vs event study vs DML vs true β |
| `99_robustness` | Alternative event definitions, placebo dates |

## Identification strategy

See [METHODOLOGY.md](METHODOLOGY.md) for the full write-up.

Short version:
1. **OLS** overstates the effect because larger, more sophisticated ships have both more cabin categories *and* higher revenue per berth (scale confounding).
2. **Panel FE** (ship + month) removes time-invariant scale, bringing the estimate toward the true β.
3. **Event study** uses the *timing* of refit events — ships that expanded categories at different months — as quasi-experimental variation. Pre-trend tests validate parallel trends.
4. **CausalForest DML** controls flexibly for observables and estimates heterogeneous effects by brand tier and ship size.

## Talking about this in interviews

> "My heaviest causal work is on proprietary multi-property hotel inventory data — room-type complexity and revenue. For GitHub I built a semi-synthetic cruise panel with the same causal structure: category count, ship fixed effects, and refit events. It's explicitly simulated, reproducible, and documents the full pipeline. The public repo is the methods reference; the private work is where I validated findings on thousands of properties."

**If asked "is that real cruise data?"** → "No. Every row is generated from a documented DGP in Python. I use the cruise domain so nobody mistakes it for my employer's data."

**If asked "walk me through identification"** → Use consistency / exchangeability / positivity vocabulary. Pre-trend plot is exhibit A.

## Repository layout

```
cruise_cabin_causal/
├── README.md
├── DATA_DICTIONARY.md
├── METHODOLOGY.md
├── LICENSE
├── requirements.txt
├── config/sim_params.yaml      # DGP knobs; change seed only
├── src/simulate_panel.py       # Data generating process
├── scripts/generate_data.py    # Entry point
├── data/
│   ├── README.md
│   └── processed/              # Committed — safe synthetic outputs
├── notebooks/                  # Numbered analysis pipeline
├── outputs/                    # Gitignored — figures, tables
└── docs/blog_draft.md
```

## License

MIT
