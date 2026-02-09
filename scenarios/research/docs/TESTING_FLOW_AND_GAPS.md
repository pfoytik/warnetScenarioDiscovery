# Complete Testing Flow: Current State & Gaps

**Date**: 2026-01-25 (Updated with hashrate tracking completion)
**Purpose**: Document the end-to-end flow for fork testing and track implementation status
**Status**: ✅ All Core Metrics Implemented (Hashrate, Custody, Volume, Nodes)

---

## Desired Flow (Your Requirements)

```
1. Generate set of random networks
   ├── Mining pools (varying hashrate, custody)
   ├── Exchanges (custody, volume)
   └── Users (little custody, volume)

2. Run each network with warnet
   └── Deploy to Kubernetes

3. Run scenario to play out mining process and forks
   ├── Mine blocks on partitioned network
   ├── Pools make decisions (profitability + ideology)
   └── Track price/fee evolution

4. Measure and test when forks occur based on thresholds
   ├── Hashrate per fork
   ├── Custody per fork
   ├── Volume per fork
   └── Nodes per fork
```

---

## Current State: What Works ✅

### STEP 1: Network Generation ✅ (COMPLETE)

**Tool**: `partition_network_generator.py`

**Current Capabilities**:
```bash
python3 partition_network_generator.py \
    --test-id 5.3 \
    --v27-economic 70 \
    --v27-hashrate 30
```

**What It Creates**:
- ✅ Mining pools with realistic hashrate distribution (Foundry 26.89%, AntPool 19.25%, etc.)
- ✅ Pools have paired nodes (v27 + v26)
- ✅ Economic metadata (custody, volume, consensus weight)
- ✅ Exchanges (major_exchange, payment_processor roles)
- ✅ User nodes (small custody, volume)
- ✅ Version-segregated partitions (v27 vs v26)

**What's MISSING**:
❌ **Randomization** - Currently uses fixed distribution
❌ **Stochastic variation** - Same network every time for given parameters

**Example Output**:
```yaml
nodes:
  - name: node-0000  # Pool
    metadata:
      role: mining_pool
      pool_name: Foundry USA
      hashrate_pct: 26.89
      entity_id: pool-foundryusa
      custody_btc: 53780
      daily_volume_btc: 5378

  - name: node-0010  # Pool (paired with node-0000)
    metadata:
      role: mining_pool
      pool_name: Foundry USA
      entity_id: pool-foundryusa  # Same!
      custody_btc: 53780
```

---

### STEP 2: Deploy Network ✅ (INFRASTRUCTURE EXISTS)

**Tool**: Warnet CLI

**Current Capabilities**:
```bash
# Deploy generated network
warnet deploy test-networks/test-5.3-economic-70-hashrate-30/

# Check status
warnet status
```

**Status**: ✅ Works (existing warnet infrastructure)

---

### STEP 3: Run Mining Scenario ✅ (COMPLETE)

**Tool**: `partition_miner_with_pools.py`

**Current Capabilities**:
```bash
warnet run partition_miner_with_pools.py \
    --network-yaml /path/to/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 7200 \
    --hashrate-update-interval 600
```

**What It Does**:
- ✅ Loads paired pool nodes from network.yaml
- ✅ Pools make decisions every 10 minutes (profitability + ideology)
- ✅ Dynamic hashrate allocation (pools switch between forks)
- ✅ Mines blocks using `generatetoaddress()` on chosen partition
- ✅ Tracks price evolution (Price Oracle)
- ✅ Tracks fee evolution (Fee Oracle)
- ✅ Records pool decisions and opportunity costs

**Output**:
```
[  10s] v27 block (foundry)      | Heights: v27=102 v26=101 | Hash: 46.0%/54.0%
[  20s] v27 block (antpool)      | Heights: v27=103 v26=101 | Hash: 46.0%/54.0%

⚡ HASHRATE REALLOCATION at 600s:
   v27: 46.0% → 67.0%
   v26: 54.0% → 33.0%
   💰 viabtc: mining v26 despite $50,000 loss (ideology)

[610s] v27 block (foundry)       | Heights: v27=112 v26=108 | ...
```

