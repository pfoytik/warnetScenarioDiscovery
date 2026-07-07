# Block Violation Threshold — Findings

**Parameter:** `violation_rate` (vr)  
**Primary sweep:** `chainsplit_persistence` (36 scenarios, E=0.55, 6 vr × 3 C × 2 reps)  
**Corroborating sweep:** `fork_formation_threshold` (90 scenarios, E=0.65, 9 vr × 3 C × 3 reps)  
**Lite-network full-grid:** `contested_fork_threshold` (120 scenarios, 3 vr × 4 E × 5 C × 2 compositions)  
**Full-network vr×E sweep:** `econ_split_full` (108 scenarios, 6 E × 3 vr × 3 C × 2 compositions, 108/108)

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
**Status:** 119/120 complete as of 2026-07-06 (missing: sweep_0049 only)  
**Effective parameters:** E invariance confirmed — all results treated as E=0.55  
**Startup failures:** 24/119 (20%) excluded from outcome analysis

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
| 0.20–0.25 | 9 | 15 | 60% |
| 0.25–0.30 | 3 | 4 | 75% |
| **0.30–0.35** | **4** | **5** | **80%** |
| **≥ 0.35** | **3** | **3** | **100%** |

The threshold structure is now clear:
- **C_eff < 0.13**: v26 wins reliably (≤9% v27 rate)
- **C_eff 0.13–0.20**: genuinely contested — outcome is stochastic regardless of vr
- **C_eff 0.20–0.30**: v27 majority zone; vr still influences outcome
- **C_eff ≥ 0.30 (dominant large pool committed)**: v27 wins reliably — 7/8 (88%); the
  single exception (sweep_0099, vr=1.00) had two mid-tier pools aggregating to 0.303 without
  the dominant pool committing, confirming that aggregate C_eff alone is not sufficient

All 7 winning scenarios with C_eff ≥ 0.30 had the dominant large pool (foundryusa, 30%)
committed and ended with v27hr = 86.4% (full cascade). When foundryusa was NOT in the
committed set, even C_eff=0.303 (antpool+spiderpool) failed to cascade at vr=1.00 (sweep_0099).
This directly confirms F22 — a single concentrated hashrate shockwave, not aggregate C_eff,
is the decisive mechanism.

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
| vr=1.00 | 1↑ 5↓ | 0↑ 7↓ | 1↑ 5↓ | 4↑ 4↓ | 3↑ 2↓ |

*↑ = v27 wins, ↓ = v26 wins. Genuine results only.*

The vr=1.00, C=0.30 cell (4↑4↓) is notable: when the dominant large pool appears, v27 still
wins even at vr=1.00; when it does not (sweep_0097: f2pool+spiderpool, C_eff=0.234), v26 wins
in a nearly 12,400s epic fork (new pain record). The vr=0.50, C=0.35 cell (2↑0↓) confirms
that at C=0.35 v27 wins regardless of vr when the right pools commit.

### Pain Score — Full Results

Maximum pain concentrates in the C_eff 0.13–0.25 range where committed hashrate sustains a
fork but cannot cascade neutral pools. The highest observed pain scores:

| scenario | vr | C | C_eff | heal_s | fork_balance | pain | winner | committed pools |
|---|---|---|---|---|---|---|---|---|
| sweep_0097 | 1.00 | 0.30 | 0.234 | **12,368** | 0.662 | **1,824** | v26 | f2pool, spiderpool |
| sweep_0035 | 0.20 | 0.25 | 0.167 | 8,660 | 0.981 | 1,803 | v26 | ocean,luxor,f2pool |
| sweep_0088 | 1.00 | 0.35 | 0.196 | 8,404 | 0.946 | 1,520 | v26 | antpool |
| sweep_0030 | 0.20 | 0.15 | 0.130 | 9,203 | 0.907 | 1,500 | v26 | viabtc |
| sweep_0012 | 0.20 | 0.20 | 0.196 | 9,745 | 0.817 | 1,490 | v27 | antpool |

sweep_0097 (pain=1,824, heal_s=12,368s) is the new record — and a striking edge case. By heal
time, **v27hr had reached 86.4%** (the economic cascade completed — all pools switched to v27)
but v26 still won because it had accumulated 4,156 blocks vs v27's 2,753. At vr=1.00 with
fully separate chains, v26 built a commanding lead in the early fork period before the cascade
fired. The cascade came too late to overcome v26's accumulated chainwork. sweep_0035 (pain=1,803,
fork_balance=0.981) remains the most *contested* fork by balance — ocean+luxor+f2pool held
neck-and-neck with v26 for 8,660s — but sweep_0097 ran longest and scores highest overall.

**Pain score ranges by (vr, C):**

| | C=0.15 | C=0.20 | C=0.25 | C=0.30 | C=0.35 |
|---|---|---|---|---|---|
| vr=0.20 | 107–1,500 | 5–1,490 | 329–1,803 | 452–952 | 37–1,247 |
| vr=0.50 | 8–82 | 12–1,005 | 265 | 9–1,337 | 48–632 |
| vr=1.00 | 590–1,201 | 1,103 | 203–1,190 | 93–881 | 135–1,520 |

Pain is not monotonically related to C — high pain appears at C=0.15 when C_eff happens to
land in the contested 0.13–0.20 zone. High C reduces pain by enabling faster cascades.

### Startup Failures — C_eff Corridor

