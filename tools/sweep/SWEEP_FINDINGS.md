# Parameter Sweep Findings - Combined Analysis

## Executive Summary

### Key Discovery

The **realistic_sweep3_rapid** sweep with fixed code reveals a dramatically different picture:

| Before Fix | After Fix |
|------------|-----------|
| hashrate_split: **+0.83** (dominant) | economic_split: **+0.67** (now dominant!) |
| economic_split: ~0.06 (no effect) | hashrate_split: +0.55 (⚠️ confounded — see below) |

**The economic cascade mechanism is real and powerful.** When economic_split is properly applied:

1. **Economic majority can overcome hashrate minority** through price signals
2. **pool_committed_split has a non-monotonic effect** — it inverts at moderate economic levels due to pool-specific flip-points (see targeted_sweep1 findings)
3. **hashrate_split has no independent causal effect** — targeted grid sweep across 0.15–0.65 produced identical outcomes at every economic level (see targeted_sweep2 findings)
4. High reorg counts (5+) correlate with v27 victory (86% of cascade scenarios in exploratory sweep)
5. **pool_neutral_pct controls cascade intensity, not outcome** — varying neutral pools from 10–50% changes how long the cascade takes but not who wins; the inversion zone persists even when the v26-committed block collapses from 36% to 8% of total hashrate (see targeted_sweep3_neutral_pct findings)

### Zone Analysis Caveat

The exploratory sweep zone analysis suggested hashrate matters alongside economics:

| Economic | Hashrate | v27 Win Rate (exploratory) |
|:--------:|:--------:|:------------:|
| Low | Low | 0% |
| **High** | Low | **50%** |
| Low | **High** | 50% |
| **High** | **High** | **100%** |

**⚠️ Targeted sweep 2 contradicts this.** The apparent hashrate effect in the exploratory sweep was likely a confound — in the LHS design, higher hashrate_split scenarios happened to co-occur with pool configurations more favorable to v27. When hashrate_split is varied independently (all other params fixed), it has no effect. The "100%" in the bottom-right was driven by economics, not hashrate.

### Targeted Threshold Discovery

The targeted sweep (economic × committed grid with fixed 25% hashrate) revealed a **non-monotonic** relationship between pool commitment and v27 outcomes:

| Economic Level | pool_committed_split Effect |
|:---------------|:----------------------------|
| 0.35 | No cascade possible — v26 wins all |
| 0.50 | Higher committed → v27 wins (threshold at commit ≈ 0.20–0.30) |
| 0.60–0.70 | **INVERTED** — v27 wins only at commit=0.20; v26 wins at commit≥0.30 |
| 0.82 | Economic signal dominates — v27 wins all |

**The inversion is caused by a pool flip-point:** Foundry (30% of pool hashrate) switches from v26-preferring to v27-preferring at pool_committed_split ≈ 0.21. At commit=0.20 with strong economics, Foundry stays on v27 (economically trapped there). At commit≥0.30, Foundry is v27-committed but the remaining v26 block (AntPool+F2Pool+ViaBTC ≈ 40% hashrate) is large enough to resist the cascade at 60–70% economic strength.

### Pool Ideology Discovery

targeted_sweep2b tested pool ideology parameters near the economic threshold (econ=0.78):

| Ideology Strength | Required max_loss_pct for v27 win |
|:-----------------:|:---------------------------------:|
| 0.2 | Never wins |
| 0.4 | ≥ 0.35 |
| 0.6 | ≥ 0.25 |
| 0.8 | ≥ 0.15 |

**Ideology and loss tolerance follow a diagonal threshold:** approximately `ideology × max_loss ≳ 0.12`. Both parameters show +0.58 correlation with v27 hashrate — they are jointly necessary near the economic threshold.

> ⚠️ **Partial caveat:** Sweep 2b ran on the lite network with a role-name bug (see below) that prevented economic and user node parameters from being overridden. Pool ideology/loss parameters were correctly applied. However, the actual economic split was the lite YAML default (~43% v27 custody), not the intended 0.78. The diagonal threshold finding for pool parameters is likely directionally valid but the economic context was not as designed. Needs re-verification after fix.

---

### ⚠️ Critical Bug: Lite Network Sweep Parameter Override Failure

**Discovered:** March 2026 during sweep5/sweep4 post-analysis.

**Root cause:** `apply_scenario_to_base_network()` in `2_build_configs.py` matched role names from the full network (`major_exchange`, `exchange`, `institutional`, `payment_processor`, `merchant`, `power_user`, `casual_user`) but the lite network uses aggregate role names (`economic_aggregate`, `power_user_aggregate`, `casual_user_aggregate`). No handler existed for these roles.

**Effect on all lite network sweeps:**

| Parameter | Status on lite network (before fix) |
|-----------|--------------------------------------|
| `hashrate_split` | ✅ Worked — pool image tags reassigned correctly |
| `pool_profitability_threshold`, `pool_ideology_strength`, `pool_max_loss_pct` | ✅ Worked — `mining_pool` role matched |
| `economic_split` | ❌ **DEAD** — custody sorting filtered on full-network roles; lite econ nodes never reassigned |
| `econ_ideology_strength`, `econ_switching_threshold`, `econ_inertia` | ❌ **DEAD** — no handler for `economic_aggregate` |
| `user_ideology_strength`, `user_switching_threshold`, `solo_miner_hashrate` | ❌ **DEAD** — no handler for `power_user_aggregate` / `casual_user_aggregate` |

**Fix applied:** `2_build_configs.py` updated to include `economic_aggregate` in `econ_roles` and to handle all three aggregate role types identically to their non-aggregate counterparts. Full network behavior is unchanged.

**Affected sweeps and their validity:**

| Sweep | Network | Validity |
|-------|---------|----------|
| `exploratory_sweep_lite` | lite | ❌ Invalid — also had economic_split code bug; doubly broken |
| `targeted_sweep2b_pool_ideology` | lite | ⚠️ Partially valid — pool params correct; economic context wrong |
| `targeted_sweep3_econ_friction` | lite | ❌ **Fully invalidated** — the parameters under test (econ_inertia, econ_switching_threshold) were never applied; conclusions cannot be drawn |
| `targeted_sweep5_lite_econ_threshold` | lite | ❌ **Fully invalidated** — economic_split was never varying; all 8 scenarios ran identical economic conditions |
| All full-network sweeps | full | ✅ Valid — role names matched throughout |

---

## Overview

This document summarizes findings from four parameter sweeps exploring Bitcoin fork dynamics:

| Sweep | Scenarios | Network | Duration | Difficulty Retarget | Economic Split | Status |
|-------|-----------|---------|----------|---------------------|----------------|--------|
| realistic_sweep2 | 50 | 60 nodes | 30 min | 144 blocks (~5 min) | Bug (not applied) | Complete |
| exploratory_sweep_lite | 50 | 25 nodes | 42 min | 144 blocks (~5 min) | Bug (not applied) | Complete |
| realistic_sweep3 | 8 | 60 nodes | 134 min | **2016 blocks (~67 min)** | Fixed | Partial |
| realistic_sweep3_rapid | 50 | 60 nodes | 30 min | 144 blocks (~5 min) | **Fixed** | Complete |
| **balanced_baseline** | 27 | 24 nodes | 30 min | 144 blocks (~5 min) | N/A (50/50) | **Complete** |
| **targeted_sweep1** | 45 | 60 nodes | 30 min | 144 blocks (~5 min) | Fixed | **Complete** |
| **targeted_sweep2** | 42 | 60 nodes | 30 min | 144 blocks (~5 min) | Fixed | **Complete** |
| **targeted_sweep2b** | 20 | 25 nodes | 30 min | 144 blocks (~5 min) | Fixed | ⚠️ Partial — pool params valid; econ context wrong (role-name bug) |
| **targeted_sweep3** | 16 | 25 nodes | 30 min | 144 blocks (~5 min) | Fixed | ❌ **INVALIDATED** — econ friction params not applied (role-name bug) |
| **targeted_sweep3b** | 4 | 60 nodes | 30 min | 144 blocks (~5 min) | Fixed | **Complete (valid)** |
| **targeted_sweep4** | 35 | 60 nodes | 30 min | 144 blocks (~5 min) | Fixed | **Complete** |
| **targeted_sweep5** | 36 | 60 nodes | 30 min | 144 blocks (~5 min) | Fixed | **Complete** |
| **targeted_sweep6** | 8 | 25 nodes | 30 min | 144 blocks (~5 min) | Fixed | ❌ **INVALIDATED** — economic_split not applied (role-name bug) |

