# Complete Fork Testing Workflow

**Date**: 2026-01-25
**Status**: ✅ Fully Functional
**Purpose**: Step-by-step guide to run complete fork tests with all metrics

---

## Overview

This workflow allows you to:
1. Generate partition networks with paired pool nodes
2. Deploy to warnet
3. Run mining scenarios with dynamic pool decisions
4. Measure all fork metrics: **hashrate**, custody, volume, nodes

---

## Prerequisites

```bash
# Ensure you're in the warnet environment
cd /home/pfoytik/bitcoinTools/warnet

# Activate virtual environment if needed
source warnet/.venv/bin/activate

# Verify warnet is available
warnet status
```

---

## Complete Test Procedure

### STEP 1: Generate Test Network

**Location**: `warnetScenarioDiscovery/networkGen/`

**Command**:
```bash
cd warnetScenarioDiscovery/networkGen

python3 partition_network_generator.py \
    --test-id YOUR-TEST-NAME \
    --v27-economic 70 \
    --v27-hashrate 30
```

**Parameters**:
- `--test-id`: Unique identifier for this test (e.g., "economic-70-hash-30")
- `--v27-economic`: Economic weight on v27 partition (0-100)
- `--v27-hashrate`: Initial hashrate distribution to v27 (0-100)

**Example**:
```bash
python3 partition_network_generator.py \
    --test-id fork-test-001 \
    --v27-economic 70 \
    --v27-hashrate 30
```

**Output**:
```
✓ Saved to: ../../test-networks/test-fork-test-001-economic-70-hashrate-30/network.yaml
```

**What You Get**:
- 10 mining pools with paired nodes (20 pool nodes total)
- Each pool has one v27 node and one v26 node
- Same `entity_id` for paired nodes (e.g., `pool-foundryusa`)
- Economic metadata: custody, volume, consensus weight
- User nodes with small economic values

---

### STEP 2: Deploy Network to Warnet

**Command**:
```bash
cd /home/pfoytik/bitcoinTools/warnet

warnet deploy test-networks/test-fork-test-001-economic-70-hashrate-30/
```

**Expected Output**:
```
Deploying network...
✓ Network deployed successfully
```

**Verify Deployment**:
```bash
warnet status
```

**Wait for Nodes to Sync**:
```bash
# Wait 60-90 seconds for nodes to initialize and sync
sleep 90
```

---

### STEP 3: Run Mining Scenario

**Location**: `warnet/resources/scenarios/research/`

**Command**:
```bash
cd warnet/resources/scenarios/research

warnet run partition_miner_with_pools.py \
    --network-yaml /home/pfoytik/bitcoinTools/warnet/test-networks/test-fork-test-001-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 3600 \
    --hashrate-update-interval 600 \
    --price-update-interval 60
```

**Parameters**:
- `--network-yaml`: Absolute path to network.yaml (required for pool mapping)
- `--pool-scenario`: Pool behavior scenario from mining_pools_config.yaml
  - `realistic_current` - Current pool distribution with mild ideology
  - `ideological_fork_war` - Strong ideological preferences
  - `pure_profit` - Pools only follow profitability
- `--v27-economic`: Economic weight on v27 (should match network generation)
- `--duration`: Test duration in seconds (3600 = 1 hour)
- `--hashrate-update-interval`: Pool decision frequency (600 = 10 minutes)
- `--price-update-interval`: Price update frequency (60 = 1 minute)

**Shorter Test (30 minutes)**:
```bash
warnet run partition_miner_with_pools.py \
    --network-yaml /home/pfoytik/bitcoinTools/warnet/test-networks/test-fork-test-001-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 1800
```

