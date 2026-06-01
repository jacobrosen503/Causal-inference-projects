"""Generate the semi-synthetic cruise panel.

All outputs go to data/processed/. Parquet is primary; CSV is a convenience copy.

Usage:
    python scripts/generate_data.py
    python scripts/generate_data.py --config path/to/custom_params.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make src/ importable regardless of working directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from simulate_panel import SimulationConfig, simulate_cruise_panel, write_outputs  # noqa: E402

import numpy as np  # noqa: E402


def sanity_checks(panel, events, cfg) -> None:
    """Print key DGP checks. Warn if anything looks off."""
    xs_corr = panel["cabin_category_count"].corr(panel["log_revenue_per_berth"])
    within_corrs = [
        grp["cabin_category_count"].corr(grp["log_revenue_per_berth"])
        for _, grp in panel.groupby("ship_id")
        if grp["cabin_category_count"].std() > 0
    ]
    within_corr = float(np.mean(within_corrs))

    print("\n── Sanity checks ──────────────────────────────────────────")
    print(f"  Cross-sectional corr(categories, log_rpb) = {xs_corr:.3f}   (expect ≈ 0.90)")
    print(f"  Mean within-ship corr                     = {within_corr:.3f}   (expect ≈ 0.08)")
    print(f"  True β (per category)                     = {cfg.beta_within_log_rpb}")
    print(f"  Treated ships                             = {events['ship_id'].nunique()}"
          f"  ({events['ship_id'].nunique() / panel['ship_id'].nunique() * 100:.1f}%)")

    if xs_corr < 0.80:
        print("  ⚠️  Cross-sectional corr lower than expected — check scale_confounding_strength")
    if abs(within_corr - cfg.beta_within_log_rpb) > 0.05:
        print("  ⚠️  Within-ship corr diverges from β — expected with noise at this sample size")
    print("────────────────────────────────────────────────────────────\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cruise cabin causal demo data")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to sim_params.yaml (default: config/sim_params.yaml)",
    )
    args = parser.parse_args()

    config_path = (
        Path(args.config) if args.config else PROJECT_ROOT / "config" / "sim_params.yaml"
    )

    print(f"Loading config from: {config_path}")
    cfg = SimulationConfig.from_yaml(config_path)
    print(f"  seed={cfg.seed}  n_ships={cfg.n_ships}  β={cfg.beta_within_log_rpb}")

    print("Simulating panel...")
    panel, events = simulate_cruise_panel(cfg)

    output_dir = PROJECT_ROOT / "data" / "processed"
    print(f"Writing outputs to: {output_dir}")
    write_outputs(panel, events, output_dir)

    print(f"  ship_month_panel:         {len(panel):>7,} rows")
    print(f"  category_change_events:   {len(events):>7,} rows")

    sanity_checks(panel, events, cfg)
    print("Done.")


if __name__ == "__main__":
    main()
