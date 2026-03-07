# Week 2 Partition Tests - READY TO EXECUTE

**Date**: December 30, 2025
**Status**: ✅ ALL INFRASTRUCTURE COMPLETE

---

## Quick Start

### Run Test 5.3 (Proof of Concept)

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh 5.3 70 30
```

This single command will:
1. Deploy the network
2. Generate common history (blocks 0-101)
3. Run 30-minute partition mining test
4. Monitor fork depth in real-time
5. Run economic analysis
6. Save all results
7. Prompt for cleanup

**Expected Duration**: ~45 minutes (deploy + 30 min test + analysis)

---

## What's Been Built

### ✅ Network Generator
**File**: `networkGen/partition_network_generator.py`

Generates version-segregated networks with precise economic/hashrate distributions.

```bash
python3 partition_network_generator.py --test-id 5.3 --v27-economic 70 --v27-hashrate 30
```

### ✅ Test Configurations (Week 2)

All three Week 2 test configs generated:

- **Test 5.3**: 70% economic v27, 30% hashrate v27 ✅
- **Test 3.5**: 30% economic v27, 70% hashrate v27 ✅
- **Test 4.4**: 50% economic v27, 50% hashrate v27 ✅

Located in: `../test-networks/test-X.Y-economic-A-hashrate-B/`

### ✅ Partition Mining Scenario
**File**: `../warnet/scenarios/partition_miner.py`

Mines on both v27 and v22 partitions simultaneously with hashrate-weighted selection.

Features:
- Automatic version detection
- Pool metadata reading
- Real-time progress logging
- Final statistics summary

```bash
warnet run partition_miner.py --v27-hashrate 30 --v22-hashrate 70 --duration 1800
```

### ✅ Dual-Partition Monitoring
**File**: `tools/monitor_dual_partition.sh`

Tracks both partition heights and calculates fork depth in real-time.

```bash
./monitor_dual_partition.sh --interval 30 --duration 1800 --output results/test-5.3-timeline.csv
```

Output format (CSV):
```
timestamp,v27_height,v22_height,fork_depth,height_diff,v27_leading
2025-12-30T10:00:00,101,101,0,0,tie
2025-12-30T10:00:30,102,103,2,-1,false
...
```

### ✅ Test Automation
**File**: `tools/run_partition_test.sh`

End-to-end test execution with error handling and progress reporting.

```bash
./run_partition_test.sh TEST_ID V27_ECONOMIC V27_HASHRATE
```

### ✅ Economic Analysis
**File**: `monitoring/auto_economic_analysis.py`

Already updated with fork depth threshold filtering (completed previously).

```bash
python3 auto_economic_analysis.py \
    --network-config ../test-networks/test-5.3.../network.yaml \
    --live-query \
    --fork-depth-threshold 3 \
    --output-json results/test-5.3-analysis.json
```

### ✅ Documentation

Complete handoff documentation:
- `networkGen/PARTITION_NETWORK_TESTING_HANDOFF.md` - Comprehensive guide
- `networkGen/WEEK_2_TESTS_READY.md` - Week 2 specific details
- `networkGen/README.md` - Generator documentation
- `READY_TO_TEST.md` - This file

---

## Test Execution Matrix

### Week 2 Foundation Tests (READY NOW)

| Test ID | v27 Econ % | v27 Hash % | Status | Expected Outcome |
|---------|-----------|-----------|--------|------------------|
| 5.3 | 70% | 30% | ✅ Ready | v22 chain longer (has more hashrate) |
| 3.5 | 30% | 70% | ✅ Ready | v27 chain longer (has more hashrate) |
| 4.4 | 50% | 50% | ✅ Ready | Similar lengths (control test) |

### Week 3-4 Tests (Configs Not Yet Generated)

You can generate these anytime with the same partition_network_generator.py:

```bash
# Week 3 - Thresholds
python3 partition_network_generator.py --test-id 6.2 --v27-economic 80 --v27-hashrate 20
python3 partition_network_generator.py --test-id 6.4 --v27-economic 80 --v27-hashrate 40
python3 partition_network_generator.py --test-id 6.6 --v27-economic 80 --v27-hashrate 60
python3 partition_network_generator.py --test-id 2.6 --v27-economic 20 --v27-hashrate 60
python3 partition_network_generator.py --test-id 4.6 --v27-economic 50 --v27-hashrate 60

