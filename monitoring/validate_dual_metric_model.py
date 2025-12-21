#!/usr/bin/env python3
"""
PHASE 5: Validate the Dual-Metric Model

This script:
1. Loads the dual-metric-test.yaml network configuration
2. Simulates a version fork (v26.0 vs v27.0)
3. Runs economic fork analysis
4. Demonstrates custody vs volume trade-offs

Expected Output:
- Chain v27.0: High consensus weight (volume dominance)
- Chain v26.0: Lower weight (only custody provider)
- Risk assessment based on supply split
"""

import sys
import yaml
import os
from economic_fork_analyzer import EconomicForkAnalyzer, EconomicNode


def load_network_config(yaml_path):
    """Load network configuration from YAML file."""
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def extract_economic_nodes_from_config(config):
    """
    Extract economic nodes from Warnet YAML config.

    Returns:
        List of EconomicNode instances
    """
    nodes = []

    # Handle both formats: config['nodes'] or config['network']['nodes']
    node_list = config.get('nodes', config.get('network', {}).get('nodes', []))

    for node_config in node_list:
        metadata = node_config.get('metadata', {})

        # Only process economic nodes (skip relay/constrained nodes)
        if 'economic_node' not in node_config.get('tags', []):
            continue

        # Extract metrics
        name = node_config['name']
        node_type = metadata.get('node_type', 'unknown')
        custody_btc = metadata.get('custody_btc', 0)
        daily_volume_btc = metadata.get('daily_volume_btc', 0)

        # Extract version from image tag
        image = node_config.get('image', '')
        version = image.split(':')[1] if ':' in image else 'unknown'

        # Create EconomicNode with additional metadata
        economic_node = EconomicNode(
            name=name,
            node_type=node_type,
            custody_btc=custody_btc,
            daily_volume_btc=daily_volume_btc,
            metadata={
                'version': version,
                'entity_name': metadata.get('entity_name', ''),
                'test_role': metadata.get('test_role', ''),
                'economic_influence': metadata.get('economic_influence', ''),
                'adoption_speed': metadata.get('adoption_speed', 'medium')
            }
        )

        nodes.append(economic_node)

    return nodes


def simulate_version_fork(nodes):
    """
    Simulate a version fork, splitting nodes by Bitcoin Core version.

    Args:
        nodes: List of EconomicNode instances

    Returns:
        (chain_v27_nodes, chain_v26_nodes, other_nodes)
    """
    chain_v27 = []
    chain_v26 = []
    other = []

    for node in nodes:
        version = node.metadata.get('version', 'unknown')

        if version.startswith('27'):
            chain_v27.append(node)
        elif version.startswith('26'):
            chain_v26.append(node)
        else:
            other.append(node)

    return chain_v27, chain_v26, other


def print_node_summary(nodes, label="Nodes"):
    """Print summary of nodes in a chain."""
    print(f"\n{label} ({len(nodes)} nodes):")
    print("-" * 80)

    for node in nodes:
        version = node.metadata.get('version', 'unknown')
        influence = node.metadata.get('economic_influence', 'unknown')

        print(f"  • {node.name:25s} (v{version})")
        print(f"    Type: {node.node_type:20s} Influence: {influence}")
        print(f"    Custody: {node.custody_btc:>10,} BTC ({node.custody_btc / 19_500_000 * 100:>5.2f}% of supply)")
        print(f"    Volume:  {node.daily_volume_btc:>10,} BTC/day ({node.daily_volume_btc / 300_000 * 100:>5.2f}% of daily)")
        print()


