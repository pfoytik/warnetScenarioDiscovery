# Section 4.12 — Outcome Sensitivity: Pool Coalition and Economic Actor Leverage

**Draft:** May 17, 2026
**Status:** DRAFT — complete.

---

## 4.12 Outcome Sensitivity: Pool Coalition and Economic Actor Leverage

Section 4.11 applied the Scenario Potential framework to user nodes and recovered a structural null: user nodes cannot be pivotal in 2016-block fork outcomes at any tested parameter combination because their economic weight is negligible relative to exchanges and custodians. The null result validates the framework as a null-result detector — it correctly identifies actors who lack structural leverage.

This section applies outcome sensitivity analysis to the two actor classes that *do* determine outcomes: mining pool coalitions and economic nodes (exchanges, custodians, payment processors). The sensitivity measures for these actors are not null — they produce a quantified governance leverage map that identifies precisely where in parameter space pool or economic actor decisions are most nearly pivotal, and which specific scenarios in the historical simulation record represent the highest-leverage governance moments.

---

### 4.12.1 d_pools and d_economic: Definitions

**d_pools** measures the governance leverage of the committed pool coalition at a given parameter point. It is computed as the RF probability gradient with respect to `pool_committed_split`:

```
d_pools(x) = |dP(v27_win) / d(pool_committed_split)|  evaluated at x
```

A high d_pools value means a small shift in which large mining pools commit to which fork — for example, Foundry moving from v27-committed to v26-committed — would substantially change the predicted outcome probability. d_pools peaks near the committed_split decision boundary (~0.296 in the Phase 3 transition zone, ~0.214 at the Foundry flip-point) and approaches zero in clean-outcome regions far from the threshold where the outcome is determined regardless of pool structure.

**d_economic** measures the governance leverage of exchanges and custodians at a given parameter point. It is computed as the RF probability gradient with respect to `economic_split`, gated by position within the inversion zone:

```
d_economic(x) = |dP(v27_win) / d(economic_split)| × gate(economic_split)
```

where `gate(e)` is a triangular function that equals 1.0 at the ESP (~0.74), decays linearly to 0 at the cascade floor (E=0.50) and the economic override threshold (E=0.82), and is identically 0 outside [0.50, 0.82]. The gate encodes the structural finding that exchange and custodian custody decisions are genuinely pivotal only within the inversion zone. Below the cascade floor, v27 cannot win regardless of economic action; above the override threshold, v27 wins regardless. Economic actor leverage is structurally zero outside these bounds.

Both scores are min-max normalized to [0, 1] across the dataset. The joint governance leverage score combines them:

```
Z_joint = d_pools + d_economic + 0.5 × contentiousness
```

Contentiousness enters with a lower weight (0.5) because it is a precondition — the outcome must be in play — rather than the primary measure of leverage. `surprise = Z_joint × (1 − outcome_certainty)` identifies scenarios where high leverage was structurally available but the outcome resolved cleanly anyway.

**Gradient step size selection.** The sensitivity scores are computed via centered finite difference — each scenario's parameter is nudged ±Δx, the RF is queried at both points, and the absolute change in predicted probability divided by the step is the gradient estimate. Because the RF probability surface is piecewise constant (built from 600 binary tree votes), the choice of Δx requires care: too small and the nudge fails to cross any tree split threshold, returning a spurious zero; too large and the estimate averages over multiple distant thresholds, blurring local boundary structure. A sensitivity analysis across Δx ∈ {0.001, 0.005, 0.01, 0.02, 0.05} on the full dataset quantified both failure modes. At Δx=0.001, 57.1% of scenarios returned zero gradient — the step was too small to cross tree splits consistently. At Δx=0.05, the correlation with adjacent delta choices dropped below r=0.45, indicating over-smoothing. The pair Δx=0.01 and Δx=0.02 correlated at r=0.75 with each other while Δx=0.02 reduced the zero-gradient rate from 22.7% to 17.0% — a meaningful improvement with no loss of inter-delta agreement. Δx=0.02 was selected as the best balance between threshold-miss noise (too small) and boundary blurring (too large) and is used throughout this section. Source: `tools/discovery/scenario_potential.py` (`GRADIENT_DELTA = 0.02`).

Source: `tools/discovery/scenario_potential.py`. Dataset: n=590 scenarios, 15 sweeps, 2016-block retarget, RF OOB accuracy 79.8%.

**Contrast with SP_user (§4.11.0).** d_pools and d_economic are empirical gradient measures — derived from simulation data via RF finite difference. SP_user is analytic — derived from the network weight structure via a distance-to-threshold formula, because user parameters produce zero variation in RF predictions and the gradient approach would return identically zero everywhere. The framework uses the appropriate method for each actor class depending on whether the actor has measurable causal effect in the data.