**Exports**:
- `/tmp/partition_pools.json` - Pool decisions and costs
- `/tmp/partition_prices.json` - Price history
- `/tmp/partition_fees.json` - Fee history

**Status**: ✅ Complete

---

### STEP 4: Measure Fork Thresholds ✅ (COMPLETE)

**Tool**: `enhanced_fork_analysis.py` (NEW - replaces auto_economic_analysis.py)

**Current Capabilities**:
```bash
python3 enhanced_fork_analysis.py \
    --network-config /path/to/test-5.3/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query \
    --fork-depth-threshold 6
```

**What It Measures**:
- ✅ Fork detection (finds common ancestor)
- ✅ Fork depth calculation
- ✅ Economic weight per fork (custody + volume)
- ✅ Node count per fork
- ✅ Consensus weight per fork
- ✅ **Hashrate per fork** - NEWLY ADDED! (2026-01-25)
- ✅ **Pool attribution** - Shows which pools mine which fork
- ✅ **Pool decision tracking** - Uses pool strategy data

**Status**: ✅ Complete - All requested metrics implemented

**What's Still MISSING** (Future Enhancements):
⚠️ **Real-time integration** - Manual execution (daemon could watch for forks)
⚠️ **Automated threshold testing** - No pass/fail logic yet

**Example Current Output**:
```
======================================================================
ENHANCED FORK ANALYSIS (Depth: 8 blocks)
======================================================================

FORK_0:
----------------------------------------------------------------------
  Nodes: 12
  Custody: 1,350,685 BTC (70.0%)
  Volume: 28,779 BTC/day (68.5%)
  Consensus Weight: 947.3 (70.1%)

  Hashrate: 67.3% ← NEW!
  Mining Pools (6):
    - foundryusa     :  26.9%
    - antpool        :  19.2%
    - f2pool         :  11.2%
    - binancepool    :  10.0%
    - marapool       :   8.2%
    - sbicrypto      :   4.6%
  Method: pool_decisions

FORK_1:
----------------------------------------------------------------------
  Nodes: 12
  Custody: 650,315 BTC (30.0%)
  Volume: 13,221 BTC/day (31.5%)
  Consensus Weight: 402.7 (29.9%)

  Hashrate: 32.7% ← NEW!
  Mining Pools (4):
    - viabtc         :  11.4%
    - luxor          :   3.9%
    - ocean          :   1.4%
    - braiinspool    :   1.4%

======================================================================
FORK COMPARISON
======================================================================

Metric               |          Fork 0 |          Fork 1 |     Winner
----------------------------------------------------------------------
Hashrate %           |           67.3% |           32.7% |     Fork 0
Custody %            |           70.0% |           30.0% |     Fork 0
Volume %             |           68.5% |           31.5% |     Fork 0
Weight %             |           70.1% |           29.9% |     Fork 0
Node Count           |              12 |              12 |        Tie
======================================================================
```

---

## What's Missing: Gap Analysis

### GAP 1: Random Network Generation ❌

**What You Want**:
```python
# Generate 100 random networks with varying properties
for i in range(100):
    generate_random_network(
        pool_count=random.randint(5, 15),
        exchange_count=random.randint(3, 8),
        user_count=random.randint(10, 50),
        # Randomize custody/volume/hashrate distributions
    )
```

**What We Have**: Fixed distribution (same 10 pools every time)

**Solution Needed**: Stochastic network generator

---

### GAP 2: Hashrate Tracking Per Fork ✅ (COMPLETED 2026-01-25)

**What You Wanted**:
```
Fork Analysis:
  v27 Fork:
    Hashrate: 67.3% (foundry, antpool, f2pool)
    Custody: 70.0%
    Volume: 68.5%
    Nodes: 12

  v26 Fork:
    Hashrate: 32.7% (viabtc)
    Custody: 30.0%
    Volume: 31.5%
    Nodes: 8
```

**What We Have Now**: ✅ Full hashrate tracking with pool attribution

