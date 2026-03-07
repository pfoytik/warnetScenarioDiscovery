# Scenario Discovery: Research Plan

## Objective

Identify the subset of the Bitcoin fork simulation parameter space that produces
**genuinely contentious fork disputes** — scenarios where neither side wins cleanly
and the outcome is sensitive to small changes in real-world conditions. These
scenarios are the most policy-relevant: they represent the situations where fork
governance actually matters.

A "contentious" fork is defined by two dimensions:
1. **Outcome uncertainty** — small parameter changes flip who wins
2. **Cascade intensity** — the fork produces reorgs, orphaned blocks, and prolonged
   hashrate instability rather than a clean resolution

The plan has three phases, executed sequentially.

---

## Phase 1: Boundary Mapping (Targeted Grid Sweeps)

**Status: In progress**

Map the decision boundary by running Cartesian product sweeps that vary one or two
parameters at a time while holding everything else fixed. Each sweep produces a
grid showing where outcomes flip between v26_dominant and v27_dominant.

### What targeted sweeps accomplish

- Eliminate parameters that have no causal effect (so they can be fixed at medians
  in later phases, reducing dimensionality)
- Identify which parameters drive outcomes and in what ranges
- Reveal non-linearities and interaction effects (e.g., the inversion zone)
- Provide labeled training data for Phase 2 boundary fitting

### Completed sweeps (full network, valid)

| Sweep | Grid | Key Finding |
|-------|------|-------------|
| `targeted_sweep1` | economic_split × pool_committed_split | 2D decision boundary; non-monotonic inversion zone at econ=0.60–0.70 |
| `targeted_sweep2` | hashrate_split × economic_split | hashrate_split has no independent causal effect |
| `targeted_sweep3_neutral_pct` | pool_neutral_pct × economic_split | neutral_pct has no effect on outcome; controls cascade intensity only |
| `targeted_sweep3b` | econ_inertia × econ_switching_threshold (corners) | Economic friction irrelevant on full network |
| `targeted_sweep4` | user_ideology × user_switching_threshold × user_nodes | User parameters have zero causal effect |
| `targeted_sweep5` (lite) | economic_split | Network equivalence confirmed — lite matches full exactly at 144-block retarget |

### In progress

| Sweep | Grid | Purpose |
|-------|------|---------|
| `targeted_sweep6` (full) | pool_ideology_strength × pool_max_loss_pct | Full-network validation of diagonal threshold finding (7/20 complete) |

### Planned

| Sweep | Grid | Purpose |
|-------|------|---------|
| `targeted_sweep5_2016` (lite) | economic_split | Equivalence validation at 2016-block retarget — required before using lite network for realistic-retarget studies |

### Parameters eliminated as non-causal

The following parameters have been shown to have no effect on fork outcomes and
will be fixed at their median values in all subsequent phases:

| Parameter | Fixed Value | Evidence |
|-----------|:-----------:|---------|
| `hashrate_split` | 0.25 | targeted_sweep2 — zero effect across 0.15–0.65 |
| `pool_neutral_pct` | 30.0 | targeted_sweep3_neutral_pct — zero effect across 10–50% |
| `econ_inertia` | 0.17 | targeted_sweep3b — irrelevant on full network |
| `econ_switching_threshold` | 0.14 | targeted_sweep3b — irrelevant on full network |
| `user_ideology_strength` | 0.49 | targeted_sweep4 — zero correlation (n=36) |
| `user_switching_threshold` | 0.12 | targeted_sweep4 — zero correlation (n=36) |
| `user_nodes_per_partition` | 6 | targeted_sweep4 — zero correlation (n=36) |
| `solo_miner_hashrate` | 0.085 | targeted_sweep4 (implied) |
| `transaction_velocity` | 0.50 | No sweep has shown effect |

### Active parameters (drive outcomes)

| Parameter | Range of Interest | Evidence |
|-----------|:-----------------:|---------|
| `economic_split` | 0.50 – 0.82 | Primary driver; threshold ~0.82 for clean v27 win |
| `pool_committed_split` | 0.20 – 0.65 | Gatekeeper of cascade; non-monotonic with economic_split |
| `pool_ideology_strength` | 0.20 – 0.80 | Jointly determines threshold with max_loss_pct |
| `pool_max_loss_pct` | 0.05 – 0.45 | Jointly determines threshold with ideology_strength |

### Known structure of the decision boundary

The boundary is **non-convex** due to the inversion zone:

```
                         pool_committed_split
                  0.20  0.30  0.38  0.43  0.52  0.65  0.75
  econ=0.35        v26   v26   v26   v26   v26   v26   v26   ← always v26
  econ=0.50        v27   v26   v26   v26   v26   v26   v26   ← narrow v27 window
  econ=0.60        v27   v26   v26   v26   v26   v26   v26   ← inversion zone
  econ=0.70        v26   v26   v26   v26   v26   v26   v26   ← v26 everywhere
  econ=0.82        v27   v27   v27   v27   v27   v27   v27   ← always v27
```