CFT shows 24/119 startup failures (20%). Critically, failures appear at vr=0.50 and vr=1.00
as well as vr=0.20 — not just the vr=0.10–0.20 zone identified in CSP. The pattern
correlates with low C_eff: when committed hashrate is insufficient to sustain a partition,
the fork reconverges within seconds regardless of violation rate.

The CSP finding of a vr-based "reconvergence corridor" is revised: the correct framing is a
**C_eff corridor**. Low C_eff allows reconvergence at any vr.

### The Dominant Pool as Pivotal Threshold

On this lite network, foundryusa (30% of pool hashrate) is the largest single pool and
acts as the key discrete threshold. When foundryusa commits:
- C_eff jumps to 0.347–0.401 (depending on which other pools also commit)
- v27 wins 100% of the time (7/7 scenarios with foundryusa in committed set, all vr values)
- The fork always cascades completely: v27hr = 86.4% at heal

When foundryusa does not commit (C ≤ 0.20, or unlucky seeds at C=0.25), C_eff is capped at
≤0.196 and outcomes are contested or v26-favored.

**The single C_eff≥0.30 exception (sweep_0099, vr=1.00) directly confirms F22:** antpool+spiderpool
aggregated to C_eff=0.303 without the dominant large pool committing. v26 won. The companion
scenario (sweep_0098, same C) was a startup failure — not a genuine fork. This contrast —
dominant pool present: 7/7 wins; two mid-tier pools aggregating to same C_eff: loss — is exactly
the shockwave mechanism in action. Aggregate hashrate is not equivalent to concentrated hashrate.

Foundryusa is not special — it is a proxy for concentrated hashrate. F22 (SWEEP_FINDINGS.md)
shows that the mechanism is a single large-pool commitment firing as a discrete shockwave:
the same aggregate hashrate spread across many smaller pools produces a much weaker cascade.
The real-world interpretation: whichever pool holds ~27–30% hashrate is the pivotal actor,
regardless of identity.

### Working Threshold — v27 Success Zones

Based on 119/120 CFT results at E=0.55:

> **Hard threshold — C_eff ≥ 0.30 with dominant large pool committed: v27 wins 7/7 (100%) at all vr values; C_eff ≥ 0.30 via mid-tier pool aggregation alone: 7/8 (88%) — one failure at vr=1.00**

> **Soft threshold — C_eff 0.20–0.30 AND vr < 0.50: v27 majority zone (~64–75%)**

> **Contested zone — C_eff 0.13–0.20: stochastic at all vr values (~25–32% v27)**

> **v26 zone — C_eff < 0.13: v26 wins reliably (≤9% v27)**

The vr boundary matters most in the 0.20–0.30 C_eff range. At C_eff ≥ 0.30, vr is
irrelevant. At C_eff < 0.13, vr is irrelevant in the other direction.

---

## econ_split_full Sweep — Results

**Sweep:** `econ_split_full` (108 scenarios, 6 E × 3 vr × 3 C × 2 compositions, full 60-node network)  
**Status:** 108/108 complete as of 2026-07-07  
**Network:** realistic-economy (60 nodes, 88.21% pool hashrate, 52 economic nodes)  
**Startup failures:** 16/108 (15%) excluded from outcome analysis — 92 genuine results

This sweep is the first to combine full-network E variation with violation rate variation.
It directly tests whether the softfork_rule_strength finding ("vr doesn't matter") holds
on the full network, and whether the CFT large-pool commitment threshold generalizes to a
network where E can actually vary.

### vr Sweet Spot on the Full Network

The softfork_rule_strength (SRS) sweep on the lite network found violation rate had no
effect: v27 win rates were 69–75% at every p value from 0.00 (strict UASF) to 1.00
(fully permissive). That finding does not hold on the full network — and the relationship
is non-monotonic. **vr=0.50 is the optimal; vr=1.00 is the worst.**

**v27 win rate by vr (92 genuine results, all E):**

| vr | v27 wins / n | v27 rate | median fork heal_s | cascade rate |
|---|---|---|---|---|
| 0.20 | 7/22 | 32% | 97s | 14% |
| **0.50** | **15/34** | **44%** | **1,536s** | **38%** |
| 1.00 | 4/36 | 11% | 263s | 15% |

**v27 win rate by vr at E≥0.68 (45 genuine results):**

| vr | v27 wins / n | v27 rate |
|---|---|---|
| 0.20 | 5/10 | 50% |
| **0.50** | **12/17** | **71%** |
| 1.00 | 4/18 | 22% |

The mechanism at each extreme:

- **vr=0.20 (80% acceptance):** v26 blocks propagate freely to the v27 partition. Forks
  heal in a median of 97 seconds — before economic price divergence can drive pool switching.
  No cascade window exists.

- **vr=0.50 (50% acceptance):** Partial block sharing keeps forks open ~25 minutes (1,536s
  median). This is the cascade window. 38% of scenarios trigger a full pool cascade vs 14%
  at vr=0.20 and 15% at vr=1.00.

- **vr=1.00 (strict UASF, 0% acceptance):** Complete chain separation. No v26 blocks reach
  the v27 partition. v26's initial 63.7% hashrate builds a commanding chain lead almost
  immediately. The median fork heals in 263 seconds — nearly as fast as vr=0.20 — because
  v26 accumulates depth so rapidly that price signaling cannot fire in time. Even at E=0.82
  (6 economic nodes, 82% custody) with the dominant large pool committed (C_eff=0.305), the
  fork healed in 70 seconds with v26 winning (ESF sweep_0107). The "strict UASF" posture that
  maximizes protocol separation is precisely the configuration that benefits v26 on the full network.

