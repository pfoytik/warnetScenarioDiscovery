#!/usr/bin/env python3
"""
Latin Hypercube Sampling Parameter Sweep Generator

Generates a statistically efficient set of scenarios to explore the
fork threshold parameter space without testing every combination.

Usage:
    # Generate 200 scenarios
    python parameter_sweep.py --samples 200 --output-dir ../sweep_configs

    # Generate with specific seed for reproducibility
    python parameter_sweep.py --samples 300 --seed 42 --output-dir ../sweep_configs

    # Preview without generating files
    python parameter_sweep.py --samples 50 --preview
"""

import argparse
import json
import os
import yaml
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple
from pathlib import Path


@dataclass
class ParameterRange:
    """Defines a parameter's range and type"""
    name: str
    min_val: float
    max_val: float
    param_type: str = "continuous"  # continuous, discrete, categorical
    categories: List[Any] = None

    def sample(self, normalized_value: float) -> Any:
        """Convert normalized [0,1] value to actual parameter value"""
        if self.param_type == "continuous":
            return self.min_val + normalized_value * (self.max_val - self.min_val)
        elif self.param_type == "discrete":
            # Map to discrete integer range
            val = int(self.min_val + normalized_value * (self.max_val - self.min_val + 0.999))
            return min(val, int(self.max_val))
        elif self.param_type == "categorical":
            idx = int(normalized_value * len(self.categories))
            idx = min(idx, len(self.categories) - 1)
            return self.categories[idx]
        return normalized_value


# Define the parameter space
PARAMETER_SPACE = [
    # Initial conditions
    ParameterRange("v27_economic_pct", 20, 80, "continuous"),
    ParameterRange("v27_hashrate_pct", 20, 80, "continuous"),

    # Pool behavior
    ParameterRange("pool_ideology_strength", 0.1, 0.9, "continuous"),
    ParameterRange("pool_profitability_threshold", 0.02, 0.30, "continuous"),
    ParameterRange("pool_max_loss_pct", 0.02, 0.50, "continuous"),
    ParameterRange("pool_v27_preference_pct", 10, 70, "continuous"),  # % of pools preferring v27
    ParameterRange("pool_neutral_pct", 10, 50, "continuous"),  # % of pools neutral

    # Economic node behavior
    ParameterRange("econ_ideology_strength", 0.0, 0.8, "continuous"),
    ParameterRange("econ_switching_threshold", 0.02, 0.25, "continuous"),
    ParameterRange("econ_inertia", 0.05, 0.30, "continuous"),

    # User behavior
    ParameterRange("user_ideology_strength", 0.1, 0.9, "continuous"),
    ParameterRange("user_switching_threshold", 0.05, 0.20, "continuous"),

    # Fee market
    ParameterRange("transaction_velocity", 0.1, 0.9, "continuous"),

    # Network structure
    ParameterRange("user_nodes_per_partition", 2, 10, "discrete"),
    ParameterRange("economic_nodes_per_partition", 1, 3, "discrete"),
    ParameterRange("solo_miner_hashrate", 0.02, 0.15, "continuous"),
]


def latin_hypercube_sample(n_samples: int, n_dimensions: int, seed: int = None) -> np.ndarray:
    """
    Generate Latin Hypercube Samples.

    Returns array of shape (n_samples, n_dimensions) with values in [0, 1]
    """
    rng = np.random.RandomState(seed)

    # Create the intervals
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
        scenario = {"scenario_id": f"sweep_{i:04d}"}

        for j, param in enumerate(PARAMETER_SPACE):
            scenario[param.name] = param.sample(sample[j])

        # Round continuous values for readability
        for key in scenario:
            if isinstance(scenario[key], float):
                scenario[key] = round(scenario[key], 3)

        scenarios.append(scenario)

    return scenarios


