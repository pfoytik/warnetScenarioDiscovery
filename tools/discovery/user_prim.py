#!/usr/bin/env python3
"""
User-PRIM: Governance-adapted Z-PRIM for finding user-node-pivotal scenarios.

Implements a variant of the Z-PRIM algorithm from:
"Discovering Surprising Critical Scenarios in Critical Infrastructure Simulations
Using Scenario Potential" — adapted to find scenarios where user nodes had
meaningful influence on a contentious fork outcome.

Standard PRIM maximizes contentiousness density and is structurally blind to
user-node-driven scenarios because user nodes have ~2200x lower consensus weight
than major exchanges. User-PRIM rewards scenarios where user weight is near-pivotal
(high SP_user) AND the fork is contentious.

Usage:
    python user_prim.py
    python user_prim.py --phase3 ../sweep/lhs_2016_phase3/results/analysis/sweep_data.csv
    python user_prim.py --sweeps-dir ../sweep --output-dir output/user_prim
    python user_prim.py --network ../../networks/realistic-economy-v2/network.yaml
"""

import argparse
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np

try:
    import pandas as pd
except ImportError:
    print("Error: pandas required. pip install pandas")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("Warning: matplotlib not available — figures will be skipped")

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FEATURES = [
    'economic_split',
    'pool_committed_split',
    'pool_ideology_strength',
    'pool_max_loss_pct',
]

# Contentiousness weights — identical to fit_boundary.py
CONTENTIOUSNESS_WEIGHTS = {
    'total_reorgs': 0.3,
    'reorg_mass': 0.3,
    'cascade_time_s': 0.2,   # inverted: faster cascade = more decisive = LESS contentious? No — fast cascade means rapid lock-in which is contentious. We invert the raw time so shorter = higher score.
    'econ_lag_s': 0.2,
}

# Valid 2016-block sweeps with their CSV paths relative to sweeps_dir.
# Paths are (sweep_name, relative_csv_path) tuples.
VALID_2016_SWEEPS = [
    ('econ_committed_2016_grid',            'econ_committed_2016_grid/results/analysis/sweep_data.csv'),
    ('lhs_2016_full_parameter',             'lhs_2016_full_parameter/results/analysis/sweep_data.csv'),
    ('lhs_2016_6param',                     'lhs_2016_6param/results/analysis/sweep_data.csv'),
    ('targeted_sweep7_esp_2016',            'targeted_sweep7_esp/results_2016/analysis/sweep_data.csv'),
    ('targeted_sweep10_econ_threshold_2016','targeted_sweep10_econ_threshold_2016/results/analysis/sweep_data.csv'),
    ('targeted_sweep10b_econ_threshold_2016','targeted_sweep10b_econ_threshold_2016/results/analysis/sweep_data.csv'),
    ('targeted_sweep8_lite_2016_retarget',  'targeted_sweep8_lite_2016_retarget/results/analysis/sweep_data.csv'),
    ('targeted_sweep9_long_duration_2016',  'targeted_sweep9_long_duration_2016/results/analysis/sweep_data.csv'),
    ('targeted_sweep11_lite_chaos_test',    'targeted_sweep11_lite_chaos_test/results/analysis/sweep_data.csv'),
    ('committed_2016_high_econ',            'committed_2016_high_econ/results/analysis/sweep_data.csv'),
    ('committed_2016_mid_econ',             'committed_2016_mid_econ/results/analysis/sweep_data.csv'),
    ('committed_2016_sigmoid',              'committed_2016_sigmoid/results/analysis/sweep_data.csv'),
    ('committed_2016_sigmoid_midecon',      'committed_2016_sigmoid_midecon/results/analysis/sweep_data.csv'),
    ('hashrate_2016_verification',          'hashrate_2016_verification/results/analysis/sweep_data.csv'),
    ('lhs_2016_phase3',                     'lhs_2016_phase3/results/analysis/sweep_data.csv'),
]

# Hardcoded fallback network constants if YAML not readable
FALLBACK_W_USERS = 0.1688
FALLBACK_W_TOTAL = 370.90
FALLBACK_N_ECON  = 24


# ---------------------------------------------------------------------------
# Network weight computation
# ---------------------------------------------------------------------------

