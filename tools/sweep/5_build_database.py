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

    -- User weight parameters (user_weight_* sweeps only)
    user_custody_fraction REAL,  -- fraction of self-custodied BTC actively signaling fork preference
    user_split REAL,             -- fraction of user custody weight on v27 (0=all v26, 1=all v27)

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

    -- Temporal/cascade dynamics (from time series analysis)
    econ_initial REAL,           -- starting v27 economic %
    econ_final REAL,             -- ending v27 economic %
    econ_delta REAL,             -- change in v27 economic %
    econ_switched INTEGER,       -- 1 if econ moved >5pp
    econ_outcome TEXT,           -- 'full_switch', 'partial_switch', 'no_switch'
    econ_switch_time_s REAL,     -- time of first meaningful econ departure
    econ_95pct_time_s REAL,      -- time econ first exceeded 95%
    cascade_time_s REAL,         -- time pool cascade completed (v27 hash >65%)
    econ_lag_s REAL,             -- lag between cascade and econ switching
    peak_price_gap_pct REAL,     -- maximum (v27-v26)/v26 price divergence %

    FOREIGN KEY (sweep_id) REFERENCES sweeps(sweep_id),
    UNIQUE(sweep_id, scenario_id)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_scenarios_outcome ON scenarios(outcome);
