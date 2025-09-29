# Warnet Bitcoin Fork Testing Framework

A comprehensive Python framework for testing Bitcoin network fork scenarios using Warnet.

## 🎯 What This Framework Does

This framework allows you to:
- **Systematically induce blockchain forks** by partitioning your Warnet network
- **Monitor fork behavior in real-time** with detailed metrics
- **Analyze fork resolution** and chain reorganizations
- **Compare different Bitcoin Core versions** under identical conditions
- **Generate comprehensive reports** with visualizations
- **Automate regression testing** for Bitcoin Core development

## 📦 Components

### Core Framework (`warnet_test_framework.py`)
The main testing engine with:
- **6 built-in test scenarios** (version partition, asymmetric split, flapping connections, etc.)
- **Automatic fork detection** and analysis
- **Time-series data collection** for heights, mempools, and chain state
- **Comprehensive metrics** including reorg depth, fork duration, and block production
- **JSON report generation** for detailed analysis

### Utilities (`warnet_utils.py`)
Command-line tools for quick operations:
- `list` - Show all nodes with status
- `health` - Check network health and detect forks
- `mempool` - Display mempool status across nodes
- `reconnect` - Force reconnect partitioned network
- `partition` - Create custom network partitions
- `monitor` - Live monitoring with real-time updates
- `compare` - Compare behavior between versions

### Visualizer (`warnet_visualizer.py`)
Results analysis and visualization:
- Generate text reports from JSON results
- ASCII charts for terminal display
- Height progression tracking
- Cross-test comparisons
- Export reports to files

### Configuration (`test_config.yaml`)
YAML-based configuration for:
- Network topology definition
- Test suite specification
- Monitoring parameters
- Reporting options

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.8+
pip install pyyaml

# Warnet running with 8 nodes
warnet status
```

### Basic Usage

**1. Run complete test suite:**
```bash
python warnet_test_framework.py test_config.yaml
```

**2. Check network health:**
```bash
python warnet_utils.py health
```

**3. View results:**
```bash
python warnet_visualizer.py test_reports/test_report_*.json
```

### Example Output

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

2. asymmetric_split
   Duration: 192.1s
   Fork Detected: ✓
   Fork Point: Block 174
   Reorgs: 2 nodes
```

## 📚 Test Scenarios

### 1. Version Partition Test
Partitions network by Bitcoin Core version (e.g., v29.0 vs v28.1).

**Use case**: Compare how different versions handle identical fork scenarios.

```yaml
- name: version_test
  type: VersionPartitionTest
  config:
    duration: 180
```

### 2. Asymmetric Split Test
Creates uneven network splits (e.g., 6 nodes vs 2 nodes).

**Use case**: Study minority chain behavior and reorg dynamics.

```yaml
- name: asymmetric
  type: AsymmetricSplitTest
  config:
    majority_size: 6
    duration: 180
```

### 3. Flapping Connection Test
Simulates intermittent connectivity with repeated disconnects/reconnects.

**Use case**: Test behavior under unstable network conditions.

```yaml
- name: flapping
  type: FlappingConnectionTest
  config:
    iterations: 5
    disconnect_duration: 30
```

### 4. Rolling Isolation Test
Sequentially isolates each node one at a time.

**Use case**: Identify critical nodes and test network resilience.

```yaml
- name: rolling
  type: RollingIsolationTest
  config:
    isolation_duration: 60
```

### 5. Star Topology Test
Creates hub-and-spoke network with central node.

**Use case**: Study single point of failure scenarios.

```yaml
- name: star
  type: StarTopologyTest
  config:
    hub_node: tank-0000
```

### 6. Cascade Failure Test
Simulates sequential node failures and recovery.

**Use case**: Test network degradation and recovery patterns.

```yaml
- name: cascade
  type: CascadeFailureTest
  config:
    failure_interval: 45
```

## 🔧 Customization

### Create Your Own Test

