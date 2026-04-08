# Phase 3 Results: Dense Transition Zone Sampling

**Sweep:** `lhs_2016_phase3`
**Completed:** April 2026
**n:** 300 scenarios (server1: sweep\_0000–0149, server2: sweep\_0150–0299)
**Analysis:** `tools/sweep/lhs_2016_phase3/results/analysis/`

---

## 1. Purpose and Context

Phases 1 and 2 of this research established that Bitcoin fork outcomes at the 2016-block retarget interval are governed primarily by `pool_committed_split` (the fraction of hashrate held by ideologically committed pools). Phase 2 boundary fitting via PRIM identified that 51% of the prior 2016-block parameter space (n=152/298 scenarios) landed in a 50/50 uncertainty zone — a region where neither fork had a clear advantage under the Phase 1 sampling density.

Phase 3 deploys 300 scenarios drawn uniformly via Latin Hypercube Sampling (LHS) from within the PRIM-defined uncertainty box. Every scenario is concentrated in the transition zone where outcomes are sensitive to parameter values. There are no wasted runs confirming already-known clean outcomes on either side.

**Research questions:**
1. What precisely separates v27 wins from v26 wins within the transition zone?
2. How does economic node behavior (adoption of the new-rules chain) relate to the pool-level hashrate outcome?
3. What parameter configurations produce sustained contested forks vs. decisive outcomes?

---

## 2. Sweep Design

### Parameter space

| Parameter | PRIM uncertainty box bounds | Role |
|-----------|:---------------------------:|------|
| `economic_split` | [0.280, 0.779] | LHS sampled |
| `pool_committed_split` | [0.152, 0.526] | LHS sampled |
| `pool_ideology_strength` | [0.435, 0.797] | LHS sampled |
| `pool_max_loss_pct` | [0.163, 0.400] | LHS sampled |
| `hashrate_split` | 0.25 | Fixed (confirmed non-causal) |
| `pool_neutral_pct` | 30% | Fixed |
| `pool_profitability_threshold` | 0.16 | Fixed (confirmed non-causal) |
| `solo_miner_hashrate` | 0.085 | Fixed (confirmed non-causal) |

The PRIM box bounds are sourced from `tools/discovery/output/2016/uncertainty_bounds.yaml`. Support = 51% of prior 2016-block data; mean v27\_win rate within the box = 50.0%.

### Infrastructure
- 300 scenarios via LHS (seed=2026), 25 per namespace, 12 namespaces across 2 servers
- Lite network (25-node), 2016-block retarget, 13000s simulation duration
- Consistent with `lhs_2016_6param` for direct comparison

---

## 3. Outcome Distribution

| Outcome | n | % |
|---------|:-:|:-:|
| v27\_dominant | 147 | **49.0%** |
| v26\_dominant | 77 | **25.7%** |
| contested | 76 | **25.3%** |
| **Total** | **300** | |

The near-equal v27/v26 split confirms that Phase 3 successfully concentrated scenarios within the genuine uncertainty zone. Prior sweeps over wider parameter space yielded 64–81% v27\_dominant rates; the drop to 49% reflects successful targeting of the boundary region.

The 25.3% contested rate is the highest of any sweep in this research program. Contested outcomes are rare in clean-outcome regions of parameter space — their concentration here is itself a finding about the transition zone's structure.

---

## 4. Feature Importance Within the Transition Zone

| Rank | Parameter | Separation | Direction | Est. Threshold |
|:----:|-----------|:----------:|-----------|:--------------:|
| 1 | **pool\_committed\_split** | **0.188** | v27 when higher | **~0.296** |
| 2 | economic\_split | 0.028 | v27 when higher | ~0.533 |
| 3 | pool\_ideology\_strength | 0.021 | v27 when lower | ~0.615 |
| 4 | pool\_max\_loss\_pct | 0.012 | v27 when lower | ~0.276 |

`pool_committed_split` remains the dominant predictor even within the transition zone — its separation score is 6.7× the next-best parameter. This replicates the Phase 1 finding (separation=0.272 in `lhs_2016_6param`) in a narrower, more demanding sampling region.

The threshold estimate (~0.296) is lower than the full-space estimate (~0.346 from `lhs_2016_6param`). This is expected: the PRIM box centers on the boundary, so fewer scenarios sit far from the threshold on either side.

**Correlation with final outcomes (Pearson r):**

| Parameter | r with v27 hashrate share | r with econ final % |
|-----------|:-------------------------:|:-------------------:|
| pool\_ideology\_strength | −0.087 | −0.248 |
| economic\_split | +0.086 | +0.092 |
| pool\_max\_loss\_pct | −0.086 | **−0.417** |
| user\_ideology\_strength | ~0 | ~0 |

`pool_max_loss_pct` has the strongest correlation with the economic outcome (r=−0.417), foreshadowing the two-layer finding in Section 6.

---

## 5. Per-Outcome Parameter Profiles

