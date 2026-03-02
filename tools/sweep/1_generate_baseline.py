#!/usr/bin/env python3
"""
Generate Baseline Scenarios - Fixed Center-Point Parameters

Creates scenarios with all parameters set to their midpoint values.
Each scenario gets a unique random seed to vary stochastic outcomes
(miner selection, price fluctuations, switching decisions).

This establishes baseline variance when parameters are held constant,
enabling comparison with exploratory sweeps.

Usage:
    # Generate 30 baseline scenarios
    python 1_generate_baseline.py --samples 30

    # Specify starting seed
    python 1_generate_baseline.py --samples 30 --seed-start 1000

    # Preview without saving
    python 1_generate_baseline.py --samples 30 --preview
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any


# Parameter center points (midpoint of each range)
CENTER_POINTS = {
    # Initial conditions
    "economic_split": 0.5,        # (0.0 + 1.0) / 2
    "hashrate_split": 0.5,        # (0.0 + 1.0) / 2

    # Pool behavior
    "pool_ideology_strength": 0.5,        # (0.1 + 0.9) / 2
    "pool_profitability_threshold": 0.16, # (0.02 + 0.30) / 2
    "pool_max_loss_pct": 0.26,            # (0.02 + 0.50) / 2
    "pool_committed_split": 0.5,          # (0.0 + 1.0) / 2
    "pool_neutral_pct": 30.0,             # (10 + 50) / 2

    # Economic node behavior
    "econ_ideology_strength": 0.4,        # (0.0 + 0.8) / 2
    "econ_switching_threshold": 0.135,    # (0.02 + 0.25) / 2
    "econ_inertia": 0.175,                # (0.05 + 0.30) / 2

    # User behavior
    "user_ideology_strength": 0.5,        # (0.1 + 0.9) / 2
    "user_switching_threshold": 0.125,    # (0.05 + 0.20) / 2

    # Fee market
    "transaction_velocity": 0.5,          # (0.1 + 0.9) / 2

    # Network structure
    "user_nodes_per_partition": 6,        # (2 + 10) / 2
    "economic_nodes_per_partition": 2,    # (1 + 3) / 2
    "solo_miner_hashrate": 0.085,         # (0.02 + 0.15) / 2
}

# Parameter metadata (matching 1_generate_scenarios.py)
PARAMETER_METADATA = [
    {"name": "economic_split", "min": 0.0, "max": 1.0, "type": "continuous",
     "description": "Fraction of economic custody starting on v27"},
    {"name": "hashrate_split", "min": 0.0, "max": 1.0, "type": "continuous",
     "description": "Fraction of initial hashrate starting on v27"},
    {"name": "pool_ideology_strength", "min": 0.1, "max": 0.9, "type": "continuous",
     "description": "How much pools sacrifice for ideology"},
    {"name": "pool_profitability_threshold", "min": 0.02, "max": 0.30, "type": "continuous",
     "description": "Min profit advantage for pools to consider switching"},
    {"name": "pool_max_loss_pct", "min": 0.02, "max": 0.50, "type": "continuous",
     "description": "Max revenue loss pools tolerate for ideology"},
    {"name": "pool_committed_split", "min": 0.0, "max": 1.0, "type": "continuous",
     "description": "Fraction of committed pool hashrate preferring v27"},
    {"name": "pool_neutral_pct", "min": 10, "max": 50, "type": "continuous",
     "description": "Percentage of pools that are neutral/rational"},
    {"name": "econ_ideology_strength", "min": 0.0, "max": 0.8, "type": "continuous",
     "description": "How much economic nodes sacrifice for ideology"},
    {"name": "econ_switching_threshold", "min": 0.02, "max": 0.25, "type": "continuous",
     "description": "Min price advantage for economic nodes to switch"},
    {"name": "econ_inertia", "min": 0.05, "max": 0.30, "type": "continuous",
     "description": "Additional switching friction (infrastructure costs)"},
    {"name": "user_ideology_strength", "min": 0.1, "max": 0.9, "type": "continuous",
     "description": "How much users sacrifice for ideology"},
    {"name": "user_switching_threshold", "min": 0.05, "max": 0.20, "type": "continuous",
     "description": "Min price advantage for users to switch"},
    {"name": "transaction_velocity", "min": 0.1, "max": 0.9, "type": "continuous",
     "description": "Rate of fee-generating transactions"},
    {"name": "user_nodes_per_partition", "min": 2, "max": 10, "type": "discrete",
     "description": "Number of user nodes per partition"},
    {"name": "economic_nodes_per_partition", "min": 1, "max": 3, "type": "discrete",
     "description": "Number of economic/exchange nodes per partition"},
    {"name": "solo_miner_hashrate", "min": 0.02, "max": 0.15, "type": "continuous",
     "description": "Hashrate percentage per solo miner"},
]


def generate_baseline_scenarios(n_samples: int, seed_start: int = 1) -> List[Dict[str, Any]]:
    """
    Generate baseline scenarios with fixed center-point parameters.

    Each scenario gets a unique random_seed for stochastic variation.
    """
    scenarios = []

    for i in range(n_samples):
        scenario = {
            "scenario_id": f"baseline_{i:04d}",
            "random_seed": seed_start + i,  # Unique seed for each run
        }

        # Add all center-point parameters
        for param_name, value in CENTER_POINTS.items():
            scenario[param_name] = value

        scenarios.append(scenario)

    return scenarios


def print_summary(scenarios: List[Dict[str, Any]]):
    """Print summary of generated scenarios"""
    print("\n" + "=" * 60)
    print("BASELINE SCENARIO SUMMARY")
    print("=" * 60)

    print(f"\nTotal scenarios: {len(scenarios)}")
    print(f"Random seeds: {scenarios[0]['random_seed']} to {scenarios[-1]['random_seed']}")

    print("\nFixed center-point parameters:")
    for param, value in CENTER_POINTS.items():
        print(f"  {param}: {value}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Generate baseline scenarios with center-point parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--samples", "-n", type=int, default=30,
                        help="Number of baseline scenarios (default: 30)")
    parser.add_argument("--seed-start", type=int, default=1,
                        help="Starting random seed (default: 1)")
    parser.add_argument("--output", "-o", type=str, default="baseline_scenarios.json",
                        help="Output file path (default: baseline_scenarios.json)")
    parser.add_argument("--preview", action="store_true",
                        help="Preview scenarios without saving")

    args = parser.parse_args()

    print(f"Generating {args.samples} baseline scenarios...")
    print(f"Random seeds: {args.seed_start} to {args.seed_start + args.samples - 1}")

    scenarios = generate_baseline_scenarios(args.samples, args.seed_start)

    print_summary(scenarios)

    if args.preview:
        print("\nSample scenario:")
        print(json.dumps(scenarios[0], indent=2))
        return

    # Save scenarios
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "type": "baseline",
            "description": "Fixed center-point parameters with varying random seeds",
            "n_samples": args.samples,
            "seed_start": args.seed_start,
            "n_parameters": len(CENTER_POINTS),
            "center_points": CENTER_POINTS,
            "parameters": PARAMETER_METADATA
        },
        "scenarios": scenarios
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved {len(scenarios)} scenarios to: {output_path}")
    print(f"\nNext step: python 2_build_configs.py --input {output_path} --output-dir baseline_sweep_lite")


if __name__ == "__main__":
    main()
