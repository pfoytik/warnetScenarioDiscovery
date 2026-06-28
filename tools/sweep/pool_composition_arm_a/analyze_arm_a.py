#!/usr/bin/env python3
"""
Pool Composition Arm A — Analysis Script

Research question: Does fork outcome depend on WHICH pools are committed to v27,
or only on the TOTAL committed hashrate fraction?

Traverses results_server1/ns-*/sweep_*/results.json, joins with scenarios.json,
and produces a full analysis report.
"""

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

SWEEP_DIR = Path(__file__).parent
SCENARIOS_JSON = SWEEP_DIR / "scenarios.json"
RESULTS_DIR = SWEEP_DIR / "results_server1"
OUTPUT_DIR = SWEEP_DIR / "analysis_arm_a"

C_VALUES = [0.1, 0.15, 0.214, 0.25, 0.3, 0.4, 0.5]
E_VALUES = [0.55, 0.65, 0.74, 0.78]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_scenarios():
    with open(SCENARIOS_JSON) as f:
        data = json.load(f)
    return {s["scenario_id"]: s for s in data["scenarios"]}


def load_all_results():
    """Traverse ns-*/sweep_*/results.json and return list of result dicts."""
    results = {}
    for ns_dir in sorted(RESULTS_DIR.iterdir()):
        if not ns_dir.is_dir() or not ns_dir.name.startswith("ns-"):
            continue
        for sweep_dir in sorted(ns_dir.iterdir()):
            if not sweep_dir.is_dir() or not sweep_dir.name.startswith("sweep_"):
                continue
            results_file = sweep_dir / "results.json"
            if not results_file.exists():
                continue
            try:
                with open(results_file) as f:
                    data = json.load(f)
                sid = sweep_dir.name
                if sid in results:
                    # Duplicate (ns-7/ns-8 overlap at sweep_0111); keep first
                    continue
                results[sid] = data
            except Exception as e:
                print(f"  Warning: failed to load {results_file}: {e}")
    return results


def load_time_series(ns_dir: Path, sweep_id: str):
    for ns in sorted(RESULTS_DIR.iterdir()):
        if not ns.is_dir():
            continue
        ts_path = ns / sweep_id / "time_series.csv"
        if ts_path.exists():
            with open(ts_path) as f:
                return list(csv.DictReader(f))
    return []


# ---------------------------------------------------------------------------
# Metrics extraction
# ---------------------------------------------------------------------------

def extract_metrics(scenario: dict, result: dict) -> dict:
    row = {}
    row.update(scenario)  # all scenario params

    summary = result.get("summary", {})
    row["v27_blocks"] = summary.get("blocks_mined", {}).get("v27", 0)
    row["v26_blocks"] = summary.get("blocks_mined", {}).get("v26", 0)
    row["total_blocks"] = summary.get("total_blocks", 0)

    fhr = summary.get("final_hashrate", {})
    row["final_v27_hashrate"] = fhr.get("v27", 0.0)
    row["final_v26_hashrate"] = fhr.get("v26", 100.0)

    fecon = summary.get("final_economic", {})
    row["final_v27_economic"] = fecon.get("v27", 50.0)
    row["final_v26_economic"] = fecon.get("v26", 50.0)

    fp = summary.get("final_prices", {})
    row["final_v27_price"] = fp.get("v27", 0.0)
    row["final_v26_price"] = fp.get("v26", 0.0)

    diff = result.get("difficulty", {})
    row["winning_fork"] = diff.get("winning_fork", "unknown")

    reorg = result.get("reorg", {}).get("network_summary", {})
    row["total_reorgs"] = reorg.get("total_reorg_events", 0)
    row["reorg_mass"] = reorg.get("total_reorg_mass", 0)
    row["total_orphans"] = reorg.get("total_blocks_orphaned", 0)

    # Outcome by hashrate
    total_hr = row["final_v27_hashrate"] + row["final_v26_hashrate"]
    v27_hr_share = row["final_v27_hashrate"] / total_hr if total_hr > 0 else 0.0
    row["v27_hr_share"] = v27_hr_share

    if v27_hr_share > 0.65:
        row["outcome"] = "v27_win"
    elif v27_hr_share < 0.35:
        row["outcome"] = "v26_win"
    else:
        row["outcome"] = "contested"

    # v27 won? binary
    row["v27_won"] = 1 if row["outcome"] == "v27_win" else 0

    # Foundry in committed set?
    row["foundry_committed"] = 1 if "foundryusa" in scenario.get("committed_pool_ids_v27", []) else 0

    # Large pool presence (Foundry, AntPool, ViaBTC are the top 3 by hashrate)
    big_pools = {"foundryusa", "antpool", "viabtc"}
    committed = set(scenario.get("committed_pool_ids_v27", []))
    row["big_pool_committed_count"] = len(committed & big_pools)
    row["has_large_pool"] = 1 if committed & big_pools else 0

    return row


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def pct(n, total):
    return round(100.0 * n / total, 1) if total else 0.0


