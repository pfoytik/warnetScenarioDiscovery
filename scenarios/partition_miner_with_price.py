#!/usr/bin/env python3
"""
Partition Miner with Price Model Integration

Example integration showing how to add price tracking to partition mining scenarios.
This is a simplified version demonstrating the integration pattern.

Usage:
    warnet run partition_miner_with_price.py \\
        --v27-hashrate 10 \\
        --v26-hashrate 90 \\
        --v27-economic 90 \\
        --v26-economic 10 \\
        --duration 1800 \\
        --interval 10
"""

import sys
import os
import time
import yaml
from pathlib import Path

# Add lib directory to path for imports
_lib_dir = os.path.join(os.path.dirname(__file__), '../lib')
sys.path.insert(0, _lib_dir)

from price_oracle import PriceOracle, load_price_oracle_from_config


def load_price_config(config_path='price_model_config.yaml'):
    """Load price model configuration from YAML file"""
    try:
        # Config files are now in ../config/
        config_file = Path(__file__).parent / '../config' / config_path
        with open(config_file) as f:
            config = yaml.safe_load(f)
        return config.get('price_model', {})
    except Exception as e:
        print(f"Warning: Could not load price config: {e}")
        return {}


def simulate_partition_with_prices():
    """
    Simulated partition mining with price tracking.

    This demonstrates the integration pattern without requiring full Warnet infrastructure.
    In real scenario, this would be integrated into partition_miner.py
    """

    # Configuration (normally from command-line args)
    v27_hashrate_pct = 10.0
    v26_hashrate_pct = 90.0
    v27_economic_pct = 90.0
    v26_economic_pct = 10.0
    duration_sec = 1800  # 30 minutes
    update_interval = 60  # Update prices every minute

    print("=" * 80)
    print("PARTITION MINER WITH PRICE MODEL")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  v27: {v27_hashrate_pct}% hashrate, {v27_economic_pct}% economic")
    print(f"  v26: {v26_hashrate_pct}% hashrate, {v26_economic_pct}% economic")
    print(f"  Duration: {duration_sec}s ({duration_sec//60} minutes)")
    print(f"  Price updates: Every {update_interval}s")
    print()

    # Initialize price oracle
    price_config = load_price_config()
    if price_config and price_config.get('enabled', False):
        oracle = load_price_oracle_from_config(price_config)
        print("✓ Price oracle initialized")
        print(f"  Base price: ${oracle.base_price:,.0f}")
        print(f"  Max divergence: ±{oracle.max_divergence * 100:.0f}%")
        print(f"  Coefficients: chain={oracle.chain_weight_coef:.2f}, "
              f"econ={oracle.economic_weight_coef:.2f}, "
              f"hash={oracle.hashrate_weight_coef:.2f}")
    else:
        oracle = PriceOracle()  # Default configuration
        print("✓ Price oracle initialized (default config)")

    print()
    print("=" * 80)
    print("Starting mining simulation...")
    print("=" * 80)

    # Starting state
    start_time = time.time()
    start_height = 101  # Common ancestor
    v27_height = start_height
    v26_height = start_height

    last_update = start_time

    # Simulation loop
    elapsed = 0
    while elapsed < duration_sec:
        current_time = time.time()
        elapsed = current_time - start_time

        # Simulate block production based on hashrate
        # Bitcoin mines ~1 block per 10 minutes = 0.1 blocks/min
        # With partition, each side mines at their hashrate percentage
        time_delta = current_time - last_update

        if time_delta >= update_interval:
            # Calculate blocks mined since last update
            minutes_elapsed = elapsed / 60

            # Expected blocks = minutes * (hashrate% / 100) * (6 blocks/hour / 60 min/hour)
            v27_height = start_height + int(minutes_elapsed * (v27_hashrate_pct / 100) * 0.1 * 60)
            v26_height = start_height + int(minutes_elapsed * (v26_hashrate_pct / 100) * 0.1 * 60)

            # Update prices based on current state
            v27_price, v26_price = oracle.update_prices_from_state(
                v27_height=v27_height,
                v26_height=v26_height,
                v27_economic_pct=v27_economic_pct,
                v26_economic_pct=v26_economic_pct,
                v27_hashrate_pct=v27_hashrate_pct,
                v26_hashrate_pct=v26_hashrate_pct,
                metadata={'elapsed_sec': int(elapsed)}
            )

            # Calculate metrics
            price_ratio = v27_price / v26_price
            divergence_pct = abs(price_ratio - 1.0) * 100

            # Log state
            print(f"[{int(elapsed):4d}s] "
                  f"Heights: v27={v27_height:3d} v26={v26_height:3d} | "
                  f"Prices: v27=${v27_price:,.0f} v26=${v26_price:,.0f} | "
                  f"Ratio: {price_ratio:.4f} ({divergence_pct:+.2f}%)")

            last_update = current_time

        # Small sleep to avoid busy loop
        time.sleep(1)

    print()
    print("=" * 80)
    print("Mining simulation complete")
    print("=" * 80)

    # Final summary
    oracle.print_summary()

    # Export results
    output_path = '/tmp/partition_price_simulation.json'
    oracle.export_to_json(output_path)
    print(f"\n✓ Price history exported to: {output_path}")

    return oracle


