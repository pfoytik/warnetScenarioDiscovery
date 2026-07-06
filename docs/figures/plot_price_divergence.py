#!/usr/bin/env python3
"""
Regenerate fig_price_divergence_timeseries.png with:
  - x-axis limited to blocks 0-2000
  - Labels: softfork (blue) and legacy (red)
  - Optional hashrate row (SHOW_HASHRATE = True)

Source scenarios:
  - Clean Win (legacy-dominant): realistic_sweep2/sweep_0041
  - Cascade Win (softfork-dominant): lhs_2016_full_parameter/sweep_0002
  - Contested Outcome: econ_committed_2016_grid/sweep_0021
"""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── Config ──────────────────────────────────────────────────────────────────
SHOW_HASHRATE = True      # add hashrate row below price row
X_MAX = 2000              # block limit on x-axis
BASE_DIR = Path(__file__).parent.parent.parent   # warnetScenarioDiscovery root
OUT   = Path(__file__).parent / "fig_price_divergence_timeseries.png"

SOFTFORK_COLOR = "#2171b5"   # blue
LEGACY_COLOR   = "#cb181d"   # red
BASE_COLOR     = "#666666"

SOURCES = [
    {
        "path": "tools/sweep/lhs_2016_full_6param/results/sweep_0594/results.json",
        "title": "Clean Win\n(legacy-dominant)", 
    },
    {
        "path": "tools/sweep/lhs_2016_full_parameter/results/sweep_0002/results.json",
        "title": "Cascade Win\n(softfork-dominant)",
    },
    {
        "path": "tools/sweep/econ_committed_2016_grid/results/sweep_0021/results.json",
        "title": "Contested Outcome",
    },
]

# ── Load data ────────────────────────────────────────────────────────────────
def load_scenario(path):
    full = BASE_DIR / path
    r = json.load(open(full))
    ts   = r["time_series"]
    meta = r.get("metadata", {})
    interval = meta.get("interval", 2)  # seconds per block

    timestamps  = np.array(ts["timestamps"], dtype=float)
    x = timestamps / interval              # convert to block-units

    def extend(arr):
        """If the data ends before X_MAX, append a point at X_MAX holding the last value."""
        if x[-1] < X_MAX:
            return np.append(arr, arr[-1])
        return arr

    x_ext = np.append(x, X_MAX) if x[-1] < X_MAX else x

    return {
        "x":          x_ext,
        "v27_price":  extend(np.array(ts["v27_price"])),
        "v26_price":  extend(np.array(ts["v26_price"])),
        "v27_hr":     extend(np.array(ts.get("v27_hashrate", [0]*len(x)))),
        "v26_hr":     extend(np.array(ts.get("v26_hashrate", [0]*len(x)))),
        "base_price": r.get("prices", {}).get("config", {}).get("base_price", 60000),
        "interval":   interval,
        "x_max_data": x[-1],   # original data end, used for retarget lines
    }

scenarios = [load_scenario(s["path"]) for s in SOURCES]

# ── Helpers ──────────────────────────────────────────────────────────────────
def price_fmt(ax):
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:+.0f}%"))

def pct_fmt(ax):
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:.0f}%"))

def retarget_lines(ax, x_max, interval):
    """Dashed vertical lines at 2016-block retarget epochs."""
    epoch = 2016
    for e in range(epoch, int(x_max) + 1, epoch):
        if e <= X_MAX:
            ax.axvline(e, color="#aaaaaa", lw=0.8, ls="--", zorder=0)

def end_label(ax, x_arr, y_arr, color, fmt="${:.1f}k", frac=1000):
    """Annotate the final visible value; clamp to axis interior if x < 80% of X_MAX."""
    mask = x_arr <= X_MAX
    if not any(mask):
        return
    xi, yi = x_arr[mask][-1], y_arr[mask][-1]
    # If data ends far left, place label to the right of the last point
    # If data reaches near X_MAX, place it at the right margin
    if xi >= 0.85 * X_MAX:
        ax.annotate(
            fmt.format(yi / frac),
            xy=(xi, yi), xytext=(4, 0), textcoords="offset points",
            va="center", ha="left", fontsize=8, color=color, fontweight="bold",
            clip_on=False,
        )
    else:
        ax.annotate(
            fmt.format(yi / frac),
            xy=(xi, yi), xytext=(6, 2), textcoords="offset points",
            va="bottom", ha="left", fontsize=8, color=color, fontweight="bold",
        )

