#!/usr/bin/env python3
"""
Test: Verify import paths work after directory reorganization

Validates that all scenarios can import from lib/ and access config/ correctly.
"""

import sys
import os
from pathlib import Path


def test_scenario_imports():
    """Test that scenarios can import from lib/"""
    print("\n" + "="*70)
    print("TEST: Scenario Import Paths")
    print("="*70)

    # Test from root directory perspective (lib/ and config/ are at root level)
    root_dir = Path(__file__).parent.parent
    scenarios_dir = root_dir / 'scenarios'
    lib_dir = root_dir / 'lib'  # lib is at root level
    config_dir = root_dir / 'config'  # config is at root level

    print(f"\nDirectories:")
    print(f"  scenarios/: {scenarios_dir} ({'EXISTS' if scenarios_dir.exists() else 'MISSING'})")
    print(f"  lib/:       {lib_dir} ({'EXISTS' if lib_dir.exists() else 'MISSING'})")
    print(f"  config/:    {config_dir} ({'EXISTS' if config_dir.exists() else 'MISSING'})")

    # Test lib/ imports
    print(f"\n✓ Testing lib/ module imports:")
    sys.path.insert(0, str(lib_dir))

    try:
        import price_oracle
        print(f"  ✓ price_oracle imported successfully")
        print(f"    - Has PriceOracle: {hasattr(price_oracle, 'PriceOracle')}")
    except Exception as e:
        print(f"  ✗ price_oracle import failed: {e}")
        return False

    try:
        import fee_oracle
        print(f"  ✓ fee_oracle imported successfully")
        print(f"    - Has FeeOracle: {hasattr(fee_oracle, 'FeeOracle')}")
    except Exception as e:
        print(f"  ✗ fee_oracle import failed: {e}")
        return False

    try:
        import mining_pool_strategy
        print(f"  ✓ mining_pool_strategy imported successfully")
        print(f"    - Has MiningPoolStrategy: {hasattr(mining_pool_strategy, 'MiningPoolStrategy')}")
    except Exception as e:
        print(f"  ✗ mining_pool_strategy import failed: {e}")
        return False

    # Test config/ files exist
    print(f"\n✓ Testing config/ files:")
    config_files = [
        'mining_pools_config.yaml',
        'price_model_config.yaml',
        'fee_model_config.yaml'
    ]

    for config_file in config_files:
        config_path = config_dir / config_file
        exists = config_path.exists()
        print(f"  {'✓' if exists else '✗'} {config_file}: {'EXISTS' if exists else 'MISSING'}")
        if not exists:
            return False

    # Test relative path construction from scenarios/
    print(f"\n✓ Testing relative paths from scenarios/:")

    # Simulate being in scenarios/ directory
    fake_scenario_file = scenarios_dir / 'test_scenario.py'

    # Test ../lib/ path
    lib_relative = os.path.join(os.path.dirname(str(fake_scenario_file)), '../lib')
    lib_resolved = Path(lib_relative).resolve()
    print(f"  ../lib/ resolves to: {lib_resolved}")
    print(f"    ✓ Exists: {lib_resolved.exists()}")

    # Test ../config/ path
    config_relative = os.path.join(os.path.dirname(str(fake_scenario_file)), '../config')
    config_resolved = Path(config_relative).resolve()
    print(f"  ../config/ resolves to: {config_resolved}")
    print(f"    ✓ Exists: {config_resolved.exists()}")

    # Test specific config file access
    test_config = config_resolved / 'mining_pools_config.yaml'
    print(f"  ../config/mining_pools_config.yaml: {'✓ EXISTS' if test_config.exists() else '✗ MISSING'}")

    return True


def test_exec_pattern():
    """Test the exec() pattern used in partition_miner_with_pools.py"""
    print("\n" + "="*70)
    print("TEST: Exec Import Pattern")
    print("="*70)

    # Simulate being in scenarios/ directory
    scenarios_dir = Path(__file__).parent.parent / 'scenarios'
    fake_file = scenarios_dir / 'test.py'

    _lib_dir = os.path.join(os.path.dirname(str(fake_file)), '../lib')

    print(f"\nSimulating: scenarios/partition_miner_with_pools.py")
    print(f"  __file__ would be: {fake_file}")
    print(f"  _lib_dir resolves to: {_lib_dir}")

    # Check if files exist
    files_to_exec = ['price_oracle.py', 'fee_oracle.py', 'mining_pool_strategy.py']

    for filename in files_to_exec:
        file_path = os.path.join(_lib_dir, filename)
        exists = os.path.exists(file_path)
        print(f"  {'✓' if exists else '✗'} {filename}: {'EXISTS' if exists else 'MISSING'}")

        if not exists:
            return False

    return True


def main():
    print("\n" + "="*70)
    print("DIRECTORY REORGANIZATION - IMPORT PATH VALIDATION")
    print("="*70)

    tests = [
        ("Scenario Imports", test_scenario_imports),
        ("Exec Pattern", test_exec_pattern),
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
        print("\n✓ All import paths are correct! Directory reorganization successful.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed - some paths may be broken")
        return 1


if __name__ == "__main__":
    sys.exit(main())
