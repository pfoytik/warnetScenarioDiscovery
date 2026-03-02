# Decision Boundary Baseline: True 50/50 Variance Test

## Purpose

This sweep measures **stochastic variance at the decision boundary** — the point where outcomes are genuinely uncertain. By setting `economic_split=0.57` (instead of 0.50), we compensate for the realistic network's ~7% structural v26 bias to achieve approximately 50% actual v27 economic share.

**Key question:** How much do outcomes vary when neither side has a structural advantage?

## Comparison with Center-Point Baseline

| Baseline | economic_split | Actual v27 Econ Share | Expected Outcomes |
|----------|:--------------:|:---------------------:|-------------------|
| baseline_sweep_lite | 0.50 | ~43% | 100% v26 (structural bias) |
| **baseline_decision_boundary** | **0.57** | **~50%** | **~50/50 split** |

## Test Design

### Adjusted Parameter

```
economic_split = 0.57  (vs 0.50 in center-point baseline)
```

This adjustment compensates for the realistic-economy-lite network's structural v26 bias:
- Parameter 0.50 → Actual 0.43 (7% v26 advantage)
- Parameter 0.57 → Actual ~0.50 (neutral)

### All Other Parameters (Center Points)

| Parameter | Value |
|-----------|:-----:|
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
| transaction_velocity | 0.50 |

### Random Seeds

Seeds 101-130 (different from baseline_sweep_lite's 1-30 to ensure independent samples)

---

## Expected Outcomes

With true 50/50 economic balance:

1. **Mixed outcomes** — approximately 15 v27 wins, 15 v26 wins
2. **High variance** — random factors determine individual outcomes
3. **More reorg activity** — contested scenarios trigger economic cascades

### Metrics to Compare

| Metric | baseline_sweep_lite | Decision Boundary (expected) |
|--------|:-------------------:|:----------------------------:|
| v27 win rate | 0% | ~50% |
| v27_econ_share | 0.43 | ~0.50 |
| Outcome variance | 0 | High |
| Reorg count variance | 0 | High |

---

## Running the Sweep

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools/sweep

# Full run (~15 hours)
python 3_run_sweep.py \
    --input baseline_decision_boundary/build_manifest.json \
    --duration 1800 \
    --retarget-interval 144

# Quick test (5 scenarios)
python 3_run_sweep.py \
    --input baseline_decision_boundary/build_manifest.json \
    --duration 1800 \
    --retarget-interval 144 \
    --max-scenarios 5
```

## Analyzing Results

```bash
python 4_analyze_results.py --input baseline_decision_boundary/results
```

---

## Hypotheses

### H1: Balanced Economics → Variable Outcomes
With ~50% actual economic share for v27, outcomes should split roughly evenly.
- **Prediction:** 10-20 v27 wins out of 30 (33-67%)
- **Validation:** Check outcome distribution

### H2: Higher Variance Than Biased Baseline
Stochastic variance should be measurable when outcomes are contested.
- **Prediction:** σ(v27_block_share) > 0.05 (vs ~0.034 in biased baseline)
- **Prediction:** Outcome distribution ≠ 100% one-sided

### H3: Reorg Activity Increases
Contested scenarios should trigger more cascade attempts.
- **Prediction:** Average reorgs > 2 (vs exactly 2 in biased baseline)
- **Prediction:** Reorg count varies by scenario

---

## Files

| File | Description |
|------|-------------|
| `boundary_scenarios.json` | 30 scenarios with economic_split=0.57 |
| `build_manifest.json` | Full build configuration |
| `configs/` | Pool and economic configurations |
| `networks/` | Generated networks |

---

*Created: March 2026*
