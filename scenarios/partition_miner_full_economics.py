#!/usr/bin/env python3

"""
Partition Mining Scenario with Full Economic Model (Phase 1-2 Integration)

Includes:
- Price tracking (Phase 1)
- Fee market dynamics (Phase 2)
- Manipulation detection
- Portfolio economics
- Miner profitability

This is a standalone test version with inline implementations.
"""

from time import sleep, time
from random import random, choices
import logging
import argparse
import json
from typing import Dict, List, Tuple, Optional
from threading import Lock

from commander import Commander


# ============================================================================
# PRICE ORACLE (Phase 1)
# ============================================================================

class PriceOracle:
    """Price oracle for tracking fork prices based on weighted factors"""

    def __init__(
        self,
        base_price: float = 60000,
        max_divergence: float = 0.20,
        chain_weight_coef: float = 0.3,
        economic_weight_coef: float = 0.5,
        hashrate_weight_coef: float = 0.2
    ):
        self.base_price = base_price
        self.max_divergence = max_divergence
        self.chain_weight_coef = chain_weight_coef
        self.economic_weight_coef = economic_weight_coef
        self.hashrate_weight_coef = hashrate_weight_coef

        self.prices = {'v27': base_price, 'v26': base_price}
        self.history = []
        self.lock = Lock()

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

    def update_price(
        self,
        chain_id: str,
        chain_weight: float,
        economic_weight: float,
        hashrate_weight: float,
        metadata: Optional[Dict] = None
    ) -> float:
        """Update price for a specific chain"""
        with self.lock:
            chain_factor = 0.8 + (chain_weight * 0.4)
            economic_factor = 0.8 + (economic_weight * 0.4)
            hashrate_factor = 0.8 + (hashrate_weight * 0.4)

            combined_factor = (
                chain_factor * self.chain_weight_coef +
                economic_factor * self.economic_weight_coef +
                hashrate_factor * self.hashrate_weight_coef
            )

            new_price = self.base_price * combined_factor
            min_price = self.base_price * (1 - self.max_divergence)
            max_price = self.base_price * (1 + self.max_divergence)
            new_price = max(min_price, min(max_price, new_price))

            self.prices[chain_id] = new_price
            self.history.append({
                'timestamp': time(),
                'chain_id': chain_id,
                'price': new_price,
                'metadata': metadata or {}
            })

            return new_price

    def get_price(self, chain_id: str) -> float:
        """Get current price for a chain"""
        with self.lock:
            return self.prices.get(chain_id, self.base_price)


# ============================================================================
# FEE ORACLE (Phase 2)
# ============================================================================