def win_rate(rows):
    if not rows:
        return None, 0
    wins = sum(r["v27_won"] for r in rows)
    return pct(wins, len(rows)), len(rows)


def mean(values):
    v = [x for x in values if x is not None]
    return round(sum(v) / len(v), 3) if v else None


# ---------------------------------------------------------------------------
# Core analyses
# ---------------------------------------------------------------------------

def grid_win_rates(rows):
    """v27 win rate in each (E, C) cell."""
    grid = defaultdict(list)
    for r in rows:
        key = (r["economic_split"], r["pool_committed_split"])
        grid[key].append(r)

    print("\n=== WIN RATE GRID: v27 win% by (E, C) ===")
    print("(Arm A: all 168 scenarios, 6 compositions per cell)")
    print()
    ec_label = "E\\C"
    header = f"{ec_label:>6}" + "".join(f"  C={c:.3f}" for c in C_VALUES)
    print(header)
    print("-" * len(header))
    for e in E_VALUES:
        row_parts = [f"{e:>6.2f}"]
        for c in C_VALUES:
            key = (e, c)
            cell_rows = grid.get(key, [])
            if cell_rows:
                wr, n = win_rate(cell_rows)
                row_parts.append(f"  {wr:>5.1f}%({n})")
            else:
                row_parts.append(f"  {'--':>7}")
        print("".join(row_parts))
    print()
    return grid


def variance_across_compositions(grid):
    """Show outcome variance across the 6 compositions at each (E, C) point."""
    print("=== OUTCOME VARIANCE ACROSS COMPOSITIONS ===")
    print("(Does composition matter? High variance = yes, low = no)")
    print()
    print(f"{'E':>5} {'C':>6}  {'Outcomes (per composition)':<40}  {'Variance?'}")
    print("-" * 70)

    for e in E_VALUES:
        for c in C_VALUES:
            key = (e, c)
            cell = grid.get(key, [])
            if not cell:
                continue
            sorted_cell = sorted(cell, key=lambda r: r["composition_index"])
            outcomes = [r["outcome"] for r in sorted_cell]
            wins = sum(r["v27_won"] for r in sorted_cell)
            total = len(sorted_cell)
            variance = wins > 0 and wins < total
            variance_str = "YES — split" if variance else ("all v27" if wins == total else "all v26")
            out_str = " ".join(o[:3] for o in outcomes)
            print(f"{e:>5.2f} {c:>6.3f}  {out_str:<40}  {variance_str}")
    print()