---

### 4.12.2 The Joint Governance Leverage Surface

**Figure AA — Joint governance leverage (Z_joint) across the E×C parameter projection.** Each scenario is plotted at its (economic_split, pool_committed_split) coordinates with color indicating Z_joint (plasma colormap; brighter = higher governance leverage). Gold stars mark the top-20 scenarios by joint Z_joint. Structural thresholds are shown as dotted lines: cascade floor (E=0.50), ESP (E≈0.74, dashed), economic override (E=0.82); Foundry flip-point (C=0.214, dotted) and Phase 3 committed threshold (C≈0.296, dashed). The PRIM uncertainty box is overlaid in blue. Right panels show d_pools and d_economic distributions by outcome class (boxplots). Source: `tools/discovery/output/sp/`. See `docs/figures/fig_sp_surface.png`.

![Joint Governance Leverage Surface](figures/fig_sp_surface.png)

The leverage surface has a clear structure. The highest Z_joint values concentrate in a narrow band at the intersection of two boundaries: economic_split near the ESP (0.70–0.78) and pool_committed_split near the Foundry flip-point (0.20–0.26). This intersection is the maximum governance leverage region — both pool coalition structure and economic custody decisions are simultaneously near-pivotal there. Moving away from this intersection in either dimension reduces leverage: as economic_split rises above 0.82 or falls below 0.50, d_economic drops to zero; as pool_committed_split moves away from either threshold, d_pools decays.

The right panels reveal the gradient structure by outcome class. d_economic is highest for contested outcomes (mean=0.095) and v27-dominant outcomes (mean=0.073), and lowest for v26-dominant (mean=0.054). This is structurally expected: v26-dominant outcomes tend to occur at low economic_split values below the cascade floor, where the gate function zeros out d_economic entirely. Scenarios where v27 wins or the outcome is contested are more likely to occur within the inversion zone where economic actor leverage exists.

d_pools shows a different pattern — it is nearly equal across all three outcome classes (v27: 0.124, v26: 0.138, contested: 0.121). Pool commitment leverage does not sort by outcome direction because the committed_split threshold separates outcome classes rather than being concentrated in one. Scenarios on either side of the threshold have similarly steep RF gradients — the boundary is equally sharp from both sides.

---

### 4.12.3 Top Leverage Scenarios

**Table 19. Top-10 scenarios by joint governance leverage (Z_joint).**

| Rank | Sweep | E | C | I | M | Outcome | d_pools | d_econ | Z_joint |
|:----:|-------|:---:|:---:|:---:|:---:|---------|:-------:|:------:|:-------:|
| 1 | `targeted_sweep7_esp_2016` | 0.780 | 0.214 | 0.510 | 0.260 | v27_dominant | 0.719 | 0.966 | 1.918 |
| 2 | `lhs_2016_full_phase3_merged` | 0.761 | 0.247 | 0.582 | 0.196 | v26_dominant | 0.948 | 0.903 | 1.902 |
| 3 | `committed_2016_high_econ` | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.696 | 1.000 | 1.785 |
| 4 | `committed_2016_sigmoid` | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.696 | 1.000 | 1.785 |
| 5 | `lhs_2016_full_phase3_merged` | 0.753 | 0.245 | 0.696 | 0.327 | v26_dominant | 0.553 | 0.862 | 1.455 |
| 6 | `lhs_2016_full_phase3_merged` | 0.671 | 0.260 | 0.520 | 0.240 | v27_dominant | 1.000 | 0.194 | 1.439 |
| 7 | `lhs_2016_full_phase3_merged` | 0.772 | 0.234 | 0.753 | 0.260 | v27_dominant | 0.156 | 0.917 | 1.301 |
| 8 | `lhs_2016_6param` | 0.647 | 0.260 | 0.409 | 0.131 | v27_dominant | 0.916 | 0.036 | 1.296 |
| 9 | `lhs_2016_full_phase3_merged` | 0.696 | 0.248 | 0.522 | 0.272 | v27_dominant | 0.813 | 0.209 | 1.283 |
| 10 | `lhs_2016_full_phase3_merged` | 0.666 | 0.348 | 0.721 | 0.174 | v27_dominant | 0.103 | 0.904 | 1.278 |

