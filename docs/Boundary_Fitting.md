# Boundary Fitting Report
**Bitcoin Activation War — Phase 2 Analysis**
**Date:** 2026-04-03
**Script:** `tools/discovery/fit_boundary.py`
**Output directory:** `tools/discovery/output/`

---

## 1. Executive Summary

Phase 2 boundary fitting applied Random Forest classification, Logistic Regression with interaction terms, and Patient Rule Induction Method (PRIM) to all valid sweep scenarios, separated by retarget regime (144-block vs. 2016-block).

**Key findings:**

1. **Causal variable rank reversal confirmed across regimes.** `economic_split` dominates at 144-block (RF importance 77.2%), while `pool_committed_split` dominates at 2016-block (RF importance 52.8%). This reversal is structurally significant and not a sampling artifact.

2. **2016-block is the structurally rich regime.** The 2016-block Logistic Regression achieves 77.5% cross-validated accuracy (vs. 59.8% at 144-block), and the dominant interaction term — `economic_split × pool_committed_split` (+1.231) — reveals a synergistic relationship between economic pressure and mining pool commitment.

3. **PRIM identifies a well-defined 2016-block uncertainty zone.** The transition region where outcomes are 50/50 occupies 51% of the sample space, bounded on all four active parameters. This zone is the Phase 3 LHS target.

4. **144-block PRIM is degenerate due to network quantization.** On the 25-node lite network, all `economic_split` values in [0.30, 0.80] map to the same 1 economic node (56.7% custody), making the parameter appear non-causal. PRIM cannot find meaningful boundaries and returns a near-entire-space box.

5. **High-contentiousness zone (2016-block) is a proper subset of the v27-win zone.** The region with maximum on-chain disruption (mean contentiousness 0.360) is restricted to scenarios where committed mining pools are moderately strong but not so strong that v27 wins cleanly.

---

## 2. Data and Methods

### 2.1 Scenario Datasets by Regime

| Regime | Sweeps included | n scenarios | v27 win rate | Mean contentiousness |
|--------|----------------|-------------|--------------|---------------------|
| **144-block (clean)** | Full-network sweeps only (excl. lhs_144_6param) | 268 | 48.9% | 0.166 |
| **144-block (all)** | Full-network + lhs_144_6param | 398 | 52.0% | 0.132 |
| **2016-block** | All valid 2016-block sweeps | 298 | 67.1% | 0.271 |

The "clean" 144-block dataset (n=268) is used for all feature importance and boundary results at 144-block, because `lhs_144_6param` introduces quantization artifacts (see §6.2). The full n=398 dataset is shown for completeness in the regime comparison.

### 2.2 Active Parameters

These four parameters were varied across sweeps and are the inputs to all models:

| Parameter | Symbol | Range sampled |
|-----------|--------|---------------|
| `economic_split` | E | [0.0, 0.95] |
| `pool_committed_split` | C | [0.0, 0.75] |
| `pool_ideology_strength` | I | [0.0, 0.80] |
| `pool_max_loss_pct` | M | [0.0, 0.45] |

### 2.3 Fixed Parameters

The following parameters were held constant across all analyzed sweeps (validated at 144-block only unless otherwise noted):

| Parameter | Value | Validation status |
|-----------|-------|------------------|
| `hashrate_split` | 0.25 | **UNVALIDATED at 2016-block** |
| `pool_neutral_pct` | 30.0% | **UNVALIDATED at 2016-block** |
| `econ_inertia` | 0.17 | Validated (lhs_2016_6param, n=129) |
| `econ_switching_threshold` | 0.14 | Validated (lhs_2016_6param, n=129) |
| `user_ideology_strength` | 0.49 | **UNVALIDATED at 2016-block** |
| `user_switching_threshold` | 0.12 | **UNVALIDATED at 2016-block** |
| `pool_profitability_threshold` | (default) | Confirmed non-causal at BOTH regimes |
| `solo_miner_hashrate` | 0.085 | Confirmed non-causal at BOTH regimes |
| `transaction_velocity` | 0.5 | Not varied |
| `user_nodes_per_partition` | 6 | Not varied |
| `economic_nodes_per_partition` | 2 | Not varied |