The transition zone is not a simple rectangle — it has two distinct regions:
1. **Low-commit transition** (~econ=0.50, commit<0.30): small v27 window
2. **High-econ transition** (~econ=0.78–0.82): v27 wins across all committed splits,
   modulated by pool ideology × max_loss (pending sweep6 validation)

A naive bounding box enclosing "all scenarios where v27 sometimes wins" would
include large dead zones and waste Phase 3 sampling budget.

---

## Phase 2: Boundary Fitting

**Status: Planned — begin after targeted_sweep6 completes**

Fit statistical models to the labeled scenario data from Phase 1 to estimate the
transition zone as a function of all four active parameters simultaneously.

Three complementary methods are used, each providing different insights:

### Method 1: Logistic Regression

Fits a smooth parametric decision boundary. Produces a single equation
`P(v27_wins) = sigmoid(β₀ + β₁·econ + β₂·commit + β₃·ideology + β₄·max_loss + ...)`
including interaction terms (e.g., `ideology × max_loss`).

- **Strength:** Interpretable coefficients; produces smooth probability contours
- **Weakness:** Assumes monotonic, roughly linear boundary — will not capture the
  inversion zone accurately without explicit polynomial/interaction terms
- **Output:** Boundary equation for the research report; smooth P(v27_wins) surface

### Method 2: Random Forest Classifier

Ensemble of decision trees fit to scenario outcomes. No assumptions about boundary
shape — handles the inversion zone's non-monotonicity naturally.

- **Strength:** Best predictive accuracy; handles non-convex boundaries; out-of-bag
  uncertainty estimates
- **Weakness:** Black box — not directly interpretable
- **Output:** `predict_proba()` scores for rejection sampling in Phase 3

### Method 3: Patient Rule Induction Method (PRIM)

A bump-hunting algorithm (Friedman & Fisher, 1999) that finds axis-aligned
hyperrectangular subregions where the response is unusually high. The "patient"
aspect refers to iterative peeling with small step size, producing a trajectory
of nested boxes rather than a single cut.

- **Strength:** Output is a set of human-readable box constraints
  (`economic_split > 0.55 AND pool_committed_split < 0.48 AND ...`) that
  directly define the Phase 3 LHS sampling bounds. No rejection sampling needed —
  every LHS sample lands in the interesting region by construction.
- **Handles the inversion zone:** The peeling trajectory produces multiple boxes,
  one per transition region. Both the low-commit and high-econ transition zones
  can be captured.
- **Weakness:** Axis-aligned boxes are an approximation of curved boundaries;
  may be conservative
- **Output:** Box constraints → directly used as parameter bounds in Phase 3

### Contentiousness Score

In addition to binary win/loss, a continuous **contentiousness score** is computed
per scenario to capture cascade intensity:

```
contentiousness = f(total_reorgs, reorg_mass, cascade_duration, hashrate_volatility)
```

PRIM is run a second time using contentiousness as the response variable rather
than the binary outcome. This finds the region of highest chaos — which may differ
from the region of highest outcome uncertainty. The intersection of both PRIM boxes
defines the "genuinely contentious" zone for Phase 3.

### Implementation

`tools/sweep/4b_fit_boundary.py` — runs after `4_analyze_results.py`:

```
4_analyze_results.py   →   4b_fit_boundary.py   →   1_generate_scenarios.py (Phase 3)
```

Outputs:
- Fitted model objects (serialized)
- Boundary visualization plots
- PRIM box constraints as YAML (usable directly as LHS parameter bounds)
- Comparison table: logistic vs. RF vs. PRIM agreement on boundary location
- `scenarios.json` with Phase 3 LHS samples (if `--generate` flag is passed)

---

## Phase 3: Targeted Latin Hypercube Sampling

**Status: Planned — begin after Phase 2**

Run a dense LHS within the transition zone identified by Phase 2. Every sample
lands in the region where outcomes are sensitive to parameter changes and cascade
intensity is high.

### Why LHS within the transition zone

- **Grid sweeps** efficiently map coarse structure but are sparse within the transition zone
- **LHS** provides uniform coverage of a subspace in fewer runs than a full grid,
  handles all four active parameters simultaneously, and avoids grid artifacts
- **Within the transition zone**, every run produces information — there are no
  "obvious" scenarios that just confirm what the boundary sweeps already showed

### Sampling design

Parameters fixed at medians (from Phase 1 elimination):
```
hashrate_split = 0.25, pool_neutral_pct = 30.0, econ_inertia = 0.17,
econ_switching_threshold = 0.14, user_ideology_strength = 0.49,
user_switching_threshold = 0.12, user_nodes_per_partition = 6,
solo_miner_hashrate = 0.085, transaction_velocity = 0.50,
economic_nodes_per_partition = 2
```

Active parameters sampled within PRIM-defined bounds:
```
economic_split:        [PRIM_lo, PRIM_hi]
pool_committed_split:  [PRIM_lo, PRIM_hi]
pool_ideology_strength:[PRIM_lo, PRIM_hi]
pool_max_loss_pct:     [PRIM_lo, PRIM_hi]
```

