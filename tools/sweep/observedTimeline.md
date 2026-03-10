# Observed Timeline: targeted_sweep10b_econ_threshold_2016 — sweep_0003

A narrative walkthrough of a single scenario from `targeted_sweep10b_econ_threshold_2016`,
tracing the full sequence of events from fork split to cascade completion.

---

## Scenario Inputs

**Sweep**: `targeted_sweep10b_econ_threshold_2016`
**Scenario**: `sweep_0003`

### Sweep-Level Fixed Parameters

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `hashrate_split` | 0.50 | Equal hashrate — neither fork starts with a hashrate advantage |
| `pool_committed_split` | 0.35 | 35% of committed pools prefer v27 (Foundry flips to v26-preferring) |
| `pool_neutral_pct` | 30.0% | 30% of pools are neutral (profit-only) |
| `pool_ideology_strength` | 0.51 | Moderate ideological commitment |
| `pool_profitability_threshold` | 0.16 | Pools require 16% profit advantage before switching |
| `pool_max_loss_pct` | 0.26 | Pools tolerate up to 26% revenue loss for ideology before switching |
| `retarget_interval` | 2016 | Realistic Bitcoin difficulty retarget (every 2016 blocks) |
| `duration` | 13,000s | Extended simulation to capture retarget timing |

### Scenario-Specific Variable

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `economic_split` | 0.70 | 70% of economic custody on v27; v26 holds 30% |

### What This Setup Creates

v26 starts with a committed mining block anchored by Foundry (~30% hashrate). v27 has the
economic majority but must overcome a hashrate deficit at the start. The key question this
scenario tests: *can v27's economic advantage overcome v26's committed hashrate when the
2016-block retarget is in play?*

---

## Phase 1 — Fork Split (t=0)

The simulation begins with the network splitting along version lines. Despite equal total
hashrate, pool commitment assignments give v26 a meaningful early edge:

- **v27 hashrate**: 38.1% (ViaBTC, SpiderPool + solo miners)
- **v26 hashrate**: 48.3% (AntPool, F2Pool, MARA, Luxor, Ocean + Foundry committed v26)
- **Prices**: $60,000 on both forks — no price signal yet
- **Difficulties**: 1.0000 on both forks

The 10.2% hashrate gap means v26 is mining blocks faster. But with 70% of all economic custody
on v27, the fee revenue dynamics will soon start pulling profit-following pools toward v27.

---

## Phase 2 — Early Price Divergence (t=60 to t=544)

Both forks mine steadily. No pool switches occur. Prices begin to separate as economic nodes
signal preferences through fee generation and sentiment:

- v27 price edges up to ~$59,900
- v26 price edges down to ~$59,500
- Both difficulties remain at 1.0000
- No reorg events

The gap is small — only $400 — but it is growing. With 70% of economic custody on v27,
the aggregate fee revenue difference is real. Neutral pools are watching this signal.

---

## Phase 3 — First Pool Switches (t=600 to t=604)

At **t=600**, five simultaneous reorg events fire — the most chaotic moment in the simulation.
The price signal has grown enough to move neutral and lightly-committed pools:

**Switching to v27** (profit-driven — v27 now more profitable):
- ViaBTC (8.7% hashrate) — switches v26 → v27
- SpiderPool (5.2% hashrate) — switches v26 → v27

**Switching to v26** (commitment-driven — ideological lock-in or initial assignment resolves):
- MARA (5.9%) — switches v27 → v26
- Luxor (5.7%) — switches v27 → v26
- Ocean (5.4%) — switches v27 → v26

After the dust settles at **t=604**:
- **v27**: 50.5% hashrate
- **v26**: 35.9% hashrate

The neutral and profit-following pools have voted, and the majority chose v27. Both forks
are still mining, both difficulties still at 1.0000. A new equilibrium is reached — but it
is not the final one.

---

## Phase 4 — The Long Race (t=604 to t=8061)

This is the quiet phase: 7,457 simulation seconds of steady mining with no switches and no
drama. But the mathematics of the race are playing out beneath the surface.

| Time | v27 hashrate | v26 hashrate | v27 price | v26 price | v27 blocks | v26 blocks |
|------|-------------|-------------|-----------|-----------|-----------|-----------|
| t=604 | 50.5% | 35.9% | ~$61,380 | ~$57,967 | ~263 | ~186 |
| t=2000 | 50.5% | 35.9% | ~$61,500 | ~$57,800 | ~876 | ~620 |
| t=5000 | 50.5% | 35.9% | ~$61,800 | ~$57,600 | ~2,185 | ~1,546 |
| t=8061 | 50.5% | 35.9% | ~$62,100 | ~$57,400 | ~3,516 | ~2,488 |

Both difficulties remain at **1.0000** the entire time. v27 is mining ~40% more blocks than
v26 per unit of real time (50.5% vs 35.9% of total hashrate). v27 will mine 2016 blocks
before v26 does.

The price gap widens slowly but persistently. By t=8061, v27 commands a ~$4,700 premium
over v26. The v26-committed pools (AntPool, F2Pool, MARA, Luxor, Ocean) are absorbing this
revenue loss for ideological reasons — but their `pool_max_loss_pct` limit of 0.26 has not
yet been crossed. They hold.

