# Integrated Workflow Guide: Using Both Systems Separately

## Overview

This guide documents the optimal workflow for using the warnet test framework and persistent monitoring system as separate, complementary tools. This approach provides maximum flexibility and visibility into what each system is doing.

---

## File Organization

Your project has two complementary systems:

```
warnet-testing/
├── warnet_test_framework.py    # Automated test scenarios
├── warnet_utils.py              # Quick utility commands
├── warnet_visualizer.py         # Framework result analysis
├── test_config.yaml             # Framework configuration
├── test_reports/                # Framework test results
│
├── tools/
│   ├── persistent_monitor.sh   # Real-time monitoring
│   ├── quick_status.sh          # Status checks
│   ├── reconnect_network.sh    # Network reconnection
│   ├── verify_sync.sh           # Sync verification
│   └── analyze_test_run.py     # Monitoring analysis
│
├── monitoring/
│   └── assess_criticality.py   # Criticality scoring
│
└── test_results/
    ├── live_monitoring/         # Real-time monitoring data
    │   ├── iter_*/              # 30-second snapshots
    │   ├── current_summary.txt  # Live status
    │   └── fork_events.log      # Fork timeline
    └── integrated_test_*/       # Combined results (manual)
```

---

## Standard Testing Workflow

### Phase 1: Setup and Baseline

**Terminal 1: Start Monitoring**
```bash
# Always start this first
./tools/persistent_monitor.sh

# You'll see:
# [Iteration 1 - 20241103_XXXXXX] Monitoring 8 active nodes...
#   tank-0000: height=123 tip=abc123...
#   ...
```

**Terminal 2: Check Initial State**
```bash
# Verify network health
python3 warnet_utils.py health

# List all nodes
python3 warnet_utils.py list

# Check mempools
python3 warnet_utils.py mempool
```

**Terminal 3: Quick Status (optional)**
```bash
# Watch live summary
watch -n 10 'cat test_results/live_monitoring/current_summary.txt'

# Or periodic checks
./tools/quick_status.sh
```

---

### Phase 2: Running Tests

#### Option A: Manual Testing (Quick Experiments)

**Terminal 2: Manual Commands**
```bash
# 1. Create partition
python3 warnet_utils.py partition '0,1,2,3' '4,5,6,7'

# 2. Monitor for fork development
python3 warnet_utils.py monitor 180

# 3. Reconnect
./tools/reconnect_network.sh

# 4. Monitor reorg
python3 warnet_utils.py monitor 120
```

**Terminal 1: Watch Monitor Output**
- Monitor will automatically detect fork: 🚨 FORK DETECTED!
- Shows chain divergence in real-time
- Alerts when network resynchronizes: ✓

#### Option B: Automated Test Suite

**Terminal 2: Run Full Test Suite**
```bash
# Run all configured test scenarios
python3 warnet_test_framework.py test_config.yaml

# Test framework will:
# - Run 6 different scenarios
# - Collect detailed metrics
# - Generate JSON reports
# - Save to test_reports/
```

**Terminal 1: Monitor Running**
- Continues collecting data every 30 seconds
- Captures all state changes
- Logs fork events independently

#### Option C: Single Test Scenario

**Terminal 2: Run Specific Test**
```bash
# Create custom test script: quick_test.py
cat > quick_test.py << 'EOF'
from warnet_test_framework import *

# Load config
config = ConfigLoader.load("test_config.yaml")
nodes = config['nodes']

# Create test
orchestrator = TestOrchestrator(nodes, config)

# Run just one scenario
print("Running version partition test...")
orchestrator.run_test(VersionPartitionTest, "quick_version_test", config)

print("\nTest complete!")
EOF

python3 quick_test.py
```

---

### Phase 3: Real-Time Observation

While tests run, you can observe both systems:

**Check Framework Progress (Terminal 2)**
```bash
# Watch framework logs
tail -f warnet_tests.log

# Shows:
# - Which test is running
# - RPC calls being made
# - Snapshot collection
# - Fork detection by framework
```

**Check Monitoring Data (Terminal 3)**
```bash
# View current state
./tools/quick_status.sh

# Check for forks
cat test_results/live_monitoring/current_summary.txt

# Verify sync status
./tools/verify_sync.sh

# Count fork events so far
wc -l test_results/live_monitoring/fork_events.log
```

**Manual Node Inspection (Terminal 4 - optional)**
```bash
# Compare heights directly
for i in {0..7}; do
    NODE="tank-$(printf '%04d' $i)"
    HEIGHT=$(warnet bitcoin rpc $NODE getblockcount)
    TIP=$(warnet bitcoin rpc $NODE getbestblockhash | cut -c1-12)
    echo "$NODE: $HEIGHT $TIP..."
done

# Check peer connections
warnet bitcoin rpc tank-0000 getpeerinfo | grep '"addr"'
```

