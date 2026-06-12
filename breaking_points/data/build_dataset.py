"""
build_dataset.py
----------------
Merges topic labels with host parsing and derived features.
Run AFTER fetch_metadata.py and label_topics.py.

Usage:
    python3 build_dataset.py

Writes: analysis_dataset.csv, analysis_dataset_clean.csv

Note on segment_position:
    Uses the `timestamp` field (Unix epoch, second-level precision) from
    raw_metadata.json to order segments within each day. This is the actual
    YouTube publish time, fetched per-video by fetch_metadata.py.
    If timestamp is missing for a video, it is sorted last within its day.
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
    # labeled.json has topic labels; raw_metadata.json has timestamps.
    # Merge on video id.
    with open("labeled.json") as f:
        labeled = json.load(f)
    with open("raw_metadata.json") as f:
        raw = json.load(f)

    ts_map = {r["id"]: r.get("timestamp") for r in raw}
    for rec in labeled:
        rec["timestamp"] = ts_map.get(rec["id"])

    df = pd.DataFrame(labeled)

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

    # --- Title sensationalism proxy ---
    # Caps ratio: fraction of alpha characters that are uppercase
    # Used as robustness control (see notebook 02)
    df["caps_ratio"] = df["title"].apply(
        lambda t: sum(1 for c in t if c.isupper()) / max(sum(1 for c in t if c.isalpha()), 1)
    )

    # --- Within-day position from real publish timestamps ---
    # timestamp = Unix epoch (second-level precision) from YouTube via yt-dlp.
    # Sort by timestamp within date; NaT / missing timestamps sort last.
    df["publish_ts"] = pd.to_numeric(df["timestamp"], errors="coerce")
    df = df.sort_values(["date", "publish_ts"], na_position="last")
    df["segment_position"]  = df.groupby("date").cumcount() + 1  # 1 = first published
    df["segments_that_day"] = df.groupby("date")["date"].transform("count")

    ts_coverage = df["publish_ts"].notna().sum()
    print(f"Timestamp coverage: {ts_coverage}/{len(df)} segments ({ts_coverage/len(df)*100:.1f}%)")

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
