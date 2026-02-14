# Ideological War Scenario: Comparative Analysis

## 1. Scenario Description

This analysis compares 5 simulation runs of the **ideological_war** scenario, which models
a contentious fork between Bitcoin v27 and v26 on a 34-node virtual network (10 mining
pools, 4 economic/exchange nodes, and 20 user nodes split across both fork versions).

All runs share the same configuration:
- **Duration**: 240 simulated minutes (14,400 seconds)
- **Pool Scenario**: `ideological_war`
- **Economic Scenario**: `ideological_split`
- **Difficulty Adjustment**: Enabled (retarget every 144 blocks)
- **Reorg Metrics**: Enabled

The difference between runs is the source of randomness in block production timing:

| Run ID | Type | Date |
|--------|------|------|
| `det_idWar_021226` | **Deterministic** (no random seed) | Feb 12, 2026 |
| `idWar_seed_021326` | Random seed | Feb 13, 2026 |
| `idWar_seed_0213261` | Random seed | Feb 13, 2026 |
| `idWar_seed0213262` | Random seed | Feb 13, 2026 |
| `idWar_seed0213263` | Random seed | Feb 13, 2026 |

---

## 2. Network Configuration

### 2.1 Mining Pool Alignment

The scenario creates a hashrate imbalance where v27 supporters hold the minority:

| Pool | Hashrate | Fork Preference | Ideology Strength | Profitability Threshold | Max Loss (USD) |
|------|----------|-----------------|-------------------|------------------------|----------------|
| **Foundry USA** | 26.89% | v27 | 0.90 | 25% | $5,000,000 |
| **AntPool** | 19.25% | v26 | 0.90 | 25% | $5,000,000 |
| **ViaBTC** | 11.39% | v26 | 0.85 | 22% | $2,000,000 |
| **F2Pool** | 11.25% | v26 | 0.70 | 15% | $1,000,000 |
| **Binance Pool** | 10.04% | neutral | 0.00 | 1% | $0 |
| **MARA Pool** | 8.25% | v26 | 0.60 | 12% | $500,000 |
| **SBI Crypto** | 4.57% | neutral | 0.00 | 2% | $0 |
| **Luxor** | 3.94% | v27 | 0.80 | 20% | $500,000 |
| **OCEAN** | 1.42% | v27 | 0.85 | 22% | $200,000 |
| **Braiins Pool** | 1.37% | neutral | 0.10 | 5% | $0 |

**Faction Summary:**

| Faction | Combined Hashrate | Pool Count |
|---------|-------------------|------------|
| v27 supporters | **32.25%** | 3 (Foundry, Luxor, OCEAN) |
| v26 supporters | **50.14%** | 4 (AntPool, ViaBTC, F2Pool, MARA) |
| Neutral | **15.98%** | 3 (Binance, SBI Crypto, Braiins) |

### 2.2 Economic Configuration

Despite the hashrate disadvantage, v27 holds the **economic majority**:
- **v27 economic weight**: 55.0% (major exchanges with higher custody BTC)
- **v26 economic weight**: 45.0%

This creates the core tension: v27 is economically dominant but hash-power-deficient.

---

## 3. Results Comparison

### 3.1 Block Production

| Metric | det_021226 | seed_021326 | seed_0213261 | seed_0213262 | seed_0213263 | **Mean** | **Std Dev** |
|--------|-----------|-------------|--------------|--------------|--------------|----------|-------------|
| v27 blocks | 89 | 110 | 117 | 99 | 99 | **102.8** | 10.8 |
| v26 blocks | 1,409 | 1,414 | 1,405 | 1,435 | 1,397 | **1,412.0** | 14.3 |
| Total blocks | 1,498 | 1,524 | 1,522 | 1,534 | 1,496 | **1,514.8** | 16.6 |
| v27 share | 5.9% | 7.2% | 7.7% | 6.5% | 6.6% | **6.8%** | 0.7% |

v26 produces roughly **14x more blocks** than v27 across all runs. The v27 chain only
accumulates blocks during the brief early period before pools capitulate.

### 3.2 Final State

All runs converge to the same terminal state:

| Metric | All Runs |
|--------|----------|
| **Winning fork** | v26 |
| **Final v27 hashrate** | 0.0% |
| **Final v26 hashrate** | 98.37% |
| **Final v27 economic share** | 55.0% |
| **Final v26 economic share** | 45.0% |
| **v27 price** | ~$55,060-$55,202 |
| **v26 price** | ~$64,720-$64,862 |

Despite v27 having higher economic support, the v26 price ends ~18% higher than v27.
This is driven by the chainwork/hashrate dominance of v26, which provides stronger
security guarantees.

### 3.3 Chainwork & Difficulty

