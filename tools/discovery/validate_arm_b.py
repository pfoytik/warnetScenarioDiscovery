#!/usr/bin/env python3
"""
Arm B Out-of-Sample Validation of the 2016-Block Boundary Model
================================================================
Refits the 2016-block logistic + RF boundary model on VALID_SWEEPS_2016
(identical to fit_boundary.py) then evaluates it on arm_b WITHOUT
including arm_b in training. This answers: does the existing boundary
model predict arm_b outcomes, and where does it fail?

Also computes the economic override threshold E₅₀ from the refitted
model's predictions over the (E, C) plane, comparing to arm_b's
observed E₅₀ ≈ 0.715.

Usage:
    python tools/discovery/validate_arm_b.py --db tools/sweep/sweep_results.db
"""

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.special import expit
from scipy.optimize import brentq
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, classification_report,
                             brier_score_loss, roc_auc_score)


# ── Sweep lists (identical to fit_boundary.py) ────────────────────────────────
VALID_SWEEPS_2016 = [
    'econ_committed_2016_grid',
    'lhs_2016_full_parameter',
    'lhs_2016_6param',
    'lhs_2016_full_6param',
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
]

ACTIVE_PARAMS = [
    'economic_split',
    'pool_committed_split',
    'pool_ideology_strength',
    'pool_max_loss_pct',
]


# ── Data loading ───────────────────────────────────────────────────────────────

def load_sweep(db_path: str, sweep_names: list[str]) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    placeholders = ','.join(['?'] * len(sweep_names))
    df = pd.read_sql_query(f"""
        SELECT sr.sweep_name, s.*
        FROM scenarios s
        JOIN sweeps sr ON s.sweep_id = sr.sweep_id
        WHERE sr.sweep_name IN ({placeholders})
    """, conn, params=sweep_names)
    conn.close()
    return df


def prepare(df: pd.DataFrame, params: list[str]):
    """Return (X, y, df_clean) with interaction features added."""
    mask = df[params].notna().all(axis=1) & df['outcome'].notna()
    df_c = df[mask].copy()
    y = (df_c['outcome'] == 'v27_dominant').astype(int).values

    X = df_c[params].values.astype(float)
    names = list(params)

    # Pairwise interactions
    n = len(params)
    for i in range(n):
        for j in range(i + 1, n):
            X = np.column_stack([X, X[:, i] * X[:, j]])
            names.append(f"{params[i]}*{params[j]}")

    return X, y, df_c, names


# ── Model fitting ──────────────────────────────────────────────────────────────

def fit_models(X_train, y_train):
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X_train)

    log_model = LogisticRegression(penalty='l2', C=1.0, max_iter=1000,
                                   solver='lbfgs', random_state=42)
    log_model.fit(X_sc, y_train)

    rf_model = RandomForestClassifier(n_estimators=500, max_depth=None,
                                      min_samples_leaf=5, random_state=42,
                                      n_jobs=-1)
    rf_model.fit(X_train, y_train)   # RF uses raw (unscaled) features

    return log_model, scaler, rf_model


# ── E₅₀ from model predictions ────────────────────────────────────────────────

