#!/usr/bin/env python3
"""
prim_comparison.py — Compare custom single-pass PRIM vs. EMA Workbench PRIM
                     (peeling + pasting + bump hunting)

Runs both implementations on the same full-network 2016-block dataset and
reports differences in box bounds, support, and purity. The key question:
does pasting recover support lost by aggressive peeling, and does bump hunting
reveal a second contested box?

Usage:
    python tools/discovery/prim_comparison.py \
        --db tools/sweep/sweep_results.db \
        [--target uncertainty|v27_wins] \
        [--min-support 0.05]
"""

import argparse
import sqlite3
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

FEATURES = [
    "economic_split",
    "pool_committed_split",
    "pool_ideology_strength",
    "pool_max_loss_pct",
]

FEATURE_LABELS = {
    "economic_split":       "Economic Split",
    "pool_committed_split": "Pool Committed Split",
    "pool_ideology_strength": "Pool Ideology Strength",
    "pool_max_loss_pct":    "Pool Max Loss Pct",
}

# Full-network 2016-block sweeps only (same as fit_boundary.py Phase 2)
VALID_SWEEPS_2016 = [
    "econ_committed_2016_grid",
    "lhs_2016_full_parameter",
    "lhs_2016_6param",
    "targeted_sweep7_esp_2016",
    "targeted_sweep10_econ_threshold_2016",
    "targeted_sweep10b_econ_threshold_2016",
    "targeted_sweep8_lite_2016_retarget",
    "targeted_sweep9_long_duration_2016",
    "targeted_sweep11_lite_chaos_test",
    "committed_2016_high_econ",
    "committed_2016_mid_econ",
    "committed_2016_sigmoid",
    "committed_2016_sigmoid_midecon",
    "hashrate_2016_verification",
    # NOTE: lhs_2016_full_phase3_merged and lhs_2016_full_6param intentionally
    # excluded here — their near-50/50 design trivialises the uncertainty PRIM.
    # This list matches the original Phase 2 fit_boundary.py dataset so results
    # are directly comparable to the published Phase 2 findings.
]


# ── Data loading ─────────────────────────────────────────────────────────────

def load_data(db_path, sweeps):
    conn = sqlite3.connect(db_path)
    placeholders = ",".join(["?" for _ in sweeps])
    df = pd.read_sql(f"""
        SELECT sc.*, sw.sweep_name
        FROM scenarios sc
        JOIN sweeps sw ON sc.sweep_id = sw.sweep_id
        WHERE sw.sweep_name IN ({placeholders})
          AND sc.outcome IS NOT NULL
    """, conn, params=sweeps)
    conn.close()
    return df


def prepare(df, features):
    mask = df[features].notna().all(axis=1)
    df = df[mask].copy()
    X = df[features].values.astype(float)
    y = (df["outcome"] == "v27_dominant").astype(int).values
    return X, y, df


# ── Custom PRIM (from fit_boundary.py) ───────────────────────────────────────

def custom_prim(X, y, feature_names, alpha=0.05, min_support=0.10, mode="uncertainty"):
    """Single-pass peel-only PRIM (no pasting, no bump hunting)."""
    bounds = {name: {"min": X[:, i].min(), "max": X[:, i].max()}
              for i, name in enumerate(feature_names)}
    in_box = np.ones(len(X), dtype=bool)
    min_samples = int(len(X) * min_support)
    trajectory = []

    def score(y_sub):
        if len(y_sub) == 0:
            return -np.inf
        mean = y_sub.mean()
        if mode == "uncertainty":
            return 1 - 2 * abs(mean - 0.5)
        return mean

    while in_box.sum() > min_samples:
        box_y = y[in_box]
        current_score = score(box_y)
        current_support = in_box.sum() / len(X)
        trajectory.append({
            "support": current_support,
            "mean": box_y.mean(),
            "uncertainty": 1 - 2 * abs(box_y.mean() - 0.5),
        })

        best_peel = None
        best_gain = -np.inf

        for i, name in enumerate(feature_names):
            x_in = X[in_box, i]
            y_in = box_y

            lo = np.percentile(x_in, alpha * 100)
            mask_lo = x_in >= lo
            if mask_lo.sum() >= min_samples:
                g = score(y_in[mask_lo]) - current_score
                if g > best_gain:
                    best_gain, best_peel = g, ("min", i, name, lo)

            hi = np.percentile(x_in, (1 - alpha) * 100)
            mask_hi = x_in <= hi
            if mask_hi.sum() >= min_samples:
                g = score(y_in[mask_hi]) - current_score
                if g > best_gain:
                    best_gain, best_peel = g, ("max", i, name, hi)

        if best_peel is None or best_gain <= 0:
            break

        side, idx, name, threshold = best_peel
        if side == "min":
            bounds[name]["min"] = threshold
            in_box = in_box & (X[:, idx] >= threshold)
        else:
            bounds[name]["max"] = threshold
            in_box = in_box & (X[:, idx] <= threshold)

    final_y = y[in_box]
    return {
        "bounds": {k: (v["min"], v["max"]) for k, v in bounds.items()},
        "support": in_box.sum() / len(X),
        "n_samples": int(in_box.sum()),
        "mean": float(final_y.mean()) if len(final_y) > 0 else 0.0,
        "uncertainty": float(1 - 2 * abs(final_y.mean() - 0.5)) if len(final_y) > 0 else 0.0,
        "trajectory": trajectory,
    }