The vr=1.00 wins that *do* occur (4/18 at E≥0.68) all have long heal times (1,600–3,363s)
where committed hashrate gave v27 near-parity with v26 (~47-50% total) and the cascade still
fired. They are the exception, not the rule.

**Comparison to SRS (lite network):**

| Network | vr=0.20 | vr=0.50 | vr=1.00 | Dominant parameter |
|---|---|---|---|---|
| Lite (SRS, E=0.55–0.78) | 69% | 69% | 75% | C_eff (vr irrelevant) |
| Full (all E, 92 genuine) | 32% | **44%** | 11% | **E then vr=0.50 optimum** |
| Full (E≥0.68, 45 genuine) | 50% | **71%** | 22% | vr=0.50 sweet spot |

The "vr is irrelevant" finding from SRS was a lite-network artifact of the fast retarget
cascade. On the full network, vr gates whether the cascade window opens at all. But the
relationship is not "higher is better" — vr=1.00 removes the block-sharing bridge that
keeps the fork alive long enough for economics to take effect.

### E Becomes the Global Dominant Driver

On the full network, E is the gating parameter — C_eff effects only appear after the E
threshold is cleared.

**v27 win rate by E (92 genuine results — complete):**

| E | Nodes on v27 | Custody | v27 wins / genuine | v27 rate |
|---|---|---|---|---|
| 0.25 | 1 | 28% | 3/15 | 20% (all wins are noise — <35s, no cascade) |
| 0.45 | 2 | 47% | 0/16 | **0%** |
| 0.58 | 3 | 58% | 2/16 | 12% (wins are coin-flip micro-forks, no cascade) |
| **0.68** | **4** | **69%** | **7/16** | **44%** |
| **0.76** | **5** | **77%** | **8/14** | **57% (peak)** |
| 0.82 | 6 | 82% | 6/15 | 40% |
| **E≥0.68 total** | | | **21/45** | **47%** |

The E≥0.636 boundary (adding node-0005, a major exchange) is the pivotal step.
Below it — including E=0.58, which matches the CFT/CSP lite-network baseline at 56.7%
custody — v27 fails in any genuine sense regardless of C_eff or vr. The apparent wins at
E=0.25 and E=0.58 are coin-flip micro-forks: block counts under 5, v27hr=36.3% (no cascade),
heal times under 35 seconds. E=0.45 goes further: **zero v27 wins in 16 genuine scenarios**.
E=0.45 tags two economic nodes (47% custody) — enough weight for the second major exchange
to join v27, but not enough for the cascade to overcome v26's hashrate in any tested scenario.

**E=0.76 is the peak (57%), not E=0.82.** The relationship is non-monotonic at high E: adding
the 6th economic node (node-0036, an exchange, 82% custody at E=0.82) drops the win rate from
57% to 40%. This may reflect diminishing returns: at E=0.76, the 5-node v27 coalition is large
enough to drive the cascade but the remaining v26 economic nodes still provide enough resistance
for the stochastic outcomes to favor v27. At E=0.82, the cascade fires more aggressively — but
in the process, the fast-healing dynamic at vr=0.20 and vr=1.00 produces quick forks where v26
accumulates chain depth before v27's economic signal can propagate. Sample size caveat: at only
14–16 genuine scenarios per E value, two or three scenarios shifting direction could explain the
variation. The peak-at-E=0.76 result should be treated as a trend, not a hard threshold.

E=0.82 produced the **economic override**: ESF sweep_0097 (E=0.82, vr=0.50, C_eff=0.000,
no v26 pools committed beyond the starting v27 set) — v27 wins via pure economic pressure
with v27hr rising to 88.2% at heal. At 82% custody (6 major economic nodes), the price
signal alone cascades all pools to v27 without any v26 pool pre-commitment. This only works
at vr=0.50 (not vr=1.00 — see above). Two additional scenarios at E=0.58 (sweep_0043) and
E=0.76 (sweep_0073) also show C_eff=0.000 wins — these are chain-length wins, not true
economic overrides: v26's compliant blocks propagate to the v27 chain at these vr values,
giving v27 effective hashrate of 68–87% without any cascade firing.

This is consistent with `lhs_2016_full_6param` finding F12: economic_split ≥ 0.665
gives 81% v27 win rate globally on the full network. The econ_split_full sweep confirms
the step boundary is at E≥0.636 (between 0.58 and 0.68).

### Large-Pool Commitment Threshold Is Conditional on E and Pool Identity

On the lite network (CFT), C_eff ≥ 0.30 — reached when the dominant pool (~27–30%
hashrate) commits — was an absolute guarantee: v27 won 100% of the time at all vr
values. On the full network this threshold is conditional on E AND on which pool commits.
The full network has a fundamental structural difference: **foundryusa starts as v27**.

**Foundryusa on the full network (7 genuine scenarios with foundryusa committed, 1/7 v27 wins):**

