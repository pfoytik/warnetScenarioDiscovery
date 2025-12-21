# Phase 1: Systematic Scenario Execution - Test Scripts

**Status**: ✅ READY TO EXECUTE
**Timeline**: Weeks 2-6
**Purpose**: Validate dual-metric economic fork analyzer across 4 critical scenarios

---

## Quick Start

### Run All Tests (Automated)

```bash
cd warnetScenarioDiscovery/phase1_tests
./run_all_phase1_tests.sh
```

**Duration**: 2-3 hours
**Output**: Results in `results/` directory + `PHASE1_SUMMARY.md`

### Run Individual Tests

```bash
# Test 1: Near 50/50 custody split (Week 2)
./test_critical_50_50_split.sh

# Test 2: Custody vs volume conflict (Week 3)
./test_custody_volume_conflict.sh

# Test 3: Major exchange isolation (Week 4)
./test_single_major_exchange_fork.sh

# Test 4: Baseline validation (Week 5)
./test_dual_metric_baseline.sh
```

Each test takes ~30-45 minutes.

---

## Test Scenarios

| # | Test Script | Scenario | Key Question | Expected |
|---|-------------|----------|--------------|----------|
| 1 | `test_critical_50_50_split.sh` | Near-balanced custody split | Can volume tip the balance? | Chain B wins (volume dominance) |
| 2 | `test_custody_volume_conflict.sh` | Extreme custody vs volume | Can volume beat custody? | Chain B wins (60% volume > 10% custody) |
| 3 | `test_single_major_exchange_fork.sh` | Coinbase isolated | Can network isolate major player? | Chain B wins (network majority) |
| 4 | `test_dual_metric_baseline.sh` | Baseline validation | Does model work correctly? | Baseline established, natural forks analyzed |

---

## What Each Test Does

### Standard Test Flow

All tests follow this 8-step procedure:

1. **Deploy Network** - Start Warnet with scenario config
2. **Verify Deployment** - Wait for all pods Running
3. **Mine Initial Blocks** - 101 blocks for coinbase maturity
4. **Create Fork** - Artificial competing chains via targeted mining
5. **Economic Analysis** - Run `auto_economic_analysis.py --live-query`
6. **Collect Logs** - Save kubectl logs and chain state
7. **Validate Results** - Check risk score, consensus chain, generate FINDINGS.md
8. **Cleanup** - Tear down network (`warnet down`)

### Test-Specific Details

**Test 1: critical-50-50-split**
- Chain A (v26.0): exchange-conservative + custody-provider (15.4% supply)
- Chain B (v27.0): 3 progressive nodes (13.4% supply, 56.7% volume)
- Fork: Mine 5 blocks on A, 6 blocks on B
- Expected Risk: 30.8/100 (LOW)

**Test 2: custody-volume-conflict**
- Chain A (v26.0): custody-provider (2M BTC, 5k BTC/day)
- Chain B (v27.0): 2 payment processors (80k BTC, 180k BTC/day)
- Fork: Mine 5 blocks on A, 6 blocks on B
- Expected Risk: 20.5/100 (LOW)
- **KEY FINDING**: Volume BEATS custody (weight 18.3 vs 7.7)

**Test 3: single-major-exchange-fork**
- Chain A (v26.0): Coinbase alone (10.3% supply)
- Chain B (v27.0): Binance + Kraken + Gemini (17.4% supply)
- Fork: Mine 5 blocks on A, 6 blocks on B
- Expected Risk: 20.5/100 (LOW)

**Test 4: dual-metric-test**
- Chain A (v26.0): custody-provider (5.13% supply)
- Chain B (v27.0): 4 nodes (12.8% supply)
- Fork: Artificial (5 vs 6 blocks) + Continuous mining (15 min)
- Expected Risk: Variable
- Purpose: Establish baseline + detect natural forks

---

## Test Results Structure

After running tests, you'll have:

```
phase1_tests/
├── results/
│   ├── test_1_critical_50_50_split/
│   │   ├── FINDINGS.md               ← Key results
│   │   ├── test.log                  ← Execution log
│   │   ├── deployment_status.log     ← Kubernetes status
│   │   ├── initial_chain_state.log   ← Pre-fork chain state
│   │   ├── fork_creation.log         ← Fork creation details
│   │   ├── economic_analysis.txt     ← Analyzer output
│   │   └── kubectl_logs.txt          ← Pod logs
│   │
│   ├── test_2_custody_volume_conflict/
│   ├── test_3_single_major_exchange_fork/
│   ├── test_4_dual_metric_baseline/
│   │
│   ├── PHASE1_SUMMARY.md             ← Aggregate summary
│   └── phase1_master_execution.log   ← Complete run log
```

### Key Files to Review

**Per-test**:
- `FINDINGS.md` - Validation checklist, expected vs actual, key observations
- `economic_analysis.txt` - Raw analyzer output with risk score and consensus

**Overall**:
- `PHASE1_SUMMARY.md` - Comparison table, key findings, next steps
- `phase1_master_execution.log` - Complete execution log

---

## Prerequisites

### Required

- **Warnet deployed**: `warnet --version` works
- **Kubernetes running**: `kubectl cluster-info` works
- **Test networks exist**: `../../test-networks/{scenario}/` directories
- **Economic analyzer**: `../monitoring/auto_economic_analysis.py` executable
- **Python 3**: For analysis scripts

### Pre-Flight Check

```bash
# 1. Verify Warnet
warnet --version

# 2. Check Kubernetes
kubectl cluster-info
kubectl get nodes

# 3. Clean up previous deployments
warnet down
kubectl delete namespace warnet --ignore-not-found

# 4. Verify test scripts
ls -la *.sh

# 5. Check test networks
ls -la ../../test-networks/
```