**Total: 347 scenarios** (323 with full analysis)

### Sweep Configuration Notes

**realistic_sweep3** uses realistic Bitcoin difficulty dynamics (2016-block retarget intervals) while others use accelerated 144-block retargets. This matters because:
- More pronounced revenue divergence before difficulty catches up on the losing fork
- Fee counter-pressure sustained longer (~67 min vs ~5 min per adjustment)
- Emergency Difficulty Adjustment (EDA) events possible in extreme hashrate scenarios

### Critical Discovery

The `realistic_sweep3_rapid` sweep used **corrected code** where `economic_split` was properly applied to the network. This revealed that **economic distribution is as important as hashrate** when the parameter actually varies.

---

## Baseline Measurements

### Balanced Baseline Sweep

To establish ground truth for stochastic variance, we created a **perfectly balanced network** where neither v27 nor v26 has any structural advantage.

#### Network Design

| Component | V27 | V26 |
|-----------|:---:|:---:|
| Mining Pools | 4 | 4 |
| Pool Hashrate | 47% | 47% |
| User Hashrate | 3% | 3% |
| **Total Hashrate** | **50%** | **50%** |
| Economic Nodes | 2 | 2 |
| User Nodes | 6 | 6 |

Pool naming: Alpha/Beta/Gamma/Delta (v27) vs Epsilon/Zeta/Eta/Theta (v26), each side with 20% + 14% + 8% + 5% = 47% hashrate.

#### Results (n=27 valid runs)

| Metric | Value |
|--------|:------|
| Starting Hashrate | 47% / 47% |
| Final Hashrate | 47% / 47% (unchanged) |
| Economic Cascades | **0** |
| Reorgs | **0** |

#### Block Share Distribution

| Statistic | Value |
|-----------|:-----:|
| Mean | 48.5% v27 |
| **Std Dev** | **3.3%** |
| Min | 43.6% |
| Max | 55.5% |

#### Win Distribution

| Winner | Count | Percentage |
|--------|:-----:|:----------:|
| v27 | 10 | 37% |
| v26 | 15 | 56% |
| Tie | 2 | 7% |

#### Key Findings

1. **Perfect Stability**: With balanced starting hashrate, the economic cascade mechanism **never triggers**. All 27 runs maintained exactly 47/47 hashrate throughout.

2. **Stochastic Variance Measured**: σ(block_share) = **3.3%** — this is pure mining randomness.

3. **No Economic Dynamics**: Zero reorgs, zero cascades — the balanced network produces static equilibrium.

4. **Cascade Trigger Requires Imbalance**: The first 3 runs used a broken config with 46/52 starting hashrate. These showed cascades (2/3 runs), while all 27 balanced runs showed none. Even a ~6% initial imbalance is enough to trigger cascade dynamics.

#### Implications for Parameter Sweeps

| Observation | Threshold |
|-------------|-----------|
| Block share variance > 3.3% | Parameter influence detected |
| Any reorg events | Economic dynamics active |
| Hashrate shift from starting values | Cascade mechanism triggered |
| Outcome rate deviating from ~50/50 | Structural bias present |

#### Data Location

| File | Description |
|------|-------------|
| `balanced_baseline_sweep/results/analysis/` | Analysis outputs |
| `networks/balanced-baseline/network.yaml` | Symmetric network definition |

---

## Targeted Threshold Mapping

### targeted_sweep1: Economic × Committed Split Grid

Following the recommendations from earlier sweeps, this targeted sweep maps the interaction between `economic_split` and `pool_committed_split` with fixed hashrate disadvantage for v27.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **economic_split** | 0.35, 0.50, 0.60, 0.70, 0.82 (5 levels) |
| **pool_committed_split** | 0.20, 0.30, 0.38, 0.43, 0.47, 0.52, 0.58, 0.65, 0.75 (9 levels) |
| **hashrate_split** | **Fixed at 0.25** (v26 starts with 75% hashrate advantage) |
| Scenarios | 45 total (5 × 9 grid) |

This isolates the cascade mechanism: can economic majority + committed pool support overcome a 3:1 hashrate disadvantage?

#### Results Grid

```
                              pool_committed_split
economic_split   0.20  0.30  0.38  0.43  0.47  0.52  0.58  0.65  0.75
     0.35         26    26    26    26    26    26    26    26    26    ← v26 wins all
     0.50         26    27    27    27    27    27    27    27    27    ← threshold ~0.20–0.30
     0.60         27    26    26    26    26    26    26    26    26    ← INVERTED
     0.70         27    26*   26*   26*   26*   26*   26    26    26    ← INVERTED
     0.82         27    27    27    27    27    27    27    27    27    ← v27 wins all
```

Legend: `26` = v26_dominant, `27` = v27_dominant
`*` = v26_dominant but with partial hashrate switching (v27 retains ~34.7% final hashrate)

#### Overall Outcome Distribution

| Outcome | Count | Percentage |
|---------|:-----:|:----------:|
| v27_dominant | 20 | 44.4% |
| v26_dominant | 25 | 55.6% |

#### Key Finding: Non-Monotonic Relationship and Inversion

**The effect of `pool_committed_split` is non-monotonic and INVERTS between econ=0.50 and econ=0.60:**

| Economic Level | Committed Effect | Interpretation |
|----------------|------------------|----------------|
| econ=0.35 (minority) | No cascade possible | Economics too weak; v26 wins all |
| econ=0.50 (parity) | Higher committed → v27 wins | Threshold at commit ~0.20–0.30 |
| econ=0.60–0.70 (majority) | **Lower committed → v27 wins** | **Inverted: only commit=0.20 produces v27 win** |
| econ=0.82 (strong majority) | Committed irrelevant → v27 wins | Economic signal dominates; v27 wins all |

#### Mechanism: The Foundry Flip-Point

The inversion is caused by how pools are assigned based on cumulative hashrate position. With pool_neutral_pct=30%, the committed pool hashrate (70%) is split into v27-preferring and v26-preferring zones. The largest pool, Foundry (30% of total hashrate), crosses from v26-preferring to v27-preferring at:

```
pool_committed_split × 0.70 > 0.15  →  commit > 0.214
```

**At commit=0.20 (below flip-point):**
- Foundry is assigned v26-preferring ideology
- With 60–70% economic support for v27, the v27 price premium exceeds Foundry's max_loss tolerance
- Foundry cannot profitably abandon v27 → effectively locked on v27 chain
- Result: v27 wins via economic pressure cascade

**At commit=0.30–0.75 (above flip-point):**
- Foundry is assigned v27-preferring ideology → holds v27 chain
- BUT: the remaining v26-committed block (AntPool 18% + F2Pool 15% + ViaBTC 7% = **40% of total hashrate**) now has full ideological commitment to v26
- This 40% committed block is too large to break at 60–70% economic signal (max_loss=0.26 not exceeded)
- Result: v26 maintains dominance despite economic minority

**At econ=0.82:** Economic signal strong enough to break even a 40% committed v26 block → v27 wins regardless.

**At econ=0.50:** Lower price pressure but Foundry's v27-preferring commitment (at commit≥0.30) is sufficient for cascade with neutral pools.

#### econ=0.70 Detail: Partial Cascade Zone

At commit=0.30–0.52, econ=0.70, the outcome is v26_dominant but with **partial hashrate switching**:
- v27 retains ~34.7% final hashrate (AntPool defects from v26 partially)
- 7 reorgs occur (active but incomplete cascade)
- Still resolves to v26_dominant due to v26's remaining block strength

This is the transition zone at 70% economics — sufficient to cause significant instability but not enough to fully flip.

#### Threshold Analysis

| Dimension | Threshold | Notes |
|-----------|:---------:|-------|
| **economic_split** | ~0.35–0.50 (lower bound) | Below 0.50, v27 cannot overcome 75% hashrate disadvantage |
| **economic_split** | ~0.70–0.82 (upper bound) | Above 0.82, v27 wins regardless of pool commitment |
| **pool_committed_split flip** | ~0.214 | Foundry assignment boundary; crossing this inverts outcomes at econ=0.60–0.70 |

#### Reorg Patterns