The rank-1 scenario — `targeted_sweep7_esp_2016 sweep_0007` — is the highest governance leverage point in the entire 590-scenario dataset, with Z_joint=1.918. Its parameters (E=0.780, C=0.214) sit at the ESP × Foundry flip-point intersection: economic support is at the upper boundary of the inversion zone where exchange action is most nearly pivotal (d_economic=0.966), and pool committed split is exactly at the structural threshold where Foundry's commitment flips the pool cascade (d_pools=0.719). Both gradient scores are simultaneously near-maximum. This scenario is the empirical realization of the governance configuration that maximizes the structural leverage of multiple actor classes simultaneously — it is the most contested governance moment in the simulation record.

Ranks 2–5 are notable for being **v26_dominant** outcomes with high Z_joint. Rank 2 (E=0.761, C=0.247) has d_pools=0.948 and d_economic=0.903 — the second highest joint leverage in the dataset — yet v26 prevails. Economic support is solidly in the inversion zone and committed split is above the Foundry flip-point; both actor classes had maximum available leverage and v26 still won. The ideology × max_loss interaction (I=0.582, M=0.196) explains this: the ideology × max_loss product sits near the diagonal threshold (Section 4.3.3), enabling committed v26 pools to resist the cascade despite the structural disadvantage. Ranks 3 and 4 are identical parameter configurations from two different sweeps (`committed_2016_high_econ` and `committed_2016_sigmoid`) — both at E=0.780, C=0.200, both producing maximum d_economic=1.000 with v26_dominant outcomes.

Rank 6 (E=0.671, C=0.260) presents the opposite gradient structure from rank 1: d_pools=1.000 (maximum in the dataset) but d_economic=0.194. Pool commitment is right at the transition zone threshold — the RF gradient over committed_split is maximally steep there — but economic support at E=0.671 is below the ESP, reducing economic leverage. This is the scenario where pool coalition decisions are maximally pivotal but exchange and custodian decisions are not.

---

### 4.12.4 Surprise Scenarios: High Leverage, Clean Resolution

The surprise score identifies scenarios where governance leverage was structurally available — both pool and economic actors were near-pivotal — but the outcome resolved decisively anyway. These are the "least expected" outcomes from a governance leverage perspective.

**Table 20. Top-10 surprise scenarios (high Z_joint, clean resolution).**

| Rank | Sweep | E | C | Outcome | Z_joint | Surprise |
|:----:|-------|:---:|:---:|---------|:-------:|:--------:|
| 1 | `targeted_sweep7_esp_2016` | 0.780 | 0.214 | v27_dominant | 1.918 | 1.048 |
| 2 | `lhs_2016_full_phase3_merged` | 0.761 | 0.247 | v26_dominant | 1.902 | 0.862 |
| 3 | `lhs_2016_full_phase3_merged` | 0.709 | 0.164 | v27_dominant | 1.132 | 0.808 |
| 4 | `lhs_2016_full_phase3_merged` | 0.696 | 0.248 | v27_dominant | 1.283 | 0.796 |
| 5 | `lhs_2016_full_phase3_merged` | 0.772 | 0.234 | v27_dominant | 1.301 | 0.785 |
| 6 | `econ_committed_2016_grid` | 0.600 | 0.200 | v27_dominant | 0.993 | 0.682 |
| 7 | `lhs_2016_full_phase3_merged` | 0.733 | 0.158 | v27_dominant | 1.135 | 0.651 |
| 8 | `targeted_sweep10_econ_threshold_2016` | 0.500 | 0.350 | v27_dominant | 0.865 | 0.616 |
| 9 | `targeted_sweep10_econ_threshold_2016` | 0.350 | 0.350 | v27_dominant | 0.877 | 0.611 |
| 10 | `lhs_2016_6param` | 0.495 | 0.159 | v27_dominant | 0.768 | 0.594 |

**Figure AB — Parameter profiles of the top-15 scenarios by Z_joint.** Parallel coordinates plot showing the four active parameter values for each top scenario, colored by outcome (green = v27_dominant, red = v26_dominant, gold = contested). Horizontal dashed lines show dataset medians for each parameter. The clustering of top-leverage scenarios near the center of the economic_split axis (0.65–0.78) and the low end of pool_committed_split (0.15–0.35) is visible — these are inversion zone scenarios near the Foundry flip-point. Source: `tools/discovery/output/sp/`. See `docs/figures/fig_sp_top_scenarios.png`.

![Top Scenario Parameter Profiles](figures/fig_sp_top_scenarios.png)

The surprise rankings reveal two distinct archetypes:

