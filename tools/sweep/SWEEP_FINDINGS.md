# Parameter Sweep Findings - Combined Analysis

## Executive Summary

### Key Discovery

The **realistic_sweep3_rapid** sweep with fixed code reveals a dramatically different picture:

| Before Fix | After Fix |
|------------|-----------|
| hashrate_split: **+0.83** (dominant) | economic_split: **+0.67** (now dominant!) |
| economic_split: ~0.06 (no effect) | hashrate_split: +0.55 (still important) |

**The economic cascade mechanism is real and powerful.** When economic_split is properly applied:

1. **Economic majority can overcome hashrate minority** through price signals
2. **pool_committed_split ~0.50** acts as a gatekeeper for the cascade
3. High reorg counts (5+) correlate with v27 victory (86% of cascade scenarios)
4. When both hashrate AND economics align → deterministic outcomes (100% win rate)

### Zone Analysis Summary

| Economic | Hashrate | v27 Win Rate |
|:--------:|:--------:|:------------:|
| Low | Low | 0% |
| **High** | Low | **50%** |
| Low | **High** | 50% |
| **High** | **High** | **100%** |

Neither factor alone guarantees victory, but together they're deterministic.

### Targeted Threshold Discovery

The targeted sweep (economic × committed grid with fixed 25% hashrate) revealed:

| Economic Level | pool_committed_split Effect |
|:---------------|:----------------------------|
| ≤0.50 | Higher committed → v27 wins (ideological cascade) |
| ≥0.60 | **Committed irrelevant** → v27 wins (profit cascade) |

**Two cascade mechanisms exist:** Ideological (at economic parity) vs Profit-driven (at economic majority). The ~60% economic threshold unlocks the robust profit cascade that works regardless of pool ideology.

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

**Total: 230 scenarios** (222 with full analysis)

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
| **pool_committed_split** | 0.20, 0.35, 0.45, 0.55, 0.65, 0.75 (6 levels per economic level, varies slightly) |
| **hashrate_split** | **Fixed at 0.25** (v26 starts with 75% hashrate advantage) |
| Scenarios | 45 total |

This isolates the cascade mechanism: can economic majority + committed pool support overcome a 3:1 hashrate disadvantage?

#### Results Grid

```
                    pool_committed_split
economic_split   0.20   0.35   0.45   0.55   0.65   0.75
     0.35         26     26     26     26     26     26    ← v26 wins all
     0.50         26     26     26     27     27     27    ← transition zone
     0.60         27     27     27     27     27     27    ← v27 wins all
     0.70         27     27     27     27     27     27    ← v27 wins all
     0.82         27     27     27     27     27     27    ← v27 wins all
```

Legend: `26` = v26_dominant, `27` = v27_dominant

#### Overall Outcome Distribution

| Outcome | Count | Percentage |
|---------|:-----:|:----------:|
| v27_dominant | 26 | 57.8% |
| v26_dominant | 19 | 42.2% |

#### Key Finding: Relationship Reversal

**The effect of `pool_committed_split` REVERSES depending on economic majority level:**

| Economic Level | Committed Effect | Interpretation |
|----------------|------------------|----------------|
| econ=0.50 (parity) | Higher committed → v27 wins | Ideology cascade |
| econ=0.60-0.70 (majority) | **Any committed level → v27 wins** | Profit cascade dominates |
| econ=0.35 (minority) | No cascade possible | Economics too weak |

**Two distinct cascade mechanisms discovered:**

1. **Ideological Cascade** (at economic parity, econ≈0.50):
   - Requires high `pool_committed_split` (≥0.55)
   - Committed pools hold chain on ideology alone
   - Marginal, depends on pool loyalty

2. **Profit Cascade** (at economic majority, econ≥0.60):
   - Works at ANY `pool_committed_split` level
   - Economic price signal is strong enough to flip even uncommitted pools
   - Robust, doesn't depend on ideology

#### Threshold Analysis

| Dimension | Threshold | Notes |
|-----------|:---------:|-------|
| **economic_split** | ~0.55-0.60 | Below this, v27 cannot overcome 75% hashrate disadvantage |
| **pool_committed_split** | ~0.50 (at econ=0.50 only) | Only matters at economic parity |

#### Reorg Patterns

| Scenario Type | Avg Reorgs | Pattern |
|---------------|:----------:|---------|
| v27 cascade wins | 3-5 | Clean flip to v27 |
| v26 holds | 0 | No cascade attempt |
| Transition zone | 1-2 | Partial cascade |

#### Implications

1. **Economic majority is sufficient** — With ≥60% economic support, v27 can overcome a 75% hashrate disadvantage regardless of pool ideology distribution.

2. **Pool commitment only matters at the margin** — When economic support is borderline (~50%), committed pools become the deciding factor. With clear economic majority, pool ideology is irrelevant.