---

### Phase 4: Analysis

After tests complete, analyze data from both systems:

#### Framework Analysis

**Terminal 2: Analyze Framework Results**
```bash
# Find latest report
ls -lt test_reports/

# View summary
python3 warnet_visualizer.py test_reports/test_report_20241103_XXXXXX.json

# Save detailed analysis
python3 warnet_visualizer.py test_reports/test_report_20241103_XXXXXX.json save framework_analysis.txt

# View specific charts
python3 warnet_visualizer.py test_reports/test_report_20241103_XXXXXX.json heights version_partition
```

**What Framework Shows:**
- Test-by-test results
- Fork detection per scenario
- Reorg depths calculated
- Block production rates
- Mempool divergence
- Peer connectivity changes

#### Monitoring Analysis

**Terminal 2: Analyze Monitoring Data**
```bash
# Generate monitoring analysis
python3 tools/analyze_test_run.py

# Shows:
# - Total iterations
# - Fork events count
# - Height progressions
# - Divergence patterns

# Run criticality assessment
python3 monitoring/assess_criticality.py

# Shows:
# - Criticality score
# - Risk classification
# - Specific issues detected

# Visualize timeline
python3 tools/visualize_test.py
```

**What Monitoring Shows:**
- Continuous 30-second snapshots
- Exact fork timing
- Real-time state changes
- Complete timeline
- Network-wide view

---

### Phase 5: Saving Results

**Organize Combined Results**
```bash
# Create timestamped directory
TEST_ID="week2_mempool_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "test_results/$TEST_ID"

# Copy framework results
cp -r test_reports/* "test_results/$TEST_ID/framework/"

# Copy monitoring data
cp -r test_results/live_monitoring/* "test_results/$TEST_ID/monitoring/"

# Create summary document
cat > "test_results/$TEST_ID/SUMMARY.md" << 'EOF'
# Test Run Summary

## Configuration
- Test ID: [fill in]
- Date: $(date)
- Duration: [fill in]
- Scenario: [fill in]

## Framework Results
[Summary from warnet_visualizer.py]

## Monitoring Results
[Summary from analyze_test_run.py]

## Key Findings
- Fork detected: [Yes/No]
- Duration of fork: [time]
- Reorg depth: [blocks]
- Critical issues: [list]

## Data Files
- Framework reports: framework/
- Monitoring snapshots: monitoring/iter_*
- Fork events: monitoring/fork_events.log
EOF

echo "✓ Results saved to: test_results/$TEST_ID"
```

---

## Typical Daily Testing Routine

### Morning: Quick Test

```bash
# Terminal 1
./tools/persistent_monitor.sh

# Terminal 2
python3 warnet_utils.py health
python3 warnet_utils.py partition '0,1,2,3' '4,5,6,7'
python3 warnet_utils.py monitor 180
./tools/reconnect_network.sh

# Quick check
./tools/quick_status.sh
```

### Afternoon: Full Test Suite

```bash
# Terminal 1
./tools/persistent_monitor.sh

# Terminal 2
python3 warnet_test_framework.py test_config.yaml

# After completion
python3 warnet_visualizer.py test_reports/test_report_*.json
python3 tools/analyze_test_run.py
```

### Evening: Analysis & Documentation

```bash
# Analyze all data
python3 monitoring/assess_criticality.py

# Save results
# [Use Phase 5 commands above]

# Clean up for tomorrow
mv test_results/live_monitoring test_results/archive_$(date +%Y%m%d)
mkdir test_results/live_monitoring
```

---

## Pro Tips for Separate Systems Workflow

### 1. Monitor Placement
Keep monitor in leftmost terminal for constant visibility

### 2. Terminal Layout
```
┌─────────────────┬─────────────────┐
│   Terminal 1    │   Terminal 2    │
│   MONITOR       │   COMMANDS      │
│   (left)        │   (right)       │
├─────────────────┼─────────────────┤
│   Terminal 3    │   Terminal 4    │
│   STATUS        │   LOGS          │
│   (bottom-left) │ (bottom-right)  │
└─────────────────┴─────────────────┘
```

### 3. Quick Reference Commands

**Start Monitor**
```bash
./tools/persistent_monitor.sh
```

**Framework Commands**
```bash
python3 warnet_utils.py health
python3 warnet_utils.py partition '0,1,2,3' '4,5,6,7'
python3 warnet_utils.py monitor 180
python3 warnet_test_framework.py test_config.yaml
```

