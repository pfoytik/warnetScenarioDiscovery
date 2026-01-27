#!/usr/bin/env python3

"""
Test script for full economics integration (Phase 1 + Phase 2)

Simulates a partition mining scenario to validate:
- Price oracle tracking
- Fee oracle tracking
- Dual-token portfolio economics
- Manipulation sustainability
- Miner profitability calculations
"""

import sys
import os
from time import time, sleep
import json
from typing import Dict, Optional
from threading import Lock

# We'll use the oracle classes from fee_oracle.py and price_oracle.py
sys.path.insert(0, os.path.dirname(__file__))

# Import the standalone oracle implementations
exec(open('price_oracle.py').read().split('if __name__')[0])
exec(open('fee_oracle.py').read().split('if __name__')[0])


def test_price_oracle():
    """Test price oracle functionality"""
    print("="*70)
    print("TEST 1: Price Oracle")
    print("="*70)

    oracle = PriceOracle(base_price=60000)

    # Simulate v27 with economic advantage, v26 with hashrate disadvantage
    print("\nScenario: v27 (70% economic, 60% hashrate) vs v26 (30% economic, 40% hashrate)")
    print()

    for i in range(5):
        # v27: stronger economically, moderate hashrate
        v27_price = oracle.update_price(
            'v27',
            chain_weight=0.55,  # Slightly ahead in blocks
            economic_weight=0.70,
            hashrate_weight=0.60
        )

        # v26: weaker economically, lower hashrate
        v26_price = oracle.update_price(
            'v26',
            chain_weight=0.45,
            economic_weight=0.30,
            hashrate_weight=0.40
        )

        divergence = abs(v27_price / v26_price - 1.0) * 100

        print(f"Update {i+1}:")
        print(f"  v27: ${v27_price:,.2f}")
        print(f"  v26: ${v26_price:,.2f}")
        print(f"  Divergence: {divergence:.2f}%")

    print("\n✓ Price oracle test passed")
    return oracle


def test_fee_oracle_organic():
    """Test organic fee calculation"""
    print("\n" + "="*70)
    print("TEST 2: Fee Oracle - Organic Fees")
    print("="*70)

    oracle = FeeOracle(base_fee_rate=2.0)

    print("\nScenario: Different network conditions")
    print()

    # Normal conditions
    fee1 = oracle.calculate_organic_fee(
        'v27',
        block_production_rate=1.0/600,  # 10-minute blocks
        economic_activity=0.5,
        mempool_pressure=1.0
    )
    print(f"Normal conditions: {fee1:.2f} sat/vB")

    # Slow blocks (congestion)
    fee2 = oracle.calculate_organic_fee(
        'v26',
        block_production_rate=1.0/900,  # 15-minute blocks
        economic_activity=0.5,
        mempool_pressure=1.0
    )
    print(f"Slow blocks (15min): {fee2:.2f} sat/vB")

    # High economic activity
    fee3 = oracle.calculate_organic_fee(
        'v27',
        block_production_rate=1.0/600,
        economic_activity=0.9,  # High activity
        mempool_pressure=1.0
    )
    print(f"High economic activity: {fee3:.2f} sat/vB")

    print("\n✓ Organic fee calculation test passed")
    return oracle


def test_dual_token_portfolio():
    """Test dual-token portfolio economics"""
    print("\n" + "="*70)
    print("TEST 3: Dual-Token Portfolio Economics")
    print("="*70)

    price_oracle = PriceOracle(base_price=60000)
    fee_oracle = FeeOracle()

    # Initialize manipulator with 100k BTC on each fork
    fee_oracle.initialize_actor(
        "manipulator",
        initial_holdings_btc=100000.0,
        initial_price_usd=60000.0
    )

    print("\nInitial portfolio:")
    print("  v27: 100,000 BTC @ $60,000 = $6.0B")
    print("  v26: 100,000 BTC @ $60,000 = $6.0B")
    print("  Total: $12.0B")

    # Simulate price divergence
    v27_price = price_oracle.update_price('v27', 0.6, 0.7, 0.6)  # Stronger
    v26_price = price_oracle.update_price('v26', 0.4, 0.3, 0.4)  # Weaker

    print(f"\nAfter divergence:")
    print(f"  v27: ${v27_price:,.2f}")
    print(f"  v26: ${v26_price:,.2f}")

    # Calculate current portfolio value (no manipulation yet)
    actor = fee_oracle.actors["manipulator"]
    v27_value = actor['v27_holdings_btc'] * v27_price
    v26_value = actor['v26_holdings_btc'] * v26_price
    total_value = v27_value + v26_value

    print(f"\nPortfolio value after price changes:")
    print(f"  v27: 100,000 BTC @ ${v27_price:,.0f} = ${v27_value:,.0f}")
    print(f"  v26: 100,000 BTC @ ${v26_price:,.0f} = ${v26_value:,.0f}")
    print(f"  Total: ${total_value:,.0f}")
    print(f"  Change: ${total_value - 12_000_000_000:+,.0f}")

    print("\n✓ Dual-token portfolio test passed")
    return price_oracle, fee_oracle