```python
from warnet_test_framework import TestScenario

class MyCustomTest(TestScenario):
    """Test: Your custom scenario"""
    
    def setup(self):
        # Create your network conditions
        self.partition.partition_custom(
            ['tank-0000', 'tank-0001'],
            ['tank-0002', 'tank-0003']
        )
    
    def execute(self):
        # Monitor for desired duration
        self.monitor.monitor_session(180)
    
    def teardown(self):
        # Cleanup
        self.partition.reconnect_all()

# Run it
nodes = [f"tank-{i:04d}" for i in range(8)]
state = NetworkState(nodes)
test = MyCustomTest(name="my_test", state=state)
result = test.run()
```

### Modify Test Parameters

```yaml
# Edit test_config.yaml
test_suite:
  - name: quick_test
    type: VersionPartitionTest
    config:
      duration: 60  # Quick 1-minute test
      monitor_interval: 5
```

## 📊 Understanding Results

### Key Metrics

**Fork Detection**
- Whether network split into multiple chains
- Number of unique chain tips

**Fork Point**
- Last common block before divergence
- Indicates when split occurred

**Reorg Analysis**
- Which nodes reorganized
- How many blocks were abandoned
- Which chain "won"

**Block Production**
- Total blocks mined during test
- Per-node production rates
- Mining efficiency

**Mempool Behavior**
- Transaction accumulation patterns
- Divergence between partitions
- Clearing rates

### Report Files

**Console Output**: Real-time test progress
**JSON Reports**: `test_reports/test_report_*.json` - Complete data
**Text Reports**: Generated via visualizer - Human-readable summary
**Logs**: `warnet_tests.log` - Detailed execution log

## 🎓 Common Workflows

### Daily Testing
```bash
# Morning: Check network health
python warnet_utils.py health

# Run daily test suite
python warnet_test_framework.py test_config.yaml

# Review results
python warnet_visualizer.py test_reports/test_report_*.json
```

### Quick Experiment
```bash
# Create partition
python warnet_utils.py partition '0,1,2,3' '4,5,6,7'

# Monitor live
python warnet_utils.py monitor 300

# Reconnect
python warnet_utils.py reconnect
```

### Deep Analysis
```bash
# Run specific test
python run_single_test.py

# Generate detailed report
python warnet_visualizer.py report.json save analysis.txt

# Compare with previous results
python warnet_visualizer.py report.json compare
```

## 🐛 Troubleshooting

**"Node not responding"**
- Check Warnet status: `warnet status`
- Verify node access: `warnet bitcoin rpc tank-0000 getblockcount`

**Fork not detected**
- Verify mining is active: `warnet scenario status`
- Check peer counts after partition: `python warnet_utils.py health`
- Increase test duration in config

**Network stuck forked**
- Force reconnect: `python warnet_utils.py reconnect`
- If persistent: restart Warnet

**Tests too slow**
- Reduce duration in config
- Decrease monitoring frequency
- Disable heavy tests

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 3 steps
- **[WORKFLOW.md](WORKFLOW.md)** - Complete testing workflows
- **test_config.yaml** - Configuration reference
- **warnet_tests.log** - Execution logs

## 🎯 Use Cases

### Bitcoin Core Development
- Test consensus changes across versions
- Verify fork resolution behavior
- Regression testing for network code

### Research
- Study reorg dynamics
- Analyze network partition effects
- Compare protocol versions

### Education
- Demonstrate blockchain forks
- Visualize consensus mechanisms
- Explore Bitcoin network behavior

## 🤝 Contributing

Contributions welcome! To add new test scenarios:

1. Create a new `TestScenario` subclass
2. Implement `setup()`, `execute()`, `teardown()`
3. Add to `TEST_CLASSES` in `TestOrchestrator`
4. Update config schema
5. Document your test

## 📝 License

This framework is designed for testing and research purposes. Use responsibly.

## 🙏 Acknowledgments

Built for Bitcoin Core testing using [Warnet](https://github.com/bitcoin-dev-project/warnet).

---

**Ready to start testing?** Check out [QUICKSTART.md](QUICKSTART.md) for a step-by-step guide!

## 📞 Support

- Issues: Check logs in `warnet_tests.log`
- Questions: Review [WORKFLOW.md](WORKFLOW.md) for detailed examples
- Debug: Use `warnet_utils.py` for network inspection

Happy testing! 🚀