| Metric | det_021226 | seed_021326 | seed_0213261 | seed_0213262 | seed_0213263 |
|--------|-----------|-------------|--------------|--------------|--------------|
| v27 chainwork | 89.0 | 110.0 | 117.0 | 99.0 | 99.0 |
| v26 chainwork | 1,307.3 | 1,291.4 | 1,283.3 | 1,374.8 | 1,298.8 |
| **Chainwork ratio** | **14.7:1** | **11.7:1** | **11.0:1** | **13.9:1** | **13.1:1** |
| v26 final difficulty | 1.030 | 0.941 | 1.056 | 1.054 | 0.913 |

The chainwork ratio ranges from 11:1 to nearly 15:1, meaning v26's chain is
overwhelmingly more work. v27 never becomes competitive.

---

## 4. Reorg & Fork Dynamics

### 4.1 Network-Level Reorg Metrics

| Metric | det_021226 | seed_021326 | seed_0213261 | seed_0213262 | seed_0213263 | **Mean** |
|--------|-----------|-------------|--------------|--------------|--------------|----------|
| Reorg events | 9 | 11 | 7 | 11 | 9 | **9.4** |
| Fork incidents | 6 | 6 | 4 | 6 | 6 | **5.6** |
| Blocks orphaned | 156 | 180 | 229 | 190 | 175 | **186.0** |
| Orphan rate | 10.45% | 11.89% | 15.12% | 12.40% | 11.74% | **12.32%** |
| Reorg mass | 1,950 | 1,892 | 1,054 | 2,950 | 1,665 | **1,902.2** |
| Norm. reorg mass | 195.0 | 189.2 | 105.4 | 295.0 | 166.5 | **190.2** |
| **Consensus stress** | **24.22** | **33.10** | **16.50** | **56.98** | **21.59** | **30.48** |

The consensus stress score varies by **3.5x** across runs (16.5 to 57.0), showing that
stochastic block timing dramatically affects how turbulent the fork transition is, even
when the outcome is the same.

### 4.2 Reorg Event Timeline Pattern

All runs follow a consistent 3-phase pattern:

**Phase 1 - Early Neutral Defection (t ~600s)**
Binance Pool and Braiins Pool (neutrals) quickly switch from v27 to v26 as the v26 chain
pulls ahead. Reorg depth is small (16-29 blocks). Only 0-6 blocks orphaned per pool.

**Phase 2 - Core Capitulation (t ~2400-3000s)**
Foundry USA, Luxor, and OCEAN are forced to switch from v27 to v26 after their cumulative
opportunity costs exceed their max loss thresholds. This is the most impactful wave,
orphaning 55-90 blocks from Foundry alone.

**Phase 3 - Oscillation & Stabilization (t ~3600-10800s)**
Some pools briefly flip back to v27 before being overwhelmed again. This "rebellion"
phase varies most across seeds:

| Run | Latest reorg timestamp | Deepest single reorg | Most affected pool |
|-----|----------------------|---------------------|--------------------|
| det_021226 | t=12,608 | 1,186 blocks (Ocean) | Ocean |
| seed_021326 | t=7,204 | 621 blocks (Luxor) | Luxor |
| seed_0213261 | t=7,204 | 626 blocks (Foundry) | Foundry |
| seed_0213262 | t=10,807 | 1,018 blocks (Luxor/Ocean) | Luxor |
| seed_0213263 | t=8,406 | 756 blocks (Ocean) | Ocean |

---

## 5. Miner Cost Analysis

### 5.1 Opportunity Cost Summary

Only v27-aligned pools incur costs. v26-aligned and neutral pools pay **zero** opportunity
cost across all runs because they are always on the winning/profitable chain.

#### Foundry USA (26.89% hashrate, v27 preference)

| Metric | det_021226 | seed_021326 | seed_0213261 | seed_0213262 | seed_0213263 | **Mean** |
|--------|-----------|-------------|--------------|--------------|--------------|----------|
| Cumulative opportunity cost | $4,553,228 | $3,689,721 | $4,780,635 | $4,861,780 | $4,160,540 | **$4,409,181** |
| Ideology overrides | 4 | 4 | 5 | 4 | 4 | 4.2 |
| Forced switches | 19 | 19 | 18 | 19 | 19 | 18.8 |
| Max loss threshold | $5,000,000 | $5,000,000 | $5,000,000 | $5,000,000 | $5,000,000 | - |
| **Cost as % of max loss** | **91.1%** | **73.8%** | **95.6%** | **97.2%** | **83.2%** | **88.2%** |
| Blocks orphaned | 122 | 138 | 206 | 111 | 141 | 143.6 |
| Orphan rate | 30.4% | 33.2% | 50.0% | 28.5% | 37.3% | 35.9% |

