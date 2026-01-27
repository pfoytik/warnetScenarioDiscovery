#!/usr/bin/env python3

"""
Partition Mining Scenario with Inline Price Tracking (Validation Test)

Temporary standalone version for testing price oracle integration.
"""

from time import sleep, time
from random import random, choices
import logging
import argparse
import asyncio
import json
from typing import Dict, List, Tuple, Optional

from commander import Commander


# Inline Price Oracle Implementation (simplified for testing)
class PriceOracle:
    """Simple price oracle for fork price tracking with sustained fork detection"""

    def __init__(
        self,
        base_price: float = 60000,
        max_divergence: float = 0.20,
        chain_weight_coef: float = 0.3,
        economic_weight_coef: float = 0.5,
        hashrate_weight_coef: float = 0.2,
        min_fork_depth: int = 6
    ):
        self.base_price = base_price
        self.max_divergence = max_divergence
        self.chain_weight_coef = chain_weight_coef
        self.economic_weight_coef = economic_weight_coef
        self.hashrate_weight_coef = hashrate_weight_coef
        self.min_fork_depth = min_fork_depth

        self.prices = {'v27': base_price, 'v26': base_price}
        self.history = []

        # Sustained fork detection
        self.fork_sustained = False
        self.fork_start_height = None

        # Initialize history
        start_time = time()
        self.history.append({
            'timestamp': start_time,
            'chain_id': 'v27',
            'price': base_price,
            'metadata': {'initial': True}
        })
        self.history.append({
            'timestamp': start_time,
            'chain_id': 'v26',
            'price': base_price,
            'metadata': {'initial': True}
        })

    def update_prices_from_state(
        self,
        v27_height: int,
        v26_height: int,
        v27_economic_pct: float,
        v26_economic_pct: float,
        v27_hashrate_pct: float,
        v26_hashrate_pct: float,
        common_ancestor_height: int,
        metadata: Optional[Dict] = None
    ) -> Tuple[float, float]:
        """Update both chain prices from current network state"""

        # Check if fork is sustained
        if self.fork_start_height is None:
            self.fork_start_height = common_ancestor_height

        fork_depth = (v27_height + v26_height) - (2 * common_ancestor_height)

        if not self.fork_sustained and fork_depth >= self.min_fork_depth:
            self.fork_sustained = True

        # Only diverge prices if fork is sustained
        if not self.fork_sustained:
            # Natural chain split - keep prices equal
            v27_price = self.base_price
            v26_price = self.base_price
        else:
            # Sustained fork - calculate price divergence
            total_blocks = v27_height + v26_height

            # Calculate weights (normalized 0-1)
            v27_chain_weight = v27_height / total_blocks if total_blocks > 0 else 0.5
            v26_chain_weight = v26_height / total_blocks if total_blocks > 0 else 0.5

            v27_econ_weight = v27_economic_pct / 100.0
            v26_econ_weight = v26_economic_pct / 100.0

            v27_hash_weight = v27_hashrate_pct / 100.0
            v26_hash_weight = v26_hashrate_pct / 100.0

            # Update v27 price
            chain_factor = 0.8 + (v27_chain_weight * 0.4)
            economic_factor = 0.8 + (v27_econ_weight * 0.4)
            hashrate_factor = 0.8 + (v27_hash_weight * 0.4)

            combined_factor = (
                chain_factor * self.chain_weight_coef +
                economic_factor * self.economic_weight_coef +
                hashrate_factor * self.hashrate_weight_coef
            )

            v27_price = self.base_price * combined_factor
            min_price = self.base_price * (1 - self.max_divergence)
            max_price = self.base_price * (1 + self.max_divergence)
            v27_price = max(min_price, min(max_price, v27_price))

            # Update v26 price
            chain_factor = 0.8 + (v26_chain_weight * 0.4)
            economic_factor = 0.8 + (v26_econ_weight * 0.4)
            hashrate_factor = 0.8 + (v26_hash_weight * 0.4)

            combined_factor = (
                chain_factor * self.chain_weight_coef +
                economic_factor * self.economic_weight_coef +
                hashrate_factor * self.hashrate_weight_coef
            )

            v26_price = self.base_price * combined_factor
            v26_price = max(min_price, min(max_price, v26_price))

        # Update prices
        self.prices['v27'] = v27_price
        self.history.append({
            'timestamp': time(),
            'chain_id': 'v27',
            'price': v27_price,
            'metadata': metadata or {}
        })

        self.prices['v26'] = v26_price
        self.history.append({
            'timestamp': time(),
            'chain_id': 'v26',
            'price': v26_price,
            'metadata': metadata or {}
        })

        return v27_price, v26_price

    def export_to_json(self, output_path: str):
        """Export price history to JSON file"""
        export_data = {
            'config': {
                'base_price': self.base_price,
                'max_divergence': self.max_divergence,
                'coefficients': {
                    'chain_weight': self.chain_weight_coef,
                    'economic_weight': self.economic_weight_coef,
                    'hashrate_weight': self.hashrate_weight_coef
                }
            },
            'current_prices': self.prices.copy(),
            'history': self.history
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def print_summary(self):
        """Print current price state summary"""
        v27_price = self.prices['v27']
        v26_price = self.prices['v26']
        ratio = v27_price / v26_price if v26_price > 0 else 1.0

        print("=" * 60)
        print("PRICE ORACLE SUMMARY")
        print("=" * 60)
        print(f"v27 Price: ${v27_price:,.2f}")
        print(f"v26 Price: ${v26_price:,.2f}")
        print(f"Price Ratio (v27/v26): {ratio:.4f}")
        print(f"Divergence: {abs(ratio - 1.0) * 100:.2f}%")
        print(f"Total price updates: {len(self.history)}")
        print("=" * 60)


class PartitionMiner(Commander):
    """
    Partition-based mining scenario with price tracking.
    """

    def set_test_params(self):
        """Initialize test parameters and instance variables"""
        self.num_nodes = 0
        self.v27_nodes = []
        self.v26_nodes = []
        self.v27_pools = {}
        self.v26_pools = {}
        self.v27_hashrate_total = 0.0
        self.v26_hashrate_total = 0.0
        self.blocks_mined = {'v27': 0, 'v26': 0}
        self.price_oracle = None

    def add_options(self, parser: argparse.ArgumentParser):
        """Add command-line arguments"""
        parser.add_argument('--v27-hashrate', type=float, required=True)
        parser.add_argument('--v26-hashrate', type=float, default=None)
        parser.add_argument('--v27-economic', type=float, default=50.0)
        parser.add_argument('--v26-economic', type=float, default=None)
        parser.add_argument('--interval', type=int, default=10)
        parser.add_argument('--duration', type=int, default=1800)
        parser.add_argument('--start-height', type=int, default=101)
        parser.add_argument('--enable-price-tracking', action='store_true')

    def partition_nodes_by_version(self):
        """Separate nodes into v27 and v26 partitions based on version"""
        self.log.info("Partitioning nodes by version...")

        for node in self.nodes:
            try:
                network_info = node.getnetworkinfo()
                version_string = network_info.get('subversion', '')

                is_v27 = '27.' in version_string or ':27.' in version_string
                is_v26 = '26.' in version_string or ':26.' in version_string

                if is_v27:
                    self.v27_nodes.append(node)
                    if hasattr(node, 'metadata') and isinstance(node.metadata, dict):
                        if 'hashrate_pct' in node.metadata:
                            self.v27_pools[node] = node.metadata['hashrate_pct']
                elif is_v26:
                    self.v26_nodes.append(node)
                    if hasattr(node, 'metadata') and isinstance(node.metadata, dict):
                        if 'hashrate_pct' in node.metadata:
                            self.v26_pools[node] = node.metadata['hashrate_pct']

            except Exception as e:
                self.log.error(f"  Error querying node {node.index}: {e}")

        self.log.info(f"\nPartition summary:")
        self.log.info(f"  v27 nodes: {len(self.v27_nodes)}")
        self.log.info(f"  v26 nodes: {len(self.v26_nodes)}")

    def select_miner_in_partition(self, nodes, pools_dict):
        """Select a miner within a partition using hashrate-weighted random selection"""
        if not pools_dict:
            return choices(nodes, k=1)[0]

        pool_nodes = list(pools_dict.keys())
        hashrates = list(pools_dict.values())
        return choices(pool_nodes, weights=hashrates, k=1)[0]

    def verify_common_history(self):
        """Verify that all nodes share common history"""
        self.log.info(f"\nVerifying common history...")
        heights = []
        for node in self.nodes:
            try:
                height = node.getblockcount()
                heights.append(height)
            except Exception as e:
                self.log.warning(f"  Error querying node: {e}")

        if heights:
            self.log.info(f"  Height range: {min(heights)} - {max(heights)}")

    def run_test(self):
        """Main mining loop with price tracking"""

        if self.options.v26_hashrate is None:
            self.options.v26_hashrate = 100.0 - self.options.v27_hashrate

        if self.options.v26_economic is None:
            self.options.v26_economic = 100.0 - self.options.v27_economic

        self.v27_hashrate_total = self.options.v27_hashrate
        self.v26_hashrate_total = self.options.v26_hashrate

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining Scenario with Price Tracking")
        self.log.info(f"{'='*70}")
        self.log.info(f"v27 partition hashrate: {self.v27_hashrate_total}%")
        self.log.info(f"v26 partition hashrate: {self.v26_hashrate_total}%")
        self.log.info(f"v27 partition economic: {self.options.v27_economic}%")
        self.log.info(f"v26 partition economic: {self.options.v26_economic}%")
        self.log.info(f"Duration: {self.options.duration}s")
        self.log.info(f"{'='*70}\n")

        # Initialize price oracle if enabled
        if self.options.enable_price_tracking:
            self.price_oracle = PriceOracle()
            self.log.info("✓ Price oracle initialized (inline implementation)")
            self.log.info(f"  Base price: $60,000")
            self.log.info(f"  Max divergence: ±20%\n")

        self.partition_nodes_by_version()
        self.verify_common_history()

        # Main mining loop
        start_time = time()
        self.log.info(f"\n{'='*70}")
        self.log.info(f"Starting partition mining...")
        self.log.info(f"{'='*70}\n")

        while time() - start_time < self.options.duration:
            rand_val = random() * 100.0

            if rand_val < self.v27_hashrate_total:
                partition = 'v27'
                nodes = self.v27_nodes
                pools = self.v27_pools
            else:
                partition = 'v26'
                nodes = self.v26_nodes
                pools = self.v26_pools

            if not nodes:
                sleep(self.options.interval)
                continue

            miner = self.select_miner_in_partition(nodes, pools)

            try:
                miner_wallet = Commander.ensure_miner(miner)
                address = miner_wallet.getnewaddress()
                self.generatetoaddress(miner, 1, address, sync_fun=self.no_op)

                self.blocks_mined[partition] += 1

                v27_height = self.v27_nodes[0].getblockcount() if self.v27_nodes else 0
                v26_height = self.v26_nodes[0].getblockcount() if self.v26_nodes else 0
                fork_depth = v27_height + v26_height - (2 * self.options.start_height)

                elapsed = int(time() - start_time)

                # Update prices if enabled
                price_info = ""
                if self.price_oracle:
                    v27_price, v26_price = self.price_oracle.update_prices_from_state(
                        v27_height=v27_height,
                        v26_height=v26_height,
                        v27_economic_pct=self.options.v27_economic,
                        v26_economic_pct=self.options.v26_economic,
                        v27_hashrate_pct=self.v27_hashrate_total,
                        v26_hashrate_pct=self.v26_hashrate_total,
                        common_ancestor_height=self.options.start_height,
                        metadata={'elapsed_sec': elapsed, 'partition': partition}
                    )
                    price_ratio = v27_price / v26_price if v26_price > 0 else 1.0

                    # Add fork sustained indicator
                    sustained_marker = " [SUSTAINED]" if self.price_oracle.fork_sustained else " [natural split]"
                    price_info = f" | Prices: v27=${v27_price:,.0f} v26=${v26_price:,.0f} (ratio={price_ratio:.4f}){sustained_marker}"

                pool_name = f'node-{miner.index}'

                self.log.info(
                    f"[{elapsed:4d}s] {partition} block by {pool_name:15s} | "
                    f"Heights: v27={v27_height:3d} v26={v26_height:3d} | "
                    f"Fork depth: {fork_depth:3d} | "
                    f"Mined: v27={self.blocks_mined['v27']:3d} v26={self.blocks_mined['v26']:3d}"
                    f"{price_info}"
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
        self.log.info(f"v27 blocks mined: {self.blocks_mined['v27']}")
        self.log.info(f"v26 blocks mined: {self.blocks_mined['v26']}")
        self.log.info(f"Total blocks: {total_blocks}")

        # Price oracle summary
        if self.price_oracle:
            self.log.info("")
            self.price_oracle.print_summary()

            output_path = '/tmp/partition_miner_price_history.json'
            try:
                self.price_oracle.export_to_json(output_path)
                self.log.info(f"✓ Price history exported to: {output_path}")
            except Exception as e:
                self.log.error(f"Error exporting price history: {e}")

        self.log.info(f"{'='*70}\n")


def main():
    """Entry point for partition mining scenario"""
    PartitionMiner().main()


if __name__ == "__main__":
    main()
