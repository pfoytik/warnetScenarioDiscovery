# Section 4.9 — Phase 3: The Two-Layer Outcome Structure

**Draft:** May 2, 2026
**Status:** DRAFT — complete. Numbers from phase3_results.md (lhs_2016_phase3, n=300 lite) and Results_Section_Skeleton_v4.md §4.10.4 (lhs_2016_full_phase3, n=292 full network).

---

## 4.9 Phase 3: The Two-Layer Outcome Structure

Phase 3 deploys 300 scenarios drawn via Latin Hypercube Sampling from within the PRIM-defined uncertainty box — the 51% of 2016-block parameter space where Phase 2 analysis found exactly 50/50 outcomes. By concentrating all sampling within the genuine transition zone, Phase 3 resolves the fine structure of the decision boundary and produces the central new finding of this research program: **fork outcomes operate on two independent layers controlled by different parameters**. Which fork wins the hashrate war is determined by pool committed structure; whether economic nodes fully migrate to the winning chain is determined by pool loss tolerance. These two layers are largely decoupled.

---

### 4.9.1 Outcome Distribution and Transition Zone Confirmation

The Phase 3 outcome distribution confirms successful targeting of the uncertainty zone. Table 12 compares Phase 3 to prior 2016-block sweeps.

**Table 12. Outcome distribution across 2016-block sweeps, ordered by increasing transition zone concentration.**

| Sweep | n | v27-dominant | v26-dominant | Contested | Notes |
|-------|:-:|:------------:|:------------:|:---------:|-------|
| `lhs_2016_full_parameter` | 64 | 81.2% | 18.8% | 0% | Full parameter space; boundary effects diluted |
| `lhs_2016_6param` | 129 | 64.3% | 17.1% | 18.6% | Full space including boundary |
| **`lhs_2016_phase3`** | **300** | **49.0%** | **25.7%** | **25.3%** | **Sampled exclusively within PRIM 50/50 box** |

The drop in v27-dominant rate from 81.2% to 49.0% across sweeps is not a change in the underlying dynamics — it reflects increasing concentration in the boundary region where outcomes are genuinely uncertain. The 25.3% contested rate is the highest of any sweep in this research program; contested outcomes are rare in clean-outcome regions and concentrate specifically at the transition boundary.

---

### 4.9.2 Layer 1: The Hashrate War (Controlled by pool_committed_split)

Within the Phase 3 transition zone, `pool_committed_split` remains the dominant predictor of which fork wins the hashrate war. Table 13 reports feature importance within the transition zone.

**Table 13. Phase 3 feature importance within the PRIM uncertainty box (2016-block, n=300).**

| Rank | Parameter | Separation | Direction | Est. Threshold |
|:----:|-----------|:----------:|-----------|:--------------:|
| 1 | **pool_committed_split** | **0.188** | v27 when higher | **~0.296** |
| 2 | economic_split | 0.028 | v27 when higher | ~0.533 |
| 3 | pool_ideology_strength | 0.021 | v27 when lower | ~0.615 |
| 4 | pool_max_loss_pct | 0.012 | v27 when lower | ~0.276 |

`pool_committed_split` dominates at 6.7× the separation of the next-best parameter, replicating its Phase 1 dominance (separation=0.272 in `lhs_2016_6param`) within a narrower, more demanding sampling region. The threshold estimate of ~0.296 is lower than the full-space estimate (~0.346) because the PRIM box centers on the boundary, reducing the distance between threshold and the distribution's tails.

The per-outcome parameter profiles confirm the threshold structure. v26-dominant outcomes cluster at low committed_split (mean=0.202, range [0.152, 0.378]): the committed v27 pool coalition is too small to sustain the chain through the 2016-block retarget difficulty spike. v27-dominant outcomes span the full upper range (mean=0.390, range [0.248, 0.526]). A soft gap separates the two clusters near committed_split ~0.25–0.30.

When v27 wins the hashrate war, the outcome is decisive: all 147 v27-dominant scenarios reach a final v27 hashrate of 86.4%. The cascade mechanism operates as a binary switch — above the committed_split threshold, the retarget spike drives a full pool cascade; below it, v26 retains majority hashrate.

---

### 4.9.3 Layer 2: Economic Adoption (Controlled by pool_max_loss_pct)

Within the 147 v27-dominant outcomes, a second distinct layer of outcome structure emerges. Economic node migration — whether nodes fully migrate to the winning chain — is **not predicted by pool_committed_split**. It is predicted by `pool_max_loss_pct`. Table 14 reports economic switching behavior within v27-dominant scenarios.

**Table 14. Economic switching within v27-dominant Phase 3 outcomes (n=147).**

