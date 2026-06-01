"""Semi-synthetic cruise ship × month panel for causal methods demos.

All rows are simulated. No real operator, ship, or booking data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


REGIONS = ["Caribbean", "Mediterranean", "Alaska", "Northern_Europe", "Asia_Pacific"]
BRAND_TIERS = ["economy", "premium", "luxury"]


@dataclass(frozen=True)
class SimulationConfig:
    seed: int = 42
    n_ships: int = 800
    n_months: int = 48
    start_month: str = "2021-01-01"
    beta_within_log_rpb: float = 0.06
    scale_confounding_strength: float = 0.35
    frac_ships_with_category_event: float = 0.18
    event_month_min: int = 12
    event_month_max: int = 36
    min_categories: int = 3
    max_categories: int = 16

    @classmethod
    def from_yaml(cls, path: Path | str) -> SimulationConfig:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return cls(**{k: raw[k] for k in cls.__dataclass_fields__ if k in raw})


def _month_index_to_date(start: pd.Timestamp, month_idx: int) -> pd.Timestamp:
    return start + pd.DateOffset(months=int(month_idx))


def simulate_cruise_panel(cfg: SimulationConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (ship_month_panel, category_change_events)."""
    rng = np.random.default_rng(cfg.seed)
    start = pd.Timestamp(cfg.start_month)

    ship_ids = [f"SHIP_{i:04d}" for i in range(cfg.n_ships)]
    ship_scale = rng.normal(0, 1, size=cfg.n_ships)

    # Observable ship metadata (partial proxy for latent scale)
    brand_tier_idx = np.clip(
        (ship_scale * 0.9 + rng.normal(0, 0.6, cfg.n_ships)).astype(int) + 1,
        0,
        len(BRAND_TIERS) - 1,
    )
    region_idx = rng.integers(0, len(REGIONS), size=cfg.n_ships)
    berth_capacity = np.clip(
        (800 + 350 * ship_scale + rng.normal(0, 120, cfg.n_ships)).astype(int),
        400,
        6000,
    )

    # Ship fixed effect on log revenue per berth (confounded with category count)
    ship_fe = (
        4.2
        + cfg.scale_confounding_strength * ship_scale
        + rng.normal(0, 0.15, cfg.n_ships)
    )

    # Baseline cabin categories (before any refit event)
    base_categories = np.clip(
        np.round(6 + 2.2 * ship_scale + rng.poisson(1.0, cfg.n_ships)).astype(int),
        cfg.min_categories,
        cfg.max_categories,
    )

    # Assign category-change events
    n_event_ships = int(round(cfg.frac_ships_with_category_event * cfg.n_ships))
    event_ship_idx = rng.choice(cfg.n_ships, size=n_event_ships, replace=False)
    event_month = rng.integers(cfg.event_month_min, cfg.event_month_max + 1, size=n_event_ships)
    event_delta = rng.choice([1, 2], size=n_event_ships)

    event_map: dict[int, tuple[int, int]] = {
        int(idx): (int(m), int(d)) for idx, m, d in zip(event_ship_idx, event_month, event_delta)
    }

    events_rows: list[dict[str, Any]] = []
    for idx in event_ship_idx:
        m_idx, delta = event_map[int(idx)]
        pre = int(base_categories[idx])
        post = int(np.clip(pre + delta, cfg.min_categories, cfg.max_categories))
        events_rows.append(
            {
                "ship_id": ship_ids[idx],
                "event_month": _month_index_to_date(start, m_idx),
                "event_month_idx": m_idx,
                "delta_categories": post - pre,
                "categories_before": pre,
                "categories_after": post,
                "event_type": "cabin_mix_expansion",
            }
        )
    events = pd.DataFrame(events_rows)

    rows: list[dict[str, Any]] = []
    global_month_fe = rng.normal(0, 0.04, cfg.n_months)
    seasonality = 0.03 * np.sin(2 * np.pi * np.arange(cfg.n_months) / 12)

    for s_idx, ship_id in enumerate(ship_ids):
        pre_cats = int(base_categories[s_idx])
        post_cats = pre_cats
        event_m_idx: int | None = None
        if s_idx in event_map:
            event_m_idx, delta = event_map[s_idx]
            post_cats = int(np.clip(pre_cats + delta, cfg.min_categories, cfg.max_categories))

        for t in range(cfg.n_months):
            month_date = _month_index_to_date(start, t)
            categories = post_cats if (event_m_idx is not None and t >= event_m_idx) else pre_cats

            month_fe = global_month_fe[t] + seasonality[t]
            eps = rng.normal(0, 0.08)
            log_rpb = (
                ship_fe[s_idx]
                + month_fe
                + cfg.beta_within_log_rpb * categories
                + eps
            )
            revenue_per_berth = float(np.exp(log_rpb))
            occupancy_pct = float(
                np.clip(
                    0.72
                    + 0.06 * ship_scale[s_idx]
                    + 0.015 * np.sin(2 * np.pi * t / 12)
                    + rng.normal(0, 0.04),
                    0.35,
                    0.98,
                )
            )
            # Analog to "configured vs realized" ancillary capture (noisy, scales with sophistication)
            ancillary_capture_rate = float(
                np.clip(
                    0.55
                    + 0.08 * ship_scale[s_idx]
                    - 0.01 * categories
                    + rng.normal(0, 0.05),
                    0.2,
                    0.95,
                )
            )

            months_since_event: int | None = None
            if event_m_idx is not None:
                months_since_event = t - event_m_idx

            rows.append(
                {
                    "ship_id": ship_id,
                    "month": month_date,
                    "year_month": month_date.strftime("%Y-%m"),
                    "cabin_category_count": categories,
                    "berth_capacity": int(berth_capacity[s_idx]),
                    "brand_tier": BRAND_TIERS[brand_tier_idx[s_idx]],
                    "sailing_region": REGIONS[region_idx[s_idx]],
                    "occupancy_pct": occupancy_pct,
                    "revenue_per_berth": revenue_per_berth,
                    "log_revenue_per_berth": log_rpb,
                    "ancillary_capture_rate": ancillary_capture_rate,
                    "had_category_change": event_m_idx is not None,
                    "post_category_change": event_m_idx is not None and t >= event_m_idx,
                    "months_since_category_change": months_since_event,
                    "is_simulated": True,
                }
            )

    panel = pd.DataFrame(rows)
    panel["month"] = pd.to_datetime(panel["month"])
    events["event_month"] = pd.to_datetime(events["event_month"])
    return panel, events


def load_config(project_root: Path | None = None) -> SimulationConfig:
    root = project_root or Path(__file__).resolve().parents[1]
    return SimulationConfig.from_yaml(root / "config" / "sim_params.yaml")


def write_outputs(
    panel: pd.DataFrame,
    events: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    panel_path = output_dir / "ship_month_panel.parquet"
    events_path = output_dir / "category_change_events.parquet"
    panel.to_parquet(panel_path, index=False)
    events.to_parquet(events_path, index=False)
    panel.to_csv(output_dir / "ship_month_panel.csv", index=False)
    events.to_csv(output_dir / "category_change_events.csv", index=False)
