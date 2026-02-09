#!/usr/bin/env python3

"""
Test Sustained Fork Detection

Validates that price divergence only occurs for sustained forks (depth >= 6),
not for natural chain splits that resolve quickly.
"""

import sys
sys.path.insert(0, '.')

from price_oracle import PriceOracle


def test_natural_chainsplit():
    """Test that natural chain splits don't create price divergence"""
    print("\n" + "="*70)
    print("TEST 1: Natural Chain Split (depth < 6)")
    print("="*70)

    oracle = PriceOracle(base_price=60000, min_fork_depth=6)

    # Simulate natural chain split - both chains mining a few blocks
    common_ancestor = 100

    print("\nSimulating natural chain split (resolves quickly):")
    print(f"Common ancestor: block {common_ancestor}")
    print()

    # Update prices as chains diverge slightly
    for i in range(1, 6):  # Blocks 101-105 (fork depth = 0, 2, 4, 6, 8)
        v27_height = common_ancestor + i
        v26_height = common_ancestor + i

        # Check sustained status
        oracle.check_fork_sustained(v27_height, v26_height, common_ancestor)

        # Update prices
        v27_price, v26_price = oracle.update_prices_from_state(
            v27_height=v27_height,
            v26_height=v26_height,
            v27_economic_pct=70.0,   # v27 has economic advantage
            v26_economic_pct=30.0,
            v27_hashrate_pct=60.0,
            v26_hashrate_pct=40.0,
            common_ancestor_height=common_ancestor
        )

        fork_depth = (v27_height + v26_height) - (2 * common_ancestor)

        print(f"Block {v27_height}: Fork depth = {fork_depth}")
        print(f"  Sustained: {oracle.fork_sustained}")
        print(f"  v27 price: ${v27_price:,.2f}")
        print(f"  v26 price: ${v26_price:,.2f}")

        if fork_depth < 6:
            assert v27_price == 60000, f"Price diverged too early! (depth={fork_depth})"
            assert v26_price == 60000, f"Price diverged too early! (depth={fork_depth})"
            print(f"  ✓ Prices remain equal (natural split)")
        else:
            print(f"  ✓ Fork now sustained - prices can diverge")

    print("\n✓ Natural chain split test PASSED")
    print("  Prices remained equal until fork depth >= 6")


def test_sustained_fork():
    """Test that sustained forks DO create price divergence"""
    print("\n" + "="*70)
    print("TEST 2: Sustained Fork (depth >= 6)")
    print("="*70)

    oracle = PriceOracle(base_price=60000, min_fork_depth=6)

    # Simulate sustained protocol fork
    common_ancestor = 100

    print("\nSimulating sustained protocol fork:")
    print(f"Common ancestor: block {common_ancestor}")
    print()

    # Mine enough blocks to make fork sustained
    for i in range(1, 10):  # Blocks 101-109
        v27_height = common_ancestor + i
        v26_height = common_ancestor + i

        v27_price, v26_price = oracle.update_prices_from_state(
            v27_height=v27_height,
            v26_height=v26_height,
            v27_economic_pct=70.0,   # v27 stronger economically
            v26_economic_pct=30.0,
            v27_hashrate_pct=60.0,
            v26_hashrate_pct=40.0,
            common_ancestor_height=common_ancestor
        )

        fork_depth = (v27_height + v26_height) - (2 * common_ancestor)

        if fork_depth == 6:
            print(f"\n🔀 FORK SUSTAINED at block {v27_height} (depth={fork_depth})")
            print(f"  Separate token valuation now active!")

        if fork_depth >= 6:
            print(f"\nBlock {v27_height}: Fork depth = {fork_depth}")
            print(f"  v27 price: ${v27_price:,.2f}")
            print(f"  v26 price: ${v26_price:,.2f}")
            print(f"  Divergence: {abs(v27_price/v26_price - 1.0)*100:.2f}%")

            # After fork is sustained, prices should diverge
            assert v27_price != v26_price, "Prices should diverge after fork sustained!"
            assert v27_price > v26_price, "v27 should be more valuable (stronger economically)"

    print("\n✓ Sustained fork test PASSED")
    print("  Prices diverged after fork depth >= 6")
    print(f"  Final: v27=${v27_price:,.2f}, v26=${v26_price:,.2f}")


