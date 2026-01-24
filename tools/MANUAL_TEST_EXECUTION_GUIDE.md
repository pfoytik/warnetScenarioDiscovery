# Manual Test Execution Guide - Tier 1 & 2 Partition Tests

This guide explains how to manually run each of the 17 partition tests sequentially.

## Prerequisites

- All 17 test networks generated in `/home/pfoytik/bitcoinTools/warnet/test-networks/`
- Warnet installed and working
- Minimum 30 minutes per test (1800 seconds)

## Test List (17 total)

### TIER 1: Edge Case Validation (3 tests)
1. `test-1.1-E95-H10-dynamic` - 95% economic, 10% hashrate on v27
2. `test-1.2-E10-H95-dynamic` - 10% economic, 95% hashrate on v27
3. `test-1.3-E90-H90-dynamic` - 90% economic, 90% hashrate on v27

### TIER 2 - Series A: Economic Override Threshold (5 tests)
4. `test-2.1-E50-H40-dynamic` - 50% economic, 40% hashrate on v27
5. `test-2.2-E60-H40-dynamic` - 60% economic, 40% hashrate on v27
6. `test-2.3-E70-H40-dynamic` - 70% economic, 40% hashrate on v27
7. `test-2.4-E80-H40-dynamic` - 80% economic, 40% hashrate on v27
8. `test-2.5-E90-H40-dynamic` - 90% economic, 40% hashrate on v27

### TIER 2 - Series B: Hashrate Resistance Threshold (4 tests)
9. `test-2.6-E70-H20-dynamic` - 70% economic, 20% hashrate on v27
10. `test-2.8-E70-H40-dynamic` - 70% economic, 40% hashrate on v27
11. `test-2.9-E70-H45-dynamic` - 70% economic, 45% hashrate on v27
12. `test-2.10-E70-H49-dynamic` - 70% economic, 49% hashrate on v27

### TIER 2 - Series C: Critical Balance Zone (5 tests)
13. `test-2.11-E50-H50-dynamic` - 50% economic, 50% hashrate on v27
14. `test-2.12-E52-H48-dynamic` - 52% economic, 48% hashrate on v27
15. `test-2.13-E48-H52-dynamic` - 48% economic, 52% hashrate on v27
16. `test-2.14-E55-H55-dynamic` - 55% economic, 55% hashrate on v27
17. `test-2.15-E45-H45-dynamic` - 45% economic, 45% hashrate on v27

## Manual Execution Steps

For each test, follow these steps:

### Step 1: Ensure Clean State
```bash
cd /home/pfoytik/bitcoinTools/warnet
warnet down --force
# Wait 30 seconds for cleanup
sleep 30
```

### Step 2: Run the Test
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools

# For test-1.1-E95-H10-dynamic (example)
./run_partition_test.sh test-1.1-E95-H10-dynamic 95 10 --partition-mode dynamic --duration 1800
```

### Step 3: Monitor Progress
The test will:
1. Deploy the network
2. Wait for network to stabilize (60s)
3. Create dynamic partition using setban RPC
4. Run economic mining scenario for 30 minutes
5. Collect final metrics
6. Generate analysis report

You can monitor in another terminal:
```bash
# Watch warnet status
watch -n 10 'warnet status | head -50'

# Check mining progress
warnet status | grep -A 5 "Scenario"

# Monitor logs
tail -f /tmp/tier-1-2-test-logs/test-*.log
```

### Step 4: Review Results
After completion, check:
```bash
# Analysis file
cat ~/bitcoinTools/warnet/warnetScenarioDiscovery/results/test-<test-id>-analysis.txt

# Timeline CSV
cat ~/bitcoinTools/warnet/warnetScenarioDiscovery/results/test-<test-id>-timeline.csv

