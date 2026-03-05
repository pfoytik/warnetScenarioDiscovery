#!/usr/bin/env python3
"""
Step 5: Build Consolidated Scenario Database

Consolidates all sweep results into a single SQLite database for
cross-sweep analysis, threshold discovery, and reproducibility.

Usage:
    python 5_build_database.py
    python 5_build_database.py --output results.db
    python 5_build_database.py --sweeps targeted_sweep1 targeted_sweep2b
    python 5_build_database.py --list  # show available sweeps

Output:
    sweep_results.db (SQLite database)
"""

import argparse
import sqlite3
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Define the schema
SCHEMA = """
-- Sweep metadata table
CREATE TABLE IF NOT EXISTS sweeps (
    sweep_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sweep_name TEXT UNIQUE NOT NULL,
    sweep_type TEXT,  -- 'lhs', 'targeted_grid', 'baseline'
    description TEXT,
    network_type TEXT,  -- 'lite', 'full', 'balanced'
    n_scenarios INTEGER,
    created_at TEXT,
    spec_file TEXT,
    grid_axes TEXT,  -- JSON for targeted sweeps
    fixed_parameters TEXT  -- JSON for targeted sweeps
);

-- Main scenarios table with all inputs and outputs
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identifiers
    sweep_id INTEGER NOT NULL,
    scenario_id TEXT NOT NULL,

    -- Input parameters (sweep variables)
    economic_split REAL,
    hashrate_split REAL,
    pool_ideology_strength REAL,
    pool_profitability_threshold REAL,
    pool_max_loss_pct REAL,
    pool_committed_split REAL,
    pool_neutral_pct REAL,
    econ_ideology_strength REAL,
    econ_switching_threshold REAL,
    econ_inertia REAL,
    user_ideology_strength REAL,
    user_switching_threshold REAL,
    transaction_velocity REAL,
    user_nodes_per_partition INTEGER,
    economic_nodes_per_partition INTEGER,
    solo_miner_hashrate REAL,

    -- Primary outputs
    outcome TEXT,  -- 'v27_dominant', 'v26_dominant', 'contested'
    winning_fork TEXT,  -- 'v27', 'v26', 'contested'

    -- Hashrate outcomes
    v27_hash_share REAL,  -- final v27 hashrate fraction
    v27_block_share REAL,  -- v27 blocks / total blocks
    final_v27_hashrate REAL,
    final_v26_hashrate REAL,
    v27_blocks INTEGER,
    v26_blocks INTEGER,
    total_blocks INTEGER,

    -- Economic outcomes
    v27_econ_share REAL,
    final_v27_economic REAL,
    final_v26_economic REAL,
    final_v27_price REAL,
    final_v26_price REAL,

    -- Reorg metrics (cascade indicators)
    total_reorgs INTEGER,
    total_orphans INTEGER,
    reorg_mass INTEGER,

    -- Simulation metadata
    duration INTEGER,

    -- Fork valuation (custody_btc summed per fork × final price)
    v27_fork_valuation REAL,  -- total USD value of BTC on v27 fork
    v26_fork_valuation REAL,  -- total USD value of BTC on v26 fork

    -- Pool opportunity costs per fork
    v27_pool_opportunity_cost REAL,  -- total USD cost paid by pools committed to v27
    v26_pool_opportunity_cost REAL,  -- total USD cost paid by pools committed to v26

    -- Derived metrics (computed on insert)
    cascade_occurred INTEGER,  -- 1 if reorgs > 0
    hashrate_flipped INTEGER,  -- 1 if final hashrate differs from initial by >10%
    profitability_gap REAL,  -- (v26_price - v27_price) / v27_price

    FOREIGN KEY (sweep_id) REFERENCES sweeps(sweep_id),
    UNIQUE(sweep_id, scenario_id)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_scenarios_outcome ON scenarios(outcome);
CREATE INDEX IF NOT EXISTS idx_scenarios_sweep ON scenarios(sweep_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_economic_split ON scenarios(economic_split);
CREATE INDEX IF NOT EXISTS idx_scenarios_hashrate_split ON scenarios(hashrate_split);

-- View for easy querying with sweep names
CREATE VIEW IF NOT EXISTS scenario_results AS
SELECT
    s.sweep_name,
    sc.*
FROM scenarios sc
JOIN sweeps s ON sc.sweep_id = s.sweep_id;
"""