| Scenario Type | Avg Reorgs | Pattern |
|---------------|:----------:|---------|
| v27 wins (econ=0.82) | 4 | Clean economic dominance |
| v27 wins (econ=0.60/0.70, commit=0.20) | 12 | Full cascade, economic lock-in |
| v27 wins (econ=0.50, commit≥0.30) | 4–10 | Ideological cascade, many reorgs at low commit |
| v26 wins at econ=0.70, commit=0.30–0.52 | 7 | Partial cascade, unstable but v26 holds |
| v26 wins at econ=0.60, commit=0.30–0.75 | 8 | Active resistance cascade |
| v26 wins at econ=0.35 | 4 | Economic signal too weak, no cascade |

#### Implications

1. **Pool_committed_split is not a simple gatekeeper** — Its effect depends on the specific pool it causes to flip. The Foundry threshold (~0.214) is the critical structural boundary.

2. **High economic support with wrong committed levels can hurt v27** — At econ=0.60–0.70, increasing committed from 0.20 to 0.30 converts Foundry from "economically trapped on v27" to "ideologically committed to v27 but surrounded by a now-stronger v26 block."

3. **The 82% economic threshold overrides pool mechanics** — When economic support reaches ~82%, the price signal is strong enough to break even a 40% committed v26 block (max_loss constraint exceeded).

4. **Three distinct regimes exist:** (a) economics too weak → v26 always wins; (b) moderate economics → pool commitment inverts outcomes; (c) economics dominant → v27 always wins.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep1_committed_threshold/results/analysis/` | Analysis outputs |
| `targeted_sweep1_committed_threshold/scenarios.json` | Full scenario configurations |
| `targeted_sweep1_committed_threshold/results/analysis/sweep_data.csv` | Per-scenario metrics |

---

### targeted_sweep2: Hashrate × Economic Decision Surface

Following the targeted_sweep1 findings, this sweep maps the two most correlated parameters from the exploratory sweep — `hashrate_split` and `economic_split` — across a clean 6×7 grid with all other parameters fixed at medians.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **hashrate_split** | 0.15, 0.25, 0.35, 0.45, 0.55, 0.65 (6 levels) |
| **economic_split** | 0.35, 0.45, 0.50, 0.55, 0.60, 0.70, 0.82 (7 levels) |
| **pool_committed_split** | **Fixed at 0.50** (above Foundry flip-point ~0.214; normal operation regime) |
| Scenarios | 42 total (6 × 7 grid) |

`pool_committed_split=0.50` was chosen to sit above the Foundry flip-point (~0.214), keeping the system in the normal cascade regime and avoiding the inversion found in targeted_sweep1.

#### Results Grid

```
                                    economic_split
hashrate_split  0.35  0.45  0.50  0.55  0.60  0.70  0.82
  0.15           26    27    27    27    26*   26†   27
  0.25           26    27    27    27    26*   26†   27
  0.35           26    27    27    27    26*   26†   27
  0.45           26    27    27    27    26*   26†   27
  0.55           26    27    27    27    26*   26†   27
  0.65           26    27    27    27    26*   26†   27
```

Legend: `26` = v26_dominant, `27` = v27_dominant
`*` = v26 wins with 8 reorgs; v26 captures all hashrate (inversion zone)
`†` = v26 wins with 7 reorgs; v27 retains ~30% final hashrate (partial cascade)

#### The Headline Finding: hashrate_split Has No Causal Effect

**Outcomes are identical across all 6 hashrate levels at every economic level.** Not just the winner — the reorg counts, block shares, and final hashrate distributions are statistically identical (differences of ≤0.001 in block share, ≤7 in reorg_mass across a range of 1400–3600):

| economic_split | Reorg range | Block share range | Distinct outcomes |
|:--------------:|:-----------:|:-----------------:|:-----------------:|
| 0.35 | 4–4 | 0.126–0.126 | **1** |
| 0.45 | 10–10 | 0.613–0.613 | **1** |
| 0.50 | 10–10 | 0.613–0.614 | **1** |
| 0.55 | 10–10 | 0.612–0.614 | **1** |
| 0.60 | 8–8 | 0.344–0.347 | **1** |
| 0.70 | 7–7 | 0.457–0.460 | **1** |
| 0.82 | 4–4 | 0.848–0.849 | **1** |

This includes hash=0.65 where v27 starts with a significant hashrate advantage — it still produces identical outcomes to hash=0.15 where v27 starts at a 5.7:1 disadvantage.

**Implication:** The pool ideology structure (committed v26 block at ~36% of pool hashrate vs Foundry at 30% v27-committed) completely determines the outcome. Once the cascade dynamics engage, they run to the same conclusion regardless of starting hashrate.

#### Cross-Sweep Consistency Check

targeted_sweep2 at `hashrate_split=0.25` matches targeted_sweep1 at `pool_committed_split=0.52` exactly at every shared economic level:

| economic_split | targeted_sweep1 (commit=0.52) | targeted_sweep2 (hash=0.25) |
|:--------------:|:-----------------------------:|:----------------------------:|
| 0.35 | v26, 4 reorgs | v26, 4 reorgs |
| 0.50 | v27, 10 reorgs | v27, 10 reorgs |
| 0.60 | v26, 8 reorgs | v26, 8 reorgs |
| 0.70 | v26, 7 reorgs | v26, 7 reorgs |
| 0.82 | v27, 4 reorgs | v27, 4 reorgs |

#### Refined Economic Thresholds (at commit=0.50)

targeted_sweep2 adds `econ=0.45` and `econ=0.55` which targeted_sweep1 did not have, narrowing the transition bands:

| Transition | Previous estimate | Refined estimate |
|------------|:-----------------:|:----------------:|
| v26→v27 (lower win zone) | 0.35–0.50 | **0.35–0.45** |
| v27→v26 (inversion onset) | 0.55–0.60 | **0.55–0.60** (confirmed tight) |
| v26→v27 (upper win zone) | 0.70–0.82 | 0.70–0.82 (unchanged) |

#### Why hashrate_split Appeared Significant in the Exploratory Sweep

The +0.554 correlation from realistic_sweep3_rapid was almost certainly a confound from the LHS design. In Latin Hypercube Sampling, all parameters are drawn jointly from the full space. High hashrate_split scenarios in that sample also tended to have pool configurations (pool_committed_split, pool_ideology_strength) that independently favored v27. When hashrate_split is varied in isolation with all other parameters fixed, its effect is zero.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep2_hashrate_economic/results/analysis/` | Analysis outputs |
| `targeted_sweep2_hashrate_economic/scenarios.json` | Full scenario configurations |
| `targeted_sweep2_hashrate_economic/specs/targeted_sweep2_hashrate_economic.yaml` | Sweep spec |

---

### targeted_sweep2b: Pool Ideology Parameters

This sweep tests whether pool ideology parameters (`pool_ideology_strength` and `pool_max_loss_pct`) can influence outcomes when economic support is near the cascade threshold.

#### Background

An initial attempt (targeted_sweep2a at econ=0.65) showed no effect — the profitability gap was 10-45%, far exceeding any max_loss_pct tested. This redesign uses econ=0.78, closer to the v27 win threshold (~0.82), where the gap is small enough for ideology to matter.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **pool_ideology_strength** | 0.2, 0.4, 0.6, 0.8 (4 levels) |
| **pool_max_loss_pct** | 0.05, 0.15, 0.25, 0.35, 0.45 (5 levels) |
| **economic_split** | Fixed at 0.78 (near threshold) |
| **hashrate_split** | Fixed at 0.25 (v26 has 75% advantage) |
| **pool_committed_split** | Fixed at 0.35 |
| Network | lite (25 nodes) |
| Scenarios | 20 total (4 × 5 grid) |

#### Results Grid

```
                         pool_max_loss_pct
ideology_strength   0.05   0.15   0.25   0.35   0.45
       0.2           26     26     26     26     26    ← v26 wins ALL
       0.4           26     26     26     27     27    ← threshold at 0.35
       0.6           26     26     27     27     27    ← threshold at 0.25
       0.8           26     27     27     27     27    ← threshold at 0.15
```

Legend: `26` = v26_dominant, `27` = v27_dominant

#### Overall Outcome Distribution

| Outcome | Count | Percentage |
|---------|:-----:|:----------:|
| v27_dominant | 9 | 45% |
| v26_dominant | 11 | 55% |

#### Key Finding: Diagonal Decision Boundary