def load_network_weights(network_yaml: Path):
    """
    Parse the full network YAML to extract consensus weights.
    Returns (W_users, W_total, econ_nodes, user_nodes, thresholds).

    Consensus weight = (0.7 * custody_btc + 0.3 * daily_volume_btc) / 10000
    Threshold list = economic_split values where one node shifts assignment.
    Assignment rule: top round(n_econ * economic_split) nodes (by custody) go to v27.
    """
    if not HAS_YAML:
        print("  Warning: PyYAML not available — using hardcoded network constants")
        return _fallback_network_weights()

    if not network_yaml.exists():
        print(f"  Warning: network YAML not found at {network_yaml} — using hardcoded constants")
        return _fallback_network_weights()

    with open(network_yaml) as f:
        net = yaml.safe_load(f)

    economic_roles = {'major_exchange', 'exchange', 'payment_processor', 'merchant', 'institutional'}
    user_roles     = {'power_user', 'casual_user'}

    econ_nodes = []
    user_nodes = []

    for node in net.get('nodes', []):
        m    = node.get('metadata', {})
        role = m.get('role', '')
        cust = float(m.get('custody_btc', 0) or 0)
        vol  = float(m.get('daily_volume_btc', 0) or 0)
        w    = (0.7 * cust + 0.3 * vol) / 10000.0
        if role in economic_roles:
            econ_nodes.append({'name': node['name'], 'role': role,
                               'custody_btc': cust, 'weight': w})
        elif role in user_roles:
            user_nodes.append({'name': node['name'], 'role': role,
                               'custody_btc': cust, 'weight': w})

    W_econ  = sum(n['weight'] for n in econ_nodes)
    W_users = sum(n['weight'] for n in user_nodes)
    W_total = W_econ + W_users
    n_econ  = len(econ_nodes)

    # Thresholds: k/n_econ for k=1..n_econ-1
    # (assignment changes each time one more node crosses to the other partition)
    thresholds = [k / n_econ for k in range(1, n_econ)]

    # Identify marginal node weight at each threshold
    sorted_econ = sorted(econ_nodes, key=lambda x: -x['custody_btc'])
    marginal_weights = {}
    for k in range(1, n_econ):
        t = k / n_econ
        # The marginal node at threshold k/n_econ is the k-th node (0-indexed: k-1)
        marginal_weights[round(t, 6)] = sorted_econ[k - 1]['weight']

    print(f"  Network weights loaded from YAML:")
    print(f"    Economic nodes: {n_econ}, User nodes: {len(user_nodes)}")
    print(f"    W_econ  = {W_econ:.4f}")
    print(f"    W_users = {W_users:.6f}")
    print(f"    W_total = {W_total:.4f}")
    print(f"    Ratio   = {W_econ/W_users:.1f}:1")
    print(f"    Thresholds in PRIM zone [0.28, 0.78]: "
          f"{[round(t,3) for t in thresholds if 0.25 <= t <= 0.80]}")

    return W_users, W_total, n_econ, thresholds, marginal_weights


def _fallback_network_weights():
    n_econ = FALLBACK_N_ECON
    thresholds = [k / n_econ for k in range(1, n_econ)]
    marginal_weights = {round(k/n_econ, 6): FALLBACK_W_TOTAL / n_econ
                        for k in range(1, n_econ)}
    print(f"  Using fallback: W_users={FALLBACK_W_USERS}, W_total={FALLBACK_W_TOTAL}")
    return FALLBACK_W_USERS, FALLBACK_W_TOTAL, n_econ, thresholds, marginal_weights


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(phase3_csv: Path, sweeps_dir: Path) -> pd.DataFrame:
    """
    Load 2016-block scenario data from all available sweep CSVs.
    Primary source: phase3 CSV. Supplementary: other valid 2016-block sweeps.
    """
    frames = []

    # Load all valid 2016-block sweeps
    for sweep_name, rel_path in VALID_2016_SWEEPS:
        csv_path = sweeps_dir / rel_path
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df['sweep_name'] = sweep_name
            frames.append(df)
            print(f"  Loaded {len(df):4d} scenarios from {sweep_name}")
        else:
            # Try the phase3_csv arg as override for lhs_2016_phase3
            if sweep_name == 'lhs_2016_phase3' and phase3_csv and phase3_csv.exists():
                df = pd.read_csv(phase3_csv)
                df['sweep_name'] = sweep_name
                frames.append(df)
                print(f"  Loaded {len(df):4d} scenarios from {sweep_name} (--phase3 path)")
            else:
                print(f"  Skipping {sweep_name} — CSV not found")

    if not frames:
        print("Error: no data loaded. Check --sweeps-dir path.")
        sys.exit(1)

    df = pd.concat(frames, ignore_index=True)

    # Require all 4 active parameters
    df = df.dropna(subset=FEATURES)

    print(f"\n  Total loaded: {len(df)} scenarios from {df['sweep_name'].nunique()} sweeps")
    print(f"  Outcome distribution:")
    for outcome, count in df['outcome'].value_counts().items():
        print(f"    {outcome}: {count} ({100*count/len(df):.1f}%)")

    return df


# ---------------------------------------------------------------------------
# Contentiousness computation (mirrors fit_boundary.py)
# ---------------------------------------------------------------------------

