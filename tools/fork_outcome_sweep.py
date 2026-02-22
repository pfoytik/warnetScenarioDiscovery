#!/usr/bin/env python3
"""
Fork Outcome Phase Space Parameter Sweep Generator

Generates scenarios to map the fork outcome phase space across multiple dimensions:
- Ideology thresholds (by participant category)
- Max loss tolerance (cost to maintain fork preference)
- Hashrate distribution (minority vs majority)
- Economic distribution (custody and volume weights)
- User participation (solo miner hashrate contribution)

Uses Latin Hypercube Sampling for efficient coverage of the parameter space.

Usage:
    # Generate 100 scenarios
    python fork_outcome_sweep.py --samples 100 --output-dir sweeps/fork_outcomes_100

    # Generate with specific seed for reproducibility
    python fork_outcome_sweep.py --samples 200 --seed 42 --output-dir sweeps/fork_outcomes_200

    # Preview without generating files
    python fork_outcome_sweep.py --samples 50 --preview

    # Use custom base network
    python fork_outcome_sweep.py --samples 100 --base-network networks/realistic-economy/network.yaml
"""

import argparse
import copy
import json
import os
import shutil
import yaml
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime


def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types for YAML serialization"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


@dataclass
class ParameterRange:
    """Defines a parameter's range and sampling type"""
    name: str
    min_val: float
    max_val: float
    param_type: str = "continuous"  # continuous, discrete, categorical
    categories: List[Any] = None
    description: str = ""

    def sample(self, normalized_value: float) -> Any:
        """Convert normalized [0,1] value to actual parameter value"""
        if self.param_type == "continuous":
            return self.min_val + normalized_value * (self.max_val - self.min_val)
        elif self.param_type == "discrete":
            val = int(self.min_val + normalized_value * (self.max_val - self.min_val + 0.999))
            return min(val, int(self.max_val))
        elif self.param_type == "categorical":
            idx = int(normalized_value * len(self.categories))
            idx = min(idx, len(self.categories) - 1)
            return self.categories[idx]
        return normalized_value


# =============================================================================
# FORK OUTCOME PHASE SPACE PARAMETERS
# =============================================================================
# These parameters define the dimensions we want to explore to understand
# what conditions lead to different fork outcomes.

PARAMETER_SPACE = [
    # -------------------------------------------------------------------------
    # HASHRATE DISTRIBUTION
    # -------------------------------------------------------------------------
    ParameterRange(
        "v27_pool_hashrate_pct", 15, 85, "continuous",
        description="Percentage of pool hashrate allocated to v27 fork"
    ),

    # -------------------------------------------------------------------------
    # IDEOLOGY THRESHOLDS (by category)
    # -------------------------------------------------------------------------
    ParameterRange(
        "pool_ideology_committed", 0.7, 1.0, "continuous",
        description="Ideology strength for committed pools (Foundry, Ocean)"
    ),
    ParameterRange(
        "pool_ideology_moderate", 0.3, 0.7, "continuous",
        description="Ideology strength for moderate pools"
    ),
    ParameterRange(
        "pool_ideology_rational", 0.0, 0.3, "continuous",
        description="Ideology strength for rational/profit-driven pools"
    ),
    ParameterRange(
        "exchange_ideology", 0.0, 0.4, "continuous",
        description="Ideology strength for major exchanges"
    ),
    ParameterRange(
        "institution_ideology", 0.1, 0.8, "continuous",
        description="Ideology strength for institutional holders"
    ),
    ParameterRange(
        "power_user_ideology", 0.5, 0.95, "continuous",
        description="Ideology strength for power users/developers"
    ),
    ParameterRange(
        "casual_user_ideology", 0.0, 0.5, "continuous",
        description="Ideology strength for casual users"
    ),

    # -------------------------------------------------------------------------
    # MAX LOSS TOLERANCE (cost to maintain fork preference)
    # -------------------------------------------------------------------------
    ParameterRange(
        "pool_max_loss_committed", 0.30, 0.80, "continuous",
        description="Max loss % committed pools will accept"
    ),
    ParameterRange(
        "pool_max_loss_moderate", 0.10, 0.40, "continuous",
        description="Max loss % moderate pools will accept"
    ),
    ParameterRange(
        "exchange_max_loss", 0.02, 0.15, "continuous",
        description="Max loss % exchanges will accept"
    ),
    ParameterRange(
        "user_max_loss", 0.10, 0.50, "continuous",
        description="Max loss % users will accept"
    ),

    # -------------------------------------------------------------------------
    # ECONOMIC DISTRIBUTION
    # -------------------------------------------------------------------------
    ParameterRange(
        "v27_economic_weight", 0.2, 0.8, "continuous",
        description="Fraction of economic weight (custody) on v27"
    ),
    ParameterRange(
        "v27_volume_weight", 0.2, 0.8, "continuous",
        description="Fraction of transaction volume on v27"
    ),

    # -------------------------------------------------------------------------
    # USER PARTICIPATION
    # -------------------------------------------------------------------------
    ParameterRange(
        "user_solo_hashrate_multiplier", 0.5, 3.0, "continuous",
        description="Multiplier for user solo mining hashrate"
    ),
    ParameterRange(
        "power_user_count_multiplier", 0.5, 2.0, "continuous",
        description="Multiplier for number of power users (affects solo hash)"
    ),

    # -------------------------------------------------------------------------
    # SWITCHING BEHAVIOR
    # -------------------------------------------------------------------------
    ParameterRange(
        "switching_inertia", 0.05, 0.35, "continuous",
        description="Base inertia (resistance to switching)"
    ),
    ParameterRange(
        "switching_threshold", 0.02, 0.20, "continuous",
        description="Price advantage needed to consider switching"
    ),

    # -------------------------------------------------------------------------
    # FORK TYPE
    # -------------------------------------------------------------------------
    ParameterRange(
        "fork_type", 0, 2, "discrete",
        categories=["hard_fork", "contentious_soft_fork", "non_contentious_soft_fork"],
        description="Type of fork being simulated"
    ),
]


