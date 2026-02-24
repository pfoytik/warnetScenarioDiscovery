# Parameter Sweep Tools

A modular system for systematically testing fork threshold parameters using Latin Hypercube Sampling (LHS).

## Overview

Instead of testing all possible parameter combinations exhaustively, LHS efficiently samples the parameter space with far fewer tests while maintaining good coverage across all dimensions.

## Scripts

### 1. Generate Scenarios (`1_generate_scenarios.py`)

Generates LHS parameter combinations.

```bash
# Generate 50 scenarios with a fixed seed
python 1_generate_scenarios.py --samples 50 --seed 42

# Preview without saving
python 1_generate_scenarios.py --samples 50 --preview

# Output: scenarios.json
```

**Output:** `scenarios.json` containing all parameter combinations

### 2. Build Configs (`2_build_configs.py`)

Creates network and scenario configurations from the parameter combinations.

```bash
# Build configs using realistic-economy as a base network template (recommended)
python 2_build_configs.py --input scenarios.json \
    --base-network ../../networks/realistic-economy/network.yaml \
    --output-dir ./sweep_output

# Build configs only (skip network generation)
python 2_build_configs.py --input scenarios.json --configs-only
```

**Output:**
```
sweep_output/
├── networks/           # Generated warnet networks (one per scenario)
├── configs/
│   ├── network/        # Individual network configs
│   ├── pools/          # Pool scenario configs
│   └── economic/       # Economic scenario configs
└── build_manifest.json # Build manifest for runner
```

### 3. Run Sweep (`3_run_sweep.py`)

Executes each scenario and collects results. Supports resuming interrupted sweeps.

```bash
# Run all scenarios (1 hour each)
python 3_run_sweep.py --input sweep_output/build_manifest.json --duration 3600

# Dry run (show what would execute)
python 3_run_sweep.py --input sweep_output/build_manifest.json --dry-run

# Run specific scenarios
python 3_run_sweep.py --input sweep_output/build_manifest.json --scenarios sweep_0000 sweep_0001

# Resume an interrupted sweep (automatically skips completed scenarios)
python 3_run_sweep.py --input sweep_output/build_manifest.json --duration 3600
```

> **Note:** `3_run_sweep.py` injects sweep configs into `scenarios/config/mining_pools_config.yaml`
> and `scenarios/config/economic_nodes_config.yaml` at runtime. These files will show as
> modified during a sweep — commit them after the sweep finishes, not mid-run.

**Output:**
```
sweep_output/results/
├── sweep_0000/
│   ├── results.json
│   ├── warnet_logs.txt
│   └── scenario.log
├── sweep_0001/
│   └── ...
└── sweep_progress.json
```

### 4. Analyze Results (`4_analyze_results.py`)

Analyzes results to find critical thresholds and correlations. Safe to run while a sweep
is still in progress — it only reads completed result files and writes to a separate
`analysis/` subdirectory.

```bash
# Analyze results
python 4_analyze_results.py --input sweep_output/results

# With visualizations (requires matplotlib)
python 4_analyze_results.py --input sweep_output/results --visualize
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
python 1_generate_scenarios.py --samples 50 --seed 42

# Step 2: Build networks and configs from the realistic-economy base network
python 2_build_configs.py --input scenarios.json \
    --base-network ../../networks/realistic-economy/network.yaml \
    --output-dir ./sweep_output

# Step 3: Run all scenarios (this takes a while — ~1 hour per scenario)
python 3_run_sweep.py --input sweep_output/build_manifest.json --duration 3600

# Step 4: Analyze results
python 4_analyze_results.py --input sweep_output/results --visualize
```

## Parameters Tested

The parameter space uses **symmetric framing** — split parameters are expressed as a
fraction of the total (0 = all v26, 0.5 = equal split, 1 = all v27), ensuring neither
fork has a structural advantage in the sampling.

| Parameter | Range | Description |
|-----------|-------|-------------|
| `economic_split` | 0–1 | Fraction of economic custody starting on v27 |
| `hashrate_split` | 0–1 | Fraction of initial pool hashrate starting on v27 |
| `pool_ideology_strength` | 0.1–0.9 | Pool conviction level (0=rational, 1=ideological) |
| `pool_profitability_threshold` | 2–30% | Min profit advantage before a pool considers switching |
| `pool_max_loss_pct` | 2–50% | Max revenue loss a committed pool will absorb for ideology |
| `pool_committed_split` | 0–1 | Fraction of committed pool hashrate preferring v27 |
| `pool_neutral_pct` | 10–50% | Percentage of pool hashrate that is purely rational |
| `econ_ideology_strength` | 0–0.8 | Exchange/economic node conviction level |
| `econ_switching_threshold` | 2–25% | Price advantage needed for economic nodes to switch |
| `econ_inertia` | 5–30% | Additional switching friction (infrastructure costs) |
| `user_ideology_strength` | 0.1–0.9 | User conviction level |
| `user_switching_threshold` | 5–20% | Price advantage needed for users to switch |
| `transaction_velocity` | 0.1–0.9 | Fee-generating transaction rate (0=custodial, 1=high volume) |
| `user_nodes_per_partition` | 2–10 | Number of user nodes per network partition |
| `economic_nodes_per_partition` | 1–3 | Number of economic/exchange nodes per partition |
| `solo_miner_hashrate` | 2–15% | Hashrate percentage per solo miner |

### Symmetric Pool Parameterization

The committed pool split is computed as:

```
v27_committed = (1 - pool_neutral_pct) * pool_committed_split
v26_committed = (1 - pool_neutral_pct) * (1 - pool_committed_split)
```

This guarantees `v27_committed + v26_committed + neutral = 1.0` by construction, and
both forks have equal opportunity to receive any level of committed hashrate. A previous
design used `pool_v27_preference_pct` (10–70%) with v26 as a residual, which
structurally biased outcomes toward v27.

## Time Estimates

| Samples | Duration/run | Total Time |
|---------|-------------|------------|
| 50 | 30 min | ~25 hours |
| 50 | 60 min | ~50 hours |
| 100 | 30 min | ~50 hours |
| 100 | 60 min | ~100 hours |

## Tips

- Start with `--samples 50` to validate the pipeline before a larger run
- Use `--dry-run` to check commands before executing
- The runner automatically skips completed scenarios, so interrupted sweeps are safe to resume
- Use `--duration 3600` (60 min) for more stable results — shorter runs may not reach equilibrium
- `4_analyze_results.py` can be run mid-sweep to check progress on completed scenarios

## Analysis Output

The analysis identifies:

1. **Outcome Distribution**: How many scenarios resulted in v27 dominant, v26 dominant, or contested
2. **Critical Thresholds**: Parameter values that predict fork outcomes
3. **Correlations**: Which parameters most strongly influence results
4. **Separation Analysis**: Which parameters best discriminate between outcomes

Outcomes are classified by final v27 hashrate share:
- `v27_dominant`: v27 hashrate share > 65%
- `v26_dominant`: v27 hashrate share < 35%
- `contested`: 35–65% (sustained fork, neither side wins)