# Integration pattern for real partition_miner.py
INTEGRATION_EXAMPLE = """
# How to integrate into partition_miner.py:

## 1. Import at top of file:
import sys
import os
_lib_dir = os.path.join(os.path.dirname(__file__), '../lib')
sys.path.insert(0, _lib_dir)
from price_oracle import PriceOracle, load_price_oracle_from_config
import yaml

## 2. Initialize in main() or setup():
# Load configuration (config files are in ../config/)
_config_path = os.path.join(os.path.dirname(__file__), '../config/price_model_config.yaml')
with open(_config_path) as f:
    config = yaml.safe_load(f)
price_config = config.get('price_model', {})

# Create oracle
if price_config.get('enabled', False):
    oracle = load_price_oracle_from_config(price_config)
    logger.info(f"Price oracle enabled: base=${oracle.base_price}")
else:
    oracle = None
    logger.info("Price oracle disabled")

## 3. Update prices in mining loop:
# After each mining round or at regular intervals
if oracle:
    # Get current state
    v27_height = get_chain_height('v27')
    v26_height = get_chain_height('v26')

    # Update prices
    v27_price, v26_price = oracle.update_prices_from_state(
        v27_height=v27_height,
        v26_height=v26_height,
        v27_economic_pct=v27_economic_pct,
        v26_economic_pct=v26_economic_pct,
        v27_hashrate_pct=v27_hashrate_pct,
        v26_hashrate_pct=v26_hashrate_pct
    )

    # Log prices
    logger.info(f"Prices: v27=${v27_price:.0f} v26=${v26_price:.0f} "
                f"(ratio={v27_price/v26_price:.4f})")

## 4. Export results at end:
if oracle:
    # Save price history
    oracle.export_to_json(f'{results_dir}/price_history.json')

    # Add to result metadata
    result['price_model'] = {
        'enabled': True,
        'final_v27_price': oracle.get_price('v27'),
        'final_v26_price': oracle.get_price('v26'),
        'price_ratio': oracle.get_price_ratio(),
        'price_history_file': 'price_history.json'
    }
"""


if __name__ == '__main__':
    print("Price Oracle Integration Example")
    print()
    print("This demonstrates how to integrate price tracking into partition_miner.py")
    print()

    # Check if we should run simulation or show integration example
    if len(sys.argv) > 1 and sys.argv[1] == '--simulate':
        # Run simulation
        simulate_partition_with_prices()
    else:
        # Show integration pattern
        print(INTEGRATION_EXAMPLE)
        print()
        print("To run simulation demo:")
        print("  python3 partition_miner_with_price.py --simulate")
