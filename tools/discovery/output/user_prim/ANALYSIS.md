# User-PRIM Analysis: User Node Governance Influence in Fork Dynamics

**Date:** 2026-04-08
**Script:** `tools/discovery/user_prim.py`
**Dataset:** 598 scenarios across 15 sweeps, 2016-block retarget regime
**Method:** Z-PRIM variant adapted from "Discovering Surprising Critical Scenarios
in Critical Infrastructure Simulations Using Scenario Potential"

---

## Motivation

Standard PRIM on this dataset maximizes contentiousness density and will always
find scenarios driven by high-capacity actors — Foundry (~30% hashrate), major
exchanges (~112 consensus weight units). User nodes have a collective consensus
weight of 0.169 units across 28 nodes — a **2,196:1 disadvantage** relative to
the economic actor pool. Any density-maximizing method is structurally blind to
user-node-driven scenarios.

User-PRIM asks a different question: **are there specific parameter combinations
where user node weight is near-pivotal in a contentious outcome?** The goal is not
to prove user nodes are causal — targeted_sweep4 already established non-causality
— but to find those edge cases from a different methodological angle, and to
characterize whether non-causality holds even when we deliberately search for
counterexamples.

---

## Network Weight Structure

From `networks/realistic-economy-v2/network.yaml`:

| Actor class       | Nodes | Consensus weight | Fraction |
|-------------------|-------|-----------------|----------|
| Major exchanges   | 4     | 261.2           | 70.4%    |
| Exchanges         | 6     | 63.8            | 17.2%    |
| Institutional     | 5     | 41.3            | 11.1%    |
| Payment/Merchant  | 9     | 3.7             | 1.0%     |
| **User nodes**    | **28**| **0.169**       | **0.046%** |
| **Total**         | **52**| **370.90**      | 100%     |

Consensus weight formula: `(0.7 × custody_btc + 0.3 × daily_volume_btc) / 10000`

The top single actor (node-0034, major exchange, 1.5M BTC custody) has weight 112.5 —
**666× the entire user node collective.**

### Economic Assignment Thresholds

The `economic_split` parameter assigns economic nodes to v27/v26 by sorting on
custody_btc descending and assigning the top `round(24 × economic_split)` to v27.
Node assignment changes at each multiple of 1/24 ≈ 0.0417. Within the PRIM
uncertainty zone [0.28, 0.78], the relevant thresholds are:

```
0.292, 0.333, 0.375, 0.417, 0.458, 0.500, 0.542, 0.583, 0.625, 0.667, 0.708, 0.750
```

SP_user peaks at these values: when `economic_split` is exactly at a threshold,
the economic margin is zero and user weight is (proportionally) at its maximum
influence. At any other value, the margin far exceeds user weight.

---

## Method: Scenario Potential and Z_user

### SP_user (Scenario Potential for user nodes)

For each scenario with parameter `economic_split`:

```
economic_margin_weight = min_distance_to_threshold × W_total
SP_user = W_users / (economic_margin_weight + W_users)
```

SP_user approaches 1 when `economic_split` is exactly at a threshold (user weight
could in principle bridge the marginal gap). It approaches 0 when far from all
thresholds. With W_users=0.169 and W_total=370.9, raw values are small:

| SP_user percentile | Value    |
|--------------------|----------|
| p25                | 0.028    |
| p50                | 0.041    |
| p75                | 0.081    |
| p95                | 0.463    |
| max                | 1.000    |

The distribution is heavily right-skewed — most scenarios are far from all
thresholds and have SP_user ≈ 0.03. Scenarios at the p95+ level are those
with `economic_split` within ~0.01 of a threshold boundary.

**Min-max normalization is essential** before combining with contentiousness.
Without it, the raw SP_user variance (~0.03) is so small relative to
contentiousness variance (~0.3) that the Z_user formula degrades to pure
contentiousness PRIM.

### Z_user (Combined Score)

```
Z_user = λ1 × normalize(contentiousness) + λ2 × normalize(SP_user)
```

Default weights: λ1=0.5, λ2=1.0 (SP_user weighted 2× — we want to find the
near-threshold scenarios, not just the most contentious ones).

This **rewards** high SP_user, opposite of the original Z-PRIM formulation which
penalizes high-capacity scenarios to find surprising low-capacity ones. Here,
high SP_user IS the target condition.

Z_user correlations in the dataset:

| Parameter             | r with Z_user |
|-----------------------|---------------|
| sp_user               | +0.796        |
| contentiousness       | +0.560        |
| pool_committed_split  | +0.223        |
| pool_ideology_strength| −0.107        |
| pool_max_loss_pct     | −0.124        |
| economic_split        | +0.017        |

The dominant signal is SP_user itself (r=0.796) — meaning Z_user is primarily
tracking proximity to economic thresholds, with contentiousness as secondary.

---

## User-PRIM Results

### Peeling trajectory

The algorithm ran 45 peeling steps (α=0.05, min_support=30):

- Started: 598 scenarios, mean Z_user = 0.299
- Final box: **58 scenarios** (9.7%), mean Z_user = 0.563

The peeling concentrated on `economic_split ∈ [0.49, 0.77]` (near the 0.5,
0.583, 0.625, 0.667, 0.708, 0.750 thresholds) and progressively tightened
`pool_max_loss_pct` and `pool_ideology_strength` into very narrow bands.

### Discovered box

| Parameter              | Min    | Max    | Width  |
|------------------------|--------|--------|--------|
| economic_split         | 0.488  | 0.767  | 0.279  |
| pool_committed_split   | 0.200  | 0.500  | 0.300  |
| pool_ideology_strength | 0.468  | 0.522  | **0.054** |
| pool_max_loss_pct      | 0.249  | 0.260  | **0.011** |