# Sweeps to include with their metadata
SWEEP_METADATA = {
    'targeted_sweep1_committed_threshold': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Economic × committed split grid at fixed hashrate=0.25'
    },
    'targeted_sweep2_pool_ideology': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Pool ideology × max_loss grid at econ=0.65 (abandoned - gap too large)'
    },
    'targeted_sweep2b_pool_ideology': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Pool ideology × max_loss grid at econ=0.78 (redesigned)'
    },
    'balanced_baseline_sweep': {
        'sweep_type': 'baseline',
        'network_type': 'balanced',
        'description': 'Stochastic variance baseline with symmetric 47/47 hashrate'
    },
    'realistic_sweep3_rapid': {
        'sweep_type': 'lhs',
        'network_type': 'full',
        'description': 'LHS sweep with fixed economic_split bug (n=50)'
    },
    'realistic_sweep2': {
        'sweep_type': 'lhs',
        'network_type': 'full',
        'description': 'LHS sweep with economic_split bug (n=50)'
    },
    'exploratory_sweep_lite': {
        'sweep_type': 'lhs',
        'network_type': 'lite',
        'description': 'LHS sweep on lite network (n=50)'
    },
    'exploratory_sweep': {
        'sweep_type': 'lhs',
        'network_type': 'full',
        'description': 'Initial exploratory LHS sweep'
    },
    'realistic_sweep3': {
        'sweep_type': 'lhs',
        'network_type': 'full',
        'description': 'Long duration sweep with 2016-block difficulty'
    },
    'v26_real_baseline_lite': {
        'sweep_type': 'baseline',
        'network_type': 'lite',
        'description': 'V26 baseline on lite network'
    },
}


def find_sweep_data_files(base_dir: Path) -> Dict[str, Path]:
    """Find all sweep_data.csv files and map to sweep names."""
    results = {}
    for csv_path in base_dir.glob("**/sweep_data.csv"):
        # Extract sweep name from path
        # Pattern: <sweep_name>/results/analysis/sweep_data.csv
        parts = csv_path.parts
        if 'results' in parts and 'analysis' in parts:
            results_idx = parts.index('results')
            if results_idx > 0:
                sweep_name = parts[results_idx - 1]
                results[sweep_name] = csv_path
    return results


def load_sweep_metadata(sweep_dir: Path) -> Dict:
    """Load metadata from build_manifest.json or scenarios.json."""
    metadata = {}

    # Try build_manifest.json first
    manifest_path = sweep_dir / 'build_manifest.json'
    if manifest_path.exists():
        with open(manifest_path) as f:
            data = json.load(f)
            meta = data.get('metadata', {})
            metadata['sweep_type'] = meta.get('type', 'unknown')
            metadata['n_scenarios'] = meta.get('n_samples', 0)
            metadata['spec_file'] = meta.get('spec_file', '')
            metadata['grid_axes'] = json.dumps(meta.get('grid_axes', {}))
            metadata['fixed_parameters'] = json.dumps(meta.get('fixed_parameters', {}))
            metadata['description'] = meta.get('description', '')

    # Try scenarios.json
    scenarios_path = sweep_dir / 'scenarios.json'
    if scenarios_path.exists() and not metadata:
        with open(scenarios_path) as f:
            data = json.load(f)
            meta = data.get('metadata', {})
            metadata['sweep_type'] = meta.get('type', 'unknown')
            metadata['n_scenarios'] = meta.get('n_samples', len(data.get('scenarios', [])))
            metadata['spec_file'] = meta.get('spec_file', '')
            metadata['grid_axes'] = json.dumps(meta.get('grid_axes', {}))
            metadata['fixed_parameters'] = json.dumps(meta.get('fixed_parameters', {}))
            metadata['description'] = meta.get('description', '')

    return metadata