# ── EMA Workbench PRIM ────────────────────────────────────────────────────────

def ema_prim(X, y, feature_names, min_support=0.05, threshold=0.5,
             n_boxes=2, select_mode="uncertainty", target_coverage=None):
    """
    Full PRIM via EMA Workbench — peeling + pasting + bump hunting.

    select_mode controls which trajectory point is chosen as the box:
      'uncertainty' — point closest to mean=0.5 (contested zone search)
      'v27_wins'    — highest coverage row with mean >= threshold (v27-dominant search)
      'coverage'    — closest to target_coverage (for matched-support comparisons)
    """
    from ema_workbench.analysis.prim import Prim, PRIMObjectiveFunctions

    x_df = pd.DataFrame(X, columns=feature_names)

    prim_obj = Prim(
        x_df,
        y,
        threshold=threshold,
        obj_function=PRIMObjectiveFunctions.LENIENT1,
        peel_alpha=0.05,
        paste_alpha=0.05,
        mass_min=min_support,
        threshold_type=1,
    )

    boxes = []
    for box_num in range(n_boxes):
        try:
            box = prim_obj.find_box()
            if box is None:
                break

            traj = box.peeling_trajectory

            # Select the best trajectory point according to mode
            if select_mode == "uncertainty":
                # Point with mean closest to 0.5 — the genuine contested zone
                best_pos = int((traj["mean"] - 0.5).abs().idxmin())
            elif select_mode == "coverage" and target_coverage is not None:
                # Closest to a target coverage level (for matched-support comparison)
                best_pos = int((traj["coverage"] - target_coverage).abs().idxmin())
            else:
                # Highest coverage with mean >= threshold (v27-dominant)
                qualifying = traj[traj["mean"] >= threshold]
                if qualifying.empty:
                    qualifying = traj
                best_pos = int(qualifying["coverage"].idxmax())

            best = traj.iloc[best_pos]
            box.select(best_pos)
            limits = box.box_lim

            bounds = {}
            for feat in feature_names:
                bounds[feat] = (float(limits[feat].iloc[0]), float(limits[feat].iloc[1]))

            # Show whether pasting occurred by checking if coverage increases anywhere
            # after the minimum coverage point in the trajectory
            min_cov_idx = traj["coverage"].idxmin()
            pasting_gain = 0.0
            if min_cov_idx < len(traj) - 1:
                pasting_gain = traj["coverage"].iloc[-1] - traj["coverage"].iloc[min_cov_idx]

            boxes.append({
                "box_num": box_num + 1,
                "bounds": bounds,
                "support": float(best["coverage"]),
                "density": float(best["density"]),
                "mean": float(best["mean"]),
                "n_samples": int(best["n"]),
                "uncertainty": float(1 - 2 * abs(best["mean"] - 0.5)),
                "pasting_gain": float(pasting_gain),
                "peeling_trajectory": traj[["coverage", "density", "mean", "res_dim"]].to_dict("records"),
            })

        except Exception as e:
            print(f"  Box {box_num + 1} failed: {e}")
            import traceback; traceback.print_exc()
            break

    return boxes, prim_obj


