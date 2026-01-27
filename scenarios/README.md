# Fork Testing Research Scenarios

**Purpose**: Partition-based Bitcoin fork testing with economic analysis and mining pool dynamics.

**Status**: ✅ Production Ready (All core metrics implemented)

---

## Directory Structure

```
research/
├── scenarios/          # Main scenario scripts (run with `warnet run`)
├── lib/               # Supporting library modules (oracles, strategies)
├── config/            # YAML configuration files
├── tests/             # Unit and integration tests
└── docs/              # Documentation and guides
```

---

## 📁 Directory Contents

### `scenarios/` - Main Scenario Scripts

Run these with `warnet run <script>` to execute fork testing scenarios:

| File | Purpose | Key Features |
|------|---------|--------------|
| **partition_miner_with_pools.py** | Production scenario with full pool dynamics | ✅ Dynamic pool decisions<br>✅ Price/fee oracles<br>✅ Pool-to-node mapping<br>✅ Ideology + profitability |
| partition_miner_full_economics.py | Full economics integration (legacy) | Economic weight tracking |
| partition_miner_price_test.py | Price oracle testing scenario | Price evolution validation |
| partition_miner_with_price.py | Basic price integration (legacy) | Simple price tracking |

**Recommended**: Use `partition_miner_with_pools.py` for all new tests.

---

### `lib/` - Library Modules

Supporting Python modules imported by scenarios:

| File | Purpose | Used By |
|------|---------|---------|
| **price_oracle.py** | Fork price evolution modeling | All partition scenarios |
| **fee_oracle.py** | Transaction fee evolution modeling | All partition scenarios |
| **mining_pool_strategy.py** | Pool decision engine (profitability + ideology) | partition_miner_with_pools.py |

**Usage**:
```python
# In scenarios
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from price_oracle import PriceOracle
from fee_oracle import FeeOracle
from mining_pool_strategy import PoolStrategy
```

---

### `config/` - Configuration Files

YAML configuration files defining model parameters:

| File | Purpose | Configures |
|------|---------|------------|
| **mining_pools_config.yaml** | Pool profiles and scenarios | Pool hashrate, ideology, loss thresholds |
| **price_model_config.yaml** | Fork price evolution parameters | Alpha/beta values, initial prices |
| **fee_model_config.yaml** | Fee evolution parameters | Congestion, incentive alignment |

**Example Scenarios in mining_pools_config.yaml**:
- `realistic_current` - Current pool behavior (mild ideology)
- `ideological_fork_war` - Strong ideological preferences
- `pure_profit` - Zero ideology, pure profitability

---

### `tests/` - Unit and Integration Tests

Validation tests for all components:

| File | Tests | Status |
|------|-------|--------|
| test_paired_node_architecture.py | Paired pool nodes, binary allocation | ✅ Passing |
| test_pool_decisions.py | Pool strategy and decision engine | ✅ Passing |
| test_yaml_pool_mapping.py | Network YAML pool extraction | ✅ Passing |
| test_sustained_ideology.py | Ideological pool behavior | ✅ Passing |
| test_sustained_fork_detection.py | Fork depth detection | ✅ Passing |
| test_economics_simple.py | Basic economic analysis | ✅ Passing |
| test_full_economics_integration.py | Full economic integration | ✅ Passing |

**Run Tests**:
```bash
cd tests/
python3 test_paired_node_architecture.py
```

---

### `docs/` - Documentation

Comprehensive guides and implementation notes:

| File | Purpose |
|------|---------|
| **COMPLETE_TESTING_WORKFLOW.md** | ⭐ Full step-by-step testing guide |
| **QUICK_REFERENCE.md** | ⭐ One-page cheat sheet |
| **TESTING_FLOW_AND_GAPS.md** | Implementation status tracker |
| PAIRED_NODE_ARCHITECTURE.md | Paired pool node design |
| POOL_NODE_MAPPING_INTEGRATION.md | Pool-to-node mapping implementation |
| PHASE_2_COMPLETION_SUMMARY.md | Fee oracle implementation |
| PHASE_3_MINING_POOL_STRATEGY.md | Pool strategy implementation |
| SUSTAINED_FORK_DETECTION.md | Fork detection design |

**Start Here**: Read `COMPLETE_TESTING_WORKFLOW.md` for full testing procedure.

---

## 🚀 Quick Start

### Option 1: Use Helper Script (Easiest)
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
./run_fork_test.sh fork-test-001 70 30 1800
```

### Option 2: Manual Steps

### 1. Generate Network
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen
python3 partition_network_generator.py \
    --test-id fork-test-001 \
    --v27-economic 70 \
    --v27-hashrate 30
```

