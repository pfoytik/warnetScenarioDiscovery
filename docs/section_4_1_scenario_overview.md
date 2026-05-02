# Section 4.1 — Scenario Overview and Exploratory Process

**Draft:** May 2, 2026
**Status:** DRAFT — complete. Numbers from Results_Section_Skeleton_v4.md Table 1, SWEEP_FINDINGS.md, and writing_plan.md.

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

*Section 4.1 ends. Next: Section 4.2 — Parameter Causality: Separating Signal from Confound.*
