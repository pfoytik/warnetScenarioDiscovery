# Section 4.2 — Parameter Causality: Separating Signal from Confound

**Draft:** April 9, 2026  
**Status:** DRAFT — complete, all numbers filled

---

## 4.2 Parameter Causality: Separating Signal from Confound

A central methodological contribution of this work is the systematic separation of causal parameters from those that appeared influential in exploratory analysis but were subsequently shown to be confounds or non-causal. The parameter elimination program proceeded in three stages: (1) early exploratory sweeps using Latin Hypercube Sampling identified candidate predictors; (2) targeted grid sweeps isolated each candidate parameter while holding all others fixed to test for independent causal effects; and (3) unbiased LHS sweeps across all retained parameters confirmed the final causal structure under a 2016-block retarget regime.

Before presenting the elimination sequence, we establish that outcome variation in the simulation reflects causal parameter effects rather than stochastic noise. The `balanced_baseline` sweep (n=27, symmetric network, 47%/47% hashrate with equal economic nodes on each side) was run with no committed pool ideology, measuring pure mining stochasticity. Across 27 identically parameterized runs, the economic cascade mechanism never triggered: hashrate remained at 47%/47% throughout, with zero reorgs and zero cascades. Block share variance across runs was σ = 3.3% (mean 48.5% v27), producing a win distribution of v27=10 (37%), v26=15 (56%), tie=2 (7%) from pure mining randomness alone. This establishes 3.3% as the stochastic noise floor: any block share shift exceeding this value indicates active parameter influence rather than mining variance. All systematic effects documented in subsequent sections produce block share shifts of 15–50%, an order of magnitude above this baseline. The balanced_baseline also confirms that neither fork holds a structural simulation advantage at equal starting conditions — the roughly 50/50 win distribution rules out asymmetric bias in either direction.

Table 2 summarizes the complete list of parameters eliminated as non-causal through the targeted sweep program.

**Table 2. Parameters eliminated as non-causal through targeted sweeps.**

| Parameter | Fixed Value | Evidence |
|-----------|-------------|----------|
| hashrate_split | 0.25 | targeted_sweep2: zero outcome effect across 0.15–0.65 (n=42, 144-block); confirmed non-causal at econ≥60% by hashrate_2016_verification (n=18, 2016-block); conditional causality at econ=50% under 2016-block retarget — see §4.2.1 |
| pool_neutral_pct | 30% | targeted_sweep4: controls cascade duration only; outcome unchanged across neutral_pct ∈ [10%, 50%] (n=35) |
| econ_inertia | 0.17 | targeted_sweep3b: no effect on full 60-node network (n=4) |
| econ_switching_threshold | 0.14 | targeted_sweep3b: no effect on full 60-node network (n=4) |
| user_ideology_strength | 0.49 | targeted_sweep5: correlation = 0.000 across full parameter range (n=36) |
| user_switching_threshold | 0.12 | targeted_sweep5: correlation = 0.000 (n=36) |
| user_nodes_per_partition | 6 | targeted_sweep5: correlation = 0.000 (n=36) |
| pool_profitability_threshold | 0.16 | lhs_2016_6param: separation = 0.011 across [0.08, 0.28] at 2016-block retarget (n=129); previously untested |
| solo_miner_hashrate | 0.085 | lhs_2016_6param: separation ≈ 0 across [0.00, 0.15] at 2016-block retarget (n=129); previously untested |

The following subsections describe each elimination in the order it was discovered, since the sequence reflects the causal logic of the system: hashrate is the most common prior assumption and its elimination is therefore the most consequential finding.

---

### 4.2.1 The Hashrate Confound

Initial exploratory sweeps using Latin Hypercube Sampling identified hashrate_split as the dominant predictor of fork outcomes (Spearman r = +0.83). This finding appeared to confirm the conventional assumption that hashrate majority is the decisive factor in a contested fork. However, the correlation was subsequently shown to be a sampling artifact. In the LHS design, higher hashrate_split scenarios co-occurred with pool configurations that were independently favorable to v27 — specifically, higher values of pool_committed_split and economic_split. When hashrate_split was varied in isolation across a 6×7 grid spanning 0.15 to 0.65 with pool_committed_split fixed at 0.50 (deliberately above the Foundry flip-point of ~0.214, placing the system in the normal cascade regime) and all other parameters at medians (targeted_sweep2, n=42, 144-block retarget), outcomes were identical across all six hashrate levels at every economic level tested (Table 3).

