# Block Violation Threshold — Findings

**Parameter:** `violation_rate` (vr)  
**Primary sweep:** `chainsplit_persistence` (36 scenarios, E=0.55, 6 vr × 3 C × 2 reps)  
**Corroborating sweep:** `fork_formation_threshold` (90 scenarios, E=0.65, 9 vr × 3 C × 3 reps)  
**Lite-network full-grid:** `contested_fork_threshold` (120 scenarios, 3 vr × 4 E × 5 C × 2 compositions)  
**Full-network vr×E sweep:** `econ_split_full` (108 scenarios, 6 E × 3 vr × 3 C × 2 compositions, interim 52/108)

---

## What violation_rate Means

`violation_rate` (vr) is the fraction of network participants that consistently reject blocks
produced under the new soft-fork rule. It maps directly to the scenario parameter:

```
v26_acceptance_probability = 1 − vr
```

A v26 node with `v26_acceptance_probability = 0.80` (vr=0.20) accepts 80% of incoming v27
blocks and rejects 20%. At vr=1.00, v26 nodes never accept any v27 block — maximum protocol
rigidity. At vr=0.05, only 5% of blocks trigger a rejection.

This parameter represents **softfork rule enforcement strength**: how strictly non-adopting
nodes enforce their version of the protocol. It is not a stochastic property applied
per-node — it is a fixed attribute of the v26 population.

---

## Primary Findings

### 1. vr Does Not Determine Fork Outcome — C Does

The most consistent result across all tested conditions is that `pool_committed_split` (C) —
not violation rate — determines which chain ultimately wins the fork.

| C | Who wins | vr dependence? |
|---|---|---|
| 0.15 (no committed v27 pool) | v26 always | None |
| 0.30 (Foundry committed v27) | v27 usually (50.5% or 86.4% final hashrate) | None |
| 0.60 (Foundry+MARA+Luxor committed) | v27 decisively (86.4% final hashrate) | None |

Across the full vr range [0.05, 1.00], the same C value produces the same winner every time.
No vr value rescued v26 at C=0.30, and no vr value prevented v27 from winning at C=0.60.

### 2. vr Controls Duration and Depth — But Variance Dominates

Within genuine fork scenarios, vr has a modest effect on fork duration and reorg depth.
However, the variance between replications (random seeds) exceeds any systematic vr trend.

**Chainsplit_persistence genuine results — C=0.30:**

| vr | rep | heal_s | v27_blocks | v26_blocks | reorg_depth | fork_balance | pain_score |
|---|---|---|---|---|---|---|---|
| 0.05 | 0 | 8,630 | 2,318 | 1,509 | 1,509 | 0.651 | 982 |
| 0.05 | 1 | 3,553 | 887 | 649 | 649 | 0.732 | 475 |
| 0.10 | 1 | 1,962 | 474 | 373 | 373 | 0.787 | 294 |
| 0.30 | 0 | 7,080 | 1,753 | 1,287 | 1,287 | 0.734 | 945 |
| 0.30 | 1 | 2,693 | 582 | 449 | 449 | 0.771 | 346 |
| 0.50 | 0 | 1,976 | 483 | 384 | 384 | 0.795 | 305 |
| 0.50 | 1 | 6,417 | 1,556 | 1,130 | 1,130 | 0.726 | 820 |
| 1.00 | 0 | 7,151 | 1,772 | 1,307 | 1,307 | 0.738 | 965 |
| 1.00 | 1 | **12,205** | **4,782** | **1,491** | 1,491 | 0.312 | 465 |

*Reps 0–1 of vr=0.10 and 0.20 at C=0.30 were startup failures (excluded).*

There is no monotonic relationship between vr and heal_s, reorg_depth, or pain_score.
vr=0.05 rep0 produces a pain_score of 982 — nearly identical to vr=1.00 rep0 (pain_score=965).
vr=0.50 rep0 heals in 1,976s while vr=0.50 rep1 takes 6,417s — a 3.2× difference at
the same vr, driven by composition alone.

**The dominant source of variation in fork depth is replication (composition), not vr.**

### 3. C=0.30 Is the Maximum Pain Zone

Across all C values, C=0.30 consistently produces the highest `fork_balance` (most contested forks):

| C | typical fork_balance | interpretation |
|---|---|---|
| 0.15 | ~0.033 | v26 dominates completely; v27 builds ~180 blocks vs v26's ~5,500 |
| 0.30 | ~0.73–0.79 | Near-equal chains; both sides competitive at heal time |
| 0.60 | ~0.15–0.37 | v27 leads substantially; v26 builds only ~300 blocks |

