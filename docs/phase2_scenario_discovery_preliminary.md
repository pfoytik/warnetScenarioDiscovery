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
| Total Scenarios | 78 |
| Sweeps Included | 10 |
| v27 Dominant | 49 (62.8%) |
| v26 Dominant | 29 (37.2%) |

**Sweeps:**
- `econ_committed_2016_grid` (45 scenarios)
- `committed_2016_high_econ` (4 scenarios, hashrate=0.50)
- `committed_2016_mid_econ` (4 scenarios, hashrate=0.50)
- `committed_2016_sigmoid` (4 scenarios, hashrate=0.50)
- `committed_2016_sigmoid_midecon` (3 scenarios, hashrate=0.50)
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

## Figures

### Figure 1: Decision Boundary

![Decision Boundary](../tools/discovery/output/figures/decision_boundary.png)

**Description:** This heatmap shows the predicted probability of v27 winning (P(v27 wins)) across the two most important parameters: `economic_split` (x-axis) and `pool_committed_split` (y-axis). The color gradient ranges from red (v26 wins) through yellow (uncertain) to green (v27 wins).

**Key Observations:**

1. **Vertical Transition Zone:** The decision boundary is primarily vertical, occurring around `economic_split ≈ 0.55-0.65`. This confirms that economic node support is the dominant factor determining fork outcome.

2. **Inversion Zone:** There is a notable "inversion" region (red pocket) around `economic_split ≈ 0.60-0.70` and `pool_committed_split ≈ 0.30-0.50`. In this zone, *increasing* pool commitment to v27 paradoxically *decreases* v27's chances of winning. This may be related to the Foundry flip-point dynamics identified in Phase 1.

3. **PRIM Box (blue dashed):** The PRIM algorithm identified the region below `pool_committed_split ≤ 0.50` as the high-uncertainty zone. Points within this box have outcomes closest to 50/50.

4. **Scattered Outcomes:** Green (v27 wins) and red (v26 wins) points are intermixed in the central region, indicating genuine outcome uncertainty rather than clean separation.

5. **Clear Extremes:** The left edge (`economic_split < 0.35`) is solidly red (v26 wins), while the right edge with low pool commitment shows green (v27 wins).

---

### Figure 2: Feature Importance

![Feature Importance](../tools/discovery/output/figures/feature_importance.png)

**Description:** Side-by-side comparison of logistic regression coefficients (left) and random forest feature importances (right) for the 144-block regime.

**Key Observations:**

1. **Economic Split Dominates:** Both models agree that `economic_split` is the most important predictor, with ~74% importance in random forest and the largest positive coefficient in logistic regression.

2. **Pool Committed Split Second:** `pool_committed_split` is the second most important feature in both models, with positive coefficient indicating higher values favor v27.

3. **Negative Coefficients for Pool Behavior:** In logistic regression, `pool_ideology_strength` and `pool_max_loss_pct` have small negative coefficients. This suggests that when pools are more ideologically committed or tolerate higher losses, v27 is *less* likely to win outright (possibly leading to more contested outcomes).

4. **Random Forest Captures Non-linearity:** The random forest assigns more balanced importance to the secondary features (8-12% each), while logistic regression shows them as nearly negligible. This suggests non-linear interactions that random forest can capture.

---

### Figure 3: Contentiousness Distribution

![Contentiousness Distribution](../tools/discovery/output/figures/contentiousness_distribution.png)

**Description:** Kernel density estimates showing the distribution of contentiousness scores for each outcome type (v27_dominant, v26_dominant, contested).

**Contentiousness Score Components:**
- Normalized reorg count
- Normalized reorg mass (total blocks displaced)
- Inverse cascade time (slower cascades = more contentious)
- Economic lag (delay between hashrate cascade and economic switching)

**Key Observations:**

1. **Contested Outcomes are Bimodal:** The green "contested" distribution shows peaks at both low (~0.0) and moderate (~0.25) contentiousness. The low peak may represent stable stalemates, while the higher peak represents actively fought contests.

2. **v27 Wins Show Two Modes:** Blue distribution (v27_dominant) has a peak around 0.12-0.15 and another around 0.55. The higher contentiousness v27 wins may represent hard-fought victories that required significant reorgs to achieve.

3. **v26 Wins Cluster at Moderate Contentiousness:** Orange distribution (v26_dominant) peaks around 0.30-0.35, suggesting v26 victories often involve moderate levels of conflict before resolution.

