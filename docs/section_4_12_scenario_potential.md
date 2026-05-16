# Section 4.12 — Scenario Potential: Pool Coalition and Economic Actor Leverage

**Draft:** May 16, 2026
**Status:** DRAFT — complete.

---

## 4.12 Scenario Potential: Pool Coalition and Economic Actor Leverage

Section 4.11 applied the Scenario Potential framework to user nodes and recovered a structural null: user nodes cannot be pivotal in 2016-block fork outcomes at any tested parameter combination because their economic weight is negligible relative to exchanges and custodians. The null result validates the framework as a null-result detector — it correctly identifies actors who lack structural leverage.

This section applies the same framework to the two actor classes that *do* determine outcomes: mining pool coalitions and economic nodes (exchanges, custodians, payment processors). Scenario Potential for these actors is not a null — it produces a quantified governance leverage map that identifies precisely where in parameter space pool or economic actor decisions are most nearly pivotal, and which specific scenarios in the historical simulation record represent the highest-leverage governance moments.

---

### 4.12.1 SP_pools and SP_economic: Definitions

**SP_pools** measures the governance leverage of the committed pool coalition at a given parameter point. It is computed as the RF probability gradient with respect to `pool_committed_split`:

```
SP_pools(x) = |dP(v27_win) / d(pool_committed_split)|  evaluated at x
```

A high SP_pools value means a small shift in which large mining pools commit to which fork — for example, Foundry moving from v27-committed to v26-committed — would substantially change the predicted outcome probability. SP_pools peaks near the committed_split decision boundary (~0.296 in the Phase 3 transition zone, ~0.214 at the Foundry flip-point) and approaches zero in clean-outcome regions far from the threshold where the outcome is determined regardless of pool structure.

**SP_economic** measures the governance leverage of exchanges and custodians at a given parameter point. It is computed as the RF probability gradient with respect to `economic_split`, gated by position within the inversion zone:

```
SP_economic(x) = |dP(v27_win) / d(economic_split)| × gate(economic_split)
```

where `gate(e)` is a triangular function that equals 1.0 at the ESP (~0.74), decays linearly to 0 at the cascade floor (E=0.50) and the economic override threshold (E=0.82), and is identically 0 outside [0.50, 0.82]. The gate is not a smoothing artifact — it encodes the structural finding that exchange and custodian custody decisions are genuinely pivotal only within the inversion zone. Below the cascade floor, v27 cannot win regardless of economic action; above the override threshold, v27 wins regardless. Economic actor leverage is structurally zero outside these bounds.

Both scores are min-max normalized to [0, 1] across the dataset. The joint governance leverage score combines them:

```
Z_joint = SP_pools + SP_economic + 0.5 × contentiousness
```

Contentiousness enters with a lower weight (0.5) because it is a precondition — the outcome must be in play — rather than the primary measure of leverage. `surprise = Z_joint × (1 − outcome_certainty)` identifies scenarios where high leverage was structurally available but the outcome resolved cleanly anyway.

Source: `tools/discovery/scenario_potential.py`. Dataset: n=590 scenarios, 15 sweeps, 2016-block retarget, RF OOB accuracy 79.8%.

---

### 4.12.2 The Joint Governance Leverage Surface

**Figure AA — Joint governance leverage (Z_joint) across the E×C parameter projection.** Each scenario is plotted at its (economic_split, pool_committed_split) coordinates with color indicating Z_joint (plasma colormap; brighter = higher governance leverage). Gold stars mark the top-20 scenarios by joint Z_joint. Structural thresholds are shown as dotted lines: cascade floor (E=0.50), ESP (E≈0.74, dashed), economic override (E=0.82); Foundry flip-point (C=0.214, dotted) and Phase 3 committed threshold (C≈0.296, dashed). The PRIM uncertainty box is overlaid in blue. Right panels show SP_pools and SP_economic distributions by outcome class (boxplots). Source: `tools/discovery/output/sp/`. See `docs/figures/fig_sp_surface.png`.

