#!/usr/bin/env python3
"""
Automatic Economic Fork Analysis for Warnet

This script integrates with Warnet's fork detection to automatically analyze
the economic impact of detected forks using the dual-metric BCAP model.

Usage:
    # Analyze using network config file
    python3 auto_economic_analysis.py --network-config path/to/network/

    # Analyze using live RPC queries
    python3 auto_economic_analysis.py --live-query

    # Analyze specific fork event
    python3 auto_economic_analysis.py --fork-file path/to/fork_data.json
"""

import sys
import os
import json
import argparse
import subprocess
from typing import List, Dict, Optional
import yaml

# Import fork analyzer
sys.path.insert(0, os.path.dirname(__file__))
from economic_fork_analyzer import EconomicForkAnalyzer, EconomicNode


class WarnetEconomicAnalyzer:
    """Integrates economic fork analysis with Warnet deployment."""

    def __init__(self):
        self.analyzer = EconomicForkAnalyzer()
        self.network_config = None
        self.node_economic_data = {}

    def load_network_config(self, config_path: str):
        """
        Load network configuration from Warnet network directory.

        Args:
            config_path: Path to network directory containing network.yaml
        """
        network_yaml = os.path.join(config_path, 'network.yaml')

        if not os.path.exists(network_yaml):
            raise FileNotFoundError(f"Network config not found: {network_yaml}")

        with open(network_yaml, 'r') as f:
            self.network_config = yaml.safe_load(f)

        # Extract economic data from node configurations
        for node in self.network_config.get('nodes', []):
            node_name = node['name']
            metadata = node.get('metadata', {})

            # Only process nodes with economic metadata
            if 'custody_btc' in metadata:
                self.node_economic_data[node_name] = {
                    'node_type': metadata.get('node_type', 'unknown'),
                    'custody_btc': metadata.get('custody_btc', 0),
                    'daily_volume_btc': metadata.get('daily_volume_btc', 0),
                    'supply_percentage': metadata.get('supply_percentage', 0),
                    'consensus_weight': metadata.get('consensus_weight', 0),
                    'economic_influence': metadata.get('economic_influence', 'unknown'),
                    'version': node.get('image', '').split(':')[-1] if ':' in node.get('image', '') else 'unknown'
                }

        print(f"✓ Loaded network config: {self.network_config.get('network', {}).get('name', 'unknown')}")
        print(f"  Economic nodes: {len(self.node_economic_data)}")

    def query_chain_state(self) -> Dict[str, Dict]:
        """
        Query current chain state from Warnet using RPC.

        Returns:
            Dict mapping node names to their chain state
        """
        chain_state = {}

        try:
            # Get list of nodes - we'll use the node names from config if available
            nodes = list(self.node_economic_data.keys()) if self.node_economic_data else self._discover_nodes()

            for node in nodes:
                try:
                    # Get block height
                    height_result = subprocess.run(
                        ['warnet', 'bitcoin', 'rpc', node, 'getblockcount'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    # Get best block hash
                    hash_result = subprocess.run(
                        ['warnet', 'bitcoin', 'rpc', node, 'getbestblockhash'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if height_result.returncode == 0 and hash_result.returncode == 0:
                        chain_state[node] = {
                            'height': int(height_result.stdout.strip().strip('"')),
                            'tip': hash_result.stdout.strip().strip('"')
                        }
                except Exception as e:
                    print(f"  Warning: Could not query node {node}: {e}", file=sys.stderr)

        except Exception as e:
            print(f"  Error querying chain state: {e}", file=sys.stderr)

        return chain_state

    def _discover_nodes(self) -> List[str]:
        """
        Discover node names from deployed Warnet network.

        Returns:
            List of node names
        """
        try:
            # Try to get tank info first (always present)
            result = subprocess.run(
                ['warnet', 'bitcoin', 'rpc', 'tank', 'getpeerinfo'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse peer info to get node names
                # This is a simplified version - actual implementation may vary
                return ['tank']  # Fallback

        except Exception:
            pass

        return []

    def detect_fork(self, chain_state: Dict[str, Dict]) -> Optional[Dict]:
        """
        Detect if a fork exists based on chain state.

        Args:
            chain_state: Dict of node name -> {height, tip}

        Returns:
            Fork info dict if fork detected, None otherwise
        """
        if not chain_state or len(chain_state) < 2:
            return None

        # Group nodes by chain tip
        chains = {}
        for node, state in chain_state.items():
            tip = state['tip']
            if tip not in chains:
                chains[tip] = []
            chains[tip].append({
                'node': node,
                'height': state['height']
            })

        # Fork detected if more than one unique tip
        if len(chains) > 1:
            return {
                'num_chains': len(chains),
                'chains': chains
            }

        return None

    def analyze_economic_fork(self, fork_info: Dict) -> Optional[Dict]:
        """
        Analyze economic impact of detected fork.

        Args:
            fork_info: Fork detection data

        Returns:
            Economic analysis result
        """
        if not fork_info or not self.node_economic_data:
            print("  Warning: No economic data available for analysis")
            return None

        # Split nodes by chain
        chain_nodes_map = {}
        for tip, nodes_data in fork_info['chains'].items():
            chain_nodes_map[tip] = [n['node'] for n in nodes_data]

        # Create EconomicNode instances for each chain
        chain_economic_nodes = {}

        for chain_id, (tip, nodes) in enumerate(fork_info['chains'].items(), start=1):
            economic_nodes = []

            for node_info in nodes:
                node_name = node_info['node']

                if node_name in self.node_economic_data:
                    econ_data = self.node_economic_data[node_name]

                    economic_node = EconomicNode(
                        name=node_name,
                        node_type=econ_data['node_type'],
                        custody_btc=econ_data['custody_btc'],
                        daily_volume_btc=econ_data['daily_volume_btc'],
                        metadata={
                            'version': econ_data['version'],
                            'economic_influence': econ_data['economic_influence'],
                            'chain_tip': tip,
                            'height': node_info['height']
                        }
                    )

                    economic_nodes.append(economic_node)

            if economic_nodes:
                chain_economic_nodes[f'chain_{chain_id}'] = economic_nodes

        # If we have at least 2 chains with economic nodes, analyze
        if len(chain_economic_nodes) >= 2:
            chain_ids = list(chain_economic_nodes.keys())
            chain_a = chain_economic_nodes[chain_ids[0]]
            chain_b = chain_economic_nodes[chain_ids[1]]

            # Run economic analysis
            result = self.analyzer.analyze_fork(chain_a, chain_b)

            # Add fork-specific metadata
            result['fork_metadata'] = {
                'num_total_chains': fork_info['num_chains'],
                'chain_a_tip': chain_a[0].metadata['chain_tip'] if chain_a else 'unknown',
                'chain_b_tip': chain_b[0].metadata['chain_tip'] if chain_b else 'unknown',
                'chain_a_height': chain_a[0].metadata['height'] if chain_a else 0,
                'chain_b_height': chain_b[0].metadata['height'] if chain_b else 0,
            }

            return result

        else:
            print(f"  Warning: Only {len(chain_economic_nodes)} chain(s) with economic nodes")
            return None

    def print_analysis(self, result: Dict):
        """Print formatted economic analysis."""
        if not result:
            print("No economic analysis available")
            return

        # Use the fork analyzer's print method
        self.analyzer.print_report(result)

        # Add fork-specific details
        if 'fork_metadata' in result:
            print("\n### FORK TECHNICAL DETAILS ###")
            meta = result['fork_metadata']
            print(f"  Total chains: {meta['num_total_chains']}")
            print(f"  Chain A tip: {meta['chain_a_tip'][:16]}... (height {meta['chain_a_height']})")
            print(f"  Chain B tip: {meta['chain_b_tip'][:16]}... (height {meta['chain_b_height']})")
            print()

    def run_live_analysis(self):
        """
        Run economic analysis on current live network state.
        """
        print("Querying live network state...")
        chain_state = self.query_chain_state()

        if not chain_state:
            print("✗ Could not query chain state")
            return 1

        print(f"✓ Queried {len(chain_state)} nodes")

        # Check for fork
        fork_info = self.detect_fork(chain_state)

        if not fork_info:
            print("✓ No fork detected - all nodes on same chain")
            return 0

        print(f"⚠  Fork detected! {fork_info['num_chains']} different chains")

        # Analyze economic impact
        if not self.node_economic_data:
            print("✗ No economic metadata available. Load network config first.")
            return 1

        result = self.analyze_economic_fork(fork_info)

        if result:
            self.print_analysis(result)
            return 0
        else:
            print("✗ Could not perform economic analysis")
            return 1


def main():
    parser = argparse.ArgumentParser(
        description='Automatic economic fork analysis for Warnet',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze using network config
  python3 auto_economic_analysis.py --network-config ../../test-networks/dual-metric-test/

  # Analyze live state
  python3 auto_economic_analysis.py --live-query

  # Load config then query live
  python3 auto_economic_analysis.py --network-config path/to/network/ --live-query
        """
    )

    parser.add_argument(
        '--network-config',
        type=str,
        help='Path to network configuration directory (contains network.yaml)'
    )

    parser.add_argument(
        '--live-query',
        action='store_true',
        help='Query live network state from Warnet'
    )

    parser.add_argument(
        '--fork-file',
        type=str,
        help='Path to JSON file with fork detection data'
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = WarnetEconomicAnalyzer()

    # Load network config if provided
    if args.network_config:
        try:
            analyzer.load_network_config(args.network_config)
        except Exception as e:
            print(f"✗ Error loading network config: {e}", file=sys.stderr)
            return 1

    # Run live analysis if requested
    if args.live_query:
        return analyzer.run_live_analysis()

    # If fork file provided, load and analyze
    if args.fork_file:
        try:
            with open(args.fork_file, 'r') as f:
                fork_data = json.load(f)

            result = analyzer.analyze_economic_fork(fork_data)
            if result:
                analyzer.print_analysis(result)
                return 0
            else:
                print("✗ Could not analyze fork from file")
                return 1

        except Exception as e:
            print(f"✗ Error loading fork file: {e}", file=sys.stderr)
            return 1

    # If no action specified, show help
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
