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

---

## Asymmetric / Dynamic Scenarios (`tools/results/`)

### balanced_4hr_test — Cascade in 25 Minutes

**Configuration:** pool=`asymmetric_balanced`, economic=`asymmetric_balanced`, 240 min, difficulty enabled, retarget-interval=20

| Metric | Value |
|---|---|
| v27 blocks | 1,424 |
| v26 blocks | 41 |
| Final hashrate | v27=100%, v26=0% |
| Final prices | v27=$71,795, v26=$48,205 |
| Reorg events | 4 |
| Total orphans | 40 |
| Orphan rate | 2.73% |

**Why it cascaded so fast:** Three compounding failures in the parameter design:

1. **Economic starting bias** — `asymmetric_balanced` gave v27 ~55% initial economic weight, producing a 5.8% price premium at t=0 before any blocks were mined
2. **Neutral pools immediately piled on** — 23% hashrate joined v27 at the first decision round (v27 already more profitable), pushing v27 to ~58% effective hashrate
3. **Low committed v26 tolerances** — f2pool=8.2%, viabtc=13%, antpool=17.5% tolerances were exceeded within 3 consecutive decision rounds as the loss gap grew 5.8% → 14.3% → 22.4%

**Pool defection timeline:**
- Round 1 (t=0): antpool, viabtc, f2pool hold on v26; neutrals go v27; 5.8% gap
- Round 2 (~10 min): viabtc forced off (14.3% > 13%), f2pool forced off (14.3% > 8.2%)
- Round 3 (~20 min): antpool forced off (22.4% > 17.5%)
- Round 4 (~25 min): all pools v27 with 65.3% gap — permanently resolved

**Conclusion:** This scenario was misconfigured for study of oscillation. The economic starting bias turned a nominally "balanced" scenario into a rapid cascade.

---

### standoff_4hr_test — Sustained Oscillation via Difficulty Oracle

**Configuration:** pool=`ideological_standoff`, economic=`ideological_standoff`, 240 min, difficulty enabled, retarget-interval=20, dynamic-switching enabled
**Network:** `ideological-standoff` (generated from `networkGen/scenarios/ideological_standoff.yaml`)

| Metric | Value |
|---|---|
| v27 blocks | 1,037 |
| v26 blocks | 1,000 |
| Final hashrate | v27=31.3%, v26=68.7% |
| Final economic | v27=55%, v26=45% |
| Final prices | v27=$59,897, v26=$60,103 (0.3% spread) |
| Chainwork winner | v27 (758.8 vs 680.9) |
| Difficulty (final) | v27=0.265, v26=0.753 |
| Total decision rounds | 23 over 4 hours |

**Pool configuration:**

| Pool(s) | Hashrate | Role | Tolerance |
|---|---|---|---|
| foundryusa + ocean + braiinspool | 31.3% | v27 committed | 31.5% (0.9 × 0.35) |
| antpool + viabtc | 30.6% | v26 committed | 31.5% (0.9 × 0.35) |
| f2pool + binancepool + marapool + luxor + sbicrypto | 38.1% | neutral swing | 2–5% threshold |

**Economic configuration:** 50/50 iron-lock (effective switching threshold=60%, max price divergence=20% — nodes never switch).

#### The Oscillation Mechanism (emergent from difficulty oracle)

True sustained oscillation emerged not from price dynamics but from the interaction between the **difficulty oracle** and the **profitability calculation**:

Pool decisions evaluate each fork using `assumed_fork_hashrate=50%` but the **current real difficulty**:
```
fork_profitability = blocks_per_hour(fork, assumed_50%) × (price + fees)
```

When a fork has a **low difficulty** (because few miners are on it), the assumed-50% calculation produces a high block rate — making that fork look far more profitable than it currently is. This creates a lagged negative feedback loop:

