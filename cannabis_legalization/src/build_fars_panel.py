"""Build state-year traffic fatality panel from CDAN query export.

Expected input: data/raw/fars/fars_state_year_raw.csv
  - Format: wide table exported from https://cdan.dot.gov/query
  - Row per state, column per year (2010-2022), values are fatality counts
  - First column is state name (no header); last column is "Total"

Usage:
    python src/build_fars_panel.py

Output: data/processed/fars_state_year.parquet

Optional: add Census population file to data/raw/census/state_population_2010_2022.csv
  for per-100k rates. Download from:
  https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FILE  = PROJECT_ROOT / "data" / "raw" / "fars" / "fars_state_year_raw.csv"
POP_FILE  = PROJECT_ROOT / "data" / "raw" / "census" / "state_population_2010_2022.csv"
OUT_DIR   = PROJECT_ROOT / "data" / "processed"
CODEBOOK  = PROJECT_ROOT / "data" / "codebooks" / "state_legalization_dates.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_cdan_wide(path: Path) -> pd.DataFrame:
    """Load CDAN wide export and melt to long format."""
    raw = pd.read_csv(path, header=0)
    raw.columns = ["state"] + [str(c) for c in raw.columns[1:]]
    raw = raw[[c for c in raw.columns if c != "Total"]]

    panel = raw.melt(id_vars="state", var_name="year", value_name="total_fatalities")
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")
    panel["total_fatalities"] = (
        panel["total_fatalities"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    panel = panel.dropna(subset=["state", "year", "total_fatalities"])
    panel = panel[panel["state"].str.strip() != ""]
    return panel


def merge_population(panel: pd.DataFrame) -> pd.DataFrame:
    """Merge Census population if available; skip silently if not."""
    if not POP_FILE.exists():
        print(f"Note: Census population file not found at {POP_FILE}")
        print("      Per-100k rates will not be computed.")
        print("      Download from: https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html")
        panel["population"] = np.nan
        return panel

    pop = pd.read_csv(POP_FILE)
    pop.columns = [c.lower().strip() for c in pop.columns]
    panel = panel.merge(pop, on=["state", "year"], how="left")
    panel["total_fatalities_per_100k"] = panel["total_fatalities"] / panel["population"] * 100_000
    print(f"Population data merged. Per-100k rates computed.")
    return panel


def build_panel() -> pd.DataFrame:
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"{RAW_FILE} not found.\n"
            "Download from https://cdan.dot.gov/query:\n"
            "  Rows: State | Columns: Crash Date (Year) | Years: 2010-2022\n"
            "  Export as CSV -> save to data/raw/fars/fars_state_year_raw.csv"
        )

    print(f"Loading: {RAW_FILE}")
    panel = load_cdan_wide(RAW_FILE)
    print(f"  {panel.shape[0]} rows | {panel['state'].nunique()} states | years {panel['year'].min()}-{panel['year'].max()}")

    panel = merge_population(panel)

    # Merge legalization dates
    leg = pd.read_csv(CODEBOOK)
    leg["retail_sales_year"] = pd.to_numeric(leg["retail_sales_year"], errors="coerce")

    unmatched = set(panel["state"].unique()) - set(leg["state"].unique())
    if unmatched:
        print(f"  Warning: no legalization info for: {unmatched}")

    panel = panel.merge(
        leg[["state", "state_abbr", "fips", "retail_sales_year"]],
        on="state", how="left"
    )

    # Treatment indicators
    panel["treated"] = panel["retail_sales_year"].notna()
    panel["post"]    = panel["treated"] & (panel["year"] >= panel["retail_sales_year"])
    panel["years_since_legalization"] = np.where(
        panel["treated"],
        panel["year"] - panel["retail_sales_year"],
        np.nan
    )

    panel = panel.sort_values(["state", "year"]).reset_index(drop=True)

    out = OUT_DIR / "fars_state_year.parquet"
    panel.to_parquet(out, index=False)
    print(f"Written: {out}")

    # Quick sanity check
    co = panel[panel["state"] == "Colorado"]
    print(f"\nColorado check (legalized 2014):")
    print(co[["year","total_fatalities","post"]].to_string(index=False))
    return panel


if __name__ == "__main__":
    build_panel()