**Ideology and loss tolerance work together** — higher ideology strength lowers the required loss tolerance for v27 to win:

| Ideology Strength | Required max_loss_pct for v27 win |
|:-----------------:|:---------------------------------:|
| 0.2 | Never wins (even at 0.45) |
| 0.4 | ≥ 0.35 |
| 0.6 | ≥ 0.25 |
| 0.8 | ≥ 0.15 |

The threshold appears to follow approximately: **ideology × max_loss ≳ 0.12**

#### Correlations

| Parameter | Correlation with v27 hashrate |
|-----------|:-----------------------------:|
| pool_ideology_strength | **+0.584** |
| pool_max_loss_pct | **+0.569** |

Both are significant and roughly equal — they are **jointly necessary** for v27 to overcome the hashrate disadvantage at this economic level.

#### Cascade Signatures

| Outcome | Reorgs | v27 Final Hashrate | v27 Block Share |
|---------|:------:|:------------------:|:---------------:|
| v26_dominant | 4 | 0% | ~12.7% |
| v27_dominant | 10 | 86.4% (full flip) | ~61% |

When v27 wins, it's a complete cascade — all pool hashrate flips to v27.

#### Implications

1. **Ideology matters, but only near the economic threshold** — At econ=0.65, the profitability gap was too large for any ideology level to overcome. At econ=0.78, ideology becomes decisive.

2. **Both parameters are necessary** — High ideology (0.8) alone isn't enough if loss tolerance is too low (0.05). High loss tolerance (0.45) alone isn't enough if ideology is too low (0.2).

3. **The diagonal threshold** — The relationship suggests a multiplicative interaction: pools need both the willingness to sacrifice (ideology) AND the capacity to absorb losses (tolerance).

4. **Refines the economic threshold** — At econ=0.78 with favorable ideology (≥0.6) and loss tolerance (≥0.25), v27 can win. Without favorable ideology, the threshold remains at ~0.82.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep2b_pool_ideology/results/analysis/` | Analysis outputs |
| `targeted_sweep2b_pool_ideology/scenarios.json` | Full scenario configurations |
| `specs/targeted_sweep2b_pool_ideology.yaml` | Sweep spec |

---

### targeted_sweep3: Economic Friction Parameters

> ❌ **THIS SWEEP IS FULLY INVALIDATED** — See bug description in Executive Summary. The parameters under test (`econ_inertia` and `econ_switching_threshold`) were never applied to lite network economic nodes due to the role-name mismatch. All 16 scenarios ran with identical baked-in YAML values. No conclusions about economic friction can be drawn from this data. The finding "friction has no effect" is not supported — it is an artifact of the parameters literally not varying. See targeted_sweep3b for valid friction results on the full network.

This sweep was intended to test whether economic node friction parameters (`econ_inertia` and `econ_switching_threshold`) affect cascade dynamics.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **econ_inertia** | 0.05, 0.15, 0.25, 0.35 (4 levels) |
| **econ_switching_threshold** | 0.05, 0.12, 0.20, 0.28 (4 levels) |
| **economic_split** | Fixed at 0.65 (also not applied — baked-in ~43% v27 custody) |
| **hashrate_split** | Fixed at 0.25 |
| **pool_committed_split** | Fixed at 0.35 |
| Network | lite (25 nodes) |
| Scenarios | 16 total (4 × 4 grid) — all invalid |

#### Observed Results (invalid — do not use)

```
                    econ_switching_threshold
econ_inertia    0.05   0.12   0.20   0.28
    0.05         27     27     27     27
    0.15         27     27     27     27
    0.25         27     27     27     27
    0.35         27     27     27     27
```

All 16 ran the same effective conditions: baked-in lite YAML economic distribution (~43% v27 custody), `pool_profitability_threshold=0.16` correctly applied to pools. The uniform v27_dominant result reflects those fixed pool conditions, not friction variation.

#### Actual Explanation of Lite vs. Full Discrepancy

The previously noted "network size discrepancy" (lite → v27 wins at econ=0.65, full → v26 wins) was **not a network size effect**. It was caused by the role-name bug: the lite network's economic and user nodes were never reassigned by the sweep, so the effective economic conditions differed from what the scenario parameters specified. Sweep 3b (full network, 4 corners) remains valid and shows v26_dominant at these parameters regardless of friction values.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep3_econ_friction/results/analysis/` | Analysis outputs |
| `targeted_sweep3_econ_friction/scenarios.json` | Full scenario configurations |
| `specs/targeted_sweep3_econ_friction.yaml` | Sweep spec |

---

### targeted_sweep3b: Economic Friction Verification (Full Network)

This verification sweep confirms the network size discrepancy discovered in targeted_sweep3.

#### Background

Targeted_sweep3 on the lite network (25 nodes) showed v27 winning at econ=0.65, commit=0.35. However, targeted_sweep1 on the full network (60 nodes) showed v26 winning at similar parameters. This verification sweep runs 4 corner scenarios on the full network to confirm the discrepancy.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **econ_inertia** | 0.05, 0.35 (2 levels — corners only) |
| **econ_switching_threshold** | 0.05, 0.28 (2 levels — corners only) |
| **economic_split** | Fixed at 0.65 |
| **hashrate_split** | Fixed at 0.30 |
| **pool_committed_split** | Fixed at 0.35 |
| Network | **60 nodes (full network)** |
| Scenarios | 4 total (2 × 2 corners) |

#### Results Grid

```
                    econ_switching_threshold
econ_inertia       0.05       0.28
    0.05            26         26
    0.35            26         26
```

**All 4 scenarios: v26_dominant (100%)**

#### Key Finding: Network Size Affects Threshold

| Sweep | Network | Parameters | Result |
|-------|---------|------------|:------:|
| targeted_sweep3 | 25 nodes (lite) | econ=0.65, hash=0.25, commit=0.35 | **v27 wins** |
| **targeted_sweep3b** | **60 nodes (full)** | econ=0.65, hash=0.30, commit=0.35 | **v26 wins** |

The economic threshold for v27 to win is **higher on the full network** than on the lite network. At econ=0.65, commit=0.35:
- Lite network: v27 wins (cascade completes)
- Full network: v26 wins (cascade fails)

#### Friction Confirmation

Economic friction parameters still have no effect on outcomes:

| Metric | Value (all 4 scenarios) |
|--------|:-----------------------:|
| Outcome | v26_dominant |
| Reorgs | 8 |
| Final v27 hashrate | 0% |
| v27 block share | ~34.7% |

All four corners (fast/slow switching × low/high threshold) produce identical results.

#### Implications

1. **Economic friction confirmed irrelevant on the full network** — all 4 corners produce identical v26_dominant outcomes regardless of inertia or switching threshold values. This is a valid finding.

2. **Lite/full discrepancy now explained** — the difference between sweep3 (lite, v27 wins) and sweep3b (full, v26 wins) at econ=0.65 was NOT a network size effect. It was the role-name bug: lite economic nodes kept their baked-in YAML values (~43% v27 custody) rather than 65%. The full network correctly applied economic_split=0.65. The "threshold is network-dependent" conclusion was incorrect.

3. **Lite network sweeps require re-run** with the fixed `2_build_configs.py` before any lite/full comparison is meaningful.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep3b_econ_friction_verify/results/analysis/` | Analysis outputs |
| `targeted_sweep3b_econ_friction_verify/scenarios.json` | Full scenario configurations |
| `specs/targeted_sweep3b_econ_friction_verify.yaml` | Sweep spec |

---

### targeted_sweep3_neutral_pct: Pool Neutral Percentage

This sweep tests whether changing `pool_neutral_pct` (the fraction of pool hashrate assigned to profit-maximizing neutral pools) affects fork outcomes, particularly in the inversion zone (econ=0.60–0.70).

#### Background

At the baseline of neutral=30%, the pool structure is:
- v27-committed block: Foundry 30% = **30%**
- v26-committed block: AntPool 16.9% + F2Pool 10.9% = **35.9% (with ViaBTC+SpiderPool neutral)**
- Neutral block: ViaBTC 11.2% + SpiderPool 9.3% = **20.5%**

The hypothesis was that increasing neutral_pct moves AntPool and F2Pool from committed to neutral, collapsing the v26-committed block from 35.9% to 8.1% at neutral=50%. This should weaken the inversion zone resistance.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **pool_neutral_pct** | 10, 20, 30, 40, 50 (5 levels) |
| **economic_split** | 0.35, 0.45, 0.50, 0.55, 0.60, 0.70, 0.82 (7 levels) |
| **pool_committed_split** | Fixed at 0.50 (above Foundry flip-point) |
| Scenarios | 35 total (5 × 7 grid) |

#### Results Grid

```
                              economic_split