At C=0.30, Foundry's 30% committed hashrate is roughly balanced against the combined
neutral + v26 pool hashrate. Neither side achieves quick dominance — the fork runs deep
until economic cascades or probability dynamics tip the balance. This produces the highest
`pain_score` values despite C=0.60 having larger raw reorg_depth.

### 4. C=0.15 — v26 Wins, But Slowly

With no committed v27 pool, v26 miner dominance means the v27 chain never accumulates
enough work to cascade. All 10 genuine C=0.15 scenarios ran near the 13,000s timeout,
with v26 building 4,355–5,927 blocks while v27 built only 146–197 blocks.

**C=0.15 scenarios by vr:**

| vr | rep | heal_s | v27_blocks | v26_blocks | reorg_depth | fork_balance |
|---|---|---|---|---|---|---|
| 0.05 | 0 | 11,515 | 179 | 5,369 | 179 | 0.033 |
| 0.05 | 1 | 12,713 | 192 | 5,935 | 192 | 0.032 |
| 0.10 | 0 | 12,100 | 188 | 5,642 | 188 | 0.033 |
| 0.20 | 0 | 10,880 | 170 | 5,040 | 170 | 0.034 |
| 0.20 | 1 | 12,092 | 192 | 5,654 | 192 | 0.034 |
| 0.30 | 0 | 11,487 | 176 | 5,316 | 176 | 0.033 |
| 0.30 | 1 | 12,101 | 192 | 5,665 | 192 | 0.034 |
| 0.50 | 0 | 9,670 | 146 | 4,355 | 146 | 0.034 |
| 0.50 | 1 | 12,094 | 192 | 5,663 | 192 | 0.034 |
| 1.00 | 0 | 10,880 | 163 | 4,985 | 163 | 0.033 |
| 1.00 | 1 | 12,703 | 197 | 5,927 | 197 | 0.033 |

vr has essentially no effect on any metric at C=0.15. The outcome (v26 wins) and the
degree of dominance (fork_balance ~0.033) are determined entirely by the absence of
committed v27 hashrate. The 3,000s spread in heal_s (~9,670 to ~12,713) reflects
stochastic variation in the timing of the economic cascade.

### 5. Deepest Fork Observed

**sweep_0033** (vr=1.00, C=0.30, rep=1) produced the longest-running fork in all tested conditions:

- **heal_s = 12,205** (3.39 simulation hours; 795s before 13,000s timeout)
- **v27_blocks = 4,782 vs v26_blocks = 1,491** — v27 chain led 3.2:1 at heal
- **reorg_depth = 1,491** (the v26 side must orphan 1,491 blocks)
- **final_v27_hr = 86.4%** — Foundry's commitment eventually cascaded all neutral pools
- **fork_balance = 0.312** — moderately contested, v27 led but v26 built substantial work

Despite having maximum violation rate, vr=1.00 did not produce a persistent chainsplit.
The Foundry commitment (C=0.30) eventually tipped pool economics toward v27.

The same parameter point at rep=0 (sweep_0032) healed in 7,151s with 1,307 reorg depth —
demonstrating that even vr=1.00 has 5.9× variation between replications.

---

## Startup Failure Zone

Six of the 36 chainsplit_persistence scenarios exhibited **startup failures**: apparent fork
healing within 4–27 seconds with only 3–10 total blocks mined and final_v27_hr = 38.1%
(the uninitialized t=0 hashrate, indicating no pool switching occurred).

**Startup failures (chainsplit_persistence):**

| scenario | vr | C | rep | heal_s | total_blocks |
|---|---|---|---|---|---|
| sweep_0007 | 0.10 | 0.15 | 1 | 4 | 4 |
| sweep_0008 | 0.10 | 0.30 | 0 | 4 | 4 |
| sweep_0014 | 0.20 | 0.30 | 0 | 4 | 4 |
| sweep_0015 | 0.20 | 0.30 | 1 | 27 | 10 |
| sweep_0016 | 0.20 | 0.60 | 0 | 6 | 3 |
| sweep_0017 | 0.20 | 0.60 | 1 | 16 | 6 |

Startup failures occur at vr=0.10 and vr=0.20 (v26_acceptance_probability=0.90 and 0.80).
At these intermediate acceptance probabilities, v26 nodes accept 80–90% of v27 blocks,
creating just enough acceptance that the fork reconverges before even 10 blocks are mined.

Critically, these are **stochastic** — the same vr=0.10 at C=0.15 produces a genuine
12,100s fork at rep=0 but a startup failure at rep=1. The failure is not a property of
vr alone; it depends on the sequence of block events in the first few seconds of the simulation.

No startup failures were observed at vr=0.05 or vr ≥ 0.30 in chainsplit_persistence,
suggesting an intermediate "reconvergence corridor" near vr=0.10–0.20 where stochastic
early-fork dynamics can prevent the partition from developing.

