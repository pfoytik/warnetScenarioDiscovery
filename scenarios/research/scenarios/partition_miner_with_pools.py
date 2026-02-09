#!/usr/bin/env python3

"""
Partition Mining Scenario with Dynamic Pool Strategy

Integration of:
- Phase 1: Price Oracle (price tracking)
- Phase 2: Fee Oracle (fee market dynamics)
- Phase 3: Mining Pool Strategy (ideology + profitability)

Key changes from static partition_miner:
- Hashrate allocation is DYNAMIC (updates every 10 minutes)
- Pools make individual decisions based on profitability + ideology
- Network topology stays STATIC (v27 nodes isolated from v26 nodes)
- Only the MINING PROBABILITY changes

Network stays partitioned:
  v27 nodes ✗✗✗ v26 nodes (can't communicate)

But pools can switch which network they mine on:
  Pool chooses v27 → generatetoaddress() on v27 nodes
  Pool chooses v26 → generatetoaddress() on v26 nodes
"""

from time import sleep, time
from random import random, choices
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from commander import Commander

# Import inline implementations (warnet bundler limitation)
import os
_lib_dir = os.path.join(os.path.dirname(__file__), '../lib')
exec(open(os.path.join(_lib_dir, 'price_oracle.py')).read().split('if __name__')[0])
exec(open(os.path.join(_lib_dir, 'fee_oracle.py')).read().split('if __name__')[0])
exec(open(os.path.join(_lib_dir, 'mining_pool_strategy.py')).read().split('if __name__')[0])