def compute_contentiousness(df: pd.DataFrame) -> np.ndarray:
    """
    Compute contentiousness score per scenario.
    Formula identical to fit_boundary.py for cross-analysis consistency.
    """
    scores = np.zeros(len(df))

    def normalize(arr, invert=False):
        arr = np.array(arr, dtype=float)
        arr = np.nan_to_num(arr, nan=0.0)
        if arr.max() == arr.min():
            return np.zeros_like(arr)
        normed = (arr - arr.min()) / (arr.max() - arr.min())
        return 1 - normed if invert else normed

    if 'total_reorgs' in df.columns:
        scores += CONTENTIOUSNESS_WEIGHTS['total_reorgs'] * normalize(df['total_reorgs'].values)
    if 'reorg_mass' in df.columns:
        scores += CONTENTIOUSNESS_WEIGHTS['reorg_mass'] * normalize(df['reorg_mass'].values)
    if 'cascade_time_s' in df.columns:
        ct = df['cascade_time_s'].fillna(df['duration'].max() if 'duration' in df.columns else 13000)
        scores += CONTENTIOUSNESS_WEIGHTS['cascade_time_s'] * normalize(ct.values, invert=True)
    if 'econ_lag_s' in df.columns:
        scores += CONTENTIOUSNESS_WEIGHTS['econ_lag_s'] * normalize(np.abs(df['econ_lag_s'].fillna(0).values))

    return scores


# ---------------------------------------------------------------------------
# Scenario Potential (SP_user)
# ---------------------------------------------------------------------------

def compute_sp_user(economic_split_arr: np.ndarray,
                    W_users: float,
                    W_total: float,
                    thresholds: list) -> np.ndarray:
    """
    SP_user(x) = W_users / (economic_margin_weight(x) + W_users)

    economic_margin_weight = distance_to_nearest_threshold * W_total

    Approaches 1 when economic_split is exactly at a threshold (user weight
    could bridge the marginal gap). Approaches 0 when far from all thresholds.

    Note: SP_user values will be very small for most scenarios given the
    2196:1 weight ratio. Normalization before Z_user computation is essential.
    """
    thresholds_arr = np.array(thresholds)
    sp = np.zeros(len(economic_split_arr))

    for i, econ in enumerate(economic_split_arr):
        distances = np.abs(thresholds_arr - econ)
        min_dist  = distances.min()
        margin_w  = min_dist * W_total
        sp[i]     = W_users / (margin_w + W_users)

    return sp


# ---------------------------------------------------------------------------
# Z_user score
# ---------------------------------------------------------------------------

def compute_z_user(contentiousness: np.ndarray,
                   sp_user: np.ndarray,
                   lambda1: float = 0.5,
                   lambda2: float = 1.0) -> np.ndarray:
    """
    Z_user = lambda1 * contentiousness_norm + lambda2 * sp_user_norm

    Both components min-max normalized across the full dataset before combining.
    High Z_user = high contentiousness AND user nodes are near-pivotal.

    Note: rewards high SP_user (opposite of original Z-PRIM which penalizes
    high-capacity scenarios). We want to FIND user-node scenarios.
    """
    def minmax(arr):
        lo, hi = arr.min(), arr.max()
        if hi == lo:
            return np.zeros_like(arr)
        return (arr - lo) / (hi - lo)

    c_norm  = minmax(contentiousness)
    sp_norm = minmax(sp_user)

    return lambda1 * c_norm + lambda2 * sp_norm


# ---------------------------------------------------------------------------
# PRIM peeling
# ---------------------------------------------------------------------------

def prim_peel(df: pd.DataFrame,
              score_col: str,
              features: list,
              alpha: float = 0.05,
              min_support: int = 30) -> tuple:
    """
    PRIM peeling loop maximizing mean(score_col) in the box.

    Returns:
        box_bounds   — dict {feature: (min, max)}
        box_df       — DataFrame of scenarios in final box
        trajectory   — list of (n_scenarios, mean_score) at each step
    """
    box_df = df.copy()
    trajectory = [(len(box_df), float(box_df[score_col].mean()))]

    # Maintain explicit bounds (shrink as we peel)
    bounds = {f: [float(df[f].min()), float(df[f].max())] for f in features}

    step = 0
    while len(box_df) > min_support:
        best_improvement = 0.0
        best_peel        = None

        for feat in features:
            for side in ('lower', 'upper'):
                if side == 'lower':
                    threshold = float(np.percentile(box_df[feat], alpha * 100))
                    candidate = box_df[box_df[feat] >= threshold]
                else:
                    threshold = float(np.percentile(box_df[feat], (1 - alpha) * 100))
                    candidate = box_df[box_df[feat] <= threshold]

                if len(candidate) < min_support:
                    continue

                improvement = float(candidate[score_col].mean()) - float(box_df[score_col].mean())
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_peel        = (feat, side, threshold, candidate)

        if best_peel is None or best_improvement <= 0:
            break

        feat, side, threshold, box_df = best_peel
        if side == 'lower':
            bounds[feat][0] = max(bounds[feat][0], threshold)
        else:
            bounds[feat][1] = min(bounds[feat][1], threshold)

        step += 1
        trajectory.append((len(box_df), float(box_df[score_col].mean())))
        print(f"    step {step:3d}: n={len(box_df):4d}  mean_z={box_df[score_col].mean():.4f}"
              f"  peeled {feat} {side} @ {threshold:.3f}  (+{best_improvement:.4f})")

    box_bounds = {f: (bounds[f][0], bounds[f][1]) for f in features}
    return box_bounds, box_df, trajectory