CREATE INDEX IF NOT EXISTS idx_scenarios_sweep ON scenarios(sweep_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_economic_split ON scenarios(economic_split);
CREATE INDEX IF NOT EXISTS idx_scenarios_hashrate_split ON scenarios(hashrate_split);
CREATE INDEX IF NOT EXISTS idx_scenarios_cascade_time ON scenarios(cascade_time_s);
CREATE INDEX IF NOT EXISTS idx_scenarios_econ_outcome ON scenarios(econ_outcome);

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
    'targeted_sweep3_neutral_pct': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Pool neutral_pct × economic grid — neutral_pct has no effect on outcome, controls cascade intensity only'
    },
    'targeted_sweep3b_econ_friction_verify': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Verification of econ friction parameters on full 60-node network (4 corner scenarios vs lite network results)'
    },
    'targeted_sweep4_user_behavior': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'User behavior 3D grid: user_ideology_strength × user_switching_threshold × user_nodes_per_partition (36 scenarios)'
    },
    'targeted_sweep5_lite_econ_threshold': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Economic split threshold sweep on lite network (econ 0.5→0.85) — comparison baseline for full network thresholds'
    },
    'targeted_sweep2_hashrate_economic': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Hashrate × economic grid — hashrate shown non-causal; identical outcomes at all hashrate levels (n=42)'
    },
    'targeted_sweep3_econ_friction': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Economic friction grid on lite network — econ_inertia and econ_switching_threshold have no effect'
    },
    'targeted_sweep6_pool_ideology_full': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Pool ideology × max_loss diagonal threshold at econ=0.78 on full 60-node network (n=20) — direction corrected over sweep2b'
    },
    'targeted_sweep6_econ_override': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Ideology × max_loss × econ grid at econ≥0.82 (n=27) — 27/27 v27_dominant; economic override total above ESP; ideology delays but cannot prevent'
    },
    'targeted_sweep7_esp_144': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'ESP sweep at 144-block retarget (econ=0.28–0.85, n=9) — ESP=0.74; threshold between econ=0.70 and econ=0.78'
    },
    'targeted_sweep7_esp_2016': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'ESP sweep at 2016-block retarget (econ=0.28–0.85, n=9) — ESP=0.74 identical to 144-block; ESP invariant to retarget regime'
    },
    'targeted_sweep7_lite_inversion': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Lite network inversion zone validation (n=12) — 75% match to full network; econ=0.50 diverges'
    },
    'targeted_sweep8_lite_2016_retarget': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': '2016-block retarget validation on lite network (n=5) — qualitatively different regime; stuck contested state at econ=0.35–0.70'
    },
    'targeted_sweep9_long_duration_2016': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Long-duration confirmation (n=1, 20000s) — stuck contested state resolves at t=8106s; cascade mechanism confirmed at 2016-block'
    },
    'targeted_sweep10_econ_threshold_2016': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Accidental 144-block run labeled 2016-block (n=5) — three-phase cascade; difficulty mechanics dominate; v27_dominant at econ=0.35–0.70'
    },
    'targeted_sweep10b_econ_threshold_2016': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Corrected 2016-block rerun (n=5) — economic_split irrelevant 0.35–0.70; v27 wins via retarget at all levels incl. econ=0.35'
    },
    'targeted_sweep10c_liveness_penalty': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Liveness penalty (Option B oracle) test — compares baseline vs liveness-penalty oracle variants'
    },
    'targeted_sweep11_lite_chaos_test': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Chaos test at econ=0.50, commit=0.20, 2016-block (n=3) — 3/3 v26_dominant; NOT stochastic; confirms deterministic outcome'
    },
    'econ_committed_2016_grid': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': '5×9 economic_split × pool_committed_split grid at 2016-block retarget (n=45) — direct regime comparison to targeted_sweep1'
    },
    'econ_switching_144_verify': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Economic switching verification at 144-block (n=5) — parameter working; threshold ∈ (0.20, 0.35); perfect symmetry'
    },
    'econ_threshold_2016_v2': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': '2016-block threshold refinement v2 (n=2) — econ=0.55,0.60 both v27_dominant; threshold narrowed to (0.50, 0.55)'
    },
    'econ_threshold_2016_v2_v2': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': '2016-block threshold refinement v2 variant results — see econ_threshold_2016_v2'
    },
    'baseline_threshold_2016_narrow': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Narrow threshold sweep at 2016-block baseline — econ=0.20–0.52 all v26_dominant (quantization, not regime effect)'
    },
    'sigmoid_threshold_2016': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Sigmoid oracle threshold sweep at 2016-block — lower threshold with sigmoid oracle'
    },
    'committed_2016_high_econ': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Committed split × 2016-block at econ=0.78 (n=4) — threshold ∈ (0.20, 0.30); econ level does not shift threshold'
    },
    'committed_2016_mid_econ': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Committed split × 2016-block at econ=0.55 (n=4) — same threshold as high econ; confirms threshold invariance'
    },
    'committed_2016_sigmoid': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Committed split × 2016-block with sigmoid oracle at econ=0.78 — sigmoid triggers full econ switch (peak_gap≈40% > 18% threshold)'
    },
    'committed_2016_sigmoid_midecon': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Committed split × 2016-block with sigmoid oracle at econ=0.55 — same econ switch behavior as econ=0.78; oracle interaction is key'
    },
    'sigmoid_2016_retarget_baseline': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Baseline oracle at 2016-block retarget (initial run) — cascade at t≈8426s; econ=0.35–0.70 identical'
    },
    'sigmoid_2016_retarget_baseline_v2': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Baseline oracle at 2016-block retarget v2 (n=5) — v26=1543 blocks, cascade_t≈8426s, peak_gap=16.1%; corrected econ switching params'
    },
    'sigmoid_2016_retarget_sigmoid': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Sigmoid oracle at 2016-block retarget (initial run) — cascade at t≈4239s pre-retarget; full econ switch triggered'
    },
    'sigmoid_2016_retarget_sigmoid_v2': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Sigmoid oracle at 2016-block retarget v2 (n=5) — halves cascade time (8426→4239s), halves v26 blocks (1543→799), amplifies gap +34%'
    },
    'switching_ideology_threshold': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Econ ideology sweep at sigmoid oracle 144-block — switchover bracket ideology≈0.30–0.35; cascade amplifies gap 14.3%→35.1%'
    },
    'switching_neutral_fraction': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Econ neutral fraction sweep at sigmoid oracle 144-block — neutral fraction does NOT change cascade speed; pool cascade is bottleneck'
    },
    'threshold_144_narrow': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Narrow econ threshold sweep at 144-block (n=4) — quantization boundary ≈0.29 (between econ=0.28→v26 and econ=0.30→v27)'
    },
    'hashrate_2016_verification': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Hashrate split verification at 2016-block retarget'
    },
    'lhs_2016_full_parameter': {
        'sweep_type': 'lhs',
        'network_type': 'full',
        'description': 'Unbiased 4D LHS at 2016-block retarget (n=64) — pool_committed_split dominates (sep=0.275); hard threshold at commit≈0.25; validates regime comparison'
    },
    'lhs_2016_6param': {
        'sweep_type': 'lhs',
        'network_type': 'lite',
        'description': '6D LHS at 2016-block retarget on lite network (n=129) — pool_committed_split dominates (sep=0.272); threshold ~0.346; pool_profitability_threshold and solo_miner_hashrate confirmed non-causal; 46% full econ switch'
    },
    'lhs_144_6param': {
        'sweep_type': 'lhs',
        'network_type': 'lite',
        'description': '6D LHS at 144-block retarget on lite network (n=130) — pool_committed_split dominates (sep=0.162); threshold ~0.407; economic_split non-causal (quantization artifact); 38.5% v26_dominant; econ switch lag 2-3x longer than 2016-block'
    },
    'price_divergence_sensitivity_2016_div10': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Price divergence cap sensitivity at ±10% (n=12) — cap DOES bind in high-parameter scenarios; 5v27/3v26/4contested; 100% no_switch'
    },
    'price_divergence_sensitivity_2016_div20': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Price divergence cap sensitivity at ±20% (n=12) — cap does not bind; 3v27/9contested; 100% no_switch; stalled pool dynamics dominate'
    },
    'price_divergence_sensitivity_2016_div30': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Price divergence cap sensitivity at ±30% (n=12) — maximum stall; 12/12 contested; pool commitment insufficient to complete cascade at any cap'
    },
    'price_divergence_sensitivity_2016_div40': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': 'Price divergence cap sensitivity at ±40% (n=12) — 8v27/4contested; v27 wins via hardware-speed artifact (2016-block retarget epoch reached on fast server); 100% no_switch'
    },
    'oracle_validation_lite_baseline': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Oracle validation on lite network — baseline oracle variant'
    },
    'oracle_validation_lite_ema_only': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Oracle validation on lite network — EMA-only oracle variant'
    },
    'oracle_validation_lite_floor_only': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Oracle validation on lite network — cost floor only oracle variant'
    },
    'oracle_validation_lite_proposals': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Oracle validation on lite network — proposals oracle variant'
    },
    'oracle_validation_lite_sigmoid_only': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Oracle validation on lite network — sigmoid-only oracle variant'
    },
    'cost_floor_asymmetric_test_baseline': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Asymmetric cost floor test — baseline variant (no cost floor)'
    },
    'cost_floor_asymmetric_test_floor': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Asymmetric cost floor test — cost floor active variant'
    },
    'realistic_sweep3_replay': {
        'sweep_type': 'lhs',
        'network_type': 'full',
        'description': 'Replay of realistic_sweep3 for validation'
    },
    'user_weight_threshold': {
        'sweep_type': 'targeted_grid',
        'network_type': 'full',
        'description': '6×5 grid sweep (ucf × user_split) — identifies 2D fork outcome boundary; 7/28 v26 wins concentrated in split∈[0.30,0.50]; non-monotonic in ucf'
    },
    'lhs_user_weight_prim': {
        'sweep_type': 'lhs',
        'network_type': 'full',
        'description': '60-scenario LHS boundary characterization in (ucf, user_split) space — densifies contested zone from threshold grid; confirms non-monotonicity and falsifies split≥0.60 safe-zone assumption'
    },
}


