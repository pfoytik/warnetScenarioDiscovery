# Scenario Discovery (Phase 2-4)

Tools for boundary fitting and scenario discovery based on Phase 1 sweep data.

## Overview

This directory contains scripts for:
- **Phase 2**: Boundary fitting (logistic regression, random forest, PRIM)
- **Phase 3**: Targeted LHS sampling within the transition zone
- **Phase 4**: Analysis and archetype clustering

## Scripts

### fit_boundary.py

Fits statistical models to labeled scenario data from Phase 1 sweeps.

**Usage:**
```bash
# Basic run
python fit_boundary.py --db ../sweep/sweep_results.db

# With visualizations
python fit_boundary.py --db ../sweep/sweep_results.db --visualize

# Specify sweeps to include
python fit_boundary.py --db ../sweep/sweep_results.db --sweeps targeted_sweep1_committed_threshold econ_committed_2016_grid
```

**Output:**
```
output/
├── boundary_models.pkl       # Serialized fitted models
├── prim_bounds.yaml          # Box constraints for Phase 3 LHS
├── contentiousness_bounds.yaml
├── model_comparison.json     # Method agreement analysis
├── coefficients.json         # Logistic regression coefficients
└── figures/                   # Visualizations (if --visualize)
```

**Methods used:**
1. **Logistic Regression** - interpretable boundary equation with interaction terms
2. **Random Forest** - best predictive accuracy, handles non-convex boundaries
3. **PRIM** - axis-aligned box constraints for Phase 3 sampling bounds

## Dependencies

```bash
pip install pandas scikit-learn pyyaml matplotlib
```

## Workflow

```
Phase 1 (sweep/)                    Phase 2 (discovery/)              Phase 3 (sweep/)
─────────────────                   ────────────────────              ────────────────
1_generate_targeted.py              fit_boundary.py                   1_generate_scenarios.py
2_build_configs.py          →       (uses sweep_results.db)   →       (uses prim_bounds.yaml)
3_run_sweep.py                      outputs: prim_bounds.yaml         2_build_configs.py
4_analyze_results.py                                                  3_run_sweep.py
5_build_database.py                                                   ...
```

## Active Parameters

From Phase 1 findings, these parameters drive fork outcomes:
- `economic_split` (0.50 - 0.82)
- `pool_committed_split` (0.20 - 0.65)
- `pool_ideology_strength` (0.20 - 0.80)
- `pool_max_loss_pct` (0.05 - 0.45)

All other parameters are fixed at medians (see SCENARIO_DISCOVERY.md).

## Validation Status ⚠️

**Important**: The parameter non-causality findings are from **144-block retarget** conditions.

| Parameter | 144-block Status | 2016-block Status |
|-----------|-----------------|-------------------|
| `hashrate_split` | ✓ Non-causal (n=42) | ⚠️ UNVALIDATED |
| `pool_neutral_pct` | ✓ Non-causal (n=35) | ⚠️ UNVALIDATED |
| `user_*` params | ✓ Non-causal (n=36) | ⚠️ UNVALIDATED |
| `econ_inertia/switching` | ✓ Non-causal (n=4) | ⚠️ UNVALIDATED |

A verification sweep is planned: `specs/hashrate_2016_verification.yaml`

Under 2016-block conditions, the survival window is ~14× longer, which may change
the causal structure. Results from this tool should be interpreted with this caveat.