### 2.4 Outcome Variables

- **Primary:** `v27_win` — binary flag (1 = v27/UASF wins, 0 = v26/status-quo chain wins)
- **Contentiousness score:** Composite metric: `0.3×reorgs + 0.3×reorg_mass + 0.2×norm_inv(cascade_time) + 0.2×|econ_lag|`
  - Range: 0.0 (clean activation) to ~0.5+ (severe fork)
  - 144-block mean: 0.132 (all) / 0.166 (clean)
  - 2016-block mean: 0.271

---

## 3. Regime Comparison

### 3.1 Random Forest Feature Importance

| Parameter | 144-block (clean, n=268) | 144-block (all, n=398) | 2016-block (n=298) |
|-----------|--------------------------|------------------------|---------------------|
| `economic_split` | **77.2%** | **51.1%** | 20.2% |
| `pool_committed_split` | 11.3% | 18.3% | **52.8%** |
| `pool_ideology_strength` | 6.0% | 16.7% | 9.9% |
| `pool_max_loss_pct` | 5.5% | 13.8% | 17.1% |
| **RF OOB accuracy** | 80.0% | 78.1% | **83.2%** |
| **RF CV accuracy** | 85.5% | — | — |

**Interpretation:** The causal variable that most determines fork outcome depends on which retarget period is operative. At 144-block, how economically aligned users are with the new chain (`economic_split`) governs the result rapidly. At 2016-block, the more durable factor is mining pool commitment (`pool_committed_split`), because pools must sustain their choice through an entire 2016-block epoch before any difficulty adjustment.

The 2016-block RF OOB of 83.2% indicates the model has a reliable signal. The 144-block clean OOB of 80.0% is also credible, but the LR fit (59.8% CV) is poor, suggesting the 144-block landscape is noisier and/or the interaction structure is less stable on the lite network.

### 3.2 Contentiousness by Regime

| Metric | 144-block | 2016-block |
|--------|-----------|------------|
| Mean contentiousness | 0.132 | 0.271 |
| Ratio | 1.0× | **2.1× higher** |

The 2016-block regime produces significantly more on-chain disruption on average, consistent with longer fork persistence before difficulty-based resolution.

---

## 4. Logistic Regression with Interaction Terms

### 4.1 2016-block Full Coefficient Table

Fitted on n=298 scenarios with all four active parameters plus 6 pairwise interaction terms (10 terms total).

| Term | Coefficient (β) | Direction |
|------|----------------|-----------|
| Intercept | +1.152 | v27 baseline advantage |
| E × C (`economic_split × pool_committed_split`) | **+1.231** | Synergistic — both required |
| E × M (`economic_split × pool_max_loss_pct`) | −0.618 | Antagonistic |
| E (`economic_split`) | +0.568 | v27 favorable |
| C × I (`pool_committed_split × pool_ideology_strength`) | +0.504 | Synergistic |
| I × M (`pool_ideology_strength × pool_max_loss_pct`) | −0.374 | Antagonistic |
| E × I (`economic_split × pool_ideology_strength`) | −0.289 | Antagonistic |
| C × M (`pool_committed_split × pool_max_loss_pct`) | −0.278 | Antagonistic |
| C (`pool_committed_split`) | +0.177 | v27 favorable (weak) |
| M (`pool_max_loss_pct`) | +0.085 | v27 favorable (very weak) |
| I (`pool_ideology_strength`) | −0.083 | v26 favorable (very weak) |

**CV accuracy:** 77.5% ± 2.9%

**Full fitted equation:**
```
log-odds(v27_win) = 1.152
  + 1.231·E·C
  − 0.618·E·M
  + 0.568·E
  + 0.504·C·I
  − 0.374·I·M
  − 0.289·E·I
  − 0.278·C·M
  + 0.177·C
  + 0.085·M
  − 0.083·I
```

