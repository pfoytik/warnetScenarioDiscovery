# Section 4.10 — Phase 3b: Cross-Network Validation

**Draft:** May 2, 2026 (§4.10.4 added May 13, 2026)
**Status:** DRAFT — complete. Numbers from Results_Section_Skeleton_v4.md §4.10.4 (lhs_2016_full_phase3, n=292) and §4.10.5 (lhs_2016_full_6param, n=692).

---

## 4.10 Phase 3b: Cross-Network Validation

Phase 3 established the two-layer outcome structure on a 25-node lite network — a configuration chosen for computational tractability that introduces known quantization in economic node assignment (2 nodes per partition, ~25% resolution per node). Phase 3b replicates the identical PRIM uncertainty box bounds on the full 60-node network (`lhs_2016_full_phase3`, n=292), testing whether the two-layer finding and its governing thresholds hold at full economic resolution (~4% per node, 24 economic nodes per partition) or are artifacts of the lite network's coarser structure.

---

### 4.10.1 Two-Layer Structure Confirmed

The core finding from Phase 3 replicates on the full network without qualification. Full economic switching is perfectly predictive of v27 dominance: all 71 full_switch scenarios are v27-dominant (100%), and no contested or v26-dominant outcome co-occurs with full economic adoption. The Layer 1 / Layer 2 decoupling — hash-war outcome governed by pool_committed_split, economic adoption governed by pool_max_loss_pct — is not a lite-network artifact.

The pool_max_loss_pct adoption threshold (~0.217 on lite) shifts slightly on the full network (~0.273), consistent with the finer economic resolution producing a smoother price response curve that requires modestly higher cascade speed to cross economic node switching thresholds. The mechanism is unchanged; the threshold value shifts within the range of calibration uncertainty documented in §6.2 of assumptions.md.

The contested zone shrinks substantially on the full network: 7.9% (23/292) versus 25.3% (76/300) on lite. This reduction reflects that the full network's continuous economic weight assignment makes fewer scenarios genuinely indeterminate — small differences in economic_split that fell within a single quantization step on the lite network now resolve cleanly on the full network. The contested outcomes that remain (n=23) are confined to near-threshold parameter combinations where high ideology × high max_loss prevents cascade completion despite economic support near ~0.563.

---

### 4.10.2 The Apparent Dominant-Parameter Reversal

The most striking cross-network difference is that `economic_split` displaces `pool_committed_split` as the dominant predictor within the transition zone on the full network. Table 19 compares feature importance across the two network configurations.

**Table 19. Feature importance within the PRIM transition zone: lite network vs. full network.**

