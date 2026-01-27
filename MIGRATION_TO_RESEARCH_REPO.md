# Migration to Research Repository

**Date**: 2026-01-26
**Status**: ✅ Complete

---

## What Changed

All research materials have been migrated from:
- **OLD**: `warnet/warnet/resources/scenarios/research/`
- **NEW**: `warnetScenarioDiscovery/` (this repository)

---

## New Structure

```
warnetScenarioDiscovery/
├── scenarios/          # ← MOVED from warnet/resources/scenarios/research/
│   ├── lib/
│   ├── config/
│   └── *.py
│
├── tests/             # ← MOVED from warnet/resources/scenarios/research/tests/
│
├── docs/              # ← MOVED from warnet/resources/scenarios/research/docs/
│
├── networkGen/        # ← Already here
├── monitoring/        # ← Already here (enhanced_fork_analysis.py added)
│
├── run_scenario.sh    # ← NEW helper script
└── run_fork_test.sh   # ← NEW complete test runner
```

---

## New Commands

### OLD Way (from warnet fork)

```bash
cd /home/pfoytik/bitcoinTools/warnet

# Generate
cd warnetScenarioDiscovery/networkGen
python3 partition_network_generator.py ...

# Deploy
cd ../../
warnet deploy test-networks/...

# Run scenario
cd warnet/resources/scenarios/research
warnet run partition_miner_with_pools.py ...

# Analyze
cd ../../../warnetScenarioDiscovery/monitoring
python3 enhanced_fork_analysis.py ...
```

### NEW Way (from research repo)

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery

# Option 1: Run complete test (EASIEST)
./run_fork_test.sh test-001 70 30 1800

# Option 2: Run steps manually
cd networkGen/
python3 partition_network_generator.py --test-id test-001 --v27-economic 70 --v27-hashrate 30

warnet deploy ../test-networks/test-test-001-economic-70-hashrate-30/

cd ..
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml ../test-networks/test-test-001-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0

cd monitoring/
python3 enhanced_fork_analysis.py \
    --network-config ../test-networks/test-test-001-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query
```

---

## Key Benefits

### Before (Mixed Location)

❌ Research code split between two locations
❌ Long complex paths to navigate
❌ Hard to share as a package
❌ Documentation scattered

### After (Research Repo)

✅ All research code in one place
✅ Helper scripts for easy execution
✅ Clean separation from warnet fork
✅ Ready to contribute back when proven

---

## Quick Reference

### Run Complete Test

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
./run_fork_test.sh test-001 70 30 1800
```

### Run Just a Scenario

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml /path/to/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0
```

### View Documentation

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
cat docs/COMPLETE_TESTING_WORKFLOW.md
cat docs/QUICK_REFERENCE.md
cat README_RESEARCH.md
```

---

## Path Updates

### Network Generation

- **OLD**: `cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen`
- **NEW**: `cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen` ✅ Same

### Scenarios

- **OLD**: `cd /home/pfoytik/bitcoinTools/warnet/warnet/resources/scenarios/research`
- **NEW**: `cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/scenarios`

Or use helper:
```bash
./run_scenario.sh partition_miner_with_pools.py [args...]
```

### Analysis

- **OLD**: `cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring`
- **NEW**: `cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring` ✅ Same

### Documentation

- **OLD**: `warnet/warnet/resources/scenarios/research/docs/`
- **NEW**: `warnetScenarioDiscovery/docs/`

---

## File Locations

| Category | Old Location | New Location |
|----------|-------------|--------------|
| Scenarios | `warnet/resources/scenarios/research/scenarios/` | `warnetScenarioDiscovery/scenarios/` |
| Library | `warnet/resources/scenarios/research/lib/` | `warnetScenarioDiscovery/scenarios/lib/` |
| Config | `warnet/resources/scenarios/research/config/` | `warnetScenarioDiscovery/scenarios/config/` |
| Tests | `warnet/resources/scenarios/research/tests/` | `warnetScenarioDiscovery/tests/` |
| Docs | `warnet/resources/scenarios/research/docs/` | `warnetScenarioDiscovery/docs/` |
| Network Gen | `warnetScenarioDiscovery/networkGen/` | `warnetScenarioDiscovery/networkGen/` ✅ Same |
| Monitoring | `warnetScenarioDiscovery/monitoring/` | `warnetScenarioDiscovery/monitoring/` ✅ Same |

---

## What to Use

### For Documentation

**Start here**:
1. `README_RESEARCH.md` - Repository overview
2. `docs/COMPLETE_TESTING_WORKFLOW.md` - Full workflow
3. `docs/QUICK_REFERENCE.md` - Quick commands

### For Running Tests

**Use helper scripts**:
1. `./run_fork_test.sh` - Complete test (recommended)
2. `./run_scenario.sh` - Run scenario only

### For Development

**Source code locations**:
1. `scenarios/` - Scenario scripts
2. `scenarios/lib/` - Supporting modules
3. `scenarios/config/` - Configuration files
4. `tests/` - Test suite

---

## Validation

All paths have been validated:
- ✅ Scenarios can import from lib/
- ✅ Scenarios can access config/
- ✅ Helper scripts work correctly
- ✅ Tests pass

Run validation:
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tests
python3 test_import_paths.py
```

Expected: `2/2 tests passed`

---

## Next Steps

### For Normal Use

Just use the helper scripts:
```bash
./run_fork_test.sh test-001 70 30 1800
```

Everything is handled automatically!

### For Development

1. Edit files in `scenarios/`, `scenarios/lib/`, or `scenarios/config/`
2. Test with `./run_scenario.sh`
3. Run tests in `tests/`
4. Document in `docs/`

### For Contributing to Warnet

When features are proven and ready:
1. Document the approach
2. Clean up code for contribution
3. Prepare PR for main warnet repo
4. Include tests and documentation

---

## Troubleshooting

### "Command not found: warnet"

**Solution**: Ensure warnet is in PATH:
```bash
which warnet
# Should output: /home/pfoytik/bitcoinTools/warnet/warnet/.venv/bin/warnet
```

If not found:
```bash
cd /home/pfoytik/bitcoinTools/warnet
source warnet/.venv/bin/activate
```

### "Permission denied" on helper scripts

**Solution**: Make executable:
```bash
chmod +x run_scenario.sh run_fork_test.sh
```

### Import errors

**Solution**: Run validation test:
```bash
cd tests/
python3 test_import_paths.py
```

All tests should pass.

---

## Summary

✅ **All files migrated** to research repository
✅ **Helper scripts created** for easy execution
✅ **Documentation updated** with new structure
✅ **Paths validated** and tested
✅ **Ready for research** and testing

**Main command to remember**:
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
./run_fork_test.sh TEST_NAME V27_ECONOMIC V27_HASHRATE DURATION
```

That's it! 🚀

---

**Migration Date**: 2026-01-26
**Status**: Complete
**Next**: Run your first test!