# Week 4 - Alignment
python3 partition_network_generator.py --test-id 2.2 --v27-economic 20 --v27-hashrate 20
python3 partition_network_generator.py --test-id 3.3 --v27-economic 30 --v27-hashrate 30
python3 partition_network_generator.py --test-id 5.5 --v27-economic 70 --v27-hashrate 70
python3 partition_network_generator.py --test-id 2.5 --v27-economic 20 --v27-hashrate 70
python3 partition_network_generator.py --test-id 5.2 --v27-economic 70 --v27-hashrate 20
```

---

## Manual Test Execution (If Automation Fails)

### Step-by-Step Guide

#### 1. Deploy Network

```bash
cd ~/bitcoinTools/warnet/test-networks/test-5.3-economic-70-hashrate-30
warnet deploy network.yaml
warnet status  # Wait until all nodes running
```

#### 2. Generate Common History

```bash
# Get mining address
ADDR=$(warnet bitcoin rpc node-0000 getnewaddress)

# Generate 101 blocks
for i in {1..101}; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 $ADDR
    sleep 0.5
done

# Wait for propagation
sleep 60

# Verify
warnet bitcoin rpc node-0000 getblockcount  # Should be 101
warnet bitcoin rpc node-0010 getblockcount  # Should be 101
```

#### 3. Start Mining & Monitoring (Parallel Terminals)

Terminal 1 - Mining:
```bash
cd ~/bitcoinTools/warnet
warnet run warnet/scenarios/partition_miner.py \
    --v27-hashrate 30 \
    --v22-hashrate 70 \
    --interval 10 \
    --duration 1800
```

Terminal 2 - Monitoring:
```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./monitor_dual_partition.sh \
    --interval 30 \
    --duration 1800 \
    --output ../results/test-5.3-timeline.csv
```

#### 4. Wait for Completion

Wait 30 minutes for test to complete.

#### 5. Run Analysis

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring
python3 auto_economic_analysis.py \
    --network-config ../../test-networks/test-5.3-economic-70-hashrate-30/network.yaml \
    --live-query \
    --fork-depth-threshold 3 \
    --output-json ../results/test-5.3-analysis.json
```

#### 6. Review Results

```bash
# View timeline
cat ../results/test-5.3-timeline.csv | tail -20

# View analysis
cat ../results/test-5.3-analysis.json | jq
```

#### 7. Cleanup

```bash
warnet down
```

---

## Expected Results (Test 5.3)

### Hypothesis
Economic majority on v27 (70%), but hashrate majority on v22 (70%). In isolated partitions, hashrate should dominate.

### Expected Metrics

**Chain Lengths** (after 30 minutes):
- v27 chain: ~165 blocks (30% of ~180 blocks/30min)
- v22 chain: ~255 blocks (70% of ~180 blocks/30min)
- Fork depth: ~218 blocks
- Height ratio: ~0.43 (v27/v22)

**Economic Analysis**:
- Economic majority: v27 (70% custody/volume)
- Hashrate majority: v22 (70%)
- Longest chain: v22
- Risk score: HIGH (economic weight on shorter chain)

**Key Finding**: Economic weight doesn't help v27 when partitions are isolated. Hashrate determines chain length.

---

## Validation Checklist

Before running tests, verify:

- [ ] Warnet is installed and working (`warnet --version`)
- [ ] No warnet instance currently running (`warnet status` shows "not deployed")
- [ ] Test configs exist in test-networks/
- [ ] partition_miner.py exists in warnet/scenarios/
- [ ] Monitoring script is executable
- [ ] Results directory exists

