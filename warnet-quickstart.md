# Warnet Testing Framework - Quick Start Guide

## 📋 Prerequisites

1. **Warnet installed and running** with your Bitcoin nodes
2. **Python 3.8+** installed
3. **Required Python packages**:
   ```bash
   pip install pyyaml
   ```

## 🚀 Quick Start (3 Steps)

### Step 1: Create Your Configuration File

Save the `test_config.yaml` file in your project directory. Customize it for your setup:

```yaml
network:
  nodes:
    - tank-0000
    - tank-0001
    # ... your nodes
```

### Step 2: Run the Test Suite

```bash
# Run all tests defined in config
python warnet_test_framework.py

# Or specify a different config file
python warnet_test_framework.py my_custom_config.yaml
```

### Step 3: View Results

Results are saved in the `test_reports/` directory and printed to console.

## 📊 Usage Examples

### Run All Tests from Config
```bash
python warnet_test_framework.py test_config.yaml
```

### Run a Single Test
```python
from warnet_test_framework import *

# Setup
nodes = [f"tank-{i:04d}" for i in range(8)]
config = ConfigLoader.load("test_config.yaml")
orchestrator = TestOrchestrator(nodes, config)

# Run just one test
orchestrator.run_test(
    VersionPartitionTest, 
    name="my_version_test",
    config={'duration': 300}
)

# Generate report
orchestrator.generate_report()
```

### Run Custom Test Scenario
```python
from warnet_test_framework import *

nodes = [f"tank-{i:04d}" for i in range(8)]
state = NetworkState(nodes)

# Create custom test
class MyCustomTest(TestScenario):
    def setup(self):
        # Your setup logic
        self.partition.partition_custom(
            ['tank-0000', 'tank-0001'],
            ['tank-0002', 'tank-0003']
        )
    
    def execute(self):
        # Monitor for 3 minutes
        self.monitor.monitor_session(180)
    
    def teardown(self):
        # Cleanup
        self.partition.reconnect_all()

# Run it
test = MyCustomTest(name="my_custom_test", state=state)
result = test.run()
print(f"Fork detected: {result.fork_detected}")
```

## 🎯 Common Test Scenarios

### 1. Version-Based Partition
Tests how different Bitcoin Core versions handle network splits.

**Config:**
```yaml
- name: version_test
  type: VersionPartitionTest
  enabled: true
  config:
    duration: 180
    monitor_interval: 5
```

### 2. Asymmetric Split
Tests majority vs minority scenarios.

**Config:**
```yaml
- name: asymmetric
  type: AsymmetricSplitTest
  enabled: true
  config:
    majority_size: 6
    minority_size: 2
    duration: 180
```

### 3. Flapping Connections
Simulates unstable network conditions.

**Config:**
```yaml
- name: flapping
  type: FlappingConnectionTest
  enabled: true
  config:
    iterations: 5
    disconnect_duration: 30
    connect_duration: 30
```

### 4. Rolling Isolation
Isolates each node sequentially.

**Config:**
```yaml
- name: rolling
  type: RollingIsolationTest
  enabled: true
  config:
    isolation_duration: 60
    stabilization_period: 30
```

### 5. Star Topology
Creates hub-and-spoke network.

**Config:**
```yaml
- name: star
  type: StarTopologyTest
  enabled: true
  config:
    duration: 180
    hub_node: tank-0000
```

### 6. Cascade Failure
Sequential node failures and recovery.

**Config:**
```yaml
- name: cascade
  type: CascadeFailureTest
  enabled: true
  config:
    failure_interval: 45
    recovery_interval: 45
```

## 📝 Understanding the Output

### Console Output
During test execution, you'll see:
```
2025-09-29 10:30:00 - INFO - Starting test: version_partition
2025-09-29 10:30:05 - INFO - Setting up version partition test
[0s]
  tank-0000: 150 (a1b2c3d4e5f6...)
  tank-0001: 150 (a1b2c3d4e5f6...)
  ...
```

