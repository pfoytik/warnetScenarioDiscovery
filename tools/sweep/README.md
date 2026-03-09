# Parameter Sweep Tools

A modular system for systematically testing fork threshold parameters using Latin Hypercube Sampling (LHS) or targeted grid sweeps.

## Overview

Instead of testing all possible parameter combinations exhaustively, LHS efficiently samples the parameter space with far fewer tests while maintaining good coverage across all dimensions. For targeted follow-up questions, the grid sweep generator creates Cartesian product designs over specific axes.

## Scripts

### 1a. Generate Scenarios — LHS (`1_generate_scenarios.py`)

Generates LHS parameter combinations for broad exploration.

```bash
# Generate 50 scenarios with a fixed seed
python 1_generate_scenarios.py --samples 50 --seed 42

# Preview without saving
python 1_generate_scenarios.py --samples 50 --preview

# Output: scenarios.json
```

**Output:** `scenarios.json` containing all parameter combinations

### 1b. Generate Scenarios — Targeted Grid (`1_generate_targeted.py`)

Generates a Cartesian product grid from a YAML spec file. Use this for focused follow-up
sweeps where you want to vary one or two axes while holding everything else fixed.

```bash
# Preview the grid without saving
python 1_generate_targeted.py --spec specs/my_sweep.yaml --preview

# Generate and save
python 1_generate_targeted.py --spec specs/my_sweep.yaml
```

Spec files live in `tools/sweep/specs/`. Each spec defines:
- `name`: sweep identifier
- `description`: research question and hypotheses
- `network`: base network type (`lite` or `realistic-economy-v2`)
- `fixed`: parameters held constant
- `grid`: parameters varied (Cartesian product of all listed values)

**Output:** `tools/sweep/<name>/scenarios.json` and printed next-step commands.

### 2. Build Configs (`2_build_configs.py`)

Creates network and scenario configurations from the parameter combinations.

```bash
# Build configs using realistic-economy-lite as a base network template (recommended)
python 2_build_configs.py \
    --input tools/sweep/<name>/scenarios.json \
    --output-dir tools/sweep/<name> \
    --base-network ../../networks/realistic-economy-lite/network.yaml
```

**Output:**
```
tools/sweep/<name>/
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
# Standard run (144-block retarget, 30 min duration)
python 3_run_sweep.py \
    --input tools/sweep/<name>/build_manifest.json \
    --duration 1800 \
    --interval 2

# 2016-block retarget regime (realistic Bitcoin, ~3.6 hr/scenario)
python 3_run_sweep.py \
    --input tools/sweep/<name>/build_manifest.json \
    --duration 13000 \
    --interval 2 \
    --retarget-interval 2016

# With Option B liveness penalty enabled
python 3_run_sweep.py \
    --input tools/sweep/<name>/build_manifest.json \
    --duration 13000 \
    --interval 2 \
    --retarget-interval 2016 \
    --enable-liveness-penalty

# Dry run (show what would execute)
python 3_run_sweep.py --input tools/sweep/<name>/build_manifest.json --dry-run

# Run specific scenarios
python 3_run_sweep.py --input tools/sweep/<name>/build_manifest.json \
    --scenarios sweep_0000 sweep_0001

# Resume an interrupted sweep (automatically skips completed scenarios)
python 3_run_sweep.py --input tools/sweep/<name>/build_manifest.json --duration 13000
```

**Key flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--duration` | 1800 | Scenario duration in seconds |
| `--interval` | 10 | Block mining interval in seconds |
| `--retarget-interval` | 144 | Blocks between difficulty adjustments. Use `2016` for realistic Bitcoin. **Always set this explicitly.** |
| `--enable-liveness-penalty` | off | Enable Option B price oracle: decays economic factor by block production rate. Dead chains lose their economic premium. Raises price divergence cap from 20% → 50%. |

> **Warning:** `--retarget-interval` defaults to 144. If your research question requires
> the realistic 2016-block retarget regime, you **must** pass `--retarget-interval 2016`
> explicitly — it will not be set automatically.

> **Note:** `3_run_sweep.py` injects sweep configs into `scenarios/config/mining_pools_config.yaml`
> and `scenarios/config/economic_nodes_config.yaml` at runtime. These files will show as
> modified during a sweep — commit them after the sweep finishes, not mid-run.

**Output:**
```
tools/sweep/<name>/results/
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
python 4_analyze_results.py \
    --input tools/sweep/<name>/results \
    --manifest tools/sweep/<name>/build_manifest.json

# With visualizations (requires matplotlib)
python 4_analyze_results.py \
    --input tools/sweep/<name>/results \
    --manifest tools/sweep/<name>/build_manifest.json \
    --visualize