![Joint Governance Leverage Surface](figures/fig_sp_surface.png)

The leverage surface has a clear structure. The highest Z_joint values concentrate in a narrow band at the intersection of two boundaries: economic_split near the ESP (0.70–0.78) and pool_committed_split near the Foundry flip-point (0.20–0.26). This intersection is the maximum governance leverage region — both pool coalition structure and economic custody decisions are simultaneously near-pivotal there. Moving away from this intersection in either dimension reduces leverage: as economic_split rises above 0.82 or falls below 0.50, SP_economic drops to zero; as pool_committed_split moves away from either threshold, SP_pools decays.

The right panels reveal the SP structure by outcome class. SP_economic is highest for contested outcomes (mean=0.101) and v27-dominant outcomes (mean=0.082), and lowest for v26-dominant (mean=0.038). This is structurally expected: v26-dominant outcomes tend to occur at low economic_split values below the cascade floor, where the gate function zeros out SP_economic entirely. Scenarios where v27 wins or the outcome is contested are more likely to occur within the inversion zone where economic actor leverage exists.

SP_pools shows a different pattern — it is nearly equal across all three outcome classes (v27: 0.100, v26: 0.106, contested: 0.094). Pool commitment leverage does not sort by outcome direction because the committed_split threshold separates outcome classes rather than being concentrated in one. Scenarios on either side of the threshold have similarly steep RF gradients — the boundary is equally sharp from both sides.

---

### 4.12.3 Top Leverage Scenarios

**Table 19. Top-10 scenarios by joint governance leverage (Z_joint).**

| Rank | Sweep | E | C | I | M | Outcome | SP_pools | SP_econ | Z_joint |
|:----:|-------|:---:|:---:|:---:|:---:|---------|:--------:|:-------:|:-------:|
| 1 | `targeted_sweep7_esp_2016` | 0.780 | 0.214 | 0.510 | 0.260 | v27_dominant | 0.868 | 0.812 | 1.912 |
| 2 | `lhs_2016_full_phase3_merged` | 0.696 | 0.248 | 0.522 | 0.272 | v27_dominant | 0.908 | 0.384 | 1.553 |
| 3 | `lhs_2016_full_phase3_merged` | 0.693 | 0.252 | 0.653 | 0.176 | v26_dominant | 1.000 | 0.480 | 1.508 |
| 4 | `lhs_2016_full_phase3_merged` | 0.761 | 0.247 | 0.582 | 0.196 | v26_dominant | 0.801 | 0.484 | 1.337 |
| 5 | `econ_committed_2016_grid` | 0.600 | 0.200 | 0.510 | 0.260 | v27_dominant | 0.647 | 0.438 | 1.302 |
| 6 | `lhs_2016_full_phase3_merged` | 0.772 | 0.234 | 0.753 | 0.260 | v27_dominant | 0.051 | 1.000 | 1.280 |
| 7 | `committed_2016_high_econ` | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.848 | 0.316 | 1.254 |
| 8 | `committed_2016_sigmoid` | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.848 | 0.316 | 1.254 |
| 9 | `lhs_2016_full_phase3_merged` | 0.666 | 0.348 | 0.721 | 0.174 | v27_dominant | 0.044 | 0.917 | 1.232 |
| 10 | `lhs_2016_6param` | 0.426 | 0.261 | 0.655 | 0.117 | v27_dominant | 0.868 | 0.000 | 1.224 |

The rank-1 scenario — `targeted_sweep7_esp_2016 sweep_0007` — is the highest governance leverage point in the entire 590-scenario dataset, with Z_joint=1.912. Its parameters (E=0.780, C=0.214) sit at the ESP × Foundry flip-point intersection: economic support is at the upper boundary of the inversion zone where exchange action is most nearly pivotal (SP_economic=0.812), and pool committed split is exactly at the structural threshold where Foundry's commitment flips the pool cascade (SP_pools=0.868). Both SP scores are simultaneously near-maximum. This scenario is the empirical realization of the governance configuration that maximizes the structural leverage of multiple actor classes simultaneously — it is the most contested governance moment in the simulation record.

