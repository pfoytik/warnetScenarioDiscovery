# Warnet Economic Fork Testing - Usage Guide

**Quick reference for running economic fork analysis with Warnet**

---

## Quick Start

### 1. Deploy a Test Network

```bash
# Deploy one of the test networks
cd /path/to/warnet
warnet deploy test-networks/dual-metric-test/

# Check deployment status
warnet status

# Wait for all pods to be running
kubectl get pods -n warnet
```

### 2. Run Continuous Mining with Fork Detection

```bash
cd warnetScenarioDiscovery/tools

# Run 10-minute test with all nodes mining
./continuous_mining_test.sh --interval 5 --duration 600 --nodes allnodes
```

### 3. Check Results

```bash
# View logs
ls -la ../test_results/continuous_mining_*/

# Main log
cat ../test_results/continuous_mining_*/continuous_mining.log

# Fork events
cat ../test_results/continuous_mining_*/forks_detected.log

# Economic analysis
cat ../test_results/continuous_mining_*/economic_analysis.log
```

---

## Available Test Networks

| Network | Purpose | Risk Level | Nodes |
|---------|---------|------------|-------|
| **dual-metric-test** | Baseline test, version split | LOW (25.8) | 5 |
| **critical-50-50-split** | Near-balanced custody | LOW (30.8) | 5 |
| **custody-volume-conflict** | Volume vs custody tension | LOW (20.5) | 4 |
| **single-major-exchange-fork** | Isolated major player | LOW (20.5) | 4 |

All networks are in: `test-networks/NETWORK_NAME/`

---

## Tools

### continuous_mining_test.sh

**Purpose**: Automated fork detection and economic analysis during mining

**Options**:
- `--interval N` - Mining interval in seconds (default: 5)
- `--duration N` - Test duration in seconds (default: 3600)
- `--nodes MODE` - Mining mode: `allnodes`, `random`, or specific names
- `--network PATH` - Path to network config (auto-detected if deployed)
- `--logdir PATH` - Log directory (auto-created in test_results/)

**Examples**:
```bash
# Quick 5-minute test
./continuous_mining_test.sh --interval 5 --duration 300 --nodes random

# Long test, all nodes
./continuous_mining_test.sh --interval 10 --duration 7200 --nodes allnodes

# Specific network config
./continuous_mining_test.sh --network ../../test-networks/critical-50-50-split/
```

### auto_economic_analysis.py

**Purpose**: Standalone economic analysis of deployed network

**Options**:
- `--network-config PATH` - Path to network directory
- `--live-query` - Query live chain state from Warnet
- `--fork-file PATH` - Analyze fork from JSON file

**Examples**:
```bash
cd ../monitoring

# Analyze deployed network
python3 auto_economic_analysis.py \
    --network-config ../../test-networks/dual-metric-test/ \
    --live-query

# Analyze without deployment (offline)
python3 auto_economic_analysis.py \
    --network-config ../../test-networks/custody-volume-conflict/
```

### analyze_all_scenarios.py

**Purpose**: Batch analysis and comparison of all scenarios

**Usage**:
```bash
cd ../monitoring
python3 analyze_all_scenarios.py
```

**Output**: Comparison table ranked by risk score

---

## Manual Fork Testing

### Create Artificial Fork

```bash
# Get node list
warnet status

# Mine competing blocks on different nodes
warnet bitcoin rpc exchange-high-custody generatetoaddress 5 bcrt1qxxx...
warnet bitcoin rpc custody-provider generatetoaddress 5 bcrt1qyyy...

# Check for fork
for node in exchange-high-custody custody-provider; do
    echo "$node:"
    warnet bitcoin rpc $node getblockcount
    warnet bitcoin rpc $node getbestblockhash
done

# Run economic analysis
python3 ../monitoring/auto_economic_analysis.py \
    --network-config ../../test-networks/dual-metric-test/ \
    --live-query
```

---

## Common Workflows

### Test 1: Deploy and Validate

```bash
# 1. Deploy network
warnet deploy test-networks/dual-metric-test/

# 2. Verify all nodes running
warnet status

# 3. Quick analysis (no fork)
cd warnetScenarioDiscovery/monitoring
python3 auto_economic_analysis.py \
    --network-config ../../test-networks/dual-metric-test/

# 4. Create artificial fork
warnet bitcoin rpc exchange-high-custody generatetoaddress 3 bcrt1q...
warnet bitcoin rpc custody-provider generatetoaddress 3 bcrt1q...

# 5. Analyze fork
python3 auto_economic_analysis.py \
    --network-config ../../test-networks/dual-metric-test/ \
    --live-query
```

### Test 2: Continuous Mining

```bash
# 1. Deploy network
warnet deploy test-networks/critical-50-50-split/

# 2. Run continuous mining test
cd warnetScenarioDiscovery/tools
./continuous_mining_test.sh --interval 5 --duration 1800 --nodes allnodes

# 3. Monitor logs in real-time
tail -f ../test_results/continuous_mining_*/continuous_mining.log

# 4. When complete, review economic analysis
cat ../test_results/continuous_mining_*/economic_analysis.log
```