**Expected Output**:
```
======================================================================
Partition Mining with Dynamic Pool Strategy
======================================================================
Economic weights: v27=70.0%, v26=30.0%
Duration: 3600s (60 minutes)
Pool scenario: realistic_current
======================================================================

✓ Price oracle initialized
✓ Fee oracle initialized
✓ Pool strategy initialized (10 pools)
✓ Loaded metadata for 24 nodes

v27 partition pool distribution:
  foundryusa     : 1 nodes
  antpool        : 1 nodes
  viabtc         : 1 nodes
  ...

v26 partition pool distribution:
  foundryusa     : 1 nodes
  antpool        : 1 nodes
  viabtc         : 1 nodes
  ...

======================================================================
Starting partition mining...
======================================================================

[  10s] v27 block (foundryusa) | Heights: v27=102 v26=101 | Hash: 46.0%/54.0%
[  20s] v26 block (viabtc)     | Heights: v27=102 v26=102 | Hash: 46.0%/54.0%
...

⚡ HASHRATE REALLOCATION at 600s:
   v27: 46.0% → 67.0%
   v26: 54.0% → 33.0%

   💰 viabtc: mining v26 despite $50,000 loss (ideology: 0.50)

[610s] v27 block (foundryusa)  | Heights: v27=112 v26=108 | ...
```

**Outputs Created**:
- `/tmp/partition_pools.json` - Pool decisions and allocations
- `/tmp/partition_prices.json` - Price history
- `/tmp/partition_fees.json` - Fee history

**Monitor in Real-Time** (in another terminal):
```bash
# Watch pool decisions
tail -f /tmp/partition_pools.json

# Watch price evolution
tail -f /tmp/partition_prices.json
```

---

### STEP 4: Analyze Fork with All Metrics

**Location**: `warnetScenarioDiscovery/monitoring/`

**While Scenario is Running** (or after it completes):

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring

python3 enhanced_fork_analysis.py \
    --network-config ../../test-networks/test-fork-test-001-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query \
    --fork-depth-threshold 6
```

**Parameters**:
- `--network-config`: Path to network directory
- `--pool-decisions`: Path to pool decisions JSON (from Step 3)
- `--live-query`: Query live warnet deployment
- `--fork-depth-threshold`: Minimum fork depth to analyze (default: 6 blocks)

**Expected Output**:
```
Loading network configuration...
✓ Loaded 24 nodes from network config

Loading pool decisions...
✓ Loaded pool decisions for 10 pools

Querying warnet deployment...
✓ Queried 24 nodes

⚠️  Fork detected: 2 chains

Fork depth: 8 blocks
  Chain 1 height: 119 (+ 4 blocks)
  Chain 2 height: 115 (+ 4 blocks)
  Common ancestor: 111

======================================================================
ENHANCED FORK ANALYSIS (Depth: 8 blocks)
======================================================================

FORK_0:
----------------------------------------------------------------------
  Nodes: 12
  Custody: 1,350,685 BTC (70.0%)
  Volume: 28,779 BTC/day (68.5%)
  Consensus Weight: 947.3 (70.1%)

  Hashrate: 67.3% ← Shows actual pool allocation!
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

  Hashrate: 32.7%
  Mining Pools (4):
    - viabtc         :  11.4%
    - luxor          :   3.9%
    - ocean          :   1.4%
    - braiinspool    :   1.4%
  Method: pool_decisions

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

**What Each Metric Means**:
- **Hashrate %**: Percentage of total network hashrate mining this fork (based on pool decisions)
- **Custody %**: Percentage of total BTC held by entities on this fork
- **Volume %**: Percentage of daily transaction volume on this fork
- **Weight %**: Consensus weight (combines custody + volume)
- **Node Count**: Number of nodes on this fork

---

## Quick Reference: Complete Commands

### Full Test Sequence (Copy-Paste Ready)

```bash
# === STEP 1: Generate Network ===
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen

python3 partition_network_generator.py \
    --test-id fork-test-001 \
    --v27-economic 70 \
    --v27-hashrate 30

# === STEP 2: Deploy ===
cd /home/pfoytik/bitcoinTools/warnet

warnet deploy test-networks/test-fork-test-001-economic-70-hashrate-30/

# Wait for sync
sleep 90

# === STEP 3: Run Mining Scenario ===
cd warnet/resources/scenarios/research

warnet run partition_miner_with_pools.py \
    --network-yaml /home/pfoytik/bitcoinTools/warnet/test-networks/test-fork-test-001-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 1800

# === STEP 4: Analyze Fork (in another terminal while scenario runs) ===
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring

python3 enhanced_fork_analysis.py \
    --network-config ../../test-networks/test-fork-test-001-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query \
    --fork-depth-threshold 6
```