def create_pool_scenario_config(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create mining pool scenario config from parameters"""

    # Real pool distribution
    pools = [
        ("foundryusa", 26.89),
        ("antpool", 19.25),
        ("viabtc", 11.39),
        ("f2pool", 11.25),
        ("binancepool", 10.04),
        ("marapool", 8.25),
        ("sbicrypto", 4.57),
        ("luxor", 3.94),
        ("ocean", 1.42),
        ("braiinspool", 1.37),
    ]

    # Distribute preferences based on parameters
    v27_pct = scenario["pool_v27_preference_pct"] / 100
    neutral_pct = scenario["pool_neutral_pct"] / 100
    v26_pct = max(0, 1 - v27_pct - neutral_pct)

    # Normalize
    total = v27_pct + v26_pct + neutral_pct
    v27_pct /= total
    v26_pct /= total
    neutral_pct /= total

    pool_configs = []
    cumulative = 0

    for pool_id, hashrate in pools:
        # Assign preference based on cumulative distribution
        midpoint = cumulative + hashrate / 200  # Midpoint of this pool's "band"

        if midpoint < v27_pct * 100:
            pref = "v27"
        elif midpoint < (v27_pct + v26_pct) * 100:
            pref = "v26"
        else:
            pref = "neutral"

        # Neutral pools have lower ideology
        ideology = scenario["pool_ideology_strength"] if pref != "neutral" else 0.1

        pool_configs.append({
            "pool_id": pool_id,
            "hashrate_pct": hashrate,
            "fork_preference": pref,
            "ideology_strength": round(ideology, 2),
            "profitability_threshold": scenario["pool_profitability_threshold"],
            "max_loss_pct": scenario["pool_max_loss_pct"] if pref != "neutral" else 0.02,
        })

        cumulative += hashrate

    return {
        "description": f"Generated scenario {scenario['scenario_id']}",
        "pools": pool_configs
    }


def create_economic_scenario_config(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create economic scenario config from parameters"""
    return {
        "description": f"Generated scenario {scenario['scenario_id']}",
        "economic_defaults": {
            "fork_preference": "neutral",
            "ideology_strength": scenario["econ_ideology_strength"],
            "switching_threshold": scenario["econ_switching_threshold"],
            "inertia": scenario["econ_inertia"],
            "switching_cooldown": 1800,
            "max_loss_pct": min(0.30, scenario["econ_ideology_strength"] * 0.5),
        },
        "user_defaults": {
            "fork_preference": "neutral",
            "ideology_strength": scenario["user_ideology_strength"],
            "switching_threshold": scenario["user_switching_threshold"],
            "inertia": 0.05,
            "switching_cooldown": 3600,
            "max_loss_pct": min(0.40, scenario["user_ideology_strength"] * 0.6),
        }
    }


def create_network_config(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create network generation config from parameters"""
    return {
        "name": scenario["scenario_id"],
        "description": f"Parameter sweep scenario {scenario['scenario_id']}",
        "v27_economic_pct": scenario["v27_economic_pct"],
        "v27_hashrate_pct": scenario["v27_hashrate_pct"],
        "economic_nodes_per_partition": int(scenario["economic_nodes_per_partition"]),
        "user_nodes_per_partition": int(scenario["user_nodes_per_partition"]),
        "v27_economic": {
            "fork_preference": "v27",
            "ideology_strength": scenario["econ_ideology_strength"],
            "switching_threshold": scenario["econ_switching_threshold"],
            "inertia": scenario["econ_inertia"],
            "activity_type": "transactional",
            "transaction_velocity": scenario["transaction_velocity"],
        },
        "v26_economic": {
            "fork_preference": "v26",
            "ideology_strength": scenario["econ_ideology_strength"],
            "switching_threshold": scenario["econ_switching_threshold"],
            "inertia": scenario["econ_inertia"],
            "activity_type": "transactional",
            "transaction_velocity": scenario["transaction_velocity"],
        },
        "user_config": {
            "fork_preference": "neutral",
            "ideology_strength": scenario["user_ideology_strength"],
            "switching_threshold": scenario["user_switching_threshold"],
            "inertia": 0.05,
            "activity_type": "mixed",
            "transaction_velocity": scenario["transaction_velocity"],
            "is_solo_miner": True,
            "hashrate_pct": scenario["solo_miner_hashrate"],
        },
        "partition_mode": "static",
        "fork_observer_enabled": False,
    }


def create_run_script(scenarios: List[Dict], output_dir: Path, duration: int = 1800) -> str:
    """Create bash script to run all scenarios"""

    lines = [
        "#!/bin/bash",
        "# Parameter Sweep Runner",
        f"# Generated {len(scenarios)} scenarios",
        "",
        "set -e",
        "",
        f"SWEEP_DIR=\"{output_dir}\"",
        "SCENARIOS_DIR=\"$(dirname $0)/../scenarios\"",
        "RESULTS_DIR=\"$SWEEP_DIR/results\"",
        "",
        "mkdir -p \"$RESULTS_DIR\"",
        "",
        "echo \"Starting parameter sweep with {} scenarios\"".format(len(scenarios)),
        "echo \"Results will be saved to $RESULTS_DIR\"",
        "",
        "START_TIME=$(date +%s)",
        "",
    ]

    for i, scenario in enumerate(scenarios):
        scenario_id = scenario["scenario_id"]
        lines.extend([
            f"# Scenario {i+1}/{len(scenarios)}: {scenario_id}",
            f"echo \"[{i+1}/{len(scenarios)}] Running {scenario_id}...\"",
            f"if [ ! -f \"$RESULTS_DIR/{scenario_id}/results.json\" ]; then",
            f"  warnet run $SCENARIOS_DIR/partition_miner_with_pools.py \\",
            f"    --network=$SWEEP_DIR/networks/{scenario_id} \\",
            f"    --pool-scenario={scenario_id} \\",
            f"    --economic-scenario={scenario_id} \\",
            f"    --enable-difficulty \\",
            f"    --enable-reorg-metrics \\",
            f"    --duration={duration} \\",
            f"    --interval=10 \\",
            f"    --results-id=\"{scenario_id}\" \\",
            f"    --snapshot-interval=60 2>&1 | tee \"$RESULTS_DIR/{scenario_id}.log\"",
            f"  ",
            f"  # Extract results",
            f"  warnet logs | python $SWEEP_DIR/../tools/extract_results.py \\",
            f"    --output-dir \"$RESULTS_DIR\" 2>/dev/null || echo \"Results extraction pending\"",
            f"else",
            f"  echo \"  Skipping (already completed)\"",
            f"fi",
            "",
        ])

    lines.extend([
        "END_TIME=$(date +%s)",
        "ELAPSED=$((END_TIME - START_TIME))",
        "echo \"\"",
        "echo \"Parameter sweep complete!\"",
        "echo \"Total time: $((ELAPSED / 3600))h $((ELAPSED % 3600 / 60))m $((ELAPSED % 60))s\"",
        "echo \"Results saved to: $RESULTS_DIR\"",
    ])

    return "\n".join(lines)


def create_analysis_script(scenarios: List[Dict], output_dir: Path) -> str:
    """Create Python script to analyze sweep results"""

    return '''#!/usr/bin/env python3
"""
Analyze Parameter Sweep Results

Loads all scenario results and identifies critical thresholds.
"""

import json
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List

RESULTS_DIR = Path(__file__).parent / "results"
PARAMS_FILE = Path(__file__).parent / "parameters.json"


def load_results() -> pd.DataFrame:
    """Load all scenario results into a DataFrame"""

    # Load parameters
    with open(PARAMS_FILE) as f:
        params = {s["scenario_id"]: s for s in json.load(f)}

    rows = []
    for scenario_id, param in params.items():
        results_file = RESULTS_DIR / scenario_id / "results.json"

        if not results_file.exists():
            continue

        with open(results_file) as f:
            results = json.load(f)

        row = dict(param)

        # Extract outcome metrics
        summary = results.get("summary", {})
        row["final_v27_hashrate"] = summary.get("final_hashrate", {}).get("v27", 50)
        row["final_v26_hashrate"] = summary.get("final_hashrate", {}).get("v26", 50)
        row["final_v27_economic"] = summary.get("final_economic", {}).get("v27", 50)
        row["final_v26_economic"] = summary.get("final_economic", {}).get("v26", 50)
        row["v27_blocks"] = summary.get("blocks_mined", {}).get("v27", 0)
        row["v26_blocks"] = summary.get("blocks_mined", {}).get("v26", 0)
        row["total_blocks"] = summary.get("total_blocks", 0)

        # Calculate dominance metrics
        total_hash = row["final_v27_hashrate"] + row["final_v26_hashrate"]
        row["v27_hash_dominance"] = row["final_v27_hashrate"] / total_hash if total_hash > 0 else 0.5

        total_econ = row["final_v27_economic"] + row["final_v26_economic"]
        row["v27_econ_dominance"] = row["final_v27_economic"] / total_econ if total_econ > 0 else 0.5

        # Determine outcome
        if row["v27_hash_dominance"] > 0.7:
            row["outcome"] = "v27_dominant"
        elif row["v27_hash_dominance"] < 0.3:
            row["outcome"] = "v26_dominant"
        else:
            row["outcome"] = "contested"

        # Reorg metrics if available
        reorg = results.get("reorg", {})
        row["total_reorgs"] = reorg.get("network_summary", {}).get("total_reorg_events", 0)
        row["total_orphans"] = reorg.get("network_summary", {}).get("total_blocks_orphaned", 0)

        rows.append(row)

    return pd.DataFrame(rows)


def find_critical_thresholds(df: pd.DataFrame) -> Dict:
    """Identify critical parameter thresholds for fork outcomes"""

    thresholds = {}

    # For each parameter, find values where outcome changes
    param_cols = [
        "v27_economic_pct", "v27_hashrate_pct",
        "pool_ideology_strength", "pool_profitability_threshold", "pool_max_loss_pct",
        "econ_ideology_strength", "user_ideology_strength",
        "transaction_velocity"
    ]

    for param in param_cols:
        # Group by outcome and get parameter statistics
        grouped = df.groupby("outcome")[param].agg(["mean", "std", "min", "max"])
        thresholds[param] = grouped.to_dict()

    return thresholds


def main():
    print("Loading parameter sweep results...")
    df = load_results()

    print(f"Loaded {len(df)} completed scenarios")
    print()

    # Outcome distribution
    print("=== Outcome Distribution ===")
    print(df["outcome"].value_counts())
    print()

    # Find critical thresholds
    print("=== Critical Thresholds ===")
    thresholds = find_critical_thresholds(df)

    for param, stats in thresholds.items():
        print(f"\\n{param}:")
        for outcome in ["v27_dominant", "contested", "v26_dominant"]:
            if outcome in stats.get("mean", {}):
                mean = stats["mean"][outcome]
                std = stats["std"][outcome]
                print(f"  {outcome}: {mean:.3f} (+/- {std:.3f})")

    # Save analysis
    df.to_csv(RESULTS_DIR / "sweep_analysis.csv", index=False)
    print(f"\\nSaved analysis to {RESULTS_DIR / 'sweep_analysis.csv'}")

    with open(RESULTS_DIR / "thresholds.json", "w") as f:
        json.dump(thresholds, f, indent=2)
    print(f"Saved thresholds to {RESULTS_DIR / 'thresholds.json'}")


if __name__ == "__main__":
    main()
'''


def main():
    parser = argparse.ArgumentParser(
        description="Generate Latin Hypercube Sampling parameter sweep",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--samples", "-n", type=int, default=200,
                        help="Number of scenarios to generate (default: 200)")
    parser.add_argument("--seed", "-s", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output-dir", "-o", type=str, default="../sweep",
                        help="Output directory (default: ../sweep)")
    parser.add_argument("--duration", "-d", type=int, default=1800,
                        help="Scenario duration in seconds (default: 1800)")
    parser.add_argument("--preview", action="store_true",
                        help="Preview parameters without generating files")

    args = parser.parse_args()

    print(f"Generating {args.samples} LHS scenarios (seed={args.seed})...")
    scenarios = generate_samples(args.samples, args.seed)

    if args.preview:
        print("\n=== Parameter Space Coverage ===")
        import pandas as pd
        df = pd.DataFrame(scenarios)
        print(df.describe())
        print("\n=== Sample Scenarios ===")
        for s in scenarios[:5]:
            print(json.dumps(s, indent=2))
        return

    # Create output directories
    output_dir = Path(args.output_dir)
    networks_dir = output_dir / "networks"
    configs_dir = output_dir / "configs"

    for d in [output_dir, networks_dir, configs_dir,
              configs_dir / "pools", configs_dir / "economic"]:
        d.mkdir(parents=True, exist_ok=True)

    # Save raw parameters
    with open(output_dir / "parameters.json", "w") as f:
        json.dump(scenarios, f, indent=2)
    print(f"Saved parameters to {output_dir / 'parameters.json'}")

    # Generate configs for each scenario
    print(f"\nGenerating configs...")

    # Combined pool and economic configs
    all_pool_scenarios = {}
    all_econ_scenarios = {}

    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]

        # Pool scenario
        pool_config = create_pool_scenario_config(scenario)
        all_pool_scenarios[scenario_id] = pool_config

        # Economic scenario
        econ_config = create_economic_scenario_config(scenario)
        all_econ_scenarios[scenario_id] = econ_config

        # Network config (individual files for network generator)
        network_config = create_network_config(scenario)
        network_file = configs_dir / f"{scenario_id}_network.yaml"
        with open(network_file, "w") as f:
            yaml.dump(network_config, f, default_flow_style=False, sort_keys=False)

    # Save combined pool scenarios
    pool_config_file = configs_dir / "pools" / "sweep_pools.yaml"
    with open(pool_config_file, "w") as f:
        yaml.dump(all_pool_scenarios, f, default_flow_style=False, sort_keys=False)
    print(f"Saved pool configs to {pool_config_file}")

    # Save combined economic scenarios
    econ_config_file = configs_dir / "economic" / "sweep_economic.yaml"
    with open(econ_config_file, "w") as f:
        yaml.dump(all_econ_scenarios, f, default_flow_style=False, sort_keys=False)
    print(f"Saved economic configs to {econ_config_file}")

    # Create run script
    run_script = create_run_script(scenarios, output_dir, args.duration)
    run_script_file = output_dir / "run_sweep.sh"
    with open(run_script_file, "w") as f:
        f.write(run_script)
    os.chmod(run_script_file, 0o755)
    print(f"Saved run script to {run_script_file}")

    # Create analysis script
    analysis_script = create_analysis_script(scenarios, output_dir)
    analysis_file = output_dir / "analyze_results.py"
    with open(analysis_file, "w") as f:
        f.write(analysis_script)
    os.chmod(analysis_file, 0o755)
    print(f"Saved analysis script to {analysis_file}")

    # Create network generation script
    gen_networks_script = f"""#!/bin/bash
# Generate all sweep networks

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATOR="$SCRIPT_DIR/../networkGen/scenario_network_generator.py"

echo "Generating {args.samples} networks..."

for config in $SCRIPT_DIR/configs/sweep_*_network.yaml; do
    scenario_id=$(basename "$config" _network.yaml)
    echo "  Generating $scenario_id..."
    python3 "$GENERATOR" --config "$config" -o "$SCRIPT_DIR/networks/$scenario_id/network.yaml"
done

echo "Done! Generated {args.samples} networks in $SCRIPT_DIR/networks/"
"""

    gen_script_file = output_dir / "generate_networks.sh"
    with open(gen_script_file, "w") as f:
        f.write(gen_networks_script)
    os.chmod(gen_script_file, 0o755)
    print(f"Saved network generation script to {gen_script_file}")

    print(f"\n{'='*60}")
    print(f"Parameter sweep setup complete!")
    print(f"{'='*60}")
    print(f"\nGenerated {args.samples} scenarios in {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. Generate networks:    cd {output_dir} && ./generate_networks.sh")
    print(f"  2. Run sweep:            ./run_sweep.sh")
    print(f"  3. Analyze results:      python analyze_results.py")
    print(f"\nEstimated runtime: {args.samples * args.duration / 3600:.1f} hours")
    print(f"  ({args.samples} scenarios x {args.duration/60:.0f} min each)")


if __name__ == "__main__":
    main()
