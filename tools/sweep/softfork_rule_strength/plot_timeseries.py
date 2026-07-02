#!/usr/bin/env python3
"""
Time series plots for the softfork_rule_strength sweep.

Produces three figures, each showing a fixed (E, C) anchor across all 6 p values:
  1. C=0.30, E=0.65  — v27 wins at p≤0.50, contested at p≥0.75
  2. C=0.40, E=0.74  — v27 wins at p≤0.75, v26 wins at p=1.00
  3. C=0.50, E=0.78  — baseline inversion (contested at p=0.00) resolved at p≥0.10

Each figure has 4 panels:
  (a) v27 hashrate share over time
  (b) Price divergence (v27_price - v26_price) over time
  (c) v27 economic share over time
  (d) Chainwork ratio (v27 / v26) over time

Usage:
    python tools/sweep/softfork_rule_strength/plot_timeseries.py
"""

import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

BASE  = Path(__file__).parent / "results"
OUT   = Path(__file__).parent / "results" / "analysis"
META  = Path(__file__).parent / "results" / "analysis" / "sweep_data.csv"

P_VALS = [0.00, 0.10, 0.25, 0.50, 0.75, 1.00]
P_LABELS = {
    0.00: "p=0.00 strict",
    0.10: "p=0.10 (90% violation)",
    0.25: "p=0.25 (75% violation)",
    0.50: "p=0.50 (50% violation)",
    0.75: "p=0.75 (25% violation)",
    1.00: "p=1.00 permissive",
}
P_COLORS = plt.cm.plasma(np.linspace(0.05, 0.92, len(P_VALS)))

OUTCOME_MARKER = {
    "v27_dominant": "▲ v27 wins",
    "v26_dominant": "▼ v26 wins",
    "contested":    "● contested",
}


def load_meta():
    """Return dict (p, E, C) -> (scenario_id, outcome)."""
    mapping = {}
    with open(META, newline="") as f:
        for r in csv.DictReader(f):
            key = (round(float(r["v26_acceptance_probability"]), 2),
                   round(float(r["economic_split"]), 2),
                   round(float(r["pool_committed_split"]), 3))
            mapping[key] = (r["scenario_id"], r["outcome"])
    return mapping


def load_ts(scenario_id: str) -> list[dict]:
    path = BASE / scenario_id / "time_series.csv"
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            parsed = {}
            for k, v in r.items():
                try:
                    parsed[k] = float(v) if v not in ("None", "") else np.nan
                except ValueError:
                    parsed[k] = v
            rows.append(parsed)
    return rows


def ts_col(rows, col):
    t = np.array([r["timestamps"] / 60 for r in rows])   # → minutes
    v = np.array([r.get(col, np.nan) for r in rows])
    return t, v


def chainwork_ratio(rows):
    t = np.array([r["timestamps"] / 60 for r in rows])
    cw27 = np.array([r.get("v27_chainwork", np.nan) for r in rows])
    cw26 = np.array([r.get("v26_chainwork", np.nan) for r in rows])
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(cw26 > 0, cw27 / cw26, np.nan)
    return t, ratio


def price_gap(rows):
    t = np.array([r["timestamps"] / 60 for r in rows])
    gap = np.array([(r.get("v27_price", np.nan) - r.get("v26_price", np.nan))
                    for r in rows])
    return t, gap