**Table 3. targeted_sweep2 results: fork outcomes across hashrate_split × economic_split (144-block retarget). Identical columns across all hashrate levels confirm non-causality.**

| hash \ econ | 0.35 | 0.45 | 0.50 | 0.55 | 0.60 | 0.70 | 0.82 |
|-------------|------|------|------|------|------|------|------|
| hash = 0.15 | v26 | v27 | v27 | v27 | v26 | v26 | v27 |
| hash = 0.25 | v26 | v27 | v27 | v27 | v26 | v26 | v27 |
| hash = 0.35 | v26 | v27 | v27 | v27 | v26 | v26 | v27 |
| hash = 0.45 | v26 | v27 | v27 | v27 | v26 | v26 | v27 |
| hash = 0.55 | v26 | v27 | v27 | v27 | v26 | v26 | v27 |
| hash = 0.65 | v26 | v27 | v27 | v27 | v26 | v26 | v27 |

The columns in Table 3 are perfectly uniform: every outcome is determined entirely by economic_split, with hashrate_split contributing zero independent effect. This finding has direct implications for understanding Bitcoin fork governance — the widespread assumption that hashrate majority is the decisive factor in fork outcomes does not hold when pool ideology and economic signals are controlled. The mechanism underlying this result is the Difficulty Adjustment Survival Window (Section 4.5.1): the minority chain's difficulty adjusts downward as blocks slow, equalizing block production rates for any starting hashrate split before the economic cascade resolves. Hashrate_split may only become causal at extreme values below approximately 10%, where the survival window grows long enough for price to collapse before the minority chain reaches its first adjustment epoch.

**2016-block verification and conditional causality.** A dedicated 6×3 grid sweep at the 2016-block retarget interval (hashrate_split ∈ {0.15, 0.25, 0.35, 0.45, 0.55, 0.65} × economic_split ∈ {0.50, 0.60, 0.70}, n=18, full 60-node network) confirms and qualifies the non-causality finding. At econ=0.60 and econ=0.70, all 12 cells produce v27 wins regardless of hashrate level — replicating the targeted_sweep2 result at realistic difficulty dynamics. At econ=0.50 (economic parity), however, hashrate is conditionally causal under the 2016-block retarget interval, exhibiting non-monotonic behavior (Table 3b).

**Table 3b. hashrate_2016_verification: fork outcomes at 2016-block retarget across hashrate_split × economic_split. Uniform v27-dominant columns at econ=0.60 and econ=0.70 confirm non-causality; the econ=0.50 column shows conditional causality with a non-monotonic boundary.**

| hash \ econ | econ = 0.50 | econ = 0.60 | econ = 0.70 |
|-------------|-------------|-------------|-------------|
| hash = 0.15 | SPLIT | v27 | v27 |
| hash = 0.25 | SPLIT | SPLIT† | v27 |
| hash = 0.35 | **v26** | v27 | v27 |
| hash = 0.45 | **v26** | v27 | v27 |
| hash = 0.55 | SPLIT | v27 | v27 |
| hash = 0.65 | SPLIT | v27 | v27 |

*† Anomalous: 60% economic support produces a persistent split at hash=0.25. Economic nodes shifted to 62% v27 custody but hashrate did not converge. The adjacent econ=0.70 cell resolves cleanly to v27 dominant.*

At econ=0.50, outcomes differ qualitatively from the 144-block regime. The mechanism is the 2016-block survival window: Foundry USA (30% hashrate, ideology=0.6, profitability_threshold=12%) is the decisive actor. At intermediate hashrate (35–45%), v26 builds a chain-length lead fast enough that Foundry's accumulated mining loss exceeds its 12% tolerance after approximately one retarget cycle (~3,600 seconds), forcing a switch to v26. Pool decision logs confirm the threshold crossing: *"Forced switch: loss 12.0% exceeds tolerance 12.0%"*; post-switch, the v26 profitability premium grows to 58%, trapping all remaining hashrate on v26. At low hashrate (15–25%) and high hashrate (55–65%), the v26 chain lead develops more slowly (low HR case) or is partially offset by neutral pool migration (high HR case), keeping Foundry's losses below threshold throughout the 13,000-second simulation — producing persistent splits rather than chain capture.

