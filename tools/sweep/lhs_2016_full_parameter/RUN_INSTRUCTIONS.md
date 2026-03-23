# LHS 2016-block Full Parameter Sweep

**Purpose:** Provide unbiased feature importance estimates at 2016-block retarget by sampling all 4 key parameters via Latin Hypercube Sampling.

**Status:** Generated and built. Ready to run.

## Why This Sweep?

Previous 2016-block sweeps only varied `economic_split` and `pool_committed_split` while fixing `pool_ideology_strength` and `pool_max_loss_pct`. This created sampling bias that prevented valid feature importance comparison between 144-block and 2016-block regimes.

This LHS sweep samples all 4 parameters proportionally to:
1. Provide unbiased feature importance estimates
2. Enable valid regime comparison with 144-block data
3. Detect interaction effects missed by targeted sweeps
4. Generate proper PRIM uncertainty bounds

## Quick Start (4 Namespaces)

Run all 4 commands in parallel on the same server:

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools/sweep

# Namespace 1: scenarios 0-15
python 3_run_sweep.py \
  --input lhs_2016_full_parameter/build_manifest.json \
  --results-dir lhs_2016_full_parameter/results \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --namespace ns1 \
  --scenarios sweep_0000 sweep_0001 sweep_0002 sweep_0003 sweep_0004 sweep_0005 sweep_0006 sweep_0007 sweep_0008 sweep_0009 sweep_0010 sweep_0011 sweep_0012 sweep_0013 sweep_0014 sweep_0015

# Namespace 2: scenarios 16-31
python 3_run_sweep.py \
  --input lhs_2016_full_parameter/build_manifest.json \
  --results-dir lhs_2016_full_parameter/results \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --namespace ns2 \
  --scenarios sweep_0016 sweep_0017 sweep_0018 sweep_0019 sweep_0020 sweep_0021 sweep_0022 sweep_0023 sweep_0024 sweep_0025 sweep_0026 sweep_0027 sweep_0028 sweep_0029 sweep_0030 sweep_0031

# Namespace 3: scenarios 32-47
python 3_run_sweep.py \
  --input lhs_2016_full_parameter/build_manifest.json \
  --results-dir lhs_2016_full_parameter/results \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --namespace ns3 \
  --scenarios sweep_0032 sweep_0033 sweep_0034 sweep_0035 sweep_0036 sweep_0037 sweep_0038 sweep_0039 sweep_0040 sweep_0041 sweep_0042 sweep_0043 sweep_0044 sweep_0045 sweep_0046 sweep_0047

# Namespace 4: scenarios 48-63
python 3_run_sweep.py \
  --input lhs_2016_full_parameter/build_manifest.json \
  --results-dir lhs_2016_full_parameter/results \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --namespace ns4 \
  --scenarios sweep_0048 sweep_0049 sweep_0050 sweep_0051 sweep_0052 sweep_0053 sweep_0054 sweep_0055 sweep_0056 sweep_0057 sweep_0058 sweep_0059 sweep_0060 sweep_0061 sweep_0062 sweep_0063
```

## Sweep Details

| Parameter | Value |
|-----------|-------|
| Total scenarios | 64 |
| Scenarios per namespace | 16 |
| Runtime per scenario | ~35 min |
| Runtime per namespace | ~9.5 hours |
| Runtime (4 namespaces parallel) | ~9.5 hours |

### LHS Parameters (Varied)

| Parameter | Range |
|-----------|-------|
| economic_split | [0.30, 0.80] |
| pool_committed_split | [0.15, 0.70] |
| pool_ideology_strength | [0.30, 0.80] |
| pool_max_loss_pct | [0.10, 0.40] |

### Fixed Parameters

| Parameter | Value |
|-----------|-------|
| hashrate_split | 0.25 |
| pool_neutral_pct | 30.0 |
| pool_profitability_threshold | 0.16 |
| econ_ideology_strength | 0.40 |
| econ_switching_threshold | 0.10 |
| econ_inertia | 0.05 |
| user_ideology_strength | 0.49 |
| user_switching_threshold | 0.12 |
| user_nodes_per_partition | 6 |
| economic_nodes_per_partition | 2 |
| transaction_velocity | 0.5 |
| solo_miner_hashrate | 0.085 |

## After Completion

1. Analyze results:
```bash
python 4_analyze_results.py --input lhs_2016_full_parameter/results
```

2. Add to database:
```bash
python 5_build_database.py
```

3. Re-run boundary analysis:
```bash
cd ../discovery
python fit_boundary.py --db ../sweep/sweep_results.db --compare-regimes
```

4. Compare feature importance between regimes — if the shift persists with balanced LHS data, it's a genuine regime effect.

## Regenerating This Sweep

```bash
python 1_generate_lhs.py --spec specs/lhs_2016_full_parameter.yaml
python 2_build_configs.py --input lhs_2016_full_parameter/scenarios.json --output-dir lhs_2016_full_parameter
```