Ranks 3 and 4 are notable for a different reason: both are **v26_dominant** outcomes with SP_pools ≥ 0.801 and SP_economic ≥ 0.480. These scenarios have high pool and economic leverage available and produce v26 wins — counterintuitive given that their economic support (E=0.693 and E=0.761) is well within the inversion zone and their committed splits (C=0.252 and C=0.247) are above the Foundry flip-point. The ideology × max_loss interaction (Section 4.3.3) explains the resolution: I=0.653 and M=0.176 (rank 3), I=0.582 and M=0.196 (rank 4) produce ideology × max_loss products near the diagonal threshold, enabling committed v26 pools to resist the cascade. High leverage does not guarantee a particular outcome direction — it identifies where the outcome is most sensitive to actor decisions, not which decision was made.

Rank 6 (E=0.772, C=0.234, I=0.753, M=0.260) presents the opposite SP structure: SP_pools≈0 but SP_economic=1.000 (maximum in the dataset). Pool commitment is above the Foundry flip-point by enough margin that the committed split gradient is shallow — pool structure is not at its threshold. But economic support at E=0.772 is very near the ESP, where the self-sustaining threshold is closest. This is a scenario where exchange and custodian custody decisions are maximally pivotal but pool coalition structure is not.

---

### 4.12.4 Surprise Scenarios: High Leverage, Clean Resolution

The surprise score identifies scenarios where governance leverage was structurally available — both pool and economic actors were near-pivotal — but the outcome resolved decisively anyway. These are the "least expected" outcomes from a governance leverage perspective.

**Table 20. Top-10 surprise scenarios (high Z_joint, clean resolution).**

| Rank | Sweep | E | C | Outcome | Z_joint | Surprise |
|:----:|-------|:---:|:---:|---------|:-------:|:--------:|
| 1 | `targeted_sweep7_esp_2016` | 0.780 | 0.214 | v27_dominant | 1.912 | 1.045 |
| 2 | `lhs_2016_full_phase3_merged` | 0.696 | 0.248 | v27_dominant | 1.553 | 0.964 |
| 3 | `econ_committed_2016_grid` | 0.600 | 0.200 | v27_dominant | 1.302 | 0.894 |
| 4 | `lhs_2016_full_phase3_merged` | 0.772 | 0.234 | v27_dominant | 1.280 | 0.772 |
| 5 | `lhs_2016_full_phase3_merged` | 0.733 | 0.158 | v27_dominant | 1.213 | 0.695 |
| 6 | `lhs_2016_6param` | 0.495 | 0.159 | v27_dominant | 0.889 | 0.688 |
| 7 | `lhs_2016_full_phase3_merged` | 0.693 | 0.252 | v26_dominant | 1.508 | 0.657 |
| 8 | `lhs_2016_full_phase3_merged` | 0.656 | 0.346 | contested | 0.964 | 0.635 |
| 9 | `lhs_2016_full_phase3_merged` | 0.709 | 0.164 | v27_dominant | 0.877 | 0.625 |
| 10 | `lhs_2016_full_phase3_merged` | 0.761 | 0.247 | v26_dominant | 1.337 | 0.606 |

**Figure AB — Parameter profiles of the top-15 scenarios by Z_joint.** Parallel coordinates plot showing the four active parameter values for each top scenario, colored by outcome (green = v27_dominant, red = v26_dominant, gold = contested). Horizontal dashed lines show dataset medians for each parameter. The clustering of top-leverage scenarios near the center of the economic_split axis (0.60–0.78) and the low end of pool_committed_split (0.15–0.35) is visible — these are inversion zone scenarios near the Foundry flip-point. Source: `tools/discovery/output/sp/`. See `docs/figures/fig_sp_top_scenarios.png`.