### Test 3: Scenario Comparison

```bash
# Analyze all scenarios offline
cd warnetScenarioDiscovery/monitoring
python3 analyze_all_scenarios.py > scenario_comparison.txt

# View results
cat scenario_comparison.txt
```

---

## Troubleshooting

### Network Won't Deploy

**Issue**: Pods stuck in `CrashLoopBackOff`

**Fix**:
```bash
# Check pod logs
kubectl logs -n warnet POD_NAME

# Common cause: Invalid rpcauth in node-defaults.yaml
# Use simple rpcuser/rpcpassword instead
```

**Valid node-defaults.yaml**:
```yaml
defaultConfig: |
  regtest=1
  server=1
  txindex=1
  rpcuser=bitcoin
  rpcpassword=bitcoin
  rpcallowip=0.0.0.0/0
  rpcbind=0.0.0.0
  rpcport=18443
```

### No Forks Detected

**Issue**: Continuous mining doesn't detect forks

**Possible causes**:
1. Mining interval too slow (increase `--interval`)
2. Network propagation too fast (blocks sync before detection)
3. Not enough nodes mining (`--nodes allnodes` instead of `random`)

**Test**:
```bash
# Force artificial fork
warnet bitcoin rpc NODE1 generatetoaddress 1 ADDR1
warnet bitcoin rpc NODE2 generatetoaddress 1 ADDR2

# Check if detected
python3 ../monitoring/auto_economic_analysis.py --live-query
```

### Economic Analysis Returns "No Data"

**Issue**: Auto-analysis can't find economic metadata

**Fix**: Ensure network.yaml has economic metadata:
```yaml
metadata:
  custody_btc: 2000000
  daily_volume_btc: 100000
  # ... other metrics
```

### RPC Connection Fails

**Issue**: `warnet bitcoin rpc` commands fail

**Fixes**:
```bash
# Check warnet is running
warnet status

# Verify node name
warnet status | grep -A 20 "Nodes:"

# Check kubectl
kubectl get pods -n warnet

# Port forward if needed
kubectl port-forward -n warnet POD_NAME 18443:18443
```

---

## Advanced Usage

### Custom Economic Metadata

Create custom scenarios by modifying `network.yaml`:

```yaml
- name: custom-exchange
  metadata:
    custody_btc: 1500000  # Custom custody
    daily_volume_btc: 80000  # Custom volume
    # Auto-calculated:
    # supply_percentage: (1.5M / 19.5M) * 100 = 7.69%
    # consensus_weight: (7.69 * 0.7) + (26.67 * 0.3) = 13.38
```

### Fork Detection Tuning

Modify `continuous_mining_test.sh`:

```bash
# Check for forks more frequently
FORK_CHECK_INTERVAL=1  # Default: 2

# Longer test duration
TEST_DURATION=7200  # 2 hours

# Aggressive mining
MINING_INTERVAL=2  # Faster than default 5
```

### Export Results

```bash
# Export economic analysis to JSON
python3 auto_economic_analysis.py --live-query --output json > fork_analysis.json

# Export comparison table to CSV
python3 analyze_all_scenarios.py --format csv > scenarios.csv
```

---

## Directory Structure

```
warnet/
├── test-networks/
│   ├── dual-metric-test/
│   │   ├── network.yaml
│   │   └── node-defaults.yaml
│   ├── critical-50-50-split/
│   ├── custody-volume-conflict/
│   └── single-major-exchange-fork/
│
└── warnetScenarioDiscovery/
    ├── tools/
    │   ├── continuous_mining_test.sh  ← Main test script
    │   └── USAGE_GUIDE.md  ← This file
    │
    ├── monitoring/
    │   ├── economic_fork_analyzer.py  ← Core analyzer
    │   ├── auto_economic_analysis.py  ← Warnet integration
    │   ├── analyze_all_scenarios.py   ← Batch comparison
    │   └── test_fork_analyzer.py      ← Test suite
    │
    └── test_results/
        └── continuous_mining_TIMESTAMP/  ← Auto-created logs
```

---

## Tips

1. **Start simple**: Use `dual-metric-test` network first
2. **Verify deployment**: Always check `warnet status` before testing
3. **Monitor logs**: Use `tail -f` to watch tests in real-time
4. **Save results**: Test results auto-saved to `test_results/` directory
5. **Compare scenarios**: Run `analyze_all_scenarios.py` to see differences

---

## Quick Reference Card

```bash
# DEPLOY
warnet deploy test-networks/NETWORK_NAME/

# TEST (automated)
cd warnetScenarioDiscovery/tools
./continuous_mining_test.sh --interval 5 --duration 600 --nodes allnodes

# ANALYZE (manual)
cd warnetScenarioDiscovery/monitoring
python3 auto_economic_analysis.py --network-config PATH --live-query

# COMPARE
python3 analyze_all_scenarios.py

# CLEANUP
warnet down
```

---

For detailed results and findings, see: `CRITICAL_SCENARIOS_SUMMARY.md`
