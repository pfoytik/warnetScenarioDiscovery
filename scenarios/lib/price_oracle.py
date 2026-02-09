#!/usr/bin/env python3
"""
Price Oracle - Token Price Tracking for Fork Scenarios

Tracks and manages token prices for each fork (v27/v26) during partition tests.
Implements price divergence based on chain fundamentals (hashrate, economic weight, block production).

Usage:
    from price_oracle import PriceOracle

    oracle = PriceOracle(base_price=60000)
    oracle.update_price('v27', chain_weight=0.5, economic_weight=0.9, hashrate_weight=0.1)
    v27_price = oracle.get_price('v27')
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import threading


@dataclass
class PricePoint:
    """Single price observation at a point in time"""
    timestamp: float
    chain_id: str
    price: float
    metadata: Optional[Dict] = None


class PriceOracle:
    """
    Tracks token prices for forked chains with economic-based divergence.

    Price Model:
        new_price = base_price × chain_weight_factor × economic_factor × hashrate_factor

    Where factors are derived from:
        - chain_weight: Relative block production (blocks behind = sell pressure)
        - economic_weight: Custody + volume on chain (buying support)
        - hashrate_weight: Security premium for higher hashrate
    """

    def __init__(
        self,
        base_price: float = 60000,
        max_divergence: float = 0.20,
        chain_weight_coef: float = 0.3,
        economic_weight_coef: float = 0.5,
        hashrate_weight_coef: float = 0.2,
        storage_path: Optional[str] = None,
        min_fork_depth: int = 6,
        debug: bool = False
    ):
        """
        Initialize price oracle.

        Args:
            base_price: Starting price for both chains (USD)
            max_divergence: Maximum price divergence allowed (0.20 = ±20%)
            chain_weight_coef: Weight for block production factor (0-1)
            economic_weight_coef: Weight for economic factor (0-1)
            hashrate_weight_coef: Weight for hashrate factor (0-1)
            storage_path: Path to store price history (JSON file)
            min_fork_depth: Minimum fork depth to consider sustained (default: 6)
        """
        self.base_price = base_price
        self.max_divergence = max_divergence

        # Model coefficients (should sum to ~1.0)
        self.chain_weight_coef = chain_weight_coef
        self.economic_weight_coef = economic_weight_coef
        self.hashrate_weight_coef = hashrate_weight_coef

        # Validate coefficients
        total = chain_weight_coef + economic_weight_coef + hashrate_weight_coef
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Coefficients should sum to 1.0, got {total:.2f}")

        # Current prices
        self.prices: Dict[str, float] = {
            'v27': base_price,
            'v26': base_price
        }

        # Price history
        self.history: List[PricePoint] = []

        # Sustained fork detection
        self.min_fork_depth = min_fork_depth
        self.fork_sustained = False
        self.fork_start_height = None  # Min height when fork detected
        self.fork_sustained_at = None  # When fork became sustained

        # Storage
        self.storage_path = Path(storage_path) if storage_path else None
        self._lock = threading.Lock()

        # Debug mode
        self.debug = debug

        # Initialize history with starting prices
        start_time = time.time()
        self.history.append(PricePoint(start_time, 'v27', base_price, {'initial': True}))
        self.history.append(PricePoint(start_time, 'v26', base_price, {'initial': True}))

    def get_price(self, chain_id: str) -> float:
        """
        Get current price for a chain.

        Args:
            chain_id: 'v27' or 'v26'

        Returns:
            Current price in USD
        """
        with self._lock:
            return self.prices.get(chain_id, self.base_price)

    def get_price_ratio(self) -> float:
        """
        Get current price ratio (v27/v26).

        Returns:
            Price ratio, where >1.0 means v27 is more valuable
        """
        v27_price = self.get_price('v27')
        v26_price = self.get_price('v26')
        return v27_price / v26_price if v26_price > 0 else 1.0

    def check_fork_sustained(
        self,
        v27_height: int,
        v26_height: int,
        common_ancestor_height: int
    ) -> bool:
        """
        Check if fork is sustained (deep enough for separate token valuation).

        Natural chain splits happen frequently and resolve quickly.
        Only sustained protocol forks should create separate token prices.

        Args:
            v27_height: Current v27 block height
            v26_height: Current v26 block height
            common_ancestor_height: Height of last common block

        Returns:
            True if fork is sustained, False otherwise
        """
        with self._lock:
            # Calculate total fork depth (blocks mined on both chains since split)
            fork_depth = (v27_height + v26_height) - (2 * common_ancestor_height)

            # First detection
            if self.fork_start_height is None:
                self.fork_start_height = common_ancestor_height

            # Check if sustained
            if not self.fork_sustained and fork_depth >= self.min_fork_depth:
                self.fork_sustained = True
                self.fork_sustained_at = time.time()
                if self.debug:
                    print(f"  [PRICE DEBUG] Fork became SUSTAINED! depth={fork_depth} >= min={self.min_fork_depth}")
                return True

            if self.debug and not self.fork_sustained:
                print(f"  [PRICE DEBUG] Fork not yet sustained: depth={fork_depth} < min={self.min_fork_depth}")

            return self.fork_sustained

    def update_price(
        self,
        chain_id: str,
        chain_weight: float,
        economic_weight: float,
        hashrate_weight: float,
        metadata: Optional[Dict] = None
    ) -> float:
        """
        Update price based on chain fundamentals.

        NOTE: Price divergence only occurs for SUSTAINED forks (depth >= min_fork_depth).
        Natural chain splits keep both tokens at base price until fork is sustained.

        Args:
            chain_id: 'v27' or 'v26'
            chain_weight: Relative chain strength (0-1, based on blocks produced)
                         0.5 = even, >0.5 = ahead, <0.5 = behind
            economic_weight: Economic node concentration (0-1)
                           0.5 = split evenly, >0.5 = majority on this chain
            hashrate_weight: Hashrate concentration (0-1)
                           0.5 = split evenly, >0.5 = majority on this chain
            metadata: Optional additional data to store with price point

        Returns:
            New price for the chain
        """
        # Check if fork is sustained
        if not self.fork_sustained:
            # Fork not yet sustained - keep price at base
            new_price = self.base_price
            if self.debug:
                print(f"  [PRICE DEBUG] {chain_id}: fork NOT sustained, price stays at ${new_price:,.0f}")
        else:
            # Fork is sustained - calculate price divergence
            # Calculate factors (normalize to 0.8 - 1.2 range to limit divergence)
            chain_factor = 0.8 + (chain_weight * 0.4)
            economic_factor = 0.8 + (economic_weight * 0.4)
            hashrate_factor = 0.8 + (hashrate_weight * 0.4)

            # Weighted combination
            combined_factor = (
                chain_factor * self.chain_weight_coef +
                economic_factor * self.economic_weight_coef +
                hashrate_factor * self.hashrate_weight_coef
            )

            # Calculate new price
            new_price = self.base_price * combined_factor

            # Apply max divergence constraint
            min_price = self.base_price * (1 - self.max_divergence)
            max_price = self.base_price * (1 + self.max_divergence)
            new_price = max(min_price, min(max_price, new_price))

            if self.debug:
                print(f"  [PRICE DEBUG] {chain_id}: chain={chain_weight:.3f} econ={economic_weight:.3f} hash={hashrate_weight:.3f}")
                print(f"  [PRICE DEBUG] {chain_id}: factors chain={chain_factor:.3f} econ={economic_factor:.3f} hash={hashrate_factor:.3f}")
                print(f"  [PRICE DEBUG] {chain_id}: combined={combined_factor:.4f} -> ${new_price:,.0f}")

        # Update price
        with self._lock:
            self.prices[chain_id] = new_price

            # Record in history
            price_point = PricePoint(
                timestamp=time.time(),
                chain_id=chain_id,
                price=new_price,
                metadata=metadata or {}
            )
            self.history.append(price_point)

        return new_price

    def update_prices_from_state(
        self,
        v27_height: int,
        v26_height: int,
        v27_economic_pct: float,
        v26_economic_pct: float,
        v27_hashrate_pct: float,
        v26_hashrate_pct: float,
        common_ancestor_height: int,
        metadata: Optional[Dict] = None,
        v27_chain_weight_override: Optional[float] = None,
        v26_chain_weight_override: Optional[float] = None,
    ) -> Tuple[float, float]:
        """
        Update both chain prices from current network state.

        Args:
            v27_height: Current block height of v27 chain
            v26_height: Current block height of v26 chain
            v27_economic_pct: Percentage of economic weight on v27 (0-100)
            v26_economic_pct: Percentage of economic weight on v26 (0-100)
            v27_hashrate_pct: Percentage of hashrate on v27 (0-100)
            v26_hashrate_pct: Percentage of hashrate on v26 (0-100)
            common_ancestor_height: Height of last common block before fork
            metadata: Optional metadata to attach to price updates
            v27_chain_weight_override: If provided, use this instead of height-based
                chain weight for v27 (0-1, from difficulty oracle chainwork)
            v26_chain_weight_override: If provided, use this instead of height-based
                chain weight for v26 (0-1, from difficulty oracle chainwork)

        Returns:
            Tuple of (v27_price, v26_price)
        """
        # Check if fork is sustained (only for sustained forks do prices diverge)
        just_became_sustained = self.check_fork_sustained(
            v27_height, v26_height, common_ancestor_height
        )

        # Log when fork becomes sustained
        if just_became_sustained and self.fork_sustained_at is not None:
            fork_depth = (v27_height + v26_height) - (2 * common_ancestor_height)
            # Note: Actual logging should be done by caller with proper logger
            # We'll add this info to metadata
            if metadata is None:
                metadata = {}
            metadata['fork_sustained'] = True
            metadata['fork_depth'] = fork_depth

        # Use chainwork-based overrides if provided, otherwise height-based
        if v27_chain_weight_override is not None and v26_chain_weight_override is not None:
            v27_chain_weight = v27_chain_weight_override
            v26_chain_weight = v26_chain_weight_override
        else:
            total_blocks = v27_height + v26_height
            v27_chain_weight = v27_height / total_blocks if total_blocks > 0 else 0.5
            v26_chain_weight = v26_height / total_blocks if total_blocks > 0 else 0.5

        # Economic weights (convert percentage to 0-1)
        v27_econ_weight = v27_economic_pct / 100.0
        v26_econ_weight = v26_economic_pct / 100.0

        # Hashrate weights (convert percentage to 0-1)
        v27_hash_weight = v27_hashrate_pct / 100.0
        v26_hash_weight = v26_hashrate_pct / 100.0

        # Update prices
        v27_price = self.update_price(
            'v27',
            v27_chain_weight,
            v27_econ_weight,
            v27_hash_weight,
            metadata
        )

        v26_price = self.update_price(
            'v26',
            v26_chain_weight,
            v26_econ_weight,
            v26_hash_weight,
            metadata
        )

        return v27_price, v26_price

    def get_price_history(
        self,
        chain_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[PricePoint]:
        """
        Get price history with optional filtering.

        Args:
            chain_id: Filter by chain ('v27' or 'v26'), None for all
            start_time: Filter prices after this timestamp
            end_time: Filter prices before this timestamp

        Returns:
            List of PricePoint objects
        """
        with self._lock:
            history = self.history.copy()

        # Apply filters
        if chain_id:
            history = [p for p in history if p.chain_id == chain_id]
        if start_time:
            history = [p for p in history if p.timestamp >= start_time]
        if end_time:
            history = [p for p in history if p.timestamp <= end_time]

        return history

    def get_price_timeline(self) -> Dict:
        """
        Get price history formatted as timelines for visualization.

        Returns:
            Dict with timestamps and price arrays:
            {
                'timestamps': [t0, t1, ...],
                'v27_prices': [p0, p1, ...],
                'v26_prices': [p0, p1, ...]
            }
        """
        v27_history = self.get_price_history('v27')
        v26_history = self.get_price_history('v26')

        # Get all unique timestamps
        all_times = sorted(set(
            [p.timestamp for p in v27_history] +
            [p.timestamp for p in v26_history]
        ))

        # Build price arrays (using last known price for each timestamp)
        v27_prices = []
        v26_prices = []

        v27_idx = 0
        v26_idx = 0

        for t in all_times:
            # Advance v27 index to latest price <= t
            while v27_idx < len(v27_history) - 1 and v27_history[v27_idx + 1].timestamp <= t:
                v27_idx += 1

            # Advance v26 index to latest price <= t
            while v26_idx < len(v26_history) - 1 and v26_history[v26_idx + 1].timestamp <= t:
                v26_idx += 1

            v27_prices.append(v27_history[v27_idx].price if v27_idx < len(v27_history) else self.base_price)
            v26_prices.append(v26_history[v26_idx].price if v26_idx < len(v26_history) else self.base_price)

        return {
            'timestamps': all_times,
            'v27_prices': v27_prices,
            'v26_prices': v26_prices
        }

    def export_to_json(self, output_path: str):
        """
        Export price history to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        timeline = self.get_price_timeline()

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
            'timeline': timeline,
            'history': [asdict(p) for p in self.history]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def save_to_disk(self):
        """Save price history to configured storage path"""
        if self.storage_path:
            self.export_to_json(str(self.storage_path))

    def print_summary(self):
        """Print current price state summary"""
        v27_price = self.get_price('v27')
        v26_price = self.get_price('v26')
        ratio = self.get_price_ratio()

        print("=" * 60)
        print("PRICE ORACLE SUMMARY")
        print("=" * 60)
        print(f"Fork Status: {'SUSTAINED' if self.fork_sustained else 'NOT SUSTAINED'}")
        if self.fork_sustained:
            print(f"  (Sustained fork enables separate token valuation)")
        else:
            print(f"  (Natural chain split - prices remain equal)")
        print(f"v27 Price: ${v27_price:,.2f}")
        print(f"v26 Price: ${v26_price:,.2f}")
        print(f"Price Ratio (v27/v26): {ratio:.4f}")
        print(f"Divergence: {abs(ratio - 1.0) * 100:.2f}%")
        print(f"Total price updates: {len(self.history)}")
        print("=" * 60)


