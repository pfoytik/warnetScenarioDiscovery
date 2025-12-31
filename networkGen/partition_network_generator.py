#!/usr/bin/env python3
"""
Partition-Based Network Generator for Systematic Fork Testing

Generates version-segregated networks for testing economic weight vs hashrate conflicts.
Each network has two isolated partitions (v27 and v22) with configurable economic/hashrate distribution.

Usage:
    python3 partition_network_generator.py --test-id 5.3 --v27-economic 70 --v27-hashrate 30
"""

import yaml
import argparse
import sys
from typing import Dict, List, Tuple


# Real-world pool distribution (validated with R²≈0.98)
POOL_DISTRIBUTION = [
    ("Foundry USA", 26.89),
    ("AntPool", 19.25),
    ("ViaBTC", 11.39),
    ("F2Pool", 11.25),
    ("Binance Pool", 10.04),
    ("MARA Pool", 8.25),
    ("SBI Crypto", 4.57),
    ("Luxor", 3.94),
    ("OCEAN", 1.42),
    ("Braiins Pool", 1.37),
]

# Network totals (realistic values)
TOTAL_CUSTODY_BTC = 4_000_000  # 4M BTC total custody
TOTAL_VOLUME_BTC_DAY = 420_000  # 420K BTC/day total volume