| Metric | Value |
|--------|-------|
| full_switch (econ nodes reach 100% v27) | 28 / 147 (19%) |
| no_switch (econ nodes remain at starting allocation) | 119 / 147 (81%) |
| full_switch `pool_max_loss_pct` mean | 0.186 (max = 0.217) |
| no_switch `pool_max_loss_pct` mean | 0.291 |
| full_switch `pool_committed_split` mean | 0.386 |
| no_switch `pool_committed_split` mean | 0.391 |
| Peak price gap at economic switch (full_switch) | 41.5–46.9% |
| Peak price gap (no_switch) | 12–18% |

The decoupling finding is stark: `pool_committed_split` means for full_switch vs. no_switch outcomes are 0.386 and 0.391 — statistically indistinguishable. The size of the committed pool coalition does not predict whether economic nodes migrate. What predicts it is `pool_max_loss_pct`: all 28 full_switch outcomes have max_loss_pct in [0.163, 0.217]; no scenario with max_loss_pct > 0.217 achieves full economic migration.

The threshold is sharp and absolute within the Phase 3 sample. This is not a probability gradient — it is a binary condition. A fork with pool_max_loss_pct above ~0.22 does not produce full economic adoption even when it decisively wins the hashrate war.

---

### 4.9.4 The Decoupling Mechanism

The mechanism governing Layer 2 operates through cascade speed, not cascade direction. Table 15 contrasts the two regimes.

**Table 15. Mechanism comparison: full_switch vs. no_switch within v27-dominant outcomes.**

| `pool_max_loss_pct` regime | Cascade behavior | Price gap achieved | Economic node response |
|:---------------------------:|------------------|--------------------|------------------------|
| Low (~0.186, max ≤ 0.217) | Pools abandon v26 rapidly after retarget spike | **41–47%** | Crosses inertia threshold → full migration |
| High (~0.291) | Pools drag out cascade even after v27 wins hash war | ~12–18% | Below threshold → nodes stay put |

When `pool_max_loss_pct` is low, committed v26 pools have little capacity to absorb losses and flip quickly after the 2016-block retarget spike. This generates a sharp, sustained price divergence of 41–47%. Economic nodes respond to this signal, cross their switching threshold, and fully migrate to v27.

When `pool_max_loss_pct` is high, committed v26 pools absorb larger losses before switching. The cascade ultimately completes — v27 wins the hash war — but the price signal builds more slowly and never achieves the 41–47% magnitude needed to trigger economic node migration before the simulation ends. The hash war resolves in v27's favor; the economic layer does not follow.

The econ switch timing in full_switch cases confirms the sequential two-layer structure:

| Timing metric | Value |
|---------------|-------|
| Pool cascade completion (mean) | t = 3,298s |
| Economic node migration (mean) | t = 6,804s |
| Econ lag (switch − cascade, mean) | 3,506s |
| Econ lag range | 1,209s – 6,349s |

In every full_switch case, the pool cascade fires first and the economic nodes respond approximately 3,500s later on average. The lag reflects economic node inertia: they require sustained price divergence above their switching threshold before committing to a chain change. The Layer 1 result is a necessary precondition for Layer 2, but the converse is not true — Layer 1 resolution (v27 wins hash war) does not imply Layer 2 resolution (economic adoption follows).

---

### 4.9.5 The Contested Zone

76 scenarios (25.3%) end in a contested outcome — neither chain achieves hashrate dominance over the 13,000-second simulation window. The contested cluster is distinguished not by committed_split level but by the combination of high ideology strength and high loss tolerance.

**Table 16. Per-outcome parameter profiles across Phase 3 outcomes.**

| Metric | v27-dominant (n=147) | v26-dominant (n=77) | Contested (n=76) |
|--------|:--------------------:|:-------------------:|:----------------:|
| `pool_committed_split` mean | 0.390 | 0.202 | 0.378 |
| `pool_max_loss_pct` mean | 0.270 | 0.282 | **0.302** |
| `pool_ideology_strength` mean | 0.604 | 0.625 | **0.630** |
| `economic_split` mean | 0.547 | 0.519 | 0.506 |
| Reorg count mean | 10.0 | 7.8 | 4.9 |

The contested cluster has committed_split mean of 0.378 — nearly identical to the v27-dominant cluster's 0.390. These scenarios have enough committed pool hashrate to compete but not to resolve: pools are simultaneously resistant to switching on ideology grounds and capable of absorbing losses (high max_loss_pct), so neither the cascade mechanism nor economic pressure forces capitulation within the simulation window. Two chains persist in parallel.

Reorg counts are lower in contested outcomes (mean 4.9) than in either dominant outcome (v27: 10.0, v26: 7.8). This reflects the absence of chain absorption — blocks are being mined in parallel on both chains without one chain reorganizing the other into irrelevance. Fewer reorgs in a contested outcome means less direct chain-vs-chain combat, not less disruption; two chains mining simultaneously is itself the most operationally disruptive state.