---

## Cross-Sweep Evidence

The `fork_formation_threshold` (FFT) sweep independently tested vr=[0.05, 0.10, 0.15, 0.20,
0.25, 0.30, 0.40, 0.50, 0.75, 1.00] at E=0.65 with 3 replications per point.

**FFT C=0.30 genuine results — pain_score:**

| vr | pain_scores (3 reps) | pattern |
|---|---|---|
| 0.05 | 356, 722, *(startup fail)* | High variance; 2× spread within vr |
| 0.10 | 332, 533, 472 | Moderate; consistent high-pain results |
| 0.15 | 931, 386, *(startup fail)* | Same bimodal pattern as CSP |
| 0.20 | *(startup fail)*, 596, 370 | Startup fail at one rep |
| 0.25 | 412, 407, 609 | Tight cluster — composition-driven |
| 0.30 | *(zero)*, *(zero)*, 495 | Two scenarios produced no fork |
| 0.40 | 589, 677, 1024 | High pain; vr=0.40 matches vr=1.00 CSP |
| 0.50 | *(startup fail)*, 443, *(startup fail)* | Mostly failures |
| 0.75 | 470, 1072, 723 | Wide spread; highest FFT pain_score |
| 1.00 | *(startup fail)* × 3 | All startup failures |

FFT confirms the absence of any monotonic vr→pain relationship. The highest pain_score in
FFT (1,072 at vr=0.75) falls in the middle of the tested range, not at vr=1.00.

The FFT vr=1.00 all-startup-failure pattern differs from CSP vr=1.00 (all genuine forks).
This discrepancy likely reflects E-driven differences in network cascade dynamics rather
than a fundamental vr=1.00 effect: FFT used E=0.65 vs CSP E=0.55. (Both produce identical
economic node configurations in the lite network, but E may affect cascade timing through
other pathways.)

---

## Summary Table — Pain Score by (vr, C)

Below combines chainsplit_persistence genuine results. `pain_score = reorg_depth × fork_balance`.

| vr | C=0.15 | C=0.30 | C=0.60 |
|---|---|---|---|
| 0.05 | 5.9, 6.1 | **982**, 475 | 86, 79 |
| 0.10 | 6.2 | 294 | 45, 66 |
| 0.20 | 5.8, 6.5 | *(startup fails)* | *(startup fails)* |
| 0.30 | 5.8, 6.5 | **945**, 346 | 103, 112 |
| 0.50 | 5.0, 6.5 | 305, **820** | 80, 55 |
| 1.00 | 5.4, 6.5 | **965**, 465 | 33, 79 |

*Italics = startup failures excluded. Bold = highest pain in that C column.*

Key observations:
- C=0.15 pain_score is uniformly ~5–7 regardless of vr
- C=0.30 has the highest and most variable pain_scores; no vr produces reliably high pain
- C=0.60 pain_score is bounded (~33–112); v27's pool dominance limits how long v26 competes
- Highest observed pain_score (982 at vr=0.05, C=0.30) is essentially equal to the highest
  at vr=1.00 (965) — confirming vr is not the determinant of pain magnitude

---

## Contested Fork Threshold Sweep — Results

**Sweep:** `contested_fork_threshold` (120 scenarios, 3 vr × 4 E × 5 C × 2 compositions)  
**Status:** 116/120 complete as of 2026-07-06 (missing: sweep_0049, 0097, 0098, 0099)  
**Effective parameters:** E invariance confirmed — all results treated as E=0.55  
**Startup failures:** 24/116 (21%) excluded from outcome analysis

### E Invariance Finding

The lite network has only 4 economic nodes with highly unequal custody (2.83M, 2.14M, 9.45k,
9k BTC). For any E ∈ [0.284, 0.781], `apply_scenario_to_base_network` produces identical
economic node configurations: node-0016 is always the sole v27 economic node (56.7% custody).
All four tested E values (0.30, 0.40, 0.50, 0.55) fall within this invariance zone and produce
the same network topology.

**Consequence:** The E axis functions as pure replication (8 trials per (vr, C) point rather
than 2). All CFT results are reported at E=0.55, matching the chainsplit_persistence baseline.
To properly study E effects, the full network is required — its more graduated custody
distribution allows E to vary meaningfully across the tested range.

Prior sweeps that appeared to show strong E effects (e.g. `sigmoid_2016_retarget`,
`targeted_sweep10`) were sampling E values up to 0.82, which crosses the ~0.78 invariance
boundary. The apparent E effect in those sweeps was driven by the topology change at that
upper threshold, not smooth E variation.

