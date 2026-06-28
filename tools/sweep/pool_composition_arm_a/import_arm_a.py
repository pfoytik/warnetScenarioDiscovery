#!/usr/bin/env python3
"""
Import pool_composition_arm_a results into sweep_results.db.

Extends the scenarios table with arm_a-specific composition columns,
then loads all 168 scenarios with full field mapping including cascade
dynamics from individual results.json files.

Also writes a standard sweep_data.csv to results_server1/analysis/ for
compatibility with existing tooling.
"""

import csv
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

SWEEP_DIR = Path(__file__).parent
DB_PATH = SWEEP_DIR.parent / "sweep_results.db"
SCENARIOS_JSON = SWEEP_DIR / "scenarios.json"
RESULTS_DIR = SWEEP_DIR / "results_server1"
ANALYSIS_DIR = RESULTS_DIR / "analysis"
SWEEP_NAME = "pool_composition_arm_a"

FIXED_PARAMS = {
    "hashrate_split": 0.25,
    "pool_neutral_pct": 30.0,
    "pool_profitability_threshold": 0.16,
    "pool_ideology_strength": 0.51,
    "pool_max_loss_pct": 0.26,
    "econ_ideology_strength": 0.4,
    "econ_switching_threshold": 0.1,
    "econ_inertia": 0.05,
    "user_ideology_strength": 0.49,
    "user_switching_threshold": 0.12,
    "user_nodes_per_partition": 6,
    "economic_nodes_per_partition": 2,
    "transaction_velocity": 0.5,
    "solo_miner_hashrate": 0.085,
}