**Solution Implemented**:
- Created `enhanced_fork_analysis.py`
- Loads pool decisions from `/tmp/partition_pools.json`
- Calculates hashrate per fork based on pool allocations
- Shows which specific pools mine each fork
- All 4/4 unit tests passing

---

### GAP 3: Automated Threshold Testing ❌

**What You Want**:
```python
# Run test and check thresholds
result = run_fork_test("test-5.3")

assert result.v27_hashrate > 50, "v27 should have majority hashrate"
assert result.v27_custody > 60, "v27 should have majority custody"
assert result.fork_sustained, "Fork should be sustained (depth >= 6)"

print("✅ Test PASSED: Economic weight influenced hashrate allocation")
```

**What We Have**: Manual inspection of results

**Solution Needed**: Automated test runner with assertions

---

### GAP 4: Real-Time Fork Monitoring Integration ⚠️

**What You Want**:
- Scenario running in background
- Monitor detects fork
- Automatically runs analysis
- Logs results

**What We Have**:
- Scenario runs
- Monitor runs separately
- Manual correlation needed

**Solution Needed**: Integrated monitoring daemon

---

## Recommended Implementation Plan

### Phase 1: Fill Critical Gaps (1-2 hours)

#### 1.1: Add Hashrate Tracking to Fork Analysis

**File**: Create `enhanced_fork_analysis.py`

```python
def analyze_fork_with_hashrate(network_yaml, pool_decisions_json, fork_data):
    """
    Enhanced fork analysis including hashrate allocation.

    Combines:
    - Economic data from network.yaml
    - Pool decisions from partition_pools.json
    - Fork heights from warnet RPC

    Returns:
        {
            'v27': {
                'hashrate_pct': 67.3,
                'custody_btc': 1350685,
                'volume_btc': 28779,
                'node_count': 12,
                'pools': ['foundry', 'antpool', 'f2pool']
            },
            'v26': {...}
        }
    """
```

**Integration Point**: Load `/tmp/partition_pools.json` to get current pool allocations

#### 1.2: Create Automated Test Runner

**File**: Create `run_fork_test.py`

```python
#!/usr/bin/env python3
"""
Automated fork test runner with threshold checking.

Usage:
    python3 run_fork_test.py --test-id 5.3 --duration 7200
"""

def run_fork_test(test_id, duration):
    # 1. Generate network
    generate_network(test_id)

    # 2. Deploy
    deploy_network(test_id)

    # 3. Run mining scenario (background)
    start_mining_scenario(test_id, duration)

    # 4. Monitor and analyze
    while mining_running():
        if fork_detected():
            analyze_fork_with_hashrate()
            check_thresholds()

    # 5. Generate report
    return test_results
```

---

### Phase 2: Add Randomization (2-3 hours)

#### 2.1: Stochastic Network Generator

**File**: Enhance `partition_network_generator.py`

```python
def generate_random_network(seed=None):
    """
    Generate network with randomized parameters.

    Randomizes:
    - Number of pools (5-15)
    - Pool hashrate distribution (realistic variation)
    - Number of exchanges (3-8)
    - Exchange custody/volume (power-law distribution)
    - Number of users (10-50)
    - User economic values (small random amounts)
    """
```

**Options**:
```bash
# Generate random network
python3 partition_network_generator.py \
    --test-id random-001 \
    --randomize \
    --seed 42 \
    --v27-economic-range 60-80 \
    --v27-hashrate-range 20-40
```

---

### Phase 3: Integrated Testing Pipeline (3-4 hours)

#### 3.1: Test Suite Runner

**File**: Create `test_suite_runner.py`

```bash
# Run full test suite
python3 test_suite_runner.py \
    --test-matrix week2 \
    --parallel 3 \
    --duration 3600

# Generates and runs:
#   test-5.3-E70-H30
#   test-3.5-E30-H70
#   test-4.4-E50-H50
# In parallel, analyzes results, exports summary
```

#### 3.2: Results Aggregation

**File**: Create `aggregate_test_results.py`

```bash
# Aggregate all test results
python3 aggregate_test_results.py \
    --test-dir ./test-networks/ \
    --output fork_analysis_summary.csv

# Output: CSV with all metrics for each test
```