# ── Reporting ─────────────────────────────────────────────────────────────────

def print_box(label, bounds, support, n_samples, mean, uncertainty, feature_names):
    print(f"\n  {label}")
    print(f"  {'─' * 56}")
    print(f"  Support:     {support:.1%}  ({n_samples} scenarios)")
    print(f"  v27 win rate: {mean:.3f}")
    print(f"  Uncertainty:  {uncertainty:.3f}  (1.0 = perfect 50/50)")
    print(f"  Bounds:")
    for feat in feature_names:
        lo, hi = bounds[feat]
        label_str = FEATURE_LABELS.get(feat, feat)
        print(f"    {label_str:30s}  [{lo:.3f}, {hi:.3f}]")


def compare_bounds(custom_bounds, ema_bounds, feature_names):
    print(f"\n{'  Parameter':<34}  {'Custom':^18}  {'EMA':^18}  {'Δ width':>8}")
    print(f"  {'─'*80}")
    for feat in feature_names:
        c_lo, c_hi = custom_bounds[feat]
        e_lo, e_hi = ema_bounds[feat]
        c_width = c_hi - c_lo
        e_width = e_hi - e_lo
        delta = e_width - c_width
        label = FEATURE_LABELS.get(feat, feat)
        wider = "←wider" if delta > 0.01 else ("→narrower" if delta < -0.01 else "≈same")
        print(f"  {label:<32}  [{c_lo:.3f},{c_hi:.3f}]  [{e_lo:.3f},{e_hi:.3f}]  {delta:+.3f} {wider}")