def foundry_identity_analysis(rows):
    """At each C level, compare win rate when Foundry IS vs IS NOT in committed set."""
    print("=== FOUNDRY IDENTITY ANALYSIS ===")
    print("(Does Foundry specifically being committed change outcomes?)")
    print()

    by_c = defaultdict(lambda: {"foundry": [], "no_foundry": []})
    for r in rows:
        c = r["pool_committed_split"]
        key = "foundry" if r["foundry_committed"] else "no_foundry"
        by_c[c][key].append(r)

    print(f"{'C':>6}  {'With Foundry':>20}  {'Without Foundry':>20}  {'Diff':>6}")
    print("-" * 60)
    for c in C_VALUES:
        cell = by_c[c]
        f_rows = cell["foundry"]
        nf_rows = cell["no_foundry"]
        f_wr, f_n = win_rate(f_rows)
        nf_wr, nf_n = win_rate(nf_rows)
        f_str = f"{f_wr:>5.1f}% (n={f_n})" if f_n else "    -- (n=0)"
        nf_str = f"{nf_wr:>5.1f}% (n={nf_n})" if nf_n else "    -- (n=0)"
        if f_wr is not None and nf_wr is not None:
            diff = round(f_wr - nf_wr, 1)
            diff_str = f"{diff:>+6.1f}%"
        else:
            diff_str = "     --"
        print(f"{c:>6.3f}  {f_str:>20}  {nf_str:>20}  {diff_str:>6}")

    # Also by E value
    print()
    print("By E × Foundry presence:")
    by_ef = defaultdict(lambda: {"foundry": [], "no_foundry": []})
    for r in rows:
        key = "foundry" if r["foundry_committed"] else "no_foundry"
        by_ef[r["economic_split"]][key].append(r)

    print(f"{'E':>5}  {'With Foundry':>20}  {'Without Foundry':>20}  {'Diff':>6}")
    print("-" * 55)
    for e in E_VALUES:
        cell = by_ef[e]
        f_wr, f_n = win_rate(cell["foundry"])
        nf_wr, nf_n = win_rate(cell["no_foundry"])
        f_str = f"{f_wr:>5.1f}% (n={f_n})" if f_n else "    -- (n=0)"
        nf_str = f"{nf_wr:>5.1f}% (n={nf_n})" if nf_n else "    -- (n=0)"
        if f_wr is not None and nf_wr is not None:
            diff = round(f_wr - nf_wr, 1)
            diff_str = f"{diff:>+6.1f}%"
        else:
            diff_str = "     --"
        print(f"{e:>5.2f}  {f_str:>20}  {nf_str:>20}  {diff_str:>6}")
    print()


def actual_hashrate_vs_outcome(rows):
    """Win rate by actual realized committed hashrate (not target C)."""
    print("=== ACTUAL COMMITTED HASHRATE vs OUTCOME ===")
    print("(Realized hashrate after composition shuffle, binned)")
    print()
    bins = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]
    binned = defaultdict(list)
    for r in rows:
        actual = r["committed_hashrate_actual"]
        for i in range(len(bins) - 1):
            if bins[i] <= actual < bins[i + 1]:
                binned[(bins[i], bins[i + 1])].append(r)
                break

    print(f"{'Bin':>15}  {'n':>4}  {'v27 win%':>9}  {'v26 win%':>9}  {'contested%':>11}")
    print("-" * 55)
    for (lo, hi) in [(bins[i], bins[i+1]) for i in range(len(bins)-1)]:
        cell = binned[(lo, hi)]
        if not cell:
            continue
        total = len(cell)
        v27 = sum(r["v27_won"] for r in cell)
        v26 = sum(1 for r in cell if r["outcome"] == "v26_win")
        con = total - v27 - v26
        print(f"[{lo:.2f}, {hi:.2f})  {total:>4}  {pct(v27,total):>8.1f}%  {pct(v26,total):>8.1f}%  {pct(con,total):>10.1f}%")
    print()