**Archetype A — High leverage, v27 wins cleanly (ranks 1, 3–7).** These scenarios sit in the maximum leverage zone but pool commitment was sufficient to drive the cascade to completion and economic support reinforced it. The outcome resolved decisively in v27's favor despite the structural leverage available to both actor classes. Rank 1 (E=0.780, C=0.214) is the extreme case: the highest Z_joint in the dataset resolves to a clean v27 win — the leverage was real but both pool structure and economic conditions were aligned in the same direction, so the potential for intervention was present but unused.

**Archetype B — High leverage, v26 wins unexpectedly (rank 2).** Rank 2 (E=0.761, C=0.247, Z_joint=1.902) is the most analytically interesting case in the dataset: economic support is deep in the inversion zone, committed split is above the Foundry flip-point, both gradient scores are near-maximum, yet v26 prevails. This is a genuine surprise — governance leverage was maximally available to both pool coalitions and economic actors favoring v27, and the outcome went the other way. The ideology × max_loss interaction is the mechanism: pool ideology was strong enough to hold v26 pools in place through the simulation window despite the structural disadvantage. This scenario has the highest surprise score among v26_dominant outcomes (surprise=0.862) and represents the most operationally disruptive governance configuration in the dataset — maximum leverage, unexpected direction.

Ranks 8 and 9 (both from `targeted_sweep10_econ_threshold_2016`) are notable for appearing at E=0.500 and E=0.350 — below or at the cascade floor where d_economic is gated to zero. These are high-surprise v27 wins driven entirely by d_pools: committed split at C=0.350 is well above the Foundry flip-point, and pool cascade dynamics resolved the outcome cleanly despite low economic support. They illustrate that pool-only leverage (without economic co-activation) can still produce decisive outcomes when committed_split is sufficiently above threshold.

### 4.12.4a Surprise PRIM: Parameter Region of Maximum Unexpected Resolution

PRIM peeling applied to the surprise score identifies the parameter subspace where governance leverage is high but outcomes resolve decisively — the region most likely to produce unexpected fork conclusions.

![Surprise PRIM Figure](figures/fig_surprise_prim.png)

**Figure AC — Surprise PRIM analysis across the E×C parameter projection.** Main panel: each scenario plotted at (economic_split, pool_committed_split) colored by surprise score (plasma colormap; brighter = higher surprise). White stars mark the top-15 scenarios by surprise. The cyan box is the Surprise PRIM discovered region; the blue dashed box is the standard contentiousness PRIM box for reference. Structural thresholds annotated as in prior figures. Top-right: PRIM peeling trajectory showing mean surprise concentration as box shrinks (orange = trajectory, gray dashed = dataset mean, cyan = final box size). Bottom-right: surprise score distributions by outcome class with in-box scenarios overlaid as dots. Right panel: parallel coordinates of the top-15 surprise scenarios colored by outcome. Source: `tools/discovery/output/sp/sp_scores.csv`.

**Surprise PRIM discovered box:**

| Parameter | Min | Max |
|-----------|-----|-----|
| `economic_split` | 0.35 | 0.78 |
| `pool_committed_split` | 0.15 | 0.58 |
| `pool_ideology_strength` | 0.51 | 0.77 |
| `pool_max_loss_pct` | 0.17 | 0.35 |

**Box statistics:** n=264 scenarios (44.7% of dataset), mean surprise = 0.126 vs. dataset mean 0.091 — lift of 1.38×. Outcome distribution inside box: 131 v26_dominant (49.6%), 115 v27_dominant (43.6%), 18 contested (6.8%).

The Surprise PRIM box is substantially larger and less concentrated than the contentiousness PRIM box (n=229, 38.8%), reflecting the structural tension in the surprise definition: scenarios with high governance leverage tend to be contested, which reduces the clean-resolution component of the surprise score. The two requirements — high Z_joint and decisive outcome — partially oppose each other, making concentration harder to achieve through peeling.

The `pool_ideology_strength` bounds [0.51, 0.77] are the most distinctive feature of the Surprise PRIM box relative to the contentiousness box. This narrow ideology band corresponds to pools with sufficient commitment to create structural leverage (high enough ideology to resist switching purely on profitability) but not so extreme that outcomes are locked in by ideology alone. It is the regime where pool decisions are genuinely pivotal — and where decisive resolutions are therefore structurally surprising.

The near-equal outcome split inside the box (131 v26 vs. 115 v27) confirms these are genuinely uncertain-leverage scenarios that happened to resolve cleanly — not scenarios where one fork was structurally favored. The surprise PRIM box identifies where a governance analyst or practitioner should expect the least predictability from observable parameters: high leverage, aligned conditions for either fork, yet decisive resolution.

---

*Section 4.12 ends. Next: Section 4.13 — Scenario Potential Framework: Cross-Actor Leverage Comparison.*
