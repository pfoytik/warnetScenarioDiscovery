#!/usr/bin/env python3
"""
Step 2: Build Networks and Configurations

Takes the scenarios.json from step 1 and generates:
- Network YAML configs for each scenario
- Pool scenario configs
- Economic scenario configs
- Generated networks ready for warnet

Usage:
    # Build all configs from scenarios.json
    python 2_build_configs.py --input scenarios.json

    # Specify output directory
    python 2_build_configs.py --input scenarios.json --output-dir ./sweep_output

    # Build only configs (skip network generation)
    python 2_build_configs.py --input scenarios.json --configs-only

Output:
    output_dir/
    ├── networks/
    │   ├── sweep_0000/network.yaml
    │   ├── sweep_0001/network.yaml
    │   └── ...
    ├── configs/
    │   ├── network/
    │   │   ├── sweep_0000.yaml
    │   │   └── ...
    │   ├── pools/
    │   │   └── sweep_pools_config.yaml
    │   └── economic/
    │       └── sweep_economic_config.yaml
    └── build_manifest.json
"""

import argparse
import json
import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any


# Real-world pool distribution
DEFAULT_POOLS = [
    ("foundryusa", "Foundry USA", 26.89),
    ("antpool", "AntPool", 19.25),
    ("viabtc", "ViaBTC", 11.39),
    ("f2pool", "F2Pool", 11.25),
    ("binancepool", "Binance Pool", 10.04),
    ("marapool", "MARA Pool", 8.25),
    ("sbicrypto", "SBI Crypto", 4.57),
    ("luxor", "Luxor", 3.94),
    ("ocean", "OCEAN", 1.42),
    ("braiinspool", "Braiins Pool", 1.37),
]