def model_e50_at_low_c(log_model, scaler, params, ideology=0.51, max_loss=0.26,
                        c_vals=(0.10, 0.15)):
    """
    Find E where logistic model predicts 50% win rate, evaluated at low C values.
    Uses the marginal mean over c_vals.
    """
    def mean_prob_at_e(e):
        probs = []
        for c in c_vals:
            row = np.array([[e, c, ideology, max_loss]])
            n = len(params)
            idx = 0
            for i in range(n):
                for j in range(i + 1, n):
                    row = np.column_stack([row, row[:, i] * row[:, j]])
                    idx += 1
            p = log_model.predict_proba(scaler.transform(row))[0, 1]
            probs.append(p)
        return np.mean(probs) - 0.5

    try:
        e50 = brentq(mean_prob_at_e, 0.3, 0.99)
        return e50
    except ValueError:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='tools/sweep/sweep_results.db')
    parser.add_argument('--output-dir',
                        default='tools/discovery/output/arm_b_validation')
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── Load training data (VALID_SWEEPS_2016) ────────────────────────────────
    print("Loading training data (VALID_SWEEPS_2016)...")
    df_train_raw = load_sweep(args.db, VALID_SWEEPS_2016)
    X_tr, y_tr, df_tr, feat_names = prepare(df_train_raw, ACTIVE_PARAMS)
    print(f"  {len(y_tr)} training scenarios  ({y_tr.sum()} v27 wins)")

    # ── Load arm_b (held-out) ─────────────────────────────────────────────────
    print("Loading arm_b (held-out test set)...")
    df_b_raw = load_sweep(args.db, ['pool_composition_arm_b'])
    X_b, y_b, df_b, _ = prepare(df_b_raw, ACTIVE_PARAMS)
    print(f"  {len(y_b)} arm_b scenarios  ({y_b.sum()} v27 wins)")

    # ── Fit models ────────────────────────────────────────────────────────────
    print("\nFitting logistic + RF on training data...")
    log_model, scaler, rf_model = fit_models(X_tr, y_tr)

    # Training accuracy (sanity check matches saved coefficients.json)
    X_tr_sc = scaler.transform(X_tr)
    tr_acc = accuracy_score(y_tr, log_model.predict(X_tr_sc))
    print(f"  Train accuracy (logistic): {tr_acc:.3f}")

    # ── Predict on arm_b ──────────────────────────────────────────────────────
    X_b_sc = scaler.transform(X_b)
    log_prob_b  = log_model.predict_proba(X_b_sc)[:, 1]
    log_pred_b  = (log_prob_b >= 0.5).astype(int)
    rf_prob_b   = rf_model.predict_proba(X_b)[:, 1]
    rf_pred_b   = (rf_prob_b >= 0.5).astype(int)

    log_acc  = accuracy_score(y_b, log_pred_b)
    rf_acc   = accuracy_score(y_b, rf_pred_b)
    log_brier = brier_score_loss(y_b, log_prob_b)
    rf_brier  = brier_score_loss(y_b, rf_prob_b)
    log_auc   = roc_auc_score(y_b, log_prob_b)
    rf_auc    = roc_auc_score(y_b, rf_prob_b)

    print(f"\n{'='*60}")
    print("ARM B OUT-OF-SAMPLE VALIDATION")
    print(f"{'='*60}")
    print(f"\n  {'Metric':<22} {'Logistic':>10}  {'RF':>10}")
    print(f"  {'-'*22}  {'-'*10}  {'-'*10}")
    print(f"  {'Accuracy':<22} {log_acc:>10.3f}  {rf_acc:>10.3f}")
    print(f"  {'Brier score':<22} {log_brier:>10.3f}  {rf_brier:>10.3f}")
    print(f"  {'ROC-AUC':<22} {log_auc:>10.3f}  {rf_auc:>10.3f}")

    # ── Per-cell predicted vs observed ────────────────────────────────────────
    df_b['log_prob'] = log_prob_b
    df_b['rf_prob']  = rf_prob_b
    df_b['y_true']   = y_b
    df_b['log_correct'] = (log_pred_b == y_b)
    df_b['rf_correct']  = (rf_pred_b  == y_b)

    e_vals = sorted(df_b['economic_split'].unique())
    c_vals = sorted(df_b['pool_committed_split'].unique())

    print(f"\nPer-cell: observed win rate vs logistic predicted probability")
    print(f"  {'E':<6}  {'C':<6}  {'obs':>6}  {'n':>4}  {'log_pred':>9}  {'rf_pred':>9}  {'error':>7}")
    print(f"  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*4}  {'-'*9}  {'-'*9}  {'-'*7}")

    cell_results = []
    for e in e_vals:
        for c in c_vals:
            mask = (df_b['economic_split'].round(4) == round(e, 4)) & \
                   (df_b['pool_committed_split'].round(4) == round(c, 4))
            sub = df_b[mask]
            if len(sub) == 0:
                continue
            obs  = sub['y_true'].mean()
            lp   = sub['log_prob'].mean()
            rp   = sub['rf_prob'].mean()
            err  = lp - obs
            flag = " ←" if abs(err) > 0.30 else ""
            print(f"  {e:<6}  {c:<6}  {obs:>6.3f}  {len(sub):>4}  "
                  f"{lp:>9.3f}  {rp:>9.3f}  {err:>+7.3f}{flag}")
            cell_results.append({'e': e, 'c': c, 'obs': obs, 'log_pred': lp,
                                  'rf_pred': rp, 'n': len(sub)})

    # ── E₅₀ comparison ───────────────────────────────────────────────────────
    model_e50 = model_e50_at_low_c(log_model, scaler, ACTIVE_PARAMS)
    observed_e50 = 0.715   # from logistic fit on arm_b data (boundary comparison)

    print(f"\n{'='*60}")
    print("ECONOMIC OVERRIDE THRESHOLD COMPARISON")
    print(f"{'='*60}")
    print(f"  Boundary model (logistic, at C≤0.15):  E₅₀ = "
          f"{model_e50:.3f}" if model_e50 else "  Boundary model: no crossing found")
    print(f"  Arm B observed (logistic fit on data):  E₅₀ = {observed_e50:.3f}")
    if model_e50:
        delta = observed_e50 - model_e50
        print(f"  Delta:                                  {delta:+.3f}")
        print(f"  {'Model underestimates' if delta > 0 else 'Model overestimates'} the threshold "
              f"by {abs(delta):.3f}")

    # ── Calibration plot ─────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Panel 1: calibration scatter (mean predicted vs observed per cell)
    ax = axes[0]
    obs_arr  = [r['obs']      for r in cell_results]
    log_arr  = [r['log_pred'] for r in cell_results]
    rf_arr   = [r['rf_pred']  for r in cell_results]
    n_arr    = [r['n']        for r in cell_results]

    ax.scatter(log_arr, obs_arr, s=[n*15 for n in n_arr], alpha=0.7,
               color='#cc4444', label='Logistic', zorder=4)
    ax.scatter(rf_arr,  obs_arr, s=[n*15 for n in n_arr], alpha=0.7,
               color='#2255cc', marker='^', label='RF', zorder=4)
    ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5, label='Perfect calibration')
    ax.set_xlabel("Mean predicted probability", fontsize=10)
    ax.set_ylabel("Observed win rate", fontsize=10)
    ax.set_title("Calibration: Model Predictions vs Arm B Observations\n(point size ∝ n)", fontsize=9)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.text(0.05, 0.92,
            f"Logistic  acc={log_acc:.2f}  AUC={log_auc:.2f}\n"
            f"RF        acc={rf_acc:.2f}  AUC={rf_auc:.2f}",
            transform=ax.transAxes, fontsize=8,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Panel 2: heatmap of logistic predicted − observed
    ax = axes[1]
    err_grid = np.full((len(e_vals), len(c_vals)), np.nan)
    for r in cell_results:
        i = e_vals.index(round(r['e'], 4))
        j = c_vals.index(round(r['c'], 4))
        err_grid[i, j] = r['log_pred'] - r['obs']

    diff_cmap = mcolors.LinearSegmentedColormap.from_list(
        "diff", ["#2255cc", "#f5f5f5", "#cc2222"], N=256)
    im = ax.imshow(err_grid, origin='lower', aspect='auto',
                   vmin=-0.6, vmax=0.6, cmap=diff_cmap,
                   extent=[c_vals[0]-0.02, c_vals[-1]+0.02,
                           e_vals[0]-0.02, e_vals[-1]+0.02])
    for r in cell_results:
        e, c, err = r['e'], r['c'], r['log_pred'] - r['obs']
        color = 'white' if abs(err) > 0.35 else 'black'
        ax.text(c, e, f"{err:+.2f}", ha='center', va='center', fontsize=8, color=color)
    ax.set_xticks(c_vals); ax.set_xticklabels([str(v) for v in c_vals], fontsize=8)
    ax.set_yticks(e_vals); ax.set_yticklabels([str(v) for v in e_vals], fontsize=8)
    ax.set_xlabel("pool_committed_split (C)", fontsize=9)
    ax.set_ylabel("economic_split (E)", fontsize=9)
    ax.set_title("Logistic Error (Predicted − Observed)\non Arm B", fontsize=9, fontweight='bold')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("Error", fontsize=8)

    # Panel 3: RF predicted − observed
    ax = axes[2]
    rf_err_grid = np.full((len(e_vals), len(c_vals)), np.nan)
    for r in cell_results:
        i = e_vals.index(round(r['e'], 4))
        j = c_vals.index(round(r['c'], 4))
        rf_err_grid[i, j] = r['rf_pred'] - r['obs']

    im2 = ax.imshow(rf_err_grid, origin='lower', aspect='auto',
                    vmin=-0.6, vmax=0.6, cmap=diff_cmap,
                    extent=[c_vals[0]-0.02, c_vals[-1]+0.02,
                            e_vals[0]-0.02, e_vals[-1]+0.02])
    for r in cell_results:
        e, c, err = r['e'], r['c'], r['rf_pred'] - r['obs']
        color = 'white' if abs(err) > 0.35 else 'black'
        ax.text(c, e, f"{err:+.2f}", ha='center', va='center', fontsize=8, color=color)
    ax.set_xticks(c_vals); ax.set_xticklabels([str(v) for v in c_vals], fontsize=8)
    ax.set_yticks(e_vals); ax.set_yticklabels([str(v) for v in e_vals], fontsize=8)
    ax.set_xlabel("pool_committed_split (C)", fontsize=9)
    ax.set_ylabel("economic_split (E)", fontsize=9)
    ax.set_title("RF Error (Predicted − Observed)\non Arm B", fontsize=9, fontweight='bold')
    fig.colorbar(im2, ax=ax, fraction=0.046, pad=0.04).set_label("Error", fontsize=8)

    plt.suptitle("Boundary Model Validation on Arm B (Out-of-Sample)", fontsize=11)
    plt.tight_layout()
    plt.savefig(out / 'arm_b_validation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nSaved: {out}/arm_b_validation.png")

    # ── Save summary JSON ─────────────────────────────────────────────────────
    summary = {
        'n_train': int(len(y_tr)),
        'n_test': int(len(y_b)),
        'logistic': {'accuracy': log_acc, 'brier': log_brier, 'roc_auc': log_auc},
        'rf':       {'accuracy': rf_acc,  'brier': rf_brier,  'roc_auc': rf_auc},
        'economic_override_e50': {
            'model_prediction': float(model_e50) if model_e50 else None,
            'arm_b_observed':   observed_e50,
            'delta':            float(observed_e50 - model_e50) if model_e50 else None,
        },
        'cells': cell_results,
    }
    with open(out / 'arm_b_validation.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {out}/arm_b_validation.json")
    print("\nDone.")


if __name__ == '__main__':
    main()
