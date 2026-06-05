"""Generate the synthetic city-month Airbnb panel.

This creates a reproducible synthetic dataset calibrated to public reporting
on NYC Local Law 18 and Florence's historic-centre STR ban.

To use REAL Inside Airbnb data instead:
    python scripts/download_inside_airbnb.py   (run locally in Cursor)
    python scripts/build_real_panel.py

Usage (synthetic):
    python scripts/generate_data.py
    python scripts/generate_data.py --config path/to/custom.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from simulate_panel import SimulationConfig, simulate_airbnb_panel, write_outputs


def sanity_checks(panel) -> None:
    import numpy as np

    print("\n── Sanity checks ──────────────────────────────────────────────")
    for city in panel["city"].unique():
        c = panel[panel["city"] == city]
        pre  = c[~c["post"]]["log_listings"].mean()
        post = c[c["post"]]["log_listings"].mean()
        diff = post - pre if c["post"].any() else float("nan")
        tag  = f"  ATT(log_listings) ≈ {diff:+.2f}" if not np.isnan(diff) else "  (control)"
        print(f"  {city:<20} {tag}")

    nyc   = panel[panel["city"] == "New York City"]
    pre_l = nyc[nyc["month"] < "2023-09-01"]["listings"].mean()
    post_l = nyc[nyc["month"] >= "2023-09-01"]["listings"].mean()
    print(f"\n  NYC listings: {pre_l:,.0f} pre → {post_l:,.0f} post LL18")
    print(f"  Pct change  : {(post_l/pre_l - 1)*100:+.0f}%  (expect ≈ -80%)")
    print("────────────────────────────────────────────────────────────────\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    config_path = (
        Path(args.config) if args.config
        else PROJECT_ROOT / "config" / "sim_params.yaml"
    )

    print(f"Config: {config_path}")
    cfg = SimulationConfig.from_yaml(config_path)
    print(f"  seed={cfg.seed}  cities={len(cfg.cities)}  months={cfg.n_months}")

    panel = simulate_airbnb_panel(cfg)

    output_dir = PROJECT_ROOT / "data" / "processed"
    write_outputs(panel, output_dir)

    sanity_checks(panel)
    print("Done. Run notebooks in order starting with 00_data_audit.ipynb")


if __name__ == "__main__":
    main()