def import_sweep(conn: sqlite3.Connection, sweep_name: str, csv_path: Path,
                 override_metadata: Optional[Dict] = None) -> int:
    """Import a single sweep's data into the database."""
    cursor = conn.cursor()

    # Get or create sweep record
    sweep_dir = csv_path.parent.parent.parent
    file_metadata = load_sweep_metadata(sweep_dir)

    # Merge with override metadata
    metadata = SWEEP_METADATA.get(sweep_name, {})
    metadata.update(file_metadata)
    if override_metadata:
        metadata.update(override_metadata)

    # Insert sweep record
    cursor.execute("""
        INSERT OR REPLACE INTO sweeps
        (sweep_name, sweep_type, description, network_type, n_scenarios,
         created_at, spec_file, grid_axes, fixed_parameters)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sweep_name,
        metadata.get('sweep_type', 'unknown'),
        metadata.get('description', ''),
        metadata.get('network_type', 'unknown'),
        metadata.get('n_scenarios', 0),
        datetime.now().isoformat(),
        metadata.get('spec_file', ''),
        metadata.get('grid_axes', '{}'),
        metadata.get('fixed_parameters', '{}')
    ))

    sweep_id = cursor.execute(
        "SELECT sweep_id FROM sweeps WHERE sweep_name = ?", (sweep_name,)
    ).fetchone()[0]

    # Delete existing scenarios for this sweep (for re-import)
    cursor.execute("DELETE FROM scenarios WHERE sweep_id = ?", (sweep_id,))

    # Import scenarios from CSV
    imported = 0
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Compute derived metrics
            cascade_occurred = 1 if int(row.get('total_reorgs', 0) or 0) > 0 else 0

            # Hashrate flipped if final differs from initial by >10%
            initial_hash = float(row.get('hashrate_split', 0.5) or 0.5)
            final_hash = float(row.get('v27_hash_share', 0.5) or 0.5)
            hashrate_flipped = 1 if abs(final_hash - initial_hash) > 0.1 else 0

            # Profitability gap
            v27_price = float(row.get('final_v27_price', 1) or 1)
            v26_price = float(row.get('final_v26_price', 1) or 1)
            profitability_gap = (v26_price - v27_price) / v27_price if v27_price > 0 else 0

            cursor.execute("""
                INSERT INTO scenarios (
                    sweep_id, scenario_id,
                    economic_split, hashrate_split,
                    pool_ideology_strength, pool_profitability_threshold,
                    pool_max_loss_pct, pool_committed_split, pool_neutral_pct,
                    econ_ideology_strength, econ_switching_threshold, econ_inertia,
                    user_ideology_strength, user_switching_threshold,
                    transaction_velocity, user_nodes_per_partition,
                    economic_nodes_per_partition, solo_miner_hashrate,
                    outcome, winning_fork,
                    v27_hash_share, v27_block_share,
                    final_v27_hashrate, final_v26_hashrate,
                    v27_blocks, v26_blocks, total_blocks,
                    v27_econ_share, final_v27_economic, final_v26_economic,
                    final_v27_price, final_v26_price,
                    total_reorgs, total_orphans, reorg_mass,
                    duration,
                    v27_fork_valuation, v26_fork_valuation,
                    v27_pool_opportunity_cost, v26_pool_opportunity_cost,
                    cascade_occurred, hashrate_flipped, profitability_gap
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                sweep_id, row.get('scenario_id', ''),
                float(row.get('economic_split') or 0),
                float(row.get('hashrate_split') or 0),
                float(row.get('pool_ideology_strength') or 0),
                float(row.get('pool_profitability_threshold') or 0),
                float(row.get('pool_max_loss_pct') or 0),
                float(row.get('pool_committed_split') or 0),
                float(row.get('pool_neutral_pct') or 0),
                float(row.get('econ_ideology_strength') or 0),
                float(row.get('econ_switching_threshold') or 0),
                float(row.get('econ_inertia') or 0),
                float(row.get('user_ideology_strength') or 0),
                float(row.get('user_switching_threshold') or 0),
                float(row.get('transaction_velocity') or 0),
                int(row.get('user_nodes_per_partition') or 0),
                int(row.get('economic_nodes_per_partition') or 0),
                float(row.get('solo_miner_hashrate') or 0),
                row.get('outcome', ''),
                row.get('winning_fork', ''),
                float(row.get('v27_hash_share') or 0),
                float(row.get('v27_block_share') or 0),
                float(row.get('final_v27_hashrate') or 0),
                float(row.get('final_v26_hashrate') or 0),
                int(row.get('v27_blocks') or 0),
                int(row.get('v26_blocks') or 0),
                int(row.get('total_blocks') or 0),
                float(row.get('v27_econ_share') or 0),
                float(row.get('final_v27_economic') or 0),
                float(row.get('final_v26_economic') or 0),
                float(row.get('final_v27_price') or 0),
                float(row.get('final_v26_price') or 0),
                int(row.get('total_reorgs') or 0),
                int(row.get('total_orphans') or 0),
                int(row.get('reorg_mass') or 0),
                int(row.get('duration') or 0),
                float(row.get('v27_fork_valuation') or 0),
                float(row.get('v26_fork_valuation') or 0),
                float(row.get('v27_pool_opportunity_cost') or 0),
                float(row.get('v26_pool_opportunity_cost') or 0),
                cascade_occurred,
                hashrate_flipped,
                profitability_gap
            ))
            imported += 1

    conn.commit()
    return imported