pool_neutral_pct  0.35  0.45  0.50  0.55  0.60  0.70  0.82
      10%          26    27    27    27    26    CON   27
      20%          26    27    27    27    26    26    27
      30%          26    27    27    27    26    26    27   ← baseline
      40%          26    27    27    27    26    26    27
      50%          26    27    27    27    26    26    27
```

Legend: `26` = v26_dominant, `27` = v27_dominant, `CON` = contested

#### Overall Outcome Distribution

| Outcome | Count | Percentage |
|---------|:-----:|:----------:|
| v27_dominant | 20 | 57.1% |
| v26_dominant | 14 | 40.0% |
| contested | 1 | 2.9% |

#### Finding 1: pool_neutral_pct Has No Effect on Outcomes

**Outcomes at neutral=20%, 30%, 40%, and 50% are completely identical** — 4 v27 wins and 3 v26 wins per row. Moving AntPool+F2Pool from committed to neutral (collapsing the v26-committed block from 35.9% to 8.1% of total hashrate) did not shift a single outcome.

This directly refutes the structural hypothesis. Neutral pools are profit-maximizers who follow price signals — at econ=0.60–0.70, v26's economic backing is sufficient to maintain a price premium that keeps neutral pools on v26 without any ideological commitment required.

#### Finding 2: The Inversion Zone Is Price-Signal Driven, Not Ideology Driven

The inversion zone (v26 wins at econ=0.60–0.70) persists at **all five neutral_pct levels** including neutral=50% where the v26-committed block is only 8.1%. This establishes that the inversion is a property of the economic price signal, not of the committed pool block structure.

The causal chain: v26 economic nodes (~40% weight at econ=0.60) → v26 coin price premium → neutral profit-maximizing pools follow v26 price → v26 maintains hashrate majority → cascade stalls.

#### Finding 3: pool_neutral_pct Controls Cascade Intensity

Increasing neutral_pct extends the cascade without changing its conclusion:

| pool_neutral_pct | Avg reorgs | Avg reorg_mass | Interpretation |
|:----------------:|:----------:|:--------------:|----------------|
| 10% | 4.0 | 1,300 | Large committed blocks resolve quickly |
| 20% | 6.9 | 2,074 | More swing voters → more oscillation |
| 30% | 7.6 | 2,166 | Baseline |
| 40% | 8.3 | 2,405 | More neutral = longer contested period |
| 50% | 8.9 | 2,602 | Most contested, slowest resolution |

More neutral pools means more hashrate available to switch back and forth during the cascade, extending the fight — but the same side wins each time.

#### Finding 4: neutral=10% at econ=0.70 Is Uniquely Contested

The sole deviation: at neutral=10%, econ=0.70, the result is `contested` (2 reorgs, reorg_mass=552). With a very large v27-committed block (Foundry alone = 38.1% of total hashrate at neutral=10%), Foundry has enough committed allies to resist the v26 economic signal at econ=0.70 — but not enough to fully win. Both sides pay significant opportunity costs: v27_pool_opportunity_cost=$12.3M, v26_pool_opportunity_cost=$8.0M. At neutral=20%+, the v27-committed block shrinks and v26 takes a clean win.

#### Inversion Zone Detail (econ=0.60 and 0.70)

| pool_neutral_pct | econ | outcome | reorgs | reorg_mass | v27 opp_cost | v26 opp_cost |
|:----------------:|:----:|:-------:|:------:|:----------:|:------------:|:------------:|
| 10% | 0.60 | v26 | 6 | 2,206 | $0 | $3.77M |
| 20% | 0.60 | v26 | 8 | 2,264 | $0 | $3.02M |
| 30% | 0.60 | v26 | 8 | 1,887 | $0 | $3.54M |
| 40% | 0.60 | v26 | 10 | 2,522 | $0 | $2.46M |
| 50% | 0.60 | v26 | 12 | 3,205 | $0 | $0.80M |
| 10% | 0.70 | contested | 2 | 552 | $12.29M | $7.99M |
| 20% | 0.70 | v26 | 8 | 2,292 | $0 | $6.47M |
| 30% | 0.70 | v26 | 7 | 1,469 | $0 | $7.42M |
| 40% | 0.70 | v26 | 10 | 2,522 | $0 | $5.17M |
| 50% | 0.70 | v26 | 12 | 3,205 | $0 | $1.67M |

Note: v26 opportunity costs decline as neutral_pct increases because there are fewer committed v26 pools remaining to absorb ideology-driven losses.

#### Implications

1. **pool_neutral_pct can be deprioritized as a threshold parameter** — it does not affect which fork wins at any tested economic level.

2. **Breaking the inversion zone requires economic means, not structural ones** — only `economic_split > ~0.82` or `pool_committed_split < 0.214` (Foundry flip-point) can resolve the inversion. Adjusting pool composition does not.

3. **Cascade duration scales with neutral_pct** — in a real fork scenario, a network with more profit-maximizing pools would experience longer, more chaotic transition periods even though the eventual winner is the same.

4. **The $12M+ combined opportunity cost at neutral=10%, econ=0.70** shows the contested zone is economically costly for both sides — this is the boundary condition where neither committed block is strong enough to win cleanly.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep3_neutral_pct/results/analysis/` | Analysis outputs |
| `targeted_sweep3_neutral_pct/scenarios.json` | Full scenario configurations |
| `specs/targeted_sweep3_neutral_pct.yaml` | Sweep spec |

---

### targeted_sweep4: User Behavior Parameters

This sweep tests whether user node parameters affect fork outcomes in a directional (asymmetric soft fork) topology.

#### Background

Earlier exploratory sweeps showed `user_ideology_strength` with a modest but consistent correlation (+0.16 to +0.23). This targeted sweep isolates the three user-facing parameters in a clean 3D grid using the full 60-node network to determine whether that signal was real or a confound.

The sweep uses the **directional (asymmetric) soft fork** model, which is the realistic soft fork topology:
- v27 nodes: `accepts_foreign_blocks: false` — strict, reject non-compliant (v26) blocks
- v26 nodes: `accepts_foreign_blocks: true` — permissive, accept any valid chain

This asymmetry reflects how soft forks actually work: the new stricter rules reject old blocks, while legacy nodes remain permissive and follow the longest valid chain.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **user_ideology_strength** | 0.2, 0.4, 0.6, 0.8 (4 levels) |
| **user_switching_threshold** | 0.06, 0.12, 0.18 (3 levels) |
| **user_nodes_per_partition** | 2, 6, 10 (3 levels) |
| **economic_split** | Fixed at 0.65 (cascade zone) |
| **hashrate_split** | Fixed at 0.25 (v26 hash dominant) |
| **pool_committed_split** | Fixed at 0.35 (above Foundry flip-point) |
| Network | 60-node full network |
| Scenarios | 36 total (4 × 3 × 3 grid) |

#### Results (36 of 36 — complete)

**All 36 scenarios → v26_dominant (100%)**

| Metric | Value (all scenarios) |
|--------|:---------------------:|
| Outcome | v26_dominant |
| Final v27 hashrate | **0.0%** |
| Final v27 economic share | ~62.15% (frozen) |
| v27_pool_opportunity_cost | $0 (all switched) |
| user_ideology_strength correlation | **0.000** |
| user_switching_threshold correlation | **0.000** |
| user_nodes_per_partition correlation | **0.000** |

Not only does the outcome not change — **no output metric shows any variation** across user parameters. The v27 hashrate always collapses to 0.0 and economic shares are identical across all rows.

#### Key Finding: User Nodes Have Zero Effect on Fork Outcomes

The exploratory sweep correlations (+0.16 to +0.23) for `user_ideology_strength` were a **confound from LHS co-sampling**, not a real causal effect. When user parameters are varied in isolation with all other parameters fixed, their effect is exactly zero.