def print_trajectory_summary(trajectory, label, n=8):
    """Print evenly-spaced points from the peeling trajectory."""
    print(f"\n  {label} peeling trajectory (support → mean):")
    if isinstance(trajectory, list) and len(trajectory) > 0:
        # Custom trajectory
        step = max(1, len(trajectory) // n)
        rows = trajectory[::step] + [trajectory[-1]]
        for r in rows:
            bar = "█" * int(r["mean"] * 20)
            print(f"    support={r['support']:.2f}  mean={r['mean']:.3f}  [{bar:<20}]")
    elif hasattr(trajectory, "iterrows"):
        # EMA DataFrame
        step = max(1, len(trajectory) // n)
        for _, row in trajectory.iloc[::step].iterrows():
            bar = "█" * int(row["mean"] * 20)
            print(f"    coverage={row['coverage']:.2f}  mean={row['mean']:.3f}  [{bar:<20}]")


# ── Visualisation ────────────────────────────────────────────────────────────

def make_figures(X, y, df_clean, custom_result, ema_boxes, feature_names, target, output_dir):
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.lines import Line2D
    from pathlib import Path

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    COLORS = {"v27_dominant": "#3fb950", "v26_dominant": "#f85149", "contested": "#d29922"}
    SHORT = {
        "economic_split":         "Econ Split",
        "pool_committed_split":   "Committed",
        "pool_ideology_strength": "Ideology",
        "pool_max_loss_pct":      "Max Loss",
    }

    # ── Figure 1: Peeling trajectories ──────────────────────────────────────
    fig, axes = plt.subplots(1, 2 if len(ema_boxes) > 1 else 1,
                             figsize=(12 if len(ema_boxes) > 1 else 6, 4.5),
                             sharey=False)
    if len(ema_boxes) <= 1:
        axes = [axes]

    # Custom trajectory
    c_traj = custom_result["trajectory"]
    c_cov = [r["support"] for r in c_traj]
    c_mean = [r["mean"] for r in c_traj]

    for ax_idx, (ax, ema_box) in enumerate(zip(axes, ema_boxes)):
        e_traj = pd.DataFrame(ema_box["peeling_trajectory"])

        ax.plot(c_cov, c_mean, color="#58a6ff", lw=2, label="Custom (peel only)", zorder=3)
        ax.plot(e_traj["coverage"], e_traj["mean"], color="#f0883e", lw=2,
                label=f"EMA Box {ema_box['box_num']} (peel + paste)", zorder=3)

        # Mark selected points
        ax.scatter([custom_result["support"]], [custom_result["mean"]],
                   color="#58a6ff", s=80, zorder=5)
        ax.scatter([ema_box["support"]], [ema_box["mean"]],
                   color="#f0883e", s=80, zorder=5)

        # Mark where pasting starts (coverage increases)
        cov_vals = e_traj["coverage"].values
        paste_start = None
        for i in range(1, len(cov_vals)):
            if cov_vals[i] > cov_vals[i - 1]:
                paste_start = cov_vals[i - 1]
                break
        if paste_start is not None:
            ax.axvline(paste_start, color="#f0883e", lw=1, ls="--", alpha=0.6, label="Pasting begins")

        # Reference line at mean=0.5
        ax.axhline(0.5, color="#8b949e", lw=1, ls=":", alpha=0.7)
        ax.text(0.02, 0.51, "50/50", color="#8b949e", fontsize=8, va="bottom",
                transform=ax.get_yaxis_transform())

        ax.set_xlabel("Coverage (support fraction)", fontsize=10)
        ax.set_ylabel("Mean v27 win rate", fontsize=10)
        ax.set_title(f"Peeling Trajectory — EMA Box {ema_box['box_num']}" if len(ema_boxes) > 1
                     else "Peeling Trajectory", fontsize=11)
        ax.legend(fontsize=8)
        ax.set_xlim(0, 1.02)
        ax.set_ylim(0.3, 1.02)
        ax.grid(True, alpha=0.3)

    fig.suptitle(f"Custom vs. EMA Workbench PRIM — {target} mode", fontsize=12, y=1.01)
    plt.tight_layout()
    path = out / "prim_trajectories.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")

    # ── Figure 2: Bound comparison bars ─────────────────────────────────────
    if not ema_boxes:
        return

    n_feat = len(feature_names)
    fig, axes = plt.subplots(1, n_feat, figsize=(14, 3.5))

    for ax, feat in zip(axes, feature_names):
        c_lo, c_hi = custom_result["bounds"][feat]
        e_lo, e_hi = ema_boxes[0]["bounds"][feat]

        # Global range for this parameter
        g_lo = X[:, feature_names.index(feat)].min()
        g_hi = X[:, feature_names.index(feat)].max()

        ax.barh(1.8, c_hi - c_lo, left=c_lo, height=0.5,
                color="#58a6ff", alpha=0.85, label="Custom")
        ax.barh(1.0, e_hi - e_lo, left=e_lo, height=0.5,
                color="#f0883e", alpha=0.85, label="EMA Box 1")
        if len(ema_boxes) > 1:
            e2_lo, e2_hi = ema_boxes[1]["bounds"][feat]
            ax.barh(0.2, e2_hi - e2_lo, left=e2_lo, height=0.5,
                    color="#a371f7", alpha=0.85, label="EMA Box 2")

        ax.set_xlim(g_lo - 0.02, g_hi + 0.02)
        ax.set_ylim(-0.2, 2.6)
        ax.set_yticks([])
        ax.set_xlabel(SHORT.get(feat, feat), fontsize=9)
        ax.grid(axis="x", alpha=0.3)

    # Legend on last axis
    handles = [
        mpatches.Patch(color="#58a6ff", label="Custom (peel only)"),
        mpatches.Patch(color="#f0883e", label="EMA Box 1 (peel+paste)"),
    ]
    if len(ema_boxes) > 1:
        handles.append(mpatches.Patch(color="#a371f7", label="EMA Box 2 (bump hunt)"))
    axes[-1].legend(handles=handles, loc="upper right", fontsize=8,
                    bbox_to_anchor=(1.0, 1.35))

    fig.suptitle("PRIM Box Bounds by Parameter — Custom vs. EMA Workbench", fontsize=11)
    plt.tight_layout()
    path = out / "prim_bounds_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")

    # ── Figure 3: 2D scatter with box overlays ───────────────────────────────
    x_feat, y_feat = "economic_split", "pool_committed_split"
    xi = feature_names.index(x_feat)
    yi = feature_names.index(y_feat)

    outcomes = df_clean["outcome"].values
    fig, axes = plt.subplots(1, 1 + len(ema_boxes), figsize=(6 * (1 + len(ema_boxes)), 5))
    if not hasattr(axes, "__iter__"):
        axes = [axes]

    def scatter_base(ax):
        for outcome, color in COLORS.items():
            mask = outcomes == outcome
            ax.scatter(X[mask, xi], X[mask, yi], c=color, s=18, alpha=0.6,
                       label=outcome.replace("_dominant", " dom."), zorder=2)
        ax.set_xlabel(SHORT.get(x_feat, x_feat), fontsize=10)
        ax.set_ylabel(SHORT.get(y_feat, y_feat), fontsize=10)
        ax.grid(True, alpha=0.2)

    # Custom box
    scatter_base(axes[0])
    c_rect = mpatches.Rectangle(
        (custom_result["bounds"][x_feat][0], custom_result["bounds"][y_feat][0]),
        custom_result["bounds"][x_feat][1] - custom_result["bounds"][x_feat][0],
        custom_result["bounds"][y_feat][1] - custom_result["bounds"][y_feat][0],
        linewidth=2, edgecolor="#58a6ff", facecolor="none", zorder=4,
        label=f"Custom box ({custom_result['support']:.0%} support)"
    )
    axes[0].add_patch(c_rect)
    axes[0].set_title("Custom PRIM (peel only)", fontsize=11)
    axes[0].legend(fontsize=8, markerscale=1.5)

    # EMA boxes
    ema_colors = ["#f0883e", "#a371f7"]
    for ax, ema_box, color in zip(axes[1:], ema_boxes, ema_colors):
        scatter_base(ax)
        rect = mpatches.Rectangle(
            (ema_box["bounds"][x_feat][0], ema_box["bounds"][y_feat][0]),
            ema_box["bounds"][x_feat][1] - ema_box["bounds"][x_feat][0],
            ema_box["bounds"][y_feat][1] - ema_box["bounds"][y_feat][0],
            linewidth=2, edgecolor=color, facecolor="none", zorder=4,
            label=f"EMA Box {ema_box['box_num']} ({ema_box['support']:.0%} support)"
        )
        ax.add_patch(rect)
        # Also show custom box faintly for reference
        c_ref = mpatches.Rectangle(
            (custom_result["bounds"][x_feat][0], custom_result["bounds"][y_feat][0]),
            custom_result["bounds"][x_feat][1] - custom_result["bounds"][x_feat][0],
            custom_result["bounds"][y_feat][1] - custom_result["bounds"][y_feat][0],
            linewidth=1.5, edgecolor="#58a6ff", facecolor="none", zorder=3,
            linestyle="--", label="Custom box (ref.)"
        )
        ax.add_patch(c_ref)
        ax.set_title(f"EMA Box {ema_box['box_num']} — peel+paste" +
                     (" (bump hunt)" if ema_box["box_num"] > 1 else ""), fontsize=11)
        ax.legend(fontsize=8, markerscale=1.5)

    fig.suptitle(f"PRIM Box Projections: {SHORT.get(x_feat)} × {SHORT.get(y_feat)}",
                 fontsize=12)
    plt.tight_layout()
    path = out / "prim_scatter_boxes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="tools/sweep/sweep_results.db")
    parser.add_argument("--target", choices=["uncertainty", "v27_wins"], default="uncertainty",
                        help="uncertainty: find contested zone; v27_wins: find v27-dominant region")
    parser.add_argument("--min-support", type=float, default=0.05,
                        help="Minimum fraction of data in box (default: 0.05)")
    parser.add_argument("--n-boxes", type=int, default=2,
                        help="Number of boxes for EMA bump hunting (default: 2)")
    parser.add_argument("--output-dir", default="tools/discovery/output/figures/prim_comparison",
                        help="Directory for output figures")
    args = parser.parse_args()

    print("=== Loading data ===")
    df = load_data(args.db, VALID_SWEEPS_2016)
    print(f"  {len(df)} scenarios from {df['sweep_name'].nunique()} sweeps")

    X, y, df_clean = prepare(df, FEATURES)
    print(f"  v27 win rate: {y.mean():.3f}  (n={len(y)})")

    # For uncertainty mode, EMA Workbench needs a target threshold.
    # We invert y to a continuous uncertainty score so PRIM maximises it.
    if args.target == "uncertainty":
        # Transform binary y → uncertainty score (high when close to 0.5)
        # We'll use a rolling window approach: for EMA we pass the raw binary y
        # but set threshold to capture the ~50/50 zone.
        ema_threshold = 0.35   # boxes with mean >= 0.35 (not lopsided v26 or v27)
        ema_threshold_type = 1
        custom_mode = "uncertainty"
        print(f"\n  Mode: uncertainty (find contested transition zone)")
        print(f"  EMA threshold: mean >= {ema_threshold} (excludes strongly v26-dominant regions)")
    else:
        ema_threshold = 0.60   # boxes with > 60% v27 win rate
        custom_mode = "maximize"
        print(f"\n  Mode: v27_wins (find v27-dominant region)")
        print(f"  EMA threshold: mean >= {ema_threshold}")

    # ── Run custom PRIM ──────────────────────────────────────────────────────
    print("\n=== Custom PRIM (peel only, no pasting) ===")
    custom_result = custom_prim(X, y, FEATURES, alpha=0.05,
                                min_support=args.min_support,
                                mode=custom_mode)
    print_box(
        "Custom result",
        custom_result["bounds"],
        custom_result["support"],
        custom_result["n_samples"],
        custom_result["mean"],
        custom_result["uncertainty"],
        FEATURES,
    )
    print_trajectory_summary(custom_result["trajectory"], "Custom PRIM")

    # ── Run EMA Workbench PRIM ───────────────────────────────────────────────
    print("\n=== EMA Workbench PRIM (peel + paste + bump hunting) ===")
    # For both modes: match EMA trajectory point to custom support level so
    # the bound comparison is apples-to-apples at equivalent coverage.
    ema_select = "coverage"
    try:
        ema_boxes, prim_obj = ema_prim(
            X, y, FEATURES,
            min_support=args.min_support,
            threshold=ema_threshold,
            n_boxes=args.n_boxes,
            select_mode=ema_select,
            target_coverage=custom_result["support"],
        )
    except Exception as e:
        print(f"  EMA PRIM failed: {e}")
        import traceback; traceback.print_exc()
        return

    for box in ema_boxes:
        print_box(
            f"EMA Box {box['box_num']}",
            box["bounds"],
            box["support"],
            box["n_samples"],
            box["mean"],
            box["uncertainty"],
            FEATURES,
        )
        if box["pasting_gain"] > 0.005:
            print(f"  Pasting recovered: +{box['pasting_gain']:.1%} support")
        else:
            print(f"  Pasting: no meaningful gain (peeled box was already stable)")
        print_trajectory_summary(
            pd.DataFrame(box["peeling_trajectory"]),
            f"EMA Box {box['box_num']}",
        )

    # ── Side-by-side comparison ──────────────────────────────────────────────
    if ema_boxes:
        print("\n=== Bound comparison: Custom vs. EMA Box 1 ===")
        compare_bounds(custom_result["bounds"], ema_boxes[0]["bounds"], FEATURES)

        c_sup = custom_result["support"]
        e_sup = ema_boxes[0]["support"]
        print(f"\n  Support: custom={c_sup:.1%}  →  EMA={e_sup:.1%}  "
              f"({'pasting recovered ' + f'{(e_sup-c_sup):.1%}' if e_sup > c_sup else 'EMA is tighter'})")

        c_unc = custom_result["uncertainty"]
        e_unc = ema_boxes[0]["uncertainty"]
        print(f"  Uncertainty: custom={c_unc:.3f}  →  EMA={e_unc:.3f}")

    if len(ema_boxes) > 1:
        print(f"\n=== EMA Box 2 (bump hunting) ===")
        print(f"  A second distinct contested region was found — see bounds above.")
        print(f"  This is not captured by single-pass custom PRIM.")

    # ── Figures ──────────────────────────────────────────────────────────────
    print(f"\n=== Generating figures → {args.output_dir} ===")
    try:
        make_figures(X, y, df_clean, custom_result, ema_boxes, FEATURES,
                     args.target, args.output_dir)
    except ImportError:
        print("  matplotlib not available — skipping figures")


if __name__ == "__main__":
    main()