This conditional causality is regime-dependent: at 144-block retarget, the survival window is too narrow for loss accumulation to reach the committed pool tolerance boundary at economic parity; at 2016-block, the window is wide enough that intermediate hashrate imbalances cross that boundary. The finding qualifies rather than reverses the non-causality result: hashrate_split is non-causal at econ ≥ 0.60, which covers the realistic range of contested forks with meaningful economic support on either side.

---

### 4.2.2 User Behavior Parameters

Three user behavior parameters — `user_ideology_strength`, `user_switching_threshold`, and `user_nodes_per_partition` — were tested across a fully crossed 3-dimensional grid on the full 60-node network (targeted_sweep5, n=36, 144-block retarget) with economic_split fixed at 0.65 (cascade zone), hashrate_split at 0.25, and pool_committed_split at 0.35 (above the Foundry flip-point). All 36 scenarios produced v26_dominant outcomes, and no user parameter showed any detectable correlation with fork outcome metrics:

| Parameter | Spearman r (vs. outcome) |
|-----------|--------------------------|
| user_ideology_strength | 0.000 |
| user_switching_threshold | 0.000 |
| user_nodes_per_partition | 0.000 |

Notably, no output metric showed any variation across user parameters — not only did the binary outcome not change, but the final v27 hashrate (0.0% in all 36 scenarios), the final economic share, and the pool opportunity cost were identical across every row of the grid. This is not a near-zero effect that could be obscured by simulation noise; it is an exact null.

User nodes collectively represent approximately 11.75% of total hashrate and a modest share of economic consensus weight in the model. This combination is insufficient to shift outcomes even under extreme parameterizations. The structural explanation is that user nodes have no independent pricing power: miners respond to revenue, which is set by exchanges and custodians — entities in the economic node class, not the user node class. A user node operator running a strict-validation full node cannot orphan miners' blocks unless the economic infrastructure that prices the resulting coins also refuses to accept them. This finding is consistent with the Phase 3 User-PRIM analysis (Section 4.11), which confirms the structural ceiling quantitatively: with W_users/W_total = 0.169/370.90 (a 2197:1 economic weight ratio), user nodes cannot be near-pivotal in any realistic parameter configuration.

User behavior parameters are fixed at their median values in all subsequent analysis.

---

### 4.2.3 Pool Neutral Percentage and Economic Friction Parameters

`pool_neutral_pct` — the share of mining pool hashrate that follows profit signals rather than ideological commitment — was expected to modulate the cascade threshold. Targeted testing (targeted_sweep3_neutral_pct, n=35, 144-block retarget) showed that while neutral_pct affects cascade duration and intensity (higher neutral_pct prolongs contested periods and reduces peak reorg depth), it does not change which fork ultimately wins. The inversion zone described in Section 4.3 persists across all tested neutral_pct levels from 10% to 50%. Even when the v26-committed block collapses from 36% to 8% of total hashrate as neutral_pct increases from 10% to 50%, the identity of the winning fork is unchanged — neutral pools migrate after the committed pool cascade, amplifying rather than initiating the outcome. The sole exception is the contested outcome at neutral=10%, econ=0.70, where Foundry's enlarged committed block (38.1% of total hashrate at neutral=10%) resists the cascade without being able to win — producing a persistent split. This contested cell resolves to v26_dominant at all neutral_pct levels above 10%. `pool_neutral_pct` is fixed at 30% for all subsequent analysis.

Economic friction parameters (`econ_inertia`, `econ_switching_threshold`) similarly showed no independent effect on the full 60-node network (targeted_sweep3b, n=4, 144-block retarget). These parameters modulate the speed at which economic nodes respond to price divergence signals, but the full-network cascade mechanism resolves before friction parameters have time to meaningfully constrain the outcome. An earlier sweep on the lite network (targeted_sweep3, n=16) suggested these parameters mattered, but that sweep was subsequently invalidated by the role-name parameter bug (see Section 4.1 and the sweep inventory). The full-network replication confirmed the null result. Both parameters are fixed at empirically motivated defaults (`econ_inertia=0.17`, `econ_switching_threshold=0.14`) in all subsequent analysis.

---

### 4.2.4 Profitability Threshold and Solo Miner Hashrate

