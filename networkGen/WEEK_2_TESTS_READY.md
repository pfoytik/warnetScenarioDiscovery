# Week 2 Foundation Tests - READY TO EXECUTE

**Date**: December 30, 2025
**Status**: ✅ All configurations generated successfully

---

## Summary

All three Week 2 foundation test configurations have been generated and are ready for deployment and testing.

---

## Generated Test Configurations

### Test 5.3 ✅
**Configuration**: 70% economic on v27, 30% hashrate on v27

**File**: `../../test-networks/test-5.3-economic-70-hashrate-30/network.yaml`

**Actual Distribution**:
- v27 partition (nodes 0-9): 70% economic weight, **31.46%** hashrate
- v22 partition (nodes 10-19): 30% economic weight, **66.91%** hashrate
- Total nodes: 20
- Total edges: 27
- Cross-partition edges: 0 ✅

**Expected Outcome**: Economic majority on v27, hashrate majority on v22. Question: Can economic weight overcome hashrate deficit?

---

### Test 3.5 ✅
**Configuration**: 30% economic on v27, 70% hashrate on v27

**File**: `../../test-networks/test-3.5-economic-30-hashrate-70/network.yaml`

**Actual Distribution**:
- v27 partition (nodes 0-9): 30% economic weight, **70.20%** hashrate
- v22 partition (nodes 10-19): 70% economic weight, **28.17%** hashrate
- Total nodes: 20
- Total edges: 50
- Cross-partition edges: 0 ✅

**Expected Outcome**: Inverse of Test 5.3. Economic minority on v27, hashrate majority on v27. Confirms hashrate dominance in isolated partitions?

---

### Test 4.4 ✅
**Configuration**: 50% economic on v27, 50% hashrate on v27

**File**: `../../test-networks/test-4.4-economic-50-hashrate-50/network.yaml`

**Actual Distribution**:
- v27 partition (nodes 0-9): 50% economic weight, **50.71%** hashrate
- v22 partition (nodes 10-19): 50% economic weight, **47.66%** hashrate
- Total nodes: 20
- Total edges: 36
- Cross-partition edges: 0 ✅

**Expected Outcome**: Control test with parity. Both partitions should grow at similar rates (random walk).

---

## Pool Distribution Accuracy

All tests achieved excellent pool distribution accuracy:

| Test | Target v27 Hashrate | Actual v27 Hashrate | Error |
|------|-------------------|-------------------|-------|
| 5.3  | 30%              | 31.46%           | +1.46% |
| 3.5  | 70%              | 70.20%           | +0.20% |
| 4.4  | 50%              | 50.71%           | +0.71% |

**Note**: Small variations are due to discrete pool sizes from real-world distribution. All within acceptable tolerance.

---

## Real Pool Distribution Used

All tests use actual Bitcoin network pool hashrate data:

1. Foundry USA: 26.89%
2. AntPool: 19.25%
3. ViaBTC: 11.39%
4. F2Pool: 11.25%
5. Binance Pool: 10.04%
6. MARA Pool: 8.25%
7. SBI Crypto: 4.57%
8. Luxor: 3.94%
9. OCEAN: 1.42%
10. Braiins Pool: 1.37%

These pools are intelligently distributed between v27 and v22 partitions using a greedy assignment algorithm to match target hashrate percentages.

---

## Economic Weight Distribution

**Total Network Capacity**:
- Total custody: 4,000,000 BTC
- Total volume: 420,000 BTC/day

**Test 5.3 Example** (70% v27 economic):
- v27 partition: 2,800,000 BTC custody, 294,000 BTC/day volume
- v22 partition: 1,200,000 BTC custody, 126,000 BTC/day volume

**Test 3.5 Example** (30% v27 economic):
- v27 partition: 1,200,000 BTC custody, 126,000 BTC/day volume
- v22 partition: 2,800,000 BTC custody, 294,000 BTC/day volume

**Test 4.4 Example** (50% v27 economic):
- v27 partition: 2,000,000 BTC custody, 210,000 BTC/day volume
- v22 partition: 2,000,000 BTC custody, 210,000 BTC/day volume

Within each partition, economic weight is distributed using a power-law (harmonic series) among economic nodes.

