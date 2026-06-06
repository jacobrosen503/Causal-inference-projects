"""Combine Census NST-EST Excel files into a clean state-year population CSV.

Inputs (download from Census Bureau):
  data/raw/census/nst-est2020.xlsx      — 2010-2019 estimates
  data/raw/census/NST-EST2022-POP.xlsx  — 2020-2022 estimates

Download links:
  https://www2.census.gov/programs-surveys/popest/tables/2010-2020/state/totals/nst-est2020.xlsx
  https://www2.census.gov/programs-surveys/popest/tables/2020-2022/state/totals/NST-EST2022-POP.xlsx

Output: data/raw/census/state_population_2010_2022.csv

Usage:
    python scripts/build_census_pop.py
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW = PROJECT_ROOT / "data" / "raw" / "census"
RAW.mkdir(parents=True, exist_ok=True)


def parse_2010_2019(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, header=None)
    year_cols = {3: 2010, 4: 2011, 5: 2012, 6: 2013, 7: 2014,
                 8: 2015, 9: 2016, 10: 2017, 11: 2018, 12: 2019}
    data = df.iloc[4:, [0] + list(year_cols.keys())].copy()
    data.columns = ["state"] + [year_cols[c] for c in year_cols]
    data = data[data["state"].astype(str).str.startswith(".")]
    data["state"] = data["state"].str.lstrip(".")
    pop = data.melt(id_vars="state", var_name="year", value_name="population")
    pop["year"] = pop["year"].astype(int)
    pop["population"] = pd.to_numeric(pop["population"], errors="coerce")
    return pop


def parse_2020_2022(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, header=None)
    data = df.iloc[4:, [0, 2, 3, 4]].copy()
    data.columns = ["state", 2020, 2021, 2022]
    data = data[data["state"].astype(str).str.startswith(".")]
    data["state"] = data["state"].str.lstrip(".")
    pop = data.melt(id_vars="state", var_name="year", value_name="population")
    pop["year"] = pop["year"].astype(int)
    pop["population"] = pd.to_numeric(pop["population"], errors="coerce")
    return pop


def main():
    f1 = RAW / "nst-est2020.xlsx"
    f2 = RAW / "NST-EST2022-POP.xlsx"

    for f in [f1, f2]:
        if not f.exists():
            raise FileNotFoundError(f"{f} not found. See download links in script header.")

    pop = pd.concat([parse_2010_2019(f1), parse_2020_2022(f2)], ignore_index=True)
    pop = pop.dropna(subset=["state", "year", "population"])
    pop = pop[pop["population"] > 0]
    pop = pop.sort_values(["state", "year"]).reset_index(drop=True)

    out = RAW / "state_population_2010_2022.csv"
    pop.to_csv(out, index=False)
    print(f"Written: {out}  ({len(pop):,} rows, {pop['state'].nunique()} states)")


if __name__ == "__main__":
    main()