| Metric | v27\_dominant (n=147) | v26\_dominant (n=77) | contested (n=76) |
|--------|:--------------------:|:-------------------:|:----------------:|
| `pool_committed_split` mean | 0.390 | **0.202** | 0.378 |
| `pool_committed_split` range | [0.248, 0.526] | [0.152, 0.378] | [0.187, 0.521] |
| `pool_max_loss_pct` mean | 0.270 | 0.282 | **0.302** |
| `economic_split` mean | 0.547 | 0.519 | 0.506 |
| `pool_ideology_strength` mean | 0.604 | 0.625 | **0.630** |
| Final v27 hashrate | 86.4% (all) | — | — |
| Final v26 hashrate | — | 86.4% (all) | — |
| Reorg count mean | 10.0 | 7.8 | 4.9 |

**v26\_dominant cluster:** Nearly all v26 wins occur at `pool_committed_split` ≤ 0.378 with mean 0.202 — concentrated at the low end of the PRIM box. The committed pool coalition is insufficient to sustain v27 through the 2016-block retarget difficulty spike.

**v27\_dominant cluster:** Spans the full committed\_split range [0.248, 0.526] with mean 0.390. A soft gap separates the two outcome groups near committed\_split ~0.25–0.30.

**Contested cluster:** Distinguished not by committed\_split level (mean 0.378, comparable to v27\_dominant at 0.390) but by higher `pool_ideology_strength` (0.630) and `pool_max_loss_pct` (0.302). When pools are simultaneously resistant to switching (high ideology) and capable of absorbing losses (high max\_loss\_pct), both chains remain viable without either achieving dominance.

---

## 6. Key Finding: Two-Layer Outcome Structure

This is the central new result from Phase 3.

Fork outcomes operate on **two independent layers**: (1) which chain wins the hashrate war, and (2) whether economic nodes fully migrate to the winning chain. These layers are controlled by different parameters and are largely decoupled.

### Layer 1: The hash war (controlled by pool\_committed\_split)

`pool_committed_split` above ~0.296 gives v27 the hashrate war. The pool cascade fires after the 2016-block difficulty retarget spike, driving v27 to 86.4% hashrate. This layer is described well by the Phase 1 separation analysis.

### Layer 2: Economic adoption (controlled by pool\_max\_loss\_pct)

**Economic switching among v27\_dominant outcomes (n=147):**

| Metric | Value |
|--------|-------|
| full\_switch (econ nodes reach 100% v27) | **28 / 147 (19%)** |
| no\_switch (econ nodes remain at 56.7%) | **119 / 147 (81%)** |
| full\_switch `pool_max_loss_pct` mean | **0.186** (max = 0.217) |
| no\_switch `pool_max_loss_pct` mean | **0.291** |
| full\_switch `pool_committed_split` mean | 0.386 |
| no\_switch `pool_committed_split` mean | 0.391 |

**`pool_committed_split` does not separate full\_switch from no\_switch** — the means are 0.386 vs. 0.391, statistically indistinguishable. Economic adoption is not a function of how large the committed pool coalition is.

What separates them is `pool_max_loss_pct`. All 28 full\_switch outcomes have max\_loss\_pct in [0.163, 0.217]. No scenario with max\_loss\_pct > 0.217 achieves full economic migration.

### The mechanism

| `pool_max_loss_pct` | Cascade behavior | Price gap | Econ node response |
|:-------------------:|-----------------|:---------:|-------------------|
| Low (~0.186) | Pools abandon v26 rapidly after retarget spike | **41–47%** | Crosses inertia threshold → full migration |
| High (~0.291) | Pools drag out the cascade even after v27 wins hash war | ~12–18% | Below threshold → nodes stay put |

When `pool_max_loss_pct` is low, pools have little tolerance for losses on v26 and flip quickly after the retarget spike. This generates a sharp, sustained price divergence of 41–47%. Economic nodes process this signal, cross their switching threshold, and fully migrate to v27.

When `pool_max_loss_pct` is high, pools absorb more losses before switching. The cascade completes eventually — v27 still wins the hash war — but the price signal builds more slowly and never achieves the magnitude needed to trigger economic node migration before the simulation ends.

### Econ switching timing (full\_switch cases, n=28)

| Metric | Value |
|--------|-------|
| Cascade time (pool flip) | min=1,203s, max=6,104s, **mean=3,298s** |
| Econ switch time (nodes respond) | min=2,456s, max=12,398s, **mean=6,804s** |
| Econ lag (switch − cascade) | min=1,209s, max=6,349s, **mean=3,506s** |
| Peak price gap | 41.5–46.9% |

All 28 full\_switch cases: cascade fires first (mean t=3,298s), then economic nodes respond ~3,500s later on average. The lag reflects economic node inertia — they require sustained price divergence before committing to a chain change.

**Overall econ switching rate: 28/300 = 9.3%.** This is much lower than `lhs_2016_6param` (46%). The reason is structural: the PRIM box constrains `pool_max_loss_pct` ≥ 0.163, but full\_switch requires max\_loss\_pct ≤ 0.217. Only a narrow slice of the PRIM box can produce fast cascades. This is not a change in the underlying mechanism — it reflects that the transition zone is specifically the region where pools have higher loss tolerance (which is *why* outcomes are uncertain there).

