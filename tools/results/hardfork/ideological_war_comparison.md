# Fork Threshold Analysis: Hashrate vs Economic Ideology

## Overview

This analysis explores the thresholds at which Bitcoin network forks persist or collapse,
focusing on two key variables:

1. **Hashrate alignment** (pool scenario) — how mining pools distribute across forks
2. **Economic ideology** (economic scenario) — how exchanges and users choose which fork to support

The original two scenario runs changed both variables simultaneously, making it impossible
to isolate which factor drove the different outcomes. Two cross-tests swap the economic
scenarios to isolate each variable independently.

---

## Test Matrix

| | **realistic_current** (neutral economics) | **ideological_split** (ideological economics) |
|---|---|---|
| **close_battle** (near-even hashrate) | close_battle_021326 | **NEW**: close_idSplit_021326 |
| **ideological_war** (v26 dominant hashrate) | **NEW**: idWar_close_021426 | idWar_seed_021326 |

All runs use seed 021326 for reproducibility (except idWar_close_021426 which uses 021426).

---

## Scenario Configurations

### Pool Scenarios

#### close_battle — Near-Even Hashrate Split

| Pool | Hashrate | Fork Pref | Ideology | Max Loss % | Max Loss USD |
|------|----------|-----------|----------|------------|--------------|
| foundryusa | 26.89% | v27 | 0.85 | 35% | $10,000,000 |
| f2pool | 11.25% | v27 | 0.60 | 20% | $3,000,000 |
| antpool | 19.25% | v26 | 0.85 | 35% | $10,000,000 |
| viabtc | 11.39% | v26 | 0.70 | 25% | $2,000,000 |
| marapool | 8.25% | v26 | 0.50 | 15% | $1,000,000 |
| binancepool | 10.04% | neutral | 0.0 | 0% | — |
| sbicrypto | 4.57% | neutral | 0.0 | 0% | — |
| luxor | 3.94% | neutral | 0.1 | 2% | $500,000 |
| ocean | 1.42% | neutral | 0.2 | 5% | $200,000 |
| braiinspool | 1.37% | neutral | 0.1 | 2% | $100,000 |

**Starting hashrate**: v27=38.14%, v26=38.89%, neutral=21.34%

#### ideological_war — v26 Dominant Hashrate

| Pool | Hashrate | Fork Pref | Ideology | Max Loss % | Max Loss USD |
|------|----------|-----------|----------|------------|--------------|
| foundryusa | 26.89% | v27 | 0.85 | 40% | $5,000,000 |
| luxor | 3.94% | v27 | 0.80 | 35% | $500,000 |
| ocean | 1.42% | v27 | 0.85 | 35% | $200,000 |
| antpool | 19.25% | v26 | 0.90 | 40% | $5,000,000 |
| viabtc | 11.39% | v26 | 0.85 | 35% | $2,000,000 |
| f2pool | 11.25% | v26 | 0.70 | 25% | $1,000,000 |
| marapool | 8.25% | v26 | 0.60 | 20% | $500,000 |
| binancepool | 10.04% | neutral | 0.0 | 0% | — |
| sbicrypto | 4.57% | neutral | 0.0 | 0% | — |
| braiinspool | 1.37% | neutral | 0.1 | 2% | $100,000 |

**Starting hashrate**: v27=32.25%, v26=50.14%, neutral=15.98%

### Economic Scenarios

#### realistic_current — Neutral/Rational Exchanges

- Major exchanges: ideology_strength=0.0, fork_preference=neutral, inertia=0.20
- Regular exchanges: ideology_strength=0.05, fork_preference=neutral
- Users: ideology_strength=0.3, fork_preference=neutral
- max_loss_pct: 0.05 (economic), 0.15 (users)

Exchanges are purely rational profit-followers with high inertia (switching costs).

#### ideological_split — Ideological Exchanges

Distribution pattern applied to economic nodes:
- 40% of economic nodes: fork_preference=v27, ideology_strength=0.7, max_loss_pct=0.20
- 40% of economic nodes: fork_preference=v26, ideology_strength=0.7, max_loss_pct=0.20
- 20% of economic nodes: neutral, ideology_strength=0.0

Users: 50% v27 (ideology 0.8), 30% v26 (ideology 0.6), 20% neutral

**Important implementation note**: The `distribution_pattern` in the config overrides the
`major_exchange` role override (which sets ideology=0.1). The distribution gets the last
word, so major exchanges end up with ideology_strength=0.7.

**Also note**: The `ideology_strength` values in `network.yaml` metadata are NOT used at
runtime. Pool ideology comes from `mining_pools_config.yaml`, economic node ideology comes
from `economic_nodes_config.yaml`. The network.yaml values are documentation-only.

---

## Completed Results

### Run 1: close_battle_021326

