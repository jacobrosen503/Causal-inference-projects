"""
build_dataset.py
----------------
Merges topic labels with host parsing and derived features.
Run AFTER label_topics.py.

Usage:
    python3 build_dataset.py

Writes: analysis_dataset.csv
"""

import json, re
import pandas as pd
import numpy as np

HOSTS = ["Krystal", "Saagar", "Ryan", "Emily", "Kyle"]


def parse_hosts(description: str) -> list[str]:
    if not description:
        return []
    first_line = description.split("\n")[0]
    return sorted(h for h in HOSTS if h in first_line)


def main():
    with open("labeled.json") as f:
        records = json.load(f)

    df = pd.DataFrame(records)

    # --- Date / time features ---
    df["upload_date"] = pd.to_datetime(df["upload_date"], format="%Y%m%d")
    df["date"]        = df["upload_date"].dt.date.astype(str)
    df["dow"]         = df["upload_date"].dt.day_name()
    df["dow_num"]     = df["upload_date"].dt.dayofweek  # 0=Mon

    # --- Host parsing ---
    df["hosts"]       = df["description"].apply(parse_hosts)
    df["host_pair"]   = df["hosts"].apply(lambda x: " & ".join(x) if x else "Unknown")
    df["n_hosts"]     = df["hosts"].apply(len)
    df["has_krystal"] = df["hosts"].apply(lambda x: "Krystal" in x).astype(int)
    df["has_saagar"]  = df["hosts"].apply(lambda x: "Saagar"  in x).astype(int)
    df["has_ryan"]    = df["hosts"].apply(lambda x: "Ryan"    in x).astype(int)
    df["has_emily"]   = df["hosts"].apply(lambda x: "Emily"   in x).astype(int)

    # --- Outcome ---
    df["log_views"]   = np.log(df["view_count"].clip(lower=1))
    df["log_likes"]   = np.log(df["like_count"].clip(lower=1))
    df["log_duration"]= np.log(df["duration"].clip(lower=1))

    # --- Within-day position (rank by upload timestamp within date) ---
    # Sort within day by upload_date string (best proxy for publish order without timestamp)
    df = df.sort_values(["date", "upload_date"])
    df["segment_position"] = df.groupby("date").cumcount() + 1   # 1 = first video of the day
    df["segments_that_day"] = df.groupby("date")["date"].transform("count")

    # --- Filter to clean 2-host labels ---
    clean = df[df["n_hosts"] == 2].copy()

    # --- Save ---
    df.to_csv("analysis_dataset.csv", index=False)
    clean.to_csv("analysis_dataset_clean.csv", index=False)

    print(f"Full dataset:  {len(df)} rows → analysis_dataset.csv")
    print(f"Clean 2-host:  {len(clean)} rows → analysis_dataset_clean.csv")
    print(f"\nTopic counts:")
    print(clean["topic"].value_counts().to_string())
    print(f"\nHost pair counts:")
    print(clean["host_pair"].value_counts().to_string())
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique days: {df['date'].nunique()}")


if __name__ == "__main__":
    main()
