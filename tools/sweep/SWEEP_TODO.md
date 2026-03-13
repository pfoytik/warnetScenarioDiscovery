# Sweep TODO: Progress Tracker

**Reference document:** `docs/Results_Section_Skeleton_v4.md`
**Last updated:** 2026-03-13
**Econ switching fixes committed:** `eb127a0` (pushed to GitHub 2026-03-13)
**All v2 sweeps running against committed, fixed code.**

This file tracks which sweeps are complete, running, and still needed to fill all
`[TODO]` and `[PENDING DATA]` placeholders in the Results skeleton.

---

## ✅ Phase 1 — Completed & Valid

| Sweep | n | Paper Section | Status | Notes |
|---|---|---|---|---|
| `realistic_sweep3_rapid` | 50 | §4.1, §4.6 archetypes | ✅ Done | Full 60-node |
| `balanced_baseline_sweep` | 27 | §4.1 stochastic variance | ✅ Done | Full 60-node |
| `targeted_sweep1_committed_threshold` | 45 | **§4.3.1 Table 4** — econ×committed grid | ✅ Done | Core result |
| `targeted_sweep2_hashrate_economic` | 42 | **§4.2.1 Table 3** — hashrate confound | ✅ Done | |
| `targeted_sweep2b_pool_ideology` | 20 | §4.3.3 ideology baseline | ✅ Done | |
| `targeted_sweep3b_econ_friction_verify` | 4 | §4.2 Table 2 — econ_inertia/threshold non-causal | ✅ Done | |
| `targeted_sweep4_user_behavior` | 36 | §4.2 Table 2 — user params non-causal | ✅ Done | |
| `targeted_sweep6_pool_ideology_full` | 20 | **§4.3.3, Table 5** — pool ideology diagonal | ✅ Done | grid: ideology×max_loss (4×5), econ=0.78, hash=0.25. Document incorrectly marks as PENDING — results exist. |
| `switching_ideology_threshold` | 4 | Model validation | ✅ Done 2026-03-13 | Confirms econ switching formula; switchover bracketed at ideology≈0.30–0.35 |
| `switching_neutral_fraction` | 3 | Model validation | ✅ Done 2026-03-13 | Confirms neutral fraction effect; pool cascade is timing bottleneck |

---

## ⚠️ Invalidated — Do Not Use

| Sweep | Reason | Replacement |
|---|---|---|
| `targeted_sweep5_lite_econ_threshold` | Role-name bug (lite network) | See §4.1 Table 1 footnote |
| `targeted_sweep6_lite_user_behavior` | Role-name bug (lite network) | See §4.1 Table 1 footnote |
| `targeted_sweep7_lite_inversion` | Role-name bug (lite network) | — |
| `targeted_sweep10_econ_threshold_2016` | Wrong retarget=144 (should be 2016) | `econ_threshold_2016_v2` |
| `sigmoid_2016_retarget/results_baseline` | Econ switching broken (flat 56.7%) | `results_baseline_v2` |
| `sigmoid_2016_retarget/results_sigmoid` | Econ switching broken (flat 56.7%) | `results_sigmoid_v2` |
| `econ_threshold_2016_v2/results` | Econ switching broken (flat 56.7%) | `results_v2` |

---

## 🔄 Currently Running (as of 2026-03-13)

| Sweep | Namespace | n | Duration | Retarget | ETA | Purpose |
|---|---|---|---|---|---|---|
| `econ_threshold_2016_v2/results_v2` | `sweep-econ-thresh-v2` | 2 | 13,000s | 2016 | ~7h | Bracket econ threshold in 2016-block regime (econ=0.55, 0.60) |
| `sigmoid_2016_retarget/results_baseline_v2` | `sweep-2016-base-a` | 5 | 13,000s | 2016 | ~18h | §4.5 baseline arm (econ=0.35–0.82) with working switching |
| `sigmoid_2016_retarget/results_sigmoid_v2` | `sweep-2016-sig-a` | 5 | 13,000s | 2016 | ~18h | §4.5 sigmoid oracle comparison |

---

## ❌ Still Needed — Phase 1