1. Neutral pools + committed v26 (68.7%) mine v26 → v26 difficulty rises, v27 difficulty falls
2. At next decision: "v27 at low difficulty, assuming 50% miners → many blocks" → v27 looks 40–60%+ more profitable
3. Loss gap exceeds antpool/viabtc's 31.5% tolerance → **forced off v26**
4. Now 100% on v27 → v27 difficulty spikes, v26 difficulty collapses
5. At next decision: v26 looks cheap → gap hits 33–42% → **foundryusa/ocean/braiinspool forced off v27**
6. Repeat every ~20 minutes for the full 4 hours

**Key observations:**
- Both chains produced nearly equal blocks (1,037 vs 1,000) throughout — neither chain died
- Prices stayed within 0.3% of each other at the end — no sustained price divergence
- v27 wins chainwork (758 vs 681) despite ending with only 31.3% hashrate, because it accumulated more work during periods of 100% dominance
- The 31.5% tolerance is not a "never switch" threshold here — it becomes a **damping factor** that delays switching by one decision round, sustaining oscillation rather than triggering immediate cascade
- Committed factions alternate between ideology-override (holding at 5–30% loss) and forced-switch (60%+ loss), then return to their preferred fork each cycle

**Sample oscillation cycle (antpool as reference):**

| Round | t (min) | antpool | loss gap |
|---|---|---|---|
| 1 | 0 | v26 (ideology+profit) | — |
| 2 | 10 | v27 (forced) | 60.0% |
| 3 | 20 | v26 (returned) | — |
| 4 | 30 | v26 (ideology, holds) | 19.5% |
| 5 | 40 | v27 (forced) | 46.6% |
| 6 | 50 | v26 (returned) | — |
| 7 | 60 | v26 (ideology, holds) | 12.1% |
| 8 | 70 | v27 (forced) | 51.4% |
| ... | ... | repeats 15 more rounds | ... |

**Tuning knobs for oscillation speed:**
- `retarget-interval` — shorter = faster difficulty swings = faster cycles (current: 20 blocks ≈ 20-min cycle)
- `ideology_strength × max_loss_pct` — higher = longer hold before switching = slower oscillation
- Neutral pool size — larger neutral bloc = larger hashrate swings = more extreme profitability gaps

---

### idwar_reunion_test — Fork Expiry with Real Bitcoin Reorg

**Configuration:** pool=`ideological_war`, economic=`purely_rational`, 900 sec, difficulty enabled, retarget-interval=20, `--enable-reunion --reunion-timeout 90`

| Metric | Value |
|---|---|
| v27 blocks | 18 |
| v26 blocks | 80 |
| Final hashrate | v27=0%, v26=98.4% |
| Final prices | v27=$56,275, v26=$63,647 (13% spread) |
| Chainwork winner | v26 (64.86 vs 18.0) |

**Pool defection timeline (single decision round at t=600s):**

| Pool | Starting fork | Final fork | Reason |
|---|---|---|---|
| foundryusa | v27 | v26 | Forced switch: exceeded max loss $5M |
| luxor | v27 | v26 | Forced switch: exceeded max loss $500k |
| ocean | v27 | v26 | Forced switch: exceeded max loss $200k |
| antpool | v26 | v26 | Ideology and profit aligned |
| viabtc | v26 | v26 | Ideology and profit aligned |
| f2pool | v26 | v26 | Ideology and profit aligned |
| marapool | v26 | v26 | Ideology and profit aligned |
| binancepool | neutral | v26 | Rational profit maximization |
| sbicrypto | neutral | v26 | Rational profit maximization |
| braiinspool | neutral | v26 | Rational profit maximization |

v27's committed pools (foundryusa 26.89%, luxor 3.94%, ocean 1.42%) provided ~32% hashrate for the first 600 seconds (one decision interval), mining 18 v27 blocks. At t=600s the profitability gap (~$6.5M/day for foundryusa) exceeded all their max-loss thresholds and all three were **forced off** in the same decision round. v26 mined the final 300 seconds at 100%.