Foundry USA, as the largest v27 supporter, bears the greatest absolute cost. Their
ideology strength (0.9) keeps them mining on v27 for 3-5 decision intervals before the
cumulative losses trigger a forced switch. Across runs, they lose **$3.7M-$4.9M**, which
is 74-97% of their $5M max loss tolerance. In the worst case (seed_0213262), they came
within 2.8% of their absolute maximum.

The 18-19 forced switches indicate that after the initial capitulation, the system keeps
re-evaluating and Foundry stays forced onto v26 for the remainder of the simulation.

#### Luxor (3.94% hashrate, v27 preference)

| Metric | det_021226 | seed_021326 | seed_0213261 | seed_0213262 | seed_0213263 | **Mean** |
|--------|-----------|-------------|--------------|--------------|--------------|----------|
| Cumulative opportunity cost | $387,414 | $479,396 | $466,884 | $480,627 | $353,870 | **$433,438** |
| Ideology overrides | 3 | 4 | 4 | 4 | 3 | 3.6 |
| Forced switches | 20 | 19 | 19 | 19 | 20 | 19.4 |
| Max loss threshold | $500,000 | $500,000 | $500,000 | $500,000 | $500,000 | - |
| **Cost as % of max loss** | **77.5%** | **95.9%** | **93.4%** | **96.1%** | **70.8%** | **86.7%** |
| Blocks orphaned | 8 | 30 | 11 | 62 | 11 | 24.4 |
| Orphan rate | 16.0% | 52.6% | 21.6% | 77.5% | 20.8% | 37.7% |

Luxor's costs range from $354K to $481K against a $500K max loss threshold.
Notably, seed_0213262 pushes Luxor to a 77.5% orphan rate -- the highest of any
pool in any run -- due to a massive late-game reorg at t=10,206 with depth 1,018 that
orphaned 44 of Luxor's blocks.

#### OCEAN (1.42% hashrate, v27 preference)

| Metric | det_021226 | seed_021326 | seed_0213261 | seed_0213262 | seed_0213263 | **Mean** |
|--------|-----------|-------------|--------------|--------------|--------------|----------|
| Cumulative opportunity cost | $183,088 | $194,846 | $168,268 | $173,221 | $199,999 | **$183,884** |
| Ideology overrides | 4 | 4 | 4 | 4 | 4 | 4.0 |
| Forced switches | 19 | 19 | 19 | 19 | 19 | 19.0 |
| Max loss threshold | $200,000 | $200,000 | $200,000 | $200,000 | $200,000 | - |
| **Cost as % of max loss** | **91.5%** | **97.4%** | **84.1%** | **86.6%** | **100.0%** | **91.9%** |
| Blocks orphaned | 20 | 9 | 7 | 11 | 20 | 13.4 |
| Orphan rate | 80.0% | 36.0% | 21.2% | 64.7% | 69.0% | 54.2% |

OCEAN is the smallest v27 supporter and proportionally the hardest hit. In seed_0213263,
OCEAN reaches **$199,999.82** -- essentially hitting its $200,000 max loss cap exactly.
OCEAN also has the most consistently high orphan rate (avg 54.2%) because its small
hashrate means nearly every block it mines on v27 gets orphaned when it capitulates.

### 5.2 Total v27 Coalition Costs

| Run | Foundry Cost | Luxor Cost | OCEAN Cost | **Total v27 Cost** |
|-----|-------------|------------|------------|-------------------|
| det_021226 | $4,553,228 | $387,414 | $183,088 | **$5,123,731** |
| seed_021326 | $3,689,721 | $479,396 | $194,846 | **$4,363,963** |
| seed_0213261 | $4,780,635 | $466,884 | $168,268 | **$5,415,786** |
| seed_0213262 | $4,861,780 | $480,627 | $173,221 | **$5,515,628** |
| seed_0213263 | $4,160,540 | $353,870 | $200,000 | **$4,714,410** |
| **Mean** | **$4,409,181** | **$433,438** | **$183,884** | **$5,026,504** |

The entire v27 coalition loses approximately **$5.0M on average** per simulation run.
Foundry absorbs 88% of that total cost, proportional to its hashrate share within the
v27 coalition.

### 5.3 v26-Aligned and Neutral Pool Costs

| Pool | Preference | Hashrate | Opportunity Cost (all runs) | Forced Switches | Orphan Rate |
|------|-----------|----------|----------------------------|-----------------|-------------|
| AntPool | v26 | 19.25% | **$0** | 0 | 0.0% |
| ViaBTC | v26 | 11.39% | **$0** | 0 | 0.0% |
| F2Pool | v26 | 11.25% | **$0** | 0 | 0.0% |
| MARA Pool | v26 | 8.25% | **$0** | 0 | 0.0% |
| Binance Pool | neutral | 10.04% | **$0** | 0 | 0.0% |
| SBI Crypto | neutral | 4.57% | **$0** | 0 | 0.0% |
| Braiins Pool | neutral | 1.37% | **$0** | 0 | 0.0% |