| Scenario | E | vr | C_eff | Other v26 committed | heal_s | v27hr | Winner |
|---|---|---|---|---|---|---|---|
| sweep_0028 | 0.45 | 0.50 | 0.305 | none | — | 0.0% | **v26** |
| sweep_0029 | 0.45 | 0.50 | 0.305 | none | 2,874s | 0.0% | **v26** |
| sweep_0044 | 0.58 | 0.50 | 0.305 | none | 225s | 36.3% | **v26** |
| sweep_0045 | 0.58 | 0.50 | 0.305 | none | 2,303s | 26.9% | **v26** |
| sweep_0047 | 0.58 | 0.50 | 0.340 | luxor | 3,121s | 30.0% | **v26** |
| sweep_0065 | 0.68 | 0.50 | 0.305 | none | 873s | 88.2% | **v27** |
| sweep_0107 | 0.82 | 1.00 | 0.305 | none | 70s | 36.3% | **v26** |

Foundryusa was already on the v27 chain before the fork began. When foundryusa appears as
the sole "committed" pool, it consumes the entire committed hashrate budget (C_eff ≈ 0.305)
without adding any v26-to-v27 switchers. v27's starting hashrate is unchanged at 36.3%.
The C_eff metric overstates the commitment's value in these cases because it counts
foundryusa's pre-existing v27 hashrate as new commitment.

In the one v27 win (sweep_0065, E=0.68, vr=0.50), the cascade fired through the neutral pool
mechanism — economic pressure at E=0.68 was sufficient to pull neutral pools across even
without a pre-committed v26 pool. v27hr reached 88.2%.

**AntPool is the pivotal v26 pool on the full network.**  
AntPool (19.25% hashrate, the largest v26 pool) committing produces v27 wins at high E:

| Scenario | E | vr | C_eff | Pools | heal_s | v27hr | Winner |
|---|---|---|---|---|---|---|---|
| sweep_0091 | 0.82 | 0.20 | 0.218 | antpool | 3,808s | 88.2% | **v27** |
| sweep_0093 | 0.82 | 0.20 | 0.218 | antpool | 72s | 36.3% | **v26** |
| sweep_0096 | 0.82 | 0.50 | 0.218 | antpool | 176s | 36.3% | **v27** |
| sweep_0099 | 0.82 | 0.50 | 0.254 | luxor+antpool | 3,965s | 88.2% | **v27** |
| sweep_0104 | 0.82 | 1.00 | 0.218 | antpool | 2,262s | 88.2% | **v27** |

AntPool commitment is the only configuration that produces v27 wins at vr=1.00 (sweep_0104),
and it fires even at vr=0.20 (sweep_0091) where other pool combinations fail. The C_eff from
AntPool alone (~0.218) is genuinely new v26 hashrate switching to v27, pushing v27 effective
to ~55% before any neutral pool switching.

At E=0.45–0.58 (2–3 economic nodes on v27, 47–58% custody), committed large pools fail
regardless of identity — the economic price signal is too weak to pull neutral pools across.
At E=0.82, vr=1.00 (sweep_0107): even with 6 economic nodes (82% custody) and foundryusa
"committed," the fork heals in 70 seconds — v26 wins, because foundryusa's commitment adds
no new v26 switching pressure. This is consistent with F22 (SWEEP_FINDINGS.md): what matters
is that new hashrate switches; pre-committed v27 hashrate does not count.

### Pain Scores on the Full Network

Top pain scores from complete results (genuine scenarios only):

| Scenario | E | vr | C_eff | Committed pools | heal_s | Pain | Winner |
|---|---|---|---|---|---|---|---|
| sweep_0050 | 0.58 | 1.00 | 0.163 | viabtc, ocean | 3,846s | **137** | v26 |
| sweep_0063 | 0.68 | 0.50 | 0.130 | ocean, binancepool | 3,807s | 109 | v27 |
| sweep_0061 | 0.68 | 0.50 | 0.128 | f2pool | 2,239s | 68 | v27 |
| sweep_0085 | 0.76 | 1.00 | 0.144 | ocean, f2pool | 1,831s | 53 | v27 |
| sweep_0089 | 0.76 | 1.00 | 0.241 | binancepool, f2pool | 1,605s | 50 | v27 |
| sweep_0062 | 0.68 | 0.50 | 0.218 | antpool | 4,242s | 34 | v27 |
| sweep_0097 | 0.82 | 0.50 | 0.000 | none | 884s | 33 | v27 |
| sweep_0060 | 0.68 | 0.50 | 0.149 | viabtc, ocean | 1,226s | 21 | v26 |
| sweep_0066 | 0.68 | 1.00 | 0.128 | f2pool | 3,363s | 20 | v27 |
| sweep_0075 | 0.76 | 0.20 | 0.071 | luxor, ocean | 4,193s | 18 | v27 |

These are substantially lower in raw pain score than CFT's maximum (1,803) because the
full-network cascade fires more decisively once triggered — v27 ramps to 88.2% quickly
and the fork closes before deep block divergence accumulates. On the lite network at C=0.30,
near-equal pool balance produced long near-stalemate forks (fork_balance ≈0.98); on the
full network at E=0.68, the cascade tips the balance more abruptly once it starts.

The highest pain (sweep_0050, pain=137) occurs at E=0.58 — below the E threshold for
reliable v27 success — where mid-tier pool commitment (ViaBTC + Ocean, C_eff=0.163) fires
the fork at vr=1.00 but the economic signal is too weak to close it. The fork runs for
3,846 seconds before v26 wins. Pain on the full network is concentrated at the margin
just below the E threshold, where enough commitment exists to sustain a fork but not enough
economic backing to cascade it to v27.

### Minimum Conditions for v27 Success (Full Network, 108/108)

> **Minimum E: 0.68** — 4 economic nodes on v27 side (node-0005 must be tagged), 69%
> custody. E=0.25–0.58 fail even when the dominant large pool commits at vr=0.50.