def latin_hypercube_sample(n_samples: int, n_dimensions: int, seed: int = None) -> np.ndarray:
    """
    Generate Latin Hypercube Samples for efficient parameter space coverage.
    Returns array of shape (n_samples, n_dimensions) with values in [0, 1].
    """
    rng = np.random.RandomState(seed)
    samples = np.zeros((n_samples, n_dimensions))

    for dim in range(n_dimensions):
        # Create evenly spaced intervals
        intervals = np.linspace(0, 1, n_samples + 1)
        # Sample uniformly within each interval
        points = np.array([
            rng.uniform(intervals[i], intervals[i + 1])
            for i in range(n_samples)
        ])
        # Randomly permute
        rng.shuffle(points)
        samples[:, dim] = points

    return samples


def generate_samples(n_samples: int, seed: int = None) -> List[Dict[str, Any]]:
    """Generate LHS samples across the parameter space"""
    n_dims = len(PARAMETER_SPACE)
    lhs_samples = latin_hypercube_sample(n_samples, n_dims, seed)

    scenarios = []
    for i, sample in enumerate(lhs_samples):
        scenario = {"scenario_id": f"fork_sweep_{i:04d}"}

        for j, param in enumerate(PARAMETER_SPACE):
            value = param.sample(sample[j])
            # Handle categorical separately
            if param.param_type == "categorical":
                scenario[param.name] = param.categories[int(value)]
            else:
                scenario[param.name] = round(value, 4) if isinstance(value, float) else value

        scenarios.append(scenario)

    return scenarios


def load_base_network(network_path: Path) -> Dict:
    """Load the base network configuration"""
    with open(network_path) as f:
        return yaml.safe_load(f)


