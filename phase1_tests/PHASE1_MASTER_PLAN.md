# Phase 1: Systematic Scenario Execution - Master Test Plan

**Timeline**: Weeks 2-6
**Status**: 🟢 READY TO EXECUTE

---

## Overview

Phase 1 executes systematic tests on all 4 scenarios created in Phase 0, validating the dual-metric economic fork analyzer under controlled conditions.

### Objectives

1. **Validate fork detection** in deployed Warnet networks
2. **Confirm economic analysis accuracy** for each scenario type
3. **Document consensus behavior** under different custody/volume distributions
4. **Establish baseline metrics** for future testing

---

## Test Scenarios

| # | Scenario | Risk Profile | Primary Test Goal |
|---|----------|--------------|-------------------|
| 1 | **critical-50-50-split** | Near-balanced custody | Test risk detection at near-parity |
| 2 | **custody-volume-conflict** | Custody vs volume tension | Validate 70/30 weighting |
| 3 | **single-major-exchange-fork** | Network isolation | Test network majority power |
| 4 | **dual-metric-test** | Baseline validation | Confirm fundamental model correctness |

---

## Test Execution Sequence

### Week 2: Test 1 - critical-50-50-split

**Duration**: 2 days
**Method**: Artificial fork (controlled block mining)

**Steps**:
1. Deploy network (5 nodes, v26 vs v27 split)
2. Mine initial blocks to maturity (101 blocks)
3. Create competing chains:
   - Chain A (v26): Mine on exchange-conservative + custody-provider
   - Chain B (v27): Mine on exchange-progressive-1 + exchange-progressive-2
4. Analyze fork with economic analyzer
5. Document results

**Expected Outcome**:
- Fork detected: 2 chains
- Chain B wins (higher volume despite lower custody)
- Risk score: 25-35/100 (LOW)

### Week 3: Test 2 - custody-volume-conflict

**Duration**: 2 days
**Method**: Extreme profile isolation

**Steps**:
1. Deploy network (4 nodes, custody vs volume extremes)
2. Mine initial blocks
3. Create fork:
   - Chain A (v26): Mine on custody-provider (high custody, low volume)
   - Chain B (v27): Mine on payment-processor-1 + payment-processor-2 (low custody, high volume)
4. Analyze economic impact
5. Validate 70/30 weighting behavior

**Expected Outcome**:
- Chain B wins (volume overcomes custody at extreme levels)
- Demonstrates operational chokepoint power
- Risk score: 20-25/100 (LOW)

### Week 4: Test 3 - single-major-exchange-fork

**Duration**: 2 days
**Method**: Network majority isolation

**Steps**:
1. Deploy network (4 major exchanges)
2. Mine initial blocks
3. Create fork:
   - Chain A (v26): Mine on coinbase (isolated major player)
   - Chain B (v27): Mine on binance + kraken + gemini (network majority)
4. Analyze network effect vs individual custody power
5. Document isolation dynamics

**Expected Outcome**:
- Chain B wins (network majority isolates Coinbase)
- Binance alone has more weight than Coinbase
- Risk score: 20-25/100 (LOW)

### Week 5: Test 4 - dual-metric-test (Baseline)

**Duration**: 2 days
**Method**: Natural fork from continuous mining

**Steps**:
1. Deploy network (5 nodes, baseline configuration)
2. Run continuous mining test (longer duration)
3. Wait for natural forks from propagation delays
4. Analyze all detected forks automatically
5. Establish baseline behavior

**Expected Outcome**:
- Multiple transient forks detected
- All resolve to consensus (no sustained split)
- Economic analysis validates expected chain
- Risk score varies per fork event

### Week 6: Analysis and Documentation

**Duration**: 1 week
**Tasks**:
1. Aggregate results from all 4 tests
2. Compare expected vs actual outcomes
3. Identify any anomalies or unexpected behaviors
4. Document lessons learned
5. Update model if needed

---

## Test Methodology

### Pre-Test Checklist

```bash
# 1. Verify Warnet environment
kubectl cluster-info
warnet --version

# 2. Check available resources
kubectl get nodes
kubectl get pods --all-namespaces

# 3. Clean up any previous deployments
warnet down
kubectl delete namespace warnet --ignore-not-found

# 4. Verify test scripts executable
ls -la phase1_tests/*.sh
```

### Standard Test Procedure

Each test follows this standard procedure:

#### 1. Deployment
```bash
# Deploy scenario
warnet deploy test-networks/SCENARIO_NAME/

# Verify deployment (wait for all Running)
kubectl get pods -n warnet -w

# Check network status
warnet status
```

#### 2. Initial Block Mining
```bash
# Mine 101 blocks for maturity (coinbase maturity = 100)
warnet run scenarios/miner_std.py --mature --interval 5

# Verify all nodes at same height
for node in NODE_LIST; do
  warnet bitcoin rpc $node getblockcount
done
```

#### 3. Fork Creation

**Method A: Artificial Fork (Controlled)**
```bash
# Disconnect nodes if needed
# (Warnet doesn't have direct disconnect, so we mine competing blocks)

# Mine on Chain A nodes
warnet bitcoin rpc NODE_A generatetoaddress 5 ADDRESS_A

# Mine on Chain B nodes
warnet bitcoin rpc NODE_B generatetoaddress 5 ADDRESS_B

# Verify fork exists
for node in ALL_NODES; do
  echo "$node: $(warnet bitcoin rpc $node getblockcount) $(warnet bitcoin rpc $node getbestblockhash)"
done
```

**Method B: Natural Fork (Continuous Mining)**
```bash
# Start continuous mining
cd ../tools
./continuous_mining_test.sh --interval 5 --duration 1800 --nodes allnodes

# Monitor for forks
tail -f ../test_results/continuous_mining_*/forks_detected.log
```