| User parameter channel | Reality |
|---|---|
| Solo mining (~8.5% hashrate) | Too small — v26 has 75% pool hashrate; even all solo on v27 gives 33.5% vs 66.5% |
| Fee generation (tx volume) | After difficulty retarget, both forks hit ~6 bph → per-block fees equalize; no sustained differential |
| Sentiment / network signal | User nodes are not wired into the price oracle (`econ_f` comes from economic nodes only) |

The committed v27 pool tolerance (ideology=0.51 × max_loss=0.26 = **13.3%**) is less than the maximum price divergence the hashrate imbalance creates (~**22.2%**). Once pool switching begins, it cascades to completion regardless of what user nodes do.

#### What Would Be Required for Users to Matter

For user nodes to influence fork outcomes in the current model, one of the following would be needed:

1. **Much higher solo mining hashrate (~30–40%)** — at 8.5%, solo miners cannot shift the hashrate balance enough even with perfect fork alignment
2. **User activity wired into the price oracle** — currently only economic nodes (`econ_f`) drive price; a code change connecting user transaction volume to fork price would give users economic leverage
3. **Sustained fee differential** — only possible before difficulty retarget closes the block rate gap; the window is too short at current transaction_velocity levels
4. **UASF-style coercion mechanism** — if users could enforce miner compliance via block relay or peer banning, that is a fundamentally different model not present here

#### The "Users as Rule Makers" Narrative — A Critical Finding

A prominent narrative in Bitcoin governance holds that **economic full nodes are the real rule makers**: because they verify and reject invalid blocks, miners must follow user-defined rules or lose revenue. This is the theoretical basis for UASF (User Activated Soft Fork) arguments.

**This simulation challenges that narrative.** The results show:

1. **User nodes verify but cannot coerce** — rejecting a block only affects the rejecting node's local view. It does not prevent miners from earning revenue from other network participants who accept those blocks.

2. **The real leverage is economic gateways** — exchanges and large custodians (the "economic nodes" in this model) control where miners convert block rewards to fiat. They are the actual economic pressure point on miners. User nodes are not.

3. **The narrative conflates two distinct actor classes** — "users" and "economic nodes" are modeled separately here, and only economic nodes move pool decisions. The UASF narrative has force (to the extent it does) because exchanges and major economic actors also signaled alongside users in 2017. It was not the user nodes themselves — it was who they represented.

4. **Even 62% economic node support on v27 cannot overcome 75% hashrate on v26** at these parameters (econ=0.65, commit=0.35). User node preferences add nothing on top of that.

**Bottom line:** In a directional soft fork with realistic pool economics, fork outcomes are determined by hashrate commitment structure and economic gateway behavior. Individual user node preferences — regardless of ideology strength, switching threshold, or node count — are noise.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep4_user_behavior/results/analysis/` | Analysis outputs |
| `targeted_sweep4_user_behavior/results/sweep_data.csv` | Per-scenario metrics |
| `specs/targeted_sweep4_user_behavior.yaml` | Sweep spec |

---

### targeted_sweep5: Lite Economic Threshold (INVALIDATED)

> ❌ **THIS SWEEP IS FULLY INVALIDATED** — `economic_split` was never applied to lite network economic nodes due to the role-name bug. All 8 scenarios ran with the same baked-in YAML economic distribution (~43% v27 custody). The parameter being varied had no effect. Results cannot be used for any threshold comparison.

This sweep was intended to map the economic threshold on the lite network for comparison with the full network threshold (~0.82 from targeted_sweep1).

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **economic_split** | 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85 (8 levels) |
| **hashrate_split** | Fixed at 0.30 |
| **pool_profitability_threshold** | Fixed at 0.05 (low — pools switch at small profit edge) |
| **pool_committed_split** | Fixed at 0.35 |
| Network | lite (25 nodes) |
| Scenarios | 8 total — all invalid |

#### Observed Results (invalid — do not use)

**All 8 scenarios: v27_dominant (100%)**

The uniform v27_dominant result across the full 0.50–0.85 range appeared to suggest the lite network has no economic threshold. In reality:
- `economic_split` was never applied — all scenarios used ~43% v27 custody (baked-in YAML)
- `pool_profitability_threshold=0.05` WAS correctly applied to pools, causing pools to flip at any tiny price signal
- `hashrate_split=0.30` (v27 starts with more hashrate) WAS correctly applied
- The cascade completed due to pool dynamics alone, independent of economic conditions

#### What This Sweep Will Show After Fix

Once re-run with the corrected `2_build_configs.py`, this sweep will produce a valid economic threshold curve for the lite network. The threshold is expected to be lower than the full network's ~0.82, but the magnitude of that difference is currently unknown.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep5_lite_econ_threshold/results/analysis/` | Analysis outputs (invalid) |
| `targeted_sweep5_lite_econ_threshold/build_manifest.json` | Sweep configuration |

---

## Outcome Distribution

| Sweep | v27 Wins | v26 Wins | Contested |
|-------|----------|----------|-----------|
| realistic_sweep2 | 28 (56%) | 19 (38%) | 3 (6%) |
| exploratory_sweep_lite | 26 (52%) | 24 (48%) | 0 (0%) |
| realistic_sweep3_rapid | 25 (50%) | 22 (44%) | 3 (6%) |
| **Combined** | **79 (53%)** | **65 (43%)** | **6 (4%)** |

---

## Key Finding: Economic Split Changes Everything

### Before Fix (realistic_sweep2 + exploratory_sweep_lite)

| Parameter | Correlation | Interpretation |
|-----------|-------------|----------------|
| hashrate_split | **+0.83** | Dominant factor |
| user_ideology_strength | +0.20 | Secondary |
| econ_ideology_strength | -0.15 | Moderate |
| economic_split | ~0.06 | **No effect (bug)** |

### After Fix (realistic_sweep3_rapid)

| Parameter | Correlation | Interpretation |
|-----------|-------------|----------------|
| **economic_split** | **+0.666** | **Dominant — confirmed causal by targeted sweeps** |
| hashrate_split | +0.554 | **⚠️ CONFOUNDED** — targeted sweep shows no independent causal effect |
| pool_committed_split | +0.360 | **⚠️ SPURIOUS** — parameter was dead in this sweep (see note below) |
| econ_switching_threshold | +0.330 | Cascade speed |
| econ_inertia | -0.324 | Switching friction |

> **⚠️ Two confounded correlations in this sweep:**
> - `pool_committed_split` +0.360: Artifact of the dead-parameter bug in `2_build_configs.py`. Pool configs were identical regardless of the value. Corrected in targeted_sweep1.
> - `hashrate_split` +0.554: Likely a confound from LHS co-sampling. In the LHS design, higher hashrate scenarios happened to co-occur with pool configurations more favorable to v27. targeted_sweep2 varied hashrate_split from 0.15–0.65 in isolation and found **zero effect** on outcomes. The economic cascade mechanism, once triggered, runs to the same conclusion regardless of starting hashrate.

**The economic cascade mechanism is real.** When properly implemented, economic majority can overcome hashrate minority.

---

## Correlation Comparison Across All Sweeps

| Parameter | sweep2 | lite | rapid (fixed) | sweep3 (expected) | Notes |
|-----------|:------:|:----:|:-------------:|:-----------------:|-------|
| **hashrate_split** | +0.81 | +0.85 | ~~+0.55~~ ⚠️ | TBD | ⚠️ confounded in LHS; targeted sweep shows zero causal effect |
| **economic_split** | +0.03 | +0.09 | **+0.67** | **+0.67** | Only works when fixed; confirmed causal |
| **pool_committed_split** | +0.27* | +0.09 | ~~+0.36~~ ⚠️ | TBD | ⚠️ rapid value spurious (dead param bug); non-monotonic in targeted sweeps |
| user_ideology_strength | +0.17 | +0.23 | +0.16 | **0.000** | ⚠️ LHS confound; targeted sweep shows zero causal effect |
| econ_ideology_strength | -0.14 | -0.15 | - | ~-0.14 | Consistent |
| pool_max_loss_pct | +0.11 | +0.16 | - | - | Moderate effect |
| solo_miner_hashrate | low | low | - | **may rise** | v2 power user hashrate now meaningful |

*separation metric, not correlation

**Note:** realistic_sweep3 uses the same LHS sample (seed=42) as sweep2, enabling direct comparison when complete.

---

## The Economic Cascade Mechanism

The `realistic_sweep3_rapid` sweep revealed a crucial mechanism: **economic majority can flip hashrate allocation** through price signals.