---

## Timeline Expectations

| Step | Duration | Notes |
|------|----------|-------|
| Network Generation | 5-10 seconds | Instant |
| Deployment | 30-60 seconds | Kubernetes pod startup |
| Node Sync | 60-90 seconds | Bitcoin nodes syncing |
| Mining Scenario | 30-60 minutes | Configurable with `--duration` |
| Fork Analysis | 5-10 seconds | Can run multiple times during scenario |

**Total Time for 30-Minute Test**: ~35 minutes

---

## Monitoring During Test

### Terminal 1: Run Scenario
```bash
cd warnet/resources/scenarios/research
warnet run partition_miner_with_pools.py ...
# Watch mining output
```

### Terminal 2: Monitor Pool Decisions
```bash
watch -n 10 'cat /tmp/partition_pools.json | jq ".pools | to_entries | .[] | {pool: .key, allocation: .value.current_allocation, hashrate: .value.profile.hashrate_pct}"'
```

### Terminal 3: Check Fork Status
```bash
# Run analysis every 60 seconds
while true; do
    cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring
    python3 enhanced_fork_analysis.py \
        --network-config ../../test-networks/test-fork-test-001-economic-70-hashrate-30/ \
        --pool-decisions /tmp/partition_pools.json \
        --live-query
    sleep 60
done
```

---

## Testing Different Scenarios

### Test 1: Economic Majority Aligns with Hashrate Majority
```bash
python3 partition_network_generator.py --test-id aligned-70-70 --v27-economic 70 --v27-hashrate 70
# Both economic weight and hashrate favor v27
```

### Test 2: Economic vs Hashrate Conflict
```bash
python3 partition_network_generator.py --test-id conflict-70-30 --v27-economic 70 --v27-hashrate 30
# Economic weight favors v27, but initial hashrate favors v26
# Pools should reallocate based on profitability
```

### Test 3: Balanced Split
```bash
python3 partition_network_generator.py --test-id balanced-50-50 --v27-economic 50 --v27-hashrate 50
# Even split - see which fork pools choose
```

### Test 4: Extreme Economic Dominance
```bash
python3 partition_network_generator.py --test-id extreme-95-10 --v27-economic 95 --v27-hashrate 10
# v27 has overwhelming economic weight but minimal hashrate
# Test if pools abandon v26 for profitability
```

---

## Pool Scenarios Explained

### `realistic_current` (Recommended)
- Reflects current mining pool behavior
- Mild ideological preferences (0.1-0.3)
- Moderate loss thresholds ($50k-$500k)
- Most pools are profit-focused

**Use when**: Testing realistic market conditions

### `ideological_fork_war`
- Strong ideological preferences (0.5-0.8)
- High loss thresholds ($500k-$2M)
- Pools willing to mine unprofitable fork

**Use when**: Testing sustained fork scenarios

### `pure_profit`
- Zero ideology (0.0)
- Low loss thresholds ($10k-$50k)
- Pools switch immediately for profit

**Use when**: Testing maximum hashrate mobility

---

## Troubleshooting

### No Fork Detected
```
✓ No fork detected - network is synchronized
```

**Causes**:
- Network hasn't forked yet (scenario just started)
- Fork depth below threshold
- Network converged to single chain

**Solutions**:
- Wait longer (forks may take 10-20 minutes)
- Lower `--fork-depth-threshold` to 3
- Check warnet status: `warnet status`

### Pool Decisions File Not Found
```
⚠️  Pool decisions file not found: /tmp/partition_pools.json
```

**Causes**:
- Mining scenario hasn't started yet
- Scenario crashed or wasn't run with `--network-yaml`

