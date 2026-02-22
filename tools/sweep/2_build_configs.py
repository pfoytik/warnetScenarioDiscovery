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
import copy
import json
import os
import shutil
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


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
    """Create mining pool scenario config from parameters.

    Two independent axes are assigned per pool:
    - fork_preference / ideology: which fork the pool *wants* to mine long-term,
      controlled by pool_v27_preference_pct and pool_neutral_pct.
    - initial_fork: which fork the pool *starts* mining on, controlled by
      v27_hashrate_pct. This decouples "where you are" from "where you want to be",
      allowing scenarios where pools start on the incumbent chain but prefer the new one.
    """

    # --- Ideology / preference assignment (pool_v27_preference_pct, pool_neutral_pct) ---
    v27_pct = scenario["pool_v27_preference_pct"] / 100
    neutral_pct = scenario["pool_neutral_pct"] / 100
    v26_pct = max(0, 1 - v27_pct - neutral_pct)

    # Normalize to 100%
    total = v27_pct + v26_pct + neutral_pct
    v27_pct /= total
    v26_pct /= total
    neutral_pct /= total

    # --- Initial fork assignment (v27_hashrate_pct) ---
    # Pools are sorted by cumulative real-world hashrate. The top v27_hashrate_pct%
    # start on v27, the rest start on v26. This is independent of their ideology.
    v27_init_threshold = scenario["v27_hashrate_pct"] / 100

    pool_configs = []
    cumulative_hashrate = 0

    for pool_id, pool_name, hashrate in DEFAULT_POOLS:
        midpoint = (cumulative_hashrate + hashrate / 2) / 100

        # Ideology assignment
        if midpoint < v27_pct:
            pref = "v27"
        elif midpoint < v27_pct + v26_pct:
            pref = "v26"
        else:
            pref = "neutral"

        # Initial fork assignment (independent of ideology)
        initial_fork = "v27" if midpoint < v27_init_threshold else "v26"

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
            "initial_fork": initial_fork,
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


def load_base_network(network_path: Path) -> Dict:
    """Load a base network template"""
    with open(network_path) as f:
        return yaml.safe_load(f)