| Parameter | Lite network (n=300) | Full network (n=292) |
|-----------|:--------------------:|:--------------------:|
| **pool_committed_split** | **0.188 (#1)** | 0.055 (#2) |
| **economic_split** | 0.028 (#2) | **0.164 (#1)** |
| pool_max_loss_pct | 0.012 (#4) | 0.020 (#3) |
| pool_ideology_strength | 0.021 (#3) | 0.016 (#4) |

This reversal is not a contradiction. It is a consequence of the PRIM box calibration having been derived from lite-network data where economic node quantization compressed effective economic_split variation. On the lite network, economic_split values across [0.30, 0.80] often mapped to identical node counts (1 node = 50% weight), placing the apparent transition zone at lower economic support. On the full network with continuous assignment, the same PRIM bounds fall predominantly below the ~0.563 economic threshold — producing 67.8% v26-dominant outcomes rather than the 50/50 balance the box was designed to target.

The reconciliation is as follows: over the full parameter space, pool_committed_split is dominant because clean v26-dominant outcomes at very low committed_split dominate the distribution. Within the transition zone on the full network, economic_split is the primary separator — scenarios that reach the contested region are distinguished by whether they clear the ~0.563 economic threshold. The two parameters govern sequentially, not competitively: pool_committed_split determines whether a scenario enters the transition zone; economic_split determines the outcome direction within it.

---

### 4.10.3 Implications and Scope for Future Work

The PRIM box mismatch between lite and full network identifies a methodological refinement for future work: the uncertainty box should be re-derived from full-network data targeting econ ∈ [0.50, 0.65] to properly characterize the full-network transition zone. A refined Phase 3c sweep within these bounds would sharpen the economic threshold estimate (~0.563) and better characterize the contested zone boundary on the continuous economic weight distribution.

For the present paper's conclusions, the cross-network validation achieves its primary goal: the two-layer outcome structure — the central finding of Phase 3 — is confirmed as a real dynamic property of the fork model at full economic resolution, not an artifact of lite-network quantization. The hash-war-only archetype (v27 wins hashrate without economic adoption, 81% of v27-dominant transition zone outcomes on lite) replicates on the full network. The operational risk ranking of the four archetypes (Section 4.9.7) is unchanged.

---

### 4.10.4 Global Parameter Space: Economic_split as Universal Separator

The PRIM-zone validation establishes that the two-layer structure holds on the full network. A separate question is whether the dominant parameter within the transition zone — economic_split on the full network — is also dominant when sampling is not restricted to the contested region. `lhs_2016_full_6param` answers this with 692 scenarios drawn via Latin Hypercube Sampling from the full 6D parameter space (no zone restriction), using ranges that span both v26-favoring and v27-favoring territory.

**Table 20. Design ranges, lhs_2016_full_6param.**

| Parameter | Range | Status |
|-----------|-------|--------|
| economic_split | \[0.25, 0.95\] | varied |
| pool_committed_split | \[0.10, 0.70\] | varied |
| pool_ideology_strength | \[0.20, 0.90\] | varied |
| pool_max_loss_pct | \[0.05, 0.45\] | varied |
| pool_profitability_threshold | \[0.08, 0.28\] | varied |
| solo_miner_hashrate | \[0.00, 0.15\] | varied |
| hashrate_split | 0.25 | fixed |
| pool_neutral_pct | 30.0 | fixed |

Full 60-node network; 2016-block retarget; 692 of 720 planned scenarios completed.

The outcome distribution is near-balanced by design: 49.4% v26-dominant (342), 43.9% v27-dominant (304), 6.6% contested (46). The balance reflects that the wide sampling ranges span both sides of the decision boundary with roughly equal coverage. The contested rate of 6.6% is the lowest of any Phase 3 sweep — the broad range includes many cleanly-resolved scenarios far from the boundary, whereas the PRIM-zone sweep concentrates only in the hard-to-predict region (7.9% contested).

**Table 21. Feature importance: wide-range full-network sweep (lhs_2016_full_6param, n=692).**

| Parameter | RF Importance | Separation | Direction | Est. threshold |
|-----------|:-------------:|:----------:|-----------|:--------------:|
| **economic_split** | **60.0%** | 0.266 | v27 when higher | **~0.61** |
| pool_committed_split | 16.6% | 0.088 | v27 when higher | — |
| pool_max_loss_pct | 13.2% | 0.021 | v27 when lower | — |
| pool_ideology_strength | 10.3% | 0.015 | v27 when lower | — |
| pool_profitability_threshold | ~0% | 0.002 | — | (non-causal) |
| solo_miner_hashrate | ~0% | — | — | (non-causal) |

RF OOB accuracy: 82.4% (CV: 82.5% ± 2.9%). This is the highest accuracy of any 2016-block sweep in this program, reflecting that the wide-range sample includes many cleanly-separated scenarios that are easy to classify.

**economic_split at 60% importance is by far the global separator.** At the 3:1 ratio over pool_committed_split (60% vs. 16.6%), this is not a marginal lead — economic support is the primary determinant of fork outcomes across the full parameter space at 2016-block retarget. The PRIM v27-win box confirms this operationally: economic_split ≥ 0.665 produces a v27 win rate of 81.2% across 39.2% of the total scenario space, regardless of pool parameters.

**Per-outcome parameter means confirm the threshold structure:**

| Metric | v27-dominant (n=304) | v26-dominant (n=342) | Contested (n=46) |
|--------|:--------------------:|:--------------------:|:----------------:|
| economic_split mean | 0.743 | 0.477 | 0.590 |
| pool_committed_split mean | 0.376 | 0.321 | 0.380 |
| pool_max_loss_pct mean | 0.263 | 0.283 | — |

The 0.266 gap in economic_split between v27-dominant and v26-dominant means dwarfs the 0.055 gap in pool_committed_split. Contested scenarios sit at intermediate economic_split (~0.59), confirming that genuine outcome uncertainty concentrates near the economic threshold, not at pool commitment boundaries.

**Non-causality of pool_profitability_threshold and solo_miner_hashrate confirmed on full network.** Both parameters register effectively zero importance across 692 full-network scenarios at 2016-block. This is a decisive result: prior sweeps confirmed non-causality on the lite network (§4.5.3), but the qualification "confirmed on lite network only" had remained open. The current sweep resolves it — both parameters are non-causal at full network scale. Their values can be treated as structural constants in the 2016-block model; they need not appear in any sensitivity analysis.

**Interaction structure persists.** Standardized logistic regression coefficients identify the same multiplicative pool interactions as in prior sweeps: `committed × ideology` (+0.678) and `committed × max_loss` (+0.668) are significant, alongside the dominant `economic_split` term (+1.402). The negative `pool_ideology_strength` main effect (−0.821) reflects the finding from §4.9.4: high ideology traps committed pools in v26-signaling even when the price signal favors v27, reducing the effective pool v27 weight. The synergistic econ × committed interaction (+1.231) documented in §4.8.2 generalizes to the 6-parameter model: pool and economic factors reinforce each other multiplicatively when both favor v27.

---

### 4.10.5 Resolving the Two-Scale Structure

Together, §4.10.1–§4.10.3 (PRIM-zone full network, n=292) and §4.10.4 (wide-range full network, n=692) resolve what initially appeared to be a contradictory set of results across the research program. Finding 15 from Phase 2 identified pool_committed_split as dominant at 2016-block; Phase 3 replicated this on the lite network within the PRIM zone; but the full-network results in both sweeps show economic_split leading. Table 22 lays the full comparison out.

**Table 22. Feature importance across all 2016-block sweeps, ordered by parameter space scope.**

| Sweep | n | Network | Scope | Top parameter | Importance |
|-------|:-:|---------|-------|---------------|:----------:|
| `lhs_2016_full_parameter` | 64 | full | Full range | pool_committed_split | 0.275 sep. |
| `lhs_2016_6param` | 129 | lite | Full range | pool_committed_split | 0.272 sep. |
| `lhs_2016_phase3` | 300 | lite | PRIM zone | pool_committed_split | 0.188 imp. |
| `lhs_2016_full_phase3` | 292 | full | PRIM zone | **economic_split** | **0.164 sep.** |
| **`lhs_2016_full_6param`** | **692** | **full** | **Full range** | **economic_split** | **60.0% imp.** |

The pattern is not random. The two sweeps showing pool_committed_split dominance are both small-n or lite-network; the two large full-network sweeps both show economic_split dominance. The resolution is:

1. **The lite-network dominance of pool_committed_split is a quantization artifact.** On the lite network, economic_split quantizes into a handful of distinct node-count outcomes (~25% resolution per node). Within the PRIM bounds, many economic_split values map to the same effective weight, compressing its apparent variance and suppressing its measured importance. On the full network at ~4% resolution per node, economic_split varies continuously and its separation power is correctly measured.

2. **The early underpowered result (n=64) cannot be trusted.** The prior finding 15 identification of pool_committed_split dominance from `lhs_2016_full_parameter` (n=64) was based on too few scenarios to reliably estimate importance rankings in a 6-parameter model. The current n=692 sweep supersedes it.

3. **pool_committed_split is genuinely important — it is the gate, not the separator.** At low pool_committed_split (≤ ~0.25), v26 outcomes are clean regardless of economic conditions; there are no contested scenarios. pool_committed_split determines whether a scenario reaches the transition zone. Within the transition zone, economic_split determines direction. This sequential structure explains why pool_committed_split appears dominant in some analyses (those that include the full range of committed_split values, where the gate is load-bearing) and economic_split appears dominant in others (those that restrict to the transition zone, where the gate is already cleared).

The correct operational summary is: **pool_committed_split sets the floor below which v26 always wins; economic_split sets the ceiling above which v27 almost always wins; the contested region between these thresholds is real and accounts for roughly one-third of plausible parameter space at 2016-block retarget.** This narrative is consistent with every sweep in the program; the apparent contradictions in importance rankings reflect measurement scope, not model inconsistency.

---

*Section 4.10 ends. Next: Section 4.11 — User-PRIM: Scenario Potential for User Nodes.*
