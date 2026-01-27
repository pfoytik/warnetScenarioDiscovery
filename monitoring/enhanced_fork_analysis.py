#!/usr/bin/env python3
"""
Enhanced Fork Analysis with Hashrate Tracking

Extends auto_economic_analysis.py to include hashrate distribution per fork
by integrating pool decision data from mining scenarios.

Features:
- All existing economic analysis (custody, volume, consensus weight)
- NEW: Hashrate per fork based on pool decisions
- NEW: Pool-by-pool breakdown showing which pools mine which fork
- NEW: Combined metrics (economic + hashrate alignment)

Usage:
    # Analyze with pool decisions
    python3 enhanced_fork_analysis.py \
        --network-config /path/to/network/ \
        --pool-decisions /tmp/partition_pools.json \
        --live-query

    # Analyze without pool data (falls back to economic-only)
    python3 enhanced_fork_analysis.py \
        --network-config /path/to/network/ \
        --live-query
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Optional, Tuple
import yaml

# Import base analyzer
sys.path.insert(0, os.path.dirname(__file__))
from auto_economic_analysis import WarnetEconomicAnalyzer


class EnhancedForkAnalyzer(WarnetEconomicAnalyzer):
    """
    Enhanced fork analyzer with hashrate tracking.

    Extends WarnetEconomicAnalyzer to include pool mining decisions.
    """

    def __init__(self, fork_depth_threshold: int = 3, start_height: int = None):
        super().__init__(fork_depth_threshold, start_height)
        self.pool_data = {}
        self.pool_allocations = {}  # pool_id -> 'v27' or 'v26'

    def load_pool_decisions(self, pool_decisions_path: str):
        """
        Load pool mining decisions from partition_miner_with_pools output.

        Args:
            pool_decisions_path: Path to partition_pools.json
        """
        if not os.path.exists(pool_decisions_path):
            print(f"⚠️  Pool decisions file not found: {pool_decisions_path}")
            print(f"   Hashrate analysis will be skipped")
            return

        try:
            with open(pool_decisions_path, 'r') as f:
                data = json.load(f)

            # Extract pool profiles and current allocations
            pools_data = data.get('pools', {})

            for pool_id, pool_info in pools_data.items():
                profile = pool_info.get('profile', {})
                current_allocation = pool_info.get('current_allocation')

                self.pool_data[pool_id] = {
                    'hashrate_pct': profile.get('hashrate_pct', 0),
                    'fork_preference': profile.get('fork_preference', 'neutral'),
                    'current_allocation': current_allocation
                }

                self.pool_allocations[pool_id] = current_allocation

            print(f"✓ Loaded pool decisions for {len(self.pool_data)} pools")

        except Exception as e:
            print(f"⚠️  Error loading pool decisions: {e}")

    def load_pool_data_from_network(self):
        """
        Extract pool data from network.yaml if pool decisions not available.

        This provides pool hashrate percentages but no allocation decisions.
        """
        if not self.network_config:
            return

        for node in self.network_config.get('nodes', []):
            metadata = node.get('metadata', {})

            if metadata.get('role') == 'mining_pool':
                pool_name = metadata.get('pool_name', '')
                entity_id = metadata.get('entity_id', '')

                # Extract pool_id from entity_id (pool-foundryusa -> foundryusa)
                pool_id = entity_id.replace('pool-', '') if entity_id else pool_name.lower()

                if pool_id not in self.pool_data:
                    self.pool_data[pool_id] = {
                        'hashrate_pct': metadata.get('hashrate_pct', 0),
                        'pool_name': metadata.get('entity_name', pool_name),
                        'node_name': node.get('name'),
                        'version': node.get('image', {}).get('tag', 'unknown')
                    }

        if self.pool_data:
            print(f"✓ Extracted pool metadata for {len(self.pool_data)} pools from network config")

    def map_nodes_to_forks(self, fork_data: Dict) -> Dict[str, List[str]]:
        """
        Map nodes to their respective forks based on chain tips.

        Args:
            fork_data: Fork detection data from detect_fork()

        Returns:
            Dict mapping fork_id -> list of node names
        """
        fork_nodes = {}

        for fork_id, (tip, nodes_data) in enumerate(fork_data['chains'].items()):
            fork_key = f"fork_{fork_id}"
            fork_nodes[fork_key] = [n['node'] for n in nodes_data]

        return fork_nodes

    def calculate_hashrate_per_fork(self, fork_nodes: Dict[str, List[str]]) -> Dict[str, Dict]:
        """
        Calculate hashrate distribution across forks.

        Two methods:
        1. If pool decisions available: Use current allocations
        2. If not: Infer from which fork pool nodes are on

        Args:
            fork_nodes: Dict of fork_id -> list of node names

        Returns:
            Dict of fork_id -> {hashrate_pct, pools: [...]}
        """
        hashrate_distribution = {}

        if self.pool_allocations:
            # Method 1: Use pool decisions (accurate)
            hashrate_distribution = self._calculate_from_decisions(fork_nodes)
        else:
            # Method 2: Infer from node positions (less accurate)
            hashrate_distribution = self._calculate_from_nodes(fork_nodes)

        return hashrate_distribution

    def _calculate_from_decisions(self, fork_nodes: Dict[str, List[str]]) -> Dict:
        """Calculate hashrate using pool allocation decisions"""

        # Map v27/v26 to fork_0/fork_1
        # Assumption: fork with higher version number is v27
        fork_versions = {}
        for fork_id, nodes in fork_nodes.items():
            # Check version of first node in this fork
            for node_name in nodes:
                if node_name in self.node_economic_data:
                    version = self.node_economic_data[node_name].get('version', '26.0')
                    fork_versions[fork_id] = version
                    break

        # Determine which fork is v27 and which is v26
        v27_fork = None
        v26_fork = None
        for fork_id, version in fork_versions.items():
            if '27' in str(version):
                v27_fork = fork_id
            elif '26' in str(version):
                v26_fork = fork_id

        hashrate_dist = {}

        for fork_id in fork_nodes.keys():
            fork_allocation = 'v27' if fork_id == v27_fork else 'v26'

            pools_on_fork = []
            total_hashrate = 0.0

            for pool_id, allocation in self.pool_allocations.items():
                if allocation == fork_allocation:
                    pool_info = self.pool_data[pool_id]
                    hashrate = pool_info.get('hashrate_pct', 0)

                    pools_on_fork.append({
                        'pool_id': pool_id,
                        'hashrate_pct': hashrate
                    })
                    total_hashrate += hashrate

            hashrate_dist[fork_id] = {
                'hashrate_pct': total_hashrate,
                'pools': pools_on_fork,
                'method': 'pool_decisions'
            }

        return hashrate_dist

    def _calculate_from_nodes(self, fork_nodes: Dict[str, List[str]]) -> Dict:
        """Calculate hashrate by inferring which nodes are pool nodes"""

        hashrate_dist = {}

        for fork_id, nodes in fork_nodes.items():
            pools_on_fork = []
            total_hashrate = 0.0

            for node_name in nodes:
                # Check if this node is a pool node
                for pool_id, pool_info in self.pool_data.items():
                    if pool_info.get('node_name') == node_name:
                        hashrate = pool_info.get('hashrate_pct', 0)

                        pools_on_fork.append({
                            'pool_id': pool_id,
                            'hashrate_pct': hashrate
                        })
                        total_hashrate += hashrate
                        break

            hashrate_dist[fork_id] = {
                'hashrate_pct': total_hashrate,
                'pools': pools_on_fork,
                'method': 'node_inference'
            }

        return hashrate_dist

    def analyze_fork_comprehensive(self, fork_data: Dict, chain_state: Dict) -> Dict:
        """
        Comprehensive fork analysis including hashrate.

        Args:
            fork_data: Fork detection data
            chain_state: Current chain state

        Returns:
            Enhanced analysis dict with hashrate metrics
        """
        # Map nodes to forks
        fork_nodes = self.map_nodes_to_forks(fork_data)

        # Calculate hashrate per fork
        hashrate_dist = self.calculate_hashrate_per_fork(fork_nodes)

        # Perform economic analysis for each fork (existing functionality)
        fork_analysis = {}

        for fork_id, nodes in fork_nodes.items():
            # Create economic nodes list for this fork
            economic_nodes = []

            for node_name in nodes:
                if node_name in self.node_economic_data:
                    node_data = self.node_economic_data[node_name]
                    economic_nodes.append(self.analyzer.create_node(
                        node_id=node_name,
                        custody=node_data.get('custody_btc', 0),
                        volume=node_data.get('daily_volume_btc', 0)
                    ))

            # Analyze this fork
            analysis = self.analyzer.analyze_fork(economic_nodes)

            # Add hashrate data
            fork_analysis[fork_id] = {
                **analysis,
                'hashrate': hashrate_dist.get(fork_id, {})
            }

        return fork_analysis

    def print_enhanced_analysis(self, fork_analysis: Dict, fork_depth: int):
        """
        Print comprehensive fork analysis including hashrate.

        Args:
            fork_analysis: Analysis results from analyze_fork_comprehensive()
            fork_depth: Fork depth in blocks
        """
        print("\n" + "="*70)
        print(f"ENHANCED FORK ANALYSIS (Depth: {fork_depth} blocks)")
        print("="*70)

        for fork_id, analysis in sorted(fork_analysis.items()):
            fork_num = fork_id.replace('fork_', '')
            print(f"\n{fork_id.upper()}:")
            print("-" * 70)

            # Economic metrics (existing)
            print(f"  Nodes: {analysis.get('node_count', 0)}")
            print(f"  Custody: {analysis.get('total_custody', 0):,.0f} BTC ({analysis.get('custody_pct', 0):.1f}%)")
            print(f"  Volume: {analysis.get('total_volume', 0):,.0f} BTC/day ({analysis.get('volume_pct', 0):.1f}%)")
            print(f"  Consensus Weight: {analysis.get('consensus_weight', 0):.1f} ({analysis.get('weight_pct', 0):.1f}%)")

            # Hashrate metrics (NEW)
            hashrate_data = analysis.get('hashrate', {})
            hashrate_pct = hashrate_data.get('hashrate_pct', 0)
            pools = hashrate_data.get('pools', [])
            method = hashrate_data.get('method', 'unknown')

            print(f"\n  Hashrate: {hashrate_pct:.1f}% ← NEW!")

            if pools:
                print(f"  Mining Pools ({len(pools)}):")
                for pool in sorted(pools, key=lambda p: p['hashrate_pct'], reverse=True):
                    print(f"    - {pool['pool_id']:15s}: {pool['hashrate_pct']:5.1f}%")
            else:
                print(f"  Mining Pools: (none detected)")

            print(f"  Method: {method}")

        # Summary comparison
        print("\n" + "="*70)
        print("FORK COMPARISON")
        print("="*70)

        fork_ids = sorted(fork_analysis.keys())
        if len(fork_ids) >= 2:
            fork_0 = fork_analysis[fork_ids[0]]
            fork_1 = fork_analysis[fork_ids[1]]

            print(f"\n{'Metric':<20} | {'Fork 0':>15} | {'Fork 1':>15} | {'Winner':>10}")
            print("-" * 70)

            metrics = [
                ('Hashrate %', 'hashrate.hashrate_pct', lambda v: f"{v:.1f}%"),
                ('Custody %', 'custody_pct', lambda v: f"{v:.1f}%"),
                ('Volume %', 'volume_pct', lambda v: f"{v:.1f}%"),
                ('Weight %', 'weight_pct', lambda v: f"{v:.1f}%"),
                ('Node Count', 'node_count', lambda v: f"{v}"),
            ]

            for metric_name, key, formatter in metrics:
                # Handle nested keys (e.g., 'hashrate.hashrate_pct')
                keys = key.split('.')
                val_0 = fork_0
                val_1 = fork_1

                for k in keys:
                    val_0 = val_0.get(k, 0) if isinstance(val_0, dict) else 0
                    val_1 = val_1.get(k, 0) if isinstance(val_1, dict) else 0

                winner = "Fork 0" if val_0 > val_1 else ("Fork 1" if val_1 > val_0 else "Tie")

                print(f"{metric_name:<20} | {formatter(val_0):>15} | {formatter(val_1):>15} | {winner:>10}")

        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced fork analysis with hashrate tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With pool decisions
  python3 enhanced_fork_analysis.py \\
      --network-config ../../test-networks/test-5.3/ \\
      --pool-decisions /tmp/partition_pools.json \\
      --live-query

  # Without pool decisions (economic only)
  python3 enhanced_fork_analysis.py \\
      --network-config ../../test-networks/test-5.3/ \\
      --live-query
        """
    )

    parser.add_argument('--network-config', required=True,
                       help='Path to network directory containing network.yaml')
    parser.add_argument('--pool-decisions',
                       help='Path to pool decisions JSON (partition_pools.json)')
    parser.add_argument('--live-query', action='store_true',
                       help='Query live warnet deployment for current state')
    parser.add_argument('--fork-depth-threshold', type=int, default=6,
                       help='Minimum fork depth to analyze (default: 6)')

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = EnhancedForkAnalyzer(fork_depth_threshold=args.fork_depth_threshold)

    # Load network configuration
    print("Loading network configuration...")
    analyzer.load_network_config(args.network_config)

    # Load pool data
    if args.pool_decisions:
        print("Loading pool decisions...")
        analyzer.load_pool_decisions(args.pool_decisions)
    else:
        print("⚠️  No pool decisions file provided")
        print("   Attempting to extract pool data from network.yaml...")
        analyzer.load_pool_data_from_network()
        print("   Note: Hashrate analysis will be based on network topology, not actual decisions")

    if args.live_query:
        print("\nQuerying warnet deployment...")
        chain_state = analyzer.query_chain_state()

        print(f"✓ Queried {len(chain_state)} nodes")

        # Detect fork
        fork_data = analyzer.detect_fork(chain_state)

        if not fork_data:
            print("\n✓ No fork detected - network is synchronized")
            sys.exit(0)

        print(f"\n⚠️  Fork detected: {fork_data['num_chains']} chains")

        # Calculate fork depth
        chains = list(fork_data['chains'].items())
        if len(chains) >= 2:
            tip1 = chains[0][0]
            tip2 = chains[1][0]

            # Use any node to query (they should all have the blocks)
            node = chains[0][1][0]['node']

            common_ancestor, ancestor_height = analyzer.find_common_ancestor(node, tip1, tip2)

            if common_ancestor and ancestor_height is not None:
                height1 = chains[0][1][0]['height']
                height2 = chains[1][1][0]['height']
                fork_depth = (height1 - ancestor_height) + (height2 - ancestor_height)

                print(f"Fork depth: {fork_depth} blocks")
                print(f"  Chain 1 height: {height1} (+ {height1 - ancestor_height} blocks)")
                print(f"  Chain 2 height: {height2} (+ {height2 - ancestor_height} blocks)")
                print(f"  Common ancestor: {ancestor_height}")

                if fork_depth < analyzer.fork_depth_threshold:
                    print(f"\n✓ Fork depth ({fork_depth}) below threshold ({analyzer.fork_depth_threshold})")
                    print(f"  Likely natural chain split, ignoring")
                    sys.exit(0)

                # Perform comprehensive analysis
                fork_analysis = analyzer.analyze_fork_comprehensive(fork_data, chain_state)

                # Print results
                analyzer.print_enhanced_analysis(fork_analysis, fork_depth)

            else:
                print("⚠️  Could not determine common ancestor")

    else:
        print("\n⚠️  --live-query not specified, no analysis performed")
        print("   Use --live-query to analyze current warnet state")


if __name__ == "__main__":
    main()