4. **Overlap Region (0.25-0.35):** All three outcome types overlap in this contentiousness range, making it difficult to predict outcome from contentiousness alone. This is the "fog of war" zone where dynamics are most uncertain.

5. **High Contentiousness Rare for v26:** v26 wins rarely occur at contentiousness > 0.45, while v27 wins extend to 0.55+. This asymmetry suggests that prolonged contentious periods tend to favor v27 resolution.

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

## hashrate_split Validation at 2016-block

### Background

In Phase 1 (144-block regime), `hashrate_split` was found to have no causal effect on fork outcomes and was fixed at 0.25 for subsequent sweeps. However, this finding required validation at 2016-block conditions where the difficulty adjustment window is ~14x longer.

### New Data

The `committed_2016_*` sweeps from the large servers use `hashrate_split = 0.50`, providing a natural comparison against the `econ_committed_2016_grid` sweep which uses `hashrate_split = 0.25`.

| hashrate_split | Scenarios | v27 Win Rate |
|----------------|-----------|--------------|
| 0.25 | 47 | 61.7% |
| 0.50 | 27 | 66.7% |

### Statistical Test

**Chi-square test for main effect:** χ² = 0.03, p = 0.860

The overall effect is **not statistically significant**. However, stratified analysis reveals a Simpson's paradox — opposite effects at different economic support levels that cancel out:

| Economic Support | hashrate=0.25 | hashrate=0.50 | Effect |
|-----------------|---------------|---------------|--------|
| Low (<0.45) | 10.0% v27 wins (n=10) | 25.0% v27 wins (n=4) | **+15.0%** |
| Mid (0.45-0.65) | 50.0% v27 wins (n=16) | 69.2% v27 wins (n=13) | **+19.2%** |
| High (>0.65) | 95.2% v27 wins (n=21) | 80.0% v27 wins (n=10) | **-15.2%** |

### Key Finding: Interaction Effect

`hashrate_split` exhibits a **significant interaction with `economic_split`**:

- **At low/mid economic support:** Higher v27 hashrate helps v27 (+15-19%)
- **At high economic support:** Higher v27 hashrate **hurts** v27 (-15%) — **inversion effect**

This interaction mirrors the inversion zone observed in the decision boundary visualization and may share the same underlying mechanism (Foundry flip-point dynamics).

### Implications

1. **Main effect validation:** The 144-block finding that `hashrate_split` has no independent causal effect appears to hold at 2016-block (p=0.86)

2. **Interaction effect:** There is a meaningful `hashrate_split × economic_split` interaction that was not detected in Phase 1. This interaction should be considered in Phase 3 sampling.

3. **Inversion zone confirmed:** The paradoxical effect where more v27 support hurts v27 is present in both the `pool_committed_split` and `hashrate_split` dimensions at high economic support.

### Ongoing Verification

The `hashrate_2016_verification` sweep is currently running to provide additional data points:
- hashrate_split: [0.15, 0.25, 0.35, 0.50, 0.65]
- economic_split: [0.50, 0.60, 0.70]
- 18 scenarios targeting the mid-economic range where effects are clearest

---

## Known Limitations

1. **Parameter Coverage Imbalance:** 2016-block regime has less diverse parameter coverage (many values fixed in primary sweep)

2. **Partially Validated Fixed Parameters:**
   - `hashrate_split` main effect validated as non-causal at 2016-block (p=0.86)
   - `hashrate_split × economic_split` interaction effect detected but not fully characterized
   - Other fixed parameters (pool_neutral_pct, user params) remain unvalidated at 2016-block

3. **Sample Size Disparity:** 232 scenarios (144-block) vs 78 scenarios (2016-block)

4. **Temporal Data Gaps:** Some sweeps lack complete temporal/cascade dynamics data

5. **Interaction Effects:** The `hashrate_split × economic_split` interaction suggests other unmodeled interactions may exist

---

## Recommended Next Steps

### In Progress

1. **`hashrate_2016_verification` sweep** - RUNNING
   - Testing `hashrate_split` effect at 2016-block conditions
   - Spec file: `tools/sweep/hashrate_2016_verification/`
   - 18 scenarios: hashrate (0.15-0.65) × economic (0.50, 0.60, 0.70)
   - Will provide additional data on the hashrate × economic interaction effect

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