### How It Works

1. Economic nodes prefer one fork → higher transaction fees on that fork
2. Higher fees → higher effective price for that fork's coin
3. Profit-driven pools see price difference → switch hashrate
4. More hashrate → more security → more economic confidence (feedback loop)

### Zone Analysis (from realistic_sweep3_rapid)

| Zone | n | v27 wins | contested | v26 wins |
|------|:-:|:--------:|:---------:|:--------:|
| low_hash + low_econ | 12 | 0 (0%) | 1 | **11 (92%)** |
| low_hash + **high_econ** | 12 | **6 (50%)** | 2 | 4 (33%) |
| **high_hash** + low_econ | 12 | 6 (50%) | 0 | 6 (50%) |
| **high_hash + high_econ** | 13 | **13 (100%)** | 0 | 0 |

**Key insight:** When hashrate and economics align, outcomes are deterministic. When they conflict, outcomes are ~50/50.

---

## The pool_committed_split Mechanism

> **⚠️ Revision:** Earlier analysis estimated a simple +0.50 threshold for pool_committed_split from realistic_sweep3_rapid. This was based on a **dead parameter** (pool configs were identical regardless of committed_split value due to a bug). The targeted sweep with the fixed parameter reveals a **non-monotonic** relationship.

**From targeted_sweep1 (45 scenarios, fixed hashrate_split=0.25):**

The pool_committed_split threshold is **not monotonic** — its effect depends on economic level:

| Economic Level | commit=0.20 | commit=0.30–0.75 | Interpretation |
|:--------------|:-----------:|:----------------:|----------------|
| econ=0.35 | v26 wins | v26 wins | Too weak for any cascade |
| econ=0.50 | v26 wins | **v27 wins** | Normal positive relationship |
| econ=0.60 | **v27 wins** | v26 wins | **INVERTED** |
| econ=0.70 | **v27 wins** | v26 wins | **INVERTED** |
| econ=0.82 | v27 wins | v27 wins | Strong enough for any config |

The critical structural point is at commit ≈ 0.21 where **Foundry (30% hashrate)** switches assignment from v26-preferring to v27-preferring. Crossing this boundary reorganizes which faction has the "committed anchor pool" and produces opposite outcomes at moderate economic levels (60–70%).

**The real gatekeeper is not a simple threshold but the pool-specific flip-point.**

---

## Consolidated Threshold Estimates

| Parameter | Threshold | v27 Favored When | Confidence |
|-----------|:---------:|------------------|------------|
| **hashrate_split** | ⚠️ No independent effect detected | N/A — confounded in LHS | Low (confounded) |
| **economic_split** | ~0.35–0.45 (lower win zone entry) | Higher | High (targeted sweep, n=42) |
| **economic_split** | ~0.55–0.60 (inversion onset) | — | High (confirmed by two sweeps) |
| **economic_split** | ~0.70–0.82 (upper win zone entry) | Higher | High (targeted sweep, n=45) |
| **pool_committed_split** | Non-monotonic — Foundry flip-point at ~0.214 | Depends on economic level | High (targeted sweep) |
| **pool_neutral_pct** | ⚠️ No independent effect on outcome | N/A — controls cascade intensity only | High (targeted sweep 4, n=35) |
| econ_inertia | ~0.18 | Lower | Medium |
| econ_switching_threshold | ~0.13 | Higher | Medium |
| **user_ideology_strength** | ⚠️ No independent effect detected | N/A — confounded in LHS; targeted sweep shows zero causal effect | High (targeted sweep 5, n=36) |
| econ_ideology_strength | ~0.40 | Lower | Medium |

---

## Fork Dynamics Model (Updated)

The model has three primary axes: economic_split (dominant), pool_committed_split (non-monotonic, structural), and hashrate_split (no independent causal effect detected).

```
PRIMARY DRIVER: economic_split
═══════════════════════════════════════════════════════════════

ZONE A: WEAK ECONOMICS (econ ≤ ~0.40)
┌────────────────────────────────────────────────────────────┐
│  economic_split ≤ ~0.40                                    │
│  → v26 wins regardless of hashrate or pool commitment      │
│  → 4 reorgs, v27 block share ~12.6%, no cascade           │
│  → Economic signal too weak to move any pools              │
└────────────────────────────────────────────────────────────┘

ZONE B: LOWER v27 WIN ZONE (econ ~0.45–0.55)
┌────────────────────────────────────────────────────────────┐
│  economic_split ~0.45–0.55 (at commit=0.50)               │
│  → v27 wins regardless of hashrate (tested 0.15–0.65)     │
│  → 10 reorgs, full cascade (v26 ends at 0% hashrate)      │
│  → Threshold exact: between econ=0.35 and econ=0.45        │
│                                                            │
│  pool_committed_split modifies this:                       │
│    commit < 0.30 → threshold rises; v27 may not win        │
│    commit ≥ 0.30 → full cascade at econ≥0.45              │
└────────────────────────────────────────────────────────────┘

ZONE C: INVERSION ZONE (econ ~0.60–0.70)
┌────────────────────────────────────────────────────────────┐
│  economic_split ~0.60–0.70, pool_committed_split ≥ 0.30   │
│  → COUNTER-INTUITIVE: v26 wins despite v27 economic lead   │
│  → Committed v26 block (AntPool+F2Pool ≈ 36% hashrate)    │
│    holds firm; 60–70% economic signal insufficient         │
│  → 7–8 reorgs, active but incomplete cascade              │
│  → hashrate_split still irrelevant (0.15–0.65 tested)     │
│  → pool_neutral_pct has no effect on outcome              │
│    (tested 10–50%; inversion zone persists at all levels) │
│                                                            │
│  Exception: pool_committed_split < 0.214                  │
│    → Foundry economically trapped on v27                  │
│    → Cascade succeeds, v27 wins (12 reorgs)               │
└────────────────────────────────────────────────────────────┘

ZONE D: UPPER v27 WIN ZONE (econ ≥ ~0.82)
┌────────────────────────────────────────────────────────────┐
│  economic_split ≥ ~0.82                                    │
│  → v27 wins regardless of hashrate or pool commitment      │
│  → 4 reorgs, clean cascade (price signal breaks all blocks) │
│  → Threshold exact: between econ=0.70 and econ=0.82        │
└────────────────────────────────────────────────────────────┘

HASHRATE EFFECT (across all zones):
┌────────────────────────────────────────────────────────────┐
│  hashrate_split tested: 0.15 → 0.65 (4.3:1 range)        │
│  → Zero effect on outcome, reorg count, or final state     │
│  → Pool ideology overrides initial hashrate distribution   │
│  → Once cascade engages, it runs to ideologically-         │
│    determined endpoint regardless of starting conditions   │
└────────────────────────────────────────────────────────────┘
```

---

## Reorg Analysis

From realistic_sweep3_rapid:

| Reorg Level | Scenarios | v27 Wins | v26 Wins | Contested |
|-------------|:---------:|:--------:|:--------:|:---------:|
| ≥5 reorgs (cascade active) | 21 | **18 (86%)** | 2 | 1 |
| 0 reorgs (no cascade) | 10 | 1 | **8 (80%)** | 1 |

**Reorgs are a signature of the economic cascade in action.** High reorg counts correlate with v27 victory because they indicate pools are switching in response to economic signals.

---

## Notable Anomalies

### sweep_0007 (realistic_sweep3_rapid) — Reverse Cascade
- Config: hashrate=90% v27, economic=7% v27
- Result: **v26 wins** with 7 reorgs, 437 orphans
- v26's 93% economic majority drove pools away from v27
- Final: v26 captures 100% hashrate despite starting with 10%

### sweep_0045 — Clean Hashrate Win
- Config: hashrate=98.5% v27, economic=19% v27
- Result: v27 wins with 0 reorgs
- Overwhelming hashrate prevents any cascade attempt

### sweep_0020 — Maximum Chaos
- Config: hashrate=84% v27, economic=24% v27, pool_committed_split=0.485
- Result: v26 wins after 13 reorgs (most in dataset)
- Near-threshold committed_split created prolonged instability

---

## Confidence Assessment