![Top Scenario Parameter Profiles](figures/fig_sp_top_scenarios.png)

The surprise rankings reveal two distinct surprise archetypes:

**Archetype A — High leverage, v27 wins cleanly (ranks 1–5, 9).** These scenarios sit in the maximum leverage zone but pool commitment was sufficient to drive the cascade to completion and economic support was high enough to approach the ESP. The outcome resolved decisively in v27's favor despite the structural leverage available to both actor classes. The governance interpretation is that the pool coalition and economic conditions were aligned — committed hashrate crossed the threshold and economic support was high enough to reinforce it — so the leverage that existed was exercised in the same direction by both actor classes simultaneously.

**Archetype B — High leverage, v26 wins unexpectedly (ranks 7, 10).** These are the more analytically interesting cases: E=0.693 and E=0.761 are solidly within the inversion zone, committed splits (C=0.252 and C=0.247) are above the Foundry flip-point, yet v26 prevails. The ideology × max_loss interaction is the mechanism — pool ideology structure prevented the cascade from completing even though the structural preconditions for a v27 win were present. These scenarios demonstrate that high governance leverage does not imply a predictable outcome direction: the leverage exists, but ideology and loss tolerance determine which direction it resolves.

Rank 8 — a contested outcome at E=0.656, C=0.346 — is the highest-surprise contested scenario in the dataset. Committed split is well above the Foundry flip-point and economic support is in the middle of the inversion zone, yet neither fork achieves dominance. This is the contested stalemate archetype from Section 4.9.5 (high ideology × high loss tolerance) appearing in the maximum leverage zone — the governance configuration that produces the most operationally disruptive outcome while simultaneously offering the most potential for intervention by either pool coalitions or economic actors.

---

### 4.12.5 Framework Validation: Comparing SP Across Actor Classes

The three Scenario Potential analyses — SP_user (Section 4.11), SP_pools, and SP_economic — together demonstrate the framework's capacity to discriminate between actor classes with and without structural governance leverage.

**Table 21. Scenario Potential framework comparison across actor classes.**

| Actor class | Structural weight | Max SP achievable | Bias ratio (PRIM) | Interpretation |
|-------------|:-----------------:|:-----------------:|:-----------------:|----------------|
| User nodes | W/W_total = 0.046% | ~0.05% | 1.256 | Structural null — weight ratio forecloses pivotality |
| Pool coalitions | Controls ~75% of hashrate | SP_pools max = 1.000 | — | Pivotal near committed_split thresholds |
| Economic nodes | Controls price signal | SP_economic max = 1.000 | — | Pivotal within inversion zone [0.50, 0.82] |

User nodes produce a near-unity bias ratio (1.256) in PRIM — the algorithm cannot concentrate user-pivotal scenarios because the 2197:1 weight ratio ensures SP_user is near-zero everywhere. Pool coalitions and economic actors produce SP scores that reach the maximum (1.000) and vary meaningfully across the parameter space — the framework correctly identifies both where leverage exists (inversion zone × Foundry flip-point neighborhood) and where it does not (clean-outcome regions far from both thresholds).

The governance implication is direct. A coordination campaign for v27 activation achieves maximum leverage when it targets the inversion zone simultaneously across both actor classes: pool operators near the Foundry flip-point (C ≈ 0.21–0.30) and economic actors near the ESP (E ≈ 0.70–0.78). Campaigns operating outside these ranges — recruiting additional committed pool hashrate when C is already well above 0.30, or seeking economic custody shifts when economic support is already above 0.82 — are targeting parameter regions where additional effort produces near-zero marginal governance leverage. The SP surface maps where effort translates into outcome influence and where it does not.

---

*Section 4.12 ends.*