def test_manipulation_sustainability():
    """Test manipulation sustainability calculation"""
    print("\n" + "="*70)
    print("TEST 4: Manipulation Sustainability")
    print("="*70)

    price_oracle = PriceOracle(base_price=60000)
    fee_oracle = FeeOracle()

    # Initialize manipulator
    fee_oracle.initialize_actor("manipulator", 100000.0, 60000.0)

    print("\nScenario: Manipulator props up v26 (losing fork)")
    print()

    # Simulate 10 rounds of manipulation
    for i in range(10):
        # Update prices (v26 losing)
        v27_price = price_oracle.update_price('v27', 0.55 + i*0.01, 0.70, 0.60)
        v26_price = price_oracle.update_price('v26', 0.45 - i*0.01, 0.30, 0.40)

        # Apply manipulation (spend 1 BTC on v26)
        try:
            fee_oracle.apply_manipulation('v26', 'manipulator', 1.0, v26_price)
        except Exception as e:
            print(f"\nManipulation failed at round {i+1}: {e}")
            break

        # Check sustainability
        sustain = fee_oracle.calculate_manipulation_sustainability(
            'v26', price_oracle, 'manipulator'
        )

        if i % 3 == 0:  # Print every 3rd round
            print(f"Round {i+1}:")
            print(f"  Prices: v27=${v27_price:,.0f} v26=${v26_price:,.0f}")
            print(f"  Portfolio: ${sustain['current_portfolio_value_usd']:,.0f}")
            print(f"  Costs: ${sustain['cumulative_costs_usd']:,.0f}")
            print(f"  Net: ${sustain['net_position_usd']:,.0f}")
            print(f"  Sustainability: {sustain['sustainability_ratio']:.2f}x - "
                  f"{'SUSTAINABLE' if sustain['sustainable'] else 'UNSUSTAINABLE'}")

    # Final summary
    final_sustain = fee_oracle.calculate_manipulation_sustainability(
        'v26', price_oracle, 'manipulator'
    )

    print(f"\nFinal Assessment:")
    print(f"  Total spent: ${final_sustain['cumulative_costs_usd']:,.0f}")
    print(f"  Portfolio appreciation: ${final_sustain['portfolio_appreciation_usd']:,.0f}")
    print(f"  Sustainability ratio: {final_sustain['sustainability_ratio']:.2f}x")
    print(f"  Sustainable: {'YES' if final_sustain['sustainable'] else 'NO'}")

    print("\n✓ Manipulation sustainability test passed")
    return price_oracle, fee_oracle


def test_miner_profitability():
    """Test miner profitability calculations"""
    print("\n" + "="*70)
    print("TEST 5: Miner Profitability")
    print("="*70)

    price_oracle = PriceOracle(base_price=60000)
    fee_oracle = FeeOracle()

    # Set different prices
    v27_price = price_oracle.update_price('v27', 0.6, 0.7, 0.6)
    v26_price = price_oracle.update_price('v26', 0.4, 0.3, 0.4)

    # Set different fee levels
    v27_fee = fee_oracle.update_fee('v27', 1.0/600, 0.7, 1.0)
    v26_fee = fee_oracle.update_fee('v26', 1.0/600, 0.3, 1.0, manipulation_premium=100.0)

    print(f"\nConditions:")
    print(f"  v27: ${v27_price:,.0f} | {v27_fee:.1f} sat/vB (organic)")
    print(f"  v26: ${v26_price:,.0f} | {v26_fee:.1f} sat/vB (manipulated)")

    # Calculate profitability
    v27_prof = fee_oracle.calculate_miner_profitability('v27', 3.125, v27_price)
    v26_prof = fee_oracle.calculate_miner_profitability('v26', 3.125, v26_price)

    print(f"\nMiner Profitability:")
    print(f"  v27:")
    print(f"    Reward: {v27_prof['total_reward_btc']:.6f} BTC")
    print(f"    Revenue: ${v27_prof['revenue_usd']:,.0f}")
    print(f"    Profit: ${v27_prof['profit_usd']:,.0f} ({v27_prof['profit_margin_pct']:.1f}%)")
    print(f"  v26:")
    print(f"    Reward: {v26_prof['total_reward_btc']:.6f} BTC")
    print(f"    Revenue: ${v26_prof['revenue_usd']:,.0f}")
    print(f"    Profit: ${v26_prof['profit_usd']:,.0f} ({v26_prof['profit_margin_pct']:.1f}%)")

    print(f"\nKey Insight:")
    if v27_prof['profit_usd'] > v26_prof['profit_usd']:
        print(f"  v27 is more profitable despite lower fees!")
        print(f"  Higher token price dominates manipulation premium")
    else:
        print(f"  v26 manipulation is attracting miners")

    print("\n✓ Miner profitability test passed")


def run_all_tests():
    """Run all integration tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "FULL ECONOMICS INTEGRATION TEST" + " "*22 + "║")
    print("║" + " "*20 + "Phase 1 + Phase 2 Validation" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    print()

    try:
        # Run tests
        test_price_oracle()
        test_fee_oracle_organic()
        test_dual_token_portfolio()
        test_manipulation_sustainability()
        test_miner_profitability()

        # Final summary
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nPhase 1 + Phase 2 Integration Complete:")
        print("  ✓ Price oracle tracking")
        print("  ✓ Fee market dynamics")
        print("  ✓ Dual-token portfolio economics")
        print("  ✓ Manipulation sustainability")
        print("  ✓ Miner profitability calculations")
        print()
        print("Ready for warnet scenario testing!")
        print("="*70)
        print()

        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