def apply_scenario_to_network(base_network: Dict, scenario: Dict) -> Dict:
    """
    Apply scenario parameters to the base network configuration.
    Returns a modified copy of the network.
    """
    network = copy.deepcopy(base_network)
    nodes = network.get('nodes', [])

    # Calculate hashrate distribution
    v27_hash_target = scenario['v27_pool_hashrate_pct']
    v26_hash_target = 100 - v27_hash_target

    # Track pool assignments for hashrate balancing
    pool_nodes = [n for n in nodes if n.get('metadata', {}).get('role') == 'mining_pool']
    total_hashrate = sum(n['metadata'].get('hashrate_pct', 0) for n in pool_nodes)

    # Sort pools by hashrate for strategic assignment
    pool_nodes_sorted = sorted(pool_nodes, key=lambda n: n['metadata'].get('hashrate_pct', 0), reverse=True)

    # Assign pools to forks to match target distribution
    v27_hash_accumulated = 0
    v27_pools = set()

    for pool in pool_nodes_sorted:
        pool_hash = pool['metadata'].get('hashrate_pct', 0)
        # Assign to v27 if it helps reach target without overshooting too much
        if v27_hash_accumulated + pool_hash <= v27_hash_target + 5:  # 5% tolerance
            v27_pools.add(pool['name'])
            v27_hash_accumulated += pool_hash

    # Apply parameters to each node
    for node in nodes:
        metadata = node.get('metadata', {})
        role = metadata.get('role', '')
        node_name = node.get('name', '')

        # Determine fork preference based on partition and scenario
        is_v27_partition = node['image']['tag'] == '27.0'

        # =====================================================================
        # MINING POOLS
        # =====================================================================
        if role == 'mining_pool':
            # Assign fork preference based on hashrate distribution
            if node_name in v27_pools:
                metadata['fork_preference'] = 'v27'
            else:
                metadata['fork_preference'] = 'v26'

            # Apply ideology based on pool type
            pool_name = metadata.get('pool_name', '').lower()
            if 'foundry' in pool_name or 'ocean' in pool_name:
                # Committed pools
                metadata['ideology_strength'] = scenario['pool_ideology_committed']
                metadata['max_loss_pct'] = scenario['pool_max_loss_committed']
            elif 'mara' in pool_name or 'luxor' in pool_name or 'braiins' in pool_name:
                # Moderate pools
                metadata['ideology_strength'] = scenario['pool_ideology_moderate']
                metadata['max_loss_pct'] = scenario['pool_max_loss_moderate']
            else:
                # Rational pools
                metadata['ideology_strength'] = scenario['pool_ideology_rational']
                metadata['max_loss_pct'] = scenario['pool_max_loss_moderate'] * 0.5

        # =====================================================================
        # MAJOR EXCHANGES
        # =====================================================================
        elif role == 'major_exchange':
            metadata['ideology_strength'] = scenario['exchange_ideology']
            metadata['max_loss_pct'] = scenario['exchange_max_loss']
            metadata['switching_threshold'] = scenario['switching_threshold']
            metadata['inertia'] = scenario['switching_inertia'] * 1.5  # Higher inertia for exchanges

        # =====================================================================
        # MID-TIER EXCHANGES
        # =====================================================================
        elif role == 'exchange':
            metadata['ideology_strength'] = scenario['exchange_ideology'] * 1.5  # Slightly more ideological
            metadata['max_loss_pct'] = scenario['exchange_max_loss'] * 1.2
            metadata['switching_threshold'] = scenario['switching_threshold']
            metadata['inertia'] = scenario['switching_inertia']

        # =====================================================================
        # INSTITUTIONAL HOLDERS
        # =====================================================================
        elif role == 'institutional':
            metadata['ideology_strength'] = scenario['institution_ideology']
            metadata['max_loss_pct'] = scenario['user_max_loss']
            metadata['inertia'] = scenario['switching_inertia'] * 2  # Very high inertia

        # =====================================================================
        # PAYMENT PROCESSORS
        # =====================================================================
        elif role == 'payment_processor':
            metadata['ideology_strength'] = scenario['power_user_ideology'] * 0.8
            metadata['max_loss_pct'] = scenario['user_max_loss'] * 0.8
            metadata['switching_threshold'] = scenario['switching_threshold']

        # =====================================================================
        # MERCHANTS
        # =====================================================================
        elif role == 'merchant':
            metadata['ideology_strength'] = scenario['casual_user_ideology'] * 1.5
            metadata['max_loss_pct'] = scenario['exchange_max_loss']
            metadata['switching_threshold'] = scenario['switching_threshold']

        # =====================================================================
        # POWER USERS
        # =====================================================================
        elif role == 'power_user':
            metadata['ideology_strength'] = scenario['power_user_ideology']
            metadata['max_loss_pct'] = scenario['user_max_loss']
            metadata['switching_threshold'] = scenario['switching_threshold'] * 2

            # Scale solo mining hashrate
            if metadata.get('hashrate_pct', 0) > 0:
                metadata['hashrate_pct'] *= scenario['user_solo_hashrate_multiplier']

        # =====================================================================
        # CASUAL USERS
        # =====================================================================
        elif role == 'casual_user':
            metadata['ideology_strength'] = scenario['casual_user_ideology']
            metadata['max_loss_pct'] = scenario['user_max_loss'] * 0.6
            metadata['switching_threshold'] = scenario['switching_threshold']

            # Scale solo mining hashrate (if any)
            if metadata.get('hashrate_pct', 0) > 0:
                metadata['hashrate_pct'] *= scenario['user_solo_hashrate_multiplier']

        # =====================================================================
        # FORK TYPE - affects accepts_foreign_blocks
        # =====================================================================
        fork_type = scenario.get('fork_type', 'contentious_soft_fork')
        if fork_type == 'hard_fork':
            metadata['accepts_foreign_blocks'] = False
        elif fork_type == 'contentious_soft_fork':
            metadata['accepts_foreign_blocks'] = False  # URSF active
        elif fork_type == 'non_contentious_soft_fork':
            # v26 nodes accept v27 blocks (permissive)
            metadata['accepts_foreign_blocks'] = not is_v27_partition

        node['metadata'] = metadata

    return network