---

## Running Tests

### Option 1: Run All Tests (Recommended)

```bash
./run_all_phase1_tests.sh
```

**What happens**:
1. Asks for confirmation
2. Runs all 4 tests sequentially
3. 30-second pause between tests
4. Generates `PHASE1_SUMMARY.md` with aggregate results
5. Creates master execution log

**When to use**: Initial validation, complete Phase 1 execution

### Option 2: Run Individual Tests

```bash
# Run just one test
./test_critical_50_50_split.sh

# Review results
cat results/test_1_critical_50_50_split/FINDINGS.md
```

**When to use**: Debugging specific scenario, iterating on test parameters

---

## Validation Criteria

Each test validates:

### ✅ Pass Criteria

1. **Fork detected**: Different chain tips after artificial mining
2. **Economic analysis runs**: `auto_economic_analysis.py` completes
3. **Risk score in range**: Within expected ±5 points
4. **Consensus chain correct**: Matches prediction (usually Chain B)
5. **All files generated**: FINDINGS.md, logs, analysis output

### ⚠️ Warning Criteria

- Risk score outside expected range (may indicate real insight)
- Unexpected consensus chain (may reveal model issue)
- No natural forks detected in Test 4 (network propagation too fast)

### ❌ Fail Criteria

- Deployment fails (pods CrashLoopBackOff)
- Economic analysis crashes
- Fork not detected (nodes auto-synced before detection)
- Missing required files

---

## Troubleshooting

### Test Fails at Deployment

**Symptom**: Pods stuck in `CrashLoopBackOff` or `Pending`

**Fix**:
```bash
# Check pod status
kubectl get pods -n warnet

# Check pod logs
kubectl logs -n warnet POD_NAME

# Common cause: RPC auth issue
# Verify node-defaults.yaml has simple rpcuser/rpcpassword
```

### Fork Not Detected

**Symptom**: Economic analysis shows "No fork detected"

**Possible causes**:
1. Nodes synced before detection (network too fast)
2. Mining didn't create different tips
3. Propagation delay too short

**Fix**:
```bash
# Manually verify fork exists
warnet bitcoin rpc NODE_A getbestblockhash
warnet bitcoin rpc NODE_B getbestblockhash

# If same, re-run fork creation step
```

### Economic Analysis Fails

**Symptom**: `auto_economic_analysis.py` crashes or returns no data

**Fix**:
```bash
# Run manually for debugging
cd ../monitoring
python3 auto_economic_analysis.py \
    --network-config ../../test-networks/SCENARIO/ \
    --live-query

# Check network config has economic metadata
cat ../../test-networks/SCENARIO/network.yaml | grep -A 5 metadata
```

### Test Timeout

**Symptom**: Test hangs waiting for pods

**Fix**:
- Increase `MAX_WAIT` in test script (default: 180s)
- Check Kubernetes resources: `kubectl top nodes`
- Verify network not conflicting with previous deployment

---

## Expected Results Summary

| Test | Risk Score | Risk Level | Consensus | Key Validation |
|------|------------|------------|-----------|----------------|
| 1 | 30.8/100 | LOW | Chain B | Volume tips near-equal custody |
| 2 | 20.5/100 | LOW | Chain B | 60% volume beats 10% custody |
| 3 | 20.5/100 | LOW | Chain B | Network majority isolates Coinbase |
| 4 | Variable | LOW | Chain B | Baseline + natural fork detection |

All scenarios should show:
- Chain B wins (v27.0 network majority)
- LOW risk (not enough custody for EXTREME risk)
- Risk correlates with supply split distance from 50/50

---

## Master Plan Reference

For detailed test procedures, see:
- `PHASE1_MASTER_PLAN.md` - Complete 5-week plan
- `../../monitoring/USAGE_GUIDE.md` - Tool usage
- `../../CRITICAL_SCENARIOS_SUMMARY.md` - Scenario analysis

---

## Timeline

| Week | Test | Duration | Action |
|------|------|----------|--------|
| 2 | Test 1 | 2 days | Run `test_critical_50_50_split.sh` |
| 3 | Test 2 | 2 days | Run `test_custody_volume_conflict.sh` |
| 4 | Test 3 | 2 days | Run `test_single_major_exchange_fork.sh` |
| 5 | Test 4 | 2 days | Run `test_dual_metric_baseline.sh` |
| 6 | Analysis | 5 days | Review results, create final report |

**Total**: 5 weeks (Weeks 2-6)

---

## Next Steps After Phase 1

### Week 6: Analysis & Documentation

1. **Review all FINDINGS.md**
   ```bash
   for f in results/test_*/FINDINGS.md; do
       echo "=== $f ==="
       cat "$f"
       echo ""
   done
   ```

2. **Compare expected vs actual**
   - Did all tests pass validation?
   - Any unexpected behaviors?
   - Risk scores match predictions?

3. **Model validation**
   - 70/30 weighting correct?
   - Volume threshold appropriate?
   - Edge cases discovered?

4. **Create final report**
   - Aggregate findings
   - Model improvements needed?
   - Phase 2 recommendations

---

## Support

### Quick Commands

```bash
# Check Warnet status
warnet status

# Check Kubernetes pods
kubectl get pods -n warnet

# View running test log
tail -f results/test_*/test.log

# Quick re-run after fixing issue
warnet down && sleep 5 && ./test_NAME.sh
```

### Common Issues

See **Troubleshooting** section above.

For tool usage, see: `../monitoring/USAGE_GUIDE.md`

---

**Phase 1 Status**: ✅ READY TO EXECUTE
**Created**: 2024-11-28
**Purpose**: Validate BCAP dual-metric economic fork analyzer