### 4.2 Key Term Interpretations

**E × C (+1.231) — Dominant synergistic term**
When both economic pressure (user alignment with new chain) and mining pool commitment are simultaneously high, v27 wins with dramatically higher probability. Neither variable alone is sufficient — this is the "conviction plus economics" interaction. It explains why the 2016-block regime has a strong RF signal on committed_split: economic split is a necessary co-variable.

**E × M (−0.618) — Economic pressure dampened by loss tolerance**
If mining pools are both economically pressured AND willing to absorb large losses, the economic pressure signal weakens. Pools that accept losses can sustain chain split longer even under economic headwinds.

**C × I (+0.504) — Ideology amplifies commitment**
Strongly ideological pools that are also committed sustain position longer. This confirms that ideology operates as a commitment multiplier rather than an independent force.

**I × M (−0.374) — Ideology and loss tolerance antagonistic**
High ideology combined with high loss tolerance is destabilizing — these pools are hardest to move economically. The negative coefficient reflects that this combination resists the v27 outcome even when other factors favor it.

**Main effect structure:** E and C are the two meaningful main effects (+0.568, +0.177). I and M are near-zero main effects (−0.083, +0.085), operating primarily through interactions.

### 4.3 144-block Clean LR Results (For Comparison)

| Term | Coefficient (β) |
|------|----------------|
| `pool_ideology_strength` (main) | −1.104 |
| `pool_max_loss_pct` (main) | −1.101 |
| E × M | +1.085 |
| E × I | +0.930 |
| E × C | −0.582 |

**CV accuracy:** 59.8% (poor fit — 10% above chance but not structurally reliable)

The 144-block LR has inverted signs relative to 2016-block for E×C (positive at 2016, negative at 144), and large main effects for I and M that are near-zero at 2016-block. This is consistent with the 144-block regime being noise-dominated on the lite network. The RF importances (which are less sensitive to multicollinearity) are more trustworthy for 144-block conclusions.

---

## 5. PRIM Boundary Analysis

### 5.1 PRIM Methodology

PRIM (Patient Rule Induction Method) iteratively "peels" the parameter space, removing the 10% of observations in the current box with the lowest target value, until the mean target in the box exceeds a threshold. The result is an axis-aligned hyperrectangle (a "box") in parameter space, described by min/max bounds on each parameter.

Three PRIM runs were executed per regime:
1. **v27-win maximization** — finds the region where v27 wins most often
2. **Uncertainty (transition zone)** — finds the region closest to 50/50 outcome (maximum ambiguity)
3. **Contentiousness maximization** — finds the region with highest on-chain disruption score

### 5.2 2016-block: v27-Win Maximization Box

The region where v27 is most likely to win.

| Parameter | Min | Max | Width |
|-----------|-----|-----|-------|
| `economic_split` | 0.338 | 0.850 | 0.512 |
| `pool_committed_split` | 0.253 | 0.677 | 0.424 |
| `pool_ideology_strength` | 0.301 | 0.797 | 0.496 |
| `pool_max_loss_pct` | 0.101 | 0.310 | 0.209 |

| Statistic | Value |
|-----------|-------|
| Support (fraction of data in box) | 58.7% |
| Mean v27 win rate inside box | **85.7%** |
| n scenarios in box | 175 |
| n PRIM peeling steps | 18 |

**Interpretation:** v27 wins 85.7% of the time when economic pressure is moderate-to-high (E ≥ 0.338), pools are at least moderately committed (C ≥ 0.253), and loss tolerance is bounded (M ≤ 0.310). The `pool_max_loss_pct` upper bound is the tightest constraint — very loss-tolerant pools can sustain chain splits that defeat v27 even when other conditions favor it.

### 5.3 2016-block: Uncertainty / Transition Zone (Phase 3 LHS Target)

