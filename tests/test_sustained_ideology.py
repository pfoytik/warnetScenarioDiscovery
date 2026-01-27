#!/usr/bin/env python3

"""
Test: Gradual Erosion of Ideological Mining

Shows realistic scenario where:
1. Fork starts with small price difference
2. Ideological miners sustain unprofitable fork initially
3. Price gap widens over time
4. Eventually ideology becomes economically unsustainable
5. Tracks total cost of ideological stance
"""

import sys
sys.path.insert(0, '.')

from mining_pool_strategy import (
    MiningPoolStrategy,
    PoolProfile,
    ForkPreference
)
from price_oracle import PriceOracle
from fee_oracle import FeeOracle


def test_gradual_ideology_erosion():
    """
    Realistic scenario: Price divergence grows gradually

    Period 1 (0-30min): Small price difference, ideology sustainable
    Period 2 (30-60min): Price gap widens, some pools forced to switch
    Period 3 (60-90min): Large gap, most ideological pools abandon
    Period 4 (90-120min): Only strongest ideologues remain (if any)
    """
    print("\n" + "="*70)
    print("GRADUAL EROSION OF IDEOLOGICAL MINING")
    print("="*70)

    # Setup oracles
    price_oracle = PriceOracle(base_price=60000, min_fork_depth=0, max_divergence=0.25)
    price_oracle.fork_sustained = True

    fee_oracle = FeeOracle()

    # Create custom pool distribution for this test
    pools = [
        # Purely rational pools (54%)
        PoolProfile("foundry", 28.0, ForkPreference.NEUTRAL, 0.0, 0.03),
        PoolProfile("antpool", 18.0, ForkPreference.NEUTRAL, 0.0, 0.05),
        PoolProfile("binance", 8.0, ForkPreference.NEUTRAL, 0.0, 0.02),

        # Moderate ideological preference for v26 (27%)
        PoolProfile(
            "viabtc", 12.0, ForkPreference.V26,
            ideology_strength=0.4,  # Moderate
            profitability_threshold=0.08,
            max_loss_usd=500_000,  # Lower threshold
            max_loss_pct=0.12
        ),
        PoolProfile(
            "f2pool", 15.0, ForkPreference.V26,
            ideology_strength=0.3,  # Weak ideology
            profitability_threshold=0.05,
            max_loss_usd=300_000,
            max_loss_pct=0.10
        ),

        # Strong ideological preference for v26 (15%)
        PoolProfile(
            "btc_com", 10.0, ForkPreference.V26,
            ideology_strength=0.7,  # Strong ideology
            profitability_threshold=0.15,
            max_loss_usd=1_500_000,
            max_loss_pct=0.25
        ),
        PoolProfile(
            "ideological_pool", 5.0, ForkPreference.V26,
            ideology_strength=0.9,  # Very strong ideology
            profitability_threshold=0.25,
            max_loss_usd=800_000,
            max_loss_pct=0.35
        ),

        # Neutral small pools (4%)
        PoolProfile("other", 4.0, ForkPreference.NEUTRAL, 0.1, 0.05),
    ]

    pool_strategy = MiningPoolStrategy(pools)

    print("\nScenario:")
    print("  Fork starts: v27 (70% economic) vs v26 (30% economic)")
    print("  Initial hashrate: 46% v27, 54% v26 (some pools prefer v26 ideologically)")
    print("  As v27 price rises, ideological pools face increasing losses")
    print()

    # Track which pools switch when
    switch_events = []

    print("Time | v27 Price | v26 Price | Gap  | v27 Hash | v26 Hash | Active Ideologues")
    print("-" * 95)

    for period in range(13):
        current_time = period * 600

        # Gradually diverging prices (simulating growing economic confidence)
        # v27 advantage grows from 0% to ~15% over 2 hours
        price_factor = min(0.15, period * 0.012)  # 1.2% per period

        # Simulate block heights (v26 mining faster initially due to more hashrate)
        v26_advantage_blocks = max(0, 5 - period)  # Advantage shrinks as pools switch
        v27_height = 100 + (period * 3)
        v26_height = 100 + (period * 4) + v26_advantage_blocks

        v27_price, v26_price = price_oracle.update_prices_from_state(
            v27_height=v27_height,
            v26_height=v26_height,
            v27_economic_pct=70.0,
            v26_economic_pct=30.0,
            v27_hashrate_pct=46.0 + (period * 2),  # Gradually shifts
            v26_hashrate_pct=54.0 - (period * 2),
            common_ancestor_height=100
        )

        # Update fees (v27 has more transactions due to economic activity)
        fee_oracle.fees['v27'] = 2.5
        fee_oracle.fees['v26'] = 1.8

        # Get hashrate allocation
        v27_hash, v26_hash = pool_strategy.calculate_hashrate_allocation(
            current_time, price_oracle, fee_oracle
        )

        # Count pools mining each fork
        v26_ideologues = []
        for pool_id, choice in pool_strategy.current_allocation.items():
            pool = pool_strategy.pools[pool_id]
            if choice == 'v26' and pool.fork_preference == ForkPreference.V26:
                v26_ideologues.append(f"{pool_id}({pool.hashrate_pct:.0f}%)")

        price_gap_pct = ((v27_price / v26_price) - 1.0) * 100

        ideologues_str = ", ".join(v26_ideologues) if v26_ideologues else "none"

        print(f"{period*10:3d}m | ${v27_price:8,.0f} | ${v26_price:8,.0f} | {price_gap_pct:4.1f}% | "
              f"{v27_hash:6.1f}% | {v26_hash:6.1f}% | {ideologues_str}")

        # Detect switches
        for pool_id, pool in pool_strategy.pools.items():
            if pool.fork_preference == ForkPreference.V26:
                current_choice = pool_strategy.current_allocation[pool_id]
                costs = pool_strategy.pool_costs[pool_id]

                if current_choice == 'v27' and costs['forced_switch_count'] == 1:
                    # Just switched
                    switch_events.append({
                        'time': period * 10,
                        'pool': pool_id,
                        'hashrate': pool.hashrate_pct,
                        'ideology': pool.ideology_strength,
                        'cost': costs['cumulative_opportunity_cost_usd'],
                        'price_gap': price_gap_pct
                    })

    print("-" * 95)

    # Analysis
    print("\n" + "="*70)
    print("IDEOLOGY SUSTAINABILITY ANALYSIS")
    print("="*70)

    print("\nSwitch Events (when ideological pools abandoned v26):")
    if switch_events:
        for event in switch_events:
            print(f"\n  {event['time']:3d}min - {event['pool']:20s} ({event['hashrate']:4.1f}% hashrate)")
            print(f"          Ideology strength: {event['ideology']*100:5.0f}%")
            print(f"          Price gap when switched: {event['price_gap']:5.1f}%")
            print(f"          Cost before switching: ${event['cost']:,.0f}")
    else:
        print("\n  All ideological pools sustained their preference!")

    print("\n\nFinal Pool Status:")
    for pool_id in ['viabtc', 'f2pool', 'btc_com', 'ideological_pool']:
        if pool_id in pool_strategy.pools:
            summary = pool_strategy.get_pool_summary(pool_id)
            pool = pool_strategy.pools[pool_id]

            status = "✓ SUSTAINED" if summary['current_allocation'] == 'v26' else "✗ ABANDONED"

            print(f"\n  {pool_id:20s} ({pool.hashrate_pct:.1f}%) {status}")
            print(f"    Ideology: {pool.ideology_strength*100:.0f}% | "
                  f"Max loss tolerance: ${pool.max_loss_usd:,.0f} or {pool.max_loss_pct*100:.0f}%")
            print(f"    Opportunity cost: ${summary['cumulative_opportunity_cost_usd']:,.0f}")
            print(f"    Forced switches: {summary['forced_switch_count']}")

    # Calculate total cost of ideology
    total_ideology_cost = sum(
        pool_strategy.pool_costs[pool_id]['cumulative_opportunity_cost_usd']
        for pool_id in pool_strategy.pools.keys()
        if pool_strategy.pools[pool_id].fork_preference == ForkPreference.V26
    )

    print(f"\n\nTotal Cost of v26 Ideology: ${total_ideology_cost:,.0f}")

    print("\n" + "="*70)
    print("Key Insights:")
    print("="*70)
    print("1. Weak ideologues (f2pool) switch early when losses are small")
    print("2. Moderate ideologues (viabtc) sustain for longer but eventually switch")
    print("3. Strong ideologues (btc_com, ideological_pool) may sustain despite high costs")
    print("4. Total opportunity cost shows aggregate price of maintaining minority fork")
    print("5. Economic reality eventually dominates unless ideology is very strong")
    print("="*70)


if __name__ == "__main__":
    test_gradual_ideology_erosion()