def create_sweep_manifest(scenarios: List[Dict], output_dir: Path, base_network_path: Path) -> Dict:
    """Create manifest file describing the sweep"""
    return {
        "sweep_id": f"fork_sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created": datetime.now().isoformat(),
        "n_scenarios": len(scenarios),
        "base_network": str(base_network_path),
        "parameter_space": [
            {
                "name": p.name,
                "min": p.min_val,
                "max": p.max_val,
                "type": p.param_type,
                "description": p.description
            }
            for p in PARAMETER_SPACE
        ],
        "scenarios": [s["scenario_id"] for s in scenarios],
    }


def create_run_script(scenarios: List[Dict], output_dir: Path, duration: int = 3600) -> str:
    """Create bash script to run all scenarios"""
    lines = [
        "#!/bin/bash",
        "# Fork Outcome Parameter Sweep Runner",
        f"# Generated {len(scenarios)} scenarios",
        f"# Duration per scenario: {duration}s ({duration/60:.0f} min)",
        "",
        "set -e",
        "",
        "# Get absolute path of script directory",
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        'SWEEP_DIR="$SCRIPT_DIR"',
        'RESULTS_DIR="$SWEEP_DIR/results"',
        'PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"',
        'SCENARIOS_DIR="$PROJECT_DIR/scenarios"',
        'TOOLS_DIR="$PROJECT_DIR/tools"',
        "",
        'mkdir -p "$RESULTS_DIR"',
        "",
        f'echo "Starting fork outcome sweep with {len(scenarios)} scenarios"',
        'echo "Results will be saved to $RESULTS_DIR"',
        'echo ""',
        "",
        'START_TIME=$(date +%s)',
        'COMPLETED=0',
        'FAILED=0',
        "",
    ]

    # Add wait_for_scenario function
    lines.extend([
        '# Function to wait for scenario completion by polling warnet status',
        'wait_for_scenario() {',
        '  local max_wait=$1',
        '  local poll_interval=30',
        '  local elapsed=0',
        '  ',
        '  echo "  Waiting for scenario to complete (max ${max_wait}s)..."',
        '  while [ $elapsed -lt $max_wait ]; do',
        '    sleep $poll_interval',
        '    elapsed=$((elapsed + poll_interval))',
        '    ',
        '    # Check warnet status for scenario completion',
        '    status_output=$(warnet status 2>&1)',
        '    ',
        '    # Check for success',
        '    if echo "$status_output" | grep -qi "succeeded\\|completed"; then',
        '      echo "  Scenario completed successfully"',
        '      return 0',
        '    fi',
        '    ',
        '    # Check for failure',
        '    if echo "$status_output" | grep -qi "failed\\|error"; then',
        '      echo "  Scenario failed"',
        '      return 1',
        '    fi',
        '    ',
        '    # Check if no active scenarios (might have finished)',
        '    if echo "$status_output" | grep -qi "no active scenarios"; then',
        '      echo "  No active scenarios - assuming completed"',
        '      return 0',
        '    fi',
        '    ',
        '    echo "  Still running... (${elapsed}s elapsed)"',
        '  done',
        '  ',
        '  echo "  Timeout waiting for scenario"',
        '  return 1',
        '}',
        '',
    ])

    for i, scenario in enumerate(scenarios):
        scenario_id = scenario["scenario_id"]
        # Add buffer time for scenario (duration + 5 min for startup/cleanup)
        max_wait = duration + 300
        lines.extend([
            f'# Scenario {i+1}/{len(scenarios)}: {scenario_id}',
            f'echo "[{i+1}/{len(scenarios)}] Running {scenario_id}..."',
            f'if [ -f "$RESULTS_DIR/{scenario_id}/results.json" ]; then',
            f'  echo "  Skipping (already completed)"',
            f'  ((COMPLETED++)) || true',
            'else',
            '  # Deploy network (warnet expects a directory containing network.yaml)',
            f'  if warnet deploy "$SWEEP_DIR/networks/{scenario_id}" 2>&1; then',
            '    sleep 30  # Wait for network to stabilize',
            '',
            '    # Start scenario (runs in background)',
            f'    echo "  Starting scenario..."',
            f'    warnet run "$SCENARIOS_DIR/partition_miner_with_pools.py" \\',
            f'        --network "$SWEEP_DIR/networks/{scenario_id}/network.yaml" \\',
            '        --enable-difficulty \\',
            '        --retarget-interval 144 \\',
            '        --interval 1 \\',
            f'        --duration {duration} \\',
            f'        --results-id "{scenario_id}" \\',
            f'        2>&1 | tee "$RESULTS_DIR/{scenario_id}_start.log"',
            '',
            '    # Wait for scenario to complete',
            f'    if wait_for_scenario {max_wait}; then',
            '      # Extract results',
            f'      echo "  Extracting results..."',
            f'      python "$TOOLS_DIR/extract_results.py" {scenario_id} \\',
            f'        --output-dir "$RESULTS_DIR/{scenario_id}" 2>&1 || true',
            '      ',
            '      # Save warnet logs',
            f'      warnet logs > "$RESULTS_DIR/{scenario_id}_warnet.log" 2>&1 || true',
            '      ((COMPLETED++)) || true',
            '    else',
            f'      echo "  FAILED: Scenario {scenario_id}"',
            f'      warnet logs > "$RESULTS_DIR/{scenario_id}_warnet.log" 2>&1 || true',
            '      ((FAILED++)) || true',
            '    fi',
            '',
            '    # Cleanup',
            '    echo "  Cleaning up..."',
            '    warnet stop 2>/dev/null || true',
            '    sleep 5',
            '    warnet down --force 2>/dev/null || true',
            '    sleep 10',
            '  else',
            f'    echo "  FAILED: Could not deploy network for {scenario_id}"',
            '    ((FAILED++)) || true',
            '  fi',
            'fi',
            'echo ""',
            '',
        ])

    lines.extend([
        'END_TIME=$(date +%s)',
        'ELAPSED=$((END_TIME - START_TIME))',
        'echo ""',
        'echo "========================================"',
        'echo "Fork outcome sweep complete!"',
        'echo "========================================"',
        'echo "Total scenarios: ' + str(len(scenarios)) + '"',
        'echo "Completed: $COMPLETED"',
        'echo "Failed: $FAILED"',
        'echo "Total time: $((ELAPSED / 3600))h $((ELAPSED % 3600 / 60))m $((ELAPSED % 60))s"',
        'echo "Results saved to: $RESULTS_DIR"',
    ])

    return "\n".join(lines)