# ── Figure layout ────────────────────────────────────────────────────────────
N_ROWS = 2 if SHOW_HASHRATE else 1
N_COLS = 3
FIG_W  = 13
FIG_H  = 4.5 * N_ROWS + 0.6   # extra for suptitle

fig, axes = plt.subplots(
    N_ROWS, N_COLS,
    figsize=(FIG_W, FIG_H),
    sharex="col",
    gridspec_kw={"hspace": 0.10, "wspace": 0.28,
                 "top": 0.88, "bottom": 0.10},
)
if N_ROWS == 1:
    axes = axes[np.newaxis, :]   # keep 2D

fig.suptitle(
    "Price Change" + (" and Hashrate" if SHOW_HASHRATE else "") +
    " Dynamics by Outcome Category\n"
    "Blocks 0–2,000 | softfork chain (blue) vs legacy chain (red) | "
    "dotted = base (0%)",
    fontsize=11, y=0.97,
)

# ── Plot ─────────────────────────────────────────────────────────────────────
LEGEND_DONE = False

for col, (sc, info) in enumerate(zip(scenarios, SOURCES)):
    x       = sc["x"]
    v27_px  = sc["v27_price"]
    v26_px  = sc["v26_price"]
    v27_hr  = sc["v27_hr"]
    v26_hr  = sc["v26_hr"]
    base    = sc["base_price"]
    x_data_max = sc["x_max_data"]

    # ── Price row ────────────────────────────────────────────────────────────
    ax_p = axes[0, col]

    v27_pct = (v27_px / base - 1) * 100
    v26_pct = (v26_px / base - 1) * 100

    ax_p.plot(x, v27_pct, color=SOFTFORK_COLOR, lw=1.6, label="softfork price")
    ax_p.plot(x, v26_pct, color=LEGACY_COLOR,   lw=1.6, label="legacy price")
    ax_p.axhline(0, color=BASE_COLOR, lw=0.9, ls=":", label="base (0%)")
    retarget_lines(ax_p, x_data_max, sc["interval"])

    end_label(ax_p, x, v27_pct, SOFTFORK_COLOR, fmt="{:+.1f}%", frac=1)
    end_label(ax_p, x, v26_pct, LEGACY_COLOR,   fmt="{:+.1f}%", frac=1)

    ax_p.set_xlim(0, X_MAX)
    ax_p.set_ylim(-25, 25)
    price_fmt(ax_p)
    ax_p.set_title(info["title"], fontsize=10, fontweight="bold", pad=6)
    #ax_p.text(0.5, -0.06, info["subtitle"], transform=ax_p.transAxes,
    #          ha="center", fontsize=7.5, color="#444444")

    if col == 0:
        ax_p.set_ylabel("Price change (%)", fontsize=9)
        if not LEGEND_DONE:
            ax_p.legend(fontsize=8, loc="lower left", framealpha=0.8)
            LEGEND_DONE = True

    # ── Hashrate row ─────────────────────────────────────────────────────────
    if SHOW_HASHRATE:
        ax_h = axes[1, col]

        ax_h.plot(x, v27_hr, color=SOFTFORK_COLOR, lw=1.6, label="softfork hashrate")
        ax_h.plot(x, v26_hr, color=LEGACY_COLOR,   lw=1.6, label="legacy hashrate")
        retarget_lines(ax_h, x_data_max, sc["interval"])

        end_label(ax_h, x, v27_hr, SOFTFORK_COLOR, fmt="{:.1f}%", frac=1)
        end_label(ax_h, x, v26_hr, LEGACY_COLOR,   fmt="{:.1f}%", frac=1)

        ax_h.set_xlim(0, X_MAX)
        ax_h.set_ylim(-2, 105)
        pct_fmt(ax_h)
        ax_h.set_xlabel("Blocks", fontsize=9)

        if col == 0:
            ax_h.set_ylabel("Hashrate share (%)", fontsize=9)
            ax_h.legend(fontsize=8, loc="center left", framealpha=0.8)
    else:
        axes[0, col].set_xlabel("Blocks", fontsize=9)

# ── Save ─────────────────────────────────────────────────────────────────────
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT}")