def create_pool_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create mining pool scenario config from parameters"""

    # Distribute preferences based on parameters
    v27_pct = scenario["pool_v27_preference_pct"] / 100
    neutral_pct = scenario["pool_neutral_pct"] / 100
    v26_pct = max(0, 1 - v27_pct - neutral_pct)

    # Normalize to 100%
    total = v27_pct + v26_pct + neutral_pct
    v27_pct /= total
    v26_pct /= total
    neutral_pct /= total

    pool_configs = []
    cumulative_hashrate = 0

    for pool_id, pool_name, hashrate in DEFAULT_POOLS:
        # Assign preference based on cumulative distribution
        midpoint = (cumulative_hashrate + hashrate / 2) / 100

        if midpoint < v27_pct:
            pref = "v27"
        elif midpoint < v27_pct + v26_pct:
            pref = "v26"
        else:
            pref = "neutral"

        # Neutral pools have minimal ideology
        if pref == "neutral":
            ideology = 0.1
            max_loss = 0.02
        else:
            ideology = scenario["pool_ideology_strength"]
            max_loss = scenario["pool_max_loss_pct"]

        pool_configs.append({
            "pool_id": pool_id,
            "pool_name": pool_name,
            "hashrate_pct": hashrate,
            "fork_preference": pref,
            "ideology_strength": round(ideology, 3),
            "profitability_threshold": scenario["pool_profitability_threshold"],
            "max_loss_pct": round(max_loss, 3),
        })

        cumulative_hashrate += hashrate

    return {
        "description": f"Pool scenario for {scenario['scenario_id']}",
        "pools": pool_configs
    }


def create_economic_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create economic scenario config from parameters"""
    return {
        "description": f"Economic scenario for {scenario['scenario_id']}",
        "economic_defaults": {
            "fork_preference": "neutral",
            "ideology_strength": scenario["econ_ideology_strength"],
            "switching_threshold": scenario["econ_switching_threshold"],
            "inertia": scenario["econ_inertia"],
            "switching_cooldown": 1800,
            "max_loss_pct": round(min(0.30, scenario["econ_ideology_strength"] * 0.5), 3),
        },
        "user_defaults": {
            "fork_preference": "neutral",
            "ideology_strength": scenario["user_ideology_strength"],
            "switching_threshold": scenario["user_switching_threshold"],
            "inertia": 0.05,
            "switching_cooldown": 3600,
            "max_loss_pct": round(min(0.40, scenario["user_ideology_strength"] * 0.6), 3),
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


def generate_network(config_path: Path, output_path: Path, generator_path: Path) -> bool:
    """Run the network generator for a single config"""
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(generator_path),
                "--config", str(config_path),
                "-o", str(output_path)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  Error generating network: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build network and scenario configs from parameter scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Input scenarios.json file from step 1")
    parser.add_argument("--output-dir", "-o", type=str, default="./sweep_output",
                        help="Output directory (default: ./sweep_output)")
    parser.add_argument("--configs-only", action="store_true",
                        help="Only generate config files, skip network generation")
    parser.add_argument("--generator", "-g", type=str, default=None,
                        help="Path to scenario_network_generator.py")

    args = parser.parse_args()

    # Load scenarios
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path) as f:
        data = json.load(f)

    scenarios = data["scenarios"]
    metadata = data.get("metadata", {})

    print(f"Loaded {len(scenarios)} scenarios from {input_path}")

    # Setup output directories
    output_dir = Path(args.output_dir)
    networks_dir = output_dir / "networks"
    configs_dir = output_dir / "configs"
    network_configs_dir = configs_dir / "network"
    pools_dir = configs_dir / "pools"
    economic_dir = configs_dir / "economic"

    for d in [output_dir, networks_dir, configs_dir, network_configs_dir, pools_dir, economic_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Find network generator
    if args.generator:
        generator_path = Path(args.generator)
    else:
        # Try to find it relative to this script
        script_dir = Path(__file__).parent
        generator_path = script_dir.parent.parent / "networkGen" / "scenario_network_generator.py"

    if not generator_path.exists():
        print(f"Warning: Network generator not found at {generator_path}")
        print("  Network generation will be skipped")
        args.configs_only = True

    # Generate configs
    print(f"\nGenerating configs...")

    all_pool_scenarios = {}
    all_economic_scenarios = {}
    manifest = {
        "metadata": metadata,
        "scenarios": [],
        "generated_networks": 0,
        "failed_networks": 0,
    }

    for i, scenario in enumerate(scenarios):
        scenario_id = scenario["scenario_id"]

        # Create individual network config
        network_config = create_network_config(scenario)
        network_config_path = network_configs_dir / f"{scenario_id}.yaml"
        with open(network_config_path, "w") as f:
            yaml.dump(network_config, f, default_flow_style=False, sort_keys=False)

        # Create pool scenario
        pool_config = create_pool_scenario(scenario)
        all_pool_scenarios[scenario_id] = pool_config

        # Create economic scenario
        econ_config = create_economic_scenario(scenario)
        all_economic_scenarios[scenario_id] = econ_config

        # Track in manifest
        manifest["scenarios"].append({
            "scenario_id": scenario_id,
            "parameters": scenario,
            "network_config": str(network_config_path),
            "network_path": str(networks_dir / scenario_id / "network.yaml"),
        })

        if (i + 1) % 50 == 0:
            print(f"  Generated configs for {i + 1}/{len(scenarios)} scenarios")

    # Save combined pool scenarios
    pools_config_path = pools_dir / "sweep_pools_config.yaml"
    with open(pools_config_path, "w") as f:
        yaml.dump(all_pool_scenarios, f, default_flow_style=False, sort_keys=False)
    print(f"Saved pool configs to {pools_config_path}")

    # Save combined economic scenarios
    econ_config_path = economic_dir / "sweep_economic_config.yaml"
    with open(econ_config_path, "w") as f:
        yaml.dump(all_economic_scenarios, f, default_flow_style=False, sort_keys=False)
    print(f"Saved economic configs to {econ_config_path}")

    # Generate networks
    if not args.configs_only:
        print(f"\nGenerating networks using {generator_path}...")

        for i, scenario in enumerate(scenarios):
            scenario_id = scenario["scenario_id"]
            config_path = network_configs_dir / f"{scenario_id}.yaml"
            network_output = networks_dir / scenario_id / "network.yaml"

            # Skip if already exists
            if network_output.exists():
                manifest["generated_networks"] += 1
                continue

            success = generate_network(config_path, network_output, generator_path)

            if success:
                manifest["generated_networks"] += 1
            else:
                manifest["failed_networks"] += 1
                print(f"  Failed: {scenario_id}")

            if (i + 1) % 20 == 0:
                print(f"  Generated {i + 1}/{len(scenarios)} networks")

        print(f"\nNetworks: {manifest['generated_networks']} generated, {manifest['failed_networks']} failed")

    # Save manifest
    manifest_path = output_dir / "build_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nSaved build manifest to {manifest_path}")

    print(f"\n{'='*60}")
    print("Build complete!")
    print(f"{'='*60}")
    print(f"\nOutput directory: {output_dir}")
    print(f"  - Network configs: {network_configs_dir}")
    print(f"  - Pool scenarios:  {pools_config_path}")
    print(f"  - Economic scenarios: {econ_config_path}")
    if not args.configs_only:
        print(f"  - Networks: {networks_dir}")

    print(f"\nNext step: python 3_run_sweep.py --input {manifest_path}")


if __name__ == "__main__":
    main()
