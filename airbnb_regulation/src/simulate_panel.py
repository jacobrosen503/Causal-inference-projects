"""
Synthetic city-month Airbnb panel — data generating process.

Calibrated to publicly reported figures:
  - NYC Local Law 18 (Sep 2023): listings fell ~80% (22k → ~4k)
  - Florence historic centre ban (Oct 2023): ~40% listing decline
  - Price, availability, and entire-home-share effects from STR literature

Structural equations
--------------------
log_listings_ct  = city_FE_c + month_FE_t + season_t + β_treat * D_ct + ε_ct
log_price_ct     = city_FE_c + month_FE_t + γ_treat * D_ct + ε_ct
availability_ct  = city_FE_c + month_FE_t + season_t + δ_treat * D_ct + ε_ct
entire_home_ct   = city_FE_c + month_FE_t + η_treat * D_ct + ε_ct

D_ct = 1 if city c is treated at or after its enforcement month.

Usage
-----
    from simulate_panel import SimulationConfig, simulate_airbnb_panel, write_outputs
    cfg = SimulationConfig.from_yaml("config/sim_params.yaml")
    panel = simulate_airbnb_panel(cfg)
    write_outputs(panel, Path("data/processed"))
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml


@dataclass
class CityConfig:
    name: str
    country: str
    baseline_listings: int
    baseline_price_usd: float
    baseline_availability: float
    baseline_entire_home_share: float
    treat_month: Optional[str]       # "YYYY-MM-DD" or None
    treat_col: Optional[str]


@dataclass
class EffectConfig:
    nyc_log_listings: float = -1.65
    nyc_log_price: float = 0.08
    nyc_availability: float = -0.12
    nyc_entire_home_share: float = -0.28

    florence_log_listings: float = -0.51
    florence_log_price: float = 0.04
    florence_availability: float = -0.06
    florence_entire_home_share: float = -0.15


@dataclass
class SimulationConfig:
    seed: int = 42
    start_month: str = "2021-01-01"
    n_months: int = 48
    cities: list[CityConfig] = field(default_factory=list)
    effects: EffectConfig = field(default_factory=EffectConfig)
    listing_noise_sd: float = 0.04
    price_noise_sd: float = 8.0
    seasonality_amplitude: float = 0.18

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SimulationConfig":
        with open(path) as f:
            raw = yaml.safe_load(f)

        cities = [
            CityConfig(
                name=c["name"],
                country=c["country"],
                baseline_listings=int(c["baseline_listings"]),
                baseline_price_usd=float(c["baseline_price_usd"]),
                baseline_availability=float(c["baseline_availability"]),
                baseline_entire_home_share=float(c["baseline_entire_home_share"]),
                treat_month=c.get("treat_month"),
                treat_col=c.get("treat_col"),
            )
            for c in raw.get("cities", [])
        ]

        eff_raw = raw.get("effects", {})
        effects = EffectConfig(
            nyc_log_listings=eff_raw.get("nyc_log_listings", -1.65),
            nyc_log_price=eff_raw.get("nyc_log_price", 0.08),
            nyc_availability=eff_raw.get("nyc_availability", -0.12),
            nyc_entire_home_share=eff_raw.get("nyc_entire_home_share", -0.28),
            florence_log_listings=eff_raw.get("florence_log_listings", -0.51),
            florence_log_price=eff_raw.get("florence_log_price", 0.04),
            florence_availability=eff_raw.get("florence_availability", -0.06),
            florence_entire_home_share=eff_raw.get("florence_entire_home_share", -0.15),
        )

        return cls(
            seed=int(raw.get("seed", 42)),
            start_month=str(raw.get("start_month", "2021-01-01")),
            n_months=int(raw.get("n_months", 48)),
            cities=cities,
            effects=effects,
            listing_noise_sd=float(raw.get("listing_noise_sd", 0.04)),
            price_noise_sd=float(raw.get("price_noise_sd", 8.0)),
            seasonality_amplitude=float(raw.get("seasonality_amplitude", 0.18)),
        )


def _seasonality(month: int, amplitude: float) -> float:
    """Summer peak (July = max), winter trough (Jan = min)."""
    return amplitude * math.sin(2 * math.pi * (month - 3) / 12)


def simulate_airbnb_panel(cfg: SimulationConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)

    months = pd.date_range(cfg.start_month, periods=cfg.n_months, freq="MS")

    rows = []
    for city in cfg.cities:
        treat_date = pd.Timestamp(str(city.treat_month)) if city.treat_month else None
        log_base = math.log(city.baseline_listings)

        for i, month in enumerate(months):
            # Post-treatment indicator
            post = (treat_date is not None) and (month >= treat_date)

            # Seasonality
            season = _seasonality(month.month, cfg.seasonality_amplitude)

            # Slow city-level trend (±1% per year)
            trend = rng.normal(0, 0.003)

            # Treatment city identifier for effect lookup
            city_key = city.name.lower().replace(" ", "_")

            # --- log_listings ---
            treat_effect_log_listings = 0.0
            if post:
                if city_key == "new_york_city":
                    treat_effect_log_listings = cfg.effects.nyc_log_listings
                elif city_key == "florence":
                    treat_effect_log_listings = cfg.effects.florence_log_listings

            log_listings = (
                log_base
                + season
                + trend * i
                + treat_effect_log_listings
                + rng.normal(0, cfg.listing_noise_sd)
            )

            # --- mean_price ---
            treat_effect_price = 0.0
            if post:
                if city_key == "new_york_city":
                    treat_effect_price = cfg.effects.nyc_log_price * city.baseline_price_usd
                elif city_key == "florence":
                    treat_effect_price = cfg.effects.florence_log_price * city.baseline_price_usd

            mean_price = (
                city.baseline_price_usd
                + season * 40        # price seasonality
                + treat_effect_price
                + rng.normal(0, cfg.price_noise_sd)
            )

            # --- availability_rate ---
            treat_effect_avail = 0.0
            if post:
                if city_key == "new_york_city":
                    treat_effect_avail = cfg.effects.nyc_availability
                elif city_key == "florence":
                    treat_effect_avail = cfg.effects.florence_availability

            availability_rate = np.clip(
                city.baseline_availability
                + season * 0.08
                + treat_effect_avail
                + rng.normal(0, 0.02),
                0.05, 0.95
            )

            # --- entire_home_share ---
            treat_effect_eh = 0.0
            if post:
                if city_key == "new_york_city":
                    treat_effect_eh = cfg.effects.nyc_entire_home_share
                elif city_key == "florence":
                    treat_effect_eh = cfg.effects.florence_entire_home_share

            entire_home_share = np.clip(
                city.baseline_entire_home_share
                + treat_effect_eh
                + rng.normal(0, 0.015),
                0.05, 0.98
            )

            rows.append({
                "city":                city.name,
                "country":             city.country,
                "month":               month,
                "year_month":          month.strftime("%Y-%m"),
                "month_idx":           i,
                "is_treated_city":     treat_date is not None,
                "post":                post,
                "treat_col":           city.treat_col or "",
                "log_listings":        round(log_listings, 4),
                "listings":            max(1, round(math.exp(log_listings))),
                "mean_price_usd":      round(max(20.0, mean_price), 2),
                "log_price":           round(math.log(max(20.0, mean_price)), 4),
                "availability_rate":   round(availability_rate, 4),
                "entire_home_share":   round(entire_home_share, 4),
                "is_simulated":        True,
            })

    panel = pd.DataFrame(rows)
    panel["month"] = pd.to_datetime(panel["month"])
    return panel


def write_outputs(panel: pd.DataFrame, output_dir: Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_dir / "city_month_panel.parquet", index=False)
    panel.to_csv(output_dir / "city_month_panel.csv", index=False)
    print(f"Written: city_month_panel  ({len(panel):,} rows, {panel['city'].nunique()} cities)")
