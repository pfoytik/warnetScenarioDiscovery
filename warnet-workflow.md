# Complete Warnet Testing Workflow

This guide walks you through a complete testing workflow from setup to analysis.

## 📁 Project Structure

```
your_project/
├── warnet_test_framework.py    # Main testing framework
├── warnet_utils.py              # Utility commands
├── warnet_visualizer.py         # Results visualization
├── test_config.yaml             # Test configuration
├── test_reports/                # Generated reports
│   ├── test_report_*.json
│   └── test_report_*.txt
└── warnet_tests.log            # Execution logs
```

## 🔄 Complete Workflow

### Phase 1: Setup & Verification (5 minutes)

**Step 1: Verify Your Warnet Setup**
```bash
# Check your Warnet is running
warnet status

# Verify nodes are accessible
warnet bitcoin rpc tank-0000 getblockcount
warnet bitcoin rpc tank-0001 getblockcount
```

**Step 2: Check Current Network State**
```bash
# Use utilities to inspect your network
python warnet_utils.py list
python warnet_utils.py health
python warnet_utils.py mempool
```

Expected output:
```
================================================================================
WARNET NETWORK STATUS
================================================================================

Total Nodes: 8
--------------------------------------------------------------------------------
Node            IP Address           Version              Height     Peers     
--------------------------------------------------------------------------------
tank-0000       10.244.0.129         /Satoshi:29.0.0/     150        7         
tank-0001       10.244.0.127         /Satoshi:29.0.0/     150        7         
...
```

**Step 3: Customize Configuration**
Edit `test_config.yaml` to match your setup:
```yaml
network:
  nodes:
    - tank-0000  # Update these to match your nodes
    - tank-0001
    # ...
```

### Phase 2: Running Tests (30-60 minutes)

**Option A: Run Complete Test Suite**
```bash
# Run all configured tests
python warnet_test_framework.py test_config.yaml

# This will:
# 1. Discover all nodes
# 2. Run each enabled test sequentially
# 3. Generate comprehensive reports
# 4. Save results to test_reports/
```

**Option B: Run Individual Tests**
```python
# Create a custom test script: run_single_test.py
from warnet_test_framework import *

# Setup
nodes = [f"tank-{i:04d}" for i in range(8)]
config = ConfigLoader.load("test_config.yaml")
orchestrator = TestOrchestrator(nodes, config)

# Run just one test
result = orchestrator.run_test(
    VersionPartitionTest,
    name="quick_version_test",
    config={'duration': 120, 'monitor_interval': 5}
)

# Check results
print(f"Fork detected: {result.fork_detected}")
if result.fork_detected:
    print(f"Fork point: {result.metrics.get('fork_point')}")

# Generate report
orchestrator.generate_report()
```

```bash
python run_single_test.py
```

**Option C: Interactive Testing**
```python
# Interactive session: interactive_test.py
from warnet_test_framework import *
import time

nodes = [f"tank-{i:04d}" for i in range(8)]
state = NetworkState(nodes)
partition = NetworkPartition(state)
monitor = Monitor(state)

# Take initial snapshot
print("Initial state:")
snapshot = state.snapshot()
print(f"Fork detected: {snapshot.fork_detected}")

# Create a partition
print("\nPartitioning by version...")
partition.partition_by_version("29.0", "28.1")

# Monitor for a while
print("\nMonitoring for 3 minutes...")
monitor.monitor_session(180, height_interval=5)

# Reconnect
print("\nReconnecting network...")
partition.reconnect_all()
time.sleep(30)

# Final state
print("\nFinal state:")
snapshot = state.snapshot()
print(f"Fork detected: {snapshot.fork_detected}")

# Get summary
stats = monitor.collector.get_summary_stats()
print(f"\nBlocks produced:")
for node, data in stats.get('height_progression', {}).items():
    print(f"  {node}: {data['blocks_produced']} blocks")
```

```bash
python interactive_test.py
```

### Phase 3: Real-Time Monitoring (During Tests)

**Terminal 1: Run Tests**
```bash
python warnet_test_framework.py test_config.yaml
```

**Terminal 2: Monitor Live**
```bash
# Watch network health in real-time
watch -n 5 'python warnet_utils.py health'

# Or monitor continuously
python warnet_utils.py monitor 300
```

**Terminal 3: Watch Logs**
```bash
# Watch test framework logs
tail -f warnet_tests.log

# Watch specific node logs
warnet logs tank-0000 --follow
```

**Terminal 4: Quick Checks**
```bash
# Quick mempool check
python warnet_utils.py mempool

# Compare versions
python warnet_utils.py compare '29.0' '28.1'
```

### Phase 4: Analysis & Visualization (10-15 minutes)

**Step 1: View Summary Report**
```bash
# Find your latest report
ls -lt test_reports/

# View text summary
python warnet_visualizer.py test_reports/test_report_20250929_103000.json
```

**Step 2: Generate Detailed Reports**
```bash
# Save detailed text report
python warnet_visualizer.py test_reports/test_report_20250929_103000.json save analysis.txt

# View specific test charts
python warnet_visualizer.py test_reports/test_report_20250929_103000.json heights version_partition

# Compare all tests
python warnet_visualizer.py test_reports/test_report_20250929_103000.json compare
```

