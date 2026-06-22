# Section 4.13 — Scenario Potential Framework: Cross-Actor Leverage Comparison

**Draft:** June 20, 2026
**Status:** DRAFT — complete.

---

## 4.13 Scenario Potential Framework: Cross-Actor Leverage Comparison

The three actor-class analyses — SP_user (Section 4.11), d_pools, and d_economic (Section 4.12) — together demonstrate the framework's capacity to discriminate between actor classes with and without structural governance leverage. Each analysis uses the method appropriate to the actor's causal footprint in the simulation data: RF probability gradient for actors with measurable effect (pools, economic nodes), and analytic distance-to-threshold for actors whose parameters produce no RF variation (user nodes).

**Table 21. Actor leverage comparison across the Scenario Potential framework.**

| Actor class | Structural weight | Measure | Max value | Bias ratio (PRIM) | Interpretation |
|-------------|:-----------------:|---------|:---------:|:-----------------:|----------------|
| User nodes | W/W_total = 0.046% | SP_user (analytic) | ~0.05% | 1.256 | Structural null — weight ratio forecloses pivotality |
| Pool coalitions | Controls ~75% of hashrate | d_pools (RF gradient) | 1.000 | — | Pivotal near committed_split thresholds |
| Economic nodes | Controls price signal | d_economic (RF gradient) | 1.000 | — | Pivotal within inversion zone [0.50, 0.82] |

User nodes produce a near-unity bias ratio (1.256) in PRIM — the algorithm cannot concentrate user-pivotal scenarios because the 2197:1 weight ratio ensures SP_user is near-zero everywhere. Pool coalitions and economic actors produce gradient scores that reach the maximum (1.000) and vary meaningfully across the parameter space — the framework correctly identifies both where leverage exists (inversion zone × Foundry flip-point neighborhood) and where it does not (clean-outcome regions far from both thresholds).

The contrast between methods is also a substantive finding. SP_user requires an analytic formula because user parameters have no causal path to the RF's learned decision surface — the simulation confirms this mechanistically (targeted_sweep5 produced zero variation across the full user parameter space). d_pools and d_economic are empirical because pool and economic parameters *do* causally determine the RF's predictions; the gradient surface reflects real boundary structure in the data rather than theoretical weight ratios.

**Governance implication.** A coordination campaign for v27 activation achieves maximum leverage when it targets the inversion zone simultaneously across both actor classes: pool operators near the Foundry flip-point (C ≈ 0.21–0.30) and economic actors near the ESP (E ≈ 0.70–0.78). Campaigns operating outside these ranges — recruiting additional committed pool hashrate when C is already well above 0.30, or seeking economic custody shifts when economic support is already above 0.82 — are targeting parameter regions where additional effort produces near-zero marginal governance leverage. The sensitivity surface maps where effort translates into outcome influence and where it does not.

---

*Section 4.13 ends.*
