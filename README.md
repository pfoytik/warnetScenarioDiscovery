# Warnet Scenario Discovery - Bitcoin Fork Research

Independent research repository for testing Bitcoin protocol forks using Warnet.

**Status**: ✅ Production Ready | **Last Updated**: 2026-01-26

---

## Quick Start

### Run a Complete Fork Test

```bash
# One command runs everything (generate → deploy → mine → analyze):
./run_fork_test.sh test-001 70 30 1800
```

That's it! See results in ~35 minutes.

---

## What This Does

Tests Bitcoin forks with:
- ✅ **Hashrate tracking** (which pools mine which fork)
- ✅ **Economic analysis** (custody, volume, consensus weight)
- ✅ **Mining pool dynamics** (profitability + ideology)
- ✅ **Price & fee evolution**
- ✅ **Paired-node architecture** (realistic simulation)

---

## Documentation

| Document | Purpose |
|----------|---------|
| **README_RESEARCH.md** | Complete repository guide |
| **MIGRATION_TO_RESEARCH_REPO.md** | Migration notes & new commands |
| **docs/COMPLETE_TESTING_WORKFLOW.md** | Step-by-step testing guide |
| **docs/QUICK_REFERENCE.md** | One-page cheat sheet |

---

## Repository Structure

```
warnetScenarioDiscovery/
├── scenarios/          # Warnet scenario scripts
│   ├── lib/            # Supporting modules
│   ├── config/         # Configuration files
│   └── *.py            # Scenario scripts
│
├── networkGen/         # Network generation
├── monitoring/         # Fork analysis tools
├── tests/              # Test suite
├── docs/               # Documentation
│
├── run_scenario.sh     # Helper: Run any scenario
└── run_fork_test.sh    # Helper: Complete test
```

---

## Helper Scripts

### `run_fork_test.sh` - Complete Test (Recommended)

```bash
./run_fork_test.sh TEST_NAME V27_ECONOMIC V27_HASHRATE DURATION

# Example: 30-minute test with 70% economic on v27, 30% hashrate
./run_fork_test.sh test-001 70 30 1800
```

Runs all 4 steps automatically:
1. Generate network
2. Deploy to warnet
3. Run mining scenario
4. Analyze fork with all metrics

### `run_scenario.sh` - Run Scenario Only

```bash
./run_scenario.sh SCENARIO_FILE [ARGS...]

# Example:
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml /path/to/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0
```

---

## Example Output

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

## Testing Scenarios

| Scenario | v27-economic | v27-hashrate | Purpose |
|----------|--------------|--------------|---------|
| Aligned | 70 | 70 | Both favor same fork |
| Conflict | 70 | 30 | Test pool reallocation |
| Balanced | 50 | 50 | Contested fork |
| Extreme | 95 | 10 | Overwhelming dominance |

---

## Manual Workflow

If you prefer step-by-step control:

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

## All Implemented Features ✅

1. Network generation with paired pool nodes
2. Partition-based fork simulation
3. Dynamic mining pool decisions (profitability + ideology)
4. Price oracle (fork value evolution)
5. Fee oracle (transaction fee dynamics)
6. **Hashrate tracking per fork** (NEW!)
7. Economic weight analysis (custody, volume)
8. Consensus weight calculation
9. Pool-to-node mapping
10. Complete fork analysis with all metrics

---

## Timeline

| Step | Duration |
|------|----------|
| Generate | 10s |
| Deploy | 90s |
| Sync | 90s |
| Mine (30min) | 1800s |
| Analyze | 10s |
| **Total** | **~35 min** |

---

## Output Files

After running a test:

- `/tmp/partition_pools.json` - Pool decisions
- `/tmp/partition_prices.json` - Price history
- `/tmp/partition_fees.json` - Fee history

---

## Testing

```bash
cd tests/
python3 test_paired_node_architecture.py  # Test paired nodes
python3 test_pool_decisions.py            # Test pool strategy
python3 test_import_paths.py              # Validate paths
```

All tests should pass ✅

---

## Requirements

- Warnet (Kubernetes-based Bitcoin testing)
- Python 3.8+
- kubectl (for warnet)
- Bitcoin Core (v27.0, v26.0)

---

## Development Philosophy

This is your **independent research repository**:

1. **Develop** - Test implementations here
2. **Validate** - Prove the approach works
3. **Document** - Record findings
4. **Contribute** - Submit proven features to main warnet repo

---

## Getting Help

- **Quick commands**: `docs/QUICK_REFERENCE.md`
- **Full workflow**: `docs/COMPLETE_TESTING_WORKFLOW.md`
- **Migration notes**: `MIGRATION_TO_RESEARCH_REPO.md`
- **Repository guide**: `README_RESEARCH.md`

---

## Common Commands

```bash
# Complete test (easiest)
./run_fork_test.sh test-001 70 30 1800

# Run scenario only
./run_scenario.sh partition_miner_with_pools.py [args...]

# Generate network only
cd networkGen/
python3 partition_network_generator.py --test-id test-001 --v27-economic 70 --v27-hashrate 30

# Analyze only
cd monitoring/
python3 enhanced_fork_analysis.py --network-config /path/to/network/ --pool-decisions /tmp/partition_pools.json --live-query

# Stop network
warnet stop

# View docs
cat docs/QUICK_REFERENCE.md
```

---

**Status**: Production Ready 🚀
**All Core Metrics**: Implemented and Tested ✅
**Ready For**: Research, Testing, Validation

**Start here**: `./run_fork_test.sh test-001 70 30 1800`
