# Automated Test Execution - Tier 1 & 2 Tests

This guide explains how to use the automated test runner to execute all 17 partition tests sequentially.

## Overview

The automated test runner (`run_tier_1_2_tests.sh`) handles:
- Sequential execution of all 17 tests
- Automatic cleanup between tests using kubectl
- Detailed logging for each test
- Progress tracking and final summary

## Prerequisites

- All 17 test networks generated in `/home/pfoytik/bitcoinTools/warnet/test-networks/`
- Warnet installed and working
- kubectl access to default namespace
- No network currently running (run cleanup first if needed)

## Quick Start

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_tier_1_2_tests.sh
```

## What the Script Does

1. **Runs each test sequentially** (17 tests total)
   - Each test runs for 30 minutes (1800 seconds)
   - Deploys network, creates partition, runs mining scenario
   - Generates analysis report and timeline CSV

2. **Automatic cleanup between tests**
   - Uses `kubectl delete pods --all -n default` to bring down network
   - Waits 5 seconds for cleanup to complete
   - Waits 30 additional seconds before starting next test
   - No interactive prompts required

3. **Progress tracking**
   - Shows which test is running
   - Displays configuration (economic/hashrate split)
   - Logs all output to individual files

4. **Final summary**
   - Total time elapsed
   - Success/failure count
   - List of generated result files

## Test Execution Order

The script runs tests in this order:

**TIER 1: Edge Case Validation (3 tests)**
1. test-1.1-E95-H10-dynamic - 95% economic, 10% hashrate on v27
2. test-1.2-E10-H95-dynamic - 10% economic, 95% hashrate on v27
3. test-1.3-E90-H90-dynamic - 90% economic, 90% hashrate on v27

**TIER 2 - Series A: Economic Override Threshold (5 tests)**
4. test-2.1-E50-H40-dynamic - 50% economic, 40% hashrate on v27
5. test-2.2-E60-H40-dynamic - 60% economic, 40% hashrate on v27
6. test-2.3-E70-H40-dynamic - 70% economic, 40% hashrate on v27
7. test-2.4-E80-H40-dynamic - 80% economic, 40% hashrate on v27
8. test-2.5-E90-H40-dynamic - 90% economic, 40% hashrate on v27

**TIER 2 - Series B: Hashrate Resistance Threshold (4 tests)**
9. test-2.6-E70-H20-dynamic - 70% economic, 20% hashrate on v27
10. test-2.8-E70-H40-dynamic - 70% economic, 40% hashrate on v27
11. test-2.9-E70-H45-dynamic - 70% economic, 45% hashrate on v27
12. test-2.10-E70-H49-dynamic - 70% economic, 49% hashrate on v27

**TIER 2 - Series C: Critical Balance Zone (5 tests)**
13. test-2.11-E50-H50-dynamic - 50% economic, 50% hashrate on v27
14. test-2.12-E52-H48-dynamic - 52% economic, 48% hashrate on v27
15. test-2.13-E48-H52-dynamic - 48% economic, 52% hashrate on v27
16. test-2.14-E55-H55-dynamic - 55% economic, 55% hashrate on v27
17. test-2.15-E45-H45-dynamic - 45% economic, 45% hashrate on v27

## Monitoring Progress

### In Real-Time

In another terminal window, you can monitor:

```bash
# Watch test logs
tail -f /tmp/tier-1-2-test-logs/<test-id>.log

# Check warnet status
watch -n 10 'warnet status | head -50'

# Monitor blocks being mined
watch -n 5 'warnet bitcoin rpc node-0000 getblockcount'
```

### Check Individual Test Logs

```bash
# List all test logs
ls -lh /tmp/tier-1-2-test-logs/

# View specific test log
cat /tmp/tier-1-2-test-logs/test-1.1-E95-H10-dynamic.log
```

## Output Files

After completion, you'll find:

**Test Logs**: `/tmp/tier-1-2-test-logs/`
- One log file per test
- Contains full output from each test run

**Analysis Results**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/results/`
- `test-<test-id>-analysis.txt` - BCAP framework analysis
- `test-<test-id>-timeline.csv` - Fork progression over time

## Estimated Time

- **17 tests × 30 minutes** = 8.5 hours
- **Plus cleanup time** (~30 seconds × 16) = 8 minutes
- **Total: ~8 hours 38 minutes**

## Stopping the Script

If you need to stop the script:

1. Press `Ctrl+C` to interrupt
2. Clean up the current network:
   ```bash
   kubectl delete pods --all -n default --wait=true --timeout=120s
   ```

## Manual Cleanup (if needed)

If a test fails or you need to manually clean up:

```bash
# Delete all pods
kubectl delete pods --all -n default --wait=true --timeout=120s

# Wait for cleanup
sleep 5

# Verify network is down
warnet status
# Should show "Total Tanks: 0"
```

## Resuming After Interruption

To resume from a specific test, edit the `TESTS` array in `run_tier_1_2_tests.sh`:

1. Comment out completed tests (add `#` at start of line)
2. Keep remaining tests uncommented
3. Run the script again

Example - to start from test-2.3:
```bash
declare -a TESTS=(
    # TIER 1: Edge Case Validation (3 tests)
    #"test-1.1-E95-H10-dynamic 95 10"
    #"test-1.2-E10-H95-dynamic 10 95"
    #"test-1.3-E90-H90-dynamic 90 90"

    # TIER 2 - Series A: Economic Override Threshold (5 tests)
    #"test-2.1-E50-H40-dynamic 50 40"
    #"test-2.2-E60-H40-dynamic 60 40"
    "test-2.3-E70-H40-dynamic 70 40"  # Start here
    "test-2.4-E80-H40-dynamic 80 40"
    # ... rest of tests
)
```

## Troubleshooting

### Network Won't Deploy
**Problem**: Test fails to deploy network
**Solution**:
- Check previous network is fully down: `warnet status`
- Manual cleanup: `kubectl delete pods --all -n default`
- Wait 30 seconds and retry

### Tests Failing
**Problem**: Multiple tests reporting failures
**Solution**:
- Check individual test logs in `/tmp/tier-1-2-test-logs/`
- Look for error patterns
- Verify test networks exist in `/home/pfoytik/bitcoinTools/warnet/test-networks/`

### kubectl Access Issues
**Problem**: kubectl commands fail
**Solution**:
- Verify kubectl is installed: `kubectl version`
- Check cluster access: `kubectl get namespaces`
- Ensure you have permissions to delete pods in default namespace

## After All Tests Complete

1. **Review summary**
   - Check success/failure counts
   - Note any failed tests

2. **Analyze results**
   - Compare economic threshold tests (Series A)
   - Compare hashrate threshold tests (Series B)
   - Examine critical balance zone (Series C)

3. **Generate final report**
   - Identify threshold where economic consensus overrides hashpower
   - Document findings from all 17 tests

## Script Location

`/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools/run_tier_1_2_tests.sh`

## Key Improvement: kubectl Cleanup

The automated script uses `kubectl delete pods` instead of `warnet down --force` because:
- Bypasses interactive prompts entirely
- Fully automated, no user input required
- Reliable and fast (~5 seconds)
- Confirmed to work with `warnet status` verification

This enables true unattended execution of all 17 tests.
