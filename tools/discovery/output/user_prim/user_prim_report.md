# User-PRIM Analysis Report

## Summary

**Dataset:** 598 scenarios across 15 sweeps (2016-block regime)
**Network:** 24 economic nodes, 28 user nodes
**W_users / W_total:** 0.168839 / 370.8998 (2197:1 ratio)

---

## Discovered User-PRIM Box

**Scenarios in box:** 58 (9.7% of dataset)
**Mean Z_user in box:** 0.5632 (dataset mean: 0.2991)
**Mean contentiousness:** 0.2973
**Mean SP_user:** 0.336007

**Parameter bounds (User-PRIM box):**

| Parameter | Min | Max |
|-----------|-----|-----|
| economic_split | 0.4878 | 0.7665 |
| pool_committed_split | 0.2000 | 0.5000 |
| pool_ideology_strength | 0.4675 | 0.5218 |
| pool_max_loss_pct | 0.2485 | 0.2600 |

**Outcome distribution inside box:**

- v27_dominant: 38 (65.5%)
- v26_dominant: 16 (27.6%)
- contested: 4 (6.9%)

---

## Standard PRIM vs User-PRIM: Bias Ratio Comparison

Bias ratio = recall(top-2 SP_user quintiles) / recall(bottom-2 quintiles).
Ratio > 1 → box over-represents high-SP_user scenarios (high-capacity bias).
Ratio < 1 → box concentrates on low-SP_user scenarios (user-node focus).

| Method | Bias Ratio | Completeness | N in box |
|--------|-----------|--------------|----------|
| Standard PRIM | 0.975 | 1.00 | 229 |
| User-PRIM     | 1.256 | 0.60 | 58 |

---

## Sensitivity Analysis (Lambda Configurations)

Stability of the discovered box across three λ weightings:

| λ1 (contentiousness) | λ2 (SP_user) | N in box | Mean Z_user | Box stable? |
|----------------------|-------------|----------|-------------|-------------|
| 0.5 | 1.0 | 58 | 0.5632 | ✓ |
| 1.0 | 0.5 | 72 | 0.7296 | ~ |
| 0.5 | 2.0 | 57 | 0.8659 | ~ |

---

## Interpretation

**Weak/ambiguous result.** Bias ratio = 1.256.
User-PRIM found a box but it does not strongly concentrate on
user-node-pivotal scenarios relative to the standard PRIM baseline.
The 2016-block dynamics appear primarily determined by pool and economic
actors at all parameter combinations tested — user influence remains marginal.

---

## Notes on SP_user Magnitude

With W_users=0.1688 and W_total=370.90, raw SP_user values
are near-zero for most scenarios (weight ratio ~2200:1).
The min-max normalization step is essential — without it, SP_user contributes
negligibly to Z_user variance and the analysis degrades to pure contentiousness PRIM.
SP_user range in this dataset: [0.021552, 1.000000]
After normalization, SP_user contributes meaningfully to Z_user variance.