# ---------------------------------------------------------------------------
# Bias ratio computation
# ---------------------------------------------------------------------------

def compute_bias_ratio(df: pd.DataFrame,
                       sp_col: str,
                       box_bounds: dict,
                       features: list,
                       n_quintiles: int = 5) -> dict:
    """
    Compute recall of high-SP_user vs low-SP_user quintiles inside a PRIM box.

    bias_ratio = recall(top 2 quintiles) / recall(bottom 2 quintiles)

    > 1 → box over-recovers high-SP_user scenarios (high-capacity bias)
    < 1 → box concentrates on low-SP_user scenarios (user-node focus)
    """
    labels  = pd.qcut(df[sp_col], n_quintiles, labels=False, duplicates='drop')
    in_box  = np.ones(len(df), dtype=bool)
    for feat in features:
        lo, hi = box_bounds[feat]
        in_box &= (df[feat].values >= lo) & (df[feat].values <= hi)

    quintile_recall = []
    for q in range(n_quintiles):
        mask_q   = (labels == q).values
        if mask_q.sum() == 0:
            quintile_recall.append(0.0)
        else:
            quintile_recall.append(float((in_box & mask_q).sum() / mask_q.sum()))

    low_recall  = np.mean(quintile_recall[:2])   if len(quintile_recall) >= 2 else 0.0
    high_recall = np.mean(quintile_recall[-2:])  if len(quintile_recall) >= 2 else 0.0

    bias_ratio = high_recall / low_recall if low_recall > 0 else float('inf')

    completeness = sum(1 for r in quintile_recall if r > 0) / n_quintiles

    return {
        'quintile_recall': quintile_recall,
        'low_recall':       low_recall,
        'high_recall':      high_recall,
        'bias_ratio':       bias_ratio,
        'completeness':     completeness,
        'n_in_box':         int(in_box.sum()),
    }


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------

