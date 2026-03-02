# Balanced Baseline Sweep

Baseline variance test using a perfectly symmetric network where neither v27 nor v26 has structural advantage.

## Purpose

Unlike the realistic-economy-lite network (which favors v26 with 57% hashrate vs 41%), this balanced network provides **true ground truth** for measuring:

1. **Stochastic variance** - How much outcomes vary from random factors alone
2. **Decision boundary behavior** - Expected ~50/50 outcomes at center-point parameters
3. **Parameter sensitivity** - Clean baseline for comparison with parameter sweeps

## Network Structure

| Component | V27 | V26 |
|-----------|:---:|:---:|
| Mining Pools | 4 | 4 |
| Pool Hashrate | 47% | 47% |
| User Hashrate | 3% | 3% |
| **Total Hashrate** | **50%** | **50%** |
| Economic Nodes | 2 | 2 |
| User Nodes | 6 | 6 |

## Test Parameters

All parameters at center points:

| Parameter | Value |
|-----------|:-----:|
| economic_split | 0.50 |
| hashrate_split | 0.50 |
| pool_ideology_strength | 0.50 |
| pool_profitability_threshold | 0.16 |
| pool_max_loss_pct | 0.26 |
| pool_committed_split | 0.50 |
| pool_neutral_pct | 30.0 |
| econ_ideology_strength | 0.40 |
| econ_switching_threshold | 0.135 |
| econ_inertia | 0.175 |
| user_ideology_strength | 0.50 |
| user_switching_threshold | 0.125 |

### Random Seeds

Seeds 201-230 (30 independent samples)

## Expected Outcomes

With true symmetric structure:

1. **~50/50 outcome split** - approximately 15 v27 wins, 15 v26 wins
2. **High outcome variance** - random factors determine individual results
3. **Measurable stochastic variance** - σ(block_share) represents true randomness

## Comparison with Previous Baselines

| Baseline | Network | Structure | Expected Outcome |
|----------|---------|:---------:|:----------------:|
| baseline_sweep_lite | realistic-lite | 57% v26 | 100% v26 |
| baseline_decision_boundary | realistic-lite | 57% v26, adjusted params | ~50/50 |
| **balanced_baseline_sweep** | **balanced-baseline** | **50/50** | **~50/50** |

## Running the Sweep

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools/sweep

python 3_run_sweep.py \
    --input balanced_baseline_sweep/build_manifest.json \
    --duration 1800 \
    --retarget-interval 144
```

## Analyzing Results

```bash
python 4_analyze_results.py --input balanced_baseline_sweep/results
```

## Files

| File | Description |
|------|-------------|
| `balanced_scenarios.json` | 30 scenarios with center-point parameters |
| `build_manifest.json` | Build configuration |
| `configs/` | Pool and economic configurations |
| `networks/` | Generated symmetric networks |

---

*Created: March 2026*
