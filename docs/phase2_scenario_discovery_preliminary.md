# Phase 2: Scenario Discovery - Preliminary Findings

**Date:** 2026-03-22
**Status:** PRELIMINARY - Analysis ongoing

## Overview

This document summarizes preliminary findings from Phase 2 scenario discovery, which aims to identify parameter regions where Bitcoin soft fork outcomes are most uncertain (transition zones). The analysis uses Patient Rule Induction Method (PRIM) and machine learning classifiers to characterize decision boundaries.

## Methodology

### Tools Developed

**Location:** `tools/discovery/`

| Script | Purpose |
|--------|---------|
| `fit_boundary.py` | Main analysis script - fits logistic regression, random forest, and PRIM |
| `output/` | Generated YAML bounds, JSON comparisons, and figures |

### Analysis Pipeline

1. Load labeled scenarios from `sweep_results.db`
2. Filter to valid sweeps (exclude `balanced_baseline_sweep` which creates artificial 50/50 stalemates)
3. Fit statistical models to predict fork outcome
4. Run PRIM to find axis-aligned boxes with maximum uncertainty
5. Compute contentiousness scores from cascade dynamics

### Key Parameters Analyzed

The analysis focuses on 4 parameters identified as potentially causal in Phase 1:

| Parameter | Description | Range |
|-----------|-------------|-------|
| `economic_split` | Fraction of economic nodes initially on v27 | 0.0 - 1.0 |
| `pool_committed_split` | Fraction of committed hashrate on v27 | 0.0 - 1.0 |
| `pool_ideology_strength` | How strongly pools weight ideology vs profit | 0.0 - 1.0 |
| `pool_max_loss_pct` | Maximum loss pools tolerate before switching | 0.0 - 1.0 |

### Fixed Parameters

The following parameters were fixed at median values based on Phase 1 non-causality findings:

| Parameter | Fixed Value | Validation Status |
|-----------|-------------|-------------------|
| `hashrate_split` | 0.25 | **UNVALIDATED at 2016-block** |
| `pool_neutral_pct` | 30.0 | UNVALIDATED at 2016-block |
| `econ_inertia` | 0.17 | UNVALIDATED at 2016-block |
| `econ_switching_threshold` | 0.14 | UNVALIDATED at 2016-block |
| `user_ideology_strength` | 0.49 | UNVALIDATED at 2016-block |
| `user_switching_threshold` | 0.12 | UNVALIDATED at 2016-block |
| `user_nodes_per_partition` | 6 | UNVALIDATED at 2016-block |
| `solo_miner_hashrate` | 0.085 | UNVALIDATED at 2016-block |
| `transaction_velocity` | 0.5 | UNVALIDATED at 2016-block |
| `economic_nodes_per_partition` | 2 | UNVALIDATED at 2016-block |

**Important:** These non-causality findings are from 144-block retarget conditions only. A verification sweep is recommended at 2016-block conditions.

---

## Data Summary

### 144-block Regime

| Metric | Value |
|--------|-------|
| Total Scenarios | 232 |
| Sweeps Included | 7 |
| v27 Dominant | 102 (44.0%) |
| v26 Dominant | 130 (56.0%) |

**Sweeps:**
- `targeted_sweep1_committed_threshold`
- `targeted_sweep2_hashrate_economic`
- `targeted_sweep3_neutral_pct`
- `targeted_sweep3b_econ_friction_verify`
- `targeted_sweep4_user_behavior`
- `targeted_sweep6_pool_ideology_full`
- `realistic_sweep3_rapid`

### 2016-block Regime

| Metric | Value |
|--------|-------|
| Total Scenarios | 63 |
| Sweeps Included | 6 |
| v27 Dominant | 34 (54.0%) |
| v26 Dominant | 29 (46.0%) |

**Sweeps:**
- `econ_committed_2016_grid` (45 scenarios - newly imported)
- `targeted_sweep10_econ_threshold_2016`
- `targeted_sweep10b_econ_threshold_2016`
- `targeted_sweep8_lite_2016_retarget`
- `targeted_sweep9_long_duration_2016`
- `targeted_sweep11_lite_chaos_test`

---

## Key Findings

### 1. Economic Split Dominates Outcome Prediction

Random Forest feature importance shows `economic_split` is the strongest predictor in both regimes:

| Parameter | 144-block | 2016-block |
|-----------|-----------|------------|
| `economic_split` | **74.2%** | **71.0%** |
| `pool_committed_split` | 11.7% | 29.0% |
| `pool_ideology_strength` | 6.1% | 0.0%* |
| `pool_max_loss_pct` | 8.1% | 0.0%* |

*Zero importance in 2016-block due to fixed values in `econ_committed_2016_grid`

### 2. Pool Commitment More Important at 2016-block

`pool_committed_split` importance nearly **triples** in the 2016-block regime (29% vs 12%). This suggests mining pool commitment becomes more critical when difficulty adjustments are slower.

