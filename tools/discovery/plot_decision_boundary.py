#!/usr/bin/env python3
"""
Publication-quality decision boundary figure — 2016-block retarget.

Trains a Random Forest on the full 2016-block dataset (VALID_SWEEPS_2016 +
lhs_2016_full_phase3_merged) and plots the RF probability surface across four
parameter projections with an asymmetric layout:
  - Left (dominant): economic_split × pool_committed_split (E×C)
  - Right top:       economic_split × pool_max_loss_pct   (E×M)
  - Right middle:    pool_committed_split × pool_ideology_strength (C×I)
  - Right bottom:    pool_ideology_strength × pool_max_loss_pct   (I×M)

Each panel shows:
  - RF P(v27 win) probability surface (RdYlGn colormap)
  - P=0.50 decision contour (white dashed line)
  - Individual scenario outcomes (triangle=v27 win, circle=v26 win)
  - PRIM uncertainty box overlay (dashed blue rectangle)

The E×C panel additionally annotates three structural thresholds:
  - Cascade floor (E≈0.50)
  - Economic override (E≈0.82)
  - Foundry flip-point (C≈0.214)
  - Inversion zone bracket with double-headed arrow

Usage:
    python tools/discovery/plot_decision_boundary.py
    python tools/discovery/plot_decision_boundary.py --db path/to/sweep_results.db
    python tools/discovery/plot_decision_boundary.py --output path/to/output.png

Output:
    docs/figures/fig_decision_boundary_full.png  (default)
"""

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from sklearn.ensemble import RandomForestClassifier

# =============================================================================
# Configuration
# =============================================================================

DB_PATH = Path('tools/sweep/sweep_results.db')
OUTPUT_PATH = Path('docs/figures/fig_decision_boundary_full.png')

ACTIVE_PARAMS = [
    'economic_split',
    'pool_committed_split',
    'pool_ideology_strength',
    'pool_max_loss_pct',
]

# Canonical 2016-block dataset (VALID_SWEEPS_2016 from fit_boundary.py)
VALID_SWEEPS_2016 = [
    'econ_committed_2016_grid',
    'lhs_2016_full_parameter',
    'lhs_2016_6param',
    'targeted_sweep7_esp_2016',
    'targeted_sweep10_econ_threshold_2016',
    'targeted_sweep10b_econ_threshold_2016',
    'targeted_sweep8_lite_2016_retarget',
    'targeted_sweep9_long_duration_2016',
    'targeted_sweep11_lite_chaos_test',
    'committed_2016_high_econ',
    'committed_2016_mid_econ',
    'committed_2016_sigmoid',
    'committed_2016_sigmoid_midecon',
    'hashrate_2016_verification',
    # Phase 3 full-network LHS — included for full boundary coverage
    'lhs_2016_full_phase3_merged',
]

# PRIM uncertainty box bounds (from fit_boundary.py output, n=295 VALID_SWEEPS_2016)
PRIM_BOX = {
    'economic_split':         (0.28, 0.78),
    'pool_committed_split':   (0.15, 0.53),
    'pool_ideology_strength': (0.44, 0.80),
    'pool_max_loss_pct':      (0.16, 0.40),
}

# Structural thresholds (from Phase 1 findings)
ECON_CASCADE_FLOOR   = 0.50   # below this v27 cannot win regardless of pool structure
ECON_OVERRIDE        = 0.82   # above this v27 wins regardless of pool structure
FOUNDRY_FLIP_POINT   = 0.214  # pool_committed_split level corresponding to Foundry hashrate

# RF grid resolution
GRID_N_MAIN       = 120   # resolution for the dominant E×C panel
GRID_N_SUPPORTING = 80    # resolution for the three right-column panels

RF_N_ESTIMATORS = 600
RF_RANDOM_STATE = 42

DPI = 300


# =============================================================================
# Data loading
# =============================================================================

def load_data(db_path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    placeholders = ','.join(['?' for _ in VALID_SWEEPS_2016])
    query = f"""
        SELECT
            sr.sweep_name,
            sr.network_type,
            s.economic_split,
            s.pool_committed_split,
            s.pool_ideology_strength,
            s.pool_max_loss_pct,
            s.outcome
        FROM scenarios s
        JOIN sweeps sr ON s.sweep_id = sr.sweep_id
        WHERE sr.sweep_name IN ({placeholders})
          AND s.outcome IN ('v27_dominant', 'v26_dominant', 'contested')
    """
    df = pd.read_sql_query(query, conn, params=VALID_SWEEPS_2016)
    conn.close()

    # Drop rows missing any active parameter
    df = df.dropna(subset=ACTIVE_PARAMS).reset_index(drop=True)
    print(f"Loaded {len(df)} scenarios from {df['sweep_name'].nunique()} sweeps")
    for outcome in ['v27_dominant', 'v26_dominant', 'contested']:
        n = (df['outcome'] == outcome).sum()
        print(f"  {outcome}: {n} ({n/len(df)*100:.1f}%)")
    return df


# =============================================================================
# RF training
# =============================================================================

def train_rf(df: pd.DataFrame):
    X = df[ACTIVE_PARAMS].values
    y = (df['outcome'] == 'v27_dominant').astype(int).values
    rf = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        oob_score=True,
        random_state=RF_RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X, y)
    print(f"RF OOB accuracy: {rf.oob_score_*100:.1f}%")
    return rf