---

## What's Needed to Run Tests

### Critical Components (Not Yet Created)

1. **partition_miner.py** ⏳
   - Mining scenario that operates on both partitions
   - Hashrate-weighted block production
   - No fork choice logic (each partition independent)
   - Estimated implementation: 15-20 minutes

2. **monitor_dual_partition.sh** ⏳
   - Real-time monitoring of both partition heights
   - Calculates fork depth: `v27_height + v22_height - 202`
   - Outputs time series CSV
   - Estimated implementation: 5-10 minutes

3. **Network Partition Enforcement** ⏳
   - Kubernetes network policy OR manual disconnection
   - Ensures v27 and v22 nodes cannot communicate
   - Estimated implementation: 10 minutes

### Optional But Recommended

4. **run_partition_test.sh** ⏳
   - End-to-end test automation
   - Reduces manual steps and errors
   - Estimated implementation: 20 minutes

5. **aggregate_results.py** ⏳
   - Structured results aggregation
   - Enables cross-test comparison
   - Estimated implementation: 30 minutes

---

## Quick Start Guide

### Option A: Manual Test Execution (Once Scripts Ready)

```bash
# 1. Deploy Test 5.3
cd ~/bitcoinTools/warnet/test-networks/test-5.3-economic-70-hashrate-30
warnet deploy network.yaml
warnet status  # Wait for all pods running

# 2. Create common history (blocks 0-101)
for i in {1..101}; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 bcrt1q...
    sleep 0.5
done
sleep 60  # Allow propagation

# 3. Verify common history
warnet bitcoin rpc node-0000 getblockcount  # Should be 101
warnet bitcoin rpc node-0010 getblockcount  # Should be 101

# 4. Enforce network partition
kubectl apply -f ../partition-network-policy.yaml

# 5. Run mining (30 minutes)
warnet run partition_miner.py --v27-hashrate 30 --v22-hashrate 70 --duration 1800 &

# 6. Monitor in parallel
cd ../../warnetScenarioDiscovery/tools
./monitor_dual_partition.sh --interval 30 --duration 1800 > ../results/test-5.3-timeline.csv &

# 7. Wait for completion (30 minutes)
wait

# 8. Run economic analysis
cd ../monitoring
python3 auto_economic_analysis.py \
    --network-config ../../test-networks/test-5.3-economic-70-hashrate-30/network.yaml \
    --live-query \
    --fork-depth-threshold 3 \
    --output-json ../results/test-5.3-analysis.json

# 9. Cleanup
warnet down
```

### Option B: Automated Execution (Once run_partition_test.sh Ready)

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools

# Run single test
./run_partition_test.sh 5.3 70 30

# Run all Week 2 tests sequentially
./run_partition_test.sh 5.3 70 30
./run_partition_test.sh 3.5 30 70
./run_partition_test.sh 4.4 50 50