| Finding | Confidence | Evidence |
|---------|------------|----------|
| Hashrate matters | **Very High** | +0.55 to +0.85 across all sweeps |
| Economic split matters (when fixed) | **High** | +0.67 in fixed sweep |
| pool_committed_split threshold ~0.50 | **High** | Clear pattern in 9 cascade scenarios |
| Economic cascade mechanism | **High** | Demonstrated in multiple scenarios |
| User ideology effect | **None detected** | Zero correlation in targeted sweep (n=36); earlier +0.16 to +0.23 was LHS confound |
| Zone boundaries (50/50 splits) | **Medium** | Based on 50 scenarios |

---

## Implications for Real Fork Scenarios

1. **Neither hashrate nor economics alone determines outcomes** — both matter, and their interaction is complex.

2. **The ~50% threshold applies to both dimensions** — a fork needs roughly half of either hashrate or economic support to have a chance.

3. **Committed pools are the linchpin** — they enable or block the economic cascade. A fork with economic majority but without committed pool support will fail.

4. **Cascades create instability** — high-reorg scenarios indicate active competition. Clean wins (0 reorgs) occur when one side dominates both dimensions.

5. **Extreme hashrate dominance (>80%) is hard to overcome** — even strong economic opposition cannot trigger a cascade against overwhelming hashrate.

---

## Recommendations for Future Work

### 1. ~~Targeted Threshold Mapping~~ ✓ COMPLETE
- ~~Grid sweep around pool_committed_split [0.20–0.75] × economic_split [0.35–0.82]~~
- ~~Fixed hashrate_split=0.25 to isolate cascade dynamics~~
- **See targeted_sweep1 section above for results**

### 2. ~~Hashrate × Economic Decision Surface~~ ✓ COMPLETE
- ~~Grid sweep: hashrate_split [0.15–0.65] × economic_split [0.35–0.82]~~
- **Key finding: hashrate_split has no independent causal effect — pool ideology dominates**
- **See targeted_sweep2 section above for results**

### 3. ~~Pool Neutral Percentage~~ ✓ COMPLETE
- ~~Grid sweep: pool_neutral_pct [10–50] × economic_split [0.35–0.82]~~
- **Key finding: pool_neutral_pct has no effect on outcome — controls cascade intensity only; inversion zone persists at all levels**
- **See targeted_sweep4 section above for results**

### 4. Longer Duration Verification (realistic_sweep3)
- Same parameters but with 2016-block difficulty (realistic Bitcoin timing)
- Confirm findings hold at equilibrium, not just short-run dynamics
- Currently 8/50 scenarios complete; full results pending

### 4. Dynamic Scenarios
- Test scenarios where economic distribution shifts mid-simulation
- Model exchange announcements, institutional pivots

### 5. Difficulty Dynamics Analysis
When realistic_sweep3 completes, examine:
- Whether `hashrate_split` threshold shifts from ~0.46 (sweep2 baseline)
- EDA events in `partition_difficulty.json` for extreme hashrate scenarios
- Difficulty curve shapes responding to hashrate changes
- Extended fee counter-pressure effects on fork persistence

---

## Diagnostic Red Flags

When analyzing new sweep results, watch for these indicators of potential bugs:

| Red Flag | Indicates |
|----------|-----------|
| `economic_split` correlation ~0 | Economic split parameter not being applied |
| Identical difficulty curves across scenarios | Difficulty oracle not responding to hashrate |
| No EDA events in extreme hashrate scenarios | Emergency adjustment not firing |
| Contested rate stuck at 6% | Fee counter-pressure not extending fork persistence |
| `v27_econ_share` constant in sweep_data.csv | Economic nodes not following parameter |

---

## Data Sources

| Sweep | Location | Scenarios | Notes |
|-------|----------|-----------|-------|
| realistic_sweep2 | `realistic_sweep2/results/analysis/` | 50 | economic_split bug |
| exploratory_sweep_lite | `exploratory_sweep_lite/results/analysis/` | 50 | economic_split bug |
| realistic_sweep3 | `realistic_sweep3/results/` | 8 | Long duration, 2016-block difficulty, incomplete |
| realistic_sweep3_rapid | `realistic_sweep3_rapid/results/analysis/` | 50 | **Fixed code** |
| balanced_baseline | `balanced_baseline_sweep/results/analysis/` | 27 | **Stochastic variance baseline** |
| **targeted_sweep1** | `targeted_sweep1_committed_threshold/results/analysis/` | 45 | **Economic × committed grid** |
| **targeted_sweep2** | `targeted_sweep2_hashrate_economic/results/analysis/` | 42 | **Hashrate × economic grid — hashrate shown to be non-causal** |
| **targeted_sweep2b** | `targeted_sweep2b_pool_ideology/results/analysis/` | 20 | **Pool ideology × loss tolerance grid (lite network)** |
| **targeted_sweep3** | `targeted_sweep3_econ_friction/results/analysis/` | 16 | **Economic friction grid (lite network) — friction has no effect** |
| **targeted_sweep3b** | `targeted_sweep3b_econ_friction_verify/results/analysis/` | 4 | **Friction verification (full network) — confirms network size effect** |
| **targeted_sweep4** | `targeted_sweep3_neutral_pct/results/analysis/` | 35 | **Pool neutral_pct × economic grid — neutral_pct has no effect on outcome** |
| **targeted_sweep5** | `targeted_sweep4_user_behavior/results/analysis/` | 36 | **User behavior 3D grid — user nodes have zero causal effect on fork outcomes** |
| **targeted_sweep6** | `targeted_sweep5_lite_econ_threshold/results/analysis/` | 8 | ❌ **INVALIDATED** — lite network role-name bug; economic_split was dead |

### Network Versions

**balanced-baseline** (used in balanced_baseline_sweep):
- 24 nodes, perfectly symmetric (12 per partition)
- 4 pools per side: 20% + 14% + 8% + 5% = 47% each
- 2 economic nodes per side with equal custody
- 6 user nodes per side with 3% hashrate each
- No structural advantage for either fork
- Purpose: Measure stochastic variance baseline

**realistic-economy-lite** (used in targeted_sweep2b, targeted_sweep3, targeted_sweep6, exploratory_sweep_lite):
- 25 nodes, 8 mining pools (all 8 pools identical to full network)
- 4 economic nodes (consolidated from 24 in full network) using role `economic_aggregate`
- 13 user nodes (consolidated from 28) using roles `power_user_aggregate`, `casual_user_aggregate`
- 86.4% total pool hashrate preserved
- ⚠️ **Role-name mismatch bug (fixed March 2026):** The lite network's aggregate roles (`economic_aggregate`, `power_user_aggregate`, `casual_user_aggregate`) were not handled by `2_build_configs.py`. All lite sweeps prior to the fix ran with baked-in YAML values for economic and user nodes. Only pool parameters and hashrate_split were correctly overridden. Fix applied: these role types now map to the same handlers as their non-aggregate counterparts.

**realistic-economy-v2** (used in sweep3, sweep3_rapid):
- Power user hashrates now meaningful (e.g., node-0048: 0.05% → 7.8%)
- All nodes have `representation_tier` (1=direct actors, 2=aggregated populations)
- User nodes have `represents_count` (power_user=400 real users, casual_user=1250)
- SpiderPool replaces Binance Pool
- Institutional custody rebalanced (node-0043: 620K → 230K BTC)

**realistic-economy-v1** (used in sweep2):
- Lower power user hashrates
- No representation metadata

---

## Appendix: Parameter Definitions

| Parameter | Range | Description |
|-----------|-------|-------------|
| economic_split | 0-1 | Fraction of economic custody starting on v27 |
| hashrate_split | 0-1 | Fraction of initial pool hashrate on v27 |
| pool_ideology_strength | 0.1-0.9 | How much pools sacrifice for ideology |
| pool_profitability_threshold | 2-30% | Min profit advantage for pools to switch |
| pool_max_loss_pct | 2-50% | Max revenue loss pools tolerate for ideology |
| pool_committed_split | 0-1 | Fraction of committed pool hashrate preferring v27 |
| pool_neutral_pct | 10-50% | Percentage of pools that are neutral/rational |
| econ_ideology_strength | 0-0.8 | How much economic nodes sacrifice for ideology |
| econ_inertia | 5-30% | Switching friction (infrastructure costs) |
| econ_switching_threshold | 2-25% | Min price advantage for economic nodes to switch |
| user_ideology_strength | 0.1-0.9 | How much users sacrifice for ideology |
| transaction_velocity | 0.1-0.9 | Fee-generating transaction rate |

---

*Analysis compiled February-March 2026*