def per_pool_win_rates(rows):
    """For each pool, what is the v27 win rate when that pool IS committed?"""
    print("=== PER-POOL WIN RATE WHEN POOL IS COMMITTED ===")
    print("(Across all E×C cells; reveals which pool's commitment predicts v27 win)")
    print()

    all_pools = set()
    for r in rows:
        for p in r.get("committed_pool_ids_v27", []):
            all_pools.add(p)

    pool_stats = {}
    for pool in sorted(all_pools):
        committed_rows = [r for r in rows if pool in r.get("committed_pool_ids_v27", [])]
        not_committed = [r for r in rows if pool not in r.get("committed_pool_ids_v27", [])]
        wr_c, n_c = win_rate(committed_rows)
        wr_nc, n_nc = win_rate(not_committed)
        act_c = mean([r["committed_hashrate_actual"] for r in committed_rows])
        diff = round(wr_c - wr_nc, 1) if wr_c is not None and wr_nc is not None else None
        pool_stats[pool] = (wr_c, n_c, wr_nc, n_nc, act_c, diff)

    # Sort by win rate when committed (descending)
    sorted_pools = sorted(pool_stats.items(), key=lambda x: (x[1][0] or 0), reverse=True)

    print(f"{'Pool':<15}  {'Committed':>16}  {'Not Committed':>18}  {'Delta':>8}  {'Avg actual C':>13}")
    print("-" * 80)
    for pool, (wr_c, n_c, wr_nc, n_nc, act_c, diff) in sorted_pools:
        c_str = f"{wr_c:>5.1f}% (n={n_c})" if wr_c is not None else "    -- (n=0)"
        nc_str = f"{wr_nc:>5.1f}% (n={n_nc})" if wr_nc is not None else "    -- (n=0)"
        d_str = f"{diff:>+7.1f}%" if diff is not None else "       --"
        ac_str = f"{act_c:.3f}" if act_c is not None else "   --"
        print(f"{pool:<15}  {c_str:>16}  {nc_str:>18}  {d_str:>8}  {ac_str:>13}")
    print()


def large_pool_effect(rows):
    """Compare outcomes by whether any big pool (Foundry, AntPool, ViaBTC) is committed."""
    print("=== BIG POOL EFFECT (Foundry/AntPool/ViaBTC) ===")
    print()
    by_bigpool = defaultdict(list)
    for r in rows:
        by_bigpool[r["big_pool_committed_count"]].append(r)

    print(f"{'# big pools committed':>22}  {'n':>4}  {'v27 win%':>9}")
    print("-" * 42)
    for k in sorted(by_bigpool.keys()):
        cell = by_bigpool[k]
        wr, n = win_rate(cell)
        print(f"{k:>22}  {n:>4}  {wr:>8.1f}%")
    print()


def composition_consistency(grid):
    """
    For each (E, C) cell with mixed outcomes, show which composition_index wins/loses.
    This reveals if a specific shuffle order reliably shifts outcomes.
    """
    print("=== COMPOSITION CONSISTENCY: WHERE OUTCOMES SPLIT ===")
    print("(Cells where not all 6 compositions agree on outcome)")
    print()

    mixed_cells = 0
    for e in E_VALUES:
        for c in C_VALUES:
            key = (e, c)
            cell = grid.get(key, [])
            if not cell:
                continue
            outcomes = [r["outcome"] for r in sorted(cell, key=lambda r: r["composition_index"])]
            wins = sum(r["v27_won"] for r in cell)
            if wins > 0 and wins < len(cell):
                mixed_cells += 1
                print(f"E={e:.2f} C={c:.3f}:")
                for r in sorted(cell, key=lambda r: r["composition_index"]):
                    pools = r.get("committed_pool_ids_v27", [])
                    pool_str = "+".join(sorted(pools)) if pools else "(none)"
                    foundry = "FOUNDRY" if "foundryusa" in pools else ""
                    print(f"  comp={r['composition_index']} seed={r['composition_seed']:4d}  "
                          f"actual_C={r['committed_hashrate_actual']:.3f}  "
                          f"outcome={r['outcome']:<12} pools=[{pool_str}] {foundry}")
                print()

    if mixed_cells == 0:
        print("  No mixed cells found — composition identity does NOT change outcomes.")
    print()