class FeeOracle:
    """Fee market oracle with manipulation detection and portfolio tracking"""

    def __init__(
        self,
        base_fee_rate: float = 2.0,
        min_fee_rate: float = 1.0,
        max_fee_rate: float = 500.0,
        block_target_interval: int = 600
    ):
        self.base_fee_rate = base_fee_rate
        self.min_fee_rate = min_fee_rate
        self.max_fee_rate = max_fee_rate
        self.block_target_interval = block_target_interval

        # Fee state
        self.fees = {}  # {chain_id: current_fee_sat_per_vb}
        self.organic_fees = {}  # Calculated organic fee
        self.manipulation_premiums = {}  # Artificial inflation
        self.last_block_time = {}  # Track block production

        # Actor portfolios (dual-token holdings)
        self.actors = {}  # {actor_id: {v27_holdings, v26_holdings, costs, etc}}

        # History
        self.fee_history = []
        self.portfolio_snapshots = []
        self.miner_profitability = []

        self.lock = Lock()

    def initialize_actor(
        self,
        actor_id: str,
        initial_holdings_btc: float,
        initial_price_usd: float = 60000.0
    ):
        """Initialize an economic actor with dual-token portfolio"""
        with self.lock:
            self.actors[actor_id] = {
                'v27_holdings_btc': initial_holdings_btc,
                'v26_holdings_btc': initial_holdings_btc,
                'initial_value_usd': 2 * initial_holdings_btc * initial_price_usd,
                'cumulative_costs_usd': 0.0,
                'cumulative_earnings_usd': 0.0,
                'manipulation_events': []
            }

    def calculate_organic_fee(
        self,
        chain_id: str,
        block_production_rate: float,
        economic_activity: float,
        mempool_pressure: float = 1.0
    ) -> float:
        """Calculate organic fee based on network conditions"""
        # Base fee adjusted for block production (slower blocks = higher fees)
        target_rate = 1.0 / self.block_target_interval  # blocks per second
        production_factor = min(3.0, max(0.5, target_rate / block_production_rate))

        # Economic activity factor (more activity = more txs = higher fees)
        activity_factor = 0.8 + (economic_activity * 0.4)

        # Mempool pressure (normalized)
        pressure_factor = mempool_pressure

        organic_fee = (
            self.base_fee_rate *
            production_factor *
            activity_factor *
            pressure_factor
        )

        return max(self.min_fee_rate, min(self.max_fee_rate, organic_fee))

    def update_fee(
        self,
        chain_id: str,
        block_production_rate: float,
        economic_activity: float,
        mempool_pressure: float = 1.0,
        manipulation_premium: float = 0.0
    ) -> float:
        """Update fee for a chain"""
        with self.lock:
            organic = self.calculate_organic_fee(
                chain_id,
                block_production_rate,
                economic_activity,
                mempool_pressure
            )

            total_fee = organic + manipulation_premium
            total_fee = max(self.min_fee_rate, min(self.max_fee_rate, total_fee))

            self.fees[chain_id] = total_fee
            self.organic_fees[chain_id] = organic
            self.manipulation_premiums[chain_id] = manipulation_premium

            self.fee_history.append({
                'timestamp': time(),
                'chain_id': chain_id,
                'total_fee_sat_per_vb': total_fee,
                'organic_fee': organic,
                'manipulation_premium': manipulation_premium
            })

            return total_fee

    def apply_manipulation(
        self,
        chain_id: str,
        actor_id: str,
        btc_spent: float,
        price_usd: float
    ):
        """Apply fee market manipulation (spend BTC on artificial fees)"""
        with self.lock:
            if actor_id not in self.actors:
                raise ValueError(f"Actor {actor_id} not initialized")

            actor = self.actors[actor_id]
            cost_usd = btc_spent * price_usd

            # Deduct from holdings on the manipulated chain
            if chain_id == 'v27':
                if actor['v27_holdings_btc'] < btc_spent:
                    raise ValueError(f"Insufficient v27 holdings")
                actor['v27_holdings_btc'] -= btc_spent
            else:
                if actor['v26_holdings_btc'] < btc_spent:
                    raise ValueError(f"Insufficient v26 holdings")
                actor['v26_holdings_btc'] -= btc_spent

            actor['cumulative_costs_usd'] += cost_usd

            # Record event
            actor['manipulation_events'].append({
                'timestamp': time(),
                'chain_id': chain_id,
                'btc_spent': btc_spent,
                'price_usd': price_usd,
                'cost_usd': cost_usd
            })

    def calculate_manipulation_sustainability(
        self,
        chain_id: str,
        price_oracle,
        actor_id: str = "manipulator"
    ) -> Dict:
        """Calculate whether fee manipulation is economically sustainable"""
        with self.lock:
            if actor_id not in self.actors:
                return {'sustainable': False, 'error': 'Actor not initialized'}

            actor = self.actors[actor_id]

            # Get current prices
            v27_price = price_oracle.get_price('v27')
            v26_price = price_oracle.get_price('v26')

            # Calculate current total portfolio value (BOTH forks)
            current_v27_value = actor['v27_holdings_btc'] * v27_price
            current_v26_value = actor['v26_holdings_btc'] * v26_price
            current_total_value = current_v27_value + current_v26_value

            # Net position
            initial_value = actor['initial_value_usd']
            costs = actor['cumulative_costs_usd']
            net_position = current_total_value - initial_value - costs

            # Portfolio appreciation
            portfolio_appreciation = current_total_value - initial_value

            # Sustainability ratio
            if costs > 0:
                sustainability_ratio = portfolio_appreciation / costs
            else:
                sustainability_ratio = float('inf') if portfolio_appreciation > 0 else 1.0

            # Sustainable if portfolio appreciation > costs
            sustainable = sustainability_ratio > 1.0

            return {
                'sustainable': sustainable,
                'sustainability_ratio': sustainability_ratio,
                'current_portfolio_value_usd': current_total_value,
                'initial_value_usd': initial_value,
                'portfolio_appreciation_usd': portfolio_appreciation,
                'cumulative_costs_usd': costs,
                'net_position_usd': net_position,
                'v27_holdings_btc': actor['v27_holdings_btc'],
                'v26_holdings_btc': actor['v26_holdings_btc'],
                'v27_value_usd': current_v27_value,
                'v26_value_usd': current_v26_value,
                'manipulation_events_count': len(actor['manipulation_events'])
            }

    def calculate_miner_profitability(
        self,
        chain_id: str,
        block_subsidy: float,
        current_price: float,
        hashrate_cost_usd: float = 100000.0
    ) -> Dict:
        """Calculate miner profitability in USD terms"""
        with self.lock:
            current_fee_rate = self.fees.get(chain_id, self.base_fee_rate)
            vbytes_per_block = 1_000_000
            fee_btc = (current_fee_rate * vbytes_per_block) / 100_000_000

            total_reward_btc = block_subsidy + fee_btc
            revenue_usd = total_reward_btc * current_price
            profit_usd = revenue_usd - hashrate_cost_usd
            profit_margin = (profit_usd / hashrate_cost_usd * 100) if hashrate_cost_usd > 0 else 0

            result = {
                'timestamp': time(),
                'chain_id': chain_id,
                'block_subsidy_btc': block_subsidy,
                'fee_btc': fee_btc,
                'total_reward_btc': total_reward_btc,
                'price_usd': current_price,
                'revenue_usd': revenue_usd,
                'cost_usd': hashrate_cost_usd,
                'profit_usd': profit_usd,
                'profit_margin_pct': profit_margin,
                'profitable': profit_usd > 0
            }

            self.miner_profitability.append(result)
            return result

    def record_portfolio_snapshot(
        self,
        actor_id: str,
        price_oracle,
        metadata: Optional[Dict] = None
    ):
        """Record a portfolio snapshot for an actor"""
        with self.lock:
            if actor_id not in self.actors:
                return

            actor = self.actors[actor_id]
            v27_price = price_oracle.get_price('v27')
            v26_price = price_oracle.get_price('v26')

            snapshot = {
                'timestamp': time(),
                'actor_id': actor_id,
                'v27_holdings_btc': actor['v27_holdings_btc'],
                'v26_holdings_btc': actor['v26_holdings_btc'],
                'v27_price_usd': v27_price,
                'v26_price_usd': v26_price,
                'v27_value_usd': actor['v27_holdings_btc'] * v27_price,
                'v26_value_usd': actor['v26_holdings_btc'] * v26_price,
                'total_value_usd': (actor['v27_holdings_btc'] * v27_price +
                                    actor['v26_holdings_btc'] * v26_price),
                'cumulative_costs_usd': actor['cumulative_costs_usd'],
                'net_profit_usd': (actor['v27_holdings_btc'] * v27_price +
                                   actor['v26_holdings_btc'] * v26_price -
                                   actor['initial_value_usd'] -
                                   actor['cumulative_costs_usd']),
                'metadata': metadata or {}
            }

            self.portfolio_snapshots.append(snapshot)

    def get_fee(self, chain_id: str) -> float:
        """Get current fee for a chain"""
        with self.lock:
            return self.fees.get(chain_id, self.base_fee_rate)