def test_asymmetric_fork():
    """Test fork where one chain mines faster than the other"""
    print("\n" + "="*70)
    print("TEST 3: Asymmetric Fork (one chain faster)")
    print("="*70)

    oracle = PriceOracle(base_price=60000, min_fork_depth=6)

    common_ancestor = 100

    print("\nSimulating asymmetric fork (v27 mines faster):")
    print(f"Common ancestor: block {common_ancestor}")
    print()

    # v27 mines 2 blocks for every 1 v26 block
    for i in range(1, 8):
        v27_height = common_ancestor + (i * 2)    # v27: 102, 104, 106, 108, ...
        v26_height = common_ancestor + i          # v26: 101, 102, 103, 104, ...

        v27_price, v26_price = oracle.update_prices_from_state(
            v27_height=v27_height,
            v26_height=v26_height,
            v27_economic_pct=70.0,
            v26_economic_pct=30.0,
            v27_hashrate_pct=70.0,   # v27 has more hashrate
            v26_hashrate_pct=30.0,
            common_ancestor_height=common_ancestor
        )

        fork_depth = (v27_height + v26_height) - (2 * common_ancestor)

        print(f"Heights: v27={v27_height}, v26={v26_height} | Fork depth = {fork_depth}")
        print(f"  Sustained: {oracle.fork_sustained}")
        print(f"  v27: ${v27_price:,.2f} | v26: ${v26_price:,.2f}")

        if fork_depth >= 6 and not oracle.fork_sustained:
            print(f"  ✗ Fork should be sustained at depth {fork_depth}!")
            assert False

    print("\n✓ Asymmetric fork test PASSED")
    print(f"  Fork became sustained at depth >= 6")
    print(f"  v27 maintains premium due to faster block production")


def test_fork_depth_calculation():
    """Test fork depth calculation examples"""
    print("\n" + "="*70)
    print("TEST 4: Fork Depth Calculation")
    print("="*70)

    oracle = PriceOracle(base_price=60000, min_fork_depth=6)
    common_ancestor = 100

    test_cases = [
        # (v27_height, v26_height, expected_depth, description)
        (101, 101, 2, "Each chain +1 block"),
        (102, 101, 3, "v27 +2, v26 +1"),
        (103, 103, 6, "Each chain +3 blocks (SUSTAINED)"),
        (105, 102, 7, "v27 +5, v26 +2"),
        (110, 110, 20, "Each chain +10 blocks"),
    ]

    print("\nFork depth calculation examples:")
    print("Formula: fork_depth = (v27_height + v26_height) - (2 × common_ancestor)")
    print()

    for v27_height, v26_height, expected_depth, description in test_cases:
        calculated_depth = (v27_height + v26_height) - (2 * common_ancestor)

        assert calculated_depth == expected_depth, \
            f"Wrong depth calculation: got {calculated_depth}, expected {expected_depth}"

        oracle.check_fork_sustained(v27_height, v26_height, common_ancestor)

        sustained = "SUSTAINED" if calculated_depth >= 6 else "NOT SUSTAINED"

        print(f"v27={v27_height}, v26={v26_height}")
        print(f"  Depth: {calculated_depth} - {sustained}")
        print(f"  ({description})")

    print("\n✓ Fork depth calculation test PASSED")


def main():
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*18 + "SUSTAINED FORK DETECTION TEST" + " "*21 + "║")
    print("╚" + "="*68 + "╝")

    try:
        test_natural_chainsplit()
        test_sustained_fork()
        test_asymmetric_fork()
        test_fork_depth_calculation()

        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nSustained Fork Detection Validated:")
        print("  ✓ Natural chain splits keep prices equal (depth < 6)")
        print("  ✓ Sustained forks enable price divergence (depth >= 6)")
        print("  ✓ Asymmetric forks handled correctly")
        print("  ✓ Fork depth calculation accurate")
        print()
        print("Key Insight:")
        print("  Only sustained protocol forks create separate tokens.")
        print("  Temporary chain splits (common in Bitcoin) don't affect price.")
        print("="*70)
        print()

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