**Config**: close_battle pools + realistic_current economics | Duration: 120 min | Network: close-battle

| Metric | Value |
|--------|-------|
| **Winner** | **v27** |
| Blocks mined | v27=658, v26=123 |
| Final hashrate | v27=79.1%, v26=19.2% |
| Final prices | v27=$64,269, v26=$55,653 |
| Chainwork | v27=543.5, v26=123.0 (ratio 4.4:1) |
| v27 difficulty | 0.940 (4 retargets) |
| v26 difficulty | 1.000 (no retargets) |
| Reorg events | 6 |
| Orphan rate | **25.38%** |
| Consensus stress | 12.42 |
| Final economic split | v27=55.0%, v26=45.0% |

#### Pool Defection Timeline
1. **t=600s** — sbicrypto, ocean switch v26→v27 (neutral, followed profit)
2. **t=1200s** — marapool forced switch v26→v27 (ideology 0.5, loss 8.4% > 7.5% tolerance)
3. **t=3001s** — antpool, viabtc switch v26→v27 (antpool: loss 51.2% > 29.8% tolerance; viabtc: exceeded $2M max)
4. **t=6604s** — antpool switches back v27→v26 (loss narrowed to 28.1% < 29.8% tolerance)

#### Economic Dynamics
- Exchanges were purely rational, no ideology overrides
- 2 major exchanges stayed on v26 due to inertia (22% switching threshold)
- v27 price advantage reached 18% but didn't exceed their inertia threshold
- Economics were slowly converging toward v27 (the hashrate winner)

---

### Run 2: idWar_seed_021326

**Config**: ideological_war pools + ideological_split economics | Duration: 240 min | Network: ideological-war

| Metric | Value |
|--------|-------|
| **Winner** | **v26** |
| Blocks mined | v27=110, v26=1,414 |
| Final hashrate | v27=0.0%, v26=98.4% |
| Final prices | v27=$55,167, v26=$64,754 |
| Chainwork | v27=110.0, v26=1,291.4 (ratio 11.7:1) |
| v27 difficulty | 1.000 (no retargets — never reached 144 blocks) |
| v26 difficulty | 0.941 (9 retargets) |
| Reorg events | 11 |
| Orphan rate | **11.89%** |
| Consensus stress | 33.1 |
| Final economic split | v27=55.0%, v26=45.0% |

#### Pool Dynamics
- v26's 50.14% starting majority attracted neutral pools, snowballing to ~66%
- foundryusa, luxor, ocean (v27 ideologues) were each forced to switch **19 times**
  with only **4 ideology overrides** each
- By end of run, **all 10 pools were on v26** — v27 hashrate dropped to 0%
- v27 never reached a difficulty retarget (stuck at difficulty 1.0, expected block interval 10,000s)

#### Economic Dynamics — The Zombie Fork
- Despite v26's total hashrate victory, **economic split stayed at 55/45 favoring v27**
- The two largest v27 exchanges (consensus_weight 80.47 each) held firm through
  **4 ideology overrides** and **7 inertia holds** each
- v27 price advantage at one point reached 18% over v26, but the v26 exchanges' ideology
  (0.7) with inertia (0.15) kept them locked on v26
- v27 is effectively a zombie chain: 0% hashrate, no blocks, but 55% economic activity

#### v27 Coalition Costs
| Pool | Opportunity Cost | Forced Switches | Ideology Overrides | Orphan Rate |
|------|-----------------|-----------------|-------------------|-------------|
| foundryusa | $3,689,721 | 19 | 4 | 33.2% |
| luxor | $479,396 | 19 | 4 | 52.6% |
| ocean | $194,846 | 19 | 4 | 36.0% |
| **Total** | **$4,363,963** | — | — | — |

v26-aligned and neutral pools paid $0 in opportunity costs across the entire run.

---

## Key Observations from Original Runs

### 1. Near-even hashrate produces more orphan churn
close_battle had **25.4% orphan rate** vs ideological_war's 11.9%. When pools are near
the tipping point, they switch sides repeatedly, orphaning blocks each time.

### 2. A >50% committed hashrate majority is decisive
In ideological_war, v26's 50.14% starting majority attracted neutral pools and snowballed.
In close_battle, the near-even split meant neutral pools tipped the balance.

### 3. Economic ideology can decouple from hashrate outcomes
In ideological_war, v27 held 55% economic weight despite 0% hashrate — a persistent
zombie fork sustained purely by exchange ideology (0.7 strength).

### 4. Price divergence equilibrium
Both scenarios ended with roughly $64k/$55k price splits (~15% spread), suggesting this
is the natural equilibrium for a 55/45 economic split regardless of which fork wins hashrate.

### 5. Pool defection thresholds
- ideology_strength < 0.6 with loss tolerance < 10% guarantees early defection (marapool)
- The ~30% tolerance is the "true believer" threshold (antpool briefly returned to v26 in close_battle)
- Even 0.85 ideology with 40% tolerance is insufficient against a 50%+ hashrate majority (foundryusa in ideological_war)