#### 4. Economic Analysis
```bash
# Run automated analysis
cd ../monitoring
python3 auto_economic_analysis.py \
  --network-config ../../test-networks/SCENARIO_NAME/ \
  --live-query

# Save results
python3 auto_economic_analysis.py \
  --network-config ../../test-networks/SCENARIO_NAME/ \
  --live-query > ../phase1_tests/results/SCENARIO_results.txt
```

#### 5. Data Collection

Capture:
- **Chain state**: Heights, tips, node distribution
- **Economic metrics**: Custody %, volume %, consensus weights
- **Risk assessment**: Score, level, consensus chain
- **Timestamps**: Fork creation, resolution, duration

#### 6. Cleanup
```bash
# Stop mining
pkill -f miner_std.py

# Tear down network
warnet down

# Save logs
kubectl logs -n warnet --all-containers --prefix > logs/SCENARIO_logs.txt
```

---

## Automated Test Scripts

Individual test scripts created for each scenario:
- `test_critical_50_50_split.sh`
- `test_custody_volume_conflict.sh`
- `test_single_major_exchange_fork.sh`
- `test_dual_metric_baseline.sh`

Run all tests:
```bash
./run_all_phase1_tests.sh
```

---

## Results Documentation

### Results Directory Structure
```
phase1_tests/results/
├── test_1_critical_50_50_split/
│   ├── deployment_status.log
│   ├── initial_chain_state.log
│   ├── fork_creation.log
│   ├── economic_analysis.json
│   ├── kubectl_logs.txt
│   └── FINDINGS.md
├── test_2_custody_volume_conflict/
├── test_3_single_major_exchange_fork/
└── test_4_dual_metric_baseline/
```

### Results Template

For each test, document:

**1. Deployment Verification**
- Timestamp
- All pods Running? (Y/N)
- Initial block height
- Node connectivity

**2. Fork Creation**
- Method used (artificial/natural)
- Timestamp
- Nodes per chain
- Initial chain heights

**3. Economic Analysis**
- Chain A: custody %, volume %, weight
- Chain B: custody %, volume %, weight
- Risk score
- Consensus chain
- Match expected outcome? (Y/N)

**4. Observations**
- Any unexpected behaviors
- Performance notes
- Timing observations

**5. Validation**
- ✅ Fork detected correctly
- ✅ Economic analysis accurate
- ✅ Risk score in expected range
- ✅ Consensus chain matches prediction

---

## Success Criteria

### Test 1: critical-50-50-split
- ✅ Fork detected between v26 and v27 nodes
- ✅ Chain B wins (volume dominance)
- ✅ Risk score 25-35/100 (LOW)
- ✅ Weight split: ~20 vs ~26

### Test 2: custody-volume-conflict
- ✅ Fork detected between custody and volume nodes
- ✅ Chain B wins (volume beats custody)
- ✅ Weight demonstrates 70/30 formula correctly
- ✅ Validates operational chokepoint concept

### Test 3: single-major-exchange-fork
- ✅ Fork detected between Coinbase and network majority
- ✅ Chain B wins (network effect)
- ✅ Coinbase isolated despite significant custody
- ✅ Binance alone > Coinbase

### Test 4: dual-metric-test
- ✅ Natural forks detected during continuous mining
- ✅ All forks resolve to consensus eventually
- ✅ Economic analysis consistent across fork events
- ✅ No sustained splits (baseline stable)

---

## Troubleshooting

### Common Issues

**1. Pods Not Starting**
- Check: `kubectl describe pod -n warnet POD_NAME`
- Fix: Verify node-defaults.yaml has valid rpcuser/rpcpassword

**2. No Fork Detected**
- Check: Nodes may have auto-synced before detection
- Fix: Mine more blocks on isolated nodes, or increase mining speed

**3. Economic Analysis Returns "No Data"**
- Check: Network config has economic metadata
- Fix: Verify custody_btc, daily_volume_btc in network.yaml

**4. RPC Connection Fails**
- Check: `warnet status` shows network running
- Fix: Port-forward: `kubectl port-forward -n warnet POD 18443:18443`

---

## Phase 1 Deliverables

### Week 6 Final Deliverables

1. **Test Results Package**
   - 4 complete test result directories
   - Economic analysis outputs
   - All logs and chain state captures

2. **Findings Report**
   - Comparison of expected vs actual outcomes
   - Model validation summary
   - Any discovered anomalies

3. **Updated Documentation**
   - Refined test procedures
   - Lessons learned
   - Best practices for Warnet economic testing

4. **Phase 2 Recommendations**
   - Scenarios that need refinement
   - New test cases discovered
   - Model improvements if needed

---

## Timeline Summary

| Week | Test | Duration | Status |
|------|------|----------|--------|
| 2 | critical-50-50-split | 2 days | 🟡 Pending |
| 3 | custody-volume-conflict | 2 days | 🟡 Pending |
| 4 | single-major-exchange-fork | 2 days | 🟡 Pending |
| 5 | dual-metric-test | 2 days | 🟡 Pending |
| 6 | Analysis & Documentation | 5 days | 🟡 Pending |

**Total**: 5 weeks (Weeks 2-6)

---

## Next Steps

To begin Phase 1:

```bash
# 1. Review this master plan
cat PHASE1_MASTER_PLAN.md

# 2. Start with Test 1
cd phase1_tests
./test_critical_50_50_split.sh

# 3. Document results
vi results/test_1_critical_50_50_split/FINDINGS.md

# 4. Proceed to next test
./test_custody_volume_conflict.sh
```

---

**Phase 1 Status**: 🟢 READY TO EXECUTE
**Estimated Completion**: Week 6
**Owner**: User
**Support**: All tools operational, scripts ready
