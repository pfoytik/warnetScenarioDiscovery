#!/usr/bin/env python3
"""
Automatic Economic Fork Analysis for Warnet

This script integrates with Warnet's fork detection to automatically analyze
the economic impact of detected forks using the dual-metric BCAP model.

Features:
- Fork depth analysis (finds common ancestor and measures divergence)
- Configurable fork depth threshold (ignores natural chain splits)
- Economic impact assessment for sustained forks only

Usage:
    # Analyze using network config file
    python3 auto_economic_analysis.py --network-config path/to/network/

    # Analyze using live RPC queries with default threshold
    python3 auto_economic_analysis.py --live-query

    # Custom fork depth threshold (default: 3 blocks)
    python3 auto_economic_analysis.py --live-query --fork-depth-threshold 5

    # Analyze specific fork event
    python3 auto_economic_analysis.py --fork-file path/to/fork_data.json
"""

import sys
import os
import json
import argparse
import subprocess
from typing import List, Dict, Optional, Tuple
import yaml

# Import fork analyzer
sys.path.insert(0, os.path.dirname(__file__))
from economic_fork_analyzer import EconomicForkAnalyzer, EconomicNode


class WarnetEconomicAnalyzer:
    """Integrates economic fork analysis with Warnet deployment."""

    def __init__(self, fork_depth_threshold: int = 3, start_height: int = None, custody_weight: float = None, volume_weight: float = None):
        self.analyzer = EconomicForkAnalyzer(
            custody_weight=custody_weight,
            volume_weight=volume_weight
        )
        self.network_config = None
        self.node_economic_data = {}
        self.fork_depth_threshold = fork_depth_threshold  # Minimum depth to be considered a fork
        self.start_height = start_height  # Common ancestor height for controlled tests

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

    def rpc_call(self, node: str, method: str, params: List = None) -> any:
        """Execute warnet bitcoin rpc command"""
        cmd = ['warnet', 'bitcoin', 'rpc', node, method]
        if params:
            cmd.extend([json.dumps(p) for p in params])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return None
        except json.JSONDecodeError:
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return None

    def get_block_header(self, node: str, block_hash: str) -> Optional[Dict]:
        """Get block header information"""
        result = self.rpc_call(node, 'getblockheader', [block_hash, True])
        if result is None or isinstance(result, str):
            return None
        return result

    def walk_to_height(self, node: str, tip: str, target_height: int) -> Optional[str]:
        """Walk backwards from tip to target height"""
        current = tip
        header = self.get_block_header(node, current)

        if not header:
            return None

        while header and header.get('height', -1) > target_height:
            current = header.get('previousblockhash')
            if not current:
                return None
            header = self.get_block_header(node, current)

        if header and header.get('height') == target_height:
            return current

        return None

    def find_common_ancestor(self, node: str, tip1: str, tip2: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Find common ancestor block of two chain tips.

        Returns:
            (common_ancestor_hash, height) or (None, None) if not found
        """
        header1 = self.get_block_header(node, tip1)
        header2 = self.get_block_header(node, tip2)

        if not header1 or not header2:
            return None, None

        height1 = header1.get('height')
        height2 = header2.get('height')

        if height1 is None or height2 is None:
            return None, None

        # Start from the lower height
        current_height = min(height1, height2)

        # Walk backwards until we find a common block
        while current_height >= 0:
            block_at_height_1 = self.walk_to_height(node, tip1, current_height)
            block_at_height_2 = self.walk_to_height(node, tip2, current_height)

            if block_at_height_1 and block_at_height_2 and block_at_height_1 == block_at_height_2:
                return block_at_height_1, current_height

            current_height -= 1

            # Safety limit - don't search too far back
            if current_height < max(0, min(height1, height2) - 1000):
                break

        return None, None

    def calculate_fork_depth(self, fork_info: Dict, chain_state: Dict) -> Optional[Dict]:
        """
        Calculate fork depth for detected chains.

        If start_height is provided (controlled test), uses exact calculation:
            fork_depth = (height1 - start_height) + (height2 - start_height)

        Otherwise uses height-based estimation for live fork detection.

        Args:
            fork_info: Fork detection data with chains
            chain_state: Node chain state

        Returns:
            Dict with fork depth analysis or None if depth below threshold
        """
        chains = fork_info['chains']

        if len(chains) < 2:
            return None

        # Get two largest chains
        sorted_chains = sorted(chains.items(), key=lambda x: len(x[1]), reverse=True)
        tip1, nodes1 = sorted_chains[0]
        tip2, nodes2 = sorted_chains[1]

        # Get heights
        height1 = nodes1[0]['height']
        height2 = nodes2[0]['height']

        # If start_height is known (controlled test), use exact calculation
        if self.start_height is not None:
            depth1 = height1 - self.start_height
            depth2 = height2 - self.start_height
            total_depth = depth1 + depth2
            common_height = self.start_height
            method = 'exact (from known start_height)'
        else:
            # Simplified fork depth calculation for live detection
            # Height difference indicates how far chains have diverged
            height_diff = abs(height1 - height2)

            # Estimate total depth:
            # - If heights are same (diff=0): assume 1-block natural split, depth = 2 (1 on each side)
            # - If heights differ: depth = height_diff + 2 (accounting for blocks on both chains)
            if height_diff == 0:
                # Same height: likely 1-block split on each side
                total_depth = 2
                depth1 = 1
                depth2 = 1
            else:
                # Different heights: one chain advanced more
                # Conservative estimate: height_diff + 2 blocks minimum divergence
                total_depth = height_diff + 2
                depth1 = max(1, height_diff) if height1 > height2 else 1
                depth2 = max(1, height_diff) if height2 > height1 else 1

            # Estimate common ancestor height (lower of the two minus estimated depth)
            common_height = min(height1, height2) - 1
            method = 'height-based estimation'

        # Check if this exceeds threshold (sustained fork)
        is_sustained = total_depth >= self.fork_depth_threshold

        return {
            'common_ancestor': {
                'hash': 'estimated (not queried)' if self.start_height is None else f'height {self.start_height}',
                'height': common_height
            },
            'chain_a': {
                'tip': tip1,
                'height': height1,
                'blocks_since_fork': depth1,
                'num_nodes': len(nodes1)
            },
            'chain_b': {
                'tip': tip2,
                'height': height2,
                'blocks_since_fork': depth2,
                'num_nodes': len(nodes2)
            },
            'total_depth': total_depth,
            'is_sustained_fork': is_sustained,
            'threshold': self.fork_depth_threshold,
            'method': method
        }

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

        # Output JSON for programmatic consumption (single line for parsing)
        print("\n### JSON OUTPUT ###")
        print(json.dumps(result))
        print()

    def run_live_analysis(self):
        """
        Run economic analysis on current live network state.
        Only analyzes sustained forks (depth >= threshold).
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
            # Output JSON for programmatic consumption (single line for parsing)
            no_fork_result = {
                "fork_detected": False,
                "message": "No fork detected - all nodes on same chain"
            }
            print("\n### JSON OUTPUT ###")
            print(json.dumps(no_fork_result))
            print()
            return 0

        print(f"⚠  Fork detected! {fork_info['num_chains']} different chains")

        # Calculate fork depth
        print(f"📊 Calculating fork depth (threshold: {self.fork_depth_threshold} blocks)...")
        fork_depth = self.calculate_fork_depth(fork_info, chain_state)

        if not fork_depth:
            print("✗ Could not calculate fork depth")
            return 1

        # Check if this is a sustained fork
        if not fork_depth['is_sustained_fork']:
            print(f"✓ Natural chain split detected (depth: {fork_depth['total_depth']} blocks, {fork_depth.get('method', 'calculated')})")
            print(f"  Chain A: height {fork_depth['chain_a']['height']}, {fork_depth['chain_a']['num_nodes']} nodes")
            print(f"  Chain B: height {fork_depth['chain_b']['height']}, {fork_depth['chain_b']['num_nodes']} nodes")
            print(f"  Height difference: {abs(fork_depth['chain_a']['height'] - fork_depth['chain_b']['height'])} blocks")
            print(f"✓ Below threshold ({fork_depth['total_depth']} < {self.fork_depth_threshold}) - not analyzing")
            print("  (This is normal Bitcoin behavior - chains will re-converge)")
            # Output JSON for programmatic consumption (single line for parsing)
            below_threshold_result = {
                "fork_detected": True,
                "is_sustained_fork": False,
                "fork_depth": fork_depth,
                "threshold": self.fork_depth_threshold,
                "message": "Natural chain split - below threshold"
            }
            print("\n### JSON OUTPUT ###")
            print(json.dumps(below_threshold_result))
            print()
            return 0
        else:
            print(f"⚠  SUSTAINED FORK detected (depth: {fork_depth['total_depth']} blocks >= {self.fork_depth_threshold}, {fork_depth.get('method', 'calculated')})")
            print(f"  Chain A: height {fork_depth['chain_a']['height']}, {fork_depth['chain_a']['num_nodes']} nodes")
            print(f"  Chain B: height {fork_depth['chain_b']['height']}, {fork_depth['chain_b']['num_nodes']} nodes")
            print(f"  Height difference: {abs(fork_depth['chain_a']['height'] - fork_depth['chain_b']['height'])} blocks")
            print()

        # Analyze economic impact (only for sustained forks)
        if not self.node_economic_data:
            print("✗ No economic metadata available. Load network config first.")
            return 1

        result = self.analyze_economic_fork(fork_info)

        if result:
            # Add fork depth info to result
            if 'fork_metadata' not in result:
                result['fork_metadata'] = {}
            result['fork_metadata']['fork_depth'] = fork_depth

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

  # Use custom fork depth threshold (only analyze forks >= 5 blocks deep)
  python3 auto_economic_analysis.py --live-query --fork-depth-threshold 5
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

    parser.add_argument(
        '--fork-depth-threshold',
        type=int,
        default=3,
        help='Minimum fork depth (total blocks) to be considered a sustained fork (default: 3)'
    )

    parser.add_argument(
        '--start-height',
        type=int,
        default=None,
        help='Common ancestor height (for controlled tests). If provided, fork depth will be calculated from this height.'
    )

    parser.add_argument(
        '--custody-weight',
        type=float,
        default=0.7,
        help='Weight for custody metric in consensus weight calculation (default: 0.7 for 70%%)'
    )

    parser.add_argument(
        '--volume-weight',
        type=float,
        default=0.3,
        help='Weight for volume metric in consensus weight calculation (default: 0.3 for 30%%)'
    )

    args = parser.parse_args()

    # Validate weights sum to 1.0
    if abs(args.custody_weight + args.volume_weight - 1.0) > 0.001:
        print(f"Error: --custody-weight and --volume-weight must sum to 1.0", file=sys.stderr)
        print(f"Got: custody={args.custody_weight}, volume={args.volume_weight}, sum={args.custody_weight + args.volume_weight}", file=sys.stderr)
        return 1

    # Initialize analyzer
    analyzer = WarnetEconomicAnalyzer(
        fork_depth_threshold=args.fork_depth_threshold,
        start_height=args.start_height,
        custody_weight=args.custody_weight,
        volume_weight=args.volume_weight
    )

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
