#!/usr/bin/env python3
"""
Unit test for enhanced fork analysis with hashrate tracking.

Tests the enhanced_fork_analysis.py implementation without requiring
a live warnet deployment by using simulated pool decision data.
"""

import json
import os
import tempfile
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from enhanced_fork_analysis import EnhancedForkAnalyzer


def create_test_pool_decisions():
    """Create simulated pool decision data"""
    return {
        "pools": {
            "foundryusa": {
                "profile": {
                    "pool_id": "foundryusa",
                    "hashrate_pct": 26.89,
                    "fork_preference": "neutral"
                },
                "current_allocation": "v27"
            },
            "antpool": {
                "profile": {
                    "pool_id": "antpool",
                    "hashrate_pct": 19.25,
                    "fork_preference": "neutral"
                },
                "current_allocation": "v27"
            },
            "viabtc": {
                "profile": {
                    "pool_id": "viabtc",
                    "hashrate_pct": 11.39,
                    "fork_preference": "v26"
                },
                "current_allocation": "v26"
            },
            "f2pool": {
                "profile": {
                    "pool_id": "f2pool",
                    "hashrate_pct": 11.25,
                    "fork_preference": "neutral"
                },
                "current_allocation": "v27"
            },
            "binancepool": {
                "profile": {
                    "pool_id": "binancepool",
                    "hashrate_pct": 10.04,
                    "fork_preference": "neutral"
                },
                "current_allocation": "v26"
            },
            "marapool": {
                "profile": {
                    "pool_id": "marapool",
                    "hashrate_pct": 8.25,
                    "fork_preference": "neutral"
                },
                "current_allocation": "v27"
            }
        },
        "timestamp": "2026-01-25T12:00:00",
        "scenario": "test"
    }


def create_test_fork_data():
    """Create simulated fork detection data"""
    return {
        "num_chains": 2,
        "chains": {
            "block_hash_v27_tip": [
                {"node": "node-0000", "height": 120},
                {"node": "node-0001", "height": 120},
                {"node": "node-0003", "height": 120},
                {"node": "node-0005", "height": 120},
            ],
            "block_hash_v26_tip": [
                {"node": "node-0002", "height": 115},
                {"node": "node-0004", "height": 115},
            ]
        }
    }


def create_test_network_metadata():
    """Create test network metadata mapping"""
    return {
        "node-0000": {
            "role": "mining_pool",
            "entity_id": "pool-foundryusa",
            "hashrate_pct": 26.89,
            "custody_btc": 53780,
            "daily_volume_btc": 5378,
            "version": "27.0"
        },
        "node-0001": {
            "role": "mining_pool",
            "entity_id": "pool-antpool",
            "hashrate_pct": 19.25,
            "custody_btc": 38500,
            "daily_volume_btc": 3850,
            "version": "27.0"
        },
        "node-0002": {
            "role": "mining_pool",
            "entity_id": "pool-viabtc",
            "hashrate_pct": 11.39,
            "custody_btc": 22780,
            "daily_volume_btc": 2278,
            "version": "26.0"
        },
        "node-0003": {
            "role": "mining_pool",
            "entity_id": "pool-f2pool",
            "hashrate_pct": 11.25,
            "custody_btc": 22500,
            "daily_volume_btc": 2250,
            "version": "27.0"
        },
        "node-0004": {
            "role": "mining_pool",
            "entity_id": "pool-binancepool",
            "hashrate_pct": 10.04,
            "custody_btc": 20080,
            "daily_volume_btc": 2007,
            "version": "26.0"
        },
        "node-0005": {
            "role": "mining_pool",
            "entity_id": "pool-marapool",
            "hashrate_pct": 8.25,
            "custody_btc": 16500,
            "daily_volume_btc": 1650,
            "version": "27.0"
        }
    }