### 3. v27 Win Rate Higher at 2016-block

| Regime | v27 Win Rate |
|--------|--------------|
| 144-block | 44.0% |
| 2016-block | **54.0%** |

The 10% difference suggests longer retarget periods may favor v27, though this needs validation with more balanced parameter coverage.

### 4. PRIM Uncertainty Bounds

#### 144-block Regime (High Uncertainty Zone)

```yaml
economic_split:        [0.00, 0.82]
pool_committed_split:  [0.00, 0.50]
pool_ideology_strength: [0.00, 0.80]
pool_max_loss_pct:     [0.00, 0.26]
```

- Support: 87.9% (204 samples)
- Mean v27 win rate: 44.6%
- Uncertainty score: 0.892 (1.0 = perfect 50/50)

#### 2016-block Regime (High Uncertainty Zone)

```yaml
economic_split:        [0.35, 0.82]
pool_committed_split:  [0.20, 0.75]
pool_ideology_strength: [0.51, 0.51]  # Fixed in sweep
pool_max_loss_pct:     [0.26, 0.26]  # Fixed in sweep
```

- Support: 100% (63 samples)
- Mean v27 win rate: 54.0%
- Uncertainty score: 0.921

**Note:** The degenerate bounds for `pool_ideology_strength` and `pool_max_loss_pct` in 2016-block reflect that these were fixed in the primary sweep (`econ_committed_2016_grid`), not genuine constraint discovery.

### 5. Model Accuracy

| Model | 144-block | 2016-block |
|-------|-----------|------------|
| Random Forest CV | 83.8% | 74.1% |
| Random Forest OOB | 81.5% | 79.4% |

The 144-block regime has better model accuracy, likely due to larger sample size and more diverse parameter coverage.

### 6. Contentiousness Analysis

Mean contentiousness (composite of reorgs, reorg mass, cascade time, economic lag):

| Regime | Mean Contentiousness |
|--------|---------------------|
| 144-block | 0.275 |
| 2016-block | 0.279 |

Contentiousness is similar across regimes, suggesting the dynamics of contested forks don't differ dramatically between retarget periods.

---

## Logistic Regression Insights

Top interaction terms (144-block):

| Feature | Coefficient |
|---------|-------------|
| `pool_ideology_strength * pool_max_loss_pct` | -1.56 |
| `economic_split` | +0.75 |
| `pool_committed_split` | +0.62 |

The negative interaction between `pool_ideology_strength` and `pool_max_loss_pct` suggests these parameters have opposing effects that partially cancel out.

---

## Known Limitations

1. **Parameter Coverage Imbalance:** 2016-block regime has less diverse parameter coverage (many values fixed in primary sweep)

2. **Unvalidated Fixed Parameters:** Non-causality findings for fixed parameters have only been validated at 144-block conditions

3. **Sample Size Disparity:** 232 scenarios (144-block) vs 63 scenarios (2016-block)

4. **Temporal Data Gaps:** Some sweeps lack complete temporal/cascade dynamics data

---

## Recommended Next Steps

### Immediate (Tomorrow)

1. **Run `hashrate_2016_verification` sweep** - Test if `hashrate_split` non-causality holds at 2016-block
   - Spec file: `tools/sweep/specs/hashrate_2016_verification.yaml`
   - 18 scenarios: hashrate (0.15-0.65) x economic (0.50, 0.60, 0.70)

### Short-term

2. **Import remaining server sweep results** when complete
3. **Run 4-parameter grid at 2016-block** to get unbiased PRIM bounds
4. **Validate other fixed parameters** at 2016-block conditions

### Phase 3 Preparation

5. **Generate LHS samples** within PRIM bounds for focused uncertainty exploration
6. **Define success metrics** for Phase 3 runs

---

## Output Files

| File | Description |
|------|-------------|
| `output/prim_bounds.yaml` | PRIM box for v27 win probability |
| `output/uncertainty_bounds.yaml` | PRIM box for maximum outcome uncertainty |
| `output/contentiousness_bounds.yaml` | PRIM box for high contentiousness |
| `output/model_comparison.json` | Full model comparison data |
| `output/regime_comparison/regime_comparison.json` | 144 vs 2016 block comparison |
| `output/figures/decision_boundary.png` | 2D decision boundary visualization |
| `output/figures/feature_importance.png` | Random forest feature importance |
| `output/figures/contentiousness_distribution.png` | Contentiousness by outcome |

---

## Appendix: Command Reference

```bash
# Run standard analysis (144-block)
python fit_boundary.py --db ../sweep/sweep_results.db

# Run with uncertainty optimization
python fit_boundary.py --db ../sweep/sweep_results.db --mode uncertainty

# Compare regimes
python fit_boundary.py --db ../sweep/sweep_results.db --compare-regimes

# Analyze specific regime
python fit_boundary.py --db ../sweep/sweep_results.db --regime 2016
```

---

*Last updated: 2026-03-22*