def extend_schema(conn):
    """Add arm_a-specific columns to scenarios table if not present."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(scenarios)")
    existing = {row[1] for row in cur.fetchall()}

    new_cols = {
        "composition_seed": "INTEGER",
        "composition_index": "INTEGER",
        "committed_hashrate_actual": "REAL",
        "committed_pool_ids": "TEXT",
        "foundry_committed": "INTEGER",
        "big_pool_committed_count": "INTEGER",
    }
    for col, dtype in new_cols.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE scenarios ADD COLUMN {col} {dtype}")
            print(f"  Added column: {col} {dtype}")

    conn.commit()


def load_scenarios():
    with open(SCENARIOS_JSON) as f:
        data = json.load(f)
    return {s["scenario_id"]: s for s in data["scenarios"]}


def load_all_results():
    results = {}
    seen = set()
    for ns_dir in sorted(RESULTS_DIR.iterdir()):
        if not ns_dir.is_dir() or not ns_dir.name.startswith("ns-"):
            continue
        for sweep_dir in sorted(ns_dir.iterdir()):
            if not sweep_dir.is_dir() or not sweep_dir.name.startswith("sweep_"):
                continue
            if sweep_dir.name in seen:
                continue
            seen.add(sweep_dir.name)
            rf = sweep_dir / "results.json"
            if rf.exists():
                try:
                    with open(rf) as f:
                        results[sweep_dir.name] = json.load(f)
                except Exception as e:
                    print(f"  Warning: {rf}: {e}")
    return results


def load_time_series(sid):
    for ns_dir in sorted(RESULTS_DIR.iterdir()):
        if not ns_dir.is_dir():
            continue
        ts_path = ns_dir / sid / "time_series.csv"
        if ts_path.exists():
            with open(ts_path) as f:
                return list(csv.DictReader(f))
    return []


def analyze_econ_trajectory(ts_rows):
    if not ts_rows:
        return {}

    def fval(row, key, default=0.0):
        try:
            return float(row[key])
        except (KeyError, TypeError, ValueError):
            return default

    econ_initial = fval(ts_rows[0], "v27_economic")
    econ_final = fval(ts_rows[-1], "v27_economic")
    econ_delta = econ_final - econ_initial

    econ_switch_time_s = None
    for row in ts_rows:
        if abs(fval(row, "v27_economic") - econ_initial) > 2.0:
            econ_switch_time_s = fval(row, "timestamps")
            break

    econ_95pct_time_s = None
    for row in ts_rows:
        if fval(row, "v27_economic") > 95.0:
            econ_95pct_time_s = fval(row, "timestamps")
            break

    peak_price_gap_pct = 0.0
    for row in ts_rows:
        v27p = fval(row, "v27_price")
        v26p = fval(row, "v26_price")
        if v26p > 0:
            gap = (v27p - v26p) / v26p * 100
            if gap > peak_price_gap_pct:
                peak_price_gap_pct = gap

    cascade_time_s = None
    for row in ts_rows:
        if fval(row, "v27_hashrate") > 65.0:
            cascade_time_s = fval(row, "timestamps")
            break

    econ_lag_s = None
    if cascade_time_s is not None and econ_switch_time_s is not None:
        econ_lag_s = econ_switch_time_s - cascade_time_s

    if econ_final > 95.0:
        econ_outcome = "full_switch"
    elif econ_final > 60.0:
        econ_outcome = "partial_switch"
    else:
        econ_outcome = "no_switch"

    return {
        "econ_initial": round(econ_initial, 2),
        "econ_final": round(econ_final, 2),
        "econ_delta": round(econ_delta, 2),
        "econ_switched": 1 if econ_delta > 5.0 else 0,
        "econ_outcome": econ_outcome,
        "econ_switch_time_s": econ_switch_time_s,
        "econ_95pct_time_s": econ_95pct_time_s,
        "peak_price_gap_pct": round(peak_price_gap_pct, 2),
        "cascade_time_s": cascade_time_s,
        "econ_lag_s": econ_lag_s,
    }


def build_row(scen, result):
    summary = result.get("summary", {})
    diff = result.get("difficulty", {})
    reorg = result.get("reorg", {}).get("network_summary", {})
    meta = result.get("metadata", {})

    hr = summary.get("final_hashrate", {})
    total_hr = hr.get("v27", 0) + hr.get("v26", 100)
    v27_hr_share = hr.get("v27", 0) / total_hr if total_hr > 0 else 0.0

    v27_blocks = summary.get("blocks_mined", {}).get("v27", 0)
    v26_blocks = summary.get("blocks_mined", {}).get("v26", 0)
    total_blocks = summary.get("total_blocks", 0)
    v27_block_share = v27_blocks / total_blocks if total_blocks > 0 else 0.0

    fecon = summary.get("final_economic", {})
    total_econ = fecon.get("v27", 50) + fecon.get("v26", 50)
    v27_econ_share = fecon.get("v27", 50) / total_econ if total_econ > 0 else 0.5

    if v27_hr_share > 0.65:
        outcome = "v27_dominant"
    elif v27_hr_share < 0.35:
        outcome = "v26_dominant"
    else:
        outcome = "contested"

    big_pools = {"foundryusa", "antpool", "viabtc"}
    committed = set(scen.get("committed_pool_ids_v27", []))
    foundry_committed = 1 if "foundryusa" in committed else 0
    big_pool_committed_count = len(committed & big_pools)

    row = {
        "scenario_id": scen["scenario_id"],
        # Standard sweep params
        "economic_split": scen["economic_split"],
        "pool_committed_split": scen["pool_committed_split"],
        **FIXED_PARAMS,
        # Arm A composition params
        "composition_seed": scen["composition_seed"],
        "composition_index": scen["composition_index"],
        "committed_hashrate_actual": scen["committed_hashrate_actual"],
        "committed_pool_ids": "+".join(sorted(scen.get("committed_pool_ids_v27", []))),
        "foundry_committed": foundry_committed,
        "big_pool_committed_count": big_pool_committed_count,
        # Outcome
        "outcome": outcome,
        "winning_fork": diff.get("winning_fork", "unknown"),
        # Hashrate metrics
        "v27_hash_share": round(v27_hr_share, 4),
        "v27_block_share": round(v27_block_share, 4),
        "final_v27_hashrate": hr.get("v27", 0),
        "final_v26_hashrate": hr.get("v26", 100),
        "v27_blocks": v27_blocks,
        "v26_blocks": v26_blocks,
        "total_blocks": total_blocks,
        # Economic metrics
        "v27_econ_share": round(v27_econ_share, 4),
        "final_v27_economic": fecon.get("v27", 50),
        "final_v26_economic": fecon.get("v26", 50),
        "final_v27_price": summary.get("final_prices", {}).get("v27", 0),
        "final_v26_price": summary.get("final_prices", {}).get("v26", 0),
        # Reorg metrics
        "total_reorgs": reorg.get("total_reorg_events", 0),
        "total_orphans": reorg.get("total_blocks_orphaned", 0),
        "reorg_mass": reorg.get("total_reorg_mass", 0),
        "duration": meta.get("duration_seconds", 0),
        # Placeholders for fields not available in this sweep
        "v27_fork_valuation": 0,
        "v26_fork_valuation": 0,
        "v27_pool_opportunity_cost": 0,
        "v26_pool_opportunity_cost": 0,
        "user_custody_fraction": None,
        "user_split": None,
    }

    # Add cascade/econ trajectory
    ts_rows = load_time_series(scen["scenario_id"])
    traj = analyze_econ_trajectory(ts_rows)
    row.update(traj)

    # Derived
    initial_hash = FIXED_PARAMS["hashrate_split"]
    row["cascade_occurred"] = 1 if row["total_reorgs"] > 0 else 0
    row["hashrate_flipped"] = 1 if abs(v27_hr_share - initial_hash) > 0.1 else 0
    v27p = row["final_v27_price"]
    v26p = row["final_v26_price"]
    row["profitability_gap"] = (v26p - v27p) / v27p if v27p > 0 else 0

    return row


def import_to_db(conn, rows):
    cur = conn.cursor()

    # Upsert sweep record
    with open(SCENARIOS_JSON) as f:
        meta = json.load(f).get("metadata", {})

    cur.execute("""
        INSERT OR REPLACE INTO sweeps
        (sweep_name, sweep_type, description, network_type, n_scenarios,
         created_at, spec_file, grid_axes, fixed_parameters)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        SWEEP_NAME,
        meta.get("type", "compositional_grid"),
        meta.get("description", "")[:500],
        "lite",
        len(rows),
        datetime.now().isoformat(),
        meta.get("spec_file", ""),
        json.dumps({
            "economic_split": meta.get("e_values", []),
            "pool_committed_split": meta.get("c_values", []),
            "compositions_per_point": meta.get("compositions_per_point", 6),
        }),
        json.dumps(FIXED_PARAMS),
    ))

    sweep_id = cur.execute(
        "SELECT sweep_id FROM sweeps WHERE sweep_name = ?", (SWEEP_NAME,)
    ).fetchone()[0]

    cur.execute("DELETE FROM scenarios WHERE sweep_id = ?", (sweep_id,))

    for row in rows:
        cur.execute("""
            INSERT INTO scenarios (
                sweep_id, scenario_id,
                economic_split, hashrate_split,
                pool_ideology_strength, pool_profitability_threshold,
                pool_max_loss_pct, pool_committed_split, pool_neutral_pct,
                econ_ideology_strength, econ_switching_threshold, econ_inertia,
                user_ideology_strength, user_switching_threshold,
                transaction_velocity, user_nodes_per_partition,
                economic_nodes_per_partition, solo_miner_hashrate,
                user_custody_fraction, user_split,
                outcome, winning_fork,
                v27_hash_share, v27_block_share,
                final_v27_hashrate, final_v26_hashrate,
                v27_blocks, v26_blocks, total_blocks,
                v27_econ_share, final_v27_economic, final_v26_economic,
                final_v27_price, final_v26_price,
                total_reorgs, total_orphans, reorg_mass, duration,
                v27_fork_valuation, v26_fork_valuation,
                v27_pool_opportunity_cost, v26_pool_opportunity_cost,
                cascade_occurred, hashrate_flipped, profitability_gap,
                econ_initial, econ_final, econ_delta, econ_switched,
                econ_outcome, econ_switch_time_s, econ_95pct_time_s,
                cascade_time_s, econ_lag_s, peak_price_gap_pct,
                composition_seed, composition_index,
                committed_hashrate_actual, committed_pool_ids,
                foundry_committed, big_pool_committed_count
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
        """, (
            sweep_id, row["scenario_id"],
            row["economic_split"], row["hashrate_split"],
            row["pool_ideology_strength"], row["pool_profitability_threshold"],
            row["pool_max_loss_pct"], row["pool_committed_split"], row["pool_neutral_pct"],
            row["econ_ideology_strength"], row["econ_switching_threshold"], row["econ_inertia"],
            row["user_ideology_strength"], row["user_switching_threshold"],
            row["transaction_velocity"], row["user_nodes_per_partition"],
            row["economic_nodes_per_partition"], row["solo_miner_hashrate"],
            row.get("user_custody_fraction"), row.get("user_split"),
            row["outcome"], row["winning_fork"],
            row["v27_hash_share"], row["v27_block_share"],
            row["final_v27_hashrate"], row["final_v26_hashrate"],
            row["v27_blocks"], row["v26_blocks"], row["total_blocks"],
            row["v27_econ_share"], row["final_v27_economic"], row["final_v26_economic"],
            row["final_v27_price"], row["final_v26_price"],
            row["total_reorgs"], row["total_orphans"], row["reorg_mass"], row["duration"],
            row["v27_fork_valuation"], row["v26_fork_valuation"],
            row["v27_pool_opportunity_cost"], row["v26_pool_opportunity_cost"],
            row["cascade_occurred"], row["hashrate_flipped"], row["profitability_gap"],
            row.get("econ_initial"), row.get("econ_final"), row.get("econ_delta"),
            row.get("econ_switched"), row.get("econ_outcome"),
            row.get("econ_switch_time_s"), row.get("econ_95pct_time_s"),
            row.get("cascade_time_s"), row.get("econ_lag_s"), row.get("peak_price_gap_pct"),
            row["composition_seed"], row["composition_index"],
            row["committed_hashrate_actual"], row["committed_pool_ids"],
            row["foundry_committed"], row["big_pool_committed_count"],
        ))

    conn.commit()
    print(f"  Imported {len(rows)} scenarios as sweep_id={sweep_id}")