---

## Phase 5 — The Retarget Event (t=8122)

At **t=8122**, v27 mines its **2016th block** and triggers the first difficulty adjustment.
This is the turning point of the entire scenario.

**Before retarget:**
- v27 difficulty: 1.0000
- v26 difficulty: 1.0000

**After retarget:**
- **v27 difficulty: 0.4975** — drops 50.25%
- v26 difficulty: 1.0000 — unchanged

Why did v27 difficulty drop? The retarget algorithm compares actual time to mine 2016 blocks
against the 2-week target. v27 only had ~50.5% of total hashrate, so it mined blocks slower
than if the full network were on v27. The algorithm concludes: "blocks are coming too slowly,
lower difficulty." The result is a 50% difficulty drop.

Immediately after the retarget:
- v27 blocks now require half the work to mine
- v27's revenue per unit of hashrate **roughly doubles**
- v27 price is ~$62,300 vs v26 ~$57,200 — a $5,100 gap
- v26-committed pools are now mining full-difficulty v26 while v27 just got 50% cheaper

The revenue math now crushes even committed pools. Their 26% maximum loss tolerance is
exceeded by the combination of the price gap and the difficulty asymmetry.

---

## Phase 6 — Cascade Completion (t=8362 to t=8423)

At **t=8408**, all five remaining v26 pools switch simultaneously. The retarget event pushed
every one of them past their `pool_max_loss_pct` threshold:

- **AntPool** (14.1% hashrate) — switches v26 → v27
- **F2Pool** (12.0% hashrate) — switches v26 → v27
- **MARA** (5.9% hashrate) — switches v26 → v27
- **Luxor** (5.7% hashrate) — switches v26 → v27
- **Ocean** (5.4% hashrate) — switches v26 → v27

Five reorg events fire. v26 drops to **0.00% hashrate**. The v26 chain stops advancing.

**Total opportunity cost paid by v26-committed pools**: ~$76.3M USD accumulated over the
7,800 seconds they mined v26 at an economic disadvantage.

After t=8423:
- **v27**: 86.4% hashrate
- **v26**: 0.00% hashrate
- **v26 blocks**: frozen at 1,541 — the v26 chain is abandoned

---

## Phase 7 — Post-Cascade Price Divergence (t=8483 to t=10659)

v26 is dead but the simulation continues. v27 is now mining with 86.4% of original network
hashrate at difficulty 0.4975 — blocks are arriving roughly 1.7× faster than the target rate.
Economic confidence in v27 surges as the chain consolidates:

- v27 price climbs from ~$63,000 toward $64,000+
- v26 price falls from ~$57,000 toward $55,000
- v27 block count accumulates rapidly
- v26 block count frozen at 1,541

---

## Phase 8 — v27 Second Retarget (t=10660)

At **t=10660**, v27 mines its second batch of 2016 blocks since the first retarget. This time
the situation is reversed — v27 has *too much* hashrate and is mining too fast:

- **v27 difficulty: 0.4975 → 0.7928** (adjusts upward — blocks were coming too fast)
- v26 difficulty: still 1.0000 (irrelevant, v26 is abandoned)

The difficulty retarget mechanism is self-correcting. With 86.4% of hashrate and difficulty
0.4975, v27 was mining blocks far faster than the 10-minute target. The second retarget
pulls difficulty back toward equilibrium.

---

## Final State (t=13,001)

| Metric | v27 | v26 |
|--------|-----|-----|
| Hashrate share | 86.4% | 0.00% |
| Blocks mined | 5,276 | 1,546 |
| Final price | $64,145 | $55,202 |
| Difficulty | 0.7928 | 1.0000 |
| Fork valuation | ~$2.8B | ~$1.2B |

---

## Key Insight: What Actually Decided This

The retarget event at **t=8122** — not the economic price signal — was the decisive mechanism.

For 7,500 simulation seconds, the v26-committed pools (AntPool, F2Pool, MARA, Luxor, Ocean)
absorbed a growing economic penalty for mining v26. Despite a $4,700 price gap at t=8061, they
held. Their ideological commitment and 26% loss tolerance kept them on v26 through all of
Phase 4.

What broke them was the retarget: a 50% difficulty drop on v27 that made mining v27 twice as
profitable per unit of work in a single instant. No pool's loss threshold could survive that
shock. All five switched within 286 seconds of the retarget.

This explains why `targeted_sweep10b` found *identical outcomes across economic_split=0.35
through 0.70*: the retarget fires regardless of economic split, and the resulting profitability
shock is large enough to push any pool past its `pool_max_loss_pct` threshold. Economic split
determines how fast prices diverge post-cascade — it does not determine whether the cascade
happens.

The minimum economic split for v27 victory via the 2016-block retarget mechanism is below 0.35.

---

*Scenario source: `targeted_sweep10b_econ_threshold_2016/results/sweep_0003/results.json`*
*Sweep spec: `specs/` (hashrate_split=0.50, retarget_interval=2016, duration=13000s)*