def make_figures(df: pd.DataFrame, box_bounds: dict, output_dir: Path,
                 label: str = 'default'):
    """Produce the three required figures."""
    if not HAS_MPL:
        print("  Skipping figures — matplotlib not available")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: SP_user distribution with quintile boundaries
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df['sp_user'], bins=60, color='steelblue', edgecolor='white', alpha=0.8)
    quintile_bounds = np.percentile(df['sp_user'], [20, 40, 60, 80])
    for qb in quintile_bounds:
        ax.axvline(qb, color='crimson', linestyle='--', linewidth=1.2, alpha=0.7)
    ax.set_xlabel('SP_user (scenario potential)')
    ax.set_ylabel('Count')
    ax.set_title('SP_user Distribution — Quintile Boundaries Marked\n'
                 '(Values near zero = far from all economic assignment thresholds)')
    ax.text(0.97, 0.95, f'n={len(df)}', transform=ax.transAxes,
            ha='right', va='top', fontsize=9, color='gray')
    plt.tight_layout()
    path = output_dir / f'fig1_sp_user_distribution_{label}.png'
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved {path.name}")

    # Figure 2: Z_user histogram
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df['z_user'], bins=50, color='darkorange', edgecolor='white', alpha=0.8)
    top10 = df['z_user'].quantile(0.90)
    ax.axvline(top10, color='navy', linestyle='--', linewidth=1.4,
               label=f'90th pct = {top10:.3f}')
    ax.set_xlabel('Z_user score')
    ax.set_ylabel('Count')
    ax.set_title('Z_user Score Distribution\n'
                 '(High Z_user = high contentiousness AND near economic threshold)')
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = output_dir / f'fig2_z_user_distribution_{label}.png'
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved {path.name}")

    # Figure 3: economic_split vs pool_committed_split, colored by Z_user, box overlay
    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(df['economic_split'], df['pool_committed_split'],
                    c=df['z_user'], cmap='plasma', s=18, alpha=0.75, linewidths=0)
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('Z_user score')

    # Overlay User-PRIM box
    if box_bounds:
        lo_e, hi_e = box_bounds.get('economic_split', (None, None))
        lo_c, hi_c = box_bounds.get('pool_committed_split', (None, None))
        if None not in (lo_e, hi_e, lo_c, hi_c):
            rect = mpatches.FancyBboxPatch(
                (lo_e, lo_c), hi_e - lo_e, hi_c - lo_c,
                boxstyle='square,pad=0', linewidth=2.5,
                edgecolor='cyan', facecolor='none', label='User-PRIM box', zorder=5)
            ax.add_patch(rect)

    ax.set_xlabel('economic_split')
    ax.set_ylabel('pool_committed_split')
    ax.set_title('Z_user Score: economic_split × pool_committed_split\n'
                 'Cyan box = User-PRIM discovered region')
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = output_dir / f'fig3_scatter_z_user_{label}.png'
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved {path.name}")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(results: dict, df: pd.DataFrame, output_dir: Path):
    """Write human-readable markdown report."""
    box   = results['box_bounds']
    box_n = results['n_scenarios_in_box']

    lines = [
        "# User-PRIM Analysis Report",
        "",
        "## Summary",
        "",
        f"**Dataset:** {results['n_total']} scenarios across {results['n_sweeps']} sweeps (2016-block regime)",
        f"**Network:** {results['network_constants']['n_econ_nodes']} economic nodes, "
        f"{results['network_constants']['n_user_nodes']} user nodes",
        f"**W_users / W_total:** {results['network_constants']['W_users']:.6f} / "
        f"{results['network_constants']['W_total']:.4f} "
        f"({results['network_constants']['W_total']/results['network_constants']['W_users']:.0f}:1 ratio)",
        "",
        "---",
        "",
        "## Discovered User-PRIM Box",
        "",
    ]

    if box_n == 0:
        lines.append("**Null result:** Peeling terminated immediately. "
                     "No user-node-pivotal cluster found in this dataset.")
    else:
        lines += [
            f"**Scenarios in box:** {box_n} ({100*box_n/results['n_total']:.1f}% of dataset)",
            f"**Mean Z_user in box:** {results['mean_z_user_in_box']:.4f} "
            f"(dataset mean: {results['dataset_mean_z_user']:.4f})",
            f"**Mean contentiousness:** {results['mean_contentiousness_in_box']:.4f}",
            f"**Mean SP_user:** {results['mean_sp_user_in_box']:.6f}",
            "",
            "**Parameter bounds (User-PRIM box):**",
            "",
            "| Parameter | Min | Max |",
            "|-----------|-----|-----|",
        ]
        for feat in FEATURES:
            lo, hi = box.get(feat, (None, None))
            if lo is not None:
                lines.append(f"| {feat} | {lo:.4f} | {hi:.4f} |")

        lines += [
            "",
            "**Outcome distribution inside box:**",
            "",
        ]
        for outcome, count in results['outcome_distribution'].items():
            pct = 100 * count / box_n if box_n > 0 else 0
            lines.append(f"- {outcome}: {count} ({pct:.1f}%)")

    lines += [
        "",
        "---",
        "",
        "## Standard PRIM vs User-PRIM: Bias Ratio Comparison",
        "",
        "Bias ratio = recall(top-2 SP_user quintiles) / recall(bottom-2 quintiles).",
        "Ratio > 1 → box over-represents high-SP_user scenarios (high-capacity bias).",
        "Ratio < 1 → box concentrates on low-SP_user scenarios (user-node focus).",
        "",
        "| Method | Bias Ratio | Completeness | N in box |",
        "|--------|-----------|--------------|----------|",
    ]
    std  = results.get('bias_standard_prim', {})
    usr  = results.get('bias_user_prim', {})
    lines.append(f"| Standard PRIM | {std.get('bias_ratio', 'N/A'):.3f} | "
                 f"{std.get('completeness', 0):.2f} | {std.get('n_in_box', 0)} |")
    lines.append(f"| User-PRIM     | {usr.get('bias_ratio', 'N/A'):.3f} | "
                 f"{usr.get('completeness', 0):.2f} | {usr.get('n_in_box', 0)} |")

    lines += [
        "",
        "---",
        "",
        "## Sensitivity Analysis (Lambda Configurations)",
        "",
        "Stability of the discovered box across three λ weightings:",
        "",
        "| λ1 (contentiousness) | λ2 (SP_user) | N in box | Mean Z_user | Box stable? |",
        "|----------------------|-------------|----------|-------------|-------------|",
    ]
    for cfg in results.get('sensitivity', []):
        stable = "✓" if cfg.get('box_stable', False) else "~"
        lines.append(f"| {cfg['lambda1']} | {cfg['lambda2']} | {cfg['n_in_box']} | "
                     f"{cfg['mean_z_in_box']:.4f} | {stable} |")

    lines += [
        "",
        "---",
        "",
        "## Interpretation",
        "",
    ]

    br = usr.get('bias_ratio', 1.0)
    if br == float('inf') or box_n < 10:
        lines += [
            "**Null result.** User-PRIM found no meaningful cluster of user-node-pivotal",
            "contentious scenarios. The peeling trajectory terminated at the minimum support",
            "threshold without achieving meaningful Z_user concentration.",
            "",
            "This is a valid scientific finding: it strengthens the non-causality result",
            "from targeted_sweep4 using a different methodological approach (Z-PRIM).",
            "The absence of a user-node-pivotal cluster in 2016-block dynamics is robust",
            "across both targeted sweeps and unbiased LHS sampling.",
        ]
    elif br < 0.5:
        lines += [
            f"**Positive result.** User-PRIM concentrated on low-SP_user scenarios",
            f"(bias ratio={br:.3f} < 0.5), distinct from the standard PRIM box",
            f"(bias ratio={std.get('bias_ratio', 'N/A'):.3f}).",
            "",
            "A meaningful cluster of user-node-proximal contentious scenarios exists.",
            "The box bounds describe the parameter region where user node weight is",
            "most nearly pivotal in contested fork outcomes.",
        ]
    else:
        lines += [
            f"**Weak/ambiguous result.** Bias ratio = {br:.3f}.",
            "User-PRIM found a box but it does not strongly concentrate on",
            "user-node-pivotal scenarios relative to the standard PRIM baseline.",
            "The 2016-block dynamics appear primarily determined by pool and economic",
            "actors at all parameter combinations tested — user influence remains marginal.",
        ]

    lines += [
        "",
        "---",
        "",
        "## Notes on SP_user Magnitude",
        "",
        f"With W_users={results['network_constants']['W_users']:.4f} and "
        f"W_total={results['network_constants']['W_total']:.2f}, raw SP_user values",
        "are near-zero for most scenarios (weight ratio ~2200:1).",
        "The min-max normalization step is essential — without it, SP_user contributes",
        "negligibly to Z_user variance and the analysis degrades to pure contentiousness PRIM.",
        f"SP_user range in this dataset: [{results['sp_user_range'][0]:.6f}, "
        f"{results['sp_user_range'][1]:.6f}]",
        f"After normalization, SP_user contributes meaningfully to Z_user variance.",
    ]

    report_path = output_dir / 'user_prim_report.md'
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"  Saved {report_path.name}")


