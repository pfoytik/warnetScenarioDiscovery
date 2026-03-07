# Warnet Scenario Discovery - Fork Research

**Research repository for Bitcoin fork testing with economic analysis and mining pool dynamics**

**Status**: ✅ Production Ready
**Last Updated**: 2026-01-26

---

## Overview

This repository contains a complete framework for testing Bitcoin protocol forks using Warnet, with focus on:

- **Economic weight analysis** (custody, volume, consensus weight)
- **Mining pool dynamics** (profitability + ideology-driven decisions)
- **Hashrate distribution** (which pools mine which fork)
- **Price & fee evolution** (market dynamics during forks)
- **Paired-node architecture** (realistic fork simulation)

---

## Quick Start

### Run a Complete Fork Test (4 Steps)

```bash
# One command runs everything:
./run_fork_test.sh test-001 70 30 1800

# What it does:
# 1. Generates network (70% economic on v27, 30% hashrate on v27)
# 2. Deploys to warnet
# 3. Runs 30-minute mining scenario
# 4. Analyzes fork with all metrics
```

### Or Run Steps Manually

```bash
# 1. Generate network
cd networkGen/
python3 partition_network_generator.py --test-id test-001 --v27-economic 70 --v27-hashrate 30

# 2. Deploy
warnet deploy ../test-networks/test-test-001-economic-70-hashrate-30/

# 3. Run scenario
cd ..
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml ../test-networks/test-test-001-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 1800

# 4. Analyze
cd monitoring/
python3 enhanced_fork_analysis.py \
    --network-config ../test-networks/test-test-001-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query
```

---

## Repository Structure

```
warnetScenarioDiscovery/
├── scenarios/                  # Warnet scenario scripts
│   ├── lib/                    # Supporting modules (oracles, strategies)
│   ├── config/                 # Configuration files (pools, prices, fees)
│   ├── partition_miner_with_pools.py  ⭐ Main production scenario
│   └── README.md               # Scenario documentation
│
├── networkGen/                 # Network generation tools
│   └── partition_network_generator.py  ⭐ Generate test networks
│
├── monitoring/                 # Analysis & monitoring tools
│   ├── enhanced_fork_analysis.py       ⭐ Complete fork analysis
│   └── auto_economic_analysis.py       Economic analysis only
│
├── tests/                      # Test suite
│   ├── test_paired_node_architecture.py
│   ├── test_import_paths.py
│   └── ... (6 more tests)
│
├── docs/                       # Documentation
│   ├── COMPLETE_TESTING_WORKFLOW.md   ⭐ Full guide
│   ├── QUICK_REFERENCE.md             ⭐ Cheat sheet
│   └── ... (8 more docs)
│
├── results/                    # Test results (CSV, logs)
├── tools/                      # Additional utilities
│
├── run_scenario.sh             ⭐ Helper: Run any scenario
├── run_fork_test.sh            ⭐ Helper: Run complete test
└── README_RESEARCH.md          ⭐ This file
```

---

## What You Get

### Complete Fork Analysis

```
FORK_0:
  Hashrate: 67.3%        ← Which pools mine this fork
  Custody: 70.0%         ← BTC held by entities
  Volume: 68.5%          ← Daily transaction volume
  Consensus Weight: 70.1%
  Mining Pools (6):
    - foundryusa  :  26.9%
    - antpool     :  19.2%
    - f2pool      :  11.2%
    - ...

FORK_1:
  Hashrate: 32.7%
  Custody: 30.0%
  Volume: 31.5%
  Consensus Weight: 29.9%
  Mining Pools (4):
    - viabtc      :  11.4%
    - luxor       :   3.9%
    - ...

COMPARISON TABLE:
  Shows winner for each metric side-by-side
```

### All Implemented Metrics ✅

1. ✅ Hashrate per fork (with pool attribution)
2. ✅ Custody per fork (BTC held)
3. ✅ Volume per fork (daily transactions)
4. ✅ Consensus weight (custody + volume)
5. ✅ Node count per fork
6. ✅ Pool decisions (profitability + ideology)
7. ✅ Price evolution (fork value over time)
8. ✅ Fee evolution (transaction fees)
9. ✅ Fork depth detection
10. ✅ Opportunity cost tracking

---

## Key Features

### Paired-Node Architecture

Each mining pool has **two nodes** (one per partition):
- Same `entity_id` (e.g., `pool-foundryusa`)
- Same total hashrate (e.g., 26.89%)
- Pool makes **binary decision**: mine v27 OR v26
- Pool's full hashrate goes to chosen fork

**Why**: Mirrors real-world forks (Bitcoin Cash, Ethereum Classic) where pools had infrastructure on both chains but chose which to mine.

### Dynamic Pool Decisions

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

### Testing Scenarios

| Scenario | v27-economic | v27-hashrate | Purpose |
|----------|--------------|--------------|---------|
| **Aligned** | 70 | 70 | Economic & hashrate favor same fork |
| **Conflict** | 70 | 30 | Test if pools reallocate to profitable fork |
| **Balanced** | 50 | 50 | Contested fork with no clear winner |
| **Extreme** | 95 | 10 | Overwhelming economic dominance |