The region where outcomes are maximally uncertain — the 50/50 "knife edge" between fork outcomes.

| Parameter | Min | Max | Width |
|-----------|-----|-----|-------|
| `economic_split` | 0.280 | 0.779 | 0.499 |
| `pool_committed_split` | 0.152 | 0.526 | 0.374 |
| `pool_ideology_strength` | 0.435 | 0.797 | 0.362 |
| `pool_max_loss_pct` | 0.163 | 0.400 | 0.237 |

| Statistic | Value |
|-----------|-------|
| Support (fraction of data in box) | 51.0% |
| Mean v27 win rate inside box | **50.0%** (exactly 50/50) |
| Uncertainty score | 0.992 (near-perfect) |
| n scenarios in box | 152 |

**This box is the Phase 3 LHS target.** Running additional scenarios uniformly sampled within these bounds will resolve the uncertainty about which parameter combinations cause fork outcomes to go either way.

**Saved at:** `tools/discovery/output/2016/uncertainty_bounds.yaml`

**Phase 3 LHS command:**
```bash
python scenarios/lhs_sampler.py \
    --bounds tools/discovery/output/2016/uncertainty_bounds.yaml \
    --n 300 \
    --regime 2016 \
    --output scenarios/lhs_2016_phase3/
```

### 5.4 2016-block: Contentiousness Maximization Box

The region with the highest on-chain disruption (reorgs, reorg mass, cascade time, economic lag).

| Parameter | Min | Max | Width |
|-----------|-----|-----|-------|
| `economic_split` | 0.338 | 0.780 | 0.442 |
| `pool_committed_split` | 0.253 | 0.568 | 0.315 |
| `pool_ideology_strength` | 0.301 | 0.750 | 0.449 |
| `pool_max_loss_pct` | 0.101 | 0.312 | 0.211 |

| Statistic | Value |
|-----------|-------|
| Support (fraction of data in box) | 40.3% |
| Mean contentiousness in box | **0.360** (vs. overall 0.271) |
| Mean v27 win rate inside box | 36.0% |
| n scenarios in box | 120 |

**Interpretation:** The high-contentiousness zone occupies the lower-right portion of the v27-win zone (`pool_committed_split` capped at 0.568 vs. 0.677 for v27-win). This reveals that the most disruptive scenarios are those where pools are committed enough to cause a real fork, but NOT committed enough to win decisively — the activation war is contested rather than decisive. The 36% v27 win rate (vs. 67.1% overall) confirms these are primarily v26-dominant but contentious scenarios.

### 5.5 Intersection of Outcome-Uncertainty and Contentiousness Zones

The overlap between the uncertainty zone (§5.3) and the contentiousness zone (§5.4) identifies scenarios that are simultaneously hard to predict AND disruptive.

| Parameter | Min | Max |
|-----------|-----|-----|
| `economic_split` | 0.338 | 0.779 |
| `pool_committed_split` | 0.253 | 0.526 |
| `pool_ideology_strength` | 0.435 | 0.750 |
| `pool_max_loss_pct` | 0.163 | 0.310 |

**Interpretation:** The intersection is dominated by the tighter contentiousness bounds on `pool_committed_split` [0.253, 0.526] and `pool_ideology_strength` [0.435, 0.750], with `pool_max_loss_pct` bounded by both ([0.163, 0.310]). This is the parameter region of greatest research interest: scenarios here are unpredictable in outcome AND cause significant on-chain disruption if they occur.

---

## 6. 144-block Boundary Analysis: Limitations

### 6.1 PRIM Degeneration

The 144-block PRIM analysis (both with and without `lhs_144_6param`) returns near-entire-space boxes after very few peeling steps:

| PRIM run | Final support | n scenarios | Mean target | Steps |
|----------|--------------|-------------|-------------|-------|
| v27-win (clean) | 92.5% | 248 | 49.6% | 3 |
| Uncertainty (clean) | 92.5% | 248 | 49.6% | 3 |
| Contentiousness (clean) | 92.5% | 248 | 16.6% | 3 |