class PartitionNetworkGenerator:
    """Generate version-segregated networks for systematic testing"""

    def __init__(self, test_id: str, v27_economic_pct: float, v27_hashrate_pct: float):
        """
        Initialize generator for specific test configuration.

        Args:
            test_id: Test identifier (e.g., "5.3")
            v27_economic_pct: Percentage of economic weight on v27 (0-100)
            v27_hashrate_pct: Percentage of hashrate on v27 (0-100)
        """
        self.test_id = test_id
        self.v27_economic_pct = v27_economic_pct / 100.0
        self.v27_hashrate_pct = v27_hashrate_pct / 100.0

        # Calculate v22 percentages
        self.v22_economic_pct = 1.0 - self.v27_economic_pct
        self.v22_hashrate_pct = 1.0 - self.v27_hashrate_pct

        # Node allocation (total 20 nodes)
        self.v27_node_count = 10
        self.v22_node_count = 10

        # Partition configuration
        self.v27_partition = None
        self.v22_partition = None

    def distribute_pools(self) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """
        Distribute pools between partitions to match target hashrate percentages.

        Returns:
            (v27_pools, v22_pools) where each is list of (name, hashrate) tuples
        """
        target_v27 = self.v27_hashrate_pct * 100
        target_v22 = self.v22_hashrate_pct * 100

        v27_pools = []
        v22_pools = []
        v27_total = 0.0
        v22_total = 0.0

        # Greedy assignment: assign pools to v27 until we reach target
        for pool_name, hashrate in POOL_DISTRIBUTION:
            if v27_total < target_v27 and abs(v27_total + hashrate - target_v27) < abs(v27_total - target_v27):
                v27_pools.append((pool_name, hashrate))
                v27_total += hashrate
            else:
                v22_pools.append((pool_name, hashrate))
                v22_total += hashrate

        print(f"  Pool distribution:")
        print(f"    v27: {v27_total:.2f}% (target: {target_v27:.0f}%)")
        print(f"    v22: {v22_total:.2f}% (target: {target_v22:.0f}%)")

        return v27_pools, v22_pools

    def distribute_economic_weight(self, num_econ_nodes: int, target_weight_pct: float) -> List[Dict]:
        """
        Distribute economic metadata across nodes to match target weight percentage.

        Uses power-law distribution: first node gets most, subsequent nodes get less.

        Args:
            num_econ_nodes: Number of economic nodes in partition
            target_weight_pct: Target economic weight (0.0-1.0)

        Returns:
            List of {custody_btc, daily_volume_btc} dicts
        """
        if num_econ_nodes == 0:
            return []

        target_custody = TOTAL_CUSTODY_BTC * target_weight_pct
        target_volume = TOTAL_VOLUME_BTC_DAY * target_weight_pct

        # Power-law distribution weights (first node gets most)
        # Using harmonic series: 1, 1/2, 1/3, 1/4, ...
        weights = [1.0 / (i + 1) for i in range(num_econ_nodes)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        nodes = []
        for i, weight in enumerate(normalized_weights):
            node_custody = int(target_custody * weight)
            node_volume = int(target_volume * weight)

            nodes.append({
                'custody_btc': node_custody,
                'daily_volume_btc': node_volume,
                'role': 'major_exchange' if i == 0 else ('exchange' if i < 2 else 'payment_processor')
            })

        return nodes

    def create_partition_config(self, version: str, economic_pct: float, pools: List[Tuple[str, float]],
                                node_start_idx: int, partition_size: int) -> Dict:
        """
        Create configuration for one partition.

        Args:
            version: Bitcoin Core version (e.g., "27.0")
            economic_pct: Economic weight percentage (0.0-1.0)
            pools: List of (pool_name, hashrate) for this partition
            node_start_idx: Starting node index
            partition_size: Total nodes in partition

        Returns:
            Partition configuration dict
        """
        # Allocate nodes
        num_pools = len(pools)
        num_economic = min(3, partition_size - num_pools - 2)  # At least 3 economic or max available
        num_network = partition_size - num_economic - num_pools

        # Distribute economic weight
        economic_nodes = self.distribute_economic_weight(num_economic, economic_pct)

        # Build partition
        partition = {
            'version': version,
            'nodes': [],
            'pools': pools,
            'start_index': node_start_idx,
            'end_index': node_start_idx + partition_size - 1,
        }

        current_idx = node_start_idx

        # Add economic nodes
        for econ_config in economic_nodes:
            partition['nodes'].append({
                'index': current_idx,
                'type': 'economic',
                'version': version,
                **econ_config
            })
            current_idx += 1

        # Add pool nodes
        for pool_name, hashrate in pools:
            partition['nodes'].append({
                'index': current_idx,
                'type': 'pool',
                'version': version,
                'pool_name': pool_name,
                'hashrate_percent': hashrate
            })
            current_idx += 1

        # Add network nodes
        for _ in range(num_network):
            partition['nodes'].append({
                'index': current_idx,
                'type': 'network',
                'version': version
            })
            current_idx += 1

        return partition

    def generate_edges(self, v27_partition: Dict, v22_partition: Dict) -> List[List[int]]:
        """
        Generate network topology with version segregation.

        NO edges between v27 and v22 partitions!

        Args:
            v27_partition: v27 partition configuration
            v22_partition: v22 partition configuration

        Returns:
            List of edges (node pairs)
        """
        edges = []

        # Generate edges within each partition
        for partition in [v27_partition, v22_partition]:
            partition_nodes = [n['index'] for n in partition['nodes']]
            economic_nodes = [n['index'] for n in partition['nodes'] if n['type'] == 'economic']
            pool_nodes = [n['index'] for n in partition['nodes'] if n['type'] == 'pool']
            network_nodes = [n['index'] for n in partition['nodes'] if n['type'] == 'network']

            # 1. Full mesh among economic nodes
            for i in range(len(economic_nodes)):
                for j in range(i + 1, len(economic_nodes)):
                    edges.append([economic_nodes[i], economic_nodes[j]])

            # 2. Pools connect to all economic nodes in partition
            for pool_idx in pool_nodes:
                for econ_idx in economic_nodes:
                    if [pool_idx, econ_idx] not in edges and [econ_idx, pool_idx] not in edges:
                        edges.append([pool_idx, econ_idx])

            # 3. Pools connect to adjacent pools
            for i in range(len(pool_nodes) - 1):
                edges.append([pool_nodes[i], pool_nodes[i + 1]])

            # 4. Network nodes form ring
            for i in range(len(network_nodes)):
                next_idx = (i + 1) % len(network_nodes)
                if [network_nodes[i], network_nodes[next_idx]] not in edges:
                    edges.append([network_nodes[i], network_nodes[next_idx]])

            # 5. Connect some network nodes to economic nodes
            for i, net_idx in enumerate(network_nodes):
                if i % 2 == 0 and economic_nodes:  # Every other network node
                    econ_idx = economic_nodes[i % len(economic_nodes)]
                    if [net_idx, econ_idx] not in edges and [econ_idx, net_idx] not in edges:
                        edges.append([net_idx, econ_idx])

        return edges

    def generate_network_yaml(self) -> Dict:
        """
        Generate complete network configuration.

        Returns:
            Network YAML dict
        """
        print(f"\nGenerating network for Test {self.test_id}")
        print(f"  v27: {self.v27_economic_pct*100:.0f}% economic, {self.v27_hashrate_pct*100:.0f}% hashrate")
        print(f"  v22: {self.v22_economic_pct*100:.0f}% economic, {self.v22_hashrate_pct*100:.0f}% hashrate")

        # Distribute pools
        v27_pools, v22_pools = self.distribute_pools()

        # Create partitions
        v27_partition = self.create_partition_config(
            version="27.0",
            economic_pct=self.v27_economic_pct,
            pools=v27_pools,
            node_start_idx=0,
            partition_size=self.v27_node_count
        )

        v22_partition = self.create_partition_config(
            version="26.0",
            economic_pct=self.v22_economic_pct,
            pools=v22_pools,
            node_start_idx=self.v27_node_count,
            partition_size=self.v22_node_count
        )

        # Generate topology
        edges = self.generate_edges(v27_partition, v22_partition)

        # Build network config
        all_nodes = v27_partition['nodes'] + v22_partition['nodes']

        # Convert edges to adjacency list for addnode directives
        adjacency = {i: [] for i in range(len(all_nodes))}
        for edge in edges:
            adjacency[edge[0]].append(edge[1])
            adjacency[edge[1]].append(edge[0])

        # Convert to Warnet format
        warnet_nodes = []
        for node in all_nodes:
            node_idx = node['index']
            node_name = f"node-{node_idx:04d}"

            warnet_node = {
                'name': node_name,
                'image': {
                    'tag': node['version']
                }
            }

            # Add addnode list (edges)
            if adjacency[node_idx]:
                warnet_node['addnode'] = [f"node-{n:04d}" for n in sorted(adjacency[node_idx])]

            # Add bitcoin_config based on node type
            if node['type'] == 'economic':
                warnet_node['bitcoin_config'] = {
                    'maxconnections': 125,
                    'maxmempool': 300,
                    'txindex': 1
                }
                warnet_node['metadata'] = {
                    'role': node['role'],
                    'custody_btc': node['custody_btc'],
                    'daily_volume_btc': node['daily_volume_btc'],
                    'consensus_weight': round((0.7 * node['custody_btc'] + 0.3 * node['daily_volume_btc']) / 10000, 2)
                }

            elif node['type'] == 'pool':
                warnet_node['bitcoin_config'] = {
                    'maxconnections': 50,
                    'maxmempool': 200,
                    'txindex': 1
                }
                warnet_node['metadata'] = {
                    'pool_name': node['pool_name'],
                    'hashrate_percent': node['hashrate_percent']
                }

            else:  # network node
                warnet_node['bitcoin_config'] = {
                    'maxconnections': 30,
                    'maxmempool': 100,
                    'txindex': 1
                }

            warnet_nodes.append(warnet_node)

        network = {
            'caddy': {
                'enabled': True
            },
            'fork_observer': {
                'enabled': True,
                'configQueryInterval': 10
            },
            'nodes': warnet_nodes
        }

        # Print summary
        print(f"\n  Generated network:")
        print(f"    Total nodes: {len(all_nodes)}")
        print(f"    v27 partition: nodes {v27_partition['start_index']}-{v27_partition['end_index']}")
        print(f"    v22 partition: nodes {v22_partition['start_index']}-{v22_partition['end_index']}")
        print(f"    Total edges: {len(edges)}")
        print(f"    Cross-partition edges: 0 (version-segregated)")

        return network

    def write_network_yaml(self, output_path: str):
        """Generate and write network configuration to file"""
        network = self.generate_network_yaml()

        with open(output_path, 'w') as f:
            yaml.dump(network, f, default_flow_style=False, sort_keys=False)

        print(f"\n  ✓ Saved to: {output_path}")

        # Also create node-defaults.yaml in the same directory
        import os
        output_dir = os.path.dirname(output_path)
        node_defaults_path = os.path.join(output_dir, 'node-defaults.yaml')

        node_defaults = {
            'chain': 'regtest',
            'image': {
                'repository': 'bitcoindevproject/bitcoin',
                'pullPolicy': 'IfNotPresent'
            },
            'defaultConfig': (
                'regtest=1\n'
                'server=1\n'
                'txindex=1\n'
                'fallbackfee=0.00001\n'
                'rpcuser=bitcoin\n'
                'rpcpassword=bitcoin\n'
                'rpcallowip=0.0.0.0/0\n'
                'rpcbind=0.0.0.0\n'
                'rpcport=18443\n'
                'zmqpubrawblock=tcp://0.0.0.0:28332\n'
                'zmqpubrawtx=tcp://0.0.0.0:28333\n'
                'debug=rpc'
            ),
            'collectLogs': False,
            'metricsExport': False
        }

        with open(node_defaults_path, 'w') as f:
            yaml.dump(node_defaults, f, default_flow_style=False, sort_keys=False)

        print(f"  ✓ Created node-defaults.yaml")


def main():
    parser = argparse.ArgumentParser(
        description='Generate version-segregated networks for systematic fork testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test 5.3: 70% economic, 30% hashrate on v27
  python3 partition_network_generator.py --test-id 5.3 --v27-economic 70 --v27-hashrate 30

  # Test 3.5: 30% economic, 70% hashrate on v27
  python3 partition_network_generator.py --test-id 3.5 --v27-economic 30 --v27-hashrate 70

  # Test 4.4: 50/50 split
  python3 partition_network_generator.py --test-id 4.4 --v27-economic 50 --v27-hashrate 50
        """
    )

    parser.add_argument('--test-id', required=True, help='Test identifier (e.g., 5.3)')
    parser.add_argument('--v27-economic', type=float, required=True,
                        help='Percentage of economic weight on v27 (0-100)')
    parser.add_argument('--v27-hashrate', type=float, required=True,
                        help='Percentage of hashrate on v27 (0-100)')
    parser.add_argument('--output', '-o', help='Output file path (default: auto-generated)')

    args = parser.parse_args()

    # Validate inputs
    if not (0 <= args.v27_economic <= 100):
        print(f"Error: v27-economic must be 0-100, got {args.v27_economic}", file=sys.stderr)
        sys.exit(1)

    if not (0 <= args.v27_hashrate <= 100):
        print(f"Error: v27-hashrate must be 0-100, got {args.v27_hashrate}", file=sys.stderr)
        sys.exit(1)

    # Generate output path if not specified
    if not args.output:
        test_dir = f"../../test-networks/test-{args.test_id}-economic-{int(args.v27_economic)}-hashrate-{int(args.v27_hashrate)}"
        import os
        os.makedirs(test_dir, exist_ok=True)
        args.output = f"{test_dir}/network.yaml"

    # Generate network
    generator = PartitionNetworkGenerator(args.test_id, args.v27_economic, args.v27_hashrate)
    generator.write_network_yaml(args.output)

    print(f"\n✓ Test {args.test_id} network configuration complete!")
    print(f"\nNext steps:")
    print(f"  1. Review: cat {args.output}")
    print(f"  2. Deploy: warnet deploy {os.path.dirname(args.output)}")
    print(f"  3. Run test: ./run_partition_test.sh {args.test_id}")


if __name__ == "__main__":
    main()
