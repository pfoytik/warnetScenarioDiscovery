#!/usr/bin/env python3
"""
Configurable Bitcoin Network Generator for Economic Fork Testing

This script generates Warnet network configurations with full control over:
- Bitcoin Core versions per node
- Economic metadata (custody, volume, consensus weight)
- Pool-to-node connection mappings
- Network topology
- Pool hashrate distribution

Usage:
    python3 configurable_network_generator.py scenario_config.yaml

Example scenario config:
    See example_scenarios/ directory for templates
"""

import yaml
import sys
from typing import Dict, List, Any


class ConfigurableNetworkGenerator:
    """Generate Warnet networks from scenario configuration files"""

    def __init__(self, scenario_config_path: str):
        """
        Initialize generator with scenario configuration.

        Args:
            scenario_config_path: Path to YAML scenario configuration file
        """
        with open(scenario_config_path, 'r') as f:
            self.scenario = yaml.safe_load(f)

        self.validate_scenario()

    def validate_scenario(self):
        """Validate scenario configuration has all required fields"""
        required = ['name', 'description', 'economic_nodes', 'pool_nodes', 'network_nodes', 'topology']

        for field in required:
            if field not in self.scenario:
                raise ValueError(f"Missing required field in scenario: {field}")

        # Validate economic nodes
        for node in self.scenario['economic_nodes']:
            if 'custody_btc' not in node or 'daily_volume_btc' not in node:
                raise ValueError(f"Economic node missing custody_btc or daily_volume_btc: {node}")

        # Validate pool nodes
        for node in self.scenario['pool_nodes']:
            if 'pool_name' not in node or 'hashrate_percent' not in node:
                raise ValueError(f"Pool node missing pool_name or hashrate_percent: {node}")

        print(f"✓ Validated scenario: {self.scenario['name']}")

    def generate_network(self) -> Dict:
        """
        Generate complete network configuration.

        Returns:
            Dict suitable for writing to network.yaml
        """
        network = {
            'name': self.scenario['name'],
            'nodes': [],
            'edges': []
        }

        # Track node indices
        node_index = 0

        # Generate economic nodes
        economic_nodes = []
        for econ_config in self.scenario['economic_nodes']:
            node = self._create_economic_node(node_index, econ_config)
            network['nodes'].append(node)
            economic_nodes.append(node_index)
            node_index += 1

        # Generate pool nodes
        pool_nodes = []
        for pool_config in self.scenario['pool_nodes']:
            node = self._create_pool_node(node_index, pool_config)
            network['nodes'].append(node)
            pool_nodes.append(node_index)
            node_index += 1

        # Generate network nodes
        network_nodes_list = []
        for net_config in self.scenario['network_nodes']:
            node = self._create_network_node(node_index, net_config)
            network['nodes'].append(node)
            network_nodes_list.append(node_index)
            node_index += 1

        # Generate topology/edges
        edges = self._generate_topology(economic_nodes, pool_nodes, network_nodes_list)
        network['edges'] = edges

        return network

    def _create_economic_node(self, index: int, config: Dict) -> Dict:
        """
        Create economic node configuration.

        Args:
            index: Node index
            config: Economic node configuration from scenario

        Returns:
            Node configuration dict
        """
        # Calculate consensus weight (70% custody + 30% volume)
        custody = config['custody_btc']
        volume = config['daily_volume_btc']
        consensus_weight = round((0.7 * custody + 0.3 * volume) / 10000, 2)

        node = {
            'index': index,
            'version': config.get('version', '27.0'),  # Default to 27.0
            'bitcoin_config': config.get('bitcoin_config', {}),
        }

        # Add economic metadata
        node['metadata'] = {
            'role': config.get('role', 'exchange'),
            'custody_btc': custody,
            'daily_volume_btc': volume,
            'consensus_weight': consensus_weight,
            'description': config.get('description', f'Economic node {index}')
        }

        # Add connection limits
        node['bitcoin_config'] = {
            **node['bitcoin_config'],
            'maxconnections': config.get('max_connections', 125),
            'maxmempool': config.get('max_mempool_mb', 500)
        }

        return node

    def _create_pool_node(self, index: int, config: Dict) -> Dict:
        """
        Create pool node configuration.

        Args:
            index: Node index
            config: Pool node configuration from scenario

        Returns:
            Node configuration dict
        """
        node = {
            'index': index,
            'version': config.get('version', '27.0'),
            'bitcoin_config': config.get('bitcoin_config', {}),
        }

        # Add pool metadata
        node['metadata'] = {
            'pool_name': config['pool_name'],
            'hashrate_percent': config['hashrate_percent'],
            'connected_to': config.get('connected_to', []),  # List of node indices
            'description': config.get('description', f"Mining pool: {config['pool_name']}")
        }

        # Add connection limits
        node['bitcoin_config'] = {
            **node['bitcoin_config'],
            'maxconnections': config.get('max_connections', 50),
            'maxmempool': config.get('max_mempool_mb', 200)
        }

        return node

    def _create_network_node(self, index: int, config: Dict) -> Dict:
        """
        Create network propagation node configuration.

        Args:
            index: Node index
            config: Network node configuration from scenario

        Returns:
            Node configuration dict
        """
        node = {
            'index': index,
            'version': config.get('version', '27.0'),
            'bitcoin_config': config.get('bitcoin_config', {}),
        }

        # Optional economic metadata for network nodes
        if 'custody_btc' in config or 'daily_volume_btc' in config:
            custody = config.get('custody_btc', 0)
            volume = config.get('daily_volume_btc', 0)
            consensus_weight = round((0.7 * custody + 0.3 * volume) / 10000, 2)

            node['metadata'] = {
                'role': config.get('role', 'network_node'),
                'custody_btc': custody,
                'daily_volume_btc': volume,
                'consensus_weight': consensus_weight,
                'description': config.get('description', f'Network node {index}')
            }
        else:
            node['metadata'] = {
                'description': config.get('description', f'Network propagation node {index}')
            }

        # Add connection limits
        node['bitcoin_config'] = {
            **node['bitcoin_config'],
            'maxconnections': config.get('max_connections', 30),
            'maxmempool': config.get('max_mempool_mb', 100)
        }

        return node

    def _generate_topology(self, economic_nodes: List[int], pool_nodes: List[int],
                          network_nodes: List[int]) -> List[List[int]]:
        """
        Generate network topology/edges based on scenario configuration.

        Args:
            economic_nodes: List of economic node indices
            pool_nodes: List of pool node indices
            network_nodes: List of network node indices

        Returns:
            List of edges (connections between nodes)
        """
        edges = []

        # Use custom topology if provided
        if 'custom_edges' in self.scenario['topology']:
            return self.scenario['topology']['custom_edges']

        # Otherwise, generate topology based on rules
        topology_type = self.scenario['topology'].get('type', 'full_economic_mesh')

        # 1. Connect economic nodes (typically full mesh)
        if topology_type in ['full_economic_mesh', 'default']:
            for i in range(len(economic_nodes)):
                for j in range(i + 1, len(economic_nodes)):
                    edges.append([economic_nodes[i], economic_nodes[j]])

        # 2. Connect pools to economic nodes based on pool metadata
        for pool_idx in pool_nodes:
            # Find pool node in scenario config
            pool_config = self.scenario['pool_nodes'][pool_idx - len(economic_nodes)]

            if 'connected_to' in pool_config and pool_config['connected_to']:
                # Use explicit connections
                for target_idx in pool_config['connected_to']:
                    if [pool_idx, target_idx] not in edges and [target_idx, pool_idx] not in edges:
                        edges.append([pool_idx, target_idx])
            else:
                # Default: connect to all economic nodes
                for econ_idx in economic_nodes:
                    edges.append([pool_idx, econ_idx])

        # 3. Connect pools to each other (neighbors)
        pool_peer_strategy = self.scenario['topology'].get('pool_peering', 'neighbors')

        if pool_peer_strategy == 'neighbors':
            for i in range(len(pool_nodes) - 1):
                edges.append([pool_nodes[i], pool_nodes[i + 1]])

        elif pool_peer_strategy == 'full_mesh':
            for i in range(len(pool_nodes)):
                for j in range(i + 1, len(pool_nodes)):
                    edges.append([pool_nodes[i], pool_nodes[j]])

        # 4. Connect network nodes
        network_strategy = self.scenario['topology'].get('network_topology', 'ring_plus_economic')

        if network_strategy == 'ring_plus_economic':
            # Ring among network nodes
            for i in range(len(network_nodes)):
                edges.append([network_nodes[i], network_nodes[(i + 1) % len(network_nodes)]])

            # Connect some network nodes to economic nodes
            for i, net_idx in enumerate(network_nodes):
                # Every 3rd network node connects to an economic node
                if i % 3 == 0 and economic_nodes:
                    econ_idx = economic_nodes[i % len(economic_nodes)]
                    edges.append([net_idx, econ_idx])

        return edges

    def write_network_yaml(self, output_path: str):
        """
        Generate and write network configuration to YAML file.

        Args:
            output_path: Path to output network.yaml file
        """
        network = self.generate_network()

        with open(output_path, 'w') as f:
            yaml.dump(network, f, default_flow_style=False, sort_keys=False)

        print(f"\n✓ Generated network configuration:")
        print(f"  Scenario: {self.scenario['name']}")
        print(f"  Economic nodes: {len(self.scenario['economic_nodes'])}")
        print(f"  Pool nodes: {len(self.scenario['pool_nodes'])}")
        print(f"  Network nodes: {len(self.scenario['network_nodes'])}")
        print(f"  Total nodes: {len(network['nodes'])}")
        print(f"  Total connections: {len(network['edges'])}")
        print(f"\n  Saved to: {output_path}")

    def print_summary(self):
        """Print detailed summary of network configuration"""
        print("\n" + "=" * 80)
        print(f"NETWORK CONFIGURATION SUMMARY: {self.scenario['name']}")
        print("=" * 80)
        print(f"\nDescription: {self.scenario.get('description', 'N/A')}")

        print("\n--- ECONOMIC NODES ---")
        for i, node in enumerate(self.scenario['economic_nodes']):
            print(f"  Node {i}:")
            print(f"    Version: {node.get('version', '27.0')}")
            print(f"    Role: {node.get('role', 'exchange')}")
            print(f"    Custody: {node['custody_btc']:,} BTC")
            print(f"    Volume: {node['daily_volume_btc']:,} BTC/day")
            weight = round((0.7 * node['custody_btc'] + 0.3 * node['daily_volume_btc']) / 10000, 2)
            print(f"    Consensus Weight: {weight}")

        print("\n--- POOL NODES ---")
        for i, node in enumerate(self.scenario['pool_nodes']):
            pool_idx = i + len(self.scenario['economic_nodes'])
            print(f"  Node {pool_idx} ({node['pool_name']}):")
            print(f"    Version: {node.get('version', '27.0')}")
            print(f"    Hashrate: {node['hashrate_percent']}%")
            if 'connected_to' in node:
                print(f"    Connects to nodes: {node['connected_to']}")

        print("\n--- NETWORK NODES ---")
        offset = len(self.scenario['economic_nodes']) + len(self.scenario['pool_nodes'])
        for i, node in enumerate(self.scenario['network_nodes']):
            net_idx = i + offset
            print(f"  Node {net_idx}:")
            print(f"    Version: {node.get('version', '27.0')}")
            if 'custody_btc' in node:
                print(f"    Custody: {node.get('custody_btc', 0):,} BTC")
                print(f"    Volume: {node.get('daily_volume_btc', 0):,} BTC/day")

        print("\n" + "=" * 80)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 configurable_network_generator.py <scenario_config.yaml> [output.yaml]")
        print("\nExample:")
        print("  python3 configurable_network_generator.py scenarios/custody_vs_volume.yaml")
        sys.exit(1)

    scenario_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'network.yaml'

    try:
        generator = ConfigurableNetworkGenerator(scenario_path)
        generator.print_summary()
        generator.write_network_yaml(output_path)

        print("\n✓ Network generation complete!")
        print(f"\nNext steps:")
        print(f"  1. Review: cat {output_path}")
        print(f"  2. Deploy: warnet deploy {output_path}")
        print(f"  3. Run mining: warnet run ~/bitcoinTools/warnet/warnet/scenarios/economic_miner.py")

    except Exception as e:
        print(f"\n✗ Error generating network: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