def create_analysis_script(output_dir: Path) -> str:
    """Create Python script to analyze sweep results"""
    return '''#!/usr/bin/env python3
"""
Fork Outcome Sweep Analysis

Analyzes parameter sweep results to identify:
- Critical ideology thresholds for fork victory
- Max loss tolerance boundaries
- Hashrate minority survival thresholds
- Economic weight influence on outcomes
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

SWEEP_DIR = Path(__file__).parent
RESULTS_DIR = SWEEP_DIR / "results"
MANIFEST_FILE = SWEEP_DIR / "manifest.json"
PARAMS_FILE = SWEEP_DIR / "parameters.json"


def load_results() -> pd.DataFrame:
    """Load all scenario results into a DataFrame"""

    # Load parameters
    with open(PARAMS_FILE) as f:
        params = {s["scenario_id"]: s for s in json.load(f)}

    rows = []
    for scenario_dir in RESULTS_DIR.iterdir():
        if not scenario_dir.is_dir():
            continue

        scenario_id = scenario_dir.name
        results_file = scenario_dir / "results.json"

        if not results_file.exists():
            continue

        with open(results_file) as f:
            results = json.load(f)

        # Extract key outcomes
        summary = results.get("summary", {})
        difficulty = results.get("difficulty", {})
        uasf = results.get("uasf", {})

        row = {
            "scenario_id": scenario_id,
            # Outcomes
            "winner": difficulty.get("winning_fork", "unknown"),
            "v27_blocks": summary.get("blocks_mined", {}).get("v27", 0),
            "v26_blocks": summary.get("blocks_mined", {}).get("v26", 0),
            "v27_chainwork": difficulty.get("forks", {}).get("v27", {}).get("cumulative_chainwork", 0),
            "v26_chainwork": difficulty.get("forks", {}).get("v26", {}).get("cumulative_chainwork", 0),
            "v27_final_hashrate": summary.get("final_hashrate", {}).get("v27", 0),
            "v26_final_hashrate": summary.get("final_hashrate", {}).get("v26", 0),
            "v27_final_economic": summary.get("final_economic", {}).get("v27", 0),
            "v26_final_economic": summary.get("final_economic", {}).get("v26", 0),
            "uasf_outcome": uasf.get("uasf_outcome", "n/a"),
        }

        # Add input parameters
        if scenario_id in params:
            row.update(params[scenario_id])

        rows.append(row)

    return pd.DataFrame(rows)


def analyze_ideology_thresholds(df: pd.DataFrame) -> Dict:
    """Find critical ideology thresholds for fork victory"""

    results = {}

    # For each ideology parameter, find the threshold where v27 starts winning
    ideology_params = [col for col in df.columns if "ideology" in col]

    for param in ideology_params:
        v27_wins = df[df["winner"] == "v27"][param]
        v26_wins = df[df["winner"] == "v26"][param]

        if len(v27_wins) > 0 and len(v26_wins) > 0:
            results[param] = {
                "v27_win_mean": float(v27_wins.mean()),
                "v27_win_std": float(v27_wins.std()),
                "v26_win_mean": float(v26_wins.mean()),
                "v26_win_std": float(v26_wins.std()),
                "threshold_estimate": float((v27_wins.mean() + v26_wins.mean()) / 2),
            }

    return results


def analyze_hashrate_requirements(df: pd.DataFrame) -> Dict:
    """Find minimum hashrate for minority fork survival"""

    v27_wins = df[df["winner"] == "v27"]

    if len(v27_wins) == 0:
        return {"min_v27_hashrate_for_victory": None}

    return {
        "min_v27_hashrate_for_victory": float(v27_wins["v27_pool_hashrate_pct"].min()),
        "median_v27_hashrate_for_victory": float(v27_wins["v27_pool_hashrate_pct"].median()),
        "scenarios_where_minority_won": len(v27_wins[v27_wins["v27_pool_hashrate_pct"] < 50]),
    }


def analyze_economic_influence(df: pd.DataFrame) -> Dict:
    """Analyze how economic weight affects outcomes"""

    v27_wins = df[df["winner"] == "v27"]
    v26_wins = df[df["winner"] == "v26"]

    return {
        "v27_win_avg_economic_weight": float(v27_wins["v27_economic_weight"].mean()) if len(v27_wins) > 0 else None,
        "v26_win_avg_economic_weight": float(v26_wins["v27_economic_weight"].mean()) if len(v26_wins) > 0 else None,
        "economic_weight_correlation": float(df["v27_economic_weight"].corr(df["winner"].map({"v27": 1, "v26": 0}))),
    }


def generate_report(df: pd.DataFrame) -> str:
    """Generate analysis report"""

    lines = [
        "# Fork Outcome Sweep Analysis Report",
        f"",
        f"**Total scenarios analyzed:** {len(df)}",
        f"**v27 victories:** {len(df[df['winner'] == 'v27'])} ({100*len(df[df['winner'] == 'v27'])/len(df):.1f}%)",
        f"**v26 victories:** {len(df[df['winner'] == 'v26'])} ({100*len(df[df['winner'] == 'v26'])/len(df):.1f}%)",
        "",
        "## Ideology Thresholds",
        "",
    ]

    ideology_analysis = analyze_ideology_thresholds(df)
    for param, data in ideology_analysis.items():
        lines.append(f"### {param}")
        lines.append(f"- Threshold estimate: **{data['threshold_estimate']:.3f}**")
        lines.append(f"- v27 wins when: {data['v27_win_mean']:.3f} ± {data['v27_win_std']:.3f}")
        lines.append(f"- v26 wins when: {data['v26_win_mean']:.3f} ± {data['v26_win_std']:.3f}")
        lines.append("")

    lines.append("## Hashrate Requirements")
    hashrate_analysis = analyze_hashrate_requirements(df)
    for key, value in hashrate_analysis.items():
        lines.append(f"- {key}: **{value}**")
    lines.append("")

    lines.append("## Economic Influence")
    econ_analysis = analyze_economic_influence(df)
    for key, value in econ_analysis.items():
        lines.append(f"- {key}: **{value}**")

    return "\\n".join(lines)


def plot_phase_space(df: pd.DataFrame, output_dir: Path):
    """Generate phase space visualizations"""

    # Ideology vs Hashrate phase diagram
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Plot 1: Pool ideology vs hashrate
    ax = axes[0, 0]
    colors = df["winner"].map({"v27": "blue", "v26": "red"})
    ax.scatter(df["v27_pool_hashrate_pct"], df["pool_ideology_committed"], c=colors, alpha=0.6)
    ax.set_xlabel("v27 Pool Hashrate %")
    ax.set_ylabel("Pool Ideology (Committed)")
    ax.set_title("Pool Ideology vs Hashrate")
    ax.axvline(50, color="gray", linestyle="--", alpha=0.5)

    # Plot 2: Economic weight vs hashrate
    ax = axes[0, 1]
    ax.scatter(df["v27_pool_hashrate_pct"], df["v27_economic_weight"], c=colors, alpha=0.6)
    ax.set_xlabel("v27 Pool Hashrate %")
    ax.set_ylabel("v27 Economic Weight")
    ax.set_title("Economic Weight vs Hashrate")
    ax.axvline(50, color="gray", linestyle="--", alpha=0.5)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)

    # Plot 3: Max loss tolerance vs ideology
    ax = axes[1, 0]
    ax.scatter(df["pool_ideology_committed"], df["pool_max_loss_committed"], c=colors, alpha=0.6)
    ax.set_xlabel("Pool Ideology (Committed)")
    ax.set_ylabel("Pool Max Loss Tolerance")
    ax.set_title("Max Loss vs Ideology")

    # Plot 4: User participation effect
    ax = axes[1, 1]
    ax.scatter(df["user_solo_hashrate_multiplier"], df["power_user_ideology"], c=colors, alpha=0.6)
    ax.set_xlabel("User Solo Hashrate Multiplier")
    ax.set_ylabel("Power User Ideology")
    ax.set_title("User Participation Effect")

    plt.tight_layout()
    plt.savefig(output_dir / "phase_space.png", dpi=150)
    plt.close()

    print(f"Phase space plot saved to {output_dir / 'phase_space.png'}")


if __name__ == "__main__":
    print("Loading results...")
    df = load_results()

    if len(df) == 0:
        print("No results found!")
        exit(1)

    print(f"Loaded {len(df)} scenarios")

    # Generate report
    report = generate_report(df)
    report_file = SWEEP_DIR / "analysis_report.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"Report saved to {report_file}")

    # Save data
    df.to_csv(SWEEP_DIR / "sweep_data.csv", index=False)
    print(f"Data saved to {SWEEP_DIR / 'sweep_data.csv'}")

    # Generate plots
    plot_phase_space(df, SWEEP_DIR)

    print("\\nAnalysis complete!")
'''