### 6. The unanswered question
Both the hashrate alignment AND economic ideology changed between runs. We cannot determine
from these two runs alone whether:
- The zombie fork is caused by exchange ideology or would occur with neutral exchanges too
- Economic ideology can change the winner of a close hashrate race
- Hashrate or economics is the dominant factor

---

## Upcoming Cross-Tests

### New Run 1: idWar_close_021426
**Question: Does the zombie fork collapse without economic ideology?**

| Parameter | Value |
|-----------|-------|
| Pool Scenario | `ideological_war` (v26 dominant — same as idWar_seed_021326) |
| Economic Scenario | `realistic_current` (neutral exchanges — same as close_battle_021326) |
| Duration | 240 min (14,400s) |
| Network | ideological-war (default namespace) |
| Seed | 021326 |
| Command | `warnet run scenarios/partition_miner_with_pools.py --duration 14400 --pool-scenario ideological_war --economic-scenario realistic_current --enable-reorg-metrics --enable-difficulty --results-id idWar_close_021426 --randomseed 021326` |

**What this tests**: The original ideological_war produced a zombie chain — v27 had 0%
hashrate but 55% economic support from ideological exchanges. With neutral exchanges
instead, will the economic layer converge to v26 along with hashrate?

**Expected outcomes**:
- Hashrate outcome should be similar to original idWar (v26 wins decisively) since pool configs are unchanged
- Economic split should shift toward v26 since neutral exchanges follow price, and v26 has the higher price ($64k vs $55k)
- The 2 major exchanges with inertia=0.20 may still lag on v27 briefly, but with ideology=0.0 and max_loss_pct=0.05, they should eventually switch
- If economics fully converge to v26, it confirms that ideology_strength=0.7 on exchanges was the sole reason for the persistent zombie fork

**Comparison**: vs idWar_seed_021326 — isolates the effect of economic ideology removal on a decisive hashrate war.

---

### New Run 2: close_idSplit_021326
**Question: Can economic ideology change the winner of a close hashrate race?**

| Parameter | Value |
|-----------|-------|
| Pool Scenario | `close_battle` (near-even hashrate — same as close_battle_021326) |
| Economic Scenario | `ideological_split` (ideological exchanges — same as idWar_seed_021326) |
| Duration | 240 min (14,400s) |
| Network | close-battle (wargames-run2 namespace) |
| Seed | 021326 |
| Command | `warnet run scenarios/partition_miner_with_pools.py --duration 14400 --pool-scenario close_battle --economic-scenario ideological_split --enable-reorg-metrics --enable-difficulty --results-id close_idSplit_021326 --namespace wargames-run2 --randomseed 021326` |

**What this tests**: The original close_battle with neutral economics saw v27 win and
economics slowly follow. With ideological exchanges, do v26-supporting exchanges prop
up v26's price enough to keep miners from defecting?

**Expected outcomes**:
- The close hashrate split (38.14% vs 38.89%) means small economic signals could tip the balance
- Ideological v26 exchanges maintaining economic activity on v26 could keep v26 prices
  higher, reducing the profitability gap that caused marapool and viabtc to defect originally
- This could result in: (a) a more sustained fork with higher consensus stress,
  (b) a different winner, or (c) v27 still winning but with a persistent economic split (zombie fork on both sides)
- Duration is doubled (240 min vs original 120 min), allowing more time for economic feedback effects

**Comparison**: vs close_battle_021326 — isolates the effect of economic ideology on a close hashrate race.

---

## What the Cross-Tests Will Reveal

### 1. Is the zombie fork driven by exchange ideology or hashrate dynamics?
- If New Run 1 (idWar + neutral economics) still shows a persistent v27 economic split → hashrate dynamics alone create zombie forks
- If New Run 1 converges economics to v26 → **exchange ideology is the critical factor**

### 2. Can economic ideology change the outcome of a close hashrate race?
- If New Run 2 (close_battle + ideological economics) produces a different winner → **economics are a deciding factor in close races**
- If New Run 2 still has v27 winning → hashrate alignment dominates regardless of economic ideology

### 3. What is the economic ideology threshold for fork persistence?
- The four runs bracket the space: ideology=0.0 (rational) vs ideology=0.7 (ideological)
- Comparing economic splits across all four runs will identify where the tipping point lies
- Future runs with intermediate ideology values (0.3, 0.5) can narrow the threshold

### 4. Does the economic-hashrate feedback loop exist?
- If ideological v26 exchanges in New Run 2 change the hashrate outcome, it proves economics feed back into mining decisions
- If they don't, it suggests the price oracle's influence on pool profitability is too weak to overcome hashrate fundamentals
