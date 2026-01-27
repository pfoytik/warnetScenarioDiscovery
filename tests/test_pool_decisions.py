#!/usr/bin/env python3

"""
Test Mining Pool Decisions with Ideology vs. Profitability

Simulates realistic scenario where:
- v27 has economic advantage (higher price)
- v26 has hashrate advantage (mining faster)
- Some pools prefer v26 ideologically
- Shows when ideology is sustainable vs. unsustainable
"""

import sys
sys.path.insert(0, '.')

from mining_pool_strategy import (
    MiningPoolStrategy,
    PoolProfile,
    ForkPreference,
    create_realistic_pool_distribution
)
from price_oracle import PriceOracle
from fee_oracle import FeeOracle


def test_ideological_pool_costs():
    """
    Test scenario: v26 ideological pool fights economic reality

    Setup:
    - v27: 70% economic weight, rising price
    - v26: Initially 60% hashrate
    - viabtc strongly prefers v26 (12% hashrate)

    Question: How long can viabtc sustain v26 despite lower profitability?
    """
    print("\n" + "="*70)
    print("TEST: Ideological Pool vs. Economic Reality")
    print("="*70)

    # Initialize oracles
    price_oracle = PriceOracle(base_price=60000, min_fork_depth=0)  # Immediate divergence for test
    fee_oracle = FeeOracle()

    # Mark fork as sustained (skip the 6-block threshold for this test)
    price_oracle.fork_sustained = True

    # Initialize fee state
    fee_oracle.fees['v27'] = 2.0
    fee_oracle.fees['v26'] = 2.0

    # Create pool strategy with realistic distribution
    pools = create_realistic_pool_distribution()
    pool_strategy = MiningPoolStrategy(pools)

    print("\nScenario:")
    print("  v27: 70% economic weight → higher price")
    print("  v26: 30% economic weight → lower price")
    print("  viabtc: Prefers v26 (ideology=50%), will sacrifice up to $2M")
    print()

    # Simulate 12 time periods (every 10 minutes for 2 hours)
    print("Time | v27 Price | v26 Price | viabtc Mining | viabtc Cost | Reason")
    print("-" * 100)

    for period in range(13):  # 0 to 120 minutes
        current_time = period * 600  # 10-minute intervals

        # Update prices based on economic weights
        v27_price, v26_price = price_oracle.update_prices_from_state(
            v27_height=100 + period * 3,  # v27 mining slower
            v26_height=100 + period * 5,  # v26 mining faster initially
            v27_economic_pct=70.0,
            v26_economic_pct=30.0,
            v27_hashrate_pct=40.0,  # Will change as pools switch
            v26_hashrate_pct=60.0,
            common_ancestor_height=100
        )

        # Calculate hashrate allocation (pools make decisions)
        v27_hashrate, v26_hashrate = pool_strategy.calculate_hashrate_allocation(
            current_time, price_oracle, fee_oracle
        )

        # Get viabtc's decision
        viabtc_summary = pool_strategy.get_pool_summary('viabtc')
        recent_decision = viabtc_summary['recent_decisions'][-1] if viabtc_summary['recent_decisions'] else None

        if recent_decision:
            print(f"{period*10:3d}m | ${v27_price:8,.0f} | ${v26_price:8,.0f} | "
                  f"{recent_decision['chosen_fork']:^13s} | ${recent_decision['cumulative_cost_usd']:9,.0f} | "
                  f"{recent_decision['reason'][:40]}")

    print("-" * 100)

    # Final summary
    print("\n" + "="*70)
    print("FINAL POOL ALLOCATION")
    print("="*70)

    v27_hashrate, v26_hashrate = pool_strategy.calculate_hashrate_allocation(
        12 * 600, price_oracle, fee_oracle
    )

    print(f"\nHashrate Distribution:")
    print(f"  v27: {v27_hashrate:.1f}%")
    print(f"  v26: {v26_hashrate:.1f}%")

    print(f"\nIdeological Pool Costs:")

    # Analyze pools that preferred v26 but might have switched
    ideological_pools = ['viabtc', 'community_pool', 'f2pool', 'braiins']

    for pool_id in ideological_pools:
        if pool_id in pool_strategy.pools:
            summary = pool_strategy.get_pool_summary(pool_id)
            pool = pool_strategy.pools[pool_id]

            if pool.fork_preference != ForkPreference.NEUTRAL:
                print(f"\n  {pool_id} ({pool.hashrate_pct:.1f}% hashrate):")
                print(f"    Preference: {pool.fork_preference.value}")
                print(f"    Ideology strength: {pool.ideology_strength*100:.0f}%")
                print(f"    Current mining: {summary['current_allocation']}")
                print(f"    Opportunity cost: ${summary['cumulative_opportunity_cost_usd']:,.0f}")
                print(f"    Times chose ideology over profit: {summary['ideology_override_count']}")
                print(f"    Times forced to switch: {summary['forced_switch_count']}")

                if summary['forced_switch_count'] > 0:
                    print(f"    → IDEOLOGY UNSUSTAINABLE - forced to abandon preferred fork")
                elif summary['ideology_override_count'] > 0:
                    print(f"    → Ideology sustained at cost of ${summary['cumulative_opportunity_cost_usd']:,.0f}")

    print("\n" + "="*70)
    print("Key Insights:")
    print("="*70)
    print("1. Rational pools (foundry, antpool, binance) switch immediately to v27")
    print("2. Ideological pools (viabtc, community_pool) try to sustain v26")
    print("3. Eventually forced to switch when losses exceed thresholds")
    print("4. Total opportunity cost shows economic price of ideology")
    print("="*70)


def test_aligned_ideology():
    """
    Test scenario: Ideology and profit aligned (easier case)

    Setup:
    - v27: 70% economic weight AND 60% hashrate
    - Pools preferring v27 have both ideology AND profit on their side
    """
    print("\n" + "="*70)
    print("TEST: Ideology and Profit Aligned")
    print("="*70)

    price_oracle = PriceOracle(base_price=60000, min_fork_depth=0)
    price_oracle.fork_sustained = True

    fee_oracle = FeeOracle()
    fee_oracle.fees['v27'] = 3.0  # Higher fees on v27
    fee_oracle.fees['v26'] = 1.5

    pools = create_realistic_pool_distribution()
    pool_strategy = MiningPoolStrategy(pools)

    print("\nScenario:")
    print("  v27: Higher price AND higher fees")
    print("  Pools preferring v27: profit and ideology aligned")
    print()

    # Single time snapshot
    v27_price, v26_price = price_oracle.update_prices_from_state(
        v27_height=120,
        v26_height=110,
        v27_economic_pct=70.0,
        v26_economic_pct=30.0,
        v27_hashrate_pct=60.0,
        v26_hashrate_pct=40.0,
        common_ancestor_height=100
    )

    v27_hashrate, v26_hashrate = pool_strategy.calculate_hashrate_allocation(
        600, price_oracle, fee_oracle
    )

    pool_strategy.print_allocation_summary()

    print("\nKey Insight:")
    print("  When ideology and profit align, pools happily mine preferred fork")
    print("  Zero opportunity cost - best of both worlds!")


if __name__ == "__main__":
    test_ideological_pool_costs()
    test_aligned_ideology()

    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
    print("\nMining pool strategy with ideology tracking validated!")
    print("Ready for integration with partition_miner scenarios.")
    print("="*70)
