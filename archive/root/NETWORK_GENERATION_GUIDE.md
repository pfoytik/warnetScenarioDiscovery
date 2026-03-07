# Network Generation & Fork Analysis Guide

## Overview

This guide covers:
1. **Generating networks** using `generate_warnet_network.py`
2. **Monitoring forks** with enhanced depth tracking
3. **Analyzing fork depth** manually

---

## Part 1: Generate Phase 1 Test Networks

### Quick Start

Generate all 4 Phase 1 scenario networks:

```bash
cd warnetScenarioDiscovery/networkGen

# Scenario 1: Critical 50/50 Split
python3 generate_warnet_network.py --config scenario1_critical_50_50_split.yaml

# Scenario 2: Custody vs Volume Conflict
python3 generate_warnet_network.py --config scenario2_custody_volume_conflict.yaml

# Scenario 3: Single Major Exchange Fork
python3 generate_warnet_network.py --config scenario3_single_major_exchange_fork.yaml

# Scenario 4: Dual Metric Baseline
python3 generate_warnet_network.py --config scenario4_dual_metric_baseline.yaml
```

This creates properly formatted network files in the correct directories.

### What Gets Generated

Each config creates:
- `<scenario>-network.yaml` - Complete Warnet-compatible network file
- Properly formatted node definitions
- Version distributions
- Network topology
- Bitcoin Core configurations

### Move to Test Networks Directory

```bash
# Create test-networks directory structure if needed
mkdir -p ../../test-networks/critical-50-50-split
mkdir -p ../../test-networks/custody-volume-conflict
mkdir -p ../../test-networks/single-major-exchange-fork
mkdir -p ../../test-networks/dual-metric-test

# Copy generated networks
cp critical-50-50-split-network.yaml ../../test-networks/critical-50-50-split/network.yaml
cp custody-volume-conflict-network.yaml ../../test-networks/custody-volume-conflict/network.yaml
cp single-major-exchange-fork-network.yaml ../../test-networks/single-major-exchange-fork/network.yaml
cp dual-metric-test-network.yaml ../../test-networks/dual-metric-test/network.yaml
```

### Copy node-defaults.yaml

Each network needs a `node-defaults.yaml`:

```bash
# Use the working node-defaults from dual-metric-test
cd ../../test-networks

for scenario in critical-50-50-split custody-volume-conflict single-major-exchange-fork; do
    cp dual-metric-test/node-defaults.yaml $scenario/
done
```

### Deploy and Test

```bash
cd ../..  # Back to warnet root

# Deploy a scenario
warnet deploy test-networks/critical-50-50-split/

# Check status
warnet status

# Verify all pods running
kubectl get pods -n warnet
```

---

## Part 2: Enhanced Fork Monitoring

### Enhanced Fork Monitor (Recommended)

Detects forks **instantly** AND measures **fork depth**:

```bash
cd warnetScenarioDiscovery/tools

./enhanced_fork_monitor.sh
```

**Output**:
```
[Iteration 5 - 20251128_143000] Monitoring 5 active nodes
  node-0000: height=150 tip=abc123def456... version=/Satoshi:26.0/
  node-0001: height=150 tip=abc123def456... version=/Satoshi:26.0/
  node-0002: height=151 tip=def789ghi012... version=/Satoshi:27.0/
  node-0003: height=151 tip=def789ghi012... version=/Satoshi:27.0/
  node-0004: height=151 tip=def789ghi012... version=/Satoshi:27.0/

⚠️  FORK DETECTED! 2 different chain tips

📊 Analyzing fork depth...

🔥 FORK DETECTED
============================================================

Chain A:
  Tip:    abc123def456...
  Height: 150
  Blocks since fork: 3

Chain B:
  Tip:    def789ghi012...
  Height: 151
  Blocks since fork: 5

Common Ancestor:
  Hash:   xyz999abc777...
  Height: 147

Fork Depth Analysis:
  Chain A: 3 blocks
  Chain B: 5 blocks
  Total:   8 blocks

Fork depth: 8 blocks (3 + 5)
============================================================
```

**What it tracks**:
- Instant fork detection (any tip difference)
- Fork depth (how many blocks deep)
- Common ancestor location
- Blocks built on each chain
- Saved to `test_results/enhanced_monitoring/fork_depths.log`

### Original Persistent Monitor

Still works exactly as before:

```bash
./persistent_monitor.sh
```

Detects forks instantly but doesn't calculate depth.

---

## Part 3: Manual Fork Depth Analysis

### Analyze Fork Between Two Nodes

```bash
cd warnetScenarioDiscovery/tools

# Compare two nodes
python3 analyze_fork_depth.py --node1 node-0000 --node2 node-0002
```

### Analyze Fork Using Specific Tips

```bash
# If you know the tip hashes
python3 analyze_fork_depth.py \
    --tip1 abc123def456... \
    --tip2 def789ghi012... \
    --node1 node-0000
```

### JSON Output