**Step 3: Analyze JSON Data**
```python
# Custom analysis script: analyze_results.py
import json

# Load results
with open('test_reports/test_report_20250929_103000.json', 'r') as f:
    data = json.load(f)

# Find tests with forks
forked_tests = [t for t in data['tests'] if t['fork_detected']]
print(f"Tests with forks: {len(forked_tests)}")

for test in forked_tests:
    print(f"\n{test['name']}:")
    print(f"  Duration: {test['duration']:.1f}s")
    print(f"  Fork point: {test['metrics'].get('fork_point')}")
    
    # Analyze which nodes had different tips
    post_snap = test['post_snapshot']
    tips = {}
    for node, data in post_snap['nodes'].items():
        hash = data['best_hash']
        if hash not in tips:
            tips[hash] = []
        tips[hash].append(node)
    
    print(f"  Chain splits:")
    for hash, nodes in tips.items():
        print(f"    {hash[:12]}... : {nodes}")
```

```bash
python analyze_results.py
```

### Phase 5: Iteration & Refinement

**Based on results, adjust your tests:**

**If forks aren't occurring:**
```yaml
# Increase test duration
config:
  duration: 300  # 5 minutes instead of 3

# Try more aggressive partitions
- name: complete_isolation
  type: AsymmetricSplitTest
  config:
    majority_size: 7
    minority_size: 1
```

**If tests are too slow:**
```yaml
# Reduce monitoring frequency
monitoring:
  height_monitor_interval: 10  # Check less often
  
# Disable slow tests
- name: cascade_failure
  enabled: false  # Skip this one
```

**If you want more granular data:**
```yaml
monitoring:
  snapshot_interval: 10  # More frequent snapshots
  enable_detailed_logging: true
```

## 🎯 Common Testing Scenarios

### Scenario 1: Quick Health Check

**Goal:** Verify network is working correctly before tests

```bash
# 30 second workflow
python warnet_utils.py list
python warnet_utils.py health
# If healthy, proceed with tests
```

### Scenario 2: Version Comparison Study

**Goal:** Compare how v29.0 vs v28.1 handle same conditions

```bash
# Run version-specific tests
python warnet_test_framework.py test_config.yaml

# Analyze version differences
python warnet_utils.py compare '29.0' '28.1'

# Review detailed results
python warnet_visualizer.py test_reports/test_report_*.json
```

### Scenario 3: Stress Testing

**Goal:** Find breaking points of the network

```bash
# 1. Start with tx flood
warnet scenario run tx_flood.py

# 2. Create partition while flooding
python warnet_utils.py partition '0,1,2,3' '4,5,6,7'

# 3. Monitor live
python warnet_utils.py monitor 600

# 4. Analyze mempools during stress
python warnet_utils.py mempool

# 5. Reconnect and observe reorg
python warnet_utils.py reconnect
```

### Scenario 4: Reproducibility Testing

**Goal:** Verify specific scenario consistently produces forks

```bash
# Run same test 5 times
for i in {1..5}; do
    echo "Run $i"
    python -c "
from warnet_test_framework import *
nodes = [f'tank-{i:04d}' for i in range(8)]
orchestrator = TestOrchestrator(nodes, {})
orchestrator.run_test(VersionPartitionTest, 'run_$i', {'duration': 120})
    "
    sleep 120  # Stabilization between runs
done

# Compare results across runs
ls test_reports/*.json
```

### Scenario 5: Manual Fork Creation & Study

**Goal:** Manually create and study a specific fork scenario

```python
# manual_fork_study.py
from warnet_test_framework import *
import time

nodes = [f"tank-{i:04d}" for i in range(8)]
state = NetworkState(nodes)
partition = NetworkPartition(state)
monitor = Monitor(state)

print("Step 1: Take baseline snapshot")
baseline = state.snapshot()
print(f"Heights: {[(n, d['height']) for n, d in baseline.nodes.items()]}")

print("\nStep 2: Create partition")
group_a = nodes[:4]  # tank-0000 to tank-0003
group_b = nodes[4:]  # tank-0004 to tank-0007
partition.partition_custom(group_a, group_b)

print("\nStep 3: Wait for divergence (2 minutes)")
for i in range(24):  # 2 minutes in 5-second intervals
    time.sleep(5)
    monitor.collector.collect_heights()
    if state.detect_fork():
        print(f"  Fork detected at {i*5}s!")
        break

print("\nStep 4: Analyze fork")
fork_point = state.find_fork_point()
print(f"Fork point: Block {fork_point}")

tips = state.get_chain_tips()
print("\nCurrent tips:")
for node, (height, hash) in tips.items():
    group = "A" if node in group_a else "B"
    print(f"  [{group}] {node}: {height} ({hash[:12]}...)")

print("\nStep 5: Reconnect and observe reorg")
partition.reconnect_all()

print("Waiting for reorg (1 minute)...")
time.sleep(60)

final = state.snapshot()
print("\nFinal state:")
print(f"Fork resolved: {not final.fork_detected}")
print(f"Winning tip: {list(final.nodes.values())[0]['best_hash'][:12]}...")

# Calculate reorg depths
from warnet_test_framework import Analyzer
reorg_analysis = Analyzer.calculate_reorg_depth(baseline, final)
print("\nReorg analysis:")
for node, data in reorg_analysis.items():
    if data.get('occurred'):
        print(f"  {node}: reorged {data['height_change']} blocks")
```

```bash
python manual_fork_study.py
```

## 🔍 Debugging Tips

### Test fails with "Node not responding"
```bash
# Check Warnet status
warnet status

# Test individual node
warnet bitcoin rpc tank-0000 getblockcount

# Check logs
warnet logs tank-0000 --tail 50
```

### Fork not detected when expected
```bash
# Verify partition was created
python warnet_utils.py health

# Check peer counts (should be lower after partition)
python -c "
from warnet_test_framework import *
nodes = [f'tank-{i:04d}' for i in range(8)]
state = NetworkState(nodes)
for node in nodes:
    peers = len(WarnetRPC.get_peer_info(node))
    print(f'{node