---

## Documentation

### Start Here

- **docs/COMPLETE_TESTING_WORKFLOW.md** - Full step-by-step guide
- **docs/QUICK_REFERENCE.md** - One-page cheat sheet

### Implementation Details

- **docs/PAIRED_NODE_ARCHITECTURE.md** - Paired pool node design
- **docs/PHASE_3_MINING_POOL_STRATEGY.md** - Pool decision engine
- **docs/PATH_VALIDATION_REPORT.md** - Import path validation
- **docs/TESTING_FLOW_AND_GAPS.md** - Status tracker

### Historical

- **docs/POOL_NODE_MAPPING_INTEGRATION.md** - Pool-to-node mapping
- **docs/PHASE_2_COMPLETION_SUMMARY.md** - Fee oracle
- **docs/SUSTAINED_FORK_DETECTION.md** - Fork detection

---

## Helper Scripts

### `run_scenario.sh` - Run Any Scenario

```bash
./run_scenario.sh SCENARIO_FILE [ARGS...]

# Example:
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml /path/to/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0
```

### `run_fork_test.sh` - Complete Test

```bash
./run_fork_test.sh TEST_NAME V27_ECONOMIC V27_HASHRATE [DURATION]

# Example:
./run_fork_test.sh test-001 70 30 1800

# Runs all 4 steps automatically:
# 1. Generate → 2. Deploy → 3. Mine → 4. Analyze
```

---

## Testing

### Run Unit Tests

```bash
cd tests/
python3 test_paired_node_architecture.py  # Test paired nodes
python3 test_pool_decisions.py            # Test pool strategy
python3 test_import_paths.py              # Validate paths
```

### All Tests

```bash
cd tests/
for test in test_*.py; do
    echo "Running $test..."
    python3 "$test"
done
```

---

## Pool Scenarios

Available in `scenarios/config/mining_pools_config.yaml`:

| Scenario | Ideology | Behavior |
|----------|----------|----------|
| `realistic_current` | Low (0.1-0.3) | Mostly profit-focused (recommended) |
| `ideological_fork_war` | High (0.5-0.8) | Willing to mine at loss |
| `pure_profit` | None (0.0) | Switch immediately for profit |

---

## Output Files

After running a test:

| File | Content |
|------|---------|
| `/tmp/partition_pools.json` | Pool decisions and allocations |
| `/tmp/partition_prices.json` | Fork price evolution history |
| `/tmp/partition_fees.json` | Transaction fee evolution |
| `results/test-NAME-analysis.txt` | Fork analysis results |

---

## Timeline

| Step | Duration | Notes |
|------|----------|-------|
| Generate network | 10 seconds | Instant |
| Deploy | 90 seconds | Kubernetes pods |
| Sync | 90 seconds | Bitcoin node sync |
| Mine (30 min) | 1800 seconds | Configurable |
| Analyze | 10 seconds | Can run multiple times |
| **Total** | **~35 minutes** | For 30-minute test |

---

## Requirements

- **Warnet**: Kubernetes-based Bitcoin testing framework
- **Python 3.8+**: For scripts
- **kubectl**: Kubernetes CLI (for warnet)
- **Bitcoin Core**: Multiple versions (v27.0, v26.0)

---

## Development Workflow

This is your **independent research repository**:

1. **Develop** here in `warnetScenarioDiscovery/`
2. **Test** your implementations
3. **Document** your findings
4. **Prove** the approach works

When ready:
5. **Contribute** proven features back to main warnet repo

---

## Common Commands

```bash
# Full test (recommended)
./run_fork_test.sh test-001 70 30 1800

# Generate only
cd networkGen/
python3 partition_network_generator.py --test-id test-001 --v27-economic 70 --v27-hashrate 30

# Run scenario only
./run_scenario.sh partition_miner_with_pools.py --network-yaml /path/to/network.yaml --pool-scenario realistic_current --v27-economic 70.0 --duration 1800

# Analyze only
cd monitoring/
python3 enhanced_fork_analysis.py --network-config /path/to/network/ --pool-decisions /tmp/partition_pools.json --live-query

# Stop network
warnet stop
```

---

## Troubleshooting

### No fork detected

**Solution**: Wait longer or lower `--fork-depth-threshold 3`

### Pool decisions file not found

**Solution**: Ensure scenario running with `--network-yaml` parameter

### Hashrate shows 0%

**Solution**: Run analysis with `--pool-decisions /tmp/partition_pools.json`

### Network already exists

**Solution**: `warnet stop` first

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-26 | 2.0 | Migrated to warnetScenarioDiscovery repo |
| 2026-01-25 | 1.5 | Added hashrate tracking |
| 2026-01-25 | 1.0 | Initial complete implementation |

---

## Contact & Contribution

This is a research repository. When features are proven:
- Document the approach
- Prepare for contribution to main warnet repo
- Submit PR with tested implementation

---

**Status**: Production Ready 🚀
**All Core Features**: ✅ Implemented and Tested
**Ready For**: Research, Testing, Validation

---

For detailed workflows, see:
- `docs/COMPLETE_TESTING_WORKFLOW.md`
- `docs/QUICK_REFERENCE.md`
