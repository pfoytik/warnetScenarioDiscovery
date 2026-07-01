#!/usr/bin/env python3
"""
Arm A vs Arm B Boundary Comparison
====================================
Quantifies how the economic override threshold and committed-hashrate
flip-point shift between the lite network (arm_a, ~4 econ nodes) and the
full 60-node network (arm_b, 24 econ nodes).

Three analyses:
  1. Win-rate heatmaps: side-by-side (E × C) grids
  2. Economic override threshold: logistic fit of win_rate(E) at C≈0
     (C=0.10 and C=0.15 — near-zero committed hashrate)
  3. C flip-point by E row: isotonic / logistic fit of win_rate(C) at each E,
     reporting the C value where win_rate crosses 0.50

Usage:
    python tools/sweep/compare_arm_boundaries.py --db sweep_results.db
    python tools/sweep/compare_arm_boundaries.py --db sweep_results.db --output-dir pool_composition_arm_b/boundary_comparison
"""

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.optimize import curve_fit
from scipy.special import expit          # logistic sigmoid
from scipy.stats import chi2_contingency


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_arm(db_path: str, sweep_name: str) -> list[dict]:
    """Load all scenarios for a sweep from the database."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
        SELECT sc.*
        FROM scenarios sc
        JOIN sweeps sw ON sc.sweep_id = sw.sweep_id
        WHERE sw.sweep_name = ?
    """, (sweep_name,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


# ---------------------------------------------------------------------------
# Win-rate grid helpers
# ---------------------------------------------------------------------------

def build_winrate_grid(rows: list[dict], e_vals, c_vals):
    """
    Returns win_rate[i,j] (float 0–1), count[i,j] (int)
    for e_vals × c_vals grid.
    """
    wins   = np.zeros((len(e_vals), len(c_vals)), dtype=int)
    counts = np.zeros_like(wins)

    for r in rows:
        e = round(float(r["economic_split"]), 4)
        c = round(float(r["pool_committed_split"]), 4)
        outcome = r["outcome"]
        for i, ev in enumerate(e_vals):
            if abs(e - ev) < 1e-4:
                for j, cv in enumerate(c_vals):
                    if abs(c - cv) < 1e-4:
                        counts[i, j] += 1
                        if outcome == "v27_dominant":
                            wins[i, j] += 1
                        break
                break

    with np.errstate(invalid="ignore"):
        rates = np.where(counts > 0, wins / counts, np.nan)
    return rates, wins, counts


# ---------------------------------------------------------------------------
# Boundary fitting
# ---------------------------------------------------------------------------

def logistic(x, x0, k):
    """Standard logistic: 1 / (1 + exp(-k*(x - x0)))"""
    return expit(k * (x - x0))


def fit_threshold(x_vals: np.ndarray, win_rates: np.ndarray,
                  counts: np.ndarray, min_count: int = 3):
    """
    Fit a logistic curve to (x, win_rate) pairs weighted by count.
    Returns (x0, k, x_50pct, ci_low, ci_high) or None on failure.
    x0    — inflection point (50% win rate)
    k     — steepness
    ci    — 95% confidence interval on x0 (from param covariance)
    """
    mask = counts >= min_count
    if mask.sum() < 3:
        return None
    x = x_vals[mask]
    y = win_rates[mask]
    w = np.sqrt(counts[mask].astype(float))  # weight by sqrt(n)

    try:
        p0 = [np.median(x), 10.0]
        popt, pcov = curve_fit(logistic, x, y, p0=p0, sigma=1/w,
                               absolute_sigma=False, maxfev=5000)
        x0, k = popt
        # 95% CI on x0 from covariance diagonal
        se_x0 = np.sqrt(pcov[0, 0]) if pcov[0, 0] >= 0 else np.nan
        ci_low  = x0 - 1.96 * se_x0
        ci_high = x0 + 1.96 * se_x0
        return dict(x0=x0, k=k, ci_low=ci_low, ci_high=ci_high)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

CMAP = mcolors.LinearSegmentedColormap.from_list(
    "rv", ["#cc2222", "#f5f5f5", "#2255cc"], N=256
)


def plot_heatmap(ax, rates, wins, counts, e_vals, c_vals,
                 title: str, show_cbar: bool = False, fig=None):
    im = ax.imshow(
        rates, origin="lower", aspect="auto",
        vmin=0, vmax=1, cmap=CMAP,
        extent=[c_vals[0]-0.02, c_vals[-1]+0.02,
                e_vals[0]-0.02, e_vals[-1]+0.02]
    )
    # Annotate cells
    for i, ev in enumerate(e_vals):
        for j, cv in enumerate(c_vals):
            if counts[i, j] > 0:
                pct = f"{rates[i,j]:.0%}\n({wins[i,j]}/{counts[i,j]})"
                color = "white" if (rates[i,j] < 0.25 or rates[i,j] > 0.75) else "black"
                ax.text(cv, ev, pct, ha="center", va="center",
                        fontsize=7, color=color)

    ax.set_xticks(c_vals)
    ax.set_xticklabels([str(v) for v in c_vals], fontsize=8)
    ax.set_yticks(e_vals)
    ax.set_yticklabels([str(v) for v in e_vals], fontsize=8)
    ax.set_xlabel("pool_committed_split (C)", fontsize=9)
    ax.set_ylabel("economic_split (E)", fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold")

    if show_cbar and fig is not None:
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("v27 win rate", fontsize=8)
    return im


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Arm A vs Arm B boundary comparison")
    parser.add_argument("--db", default="sweep_results.db")
    parser.add_argument("--output-dir", default="pool_composition_arm_b/boundary_comparison")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── Load data ────────────────────────────────────────────────────────────
    print("Loading arm_a (lite network)...")
    arm_a = load_arm(args.db, "pool_composition_arm_a")
    print(f"  {len(arm_a)} scenarios")

    print("Loading arm_b (full network)...")
    arm_b = load_arm(args.db, "pool_composition_arm_b")
    print(f"  {len(arm_b)} scenarios")

    # Shared grid axes (union, sorted)
    e_vals = sorted(set(round(float(r["economic_split"]),    4) for r in arm_a + arm_b))
    c_vals = sorted(set(round(float(r["pool_committed_split"]), 4) for r in arm_a + arm_b))
    print(f"\nGrid: E={e_vals}")
    print(f"      C={c_vals}")

    rates_a, wins_a, counts_a = build_winrate_grid(arm_a, e_vals, c_vals)
    rates_b, wins_b, counts_b = build_winrate_grid(arm_b, e_vals, c_vals)

    e_arr = np.array(e_vals)
    c_arr = np.array(c_vals)

    # ── 1. Side-by-side heatmaps ─────────────────────────────────────────────
    print("\n[1] Generating heatmaps...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    plot_heatmap(axes[0], rates_a, wins_a, counts_a, e_vals, c_vals,
                 "Arm A — Lite network (~4 econ nodes)", fig=fig)
    plot_heatmap(axes[1], rates_b, wins_b, counts_b, e_vals, c_vals,
                 "Arm B — Full network (24 econ nodes)", show_cbar=True, fig=fig)

    # Difference panel: B − A
    diff = np.where(
        np.isnan(rates_a) | np.isnan(rates_b),
        np.nan,
        rates_b - rates_a
    )
    diff_cmap = mcolors.LinearSegmentedColormap.from_list(
        "diff", ["#cc2222", "#f5f5f5", "#2255cc"], N=256
    )
    im_diff = axes[2].imshow(
        diff, origin="lower", aspect="auto",
        vmin=-1, vmax=1, cmap=diff_cmap,
        extent=[c_vals[0]-0.02, c_vals[-1]+0.02,
                e_vals[0]-0.02, e_vals[-1]+0.02]
    )
    for i, ev in enumerate(e_vals):
        for j, cv in enumerate(c_vals):
            if not np.isnan(diff[i, j]):
                val = diff[i, j]
                color = "white" if abs(val) > 0.5 else "black"
                axes[2].text(cv, ev, f"{val:+.2f}", ha="center", va="center",
                             fontsize=8, color=color)
    axes[2].set_xticks(c_vals)
    axes[2].set_xticklabels([str(v) for v in c_vals], fontsize=8)
    axes[2].set_yticks(e_vals)
    axes[2].set_yticklabels([str(v) for v in e_vals], fontsize=8)
    axes[2].set_xlabel("pool_committed_split (C)", fontsize=9)
    axes[2].set_ylabel("economic_split (E)", fontsize=9)
    axes[2].set_title("Δ Win Rate (Arm B − Arm A)", fontsize=10, fontweight="bold")
    fig.colorbar(im_diff, ax=axes[2], fraction=0.046, pad=0.04).set_label("Δ win rate", fontsize=8)

    plt.suptitle("Pool Composition Arm A vs Arm B — v27 Win Rate by (E, C)", fontsize=12, y=1.02)
    plt.tight_layout()
    heatmap_path = out / "heatmap_comparison.png"
    plt.savefig(heatmap_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {heatmap_path}")

    # ── 2. Economic override threshold: win_rate(E) at near-zero C ───────────
    print("\n[2] Economic override threshold (logistic fit over E at low C)...")

    # Use C=0.10 and C=0.15 combined as "near-zero committed" proxy
    low_c_mask_a = [r for r in arm_a if float(r["pool_committed_split"]) <= 0.15]
    low_c_mask_b = [r for r in arm_b if float(r["pool_committed_split"]) <= 0.15]

    # Aggregate by E
    def agg_by_e(rows, e_vals):
        wins_e   = {e: 0 for e in e_vals}
        counts_e = {e: 0 for e in e_vals}
        for r in rows:
            e = round(float(r["economic_split"]), 4)
            if e in wins_e:
                counts_e[e] += 1
                if r["outcome"] == "v27_dominant":
                    wins_e[e] += 1
        wr = np.array([wins_e[e] / counts_e[e] if counts_e[e] > 0 else np.nan for e in e_vals])
        ct = np.array([counts_e[e] for e in e_vals])
        return wr, ct

    wr_a_low, ct_a_low = agg_by_e(low_c_mask_a, e_vals)
    wr_b_low, ct_b_low = agg_by_e(low_c_mask_b, e_vals)

    fit_a_low = fit_threshold(e_arr, wr_a_low, ct_a_low)
    fit_b_low = fit_threshold(e_arr, wr_b_low, ct_b_low)

    # Also fit across all C values (marginal E effect)
    def agg_by_e_all(rows, e_vals):
        wins_e = {e: 0 for e in e_vals}
        cnts_e = {e: 0 for e in e_vals}
        for r in rows:
            e = round(float(r["economic_split"]), 4)
            if e in wins_e:
                cnts_e[e] += 1
                if r["outcome"] == "v27_dominant":
                    wins_e[e] += 1
        wr = np.array([wins_e[e] / cnts_e[e] if cnts_e[e] > 0 else np.nan for e in e_vals])
        ct = np.array([cnts_e[e] for e in e_vals])
        return wr, ct

    wr_a_all, ct_a_all = agg_by_e_all(arm_a, e_vals)
    wr_b_all, ct_b_all = agg_by_e_all(arm_b, e_vals)

    fit_a_all = fit_threshold(e_arr, wr_a_all, ct_a_all)
    fit_b_all = fit_threshold(e_arr, wr_b_all, ct_b_all)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    e_fine = np.linspace(e_arr.min() - 0.05, e_arr.max() + 0.05, 300)

    for ax, (wr_a, ct_a, wr_b, ct_b, fit_a, fit_b, label) in zip(
        axes,
        [
            (wr_a_low, ct_a_low, wr_b_low, ct_b_low, fit_a_low, fit_b_low,
             "At low C (≤0.15)"),
            (wr_a_all, ct_a_all, wr_b_all, ct_b_all, fit_a_all, fit_b_all,
             "Marginal (all C)"),
        ]
    ):
        mask_a = ct_a > 0
        mask_b = ct_b > 0
        ax.scatter(e_arr[mask_a], wr_a[mask_a], s=ct_a[mask_a]*8,
                   color="#cc4444", zorder=5, label="Arm A (lite)", alpha=0.85)
        ax.scatter(e_arr[mask_b], wr_b[mask_b], s=ct_b[mask_b]*8,
                   color="#2255cc", zorder=5, label="Arm B (full)", alpha=0.85, marker="^")

        if fit_a:
            ax.plot(e_fine, logistic(e_fine, fit_a["x0"], fit_a["k"]),
                    color="#cc4444", lw=2, ls="--", alpha=0.8)
            ax.axvline(fit_a["x0"], color="#cc4444", lw=1, ls=":",
                       label=f"Arm A E₅₀={fit_a['x0']:.3f} [{fit_a['ci_low']:.3f},{fit_a['ci_high']:.3f}]")

        if fit_b:
            ax.plot(e_fine, logistic(e_fine, fit_b["x0"], fit_b["k"]),
                    color="#2255cc", lw=2, ls="--", alpha=0.8)
            ax.axvline(fit_b["x0"], color="#2255cc", lw=1, ls=":",
                       label=f"Arm B E₅₀={fit_b['x0']:.3f} [{fit_b['ci_low']:.3f},{fit_b['ci_high']:.3f}]")

        ax.axhline(0.5, color="gray", lw=0.8, ls="--", alpha=0.5)
        ax.set_xlim(0.50, 0.85)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel("economic_split (E)", fontsize=10)
        ax.set_ylabel("v27 win rate", fontsize=10)
        ax.set_title(f"Economic Override — {label}", fontsize=10, fontweight="bold")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(alpha=0.3)

    plt.suptitle("Economic Override Threshold: Arm A vs Arm B", fontsize=12)
    plt.tight_layout()
    econ_path = out / "economic_override_threshold.png"
    plt.savefig(econ_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {econ_path}")

    # ── 3. C flip-point by E row ─────────────────────────────────────────────
    print("\n[3] Committed-hashrate flip-point (C₅₀) by E row...")

    results = {}
    fig, axes = plt.subplots(2, len(e_vals), figsize=(4*len(e_vals), 8), sharey=True)

    for col, ev in enumerate(e_vals):
        ei = e_vals.index(ev)

        for row_idx, (label, rates, wins, counts, color) in enumerate([
            ("Arm A (lite)",   rates_a, wins_a, counts_a, "#cc4444"),
            ("Arm B (full)",   rates_b, wins_b, counts_b, "#2255cc"),
        ]):
            ax = axes[row_idx, col]
            wr  = rates[ei, :]
            ct  = counts[ei, :]
            w   = wins[ei, :]

            # raw data
            mask = ct > 0
            ax.bar(c_arr[mask], wr[mask], width=0.04, color=color, alpha=0.65,
                   label=label, zorder=3)
            ax.errorbar(
                c_arr[mask], wr[mask],
                yerr=np.where(ct[mask] > 0,
                              np.sqrt(wr[mask]*(1-wr[mask])/ct[mask]), 0),
                fmt="none", color="black", capsize=3, lw=1, zorder=4
            )

            fit = fit_threshold(c_arr, wr, ct, min_count=2)
            c_fine = np.linspace(c_arr.min() - 0.02, c_arr.max() + 0.02, 300)
            if fit:
                ax.plot(c_fine, logistic(c_fine, fit["x0"], fit["k"]),
                        color=color, lw=2, ls="--", zorder=5)
                ax.axvline(fit["x0"], color=color, lw=1.5, ls=":",
                           label=f"C₅₀={fit['x0']:.3f}", zorder=5)
                ax.fill_betweenx([0, 1], fit["ci_low"], fit["ci_high"],
                                 color=color, alpha=0.10)

            ax.axhline(0.5, color="gray", lw=0.8, ls="--", alpha=0.5)
            ax.set_xlim(c_arr.min() - 0.04, c_arr.max() + 0.04)
            ax.set_ylim(-0.05, 1.10)
            ax.set_xlabel("pool_committed_split (C)", fontsize=9)
            if col == 0:
                ax.set_ylabel("v27 win rate", fontsize=9)
            ax.set_title(f"E={ev}  {label}", fontsize=8, fontweight="bold")
            ax.legend(fontsize=7)
            ax.grid(alpha=0.3)
            ax.set_xticks(c_arr)
            ax.set_xticklabels([str(c) for c in c_vals], fontsize=7, rotation=45)

            results.setdefault(f"E={ev}", {})[label] = fit

    plt.suptitle("Committed-Hashrate Flip-Point (C₅₀) by E: Arm A vs Arm B", fontsize=12)
    plt.tight_layout()
    cflip_path = out / "c_flippoint_by_e.png"
    plt.savefig(cflip_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {cflip_path}")

    # ── 4. Summary stats: chi-square test for independence ───────────────────
    print("\n[4] Chi-square tests: are arm_a and arm_b outcomes drawn from the same distribution?")

    def chi2_for_e(ev, arm_a_rows, arm_b_rows):
        def counts_for(rows):
            v27 = sum(1 for r in rows
                      if abs(float(r["economic_split"]) - ev) < 1e-4
                      and r["outcome"] == "v27_dominant")
            total = sum(1 for r in rows
                        if abs(float(r["economic_split"]) - ev) < 1e-4)
            return v27, total - v27
        v27_a, v26_a = counts_for(arm_a_rows)
        v27_b, v26_b = counts_for(arm_b_rows)
        if (v27_a + v26_a) == 0 or (v27_b + v26_b) == 0:
            return None
        table = [[v27_a, v26_a], [v27_b, v26_b]]
        chi2, p, dof, _ = chi2_contingency(table, correction=False)
        return chi2, p, table

    chi2_results = {}
    for ev in e_vals:
        res = chi2_for_e(ev, arm_a, arm_b)
        if res:
            chi2, p, table = res
            chi2_results[ev] = {"chi2": chi2, "p": p, "table": table}
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            print(f"  E={ev}: chi2={chi2:.2f}  p={p:.4f}{sig}  "
                  f"  arm_a={table[0][0]}/{sum(table[0])} v27  "
                  f"  arm_b={table[1][0]}/{sum(table[1])} v27")

    # ── 5. Print quantitative summary ────────────────────────────────────────
    print("\n" + "="*70)
    print("BOUNDARY SHIFT SUMMARY")
    print("="*70)

    # Economic override E50
    print("\nEconomic Override Threshold (E where win_rate crosses 50%):")
    print(f"  {'Condition':<28}  {'Arm A (lite)':<22}  {'Arm B (full)'}")
    print(f"  {'-'*28}  {'-'*22}  {'-'*22}")
    for (label, fa, fb) in [
        ("At low C (≤0.15)",  fit_a_low, fit_b_low),
        ("Marginal (all C)",  fit_a_all, fit_b_all),
    ]:
        a_str = f"E₅₀={fa['x0']:.3f} ±{(fa['ci_high']-fa['ci_low'])/2:.3f}" if fa else "no fit"
        b_str = f"E₅₀={fb['x0']:.3f} ±{(fb['ci_high']-fb['ci_low'])/2:.3f}" if fb else "no fit"
        shift = ""
        if fa and fb:
            delta = fb["x0"] - fa["x0"]
            shift = f"  Δ={delta:+.3f} ({'lower' if delta < 0 else 'higher'} on full net)"
        print(f"  {label:<28}  {a_str:<22}  {b_str}{shift}")

    print("\nC Flip-Point (C where win_rate crosses 50%) by E:")
    print(f"  {'E':<8}  {'Arm A C₅₀':<22}  {'Arm B C₅₀':<22}  {'Δ C₅₀'}")
    print(f"  {'-'*8}  {'-'*22}  {'-'*22}  {'-'*10}")
    for ev in e_vals:
        fa = results.get(f"E={ev}", {}).get("Arm A (lite)")
        fb = results.get(f"E={ev}", {}).get("Arm B (full)")
        a_str = f"{fa['x0']:.3f} [{fa['ci_low']:.3f},{fa['ci_high']:.3f}]" if fa else "no fit"
        b_str = f"{fb['x0']:.3f} [{fb['ci_low']:.3f},{fb['ci_high']:.3f}]" if fb else "no fit"
        delta_str = ""
        if fa and fb:
            d = fb["x0"] - fa["x0"]
            delta_str = f"{d:+.3f}"
        print(f"  {ev:<8}  {a_str:<22}  {b_str:<22}  {delta_str}")

    print("\nCell-level win rate differences (Arm B − Arm A):")
    print(f"  {'E':<6}  {'C':<6}  {'Arm A':<10}  {'Arm B':<10}  {'Delta':<8}  {'Direction'}")
    print(f"  {'-'*6}  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*8}  {'-'*12}")
    for i, ev in enumerate(e_vals):
        for j, cv in enumerate(c_vals):
            ra = rates_a[i, j]
            rb = rates_b[i, j]
            if np.isnan(ra) or np.isnan(rb):
                continue
            d = rb - ra
            direction = (
                "B>>A" if d >  0.4 else
                "B>A"  if d >  0.15 else
                "A>B"  if d < -0.15 else
                "A>>B" if d < -0.4 else
                "~="
            )
            if abs(d) >= 0.15:
                print(f"  {ev:<6}  {cv:<6}  {ra:<10.3f}  {rb:<10.3f}  {d:<+8.3f}  {direction}")

    # ── 6. Save JSON results ──────────────────────────────────────────────────
    output = {
        "economic_override": {
            "at_low_c": {
                "arm_a": fit_a_low,
                "arm_b": fit_b_low,
                "delta_e50": (fit_b_low["x0"] - fit_a_low["x0"])
                             if fit_a_low and fit_b_low else None
            },
            "marginal_all_c": {
                "arm_a": fit_a_all,
                "arm_b": fit_b_all,
                "delta_e50": (fit_b_all["x0"] - fit_a_all["x0"])
                             if fit_a_all and fit_b_all else None
            }
        },
        "c_flippoint_by_e": {
            str(ev): {
                "arm_a": results.get(f"E={ev}", {}).get("Arm A (lite)"),
                "arm_b": results.get(f"E={ev}", {}).get("Arm B (full)"),
            }
            for ev in e_vals
        },
        "chi2_by_e": {
            str(ev): {"chi2": v["chi2"], "p": v["p"]}
            for ev, v in chi2_results.items()
        },
        "win_rate_grids": {
            "arm_a": rates_a.tolist(),
            "arm_b": rates_b.tolist(),
            "diff":  diff.tolist(),
            "e_vals": e_vals,
            "c_vals": c_vals,
        }
    }

    json_path = out / "boundary_comparison.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, default=lambda x: None if np.isnan(x) else float(x))
    print(f"\nSaved JSON: {json_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