def write_sweep_data_csv(rows):
    ANALYSIS_DIR.mkdir(exist_ok=True)
    csv_path = ANALYSIS_DIR / "sweep_data.csv"

    priority_cols = [
        "scenario_id", "outcome", "economic_split", "pool_committed_split",
        "composition_index", "composition_seed", "committed_hashrate_actual",
        "committed_pool_ids", "foundry_committed", "big_pool_committed_count",
        "hashrate_split", "pool_ideology_strength", "pool_max_loss_pct",
        "pool_neutral_pct",
        "v27_hash_share", "v27_block_share", "v27_econ_share",
        "final_v27_hashrate", "final_v26_hashrate",
        "final_v27_economic", "final_v26_economic",
        "final_v27_price", "final_v26_price",
        "v27_blocks", "v26_blocks", "total_blocks",
        "econ_initial", "econ_final", "econ_delta", "econ_outcome",
        "cascade_time_s", "econ_switch_time_s", "peak_price_gap_pct",
        "total_reorgs", "reorg_mass", "total_orphans",
        "winning_fork", "duration",
    ]
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    cols = [c for c in priority_cols if c in all_keys]
    cols += sorted(c for c in all_keys if c not in cols)

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote sweep_data.csv to {csv_path} ({len(rows)} rows)")