### Test Report
After completion:
```
================================================================================
                           WARNET TEST REPORT
================================================================================

Generated: 2025-09-29 10:45:30
Total Tests: 6
Network: 8 nodes
--------------------------------------------------------------------------------

1. version_partition
   Duration: 185.3s
   Fork Detected: ✓
   Fork Point: Block 150
   Fork Duration: 180.0s
   Total Blocks Produced: 24
```

### JSON Report
Detailed results saved to `test_reports/test_report_YYYYMMDD_HHMMSS.json`:
```json
{
  "timestamp": "2025-09-29T10:45:30",
  "network": {
    "nodes": ["tank-0000", "tank-0001", ...],
    "node_info": {...}
  },
  "tests": [
    {
      "name": "version_partition",
      "fork_detected": true,
      "metrics": {...}
    }
  ]
}
```

## 🔧 Customization

### Modify Test Duration
```yaml
config:
  duration: 300  # 5 minutes instead of 3
```

### Change Monitoring Intervals
```yaml
monitoring:
  height_monitor_interval: 10  # Check every 10s
  mempool_monitor_interval: 60  # Check every 60s
```

### Select Specific Tests
```yaml
test_suite:
  - name: quick_version_test
    enabled: true
    type: VersionPartitionTest
    config:
      duration: 60  # Quick 1-minute test
  
  - name: long_running_test
    enabled: false  # Skip this one
    type: AsymmetricSplitTest
```

## 🐛 Troubleshooting

### "Node not responding"
- Check that Warnet is running: `warnet status`
- Verify node names match your setup
- Ensure nodes are accessible: `warnet bitcoin rpc tank-0000 getblockcount`

### "Config file not found"
- Make sure `test_config.yaml` is in the same directory
- Or specify full path: `python warnet_test_framework.py /path/to/config.yaml`

### Tests taking too long
- Reduce `duration` in test configs
- Reduce number of iterations in flapping/rolling tests
- Disable slow tests by setting `enabled: false`

### No forks detected
- Ensure mining scenario is running: `warnet scenario status`
- Increase test duration to allow more blocks to be mined
- Check that partitions are actually isolating nodes (look at peer counts)

## 📚 Advanced Usage

### Monitor in Real-Time
```python
from warnet_test_framework import *

nodes = [f"tank-{i:04d}" for i in range(8)]
state = NetworkState(nodes)
monitor = Monitor(state)

# Monitor heights for 5 minutes
monitor.monitor_session(duration=300, height_interval=5)
```

### Analyze Existing Results
```python
import json

# Load previous test results
with open('test_reports/test_report_20250929_103000.json', 'r') as f:
    report = json.load(f)

# Analyze
for test in report['tests']:
    print(f"{test['name']}: Fork={test['fork_detected']}")
    if test['fork_detected']:
        print(f"  Fork point: {test['metrics']['fork_point']}")
```

### Create Network Snapshot Manually
```python
from warnet_test_framework import *

nodes = [f"tank-{i:04d}" for i in range(8)]
state = NetworkState(nodes)

# Take snapshot
snapshot = state.snapshot()
print(f"Fork detected: {snapshot.fork_detected}")
print(f"Unique chain tips: {snapshot.unique_tips}")

for node, data in snapshot.nodes.items():
    print(f"{node}: height={data['height']}, peers={data['peer_count']}")
```

## 🎓 Next Steps

1. **Run the default test suite** to familiarize yourself with the framework
2. **Customize the config** for your specific testing needs
3. **Create custom test scenarios** for edge cases you want to explore
4. **Analyze the results** to understand Bitcoin's fork behavior
5. **Integrate with CI/CD** for automated regression testing

## 📖 Further Reading

- See `test_config.yaml` for all configuration options
- Check the test scenario classes in the framework for implementation details
- Review logs in `warnet_tests.log` for debugging

Happy testing! 🚀