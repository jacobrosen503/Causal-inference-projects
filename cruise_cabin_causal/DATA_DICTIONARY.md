# Data dictionary — semi-synthetic cruise panel

## `ship_month_panel`

| Column | Type | Description |
|--------|------|-------------|
| `ship_id` | string | Fake identifier `SHIP_0000` … |
| `month` | date | Month start date |
| `year_month` | string | `YYYY-MM` |
| `cabin_category_count` | int | Count of distinct cabin categories offered (treatment proxy) |
| `berth_capacity` | int | Simulated passenger berth capacity |
| `brand_tier` | category | `economy`, `premium`, `luxury` (partial scale proxy) |
| `sailing_region` | category | Simulated home region label |
| `occupancy_pct` | float | Simulated occupancy rate 0–1 |
| `revenue_per_berth` | float | Simulated revenue per available berth (USD-like index) |
| `log_revenue_per_berth` | float | Primary outcome for regressions |
| `ancillary_capture_rate` | float | Share of configured ancillary revenue captured (leakage analog) |
| `had_category_change` | bool | Ship ever receives a sustained category-mix expansion |
| `post_category_change` | bool | Month is on/after refit event |
| `months_since_category_change` | int/null | Months since event; null if never treated |
| `is_simulated` | bool | Always `True` |

## `category_change_events`

| Column | Type | Description |
|--------|------|-------------|
| `ship_id` | string | Treated ship |
| `event_month` | date | First month with new category count |
| `event_month_idx` | int | 0-based month index in panel |
| `delta_categories` | int | Change in category count (+1 or +2) |
| `categories_before` | int | Pre-event count |
| `categories_after` | int | Post-event count |
| `event_type` | string | Always `cabin_mix_expansion` |

## DGP summary (known ground truth)

- Latent **ship scale** shifts both baseline categories and baseline revenue (confounding).
- True within-ship effect: **`beta_within_log_rpb` per category** on `log_revenue_per_berth` (see `config/sim_params.yaml`, default 0.06).
- ~18% of ships receive a random **refit** (category expansion) between months 12–36.