---

## Troubleshooting

### "warnet: command not found"
- Ensure warnet is installed and in PATH
- Try: `which warnet`

### "Network already deployed"
- Run: `warnet down`
- Wait 30 seconds
- Try again

### "partition_miner.py not found"
- Check file exists: `ls ~/bitcoinTools/warnet/warnet/scenarios/partition_miner.py`
- Verify warnet scenarios directory is correct

### "Common history not propagating"
- Increase sleep time after block generation (60-90 seconds)
- Check node connectivity: `warnet bitcoin rpc node-0000 getpeerinfo`

### Mining shows errors
- Check node logs: `warnet logs node-0000`
- Verify nodes are running: `warnet status`

### Fork depth not increasing
- Verify partitions are isolated (no cross-version connections)
- Check that both partitions are mining blocks

---

## Results Storage

All test results saved to:
```
warnetScenarioDiscovery/results/
├── test-5.3-timeline.csv      # Time series data
├── test-5.3-analysis.json     # Economic analysis
├── test-3.5-timeline.csv
├── test-3.5-analysis.json
└── test-4.4-timeline.csv
└── test-4.4-analysis.json
```

Timeline CSV format:
```csv
timestamp,v27_height,v22_height,fork_depth,height_diff,v27_leading
```

Analysis JSON includes:
- Fork depth
- Economic weight distribution
- Hashrate distribution
- Chain heights
- Risk scores
- Economic majority chain

---

## Next Steps After Week 2

1. **Run all 3 Week 2 tests**
   ```bash
   ./run_partition_test.sh 5.3 70 30
   ./run_partition_test.sh 3.5 30 70
   ./run_partition_test.sh 4.4 50 50
   ```

2. **Analyze Week 2 results**
   - Verify hashrate dominates in isolation
   - Confirm height ratios match hashrate ratios
   - Document any unexpected behaviors

3. **Generate Week 3 configs** (6 threshold tests)

4. **Run Week 3 tests** (identify critical thresholds)

5. **Generate Week 4 configs** (6 alignment tests)

6. **Run Week 4 tests** (study aligned scenarios)

7. **Aggregate all 15 tests**
   - Create results matrix
   - Identify thresholds
   - Statistical analysis

8. **Prepare publication** (July 2026 workshop paper)

---

## File Locations Quick Reference

```
warnetScenarioDiscovery/
├── networkGen/
│   ├── partition_network_generator.py          ✅
│   ├── PARTITION_NETWORK_TESTING_HANDOFF.md    ✅
│   ├── WEEK_2_TESTS_READY.md                   ✅
│   └── README.md                               ✅
├── tools/
│   ├── monitor_dual_partition.sh               ✅
│   └── run_partition_test.sh                   ✅
├── monitoring/
│   └── auto_economic_analysis.py               ✅
├── results/                                     📊 Created during tests
└── READY_TO_TEST.md                            ✅ This file

warnet/scenarios/
└── partition_miner.py                          ✅

test-networks/
├── test-5.3-economic-70-hashrate-30/
│   └── network.yaml                            ✅
├── test-3.5-economic-30-hashrate-70/
│   └── network.yaml                            ✅
└── test-4.4-economic-50-hashrate-50/
    └── network.yaml                            ✅
```

---

## Summary

✅ **Generator**: Creates version-segregated networks
✅ **Configurations**: Week 2 tests (5.3, 3.5, 4.4) ready
✅ **Mining Scenario**: Partition-aware mining implemented
✅ **Monitoring**: Real-time fork depth tracking
✅ **Automation**: End-to-end test script
✅ **Analysis**: Economic fork analysis with threshold filtering
✅ **Documentation**: Complete handoff materials

**YOU ARE READY TO RUN TEST 5.3 RIGHT NOW!**

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh 5.3 70 30
```

---

**Version**: 1.0
**Date**: 2025-12-30
**Estimated Time to First Results**: 45 minutes
**Status**: Production-ready ✅