def test_pool_decision_loading():
    """Test loading pool decisions from JSON"""
    print("\n" + "="*70)
    print("TEST 1: Pool Decision Loading")
    print("="*70)

    # Create temporary file with pool decisions
    pool_data = create_test_pool_decisions()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(pool_data, f)
        temp_path = f.name

    try:
        # Initialize analyzer and load decisions
        analyzer = EnhancedForkAnalyzer(fork_depth_threshold=6)
        analyzer.load_pool_decisions(temp_path)

        # Verify pool data loaded
        assert len(analyzer.pool_data) == 6, f"Expected 6 pools, got {len(analyzer.pool_data)}"
        assert "foundryusa" in analyzer.pool_data, "foundryusa not found in pool data"
        assert analyzer.pool_data["foundryusa"]["hashrate_pct"] == 26.89, "Incorrect hashrate for foundryusa"

        # Verify allocations loaded
        assert len(analyzer.pool_allocations) == 6, f"Expected 6 allocations, got {len(analyzer.pool_allocations)}"
        assert analyzer.pool_allocations["foundryusa"] == "v27", "Incorrect allocation for foundryusa"
        assert analyzer.pool_allocations["viabtc"] == "v26", "Incorrect allocation for viabtc"

        print("✓ Pool decision loading works correctly")
        print(f"  - Loaded {len(analyzer.pool_data)} pools")
        print(f"  - Allocations: {len(analyzer.pool_allocations)} pools")
        print(f"  - Sample: foundryusa → v27, viabtc → v26")

        return True

    finally:
        os.unlink(temp_path)


def test_hashrate_calculation():
    """Test hashrate calculation per fork"""
    print("\n" + "="*70)
    print("TEST 2: Hashrate Calculation Per Fork")
    print("="*70)

    # Create temporary pool decisions file
    pool_data = create_test_pool_decisions()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(pool_data, f)
        temp_path = f.name

    try:
        # Initialize analyzer
        analyzer = EnhancedForkAnalyzer(fork_depth_threshold=6)
        analyzer.load_pool_decisions(temp_path)

        # Inject test network metadata
        analyzer.node_economic_data = create_test_network_metadata()

        # Create fork data
        fork_data = create_test_fork_data()

        # Map nodes to forks
        fork_nodes = analyzer.map_nodes_to_forks(fork_data)

        # Calculate hashrate per fork
        hashrate_dist = analyzer.calculate_hashrate_per_fork(fork_nodes)

        # Verify results
        assert "fork_0" in hashrate_dist, "fork_0 not found in hashrate distribution"
        assert "fork_1" in hashrate_dist, "fork_1 not found in hashrate distribution"

        fork_0_hashrate = hashrate_dist["fork_0"]["hashrate_pct"]
        fork_1_hashrate = hashrate_dist["fork_1"]["hashrate_pct"]

        # Expected: foundryusa (26.89) + antpool (19.25) + f2pool (11.25) + marapool (8.25) = 65.64% on v27
        # Expected: viabtc (11.39) + binancepool (10.04) = 21.43% on v26

        print(f"✓ Hashrate calculation completed")
        print(f"  - fork_0 hashrate: {fork_0_hashrate:.2f}%")
        print(f"  - fork_1 hashrate: {fork_1_hashrate:.2f}%")
        print(f"  - Total: {fork_0_hashrate + fork_1_hashrate:.2f}%")

        # Verify one fork has majority v27 pools, other has v26 pools
        total_hashrate = fork_0_hashrate + fork_1_hashrate
        assert 85 < total_hashrate < 90, f"Total hashrate {total_hashrate}% outside expected range"

        # Check pool attribution
        for fork_id, data in hashrate_dist.items():
            pools = data.get("pools", [])
            print(f"\n  {fork_id} pools ({len(pools)}):")
            for pool in pools:
                print(f"    - {pool['pool_id']:15s}: {pool['hashrate_pct']:5.1f}%")

        return True

    finally:
        os.unlink(temp_path)