---

## 7. Contested Zone Analysis

76 scenarios (25.3%) are contested — neither chain achieves dominance over 13,000 seconds.

**What drives contention:**
- `pool_ideology_strength` mean = 0.630 (vs. 0.604 for v27\_dominant, 0.625 for v26\_dominant)
- `pool_max_loss_pct` mean = 0.302 (vs. 0.270 for v27\_dominant)

The contested zone is the intersection of high ideology and high loss tolerance. Pools are committed enough to their chain that they won't switch on ideology grounds, and loss-tolerant enough that economic pressure doesn't force them out either. The result is a sustained split where both chains continue operating past the simulation duration.

**Reorg counts:** contested mean = 4.9, range 0–5. This is lower than v26\_dominant (mean 7.8) and far lower than v27\_dominant (exactly 10). Fewer reorgs in contested outcomes reflects that neither chain is absorbing the other — blocks are being mined in parallel without chain reorganizations between them.

---

## 8. Comparison to Prior 2016-Block Sweeps

| Sweep | n | v27\_dom | v26\_dom | contested | pool\_committed\_split dominance | full\_switch rate |
|-------|:-:|:--------:|:--------:|:---------:|:------------------------------:|:-----------------:|
| `lhs_2016_full_parameter` | 64 | 81.2% | 18.8% | 0% | sep=0.275, thresh≈0.25 | 45% |
| `lhs_2016_6param` | 129 | 64.3% | 17.1% | 18.6% | sep=0.272, thresh≈0.346 | 46% |
| **`lhs_2016_phase3`** | **300** | **49.0%** | **25.7%** | **25.3%** | **sep=0.188, thresh≈0.296** | **9.3%** |

The systematic shift across sweeps reflects increasing concentration in the uncertain boundary region:
- `lhs_2016_full_parameter` sampled the full parameter space → mostly v27 wins (boundary effects diluted)
- `lhs_2016_6param` sampled full space including boundary → 64% v27, 18.6% contested
- Phase 3 sampled exclusively within the PRIM 50/50 box → 49% v27, 25.3% contested

The separation score drop (0.272 → 0.188) does not indicate that `pool_committed_split` is less important in Phase 3 — it reflects that the variance available to the separation metric is smaller when all scenarios are near the threshold. Pool committed split still dominates at 6.7× the next-best parameter within the transition zone.

---

## 9. Implications

### For fork outcome prediction

**Committed pool hashrate above ~0.296 is the primary threshold for v27 hashrate dominance** in the transition zone. Below this, v26 retains majority hashrate regardless of economic split or ideology parameters.

**Economic adoption is a secondary, independent threshold.** A fork can win the hash war without winning economic adoption. In the transition zone, 81% of v27\_dominant outcomes do not trigger full economic migration. The condition for full economic migration — `pool_max_loss_pct` ≤ ~0.22 — is more restrictive than the condition for hashrate dominance.

### For contentiousness assessment

**The contested zone is well-defined:** scenarios with `pool_committed_split` ≥ ~0.30 (enough to compete), `pool_ideology_strength` ≥ ~0.63, and `pool_max_loss_pct` ≥ ~0.30 produce sustained dual-chain situations. These are the highest-operational-risk scenarios: two chains persisting simultaneously with modest but non-trivial reorg counts.

### For real-world fork monitoring

The two-layer structure implies that observers should track two separate indicators during a contentious fork:
1. **Pool hashrate commitment** (primary): is committed-pool hashrate crossing ~0.30?
2. **Pool cascade speed** (secondary): when pools switch, how quickly? Rapid cascades (low max\_loss\_pct behavior) generate the price signal that triggers economic adoption. Slow cascades leave economic nodes stranded.

Price gap magnitude (41–47% in full\_switch vs. 12–18% in no\_switch) is a measurable real-time proxy for whether the cascade is fast enough to trigger economic migration.

---

## 10. Data Files

| File | Description |
|------|-------------|
| `tools/sweep/lhs_2016_phase3/results/analysis/sweep_data.csv` | Per-scenario data (300 rows, all metrics) |
| `tools/sweep/lhs_2016_phase3/results/analysis/report.txt` | Full feature importance report |
| `tools/sweep/lhs_2016_phase3/results/analysis/summary.json` | Outcome statistics |
| `tools/sweep/lhs_2016_phase3/results/analysis/thresholds.json` | Threshold analysis per parameter |
| `tools/sweep/lhs_2016_phase3/results/analysis/correlations.json` | Parameter correlations |
| `tools/sweep/lhs_2016_phase3/results_server1/` | Raw results ns-0–ns-5 (sweep\_0000–0149) |
| `tools/sweep/lhs_2016_phase3/results_server2/` | Raw results ns-6–ns-11 (sweep\_0150–0299) |
| `tools/sweep/lhs_2016_phase3/scenarios.json` | Full scenario configurations and PRIM box metadata |
| `tools/sweep/specs/lhs_2016_phase3.yaml` | Sweep specification |
| `tools/discovery/output/2016/uncertainty_bounds.yaml` | PRIM bounds used to define the sampling region |