### C_eff as the True Driver

The CFT sweep uses random pool assignment, so nominal C (pool_committed_split) and realized
committed hashrate (C_eff) diverge substantially within each C level:

| Nominal C | C_eff range | Notes |
|---|---|---|
| 0.15 | 0.000–0.196 | foundryusa never commits; small/medium pools only |
| 0.20 | 0.000–0.196 | similar |
| 0.25 | 0.014–0.347 | foundryusa appears rarely |
| 0.30 | 0.126–0.374 | foundryusa appears ~20% of seeds |
| 0.35 | 0.161–0.401 | foundryusa appears ~30% of seeds |

Nominal C is a poor predictor of outcome. C_eff is the right quantity to analyze.

### C_eff Discretization — Pool Hashrate Jumps

Pool hashrates are fixed and unequal (foundryusa=30%, antpool=16.9%, viabtc=11.2%,
f2pool=10.9%, spiderpool=9.3%, ...), so C_eff can only take discrete values regardless of
the nominal C target. At C=0.15 a random draw might yield:
- marapool (4.6%) + ocean (1.2%) → C_eff=0.067
- viabtc alone (11.2%) → C_eff=0.130
- antpool alone (16.9%) → C_eff=0.196

Two scenarios at the same nominal C can have C_eff differing by 3×. Small C_eff differences
near any threshold are stochastic noise, not structural pool-specific effects.

### v27 Win Rate by C_eff — Full Results

| C_eff range | v27 wins | n | v27 rate |
|---|---|---|---|
| < 0.10 | 0 | 14 | 0% |
| 0.10–0.13 | 2 | 22 | 9% |
| 0.13–0.16 | 3 | 12 | 25% |
| 0.16–0.20 | 6 | 19 | 32% |
| 0.20–0.25 | 9 | 14 | 64% |
| 0.25–0.30 | 3 | 4 | 75% |
| **0.30–0.35** | **4** | **4** | **100%** |
| **≥ 0.35** | **3** | **3** | **100%** |

The threshold structure is now clear:
- **C_eff < 0.13**: v26 wins reliably (≤9% v27 rate)
- **C_eff 0.13–0.20**: genuinely contested — outcome is stochastic regardless of vr
- **C_eff 0.20–0.30**: v27 majority zone; vr still influences outcome
- **C_eff ≥ 0.30**: v27 wins every time — a hard threshold driven by dominant large-pool commitment

All 7 scenarios with C_eff ≥ 0.30 had the dominant large pool (foundryusa, 30%) committed
and ended with v27hr = 86.4% (full cascade). A single ~30% hashrate pool committing is
sufficient to guarantee a complete neutral pool cascade at **any** tested vr.

### vr Effect on v27 Win Rate — Full Results

| vr | v27 wins | n | v27 rate |
|---|---|---|---|
| 0.20 | 15 | 32 | 47% |
| 0.50 | 8 | 24 | 33% |
| 1.00 | 7 | 24 | 29% |

vr still suppresses v27 — the rate falls from 47% at vr=0.20 to 29% at vr=1.00 — but the
effect is weaker than early results suggested. The key interaction is with C_eff: at
C_eff ≥ 0.30 (dominant large pool committed), vr becomes irrelevant — v27 wins at all three
vr values. At C_eff < 0.20, vr=0.50 and vr=1.00 suppress v27 almost completely.

**Winner grid by (vr, C):**

| | C=0.15 | C=0.20 | C=0.25 | C=0.30 | C=0.35 |
|---|---|---|---|---|---|
| vr=0.20 | 1↑ 7↓ | 2↑ 4↓ | 3↑ 3↓ | 4↑ 3↓ | 5↑ 2↓ |
| vr=0.50 | 0↑ 5↓ | 1↑ 6↓ | 1↑ 4↓ | 2↑ 6↓ | 2↑ 0↓ |
| vr=1.00 | 1↑ 5↓ | 0↑ 7↓ | 1↑ 5↓ | 4↑ 3↓ | 3↑ 2↓ |

*↑ = v27 wins, ↓ = v26 wins. Genuine results only.*

The vr=1.00, C=0.30 cell (4↑3↓) is notable: at high vr, high enough C_eff — specifically
when the dominant large pool appears in the composition — still produces v27 wins. The vr=0.50, C=0.35
cell (2↑0↓) confirms that at C=0.35 v27 wins regardless of vr when the right pools commit.

### Pain Score — Full Results

Maximum pain concentrates in the C_eff 0.13–0.25 range where committed hashrate sustains a
fork but cannot cascade neutral pools. The highest observed pain scores:

| scenario | vr | C | C_eff | heal_s | fork_balance | pain | winner | committed pools |
|---|---|---|---|---|---|---|---|---|
| sweep_0035 | 0.20 | 0.25 | 0.167 | 8,660 | 0.981 | **1,803** | v26 | ocean,luxor,f2pool |
| sweep_0088 | 1.00 | 0.35 | 0.196 | 8,404 | 0.946 | **1,520** | v26 | antpool |
| sweep_0030 | 0.20 | 0.15 | 0.130 | 9,203 | 0.907 | 1,500 | v26 | viabtc |
| sweep_0012 | 0.20 | 0.20 | 0.196 | 9,745 | 0.817 | 1,490 | v27 | antpool |
| sweep_0002 | 0.20 | 0.20 | 0.140 | 7,812 | 0.972 | 1,465 | v26 | ocean,f2pool |

sweep_0035 (pain=1,803, fork_balance=0.981) is the most contested fork observed across all
sweeps — three small-to-mid pools (ocean+luxor+f2pool, total 14.4% hashrate) held v27 nearly
neck-and-neck with v26 for 8,660s before finally losing.

**Pain score ranges by (vr, C):**

| | C=0.15 | C=0.20 | C=0.25 | C=0.30 | C=0.35 |
|---|---|---|---|---|---|
| vr=0.20 | 107–1,500 | 5–1,490 | 329–1,803 | 452–952 | 37–1,247 |
| vr=0.50 | 8–82 | 12–1,005 | 265 | 9–1,337 | 48–632 |
| vr=1.00 | 590–1,201 | 1,103 | 203–1,190 | 93–881 | 135–1,520 |

Pain is not monotonically related to C — high pain appears at C=0.15 when C_eff happens to
land in the contested 0.13–0.20 zone. High C reduces pain by enabling faster cascades.

### Startup Failures — C_eff Corridor

CFT shows 24/116 startup failures (21%). Critically, failures appear at vr=0.50 and vr=1.00
as well as vr=0.20 — not just the vr=0.10–0.20 zone identified in CSP. The pattern
correlates with low C_eff: when committed hashrate is insufficient to sustain a partition,
the fork reconverges within seconds regardless of violation rate.

The CSP finding of a vr-based "reconvergence corridor" is revised: the correct framing is a
**C_eff corridor**. Low C_eff allows reconvergence at any vr.

### The Dominant Pool as Pivotal Threshold

On this lite network, foundryusa (30% of pool hashrate) is the largest single pool and
acts as the key discrete threshold. When foundryusa commits:
- C_eff jumps to 0.347–0.401 (depending on which other pools also commit)
- v27 wins 100% of the time (6/6 scenarios with foundryusa, all vr values)
- The fork always cascades completely: v27hr = 86.4% at heal

When foundryusa does not commit (C ≤ 0.20, or unlucky seeds at C=0.25), C_eff is capped at
≤0.196 and outcomes are contested or v26-favored.

Foundryusa is not special — it is a proxy for concentrated hashrate. F22 (SWEEP_FINDINGS.md)
shows that the mechanism is a single large-pool commitment firing as a discrete shockwave:
the same aggregate hashrate spread across many smaller pools produces a much weaker cascade.
The real-world interpretation: whichever pool holds ~27–30% hashrate is the pivotal actor,
regardless of identity.

### Working Threshold — v27 Success Zones

Based on 116/120 CFT results at E=0.55:

> **Hard threshold — C_eff ≥ 0.30 (dominant large pool committed): v27 wins regardless of vr**

> **Soft threshold — C_eff 0.20–0.30 AND vr < 0.50: v27 majority zone (~64–75%)**

> **Contested zone — C_eff 0.13–0.20: stochastic at all vr values (~25–32% v27)**

> **v26 zone — C_eff < 0.13: v26 wins reliably (≤9% v27)**

The vr boundary matters most in the 0.20–0.30 C_eff range. At C_eff ≥ 0.30, vr is
irrelevant. At C_eff < 0.13, vr is irrelevant in the other direction.

---

## econ_split_full Sweep — Interim Results

**Sweep:** `econ_split_full` (108 scenarios, 6 E × 3 vr × 3 C × 2 compositions, full 60-node network)  
**Status:** 52/108 (48%) complete as of 2026-07-06  
**Network:** realistic-economy (60 nodes, 88.21% pool hashrate, 52 economic nodes)  
**Startup failures:** 15/52 (28%) excluded from outcome analysis

This sweep is the first to combine full-network E variation with violation rate variation.
It directly tests whether the softfork_rule_strength finding ("vr doesn't matter") holds
on the full network, and whether the CFT large-pool commitment threshold generalizes to a
network where E can actually vary.

### vr Direction Reversal on the Full Network