class PartitionMinerWithPools(Commander):
    """
    Partition mining with dynamic pool strategy.

    Pools individually decide which fork to mine based on:
    1. Profitability (price × fees)
    2. Ideology (fork preference)
    3. Loss tolerance (economic sustainability)
    """

    def set_test_params(self):
        """Initialize test parameters"""
        self.num_nodes = 0
        self.v27_nodes = []
        self.v26_nodes = []
        self.blocks_mined = {'v27': 0, 'v26': 0}

        # Oracles
        self.price_oracle = None
        self.fee_oracle = None
        self.pool_strategy = None

        # Current hashrate allocation (dynamic)
        self.current_v27_hashrate = 0.0
        self.current_v26_hashrate = 0.0

        # Pool-to-node mappings (per partition)
        self.pool_nodes_v27 = {}  # pool_id -> list of v27 nodes
        self.pool_nodes_v26 = {}  # pool_id -> list of v26 nodes

        # Node metadata from network.yaml
        self.node_metadata = {}  # node_name -> metadata dict

    def add_options(self, parser: argparse.ArgumentParser):
        """Add command-line arguments"""
        parser.add_argument('--v27-economic', type=float, default=70.0,
                          help='Economic weight on v27 (0-100)')
        parser.add_argument('--v26-economic', type=float, default=None)
        parser.add_argument('--interval', type=int, default=10,
                          help='Block mining interval (seconds)')
        parser.add_argument('--duration', type=int, default=7200,
                          help='Test duration (seconds), default 2 hours')
        parser.add_argument('--start-height', type=int, default=101)

        # Pool configuration
        parser.add_argument('--pool-scenario', type=str, default='realistic_current',
                          help='Pool scenario from mining_pools_config.yaml')
        parser.add_argument('--initial-v27-hashrate', type=float, default=None,
                          help='Initial v27 hashrate (if not using pools)')

        # Network configuration
        parser.add_argument('--network-yaml', type=str, default=None,
                          help='Path to network.yaml file with node metadata')

        # Update intervals
        parser.add_argument('--hashrate-update-interval', type=int, default=600,
                          help='Pool decision interval (seconds), default 10min')
        parser.add_argument('--price-update-interval', type=int, default=60,
                          help='Price update interval (seconds)')

    def load_network_metadata(self):
        """Load node metadata from network.yaml file"""
        if not self.options.network_yaml:
            self.log.warning("No network YAML specified, pool mapping will be limited")
            return

        network_yaml_path = Path(self.options.network_yaml)

        if not network_yaml_path.exists():
            self.log.error(f"Network YAML not found: {network_yaml_path}")
            return

        self.log.info(f"Loading network metadata from {network_yaml_path}")

        try:
            with open(network_yaml_path, 'r') as f:
                network_config = yaml.safe_load(f)

            # Build node name -> metadata mapping
            for node_config in network_config.get('nodes', []):
                node_name = node_config.get('name')
                metadata = node_config.get('metadata', {})

                if node_name:
                    self.node_metadata[node_name] = metadata

            self.log.info(f"✓ Loaded metadata for {len(self.node_metadata)} nodes")

        except Exception as e:
            self.log.error(f"Error loading network YAML: {e}")

    def partition_nodes_by_version(self):
        """Separate nodes into v27 and v26 partitions"""
        self.log.info("Partitioning nodes by version...")

        for node in self.nodes:
            try:
                network_info = node.getnetworkinfo()
                version_string = network_info.get('subversion', '')

                is_v27 = '27.' in version_string or ':27.' in version_string
                is_v26 = '26.' in version_string or ':26.' in version_string

                if is_v27:
                    self.v27_nodes.append(node)
                elif is_v26:
                    self.v26_nodes.append(node)

            except Exception as e:
                self.log.error(f"  Error querying node {node.index}: {e}")

        self.log.info(f"\nPartition summary:")
        self.log.info(f"  v27 nodes: {len(self.v27_nodes)}")
        self.log.info(f"  v26 nodes: {len(self.v26_nodes)}")

    def build_pool_node_mapping(self):
        """
        Build mapping from pool IDs to nodes in each partition.

        Architecture:
        - Each pool has ONE node per partition (if present)
        - Same entity_id appears in both partitions (paired nodes)
        - Pool decides which fork to mine → uses corresponding node
        """
        self.log.info("\nBuilding pool-to-node mappings...")

        # Track unmapped nodes
        v27_unmapped = 0
        v26_unmapped = 0

        # Read node metadata to extract pool assignments
        for node in self.v27_nodes:
            pool_id = self.get_node_pool_id(node)
            if pool_id:
                if pool_id not in self.pool_nodes_v27:
                    self.pool_nodes_v27[pool_id] = []
                self.pool_nodes_v27[pool_id].append(node)
            else:
                v27_unmapped += 1

        for node in self.v26_nodes:
            pool_id = self.get_node_pool_id(node)
            if pool_id:
                if pool_id not in self.pool_nodes_v26:
                    self.pool_nodes_v26[pool_id] = []
                self.pool_nodes_v26[pool_id].append(node)
            else:
                v26_unmapped += 1

        # Log pool distribution
        self.log.info("\nPool node distribution (1 node per partition per pool):")

        # Get all unique pool IDs from both partitions
        all_pools = set(self.pool_nodes_v27.keys()) | set(self.pool_nodes_v26.keys())

        for pool_id in sorted(all_pools):
            v27_nodes = self.pool_nodes_v27.get(pool_id, [])
            v26_nodes = self.pool_nodes_v26.get(pool_id, [])

            v27_str = f"node-{v27_nodes[0].index:04d}" if v27_nodes else "none"
            v26_str = f"node-{v26_nodes[0].index:04d}" if v26_nodes else "none"

            # Warn if pool has multiple nodes in one partition (unexpected)
            if len(v27_nodes) > 1:
                self.log.warning(f"  {pool_id:15s}: MULTIPLE v27 nodes ({len(v27_nodes)}) - expected 1")
            if len(v26_nodes) > 1:
                self.log.warning(f"  {pool_id:15s}: MULTIPLE v26 nodes ({len(v26_nodes)}) - expected 1")

            self.log.info(f"  {pool_id:15s}: v27={v27_str:12s} v26={v26_str:12s}")

        if v27_unmapped > 0:
            self.log.info(f"\n  {v27_unmapped} v27 nodes without pool assignment (economic/user nodes)")

        if v26_unmapped > 0:
            self.log.info(f"  {v26_unmapped} v26 nodes without pool assignment (economic/user nodes)")

    def get_node_pool_id(self, node) -> Optional[str]:
        """Extract pool ID from node metadata (read from network.yaml)"""
        try:
            # Get node name from tank_index
            # Warnet nodes are typically named "node-XXXX"
            node_name = f"node-{node.index:04d}"

            # Look up metadata from network.yaml
            if node_name in self.node_metadata:
                metadata = self.node_metadata[node_name]
                entity_id = metadata.get('entity_id', None)

                if entity_id and entity_id.startswith('pool-'):
                    # Convert pool-antpool -> antpool
                    pool_id = entity_id.replace('pool-', '')
                    return pool_id

            return None

        except Exception as e:
            self.log.debug(f"Could not extract pool ID from node {node.index}: {e}")
            return None

    def select_mining_node(self) -> Tuple[Optional[object], Optional[str]]:
        """
        Select a mining node based on pool decisions and hashrate weights.

        Architecture (Simple Binary Allocation):
        1. Each pool chooses ONE fork to mine ('v27' or 'v26')
        2. Pool's full hashrate goes to chosen fork
        3. Weighted random selection based on hashrate
        4. Selected pool's node on chosen partition mines the block
        """
        if not self.pool_strategy:
            # Fallback: random selection from aggregate hashrate
            rand_val = random() * 100.0
            if rand_val < self.current_v27_hashrate:
                partition = 'v27'
                nodes = self.v27_nodes
            else:
                partition = 'v26'
                nodes = self.v26_nodes

            if not nodes:
                return None, None
            return choices(nodes, k=1)[0], partition

        # Pool-based selection with binary allocation
        # Build weighted list of (pool_id, partition) based on pool decisions
        pool_choices = []
        pool_weights = []

        for pool_id, allocation in self.pool_strategy.current_allocation.items():
            pool = self.pool_strategy.pools[pool_id]
            hashrate_weight = pool.hashrate_pct

            # Binary allocation: pool chooses one fork
            chosen_fork = allocation  # 'v27' or 'v26'

            # Check if pool has a node in the chosen partition
            if chosen_fork == 'v27':
                if pool_id in self.pool_nodes_v27 and self.pool_nodes_v27[pool_id]:
                    pool_choices.append((pool_id, 'v27'))
                    pool_weights.append(hashrate_weight)
                else:
                    self.log.debug(f"Pool {pool_id} chose v27 but has no v27 node")
            elif chosen_fork == 'v26':
                if pool_id in self.pool_nodes_v26 and self.pool_nodes_v26[pool_id]:
                    pool_choices.append((pool_id, 'v26'))
                    pool_weights.append(hashrate_weight)
                else:
                    self.log.debug(f"Pool {pool_id} chose v26 but has no v26 node")

        if not pool_choices:
            # No pools available, fallback
            self.log.warning("No pool nodes available for current allocation")
            return None, None

        # Weighted random selection by hashrate
        selected_pool_id, partition = choices(pool_choices, weights=pool_weights, k=1)[0]

        # Get the pool's node on the chosen partition (should be exactly 1 node)
        if partition == 'v27':
            nodes = self.pool_nodes_v27.get(selected_pool_id, [])
        else:
            nodes = self.pool_nodes_v26.get(selected_pool_id, [])

        if not nodes:
            self.log.warning(f"No nodes for pool {selected_pool_id} in {partition}")
            return None, None

        # Return the pool's node (first/only node in list)
        selected_node = nodes[0]
        return selected_node, partition

    def run_test(self):
        """Main mining loop with dynamic pool strategy"""

        # Calculate complementary economic weight
        if self.options.v26_economic is None:
            self.options.v26_economic = 100.0 - self.options.v27_economic

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining with Dynamic Pool Strategy")
        self.log.info(f"{'='*70}")
        self.log.info(f"Economic weights: v27={self.options.v27_economic}%, v26={self.options.v26_economic}%")
        self.log.info(f"Duration: {self.options.duration}s ({self.options.duration/60:.0f} minutes)")
        self.log.info(f"Pool scenario: {self.options.pool_scenario}")
        self.log.info(f"{'='*70}\n")

        # Initialize oracles
        self.price_oracle = PriceOracle(base_price=60000, min_fork_depth=6)
        self.log.info("✓ Price oracle initialized")

        self.fee_oracle = FeeOracle()
        self.log.info("✓ Fee oracle initialized")

        # Initialize pool strategy
        try:
            _config_path = os.path.join(os.path.dirname(__file__), '../config/mining_pools_config.yaml')
            pools = load_pools_from_config(
                _config_path,
                self.options.pool_scenario
            )
            self.pool_strategy = MiningPoolStrategy(pools)
            self.log.info(f"✓ Pool strategy initialized ({len(pools)} pools)")

            # Set initial hashrate from pool scenario
            # Assume pools start mining their preferred fork if they have one
            initial_v27 = 0.0
            initial_v26 = 0.0
            for pool in pools:
                if pool.fork_preference == ForkPreference.V27:
                    initial_v27 += pool.hashrate_pct
                elif pool.fork_preference == ForkPreference.V26:
                    initial_v26 += pool.hashrate_pct
                else:
                    # Neutral pools split evenly initially
                    initial_v27 += pool.hashrate_pct / 2
                    initial_v26 += pool.hashrate_pct / 2

            self.current_v27_hashrate = initial_v27
            self.current_v26_hashrate = initial_v26

        except Exception as e:
            self.log.warning(f"Could not load pool config: {e}")
            self.log.info("Using static hashrate allocation")

            if self.options.initial_v27_hashrate is not None:
                self.current_v27_hashrate = self.options.initial_v27_hashrate
                self.current_v26_hashrate = 100.0 - self.options.initial_v27_hashrate
            else:
                self.current_v27_hashrate = 50.0
                self.current_v26_hashrate = 50.0

            self.pool_strategy = None

        self.log.info(f"\nInitial hashrate: v27={self.current_v27_hashrate:.1f}%, v26={self.current_v26_hashrate:.1f}%\n")

        # Load node metadata from network.yaml
        self.load_network_metadata()

        # Partition nodes
        self.partition_nodes_by_version()

        # Build pool-to-node mapping
        if self.pool_strategy:
            self.build_pool_node_mapping()

        # Main mining loop
        start_time = time()
        last_hashrate_update = start_time
        last_price_update = start_time

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Starting partition mining...")
        self.log.info(f"{'='*70}\n")

        while time() - start_time < self.options.duration:
            current_time = time()
            elapsed = int(current_time - start_time)

            # Update prices (every minute by default)
            if current_time - last_price_update >= self.options.price_update_interval:
                v27_height = self.v27_nodes[0].getblockcount() if self.v27_nodes else self.options.start_height
                v26_height = self.v26_nodes[0].getblockcount() if self.v26_nodes else self.options.start_height
                fork_depth = v27_height + v26_height - (2 * self.options.start_height)

                self.price_oracle.update_prices_from_state(
                    v27_height=v27_height,
                    v26_height=v26_height,
                    v27_economic_pct=self.options.v27_economic,
                    v26_economic_pct=self.options.v26_economic,
                    v27_hashrate_pct=self.current_v27_hashrate,
                    v26_hashrate_pct=self.current_v26_hashrate,
                    common_ancestor_height=self.options.start_height
                )

                # Update fees based on network state
                v27_blocks_per_hour = (self.blocks_mined['v27'] / max(1, elapsed/3600))
                v26_blocks_per_hour = (self.blocks_mined['v26'] / max(1, elapsed/3600))

                self.fee_oracle.update_fees_from_state(
                    v27_blocks_per_hour=v27_blocks_per_hour,
                    v26_blocks_per_hour=v26_blocks_per_hour,
                    v27_economic_pct=self.options.v27_economic,
                    v26_economic_pct=self.options.v26_economic
                )

                last_price_update = current_time

            # Update hashrate allocation (every 10 minutes by default)
            if self.pool_strategy and (current_time - last_hashrate_update >= self.options.hashrate_update_interval):

                # Pools make decisions
                old_v27_hash = self.current_v27_hashrate
                old_v26_hash = self.current_v26_hashrate

                self.current_v27_hashrate, self.current_v26_hashrate = \
                    self.pool_strategy.calculate_hashrate_allocation(
                        current_time, self.price_oracle, self.fee_oracle
                    )

                # Log significant changes
                hash_change = abs(self.current_v27_hashrate - old_v27_hash)
                if hash_change > 1.0:  # More than 1% change
                    self.log.info(f"\n⚡ HASHRATE REALLOCATION at {elapsed}s:")
                    self.log.info(f"   v27: {old_v27_hash:.1f}% → {self.current_v27_hashrate:.1f}%")
                    self.log.info(f"   v26: {old_v26_hash:.1f}% → {self.current_v26_hashrate:.1f}%")

                    # Log pool switches
                    recent_decisions = [d for d in self.pool_strategy.decision_history[-20:]
                                      if d.timestamp >= last_hashrate_update]

                    for decision in recent_decisions:
                        if decision.ideology_override:
                            self.log.info(f"   💰 {decision.pool_id}: mining {decision.chosen_fork} "
                                        f"despite ${decision.opportunity_cost_usd:,.0f} loss (ideology)")
                        elif decision.chosen_fork != decision.rational_choice:
                            self.log.info(f"   ⚠️  {decision.pool_id}: forced to switch to {decision.chosen_fork}")

                last_hashrate_update = current_time

            # Mine block with CURRENT hashrate allocation
            # Select which pool mines this block (based on individual pool decisions)
            miner, partition = self.select_mining_node()

            if not miner:
                self.log.warning("No miner available, skipping block")
                sleep(self.options.interval)
                continue

            try:
                miner_wallet = Commander.ensure_miner(miner)
                address = miner_wallet.getnewaddress()
                self.generatetoaddress(miner, 1, address, sync_fun=self.no_op)

                self.blocks_mined[partition] += 1

                v27_height = self.v27_nodes[0].getblockcount() if self.v27_nodes else 0
                v26_height = self.v26_nodes[0].getblockcount() if self.v26_nodes else 0
                fork_depth = v27_height + v26_height - (2 * self.options.start_height)

                # Get current state
                v27_price = self.price_oracle.get_price('v27')
                v26_price = self.price_oracle.get_price('v26')
                price_ratio = v27_price / v26_price if v26_price > 0 else 1.0

                fork_status = "SUSTAINED" if self.price_oracle.fork_sustained else "natural split"

                # Get pool name for logging
                pool_id = self.get_node_pool_id(miner)
                pool_str = f"({pool_id})" if pool_id else ""

                self.log.info(
                    f"[{elapsed:4d}s] {partition} block {pool_str:15s} | "
                    f"Heights: v27={v27_height:3d} v26={v26_height:3d} | "
                    f"Hash: {self.current_v27_hashrate:4.1f}%/{self.current_v26_hashrate:4.1f}% | "
                    f"Price: ${v27_price:,.0f}/${v26_price:,.0f} [{fork_status}]"
                )

            except Exception as e:
                self.log.error(f"Error mining block: {e}")

            sleep(self.options.interval)

        # Final summary
        elapsed_min = (time() - start_time) / 60.0
        total_blocks = self.blocks_mined['v27'] + self.blocks_mined['v26']

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining Complete")
        self.log.info(f"{'='*70}")
        self.log.info(f"Duration: {elapsed_min:.2f} minutes")
        self.log.info(f"Blocks mined: v27={self.blocks_mined['v27']}, v26={self.blocks_mined['v26']}, total={total_blocks}")

        # Final prices
        v27_price = self.price_oracle.get_price('v27')
        v26_price = self.price_oracle.get_price('v26')

        self.log.info(f"\nFinal State:")
        self.log.info(f"  Prices: v27=${v27_price:,.0f}, v26=${v26_price:,.0f}")
        self.log.info(f"  Hashrate: v27={self.current_v27_hashrate:.1f}%, v26={self.current_v26_hashrate:.1f}%")

        # Pool strategy summary
        if self.pool_strategy:
            self.log.info("")
            self.pool_strategy.print_allocation_summary()

            # Export results
            try:
                self.pool_strategy.export_to_json('/tmp/partition_pools.json')
                self.price_oracle.export_to_json('/tmp/partition_prices.json')
                self.fee_oracle.export_to_json('/tmp/partition_fees.json')
                self.log.info(f"\n✓ Results exported to /tmp/partition_*.json")
            except Exception as e:
                self.log.error(f"Error exporting results: {e}")

        self.log.info(f"{'='*70}\n")


def main():
    """Entry point for partition mining with pools"""
    PartitionMinerWithPools().main()


if __name__ == "__main__":
    main()