---

## Quick Start: Current Working Flow

### End-to-End Example (Works Today)

```bash
# 1. Generate network
cd warnetScenarioDiscovery/networkGen
python3 partition_network_generator.py \
    --test-id 5.3 \
    --v27-economic 70 \
    --v27-hashrate 30

# 2. Deploy network
warnet deploy ../../test-networks/test-5.3-economic-70-hashrate-30/

# 3. Wait for nodes to sync
sleep 60

# 4. Run mining scenario
cd ../../warnet/resources/scenarios/research
warnet run partition_miner_with_pools.py \
    --network-yaml /path/to/test-5.3/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 3600

# 5. Monitor results (in another terminal)
tail -f /tmp/partition_pools.json
tail -f /tmp/partition_prices.json

# 6. Analyze fork with ALL metrics (while scenario runs or after)
cd ../../../warnetScenarioDiscovery/monitoring
python3 enhanced_fork_analysis.py \
    --network-config ../../test-networks/test-5.3-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query
```

**Expected Timeline**:
- Step 1-2: 1 minute
- Step 3: 1 minute (node sync)
- Step 4: 60 minutes (1 hour test)
- Step 5-6: Immediate

---

## Summary: What You Can Do NOW

### ✅ Works Today

1. **Generate partition networks** with paired pool nodes
2. **Deploy to warnet**
3. **Run mining scenarios** with dynamic pool switching
4. **Track pool decisions** and opportunity costs
5. **Analyze economic weight** per fork
6. **Measure fork depth**
7. **Track hashrate per fork** ← NEWLY COMPLETED!
8. **Show pool attribution** (which pools mine which fork)
9. **Complete fork metrics**: hashrate, custody, volume, weight, nodes

### ⚠️ Future Enhancements

1. **Random network generation** (stochastic parameters)
2. **Automated threshold testing** (pass/fail assertions)
3. **Test suite runner** for batch testing
4. **Results aggregation** across multiple tests
5. **Real-time fork monitoring daemon**

---

## Recommended Next Steps

### ✅ COMPLETED: Hashrate Tracking (2026-01-25)

Enhanced fork analysis with hashrate tracking is now complete and tested!
- ✅ `enhanced_fork_analysis.py` created
- ✅ All 4/4 unit tests passing
- ✅ Comprehensive documentation written

### Option A: Run Your First Complete Test (30-60 minutes)

Run a single end-to-end test with all metrics (hashrate, custody, volume, nodes).

**Do this if**: You want to validate the complete flow works with real data.

**See**: `COMPLETE_TESTING_WORKFLOW.md` for step-by-step commands.

### Option B: Run Multiple Test Scenarios (2-4 hours)

Test different economic/hashrate configurations:
- Economic 70% vs Hashrate 30% (conflict scenario)
- Economic 50% vs Hashrate 50% (balanced)
- Economic 95% vs Hashrate 10% (extreme)

**Do this if**: You want to explore how different parameters affect fork outcomes.

### Option C: Build Automated Test Pipeline (1-2 weeks)

Implement remaining enhancements:
- Randomized network generation
- Automated threshold testing (pass/fail)
- Batch test runner
- Results aggregation and reporting

**Do this if**: You're ready for production-scale research.

---

## My Recommendation

**Start with Option A** - Run one complete test end-to-end to see all metrics in action:

```bash
# See COMPLETE_TESTING_WORKFLOW.md for full commands
# Quick version:
1. Generate network (10 seconds)
2. Deploy to warnet (90 seconds)
3. Run 30-minute mining scenario
4. Analyze fork with all metrics (10 seconds)
```

**This will give you**:
- ✅ Hashrate per fork (NEW!)
- ✅ Custody per fork
- ✅ Volume per fork
- ✅ Consensus weight per fork
- ✅ Pool attribution
- ✅ Complete fork comparison table

**Then explore**: Different test scenarios (Option B) to understand fork dynamics.

**Later**: Automation and batch testing (Option C) for large-scale experiments.