These are required to fill `[PENDING DATA]` tags in the skeleton before Phase 2 can begin.

### 1. Full 2016-block Economic×Committed Grid 🔴 HIGHEST PRIORITY
- **Paper section:** §4.5 Table 6, §4.5.2 discussion
- **Design:** Repeat of `targeted_sweep1` (5×9 grid) at `--retarget-interval 2016`
  - `economic_split`: [0.35, 0.50, 0.60, 0.70, 0.82]
  - `pool_committed_split`: [0.20, 0.30, 0.38, 0.43, 0.47, 0.52, 0.58, 0.65, 0.75]
  - ~45 scenarios, duration=13,000s
- **Research question:** Do the 144-block thresholds (econ~0.82, Foundry flip~0.214) hold
  under realistic 2016-block difficulty timing? Does threshold shift upward?
- **Note:** `econ_threshold_2016_v2` (2 scenarios) is partial but NOT sufficient — need full grid
- **Status:** ❌ Not started — needs spec file created

### 2. targeted_sweep7_esp (Economic Self-Sustaining Point) 🔴 HIGH PRIORITY
- **Paper section:** §4.11.1 Objective A
- **Design:**
  - `economic_split`: 0.45 to 0.85 in steps of 0.05 (~9 values)
  - `pool_committed_split`: fixed at 0.214 (Foundry flip-point)
  - `hashrate_split`: 0.25
  - Full 60-node network, ~40 scenarios
  - Duration: TBD (~20h total runtime)
- **Research question:** At what economic_split does rational preparation become
  self-reinforcing (ESP)? Expected: 0.70–0.78 range.
- **Status:** ❌ Not started — needs spec file created

### 3. targeted_sweep5_lite Re-run (Lower Priority) 🟡 LOW
- **Paper section:** §4.1 Table 1 footnote — lite network equivalence
- **Design:** Re-run `targeted_sweep5_lite_econ_threshold` after role-name bug fix
- **Research question:** Can 25-node lite network substitute for 60-node full network?
- **Status:** ❌ Not started — only do if lite equivalence claim needs supporting data

---

## ⏳ Phase 2 — Boundary Fitting (Needs Phase 1 Complete)

| Task | Paper Section | Blocker | Notes |
|---|---|---|---|
| Logistic regression boundary fit | §4.8.1 | Full 2016-block grid | Fit β coefficients for P(v27_wins) |
| Random Forest classifier | §4.8.2 | Full 2016-block grid + sweep6 | OOB accuracy, feature importance |
| PRIM box constraints | §4.8.3 | Both models above | Defines Phase 3 sampling region |
| UASF Objective B (activation threshold) | §4.11.2 | Model extension needed | New param: `activation_threshold` |
| UASF Objective C (mandatory window) | §4.11.3 | Model extension needed | New param: `mandatory_window_length` |

---

## ⏳ Phase 3 — Targeted LHS (Needs Phase 2 PRIM Complete)

| Task | Paper Section | Size | Notes |
|---|---|---|---|
| Targeted LHS in PRIM box | §4.10 | ~100–150 scenarios | ~53–80h runtime on full 60-node |
| Contentiousness score map | §4.9 | Derived | f(reorgs, reorg_mass, cascade_duration, hashrate_volatility) |
| Scenario archetype clustering | §4.10.3 | Derived | t-SNE/PCA of time-series features |

---

## Next Actions (in order)

1. **Wait** for currently running sweeps to complete (~18h)
2. **Analyze** `sigmoid_2016_retarget` v2 results — check if econ switching now visible;
   compare baseline vs sigmoid cascade timing
3. **Create spec** for full 2016-block economic×committed grid (targeted_sweep1 design at 2016-block)
   and run it — this is the single biggest remaining Phase 1 gap
4. **Create spec** for `targeted_sweep7_esp` and queue it
5. **Verify** `targeted_sweep6_pool_ideology_full` results answer §4.3.3 diagonal question —
   update skeleton's PENDING tag to reflect it's already done
6. **Begin Phase 2** boundary fitting once full 2016-block grid is complete