v26-aligned pools experience zero cost because their ideology aligns with the
profitable chain. Neutral pools also pay nothing because they follow profit immediately.
None of these 7 pools experience any reorgs, forced switches, or orphaned blocks.
They mine continuously on v26 from start to finish with perfect efficiency.

### 5.4 Cost Per Orphaned Block

| Pool | Avg Opportunity Cost | Avg Blocks Orphaned | **Avg Cost Per Orphan** |
|------|---------------------|---------------------|------------------------|
| Foundry USA | $4,409,181 | 143.6 | **$30,703** |
| Luxor | $433,438 | 24.4 | **$17,764** |
| OCEAN | $183,884 | 13.4 | **$13,723** |

Foundry's per-orphan cost is the highest because its larger hashrate means each orphaned
block represents more foregone revenue. At ~$30,700 per orphaned block, this represents
a significant fraction of a typical block reward.

---

## 6. The Ideology Override Mechanism

The simulation models a decision process where pools evaluate profitability every interval:

1. **Calculate profitability** on both forks (v27 vs v26 USD revenue)
2. **Rational choice**: pick the more profitable fork
3. **Ideology override**: if the pool prefers the less profitable fork and the loss is
   within their tolerance, they override the rational choice
4. **Forced switch**: if cumulative opportunity cost exceeds `max_loss_usd`, the pool is
   forced to follow profit regardless of ideology

In practice, the v27 pools follow this lifecycle:
- **Intervals 1-4**: Ideology overrides rational choice. Pools mine on v27 despite it
  being less profitable. The loss starts at ~7.4% and climbs to ~10.9%, staying within
  the 28-34% tolerance range.
- **Interval 4-5**: Cumulative costs cross the max loss threshold. Foundry hits $5M,
  Luxor hits $500K, OCEAN hits $200K. All three are forced onto v26.
- **Intervals 5-24**: Pools remain force-switched to v26 for the rest of the simulation.
  They never return to v27.

The early ideology overrides cost approximately:
- Foundry: ~$650K-$1M per interval (3-5 intervals = $2.0M-$4.8M before forced switch)
- Luxor: ~$95K-$150K per interval
- OCEAN: ~$34K-$54K per interval

---

## 7. Key Findings

### 7.1 The Fork is Never Competitive

With 32.25% hashrate, v27 cannot sustain a fork against v26's 50.14% (plus 16% neutrals
that immediately defect). The chainwork ratio of 11-15:1 in favor of v26 means there is
no point at which the fork is in question. The outcome is determined by hashrate
distribution, not economic weight.

### 7.2 Economic Majority Does Not Override Hashrate Majority

v27 holds 55% economic weight and its exchanges hold more custody BTC ($1.1M vs $900K),
yet v26 wins decisively. The price reflects this: v26 finishes at ~$64,800 vs v27's
~$55,100, a gap of ~18%. Hashrate security is priced in over economic ideology.

### 7.3 Cost Asymmetry is Total

The losing side (v27 coalition) pays ~$5M in aggregate opportunity costs while the
winning side pays exactly $0. There is no cost to being on the winning side of a fork
war. This creates a strong disincentive for miners to support the minority chain.

### 7.4 Stochastic Variation Affects Pain, Not Outcome

Random seeds produce a 3.5x range in consensus stress (16.5 to 57.0) and a 2.8x range
in reorg mass (1,054 to 2,950). However, the final outcome is identical across all runs.
The randomness determines *how turbulent the transition is*, not *which side wins*.

### 7.5 Foundry USA is the Critical Player

As the largest v27 supporter (26.89% hashrate, ~83% of the v27 coalition's mining power),
Foundry's decision to capitulate effectively ends the fork war. When Foundry switches at
t~2400-3000s, v27 is left with only Luxor (3.94%) and OCEAN (1.42%), which cannot sustain
any meaningful chain on their own.

### 7.6 Threshold Implications

To sustain a fork, the v27 coalition would likely need:
- Hashrate above ~50% to match v26's chainwork growth rate
- OR significantly higher max loss tolerances (>>$5M for Foundry) to delay capitulation
- OR enough hashrate that neutral pools (16%) are incentivized to join v27 instead of v26

The current 32.25% hashrate produces a fork that collapses within ~40-50 minutes of
simulated time and generates ~$5M in wasted costs for the losing coalition.