### 2. Deploy
```bash
warnet deploy ../test-networks/test-fork-test-001-economic-70-hashrate-30/
sleep 90
```

### 3. Run Scenario
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml ../test-networks/test-fork-test-001-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 1800
```

### 4. Analyze Fork
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring
python3 enhanced_fork_analysis.py \
    --network-config ../test-networks/test-fork-test-001-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query
```

**Full details**: See `../docs/COMPLETE_TESTING_WORKFLOW.md`

---

## 📊 What You Get

Complete fork analysis with all metrics:

```
FORK_0:
  Hashrate: 67.3%        ← Which pools mine this fork
  Custody: 70.0%         ← BTC held by entities
  Volume: 68.5%          ← Daily transaction volume
  Consensus Weight: 70.1%
  Mining Pools: foundryusa, antpool, f2pool, ...

FORK_1:
  Hashrate: 32.7%
  Custody: 30.0%
  Volume: 31.5%
  Consensus Weight: 29.9%
  Mining Pools: viabtc, luxor, ocean, ...
```

---

## 🔧 Import Path Updates

If you're updating older scripts, imports now use the lib/ directory:

**OLD** (before reorganization):
```python
from price_oracle import PriceOracle
from fee_oracle import FeeOracle
```

**NEW** (after reorganization):
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from price_oracle import PriceOracle
from fee_oracle import FeeOracle
from mining_pool_strategy import PoolStrategy
```

**Note**: `partition_miner_with_pools.py` already has correct import paths.

---

## 📈 Implementation Status

### ✅ Completed Features

1. **Network Generation** - Paired pool nodes with economic metadata
2. **Mining Scenarios** - Dynamic pool decisions with profitability + ideology
3. **Price Oracle** - Fork price evolution based on economic weight
4. **Fee Oracle** - Transaction fee evolution based on congestion
5. **Pool Strategy** - Dual-motivation model (profit + ideology)
6. **Fork Analysis** - All metrics: hashrate, custody, volume, weight, nodes
7. **Pool Attribution** - Shows which pools mine which fork
8. **Paired Nodes** - Each pool has nodes on both partitions

### ⚠️ Future Enhancements

- Random network generation (stochastic parameters)
- Automated threshold testing (pass/fail assertions)
- Real-time monitoring daemon
- Batch test runner

---

## 📚 Key Concepts

### Paired-Node Architecture

Each mining pool has **two nodes** (one per partition):
- **Same entity_id** (e.g., `pool-foundryusa`)
- **Same total hashrate** (e.g., 26.89%)
- Pool makes **binary decision**: mine v27 OR v26
- Pool's full hashrate goes to chosen fork

**Why**: Mirrors real-world forks (Bitcoin Cash, Ethereum Classic) where pools had infrastructure on both chains but chose which to mine.

### Pool Decision Model

Pools decide which fork to mine every 10 minutes based on:

1. **Profitability** (primary driver)
   - Expected revenue from mining each fork
   - Based on fork price × coinbase reward

2. **Ideology** (secondary influence)
   - Fork preference (neutral, v27, v26)
   - Ideology strength (0.0 = pure profit, 1.0 = ignore profit)

3. **Loss Thresholds**
   - Maximum acceptable loss (USD and %)
   - Forces switch when losses exceed tolerance

**Example**: ViaBTC mines v26 despite $50k loss due to ideology (strength 0.5)

---

## 🎯 Testing Scenarios

| Scenario | v27-economic | v27-hashrate | Purpose |
|----------|--------------|--------------|---------|
| Aligned | 70 | 70 | Economic & hashrate favor same fork |
| Conflict | 70 | 30 | Test pool reallocation |
| Balanced | 50 | 50 | Contested fork |
| Extreme | 95 | 10 | Overwhelming economic dominance |

---

## 🔗 Related Directories

- **Network Generation**: `/warnetScenarioDiscovery/networkGen/`
- **Fork Analysis**: `/warnetScenarioDiscovery/monitoring/`
- **Test Networks**: `/test-networks/`

---

## 📞 Help

- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Full Workflow**: `docs/COMPLETE_TESTING_WORKFLOW.md`
- **Status Tracker**: `docs/TESTING_FLOW_AND_GAPS.md`

---

**Last Updated**: 2026-01-26
**Status**: Production Ready 🚀
**All Core Metrics**: ✅ Implemented and Tested