# Look for:
# - Fork detected
# - Consensus chain
# - Economic weight split
# - Risk score
```

## Issues & Workarounds

### Issue 1: First Network Generation
**Problem**: test-1.1 was created as a file instead of directory
**Status**: FIXED - Regenerated correctly

### Issue 2: `warnet down --force` Still Prompts
**Problem**: The `--force` flag may still prompt for confirmation in some versions
**Status**: SOLVED - Use kubectl instead
**Solution**: Use kubectl to delete all pods:
```bash
kubectl delete pods --all -n default --wait=true --timeout=120s
sleep 5  # Wait for cleanup to complete
```
This bypasses warnet's interactive prompts entirely and is now used in the automated test script.

### Issue 3: Missing Economic Data in Analysis
**Problem**: Analysis shows only 10/20 nodes
**Explanation**: This is EXPECTED behavior. The analysis script:
- Detects all nodes (shows "Economic nodes: 20")
- Shows only the top 2 chains by economic weight
- Nodes on minor chains (3rd, 4th, etc.) are counted but not displayed
- All nodes DO have economic metadata in the network.yaml

## Quick Reference: Running All Tests Manually

```bash
# Set duration (30 minutes = 1800 seconds)
DURATION=1800

# Test 1: test-1.1-E95-H10-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-1.1-E95-H10-dynamic 95 10 --partition-mode dynamic --duration $DURATION

# Test 2: test-1.2-E10-H95-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-1.2-E10-H95-dynamic 10 95 --partition-mode dynamic --duration $DURATION

# Test 3: test-1.3-E90-H90-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-1.3-E90-H90-dynamic 90 90 --partition-mode dynamic --duration $DURATION

# Test 4: test-2.1-E50-H40-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.1-E50-H40-dynamic 50 40 --partition-mode dynamic --duration $DURATION

# Test 5: test-2.2-E60-H40-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.2-E60-H40-dynamic 60 40 --partition-mode dynamic --duration $DURATION

# Test 6: test-2.3-E70-H40-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.3-E70-H40-dynamic 70 40 --partition-mode dynamic --duration $DURATION

# Test 7: test-2.4-E80-H40-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.4-E80-H40-dynamic 80 40 --partition-mode dynamic --duration $DURATION

# Test 8: test-2.5-E90-H40-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.5-E90-H40-dynamic 90 40 --partition-mode dynamic --duration $DURATION

# Test 9: test-2.6-E70-H20-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.6-E70-H20-dynamic 70 20 --partition-mode dynamic --duration $DURATION

# Test 10: test-2.8-E70-H40-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.8-E70-H40-dynamic 70 40 --partition-mode dynamic --duration $DURATION

# Test 11: test-2.9-E70-H45-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.9-E70-H45-dynamic 70 45 --partition-mode dynamic --duration $DURATION

# Test 12: test-2.10-E70-H49-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.10-E70-H49-dynamic 70 49 --partition-mode dynamic --duration $DURATION

# Test 13: test-2.11-E50-H50-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.11-E50-H50-dynamic 50 50 --partition-mode dynamic --duration $DURATION

# Test 14: test-2.12-E52-H48-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.12-E52-H48-dynamic 52 48 --partition-mode dynamic --duration $DURATION

# Test 15: test-2.13-E48-H52-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.13-E48-H52-dynamic 48 52 --partition-mode dynamic --duration $DURATION

# Test 16: test-2.14-E55-H55-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.14-E55-H55-dynamic 55 55 --partition-mode dynamic --duration $DURATION

# Test 17: test-2.15-E45-H45-dynamic
cd /home/pfoytik/bitcoinTools/warnet && warnet down --force && sleep 30
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh test-2.15-E45-H45-dynamic 45 45 --partition-mode dynamic --duration $DURATION
```

## Expected Output Files

For each test `<test-id>`, you should get:
- `~/bitcoinTools/warnet/warnetScenarioDiscovery/results/test-<test-id>-analysis.txt`
- `~/bitcoinTools/warnet/warnetScenarioDiscovery/results/test-<test-id>-timeline.csv`

## Estimated Completion Time

- 17 tests × 30 minutes each = 8.5 hours
- Plus cleanup time between tests (~30 seconds × 16) = 8 minutes
- **Total: ~8 hours 38 minutes**

## Troubleshooting

1. **Network won't deploy**: Check `warnet status`, ensure previous network is fully down
2. **Partition fails**: Check logs in `/tmp/partition_test_*.log`
3. **No blocks being mined**: Verify economic_miner scenario is running with `warnet status`
4. **Analysis shows no fork**: The test may not have run long enough, or partition wasn't successful

## Next Steps After Completion

1. Collect all analysis files
2. Compare results across Series A (economic threshold sweep)
3. Compare results across Series B (hashrate threshold sweep)
4. Compare results across Series C (critical balance zone)
5. Identify threshold values where economic consensus overrides hashpower
6. Generate final report with findings
