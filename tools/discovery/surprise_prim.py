#!/usr/bin/env python3
"""
surprise_prim.py — PRIM analysis on the surprise score from sp_scores.csv.

Generates docs/figures/fig_surprise_prim.png.

Usage:
    python tools/discovery/surprise_prim.py
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# =============================================================================
# Config
# =============================================================================

CSV_PATH   = Path('tools/discovery/output/sp/sp_scores.csv')
OUT_PATH   = Path('docs/figures/fig_surprise_prim.png')

ACTIVE_PARAMS = [
    'economic_split',
    'pool_committed_split',
    'pool_ideology_strength',
    'pool_max_loss_pct',
]

PARAM_LABELS = {
    'economic_split':         'Economic split (E)',
    'pool_committed_split':   'Pool committed split (C)',
    'pool_ideology_strength': 'Pool ideology strength (I)',
    'pool_max_loss_pct':      'Pool max loss pct (M)',
}

# Structural thresholds (for main panel annotation)
ECON_CASCADE_FLOOR  = 0.50
ECON_ESP            = 0.74
ECON_OVERRIDE       = 0.82
FOUNDRY_FLIP        = 0.214
COMMITTED_THRESHOLD = 0.296

# Contentiousness PRIM box (from fit_boundary.py)
CONT_PRIM_BOX = {
    'economic_split':         (0.28, 0.78),
    'pool_committed_split':   (0.15, 0.53),
    'pool_ideology_strength': (0.44, 0.80),
    'pool_max_loss_pct':      (0.16, 0.40),
}

ALPHA       = 0.08   # fraction to peel per step
MIN_SUPPORT = 0.05   # stop when box has fewer than this fraction of data
DPI         = 300


# =============================================================================
# Custom PRIM — greedy peeling on a continuous objective
# =============================================================================

def prim_peel(df: pd.DataFrame, params: list, objective: str,
              alpha: float = 0.05, min_support: float = 0.05):
    """
    Greedy PRIM peeling. At each step, find the (param, boundary_side) that
    maximises mean(objective) after removing an alpha-fraction slice.

    Runs to min_support without stopping on non-improvement, then selects
    the intermediate box with the highest mean objective at each support level.
    This follows the standard PRIM trajectory approach where the analyst
    chooses the best box along the full peeling curve.

    Returns:
        box_trajectory     — list of dicts {param: (lo, hi)} at each step
        mean_trajectory    — mean(objective) at each step
        support_trajectory — fraction of data in box at each step
        best_box           — box with highest mean objective (at min 30% support)
        best_mask          — boolean mask for best_box
    """
    n_total = len(df)
    mask = np.ones(len(df), dtype=bool)

    box = {p: (df[p].min(), df[p].max()) for p in params}
    box_trajectory     = [dict(box)]
    mean_trajectory    = [df[objective].mean()]
    support_trajectory = [1.0]
    mask_history       = [mask.copy()]

    for _ in range(300):
        n_in = mask.sum()
        if n_in / n_total < min_support:
            break

        best_gain = -np.inf
        best_mask = None
        best_box  = None

        for p in params:
            vals   = df.loc[mask, p].values
            n_peel = max(1, int(np.floor(alpha * n_in)))

            # Peel from low end
            thresh_lo = np.sort(vals)[n_peel - 1]
            new_mask = mask.copy()
            new_mask[mask] = vals > thresh_lo
            if new_mask.sum() >= min_support * n_total:
                gain = df.loc[new_mask, objective].mean()
                if gain > best_gain:
                    best_gain = gain
                    best_mask = new_mask
                    new_box = dict(box)
                    new_box[p] = (df.loc[new_mask, p].min(), box[p][1])
                    best_box = new_box

            # Peel from high end
            thresh_hi = np.sort(vals)[-n_peel]
            new_mask = mask.copy()
            new_mask[mask] = vals < thresh_hi
            if new_mask.sum() >= min_support * n_total:
                gain = df.loc[new_mask, objective].mean()
                if gain > best_gain:
                    best_gain = gain
                    best_mask = new_mask
                    new_box = dict(box)
                    new_box[p] = (box[p][0], df.loc[new_mask, p].max())
                    best_box = new_box

        if best_mask is None:
            break

        mask = best_mask
        box  = best_box
        box_trajectory.append(dict(box))
        mean_trajectory.append(best_gain)
        support_trajectory.append(mask.sum() / n_total)
        mask_history.append(mask.copy())

    # Select best box: highest mean objective where support >= 30%
    # (balances concentration vs coverage)
    best_idx = 0
    best_mean = -np.inf
    for i, (m, s) in enumerate(zip(mean_trajectory, support_trajectory)):
        if s >= 0.30 and m > best_mean:
            best_mean = m
            best_idx = i

    return (box_trajectory, mean_trajectory, support_trajectory,
            box_trajectory[best_idx], mask_history[best_idx])


# =============================================================================
# Main
# =============================================================================

def main():
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} scenarios from {CSV_PATH}")
    print(f"  Columns: {list(df.columns)}")

    # Run PRIM on surprise score
    print("\nRunning PRIM on surprise score...")
    box_traj, mean_traj, supp_traj, final_box, in_box = prim_peel(
        df, ACTIVE_PARAMS, 'surprise', min_support=MIN_SUPPORT
    )

    n_in_box = in_box.sum()
    mean_in  = df.loc[in_box, 'surprise'].mean()
    mean_all = df['surprise'].mean()
    print(f"  Final box: n={n_in_box} ({100*n_in_box/len(df):.1f}%)")
    print(f"  Mean surprise in box: {mean_in:.3f}  (dataset: {mean_all:.3f})")
    print(f"  Lift: {mean_in/mean_all:.2f}×")
    for p, (lo, hi) in final_box.items():
        print(f"    {p}: [{lo:.3f}, {hi:.3f}]")

    # Outcome counts in box
    for outcome in ['v26_dominant', 'v27_dominant', 'contested']:
        n = (df.loc[in_box, 'outcome'] == outcome).sum()
        print(f"  {outcome}: {n} ({100*n/n_in_box:.1f}%)")

    # ==========================================================================
    # Figure: 4-panel layout
    # ==========================================================================
    colors = {
        'v27_dominant': '#2ca02c',
        'v26_dominant': '#d62728',
        'contested':    '#e6a800',
    }
    labels_ok = {
        'v27_dominant': 'v27 win',
        'v26_dominant': 'v26 win',
        'contested':    'Contested',
    }
    outcomes = ['v27_dominant', 'v26_dominant', 'contested']

    fig = plt.figure(figsize=(16, 9))
    gs = gridspec.GridSpec(
        2, 3,
        width_ratios=[1.7, 1.0, 1.0],
        hspace=0.38, wspace=0.32,
        left=0.06, right=0.97, top=0.91, bottom=0.08,
    )
    ax_main  = fig.add_subplot(gs[:, 0])      # left — E×C scatter
    ax_traj  = fig.add_subplot(gs[0, 1])      # top-mid — peeling trajectory
    ax_box   = fig.add_subplot(gs[1, 1])      # bot-mid — boxplot by outcome
    ax_para  = fig.add_subplot(gs[:, 2])      # right — parallel coords

    surprise = df['surprise'].values

    # ---- Main panel: E×C scatter colored by surprise ----
    sc = ax_main.scatter(
        df['economic_split'], df['pool_committed_split'],
        c=surprise, cmap='plasma', s=28, alpha=0.75,
        vmin=0, vmax=surprise.max(), zorder=4,
    )
    cbar = fig.colorbar(sc, ax=ax_main, fraction=0.046, pad=0.04)
    cbar.set_label('Unexpected-Direction Score', fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    # Top-15 by surprise
    top15_idx = np.argsort(surprise)[-15:]
    ax_main.scatter(
        df['economic_split'].values[top15_idx],
        df['pool_committed_split'].values[top15_idx],
        s=80, marker='*', color='white', edgecolors='black',
        linewidths=0.5, zorder=7, label='Top-15 unexpected-direction',
    )

    # Threshold lines
    ax_main.axvline(ECON_CASCADE_FLOOR, color='#333', lw=1.2, ls=':', alpha=0.8, zorder=5)
    ax_main.axvline(ECON_ESP,           color='#333', lw=1.2, ls='--', alpha=0.8, zorder=5)
    ax_main.axvline(ECON_OVERRIDE,      color='#333', lw=1.2, ls=':', alpha=0.8, zorder=5)
    ax_main.axhline(FOUNDRY_FLIP,       color='#555', lw=1.0, ls=':', alpha=0.7, zorder=5)
    ax_main.axhline(COMMITTED_THRESHOLD,color='#555', lw=1.0, ls='--', alpha=0.7, zorder=5)

    # Contentiousness PRIM box (blue dashed)
    cx = CONT_PRIM_BOX['economic_split']
    cy = CONT_PRIM_BOX['pool_committed_split']
    ax_main.add_patch(mpatches.FancyBboxPatch(
        (cx[0], cy[0]), cx[1]-cx[0], cy[1]-cy[0],
        boxstyle='square,pad=0', fill=False,
        edgecolor='dodgerblue', linewidth=1.5, linestyle='--', zorder=6,
    ))

    # Surprise PRIM box (cyan solid)
    sx = final_box['economic_split']
    sy = final_box['pool_committed_split']
    ax_main.add_patch(mpatches.FancyBboxPatch(
        (sx[0], sy[0]), sx[1]-sx[0], sy[1]-sy[0],
        boxstyle='square,pad=0', fill=False,
        edgecolor='cyan', linewidth=2.0, linestyle='-', zorder=6,
    ))

    # Threshold labels
    y_top = df['pool_committed_split'].max()
    tkw = dict(fontsize=7, color='#111',
               bbox=dict(boxstyle='round,pad=0.12', facecolor='white',
                         edgecolor='#aaa', alpha=0.85))
    ax_main.text(ECON_CASCADE_FLOOR+0.01, y_top-0.02, 'Cascade\nfloor', va='top', ha='left', **tkw)
    ax_main.text(ECON_ESP,                y_top-0.02, 'ESP\n~0.74',      va='top', ha='center', **tkw)
    ax_main.text(ECON_OVERRIDE-0.01,      y_top-0.02, 'Override',        va='top', ha='right', **tkw)

    # Legend patches
    legend_els = [
        Line2D([0],[0], color='white', markerfacecolor='white', marker='*',
               markeredgecolor='black', markersize=9, label='Top-15 unexpected-direction'),
        mpatches.Patch(fill=False, edgecolor='cyan', lw=2, label='High-Leverage Unexpected-Direction box'),
        mpatches.Patch(fill=False, edgecolor='dodgerblue', lw=1.5, ls='--', label='Contentiousness PRIM box'),
    ]
    ax_main.legend(handles=legend_els, fontsize=7, loc='lower right')
    ax_main.set_xlabel(PARAM_LABELS['economic_split'], fontsize=9)
    ax_main.set_ylabel(PARAM_LABELS['pool_committed_split'], fontsize=9)
    ax_main.set_title('Unexpected-Direction Score — E×C projection', fontsize=10, fontweight='bold')
    ax_main.tick_params(labelsize=8)

    # ---- Peeling trajectory ----
    steps = np.arange(len(mean_traj))
    ax_traj.plot(supp_traj, mean_traj, color='darkorange', lw=2, marker='o',
                 markersize=3, zorder=4)
    ax_traj.axhline(mean_all, color='#888', lw=1, ls='--', label=f'Dataset mean ({mean_all:.3f})')
    final_supp = supp_traj[-1]
    ax_traj.axvline(final_supp, color='cyan', lw=1.5, ls='-',
                    label=f'Final box ({100*final_supp:.0f}%)')
    ax_traj.set_xlabel('Box support (fraction of data)', fontsize=8)
    ax_traj.set_ylabel('Mean unexpected-direction score in box', fontsize=8)
    ax_traj.set_title('PRIM Peeling Trajectory', fontsize=9, fontweight='bold')
    ax_traj.legend(fontsize=7)
    ax_traj.tick_params(labelsize=7)
    ax_traj.invert_xaxis()

    # ---- Boxplot by outcome ----
    data_all  = [df.loc[df['outcome'] == o, 'surprise'].values for o in outcomes]
    data_in   = [df.loc[in_box & (df['outcome'] == o), 'surprise'].values for o in outcomes]

    bplot = ax_box.boxplot(data_all, patch_artist=True, notch=False,
                           medianprops=dict(color='black', lw=1.5),
                           positions=[1,2,3], widths=0.45)
    for patch, o in zip(bplot['boxes'], outcomes):
        patch.set_facecolor(colors[o])
        patch.set_alpha(0.55)

    # Overlay in-box points
    for j, (o, d) in enumerate(zip(outcomes, data_in)):
        if len(d):
            ax_box.scatter(
                np.full(len(d), j+1) + np.random.uniform(-0.12, 0.12, len(d)),
                d, color=colors[o], s=12, alpha=0.7, zorder=5,
                edgecolors='black', linewidths=0.3,
            )

    ax_box.set_xticks([1,2,3])
    ax_box.set_xticklabels([labels_ok[o] for o in outcomes], fontsize=8)
    ax_box.set_ylabel('Unexpected-Direction Score', fontsize=8)
    ax_box.set_title('Unexpected-Direction Score by Outcome\n(dots = in-box scenarios)', fontsize=9, fontweight='bold')
    ax_box.tick_params(labelsize=7)
    ax_box.set_ylim(-0.05, surprise.max() * 1.05)

    # ---- Parallel coordinates — top-15 surprise scenarios ----
    top15 = df.nlargest(15, 'surprise').reset_index(drop=True)
    n_params = len(ACTIVE_PARAMS)

    for _, row in top15.iterrows():
        c = colors.get(row['outcome'], 'grey')
        xs = np.arange(n_params)
        ys = [row[p] for p in ACTIVE_PARAMS]
        ax_para.plot(xs, ys, color=c, alpha=0.6, lw=1.5, marker='o', markersize=3)

    # Axis ticks and labels
    ax_para.set_xticks(np.arange(n_params))
    ax_para.set_xticklabels(
        [PARAM_LABELS[p].split('(')[0].strip() for p in ACTIVE_PARAMS],
        fontsize=7, rotation=15, ha='right',
    )
    ax_para.set_ylabel('Parameter value', fontsize=8)
    ax_para.set_title('Top-15 Unexpected-Direction Scenarios\n(parallel coordinates)', fontsize=9, fontweight='bold')
    ax_para.tick_params(labelsize=7)

    # Dataset medians as dashed reference lines
    for j, p in enumerate(ACTIVE_PARAMS):
        ax_para.axhline(df[p].median(), color='#bbb', lw=0.8, ls='--', alpha=0.6,
                        xmin=j/n_params, xmax=(j+1)/n_params)

    # Legend
    legend_els2 = [
        Line2D([0],[0], color='#2ca02c', lw=2, label='v27 win'),
        Line2D([0],[0], color='#d62728', lw=2, label='v26 win'),
        Line2D([0],[0], color='#e6a800', lw=2, label='Contested'),
    ]
    ax_para.legend(handles=legend_els2, fontsize=7, loc='lower right')

    # ---- Suptitle ----
    fig.suptitle(
        'High-Leverage, Unexpected-Direction (2016-block)',
        fontsize=12, fontweight='bold',
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"\nSaved: {OUT_PATH}")


if __name__ == '__main__':
    main()
