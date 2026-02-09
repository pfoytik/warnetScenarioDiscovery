#!/usr/bin/env python3

"""
Test: Verify pool-to-node mapping from network.yaml

This test reads a network.yaml file and validates that:
1. Node metadata can be extracted correctly
2. Pool IDs are properly parsed (pool-antpool -> antpool)
3. Nodes are correctly associated with their pools
"""

import yaml
from pathlib import Path


def test_yaml_pool_mapping():
    """Test reading pool assignments from network.yaml"""

    # Example network file
    network_yaml = Path("/home/pfoytik/bitcoinTools/warnet/test-networks/economic-vs-miners/network.yaml")

    if not network_yaml.exists():
        print(f"❌ Network YAML not found: {network_yaml}")
        return

    print("="*70)
    print("TESTING: Pool-to-Node Mapping from network.yaml")
    print("="*70)
    print(f"Reading: {network_yaml}\n")

    # Load YAML
    with open(network_yaml, 'r') as f:
        network_config = yaml.safe_load(f)

    # Build node metadata mapping
    node_metadata = {}
    for node_config in network_config.get('nodes', []):
        node_name = node_config.get('name')
        metadata = node_config.get('metadata', {})

        if node_name:
            node_metadata[node_name] = metadata

    print(f"✓ Loaded metadata for {len(node_metadata)} nodes\n")

    # Extract pool assignments
    pool_nodes = {}  # pool_id -> list of node names
    economic_nodes = []
    user_nodes = []
    unmapped_nodes = []

    for node_name, metadata in node_metadata.items():
        entity_id = metadata.get('entity_id', None)
        role = metadata.get('role', 'unknown')

        if entity_id and entity_id.startswith('pool-'):
            # Mining pool node
            pool_id = entity_id.replace('pool-', '')
            if pool_id not in pool_nodes:
                pool_nodes[pool_id] = []
            pool_nodes[pool_id].append(node_name)
        elif 'exchange' in role:
            economic_nodes.append(node_name)
        elif 'user' in role:
            user_nodes.append(node_name)
        else:
            unmapped_nodes.append(node_name)

    # Display results
    print("="*70)
    print("POOL DISTRIBUTION")
    print("="*70)

    for pool_id, nodes in sorted(pool_nodes.items()):
        print(f"\n{pool_id}:")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Sample: {', '.join(nodes[:5])}")
        if len(nodes) > 5:
            print(f"  ... and {len(nodes) - 5} more")

        # Show version distribution
        versions = {}
        for node_name in nodes:
            node_config = next(n for n in network_config['nodes'] if n['name'] == node_name)
            version = node_config.get('image', {}).get('tag', 'unknown')
            versions[version] = versions.get(version, 0) + 1

        version_str = ", ".join(f"{v}: {count}" for v, count in sorted(versions.items()))
        print(f"  Versions: {version_str}")

    print("\n" + "="*70)
    print("OTHER NODES")
    print("="*70)
    print(f"\nEconomic nodes (exchanges): {len(economic_nodes)}")
    if economic_nodes:
        print(f"  {', '.join(economic_nodes[:5])}")

    print(f"\nUser nodes: {len(user_nodes)}")
    if user_nodes:
        print(f"  {', '.join(user_nodes[:5])}")

    if unmapped_nodes:
        print(f"\n⚠️  Unmapped nodes: {len(unmapped_nodes)}")
        print(f"  {', '.join(unmapped_nodes[:5])}")

    print("\n" + "="*70)
    print("POOL ID ALIGNMENT CHECK")
    print("="*70)

    # Check if pool IDs match expected values from mining_pools_config.yaml
    expected_pools = ['foundry', 'antpool', 'f2pool', 'viabtc', 'braiins', 'binance']

    print("\nExpected pools (from mining_pools_config.yaml):")
    print(f"  {', '.join(expected_pools)}")

    print("\nActual pools (from network.yaml):")
    print(f"  {', '.join(sorted(pool_nodes.keys()))}")

    # Check alignment
    missing_pools = set(expected_pools) - set(pool_nodes.keys())
    extra_pools = set(pool_nodes.keys()) - set(expected_pools)

    if missing_pools:
        print(f"\n⚠️  Pools in config but not in network: {missing_pools}")

    if extra_pools:
        print(f"\n⚠️  Pools in network but not in config: {extra_pools}")

    if not missing_pools and not extra_pools:
        print("\n✓ Pool IDs are aligned!")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total nodes: {len(node_metadata)}")
    print(f"Mining pool nodes: {sum(len(nodes) for nodes in pool_nodes.values())}")
    print(f"Economic nodes: {len(economic_nodes)}")
    print(f"User nodes: {len(user_nodes)}")
    print(f"Unmapped nodes: {len(unmapped_nodes)}")
    print(f"\nUnique pools found: {len(pool_nodes)}")
    print("="*70)


if __name__ == "__main__":
    test_yaml_pool_mapping()
