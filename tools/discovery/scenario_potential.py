#!/usr/bin/env python3
"""
Scenario Potential Analysis — SP_pools and SP_economic

Computes per-scenario governance leverage scores for the two actor classes
that actually determine 2016-block fork outcomes:

  SP_pools    — how close is pool_committed_split to the decision boundary?
                High SP_pools = a small change in which large pools commit to
                which fork would flip the outcome. Peaks at the committed_split
                threshold (~0.296 in the transition zone, ~0.214 at the Foundry
                flip-point).

  SP_economic — how close is economic_split to the inversion zone boundaries?
                High SP_economic = exchange/custodian custody decisions are
                genuinely pivotal. Peaks near the ESP (~0.74) and cascade floor
                (~0.50). Near-zero below the cascade floor or above the economic
                override threshold (~0.82) where the outcome is structurally
                determined regardless of economic action.

Both scores are derived from the RF probability gradient rather than hard
threshold distances — they reflect how rapidly the model's predicted outcome
probability changes as the parameter moves, which is the correct measure of
governance leverage.

The joint SP surface identifies "maximum governance leverage" scenarios where
both actor classes are simultaneously pivotal, and "unexpected outcome" scenarios
where high SP was available but the outcome resolved cleanly anyway.

Usage:
    python tools/discovery/scenario_potential.py
    python tools/discovery/scenario_potential.py --db path/to/sweep_results.db
    python tools/discovery/scenario_potential.py --output-dir tools/discovery/output/sp

Output (tools/discovery/output/sp/ by default):
    sp_scores.csv                   — per-scenario SP_pools, SP_economic, Z_joint
    sp_top_scenarios.json           — top 20 scenarios by joint SP
    fig_sp_surface.png              — SP_pools × SP_economic scatter on E×C surface
    fig_sp_top_scenarios.png        — parameter profiles of top joint-SP scenarios
    sp_report.md                    — human-readable summary
"""

import argparse
import json
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
# Configuration — mirrors fit_boundary.py and plot_decision_boundary.py
# =============================================================================

DB_PATH     = Path('tools/sweep/sweep_results.db')
OUTPUT_DIR  = Path('tools/discovery/output/sp')

ACTIVE_PARAMS = [
    'economic_split',
    'pool_committed_split',
    'pool_ideology_strength',
    'pool_max_loss_pct',
]

# Full 2016-block dataset (VALID_SWEEPS_2016 + Phase 3 full-network)
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
    'lhs_2016_full_phase3_merged',
]

# Structural thresholds from Phase 1–3 findings
ECON_CASCADE_FLOOR  = 0.50   # below this v27 cannot win (economic layer inactive)
ECON_ESP            = 0.74   # Economic Self-Sustaining Point — max SP_economic
ECON_OVERRIDE       = 0.82   # above this v27 wins regardless (economic layer inactive)
COMMITTED_THRESHOLD = 0.296  # Phase 3 transition zone committed_split threshold
FOUNDRY_FLIP        = 0.214  # Foundry flip-point — structural boundary

# PRIM uncertainty box (from fit_boundary.py, n=295)
PRIM_BOX = {
    'economic_split':         (0.28, 0.78),
    'pool_committed_split':   (0.15, 0.53),
    'pool_ideology_strength': (0.44, 0.80),
    'pool_max_loss_pct':      (0.16, 0.40),
}