def apply_scenario_to_base_network(base_network: Dict, scenario: Dict) -> Dict:
    """
    Apply scenario parameters to a base network template.

    This modifies node metadata based on scenario parameters while preserving
    the network structure (nodes, connections, etc.).
    """
    network = copy.deepcopy(base_network)
    nodes = network.get('nodes', [])

    # Extract parameters with defaults for backward compatibility
    pool_ideology = scenario.get('pool_ideology_strength', 0.5)
    pool_max_loss = scenario.get('pool_max_loss_pct', 0.25)
    pool_prof_threshold = scenario.get('pool_profitability_threshold', 0.1)

    econ_ideology = scenario.get('econ_ideology_strength', 0.2)
    econ_switching = scenario.get('econ_switching_threshold', 0.1)
    econ_inertia = scenario.get('econ_inertia', 0.15)

    user_ideology = scenario.get('user_ideology_strength', 0.5)
    user_switching = scenario.get('user_switching_threshold', 0.1)

    solo_hashrate_mult = scenario.get('solo_miner_hashrate', 0.05)
    transaction_velocity = scenario.get('transaction_velocity', 0.5)

    # Calculate target distributions
    v27_hash_target = scenario.get('v27_hashrate_pct', 50)
    v27_econ_target = scenario.get('v27_economic_pct', 50)

    # --- Assign economic node image tags based on v27_economic_pct ---
    # Sort economic nodes by custody descending, assign the top ones to v27
    # until cumulative custody reaches v27_econ_target % of total.
    econ_roles = {'major_exchange', 'exchange', 'institutional', 'payment_processor', 'merchant'}
    econ_nodes = [n for n in nodes if n.get('metadata', {}).get('role') in econ_roles]
    total_econ_custody = sum(n['metadata'].get('custody_btc', 0) for n in econ_nodes)

    if total_econ_custody > 0:
        econ_nodes_sorted = sorted(
            econ_nodes,
            key=lambda n: n['metadata'].get('custody_btc', 0),
            reverse=True
        )
        v27_custody_acc = 0
        v27_custody_target = total_econ_custody * (v27_econ_target / 100)
        for econ_node in econ_nodes_sorted:
            custody = econ_node['metadata'].get('custody_btc', 0)
            midpoint = v27_custody_acc + custody / 2
            if midpoint < v27_custody_target:
                econ_node['image'] = {'tag': '27.0'}
            else:
                econ_node['image'] = {'tag': '26.0'}
            v27_custody_acc += custody

    # --- Assign pool image tags based on v27_hashrate_pct ---
    # This controls the pool's initial mining fork via node version.
    # Note: pool ideology/preference is controlled separately by the pool
    # config YAML (create_pool_scenario), not by node metadata.
    pool_nodes = [n for n in nodes if n.get('metadata', {}).get('role') == 'mining_pool']
    total_hashrate = sum(n['metadata'].get('hashrate_pct', 0) for n in pool_nodes)
    v27_hashrate_acc = 0

    for node in nodes:
        metadata = node.get('metadata', {})
        role = metadata.get('role', '')

        if role == 'mining_pool':
            hashrate = metadata.get('hashrate_pct', 0)
            midpoint = v27_hashrate_acc + hashrate / 2
            if midpoint < v27_hash_target:
                node['image'] = {'tag': '27.0'}
            else:
                node['image'] = {'tag': '26.0'}
            v27_hashrate_acc += hashrate

            # Apply ideology parameters based on original ideology strength
            original_ideology = metadata.get('ideology_strength', 0.5)
            if original_ideology > 0.7:
                # Committed pools - scale with scenario parameter
                metadata['ideology_strength'] = round(pool_ideology * 1.2, 3)
                metadata['max_loss_pct'] = round(pool_max_loss * 1.5, 3)
            elif original_ideology > 0.4:
                # Moderate pools
                metadata['ideology_strength'] = round(pool_ideology, 3)
                metadata['max_loss_pct'] = round(pool_max_loss, 3)
            else:
                # Rational pools
                metadata['ideology_strength'] = round(pool_ideology * 0.3, 3)
                metadata['max_loss_pct'] = round(pool_max_loss * 0.5, 3)

            metadata['profitability_threshold'] = round(pool_prof_threshold, 3)

        elif role in ['major_exchange', 'exchange']:
            metadata['ideology_strength'] = round(econ_ideology, 3)
            metadata['switching_threshold'] = round(econ_switching, 3)
            metadata['inertia'] = round(econ_inertia, 3)
            metadata['max_loss_pct'] = round(econ_ideology * 0.5, 3)
            if 'transaction_velocity' in metadata:
                metadata['transaction_velocity'] = round(transaction_velocity, 3)

        elif role == 'institutional':
            metadata['ideology_strength'] = round(econ_ideology * 1.2, 3)
            metadata['inertia'] = round(econ_inertia * 2, 3)
            metadata['max_loss_pct'] = round(econ_ideology * 0.4, 3)

        elif role == 'payment_processor':
            metadata['ideology_strength'] = round(user_ideology * 0.8, 3)
            metadata['switching_threshold'] = round(user_switching, 3)
            if 'transaction_velocity' in metadata:
                metadata['transaction_velocity'] = round(transaction_velocity * 1.2, 3)

        elif role == 'merchant':
            metadata['ideology_strength'] = round(user_ideology * 0.6, 3)
            metadata['switching_threshold'] = round(user_switching, 3)

        elif role == 'power_user':
            metadata['ideology_strength'] = round(user_ideology, 3)
            metadata['switching_threshold'] = round(user_switching * 1.5, 3)
            # Scale solo mining hashrate
            if metadata.get('hashrate_pct', 0) > 0:
                metadata['hashrate_pct'] = round(metadata['hashrate_pct'] * (solo_hashrate_mult / 0.05), 4)

        elif role == 'casual_user':
            metadata['ideology_strength'] = round(user_ideology * 0.5, 3)
            metadata['switching_threshold'] = round(user_switching * 0.8, 3)
            if metadata.get('hashrate_pct', 0) > 0:
                metadata['hashrate_pct'] = round(metadata['hashrate_pct'] * (solo_hashrate_mult / 0.05), 4)

        node['metadata'] = metadata

    return network