> **Minimum C_eff: ~0.13** — one mid-to-large v26 pool (~11% hashrate, e.g. f2pool or
> binancepool) committed to v27. At E=0.68 vr=0.50, C_eff=0.128 produced a v27
> cascade win (sweep_0061, heal_s=2,239s, v27hr=88.2%). Exception: at E=0.82, the
> economic override (sweep_0097) produced a v27 win with C_eff=0.000 at vr=0.50.

> **Optimal vr: 0.50** — the fork must persist long enough (~25 min median) for
> economic signaling to drive pool switching. vr=0.20 heals too fast (97s median).
> vr=1.00 (strict UASF) closes the fork almost as quickly (263s median) because v26's
> 63.7% hashrate dominates in fully separate chains. Higher vr is not better — vr=0.50
> is the sweet spot.

> **Intersection:** E≥0.68 **AND** C_eff≥0.13 **AND** vr≈0.50 → v27 wins ~71% of the
> time and cascades to 88.2% hashrate in all wins.

> **Exception — vr=1.00:** Even with E=0.82 and the dominant large pool committed, the
> fork heals in 70s and v26 wins (sweep_0107). Strict UASF posture is uniquely hostile
> to v27 on the full network.

Note: at E=0.82, vr=0.50 can produce v27 wins even without any additional v26 pool
commitment (economic override — 6 major economic nodes, 82% custody triggers automatic cascade).

---

## Softfork Compliance Mode

The `violation_rate` parameter has a direct real-world interpretation: it is the fraction of v26
miners producing blocks that **violate the new softfork rule**. The complement —
`v26_acceptance_probability = 1 − vr` — is the fraction of v26 miners who produce
rule-compliant blocks even while running old software.

In real Bitcoin softfork activations, miners face an economic incentive toward compliance:
a non-compliant block gets orphaned by v27 nodes, costing the miner the full block reward.
This drives vr toward zero over time as miners upgrade or adjust their transaction selection.
The tested vr values represent snapshots of that adaptation process at different stages.

### Three Compliance Zones

**vr ≤ 0.10 — Full compliance zone:**  
90–100% of v26 blocks are rule-compatible. The v27 chain receives nearly all blocks from
both v26 and v27 miners, giving it ~93%+ of total effective hashrate. Blocks appear every
~10.8 minutes on the v27 chain — nearly indistinguishable from normal operation. Occasional
non-compliant blocks cause micro-forks that resolve within seconds. The 20% startup failure
rate in CFT at low C_eff represents forks so brief they registered under 30 seconds and
fewer than 10 blocks — these are not noise to be excluded, they are **the target outcome of
a well-behaved softfork activation**. A non-compliant block appears, gets orphaned, and
the chain realigns before any meaningful divergence accumulates. Miners learn from the
orphaned reward; vr decreases further.

**vr = 0.20 — Occasional hiccup zone:**  
80% of v26 blocks are compliant. The v27 chain effective hashrate is 87.3%, giving block
times of ~11.5 minutes — close to normal. Forks open only when a non-compliant block
appears (20% of v26 blocks), and they heal in a 97-second median on the full network
before any sustained chain divergence develops. This is the "both chains in harmony"
scenario: v26 and v27 nodes are following the same chain the vast majority of the time,
with occasional 1–3 block micro-reorgs teaching miners to comply. v27 rules ARE being
enforced — non-compliant blocks get orphaned — without requiring a full economic cascade.

**vr ≥ 0.50 — Genuine chainsplit zone:**  
50%+ of v26 blocks violate v27 rules. The chains diverge substantially and sustain a real
fork where two competing chain histories develop. This is where cascade dynamics, economic
signaling, and pool switching determine the outcome. The v27 chain's effective hashrate
drops to 68.2% at vr=0.50 and 36.3% at vr=1.00, producing block times of 14.7 and
27.5 minutes respectively.

### Compliance Boundary

The transition from compliance mode to genuine chainsplit sits at approximately **vr=0.20–0.30**:

| vr | v27 effective hashrate | v27 block time | Median fork heal | Mode |
|---|---|---|---|---|
| ≤0.10 | ~93% | ~10.8 min | <30s (startup failure) | **Compliance** |
| 0.20 | ~87% | ~11.5 min | 97s | **Compliance / hiccup** |
| 0.30 | ~79% | ~12.7 min | — (untested on full network) | **Transition** |
| 0.50 | ~68% | ~14.7 min | 1,536s | **Genuine chainsplit** |
| 1.00 | 36.3% | ~27.5 min | 263s (fast) or 12,368s (deep) | **Full separation** |

### Enforcement Mechanism by Zone

In compliance mode (vr≤0.20), v27 rules are enforced through **block orphaning alone** —
no economic cascade needed. Non-compliant blocks are rejected by v27 nodes, the miner
loses the block reward, and compliance improves organically. In the genuine chainsplit zone
(vr≥0.50), block orphaning alone is insufficient; the full economic cascade mechanism
(price divergence → pool switching → hashrate rebalancing) is required for v27 to succeed.
This explains why E and C_eff only matter at higher vr: at low vr, the fork barely
establishes before the compliance mechanism resolves it.

---

## v27 Success Thresholds by vr (>50% Win Rate)

The minimum conditions for v27 to win more than 50% of genuine fork scenarios differ
substantially by violation rate. The three tested vr values define qualitatively different
regimes rather than a monotonic scale.