def main():
    parser = argparse.ArgumentParser(
        description="Build consolidated scenario database from sweep results",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--output", "-o", default="sweep_results.db",
                        help="Output database path (default: sweep_results.db)")
    parser.add_argument("--sweeps", nargs="+", default=None,
                        help="Specific sweeps to include (default: all found)")
    parser.add_argument("--list", action="store_true",
                        help="List available sweeps and exit")
    parser.add_argument("--exclude", nargs="+", default=['test_sweep'],
                        help="Sweeps to exclude (default: test_sweep)")

    args = parser.parse_args()

    base_dir = Path(__file__).parent
    sweep_files = find_sweep_data_files(base_dir)

    if args.list:
        print("Available sweeps:")
        for name, path in sorted(sweep_files.items()):
            meta = SWEEP_METADATA.get(name, {})
            desc = meta.get('description', 'No description')
            print(f"  {name:40} {desc[:50]}")
        return

    # Filter sweeps
    if args.sweeps:
        sweep_files = {k: v for k, v in sweep_files.items() if k in args.sweeps}
    if args.exclude:
        sweep_files = {k: v for k, v in sweep_files.items() if k not in args.exclude}

    print(f"Building database: {args.output}")
    print(f"Found {len(sweep_files)} sweeps to import")

    # Create database
    db_path = base_dir / args.output
    conn = sqlite3.connect(db_path)

    # Create schema
    conn.executescript(SCHEMA)

    # Import each sweep
    total_scenarios = 0
    for sweep_name, csv_path in sorted(sweep_files.items()):
        print(f"  Importing {sweep_name}...", end=" ")
        try:
            count = import_sweep(conn, sweep_name, csv_path)
            print(f"{count} scenarios")
            total_scenarios += count
        except Exception as e:
            print(f"ERROR: {e}")

    conn.close()

    print(f"\nDatabase created: {db_path}")
    print(f"Total scenarios: {total_scenarios}")
    print(f"\nExample queries:")
    print(f"  sqlite3 {args.output} \"SELECT sweep_name, COUNT(*) FROM scenario_results GROUP BY sweep_name\"")
    print(f"  sqlite3 {args.output} \"SELECT outcome, COUNT(*) FROM scenarios GROUP BY outcome\"")
    print(f"  sqlite3 {args.output} \"SELECT * FROM scenarios WHERE economic_split > 0.7 AND outcome = 'v27_dominant'\"")


if __name__ == "__main__":
    main()
