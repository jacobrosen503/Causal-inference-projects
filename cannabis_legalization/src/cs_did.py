"""Callaway & Sant'Anna (2021) staggered difference-in-differences.

A correct, dependency-free implementation of the group-time average treatment
effect ATT(g, t), with event-study and overall aggregations and a
state-clustered multiplier bootstrap for inference.

This is NOT a TWFE regression. It builds the estimator from C&S's 2x2 blocks:

    ATT(g, t) = [ E(Y_t - Y_{g-1} | G = g) ]            (treated cohort change)
              - [ E(Y_t - Y_{g-1} | C)     ]            (clean control change)

where the comparison group C is either the never-treated units or the
not-yet-treated units (G > t). The base period is the period just before
cohort g is treated (g - 1), so pre-treatment ATT(g, t) for t < g are valid
placebo / parallel-trends checks rather than mechanical zeros.

Reference: Callaway, B. & Sant'Anna, P. (2021), "Difference-in-Differences with
Multiple Time Periods", Journal of Econometrics 225(2), 200-230.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["att_gt", "aggregate_event_study", "aggregate_overall", "cs_did"]


def _panel_matrix(df, unit, time, outcome):
    """Return a (unit x time) wide outcome matrix and the cohort per unit."""
    wide = df.pivot_table(index=unit, columns=time, values=outcome, aggfunc="mean")
    return wide


def att_gt(
    df: pd.DataFrame,
    unit: str,
    time: str,
    outcome: str,
    cohort: str,
    control_group: str = "notyettreated",
):
    """Compute ATT(g, t) for every treated cohort g and period t.

    Parameters
    ----------
    df : long panel with one row per (unit, time)
    cohort : column giving each unit's first-treatment period; never-treated
             units must be coded as NaN or 0.
    control_group : "notyettreated" (default) or "nevertreated".

    Returns
    -------
    DataFrame with columns [cohort, time, event_time, att, n_treated].
    """
    d = df[[unit, time, outcome, cohort]].copy()
    d[cohort] = d[cohort].fillna(0)

    wide = _panel_matrix(d, unit, time, outcome)
    cohort_of = d.drop_duplicates(unit).set_index(unit)[cohort]
    cohort_of = cohort_of.reindex(wide.index)

    periods = sorted(wide.columns)
    treated_cohorts = sorted(c for c in cohort_of.unique() if c != 0 and c in periods)

    rows = []
    for g in treated_cohorts:
        base = g - 1
        if base not in wide.columns:
            continue
        treated_mask = (cohort_of == g).values
        if treated_mask.sum() == 0:
            continue

        for t in periods:
            if t == base:
                continue

            # Comparison group selection
            if control_group == "nevertreated":
                ctrl_mask = (cohort_of == 0).values
            else:  # not-yet-treated by period max(t, base): never-treated OR cohort > t
                ref = max(t, g)
                ctrl_mask = ((cohort_of == 0) | (cohort_of > ref)).values
            ctrl_mask = ctrl_mask & ~treated_mask
            if ctrl_mask.sum() == 0:
                continue

            yt = wide[t].values
            yb = wide[base].values
            ok = ~np.isnan(yt) & ~np.isnan(yb)

            tr = treated_mask & ok
            ct = ctrl_mask & ok
            if tr.sum() == 0 or ct.sum() == 0:
                continue

            d_treat = (yt[tr] - yb[tr]).mean()
            d_ctrl = (yt[ct] - yb[ct]).mean()
            rows.append({
                "cohort": int(g),
                "time": int(t),
                "event_time": int(t - g),
                "att": float(d_treat - d_ctrl),
                "n_treated": int(tr.sum()),
            })

    return pd.DataFrame(rows)


def aggregate_event_study(att_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate ATT(g,t) into dynamic effects by event time (cohort-size weighted)."""
    out = []
    for e, grp in att_df.groupby("event_time"):
        w = grp["n_treated"] / grp["n_treated"].sum()
        out.append({"event_time": int(e), "att": float((grp["att"] * w).sum())})
    return pd.DataFrame(out).sort_values("event_time").reset_index(drop=True)


def aggregate_overall(att_df: pd.DataFrame) -> float:
    """Overall ATT: cohort-size-weighted average of post-treatment ATT(g,t), t >= g."""
    post = att_df[att_df["event_time"] >= 0]
    if post.empty:
        return np.nan
    w = post["n_treated"] / post["n_treated"].sum()
    return float((post["att"] * w).sum())


def cs_did(
    df: pd.DataFrame,
    unit: str,
    time: str,
    outcome: str,
    cohort: str,
    control_group: str = "notyettreated",
    n_boot: int = 500,
    seed: int = 42,
):
    """Full C-S estimator with a unit-clustered bootstrap.

    Returns
    -------
    dict with keys:
      att_gt        : DataFrame of ATT(g,t)
      event_study   : DataFrame [event_time, att, se, ci_lo, ci_hi]
      overall_att   : float
      overall_se    : float
      overall_ci    : (lo, hi)
    """
    point_gt = att_gt(df, unit, time, outcome, cohort, control_group)
    point_es = aggregate_event_study(point_gt)
    point_overall = aggregate_overall(point_gt)

    units = df[unit].unique()
    rng = np.random.default_rng(seed)

    es_boot = {e: [] for e in point_es["event_time"]}
    overall_boot = []

    for _ in range(n_boot):
        samp = rng.choice(units, size=len(units), replace=True)
        # Build resampled panel; relabel duplicated units so they are distinct clusters
        parts = []
        for k, u in enumerate(samp):
            sub = df[df[unit] == u].copy()
            sub[unit] = f"{u}__{k}"
            sub["_cohort_keep"] = sub[cohort]
            parts.append(sub)
        bdf = pd.concat(parts, ignore_index=True)

        b_gt = att_gt(bdf, unit, time, outcome, cohort, control_group)
        if b_gt.empty:
            continue
        b_es = aggregate_event_study(b_gt)
        for _, r in b_es.iterrows():
            if r["event_time"] in es_boot:
                es_boot[r["event_time"]].append(r["att"])
        overall_boot.append(aggregate_overall(b_gt))

    # Assemble event-study CIs
    es_rows = []
    for _, r in point_es.iterrows():
        e = r["event_time"]
        draws = np.array(es_boot.get(e, []))
        if len(draws) > 1:
            se = float(np.nanstd(draws, ddof=1))
            lo, hi = np.nanpercentile(draws, [2.5, 97.5])
        else:
            se, lo, hi = np.nan, np.nan, np.nan
        es_rows.append({"event_time": int(e), "att": float(r["att"]),
                        "se": se, "ci_lo": float(lo), "ci_hi": float(hi)})
    event_study = pd.DataFrame(es_rows).sort_values("event_time").reset_index(drop=True)

    ob = np.array([x for x in overall_boot if not np.isnan(x)])
    overall_se = float(np.std(ob, ddof=1)) if len(ob) > 1 else np.nan
    overall_ci = (float(np.percentile(ob, 2.5)), float(np.percentile(ob, 97.5))) if len(ob) > 1 else (np.nan, np.nan)

    return {
        "att_gt": point_gt,
        "event_study": event_study,
        "overall_att": point_overall,
        "overall_se": overall_se,
        "overall_ci": overall_ci,
    }