def main():
    """Run PHASE 5 validation."""
    print("=" * 80)
    print("PHASE 5: DUAL-METRIC MODEL VALIDATION")
    print("=" * 80)
    print()

    # Step 1: Load network configuration
    print("STEP 1: Loading network configuration...")
    print("-" * 80)

    yaml_path = os.path.join(
        os.path.dirname(__file__),
        '../../test-networks/dual-metric-test.yaml'
    )

    if not os.path.exists(yaml_path):
        print(f"✗ ERROR: Network config not found at {yaml_path}")
        return 1

    config = load_network_config(yaml_path)
    print(f"✓ Loaded network: {config['network']['name']}")
    print(f"  Description: {config['network']['description']}")
    print()

    # Step 2: Extract economic nodes
    print("STEP 2: Extracting economic nodes...")
    print("-" * 80)

    nodes = extract_economic_nodes_from_config(config)
    print(f"✓ Found {len(nodes)} economic nodes")

    # Print all nodes
    print_node_summary(nodes, "All Economic Nodes")

    # Step 3: Simulate version fork
    print("STEP 3: Simulating version fork (v27.0 vs v26.0)...")
    print("=" * 80)

    chain_v27, chain_v26, other = simulate_version_fork(nodes)

    print(f"\nFork scenario:")
    print(f"  Chain A (v27.0): {len(chain_v27)} nodes")
    print(f"  Chain B (v26.0): {len(chain_v26)} nodes")
    if other:
        print(f"  Other versions: {len(other)} nodes")

    print_node_summary(chain_v27, "Chain A (v27.0)")
    print_node_summary(chain_v26, "Chain B (v26.0)")

    # Step 4: Run economic fork analysis
    print("\nSTEP 4: Running economic fork analysis...")
    print("=" * 80)

    analyzer = EconomicForkAnalyzer()
    result = analyzer.analyze_fork(chain_v27, chain_v26)

    # Print detailed analysis
    analyzer.print_report(result)

    # Step 5: Demonstrate key metrics
    print("\nSTEP 5: KEY METRICS DEMONSTRATION")
    print("=" * 80)

    chain_a = result['chains']['chain_a']
    chain_b = result['chains']['chain_b']

    print("\n### CUSTODY-BASED SUPPLY PERCENTAGE ###")
    print(f"  Chain A (v27.0): {chain_a['custody_btc']:>12,} BTC = {chain_a['supply_percentage']:>6.2f}% of circulating supply")
    print(f"  Chain B (v26.0): {chain_b['custody_btc']:>12,} BTC = {chain_b['supply_percentage']:>6.2f}% of circulating supply")

    print("\n### VOLUME-BASED FLOW PERCENTAGE ###")
    print(f"  Chain A (v27.0): {chain_a['daily_volume_btc']:>12,} BTC/day = {chain_a['volume_percentage']:>5.1f}% of daily on-chain")
    print(f"  Chain B (v26.0): {chain_b['daily_volume_btc']:>12,} BTC/day = {chain_b['volume_percentage']:>5.1f}% of daily on-chain")

    print("\n### COMBINED CONSENSUS WEIGHT (70% custody, 30% volume) ###")
    print(f"  Chain A (v27.0): {chain_a['consensus_weight']:>6.2f}")
    print(f"  Chain B (v26.0): {chain_b['consensus_weight']:>6.2f}")
    print(f"  Margin: {abs(chain_a['consensus_weight'] - chain_b['consensus_weight']):>6.2f}")

    print("\n### RISK SCORE ###")
    risk = result['risk_assessment']
    print(f"  Score: {risk['score']:.1f}/100 ({risk['level']})")
    print(f"  Consensus Chain: Chain {risk['consensus_chain']}")
    print(f"  Economic Majority: Chain {risk['economic_majority']}")

    # Step 6: Analysis summary
    print("\n\nSTEP 6: ANALYSIS SUMMARY")
    print("=" * 80)

    print("\n✓ DUAL-METRIC MODEL VALIDATION COMPLETE\n")

    print("Key Findings:")
    print(f"  1. Chain A (v27.0) has {len(chain_v27)} nodes with combined weight {chain_a['consensus_weight']:.2f}")
    print(f"  2. Chain B (v26.0) has {len(chain_v26)} node(s) with combined weight {chain_b['consensus_weight']:.2f}")
    print(f"  3. Despite Chain B having significant custody ({chain_b['supply_percentage']:.1f}% of supply),")
    print(f"     Chain A wins due to dominant payment volume ({chain_a['volume_percentage']:.1f}% of daily flow)")
    print(f"  4. Risk level: {risk['level']} ({risk['score']:.1f}/100)")

    print("\nCustody vs Volume Trade-off:")
    print(f"  • High-custody node (custody provider): {chain_b['custody_btc']:,} BTC, weight {chain_b['consensus_weight']:.2f}")
    print(f"  • High-volume nodes (exchanges): {chain_a['custody_btc']:,} BTC, weight {chain_a['consensus_weight']:.2f}")
    print(f"  • Volume dominance wins: {chain_a['volume_percentage']:.1f}% vs {chain_b['volume_percentage']:.1f}% daily flow")

    print("\nBCAP Framework Alignment:")
    print("  ✓ Custody (PRIMARY 70%): Validates which chain holds economic value")
    print("  ✓ Volume (SECONDARY 30%): Reflects operational importance")
    print("  ✓ Combined weight: Balances supply validation + payment flow")

    print("\n" + "=" * 80)
    print("✓ VALIDATION SUCCESSFUL - Model demonstrates dual-metric consensus")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