**Reconnect**
```bash
./tools/reconnect_network.sh
```

**Status Checks**
```bash
./tools/quick_status.sh
./tools/verify_sync.sh
```

**Analysis**
```bash
python3 warnet_visualizer.py test_reports/test_report_*.json
python3 tools/analyze_test_run.py
python3 monitoring/assess_criticality.py
```

### 4. Data Preservation

```bash
# Create alias for quick archiving
alias save-test='bash -c "TEST_ID=test_$(date +%Y%m%d_%H%M%S); mkdir -p test_results/\$TEST_ID; cp -r test_reports test_results/\$TEST_ID/framework; cp -r test_results/live_monitoring test_results/\$TEST_ID/monitoring; echo Saved to test_results/\$TEST_ID"'

# Use it:
save-test
```

---

## Advantages of This Approach

✅ **Complete Visibility**: See exactly what each system is doing  
✅ **Independent Operation**: One system failure doesn't affect the other  
✅ **Flexible Control**: Run framework OR manual tests as needed  
✅ **Rich Data**: Get both high-frequency monitoring + structured test results  
✅ **Easy Debugging**: Can troubleshoot each system separately  
✅ **Scalable**: Add more monitoring windows or analysis tools easily  

---

## Moving to Week 2 Testing

Now that you have the workflow mastered, you can start systematic testing:

### Mempool Variation Tests (Week 2)

```bash
# 1. Update test_config.yaml with mempool configs
# 2. Deploy new warnet graph with variations
# 3. Start monitor
./tools/persistent_monitor.sh

# 4. Run tests
python3 warnet_test_framework.py test_config.yaml

# 5. Analyze
python3 tools/analyze_test_run.py
python3 warnet_visualizer.py test_reports/test_report_*.json

# 6. Save
save-test
```

---

## System Comparison

### Test Framework (warnet_test_framework.py)
**Purpose:** Structured, repeatable test scenarios

**Strengths:**
- Automated test execution
- Multiple predefined scenarios
- Detailed per-test metrics
- JSON output for analysis
- Easy to add new scenarios

**Best For:**
- Regression testing
- Systematic scenario testing
- Comparing multiple configurations
- Generating reports

### Persistent Monitor (persistent_monitor.sh)
**Purpose:** Continuous network observation

**Strengths:**
- Real-time fork detection
- 30-second granularity
- Always-on monitoring
- Independent of test framework
- Simple bash-based

**Best For:**
- Background monitoring
- Fork event logging
- Complete timeline capture
- Network-wide snapshots

---

## Troubleshooting

### Monitor Not Detecting Forks

**Check:**
```bash
# Verify monitor is running
ps aux | grep persistent_monitor

# Check iteration data
ls -lah test_results/live_monitoring/iter_*/

# Verify RPC access
warnet bitcoin rpc tank-0000 getblockcount
```

### Framework Tests Failing

**Check:**
```bash
# View detailed logs
tail -50 warnet_tests.log

# Test RPC connectivity
python3 warnet_utils.py health

# Verify node status
kubectl get pods
```

### Data Not Saving

**Check:**
```bash
# Verify directories exist
ls -la test_results/
ls -la test_reports/

# Check permissions
chmod -R u+w test_results/

# Verify disk space
df -h
```

---

## Best Practices

### 1. Always Start Monitor First
The monitor captures everything, so start it before running any tests.

### 2. Let Tests Complete
Don't interrupt tests mid-execution - both systems need clean completion.

### 3. Save Results Immediately
Archive important test runs right after completion.

### 4. Document Configurations
Note what network configuration was used for each test run.

### 5. Regular Cleanup
Archive old monitoring data to prevent disk space issues:
```bash
# Weekly cleanup
mv test_results/live_monitoring test_results/archive_$(date +%Y%m%d)
mkdir test_results/live_monitoring
```

### 6. Compare Both Datasets
Always analyze both framework and monitoring results for complete picture.

---

## Next Steps

### Immediate
- ✅ Practice the workflow with a simple fork test
- ✅ Verify both systems capture data correctly
- ✅ Run analysis on both datasets

### Week 2
- 📋 Configure mempool variation tests
- 📋 Run systematic single-variable tests
- 📋 Document results for each configuration

### Week 3-4
- 📋 Connection limit testing
- 📋 Fee policy variations
- 📋 Multi-variable combinations

---

## Summary

You now have:
- ✅ Two powerful complementary systems
- ✅ Clear workflow for using them together
- ✅ Complete control and visibility
- ✅ Ready for systematic testing

**Key Principle:** The test framework provides structure and automation, while the persistent monitor provides continuous visibility and comprehensive data capture. Used together but separately, they give you the best of both worlds.