**The narrow pool_ideology_strength (0.054) and pool_max_loss_pct (0.011) bounds
are a red flag.** These represent 8% and 1.6% of their respective parameter ranges.
The algorithm is not finding a meaningful structural cluster — it is scraping the
bottom of Z_user variance within a very specific overfitted corner.

### Outcome distribution in box

- v27_dominant: 38 (65.5%)
- v26_dominant: 16 (27.6%)
- contested: 4 (6.9%)

Not notably different from the full dataset (58%/24%/18%). No distinctive
outcome character in the "user-node-pivotal" region.

---

## Bias Ratio Comparison

Scenarios binned into 5 equal-frequency quintiles by SP_user. Bias ratio =
recall(top-2 quintiles) / recall(bottom-2 quintiles):

| Method         | Bias Ratio | Quintile recall (Q1→Q5)               | Completeness | N in box |
|----------------|------------|---------------------------------------|--------------|----------|
| Standard PRIM  | 0.975      | [0.43, 0.29, 0.47, 0.34, 0.35]       | 1.00         | 229      |
| User-PRIM      | 1.256      | [0.12, 0.00, 0.17, 0.00, 0.15]       | 0.60         | 58       |

**Standard PRIM** (bias=0.975) shows near-uniform recall across all SP_user
quintiles — it does not preferentially select high or low SP_user scenarios.
High-capacity actors dominate across the board, not just in the high-SP_user
corner.

**User-PRIM** (bias=1.256) nominally concentrates slightly more on the top
quintile, but the absolute recall values are near-zero throughout (0.12 at most).
Two quintiles have zero recall entirely. The bias ratio of 1.256 is essentially
noise — the underlying absolute recalls are too small (58 scenarios in the box)
to support a meaningful ratio interpretation.

---

## Sensitivity Analysis

| Config             | λ1  | λ2  | N in box | Overlap with default |
|--------------------|-----|-----|----------|----------------------|
| default            | 0.5 | 1.0 | 58       | 1.00 (reference)     |
| outcome_weighted   | 1.0 | 0.5 | 72       | 0.48                 |
| potential_heavy    | 0.5 | 2.0 | 57       | **0.00**             |

The box is **not stable** across lambda configurations. When SP_user potential is
weighted more heavily (λ2=2.0), the discovered box has zero overlap with the
default box. This is a strong indicator that no robust structural cluster exists —
the algorithm finds different corners depending on the weighting, which is
characteristic of fitting to noise rather than a genuine signal.

---

## Interpretation: Null Result

This analysis constitutes a **null result**, and that is itself a scientific finding.

User-PRIM was given every algorithmic advantage to find user-node-pivotal scenarios:
- The objective function explicitly rewards proximity to economic assignment thresholds
- The dataset (598 scenarios) densely covers the PRIM uncertainty zone
- The algorithm ran 45 steps without constraint on box shape
- Three lambda configurations were tested

Despite this, no robust cluster of user-node-pivotal contentious scenarios was found.
The evidence:
1. Bias ratio of 1.256 is near-unity and driven by near-zero absolute recalls
2. Discovered box has implausibly narrow parameter bounds (pool_max_loss_pct width = 0.011)
3. Box stability = 0% under the strongest SP_user weighting (λ2=2.0)
4. Outcome distribution inside the box is not distinctive from the full dataset
5. Economic_split shows near-zero unconditional correlation with Z_user (r=+0.017),
   indicating that proximity to thresholds does not reliably predict contentiousness

### Why user nodes don't influence fork outcomes at 2016-block retarget

The 2196:1 weight ratio means user nodes would need economic_split to be within
`W_users / W_total ≈ 0.000455` of a threshold to exert decisive influence — a
range covering roughly 1/10th of a percent of the parameter space. In practice,
the assignment mechanism (count-based on 24 nodes) means thresholds are spaced
4.17 percentage points apart, and user weight is 0.05% of total. User nodes cannot
bridge that gap in any realistic parameter configuration.

### What this adds beyond targeted_sweep4

targeted_sweep4 established non-causality through targeted parameter variation:
user behavior parameters (ideology_strength, switching_threshold) had near-zero
separation in fork outcomes. User-PRIM establishes non-causality through a
complementary structural argument: even scenarios specifically selected to maximize
user node proximity to pivotal thresholds show no distinctive contentiousness or
outcome character. The null result holds from both the behavioral dimension
(do users switch?) and the structural dimension (are users ever near-pivotal?).

---

## Files

| File | Description |
|------|-------------|
| `ANALYSIS.md` | This document |
| `user_prim_report.md` | Auto-generated report from script |
| `user_prim_results.json` | Full machine-readable results |
| `fig1_sp_user_distribution_default.png` | SP_user distribution with quintile boundaries |
| `fig2_z_user_distribution_default.png` | Z_user score histogram |
| `fig3_scatter_z_user_default.png` | economic_split × pool_committed_split scatter, colored by Z_user |
| `fig{1-3}_*_outcome_weighted.png` | Sensitivity config: λ1=1.0, λ2=0.5 |
| `fig{1-3}_*_potential_heavy.png` | Sensitivity config: λ1=0.5, λ2=2.0 |

## Reproducing

```bash
# From project root, using the warnet venv
python tools/discovery/user_prim.py

# Custom lambda or support threshold
python tools/discovery/user_prim.py --lambda1 1.0 --lambda2 0.5 --min-support 20
```