```bash
python3 analyze_fork_depth.py --node1 node-0000 --node2 node-0002 --json
```

**Output**:
```json
{
  "fork": true,
  "tip1": {
    "hash": "abc123def456...",
    "height": 150,
    "blocks_since_fork": 3
  },
  "tip2": {
    "hash": "def789ghi012...",
    "height": 151,
    "blocks_since_fork": 5
  },
  "common_ancestor": {
    "hash": "xyz999abc777...",
    "height": 147
  },
  "fork_depth": {
    "chain1_blocks": 3,
    "chain2_blocks": 5,
    "total_blocks": 8
  },
  "message": "Fork depth: 8 blocks (3 + 5)"
}
```

---

## Part 4: Integration with Phase 1 Tests

### Update Test Scripts to Use Enhanced Monitoring

The Phase 1 test scripts can use the enhanced monitor:

```bash
# In test script (example)

# Start enhanced monitoring in background
cd ../tools
./enhanced_fork_monitor.sh > ../phase1_tests/${RESULTS_DIR}/fork_monitor.log 2>&1 &
MONITOR_PID=$!

# Run tests...

# When fork created, check depth
cd warnetScenarioDiscovery/tools
python3 analyze_fork_depth.py --node1 NODE_A --node2 NODE_B > ../phase1_tests/${RESULTS_DIR}/fork_depth.txt

# Kill monitor when done
kill $MONITOR_PID
```

---

## Part 5: Understanding Fork Metrics

### Instant Detection vs Fork Depth

**Instant Detection** (what persistent_monitor.sh does):
- Detects ANY difference in chain tips
- Includes temporary propagation delays (transient forks)
- Useful for: Catching all fork events

**Fork Depth** (what analyze_fork_depth.py adds):
- Measures how many blocks deep the fork is
- Shows which chain has more work
- Useful for: Understanding fork severity

### Example Scenarios

**Scenario 1: Transient Fork (Propagation Delay)**
```
Instant detection: Fork detected!
Fork depth: 1 block (1 + 0)
Interpretation: Node just received a new block, others haven't yet
```

**Scenario 2: Sustained Fork (Version Conflict)**
```
Instant detection: Fork detected!
Fork depth: 15 blocks (8 + 7)
Interpretation: Two competing chains, significant divergence
```

**Scenario 3: Chain Split (Critical)**
```
Instant detection: Fork detected!
Fork depth: 100 blocks (50 + 50)
Interpretation: Network partition or consensus failure
```

### Fork Depth Thresholds

Suggested interpretation:
- **1-3 blocks**: Likely propagation delay (transient)
- **4-10 blocks**: Sustained fork, investigate
- **11-50 blocks**: Serious fork, consensus issue
- **50+ blocks**: Critical chain split

---

## Part 6: Workflow for Phase 1

### Complete Workflow

```bash
# 1. Generate networks
cd warnetScenarioDiscovery/networkGen
python3 generate_warnet_network.py --config scenario1_critical_50_50_split.yaml

# 2. Deploy
cd ../..
warnet deploy test-networks/critical-50-50-split/

# 3. Start enhanced monitoring
cd warnetScenarioDiscovery/tools
./enhanced_fork_monitor.sh &

# 4. Run test (creates fork)
cd ../phase1_tests
./test_critical_50_50_split.sh

# 5. Check fork depth logs
cat ../tools/test_results/enhanced_monitoring/fork_depths.log
```

---

## Part 7: Troubleshooting

### Network Generation Issues

**Problem**: Generated network won't deploy
```bash
# Check YAML syntax
yamllint critical-50-50-split-network.yaml

# Verify node-defaults.yaml exists
ls -la ../../test-networks/critical-50-50-split/node-defaults.yaml
```

### Fork Depth Analysis Issues

**Problem**: "Could not find common ancestor"
- Nodes may not have both chain histories
- Try using a node that was running during the entire fork

**Problem**: "RPC error"
- Check node is running: `kubectl get pods -n warnet`
- Verify RPC access: `warnet bitcoin rpc NODE_NAME getblockcount`

### Monitor Not Detecting Forks

**Problem**: Forks happen but not detected
- Check monitoring interval (default: 30s)
- Fork may resolve between checks
- Use shorter interval or enhanced_fork_monitor

---

## Quick Reference

```bash
# Generate network
python3 generate_warnet_network.py --config SCENARIO.yaml

# Deploy network
warnet deploy test-networks/SCENARIO/

# Monitor with depth tracking
./enhanced_fork_monitor.sh

# Analyze specific fork
python3 analyze_fork_depth.py --node1 NODE1 --node2 NODE2

# Check fork history
cat test_results/enhanced_monitoring/fork_depths.log
```

---

## Next Steps

1. Generate all 4 Phase 1 networks
2. Test deployment of each
3. Run enhanced_fork_monitor during tests
4. Analyze fork depths in test results
5. Update FINDINGS.md with fork depth metrics