After only 3 peeling steps (removing ~7.5% of data), PRIM cannot find any region with meaningfully higher outcome concentration. The parameter space appears uniformly distributed in outcomes at 144-block. This is NOT necessarily a true finding — it reflects the limits of the lite network structure for isolating causal boundaries.

### 6.2 Quantization Artifact in lhs_144_6param

The `lhs_144_6param` sweep (n=130) sampled `economic_split` uniformly across [0.0, 0.95] on the 25-node lite network. However, the lite network has only 1 economic node per partition, meaning:

- `economic_split` ∈ [0.30, 0.80] → all map to 1 economic node → effective custody = 56.7% (constant)
- Only `economic_split` < 0.30 or > 0.80 produces a different economic node configuration

This means 87% of the lhs_144_6param economic_split samples are informationally identical, injecting near-zero separation signal into the 144-block combined dataset. The RF correctly identifies `economic_split` as important when using only full-network sweeps (77.2%), but the combined dataset shows it at only 51.1%.

**Conclusion for 144-block:** Use RF importance results from the clean (full-network only) run. Do NOT use 144-block PRIM boxes for target specification. Use 2016-block uncertainty_bounds.yaml for Phase 3 targeting.

---

## 7. Contentiousness Analysis

### 7.1 Score Definition

```
contentiousness = 0.3 × reorgs_normalized
              + 0.3 × reorg_mass_normalized
              + 0.2 × (1 - cascade_time_normalized)
              + 0.2 × |economic_lag_normalized|
```

Range: 0.0 (clean, instant activation) → ~0.5 (severe, prolonged fork)

### 7.2 Regime Comparison

| Metric | 144-block | 2016-block | Ratio |
|--------|-----------|------------|-------|
| Mean contentiousness (all scenarios) | 0.132 | 0.271 | 2.1× |
| Mean contentiousness (v27-win scenarios) | ~0.09 | ~0.18 | ~2× |
| Mean contentiousness (high-chaos PRIM box) | 0.166 (unbounded) | **0.360** | — |

The 2016-block regime produces 2× more on-chain disruption on average. This is structurally expected: with a 2016-block retarget interval, a committed minority chain can persist for ~14 days before difficulty adjusts, allowing extended periods of competitive mining with reorgs, double-spends, and economic uncertainty.

### 7.3 Contentiousness vs. Outcome Relationship (2016-block)

The high-contentiousness zone (support=40.3%, mean=0.360) has a **36% v27 win rate** — substantially below the 67.1% overall rate. This confirms that:

- **Contentious scenarios are NOT those where v27 wins easily.** Clean v27 wins have low contentiousness (committed pool minority quickly capitulates).
- **Maximum disruption occurs in the middle zone** where committed mining pools are strong enough to challenge v27 but not strong enough to win.
- **The contentiousness zone is a proper subset of the v27-win zone** — pool commitment bounds are tighter (C max 0.568 vs. 0.677), capturing the "contested" rather than "decisive" region.

---

## 8. Fixed Parameter Validation Status

| Parameter | 144-block | 2016-block | Note |
|-----------|-----------|------------|------|
| `pool_profitability_threshold` | ✓ Non-causal (lhs_144_6param) | ✓ Non-causal (lhs_2016_6param) | Confirmed at both regimes |
| `solo_miner_hashrate` | ✓ Non-causal (lhs_144_6param) | ✓ Non-causal (lhs_2016_6param) | Confirmed at both regimes |
| `econ_inertia` | ✓ Fixed | ✓ Validated (lhs_2016_6param) | |
| `econ_switching_threshold` | ✓ Fixed | ✓ Validated (lhs_2016_6param) | |
| `hashrate_split` | ✓ Non-causal (targeted sweeps) | **⚠ UNVALIDATED** | Needs 2016-block hashrate sweep |
| `pool_neutral_pct` | ✓ Fixed | **⚠ UNVALIDATED** | Assumed non-causal at 2016-block |
| `user_ideology_strength` | ✓ Fixed | **⚠ UNVALIDATED** | |
| `user_switching_threshold` | ✓ Fixed | **⚠ UNVALIDATED** | |