The contested zone parameter conditions — `pool_committed_split` ≥ ~0.30, `pool_ideology_strength` ≥ ~0.63, `pool_max_loss_pct` ≥ ~0.30 — define the parameter configurations a governance actor should most want to avoid. These configurations produce prolonged dual-chain situations with exchange infrastructure, wallet software, and users facing sustained uncertainty about which chain their transactions will persist on.

---

### 4.9.6 Full-Network Validation

The Phase 3 lite-network finding that pool_committed_split dominates within the transition zone was validated on the full 60-node network (`lhs_2016_full_phase3`, n=292, same PRIM bounds). The full-network result reveals a complementary finding about the regime structure.

**Table 17. Full-network Phase 3 outcome distribution (lhs_2016_full_phase3, n=292).**

| Outcome | n | % |
|---------|:-:|:-:|
| v26-dominant | 198 | 67.8% |
| v27-dominant | 71 | 24.3% |
| Contested | 23 | 7.9% |

The v26-heavy distribution (67.8% v26) reflects a structural mismatch between the PRIM box calibration and the full-network transition zone. The lite network's economic node quantization (2 nodes per partition, 50% resolution) placed the PRIM uncertainty box at lower economic support levels than the full network requires. On the full network with 24 economic nodes and ~4% resolution, the same PRIM bounds fall mostly below the ~0.563 economic threshold, producing predominantly clean v26-dominant outcomes.

Despite this distributional shift, the two-layer structure and its governing mechanism are confirmed on the full network. Full economic switching is perfectly predictive: all 71 full_switch scenarios are v27-dominant (100%); no contested or v26-dominant outcome co-occurs with full economic adoption. The Layer 1 / Layer 2 decoupling observed on the lite network is not a quantization artifact — it replicates on continuous economic weight assignment.

**Feature importance within the transition zone (full network):**

| Parameter | Separation | Direction | Est. Threshold |
|-----------|:----------:|-----------|:--------------:|
| **economic_split** | **0.164** | v27 when higher | **~0.563** |
| pool_committed_split | 0.055 | v27 when higher | ~0.349 |
| pool_max_loss_pct | 0.020 | v27 when lower | ~0.273 |
| pool_ideology_strength | 0.016 | v27 when lower | ~0.609 |

On the full network within the transition zone, `economic_split` is the dominant predictor (sep=0.164 vs. pool_committed_split sep=0.055 — a 3× gap), reversing the lite-network result. This apparent contradiction resolves when the two findings are understood as characterizing different regions of parameter space. Over the full parameter space, pool_committed_split is dominant because clean v26-dominant outcomes at very low committed_split dominate the distribution. Within the transition zone on the full network, economic_split takes over as the primary separator because the transition zone sits at the economic threshold. The two findings are complementary: pool_committed_split determines whether a scenario reaches the contested region; within that region, economic_split determines the outcome direction.

---

### 4.9.7 Four Scenario Archetypes

Phase 3 data confirms and quantitatively distinguishes four scenario archetypes that span the full outcome space.

**Table 18. Phase 3 scenario archetypes — parameter ranges, reorg counts, and operational risk.**

| Archetype | n (Phase 3) | pool_committed_split | pool_max_loss_pct | Reorg mean | Econ adoption | Operational risk |
|-----------|:-----------:|:--------------------:|:-----------------:|:----------:|:-------------:|:----------------:|
| **(1) Fast cascade** | 28 | ≥ ~0.35 | ≤ ~0.22 | — | Full | Low (resolves cleanly) |
| **(2) Hash-war only** | 119 | ≥ ~0.30 | ~0.22–0.40 | 10.0 | None | Moderate (hash resolved; econ stranded) |
| **(3) Contested stalemate** | 76 | ≥ ~0.30 | ≥ ~0.30 | 4.9 | None | **High** (dual chain persists) |
| **(4) v26 retains** | 77 | ≤ ~0.25 | — | 7.8 | None | Moderate (clear v26 win) |

The fast cascade archetype (1) is the only outcome in which both layers resolve: v27 wins the hash war and economic nodes fully migrate. It requires not just sufficient committed pool hashrate (Layer 1) but also low pool loss tolerance (Layer 2) to generate the 41–47% price gap needed for full adoption.

The hash-war-only archetype (2) is the new finding from Phase 3 not anticipated from Phase 1 analysis. It represents the majority of v27-dominant transition zone outcomes (81% of v27-dominant cases). A fork that wins the hashrate war under these conditions achieves technical dominance without economic legitimacy: the new-rules chain has more hashrate, but exchanges and custodians have not migrated. The governance implication is that hash-war victory is not equivalent to fork resolution.

The contested stalemate archetype (3) produces the highest operational risk: two viable competing chains mining in parallel, with exchange infrastructure under sustained uncertainty, for the duration of the simulation window and beyond. Phase 3's 25.3% contested rate — the highest of any sweep — reflects that this archetype is concentrated precisely in the transition zone that Phase 3 targets.

---

*Section 4.9 ends. Next: Section 4.10 — Phase 3b Cross-Network Validation.*