def main():
    print(f"Importing {SWEEP_NAME} → {DB_PATH}")

    scenarios = load_scenarios()
    print(f"  Loaded {len(scenarios)} scenario definitions")

    results = load_all_results()
    print(f"  Loaded {len(results)} result files")

    missing = [sid for sid in scenarios if sid not in results]
    if missing:
        print(f"  WARNING: {len(missing)} scenarios missing results")

    print("  Building rows (loading time series for econ trajectory)...")
    rows = []
    for i, (sid, result) in enumerate(sorted(results.items())):
        if sid not in scenarios:
            continue
        row = build_row(scenarios[sid], result)
        rows.append(row)
        if (i + 1) % 20 == 0:
            print(f"    {i+1}/{len(results)}...")

    print(f"  Built {len(rows)} rows")

    conn = sqlite3.connect(DB_PATH)
    print("Extending schema...")
    extend_schema(conn)

    print("Importing to database...")
    import_to_db(conn, rows)
    conn.close()

    print("Writing sweep_data.csv...")
    write_sweep_data_csv(rows)

    print(f"\nDone. {len(rows)} scenarios loaded.")
    print(f"Query: sqlite3 {DB_PATH} \"SELECT outcome, COUNT(*) FROM scenarios WHERE sweep_id=(SELECT sweep_id FROM sweeps WHERE sweep_name='{SWEEP_NAME}') GROUP BY outcome\"")


if __name__ == "__main__":
    main()