**Recommended validation sweeps:**
1. `hashrate_split × economic_split` grid at 2016-block (most important — hashrate allocation could interact with committed mining pool dynamics)
2. `pool_neutral_pct` sensitivity at 2016-block (neutral pools are a third category; current fix at 30% may be influential)

---

## 9. Phase 3 LHS Target Specification

**Objective:** Fill the outcome-uncertainty zone at 2016-block with high-quality unbiased samples.

**Target bounds** (from `tools/discovery/output/2016/uncertainty_bounds.yaml`):

```yaml
parameters:
  economic_split:
    min: 0.280
    max: 0.779
  pool_committed_split:
    min: 0.152
    max: 0.526
  pool_ideology_strength:
    min: 0.435
    max: 0.797
  pool_max_loss_pct:
    min: 0.163
    max: 0.400
fixed_parameters:
  hashrate_split: 0.25
  pool_neutral_pct: 30.0
  econ_inertia: 0.17
  econ_switching_threshold: 0.14
  user_ideology_strength: 0.49
  user_switching_threshold: 0.12
  user_nodes_per_partition: 6
  solo_miner_hashrate: 0.085
  transaction_velocity: 0.5
  economic_nodes_per_partition: 2
```

**Rationale for target selection:**
- Current 2016-block data has 67.1% v27 win rate — the dataset is skewed toward v27 wins
- The uncertainty zone (51.0% support, exactly 50/50) indicates the model has identified WHERE the decision boundary lies but does not have fine-grained coverage of the transition
- A 300-scenario LHS within these bounds will reveal the precise shape of the boundary and which combinations flip outcomes
- `pool_ideology_strength` is constrained to [0.435, 0.797] in the uncertainty zone, suggesting ideology acts as a "floor" for genuine contestation — low-ideology scenarios resolve quickly

---

## 10. Output File Index

All outputs are written to `tools/discovery/output/`:

```
output/
├── regime_comparison/
│   └── regime_comparison.json       # Side-by-side 144 vs 2016 results
├── 144/
│   ├── model_comparison.json        # RF + LR + PRIM (144-block, n=398, all sweeps)
│   ├── prim_bounds.yaml             # PRIM v27-win box
│   ├── uncertainty_bounds.yaml      # PRIM transition zone
│   └── contentiousness_bounds.yaml  # PRIM high-chaos zone
├── 144_clean/
│   ├── model_comparison.json        # RF + LR + PRIM (144-block, n=268, full-net only)
│   ├── prim_bounds.yaml
│   ├── uncertainty_bounds.yaml
│   └── contentiousness_bounds.yaml
└── 2016/
    ├── model_comparison.json        # RF + LR + PRIM (2016-block, n=298)
    ├── coefficients.json            # LR full coefficient table + CV
    ├── prim_bounds.yaml             # PRIM v27-win box
    ├── uncertainty_bounds.yaml      # PRIM transition zone (Phase 3 target)
    └── contentiousness_bounds.yaml  # PRIM high-chaos zone
```

**Commands used to generate outputs:**
```bash
cd tools/discovery

# Regime comparison (both regimes on same data)
python fit_boundary.py --compare-regimes

# 2016-block standalone
python fit_boundary.py --regime 2016

# 144-block (all sweeps including lhs_144_6param)
python fit_boundary.py --regime 144

# 144-block clean (excluding lhs_144_6param quantization artifact)
python fit_boundary.py --regime 144 --exclude lhs_144_6param --output-dir output/144_clean
```

---

*Report generated from Phase 2 boundary fitting analysis. All numeric values taken directly from JSON/YAML output files. See `tools/discovery/fit_boundary.py` for complete analysis pipeline.*