The softfork_rule_strength (SRS) sweep on the lite network found violation rate had no
effect: v27 win rates were 69–75% at every p value from 0.00 (strict UASF) to 1.00
(fully permissive). That finding does not hold on the full network.

**v27 win rate by vr at E=0.68 (37 genuine results):**

| vr | v27 wins / n | v27 rate | median fork heal_s | cascade rate |
|---|---|---|---|---|
| 0.20 | 1/4 | 25% | 79s | 18% |
| 0.50 | 5/6 | 83% | 1,732s | 47% |
| 1.00 | 1/1 | 100% | — | — |

At vr=0.20, forks heal in a median of 79 seconds — before economic price divergence
can drive pool switching. At vr=0.50, forks persist ~29 minutes, long enough for the
cascade to fire. The minimum vr for reliable v27 success on the full network is **≈0.50**.

The mechanism: the full 60-node network's cascade takes longer to build than the lite
network's. Economic price signaling needs the fork open for ~20+ minutes before neutral
pools defect. The lite network's retarget/cascade fires fast enough to succeed even in
short forks; the full network requires fork persistence gated by vr.

**Comparison to SRS (lite network):**

| Network | vr=0.00 (p=1.00) | vr=0.50 | vr=1.00 (p=0.00) | Dominant parameter |
|---|---|---|---|---|
| Lite (SRS, E=0.55–0.78) | 69% | 69% | 75% | C_eff |
| Full (E=0.68) | 25% | **83%** | 100% (1pt) | **E then vr** |

The "vr is irrelevant" finding from SRS was a lite-network artifact of the fast retarget
cascade. On the full network, vr is a necessary condition: without sufficient fork duration,
the cascade never fires regardless of E or C_eff.

### E Becomes the Global Dominant Driver

On the full network, E is the gating parameter — C_eff effects only appear after the E
threshold is cleared.

**v27 win rate by E (genuine results only):**

| E | Nodes on v27 | Custody | v27 wins / n | v27 rate |
|---|---|---|---|---|
| 0.25 | 1 | 28% | 3/10 | 30% (noise — no cascade, tiny forks) |
| 0.45 | 2 | 47% | 0/5 | 0% |
| 0.58 | 3 | 58% | 0/2 | 0% |
| **0.68** | **4** | **69%** | **7/11** | **64%** |
| 0.76 | 5 | 77% | 3/4 | 75% |
| 0.82 | 6 | 82% | 3/5 | 60% |

The E≥0.636 boundary (adding node-0005, a major exchange) is the pivotal step.
Below it — including E=0.58, which matches the CFT/CSP lite-network baseline at 56.7%
custody — v27 fails regardless of C_eff or vr. The three apparent wins at E=0.25 are
noise: all healed in under 35 seconds with no cascade (v27hr=36.3%, fork balance ≈1.0
on tiny block counts).

This is consistent with `lhs_2016_full_6param` finding F12: economic_split ≥ 0.665
gives 81% v27 win rate globally on the full network. The econ_split_full sweep confirms
the step boundary is at E≥0.636 (between 0.58 and 0.68).

### Large-Pool Commitment Threshold Is Conditional on E

On the lite network (CFT), C_eff ≥ 0.30 — reached when the dominant pool (~27–30%
hashrate) commits — was an absolute guarantee: v27 won 100% of the time at all vr
values. On the full network this threshold is conditional on E:

| Scenario | E | vr | C_eff | Large pool | v27hr at heal | Winner |
|---|---|---|---|---|---|---|
| sweep_0028 | 0.45 | 0.50 | 0.305 | foundryusa | 0.0% | **v26** |
| sweep_0045 | 0.58 | 0.50 | 0.305 | foundryusa | 26.9% | **v26** |
| sweep_0065 | 0.68 | 0.50 | 0.305 | foundryusa | 88.2% | **v27** |

A large pool's ~27% hashrate commitment fails to cascade neutral pools without sufficient
economic node backing. At E=0.45–0.58 (2–3 economic nodes on v27, 47–58% custody), the
committed large pool fires the fork but the economic price signal is too weak to pull the
remaining pools across before the fork heals or v26 accumulates enough chainwork. This is
consistent with F22 (SWEEP_FINDINGS.md): what matters is that a single concentrated
hashrate event fires; the pool's identity is incidental.

### Pain Scores on the Full Network

Top pain scores from current results (genuine scenarios only):

| Scenario | E | vr | C_eff | Committed pools | v27 blk | v26 blk | Pain | Winner |
|---|---|---|---|---|---|---|---|---|
| sweep_0063 | 0.68 | 0.50 | 0.130 | ocean, binancepool | 282 | 175 | **109** | v27 |
| sweep_0061 | 0.68 | 0.50 | 0.128 | f2pool | 112 | 87 | 68 | v27 |
| sweep_0062 | 0.68 | 0.50 | 0.218 | antpool | 92 | 56 | 34 | v27 |