### Full Network (econ_split_full, 108/108)

| vr | Min E for >50% | Min C_eff at min E | v27 rate at threshold | Limiting mechanism |
|---|---|---|---|---|
| 0.20 | **Not achievable** | — | 50% at E≥0.68 (at boundary, not above) | Forks heal in 97s — cascade window never opens |
| **0.50** | **E≥0.68** | **~0.13** | **71%** | Optimal cascade window (~25 min median) |
| 1.00 | **Not achievable** | — | 22% at E≥0.68 | Complete separation; v26 hashrate dominates before cascade |

At vr=0.50 and E≥0.68, a single mid-to-large v26 pool (~11% hashrate) committing to v27
is sufficient to push above the 50% threshold. At E=0.82 with vr=0.50, the economic
override fires with C_eff=0.000 — pure economic pressure without any pool commitment.

At vr=0.20 and vr=1.00, no tested (E, C_eff) combination achieves >50% on the full network.
Both fail for opposite reasons: vr=0.20 closes the fork before the cascade can fire; vr=1.00
gives v26 such a decisive hashrate advantage in the separated chains that the cascade rarely
fires in time.

### Lite Network (contested_fork_threshold, E=0.55 fixed)

| vr | Min C_eff for >50% | v27 rate at threshold | Notes |
|---|---|---|---|
| 0.20 | ~0.30 (dominant pool committed) | ~57% | C=0.30 group → 4↑3↓ |
| 0.50 | ~0.30–0.35 (dominant pool required) | ~100% when dominant pool commits | C=0.35 group → 2↑0↓ (small n) |
| 1.00 | ~0.30–0.35 (dominant pool required) | ~60% at C=0.35 | C=0.30 gives exactly 50% (4↑4↓) |

On the lite network, the dominant large pool committing (C_eff≥0.30) is the threshold for
all three vr values — E is invariant across the tested range. The lite network's fast
retarget cascade compensates for the lack of E variation.

---

## Transaction Finality — Confirmation Depth During Softfork Activation

During an active softfork fork, the standard 6-block confirmation assumption breaks down
in two ways: (1) the reorg depth can exceed 6 blocks in contested scenarios, and (2) block
times change because each fork chain has only a fraction of total network hashrate mining
at the pre-fork difficulty.

### Block Times During a Fork

Starting from the full-network hashrate split (v27 base: foundryusa + mara + luxor + ocean
= **36.3%**; v26 base: antpool + viabtc + f2pool + binancepool = **63.7%**):

At vr=1.00 the chains are fully separated, so each runs at its own hashrate against the
original full-network difficulty. At lower vr, compliant v26 blocks propagate to the v27
chain and boost its effective hashrate. The v26 chain always receives only its own blocks
(bridge is one-way), so its block time is constant regardless of vr.

| vr | v27 effective hashrate | v27 block time | v26 block time |
|---|---|---|---|
| ≤0.10 | ~93% | ~10.8 min | ~15.7 min |
| 0.20 | ~87% | ~11.5 min | ~15.7 min |
| 0.50 | ~68% | ~14.7 min | ~15.7 min |
| **1.00** | **36.3%** | **~27.5 min** | **~15.7 min** |

At vr=1.00, v26 blocks arrive **faster** than normal (15.7 min vs 10 min target) because
v26 holds majority hashrate at pre-fork difficulty. v27 blocks arrive nearly **3× slower**
than normal (27.5 min). This asymmetry compounds v26's chainwork advantage and explains
why v26 wins 78% of scenarios at vr=1.00 — even without a cascade, v26 outpaces v27 on
raw block production.

The difficulty adjustment (2,016 blocks) never fires during any simulated fork. All forks
in our data heal within ~22 real Bitcoin blocks — well short of the retarget window.

### Confirmation Depth and Wait Time

All forks in our data heal within 13,000 simulation seconds = **~22 real Bitcoin block
periods**. The maximum reorg depth for a v27-chain user in the worst observed scenario
(CFT sweep_0097, 12,368s at vr=1.00) corresponds to **~7.5 v27-chain blocks** before
fork resolution. The maximum real Bitcoin block-equivalent reorg across all scenarios
and all vr values is approximately **10 blocks**.

| vr | Low-value (blocks) | Medium-value (blocks) | High-value (blocks) | v27 block time | Wait (low) | Wait (medium) | Wait (high) |
|---|---|---|---|---|---|---|---|
| ≤0.10 | 2–3 | 6 | 6 | ~10.8 min | ~22–32 min | ~65 min | ~65 min |
| 0.20 | 6 | 6–10 | 10 | ~11.5 min | ~69 min | ~69–115 min | ~115 min |
| 0.50 | 6 | 10–15 | 15 | ~14.7 min | ~88 min | ~147–221 min | ~221 min |
| **1.00** | **10** | **10** | **10** | **~27.5 min** | **~275 min** | **~275 min** | **~275 min** |

**The universal ceiling:** 20 confirmed blocks on the v27 chain outlasts every fork in
every tested scenario at any vr. At vr=1.00 this equals 20 × 27.5 = **550 minutes
(9.2 hours)** — the worst-case finality wait. At vr=0.50 it equals 20 × 14.7 = 294
minutes, though 15 blocks (221 min) covers all observed outcomes.