# Aggregate results
python3 aggregate_results.py --tests 5.3,3.5,4.4 --output ../results/week2_summary.csv
```

---

## Expected Results

### Test 5.3 (Economic majority v27, Hashrate majority v22)

**Hypothesis**: Hashrate dominates in isolated networks

**Expected**:
- v22 chain grows faster (70% hashrate vs 30%)
- Final heights: v22 >> v27
- Fork depth: Large (~200+ blocks after 30 min)
- Economic analysis: Shows economic weight concentrated on shorter chain

**Key Metric**: Ratio of chain lengths should approximate hashrate ratio (70:30 ≈ 2.33:1)

### Test 3.5 (Economic majority v22, Hashrate majority v27)

**Hypothesis**: Confirms inverse of 5.3

**Expected**:
- v27 chain grows faster (70% hashrate vs 30%)
- Final heights: v27 >> v22
- Fork depth: Large (~200+ blocks)
- Economic analysis: Shows economic weight concentrated on shorter chain

**Key Metric**: Should mirror 5.3 results but inverted

### Test 4.4 (Parity on both dimensions)

**Hypothesis**: Control test, random walk behavior

**Expected**:
- Both chains grow at similar rates
- Final heights: v27 ≈ v22 (within ~10% variance)
- Fork depth: Moderate (~100-150 blocks)
- Economic analysis: Shows balanced risk

**Key Metric**: Height ratio should be close to 1:1

---

## Data Collection Plan

### Timeline Data (CSV)

**File**: `results/test-X.Y-timeline.csv`

**Format**:
```csv
timestamp,v27_height,v22_height,fork_depth
2025-12-30T10:00:00,101,101,0
2025-12-30T10:00:30,102,102,2
2025-12-30T10:01:00,104,103,5
...
```

**Frequency**: Every 30 seconds
**Duration**: 30 minutes (60 data points)

### Economic Analysis (JSON)

**File**: `results/test-X.Y-analysis.json`

**Key Fields**:
- Fork depth
- Economic weight per chain
- Hashrate per chain
- Risk scores
- Chain length comparison

### Aggregate Summary (CSV)

**File**: `results/week2_summary.csv`

**Columns**:
- test_id
- v27_economic_pct
- v27_hashrate_pct
- final_v27_height
- final_v22_height
- final_fork_depth
- height_ratio
- economic_majority_chain
- hashrate_majority_chain
- longest_chain

---

## Success Criteria

Week 2 tests will be considered successful if:

✅ All 3 tests complete without errors
✅ Fork depth >= 100 blocks (sufficient divergence)
✅ Chain length ratios approximately match hashrate ratios
✅ Economic analysis completes successfully
✅ Timeline data shows consistent block production
✅ Results are reproducible (re-running same test gives similar results)

---

## Validation Checklist

Before considering Week 2 complete:

- [ ] Test 5.3 executed successfully
- [ ] Test 3.5 executed successfully
- [ ] Test 4.4 executed successfully
- [ ] All timeline CSVs collected
- [ ] All analysis JSONs generated
- [ ] Week 2 summary CSV created
- [ ] Results validate hypothesis (hashrate dominates in isolation)
- [ ] Methodology documented for Week 3/4

---

## Files Generated

```
test-networks/
├── test-5.3-economic-70-hashrate-30/
│   └── network.yaml                    ✅ Generated
├── test-3.5-economic-30-hashrate-70/
│   └── network.yaml                    ✅ Generated
└── test-4.4-economic-50-hashrate-50/
    └── network.yaml                    ✅ Generated

results/
├── test-5.3-timeline.csv               ⏳ After test run
├── test-5.3-analysis.json              ⏳ After test run
├── test-3.5-timeline.csv               ⏳ After test run
├── test-3.5-analysis.json              ⏳ After test run
├── test-4.4-timeline.csv               ⏳ After test run
├── test-4.4-analysis.json              ⏳ After test run
└── week2_summary.csv                   ⏳ After aggregation
```

---

## Next Steps

### Immediate (To Run Tests)

1. **Implement partition_miner.py** (~15 min)
   - See PARTITION_NETWORK_TESTING_HANDOFF.md for detailed spec
   - Core logic: alternate between partitions with hashrate weighting

2. **Implement monitor_dual_partition.sh** (~5 min)
   - Query both partition heights every 30s
   - Calculate and output fork depth

3. **Create network partition policy** (~10 min)
   - Kubernetes NetworkPolicy to isolate v27 from v22
   - OR manual disconnection script

4. **Run Test 5.3** (~45 min)
   - Validate workflow
   - Identify any issues
   - Document learnings

### Short-term (Week 2 Completion)

5. **Run Test 3.5 and 4.4** (~90 min total)
6. **Aggregate Week 2 results** (~30 min)
7. **Document findings** (~60 min)
8. **Prepare for Week 3** (generate 6 threshold test configs)

---

## Reference Documentation

- **Complete Handoff Guide**: `PARTITION_NETWORK_TESTING_HANDOFF.md`
- **Generator README**: `README.md`
- **Configurable Generator Docs**: `CONFIGURABLE_NETWORK_GENERATOR.md`

---

**Status**: Week 2 foundation tests are configured and ready. Implementation of mining and monitoring scripts is the only remaining blocker.

**Estimated Time to First Test Results**: 1-2 hours (implementation + test run)

---

**Document Version**: 1.0
**Date**: 2025-12-30
**Author**: Claude Sonnet 4.5