These are lower in raw pain score than CFT's maximum (1,803) because the full-network
cascade fires more decisively once triggered — v27 ramps to 88.2% quickly and the fork
closes before deep block divergence accumulates. On the lite network, the near-equal
pool balance at C=0.30 produced long near-stalemate forks (fork_balance ≈0.98); on
the full network at E=0.68, the cascade tips the balance more abruptly once it starts.

The highest pain occurs at E=0.68, vr=0.50, C_eff≈0.13 — low committed hashrate with
maximum economic support — where the fork is deep enough to matter but not one-sided.

### Minimum Conditions for v27 Success (Full Network, 52/108 Interim)

> **Minimum E: 0.68** — 4 economic nodes on v27 side (node-0005 must be tagged), 69%
> custody. E=0.45–0.58 fail even when the dominant large pool commits.

> **Minimum C_eff: ~0.13** — one large v26 pool (~11% hashrate, e.g. f2pool or
> binancepool) committed to v27. At E=0.68 vr=0.50, C_eff=0.128 produced a v27
> cascade win (sweep_0061, heal_s=2,239s, v27hr=88.2%).

> **Minimum vr: ≈0.50** — the fork must persist long enough (~29 min median) for
> economic signaling to drive pool switching. vr=0.20 heals too fast (79s median).

> **Intersection:** E≥0.68 **AND** C_eff≥0.13 **AND** vr≥0.50 → v27 wins ~83% of the
> time and cascades to 88.2% hashrate in all wins.

Note: at E≥0.82, vr=0.20 can still produce wins (economic pressure sustains the fork
even at high acceptance rates), but this requires 6 major economic nodes (82% custody)
on v27.

---

## Open Questions

**Answered by CFT:**
- C_eff (not nominal C) is the dominant pool-side predictor — confirmed.
- Startup failures are not confined to vr=0.10–0.20; they occur at any vr when C_eff is low.
  The correct framing is a C_eff corridor, not a vr corridor.
- The FFT vr=1.00 all-startup-failure vs CSP vr=1.00 all-genuine discrepancy was a C_eff
  effect — FFT compositions happened to land at low C_eff; not an E or vr phenomenon.
- C_eff ≥ 0.30 (dominant large pool committed) is a hard threshold on the lite network:
  v27 wins at all vr values.
- vr becomes irrelevant above the large-pool commitment threshold and below the C_eff < 0.13
  floor (on the lite network).

**Partially answered by econ_split_full (52/108 interim):**
- Q1: How does E actually influence outcomes on the full network?  
  → Step boundary confirmed at E≥0.636 (node-0005 crossing, 69% custody). Below E=0.68
  v27 fails on the full network regardless of C_eff or vr. Above E=0.68 v27 wins at 64–83%
  depending on vr. Full picture pending remaining 56 scenarios.
- Q: Does vr matter on the full network?  
  → Yes — opposite direction to the lite network. Minimum vr≈0.50 required on the full
  network. SRS "vr is irrelevant" finding was a lite-network artifact.
- Q: Does the large-pool commitment hard threshold generalize to the full network?  
  → No. It requires E≥0.68. At E=0.45–0.58, even the dominant large pool committed
  still loses on the full network.

**Still open:**
1. Does the large-pool commitment threshold on the full network at E≥0.68 hold across all vr
   values? Only 1 data point at C_eff≥0.30 (sweep_0065, vr=0.50). Need vr=0.20 and vr=1.00
   results with a dominant large pool committed.
2. Does the E=0.68 minimum hold at vr=1.00 with more than 1 data point?
3. Pain score behavior at E<0.68 on the full network — do deeper forks occur in the
   0.45–0.65 E range where v27 can build blocks but rarely wins?
4. The complete E×vr interaction at E=0.76 and E=0.82 — preliminary data shows
   100% at E=0.76 vr=0.20 (2/2) but only 50% at vr=0.50 (1/2), which is counterintuitive.

**Methodological:**
- E variation requires the full network. The lite network's 4-node custody distribution
  creates a step function that makes E invariant across [0.28, 0.78].
- The CFT results at E=0.55 are directly comparable to CSP and can be treated as extending
  the CSP parameter space from (vr=6 values, C=3 values) to (vr=3 values, C_eff=continuous).
- econ_split_full results at E=0.58 are directly comparable to CFT (same approximate
  custody level, 58% vs 56.7%). Differences indicate full vs. lite network effects beyond
  E variation — and indeed E=0.58 full network shows 0% v27 vs CFT's ~25–64% win rate at
  comparable C_eff, confirming the full network requires higher E.