**Solutions**:
- Ensure Step 3 is running
- Check `/tmp/` directory: `ls -la /tmp/partition_*.json`
- Verify scenario is running: `warnet status`

### Hashrate Shows 0%
```
Hashrate: 0.0%
```

**Causes**:
- No pools allocated to this fork
- Pool decisions file missing or corrupted

**Solutions**:
- Run with `--pool-decisions /tmp/partition_pools.json`
- Check pool allocations: `cat /tmp/partition_pools.json | jq`

### Network Already Deployed
```
Error: Network already exists
```

**Solutions**:
```bash
# Stop existing network
warnet stop

# Or use a different test-id
```

---

## Data Export and Analysis

### Export Pool Decisions
```bash
cat /tmp/partition_pools.json | jq '.' > results/fork-test-001-pools.json
```

### Export Price History
```bash
cat /tmp/partition_prices.json | jq '.' > results/fork-test-001-prices.json
```

### Export Fork Analysis
```bash
python3 enhanced_fork_analysis.py \
    --network-config ../../test-networks/test-fork-test-001-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query > results/fork-test-001-analysis.txt
```

---

## Current Capabilities Summary

### ✅ What Works Today

1. **Network Generation**
   - Paired pool nodes (v27 + v26 per pool)
   - Economic metadata (custody, volume, weight)
   - Parameter-based variation (economic/hashrate splits)

2. **Mining Scenarios**
   - Dynamic pool decisions (profitability + ideology)
   - Pool-to-node mapping
   - Price and fee evolution tracking
   - Opportunity cost calculations

3. **Fork Analysis**
   - **Hashrate per fork** (NEW!)
   - Custody per fork
   - Volume per fork
   - Consensus weight per fork
   - Node count per fork
   - Pool attribution (which pools mine which fork)

### ⚠️ Future Enhancements

1. **Randomization**
   - True stochastic network generation
   - Varying pool counts and distributions
   - Random economic values

2. **Automated Testing**
   - Threshold assertions
   - Pass/fail criteria
   - Batch test runner

3. **Real-Time Monitoring**
   - Daemon that watches for forks
   - Automatic analysis on fork detection
   - Database logging

---

## Example Test Results

### Test: Economic 70% vs Hashrate 30%

**Setup**:
- v27: 70% economic weight, 30% initial hashrate
- v26: 30% economic weight, 70% initial hashrate
- Duration: 30 minutes
- Pool scenario: realistic_current

**Results After 30 Minutes**:
```
Fork Analysis:
  v27 Fork:
    Hashrate: 73.5% (pools reallocated to profitable fork)
    Custody: 70.0%
    Volume: 68.5%
    Winner: YES (economic + hashrate aligned)

  v26 Fork:
    Hashrate: 26.5% (only ideological pools remained)
    Custody: 30.0%
    Volume: 31.5%
    Winner: NO

Pool Reallocations: 4 pools switched from v26 to v27
Ideology Cost: ViaBTC mining v26 despite $75,000 loss
```

**Conclusion**: Economic weight influenced hashrate allocation as expected.

---

## Quick Start (5-Minute Test)

For a quick validation run:

```bash
# 1. Generate small network
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen
python3 partition_network_generator.py --test-id quick-test --v27-economic 70 --v27-hashrate 30

# 2. Deploy
cd /home/pfoytik/bitcoinTools/warnet
warnet deploy test-networks/test-quick-test-economic-70-hashrate-30/
sleep 90

# 3. Run 5-minute scenario
cd warnet/resources/scenarios/research
warnet run partition_miner_with_pools.py \
    --network-yaml /home/pfoytik/bitcoinTools/warnet/test-networks/test-quick-test-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 300

# 4. Analyze (after a few minutes)
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring
python3 enhanced_fork_analysis.py \
    --network-config ../../test-networks/test-quick-test-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query
```

---

**Document Version**: 2.0
**Last Updated**: 2026-01-25
**Status**: Complete and tested
**All Metrics**: ✅ Hashrate, Custody, Volume, Consensus Weight, Node Count