# =============================================================================
# Plotting helpers
# =============================================================================

def make_grid(x_param, y_param, df, n):
    """Build meshgrid for two parameters, holding others at dataset medians."""
    x_range = np.linspace(df[x_param].min(), df[x_param].max(), n)
    y_range = np.linspace(df[y_param].min(), df[y_param].max(), n)
    xx, yy = np.meshgrid(x_range, y_range)

    # Median values for the two non-plotted parameters
    other_params = [p for p in ACTIVE_PARAMS if p not in (x_param, y_param)]
    medians = {p: df[p].median() for p in other_params}

    cols = {}
    for p in ACTIVE_PARAMS:
        if p == x_param:
            cols[p] = xx.ravel()
        elif p == y_param:
            cols[p] = yy.ravel()
        else:
            cols[p] = np.full(xx.size, medians[p])

    grid_X = np.column_stack([cols[p] for p in ACTIVE_PARAMS])
    return xx, yy, grid_X


def plot_panel(ax, rf, df, x_param, y_param, grid_n, cmap='RdYlGn', show_colorbar=False, fig=None):
    """Render RF probability surface, P=0.50 contour, PRIM box, and outcome scatter."""
    xx, yy, grid_X = make_grid(x_param, y_param, df, grid_n)
    probs = rf.predict_proba(grid_X)[:, 1].reshape(xx.shape)

    # Probability surface
    cf = ax.contourf(xx, yy, probs, levels=20, cmap=cmap, alpha=0.85, vmin=0, vmax=1)
    if show_colorbar and fig is not None:
        cbar = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('P(v27 win)', fontsize=9)
        cbar.ax.tick_params(labelsize=8)

    # P=0.50 decision contour
    ax.contour(xx, yy, probs, levels=[0.5], colors='#111111',
               linewidths=1.8, linestyles='--')

    # PRIM uncertainty box
    x_box = PRIM_BOX.get(x_param)
    y_box = PRIM_BOX.get(y_param)
    if x_box and y_box:
        rect = mpatches.FancyBboxPatch(
            (x_box[0], y_box[0]),
            x_box[1] - x_box[0],
            y_box[1] - y_box[0],
            boxstyle='square,pad=0',
            fill=False,
            edgecolor='dodgerblue',
            linewidth=2.0,
            linestyle='--',
            zorder=5,
        )
        ax.add_patch(rect)

    # Outcome scatter
    v27_mask = df['outcome'] == 'v27_dominant'
    v26_mask = df['outcome'] == 'v26_dominant'
    con_mask  = df['outcome'] == 'contested'

    scatter_kw = dict(s=22, edgecolors='white', linewidths=0.4, alpha=0.65, zorder=6)
    ax.scatter(df.loc[v27_mask, x_param], df.loc[v27_mask, y_param],
               marker='^', color='#2ca02c', **scatter_kw)
    ax.scatter(df.loc[v26_mask, x_param], df.loc[v26_mask, y_param],
               marker='o', color='#d62728', **scatter_kw)
    if con_mask.any():
        ax.scatter(df.loc[con_mask, x_param], df.loc[con_mask, y_param],
                   marker='D', color='gold', **scatter_kw)

    ax.set_xlabel(_label(x_param), fontsize=9)
    ax.set_ylabel(_label(y_param), fontsize=9)
    ax.tick_params(labelsize=8)

    return cf


PARAM_LABELS = {
    'economic_split':         'Economic split (E)',
    'pool_committed_split':   'Pool committed split (C)',
    'pool_ideology_strength': 'Pool ideology strength (I)',
    'pool_max_loss_pct':      'Pool max loss pct (M)',
}

def _label(p):
    return PARAM_LABELS.get(p, p)


