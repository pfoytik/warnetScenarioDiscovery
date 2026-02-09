#!/usr/bin/env python3
"""
Fee Oracle - Fee Market Tracking for Fork Scenarios with Manipulation Detection

Tracks fee market dynamics for each fork including:
- Organic fee pressure from economic activity
- Artificial fee manipulation attempts
- Miner profitability (USD-based)
- Manipulation sustainability (dual-token portfolio economics)

Key Economic Principle:
    At fork time, all holders have EQUAL amounts of both tokens.
    Economic calculations must account for TOTAL PORTFOLIO VALUE across both forks.

Usage:
    from fee_oracle import FeeOracle

    fee_oracle = FeeOracle(base_fee_rate=1.0)
    fee_oracle.update_fees_from_state(
        v27_blocks_per_hour=6.0,
        v26_blocks_per_hour=4.0,
        v27_economic_pct=70,
        v26_economic_pct=30,
        price_oracle=price_oracle
    )
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class FeePoint:
    """Single fee observation at a point in time"""
    timestamp: float
    chain_id: str
    organic_fee: float  # sats/vbyte from natural demand
    manipulation_premium: float  # sats/vbyte from artificial inflation
    total_fee: float  # organic + manipulation
    metadata: Optional[Dict] = None


@dataclass
class PortfolioSnapshot:
    """Portfolio value snapshot for an economic actor"""
    timestamp: float
    actor_id: str  # e.g., "manipulator", "miner", "user"

    # Holdings on each fork
    v27_holdings_btc: float
    v26_holdings_btc: float

    # Current prices
    v27_price_usd: float
    v26_price_usd: float

    # Portfolio values
    v27_value_usd: float  # holdings * price
    v26_value_usd: float
    total_value_usd: float  # sum of both

    # Costs and profits
    cumulative_costs_usd: float  # Total spent on fees, etc.
    net_profit_usd: float  # total_value - initial_value - costs

    metadata: Optional[Dict] = None


class FeeOracle:
    """
    Tracks fee market dynamics with dual-token portfolio economics.

    Fee Model:
        total_fee = organic_fee + manipulation_premium

    Where:
        - organic_fee: Natural fee from transaction demand
        - manipulation_premium: Artificial inflation from attack

    Portfolio Economics:
        - All actors start with equal tokens on both forks
        - Manipulation costs reduce holdings on ONE fork
        - Total value includes holdings on BOTH forks
        - Profitability measured on TOTAL PORTFOLIO, not single fork
    """

    def __init__(
        self,
        base_fee_rate: float = 1.0,  # sats/vbyte baseline
        manipulation_detection: bool = True,
        sustainability_tracking: bool = True,
        storage_path: Optional[str] = None
    ):
        """
        Initialize fee oracle with portfolio tracking.

        Args:
            base_fee_rate: Baseline fee rate in sats/vbyte
            manipulation_detection: Track artificial fee inflation
            sustainability_tracking: Calculate manipulation sustainability
            storage_path: Path to store fee/portfolio history
        """
        self.base_fee_rate = base_fee_rate
        self.manipulation_detection = manipulation_detection
        self.sustainability_tracking = sustainability_tracking
        self.storage_path = Path(storage_path) if storage_path else None

        # Current fee rates (sats/vbyte)
        self.fees = {
            'v27': base_fee_rate,
            'v26': base_fee_rate
        }

        # Fee components
        self.organic_fees = {'v27': base_fee_rate, 'v26': base_fee_rate}
        self.manipulation_premium = {'v27': 0.0, 'v26': 0.0}

        # Manipulation tracking
        self.manipulation_active = {'v27': False, 'v26': False}
        self.manipulation_cost_btc = {'v27': 0.0, 'v26': 0.0}  # BTC spent
        self.manipulation_cost_usd = {'v27': 0.0, 'v26': 0.0}  # USD equivalent

        # History
        self.fee_history: List[FeePoint] = []
        self.portfolio_history: List[PortfolioSnapshot] = []

        # Economic actors (initialized when configured)
        self.actors: Dict[str, Dict] = {}  # actor_id -> {v27_holdings, v26_holdings, initial_value, ...}

        # Initialize with starting fees
        start_time = time.time()
        self.fee_history.append(FeePoint(
            start_time, 'v27', base_fee_rate, 0.0, base_fee_rate,
            {'initial': True}
        ))
        self.fee_history.append(FeePoint(
            start_time, 'v26', base_fee_rate, 0.0, base_fee_rate,
            {'initial': True}
        ))

    def initialize_actor(
        self,
        actor_id: str,
        initial_holdings_btc: float,
        initial_price_usd: float = 60000.0
    ):
        """
        Initialize an economic actor with dual-token portfolio.

        At fork time, actor has equal holdings on both forks.

        Args:
            actor_id: Identifier (e.g., "manipulator", "miner_pool_1")
            initial_holdings_btc: BTC held before fork
            initial_price_usd: Price at fork time (same for both initially)
        """
        self.actors[actor_id] = {
            'v27_holdings_btc': initial_holdings_btc,
            'v26_holdings_btc': initial_holdings_btc,
            'initial_value_usd': 2 * initial_holdings_btc * initial_price_usd,  # Both forks
            'cumulative_costs_usd': 0.0,
            'cumulative_earnings_usd': 0.0
        }

    def calculate_organic_fee(
        self,
        chain_id: str,
        blocks_per_hour: float,
        economic_activity_pct: float,
        mempool_pressure: float = 1.0,
        transactional_activity_pct: float = None
    ) -> float:
        """
        Calculate organic fee based on natural demand.

        Args:
            blocks_per_hour: Block production rate (6 = normal, lower = congestion)
            economic_activity_pct: Total economic activity concentration (0-100)
                Used for price support calculations.
            mempool_pressure: Additional congestion multiplier (1.0 = normal)
            transactional_activity_pct: Fee-generating activity concentration (0-100)
                If provided, this is used instead of economic_activity_pct for
                fee calculations. This represents only the portion of economic
                activity that generates transactions (exchanges, merchants),
                excluding custodial holdings (HODLers, cold storage).

        Returns:
            Organic fee rate in sats/vbyte

        Economic Insight:
            A fork with high custody but low transaction velocity will have:
            - High economic_activity_pct (price support from holdings)
            - Low transactional_activity_pct (few actual transactions)
            - Result: Lower fees, weaker miner incentive from fees

            A fork with high transaction velocity will have:
            - Potentially lower economic_activity_pct (less total value)
            - High transactional_activity_pct (lots of transactions)
            - Result: Higher fees, stronger miner incentive from fees
        """
        # Slower blocks → higher fees (inverse relationship)
        # Normal: 6 blocks/hour, if only 3 blocks/hour → 2x fee pressure
        block_factor = 6.0 / max(blocks_per_hour, 0.1)

        # Use transactional activity for fee calculation if provided
        # Otherwise fall back to total economic activity
        fee_activity = transactional_activity_pct if transactional_activity_pct is not None else economic_activity_pct

        # More transactional activity → more transactions → higher fees
        # Normalize to 50% baseline
        activity_factor = fee_activity / 50.0

        # Combined organic fee
        organic_fee = self.base_fee_rate * block_factor * activity_factor * mempool_pressure

        return organic_fee

    def apply_manipulation(
        self,
        chain_id: str,
        artificial_fee_spending_btc: float,  # BTC spent on artificial fees this period
        blocks_mined_this_period: int,  # Blocks mined to distribute fees across
        actor_id: str = "manipulator"
    ):
        """
        Apply fee market manipulation by spending BTC on artificial high-fee transactions.

        Args:
            chain_id: Which fork to manipulate
            artificial_fee_spending_btc: BTC to spend on fake txs
            blocks_mined_this_period: Blocks to spread fees across
            actor_id: Who is doing the manipulation
        """
        if artificial_fee_spending_btc <= 0 or blocks_mined_this_period <= 0:
            self.manipulation_active[chain_id] = False
            self.manipulation_premium[chain_id] = 0.0
            return

        # Calculate manipulation premium (additional fee rate created)
        # Assume each block is ~1 MB (1,000,000 vbytes)
        # Premium = (BTC spent) / (blocks * vbytes per block)
        vbytes_per_block = 1_000_000
        total_vbytes = blocks_mined_this_period * vbytes_per_block

        # Convert BTC to sats
        sats_spent = artificial_fee_spending_btc * 100_000_000

        # Premium in sats/vbyte
        premium = sats_spent / total_vbytes if total_vbytes > 0 else 0.0

        self.manipulation_premium[chain_id] = premium
        self.manipulation_active[chain_id] = True

        # Track cumulative costs (in BTC)
        self.manipulation_cost_btc[chain_id] += artificial_fee_spending_btc

        # Deduct from actor's holdings on this fork
        if actor_id in self.actors:
            holdings_key = f'{chain_id}_holdings_btc'
            self.actors[actor_id][holdings_key] -= artificial_fee_spending_btc

    def calculate_miner_profitability(
        self,
        chain_id: str,
        block_subsidy: float,  # BTC (e.g., 6.25)
        current_price: float,  # USD per BTC
        hashrate_cost_usd: float = 100000.0  # Cost to mine 1 block
    ) -> Dict:
        """
        Calculate miner profitability in USD terms.

        Miners care about USD value, not just BTC amount!

        Args:
            chain_id: Which fork
            block_subsidy: Fixed subsidy (6.25 BTC)
            current_price: Current token price for this fork
            hashrate_cost_usd: Cost to mine one block

        Returns:
            {
                'chain_id': str,
                'reward_btc': float,
                'fee_btc': float,
                'total_btc': float,
                'price_usd': float,
                'revenue_usd': float,
                'cost_usd': float,
                'profit_usd': float,
                'profit_margin_pct': float,
                'profitable': bool
            }
        """
        current_fee_rate = self.fees[chain_id]  # sats/vbyte

        # Estimate fee BTC per block
        # Assume full block: ~1 MB = 1,000,000 vbytes
        # Fee BTC = (fee_rate_sats/vbyte * vbytes) / 100,000,000
        vbytes_per_block = 1_000_000
        fee_btc = (current_fee_rate * vbytes_per_block) / 100_000_000

        total_reward_btc = block_subsidy + fee_btc
        revenue_usd = total_reward_btc * current_price
        profit_usd = revenue_usd - hashrate_cost_usd
        profit_margin = (profit_usd / hashrate_cost_usd * 100) if hashrate_cost_usd > 0 else 0

        return {
            'chain_id': chain_id,
            'reward_btc': block_subsidy,
            'fee_btc': fee_btc,
            'total_btc': total_reward_btc,
            'price_usd': current_price,
            'revenue_usd': revenue_usd,
            'cost_usd': hashrate_cost_usd,
            'profit_usd': profit_usd,
            'profit_margin_pct': profit_margin,
            'profitable': profit_usd > 0
        }

    def calculate_manipulation_sustainability(
        self,
        chain_id: str,
        price_oracle,  # PriceOracle instance
        actor_id: str = "manipulator"
    ) -> Dict:
        """
        Calculate whether fee manipulation is economically sustainable.

        KEY: Accounts for dual-token portfolio!

        Sustainability when:
            total_portfolio_value_if_successful > total_portfolio_value_if_abandoned + costs_spent

        Args:
            chain_id: Fork being manipulated
            price_oracle: PriceOracle to get current prices
            actor_id: Actor doing manipulation

        Returns:
            {
                'sustainable': bool,
                'current_portfolio_value_usd': float,
                'initial_portfolio_value_usd': float,
                'cumulative_costs_usd': float,
                'net_position_usd': float,  # current - initial - costs
                'sustainability_ratio': float,  # benefit/cost
                'recommendation': str
            }
        """
        if actor_id not in self.actors:
            return {
                'sustainable': False,
                'error': 'Actor not initialized'
            }

        actor = self.actors[actor_id]

        # Get current prices
        v27_price = price_oracle.get_price('v27')
        v26_price = price_oracle.get_price('v26')

        # Update manipulation cost in USD (at current price of manipulated chain)
        manipulated_price = v27_price if chain_id == 'v27' else v26_price
        self.manipulation_cost_usd[chain_id] = (
            self.manipulation_cost_btc[chain_id] * manipulated_price
        )
        actor['cumulative_costs_usd'] = self.manipulation_cost_usd[chain_id]

        # Calculate current total portfolio value (BOTH forks)
        current_v27_value = actor['v27_holdings_btc'] * v27_price
        current_v26_value = actor['v26_holdings_btc'] * v26_price
        current_total_value = current_v27_value + current_v26_value

        # Net position: current value - initial value - costs
        initial_value = actor['initial_value_usd']
        costs = actor['cumulative_costs_usd']
        net_position = current_total_value - initial_value - costs

        # Sustainability ratio
        # Benefit = current_total_value - initial_value (appreciation)
        # Cost = cumulative_costs_usd
        portfolio_appreciation = current_total_value - initial_value

        if costs > 0:
            sustainability_ratio = portfolio_appreciation / costs
        else:
            sustainability_ratio = float('inf') if portfolio_appreciation > 0 else 1.0

        # Sustainable if: portfolio appreciation > costs
        # (i.e., manipulation is maintaining/increasing total value despite spending)
        sustainable = sustainability_ratio > 1.0

        # Recommendation
        if sustainable:
            recommendation = "CONTINUE - Manipulation is maintaining portfolio value"
        elif sustainability_ratio > 0.5:
            recommendation = "WARNING - Approaching unsustainability"
        else:
            recommendation = "ABORT - Manipulation is destroying portfolio value"

        return {
            'sustainable': sustainable,
            'current_portfolio_value_usd': current_total_value,
            'initial_portfolio_value_usd': initial_value,
            'cumulative_costs_usd': costs,
            'net_position_usd': net_position,
            'portfolio_appreciation_usd': portfolio_appreciation,
            'sustainability_ratio': sustainability_ratio,
            'recommendation': recommendation,
            'holdings': {
                'v27_btc': actor['v27_holdings_btc'],
                'v26_btc': actor['v26_holdings_btc'],
                'v27_value_usd': current_v27_value,
                'v26_value_usd': current_v26_value
            }
        }

    def record_portfolio_snapshot(
        self,
        actor_id: str,
        price_oracle,
        metadata: Optional[Dict] = None
    ):
        """
        Record current portfolio state for an actor.

        Args:
            actor_id: Actor to snapshot
            price_oracle: PriceOracle for current prices
            metadata: Optional metadata
        """
        if actor_id not in self.actors:
            return

        actor = self.actors[actor_id]

        # Get current prices
        v27_price = price_oracle.get_price('v27')
        v26_price = price_oracle.get_price('v26')

        # Calculate values
        v27_value = actor['v27_holdings_btc'] * v27_price
        v26_value = actor['v26_holdings_btc'] * v26_price
        total_value = v27_value + v26_value

        # Net profit
        initial_value = actor['initial_value_usd']
        costs = actor['cumulative_costs_usd']
        net_profit = total_value - initial_value - costs

        snapshot = PortfolioSnapshot(
            timestamp=time.time(),
            actor_id=actor_id,
            v27_holdings_btc=actor['v27_holdings_btc'],
            v26_holdings_btc=actor['v26_holdings_btc'],
            v27_price_usd=v27_price,
            v26_price_usd=v26_price,
            v27_value_usd=v27_value,
            v26_value_usd=v26_value,
            total_value_usd=total_value,
            cumulative_costs_usd=costs,
            net_profit_usd=net_profit,
            metadata=metadata or {}
        )

        self.portfolio_history.append(snapshot)

    def update_fees_from_state(
        self,
        v27_blocks_per_hour: float,
        v26_blocks_per_hour: float,
        v27_economic_pct: float,
        v26_economic_pct: float,
        price_oracle,
        metadata: Optional[Dict] = None,
        difficulty_oracle=None,
        v27_hashrate_pct: float = 50.0,
        v26_hashrate_pct: float = 50.0,
        v27_transactional_pct: float = None,
        v26_transactional_pct: float = None,
    ) -> Tuple[float, float]:
        """
        Update fee rates for both forks based on current state.

        Args:
            v27_blocks_per_hour: v27 block production rate
            v26_blocks_per_hour: v26 block production rate
            v27_economic_pct: Total economic activity on v27 (0-100)
            v26_economic_pct: Total economic activity on v26 (0-100)
            price_oracle: PriceOracle instance
            metadata: Optional metadata
            difficulty_oracle: Optional DifficultyOracle instance. When provided,
                overrides blocks_per_hour with difficulty-derived values.
            v27_hashrate_pct: v27 hashrate percentage (used with difficulty_oracle)
            v26_hashrate_pct: v26 hashrate percentage (used with difficulty_oracle)
            v27_transactional_pct: Fee-generating activity on v27 (0-100)
                If provided, uses this for fee calculations instead of economic_pct.
                Represents exchanges, merchants, active users (not HODLers).
            v26_transactional_pct: Fee-generating activity on v26 (0-100)

        Returns:
            Tuple of (v27_fee, v26_fee) in sats/vbyte
        """
        # Override blocks_per_hour with difficulty-derived values if available
        if difficulty_oracle is not None:
            v27_blocks_per_hour = difficulty_oracle.get_blocks_per_hour('v27', v27_hashrate_pct)
            v26_blocks_per_hour = difficulty_oracle.get_blocks_per_hour('v26', v26_hashrate_pct)

        # Calculate organic fees using transactional activity if provided
        v27_organic = self.calculate_organic_fee(
            'v27',
            v27_blocks_per_hour,
            v27_economic_pct,
            transactional_activity_pct=v27_transactional_pct
        )

        v26_organic = self.calculate_organic_fee(
            'v26',
            v26_blocks_per_hour,
            v26_economic_pct,
            transactional_activity_pct=v26_transactional_pct
        )

        self.organic_fees['v27'] = v27_organic
        self.organic_fees['v26'] = v26_organic

        # Total fees = organic + manipulation
        v27_total = v27_organic + self.manipulation_premium['v27']
        v26_total = v26_organic + self.manipulation_premium['v26']

        self.fees['v27'] = v27_total
        self.fees['v26'] = v26_total

        # Record history
        timestamp = time.time()
        self.fee_history.append(FeePoint(
            timestamp, 'v27',
            v27_organic,
            self.manipulation_premium['v27'],
            v27_total,
            metadata
        ))
        self.fee_history.append(FeePoint(
            timestamp, 'v26',
            v26_organic,
            self.manipulation_premium['v26'],
            v26_total,
            metadata
        ))

        return v27_total, v26_total

    def get_fee(self, chain_id: str) -> float:
        """Get current total fee rate for a chain (sats/vbyte)"""
        return self.fees.get(chain_id, self.base_fee_rate)

    def get_organic_fee(self, chain_id: str) -> float:
        """Get current organic fee rate for a chain (sats/vbyte)"""
        return self.organic_fees.get(chain_id, self.base_fee_rate)

    def estimate_mempool_size(
        self,
        chain_id: str,
        blocks_per_hour: float,
        economic_activity_pct: float,
        base_tx_volume_mb_per_hour: float = 6.0  # ~1MB per block at normal rate
    ) -> Dict:
        """
        Estimate mempool size and congestion based on block rate and activity.

        Model assumptions:
        - Normal state: 6 blocks/hour, each ~1MB = 6 MB/hour throughput
        - Transaction volume scales with economic activity
        - Mempool grows when tx volume > throughput

        Args:
            chain_id: Fork identifier
            blocks_per_hour: Current block production rate
            economic_activity_pct: Economic activity on this fork (0-100)
            base_tx_volume_mb_per_hour: Baseline tx volume at 50% economic activity

        Returns:
            Dict with mempool estimates:
            - throughput_mb_per_hour: Block space being produced
            - tx_volume_mb_per_hour: Estimated transaction volume
            - congestion_ratio: tx_volume / throughput (>1 = backlog growing)
            - estimated_mempool_mb: Rough mempool size estimate
            - estimated_confirm_blocks: Blocks until confirmation at current fee
        """
        # Throughput = blocks/hour * ~1MB per block
        throughput_mb = blocks_per_hour * 1.0

        # Transaction volume scales with economic activity
        # At 50% activity, volume = base volume
        # More activity = more transactions
        activity_factor = economic_activity_pct / 50.0
        tx_volume_mb = base_tx_volume_mb_per_hour * activity_factor

        # Congestion ratio
        congestion_ratio = tx_volume_mb / max(throughput_mb, 0.1)

        # Mempool estimate (simplified model)
        # If congestion > 1, mempool grows; if < 1, mempool drains
        # Use fee as proxy for mempool pressure
        current_fee = self.get_fee(chain_id)
        base_fee = self.base_fee_rate

        # Higher fees indicate larger mempool backlog
        fee_pressure = current_fee / base_fee
        estimated_mempool_mb = max(0, (fee_pressure - 1) * 10)  # Rough estimate

        # Confirmation time estimate
        # At congestion_ratio=1, confirm in ~1 block
        # Higher congestion = more blocks to wait
        if congestion_ratio <= 1:
            estimated_confirm_blocks = 1
        else:
            # Each unit of congestion adds ~1-2 blocks wait
            estimated_confirm_blocks = int(1 + (congestion_ratio - 1) * 2)

        return {
            'chain_id': chain_id,
            'throughput_mb_per_hour': throughput_mb,
            'tx_volume_mb_per_hour': tx_volume_mb,
            'congestion_ratio': congestion_ratio,
            'estimated_mempool_mb': estimated_mempool_mb,
            'estimated_confirm_blocks': estimated_confirm_blocks,
            'fee_rate_sats_vb': current_fee
        }

    def get_fee_revenue_per_block(self, chain_id: str) -> float:
        """
        Calculate expected fee revenue per block in BTC.

        This represents the miner incentive from fees (separate from subsidy).

        Returns:
            Fee revenue in BTC per block
        """
        current_fee = self.get_fee(chain_id)  # sats/vbyte
        vbytes_per_block = 1_000_000  # ~1MB
        fee_sats = current_fee * vbytes_per_block
        fee_btc = fee_sats / 100_000_000
        return fee_btc

    def export_to_json(self, output_path: str):
        """Export fee and portfolio history to JSON"""
        export_data = {
            'config': {
                'base_fee_rate': self.base_fee_rate,
                'manipulation_detection': self.manipulation_detection,
                'sustainability_tracking': self.sustainability_tracking
            },
            'current_fees': {
                'v27': {
                    'total': self.fees['v27'],
                    'organic': self.organic_fees['v27'],
                    'manipulation': self.manipulation_premium['v27']
                },
                'v26': {
                    'total': self.fees['v26'],
                    'organic': self.organic_fees['v26'],
                    'manipulation': self.manipulation_premium['v26']
                }
            },
            'manipulation_status': {
                'v27_active': self.manipulation_active['v27'],
                'v26_active': self.manipulation_active['v26'],
                'v27_cost_btc': self.manipulation_cost_btc['v27'],
                'v26_cost_btc': self.manipulation_cost_btc['v26'],
                'v27_cost_usd': self.manipulation_cost_usd['v27'],
                'v26_cost_usd': self.manipulation_cost_usd['v26']
            },
            'actors': self.actors,
            'fee_history': [asdict(f) for f in self.fee_history],
            'portfolio_history': [asdict(p) for p in self.portfolio_history]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def print_summary(self):
        """Print current fee market summary"""
        print("=" * 70)
        print("FEE ORACLE SUMMARY")
        print("=" * 70)
        print(f"v27 Fee: {self.fees['v27']:.2f} sat/vB "
              f"(organic: {self.organic_fees['v27']:.2f}, "
              f"manipulation: {self.manipulation_premium['v27']:.2f})")
        print(f"v26 Fee: {self.fees['v26']:.2f} sat/vB "
              f"(organic: {self.organic_fees['v26']:.2f}, "
              f"manipulation: {self.manipulation_premium['v26']:.2f})")

        if self.manipulation_active['v27'] or self.manipulation_active['v26']:
            print("\nMANIPULATION DETECTED:")
            if self.manipulation_active['v27']:
                print(f"  v27: {self.manipulation_cost_btc['v27']:.4f} BTC spent "
                      f"(${self.manipulation_cost_usd['v27']:,.0f})")
            if self.manipulation_active['v26']:
                print(f"  v26: {self.manipulation_cost_btc['v26']:.4f} BTC spent "
                      f"(${self.manipulation_cost_usd['v26']:,.0f})")

        print(f"\nTotal fee observations: {len(self.fee_history)}")
        print(f"Portfolio snapshots: {len(self.portfolio_history)}")
        print("=" * 70)


# Example usage and testing
if __name__ == '__main__':
    # Need price oracle for testing
    import sys
    sys.path.insert(0, '.')
    from price_oracle import PriceOracle

    print("Testing Fee Oracle with Dual-Token Portfolio Economics")
    print()

    # Initialize oracles
    price_oracle = PriceOracle(base_price=60000)
    fee_oracle = FeeOracle(base_fee_rate=1.0)

    # Initialize manipulator with 100,000 BTC before fork
    # After fork: 100k BTC-v27 + 100k BTC-v26
    fee_oracle.initialize_actor(
        "manipulator",
        initial_holdings_btc=100000,
        initial_price_usd=60000
    )

    print(f"Manipulator initial portfolio:")
    print(f"  v27: 100,000 BTC @ $60,000 = $6.0B")
    print(f"  v26: 100,000 BTC @ $60,000 = $6.0B")
    print(f"  Total: $12.0B")
    print()

    # Simulate scenario: v26 is losing, manipulator tries to prop it up
    print("Scenario: v26 losing (10% hashrate), manipulator tries fee manipulation")
    print()

    for minute in range(0, 121, 10):
        # v26 mining slower, prices diverging
        v27_blocks_per_hour = 6.0
        v26_blocks_per_hour = 0.6  # Only 10% hashrate

        # Update prices (v26 declining)
        v27_price, v26_price = price_oracle.update_prices_from_state(
            v27_height=101 + int(minute * 0.9),
            v26_height=101 + int(minute * 0.1),
            v27_economic_pct=90.0,
            v26_economic_pct=10.0,
            v27_hashrate_pct=90.0,
            v26_hashrate_pct=10.0,
            metadata={'minute': minute}
        )

        # Manipulator spends 1 BTC on artificial v26 fees every 10 minutes
        # (desperate attempt to attract miners)
        blocks_in_period = max(1, int(v26_blocks_per_hour / 6))  # Blocks in 10 min
        fee_oracle.apply_manipulation(
            'v26',
            artificial_fee_spending_btc=1.0,
            blocks_mined_this_period=blocks_in_period,
            actor_id="manipulator"
        )

        # Update organic fees
        v27_fee, v26_fee = fee_oracle.update_fees_from_state(
            v27_blocks_per_hour,
            v26_blocks_per_hour,
            v27_economic_pct=90.0,
            v26_economic_pct=10.0,
            price_oracle=price_oracle,
            metadata={'minute': minute}
        )

        # Calculate miner profitability
        v27_profit = fee_oracle.calculate_miner_profitability(
            'v27', 6.25, v27_price
        )
        v26_profit = fee_oracle.calculate_miner_profitability(
            'v26', 6.25, v26_price
        )

        # Check manipulation sustainability
        sustainability = fee_oracle.calculate_manipulation_sustainability(
            'v26', price_oracle, "manipulator"
        )

        # Record portfolio snapshot
        fee_oracle.record_portfolio_snapshot(
            "manipulator", price_oracle, {'minute': minute}
        )

        print(f"[{minute:3d}min]")
        print(f"  Prices: v27=${v27_price:,.0f} v26=${v26_price:,.0f}")
        print(f"  Fees: v27={v27_fee:.2f} v26={v26_fee:.2f} sat/vB "
              f"(v26 manipulation: +{fee_oracle.manipulation_premium['v26']:.2f})")
        print(f"  Miner profit: v27=${v27_profit['profit_usd']:,.0f} "
              f"v26=${v26_profit['profit_usd']:,.0f}")
        print(f"  Manipulator portfolio: ${sustainability['current_portfolio_value_usd']:,.0f} "
              f"(net: ${sustainability['net_position_usd']:+,.0f})")
        print(f"  Sustainability: {sustainability['sustainability_ratio']:.2f}x "
              f"- {sustainability['recommendation']}")
        print()

    fee_oracle.print_summary()

    # Export results
    output_file = '/tmp/fee_oracle_test.json'
    fee_oracle.export_to_json(output_file)
    print(f"\n✓ Fee & portfolio history exported to: {output_file}")