Target sample size: **n=100–150 scenarios** (sufficient to densely cover 4D space
within the bounded region; LHS efficiency means 100 points in 4D ≈ 25 effective
points per dimension).

### Network

Full network (realistic-economy-v2, 60 nodes). Lite network may be used for rapid
iteration once network equivalence is validated by targeted_sweep5.

### Expected runtime

~53–80 hours at 32 min/scenario on the full network. Parallelizable across two
machines if lite network equivalence is confirmed.

---

## Phase 4: Analysis and Reporting

**Status: Planned**

With dense sampling of the transition zone, produce a complete characterization
of contentious fork conditions:

1. **Decision surface** — smooth estimate of P(v27_wins) as a function of all four
   active parameters. Where this surface crosses 0.5 is the boundary.

2. **Contentiousness map** — contentiousness score across the parameter space,
   showing where disputes are not just close but genuinely chaotic.

3. **Sensitivity analysis** — which parameters most change the outcome near the
   boundary? These are the parameters that real-world actors should watch.

4. **Scenario archetypes** — cluster Phase 3 scenarios by outcome profile to
   identify qualitatively distinct types of contentious fork (e.g., fast cascade
   vs. prolonged stalemate vs. oscillating hashrate).

5. **Policy implications** — translate parameter boundaries back into real-world
   conditions: what BTC custody concentration, miner ideology levels, and pool
   commitment structures produce governance crises?

---

## Pipeline Reference

```
Phase 1 (running)
  tools/sweep/1_generate_targeted.py --spec specs/<name>.yaml
  tools/sweep/2_build_configs.py --input <sweep>/scenarios.json --output-dir <sweep>
  tools/sweep/3_run_sweep.py --input <sweep>/build_manifest.json --duration 1800 --interval 2
  tools/sweep/4_analyze_results.py --input <sweep>/results --manifest <sweep>/build_manifest.json
  tools/sweep/5_build_database.py

Phase 2 (planned)
  tools/sweep/4b_fit_boundary.py --sweeps full_network_only --methods logistic,rf,prim

Phase 3 (planned)
  tools/sweep/1_generate_scenarios.py --bounds <prim_output>.yaml --n 100 --method lhs
  tools/sweep/2_build_configs.py --input scenarios.json --output-dir phase3_lhs
  tools/sweep/3_run_sweep.py --input phase3_lhs/build_manifest.json --duration 1800 --interval 2
  tools/sweep/4_analyze_results.py ...
  tools/sweep/5_build_database.py
```

---

## Current Status

| Phase | Status | Blocking on |
|-------|--------|------------|
| Phase 1 — boundary mapping | 🟡 In progress | targeted_sweep6 (full, 7/20 complete, ~7.5h remaining) |
| Phase 2 — boundary fitting | ⬜ Planned | Phase 1 complete |
| Phase 3 — targeted LHS | ⬜ Planned | Phase 2 complete |
| Phase 4 — analysis | ⬜ Planned | Phase 3 complete |

**Remaining Phase 1 work:**
- `targeted_sweep6_pool_ideology_full` — validates pool ideology diagonal threshold
  on full network; currently running (7/20 complete)
- `targeted_sweep5_2016` (planned) — lite network equivalence validation at 2016-block
  retarget; required before using the lite network for realistic-difficulty studies

**Completed Phase 1 milestones:**
- `targeted_sweep5_lite_econ_threshold` ✅ — lite network confirmed as valid proxy for
  full network at 144-block retarget; outcomes match exactly across all 5 economic_split
  levels. Phase 3 can use either network interchangeably for 144-block retarget runs.

---

## Design Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Mar 2026 | Fix role-name bug in `2_build_configs.py` | Lite network aggregate roles (`economic_aggregate`, `power_user_aggregate`, `casual_user_aggregate`) were not handled; all lite sweep parameters for econ/user nodes were dead |
| Mar 2026 | Add `network:` field to spec files | Prevents wrong network being used at build time; auto-detected by `2_build_configs.py` |
| Mar 2026 | Validate lite network equivalence (targeted_sweep5) | Lite network confirmed as valid proxy for full network at 144-block retarget; Phase 3 LHS can run on either network interchangeably for standard sweeps |
| Mar 2026 | Defer 2016-block retarget equivalence validation | 144-block equivalence confirmed but 2016-block retarget creates different difficulty dynamics (wider survival window, larger drops); separate validation sweep planned before using lite network for realistic-retarget studies |
| Mar 2026 | Invalidate targeted_sweep3, targeted_sweep5_lite, targeted_sweep6_lite | Results from all lite sweeps prior to role-name fix are invalid for econ/user parameters |
| Mar 2026 | Use PRIM + RF + logistic regression for boundary fitting | Complementary methods: PRIM gives interpretable box bounds, RF gives best predictive accuracy, logistic gives smooth boundary equation |
| Mar 2026 | Use contentiousness score as second PRIM response | Binary win/loss misses cascade intensity; high-chaos scenarios may be more policy-relevant than close-outcome scenarios |
