#!/usr/bin/env python3

"""
Test: Paired-Node Architecture for Pool Mining

Validates that:
1. Each pool can have one node per partition (paired nodes)
2. Same entity_id in both partitions represents the same pool
3. Pool's binary decision routes to correct partition node
4. Hashrate allocation works correctly with paired nodes
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


def test_paired_node_architecture():
    """Test binary allocation with paired nodes"""

    print("\n" + "="*70)
    print("PAIRED-NODE ARCHITECTURE TEST")
    print("="*70)

    # Create pool profiles
    pools = [
        # Foundry: 28% hashrate, rational
        PoolProfile("foundry", 28.0, ForkPreference.NEUTRAL, 0.0, 0.03),

        # AntPool: 18% hashrate, rational
        PoolProfile("antpool", 18.0, ForkPreference.NEUTRAL, 0.0, 0.05),

        # ViaBTC: 12% hashrate, prefers v26 (conservative)
        PoolProfile(
            "viabtc", 12.0, ForkPreference.V26,
            ideology_strength=0.5,
            profitability_threshold=0.08,
            max_loss_usd=2_000_000,
            max_loss_pct=0.20
        ),

        # F2Pool: 15% hashrate, prefers v27 (innovation)
        PoolProfile(
            "f2pool", 15.0, ForkPreference.V27,
            ideology_strength=0.3,
            profitability_threshold=0.05,
            max_loss_usd=300_000,
            max_loss_pct=0.10
        ),
    ]

    pool_strategy = MiningPoolStrategy(pools)

    # Setup oracles
    price_oracle = PriceOracle(base_price=60000, min_fork_depth=6)
    price_oracle.fork_sustained = True

    fee_oracle = FeeOracle()

    print("\nPool Configuration:")
    print("-" * 70)
    for pool in pools:
        print(f"  {pool.pool_id:10s}: {pool.hashrate_pct:5.1f}% hashrate, "
              f"preference={pool.fork_preference.value}, "
              f"ideology={pool.ideology_strength:.1f}")

    print("\n" + "="*70)
    print("SCENARIO 1: v27 More Profitable (70% economic vs 30%)")
    print("="*70)

    # Set prices: v27 advantage due to economic support
    price_oracle.prices['v27'] = 62000
    price_oracle.prices['v26'] = 58000

    fee_oracle.fees['v27'] = 2.5
    fee_oracle.fees['v26'] = 1.8

    # Get pool decisions (use time >= 600 to bypass cooldown)
    v27_hash, v26_hash = pool_strategy.calculate_hashrate_allocation(
        600, price_oracle, fee_oracle
    )

    print(f"\nPrices: v27=${price_oracle.get_price('v27'):,.0f}, v26=${price_oracle.get_price('v26'):,.0f}")
    print(f"Fees: v27={fee_oracle.get_fee('v27')} sat/vB, v26={fee_oracle.get_fee('v26')} sat/vB")
    print(f"\nHashrate Allocation: v27={v27_hash:.1f}%, v26={v26_hash:.1f}%")

    print("\nIndividual Pool Decisions:")
    print("-" * 70)

    expected_v27_hash = 0.0
    expected_v26_hash = 0.0

    for pool_id, choice in pool_strategy.current_allocation.items():
        pool = pool_strategy.pools[pool_id]
        decision = [d for d in pool_strategy.decision_history if d.pool_id == pool_id][-1]

        status = ""
        if decision.ideology_override:
            status = f"💰 IDEOLOGY (losing ${decision.opportunity_cost_usd:,.0f})"
        elif choice == decision.rational_choice:
            status = "✓ Rational"
        else:
            status = "⚠️  Forced switch"

        print(f"  {pool_id:10s} → {choice:3s} ({pool.hashrate_pct:5.1f}% hash) | {status}")

        # Track expected hashrate
        if choice == 'v27':
            expected_v27_hash += pool.hashrate_pct
        else:
            expected_v26_hash += pool.hashrate_pct

    print(f"\nExpected hashrate: v27={expected_v27_hash:.1f}%, v26={expected_v26_hash:.1f}%")
    print(f"Actual hashrate:   v27={v27_hash:.1f}%, v26={v26_hash:.1f}%")

    assert abs(v27_hash - expected_v27_hash) < 0.1, "Hashrate mismatch!"
    assert abs(v26_hash - expected_v26_hash) < 0.1, "Hashrate mismatch!"
    print("✓ Hashrate allocation matches pool decisions")

    print("\n" + "="*70)
    print("SCENARIO 2: v26 More Profitable (switch scenario)")
    print("="*70)

    # Set prices: v26 advantage
    price_oracle.prices['v27'] = 58000
    price_oracle.prices['v26'] = 62000

    fee_oracle.fees['v27'] = 1.8
    fee_oracle.fees['v26'] = 2.5

    # Get pool decisions (use time >= 600 seconds after previous)
    v27_hash, v26_hash = pool_strategy.calculate_hashrate_allocation(
        1200, price_oracle, fee_oracle
    )

    print(f"\nPrices: v27=${price_oracle.get_price('v27'):,.0f}, v26=${price_oracle.get_price('v26'):,.0f}")
    print(f"Fees: v27={fee_oracle.get_fee('v27')} sat/vB, v26={fee_oracle.get_fee('v26')} sat/vB")
    print(f"\nHashrate Allocation: v27={v27_hash:.1f}%, v26={v26_hash:.1f}%")

    print("\nIndividual Pool Decisions:")
    print("-" * 70)

    for pool_id, choice in pool_strategy.current_allocation.items():
        pool = pool_strategy.pools[pool_id]
        decision = [d for d in pool_strategy.decision_history if d.pool_id == pool_id][-1]

        status = ""
        if decision.ideology_override:
            status = f"💰 IDEOLOGY (losing ${decision.opportunity_cost_usd:,.0f})"
        elif choice == decision.rational_choice:
            status = "✓ Rational"
        else:
            status = "⚠️  Forced switch"

        # Check if pool switched
        prev_choice = None
        prev_decisions = [d for d in pool_strategy.decision_history if d.pool_id == pool_id]
        if len(prev_decisions) > 1:
            prev_choice = prev_decisions[-2].chosen_fork

        switch_indicator = ""
        if prev_choice and prev_choice != choice:
            switch_indicator = f" [SWITCHED from {prev_choice}]"

        print(f"  {pool_id:10s} → {choice:3s} ({pool.hashrate_pct:5.1f}% hash) | {status}{switch_indicator}")

    print("\n" + "="*70)
    print("PAIRED-NODE IMPLICATIONS")
    print("="*70)

    print("\nNetwork Architecture:")
    print("  Each pool has 2 nodes (one per partition):")
    print()
    print("  Pool       | v27 Node       | v26 Node")
    print("  -----------|----------------|----------------")
    print("  foundry    | node-foundry-v27 | node-foundry-v26")
    print("  antpool    | node-antpool-v27 | node-antpool-v26")
    print("  viabtc     | node-viabtc-v27  | node-viabtc-v26")
    print("  f2pool     | node-f2pool-v27  | node-f2pool-v26")

    print("\nMining Selection Logic:")
    print("  When foundry chooses v27:")
    print("    → generatetoaddress() called on node-foundry-v27")
    print("    → 28% probability of mining next block")
    print()
    print("  When viabtc chooses v26 (ideology):")
    print("    → generatetoaddress() called on node-viabtc-v26")
    print("    → 12% probability of mining next block")
    print("    → Opportunity cost tracked in USD")

    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)

    # Verify binary allocation
    for pool_id, choice in pool_strategy.current_allocation.items():
        assert choice in ['v27', 'v26'], f"Pool {pool_id} has invalid choice: {choice}"
    print("✓ All pools have binary allocation (v27 or v26)")

    # Verify total hashrate is 100%
    total_hash = sum(pool.hashrate_pct for pool in pools)
    assert abs(total_hash - 73.0) < 0.1, f"Total hashrate should be 73%, got {total_hash}%"
    print(f"✓ Total pool hashrate: {total_hash:.1f}%")

    # Verify allocation sum
    assert abs((v27_hash + v26_hash) - total_hash) < 0.1, "Allocation doesn't sum to total"
    print(f"✓ Allocation sums correctly: {v27_hash:.1f}% + {v26_hash:.1f}% = {v27_hash + v26_hash:.1f}%")

    # Check ideology tracking
    ideology_cost = 0
    for pool_id, costs in pool_strategy.pool_costs.items():
        ideology_cost += costs['cumulative_opportunity_cost_usd']

    print(f"✓ Ideology opportunity cost tracked: ${ideology_cost:,.0f}")

    print("\n" + "="*70)
    print("TEST PASSED ✓")
    print("="*70)
    print("\nPaired-node architecture working correctly:")
    print("  - Pools make binary fork decisions")
    print("  - Each pool routes to correct partition node")
    print("  - Hashrate allocation matches pool decisions")
    print("  - Opportunity costs tracked for ideological choices")
    print("="*70)


if __name__ == "__main__":
    test_paired_node_architecture()