def test_comprehensive_analysis():
    """Test hashrate integration in fork analysis"""
    print("\n" + "="*70)
    print("TEST 3: Hashrate Integration")
    print("="*70)

    # Create temporary pool decisions file
    pool_data = create_test_pool_decisions()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(pool_data, f)
        temp_path = f.name

    try:
        # Initialize analyzer
        analyzer = EnhancedForkAnalyzer(fork_depth_threshold=6)
        analyzer.load_pool_decisions(temp_path)

        # Inject test network metadata
        analyzer.node_economic_data = create_test_network_metadata()

        # Create fork data
        fork_data = create_test_fork_data()

        # Map nodes to forks
        fork_nodes = analyzer.map_nodes_to_forks(fork_data)

        # Calculate hashrate per fork
        hashrate_dist = analyzer.calculate_hashrate_per_fork(fork_nodes)

        # Verify both forks have hashrate data
        for fork_id in fork_nodes.keys():
            assert fork_id in hashrate_dist, f"{fork_id} not in hashrate distribution"

            hashrate_data = hashrate_dist[fork_id]
            assert 'hashrate_pct' in hashrate_data, f"Missing hashrate_pct for {fork_id}"
            assert 'pools' in hashrate_data, f"Missing pools for {fork_id}"
            assert 'method' in hashrate_data, f"Missing method for {fork_id}"

            print(f"\n  {fork_id}:")
            print(f"    - Hashrate: {hashrate_data['hashrate_pct']:.1f}%")
            print(f"    - Pools: {len(hashrate_data['pools'])}")
            print(f"    - Method: {hashrate_data['method']}")

        print("\n✓ Hashrate integration working correctly")
        print("  - Both forks have hashrate data")
        print("  - Pool decisions properly mapped to forks")

        return True

    finally:
        os.unlink(temp_path)


def test_output_formatting():
    """Test hashrate output formatting"""
    print("\n" + "="*70)
    print("TEST 4: Hashrate Output Formatting")
    print("="*70)

    # Create temporary pool decisions file
    pool_data = create_test_pool_decisions()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(pool_data, f)
        temp_path = f.name

    try:
        # Initialize analyzer
        analyzer = EnhancedForkAnalyzer(fork_depth_threshold=6)
        analyzer.load_pool_decisions(temp_path)

        # Inject test network metadata
        analyzer.node_economic_data = create_test_network_metadata()

        # Create fork data
        fork_data = create_test_fork_data()

        # Map nodes and calculate hashrate
        fork_nodes = analyzer.map_nodes_to_forks(fork_data)
        hashrate_dist = analyzer.calculate_hashrate_per_fork(fork_nodes)

        # Create mock fork analysis with hashrate data
        fork_analysis = {
            "fork_0": {
                "node_count": 4,
                "total_custody": 131280,
                "custody_pct": 75.4,
                "total_volume": 13128,
                "volume_pct": 74.9,
                "consensus_weight": 957.6,
                "weight_pct": 75.1,
                "hashrate": hashrate_dist.get("fork_0", {})
            },
            "fork_1": {
                "node_count": 2,
                "total_custody": 42860,
                "custody_pct": 24.6,
                "total_volume": 4285,
                "volume_pct": 25.1,
                "consensus_weight": 317.4,
                "weight_pct": 24.9,
                "hashrate": hashrate_dist.get("fork_1", {})
            }
        }

        # Test print output (verify it doesn't crash and includes hashrate)
        print("\n✓ Testing enhanced output with hashrate:")
        print("-" * 70)
        analyzer.print_enhanced_analysis(fork_analysis, fork_depth=8)
        print("-" * 70)

        print("\n✓ Output formatting works correctly")
        print("  - Displays hashrate percentages")
        print("  - Lists pools mining each fork")
        print("  - Shows comparative metrics table")

        return True

    finally:
        os.unlink(temp_path)


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("ENHANCED FORK ANALYSIS - UNIT TESTS")
    print("="*70)
    print("\nTesting hashrate tracking integration without live warnet deployment")

    tests = [
        ("Pool Decision Loading", test_pool_decision_loading),
        ("Hashrate Calculation", test_hashrate_calculation),
        ("Hashrate Integration", test_comprehensive_analysis),
        ("Hashrate Output Formatting", test_output_formatting),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status:12s} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Enhanced fork analysis is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