def make_figure(anchor_e: float, anchor_c: float, mapping: dict,
                fig_name: str, fig_title: str):

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True)
    ax_hr, ax_price, ax_econ, ax_cw = (
        axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]
    )

    for idx, p in enumerate(P_VALS):
        key = (round(p, 2), round(anchor_e, 2), round(anchor_c, 3))
        if key not in mapping:
            continue
        sid, outcome = mapping[key]
        ts = load_ts(sid)
        color = P_COLORS[idx]
        ls = "-" if outcome == "v27_dominant" else ("--" if outcome == "v26_dominant" else ":")
        lw = 2.0 if outcome == "v27_dominant" else 1.5
        label = f"{P_LABELS[p]}  [{OUTCOME_MARKER[outcome]}]"

        t, hr  = ts_col(ts, "v27_hashrate")
        _, pg  = price_gap(ts)
        _, ec  = ts_col(ts, "v27_economic")
        _, cwr = chainwork_ratio(ts)

        ax_hr.plot(t, hr,  color=color, lw=lw, ls=ls, label=label)
        ax_price.plot(t, pg, color=color, lw=lw, ls=ls)
        ax_econ.plot(t, ec,  color=color, lw=lw, ls=ls)
        ax_cw.plot(t, cwr,  color=color, lw=lw, ls=ls)

    # Hashrate panel
    ax_hr.axhline(50, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax_hr.set_ylabel("v27 hashrate share (%)", fontsize=10)
    ax_hr.set_title("(a) v27 Hashrate Share", fontsize=10, fontweight="bold")
    ax_hr.set_ylim(0, 105)
    ax_hr.legend(fontsize=7.5, loc="upper left")
    ax_hr.grid(alpha=0.3)

    # Price divergence panel
    ax_price.axhline(0, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax_price.set_ylabel("v27 price − v26 price (USD)", fontsize=10)
    ax_price.set_title("(b) Price Divergence (v27 − v26)", fontsize=10, fontweight="bold")
    ax_price.grid(alpha=0.3)

    # Economic share panel
    ax_econ.axhline(50, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax_econ.set_ylabel("v27 economic share (%)", fontsize=10)
    ax_econ.set_xlabel("Time (minutes)", fontsize=10)
    ax_econ.set_title("(c) v27 Economic Share", fontsize=10, fontweight="bold")
    ax_econ.set_ylim(0, 105)
    ax_econ.grid(alpha=0.3)

    # Chainwork ratio panel
    ax_cw.axhline(1.0, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax_cw.set_ylabel("chainwork ratio (v27 / v26)", fontsize=10)
    ax_cw.set_xlabel("Time (minutes)", fontsize=10)
    ax_cw.set_title("(d) Chainwork Ratio (v27 / v26 > 1 → v27 heavier)", fontsize=10, fontweight="bold")
    ax_cw.grid(alpha=0.3)

    plt.suptitle(
        f"Softfork Rule Strength — Time Series\n"
        f"E={anchor_e:.2f}, C={anchor_c:.3f} — all 6 p values\n"
        f"({fig_title})",
        fontsize=11, y=1.01
    )
    plt.tight_layout()
    out_path = OUT / fig_name
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


def make_panel_grid(mapping: dict):
    """
    Single large figure: 4 rows (metrics) × 3 cols (anchor cells).
    Anchors chosen to show the full range of p effects.
    """
    anchors = [
        (0.65, 0.30, "E=0.65, C=0.30\n(v27 wins → contested as p rises)"),
        (0.74, 0.40, "E=0.74, C=0.40\n(v27 wins → v26 wins at p=1.00)"),
        (0.78, 0.50, "E=0.78, C=0.50\n(contested at p=0.00 → v27 at p≥0.10)"),
    ]
    metrics = [
        ("v27_hashrate",  "v27 hashrate (%)",         None,   (0, 105)),
        ("price_gap",     "Price gap USD (v27−v26)",   None,   None),
        ("v27_economic",  "v27 economic share (%)",    None,   (0, 105)),
        ("chainwork",     "Chainwork ratio (v27/v26)", 1.0,    None),
    ]

    fig, axes = plt.subplots(4, 3, figsize=(18, 14), sharex=False)

    for col, (anchor_e, anchor_c, col_title) in enumerate(anchors):
        for row, (metric, ylabel, ref_line, ylim) in enumerate(metrics):
            ax = axes[row, col]

            for idx, p in enumerate(P_VALS):
                key = (round(p, 2), round(anchor_e, 2), round(anchor_c, 3))
                if key not in mapping:
                    continue
                sid, outcome = mapping[key]
                ts = load_ts(sid)
                color = P_COLORS[idx]
                ls = "-" if outcome == "v27_dominant" else ("--" if outcome == "v26_dominant" else ":")
                lw = 1.8

                if metric == "price_gap":
                    t, v = price_gap(ts)
                elif metric == "chainwork":
                    t, v = chainwork_ratio(ts)
                else:
                    t, v = ts_col(ts, metric)

                t_min = t  # already in minutes from load_ts helpers
                short = f"p={p:.2f} [{OUTCOME_MARKER[outcome]}]"
                ax.plot(t_min, v, color=color, lw=lw, ls=ls,
                        label=short if row == 0 else None)

            if ref_line is not None:
                ax.axhline(ref_line, color="gray", lw=0.8, ls="--", alpha=0.5)
            if ylim:
                ax.set_ylim(*ylim)
            ax.grid(alpha=0.25)

            if row == 0:
                ax.set_title(col_title, fontsize=9, fontweight="bold")
                ax.legend(fontsize=6.5, loc="upper left", ncol=1)
            if col == 0:
                ax.set_ylabel(ylabel, fontsize=8)
            if row == 3:
                ax.set_xlabel("Time (minutes)", fontsize=8)

    plt.suptitle(
        "Softfork Rule Strength — Time Series Comparison Across p Values\n"
        "(solid = v27 wins, dashed = v26 wins, dotted = contested)",
        fontsize=11, y=1.01
    )
    plt.tight_layout()
    out_path = OUT / "srs_timeseries_grid.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mapping = load_meta()
    print(f"Loaded {len(mapping)} scenarios")

    print("\nGenerating individual anchor figures...")
    make_figure(0.65, 0.30, mapping,
                "srs_ts_e065_c030.png",
                "Contested zone — v27 wins at p≤0.50, fails at p≥0.75")
    make_figure(0.74, 0.40, mapping,
                "srs_ts_e074_c040.png",
                "Strong commitment — v27 wins until p=1.00 breaks cascade")
    make_figure(0.78, 0.50, mapping,
                "srs_ts_e078_c050.png",
                "High C — baseline inversion resolved by accepting v26 blocks")
    make_figure(0.55, 0.30, mapping,
                "srs_ts_e055_c030.png",
                "Low E — cascade only survives at intermediate p")

    print("\nGenerating combined panel grid...")
    make_panel_grid(mapping)

    print("\nDone.")


if __name__ == "__main__":
    main()