RF_N_ESTIMATORS = 600
RF_RANDOM_STATE = 42
GRADIENT_DELTA  = 0.01   # step size for numerical gradient computation
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
            s.economic_split,
            s.pool_committed_split,
            s.pool_ideology_strength,
            s.pool_max_loss_pct,
            s.outcome,
            s.total_reorgs,
            s.reorg_mass,
            s.cascade_time_s,
            s.econ_lag_s,
            s.duration,
            s.scenario_id
        FROM scenarios s
        JOIN sweeps sr ON s.sweep_id = sr.sweep_id
        WHERE sr.sweep_name IN ({placeholders})
          AND s.outcome IN ('v27_dominant', 'v26_dominant', 'contested')
    """
    df = pd.read_sql_query(query, conn, params=VALID_SWEEPS_2016)
    conn.close()
    df = df.dropna(subset=ACTIVE_PARAMS).reset_index(drop=True)
    print(f"Loaded {len(df)} scenarios from {df['sweep_name'].nunique()} sweeps")
    return df


# =============================================================================
# RF training
# =============================================================================

def train_rf(df: pd.DataFrame) -> RandomForestClassifier:
    X = df[ACTIVE_PARAMS].values
    y = (df['outcome'] == 'v27_dominant').astype(int).values
    rf = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        oob_score=True,
        random_state=RF_RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X, y)
    print(f"RF OOB accuracy: {rf.oob_score_*100:.1f}%  "
          f"(n={len(X)}, v27_win_rate={y.mean()*100:.1f}%)")
    return rf


# =============================================================================
# Contentiousness (mirrors fit_boundary.py / user_prim.py)
# =============================================================================

def compute_contentiousness(df: pd.DataFrame) -> np.ndarray:
    scores = np.zeros(len(df))

    def normalize(arr, invert=False):
        arr = np.array(arr, dtype=float)
        arr = np.nan_to_num(arr, nan=0.0)
        if arr.max() == arr.min():
            return np.zeros_like(arr)
        n = (arr - arr.min()) / (arr.max() - arr.min())
        return 1 - n if invert else n

    if 'total_reorgs' in df.columns:
        scores += 0.3 * normalize(df['total_reorgs'].values)
    if 'reorg_mass' in df.columns:
        scores += 0.3 * normalize(df['reorg_mass'].values)
    if 'cascade_time_s' in df.columns:
        fill = df['duration'].max() if 'duration' in df.columns else 13000
        ct = df['cascade_time_s'].fillna(fill).values
        scores += 0.2 * normalize(ct, invert=True)
    if 'econ_lag_s' in df.columns:
        scores += 0.2 * normalize(np.abs(df['econ_lag_s'].fillna(0).values))

    return scores


# =============================================================================
# Scenario Potential computation
# =============================================================================

def compute_sp_pools(df: pd.DataFrame, rf: RandomForestClassifier) -> np.ndarray:
    """
    SP_pools — RF probability gradient with respect to pool_committed_split.

    For each scenario, numerically estimate |dP(v27_win)/d(pool_committed_split)|
    at that scenario's parameter values. High gradient = small change in committed
    hashrate structure flips the predicted outcome. Peaks near the committed_split
    decision boundary.

    Result is min-max normalized to [0, 1] across the dataset.
    """
    X = df[ACTIVE_PARAMS].values
    committed_idx = ACTIVE_PARAMS.index('pool_committed_split')

    sp = np.zeros(len(df))
    for i, row in enumerate(X):
        x_lo = row.copy()
        x_hi = row.copy()
        x_lo[committed_idx] = max(0.0, row[committed_idx] - GRADIENT_DELTA)
        x_hi[committed_idx] = min(1.0, row[committed_idx] + GRADIENT_DELTA)
        p_lo = rf.predict_proba(x_lo.reshape(1, -1))[0, 1]
        p_hi = rf.predict_proba(x_hi.reshape(1, -1))[0, 1]
        step = x_hi[committed_idx] - x_lo[committed_idx]
        sp[i] = abs(p_hi - p_lo) / step if step > 0 else 0.0

    # Min-max normalize
    lo, hi = sp.min(), sp.max()
    return (sp - lo) / (hi - lo) if hi > lo else np.zeros_like(sp)


def compute_sp_economic(df: pd.DataFrame, rf: RandomForestClassifier) -> np.ndarray:
    """
    SP_economic — RF probability gradient with respect to economic_split,
    gated by position in the inversion zone.

    Economic actors are only genuinely pivotal when economic_split is in the
    inversion zone [CASCADE_FLOOR, ECON_OVERRIDE]. Outside this range the outcome
    is structurally determined and exchange/custodian decisions cannot flip it.

    The raw gradient is computed the same way as SP_pools, then multiplied by
    a gate function that is 1.0 at the ESP (~0.74) and decays toward 0 at the
    zone boundaries. This reflects the structural ceiling: high gradient outside
    the inversion zone doesn't represent real governance leverage.

    Result is min-max normalized to [0, 1] across the dataset.
    """
    X = df[ACTIVE_PARAMS].values
    econ_idx = ACTIVE_PARAMS.index('economic_split')

    # Raw gradient
    grad = np.zeros(len(df))
    for i, row in enumerate(X):
        x_lo = row.copy()
        x_hi = row.copy()
        x_lo[econ_idx] = max(0.0, row[econ_idx] - GRADIENT_DELTA)
        x_hi[econ_idx] = min(1.0, row[econ_idx] + GRADIENT_DELTA)
        p_lo = rf.predict_proba(x_lo.reshape(1, -1))[0, 1]
        p_hi = rf.predict_proba(x_hi.reshape(1, -1))[0, 1]
        step = x_hi[econ_idx] - x_lo[econ_idx]
        grad[i] = abs(p_hi - p_lo) / step if step > 0 else 0.0

    # Inversion zone gate: triangular, peaks at ESP, 0 at zone boundaries
    econ_vals = df['economic_split'].values
    gate = np.zeros(len(df))
    for i, e in enumerate(econ_vals):
        if e < ECON_CASCADE_FLOOR or e > ECON_OVERRIDE:
            gate[i] = 0.0   # structurally determined — no economic leverage
        elif e <= ECON_ESP:
            gate[i] = (e - ECON_CASCADE_FLOOR) / (ECON_ESP - ECON_CASCADE_FLOOR)
        else:
            gate[i] = (ECON_OVERRIDE - e) / (ECON_OVERRIDE - ECON_ESP)

    sp = grad * gate

    # Min-max normalize
    lo, hi = sp.min(), sp.max()
    return (sp - lo) / (hi - lo) if hi > lo else np.zeros_like(sp)


def compute_z_joint(sp_pools: np.ndarray,
                    sp_economic: np.ndarray,
                    contentiousness: np.ndarray,
                    w_pools: float = 1.0,
                    w_econ: float = 1.0,
                    w_cont: float = 0.5) -> np.ndarray:
    """
    Joint governance leverage score.

    Z_joint = w_pools * SP_pools + w_econ * SP_economic + w_cont * contentiousness

    Contentiousness enters with lower weight — it's a precondition (outcome must
    be in play) but the primary interest is where actor leverage is highest.
    All inputs are already normalized to [0, 1].
    """
    def minmax(arr):
        lo, hi = arr.min(), arr.max()
        return (arr - lo) / (hi - lo) if hi > lo else np.zeros_like(arr)

    return w_pools * sp_pools + w_econ * sp_economic + w_cont * minmax(contentiousness)


# =============================================================================
# Surprise score — high SP but clean outcome
# =============================================================================

def compute_surprise(df: pd.DataFrame,
                     z_joint: np.ndarray,
                     rf: RandomForestClassifier) -> np.ndarray:
    """
    Surprise score: scenarios where governance leverage was high but the outcome
    resolved cleanly (low contentiousness, decisive outcome).

    surprise = Z_joint * (1 - outcome_certainty)

    outcome_certainty = |P(v27_win) - 0.5| * 2   (0 = 50/50, 1 = certain)

    High surprise = actor leverage was available but the dynamics resolved
    decisively anyway — the "least expected" scenarios.
    """
    X = df[ACTIVE_PARAMS].values
    probs = rf.predict_proba(X)[:, 1]
    certainty = np.abs(probs - 0.5) * 2
    return z_joint * (1 - certainty)


# =============================================================================
# Figures
# =============================================================================

PARAM_LABELS = {
    'economic_split':         'Economic split (E)',
    'pool_committed_split':   'Pool committed split (C)',
    'pool_ideology_strength': 'Pool ideology strength (I)',
    'pool_max_loss_pct':      'Pool max loss pct (M)',
}


def fig_sp_surface(df: pd.DataFrame, rf: RandomForestClassifier,
                   output_dir: Path):
    """
    Main SP surface figure: 3-panel layout.
      Left:   E×C with SP_pools color overlay + SP_economic contour
      Top-R:  SP_pools distribution by outcome
      Bot-R:  SP_economic distribution by outcome
    """
    fig = plt.figure(figsize=(14, 8))
    gs = gridspec.GridSpec(2, 2, width_ratios=[1.6, 1],
                           hspace=0.35, wspace=0.30,
                           left=0.07, right=0.97, top=0.91, bottom=0.09)

    ax_main = fig.add_subplot(gs[:, 0])
    ax_top  = fig.add_subplot(gs[0, 1])
    ax_bot  = fig.add_subplot(gs[1, 1])

    # --- Main panel: E×C scatter colored by Z_joint ---
    sp_pools    = df['sp_pools'].values
    sp_econ     = df['sp_economic'].values
    z_joint     = df['z_joint'].values

    sc = ax_main.scatter(
        df['economic_split'], df['pool_committed_split'],
        c=z_joint, cmap='plasma', s=35, alpha=0.8,
        vmin=0, vmax=z_joint.max(), zorder=4,
    )
    cbar = fig.colorbar(sc, ax=ax_main, fraction=0.046, pad=0.04)
    cbar.set_label('Z_joint (governance leverage)', fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    # Mark top-20 joint SP scenarios
    top_idx = np.argsort(z_joint)[-20:]
    ax_main.scatter(
        df['economic_split'].values[top_idx],
        df['pool_committed_split'].values[top_idx],
        s=90, marker='*', color='gold', edgecolors='black',
        linewidths=0.6, zorder=6, label='Top-20 joint SP',
    )

    # Threshold lines
    ax_main.axvline(ECON_CASCADE_FLOOR, color='#333333', lw=1.3, ls=':', alpha=0.8, zorder=5)
    ax_main.axvline(ECON_ESP,           color='#333333', lw=1.3, ls='--', alpha=0.8, zorder=5)
    ax_main.axvline(ECON_OVERRIDE,      color='#333333', lw=1.3, ls=':', alpha=0.8, zorder=5)
    ax_main.axhline(FOUNDRY_FLIP,       color='#555555', lw=1.0, ls=':', alpha=0.7, zorder=5)
    ax_main.axhline(COMMITTED_THRESHOLD,color='#555555', lw=1.0, ls='--', alpha=0.7, zorder=5)

    # PRIM uncertainty box
    pbox_x = PRIM_BOX['economic_split']
    pbox_y = PRIM_BOX['pool_committed_split']
    ax_main.add_patch(mpatches.FancyBboxPatch(
        (pbox_x[0], pbox_y[0]), pbox_x[1]-pbox_x[0], pbox_y[1]-pbox_y[0],
        boxstyle='square,pad=0', fill=False,
        edgecolor='dodgerblue', linewidth=1.8, linestyle='--', zorder=5,
    ))

    # Threshold labels
    y_top = df['pool_committed_split'].max()
    tkw = dict(fontsize=7.5, color='#111111',
               bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                         edgecolor='#aaaaaa', alpha=0.85))
    ax_main.text(ECON_CASCADE_FLOOR+0.01, y_top-0.02, f'Cascade\nfloor', va='top', ha='left', **tkw)
    ax_main.text(ECON_ESP,                y_top-0.02, f'ESP\n~0.74',     va='top', ha='center', **tkw)
    ax_main.text(ECON_OVERRIDE-0.01,      y_top-0.02, f'Override',       va='top', ha='right', **tkw)

    ax_main.set_xlabel(PARAM_LABELS['economic_split'], fontsize=9)
    ax_main.set_ylabel(PARAM_LABELS['pool_committed_split'], fontsize=9)
    ax_main.set_title('Joint Governance Leverage (Z_joint) — E×C projection',
                      fontsize=10, fontweight='bold')
    ax_main.legend(fontsize=8, loc='lower right')
    ax_main.tick_params(labelsize=8)

    # --- Right panels: SP distributions by outcome ---
    outcomes  = ['v27_dominant', 'v26_dominant', 'contested']
    colors    = {'v27_dominant': '#2ca02c', 'v26_dominant': '#d62728', 'contested': '#e6a800'}
    labels_ok = {'v27_dominant': 'v27 win', 'v26_dominant': 'v26 win', 'contested': 'Contested'}

    for ax, col, title in [
        (ax_top, 'sp_pools',    'SP_pools by outcome'),
        (ax_bot, 'sp_economic', 'SP_economic by outcome'),
    ]:
        data  = [df.loc[df['outcome'] == o, col].values for o in outcomes]
        bplot = ax.boxplot(data, patch_artist=True, notch=False,
                           medianprops=dict(color='black', lw=1.5))
        for patch, outcome in zip(bplot['boxes'], outcomes):
            patch.set_facecolor(colors[outcome])
            patch.set_alpha(0.7)
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels([labels_ok[o] for o in outcomes], fontsize=8)
        ax.set_ylabel(col, fontsize=8)
        ax.set_title(title, fontsize=9, fontweight='bold')
        ax.tick_params(labelsize=7)
        ax.set_ylim(-0.05, 1.05)

    fig.suptitle('Scenario Potential — Pool Coalitions and Economic Actors (2016-block)',
                 fontsize=12, fontweight='bold')

    out = output_dir / 'fig_sp_surface.png'
    plt.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out}")


def fig_sp_top_scenarios(df: pd.DataFrame, output_dir: Path, n_top: int = 15):
    """
    Parallel coordinates plot of the top-N scenarios by Z_joint.
    Shows which parameter combinations generate the highest governance leverage
    and how they relate to outcome and surprise score.
    """
    top = df.nlargest(n_top, 'z_joint').reset_index(drop=True)

    fig, axes = plt.subplots(1, 4, figsize=(13, 5), sharey=False)
    params = ACTIVE_PARAMS
    colors = {'v27_dominant': '#2ca02c', 'v26_dominant': '#d62728', 'contested': '#e6a800'}

    for i, row in top.iterrows():
        c = colors.get(row['outcome'], 'grey')
        vals = [row[p] for p in params]
        for j in range(len(params) - 1):
            axes[j].plot([0, 1], [vals[j], vals[j+1]], color=c, alpha=0.6, lw=1.5)
        # Last axis
        axes[-1].plot([0], [vals[-1]], 'o', color=c, alpha=0.6)

    for j, (ax, p) in enumerate(zip(axes, params)):
        ax.set_xlim(0, 1)
        ax.set_ylim(df[p].min() - 0.02, df[p].max() + 0.02)
        ax.set_xticks([])
        ax.set_ylabel(PARAM_LABELS[p], fontsize=8)
        ax.tick_params(labelsize=7)
        ax.axhline(df[p].median(), color='#aaaaaa', lw=0.8, ls='--', alpha=0.6)

    # Legend
    legend_els = [
        Line2D([0],[0], color='#2ca02c', lw=2, label='v27 win'),
        Line2D([0],[0], color='#d62728', lw=2, label='v26 win'),
        Line2D([0],[0], color='#e6a800', lw=2, label='Contested'),
    ]
    fig.legend(handles=legend_els, loc='lower center', ncol=3,
               fontsize=8, bbox_to_anchor=(0.5, 0.01))

    fig.suptitle(f'Top-{n_top} Scenarios by Joint Governance Leverage (Z_joint)',
                 fontsize=11, fontweight='bold')
    plt.tight_layout(rect=[0, 0.07, 1, 0.95])

    out = output_dir / 'fig_sp_top_scenarios.png'
    plt.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out}")


# =============================================================================
# Report
# =============================================================================

def write_report(df: pd.DataFrame, rf: RandomForestClassifier, output_dir: Path):
    top_joint   = df.nlargest(10, 'z_joint')
    top_surprise = df.nlargest(10, 'surprise')

    lines = [
        "# Scenario Potential Report — SP_pools and SP_economic",
        "",
        f"**Dataset:** n={len(df)} scenarios, {df['sweep_name'].nunique()} sweeps, 2016-block retarget",
        f"**RF OOB accuracy:** {rf.oob_score_*100:.1f}%",
        "",
        "## Score Distributions",
        "",
        "| Score | Mean | Median | Max | Std |",
        "|-------|:----:|:------:|:---:|:---:|",
    ]
    for col in ['sp_pools', 'sp_economic', 'z_joint', 'surprise']:
        s = df[col]
        lines.append(f"| {col} | {s.mean():.3f} | {s.median():.3f} | {s.max():.3f} | {s.std():.3f} |")

    lines += [
        "",
        "## Mean SP by Outcome",
        "",
        "| Outcome | n | Mean SP_pools | Mean SP_economic | Mean Z_joint |",
        "|---------|:-:|:-------------:|:----------------:|:------------:|",
    ]
    for outcome in ['v27_dominant', 'v26_dominant', 'contested']:
        sub = df[df['outcome'] == outcome]
        if len(sub):
            lines.append(
                f"| {outcome} | {len(sub)} "
                f"| {sub['sp_pools'].mean():.3f} "
                f"| {sub['sp_economic'].mean():.3f} "
                f"| {sub['z_joint'].mean():.3f} |"
            )

    lines += [
        "",
        "## Top-10 Scenarios by Joint Governance Leverage (Z_joint)",
        "",
        "| Rank | Sweep | Scenario | E | C | I | M | Outcome | SP_pools | SP_econ | Z_joint |",
        "|:----:|-------|----------|:-:|:-:|:-:|:-:|---------|:--------:|:-------:|:-------:|",
    ]
    for rank, (_, row) in enumerate(top_joint.iterrows(), 1):
        lines.append(
            f"| {rank} | {row['sweep_name']} | {row.get('scenario_id','')} "
            f"| {row['economic_split']:.3f} | {row['pool_committed_split']:.3f} "
            f"| {row['pool_ideology_strength']:.3f} | {row['pool_max_loss_pct']:.3f} "
            f"| {row['outcome']} "
            f"| {row['sp_pools']:.3f} | {row['sp_economic']:.3f} | {row['z_joint']:.3f} |"
        )

    lines += [
        "",
        "## Top-10 Surprise Scenarios (high leverage, clean resolution)",
        "",
        "These scenarios had high governance leverage available but resolved",
        "decisively anyway — the 'least expected' outcomes.",
        "",
        "| Rank | Sweep | Scenario | E | C | Outcome | Z_joint | Surprise |",
        "|:----:|-------|----------|:-:|:-:|---------|:-------:|:--------:|",
    ]
    for rank, (_, row) in enumerate(top_surprise.iterrows(), 1):
        lines.append(
            f"| {rank} | {row['sweep_name']} | {row.get('scenario_id','')} "
            f"| {row['economic_split']:.3f} | {row['pool_committed_split']:.3f} "
            f"| {row['outcome']} "
            f"| {row['z_joint']:.3f} | {row['surprise']:.3f} |"
        )

    lines += [
        "",
        "## Structural Notes",
        "",
        "**SP_pools** peaks near pool_committed_split ≈ 0.296 (Phase 3 transition threshold)",
        "and ≈ 0.214 (Foundry flip-point). It is computed as the RF probability gradient",
        "|dP(v27_win)/d(pool_committed_split)| — how rapidly the predicted outcome changes",
        "with a small shift in committed pool hashrate.",
        "",
        "**SP_economic** is gated to zero outside the inversion zone [0.50, 0.82].",
        "Outside this range the outcome is structurally determined regardless of exchange",
        "or custodian custody decisions. Within the zone it peaks near the ESP (≈0.74),",
        "where a small shift in economic custody crosses the self-sustaining threshold.",
        "",
        "**Surprise** = Z_joint × (1 - outcome_certainty). High surprise identifies",
        "scenarios where governance leverage was structurally available but dynamics",
        "resolved cleanly — counterintuitive outcomes from the actor leverage perspective.",
    ]

    out = output_dir / 'sp_report.md'
    out.write_text('\n'.join(lines))
    print(f"  Saved: {out}")


# =============================================================================
# Entry point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db', type=Path, default=DB_PATH,
                        help=f'sweep_results.db path (default: {DB_PATH})')
    parser.add_argument('--output-dir', type=Path, default=OUTPUT_DIR,
                        help=f'Output directory (default: {OUTPUT_DIR})')
    parser.add_argument('--w-pools', type=float, default=1.0,
                        help='Weight for SP_pools in Z_joint (default: 1.0)')
    parser.add_argument('--w-econ', type=float, default=1.0,
                        help='Weight for SP_economic in Z_joint (default: 1.0)')
    parser.add_argument('--w-cont', type=float, default=0.5,
                        help='Weight for contentiousness in Z_joint (default: 0.5)')
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== Loading data ===")
    df = load_data(args.db)

    print("\n=== Training RF ===")
    rf = train_rf(df)

    print("\n=== Computing contentiousness ===")
    df['contentiousness'] = compute_contentiousness(df)

    print("\n=== Computing SP_pools (RF gradient over pool_committed_split) ===")
    df['sp_pools'] = compute_sp_pools(df, rf)
    print(f"  SP_pools: mean={df['sp_pools'].mean():.3f}  max={df['sp_pools'].max():.3f}")

    print("\n=== Computing SP_economic (RF gradient over economic_split, gated) ===")
    df['sp_economic'] = compute_sp_economic(df, rf)
    print(f"  SP_economic: mean={df['sp_economic'].mean():.3f}  max={df['sp_economic'].max():.3f}")

    print("\n=== Computing Z_joint and surprise ===")
    df['z_joint'] = compute_z_joint(
        df['sp_pools'].values, df['sp_economic'].values,
        df['contentiousness'].values,
        w_pools=args.w_pools, w_econ=args.w_econ, w_cont=args.w_cont,
    )
    df['surprise'] = compute_surprise(df, df['z_joint'].values, rf)

    print("\n=== SP by outcome ===")
    for outcome in ['v27_dominant', 'v26_dominant', 'contested']:
        sub = df[df['outcome'] == outcome]
        if len(sub):
            print(f"  {outcome:20s} n={len(sub):4d}  "
                  f"SP_pools={sub['sp_pools'].mean():.3f}  "
                  f"SP_econ={sub['sp_economic'].mean():.3f}  "
                  f"Z_joint={sub['z_joint'].mean():.3f}")

    # Save scores CSV
    out_csv = args.output_dir / 'sp_scores.csv'
    df.to_csv(out_csv, index=False)
    print(f"\n  Saved: {out_csv}")

    # Save top scenarios JSON
    top20 = df.nlargest(20, 'z_joint')[
        ['sweep_name', 'scenario_id', 'economic_split', 'pool_committed_split',
         'pool_ideology_strength', 'pool_max_loss_pct', 'outcome',
         'sp_pools', 'sp_economic', 'z_joint', 'surprise']
    ].to_dict(orient='records')
    out_json = args.output_dir / 'sp_top_scenarios.json'
    out_json.write_text(json.dumps(top20, indent=2))
    print(f"  Saved: {out_json}")

    print("\n=== Generating figures ===")
    fig_sp_surface(df, rf, args.output_dir)
    fig_sp_top_scenarios(df, args.output_dir)

    print("\n=== Writing report ===")
    write_report(df, rf, args.output_dir)

    print("\nDone. Outputs in:", args.output_dir)


if __name__ == '__main__':
    main()