Two additional parameters, `pool_profitability_threshold` and `solo_miner_hashrate`, had not been isolated in earlier sweeps and were tested for the first time via the 6-dimensional LHS sweep at 2016-block retarget (lhs_2016_6param, n=129).

`pool_profitability_threshold` — the minimum profit margin at which a neutral pool will switch chains — was varied across [0.08, 0.28]. Feature importance separation: 0.011 (compared to 0.272 for pool_committed_split). This parameter falls below the detection threshold; neutral pools switch within the time window of any simulated cascade regardless of where the profitability threshold is set, because the eventual price divergence far exceeds the tested threshold range.

`solo_miner_hashrate` — the fraction of total hashrate held by solo miners acting independently of pool ideology — was varied across [0.00, 0.15]. Feature importance separation: approximately 0. Solo miners in the model follow the same profitability signal as neutral pools rather than acting on ideological commitment; they do not add an independent causal pathway.

Both parameters are confirmed non-causal and fixed at defaults (0.16 and 0.085 respectively) for all Phase 2 and Phase 3 analysis.

---

### 4.2.5 Input Potential Assessment

Beyond binary causal classification, parameters differ in their capacity to determine fork outcomes across the full range of conditions. We characterize this as *input potential* — a composite measure combining causal influence, sensitivity near threshold values, and the nature of any nonlinearity. High-potential inputs are those real-world actors should monitor during a contentious fork and that Phase 3 sampling should concentrate resources on. Table 2b summarizes the input potential ranking derived from the targeted sweep program.

**Table 2b. Input potential ranking for all sweep parameters.**

| Parameter | Input Potential | Rationale |
|-----------|-----------------|-----------|
| economic_split | **Very High** | Primary driver with two distinct instability mechanisms: a knife-edge threshold at ~0.78–0.82 (economic override) AND a causal inversion zone at econ=0.60–0.70 where it reverses the sign of pool_committed_split's effect |
| pool_committed_split | **High (conditional)** | Non-monotonic and maximally sensitive in interaction with economic_split; a 0.20→0.30 shift crosses the Foundry flip-point and reverses outcome direction. Inert outside the transition zone. |
| ideology_strength × max_loss_pct | **High (near diagonal)** | Their product gates the committed pool mechanism; product ~0.12 is a binary switch between "pools eventually capitulate" and "pools hold indefinitely." Neither parameter is sufficient alone. |
| hashrate_split | **Zero (conditional)** | Confirmed non-causal at econ ≥ 0.60: targeted_sweep2 (144-block, n=42) and hashrate_2016_verification (2016-block, n=12/12 econ≥0.60 cells) both show identical outcomes across all hashrate levels. The Difficulty Adjustment Survival Window mechanism explains why: difficulty equalization neutralizes starting hashrate advantage before the economic cascade resolves (§4.5.1). Exception: at econ=0.50 under 2016-block retarget, hashrate is conditionally causal — see §4.2.1. |
| pool_neutral_pct; all user params; econ friction params | **Zero** | No causal effect on outcomes; confirmed by multiple targeted sweeps. Fixed at medians for all subsequent phases. |
| pool_profitability_threshold; solo_miner_hashrate | **Zero** | lhs_2016_6param (n=129): separation = 0.011 and ≈0 respectively across [0.08, 0.28] and [0.00, 0.15] at 2016-block retarget. First sweep to vary these parameters; both confirmed non-causal. Fixed at defaults for all analyses. |

The input potential ranking has direct implications for subsequent Latin Hypercube sampling bounds: economic_split should be sampled densely across [0.50, 0.82] where both instability mechanisms are active; pool_committed_split across [0.20, 0.65] to capture both sides of the inversion zone; ideology_strength and max_loss_pct sampled such that their product spans [0.05, 0.30], crossing the ~0.12 diagonal threshold. All zero-potential parameters are fixed at medians, reducing the effective dimensionality of the problem from eleven parameters to four.

After completing the elimination program, three active causal parameters remain: `economic_split`, `pool_committed_split`, and the `pool_ideology_strength × pool_max_loss_pct` interaction. The structure and thresholds governing these parameters are the subject of Section 4.3.

---

*Section 4.2 ends. Next: Section 4.3 — The Foundry Flip-point and Decision Boundary.*