def generate_from_base_network(
    base_network: Dict,
    scenario: Dict,
    output_dir: Path,
    node_defaults_path: Optional[Path] = None
) -> bool:
    """Generate a network by applying scenario to base network template"""
    try:
        # Apply scenario parameters to base network
        network = apply_scenario_to_base_network(base_network, scenario)

        # Create output directory
        scenario_id = scenario['scenario_id']
        network_dir = output_dir / scenario_id
        network_dir.mkdir(parents=True, exist_ok=True)

        # Write network.yaml
        network_file = network_dir / "network.yaml"
        with open(network_file, "w") as f:
            yaml.dump(network, f, default_flow_style=False, sort_keys=False)

        # Copy node-defaults.yaml if provided
        if node_defaults_path and node_defaults_path.exists():
            shutil.copy(node_defaults_path, network_dir / "node-defaults.yaml")
        else:
            # Create a minimal node-defaults.yaml
            node_defaults = {
                "chain": "regtest",
                "image": {
                    "repository": "bitcoindevproject/bitcoin",
                    "pullPolicy": "IfNotPresent"
                },
                "defaultConfig": "regtest=1\n  server=1\n  txindex=1\n  fallbackfee=0.00001\n  rpcuser=bitcoin\n  rpcpassword=bitcoin\n  rpcallowip=0.0.0.0/0\n  rpcbind=0.0.0.0\n  rpcport=18443\n  zmqpubrawblock=tcp://0.0.0.0:28332\n  zmqpubrawtx=tcp://0.0.0.0:28333\n  debug=rpc",
                "collectLogs": False,
                "metricsExport": False
            }
            with open(network_dir / "node-defaults.yaml", "w") as f:
                yaml.dump(node_defaults, f, default_flow_style=False)

        return True
    except Exception as e:
        print(f"  Error generating network from base: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build network and scenario configs from parameter scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate networks from scratch (default)
    python 2_build_configs.py --input scenarios.json

    # Use realistic-economy as base template
    python 2_build_configs.py --input scenarios.json \\
        --base-network ../../networks/realistic-economy/network.yaml

    # Use custom network as base
    python 2_build_configs.py --input scenarios.json \\
        --base-network path/to/my-network/network.yaml
        """
    )
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Input scenarios.json file from step 1")
    parser.add_argument("--output-dir", "-o", type=str, default="./sweep_output",
                        help="Output directory (default: ./sweep_output)")
    parser.add_argument("--configs-only", action="store_true",
                        help="Only generate config files, skip network generation")
    parser.add_argument("--generator", "-g", type=str, default=None,
                        help="Path to scenario_network_generator.py (for from-scratch generation)")
    parser.add_argument("--base-network", "-b", type=str, default=None,
                        help="Path to base network.yaml to use as template (e.g., realistic-economy)")

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

    # Determine network generation mode
    use_base_network = args.base_network is not None
    base_network = None
    node_defaults_path = None

    if use_base_network:
        base_network_path = Path(args.base_network)
        if not base_network_path.exists():
            print(f"Error: Base network not found: {base_network_path}")
            sys.exit(1)

        print(f"Using base network template: {base_network_path}")
        base_network = load_base_network(base_network_path)

        # Look for node-defaults.yaml
        node_defaults_path = base_network_path.parent / "node-defaults.yaml"
        if not node_defaults_path.exists():
            node_defaults_path = base_network_path.parent.parent / "node-defaults.yaml"
        if not node_defaults_path.exists():
            node_defaults_path = None
            print("  Note: No node-defaults.yaml found, will create default")

    else:
        # Find network generator for from-scratch generation
        if args.generator:
            generator_path = Path(args.generator)
        else:
            # Try to find it relative to this script
            script_dir = Path(__file__).parent
            generator_path = script_dir.parent.parent / "networkGen" / "scenario_network_generator.py"

        if not generator_path.exists():
            print(f"Warning: Network generator not found at {generator_path}")
            print("  Network generation will be skipped")
            print("  Tip: Use --base-network to generate from an existing network template")
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
        if use_base_network:
            print(f"\nGenerating networks from base template...")
        else:
            print(f"\nGenerating networks using {generator_path}...")

        for i, scenario in enumerate(scenarios):
            scenario_id = scenario["scenario_id"]
            network_output = networks_dir / scenario_id / "network.yaml"

            # Skip if already exists
            if network_output.exists():
                manifest["generated_networks"] += 1
                continue

            if use_base_network:
                # Generate from base network template
                success = generate_from_base_network(
                    base_network,
                    scenario,
                    networks_dir,
                    node_defaults_path
                )
            else:
                # Generate from scratch using generator
                config_path = network_configs_dir / f"{scenario_id}.yaml"
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
    if use_base_network:
        print(f"  - Base network: {args.base_network}")
    print(f"  - Network configs: {network_configs_dir}")
    print(f"  - Pool scenarios:  {pools_config_path}")
    print(f"  - Economic scenarios: {econ_config_path}")
    if not args.configs_only:
        print(f"  - Networks: {networks_dir}")

    print(f"\nNext step: python 3_run_sweep.py --input {manifest_path}")


if __name__ == "__main__":
    main()
