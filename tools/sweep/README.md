# Parameter Sweep Tools

A modular system for systematically testing fork threshold parameters using Latin Hypercube Sampling (LHS).

## Overview

Instead of testing all 59,049 parameter combinations (3^10), LHS efficiently samples the parameter space with far fewer tests while maintaining good coverage.

## Scripts

### 1. Generate Scenarios (`1_generate_scenarios.py`)

Generates LHS parameter combinations.

```bash
# Generate 200 scenarios (recommended starting point)
python 1_generate_scenarios.py --samples 200 --seed 42

# Preview without saving
python 1_generate_scenarios.py --samples 50 --preview

# Output: scenarios.json
```

**Output:** `scenarios.json` containing all parameter combinations

### 2. Build Configs (`2_build_configs.py`)

Creates network and scenario configurations from the parameter combinations.

```bash
# Build all configs
python 2_build_configs.py --input scenarios.json --output-dir ./sweep_output

# Build configs only (skip network generation)
python 2_build_configs.py --input scenarios.json --configs-only

# Output: sweep_output/
```

**Output:**
```
sweep_output/
├── networks/           # Generated warnet networks
├── configs/
│   ├── network/        # Individual network configs
│   ├── pools/          # Pool scenario configs
│   └── economic/       # Economic scenario configs
└── build_manifest.json # Build manifest for runner
```

### 3. Run Sweep (`3_run_sweep.py`)

Executes each scenario and collects results. Supports resuming interrupted sweeps.

```bash
# Run all scenarios (30 min each)
python 3_run_sweep.py --input sweep_output/build_manifest.json

# Run with custom duration
python 3_run_sweep.py --input sweep_output/build_manifest.json --duration 3600

# Dry run (show what would execute)
python 3_run_sweep.py --input sweep_output/build_manifest.json --dry-run

# Run specific scenarios
python 3_run_sweep.py --input sweep_output/build_manifest.json --scenarios sweep_0000 sweep_0001

# Output: sweep_output/results/
```

**Output:**
```
sweep_output/results/
├── sweep_0000/
│   ├── results.json
│   └── scenario.log
├── sweep_0001/
│   └── ...
└── sweep_progress.json
```

### 4. Analyze Results (`4_analyze_results.py`)

Analyzes results to find critical thresholds and correlations.

```bash
# Analyze results
python 4_analyze_results.py --input sweep_output/results

# With visualizations
python 4_analyze_results.py --input sweep_output/results --visualize

# Output: sweep_output/results/analysis/
```

**Output:**
```
sweep_output/results/analysis/
├── report.txt          # Human-readable summary
├── summary.json        # Outcome statistics
├── thresholds.json     # Critical threshold analysis
├── correlations.json   # Parameter correlations
├── sweep_data.csv      # Full dataset for external analysis
└── figures/            # Visualizations (if --visualize)
```

## Complete Workflow

```bash
cd tools/sweep

# Step 1: Generate parameter combinations
python 1_generate_scenarios.py --samples 200 --seed 42

# Step 2: Build networks and configs
python 2_build_configs.py --input scenarios.json --output-dir ./sweep_output

# Step 3: Run all scenarios (this takes a while!)
python 3_run_sweep.py --input sweep_output/build_manifest.json --duration 1800

# Step 4: Analyze results
python 4_analyze_results.py --input sweep_output/results --visualize
```

## Parameters Tested

| Parameter | Range | Description |
|-----------|-------|-------------|
| `v27_economic_pct` | 20-80% | Initial economic weight on v27 |
| `v27_hashrate_pct` | 20-80% | Initial hashrate on v27 |
| `pool_ideology_strength` | 0.1-0.9 | Pool conviction level |
| `pool_profitability_threshold` | 2-30% | Min profit to switch |
| `pool_max_loss_pct` | 2-50% | Max loss for ideology |
| `pool_v27_preference_pct` | 10-70% | % pools favoring v27 |
| `pool_neutral_pct` | 10-50% | % neutral pools |
| `econ_ideology_strength` | 0-0.8 | Exchange conviction |
| `econ_switching_threshold` | 2-25% | Exchange price sensitivity |
| `econ_inertia` | 5-30% | Exchange switching friction |
| `user_ideology_strength` | 0.1-0.9 | User conviction |
| `user_switching_threshold` | 5-20% | User price sensitivity |
| `transaction_velocity` | 0.1-0.9 | Fee generation rate |
| `user_nodes_per_partition` | 2-10 | Network structure |
| `economic_nodes_per_partition` | 1-3 | Network structure |
| `solo_miner_hashrate` | 2-15% | Solo miner participation |

## Time Estimates

| Samples | Duration | Total Time |
|---------|----------|------------|
| 50 | 30 min | ~25 hours |
| 100 | 30 min | ~50 hours |
| 200 | 30 min | ~100 hours |
| 200 | 15 min | ~50 hours |

## Tips

- Start with `--samples 50` to validate the pipeline
- Use `--dry-run` to check commands before running
- The runner skips completed scenarios, so you can resume interrupted sweeps
- Use shorter `--duration` for faster iteration (15-20 min may be sufficient)
- Run overnight or on a dedicated machine for large sweeps

## Analysis Output

The analysis identifies:

1. **Outcome Distribution**: How many scenarios resulted in v27 dominant, v26 dominant, or contested
2. **Critical Thresholds**: Parameter values that predict fork outcomes
3. **Correlations**: Which parameters most strongly influence results
4. **Separation Analysis**: Which parameters best discriminate between outcomes

Example threshold finding:
```
v27 becomes dominant when:
  - pool_ideology_strength > 0.6 AND
  - v27_economic_pct > 45%

v26 wins when:
  - pool_max_loss_pct < 0.15 (low conviction)
  - regardless of economic support
```