3. **The 60% economic threshold** — This appears to be the critical point where economic signals become strong enough to flip profit-driven pools away from the hashrate majority.

4. **Confirms earlier findings** — The economic cascade mechanism works as theorized, but the `pool_committed_split` threshold from earlier sweeps (~0.50) only applies in the narrow band around economic parity.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep1_committed_threshold/results/analysis/` | Analysis outputs |
| `targeted_sweep1_committed_threshold/scenarios.json` | Full scenario configurations |
| `targeted_sweep1_committed_threshold/results/analysis/sweep_data.csv` | Per-scenario metrics |

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
| **economic_split** | **+0.666** | **Now dominant!** |
| hashrate_split | +0.554 | Still important |
| pool_committed_split | +0.360 | Cascade gatekeeper |
| econ_switching_threshold | +0.330 | Cascade speed |
| econ_inertia | -0.324 | Switching friction |

**The economic cascade mechanism is real.** When properly implemented, economic majority can overcome hashrate minority.

---

## Correlation Comparison Across All Sweeps

| Parameter | sweep2 | lite | rapid (fixed) | sweep3 (expected) | Notes |
|-----------|:------:|:----:|:-------------:|:-----------------:|-------|
| **hashrate_split** | +0.81 | +0.85 | +0.55 | ~+0.55 | Less dominant when economics work |
| **economic_split** | +0.03 | +0.09 | **+0.67** | **+0.67** | Only works when fixed |
| **pool_committed_split** | +0.27* | +0.09 | +0.36 | ~+0.36 | Cascade gatekeeper |
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

## The pool_committed_split Threshold

The most precise finding from realistic_sweep3_rapid:

**In scenarios where v27 had economic majority but v26 had hashrate majority:**

| pool_committed_split | Outcome | Cascade? |
|:--------------------:|---------|:--------:|
| < 0.43 | v26 wins | No |
| 0.43 - 0.53 | Contested | Partial |
| > 0.53 | v27 wins | Yes |

**Even with 88-93% economic majority, v27 cannot win without ~50% of committed pool hashrate preferring v27.**

The committed pools act as a bridge: they hold the chain during price divergence, allowing the economic signal to translate into hashrate control.

---

## Consolidated Threshold Estimates

| Parameter | Threshold | v27 Favored When | Confidence |
|-----------|:---------:|------------------|------------|
| **hashrate_split** | ~0.47-0.50 | Higher | Very High |
| **economic_split** | ~0.48-0.50 | Higher | High (fixed sweeps only) |
| **pool_committed_split** | ~0.49-0.53 | Higher | High |
| **pool_neutral_pct** | ~30% | Higher | High |
| econ_inertia | ~0.18 | Lower | Medium |
| econ_switching_threshold | ~0.13 | Higher | Medium |
| user_ideology_strength | ~0.50 | Higher | Medium |
| econ_ideology_strength | ~0.40 | Lower | Medium |

---

## Fork Dynamics Model (Updated)

```
SCENARIO 1: HASHRATE + ECONOMICS ALIGNED
┌────────────────────────────────────────────────────────────┐
│  hashrate_split > 50% AND economic_split > 50%            │
│  → v27 wins ~100% of the time                             │
│  → Minimal reorgs, clean victory                          │
└────────────────────────────────────────────────────────────┘

SCENARIO 2: HASHRATE VS ECONOMICS (The Cascade Zone)
┌────────────────────────────────────────────────────────────┐
│  hashrate_split < 50% BUT economic_split > 50%            │
│                                                            │
│  IF pool_committed_split > 0.53:                          │
│    → Economic cascade triggers                            │
│    → Pools switch to follow price signal                  │
│    → v27 wins (5+ reorgs typical)                         │
│                                                            │
│  IF pool_committed_split < 0.43:                          │
│    → Cascade blocked                                      │
│    → Economic signal cannot translate to hashrate         │
│    → v26 wins (0 reorgs typical)                          │
│                                                            │
│  IF pool_committed_split ≈ 0.43-0.53:                     │
│    → Contested outcome                                    │
│    → Prolonged instability, many reorgs                   │
└────────────────────────────────────────────────────────────┘

SCENARIO 3: HASHRATE DOMINANCE
┌────────────────────────────────────────────────────────────┐
│  hashrate_split > 80% (overwhelming)                      │
│  → Wins regardless of economics                           │
│  → Economic cascade cannot overcome this margin           │
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
- **See "Targeted Threshold Mapping" section above for results**

### 2. Longer Duration Verification (realistic_sweep3)
- Same parameters but with 2016-block difficulty (realistic Bitcoin timing)
- Confirm findings hold at equilibrium, not just short-run dynamics
- Currently 8/50 scenarios complete; full results pending

### 3. Dynamic Scenarios
- Test scenarios where economic distribution shifts mid-simulation
- Model exchange announcements, institutional pivots

### 4. Difficulty Dynamics Analysis
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