def load_price_oracle_from_config(config: Dict) -> PriceOracle:
    """
    Create PriceOracle from configuration dictionary.

    Args:
        config: Configuration dict with keys:
            - base_price (optional, default 60000)
            - max_divergence (optional, default 0.20)
            - coefficients (optional, dict with chain_weight, economic_weight, hashrate_weight)
            - storage_path (optional)
            - min_fork_depth (optional, default 6)

    Returns:
        Configured PriceOracle instance
    """
    coeffs = config.get('coefficients', {})

    return PriceOracle(
        base_price=config.get('base_price', 60000),
        max_divergence=config.get('max_divergence', 0.20),
        chain_weight_coef=coeffs.get('chain_weight', 0.3),
        economic_weight_coef=coeffs.get('economic_weight', 0.5),
        hashrate_weight_coef=coeffs.get('hashrate_weight', 0.2),
        storage_path=config.get('storage_path'),
        min_fork_depth=config.get('min_fork_depth', 6)
    )


# Example usage and testing
if __name__ == '__main__':
    import sys

    # Create oracle
    oracle = PriceOracle(base_price=60000)

    print("Testing Price Oracle")
    print()

    # Simulate scenario: v27 has economic advantage, v26 has hashrate advantage
    print("Scenario: v27 = 90% economic, 10% hashrate | v26 = 10% economic, 90% hashrate")
    print()

    # Simulate over 2 hours (120 minutes)
    for minute in range(0, 121, 10):  # Every 10 minutes
        # Simulate block production
        # v26 mines faster due to more hashrate
        v27_height = 101 + int(minute * 0.1)  # Slow mining
        v26_height = 101 + int(minute * 0.9)  # Fast mining

        # Update prices
        v27_price, v26_price = oracle.update_prices_from_state(
            v27_height=v27_height,
            v26_height=v26_height,
            v27_economic_pct=90.0,
            v26_economic_pct=10.0,
            v27_hashrate_pct=10.0,
            v26_hashrate_pct=90.0,
            metadata={'minute': minute}
        )

        ratio = v27_price / v26_price
        print(f"[{minute:3d}min] Heights: v27={v27_height} v26={v26_height} | "
              f"Prices: v27=${v27_price:,.0f} v26=${v26_price:,.0f} | "
              f"Ratio: {ratio:.4f}")

    print()
    oracle.print_summary()

    # Export data
    output_file = '/tmp/price_oracle_test.json'
    oracle.export_to_json(output_file)
    print(f"\n✓ Price history exported to: {output_file}")