def summary_statistics(rows):
    print("=== OVERALL SUMMARY ===")
    print(f"Total scenarios: {len(rows)}")
    total_v27 = sum(r["v27_won"] for r in rows)
    total_v26 = sum(1 for r in rows if r["outcome"] == "v26_win")
    total_con = len(rows) - total_v27 - total_v26
    print(f"  v27 win:   {total_v27} ({pct(total_v27, len(rows))}%)")
    print(f"  v26 win:   {total_v26} ({pct(total_v26, len(rows))}%)")
    print(f"  contested: {total_con} ({pct(total_con, len(rows))}%)")
    print()

    # By E
    print("By economic_split (E):")
    by_e = defaultdict(list)
    for r in rows:
        by_e[r["economic_split"]].append(r)
    for e in E_VALUES:
        cell = by_e.get(e, [])
        wr, n = win_rate(cell)
        print(f"  E={e:.2f}: {wr:>5.1f}% v27 win (n={n})")
    print()

    # By C
    print("By pool_committed_split (C):")
    by_c = defaultdict(list)
    for r in rows:
        by_c[r["pool_committed_split"]].append(r)
    for c in C_VALUES:
        cell = by_c.get(c, [])
        wr, n = win_rate(cell)
        print(f"  C={c:.3f}: {wr:>5.1f}% v27 win (n={n})")
    print()


def export_csv(rows):
    """Export merged scenario+result data to CSV."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / "arm_a_results.csv"

    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())

    priority = [
        "scenario_id", "economic_split", "pool_committed_split", "composition_index",
        "composition_seed", "committed_hashrate_actual", "committed_pool_ids_v27",
        "foundry_committed", "big_pool_committed_count", "has_large_pool",
        "outcome", "v27_won", "winning_fork",
        "v27_hr_share", "final_v27_hashrate", "final_v26_hashrate",
        "final_v27_economic", "final_v26_economic",
        "final_v27_price", "final_v26_price",
        "v27_blocks", "v26_blocks", "total_blocks",
        "total_reorgs", "reorg_mass", "total_orphans",
    ]
    cols = [c for c in priority if c in all_keys]
    cols += sorted([c for c in all_keys if c not in cols])

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            # Serialize list fields
            r2 = dict(r)
            for k, v in r2.items():
                if isinstance(v, list):
                    r2[k] = "+".join(str(x) for x in v)
            writer.writerow(r2)

    print(f"Exported {len(rows)} rows to {csv_path}")
    return csv_path


def save_report(text: str):
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_path = OUTPUT_DIR / "arm_a_analysis.txt"
    with open(report_path, "w") as f:
        f.write(text)
    print(f"\nFull report saved to {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import io
    import sys

    print("Loading scenarios...")
    scenarios = load_scenarios()
    print(f"  {len(scenarios)} scenarios defined")

    print("Loading results...")
    results = load_all_results()
    print(f"  {len(results)} result files loaded")

    missing = [sid for sid in scenarios if sid not in results]
    if missing:
        print(f"  WARNING: {len(missing)} scenarios have no results: {missing[:5]}{'...' if len(missing)>5 else ''}")

    # Merge scenario params + result metrics
    rows = []
    for sid, result in results.items():
        if sid not in scenarios:
            print(f"  WARNING: {sid} not in scenarios.json — skipping")
            continue
        row = extract_metrics(scenarios[sid], result)
        rows.append(row)

    rows.sort(key=lambda r: r["scenario_id"])
    print(f"\n{len(rows)} scenarios ready for analysis")
    print("=" * 70)

    # Capture output for report file
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf

    print("=" * 70)
    print("POOL COMPOSITION ARM A — ANALYSIS REPORT")
    print(f"Scenarios: {len(rows)} / 168  (server1 complete, server2 pending)")
    print("=" * 70)

    summary_statistics(rows)
    grid = grid_win_rates(rows)
    variance_across_compositions(grid)
    foundry_identity_analysis(rows)
    actual_hashrate_vs_outcome(rows)
    per_pool_win_rates(rows)
    large_pool_effect(rows)
    composition_consistency(grid)

    sys.stdout = old_stdout
    report = buf.getvalue()

    print(report)
    save_report(report)
    export_csv(rows)


if __name__ == "__main__":
    main()
