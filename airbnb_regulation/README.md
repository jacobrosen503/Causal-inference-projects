# Airbnb Regulation Impact Study

When cities restrict short-term rentals, what actually happens to listings, prices, and availability?

This project applies staggered DiD, synthetic control, and event study methods to estimate the causal effect of short-term rental regulation. The headline case is New York City's Local Law 18 (September 2023), which required hosts to register in person and be present during guest stays. Within weeks, active listings fell from roughly 22,000 to around 4,000.

> **Note on data:** This project was designed around Inside Airbnb's historical listing snapshots, which were previously free to download. As of 2025, Inside Airbnb only serves the current snapshot per city — historical files have been removed. The analysis panel therefore uses simulated data that replicates the documented policy impact (NYC listings −81% post-LL18, control cities stable) and the correct panel structure. The causal design, identification strategy, and all methods are unchanged; the underlying numbers are synthetic. See `scripts/generate_data.py` for the DGP.

---

## Causal question

What is the effect of short-term rental regulation on market outcomes — listing counts, prices, availability, and room-type composition?

| Estimand | Method |
|----------|--------|
| ATT (NYC post LL18) | Two-period DiD + event study |
| ATT (Florence historic centre ban) | Synthetic control |
| Cohort-specific ATTs | Callaway-Sant'Anna staggered DiD |
| Dynamic effects | Event study leads and lags |

---

## Data

**Source:** [Inside Airbnb](http://insideairbnb.com/get-the-data/) — public listing snapshots, free for non-commercial use.

**Cities:**

| City | Role | Policy |
|------|------|--------|
| New York City | Treated | Local Law 18, Sep 2023 |
| Florence | Treated | Historic centre STR ban, Oct 2023 |
| Amsterdam | Control | Cap pre-dates panel |
| Lisbon | Control | No major shock in window |
| Vienna | Control | No major shock in window |
| Barcelona | Control | Moratorium announced but not enforced in window |

**Simulated panel (default — runs out of the box):**
```bash
python scripts/generate_data.py   # writes data/processed/city_month_panel.parquet
```

**Real data (if Inside Airbnb restores historical access):**
```bash
python scripts/download_inside_airbnb.py   # pulls snapshots to data/raw/
python scripts/build_real_panel.py          # aggregates to city-month panel
# Then update DATA_FILE in each notebook to city_month_panel_real.parquet
```

The panel grain is city × month with four primary outcomes: `log_listings`, `mean_price_usd`, `availability_rate`, `entire_home_share`.

Treatment dates and policy notes are in `data/regulations.csv`.

---

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `00_data_audit` | Load panel, describe cities, check balance |
| `02_eda_nyc` | NYC pre/post visualization and descriptives |
| `03_did_two_period_nyc` | Two-period DiD: pre/post Sep 2023 |
| `04_event_study_nyc` | Leads and lags around LL18 enforcement |
| `05_staggered_did` | Callaway-Sant'Anna across NYC and Florence |
| `06_synthetic_control` | Florence vs donor pool (Abadie weights) |
| `07_placebo_tests` | Fake treatment dates and fake treated cities |
| `99_robustness` | Alternative controls, outcomes, specifications |

---

## Identification

See [METHODOLOGY.md](METHODOLOGY.md) for the full write-up.

The core design exploits the fact that regulatory enforcement dates vary across cities and are driven by local political processes largely independent of short-term rental market trends. NYC's LL18 is particularly clean because enforcement was abrupt — hosts had to register in person by a hard deadline, and Airbnb de-listed non-compliant listings automatically.

Key assumptions: parallel trends (pre-regulation trends similar across cities), no anticipation of enforcement date (some NYC pre-announcement coverage violates this slightly — discussed in notebook 04), and SUTVA (cross-city spillovers unlikely given distinct tourist markets).

---

## Stack

```
pandas, numpy, pyarrow, statsmodels, linearmodels, matplotlib, seaborn
```

Staggered DiD: `linearmodels` TWFE + manual Callaway-Sant'Anna implementation.
Synthetic control: Abadie (2010) weights via `scipy.optimize`.

---

## Related

This project is part of a five-project causal inference portfolio. See the [repo root](../) for the full index.