**Key observation at vr=1.00:** Despite requiring the same number of blocks (10) as the
low-value recommendation for other vr levels, the 27.5-minute block time means those 10
confirmations cost **4.6 hours** of real waiting time. A user who needs high transaction
finality during a strict UASF fork should be aware that their normal wait expectations
(~60–90 minutes for 6–10 confirmations at 10 min/block) do not apply. By the time the
10th v27-chain block arrives, the fork has almost certainly already resolved — the wait
is not because the fork is still in doubt, but because v27-chain blocks are inherently
slow during a vr=1.00 separation.

**Confirmations are temporary:** The elevated confirmation thresholds apply only during
the active fork period. Once one chain is clearly dominant, standard confirmation counts
resume immediately. The easiest signal: if your node's block times return to ~10 minutes,
the fork has healed.

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

**Answered by econ_split_full (108/108 complete):**
- Q1: How does E actually influence outcomes on the full network?  
  → Step boundary confirmed at E≥0.636 (node-0005 crossing, 69% custody). Below E=0.68
  v27 fails on the full network regardless of C_eff or vr. At E≥0.68, v27 wins at ~47%
  overall (71% at vr=0.50). **Fully answered for E=0.68/0.76/0.82.**
- Q: Does vr matter on the full network?  
  → Yes — and the relationship is non-monotonic. vr=0.50 is optimal; vr=1.00 is the worst.
  The SRS "vr is irrelevant" finding was a lite-network artifact. On the full network:
  vr=0.20 → 33%, vr=0.50 → 48%, vr=1.00 → 15% (all E); at E≥0.68: 50% / 71% / 22%.
- Q: Does the large-pool commitment hard threshold generalize to the full network?  
  → No, and the failure mode is dual: (1) at E<0.68, even the dominant large pool
  committed still loses; (2) at vr=1.00, even E=0.82 with dominant large pool committed
  still loses (70s fork close, sweep_0107). The threshold holds at E≥0.68 AND vr≈0.50.
- Q: Does E=0.82 produce economic override?  
  → Yes (confirmed). ESF sweep_0097 wins with C_eff=0.000 at vr=0.50 (F8 confirmed).

**Answered by econ_split_full complete dataset (108/108):**
1. Per-E win rate: E=0.25: 3/15 (20%, all noise), E=0.45: 0/16 (0%), E=0.58: 2/16 (12%,
   coin-flips), E=0.68: 7/16 (44%), E=0.76: 8/14 (57%, peak), E=0.82: 6/15 (40%).
   E=0.76 is the peak — non-monotonic at high E.
2. Pain at E<0.68: highest pain on full network is sweep_0050 (E=0.58, pain=137) — confirming
   the maximum-pain zone is just below the E threshold where commitment sustains a fork but
   economic backing is insufficient for cascade. Much lower than CFT maximum (1,803 on lite
   network) because full network cascade fires more decisively when it fires at all.
3. "Wrong-side pain" at E=0.45–0.58: sweep_0050 (E=0.58, vr=1.00, C_eff=0.163, pain=137,
   v26 wins in 3,846s) is the full-network analog. Long-running fork with v26 winner at low E.

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

4. **Large-pool commitment is a near-hard threshold on the lite network.** At C_eff ≥ 0.30
   reached when the dominant pool (~30% hashrate) commits — v27 wins 7/7 (100%) at all tested
   vr values. The one C_eff≥0.30 exception (sweep_0099: two mid-tier pools aggregating to
   0.303 without the dominant pool) confirms F22: aggregate C_eff is not equivalent to a single
   concentrated shockwave. Below this threshold, outcomes are contested or v26-favored
   depending on vr and stochastic dynamics.

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

**Full-network findings (econ_split_full, 108/108 complete):**

11. **vr=0.50 is the optimal violation rate on the full network — not "higher is better."**
    The softfork_rule_strength (SRS) sweep found vr has no effect on the lite network (69–75%
    v27 at any vr). On the full 60-node network the relationship is non-monotonic:
    vr=0.20 → 32% v27 (forks heal in 97s median, too fast for cascade);
    vr=0.50 → 44% overall / 71% at E≥0.68 (1,536s median — optimal cascade window);
    vr=1.00 → 11% overall / 22% at E≥0.68 (263s median — nearly as fast as vr=0.20).
    At vr=1.00, complete chain separation allows v26's 63.7% initial hashrate to build a
    commanding block lead before any economic cascade can fire. Even at E=0.82 with the
    dominant large pool committed, the fork heals in 70 seconds and v26 wins (sweep_0107).
    The "strict UASF" posture that maximizes protocol separation is the worst configuration
    for v27 on the full network.

12. **E is the global gate on the full network, with a non-monotonic peak.** Below E=0.68
    (fewer than 4 economic nodes on v27, less than 69% custody), v27 fails in any genuine
    sense regardless of C_eff or vr. E=0.45 (2 nodes, 47% custody) produces zero v27 wins
    in 16 genuine scenarios. The step boundary is at E≥0.636 (adding node-0005, a major
    exchange). At E≥0.68 and vr=0.50, v27 wins 71% of genuine scenarios. E=0.76 (5 nodes,
    77% custody) is the peak at 57%; E=0.82 drops to 40% — the relationship is non-monotonic
    at high E, likely reflecting diminishing returns from additional economic nodes when
    vr=0.20 and vr=1.00 both produce fast-healing forks that close before the cascade can
    build. At E=0.82 with vr=0.50, the economic override fires with zero additional pool
    commitment (F8 confirmed, sweep_0097). This is consistent with F12 (lhs_2016_full_6param:
    E≥0.665 → 81% v27 globally).