**Reunion results:**

| Metric | Value |
|---|---|
| Winner | v26 |
| Loser (v27) pre-reorg height | 17 |
| Winner (v26) tip height | 82 |
| Reorg depth | 17 blocks orphaned |
| Nodes converged | 16/16 |
| Convergence time | **2.0 seconds** |
| Timed out | No |

All 16 v27 partition nodes reorged from height 17 to height 82 (jumped 65 blocks, orphaned 17) within **2 seconds** of cross-partition connections being established. The 3.6× chainwork advantage (64.86 vs 18.0) was immediately decisive — nodes accepted the heavier chain without any ambiguity.

**Economic note:** Final economic weight remained 55/45 (v27 favored) despite `purely_rational` config. This is an artifact of the `ideological-standoff` network YAML, which bakes in `ideology_strength: 0.9` at the node level. Per-node ideology from the network YAML takes precedence over the economic scenario config in the current implementation, producing the same 55/45 zombie pattern even when the scenario intends pure rationality.

---

## Updated Conclusions

### 9. Price and profitability can decouple under difficulty dynamics
When the difficulty oracle is active, a fork's **profitability** (blocks-per-hour × price, evaluated at assumed 50% hashrate) can diverge dramatically from its current **price** alone. A fork with low real hashrate and low difficulty appears far more profitable in the pool decision model than its price ratio suggests. This is the primary driver of oscillation in `standoff_4hr_test`.

### 10. Sustained oscillation requires symmetric committed factions + difficulty oracle
In `standoff_4hr_test`, both committed factions had equal tolerance (~31%) and the difficulty oracle created profitability swings of 40–60%. The combination produced a repeating forced-switch cycle that kept both chains viable for the full 4 hours. Without the difficulty oracle (flat block rate assumed), this oscillation does not occur — the system finds a stable attractor.

### 11. The difficulty oracle is a natural stabilizer against cascade
In `balanced_4hr_test` (no oscillation), difficulty was enabled but tolerances were too low — the cascade resolved before difficulty could create counter-pressure. In `standoff_4hr_test`, higher tolerances gave the difficulty mechanism time to operate, resulting in oscillation instead of cascade. The key parameter relationship: **if tolerance is high enough to survive one full oscillation cycle, the fork persists indefinitely**.

### 12. Chainwork winner ≠ current hashrate winner
`standoff_4hr_test` ended with v26 at 68.7% current hashrate but v27 winning chainwork (758 vs 681). Periods of 100% dominance (when one side is forced off entirely) accumulate disproportionate chainwork. A fork that survives oscillation cycles while briefly dominating hashrate can "win" by chainwork despite spending most of the simulation as the minority chain.

### 13. Fork reunion via real Bitcoin reorg is instantaneous when chainwork advantage is decisive
In `idwar_reunion_test`, the losing v27 partition (17 orphaned blocks, chainwork=18.0) was reconnected to the winning v26 partition (chainwork=64.86). All 16 losing-fork nodes reorged in **2 seconds** via normal Bitcoin P2P `headers` propagation — no custom logic required beyond `addnode`. A 3.6× chainwork advantage leaves no ambiguity; nodes immediately switch to the heavier chain. Convergence time will be longer in oscillation scenarios where chainwork is closer.

### 14. Forced pool defection from economic loss can occur in a single decision round
The three `ideological_war` v27-committed pools (foundryusa, luxor, ocean) entered the scenario with `max_loss_pct` of 35–40%. With `purely_rational` economics, v26's profitability advantage grew to ~80% by t=600s (the first decision round). All three pools were simultaneously forced off v27 in a single round, collapsing v27 hashrate from 32% to 0% instantaneously. This confirms: under rational economics, pool ideology thresholds act as a **one-way ratchet** — once the cumulative loss exceeds the threshold, defection is abrupt rather than gradual.
