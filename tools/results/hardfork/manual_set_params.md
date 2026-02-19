# Bitcoin Warnet Fork Scenario Results — Manual Parameter Study

## Framework Overview

The simulations model a Bitcoin network fork between **v27** (new version) and **v26** (legacy version) across two independent layers:

- **Pool scenario**: distribution of mining hashrate and degree of ideological commitment among miners
- **Economic scenario**: how exchanges and users respond to the competing chains

Key output metrics: hashrate winner, economic activity winner, orphan rate, reorg count, and whether a **zombie fork** emerges (a chain with zero hashrate but persistent economic activity).

---

## Named Scenarios (`tools/results/`)

### Group A: Close Battle (near-even starting hashrate)

| Scenario | Hashrate Winner | Economic Winner | Orphan Rate | Notes |
|---|---|---|---|---|
| `close_battle_null` | v27 (98.4%) | v27 (55%) | 20.2% | Clean v27 win |
| `close_battle_021326` | v27 (79.1%) | v27 (55%) | 25.4% | Some v26 pools still active at end |
| `close_battle_120min_test` | v27 (98.4%) | v27 (100%) | 3.9% | Only run with full economic convergence |
| `close_idSplit_021326` | v27 (98.4%) | v27 (55%, zombie) | **78.0%** | Most chaotic: 31 reorgs, 1,411 orphans |

**Key insight:** Close hashrate + ideological economics = catastrophic network instability. Exchanges sustaining artificial prices on the losing fork kept v26 miners fighting far longer than rational economics would dictate.

---

### Group B: Ideological War (v26-dominant hashrate)

All 8+ runs with the `ideological_war` pool configuration produced the same result regardless of random seed or economic scenario:

- **v26 wins hashrate**: 98–100% in every run
- **v27 zombie fork persists at 55/45 economic split**: in every run
- Orphan rates: 10–15%

The zombie fork is a **robust, repeatable outcome** — confirmed across 4 random seeds and multiple economic configurations.

| Scenario | Pool Config | Economic Config | Zombie? |
|---|---|---|---|
| `det_idWar_021226` | ideological_war | ideological_split | YES |
| `det_idWar_021326` | ideological_war | ideological_split | YES |
| `idWar_seed_021326` | ideological_war | ideological_split | YES |
| `idWar_seed_0213261` | ideological_war | ideological_split | YES |
| `idWar_seed0213262` | ideological_war | ideological_split | YES |
| `idWar_seed0213263` | ideological_war | ideological_split | YES |
| `idWar_strongv27_021326` | ideological_war | strong_v26_resistance | YES |
| `idWar_close_021426` | ideological_war | realistic_current | YES |
| `userHeavy_ideological_ideological` | ideological_war | ideological_split | YES |
| `userHeavy_weakResist_realistic_current` | weak_resistance | realistic_current | YES (at v26 100% hashrate) |

---

### Group C: Rational and Cross-Test Scenarios

| Scenario | Pool Config | Economic Config | Hashrate Winner | Economic Winner | Orphan Rate |
|---|---|---|---|---|---|
| `purely_rational_021326` | purely_rational | purely_rational | v27 (100%) | v27 (100%) | 0.0% |
| `close_purely_ideological` | purely_rational | ideological_split | v27 (100%) | v27 (100%) | 0.0% |
| `close_ideological_purely` | ideological_war | purely_rational | v26 (98.4%) | v26 (100%) | 6.3% |
| `custodyVvolume_realistic_realistic` | realistic_current | realistic_current | v27 (98.4%) | v27 (100%) | 2.2% |
| `flawed_idWar` | realistic_current | realistic_current | TIE (50%/50%) | v27 (70%) | 0.0% |

**Cross-test insights:**
- `close_purely_ideological`: Purely rational pools negate exchange ideology entirely — v27 wins both layers cleanly.
- `close_ideological_purely`: Purely rational exchanges eliminate the zombie — v26 wins both layers cleanly.
- `flawed_idWar`: Configuration error produced a true 50/50 hashrate stalemate with no reorgs; v27 won economics 70/30 but hashrate never resolved.

---

## Numbered Tests (`results/`) — BCAP Risk Scoring

These tests map how **E (% economic support)** and **H (% hashrate on Chain A)** affect a composite fork risk score (0–100; higher = more persistent fork risk).

### Tier 1: Extreme Parameter Combinations

| Test | Economic % | Hashrate % | Risk Score | Assessment |
|---|---|---|---|---|
| test-1.1 | 95% | 10% | 39.4 | LOW |
| test-1.2 | 10% | 95% | 2.0 | MINIMAL |
| test-1.3 | 90% | 90% | 38.8 | LOW |