# ============================================================================
# PARTITION MINER WITH FULL ECONOMICS
# ============================================================================

class PartitionMinerFullEconomics(Commander):
    """Partition mining with price and fee tracking"""

    def set_test_params(self):
        """Initialize test parameters"""
        self.num_nodes = 0
        self.v27_nodes = []
        self.v26_nodes = []
        self.v27_pools = {}
        self.v26_pools = {}
        self.v27_hashrate_total = 0.0
        self.v26_hashrate_total = 0.0
        self.blocks_mined = {'v27': 0, 'v26': 0}
        self.last_block_time = {'v27': time(), 'v26': time()}
        self.price_oracle = None
        self.fee_oracle = None

    def add_options(self, parser: argparse.ArgumentParser):
        """Add command-line arguments"""
        parser.add_argument('--v27-hashrate', type=float, required=True)
        parser.add_argument('--v26-hashrate', type=float, default=None)
        parser.add_argument('--v27-economic', type=float, default=50.0)
        parser.add_argument('--v26-economic', type=float, default=None)
        parser.add_argument('--interval', type=int, default=10)
        parser.add_argument('--duration', type=int, default=1800)
        parser.add_argument('--start-height', type=int, default=101)

        # Economic model options
        parser.add_argument('--enable-price-tracking', action='store_true')
        parser.add_argument('--enable-fee-tracking', action='store_true')
        parser.add_argument('--enable-manipulation', action='store_true')
        parser.add_argument('--manipulation-chain', type=str, default='v26')
        parser.add_argument('--manipulation-budget-btc', type=float, default=1.0)
        parser.add_argument('--manipulation-interval', type=int, default=600)

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
        """Select a miner using hashrate-weighted random selection"""
        if not pools_dict:
            return choices(nodes, k=1)[0]

        pool_nodes = list(pools_dict.keys())
        hashrates = list(pools_dict.values())
        return choices(pool_nodes, weights=hashrates, k=1)[0]

    def run_test(self):
        """Main mining loop with full economic tracking"""

        # Calculate complementary values
        if self.options.v26_hashrate is None:
            self.options.v26_hashrate = 100.0 - self.options.v27_hashrate
        if self.options.v26_economic is None:
            self.options.v26_economic = 100.0 - self.options.v27_economic

        self.v27_hashrate_total = self.options.v27_hashrate
        self.v26_hashrate_total = self.options.v26_hashrate

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining with Full Economic Model")
        self.log.info(f"{'='*70}")
        self.log.info(f"v27 hashrate: {self.v27_hashrate_total}% | economic: {self.options.v27_economic}%")
        self.log.info(f"v26 hashrate: {self.v26_hashrate_total}% | economic: {self.options.v26_economic}%")
        self.log.info(f"Duration: {self.options.duration}s ({self.options.duration/60:.1f} min)")

        if self.options.enable_manipulation:
            self.log.info(f"Manipulation: {self.options.manipulation_chain} "
                         f"({self.options.manipulation_budget_btc} BTC every "
                         f"{self.options.manipulation_interval}s)")
        self.log.info(f"{'='*70}\n")

        # Initialize oracles
        if self.options.enable_price_tracking:
            self.price_oracle = PriceOracle()
            self.log.info("✓ Price oracle initialized")

        if self.options.enable_fee_tracking:
            self.fee_oracle = FeeOracle()
            self.log.info("✓ Fee oracle initialized")

            # Initialize manipulator if enabled
            if self.options.enable_manipulation:
                self.fee_oracle.initialize_actor(
                    "manipulator",
                    initial_holdings_btc=100000.0,
                    initial_price_usd=60000.0
                )
                self.log.info("✓ Manipulator initialized (100k BTC on each fork)\n")

        self.partition_nodes_by_version()

        # Main mining loop
        start_time = time()
        last_manipulation_time = start_time
        last_snapshot_time = start_time

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Starting partition mining...")
        self.log.info(f"{'='*70}\n")

        while time() - start_time < self.options.duration:
            current_time = time()
            rand_val = random() * 100.0

            # Select partition
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
                # Mine block
                miner_wallet = Commander.ensure_miner(miner)
                address = miner_wallet.getnewaddress()
                self.generatetoaddress(miner, 1, address, sync_fun=self.no_op)

                self.blocks_mined[partition] += 1
                block_time = time()
                time_since_last = block_time - self.last_block_time[partition]
                self.last_block_time[partition] = block_time

                # Get heights
                v27_height = self.v27_nodes[0].getblockcount() if self.v27_nodes else 0
                v26_height = self.v26_nodes[0].getblockcount() if self.v26_nodes else 0
                fork_depth = v27_height + v26_height - (2 * self.options.start_height)

                elapsed = int(current_time - start_time)

                # Update prices
                v27_price = v26_price = 60000.0
                if self.price_oracle:
                    total_blocks = v27_height + v26_height
                    v27_chain_weight = v27_height / total_blocks if total_blocks > 0 else 0.5
                    v26_chain_weight = v26_height / total_blocks if total_blocks > 0 else 0.5

                    v27_price = self.price_oracle.update_price(
                        'v27', v27_chain_weight,
                        self.options.v27_economic / 100.0,
                        self.v27_hashrate_total / 100.0
                    )
                    v26_price = self.price_oracle.update_price(
                        'v26', v26_chain_weight,
                        self.options.v26_economic / 100.0,
                        self.v26_hashrate_total / 100.0
                    )

                # Update fees
                v27_fee = v26_fee = 2.0
                if self.fee_oracle:
                    # Calculate block production rates
                    v27_rate = 1.0 / 600.0  # Approximate
                    v26_rate = 1.0 / 600.0

                    # Update fees (organic only for now)
                    v27_fee = self.fee_oracle.update_fee(
                        'v27', v27_rate,
                        self.options.v27_economic / 100.0
                    )
                    v26_fee = self.fee_oracle.update_fee(
                        'v26', v26_rate,
                        self.options.v26_economic / 100.0
                    )

                    # Calculate miner profitability
                    v27_prof = self.fee_oracle.calculate_miner_profitability(
                        'v27', 3.125, v27_price
                    )
                    v26_prof = self.fee_oracle.calculate_miner_profitability(
                        'v26', 3.125, v26_price
                    )

                # Apply manipulation if enabled
                if (self.options.enable_manipulation and
                    self.fee_oracle and
                    current_time - last_manipulation_time >= self.options.manipulation_interval):

                    try:
                        chain = self.options.manipulation_chain
                        self.fee_oracle.apply_manipulation(
                            chain,
                            "manipulator",
                            self.options.manipulation_budget_btc,
                            v27_price if chain == 'v27' else v26_price
                        )

                        # Update fee with manipulation premium
                        premium = 100.0  # sat/vB
                        if chain == 'v27':
                            v27_fee = self.fee_oracle.update_fee(
                                'v27', v27_rate,
                                self.options.v27_economic / 100.0,
                                manipulation_premium=premium
                            )
                        else:
                            v26_fee = self.fee_oracle.update_fee(
                                'v26', v26_rate,
                                self.options.v26_economic / 100.0,
                                manipulation_premium=premium
                            )

                        last_manipulation_time = current_time

                    except Exception as e:
                        self.log.warning(f"Manipulation failed: {e}")

                # Portfolio snapshot every 10 minutes
                if (self.fee_oracle and
                    self.options.enable_manipulation and
                    current_time - last_snapshot_time >= 600):

                    self.fee_oracle.record_portfolio_snapshot(
                        "manipulator",
                        self.price_oracle,
                        {'elapsed_sec': elapsed}
                    )
                    last_snapshot_time = current_time

                # Log status
                price_info = f"Prices: v27=${v27_price:,.0f} v26=${v26_price:,.0f}"
                fee_info = f"Fees: v27={v27_fee:.1f} v26={v26_fee:.1f} sat/vB"

                self.log.info(
                    f"[{elapsed:4d}s] {partition} block | "
                    f"Heights: v27={v27_height:3d} v26={v26_height:3d} | "
                    f"{price_info} | {fee_info}"
                )

            except Exception as e:
                self.log.error(f"Error mining block: {e}")

            sleep(self.options.interval)

        # Final summary
        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining Complete")
        self.log.info(f"{'='*70}")
        self.log.info(f"Duration: {(time() - start_time)/60:.2f} minutes")
        self.log.info(f"v27 blocks: {self.blocks_mined['v27']}")
        self.log.info(f"v26 blocks: {self.blocks_mined['v26']}")

        # Price summary
        if self.price_oracle:
            v27_price = self.price_oracle.get_price('v27')
            v26_price = self.price_oracle.get_price('v26')
            self.log.info(f"\nFinal Prices:")
            self.log.info(f"  v27: ${v27_price:,.2f}")
            self.log.info(f"  v26: ${v26_price:,.2f}")
            self.log.info(f"  Divergence: {abs(v27_price/v26_price - 1.0)*100:.2f}%")

        # Fee summary
        if self.fee_oracle:
            v27_fee = self.fee_oracle.get_fee('v27')
            v26_fee = self.fee_oracle.get_fee('v26')
            self.log.info(f"\nFinal Fees:")
            self.log.info(f"  v27: {v27_fee:.2f} sat/vB")
            self.log.info(f"  v26: {v26_fee:.2f} sat/vB")

        # Manipulation sustainability
        if self.options.enable_manipulation and self.fee_oracle:
            sustain = self.fee_oracle.calculate_manipulation_sustainability(
                self.options.manipulation_chain,
                self.price_oracle
            )

            self.log.info(f"\nManipulation Sustainability:")
            self.log.info(f"  Sustainable: {'YES' if sustain['sustainable'] else 'NO'}")
            self.log.info(f"  Ratio: {sustain['sustainability_ratio']:.2f}x")
            self.log.info(f"  Portfolio value: ${sustain['current_portfolio_value_usd']:,.0f}")
            self.log.info(f"  Net position: ${sustain['net_position_usd']:,.0f}")
            self.log.info(f"  Costs: ${sustain['cumulative_costs_usd']:,.0f}")

        # Export results
        if self.price_oracle or self.fee_oracle:
            output_path = '/tmp/partition_full_economics.json'
            export_data = {}

            if self.price_oracle:
                export_data['price_history'] = self.price_oracle.history

            if self.fee_oracle:
                export_data['fee_history'] = self.fee_oracle.fee_history
                export_data['portfolio_snapshots'] = self.fee_oracle.portfolio_snapshots
                export_data['miner_profitability'] = self.fee_oracle.miner_profitability

            try:
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                self.log.info(f"\n✓ Results exported to: {output_path}")
            except Exception as e:
                self.log.error(f"Error exporting results: {e}")

        self.log.info(f"{'='*70}\n")


def main():
    """Entry point for partition mining with full economics"""
    PartitionMinerFullEconomics().main()


if __name__ == "__main__":
    main()