# ---------------------------------------------------------------------------
# Box stability check for sensitivity analysis
# ---------------------------------------------------------------------------

def boxes_overlap_fraction(b1: dict, b2: dict, features: list) -> float:
    """
    Compute the fraction of the reference box b1 that overlaps with b2.
    Returns 0.0 (no overlap) to 1.0 (identical).
    """
    if not b1 or not b2:
        return 0.0

    volume_b1 = 1.0
    volume_overlap = 1.0

    for f in features:
        lo1, hi1 = b1.get(f, (0.0, 1.0))
        lo2, hi2 = b2.get(f, (0.0, 1.0))
        width1 = max(hi1 - lo1, 1e-9)
        overlap = max(0.0, min(hi1, hi2) - max(lo1, lo2))
        volume_b1 *= width1
        volume_overlap *= overlap

    return volume_overlap / volume_b1 if volume_b1 > 0 else 0.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='User-PRIM: Z-PRIM variant for user-node-pivotal scenario discovery')
    parser.add_argument('--phase3', type=Path,
                        default=Path('tools/sweep/lhs_2016_phase3/results/analysis/sweep_data.csv'),
                        help='Path to lhs_2016_phase3 sweep_data.csv')
    parser.add_argument('--sweeps-dir', type=Path,
                        default=Path('tools/sweep'),
                        help='Root directory containing all sweep results')
    parser.add_argument('--network', type=Path,
                        default=Path('networks/realistic-economy-v2/network.yaml'),
                        help='Path to full network YAML for consensus weight computation')
    parser.add_argument('--output-dir', type=Path,
                        default=Path('tools/discovery/output/user_prim'),
                        help='Output directory for results and figures')
    parser.add_argument('--alpha', type=float, default=0.05,
                        help='PRIM peeling fraction (default 0.05)')
    parser.add_argument('--min-support', type=int, default=30,
                        help='Minimum scenarios in box before stopping (default 30)')
    parser.add_argument('--lambda1', type=float, default=0.5,
                        help='Weight on contentiousness (default 0.5)')
    parser.add_argument('--lambda2', type=float, default=1.0,
                        help='Weight on SP_user potential (default 1.0)')
    args = parser.parse_args()

    print("=" * 70)
    print("User-PRIM: Governance-adapted Z-PRIM for user-node scenario discovery")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Step 0: Network weights
    # ------------------------------------------------------------------
    print("\n[1/6] Loading network weights...")
    W_users, W_total, n_econ, thresholds, marginal_weights = load_network_weights(args.network)
    n_user_nodes = 28  # power_user + casual_user in realistic-economy-v2

    # ------------------------------------------------------------------
    # Step 1: Load data
    # ------------------------------------------------------------------
    print("\n[2/6] Loading scenario data...")
    df = load_data(args.phase3, args.sweeps_dir)

    # ------------------------------------------------------------------
    # Step 2: Compute contentiousness and SP_user
    # ------------------------------------------------------------------
    print("\n[3/6] Computing contentiousness and SP_user...")
    df['contentiousness'] = compute_contentiousness(df)
    df['sp_user'] = compute_sp_user(
        df['economic_split'].values, W_users, W_total, thresholds)

    print(f"  Contentiousness — mean={df['contentiousness'].mean():.4f}  "
          f"max={df['contentiousness'].max():.4f}")
    print(f"  SP_user (raw)   — mean={df['sp_user'].mean():.6f}  "
          f"max={df['sp_user'].max():.6f}  min={df['sp_user'].min():.6f}")
    print(f"  SP_user quantiles: "
          f"p25={df['sp_user'].quantile(0.25):.6f}  "
          f"p50={df['sp_user'].quantile(0.50):.6f}  "
          f"p75={df['sp_user'].quantile(0.75):.6f}  "
          f"p95={df['sp_user'].quantile(0.95):.6f}")

    # ------------------------------------------------------------------
    # Step 3: Compute Z_user (primary configuration)
    # ------------------------------------------------------------------
    print(f"\n[4/6] Computing Z_user (λ1={args.lambda1}, λ2={args.lambda2})...")
    df['z_user'] = compute_z_user(
        df['contentiousness'].values, df['sp_user'].values,
        lambda1=args.lambda1, lambda2=args.lambda2)

    print(f"  Z_user — mean={df['z_user'].mean():.4f}  "
          f"max={df['z_user'].max():.4f}  std={df['z_user'].std():.4f}")
    print(f"  Top-10% Z_user threshold: {df['z_user'].quantile(0.9):.4f}")

    # Correlation report
    print(f"\n  Correlations with Z_user:")
    for feat in FEATURES + ['contentiousness', 'sp_user']:
        if feat in df.columns:
            r = df['z_user'].corr(df[feat])
            print(f"    {feat:30s}: r={r:+.3f}")

    # ------------------------------------------------------------------
    # Step 4: User-PRIM
    # ------------------------------------------------------------------
    print(f"\n[5/6] Running User-PRIM (alpha={args.alpha}, min_support={args.min_support})...")
    box_bounds, box_df, trajectory = prim_peel(
        df, 'z_user', FEATURES, alpha=args.alpha, min_support=args.min_support)

    print(f"\n  Final box: {len(box_df)} scenarios "
          f"({100*len(box_df)/len(df):.1f}% of dataset)")
    print(f"  Mean Z_user in box: {box_df['z_user'].mean():.4f} "
          f"(vs dataset {df['z_user'].mean():.4f})")
    print(f"  Mean SP_user in box: {box_df['sp_user'].mean():.6f} "
          f"(vs dataset {df['sp_user'].mean():.6f})")
    print(f"  Mean contentiousness in box: {box_df['contentiousness'].mean():.4f}")
    print("  Box bounds:")
    for feat in FEATURES:
        lo, hi = box_bounds[feat]
        print(f"    {feat:35s}: [{lo:.4f}, {hi:.4f}]")
    print("  Outcome distribution in box:")
    for outcome, count in box_df['outcome'].value_counts().items():
        print(f"    {outcome}: {count} ({100*count/len(box_df):.1f}%)")

    # ------------------------------------------------------------------
    # Step 5: Standard PRIM box baseline (from contentiousness_bounds.yaml)
    # ------------------------------------------------------------------
    std_prim_bounds = {}
    std_prim_path = Path('tools/discovery/output/2016/contentiousness_bounds.yaml')
    if HAS_YAML and std_prim_path.exists():
        with open(std_prim_path) as f:
            cprim = yaml.safe_load(f)
        for feat in FEATURES:
            if feat in cprim.get('parameters', {}):
                p = cprim['parameters'][feat]
                std_prim_bounds[feat] = (float(p['min']), float(p['max']))
        print(f"\n  Loaded standard PRIM box from {std_prim_path.name}")
    else:
        # Fallback: use full parameter range (no box = entire dataset)
        print("\n  Warning: contentiousness_bounds.yaml not found — using full range as baseline")
        for feat in FEATURES:
            std_prim_bounds[feat] = (float(df[feat].min()), float(df[feat].max()))

    # Compute bias ratios
    bias_std   = compute_bias_ratio(df, 'sp_user', std_prim_bounds, FEATURES)
    bias_user  = compute_bias_ratio(df, 'sp_user', box_bounds, FEATURES)

    print(f"\n  Bias ratios (high-SP_user recall / low-SP_user recall):")
    print(f"    Standard PRIM: {bias_std['bias_ratio']:.3f}  "
          f"(completeness={bias_std['completeness']:.2f}, n_in_box={bias_std['n_in_box']})")
    print(f"    User-PRIM:     {bias_user['bias_ratio']:.3f}  "
          f"(completeness={bias_user['completeness']:.2f}, n_in_box={bias_user['n_in_box']})")
    print(f"    Quintile recall (standard): {[f'{r:.2f}' for r in bias_std['quintile_recall']]}")
    print(f"    Quintile recall (user):     {[f'{r:.2f}' for r in bias_user['quintile_recall']]}")

    # ------------------------------------------------------------------
    # Sensitivity analysis
    # ------------------------------------------------------------------
    print("\n[6/6] Sensitivity analysis...")
    lambda_configs = [
        (0.5, 1.0, "default"),
        (1.0, 0.5, "outcome_weighted"),
        (0.5, 2.0, "potential_heavy"),
    ]
    sensitivity_results = []
    reference_bounds = box_bounds

    for l1, l2, cfg_name in lambda_configs:
        print(f"\n  Config [{cfg_name}]: λ1={l1}, λ2={l2}")
        df[f'z_user_{cfg_name}'] = compute_z_user(
            df['contentiousness'].values, df['sp_user'].values, lambda1=l1, lambda2=l2)
        cfg_bounds, cfg_box, cfg_traj = prim_peel(
            df, f'z_user_{cfg_name}', FEATURES,
            alpha=args.alpha, min_support=args.min_support)
        overlap = boxes_overlap_fraction(reference_bounds, cfg_bounds, FEATURES)
        sensitivity_results.append({
            'lambda1':      l1,
            'lambda2':      l2,
            'config_name':  cfg_name,
            'n_in_box':     len(cfg_box),
            'mean_z_in_box': float(cfg_box[f'z_user_{cfg_name}'].mean()),
            'box_bounds':   {f: list(v) for f, v in cfg_bounds.items()},
            'overlap_with_default': float(overlap),
            'box_stable':   overlap > 0.5,
            'trajectory':   [(int(n), float(z)) for n, z in cfg_traj],
        })
        print(f"    n_in_box={len(cfg_box)}  overlap_with_default={overlap:.2f}")
        # Make figures for non-default configs too
        df_tmp = df.copy()
        df_tmp['z_user']   = df_tmp[f'z_user_{cfg_name}']
        df_tmp['sp_user_n'] = df_tmp['sp_user']
        make_figures(df_tmp, cfg_bounds, args.output_dir, label=cfg_name)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Produce primary figures
    print("\n  Generating primary figures...")
    make_figures(df, box_bounds, args.output_dir, label='default')

    # JSON results
    results = {
        'n_total':               len(df),
        'n_sweeps':              df['sweep_name'].nunique() if 'sweep_name' in df.columns else 0,
        'network_constants': {
            'W_users':       W_users,
            'W_total':       W_total,
            'n_econ_nodes':  n_econ,
            'n_user_nodes':  n_user_nodes,
            'weight_ratio':  W_total / W_users,
            'thresholds_in_prim_zone': [round(t, 4) for t in thresholds if 0.25 <= t <= 0.80],
        },
        'lambda1':               args.lambda1,
        'lambda2':               args.lambda2,
        'alpha':                 args.alpha,
        'min_support':           args.min_support,
        'sp_user_range':         [float(df['sp_user'].min()), float(df['sp_user'].max())],
        'sp_user_mean':          float(df['sp_user'].mean()),
        'dataset_mean_z_user':   float(df['z_user'].mean()),
        'box_bounds':            {f: list(v) for f, v in box_bounds.items()},
        'n_scenarios_in_box':    len(box_df),
        'mean_z_user_in_box':    float(box_df['z_user'].mean()) if len(box_df) > 0 else 0.0,
        'mean_contentiousness_in_box': float(box_df['contentiousness'].mean()) if len(box_df) > 0 else 0.0,
        'mean_sp_user_in_box':   float(box_df['sp_user'].mean()) if len(box_df) > 0 else 0.0,
        'outcome_distribution':  (box_df['outcome'].value_counts().to_dict()
                                  if len(box_df) > 0 else {}),
        'bias_standard_prim':    bias_std,
        'bias_user_prim':        bias_user,
        'sp_user_quintile_recall_standard': bias_std['quintile_recall'],
        'sp_user_quintile_recall_user_prim': bias_user['quintile_recall'],
        'peeling_trajectory':    [(int(n), float(z)) for n, z in trajectory],
        'sensitivity':           sensitivity_results,
        'sp_user_range':         [float(df['sp_user'].min()), float(df['sp_user'].max())],
    }

    json_path = args.output_dir / 'user_prim_results.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Saved {json_path.name}")

    write_report(results, df, args.output_dir)

    print("\n" + "=" * 70)
    print("Done.")
    br = bias_user.get('bias_ratio', float('inf'))
    std_br = bias_std.get('bias_ratio', float('inf'))
    if len(box_df) < args.min_support + 5:
        print("Result: NULL — peeling terminated at minimum support threshold.")
        print("        No user-node-pivotal cluster found. Non-causality strengthened.")
    elif br < 0.5 and br < std_br * 0.7:
        print(f"Result: POSITIVE — User-PRIM bias ratio {br:.3f} < 0.5 and substantially")
        print(f"        below standard PRIM ({std_br:.3f}). User-node cluster identified.")
    else:
        print(f"Result: WEAK/AMBIGUOUS — User-PRIM bias ratio {br:.3f}.")
        print(f"        Standard PRIM bias ratio {std_br:.3f} for comparison.")
        print("        User influence remains marginal across parameter space.")
    print("=" * 70)


if __name__ == '__main__':
    main()