def main():
    parser = argparse.ArgumentParser(
        description="Generate fork outcome parameter sweep scenarios"
    )
    parser.add_argument(
        "--samples", type=int, default=100,
        help="Number of scenarios to generate (default: 100)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir", type=str, required=True,
        help="Output directory for sweep files"
    )
    parser.add_argument(
        "--base-network", type=str,
        default="networks/realistic-economy/network.yaml",
        help="Path to base network configuration"
    )
    parser.add_argument(
        "--duration", type=int, default=3600,
        help="Duration per scenario in seconds (default: 3600)"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Preview scenarios without generating files"
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    base_network_path = script_dir.parent / args.base_network
    output_dir = Path(args.output_dir)

    if not base_network_path.exists():
        print(f"Error: Base network not found: {base_network_path}")
        return 1

    print(f"Fork Outcome Parameter Sweep Generator")
    print(f"=" * 50)
    print(f"Samples: {args.samples}")
    print(f"Seed: {args.seed or 'random'}")
    print(f"Base network: {base_network_path}")
    print(f"Output dir: {output_dir}")
    print(f"Duration per scenario: {args.duration}s")
    print()

    # Generate samples
    print(f"Generating {args.samples} scenarios using Latin Hypercube Sampling...")
    scenarios = generate_samples(args.samples, args.seed)

    if args.preview:
        print("\nPreview of first 5 scenarios:")
        for s in scenarios[:5]:
            print(f"\n{s['scenario_id']}:")
            for k, v in list(s.items())[:8]:
                print(f"  {k}: {v}")
            print("  ...")
        return 0

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "networks").mkdir(exist_ok=True)
    (output_dir / "results").mkdir(exist_ok=True)

    # Load base network
    print(f"\nLoading base network: {base_network_path}")
    base_network = load_base_network(base_network_path)

    # Find node-defaults.yaml (check base network dir first, then parent networks/ dir)
    node_defaults_path = base_network_path.parent / "node-defaults.yaml"
    if not node_defaults_path.exists():
        node_defaults_path = base_network_path.parent.parent / "node-defaults.yaml"
    if not node_defaults_path.exists():
        # Create a minimal node-defaults.yaml
        node_defaults_content = """chain: regtest
image:
  repository: bitcoindevproject/bitcoin
  pullPolicy: IfNotPresent
defaultConfig: 'regtest=1
  server=1
  txindex=1
  fallbackfee=0.00001
  rpcuser=bitcoin
  rpcpassword=bitcoin
  rpcallowip=0.0.0.0/0
  rpcbind=0.0.0.0
  rpcport=18443
  zmqpubrawblock=tcp://0.0.0.0:28332
  zmqpubrawtx=tcp://0.0.0.0:28333
  debug=rpc'
collectLogs: false
metricsExport: false
"""
        node_defaults_path = None
        node_defaults_inline = node_defaults_content
    else:
        node_defaults_inline = None

    # Generate network configs (each in its own directory for warnet deploy)
    print(f"Generating {args.samples} network configurations...")
    for scenario in scenarios:
        network = apply_scenario_to_network(base_network, scenario)
        # Convert numpy types to native Python types for clean YAML output
        network = convert_numpy_types(network)
        # Create directory for this scenario's network
        network_dir = output_dir / "networks" / scenario['scenario_id']
        network_dir.mkdir(parents=True, exist_ok=True)
        network_file = network_dir / "network.yaml"
        with open(network_file, "w") as f:
            yaml.dump(network, f, default_flow_style=False, sort_keys=False)

        # Copy or create node-defaults.yaml
        node_defaults_dest = network_dir / "node-defaults.yaml"
        if node_defaults_path:
            shutil.copy(node_defaults_path, node_defaults_dest)
        else:
            with open(node_defaults_dest, "w") as f:
                f.write(node_defaults_inline)

    # Save parameters (convert numpy types for clean JSON)
    params_file = output_dir / "parameters.json"
    with open(params_file, "w") as f:
        json.dump(convert_numpy_types(scenarios), f, indent=2)
    print(f"Parameters saved to: {params_file}")

    # Create manifest
    manifest = create_sweep_manifest(scenarios, output_dir, base_network_path)
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to: {manifest_file}")

    # Create run script
    run_script = create_run_script(scenarios, output_dir, args.duration)
    run_script_file = output_dir / "run_sweep.sh"
    with open(run_script_file, "w") as f:
        f.write(run_script)
    os.chmod(run_script_file, 0o755)
    print(f"Run script saved to: {run_script_file}")

    # Create analysis script
    analysis_script = create_analysis_script(output_dir)
    analysis_file = output_dir / "analyze_results.py"
    with open(analysis_file, "w") as f:
        f.write(analysis_script)
    os.chmod(analysis_file, 0o755)
    print(f"Analysis script saved to: {analysis_file}")

    print(f"\n{'=' * 50}")
    print("Sweep generation complete!")
    print(f"{'=' * 50}")
    print(f"\nTo run the sweep:")
    print(f"  cd {output_dir}")
    print(f"  ./run_sweep.sh")
    print(f"\nTo analyze results:")
    print(f"  python {analysis_file}")

    return 0


if __name__ == "__main__":
    exit(main())
