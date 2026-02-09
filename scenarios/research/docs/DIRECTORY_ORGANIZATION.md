# Research Directory Organization

**Date**: 2026-01-26
**Status**: Reorganized for better maintainability

---

## Directory Structure

```
research/
├── README.md                          # Main directory guide
├── DIRECTORY_ORGANIZATION.md          # This file
│
├── scenarios/                         # 🎬 Main scenario scripts
│   ├── partition_miner_with_pools.py          ⭐ Production scenario
│   ├── partition_miner_full_economics.py      Legacy
│   ├── partition_miner_price_test.py          Testing
│   └── partition_miner_with_price.py          Legacy
│
├── lib/                              # 📚 Supporting library modules
│   ├── __init__.py                            Package initialization
│   ├── price_oracle.py                        Fork price evolution
│   ├── fee_oracle.py                          Fee market dynamics
│   └── mining_pool_strategy.py                Pool decision engine
│
├── config/                           # ⚙️ Configuration files
│   ├── mining_pools_config.yaml               Pool profiles & scenarios
│   ├── price_model_config.yaml                Price model parameters
│   └── fee_model_config.yaml                  Fee model parameters
│
├── tests/                            # ✅ Unit & integration tests
│   ├── test_paired_node_architecture.py       Paired pool nodes
│   ├── test_pool_decisions.py                 Pool strategy
│   ├── test_yaml_pool_mapping.py              Network parsing
│   ├── test_sustained_ideology.py             Ideological behavior
│   ├── test_sustained_fork_detection.py       Fork detection
│   ├── test_economics_simple.py               Basic economics
│   └── test_full_economics_integration.py     Full integration
│
└── docs/                             # 📖 Documentation
    ├── COMPLETE_TESTING_WORKFLOW.md           ⭐ Step-by-step guide
    ├── QUICK_REFERENCE.md                     ⭐ One-page cheat sheet
    ├── TESTING_FLOW_AND_GAPS.md               Status tracker
    ├── PAIRED_NODE_ARCHITECTURE.md            Design doc
    ├── POOL_NODE_MAPPING_INTEGRATION.md       Implementation notes
    ├── PHASE_2_COMPLETION_SUMMARY.md          Fee oracle
    ├── PHASE_3_MINING_POOL_STRATEGY.md        Pool strategy
    └── SUSTAINED_FORK_DETECTION.md            Fork detection
```

---

## File Count Summary

| Directory | Files | Purpose |
|-----------|-------|---------|
| scenarios/ | 4 | Main executable scenarios |
| lib/ | 3 + __init__ | Supporting library code |
| config/ | 3 | YAML configuration |
| tests/ | 7 | Test suite |
| docs/ | 8 | Documentation |
| **Total** | **26** | |

---

## Changes from Previous Organization

### Before (Flat Structure)
```
research/
├── partition_miner_with_pools.py
├── partition_miner_full_economics.py
├── partition_miner_price_test.py
├── partition_miner_with_price.py
├── price_oracle.py
├── fee_oracle.py
├── mining_pool_strategy.py
├── mining_pools_config.yaml
├── price_model_config.yaml
├── fee_model_config.yaml
├── test_paired_node_architecture.py
├── test_pool_decisions.py
├── test_yaml_pool_mapping.py
├── ... (7 more test files)
├── COMPLETE_TESTING_WORKFLOW.md
├── ... (7 more docs)
└── __pycache__/
```

**Problems**:
- ❌ All 26+ files in one directory
- ❌ Hard to find specific files
- ❌ No clear separation of concerns
- ❌ Documentation mixed with code

### After (Organized Structure)
```
research/
├── scenarios/      # 4 files - What you run
├── lib/           # 4 files - Supporting code
├── config/        # 3 files - Configuration
├── tests/         # 7 files - Validation
└── docs/          # 8 files - Documentation
```

**Benefits**:
- ✅ Clear separation by purpose
- ✅ Easy to find what you need
- ✅ Logical grouping
- ✅ Scalable structure

---

## Import Path Updates

### For Scenarios (in scenarios/)

Import library modules from lib/:

```python
import os
_lib_dir = os.path.join(os.path.dirname(__file__), '../lib')
exec(open(os.path.join(_lib_dir, 'price_oracle.py')).read().split('if __name__')[0])
exec(open(os.path.join(_lib_dir, 'fee_oracle.py')).read().split('if __name__')[0])
exec(open(os.path.join(_lib_dir, 'mining_pool_strategy.py')).read().split('if __name__')[0])
```

Load config files from config/:

```python
_config_path = os.path.join(os.path.dirname(__file__), '../config/mining_pools_config.yaml')
pools = load_pools_from_config(_config_path, scenario_name)
```

### For Tests (in tests/)

Tests can remain as-is since they reference the parent modules directly.

---

## Running Commands

### Before Reorganization
```bash
warnet run partition_miner_with_pools.py ...
```

### After Reorganization
```bash
warnet run scenarios/partition_miner_with_pools.py ...
```

**Note**: Add `scenarios/` prefix to scenario path.

---

## Migration Checklist

✅ **Completed**:
- [x] Created directory structure (scenarios/, lib/, config/, tests/, docs/)
- [x] Moved all scenario scripts to scenarios/
- [x] Moved all library modules to lib/
- [x] Moved all config files to config/
- [x] Moved all test files to tests/
- [x] Moved all documentation to docs/
- [x] Created lib/__init__.py
- [x] Updated partition_miner_with_pools.py import paths
- [x] Created README.md
- [x] Created DIRECTORY_ORGANIZATION.md

⚠️ **To Test**:
- [ ] Run partition_miner_with_pools.py scenario
- [ ] Verify pool strategy loads correctly
- [ ] Confirm config files are found
- [ ] Run test suite

---

## Quick Reference

### Find a Scenario
```bash
ls scenarios/
```

### Find Configuration
```bash
ls config/
```

### Find Documentation
```bash
ls docs/
# Start with: docs/COMPLETE_TESTING_WORKFLOW.md
```

### Run Tests
```bash
cd tests/
python3 test_paired_node_architecture.py
```

---

## Maintenance Notes

### Adding New Files

**New Scenario**:
- Place in `scenarios/`
- Use lib/ imports as shown above
- Update README.md scenarios table

**New Library Module**:
- Place in `lib/`
- Add to lib/__init__.py __all__ list
- Document in README.md

**New Config**:
- Place in `config/`
- Document parameters in README.md
- Reference from scenarios using relative path

**New Test**:
- Place in `tests/`
- Name with `test_` prefix
- Add to README.md test table

**New Documentation**:
- Place in `docs/`
- Add to README.md docs table
- Link from relevant files

---

**Organization Date**: 2026-01-26
**Status**: ✅ Complete
**Benefits**: Better maintainability, easier navigation, clearer structure
