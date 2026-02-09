#!/usr/bin/env python3

"""
Partition Mining Scenario for Systematic Fork Testing

This scenario enables testing version-segregated networks where:
1. Two isolated partitions (v27 and v26) mine independently
2. Mining is distributed according to configured hashrate percentages
3. NO fork choice logic - each partition builds its own chain
4. Pools within each partition use hashrate-weighted selection

Designed for systematic testing of economic weight vs hashrate conflicts.
"""

from time import sleep, time
from random import random, choices
import logging
import argparse
import asyncio
import yaml
from pathlib import Path

from commander import Commander
from price_oracle import PriceOracle, load_price_oracle_from_config


class PartitionMiner(Commander):
    """
    Partition-based mining scenario for systematic fork testing.

    Mines blocks on two isolated partitions simultaneously, respecting
    configured hashrate distributions.
    """

    def set_test_params(self):
        """Initialize test parameters and instance variables"""
        self.num_nodes = 0  # Using warnet-provided nodes
        self.v27_nodes = []
        self.v26_nodes = []
        self.v27_pools = {}  # {node: hashrate_percent}
        self.v26_pools = {}  # {node: hashrate_percent}
        self.v27_hashrate_total = 0.0
        self.v26_hashrate_total = 0.0
        self.blocks_mined = {'v27': 0, 'v26': 0}
        self.price_oracle = None  # Will be initialized if price tracking enabled

    def add_options(self, parser: argparse.ArgumentParser):
        """Add command-line arguments"""
        parser.add_argument(
            '--v27-hashrate',
            type=float,
            required=True,
            help='Percentage of total hashrate on v27 partition (0-100)'
        )
        parser.add_argument(
            '--v26-hashrate',
            type=float,
            default=None,
            help='Percentage of total hashrate on v26 partition (0-100). If not specified, calculated as 100 - v27_hashrate'
        )
        parser.add_argument(
            '--v27-economic',
            type=float,
            default=50.0,
            help='Percentage of economic weight on v27 partition (0-100, default: 50)'
        )
        parser.add_argument(
            '--v26-economic',
            type=float,
            default=None,
            help='Percentage of economic weight on v26 partition (0-100). If not specified, calculated as 100 - v27_economic'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Average seconds between blocks (default: 10)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=1800,
            help='Total mining duration in seconds (default: 1800 = 30 minutes)'
        )
        parser.add_argument(
            '--start-height',
            type=int,
            default=101,
            help='Expected common history height before partition (default: 101)'
        )
        parser.add_argument(
            '--enable-price-tracking',
            action='store_true',
            help='Enable token price tracking with economic model'
        )
        parser.add_argument(
            '--price-config',
            type=str,
            default='price_model_config.yaml',
            help='Path to price model configuration file (default: price_model_config.yaml)'
        )

    def load_price_oracle(self):
        """Initialize price oracle if price tracking is enabled"""
        if not self.options.enable_price_tracking:
            self.log.info("Price tracking disabled")
            return

        try:
            # Load configuration from file
            config_path = Path(__file__).parent / self.options.price_config
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                price_config = config.get('price_model', {})

                if price_config.get('enabled', False):
                    self.price_oracle = load_price_oracle_from_config(price_config)
                    self.log.info("✓ Price oracle initialized")
                    self.log.info(f"  Base price: ${self.price_oracle.base_price:,.0f}")
                    self.log.info(f"  Max divergence: ±{self.price_oracle.max_divergence * 100:.0f}%")
                    self.log.info(f"  Coefficients: chain={self.price_oracle.chain_weight_coef:.2f}, "
                                  f"econ={self.price_oracle.economic_weight_coef:.2f}, "
                                  f"hash={self.price_oracle.hashrate_weight_coef:.2f}")
                else:
                    self.log.warning("Price model disabled in config file")
            else:
                # No config file, use defaults
                self.price_oracle = PriceOracle()
                self.log.info("✓ Price oracle initialized (default config)")

        except Exception as e:
            self.log.warning(f"Could not initialize price oracle: {e}")
            self.log.warning("Continuing without price tracking")

    def partition_nodes_by_version(self):
        """Separate nodes into v27 and v26 partitions based on version"""
        self.log.info("Partitioning nodes by version...")

        for node in self.nodes:
            try:
                # Get node version from RPC
                network_info = node.getnetworkinfo()
                version_string = network_info.get('subversion', '')

                # Parse version (e.g., "/Satoshi:27.0.0/" or "/Satoshi:26.0.0/")
                is_v27 = '27.' in version_string or ':27.' in version_string
                is_v26 = '26.' in version_string or ':26.' in version_string

                if is_v27:
                    self.v27_nodes.append(node)
                    # Check for pool metadata
                    if hasattr(node, 'metadata') and isinstance(node.metadata, dict):
                        if 'hashrate_pct' in node.metadata:
                            self.v27_pools[node] = node.metadata['hashrate_pct']
                            self.log.info(f"  v27 pool: {node.index} ({node.metadata.get('pool_name', 'Unknown')}) - {node.metadata['hashrate_pct']}%")
                elif is_v26:
                    self.v26_nodes.append(node)
                    # Check for pool metadata
                    if hasattr(node, 'metadata') and isinstance(node.metadata, dict):
                        if 'hashrate_pct' in node.metadata:
                            self.v26_pools[node] = node.metadata['hashrate_pct']
                            self.log.info(f"  v26 pool: {node.index} ({node.metadata.get('pool_name', 'Unknown')}) - {node.metadata['hashrate_pct']}%")
                else:
                    self.log.warning(f"  Node {node.index} version unclear: {version_string}")

            except Exception as e:
                self.log.error(f"  Error querying node {node.index}: {e}")

        self.log.info(f"\nPartition summary:")
        self.log.info(f"  v27 nodes: {len(self.v27_nodes)} ({len(self.v27_pools)} with pool metadata)")
        self.log.info(f"  v26 nodes: {len(self.v26_nodes)} ({len(self.v26_pools)} with pool metadata)")

        if not self.v27_nodes and not self.v26_nodes:
            raise RuntimeError("Error: Could not find any nodes!")

        if not self.v27_nodes:
            self.log.warning(f"WARNING: No v27 nodes found - mining only on v26 partition")
        if not self.v26_nodes:
            self.log.warning(f"WARNING: No v26 nodes found - mining only on v27 partition")

    def select_miner_in_partition(self, nodes, pools_dict):
        """
        Select a miner within a partition using hashrate-weighted random selection.

        Args:
            nodes: List of all nodes in partition
            pools_dict: {node: hashrate_percent} for pool nodes with metadata

        Returns:
            Selected node to mine the next block
        """
        if not pools_dict:
            # No pool metadata, select randomly from all nodes
            return choices(nodes, k=1)[0]

        # Weighted random selection based on pool hashrate
        pool_nodes = list(pools_dict.keys())
        hashrates = list(pools_dict.values())

        return choices(pool_nodes, weights=hashrates, k=1)[0]

    def verify_common_history(self):
        """Verify that all nodes share common history up to start_height"""
        self.log.info(f"\nVerifying common history (blocks 0-{self.options.start_height})...")

        heights = []
        hashes = []

        for node in self.nodes:
            try:
                height = node.getblockcount()
                heights.append(height)

                if height >= self.options.start_height:
                    block_hash = node.getblockhash(self.options.start_height)
                    hashes.append(block_hash)
            except Exception as e:
                self.log.warning(f"  Error querying node {node.index}: {e}")

        # Check if all nodes are at or past start_height
        min_height = min(heights) if heights else 0
        max_height = max(heights) if heights else 0

        self.log.info(f"  Height range: {min_height} - {max_height}")

        if min_height < self.options.start_height:
            self.log.warning(f"  WARNING: Some nodes below start height {self.options.start_height}")
            self.log.warning(f"  Consider waiting or regenerating common history")

        # Check if all have same hash at start_height
        if hashes:
            unique_hashes = set(hashes)
            if len(unique_hashes) == 1:
                self.log.info(f"  ✓ All nodes share common hash at height {self.options.start_height}")
            else:
                self.log.warning(f"  WARNING: Found {len(unique_hashes)} different hashes at height {self.options.start_height}")
                self.log.warning(f"  Fork may already exist before partition mining!")

    def run_test(self):
        """Main mining loop - alternate between partitions with hashrate weighting"""

        # Calculate v26 hashrate if not specified
        if self.options.v26_hashrate is None:
            self.options.v26_hashrate = 100.0 - self.options.v27_hashrate

        # Calculate v26 economic weight if not specified
        if self.options.v26_economic is None:
            self.options.v26_economic = 100.0 - self.options.v27_economic

        self.v27_hashrate_total = self.options.v27_hashrate
        self.v26_hashrate_total = self.options.v26_hashrate

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining Scenario")
        self.log.info(f"{'='*70}")
        self.log.info(f"v27 partition hashrate: {self.v27_hashrate_total}%")
        self.log.info(f"v26 partition hashrate: {self.v26_hashrate_total}%")
        self.log.info(f"v27 partition economic: {self.options.v27_economic}%")
        self.log.info(f"v26 partition economic: {self.options.v26_economic}%")
        self.log.info(f"Block interval: {self.options.interval}s")
        self.log.info(f"Duration: {self.options.duration}s ({self.options.duration // 60} minutes)")
        self.log.info(f"{'='*70}\n")

        # Initialize price oracle if enabled
        self.load_price_oracle()

        # Partition nodes
        self.partition_nodes_by_version()

        # Verify common history
        self.verify_common_history()

        # Main mining loop
        start_time = time()
        self.log.info(f"\n{'='*70}")
        self.log.info(f"Starting partition mining...")
        self.log.info(f"{'='*70}\n")

        while time() - start_time < self.options.duration:
            # Decide which partition mines this block (weighted random)
            rand_val = random() * 100.0  # 0-100

            if rand_val < self.v27_hashrate_total:
                # v27 partition mines (if it has nodes)
                partition = 'v27'
                nodes = self.v27_nodes
                pools = self.v27_pools
            else:
                # v26 partition mines (if it has nodes)
                partition = 'v26'
                nodes = self.v26_nodes
                pools = self.v26_pools

            # Skip if partition is empty
            if not nodes:
                sleep(self.options.interval)
                continue

            # Select miner within partition
            miner = self.select_miner_in_partition(nodes, pools)

            # Mine block
            try:
                # Ensure miner wallet initialized
                miner_wallet = Commander.ensure_miner(miner)
                address = miner_wallet.getnewaddress()

                # Generate block using Commander wrapper (adds invalid_call=False)
                self.generatetoaddress(miner, 1, address, sync_fun=self.no_op)

                self.blocks_mined[partition] += 1

                # Get current heights
                v27_height = self.v27_nodes[0].getblockcount() if self.v27_nodes else 0
                v26_height = self.v26_nodes[0].getblockcount() if self.v26_nodes else 0
                fork_depth = v27_height + v26_height - (2 * self.options.start_height)

                elapsed = int(time() - start_time)

                # Update prices if price oracle is enabled
                price_info = ""
                if self.price_oracle:
                    v27_price, v26_price = self.price_oracle.update_prices_from_state(
                        v27_height=v27_height,
                        v26_height=v26_height,
                        v27_economic_pct=self.options.v27_economic,
                        v26_economic_pct=self.options.v26_economic,
                        v27_hashrate_pct=self.v27_hashrate_total,
                        v26_hashrate_pct=self.v26_hashrate_total,
                        metadata={'elapsed_sec': elapsed, 'partition': partition}
                    )
                    price_ratio = v27_price / v26_price if v26_price > 0 else 1.0
                    price_info = f" | Prices: v27=${v27_price:,.0f} v26=${v26_price:,.0f} (ratio={price_ratio:.4f})"

                # Don't access miner.metadata - it's an RPC proxy, not a dict
                # Just use the node index for logging
                pool_name = f'node-{miner.index}'

                self.log.info(
                    f"[{elapsed:4d}s] {partition} block by {pool_name:15s} | "
                    f"Heights: v27={v27_height:3d} v26={v26_height:3d} | "
                    f"Fork depth: {fork_depth:3d} | "
                    f"Mined: v27={self.blocks_mined['v27']:3d} v26={self.blocks_mined['v26']:3d}"
                    f"{price_info}"
                )

            except Exception as e:
                self.log.error(f"Error mining block on {partition} partition (node {miner.index}): {e}")

            # Wait for next block interval
            sleep(self.options.interval)

        # Final summary
        elapsed_min = (time() - start_time) / 60.0
        total_blocks = self.blocks_mined['v27'] + self.blocks_mined['v26']
        blocks_per_min = total_blocks / elapsed_min if elapsed_min > 0 else 0

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining Complete")
        self.log.info(f"{'='*70}")
        self.log.info(f"Duration: {elapsed_min:.2f} minutes")

        if total_blocks > 0:
            self.log.info(f"v27 blocks mined: {self.blocks_mined['v27']} ({self.blocks_mined['v27']/total_blocks*100:.1f}%)")
            self.log.info(f"v26 blocks mined: {self.blocks_mined['v26']} ({self.blocks_mined['v26']/total_blocks*100:.1f}%)")
            self.log.info(f"Total blocks: {total_blocks} ({blocks_per_min:.2f} blocks/min)")
        else:
            self.log.warning(f"WARNING: No blocks were mined!")
            self.log.info(f"v27 blocks mined: 0")
            self.log.info(f"v26 blocks mined: 0")
            self.log.info(f"Total blocks: 0")

        # Get final heights
        try:
            v27_final = self.v27_nodes[0].getblockcount()
            v26_final = self.v26_nodes[0].getblockcount()
            final_fork_depth = v27_final + v26_final - (2 * self.options.start_height)

            self.log.info(f"\nFinal chain heights:")
            self.log.info(f"  v27: {v27_final}")
            self.log.info(f"  v26: {v26_final}")
            self.log.info(f"  Fork depth: {final_fork_depth}")
            self.log.info(f"  Height ratio: {v27_final/v26_final:.3f} (v27/v26)" if v26_final > 0 else "")
        except Exception as e:
            self.log.error(f"Error getting final heights: {e}")

        # Price oracle summary and export
        if self.price_oracle:
            self.log.info("")
            self.price_oracle.print_summary()

            # Export price history
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