```

**Output:**
```
tools/sweep/<name>/results/analysis/
├── report.txt          # Human-readable summary
├── summary.json        # Outcome statistics
├── thresholds.json     # Critical threshold analysis
├── correlations.json   # Parameter correlations
├── sweep_data.csv      # Full dataset for external analysis
└── figures/            # Visualizations (if --visualize)
```

## Complete Workflow

### Broad LHS exploration

```bash
cd tools/sweep

# Step 1: Generate parameter combinations
python 1_generate_scenarios.py --samples 50 --seed 42

# Step 2: Build networks and configs
python 2_build_configs.py --input scenarios.json \
    --base-network ../../networks/realistic-economy-lite/network.yaml \
    --output-dir ./sweep_output

# Step 3: Run all scenarios
python 3_run_sweep.py --input sweep_output/build_manifest.json \
    --duration 1800 --interval 2

# Step 4: Analyze results
python 4_analyze_results.py --input sweep_output/results \
    --manifest sweep_output/build_manifest.json --visualize
```

### Targeted grid sweep (2016-block regime)

```bash
cd tools/sweep

# Step 1: Preview and generate from spec
python 1_generate_targeted.py --spec specs/my_sweep.yaml --preview
python 1_generate_targeted.py --spec specs/my_sweep.yaml

# Step 2: Build configs
python 2_build_configs.py \
    --input targeted_my_sweep/scenarios.json \
    --output-dir targeted_my_sweep \
    --base-network ../../networks/realistic-economy-lite/network.yaml

# Step 3: Run with 2016-block retarget (MUST set --retarget-interval explicitly)
python 3_run_sweep.py \
    --input targeted_my_sweep/build_manifest.json \
    --duration 13000 --interval 2 --retarget-interval 2016

# Step 4: Analyze
python 4_analyze_results.py \
    --input targeted_my_sweep/results \
    --manifest targeted_my_sweep/build_manifest.json
```

## Price Oracle Modes

The price oracle supports two modes, controlled by a flag passed to `3_run_sweep.py`:

### Default mode (no flag)
`combined_factor = chain_f*0.3 + econ_f*0.5 + hash_f*0.2`

Each factor `f = 0.8 + weight*0.4` (range 0.8–1.2). Price divergence capped at ±20%.
Economic weight (`econ_f`) reflects custody concentration and is static — a chain with
70% economic support gets a price floor even if it produces zero blocks.

### Option B: Liveness penalty (`--enable-liveness-penalty`)
```
production_ratio = min(1.0, actual_blocks_per_hour / target_blocks_per_hour)
effective_econ_f = 1.0 + (raw_econ_f - 1.0) * production_ratio^exponent
```

At full block production rate → `effective_econ_f` unchanged (same as default).
At zero block production → `effective_econ_f = 1.0` (neutral; no economic premium or discount).
Price divergence cap raised to ±50% to allow ghost-town chains to express their true value.

**When to use:** Use `--enable-liveness-penalty` when you want market confidence to reflect
chain usability, not just custody. Default=off preserves comparability with all prior sweeps.

**Assumption (documented):** `liveness_exponent=1.0` means confidence decays linearly with
block rate. This is an explicit modeling assumption that can be updated with empirical data.

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
both forks have equal opportunity to receive any level of committed hashrate.

## Time Estimates

### 144-block retarget (accelerated, default)
| Samples | Duration/run | Total Time |
|---------|-------------|------------|
| 50 | 30 min | ~25 hours |
| 50 | 60 min | ~50 hours |

### 2016-block retarget (realistic Bitcoin)
| Samples | Duration/run | Total Time |
|---------|-------------|------------|
| 5 | ~3.6 hr | ~18 hours |
| 10 | ~3.6 hr | ~36 hours |

> **Duration guidance for 2016-block sweeps:** At 50% initial v27 hashrate and `--interval 2`,
> the first v27 difficulty retarget fires at ~8,100s. Allow ~4,000s post-retarget for cascade
> to complete. Use `--duration 13000` (validated by sweep9).

## Tips

- Always set `--retarget-interval` explicitly — the default (144) is not suitable for
  realistic Bitcoin fork dynamics research
- Use `--dry-run` to verify commands before a long run
- The runner automatically skips completed scenarios, so interrupted sweeps are safe to resume
- `4_analyze_results.py` can be run mid-sweep to check progress on completed scenarios
- New sweeps that change oracle mode (`--enable-liveness-penalty`) are not directly comparable
  to prior sweeps run without it — treat them as a separate series

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