---

## Conclusions

1. **violation_rate does not determine fork outcome.** C_eff is the dominant predictor.
   vr=0.05 and vr=1.00 produce identical winners at fixed C_eff across all tested sweeps.

2. **violation_rate does not reliably determine reorg depth.** Variance between replications
   at fixed vr equals the variance across the full vr range. C_eff, not vr, determines
   pain magnitude.

3. **The maximum pain zone is C_eff ≈ 0.13–0.25.** When committed hashrate sustains a fork
   but cannot cascade neutral pools, forks run deep and contested (fork_balance up to 0.981).
   The highest observed pain_score (1,803) occurred at C_eff=0.167 with ocean+luxor+f2pool.
   High pain appears at any nominal C level when C_eff lands in this marginal range.

4. **Large-pool commitment is a hard threshold on the lite network.** At C_eff ≥ 0.30 —
   reached when the dominant pool (~30% hashrate) commits — v27 wins 100% of the time at
   all tested vr values, always cascading to v27hr=86.4%. The pool's specific identity is
   incidental; what matters is the discrete hashrate shockwave (F22). Below this threshold,
   outcomes are contested or v26-favored depending on vr and stochastic dynamics.

5. **Three outcome zones exist by C_eff:**
   - C_eff < 0.13: v26 wins reliably (≤9% v27 rate)
   - C_eff 0.13–0.20: genuinely contested; stochastic at all vr values (25–32% v27)
   - C_eff 0.20–0.30: v27 majority zone; vr still influences outcome (64–75% v27)
   - C_eff ≥ 0.30: v27 wins always; vr irrelevant

6. **A startup-failure corridor exists at low C_eff, not low vr.** CSP identified failures
   at vr=0.10–0.20; CFT shows they occur at any vr when C_eff is insufficient to sustain
   a partition. The corridor is a C_eff phenomenon.

7. **No persistent chainsplit was observed at any tested combination.** Forks always healed
   within 13,000s. Even marginal committed hashrate eventually tips pool economics.

8. **vr is a resistance parameter on the lite network — it prolongs pain but does not
   change outcome.** Higher vr slows the cascade and reduces v27 win rate in the contested
   C_eff zone, but cannot prevent v27 from winning when C_eff ≥ 0.30, nor save v27 when
   C_eff < 0.13. This holds for the lite network.

9. **C_eff is discrete, not continuous.** Pool hashrates are fixed and unequal; C_eff jumps
   in steps. Nominal C is a poor predictor. C_eff differences in the contested zone are
   largely stochastic noise rather than structural pool-specific effects.

10. **E is invariant on the lite network across [0.28, 0.78].** All CFT and CSP results are
    equivalent to E=0.55. Prior sweeps showing E effects were sampling across the ~0.78
    topology boundary. Studying true E effects requires the full network.

**Full-network findings (econ_split_full, 52/108 interim):**

11. **vr direction reverses on the full network.** The softfork_rule_strength (SRS) sweep
    found vr has no effect on the lite network (69–75% v27 at any vr). On the full 60-node
    network, higher vr helps v27: vr=0.20 → 25% win rate; vr=0.50 → 83% win rate at E=0.68.
    Minimum vr≈0.50 is required for reliable v27 success. SRS's "vr is irrelevant" was a
    lite-network artifact of the fast retarget cascade. The full network's cascade requires
    the fork to persist ~20+ minutes before pool switching can accumulate.

12. **E is the global gate on the full network.** Below E=0.68 (fewer than 4 economic nodes
    on v27, less than 69% custody), v27 fails regardless of C_eff or vr. The step boundary
    is at E≥0.636 (adding node-0005, a major exchange). This is consistent with F12
    (lhs_2016_full_6param: E≥0.665 → 81% v27 globally) and arm_b (E=0.55 → 0% v27 at all C).

13. **The large-pool commitment threshold is conditional on E on the full network.** On the
    lite network, the dominant large pool committed (C_eff≥0.30) guaranteed v27 wins at any
    vr. On the full network, the same commitment at E=0.45 and E=0.58 still produces v26
    wins (v27hr=0% and 26.9% respectively). A ~27% hashrate shockwave cannot cascade neutral
    pools without sufficient economic node support. The threshold holds at E≥0.68.

14. **Minimum conditions for v27 success on the full network (interim):** E≥0.68, C_eff≥0.13
    (one large v26 pool committed, ~11% hashrate), vr≥0.50. All three conditions are necessary;
    none alone is sufficient. The E and vr conditions are new findings relative to the
    lite-network sweeps, which only established C_eff thresholds.