def find_sweep_data_files(base_dir: Path) -> Dict[str, Path]:
    """Find all sweep_data.csv files and map to sweep names.

    Handles both standard paths (<sweep>/results/analysis/sweep_data.csv)
    and multi-variant paths (<sweep>/results_<suffix>/analysis/sweep_data.csv).
    For variants, the sweep name becomes <sweep>_<suffix>.
    """
    results = {}
    for csv_path in base_dir.glob("**/sweep_data.csv"):
        parts = csv_path.parts
        # Find a directory component that starts with 'results' and is
        # immediately followed by 'analysis'
        results_idx = None
        for i, part in enumerate(parts):
            if part.startswith('results') and i + 1 < len(parts) and parts[i + 1] == 'analysis':
                results_idx = i
                break
        if results_idx is not None and results_idx > 0:
            sweep_name = parts[results_idx - 1]
            results_dir = parts[results_idx]
            # If results dir has a suffix (e.g., results_144), append it
            if results_dir != 'results':
                suffix = results_dir[len('results_'):]
                sweep_name = f"{sweep_name}_{suffix}"
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

            # Helper for optional float fields
            def opt_float(key):
                val = row.get(key)
                if val is None or val == '' or val == 'None':
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            # Helper for optional int/bool fields
            def opt_int(key):
                val = row.get(key)
                if val is None or val == '' or val == 'None':
                    return None
                try:
                    # Handle boolean strings
                    if val in ('True', 'true', '1'):
                        return 1
                    if val in ('False', 'false', '0'):
                        return 0
                    return int(float(val))
                except (ValueError, TypeError):
                    return None

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
                    user_custody_fraction, user_split,
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
                    cascade_occurred, hashrate_flipped, profitability_gap,
                    econ_initial, econ_final, econ_delta, econ_switched,
                    econ_outcome, econ_switch_time_s, econ_95pct_time_s,
                    cascade_time_s, econ_lag_s, peak_price_gap_pct
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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
                opt_float('user_custody_fraction'),
                opt_float('user_split'),
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
                profitability_gap,
                # Temporal/cascade dynamics
                opt_float('econ_initial'),
                opt_float('econ_final'),
                opt_float('econ_delta'),
                opt_int('econ_switched'),
                row.get('econ_outcome', None) or None,
                opt_float('econ_switch_time_s'),
                opt_float('econ_95pct_time_s'),
                opt_float('cascade_time_s'),
                opt_float('econ_lag_s'),
                opt_float('peak_price_gap_pct'),
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