### Tier 2: Threshold Mapping

**E70 series — varying hashrate at fixed 70% economic support:**

| Test | Hashrate % | Risk Score | Notes |
|---|---|---|---|
| test-2.6 (E70-H20) | 20% | 29.3 | Chain B 68 blocks ahead |
| test-2.3 (E70-H40) | 40% | 29.7 | |
| test-2.8 (E70-H40) | 40% | 29.7 | Repeat confirmation |
| test-2.9 (E70-H45) | 45% | 29.7 | |
| test-2.10 (E70-H49) | 49% | 29.8 | Near parity |

Risk score is nearly constant (~29.3–29.8) across all hashrate values when economic weight is fixed at 70%. Economic weight dominates the score.

**Near-equilibrium tests (E48–E55, H48–H55):**

| Test | Economic % | Hashrate % | Risk Score | Chain Winner |
|---|---|---|---|---|
| test-2.15 (E45-H45) | 45% | 45% | 19.4 | Chain A |
| test-2.13 (E48-H52) | 48% | 52% | 20.9 | Chain B |
| test-2.11 (E50-H50) | 50% | 50% | 21.6 | Chain A (margin: 0.07) |
| test-2.12 (E52-H48) | 52% | 48% | 22.3 | Chain A |
| test-2.14 (E55-H55) | 55% | 55% | 23.7 | Chain A |
| test-2.1 (E50-H40) | 50% | 40% | 21.5 | Chain A |
| test-2.2 (E60-H40) | 60% | 40% | 25.6 | Chain A |
| test-2.4 (E80-H40) | 80% | 40% | 33.8 | Chain A |
| test-2.5 (E90-H40) | 90% | 40% | 37.9 | Chain A |

At E48-H52, a slight hashrate advantage tips the winner to Chain B. At E50-H50, Chain A wins by only 0.07 weight units. Hashrate can determine the outcome at near-equilibrium, but economic weight is otherwise dominant.

**All 17 numbered tests scored LOW or MINIMAL risk. No HIGH or CRITICAL cases were found.**

---

## Overall Conclusions

### 1. Hashrate majority is the decisive long-run resolver
Every run where one fork held >50% committed hashrate eventually won the hashrate war. The only exception was `flawed_idWar`, a configuration error that produced a true 50/50 stalemate.

### 2. The zombie fork is caused by exchange inertia, not ideology alone
`idWar_close_021426` used `realistic_current` economics (ideology=0, inertia=20%) and still produced the 55/45 zombie fork. The zombie only collapsed in `close_ideological_purely`, where exchanges were fully rational with zero inertia. The ~15% price premium of the hashrate-winning fork is **not enough to overcome a 20% switching threshold** on major exchanges. Exchange inertia alone is sufficient to sustain a zombie.

### 3. Near-even hashrate + ideological economics = catastrophic disruption
`close_idSplit_021326` achieved a **78% orphan rate** and **31 reorg events** — by far the most destructive outcome of any scenario. Ideologically committed exchanges sustained artificial prices on the v26 losing fork, which kept v26 miners fighting far longer than rational economics would allow.

### 4. Economic feedback into mining is weak
Sustained economic activity on a losing fork slows miner defections but cannot override a committed hashrate majority. Pool defection thresholds (loss tolerance + ideology strength) matter far more than economic price signals in determining when a miner switches forks.

### 5. Purely rational networks resolve cleanly
When both pools and exchanges operate with no ideology and no inertia, forks resolve to 100% consensus on a single chain with 0% orphan rate and 0 reorg events.

### 6. Price equilibrium
- Sustained 55/45 economic split: ~$64k (winner) / ~$55k (loser), approximately a 15% spread
- Full economic consolidation: ~$71k (winner) / ~$48k (loser), approximately a 48% spread

### 7. BCAP risk scores plateau under economic weight dominance
At E70, varying hashrate from 20% to 49% moves the risk score by only 0.5 points (29.3 → 29.8). The BCAP risk score is primarily driven by the economic weight ratio. Hashrate only becomes a tipping factor when economic weight is near-equal (E48–E52 range).

### 8. Pool defection thresholds observed
From `close_battle_021326` defection timeline:
- ideology < 0.5, loss tolerance < 10%: defection within ~1,200 seconds
- ideology 0.7–0.85, loss tolerance 25–35%: sustained but vulnerable to persistent losses
- ideology 0.85, loss tolerance 40%: eventually capitulates against a >50% opposing hashrate after ~4–5 ideology overrides
- No pool configuration tested sustained indefinite resistance against a >50% opposing hashrate majority
