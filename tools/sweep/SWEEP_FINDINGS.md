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
2. **pool_committed_split has a non-monotonic effect** — it inverts at moderate economic levels due to pool-specific flip-points (see Targeted Sweep 1 findings)
3. **hashrate_split has no independent causal effect** — targeted grid sweep across 0.15–0.65 produced identical outcomes at every economic level (see Targeted Sweep 2 findings)
4. High reorg counts (5+) correlate with v27 victory (86% of cascade scenarios in exploratory sweep)

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

**The inversion is caused by a pool flip-point:** Foundry (30% of pool hashrate) switches from v26-preferring to v27-preferring at pool_committed_split ≈ 0.21. At commit=0.20 with strong economics, Foundry stays on v27 (economically trapped there). At commit≥0.30, Foundry is v27-committed but the remaining v26 bloc (AntPool+F2Pool+ViaBTC ≈ 40% hashrate) is large enough to resist the cascade at 60–70% economic strength.

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

**Total: 272 scenarios** (264 with full analysis)

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

### Targeted Sweep 1: Economic × Committed Split Grid

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
- BUT: the remaining v26-committed bloc (AntPool 18% + F2Pool 15% + ViaBTC 7% = **40% of total hashrate**) now has full ideological commitment to v26
- This 40% committed bloc is too large to break at 60–70% economic signal (max_loss=0.26 not exceeded)
- Result: v26 maintains dominance despite economic minority

**At econ=0.82:** Economic signal strong enough to break even a 40% committed v26 bloc → v27 wins regardless.

**At econ=0.50:** Lower price pressure but Foundry's v27-preferring commitment (at commit≥0.30) is sufficient for cascade with neutral pools.

#### econ=0.70 Detail: Partial Cascade Zone

At commit=0.30–0.52, econ=0.70, the outcome is v26_dominant but with **partial hashrate switching**:
- v27 retains ~34.7% final hashrate (AntPool defects from v26 partially)
- 7 reorgs occur (active but incomplete cascade)
- Still resolves to v26_dominant due to v26's remaining bloc strength

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

2. **High economic support with wrong committed levels can hurt v27** — At econ=0.60–0.70, increasing committed from 0.20 to 0.30 converts Foundry from "economically trapped on v27" to "ideologically committed to v27 but surrounded by a now-stronger v26 bloc."

3. **The 82% economic threshold overrides pool mechanics** — When economic support reaches ~82%, the price signal is strong enough to break even a 40% committed v26 bloc (max_loss constraint exceeded).

4. **Three distinct regimes exist:** (a) economics too weak → v26 always wins; (b) moderate economics → pool commitment inverts outcomes; (c) economics dominant → v27 always wins.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep1_committed_threshold/results/analysis/` | Analysis outputs |
| `targeted_sweep1_committed_threshold/scenarios.json` | Full scenario configurations |
| `targeted_sweep1_committed_threshold/results/analysis/sweep_data.csv` | Per-scenario metrics |

---

### Targeted Sweep 2: Hashrate × Economic Decision Surface

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

**Implication:** The pool ideology structure (committed v26 bloc at ~36% of pool hashrate vs Foundry at 30% v27-committed) completely determines the outcome. Once the cascade dynamics engage, they run to the same conclusion regardless of starting hashrate.

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
| user_ideology_strength | +0.17 | +0.23 | +0.16 | ~+0.16 | Consistent |
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
| **pool_neutral_pct** | ~30% | Higher | High |
| econ_inertia | ~0.18 | Lower | Medium |
| econ_switching_threshold | ~0.13 | Higher | Medium |
| user_ideology_strength | ~0.50 | Higher | Medium |
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
│  → Committed v26 bloc (AntPool+F2Pool ≈ 36% hashrate)     │
│    holds firm; 60–70% economic signal insufficient         │
│  → 7–8 reorgs, active but incomplete cascade              │
│  → hashrate_split still irrelevant (0.15–0.65 tested)     │
│                                                            │
│  Exception: pool_committed_split < 0.214                  │
│    → Foundry economically trapped on v27                  │
│    → Cascade succeeds, v27 wins (12 reorgs)               │
└────────────────────────────────────────────────────────────┘

ZONE D: UPPER v27 WIN ZONE (econ ≥ ~0.82)
┌────────────────────────────────────────────────────────────┐
│  economic_split ≥ ~0.82                                    │
│  → v27 wins regardless of hashrate or pool commitment      │
│  → 4 reorgs, clean cascade (price signal breaks all blocs) │
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
| User ideology effect | **Medium-High** | Consistent +0.16 to +0.23 |
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

### 3. Longer Duration Verification (realistic_sweep3)
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

### Network Versions

**balanced-baseline** (used in balanced_baseline_sweep):
- 24 nodes, perfectly symmetric (12 per partition)
- 4 pools per side: 20% + 14% + 8% + 5% = 47% each
- 2 economic nodes per side with equal custody
- 6 user nodes per side with 3% hashrate each
- No structural advantage for either fork
- Purpose: Measure stochastic variance baseline

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
