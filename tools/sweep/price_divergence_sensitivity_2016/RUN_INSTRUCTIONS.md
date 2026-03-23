# Price Divergence Sensitivity Sweep (2016-block)

**Purpose:** Test whether the ~65% economic support inversion threshold is an artifact of the ±20% max price divergence cap.

**Status:** Generated and built. Ready to run.

## Quick Start

Each divergence level can run on a separate server in parallel (~7 hours each):

```bash
# Server 1: ±10% divergence
python tools/sweep/3_run_sweep.py \
  --input price_divergence_sensitivity_2016/build_manifest.json \
  --results-dir price_divergence_sensitivity_2016/results_div10 \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --max-price-divergence 0.10

# Server 2: ±20% divergence (control - current default)
python tools/sweep/3_run_sweep.py \
  --input price_divergence_sensitivity_2016/build_manifest.json \
  --results-dir price_divergence_sensitivity_2016/results_div20 \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --max-price-divergence 0.20

# Server 3: ±30% divergence
python tools/sweep/3_run_sweep.py \
  --input price_divergence_sensitivity_2016/build_manifest.json \
  --results-dir price_divergence_sensitivity_2016/results_div30 \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --max-price-divergence 0.30

# Server 4: ±40% divergence
python tools/sweep/3_run_sweep.py \
  --input price_divergence_sensitivity_2016/build_manifest.json \
  --results-dir price_divergence_sensitivity_2016/results_div40 \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --max-price-divergence 0.40
```

## Sweep Details

| Parameter | Values |
|-----------|--------|
| Scenarios per divergence level | 12 |
| Total scenarios (all 4 levels) | 48 |
| Runtime per level | ~7 hours |
| Runtime (parallel) | ~7 hours |
| Runtime (sequential) | ~28 hours |

### Grid Parameters

| Parameter | Values |
|-----------|--------|
| economic_split | 0.55, 0.65, 0.75 |
| pool_committed_split | 0.30, 0.40 |
| hashrate_split | 0.25, 0.50 |

### Fixed Parameters

| Parameter | Value |
|-----------|-------|
| pool_neutral_pct | 30.0 |
| pool_ideology_strength | 0.51 |
| pool_max_loss_pct | 0.26 |
| econ_switching_threshold | 0.10 |
| econ_inertia | 0.05 |

## Expected Outcomes

| Result | Interpretation |
|--------|----------------|
| Threshold stays at ~65% across all caps | Likely fundamental dynamic |
| Threshold moves proportionally with cap | Model-dependent (ceiling effect) |
| Threshold disappears at ±30-40% | Artifact of the ±20% constraint |
| Inversion effect strengthens at higher caps | Real dynamic being dampened |

## After Completion

1. Run analysis on each results directory:
```bash
python 4_analyze_results.py --input price_divergence_sensitivity_2016/results_div10
python 4_analyze_results.py --input price_divergence_sensitivity_2016/results_div20
python 4_analyze_results.py --input price_divergence_sensitivity_2016/results_div30
python 4_analyze_results.py --input price_divergence_sensitivity_2016/results_div40
```

2. Compare v27 win rates at each economic_split level across divergence caps

3. Update `docs/phase2_scenario_discovery_preliminary.md` with findings