def annotate_ec_panel(ax, df):
    """Add structural threshold lines and inversion zone bracket to the E×C panel."""
    x_min = df['economic_split'].min()
    x_max = df['economic_split'].max()
    y_min = df['pool_committed_split'].min()
    y_max = df['pool_committed_split'].max()

    text_kw = dict(fontsize=8, color='#111111', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                             edgecolor='#aaaaaa', alpha=0.85))

    # Cascade floor — vertical line at E≈0.50
    ax.axvline(ECON_CASCADE_FLOOR, color='#333333', linewidth=1.4,
               linestyle=':', alpha=0.9, zorder=7)
    ax.text(ECON_CASCADE_FLOOR + 0.01, y_max - 0.03,
            f'Cascade floor\nE≈{ECON_CASCADE_FLOOR}', va='top', ha='left',
            **text_kw)

    # Economic override — vertical line at E≈0.82
    ax.axvline(ECON_OVERRIDE, color='#333333', linewidth=1.4,
               linestyle=':', alpha=0.9, zorder=7)
    ax.text(ECON_OVERRIDE - 0.01, y_max - 0.03,
            f'Economic override\nE≈{ECON_OVERRIDE}', va='top', ha='right',
            **text_kw)

    # Foundry flip-point — horizontal line at C≈0.214
    ax.axhline(FOUNDRY_FLIP_POINT, color='#333333', linewidth=1.4,
               linestyle=':', alpha=0.9, zorder=7)
    ax.text(x_min + 0.01, FOUNDRY_FLIP_POINT + 0.01,
            f'Foundry flip-point  C≈{FOUNDRY_FLIP_POINT}',
            va='bottom', ha='left', **text_kw)

    # Inversion zone bracket — double-headed arrow between the two vertical thresholds
    bracket_y = y_min + (y_max - y_min) * 0.10
    ax.annotate(
        '', xy=(ECON_OVERRIDE, bracket_y), xytext=(ECON_CASCADE_FLOOR, bracket_y),
        arrowprops=dict(arrowstyle='<->', color='#333333', lw=1.5),
        zorder=8,
    )
    ax.text(
        (ECON_CASCADE_FLOOR + ECON_OVERRIDE) / 2, bracket_y + 0.015,
        'Inversion zone',
        ha='center', va='bottom', fontsize=8, color='#111111', fontweight='bold', zorder=8,
    )


# =============================================================================
# Main figure
# =============================================================================

def make_figure(df, rf, output_path: Path):
    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor('white')

    gs = gridspec.GridSpec(
        3, 2,
        width_ratios=[1.6, 1],
        height_ratios=[1, 1, 1],
        hspace=0.38,
        wspace=0.30,
        left=0.07, right=0.97,
        top=0.91, bottom=0.08,
    )

    # --- Left dominant panel: E × C (spans all 3 rows) ---
    ax_ec = fig.add_subplot(gs[:, 0])
    cf = plot_panel(ax_ec, rf, df, 'economic_split', 'pool_committed_split',
                    GRID_N_MAIN, show_colorbar=True, fig=fig)
    annotate_ec_panel(ax_ec, df)
    ax_ec.set_title('Economic split × Pool committed split  (E×C)',
                    fontsize=11, fontweight='bold', color='#111111', pad=8)
    ax_ec.set_facecolor('white')
    ax_ec.tick_params(colors='#333333')
    ax_ec.xaxis.label.set_color('#333333')
    ax_ec.yaxis.label.set_color('#333333')
    ax_ec.spines[:].set_color('#cccccc')

    # --- Right column: E×M, C×I, I×M ---
    right_panels = [
        (gs[0, 1], 'economic_split',         'pool_max_loss_pct',      'E×M'),
        (gs[1, 1], 'pool_committed_split',    'pool_ideology_strength', 'C×I'),
        (gs[2, 1], 'pool_ideology_strength',  'pool_max_loss_pct',      'I×M'),
    ]

    for spec, xp, yp, title in right_panels:
        ax = fig.add_subplot(spec)
        plot_panel(ax, rf, df, xp, yp, GRID_N_SUPPORTING)
        ax.set_title(title, fontsize=10, fontweight='bold', color='#111111', pad=5)
        ax.set_facecolor('white')
        ax.tick_params(colors='#333333')
        ax.xaxis.label.set_color('#333333')
        ax.yaxis.label.set_color('#333333')
        ax.spines[:].set_color('#cccccc')

    # --- Legend ---
    legend_elements = [
        Line2D([0], [0], marker='^', color='k', markerfacecolor='#2ca02c',
               markersize=8, linewidth=0, label='v27 win'),
        Line2D([0], [0], marker='o', color='k', markerfacecolor='#d62728',
               markersize=8, linewidth=0, label='v26 win'),
        Line2D([0], [0], marker='D', color='k', markerfacecolor='#e6a800',
               markersize=7, linewidth=0, label='Contested'),
        Line2D([0], [0], color='#333333', linewidth=1.8, linestyle='--',
               label='P=0.50 boundary'),
        mpatches.Patch(facecolor='none', edgecolor='dodgerblue',
                       linewidth=2, linestyle='--', label='PRIM uncertainty box'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=5,
               fontsize=8.5, framealpha=0.9, facecolor='white',
               edgecolor='#cccccc', labelcolor='#111111',
               bbox_to_anchor=(0.5, 0.01))

    # --- Super-title ---
    n_total = len(df)
    oob = rf.oob_score_ * 100
    fig.suptitle(
        f'2016-block Fork Outcome Decision Boundary  '
        f'(n={n_total}, RF OOB={oob:.1f}%)',
        fontsize=13, fontweight='bold', color='#111111', y=0.97,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved: {output_path}")


# =============================================================================
# Entry point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db', type=Path, default=DB_PATH,
                        help=f'Path to sweep_results.db (default: {DB_PATH})')
    parser.add_argument('--output', type=Path, default=OUTPUT_PATH,
                        help=f'Output PNG path (default: {OUTPUT_PATH})')
    args = parser.parse_args()

    df = load_data(args.db)
    rf = train_rf(df)
    make_figure(df, rf, args.output)


if __name__ == '__main__':
    main()
