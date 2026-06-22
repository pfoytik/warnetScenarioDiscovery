# 4. Results

This section presents findings from 1,385 simulation scenarios across 21 sweep configurations using the Warnet testing framework. Results are organized in discovery order: parameter causality (§4.2–4.3), regime comparison and survival window mechanism (§4.4–4.5), cascade dynamics and governance implications (§4.6–4.7), formal boundary fitting (§4.8), Phase 3 transition zone analysis (§4.9–4.10), and Scenario Potential analyses across actor classes (§4.11–4.12).

---

---

## 4.1 Scenario Overview and Exploratory Process

This section presents findings from 1,385 simulation scenarios across 21 sweep configurations, generated through two complementary methods. The first is Latin Hypercube Sampling (LHS) — a space-filling design that spreads scenarios as uniformly as possible across the full parameter space, minimizing sampling bias and ensuring no region of the input space is systematically over- or under-represented. LHS sweeps were used at each major phase of the research to obtain an unbiased view of the parameter landscape before any hypothesis about structure had been formed. The second method is targeted grid sweeps — fixed-grid experiments designed after LHS analysis had identified candidate structures, thresholds, and contention points. Targeted sweeps vary one or two parameters at a time while holding all others fixed, with the explicit objective of confirming or falsifying specific causal claims and mapping threshold boundaries precisely.

The two methods are complementary by design. LHS provides broad, unbiased coverage that reveals which parameters appear to matter and roughly where boundaries lie, but it cannot resolve fine structure near thresholds or isolate individual parameter effects. Targeted sweeps provide that resolution, but only for the specific hypotheses they test — they cannot discover structure that was not anticipated from prior LHS analysis. The research program alternated between the two: LHS to discover, targeted sweeps to confirm and quantify. This section documents that sequence.

---

### 4.1.1 Sweep Inventory

Table 1 lists all 21 sweep configurations, their validity status, scenario counts, and primary purpose. Eight scenarios from the `targeted_sweep3/5/6 (lite)` group were discarded due to a role-name parameter bug identified in March 2026; all other sweeps are valid for analysis.

**Table 1. Complete sweep inventory.**

| Sweep | n | Network | Status | Primary Purpose |
|-------|:-:|:-------:|:------:|-----------------|
| `realistic_sweep3_rapid` | 50 | 60-node | ✓ Valid | Fixed-code baseline — confirms economic cascade mechanism |
| `balanced_baseline` | 27 | 24-node | ✓ Valid | Stochastic variance baseline at 50/50 starting conditions |
| `targeted_sweep1` | 45 | 60-node | ✓ Valid | Economic × pool_committed_split grid — threshold and inversion zone |
| `targeted_sweep2` | 42 | 60-node | ✓ Valid | Hashrate × economic grid — hashrate shown non-causal |
| `targeted_sweep3b` | 4 | 60-node | ✓ Valid | Economic friction verification on full network |
| `targeted_sweep4` | 35 | 60-node | ✓ Valid | Pool neutral % × economic grid — neutral % has no outcome effect |
| `targeted_sweep5` | 36 | 60-node | ✓ Valid | User ideology parameters — no causal effect detected |
| `targeted_sweep6_pool_ideology_full` | 20 | 60-node | ✓ Valid | Pool ideology × max_loss_pct diagonal threshold at econ=0.78 |
| `targeted_sweep6_econ_override` | 27 | 60-node | ✓ Valid | Economic override threshold — 27/27 v27-dominant; cascade timing 700–10,920s |
| `targeted_sweep7_esp` (144-block) | 9 | 60-node | ✓ Valid | ESP = 0.74; threshold between econ=0.70→0.78 |
| `targeted_sweep7_esp` (2016-block) | 9 | 60-node | ✓ Valid | ESP = 0.74 confirmed; retarget interval does not shift ESP |
| `hashrate_2016_verification` | 18 | 60-node | ✓ Valid | Hashrate non-causality at 2016-block; conditional causality at econ=0.50 |
| `econ_committed_2016_grid` | 45 | 60-node | ✓ Valid | 5×9 economic × pool_committed_split grid at 2016-block retarget |
| `price_divergence_sensitivity_2016` | 48 | 60-node | ✓ Valid | 4 cap levels × 12 scenarios; ±10% cap binds; confirms ideology/inertia lock |
| `lhs_2016_full_parameter` | 64 | 60-node | ✓ Valid | Unbiased LHS at 2016-block — pool_committed_split dominates (sep=0.275) |
| `lhs_2016_6param` | 129 | 25-node | ✓ Valid | 6D LHS at 2016-block — confirms dominance; adds profitability_threshold and solo_miner_hashrate as non-causal |
| `lhs_144_6param` | 130 | 25-node | ✓ Valid | Matched 144-block LHS — regime comparison; econ quantization artifact documented |
| `lhs_2016_phase3` | 300 | 25-node | ✓ Valid | Phase 3 dense LHS within PRIM uncertainty box — two-layer outcome structure |
| `lhs_2016_full_phase3` | 292 | 60-node | ✓ Valid | Full-network Phase 3 — economic_split dominates within transition zone (sep=0.164) |
| `targeted_sweep2b` (lite) | 20 | 25-node | ⚠ Partial | Pool ideology on lite network — pool params valid; economic context incorrect |
| `targeted_sweep3/5/6` (lite) | 60 | 25-node | ✗ Invalid | Role-name bug — econ/user parameters silently ignored; results discarded |
| **Total** | **1,385** | | | |

**Role-name bug (March 2026).** The 25-node lite network uses aggregate node roles (`economic_aggregate`, `power_user_aggregate`, `casual_user_aggregate`) that the parameter injection script did not handle, causing economic and user parameters to be silently ignored in early lite-network sweeps. The bug was identified in March 2026 and corrected in `2_build_configs.py`. All full 60-node network sweeps are unaffected. The three affected lite-network sweeps (targeted_sweep3/5/6, n=60) are excluded from all analysis. Targeted_sweep2b (n=20) is partially affected — pool parameters are valid but economic context is incorrect; it is excluded from quantitative analysis but contributed to identifying the diagonal ideology threshold qualitatively.

---

### 4.1.2 The Exploratory Sequence

The sweep program proceeded in three phases, each motivated by findings from the previous one. The sequence is described below in discovery order, which is the order that reveals the causal logic of the system.

**Phase 0: Baseline and initial LHS (realistic_sweep3_rapid, balanced_baseline).**

The research program began with a code-fixed baseline sweep (`realistic_sweep3_rapid`, n=50, full 60-node network) that confirmed the economic cascade mechanism is real. Correlation analysis of this initial sweep's LHS-distributed parameter configurations identified `hashrate_split` as the apparent dominant predictor (Spearman r=+0.83) — seemingly confirming the conventional assumption that hashrate determines fork outcomes. The `balanced_baseline` sweep (n=27, symmetric 47%/47% starting conditions, no committed pool ideology) established the stochastic noise floor at σ=3.3% block share variance, confirming that any shift exceeding this threshold in subsequent sweeps reflects genuine parameter effects rather than mining randomness.

**Phase 1: Targeted sweeps for causal isolation (targeted_sweep1 through targeted_sweep7).**

The apparent r=+0.83 hashrate correlation was the first contention point for targeted investigation. `targeted_sweep2` (n=42, 144-block) varied hashrate_split across 0.15–0.65 with all other parameters fixed — producing perfectly uniform columns across all hashrate levels and falsifying the correlation as a sampling artifact. High hashrate_split scenarios in the initial LHS had co-occurred with pool configurations independently favorable to v27, creating a spurious correlation.

With hashrate eliminated, `targeted_sweep1` (n=45) mapped the joint economic_split × pool_committed_split space and revealed the inversion zone at econ=0.60–0.70 — where increasing pool_committed_split reverses the outcome. This non-monotonic structure was not anticipated from any prior LHS analysis and became the central structural finding of the program. Subsequent targeted sweeps then systematically probed each remaining candidate: `targeted_sweep4` (n=35) showed pool_neutral_pct affects only cascade duration; `targeted_sweep5` (n=36) produced an exact null on all three user behavior parameters; `targeted_sweep3b` (n=4) eliminated economic friction parameters on the full network. `targeted_sweep6` (n=47 across two sub-sweeps) mapped the ideology × max_loss diagonal threshold and confirmed the economic override at econ≥0.82. `targeted_sweep7_esp` (n=18 across two regimes) established the Economic Self-Sustaining Point at econ≈0.74.

By the end of Phase 1, eleven parameters had been reduced to three active causal parameters: `economic_split`, `pool_committed_split`, and the `ideology_strength × max_loss_pct` interaction.

**Phase 2: LHS across active parameters and formal boundary fitting (lhs_2016_full_parameter, lhs_2016_6param, lhs_144_6param, plus verification targeted sweeps).**

With the active parameter set established, Phase 2 returned to LHS — now focused exclusively on the three to six causal parameters — to obtain unbiased estimates of the full decision boundary without one-at-a-time isolation constraints. `lhs_2016_full_parameter` (n=64, full network, 2016-block) confirmed pool_committed_split dominance via unbiased sampling (separation=0.275) and identified a hard threshold near committed_split≈0.25. The matched pair `lhs_2016_6param` (n=129, lite, 2016-block) and `lhs_144_6param` (n=130, lite, 144-block) extended the LHS to six parameters simultaneously, adding pool_profitability_threshold and solo_miner_hashrate to the non-causal list and enabling the regime comparison.

Phase 2 also included three verification targeted sweeps motivated by specific boundary questions the LHS had left unresolved: `hashrate_2016_verification` (n=18) tested whether hashrate non-causality held at 2016-block retarget and discovered the conditional danger window at econ=0.50; `econ_committed_2016_grid` (n=45) provided the 2016-block counterpart to targeted_sweep1 for direct regime comparison; `price_divergence_sensitivity_2016` (n=48) tested whether the ±20% price cap was binding.

Phase 2 concluded with formal boundary fitting across 566 full-network scenarios using Random Forest, logistic regression, and PRIM. The PRIM result defined the Phase 3 LHS target: the 51% region of 2016-block parameter space with exactly 50/50 outcomes — the transition zone where Phase 2 sampling density was insufficient to resolve the boundary's fine structure.

**Phase 3: Dense LHS within the transition zone (lhs_2016_phase3, lhs_2016_full_phase3).**

Phase 3 deployed LHS exclusively within the PRIM-defined uncertainty box — concentrating all sampling budget where outcomes were genuinely uncertain rather than spreading it across already-resolved clean-outcome regions. `lhs_2016_phase3` (n=300, lite network) and `lhs_2016_full_phase3` (n=292, full network) together produced the two-layer outcome structure finding: the hash-war outcome and economic adoption outcome are governed by different parameters and are largely decoupled. This finding could only emerge from dense LHS sampling within the transition zone — it is not visible in any individual targeted sweep and was not anticipated before Phase 3 analysis.

---

### 4.1.3 Data Quality and Validity

Of the 1,385 scenarios executed, 1,325 are included in quantitative analysis (95.7%). The 60 excluded scenarios consist of the role-name bug group (targeted_sweep3/5/6 lite, n=60). Targeted_sweep2b (n=20, partial) is excluded from quantitative but not qualitative analysis.

The valid dataset separates into two regime subsets used throughout the analysis:

| Regime | Full-network n | Lite-network n | Total valid |
|--------|:--------------:|:--------------:|:-----------:|
| 144-block | 268 | 130† | 398 |
| 2016-block | 298 + 292 | 129 + 300 | 1,019† |
| Other (baseline, sensitivity) | 129 | — | 129 |

*† Lite-network 144-block economic_split is subject to quantization artifact; excluded from regime comparison analysis (§4.4.4). Full-network n=268 used for all 144-block RF and logistic regression fits.*

The total valid scenario count for the boundary fitting analyses (§4.8) is 566 full-network scenarios (268 at 144-block, 298 at 2016-block), drawn from sweeps that used the full 60-node network without quantization artifacts. Phase 3 scenarios (n=300+292=592) are reported separately in §4.9–4.10.

---

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

---

## 4.3 Causal Parameters and Decision Boundary

