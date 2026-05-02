# Section 4.10 — Phase 3b: Cross-Network Validation

**Draft:** May 2, 2026
**Status:** DRAFT — complete. Numbers from Results_Section_Skeleton_v4.md §4.10.4 (lhs_2016_full_phase3, n=292).

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

*Section 4.10 ends. Next: Section 4.11 — User-PRIM: Scenario Potential for User Nodes.*