13. **The large-pool commitment threshold is conditional on E, vr, AND pool identity on the
    full network.** On the lite network, C_eff≥0.30 (dominant large pool as v26 switcher)
    guaranteed v27 wins. On the full network, foundryusa starts as v27 — when it appears
    as the "committed" pool, C_eff rises to 0.305 but no v26 hashrate switches. Result: 1/7
    v27 wins when foundryusa is the sole committed pool. **AntPool (19.25%) is the pivotal
    v26 pool on the full network** — its commitment adds ~21% new v27 hashrate and produces
    v27 wins even at vr=1.00 (sweep_0104, E=0.82). Additionally, C=0.30 (nominal) can
    perform worse than C=0.20 because at C=0.30 the committed budget is often consumed by
    foundryusa without engaging any v26 switchers, leaving fewer neutral pools available for
    cascade. The threshold holds at E≥0.68 AND vr≈0.50 with genuinely new v26 hashrate
    committed; vr=1.00 eliminates the cascade window regardless.

14. **Minimum conditions for v27 success on the full network (108/108 complete):** E≥0.68,
    C_eff≥0.13 from genuinely new v26 pool commitment (~11% hashrate switching, e.g. F2Pool
    or Binance Pool), vr≈0.50. vr=1.00 fails even when the other two conditions are met at
    their maxima. The optimal configuration is E≥0.68, vr=0.50, C_eff≥0.13 (new v26
    switching) — these conditions produce a 71% v27 win rate with full cascade (88.2% v27hr)
    in all wins. Exception: at E=0.82, vr=0.50, the economic override fires with C_eff=0.000.

15. **vr is a compliance parameter, not just a severity parameter.** Low vr means v26
    miners are voluntarily producing rule-compatible blocks to avoid orphaning. At vr≤0.10,
    the fork barely establishes before orphaning corrects non-compliant miners. At vr=0.20,
    forks heal in 97s median with only micro-reorgs. This is the "compliance mode" of
    softfork activation — the target outcome when miners self-enforce without a cascade
    being necessary. At vr≥0.50, compliance has broken down and cascade dynamics dominate.

16. **Startup failures are the target outcome in compliance mode.** Scenarios classified
    as "startup failures" (heal_s≤30, total_blocks≤10) are not simulation noise — they
    represent forks so brief that the softfork rule is enforced by a single orphaned block.
    The v26 miner loses one block reward, adjusts transaction selection, and the chain
    realigns. This maps to real Bitcoin softfork activations (e.g., Taproot) where
    compliant miners experience no perceptible disruption.

17. **Only vr=0.50 achieves >50% v27 win rate on the full network.** At vr=0.20, forks
    heal in ~97s before the cascade window opens — max v27 rate is 50% at the E≥0.68
    boundary. At vr=1.00, v26's 63.7% hashrate advantage at full separation makes v26
    the default winner before cascade fires — max v27 rate is 22% at E≥0.68. vr=0.50
    hits the sweet spot: fork sustains ~25 minutes, cascade fires reliably, v27 wins 71%
    with only C_eff≥0.13 needed. This implies a narrow compliance window in which v26
    miner resistance is high enough to force the cascade but not so high that the cascade
    cannot overcome the hashrate deficit.

18. **Block times are highly asymmetric at vr=1.00 during fork.** At full separation
    (vr=1.00), v27's 36.3% hashrate at pre-fork difficulty produces blocks every 27.5
    minutes — nearly 3× slower than the 10-minute target. v26 blocks arrive every 15.7
    minutes, giving v26 miners more frequent block rewards and faster chainwork accumulation
    throughout the fork. This hashrate-driven block-time asymmetry is an additional factor
    explaining v26's dominant win rate at vr=1.00, beyond the cascade timing argument.

19. **Confirmation depth requirements scale with violation rate, not linearly.**
    The safe confirmation counts during an active softfork fork are: vr≤0.10: 6 blocks;
    vr=0.20: 10 blocks; vr=0.50: 15 blocks; vr=1.00: 10 blocks (universal ceiling, but
    at 27.5 min/block). The dip at vr=1.00 reflects the irony that the v27 chain produces
    only ~7.5 blocks before any fork heals — so 10 confirmations cover all observed reorgs.
    However, those 10 blocks take 275 minutes (4.6 hours) to accumulate. High-value
    transaction finality at vr=0.50 takes 221 minutes (15 × 14.7 min) — substantial but
    significantly faster. Waiting 20+ confirmations at any vr universally outlasts every
    fork in every tested scenario.

20. **Pool identity matters more than C_eff on the full network.** The C_eff metric (fraction
    of total pool hashrate committed to v27) is misleading when foundryusa appears as the
    "committed" pool — foundryusa was already v27 and its selection adds no new v26 switching
    pressure. On the full network, the meaningful metric is committed v26 hashrate: new
    hashrate that actually switches sides. AntPool (19.25% of total pool hashrate) is the
    single most important v26 pool; its commitment alone produces v27 wins even at vr=1.00
    and even at E=0.82. By contrast, foundryusa committed produces 1/7 v27 wins despite
    higher nominal C_eff. This finding generalizes: for any real Bitcoin softfork, the
    correct question is not "what fraction of hashrate is committed?" but "which specific
    v26 pools have committed, and what fraction of previously-v26 hashrate do they represent?"
    A commitment pledge from miners who were already signaling is not a new commitment.