After eliminating non-causal parameters (Section 4.2), fork outcomes are determined by three active parameters: `economic_split` (the fraction of Bitcoin economic activity — custody, transaction volume, exchange liquidity — denominated on the v27 fork), `pool_committed_split` (the fraction of non-neutral committed pool hashrate ideologically assigned to v27; the complement (1 − pool_committed_split) is v26-committed, reflecting v26's status as the incumbent chain that committed pools default to before a new fork activates), and the interaction of `pool_ideology_strength` and `pool_max_loss_pct` (jointly determining whether a committed pool will switch under economic pressure). This section maps the joint decision boundary across these three parameters and identifies the structural mechanisms governing each.

---

### 4.3.1 The Economic Threshold and Inversion Zone

Mapping fork outcomes across a 5×9 grid of economic_split × pool_committed_split (targeted_sweep1, n=45, hashrate_split fixed at 0.25, 144-block retarget) reveals a non-monotonic decision boundary with three distinct regimes (Table 4).

**Table 4. targeted_sweep1: fork outcomes across economic_split × pool_committed_split. v27 = v27_dominant; v26 = v26_dominant. Note the inversion at econ = 0.60–0.70 where the effect of pool_committed_split reverses sign.**

| econ \ commit | 0.20 | 0.30 | 0.38 | 0.43 | 0.47 | 0.52 | 0.58 | 0.65 | 0.75 |
|---------------|------|------|------|------|------|------|------|------|------|
| **econ = 0.35** | v26 | v26 | v26 | v26 | v26 | v26 | v26 | v26 | v26 |
| **econ = 0.50** | v26 | v27 | v27 | v27 | v27 | v27 | v27 | v27 | v27 |
| **econ = 0.60** | v27 | v26 | v26 | v26 | v26 | v26 | v26 | v26 | v26 |
| **econ = 0.70** | v27 | v26† | v26† | v26† | v26† | v26† | v26 | v26 | v26 |
| **econ = 0.82** | v27 | v27 | v27 | v27 | v27 | v27 | v27 | v27 | v27 |

*† Partial cascade: v27 retains ~34.7% final hashrate (AntPool partially defects from v26); 7 reorgs occur but v26 maintains dominance.*

Three regimes are visible. In the **weak economics regime** (economic_split ≤ 0.45), no cascade is possible and v26 wins across all pool configurations — the economic price signal is insufficient to move neutral pools or overcome committed v26 resistance. In the **strong economics regime** (economic_split ≥ 0.82), the price signal is sufficient to break even strongly committed v26 pools and v27 wins universally. The **intermediate regime** (economic_split 0.50–0.70) exhibits an inversion: outcomes are non-monotonic in pool_committed_split, with v27 winning only at the lowest committed level (0.20) and losing at all higher levels tested. This counter-intuitive result — where more pool commitment to v27 produces worse outcomes for v27 — is the central structural finding of the sweep program and is explained by the Foundry flip-point mechanism (Section 4.3.2).

The econ=0.70 row also reveals a partial cascade zone at commit=0.30–0.52: the outcome resolves to v26_dominant, but with active contest dynamics (7 reorgs, v27 retaining ~34.7% final hashrate). This is the transition boundary at 70% economic support — sufficient economic pressure to cause significant instability but not enough to complete the cascade against the committed v26 block.

---

### 4.3.2 The Foundry Flip-Point Mechanism

The inversion in Table 4 is caused by a structural feature of the pool distribution. With pool_neutral_pct fixed at 30%, the committed pool hashrate (70% of total) is partitioned into v27-preferring and v26-preferring assignment zones based on cumulative position. The largest pool, Foundry USA (representing approximately 30% of total mining hashrate), crosses from v26-preferring to v27-preferring assignment at a specific pool_committed_split value:

```
pool_committed_split × 0.70 > 0.15  →  pool_committed_split > 0.214
```

This threshold — approximately 0.214 — is the Foundry flip-point. Its effect is asymmetric and regime-dependent:

**Below the flip-point (commit ≤ 0.20):** Foundry is assigned v26-preferring ideology. At 60–70% economic support for v27, the v27 price premium exceeds Foundry's max_loss tolerance, making it impossible for Foundry to profitably stay on the v26 chain. Foundry is economically trapped on v27, providing the committed hashrate anchor that enables the price cascade. Result: v27 wins via economic pressure.

**Above the flip-point (commit ≥ 0.30):** Foundry shifts to v27-preferring ideology and holds the v27 chain. However, the reassignment simultaneously strengthens the opposing committed v26 block: AntPool (~18% total hashrate) + F2Pool (~15%) remain committed to v26, creating a v26-committed block of approximately 40% of total hashrate. This block is too large to break at 60–70% economic signal — the price gap of ~16% stays within the committed v26 pools' max_loss tolerance of 13.3% (ideology=0.51 × max_loss=0.26). Result: v26 maintains dominance despite holding the economic minority.

The governance implication is direct: the decisive question in a contentious fork is not whether v27 holds an aggregate economic majority, but which specific large pools are on which side and what their switching costs are. A 4-percentage-point shift in pool_committed_split — from 0.20 to 0.30 — converts Foundry from "economically trapped on v27" to "ideologically committed to v27 but surrounded by a now-strengthened v26 block," reversing the fork outcome entirely.

![Pool Assignment Schematic at Foundry Flip-Point](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_pool_assignment_schematic.png)

*Two-panel pool assignment schematic at the Foundry flip-point. Left: pool_committed_split=0.20 — Foundry is economically trapped and forced to switch to v27, leaving AntPool+F2Pool (~33%) as the v26 committed bloc. Right: pool_committed_split=0.30 — Foundry shifts to v27-committed; the v26 bloc (AntPool+F2Pool, ~33%) is now undiluted and sufficient to resist the cascade at moderate economic support levels (econ=0.60–0.70).*

The flip-point is confirmed by unbiased Latin Hypercube Sampling at 2016-block retarget (lhs_2016_full_parameter, n=64): all 12 v26_dominant cases have pool_committed_split ≤ 0.246, and all 52 v27_dominant cases have pool_committed_split ≥ 0.260. The gap between 0.247 and 0.259 is clean — no scenarios fall in this range — confirming the structural nature of the threshold rather than a smooth probability gradient.

---

### 4.3.3 Pool Ideology Threshold

The pool_committed_split threshold governs whether the cascade can begin, but a second threshold determines whether it completes. The interaction of `pool_ideology_strength` and `pool_max_loss_pct` — whose product defines a pool's maximum acceptable loss (`max_acceptable_loss = ideology_strength × max_loss_pct`) — gates whether committed v26 pools ultimately capitulate under economic pressure or hold indefinitely.

This was mapped on the full 60-node network at econ=0.78 (targeted_sweep6_pool_ideology_full, n=20, 144-block retarget). A diagonal threshold is confirmed: committed v26 pools survive economic pressure when ideology × max_loss ≳ 0.16–0.20; below this product, pools capitulate regardless of individual ideology or loss tolerance levels (Table 5a).

**Table 5a. targeted_sweep6_pool_ideology_full: v26 survival conditions at econ=0.78. Entry shows outcome; threshold marks where v26 pools hold vs. capitulate.**

| ideology_strength \ max_loss_pct | 0.05 | 0.15 | 0.25 | 0.35 | 0.45 |
|----------------------------------|------|------|------|------|------|
| **ideology = 0.2** | v27 | v27 | v27 | v27 | v27 |
| **ideology = 0.4** | v27 | v27 | v27 | v27 | **v26** |
| **ideology = 0.6** | v27 | v27 | v27 | **v26** | **v26** |
| **ideology = 0.8** | v27 | v27 | **v26** | **v26** | **v26** |

The diagonal threshold separates the table: v26 survives at ideology × max_loss ≳ 0.16–0.18 (the range between the highest v27-winning product and the lowest v26-surviving product). Neither parameter is sufficient individually — ideology=0.8 with max_loss=0.05 produces v27 dominance, as does ideology=0.2 with max_loss=0.45. The product is the operative quantity.

The direction of the effect is economic-context-dependent: the threshold governs **defender resilience**. At econ=0.78 where v27 holds the economic majority, a high ideology × max_loss product protects v26 from being swept by the price cascade. At economic conditions where v26 holds the majority, the same logic applies symmetrically to v27-committed pools. The threshold characterizes how much ideological commitment is required to resist economic pressure, regardless of which fork is the economic minority.

Both parameters have substantial individual correlations with outcomes in the full-network sweep (ideology_strength: r = −0.49; max_loss_pct: r = −0.62 at econ=0.78) but neither alone is predictive: pools need both the willingness to absorb losses (ideology) and the capacity to do so (loss tolerance). Near the diagonal, small changes in either parameter cross the line from "committed pools capitulate" to "committed pools hold indefinitely," making the product a binary switch governing the entire cascade pathway.

---

### 4.3.4 Economic Override

The ideology × max_loss threshold established at econ=0.78 does not extend to higher economic levels. A dedicated override sweep (targeted_sweep6_econ_override, n=27: ideology=[0.40, 0.60, 0.80] × max_loss=[0.25, 0.35, 0.45] × econ=[0.82, 0.90, 0.95], 144-block retarget) produced v27_dominant outcomes in all 27 scenarios. Above econ≈0.82, the price signal is strong enough to force capitulation regardless of ideology × max_loss product — the economic override is total and unconditional.

However, the ideology × max_loss product continues to determine cascade timing even when it cannot change the outcome. At ideology=0.80 + max_loss=0.35, the cascade takes 10,920 seconds — approximately three times the 2016-block retarget period and more than 15× the fastest observed cascade at the same economic level (~680s at ideology=0.80, max_loss=0.25). High ideology creates maximally resistant pools that delay but cannot prevent capitulation when economic pressure is sufficient.

The joint picture of Sections 4.3.3 and 4.3.4 is therefore: the ideology × max_loss product determines whether committed pools hold at moderate economic levels (econ=0.78, threshold at product ≳ 0.16–0.18), but above econ≈0.82 this threshold vanishes — all pool configurations resolve to v27 dominance, with the product governing only the speed of resolution.

---

### 4.3.5 Consolidated Threshold Summary

Table 5 summarizes all quantitative thresholds identified across the Phase 1 targeted sweep program. These thresholds represent the primary empirical contribution of Phase 1 and provide operational guidance for interpreting real-world fork scenarios.

**Table 5. Consolidated threshold estimates with confidence and data source.**

| Parameter | Threshold | Interpretation | Confidence / Source |
|-----------|-----------|----------------|---------------------|
| economic_split (lower bound) | ~0.45–0.50 | Below this, no cascade is possible regardless of other parameters | High — targeted_sweep1 (n=45) |
| economic_split (inversion onset) | ~0.55–0.60 | Inversion zone begins; pool_committed_split effect reverses sign | High — confirmed in targeted_sweep1 and targeted_sweep2 |
| economic_split (upper bound / ESP) | ~0.78–0.82 | Above this, economic signal overrides all pool configurations; v27 wins universally | High — targeted_sweep7_esp (n=18) confirms ESP=0.74; override confirmed at 0.82 in targeted_sweep6_econ_override (n=27) |
| pool_committed_split (Foundry flip-point) | ~0.214 | Crossing this boundary reassigns Foundry (~30% hashrate) and inverts outcomes at econ=0.60–0.70; confirmed as hard threshold via unbiased LHS | High — targeted_sweep1 mechanism analysis; confirmed lhs_2016_full_parameter (n=64) |
| pool_ideology_strength × pool_max_loss_pct (product) | ~0.16–0.20 | Below this product, committed pools capitulate; above it, v26 pools survive at econ=0.78; threshold vanishes at econ≥0.82 | High — targeted_sweep6_pool_ideology_full (n=20) + targeted_sweep6_econ_override (n=27) |
| hashrate_split | No independent effect | Appears important in exploratory sweeps but is a LHS sampling confound; non-causal at econ≥0.60 | High — targeted_sweep2 (n=42); hashrate_2016_verification (n=18) |
| All user behavior parameters | No independent effect | User nodes lack sufficient economic weight or hashrate to shift outcomes under any tested configuration | High — targeted_sweep5 (n=36); User-PRIM analysis (n=598, §4.11) |

For a protocol developer or governance actor, these thresholds translate to three concrete monitoring questions during a contentious fork:

1. **Is economic_split above ~0.50?** If not, the upgrading fork cannot win regardless of mining support or pool ideology.
2. **Is pool_committed_split above or below ~0.214?** This determines whether the largest pool (Foundry-class, ~30% hashrate) is economically trapped on the upgrading chain or ideologically committed to it — a distinction that reverses the outcome at moderate economic levels.
3. **Is economic_split above ~0.82?** If so, pool ideology and commitment structure become irrelevant to the final outcome, though they continue to determine how long resolution takes.

---

---

## 4.4 Regime Comparison: The Causal Rank Reversal Between 144-Block and 2016-Block Retarget

The preceding sections established the causal structure of fork outcomes at the 2016-block retarget interval. A second, equally important finding emerges from comparing this structure to the 144-block regime: the dominant causal parameter changes entirely depending on which retarget interval is active. `economic_split` controls outcomes at 144-block; `pool_committed_split` controls them at 2016-block. The same fork, with identical actor configurations, produces different outcome logic depending only on how quickly the minority chain's difficulty adjusts.

---

### 4.4.1 The Rank Reversal

Random Forest classification was fitted separately on the full-network 144-block dataset (n=268) and the full-network 2016-block dataset (n=298), using the same four active parameters in both cases. Table 7 (reproduced from Section 4.8) reports the results.

**Table 7. Random Forest feature importance by retarget regime.**

| Parameter | 144-block (n=268) | 2016-block (n=298) | Rank change |
|-----------|:-----------------:|:------------------:|:-----------:|
| `economic_split` | **77.2%** | 20.2% | #1 → #2 |
| `pool_committed_split` | 11.3% | **52.8%** | #2 → #1 |
| `pool_max_loss_pct` | 5.5% | 17.1% | #4 → #3 |
| `pool_ideology_strength` | 6.0% | 9.9% | #3 → #4 |
| **RF OOB accuracy** | **80.0%** | **83.2%** | |

The reversal is not marginal. At 144-block, `economic_split` accounts for 77.2% of predictive importance — approximately four times the contribution of the next-best parameter (`pool_committed_split` at 11.3%). At 2016-block, `pool_committed_split` displaces it entirely, accounting for 52.8% while `economic_split` falls to 20.2%. The two parameters swap rank positions, and neither holds even a plurality in the other's dominant regime.

Two secondary observations follow from Table 7. First, the 2016-block outcomes are *more predictable* — OOB accuracy is 83.2% versus 80.0% at 144-block. A longer retarget window creates harder, more deterministic constraints around pool commitment structure; the RF extracts a cleaner signal accordingly. Second, `pool_max_loss_pct` rises from near-zero importance at 144-block (5.5%) to a meaningful secondary factor at 2016-block (17.1%). When the retarget interval is long enough that committed pools must sustain losses through an entire 2016-block epoch, how much loss they can absorb before switching becomes an independent causal factor in the outcome.

---

### 4.4.2 Mechanism: The Survival Window

The rank reversal is a consequence of the Difficulty Adjustment Survival Window — the time between fork inception and the minority chain's first difficulty retarget. During this window, the minority chain is mining at reduced hashrate against full difficulty, producing fewer blocks per hour than the majority chain. Once the retarget fires, difficulty drops proportionally, equalizing block production rates regardless of the starting hashrate split.

The survival window length is a direct function of the retarget interval:

- **144-block retarget:** Approximately 24 hours at normal block rates; under minority hashrate conditions, the window may compress to 8–16 hours depending on the initial hashrate deficit. The economic price signal — which responds to exchange activity, custodial weight migration, and fee market dynamics — operates on the same timescale. The price cascade *resolves before the retarget fires*, making economic alignment the binding constraint on which fork wins.

- **2016-block retarget:** Approximately 14 days at normal block rates; under minority conditions, the window extends further. The economic price signal still fires within hours or days, but the committed pool structure must hold through weeks of sustained losses before any difficulty relief arrives. The binding constraint is whether committed pools have sufficient loss tolerance to absorb the full epoch — making `pool_committed_split` and the `ideology_strength × max_loss_pct` interaction the operative parameters.

The 144-block regime therefore operates as an *economic auction*: whichever fork retains sufficient price support wins because the minority chain's survival window is short enough that economic weight alone determines cascade direction before pool ideology can be tested to exhaustion. The 2016-block regime operates as an *endurance contest*: economic signals still operate, but pool ideological commitment — specifically the product of how many committed pools are on which side and how long they can sustain losses — determines whether the minority chain survives long enough to reach the difficulty adjustment that equalizes competitive dynamics.

---

### 4.4.3 The 144-Block Economic Threshold

At 144-block, the decision boundary is approximately one-dimensional. The targeted_sweep1 grid (Table 4, Section 4.3.1) shows clean horizontal bands: `economic_split` at ≤0.45 always produces v26_dominant outcomes; at ≥0.82 always produces v27_dominant outcomes; the transition zone spans 0.50–0.70, where pool configuration has some secondary influence. The 11.3% RF importance for `pool_committed_split` at 144-block reflects only this secondary influence within the transition band — outside that band, the economic threshold operates as a near-binary switch.

This one-dimensional structure is also visible in the 144-block logistic regression: cross-validated accuracy is 59.8% — only 10 percentage points above chance (50%), and substantially weaker than the 77.5% achieved at 2016-block. The logistic model cannot usefully fit the 144-block boundary because the boundary is approximately a single step function of `economic_split` that does not benefit from the interaction terms the model includes. For 144-block inference, the RF feature importance scores are more informative than any regression-derived decision surface.

---

### 4.4.4 Quantization Caveat for Lite-Network 144-Block Data

One important methodological limitation applies specifically to 144-block sweeps conducted on the lite network (25-node configurations). On the lite network, economic nodes are assigned in whole-number increments: with 2 economic nodes per partition, the network has either 0, 1, or 2 economic nodes supporting v27 — corresponding to economic weights of approximately 0%, 50%, and 100% respectively. Economic weight is not continuous on the lite network; it is effectively a 3-level discrete variable.

This quantization means that the full-range economic_split variation sampled in LHS sweeps on the lite network (`lhs_144_6param`, n=129) does not correspond to genuine variation in economic weight — scenarios with `economic_split` anywhere in [0.30, 0.80] are all assigned the same 1 economic node on v27, producing identical economic dynamics. For this reason, `lhs_144_6param` is excluded from the 144-block RF fit (the 268-scenario dataset uses full-network sweeps only), and any 144-block economic_split effect observed on lite-network data should not be interpreted as a real finding.

All 144-block conclusions in this section and in Section 4.8 are drawn exclusively from full 60-node network scenarios where economic weight assignment is genuinely continuous.

---

### 4.4.5 Regime Dependence as a Governance Finding

The rank reversal has direct implications for Bitcoin governance analysis. The retarget interval is a fixed protocol parameter — Bitcoin's 2016-block (~14-day) retarget is the operationally relevant regime for any real contentious fork. Under this regime, the dominant causal parameter is not economic weight but pool committed structure: specifically, whether committed pool hashrate exceeds approximately 0.296 of total hashrate (Phase 3 transition zone threshold, Section 4.9).

This finding reframes the question governance actors should be asking during a contentious fork. The conventional framing — "which fork has more economic support?" — is the dominant question at short retarget intervals where economic signals resolve the fork before pool ideology is tested. At the 2016-block interval that governs real Bitcoin forks, the more consequential question is: "which large pools are committed to which fork, and can they sustain those losses through a full 14-day epoch?" Economic support remains relevant as a secondary amplifier and as the mechanism that forces pool switching once committed hashrate falls short — but it is not the first-order signal.

The two regimes are compared in Table 10.

**Table 10. Regime comparison summary.**

| Dimension | 144-block retarget | 2016-block retarget |
|-----------|-------------------|---------------------|
| Dominant parameter | `economic_split` (77.2% RF importance) | `pool_committed_split` (52.8% RF importance) |
| Secondary parameter | `pool_committed_split` (11.3%) | `economic_split` (20.2%) |
| Decision boundary shape | ~1-dimensional (economic threshold) | 2-dimensional (E×C interaction dominant) |
| Outcome predictability (OOB accuracy) | 80.0% | 83.2% |
| LR model strength (CV accuracy) | 59.8% — unreliable | 77.5% ± 2.9% |
| PRIM boundary resolution | Near-degenerate (92.5% support after 3 steps) | Well-resolved (51.0% uncertainty box) |
| Contentiousness (mean) | 0.132 | 0.271 (2.1× higher) |
| Governing mechanism | Economic price cascade resolves before retarget | Pool endurance through epoch before retarget |
| Primary governance question | "Which fork has economic majority?" | "Which large pools can sustain losses for 14 days?" |

The higher contentiousness at 2016-block (2.1×) reflects that longer survival windows allow more extended competitive mining, more chain reorganizations, and larger economic uncertainty periods before resolution. The same fork is approximately twice as disruptive under the operationally relevant retarget regime than under the shorter one.

---

---

## 4.5 The Difficulty Adjustment Survival Window

The non-causality of hashrate in fork outcomes — the central surprising result of Phase 1 — does not arise from hashrate being unimportant to mining economics. It arises from a specific mechanism in Bitcoin's difficulty adjustment algorithm that neutralizes the starting hashrate advantage of the dominant chain before the economic price cascade resolves. This mechanism, which we term the **Difficulty Adjustment Survival Window**, is the unifying explanation for findings across Sections 4.2, 4.3, and 4.4, and produces an additional counter-intuitive result: acquiring *moderate* hashrate support for a minority fork can be strictly worse than acquiring none at all.

---

### 4.5.1 The Mechanism

When a contentious fork creates two competing chains, the minority chain begins mining at a hashrate deficit relative to its full pre-fork difficulty target. It produces blocks more slowly than the majority chain. However, Bitcoin's difficulty adjustment algorithm periodically recalibrates each chain's target independently: when a chain's block production rate falls below target, difficulty adjusts downward in proportion to the shortfall, restoring the target block rate regardless of how much hashrate the chain retains.

The **survival window** is the period between fork inception and the minority chain's first difficulty retarget. During this window:

1. The minority chain mines slowly at full pre-fork difficulty.
2. The majority chain builds a chain-length lead.
3. Miners on the minority chain accumulate opportunity costs (mining at lower revenue than they could achieve on the majority chain).
4. Economic price signals respond to block production differentials, diverging in favor of the majority chain.

When the retarget fires, the minority chain's difficulty drops proportionally to its hashrate deficit. Block production equalizes — both chains now produce blocks at approximately the target rate regardless of their relative hashrate. From this point forward, the *revenue per block* on each chain depends on price and fees, not on hashrate. The starting hashrate advantage of the majority chain has been neutralized.

The critical observation is that the survival window must close — the retarget must fire — before the economic cascade can fully resolve. If the price cascade completes first, the fork outcome is determined by economic dynamics. If the retarget fires first, the minority chain stabilizes its block rate and the economic dynamics then operate on a more level playing field. In either case, the initial hashrate split does not determine the winner; it only influences the timing and trajectory of the resolution.

---

### 4.5.2 Window Length as a Function of Retarget Interval

The survival window length is directly proportional to the retarget interval and inversely proportional to the minority chain's block production rate during the window.

At **144-block retarget**, the window spans approximately 24 hours at normal block rates. Under a 25% minority hashrate (v27 holding 25% of total), the minority chain produces blocks at roughly 25% of the target rate — six times slower than the majority chain. At this rate, the 144-block retarget epoch takes approximately 144 × (10 minutes / 0.25) ≈ 96 hours to complete. However, in practice the window effectively closes when the price cascade resolves — typically within hours of fork inception at the economic levels tested. The survival window at 144-block is short relative to the cascade timescale, meaning retarget relief arrives quickly enough that pool losses rarely accumulate to a forcing threshold.

At **2016-block retarget**, the window spans approximately 14 days at normal block rates. Under minority hashrate conditions, it extends further: a 25% minority hashrate chain takes approximately 2016 × (10 min / 0.25) ≈ 56 days in real time before its difficulty adjusts. Even in the accelerated simulation environment (2-second intervals, 13,000-second runs), the 2016-block window is wide enough that pool opportunity costs accumulate substantially before any retarget relief arrives. Committed pools must sustain losses through the entire epoch — and whether they can do so is governed by the `ideology_strength × max_loss_pct` product established in Section 4.3.3.

This is the mechanistic basis for the causal rank reversal documented in Section 4.4: the survival window length determines which signal — economic price dynamics or pool ideological endurance — becomes the binding constraint on the fork outcome.

---

### 4.5.3 The Hashrate Parity Danger Window

The survival window mechanism produces a second counter-intuitive result at the 2016-block retarget interval and economic parity (econ=0.50): intermediate v27 hashrate (35–45%) is strictly worse for v27 than either low (15–25%) or high (55–65%) hashrate. Table 3b (reproduced from §4.2.1) shows this pattern.

**Table 3b. hashrate_2016_verification results at econ=0.50 (2016-block retarget). Non-monotonic pattern: intermediate hashrate (35–45%) produces v26_dominant outcomes while lower (15–25%) and higher (55–65%) hashrate produce persistent splits.**

| hash \ econ | econ = 0.50 | econ = 0.60 | econ = 0.70 |
|-------------|:-----------:|:-----------:|:-----------:|
| hash = 0.15 | SPLIT | v27 | v27 |
| hash = 0.25 | SPLIT | SPLIT† | v27 |
| hash = 0.35 | **v26** | v27 | v27 |
| hash = 0.45 | **v26** | v27 | v27 |
| hash = 0.55 | SPLIT | v27 | v27 |
| hash = 0.65 | SPLIT | v27 | v27 |

*† Anomalous: 62% economic support produces a persistent split at hash=0.25. Adjacent econ=0.70 cell resolves cleanly.*

The mechanism operates through Foundry USA's loss accumulation at the 2016-block interval. With `pool_committed_split` fixed at 0.50 and `pool_ideology_strength=0.51`, `pool_max_loss_pct=0.26`, Foundry's maximum acceptable loss is `0.51 × 0.26 = 13.3%` of potential revenue.

At **intermediate v27 hashrate (35–45%):** The v26 chain builds a moderate chain-length lead quickly — fast enough that Foundry's accumulated mining loss on v27 reaches the 13.3% tolerance threshold within approximately one retarget cycle (~3,600 simulation seconds). Pool decision logs confirm the forced-switch event: *"Forced switch: loss 12.0% exceeds tolerance 12.0%."* Once Foundry crosses the threshold and exits v27, the remaining v27 hashrate collapses. The post-switch v26 profitability premium grows to 58%, trapping all subsequent neutral pool decisions on v26. The outcome is v26_dominant.

At **low v27 hashrate (15–25%):** The v26 chain's lead grows slowly because v26 mining itself is only slightly faster than target rate (it holds 75–85% of total hashrate, not dramatically above target at these economic levels). Foundry's loss accumulates at a slower rate, staying below the 13.3% threshold through the 13,000-second simulation window. Neither chain achieves dominance — the outcome is a persistent split.

At **high v27 hashrate (55–65%):** The v26 chain has only 35–45% of total hashrate — itself near or below the minority zone. The competitive dynamics are more symmetric. Neutral pool migration partially offsets early v26 hashrate advantage. Foundry's losses again remain below threshold. The outcome is again a persistent split.

The danger window exists in the intermediate zone because it is precisely fast enough to accumulate decisive losses against Foundry before the simulation ends, but not fast enough that Foundry's preferred chain (v27) can resist the growing v26 lead. At low hashrate, the accumulation is too slow to cross the threshold; at high hashrate, the accumulation is slow enough or offset enough by neutral pool behavior that the threshold is never reached in the simulation window.

---

### 4.5.4 Regime Dependence of the Danger Window

The hashrate parity danger window exists only at the 2016-block retarget interval. At 144-block retarget, the same hashrate levels tested in targeted_sweep2 (Table 3, §4.2.1) produce identical outcomes across all six hashrate values — the survival window closes before loss accumulation reaches any committed pool's tolerance threshold. The danger window is a 2016-block phenomenon, driven specifically by the long epoch during which committed pools absorb losses without any retarget relief.

This regime-dependence adds a further dimension to the causal rank reversal finding of Section 4.4. Not only does the dominant causal parameter switch between regimes — at 2016-block, the survival window is long enough to create a non-monotonic hazard zone in hashrate space that does not exist at 144-block. A governance actor relying on 144-block intuitions about hashrate neutrality could incorrectly conclude that acquiring moderate minority-fork hashrate is harmless. Under 2016-block dynamics, it can actively invert the outcome.

---

### 4.5.5 Governance Implications

The survival window mechanism has three concrete implications for Bitcoin governance actors during a contentious fork.

**First**, hashrate acquisition strategy is non-linear at 2016-block retarget and economic parity. Acquiring minority hashrate in the 35–45% range without sufficient economic support (econ ≥ 0.55) is worse than acquiring either less hashrate or more. The governance question is not "how much hashrate can we acquire?" but "is our economic support sufficient to avoid the parity danger window?"

**Second**, the retarget interval is the protocol parameter that determines which signal — economic alignment or pool ideological endurance — governs the fork outcome. This is not a tunable parameter for governance actors; it is fixed at 2016 blocks in Bitcoin. But it means that experience from faster-retarget chains (Bitcoin Cash's Emergency Difficulty Adjustment, for example) does not transfer directly to Bitcoin governance scenarios. The economic-dominant intuitions from shorter retarget regimes are systematically misleading for the 2016-block world.

**Third**, the survival window provides a natural monitoring indicator during a real contentious fork. The question "has the minority chain reached its first retarget epoch?" marks a qualitative transition: before the retarget, committed pools are accumulating losses against full difficulty; after it, the playing field levels and the remaining question is purely economic. If the fork has not resolved before the minority chain's first retarget, the dynamics shift and a fork that appeared to be dying may stabilize.

---

---

## 4.6 Fork Dynamics and Cascade Signatures

The preceding sections characterize fork outcomes in terms of which fork wins and which parameters determine that result. This section examines *how* forks develop: the time-series signatures of cascade events, the price divergence patterns that drive pool switching, and the governance risk structure of the inversion zone.

---

### 4.6.1 Clean Outcomes vs. Cascade Events

Fork outcomes separate into two qualitatively distinct dynamic types based on the relationship between economic weight and pool commitment at the start of the simulation.

**Clean outcomes** occur when one fork dominates both economic and hashrate dimensions simultaneously — either econ_split is above the economic override threshold (~0.82) or below the cascade floor (~0.45), or pool_committed_split is far from the inversion boundary. In clean outcomes, the losing fork loses hashrate rapidly with zero or minimal reorg events. Neutral pools follow the economic signal immediately; committed pools on the losing side exhaust their loss tolerance within the first retarget epoch without generating competitive dynamics. The simulation resolves in one direction without meaningful contest.

**Cascade events** occur when the economic cascade mechanism is active — economic majority overcoming an initial hashrate deficit, or committed pool ideology sustaining a minority chain long enough for the price signal to develop. Cascade scenarios exhibit a characteristic signature: elevated reorg counts (typically 5–13 reorgs), a period of competitive mining on both chains, followed by rapid hashrate consolidation on the winning fork as neutral pools respond to the completed price divergence. In targeted sweep data, scenarios with 5 or more reorgs show an 86% v27 win rate when economic_split is above the cascade threshold, reflecting the systematic relationship between cascade activity and economic majority outcome.

The reverse cascade is the most striking single data point in the sweep program: sweep_0007 (starting hashrate = 90% v27, economic_split = 7% v27) results in v26 winning after 7 reorgs. A fork beginning with 90% of the network hashrate on the new-rules chain is nevertheless defeated when 93% of economic activity remains on the old-rules chain. This scenario directly demonstrates that hashrate majority is neither necessary nor sufficient for fork victory — the economic signal drives all neutral pools off the majority-hashrate chain within the simulation window.

**Symmetric cascade duration.** In the unbiased full-network LHS sample (n=532; lite-network, sigmoid oracle, and Phase 3 targeted sweeps excluded), v27-dominant and v26-dominant cascades share an identical median of 7 reorgs. Earlier analysis of biased samples that oversampled the inversion zone showed a lower v26 median (4 reorgs), suggesting v26 cascades resolve faster — an artifact of including Phase 3 scenarios where v26 wins were concentrated near the Foundry flip-point under short, ideology-limited cascades. On the unbiased data, cascade duration is symmetric: the number of reorgs required to resolve a fork is determined by the `ideology × max_loss` product of the *losing side's* committed pools, not by which fork ultimately wins. A highly committed v26 pool bloc delays the v27 cascade as effectively as a highly committed v27 pool bloc delays the v26 cascade. The winning fork's economic advantage accelerates the cascade only insofar as it increases the revenue loss rate on the losing side — a symmetric pressure regardless of direction.

![Reorg Event Distribution](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_reorg_distribution.png)
**Figure X — Reorg Event Distribution by Outcome Category.** Panel A shows clean outcomes (zero reorg events, no pool switching): v27-dominant clean wins are rare (n=3); v26-dominant clean wins are more common (n=23), occurring when economic support is too low to initiate any cascade. Panel B shows the reorg count distribution for all scenarios with at least one reorg event. v27-dominant cascades (n=296) show a median of 7 reorgs, reflecting a two-stage cascade structure in which initial neutral pool drift and subsequent committed pool capitulation each contribute a cluster of activity. v26-dominant cascades (n=196) share the same median of 7 reorgs, reflecting symmetric cascade dynamics when the economic majority is on the v26 side. Contested outcomes (n=10) are sparse and low-count (all ≤7 reorgs), consistent with their characterization as parameter-locked stalemates where high ideology and loss tolerance sustain parallel mining without forcing capitulation. Source: n=532 valid full 60-node network scenarios; lite-network, sigmoid oracle, and Phase 3 LHS sweeps excluded. See `docs/figures/fig_reorg_distribution.png`.

---

### 4.6.2 Price Divergence Patterns

Token prices for each fork diverge from the common base price ($60,000) as economic nodes shift their transaction routing and custodial commitment. The magnitude and direction of divergence varies predictably across outcome categories:

- **Decisive v27 wins (high econ, high committed_split):** winning fork reaches $64,000–$72,000; losing fork falls to $48,000–$56,000. Divergence develops quickly and sustains.
- **Decisive v26 wins:** symmetric price pattern with directions reversed.
- **Contested outcomes:** both forks hover near $57,000–$62,000 throughout. Fewer economic nodes have switched, price divergence never exceeds the switching threshold of remaining nodes, and the fork persists without resolution.

Price divergence magnitude correlates with cascade completeness: longer stalemates produce less divergence because fewer economic nodes have switched. This relationship is bidirectional — less divergence means fewer nodes cross their switching threshold, which means less divergence, producing a self-reinforcing equilibrium in contested scenarios.

![Price Divergence Time-Series](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_price_divergence_timeseries.png)
**Figure Y — Price Divergence Time-Series by Outcome Category.** Each column shows one representative scenario; top row shows the full simulation; bottom row zooms to the first 2,000 blocks to show initial switching dynamics. Blue = v27 price, red = v26 price, dotted line = base price ($60k). Dashed vertical lines mark 2016-block retarget epochs. X-axis in simulation blocks (2-second interval); see §4.6.3 for real-world translation and its limits.

*Left column — Clean Win (v26-dominant):* `econ=0.28`, `pool_committed=0.18`, 0 reorg events. Price separation is immediate — v26 rises to $65k, v27 falls to $55k within the first ~100 blocks. The simulation terminates at ~900 blocks when v27 loses all block production. The zoomed panel (first 200 blocks) confirms there is no competitive phase: prices diverge monotonically from the first block with no reversion.

*Center column — Cascade Win (v27-dominant):* `econ=0.60`, `pool_committed=0.48`, 10 reorg events. The zoomed panel shows the cascade structure clearly: prices hold near $60k for the first ~500 blocks while committed pools sustain both chains, then diverge sharply between blocks 500–1,500 as neutral pool defection accelerates. By block 2,000 the divergence is substantially complete. The full panel shows the final settled state — v27 at $71k, v26 at $48k — sustained for the remaining ~4,500 blocks after cascade completion.

*Right column — Contested Outcome:* `econ=0.60`, `pool_committed=0.43`, 5 reorg events. Both prices remain within 5% of $60k for the full 6,500-block simulation window. The zoomed panel shows early reorg activity produces minor price oscillation but no sustained divergence. Neither chain accumulates enough price advantage to push neutral pools decisively — the self-reinforcing equilibrium described above is visible: insufficient divergence → no additional pool switching → continued insufficient divergence. Final prices: v27 $61k, v26 $58k.

Source: individual scenario time-series from `realistic_sweep2/sweep_0041`, `lhs_2016_full_parameter/sweep_0002`, and `econ_committed_2016_grid/sweep_0021`. See `docs/figures/fig_price_divergence_timeseries.png`.

**Price divergence cap sensitivity.** The sensitivity of outcomes to the model's ±20% price divergence cap was tested via the `price_divergence_sensitivity_2016` sweep, running the same 12-scenario parameter grid at cap levels of ±10%, ±20%, ±30%, and ±40% (n=48 total). Table 11 summarizes the results.

**Table 11. price_divergence_sensitivity_2016: outcomes across price cap levels for fixed 12-scenario grid (2016-block retarget).**

| Cap level | v27 wins | v26 wins | Contested | Key finding |
|-----------|:--------:|:--------:|:---------:|-------------|
| ±10% | 5 | 3 | 4 | Cap binds: natural equilibrium gap is 13–16% in high-parameter scenarios; suppressing it to ±10% reduces pool loss pressure, enabling 3 v26 wins |
| ±20% | 3 | 0 | 9 | Cap no longer binds; stalled pool dynamics dominate |
| ±30% | 0 | 0 | 12 | Maximum stall: pool commitment insufficient to complete cascade at any cap level |
| ±40% | 8 | 0 | 4 | v27 wins via hardware-speed artifact: fast-server scenarios completed 2016-block retarget epoch within run window; slow-hardware scenarios remained contested |

The ±10% level is the only cap at which the price bound is causally active: natural price equilibria in these high-parameter scenarios would reach 13–16% divergence, so capping at ±10% artificially suppresses pool loss pressure and permits 3 v26 wins that would not occur at the correct cap level. Above ±10%, the cap is slack and outcomes are governed entirely by pool and economic dynamics.

The ±30% result isolates the pool commitment regime: in this 12-scenario grid, pool ideology and loss tolerance parameters are structurally insufficient to complete the cascade regardless of how large the price signal is allowed to grow. Increasing the cap further (±40%) does not change the dynamics — what changes outcomes at ±40% is a hardware timing artifact, not pool behavior. The contested zone in this grid is parameter-locked, not cap-locked.

Economic node switching behavior is invariant across all cap levels: 100% no-switch at every tested cap. The ideology/inertia dead zone permanently locks economic nodes in these scenarios regardless of price signal magnitude, confirming that the contested and v26-dominant outcomes in the inversion zone are not artifacts of the ±20% cap choice.

**Price floor from static custody (model limitation).** The cap sensitivity analysis characterizes the upper bound of price divergence; a complementary constraint operates at the lower bound. The price oracle's `economic_weight` component is driven by static `custody_btc` assignments and does not respond to chain liveness — a chain producing zero blocks retains its full custody-based price floor. In early sweep data (sweep10, econ=0.70, 144-block), a chain with 0% hashrate for ~300 blocks (600 simulation-seconds at the 2-second block interval) experienced only a ~6% price drop rather than the rapid collapse a fully dynamic model would produce. The practical consequence is that the model understates minority-chain price collapse in ghost-town scenarios: when one chain loses all block production, the opposing chain's price advantage builds more slowly than real market dynamics would generate, slightly delaying neutral pool migration and making clean-outcome thresholds marginally harder to cross. This conservative bias is consistent with the ±20% cap finding above — both model choices err toward understating the speed of price resolution rather than overstating it. The full bias assessment is documented in `assumptions.md §2.8`.

---

### 4.6.3 Cascade Timing and the Economic Lag

Cascade timing — the elapsed simulation time from fork inception to pool hashrate consolidation — varies substantially across scenarios. The simulation runs at a 2-second block interval (`--interval 2`), so all timing figures below are in simulation-seconds; the primary unit for real-world translation is **blocks and retarget epochs**, not wall-clock time (see caveat below). The primary determinant of cascade duration is the `pool_ideology_strength × pool_max_loss_pct` product (Section 4.3.3), not the economic or hashrate parameters:

- **Standard cascades** (low ideology × max_loss product): complete in approximately 700 simulation-seconds (~350 blocks) from fork inception — well within the first retarget epoch. Committed v26 pools exhaust their loss tolerance quickly, neutral pools follow the price signal, and the fork resolves without reaching difficulty adjustment.
- **High-resistance cascades** (ideology=0.80 + max_loss=0.35): complete in 10,920 simulation-seconds (~5,460 blocks) — approximately 15× longer and spanning nearly three 2016-block retarget epochs. Committed pools delay capitulation without changing the ultimate outcome when econ_split is above the economic override threshold (~0.82).

This range — ~350 to ~5,460 blocks — represents the window of maximum real-world disruption regardless of block interval. During this window, two competing chains are actively mining, exchanges face deposit/withdrawal decisions under price uncertainty, and users cannot be confident which chain their transactions will persist on.

**The economic lag** is the additional delay between pool cascade completion and full economic node migration. In Phase 3 full-switch cases (n=28), the pool cascade fires first at mean t=3,298 simulation-seconds (~1,649 blocks), with economic nodes responding approximately 3,506 simulation-seconds (~1,753 blocks) later (mean econ switch time = 6,804 simulation-seconds, ~3,402 blocks). The price gap magnitude at the time of economic switching is 41–47% in full-switch cases, versus 12–18% in no-switch cases — the gap must reach and sustain the higher range to cross economic node switching thresholds.

At 144-block retarget, the timing pattern inverts: the pool cascade completes earlier (~1,815 simulation-seconds, ~908 blocks) because the shorter survival window accelerates loss accumulation, but the economic lag extends to ~4,300–5,000 simulation-seconds (~2,150–2,500 blocks) because economic nodes process the price signal gradually over the remaining simulation window. Full-switch rates are higher at 144-block (55% vs. 46% in lhs_2016_6param), but the lag between pool resolution and economic adoption is 2–3× longer in block count.

**The econ lag as an observable signal — and its limits.** The model identifies a consistent structural sequence: pool hashrate consolidation precedes economic node migration, with a lag of approximately 1,750 blocks at 2016-block retarget. The qualitative signal — hashrate resolves first, institutional economic adoption follows — is a testable real-world observable: pool attribution data on-chain provides visibility into hashrate consolidation, while exchange deposit/withdrawal volumes and UTXO migration patterns provide visibility into economic adoption. If one chain achieves clear hashrate dominance but exchange-level activity has not migrated, the fork has completed its mechanistic phase but not its institutional adoption phase. The absence of economic migration after hashrate consolidation is a signal that the price gap was insufficient to trigger full adoption — placing the scenario in the no-switch regime regardless of the hashrate outcome.

**Important caveat on real-world timing.** The block-count translation (~1,750 blocks ≈ 12 real days at 10-minute block targets) is mechanistically valid for the model's block-driven components — pool revenue loss, difficulty retarget, and price divergence accumulation all scale correctly with block count. However, the human behavioral components of a real fork do not scale with block production. Pool operators respond to revenue losses on human decision timescales involving internal deliberation, legal review, and operational coordination that may be faster or slower than the block-count equivalent. Exchange listing decisions and custodial fork handling involve compliance review and counterparty agreement that operate on institutional timescales — potentially weeks to months — independent of how many blocks either chain has produced. The model treats these as algorithmically responsive to price signal magnitude; real institutions are not. The econ lag finding should therefore be understood as characterizing the *structure* of fork resolution (the sequencing of pool then economic adoption) rather than as a quantitative prediction of real-world timing. The specific block-count estimates carry substantial uncertainty when applied beyond the model's behavioral assumptions.

---

### 4.6.4 The Inversion Zone as Governance Risk

The inversion zone — economic_split ∈ [0.55, 0.78], pool_committed_split ∈ [0.30, 0.75] — represents a qualitatively distinct risk regime beyond what binary outcome classification captures. Within this zone, the fork outcome is determined not by aggregate economic or hashrate majority but by which side controls the structurally pivotal pool — Foundry USA in the modeled 2026 Bitcoin landscape. This creates three governance-specific hazards.

**Discontinuous outcome reversals.** A 4-percentage-point shift in pool_committed_split — from 0.20 to 0.30, crossing the ~0.214 Foundry flip-point — reverses the fork outcome entirely at econ=0.60–0.70. No continuous signal tracks this transition: aggregate hashrate shares on each side shift gradually while the underlying pivotal pool assignment changes discontinuously. A governance actor monitoring hashrate totals rather than per-pool ideological positions will not observe the approaching reversal.

**Misleading aggregate statistics.** Within the inversion zone, the side with higher aggregate economic support can lose, and the side with higher aggregate hashrate can lose, simultaneously. The winning condition is possession of the pivotal pool's commitment — a structural property invisible to aggregate monitoring. This is the practical implication of the E×C synergy term (+1.231) in the logistic regression: the two parameters are not independently predictive, so neither economic weight nor committed hashrate alone provides reliable forward guidance on outcome within this zone.

**Extended contentiousness.** Inversion zone scenarios have higher mean contentiousness than clean-outcome scenarios. The contested cluster in Phase 3 (Section 4.9) is specifically characterized by high ideology × max_loss parameters within the inversion zone's economic and committed-split ranges. These are the scenarios where pools are committed enough to sustain a genuine fork without being forced out, and loss-tolerant enough that economic pressure alone cannot complete the cascade. The result is a sustained dual-chain situation — the operationally riskiest outcome for exchange infrastructure, wallet software, and users attempting to transact.

**Natural frequency of contested outcomes.** The structural rarity of contested outcomes deserves explicit note. In the unbiased full-network LHS sample (n=532; same exclusion set as the figure), only n=10 scenarios produce a contested outcome — roughly 2% of parameter space. The Phase 3 targeted sweeps, which were designed to oversample the inversion zone, produced n=42 contested scenarios in a smaller sample; that count reflects deliberate oversampling, not natural frequency. The low natural rate follows directly from the model's dynamics: the price oracle exerts continuous and cumulative pressure on pool revenue, so contested requires three conditions to hold simultaneously — `economic_split` in [0.55, 0.78] (neither side has clean economic dominance), `pool_committed_split` near the Foundry flip-point (neither side has clear committed pool control), and `ideology × max_loss` high enough that committed pools survive the full simulation duration (13,000 simulation-seconds, ~6,500 blocks) without capitulating. This conjunction is genuinely rare in an unbiased parameter sample. The governance implication is two-sided: contested is the highest-risk outcome operationally, but reaching it requires a specific and observable configuration of pool ideology and economic split that would not arise accidentally.

---

## 4.7 Implications for Real-World Fork Assessment

The findings above suggest a structured reassessment of how fork risk is conventionally analyzed. The standard framing — "does the new version have majority hashrate support?" — addresses a parameter that is confirmed non-causal at realistic economic support levels (Section 4.2.1) and that becomes actively misleading within the inversion zone (Section 4.6.4). Three alternative questions better track the operative causal structure.

---

### 4.7.1 Three Operational Monitoring Questions

**Question 1: What fraction of economically significant Bitcoin activity is committed to each fork?**

`economic_split` is the dominant causal parameter at 144-block retarget and a critical threshold parameter at 2016-block. The economic threshold at ~0.50 is a hard floor: below it, no cascade is possible. The economic override at ~0.82 is a hard ceiling: above it, pool ideology becomes irrelevant to the final outcome. The entire operative parameter space lies between these bounds, making economic weight the primary quantity to assess.

Operationally, this corresponds to: which exchanges have committed to listing and supporting v27 deposits and withdrawals? Which custodians (institutional asset managers, ETF providers) are processing redemptions on v27? Which payment processors are routing v27 transactions? These are public or semi-public decisions — exchanges announce chain support policies, ETF providers publish their fork handling procedures, and on-chain transaction patterns reveal which UTXO sets are being spent on which chain. The fraction of circulating supply being actively transacted on each fork, weighted by entity economic significance, is an estimable quantity from public data.

**Question 2: Which major mining pools are ideologically committed versus profit-maximizing, and what is each committed pool's switching cost threshold?**

`pool_committed_split` is the dominant causal parameter at 2016-block retarget. Its threshold (~0.296 in the Phase 3 transition zone) is not determined by the total fraction of committed hashrate but by the structure of *which pools* are committed and at what ideological strength. The Foundry flip-point finding demonstrates that the identity of the pivotal pool — the largest single actor whose ideological assignment determines cascade direction — matters more than aggregate committed shares.

Operationally, pools' fork positions are partially observable from their public communications, social media statements, and block attribution data. Pool operators have historically been willing to signal their fork positions publicly (as in the SegWit2x signaling period). The more difficult estimation is `ideology_strength × max_loss_pct` — how much revenue loss a committed pool will accept before switching. Calibration against observed pool behavior during BCH and BSV fork events could provide empirical bounds; this remains an open research question.

**Question 3: Has the fork crossed the economic override threshold (~0.82), and if not, is the largest committed pool on the v27 or v26 side?**

This is the decision tree that the findings support:

- If `economic_split ≥ 0.82`: pool ideology is irrelevant to the final outcome. Monitor cascade timing (determined by ideology × max_loss) but not outcome direction.
- If `economic_split ∈ [0.50, 0.82]`: identify which side the largest committed pool (Foundry or equivalent) is assigned to relative to the ~0.214 flip-point. This single structural question determines whether the inversion zone is active and which direction it tilts the outcome.
- If `economic_split ≤ 0.50`: no cascade is possible; v26 wins regardless of pool configuration.

---

### 4.7.2 The Econ Lag as a Real-Time Fork Indicator

The model identifies a consistent structural sequence in fork resolution: pool hashrate consolidation precedes economic node migration by approximately 1,750 blocks at 2016-block retarget (~2,150–2,500 blocks at 144-block retarget). This sequencing — not the specific block counts — is the finding with real-world observational relevance. The block-count estimates carry the timing caveats documented in §4.6.3: they are mechanistically valid for the model's block-driven components but do not account for institutional decision cycles that operate on human timescales independent of block production.

With that caveat stated, the structural sequence provides two observable signals in practice:

- **Pool cascade completion** is visible on-chain: hashrate from attributed pools concentrates on one chain, and the competing chain's block production rate drops relative to its pre-fork share. This is the earlier signal.
- **Economic adoption** is visible at exchanges: the under-supported fork's deposit/withdrawal volumes decline, price divergence stabilizes, and custodial balance migration becomes observable in UTXO analysis. This signal follows hashrate consolidation.

The price gap magnitude at the time of economic switching is a diagnostic that does not depend on timing: gaps of 41–47% indicate the full-switch regime is active; gaps of 12–18% indicate no-switch. A fork that resolves at the pool hashrate level but shows only 12–18% price divergence is likely in the no-switch regime — economic adoption will not complete regardless of how much additional time passes, and the winning chain will hold its hashrate advantage without full economic migration. This price-gap diagnostic is robust to the timing uncertainty because it is magnitude-based, not duration-based.

---

### 4.7.3 What the Findings Do Not Support

The three monitoring questions above are bounded by the model's structural assumptions and calibration constraints. Several conventional claims about Bitcoin fork governance are neither supported nor refuted by these findings.

**The role of user-activated soft forks (UASF).** The User-PRIM analysis (Section 4.11) confirms that user nodes have no structural capacity to shift outcomes in the 2016-block regime under any tested parameter configuration. This does not mean UASF narratives are wrong in principle — it means that the operative mechanism of UASF (user nodes refusing to relay or build on non-compliant blocks) does not translate into a pivotal causal pathway in the modeled parameter space, given the 2197:1 economic weight ratio between institutional actors and user nodes. A UASF campaign that successfully shifts exchange and custodian positions — moving `economic_split` — would be causal. One that operates only through user node behavior would not.

**Fork outcomes beyond the ±20% price divergence regime.** All threshold findings are bounded by the model's ±20% maximum price divergence cap. Real fork events (BCH/BTC, BCH/BSV) have produced divergences of 80–95% over months. Under larger divergences, the dynamics change qualitatively: the losing chain's token may collapse before its difficulty adjustment fires, making hashrate suddenly causal in a way the model does not capture. The findings characterize short-to-medium-run fork dynamics; long-run dynamics under extreme divergence remain outside the model's scope.

**Threshold values as precise predictions.** The specific thresholds identified — ~0.50 economic floor, ~0.82 override, ~0.214 Foundry flip-point, ~0.296 committed_split transition zone — are calibrated to the modeled 2026 Bitcoin pool distribution and price oracle weights. The mechanisms that produce these thresholds are general; the specific numbers are not. A mining landscape with a different pool size distribution shifts the flip-point. A different economic weight coefficient shifts the economic thresholds. These findings establish the structure of fork dynamics and the identity of the operative parameters, not a universal quantitative prediction.

---

---

## 4.8 Phase 2: Decision Boundary Fitting

The targeted sweep program (Phase 1) identified which parameters cause fork outcomes and mapped thresholds along individual dimensions. Phase 2 applies three complementary statistical methods — Random Forest classification, Logistic Regression with interaction terms, and Patient Rule Induction Method (PRIM) — to all labeled Phase 1 scenarios simultaneously, estimating the full 4-dimensional decision boundary as a joint function of the four active parameters.

**Data.** Phase 2 uses all valid labeled scenarios separated by retarget regime. The 144-block dataset (n=268) includes full-network sweeps only, excluding `lhs_144_6param` due to the economic quantization artifact on the lite network (Section 4.2, §4.2.4). The 2016-block dataset (n=298) includes all valid 2016-block sweeps. Active inputs to all models are `economic_split` (E), `pool_committed_split` (C), `pool_ideology_strength` (I), and `pool_max_loss_pct` (M).

---

### 4.8.1 Random Forest Feature Importance: Causal Rank Reversal Confirmed

Random Forest classification was fitted separately for each regime. Table 7 reports feature importance (mean decrease in impurity) and out-of-bag (OOB) accuracy.

**Table 7. Random Forest feature importance by retarget regime. Bold = dominant parameter in each regime.**

| Parameter | 144-block (n=268) | 2016-block (n=298) | Rank change |
|-----------|:-----------------:|:------------------:|:-----------:|
| `economic_split` | **77.2%** | 20.2% | #1 → #2 |
| `pool_committed_split` | 11.3% | **52.8%** | #2 → #1 |
| `pool_max_loss_pct` | 5.5% | 17.1% | #4 → #3 |
| `pool_ideology_strength` | 6.0% | 9.9% | #3 → #4 |
| **RF OOB accuracy** | **80.0%** | **83.2%** | |

The causal rank reversal is confirmed on the full multi-sweep dataset without lite-network quantization contamination. At 144-block, `economic_split` is the dominant predictor by a wide margin (77.2%, approximately 4× the next-best parameter). At 2016-block, `pool_committed_split` displaces it as dominant (52.8%, 2.6× the next-best parameter). This is not a marginal effect: the two parameters swap rank positions entirely between regimes.

The direction of the mechanism is consistent with the Phase 1 findings. At 144-block, the retarget fires quickly enough that economic price signals determine the cascade before pool commitment structure becomes binding — economic alignment governs who wins. At 2016-block, pools must sustain their ideological commitment through an entire 2016-block epoch before any difficulty adjustment fires; the structural question of which pools are committed to which fork becomes the binding constraint, and economic signals play a secondary amplifying role.

Two additional observations follow from Table 7. First, 2016-block dynamics are *more predictable*, not less — the higher OOB accuracy (83.2% vs. 80.0%) indicates the RF extracts a cleaner signal at 2016-block, consistent with pool commitment structure being a harder, more deterministic constraint than economic price signals. Second, `pool_max_loss_pct` rises from near-zero importance (5.5%) at 144-block to a meaningful secondary factor (17.1%) at 2016-block — at longer retarget intervals, how much loss a committed pool can absorb before switching becomes material to the outcome.

---

### 4.8.2 Logistic Regression Decision Surface

Logistic regression with all pairwise interaction terms was fitted on the 2016-block dataset to characterize the shape of the decision boundary. The full fitted equation is:

```
log-odds(v27_win) = 1.152
  + 1.231 · E · C
  − 0.618 · E · M
  + 0.568 · E
  + 0.504 · C · I
  − 0.374 · I · M
  − 0.289 · E · I
  − 0.278 · C · M
  + 0.177 · C
  + 0.085 · M
  − 0.083 · I
```

where E = `economic_split`, C = `pool_committed_split`, I = `pool_ideology_strength`, M = `pool_max_loss_pct`. Cross-validated accuracy: 77.5% ± 2.9%.

Three structural features stand out. First, the dominant term is the E×C interaction (+1.231) — the largest coefficient by a factor of two over any other term. This confirms that economic pressure and pool commitment are synergistic rather than additive: high economic support combined with high pool commitment produces v27 wins with dramatically higher probability than either factor alone would predict. The two parameters co-determine outcomes at 2016-block in a way that cannot be captured by separate thresholds on each.

Second, the main effects for I and M are near-zero (−0.083 and +0.085), while both parameters appear in multiple interaction terms. Ideology and loss tolerance operate almost entirely through interactions — they amplify or dampen the E and C effects rather than directly shifting the outcome probability. This is consistent with the Phase 1 finding that the ideology × max_loss *product* is the operative quantity (Section 4.3.3), not either parameter individually.

Third, the negative E×M coefficient (−0.618) captures an important antagonism: at high economic support levels, higher pool loss tolerance *hurts* v27 — committed v26 pools that can absorb larger losses persist longer under economic pressure, resisting the cascade. This interaction explains why maximum economic support (econ≥0.82) does not instantly resolve the fork; it still takes 700–10,920 seconds depending on pool loss tolerance (Section 4.3.4).

The 144-block logistic regression (CV accuracy: 59.8%, 10% above chance) is substantially weaker and not structurally reliable. The inverted signs for several terms relative to the 2016-block fit, combined with the lite-network quantization artifact, make the 144-block LR unsuitable for inference. The RF importance scores (Table 7) are more trustworthy for 144-block conclusions.

---

### 4.8.3 PRIM Boundary Analysis

PRIM (Patient Rule Induction Method, Bryant and Lempert 2010) was applied to identify axis-aligned regions of the 2016-block parameter space with concentrated outcome properties. Three PRIM runs were executed: v27-win maximization, outcome uncertainty maximization (the transition zone), and contentiousness maximization. Table 8 summarizes the three boxes.

**Input dimensionality.** PRIM was applied to the same pre-reduced 4-dimensional space used by the RF and logistic regression models: `economic_split`, `pool_committed_split`, `pool_ideology_strength`, and `pool_max_loss_pct`. The full swept parameter space includes six parameters; `pool_profitability_threshold` and `solo_miner_hashrate` are excluded from PRIM inputs because both were confirmed non-causal in prior sweeps (`lhs_2016_6param`: permutation importance ≈ 0, separation ≤ 0.011 across the full outcome range). Including non-causal parameters in PRIM degrades box quality by allowing the algorithm to waste peeling steps on dimensions with no outcome signal. The causal screening step is therefore a prerequisite for valid PRIM application, not a post-hoc rationalization: the 4-parameter input space is the space in which the decision boundary actually lives.

**Table 8. 2016-block PRIM results: three target regions.**

| PRIM target | Support | v27 win rate in box | n scenarios |
|-------------|:-------:|:-------------------:|:-----------:|
| v27-win maximization | 58.7% | 85.7% | 175 |
| **Uncertainty (transition zone)** | **51.0%** | **50.0%** | **152** |
| Contentiousness maximization | 40.3% | 36.0% | 120 |

The uncertainty box — the region of parameter space where outcomes are exactly 50/50 — is the primary Phase 3 target. Its bounds are:

| Parameter | Min | Max |
|-----------|-----|-----|
| `economic_split` | 0.28 | 0.78 |
| `pool_committed_split` | 0.15 | 0.53 |
| `pool_ideology_strength` | 0.44 | 0.80 |
| `pool_max_loss_pct` | 0.16 | 0.40 |

This box covers 51% of the full parameter space while containing a perfectly balanced 50/50 outcome split — indicating that the decision boundary runs through this region but Phase 1 sampling did not resolve its precise shape. Phase 3 LHS sampling within these bounds (Section 4.9) is designed to resolve this uncertainty.

The contentiousness box identifies the parameter region producing the highest on-chain disruption (mean contentiousness 0.360, versus 0.271 overall at 2016-block). Notably, this region has a 36% v27 win rate — substantially below the 67.1% overall rate. The most disruptive scenarios are not those where v27 wins cleanly; they are scenarios where pools are committed enough to sustain a real fork but not committed enough to resolve it decisively. The contentiousness box is a proper subset of the uncertainty box, shifted toward higher pool_committed_split [0.25, 0.57] and lower pool_max_loss_pct [0.10, 0.31] — capturing the "contested rather than decisive" region where committed pools create prolonged reorg periods without ultimately prevailing.

![PRIM Peeling Trajectory](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_prim_peeling_trajectory.png)
**Figure Z — PRIM Uncertainty Box Peeling Trajectory (2016-block retarget).** Panel A shows the uncertainty score (1 − 2|mean − 0.5|; 1.0 = perfect 50/50, 0 = certain) as a function of the number of scenarios remaining in the box, with the x-axis inverted to show peeling direction (large to small). Panel B shows the mean v27 win rate at each of the 13 peeling steps, converging monotonically from 0.678 (full dataset) toward 0.50 (the 50/50 target). At step 12 the box contains n=155 scenarios (53% of the dataset) with a mean v27 win rate of 0.497 and uncertainty score of 0.994 — effectively a perfect decision boundary region. Each peeling step removes the lowest-scoring 5th percentile of one parameter boundary, chosen greedily to maximize the uncertainty score gain. The smooth monotonic convergence in both panels confirms that PRIM is identifying a genuine transition zone rather than overfitting to noise: the uncertainty score increases at every step without reversal. Source: n=295 scenarios from 2016-block full-network and hybrid sweeps (VALID_SWEEPS_2016 in `tools/discovery/fit_boundary.py`). See `docs/figures/fig_prim_peeling_trajectory.png`.

The 144-block PRIM analysis returns near-degenerate results: after only three peeling steps the box still covers 92.5% of the data with a 49.6% v27 win rate. PRIM cannot identify a meaningful transition zone in the 144-block dataset. This reflects the non-uniform structure of the full-network 144-block grid sweeps — targeted sweeps at fixed parameter values do not provide the uniformly distributed coverage that PRIM requires to peel effectively. The 144-block RF importance scores (Table 7) remain valid; only the PRIM-derived boxes are uninformative at 144-block.

---

### 4.8.4 Contentiousness Structure

Contentiousness — a composite score combining reorg count, reorg mass, cascade timing, and economic lag — measures the degree of on-chain disruption a fork scenario produces, independent of which fork ultimately wins. Table 9 compares contentiousness across regimes.

**Table 9. Contentiousness comparison by retarget regime.**

| Metric | 144-block | 2016-block | Ratio |
|--------|:---------:|:----------:|:-----:|
| Mean contentiousness (all scenarios) | 0.132 | 0.271 | 2.1× |
| Mean contentiousness (v27-win scenarios) | ~0.09 | ~0.18 | ~2× |
| Mean contentiousness (high-chaos PRIM box) | — | 0.360 | — |

The 2016-block regime produces 2.1× more on-chain disruption on average. This is structurally expected: with a 2016-block retarget interval, a committed minority chain can persist for approximately 14 days (at 10-minute block targets) before its difficulty adjusts downward, accumulating extended periods of competitive mining, chain reorganizations, and economic uncertainty. The 144-block regime resolves more quickly and cleanly.

The relationship between contentiousness and outcome is non-monotonic at 2016-block. Scenarios where v27 wins decisively (high economic support, high committed_split, low max_loss) have *low* contentiousness — the cascade completes quickly. Maximum contentiousness occurs at intermediate committed_split where pools are committed enough to sustain a genuine fork but not committed enough to win. This intermediate zone — the high-chaos PRIM box (committed [0.25, 0.57], econ [0.34, 0.78]) — is the parameter region a governance actor should most want to avoid: it produces the most disruptive scenarios regardless of which fork ultimately prevails.

---

### 4.8.5 Decision Boundary Visualization

![PRIM Uncertainty Bounds](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_decision_boundary_equal_weights.png)
**Figure W — 2016-block decision boundary across all parameter projections.** The Random Forest probability surface (P(v27 win); n=590, OOB accuracy 79.8%) is shown for four parameter projections. The dominant E×C panel (left, occupying 60% of the figure width) plots the joint `economic_split` × `pool_committed_split` surface with `pool_ideology_strength` and `pool_max_loss_pct` held at their dataset medians. Three structural thresholds are annotated: the cascade floor (E≈0.50, below which v27 cannot win regardless of pool commitment), the economic override threshold (E≈0.82, above which v27 wins regardless of pool commitment), and the Foundry flip-point (C≈0.214, the pool committed-split level corresponding to the Foundry hashrate fraction). The inversion zone — the region between the two vertical threshold lines where the causal rank reversal operates — is indicated with a double-headed bracket. The PRIM uncertainty box (Table 8) is overlaid as a dashed blue rectangle on all panels. Supporting panels (right column, top to bottom): E×M (`economic_split` × `pool_max_loss_pct`), C×I (`pool_committed_split` × `pool_ideology_strength`), I×M (`pool_ideology_strength` × `pool_max_loss_pct`). Individual scenario outcomes (v27 win = triangle, v26 win = circle) are overlaid on all panels with semi-transparency. The P=0.50 decision contour (white dashed line) marks the estimated boundary between outcome regions in each projection. Source: VALID_SWEEPS_2016 (n=295) plus `lhs_2016_full_phase3_merged` (n=292), full-network 2016-block scenarios only. Contentiousness score uses equal 0.25 weights across all four components. See `docs/figures/fig_decision_boundary_equal_weights.png`.

The dominant E×C panel in Figure W makes the causal structure visible in a single view. Below the cascade floor (E<0.50), the surface is uniformly blue regardless of C — economic support below the majority threshold prevents a v27 victory under any pool commitment structure. Above the economic override threshold (E>0.82), the surface is uniformly red — economic dominance is sufficient for a v27 win independent of pool structure. In the inversion zone (0.50 < E < 0.82), pool commitment is the operative variable: the P=0.50 contour runs roughly parallel to the E-axis in this region, confirming that C is the primary determinant of outcome when economic support is intermediate. The non-linearity at low C values (the boundary curves toward higher E requirements as C decreases) corresponds to the E×C interaction term dominating the logistic regression fit (coefficient +1.231, Section 4.8.2).

The three supporting panels reveal the secondary structure. The E×M panel shows the antagonism between economic support and pool loss tolerance captured by the −0.618 E×M interaction: at high E, higher M (committed v26 pools absorbing more loss) pushes the boundary rightward, requiring even higher economic support for a v27 win. The C×I panel shows the synergy captured by the +0.504 C×I interaction: high ideology strength amplifies the effect of high committed-split, shifting the 50/50 boundary toward lower C values. The I×M panel is the flattest of the three, consistent with the near-zero main effects for both parameters — their joint surface is nearly featureless, confirming that I and M operate primarily through interactions with E and C rather than independently.

---

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

---

## 4.10 Phase 3b: Cross-Network Validation

Phase 3 established the two-layer outcome structure on a 25-node lite network — a configuration chosen for computational tractability that consolidates all economic actors into a small number of aggregate nodes (~2 nodes per partition, each representing ~25% of total economic weight). Phase 3b replicates the identical PRIM uncertainty box bounds on the full 60-node network (`lhs_2016_full_phase3`, n=292), where 24 independent economic nodes per partition each represent ~4% of total economic weight.

The two network configurations are not simply different resolutions of the same model — they represent meaningfully different economic coordination assumptions. The lite network models a world where economic actors behave as coordinated blocs: a single aggregate node captures "all major exchanges" and its decision shifts a large weight at once, as would occur under industry consensus, coordinated statements, or a dominant actor that others follow. The full network models fragmented independent decision-making: each economic actor evaluates the same price signal but switches at its own threshold, so the aggregate price signal builds gradually rather than arriving in large discrete steps. These are both plausible real-world regimes and the comparison between them is a substantive finding, not a data quality issue.

---

### 4.10.1 Two-Layer Structure Confirmed

The core finding from Phase 3 replicates on the full network without qualification. Full economic switching is perfectly predictive of v27 dominance: all 71 full_switch scenarios are v27-dominant (100%), and no contested or v26-dominant outcome co-occurs with full economic adoption. The Layer 1 / Layer 2 decoupling — hash-war outcome governed by pool_committed_split, economic adoption governed by pool_max_loss_pct — is not a lite-network artifact.

The pool_max_loss_pct adoption threshold (~0.217 on lite) shifts slightly on the full network (~0.273), consistent with the finer economic resolution producing a smoother price response curve that requires modestly higher cascade speed to cross economic node switching thresholds. The mechanism is unchanged; the threshold value shifts within the range of calibration uncertainty documented in §6.2 of assumptions.md.

The contested zone shrinks substantially on the full network: 7.9% (23/292) versus 25.3% (76/300) on lite. This reduction reflects that the full network's continuous economic weight assignment makes fewer scenarios genuinely indeterminate — small differences in economic_split that fell within a single quantization step on the lite network now resolve cleanly on the full network. The contested outcomes that remain (n=23) are confined to near-threshold parameter combinations where high ideology × high max_loss prevents cascade completion despite economic support near ~0.563.

---

### 4.10.2 The Dominant-Parameter Shift Across Coordination Regimes

The most striking cross-network difference is that `economic_split` displaces `pool_committed_split` as the dominant predictor within the transition zone on the full network. Table 19 compares feature importance across the two network configurations.

**Table 19. Feature importance within the PRIM transition zone: lite network vs. full network.**

| Parameter | Lite network (n=300) | Full network (n=292) |
|-----------|:--------------------:|:--------------------:|
| **pool_committed_split** | **0.188 (#1)** | 0.055 (#2) |
| **economic_split** | 0.028 (#2) | **0.164 (#1)** |
| pool_max_loss_pct | 0.012 (#4) | 0.020 (#3) |
| pool_ideology_strength | 0.021 (#3) | 0.016 (#4) |

This shift reflects the different economic coordination structures of the two networks rather than a measurement inconsistency. On the lite network, a single aggregate economic node controls ~25% of total economic weight. When that node switches, the price oracle receives a large discrete signal — sufficient to either cross pool switching thresholds in one step or fall short entirely. In this regime, pool commitment is the critical variable: it determines whether the economic bloc's signal is large enough to force committed pools over their tolerance threshold. The outcome depends on whether a single coordinated economic trigger lands above or below the pool switching threshold, making pool_committed_split the dominant discriminator.

On the full network, 24 independent economic nodes switch at slightly different times as the price signal builds. No single node controls enough weight to resolve the outcome alone — the cascade assembles incrementally, with each individual switch reinforcing the price signal that triggers the next. In this regime, the aggregate economic_split value controls how far the cascade can propagate: higher economic_split means more nodes eventually cross their switching threshold and the self-reinforcing price signal reaches completion. Pool commitment matters less because the cascade does not depend on a single coordinated trigger — it builds continuously from many small independent decisions. economic_split is therefore the dominant discriminator.

The governance implication is direct: the relative leverage of pool operators versus economic actors depends on how coordinated economic actors are in practice. In a coordinated regime — where exchanges issue joint statements, a dominant custodian sets the standard others follow, or industry consensus forms rapidly — pool commitment is the pivotal variable because it determines whether a single large economic signal crosses the threshold. In a fragmented regime — where each exchange, custodian, and payment processor reaches its own assessment independently — aggregate economic support is the pivotal variable because it governs how far the self-reinforcing cascade propagates before stalling.

---

### 4.10.3 Implications and Scope for Future Work

The PRIM box calibration was derived from lite-network data and therefore targets the coordinated-bloc transition zone rather than the fragmented-independent one. On the full network, the same bounds fall predominantly below the ~0.563 economic threshold — producing 67.8% v26-dominant outcomes rather than the 50/50 balance the box was designed to target. A refined Phase 3c sweep re-deriving the uncertainty box from full-network data targeting econ ∈ [0.50, 0.65] would sharpen the economic threshold estimate and characterize the transition zone under the fragmented-independent coordination assumption.

For the present paper's conclusions, the cross-network validation achieves its primary goal: the two-layer outcome structure — the central finding of Phase 3 — is confirmed as a real dynamic property of the fork model under both coordination regimes. The hash-war-only archetype (v27 wins hashrate without economic adoption, 81% of v27-dominant transition zone outcomes on lite) replicates on the full network. The operational risk ranking of the four archetypes (Section 4.9.7) is unchanged across both regimes.

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

### 4.10.5 The Two-Scale Structure Across Coordination Regimes

Together, §4.10.1–§4.10.3 (PRIM-zone full network, n=292) and §4.10.4 (wide-range full network, n=692) complete a picture that spans both network configurations and both parameter space scopes. Table 22 places all 2016-block sweeps in order.

**Table 22. Feature importance across all 2016-block sweeps, ordered by parameter space scope.**

| Sweep | n | Network | Coordination | Scope | Top parameter | Importance |
|-------|:-:|---------|-------------|-------|---------------|:----------:|
| `lhs_2016_full_parameter` | 64 | full | fragmented | Full range | pool_committed_split | 0.275 sep. |
| `lhs_2016_6param` | 129 | lite | coordinated bloc | Full range | pool_committed_split | 0.272 sep. |
| `lhs_2016_phase3` | 300 | lite | coordinated bloc | PRIM zone | pool_committed_split | 0.188 imp. |
| `lhs_2016_full_phase3` | 292 | full | fragmented | PRIM zone | **economic_split** | **0.164 sep.** |
| **`lhs_2016_full_6param`** | **692** | **full** | **fragmented** | **Full range** | **economic_split** | **60.0% imp.** |

The pattern across these sweeps reflects two distinct causal structures, not a methodological inconsistency:

**Under coordinated-bloc economic decisions (lite network):** pool_committed_split is dominant because the decisive event is whether a single large economic bloc's signal crosses pool switching thresholds in one step. Pool commitment determines whether that threshold is reachable at all. economic_split matters less because the total weight moving at once is determined by node count, not the continuous parameter value. At low pool_committed_split (≤ ~0.25), v26 committed pools can absorb the bloc signal; above ~0.30, Foundry's assignment resolves the outcome before the bloc's signal propagates fully.

**Under fragmented-independent economic decisions (full network):** economic_split is dominant because the cascade assembles incrementally from many small independent switches. No single actor controls enough weight to resolve the outcome alone — the price signal builds with each switch, and how far it propagates before stalling is governed by the aggregate economic_split level. pool_committed_split remains the gate: at very low values (≤ ~0.25) v26 wins regardless, because committed v26 pool resistance is strong enough that even a fully propagating economic cascade stalls. But within the transition zone, economic_split determines how far the cascade runs.

Both structures produce the same sequential governance logic: **pool_committed_split sets the floor below which v26 always wins; economic_split sets the ceiling above which v27 almost always wins.** What changes between coordination regimes is which parameter carries the most discriminating power within the contested region between these thresholds. The finding that pool operators are pivotal under coordinated economic blocs, and that aggregate economic support is pivotal under fragmented independent decision-making, is itself a governance insight: the leverage of each actor class depends on how organized the other is.

---

---

## 4.11 User-PRIM: Scenario Potential for User Nodes

User full nodes occupy a distinct role in Bitcoin governance theory. Unlike mining pools, which can shift hashrate, or economic nodes, which control the price signals that drive miner revenue, user nodes enforcing consensus rules through strict validation exert no direct economic force. They cannot orphan miners' blocks unless the economic infrastructure — exchanges, custodians, payment processors — also refuses to accept those blocks. Whether user nodes can nonetheless exert *structural* influence on fork outcomes under any parameter configuration is an empirical question that the Scenario Potential framework is designed to answer.

This section reports the User-PRIM analysis: a governance-adapted Z-PRIM algorithm applied to the 2016-block regime dataset (n=598 scenarios, 15 sweeps) to find the parameter subspace where user nodes are most nearly pivotal. The analysis uses a composite objective combining contentiousness (scenarios where the outcome is genuinely in play) with a normalized user Scenario Potential score (SP_user). The result is a structural null: user-PRIM finds a bounded box but does not substantially concentrate user-pivotal scenarios, confirming that pool and economic dynamics dominate 2016-block fork outcomes at all parameter combinations tested.

---

### 4.11.1 Structural Ceiling from Weight Ratio

The upper bound on user node pivotality is set analytically before any simulation data is examined. In the simulation network, user nodes carry a combined economic weight of W_users = 0.1688 against a total network weight of W_total = 370.90 — a 2197:1 ratio. This ratio is not a calibration choice but a structural consequence of the model's representation of Bitcoin's economic geography: exchanges, custodians, and payment processors collectively hold vastly more economic weight than individual full node operators.

At this weight ratio, the maximum achievable SP_user value — the scenario potential of user nodes — is bounded near zero for all but the most artificially constructed parameter configurations. Even in the most favorable conceivable scenario (contested outcome, both forks at exact parity, user nodes as the sole tie-breaker), the user coalition controls less than 0.05% of total economic weight. The z-score formulation of Scenario Potential can normalize this contribution, but the normalization does not change the underlying structural fact: user nodes cannot be the swing actor in a realistic fork.

The User-PRIM analysis was conducted with this ceiling in mind, using min-max normalization of SP_user across the dataset to give user pivotality scores comparable scaling to contentiousness. Without normalization, the near-zero SP_user values would dominate none of the Z_user variance and the analysis would reduce to pure contentiousness PRIM. The normalized analysis provides the fairest possible test of whether user nodes concentrate influence in any region of parameter space.

---

### 4.11.2 User-PRIM Discovered Box

User-PRIM was applied to the 2016-block dataset (n=598 scenarios across 15 sweeps) using a composite objective Z_user = λ1 × contentiousness + λ2 × SP_user_normalized, with λ1=0.5 and λ2=1.0 (SP_user-weighted). The discovered box and its properties are reported in Table 10.

**Table 10. User-PRIM discovered box: parameter bounds and outcome properties.**

| Parameter | Min | Max |
|-----------|-----|-----|
| `economic_split` | 0.49 | 0.77 |
| `pool_committed_split` | 0.20 | 0.50 |
| `pool_ideology_strength` | 0.47 | 0.52 |
| `pool_max_loss_pct` | 0.25 | 0.26 |

**Box statistics:**

| Metric | Value |
|--------|-------|
| Scenarios in box | 58 (9.7% of dataset) |
| Mean Z_user in box | 0.563 (dataset mean: 0.299) |
| Mean SP_user in box | 0.336 |
| Mean contentiousness in box | 0.297 |
| v27_dominant | 38 (65.5%) |
| v26_dominant | 16 (27.6%) |
| contested | 4 (6.9%) |

The box identifies a region of parameter space concentrated in the transition zone for economic_split (0.49–0.77, spanning both the cascade onset and the approach to the economic override threshold) and pool_committed_split (0.20–0.50, spanning the Foundry flip-point). The ideology_strength and max_loss_pct bounds are strikingly narrow — [0.47, 0.52] and [0.25, 0.26] respectively — covering only a thin slice of the tested ideology × max_loss space. This narrow band corresponds to pool ideology × max_loss products near the diagonal threshold (Section 4.3.3), where the interaction is closest to the switching boundary.

The outcome distribution within the box (65.5% v27, 27.6% v26, 6.9% contested) is close to the overall dataset distribution. The box has not concentrated contested outcomes; the mean contentiousness in the box (0.297) is nearly identical to the overall 2016-block mean (0.271). This alone signals that the box is not finding scenarios where user nodes tip a genuinely balanced contest.

---

### 4.11.3 Bias Ratio: The Null Result

The key diagnostic for User-PRIM is the bias ratio — the recall of high-SP_user scenarios (top two quintiles) within the discovered box relative to the recall of low-SP_user scenarios (bottom two quintiles). A bias ratio substantially above 1.0 would indicate the box concentrates user-pivotal scenarios; a ratio near 1.0 indicates the box is no better than the baseline at finding them.

**Table 11. Bias ratio comparison: Standard PRIM vs. User-PRIM.**

| Method | Bias Ratio | Completeness | N in box |
|--------|:----------:|:------------:|:--------:|
| Standard PRIM | 0.975 | 1.00 | 229 |
| User-PRIM | **1.256** | 0.60 | 58 |

The User-PRIM bias ratio is 1.256. This is slightly above the standard PRIM baseline of 0.975 — indicating some improvement over random selection — but it is not substantially above 1.0. A bias ratio of 1.256 means the box is only modestly better than chance at concentrating user-pivotal scenarios. By comparison, meaningful scenario concentration in prior PRIM applications yields bias ratios of 2.0 or higher; the 1.256 result falls well short of this threshold.

A sensitivity check across three λ configurations confirms the finding is not an artifact of the objective weighting:

| λ1 (contentiousness) | λ2 (SP_user) | N in box | Mean Z_user | Stable? |
|:--------------------:|:------------:|:--------:|:-----------:|:-------:|
| 0.5 | 1.0 | 58 | 0.563 | ✓ |
| 1.0 | 0.5 | 72 | 0.730 | ~ |
| 0.5 | 2.0 | 57 | 0.866 | ~ |

The box size and Z_user concentration shift as the weighting changes, but the bias ratio does not materially improve. The near-unity bias ratio under the default weighting (λ1=0.5, λ2=1.0) is the primary result; the alternative weightings confirm it is not sensitive to that specific choice.

![SP_user Distribution by Outcome Type](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_sp_user_distribution.png)

![Z_user Scatter Plot](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_z_user_scatter.png)

---

### 4.11.4 Structural Interpretation

The User-PRIM null result has a straightforward structural explanation. Fork outcomes in the 2016-block regime are determined by two causal pathways: the pool commitment cascade (controlled by pool_committed_split crossing the Foundry flip-point, Section 4.3.2) and the economic price cascade (controlled by economic_split exceeding the override threshold, Section 4.3.4). User nodes participate in neither pathway directly. They do not set prices — that function belongs to exchanges and custodians in the economic node class. They do not produce blocks — that function belongs to pools and solo miners. A user node operator running strict-validation software can delay or complicate the propagation of non-conforming blocks only if the economic infrastructure also refuses them; in the simulation, economic infrastructure behavior is determined by economic node parameters, not user node parameters.

The 2197:1 weight ratio quantifies what this means in practice. Even in the narrow ideology band identified by User-PRIM — where pool ideology × max_loss products are closest to the switching threshold — the user coalition cannot provide the economic signal required to push pool decisions across the threshold. The simulation confirms this directly: the targeted_sweep5 grid (Section 4.2.2) produced zero variation in any output metric across the full user parameter space, with all 36 scenarios producing identical v26_dominant outcomes regardless of user ideology or switching behavior.

This finding bears directly on debates about User-Activated Soft Fork (UASF) governance strategies. The UASF argument holds that user nodes enforcing new rules creates economic pressure on miners — if miners' blocks are rejected by economic infrastructure, those blocks are worthless. This mechanism requires that user nodes *are* the economic infrastructure, or control it. In the model, they are not and do not: the economic weight ratio is 2197:1. The governance implication is that UASF campaigns succeed when they persuade exchanges, custodians, and payment processors to enforce the new rules — not when they increase the count of individual full node operators running updated software. Individual user node operators cannot be near-pivotal under any realistic parameter configuration tested.

The User-PRIM analysis validates the Scenario Potential framework as a null-result detector. It correctly distinguishes between regions of parameter space where a governance actor *could* be pivotal and regions where structural weight constraints make pivotality impossible regardless of parameter values. A bias ratio near 1.0 is the correct output for an actor class with negligible economic weight — and finding it is a contribution rather than a failure of the method.

---

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

![Joint Governance Leverage Surface](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_sp_surface.png)

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

![Top Scenario Parameter Profiles](/home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/docs/figures/fig_sp_top_scenarios.png)

The surprise rankings reveal two distinct archetypes:

**Archetype A — High leverage, v27 wins cleanly (ranks 1, 3–7).** These scenarios sit in the maximum leverage zone but pool commitment was sufficient to drive the cascade to completion and economic support reinforced it. The outcome resolved decisively in v27's favor despite the structural leverage available to both actor classes. Rank 1 (E=0.780, C=0.214) is the extreme case: the highest Z_joint in the dataset resolves to a clean v27 win — the leverage was real but both pool structure and economic conditions were aligned in the same direction, so the potential for intervention was present but unused.

**Archetype B — High leverage, v26 wins unexpectedly (rank 2).** Rank 2 (E=0.761, C=0.247, Z_joint=1.902) is the most analytically interesting case in the dataset: economic support is deep in the inversion zone, committed split is above the Foundry flip-point, both gradient scores are near-maximum, yet v26 prevails. This is a genuine surprise — governance leverage was maximally available to both pool coalitions and economic actors favoring v27, and the outcome went the other way. The ideology × max_loss interaction is the mechanism: pool ideology was strong enough to hold v26 pools in place through the simulation window despite the structural disadvantage. This scenario has the highest surprise score among v26_dominant outcomes (surprise=0.862) and represents the most operationally disruptive governance configuration in the dataset — maximum leverage, unexpected direction.

Ranks 8 and 9 (both from `targeted_sweep10_econ_threshold_2016`) are notable for appearing at E=0.500 and E=0.350 — below or at the cascade floor where d_economic is gated to zero. These are high-surprise v27 wins driven entirely by d_pools: committed split at C=0.350 is well above the Foundry flip-point, and pool cascade dynamics resolved the outcome cleanly despite low economic support. They illustrate that pool-only leverage (without economic co-activation) can still produce decisive outcomes when committed_split is sufficiently above threshold.

---

## 4.13 Scenario Potential Framework: Cross-Actor Leverage Comparison

The three actor-class analyses — SP_user (Section 4.11), d_pools, and d_economic (Section 4.12) — together demonstrate the framework's capacity to discriminate between actor classes with and without structural governance leverage.

**Table 21. Actor leverage comparison across the Scenario Potential framework.**

| Actor class | Structural weight | Measure | Max value | Bias ratio (PRIM) | Interpretation |
|-------------|:-----------------:|---------|:---------:|:-----------------:|----------------|
| User nodes | W/W_total = 0.046% | SP_user (analytic) | ~0.05% | 1.256 | Structural null — weight ratio forecloses pivotality |
| Pool coalitions | Controls ~75% of hashrate | d_pools (RF gradient) | 1.000 | — | Pivotal near committed_split thresholds |
| Economic nodes | Controls price signal | d_economic (RF gradient) | 1.000 | — | Pivotal within inversion zone [0.50, 0.82] |

User nodes produce a near-unity bias ratio (1.256) in PRIM — the algorithm cannot concentrate user-pivotal scenarios because the 2197:1 weight ratio ensures SP_user is near-zero everywhere. Pool coalitions and economic actors produce gradient scores that reach the maximum (1.000) and vary meaningfully across the parameter space — the framework correctly identifies both where leverage exists (inversion zone × Foundry flip-point neighborhood) and where it does not (clean-outcome regions far from both thresholds).

The governance implication is direct. A coordination campaign for v27 activation achieves maximum leverage when it targets the inversion zone simultaneously across both actor classes: pool operators near the Foundry flip-point (C ≈ 0.21–0.30) and economic actors near the ESP (E ≈ 0.70–0.78). Campaigns operating outside these ranges — recruiting additional committed pool hashrate when C is already well above 0.30, or seeking economic custody shifts when economic support is already above 0.82 — are targeting parameter regions where additional effort produces near-zero marginal governance leverage. The sensitivity surface maps where effort translates into outcome influence and where it does not.

---

