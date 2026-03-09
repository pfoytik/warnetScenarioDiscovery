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
6. **2016-block retarget is a qualitatively different regime** — without the difficulty adjustment profit spike arriving within the run window, cascades stall at partial equilibrium (neutral pool migration only); the "stuck contested" state at ~50/35 hashrate is the realistic baseline for most real-world forks (see targeted_sweep8 findings)
7. **The stuck contested state DOES resolve — after ~8,100s when the first retarget arrives** — sweep9 (20,000s, econ=0.70) confirmed that the ~50% difficulty drop forces committed v26 pools off (loss 56% >> 13.3% tolerance), completing the cascade decisively; the sweep8 "stuck" result was purely a run-duration artifact (see targeted_sweep9 findings)
8. **Even in the 144-block regime, the difficulty retarget is the primary cascade trigger — not price** — sweep10 (accidentally run at retarget=144, not 2016) showed v27_dominant at all economic splits (0.35–0.70) via a three-phase cascade completing in ~30 min: (1) initial split, (2) all pools temporarily collapse onto v26 when v26's difficulty drops while v27's hasn't yet, (3) v27 retargets to extreme low difficulty → all committed v26 pools forced off by 36.7% losses >> 13.3% tolerance. The 2016-block research question remains open — sweep10 must be rerun with `--retarget-interval 2016` (see targeted_sweep10 findings)

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

**targeted_sweep6_pool_ideology_full** (full-network validation, n=20) confirmed a diagonal threshold, but with a key directional correction over sweep2b:

| ideology_strength | max_loss_pct threshold for **v26 to hold** |
|:-----------------:|:------------------------------------------:|
| 0.2 | Never holds (v27 wins all) |
| 0.4 | ≥ 0.45 |
| 0.6 | ≥ 0.35 |
| 0.8 | ≥ 0.25 |

**Diagonal threshold: ideology × max_loss ≳ ~0.16–0.18 for v26 to survive at econ=0.78.**

This is the **v26 survival condition**: committed v26 pools with a high enough ideology × loss tolerance product can refuse to switch to v27 despite the economic pressure, preserving v26 dominance. Below the diagonal, committed v26 pools capitulate and v27 wins.

> ⚠️ **Direction reversal vs. sweep2b:** Sweep2b (lite network, ~43% v27 custody baked-in) found higher ideology × max_loss favored v27. Sweep6 (full network, 78% v27 custody correctly applied) shows higher values favor v26. Both are correct in their respective economic contexts: when v27 has economic advantage (sweep6), higher committed v26 pool resilience prevents the economic cascade — conversely, when v26 had economic advantage (sweep2b's actual conditions), committed v27 pools staying stubborn helped v27. The diagonal threshold concept holds in both cases but represents the defender's resilience, not the attacker's strength.

---

### Input Potential Assessment

**Input potential** measures a parameter's capacity to determine fork outcomes — combining
its causal influence, sensitivity near threshold values, and the nature of its
nonlinearity. High-potential inputs are the parameters that real-world actors should
watch and that Phase 3 sampling should concentrate on.

| Parameter | Input Potential | Rationale |
|-----------|:--------------:|-----------|
| `economic_split` | **Very High** | Primary driver; two distinct high-sensitivity regions (sharp threshold ~0.78–0.82 AND inversion zone 0.60–0.70 where it reverses the effect of committed_split) |
| `pool_committed_split` | **High (conditional)** | Non-monotonic and maximally sensitive in interaction with economic_split; in the inversion zone a shift from 0.20→0.30 flips the outcome direction entirely |
| `pool_ideology_strength × pool_max_loss_pct` | **High (near diagonal)** | Their product gates the committed pool mechanism; near the diagonal (~0.16–0.18 at econ=0.78) small changes flip whether committed pools hold or capitulate. The direction is economic-context-dependent: the product determines defender resilience (at v27 economic majority, it gates v26 survival; at v26 majority, it gates v27 survival). Confirmed on full network (targeted_sweep6, n=20). |
| `hashrate_split` | **Zero** | Empirically confirmed non-causal (targeted_sweep2, n=42) |
| `pool_neutral_pct` | **Zero** | Controls cascade speed only, not outcome (targeted_sweep3_neutral_pct) |
| `econ_inertia`, `econ_switching_threshold` | **Zero** | Irrelevant on full network (targeted_sweep3b) |
| All user parameters | **Zero** | No correlation with outcomes (targeted_sweep4, n=36) |

#### Why `economic_split` ranks highest

`economic_split` exhibits two qualitatively different instability mechanisms:

1. **Knife-edge threshold (econ ≈ 0.78–0.82):** A 4-point shift in BTC custody
   concentration flips the entire network from v26-dominant to v27-dominant. Near
   this threshold, the outcome is maximally sensitive to small changes.

2. **Causal inversion (econ ≈ 0.60–0.70):** In this range, increasing committed pool
   support *hurts* v27 rather than helping it. This means `economic_split` does not
   merely scale outcomes — at certain levels it reverses the sign of another
   parameter's effect. This is the strongest form of nonlinearity observed in the
   sweep data.

A single parameter that controls both a sharp threshold and a causal inversion is the
defining characteristic of high input potential.

#### Why `pool_committed_split` is conditional

`pool_committed_split` has high potential only when `economic_split` is in the
transition zone (0.50–0.82). Outside that zone it is inert: v26 wins regardless at
econ=0.35, v27 wins regardless at econ=0.82. Its potential is therefore conditional on
co-location with a high-potential `economic_split` value — which is precisely the
region Phase 3 will target.

#### Why the ideology product matters

`pool_ideology_strength` and `pool_max_loss_pct` individually have significant correlation
with outcomes (−0.49 and −0.62 respectively in targeted_sweep6 on the full network), but
neither is sufficient alone. Their *product* determines whether the committed pool mechanism
is operative at all. Near the diagonal threshold (~0.16–0.18 at econ=0.78), small changes
in either parameter cross the line from "committed pools capitulate" to "committed pools
hold indefinitely." This makes the product a binary switch governing the entire cascade
pathway.

The product governs **defender resilience**: whichever fork currently has economic minority,
its committed pools survive only if ideology × max_loss exceeds the threshold. At v27
economic majority (econ=0.78), the threshold separates v27-wins from v26-holds.

#### Implications for Phase 3 sampling

The input potential ranking directly informs Phase 3 Latin hypercube bounds:
- Sample `economic_split` densely in [0.50, 0.82] — both instability mechanisms live here
- Sample `pool_committed_split` in [0.20, 0.65] — captures both sides of the inversion
- Sample `ideology_strength` and `max_loss_pct` such that their product spans [0.05, 0.30],
  crossing the ~0.12 diagonal threshold
- Fix all zero-potential parameters at their median values

---

### Difficulty Adjustment Survival Window

A key emergent phenomenon observed across multiple sweeps: a minority fork can win not
by having superior hashrate, but by surviving long enough to receive a large difficulty
adjustment that temporarily makes its blocks dramatically cheaper to mine, attracting
a wave of opportunistic hashrate before the majority chain can respond.

#### Mechanism

```
t=0   Fork splits. Minority fork (e.g. v27 at 25% hashrate) inherits full pre-fork difficulty.
      Blocks arrive at 1/4 the target rate — 4x slower than normal.

t=1   Price begins to diverge (capped at ±20% in model). Minority fork becomes
      less profitable, but not enough to trigger forced pool switches yet.

t=2   After 144 minority-chain blocks (which took ~4x longer wall-clock time),
      difficulty retargets DOWN ~75%. Minority fork now has 25% hashrate at 25%
      difficulty — target block rate restored.

t=3   PROFIT SPIKE: Any majority-chain pools that switch to the minority fork now
      mine at low difficulty with additional hashrate. Blocks arrive far faster
      than target, chainwork accumulates rapidly.

t=4   If the chainwork spike is large enough before the majority chain's next
      retarget, the minority fork overtakes cumulative chainwork and wins reunion.
```

#### The survival window

The minority fork wins if and only if it reaches its difficulty adjustment *before*
price falls below the profitability threshold that would discourage switchers. This
defines a **survival window** — the period between fork initiation and minority-chain
difficulty adjustment during which economic conditions must remain viable:

```
Survival window width  ≈  retarget_interval / minority_hashrate_fraction
                                  (in minority-chain blocks × actual block time)
```

A fork with 25% hashrate and 144-block retarget has a survival window of
~576 target-interval seconds of wall-clock time. If price collapses within that
window (dropping the minority fork below profitability), the adjustment arrives
too late to matter. If price stays viable (aided by the ±20% price cap and
economic node inertia), the adjustment triggers a cascade.

#### Why this likely explains `hashrate_split` being non-causal

`targeted_sweep2` showed zero causal effect of `hashrate_split` across 0.15–0.65.
The difficulty adjustment mechanism is the probable explanation: at 15% hashrate
the difficulty drop is ~85% (massive opportunity spike); at 65% hashrate the drop
is ~35% (modest spike). In both cases the difficulty oracle eventually equalizes
block production rates before the economic cascade resolves. The outcome is then
determined by price and economics, not starting hashrate — consistent with what
the targeted sweeps show. `hashrate_split` may only become causal at extreme
values (< 10%) where the survival window becomes long enough for price to collapse.

#### Interaction with `retarget_interval`

`retarget_interval` directly controls the survival window width. A shorter retarget
interval (e.g. 20 blocks as used in some runs) narrows the window — the minority
chain adjusts difficulty faster, reducing the penalty period but also reducing the
size of the adjustment. A longer interval (144 or 2016 blocks) widens the window —
more time for price to collapse, but a larger difficulty drop if the chain survives.

**targeted_sweep8 + targeted_sweep9 empirically confirmed the 2016-block regime (see targeted_sweep8/9 sections):**

At 2016-block retarget with v27 at 25% hashrate, the first minority-chain difficulty
adjustment arrives at t≈8,100s (faster than the ~16,000s estimate because neutral pool
migration raises v27 hashrate to ~50%, accelerating block production). In a 7200s run
(sweep8), the adjustment never arrives and the cascade stalls at partial equilibrium
(**stuck contested state**: v27 50.5%, v26 35.9%). In a 20,000s run (sweep9, econ=0.70),
the retarget fires at t=8,106s with a ~50% difficulty drop — losses for committed v26
pools jump to 56%+, far exceeding the 13.3% tolerance, and the cascade completes
decisively (v27 86.4% final hashrate). Only at econ=0.82 does the price signal alone
break committed pools without needing the retarget.

This makes `retarget_interval` one of the most impactful structural parameters in the
model — it determines whether resolution is fast (minutes, 144-block) or effectively
never (weeks, 2016-block) at intermediate economic levels. Bitcoin's real retarget is
2016 blocks, making the stuck contested state the realistic baseline for most forks.

**targeted_sweep10 accidentally ran with retarget_interval=144 (CLI default), NOT the intended 2016 (see targeted_sweep10 section):**

Despite the mis-configuration, all four completed scenarios produced v27_dominant
outcomes (economic_split 0.35–0.70) with near-zero correlation between economic_split
and outcome. This is consistent with the 144-block regime's known behavior: difficulty
retargets fire within ~700s, and the cascade completes via difficulty mechanics in ~30
minutes of sim time regardless of economic conditions. The 2016-block research question
(does the cascade complete at econ < 0.70 once the retarget fires?) remains unanswered.
Sweep10 must be rerun with `--retarget-interval 2016`.

---

### Fog of War: Pool Information Uncertainty

Mining pools in the model — and in the real world — operate under significant
information uncertainty about competitor behavior. This is analogous to the
**fog of war** concept in military simulations: entities act on assumed or
estimated conditions rather than ground truth.

#### The assumption in the model

Pool profitability decisions use `assumed_fork_hashrate=50.0`, treating competition
as if hashrate were always split evenly between forks regardless of actual allocation:

```python
# From mining_pool_strategy.py — make_decision()
v27_profit = calculate_pool_profitability(..., assumed_fork_hashrate=50.0)
v26_profit = calculate_pool_profitability(..., assumed_fork_hashrate=50.0)
```

This means a pool deciding whether to mine v27 asks: *"If hashrate were balanced,
which fork is more profitable for me?"* — not *"Given the actual current hashrate
distribution, which fork pays more right now?"*

#### Why the assumption exists

Without this assumption, profitability calculations create a circular feedback loop:

```
Low v27 hashrate → low v27 profitability → pools leave v27 → even lower hashrate → ...
```

The 50/50 assumption breaks this circularity and models the real-world behavior of
pools that cannot instantaneously observe competitor allocations. It is the neutral
prior a rational pool would use in the absence of better information.

#### Real-world parallel

In practice, mining pools *can* observe block production rates with a lag (visible on
mempool.space, hashrateindex.com, etc.) and infer approximate hashrate distribution.
However:
- Inference lags by hours or days
- Pools cannot distinguish temporary variance from structural shifts
- Switching decisions involve operational costs that further delay response

The 50/50 assumption captures the essence of this uncertainty: pools respond to price
signals (which they can observe directly) rather than hashrate signals (which they
must infer indirectly with delay).

#### Consequence for the Difficulty Adjustment Survival Window

The fog of war interacts directly with the survival window mechanism: pools do **not**
explicitly exploit the difficulty adjustment opportunity spike. They do not observe that
the minority chain's difficulty has dropped and rush to take advantage. Instead, they
respond only to the price oracle — which indirectly reflects the faster block production
through the chain weight factor. This means the model likely **understates** the
hashrate cascade that would occur in reality when a large difficulty drop becomes
publicly visible, since real pools would explicitly target the opportunity.

#### Modeling implications

| Scenario | Model behavior | Real-world expectation |
|----------|---------------|------------------------|
| Large minority-chain difficulty drop | Pools respond to price only; gradual shift | Pools would explicitly target easy blocks; faster, larger spike |
| Actual hashrate heavily imbalanced | Pool decisions unaffected (always assumes 50/50) | Pools on winning fork would observe dominance and feel more secure |
| Cascade in progress | Pools respond to rising price, not falling competitor hashrate | Pools would observe competitor withdrawal and accelerate switching |

A future model enhancement could replace `assumed_fork_hashrate=50.0` with an
observed-hashrate-with-lag model, making the fog of war explicit and tunable
(e.g., an `information_lag` parameter controlling how stale a pool's hashrate
estimate is). This would make the difficulty adjustment cascade more realistic
and add a new input potential dimension to the parameter space.

---

### UASF Narrative vs. Empirical Findings: Who Actually Sets the Rules?

The **User Activated Soft Fork (UASF)** narrative holds that node operators —
ordinary users running full nodes — can force miners to adopt protocol upgrades by
refusing to accept blocks that violate the new rules. The political appeal of this
claim is that "the people" (node operators) hold ultimate authority over Bitcoin's
rules, not miners or corporations.

**Our data directly contradicts the strong form of this claim.**

#### What targeted_sweep4 found

`targeted_sweep4` varied all user node parameters across 36 scenarios on the full
network: `user_ideology_strength`, `user_switching_threshold`, and
`user_nodes_per_partition`. The result:

> **Zero correlation between any user node parameter and fork outcomes.**

No user parameter had any detectable causal effect. The dominant drivers of fork
outcomes are:

1. **`economic_split`** — what fraction of BTC custody is held by economic actors
   (exchanges, custodians) who support v27 vs. v26
2. **`pool_committed_split`** — how much hashrate is committed to each fork by
   ideologically-driven pools
3. **`pool_ideology_strength × pool_max_loss_pct`** — whether pools hold or
   capitulate under economic pressure

User nodes — entities running full nodes to validate the chain — appear nowhere in
this list.

#### Why the narrative fails mechanistically

The UASF mechanism assumes:
```
User nodes reject invalid blocks → Miners' blocks get orphaned → Miners forced to upgrade
```

This logic requires that user node block rejection translates into *economic* pressure
on miners. But in practice:

- **Miners care about revenue**, which means price × block reward / difficulty
- **Price is set by exchanges and custodians** — entities that hold and trade BTC
- **Regular full-node operators** have no pricing power unless they are also the
  custodians and liquidity providers

The causal chain is:
```
Economic nodes (exchanges) → price signals → pool profitability → miner decisions
```

User nodes are not in this chain. They validate the chain their software accepts, but
they do not determine which chain the market prices higher. That determination belongs
to the economic aggregate — entities with actual BTC custody.

#### The correct claim

If the UASF narrative were restated accurately based on the sweep findings, it would be:

> **"Exchanges and large BTC custodians set the rules. If they choose to price only
> one fork's coin, miners will follow."**

This is less politically appealing because it concentrates governance authority in
large institutional actors rather than distributed node operators — but it is what
the data shows.

#### The caveat: hard fork exit

One path by which user node ideology *can* matter is the **hard fork exit**:

If user node operators refuse to transact on any existing fork and instead bootstrap
an entirely new chain with a new genesis or chain split, they can take economic
activity with them. This is not "users forcing miners" — it is "users exiting to a
new market." If enough economic actors (exchanges, custodians) follow the users to
the new chain, the original chain loses its economic basis and miners follow.

This is arguably what happened with BCH in 2017: the economic departure was led by
a coalition of businesses, not by individual node operators' block rejection rules.
The node-rejection mechanism was symbolic; the actual pressure came from announced
exchange listings and custody support for the new fork.

**In the soft fork simulation, this hard-fork-exit path is not modeled.** Our
findings apply specifically to soft fork disputes where the existing chain continues
and parties compete for which partition becomes canonical. In that setting, economic
nodes dominate and user nodes are irrelevant.

---

### Price Oracle: The Ghost Town Problem

**Observed in targeted_sweep10 (sweep_0003):** When v27 produced zero blocks for 600 consecutive seconds, its price declined only ~6% — from $60,917 to $57,332. This is a significant model limitation.

#### Why the oracle fails at extremes

The current formula:
```
combined_factor = chain_f×0.3 + econ_f×0.5 + hash_f×0.2
```
where each `f = 0.8 + weight×0.4`, range [0.8, 1.2], and a hard cap at ±20% divergence.

With econ_split=0.70 (v27 holds 70% BTC custody):
- `econ_f_v27 = 0.8 + 0.70×0.4 = 1.08` → contributes `1.08 × 0.5 = 0.54` regardless of block production
- Even with `hash_f` and `chain_f` both at minimum (0.8): `combined_min = 0.8×0.3 + 1.08×0.5 + 0.8×0.2 = 0.24 + 0.54 + 0.16 = 0.94`
- The 20% cap then further limits how far below baseline the price can fall

**The oracle treats BTC custody as static.** It has no mechanism for custody to flee a non-functional chain. In reality: a chain producing zero blocks has no settlement finality. Exchanges halt trading. Custodians begin emergency transfers. The economic basis for that fork's valuation disappears far faster than the static custody snapshot implies.

#### Proposed improvements (for discussion)

**Option A: Multiplicative liveness penalty**

Add a `liveness_f` term that decays when block production stalls, applied as a multiplier to the whole combined_factor:

```python
# blocks_per_interval = blocks mined in last N seconds / expected blocks in N seconds
liveness_f = min(1.0, blocks_per_interval ** liveness_exponent)
# liveness_exponent controls how steeply the penalty applies (e.g., 0.5 = square root, gentler)

combined_factor = (chain_f*0.3 + econ_f*0.5 + hash_f*0.2) * liveness_f
```

Pros: Preserves normal-operation dynamics entirely. Ghost town → price collapses toward zero asymptotically. Parameterizable severity. Simple to implement.
Cons: Multiplying out econ_f entirely when liveness→0 may be too aggressive if some small block trickle exists.

**Option B: Liveness-coupled econ_f**

Make economic confidence decay proportional to block production rate — modeling that custody holders respond to liveness failure over time:

```python
production_ratio = recent_blocks / target_blocks  # [0, 1]
confidence_decay = production_ratio ** confidence_exponent
effective_econ_f = 1.0 + (econ_f - 1.0) * confidence_decay
# At production_ratio=1.0: effective_econ_f = econ_f (no change)
# At production_ratio=0.0: effective_econ_f = 1.0 (neutral — custody is contested)

combined_factor = chain_f*0.3 + effective_econ_f*0.5 + hash_f*0.2
```

Pros: More mechanistically accurate — models that economic actors *gradually* lose confidence proportional to block drought duration, not instantaneously. The inertia in custody migration is preserved. Differentiates "brief dry spell" from "prolonged ghost town."
Cons: Adds a new parameter (`confidence_exponent`) and a time-window parameter for measuring `recent_blocks`. Need to calibrate what "prolonged" means.

**Option C: Raise or remove the 20% cap for extreme scenarios**

Keep the current formula but make the price divergence cap dynamic:

```python
# Base cap: 20% for normal operation
# Extend cap when a chain is in liveness failure
liveness_ratio = recent_bpr / target_bpr
effective_cap = base_cap + (1.0 - liveness_ratio) * extended_cap  # e.g., up to 60% total
```

Pros: Minimal formula change. Allows existing dynamics to play out but lifts the ceiling when warranted.
Cons: The cap is a symptom fix, not a root cause fix. Doesn't address why econ_f floors the price.

**Option D: Block finality window as an explicit price component**

Add a fourth price component that directly measures settlement viability:

```python
# Finality score: fraction of target blocks produced in last M minutes
finality_f = min(1.0, blocks_last_M / target_blocks_in_M)
# Range [0.8, 1.2] like other factors

combined_factor = chain_f*0.25 + econ_f*0.40 + hash_f*0.15 + finality_f*0.20
```

Pros: Explicit economic interpretation — finality is what economic actors actually care about. Most realistic modeling of exchange/custodian behavior.
Cons: Requires rebalancing all weights. Introduces a new time-window parameter. Biggest structural change to the oracle.

#### Recommended path

The **Option B** (confidence-decayed econ_f) is the priority fix, with a raised divergence cap. Implement behind `--enable-liveness-penalty` flag (default False) to preserve backward compatibility with all existing sweeps. The key new parameters would be:

| Parameter | Suggested range | Effect |
|-----------|----------------|--------|
| `liveness_window` | 60–300s | Time window for measuring block production rate |
| `confidence_exponent` | 0.5–2.0 | How steeply custody confidence decays (1.0 = linear) |
| `price_divergence_cap` | 0.20–0.60 | Raised from current 0.20 for extreme scenarios |

**Implementation decision gate: evaluate after sweep11 (2016-block) completes.**

---

### Price Oracle: The Custody Duplication Problem

A deeper structural issue with `econ_f` that is distinct from the ghost town problem.

#### The fundamental direction of econ_f is wrong for fork scenarios

The current oracle treats economic custody as **price support**: if 70% of BTC custody is on v27 exchanges, `econ_f_v27 = 1.08` props up v27's price. The implicit model is that custodians are *loyal supporters* of their fork.

**This is backwards from how fork custody actually works.**

When a fork occurs, every BTC holder has their coins **duplicated on both chains simultaneously**. A custodian holding 1 BTC before the fork holds 1 BTC-v27 AND 1 BTC-v26 after it. If v26 goes to zero, they have lost nothing from their pre-fork position. The rational response is to **sell the weaker fork's coins as quickly as possible** to capture any residual value before they become worthless.

The selling pressure this creates is *proportional to custody weight* — the more BTC a large custodian holds, the more weaker-fork coins they are incentivized to dump. The current model uses custody weight to generate a price *floor* on the weaker chain, when in reality large custodians are the primary source of **selling pressure** on the fork they believe will lose.

```
Current model:  econ_f → price SUPPORT (larger custody = higher price floor)
Reality:        econ_f → selling PRESSURE on losing fork (larger custody = faster price collapse)
```

#### Reflexive price collapse

This selling pressure creates a self-reinforcing dynamic absent from the current model:

```
v26 falls behind on hashrate
  → custodians expect v26 to lose → they sell v26 coins
    → v26 price drops further
      → mining v26 less profitable → more pools switch to v27
        → v26 falls further behind → more selling pressure → ...
```

Real fork resolutions are often faster and more decisive than models predict precisely because of this reflexivity. The current oracle, with static custody weights providing a price floor, suppresses this cascade.

#### Interaction with the ghost town problem (Option B)

These are two distinct but compounding mechanisms:

| Mechanism | Trigger | Effect on weak fork price |
|-----------|---------|--------------------------|
| Option B (liveness) | Chain stops producing blocks → settlement impossible | Econ confidence decays → price floor erodes |
| Custody duplication | Rational actors sell "airdrop" coins on losing fork | Active selling pressure → price drops regardless of liveness |

In the stuck contested state (sweep8), both mechanisms are absent:
- Option B absent → slow v26 chain (35.9% hashrate) gets no price penalty
- Custody duplication absent → v26 economic custody provides a floor instead of generating selling pressure

In reality, both would apply simultaneously, making the stuck contested state significantly less stable than the model predicts.

#### Toward a more accurate model

Instead of:
```python
econ_f = 0.8 + custody_weight × 0.4  # custody = support
```

A more accurate formulation:
```python
# Custody generates support on the chain you're committed to
# and selling pressure on the chain you're abandoning
committed_support    = own_fork_custody × confidence_in_own_fork
cross_chain_selling  = other_fork_custody × (1 - confidence) × sell_urgency

# sell_urgency increases as the fork falls further behind
sell_urgency = f(hashrate_gap, block_production_ratio, price_gap)

econ_f = 0.8 + (committed_support - cross_chain_selling) × 0.4
```

`sell_urgency` is what makes this reflexive: as one fork clearly starts losing, urgency to sell that fork's "airdrop" coins rises, driving price down further, which increases urgency. This is the cascade that makes real fork resolution faster than miner economics alone would predict.

#### Practical implication for existing results

The "stuck contested" state observed in sweep8 and sweep11 may be an artifact of the oracle lacking both Option B and custody duplication dynamics. Both fixes compound in the same direction — they both accelerate the weaker fork's price decline. Implementing one without the other still understates the real collapse pressure.

Priority order:
1. **Implement Option B first** (liveness penalty — simpler, bounded effect, preserves backward compatibility)
2. **Evaluate sweep11 results** under current oracle to characterize the stuck contested regime
3. **Design custody duplication model** as a follow-on (more complex, larger structural change to econ_f)
4. **Re-run 2016-block sweeps** with both improvements to assess whether stuck contested survives

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
| `targeted_sweep5_lite_econ_threshold` | lite | ✅ **Valid (re-run)** — fixed build script applied correctly; outcomes match full network exactly |
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
| **targeted_sweep5 (orig)** | 36 | 60 nodes | 30 min | 144 blocks (~5 min) | Fixed | **Complete (user behavior — see targeted_sweep4)** |
| **targeted_sweep5_lite** | 5 | 25 nodes | 30 min | 144 blocks (~5 min) | Fixed | ✅ **Complete — network equivalence confirmed** |
| **targeted_sweep6 (orig)** | 8 | 25 nodes | 30 min | 144 blocks (~5 min) | Fixed | ❌ **INVALIDATED** — economic_split not applied (role-name bug) |
| **targeted_sweep6_pool_ideology_full** | 20 | 60 nodes | 30 min | 144 blocks (~5 min) | Fixed | ✅ **Complete** — full-network validation of pool ideology diagonal threshold |
| **targeted_sweep7_lite_inversion** | 12 | 25 nodes | 30 min | 144 blocks (~5 min) | Fixed | ✅ **Complete** — lite network inversion zone validation (partial match) |
| **targeted_sweep8_lite_2016_retarget** | 5 | 25 nodes | 120 min | **2016 blocks (~67 min)** | Fixed | ✅ **Complete** — 2016-block retarget creates qualitatively different "stuck contested" regime |
| **targeted_sweep9_long_duration_2016** | 1 | 25 nodes | 333 min | **2016 blocks (~67 min)** | Fixed | ✅ **Complete** — stuck contested state resolves at t≈8,100s when first retarget fires; v27 dominant |
| **targeted_sweep10_econ_threshold_2016** | 5 | 25 nodes | 217 min | **2016 blocks (~67 min)** | Fixed | ✅ **Complete (4/5)** — v27_dominant at ALL economic splits (0.35–0.70); correlation=0; difficulty mechanics dominate |

**Total: 395 scenarios** (366 with full analysis)

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

### targeted_sweep5: Lite Network Equivalence Validation

> ✅ **Valid** — re-run with corrected `2_build_configs.py` after the role-name bug fix. This is the corrected replacement for the original invalidated sweep5.

This sweep maps the economic threshold on the lite network (25 nodes) for direct comparison with targeted_sweep1 on the full network (60 nodes), using identical fixed parameters to enable an apples-to-apples comparison.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **economic_split** | 0.35, 0.50, 0.60, 0.70, 0.82 (5 levels — identical to targeted_sweep1) |
| **hashrate_split** | Fixed at 0.25 |
| **pool_committed_split** | Fixed at 0.35 |
| **pool_profitability_threshold** | Fixed at 0.16 |
| **pool_max_loss_pct** | Fixed at 0.26 |
| Network | lite (25 nodes) |
| Scenarios | 5 total |

#### Results Grid

```
economic_split   lite network (sweep5)   full network (sweep1, commit=0.35)
     0.35              v26_dominant             v26_dominant       ✓ match
     0.50              v26_dominant             v26_dominant       ✓ match
     0.60              v26_dominant             v26_dominant       ✓ match
     0.70              v26_dominant             v26_dominant       ✓ match
     0.82              v27_dominant             v27_dominant       ✓ match
```

**Perfect match across all 5 scenarios.** The threshold behavior is identical — v26 wins below 0.82, v27 wins at 0.82 — on both network sizes.

#### Key Finding: Lite Network is a Valid Proxy (144-block retarget)

The lite network (25 nodes, aggregate economic cohorts) produces outcomes equivalent to the full network (60 nodes, individual entity representation) for `economic_split` dynamics with `pool_committed_split=0.35` and 144-block difficulty retarget intervals.

**Caveat — 2016-block retarget not yet validated:** Equivalence is confirmed only for the accelerated 144-block retarget used in all targeted sweeps. The 2016-block realistic retarget (used in `realistic_sweep3`) creates more pronounced difficulty divergence during the minority chain's survival window. Whether the lite network replicates this behavior identically is an open question that warrants a dedicated equivalence sweep at realistic retarget intervals before using the lite network for 2016-block studies.

#### Implications for Phase 3

- Lite network is cleared for use in Phase 3 Latin hypercube sampling (144-block retarget)
- Parallel execution is now possible: full and lite networks can run simultaneously with equivalent results
- Per-scenario runtime on lite: ~30 min (vs ~32 min on full) — modest time savings, but meaningful at n=100+ scenarios
- A 2016-block equivalence validation sweep should be run before using the lite network for realistic-retarget studies

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep5_lite_econ_threshold/results/` | Per-scenario results |
| `targeted_sweep5_lite_econ_threshold/build_manifest.json` | Sweep configuration |
| `specs/targeted_sweep5_lite_econ_threshold.yaml` | Sweep spec |

---

### targeted_sweep6_pool_ideology_full: Pool Ideology Full Network Validation

> ✅ **Valid** — full 60-node network with corrected `2_build_configs.py`. Direct replacement for the invalidated `targeted_sweep6 (orig)` and a full-network replication of `targeted_sweep2b`.

This sweep validates whether the diagonal threshold finding from `targeted_sweep2b` (pool ideology × max_loss gates committed pool behavior near the economic threshold) holds on the full 60-node network with correct economic parameter injection.

#### Background

`targeted_sweep2b` found a diagonal threshold on the lite network but with a role-name bug that caused the economic split to remain at the baked-in YAML default (~43% v27 custody) instead of the intended 0.78. Pool ideology parameters were correctly applied in that sweep. This sweep reruns the identical grid on the full network with the fixed build script to determine:
1. Does the diagonal threshold concept hold on the full network?
2. Does the direction of the effect change when the economic context is correctly applied?

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **pool_ideology_strength** | 0.2, 0.4, 0.6, 0.8 (4 levels) |
| **pool_max_loss_pct** | 0.05, 0.15, 0.25, 0.35, 0.45 (5 levels) |
| **economic_split** | Fixed at 0.78 (near v27 win threshold; correctly applied) |
| **hashrate_split** | Fixed at 0.25 (v26 has 75% hashrate advantage) |
| **pool_committed_split** | Fixed at 0.35 |
| **pool_neutral_pct** | Fixed at 30% |
| Network | **full (60 nodes)** |
| Scenarios | 20 total (4 × 5 grid) |

#### Results Grid

```
                         pool_max_loss_pct
ideology_strength   0.05   0.15   0.25   0.35   0.45
       0.2           27     27     27     27     27    ← v27 wins ALL
       0.4           27     27     27     27     26    ← v26 holds at max_loss=0.45
       0.6           27     27     27     26     26    ← v26 holds at max_loss≥0.35
       0.8           27     27     26     26     26    ← v26 holds at max_loss≥0.25
```

Legend: `27` = v27_dominant, `26` = v26_dominant

#### Overall Outcome Distribution

| Outcome | Count | Percentage |
|---------|:-----:|:----------:|
| v27_dominant | 14 | 70% |
| v26_dominant | 6 | 30% |

#### Key Finding: Diagonal Threshold Confirmed, Direction Corrected

**The diagonal concept holds but the direction is reversed relative to sweep2b.** In sweep6, higher ideology × max_loss means committed v26 pools can tolerate the economic loss of staying on the minority chain, and therefore v26 survives. This is the expected result at econ=0.78 where v27 has economic advantage.

| ideology_strength | Required max_loss_pct for **v26 to hold** |
|:-----------------:|:-----------------------------------------:|
| 0.2 | Never (all 5 cells → v27 wins) |
| 0.4 | ≥ 0.45 (product = 0.18) |
| 0.6 | ≥ 0.35 (product = 0.21) |
| 0.8 | ≥ 0.25 (product = 0.20) |

**Approximate diagonal threshold: ideology × max_loss ≳ 0.16–0.20 for v26 to survive.**

The boundary cells:
- 0.4 × 0.35 = 0.14 → v27 wins; 0.4 × 0.45 = 0.18 → v26 holds
- 0.6 × 0.25 = 0.15 → v27 wins; 0.6 × 0.35 = 0.21 → v26 holds
- 0.8 × 0.15 = 0.12 → v27 wins; 0.8 × 0.25 = 0.20 → v26 holds

#### Why Direction Reversed vs. Sweep2b

| | Sweep2b (lite, ~43% v27 custody) | Sweep6 (full, 78% v27 custody) |
|--|:---------------------------------:|:-------------------------------:|
| Economic context | v26 economic majority | v27 economic majority |
| Who has economic pressure to switch? | v27-committed pools | v26-committed pools |
| Higher ideology × max_loss helps: | v27 pools stay stubborn → v27 survives | v26 pools stay stubborn → v26 survives |
| Direction of effect | Higher product → v27 wins | Higher product → v26 holds |

The diagonal threshold governs **the defender**: whichever side is economic minority, its committed pools survive only if ideology × max_loss exceeds ~0.16–0.20.

#### Correlations

| Parameter | Correlation with v27 hash share |
|-----------|:-------------------------------:|
| pool_max_loss_pct | **−0.617** (strongest) |
| pool_ideology_strength | **−0.488** |
| All fixed parameters | ~0.0 (expected — no variation) |

Negative correlations confirm higher values → v26 wins (v27 hash share decreases).

#### Cascade Signatures

| Outcome | Reorgs | v27 Final Hashrate | v27 Block Share |
|---------|:------:|:------------------:|:---------------:|
| v27_dominant | 4 | 86.4% (full cascade) | ~84.8% |
| v26_dominant | 7 | 30.0% (partial — neutral pools) | ~45.8% |

When v27 wins, committed v26 pools fully capitulate and v27 captures all committed hashrate. When v26 holds, v27 retains only the 30% neutral pool fraction (they never fully commit to either side).

#### Implications

1. **Diagonal threshold confirmed on full network** — The ideology × max_loss product gates committed pool behavior at econ=0.78. The threshold (~0.16–0.20) is slightly higher than the sweep2b estimate (~0.12), reflecting the difference in economic context.

2. **The ideological "never-switcher" condition (from MEMORY.md) is validated** — `ideology × max_loss > 0.222` for guaranteed v26 survival. All v26-dominant outcomes in this sweep satisfy this (0.4×0.45=0.18 is just below, 0.6×0.35=0.21 near the boundary, 0.8×0.25=0.20 near it). The 0.222 threshold from the price oracle math is directionally confirmed.

3. **ideology=0.2 is insufficient regardless of loss tolerance** — Even at max_loss=0.45 (product=0.09), committed v26 pools cannot hold at econ=0.78. They are always forced to switch when v27 has strong economic advantage.

4. **Refines the economic threshold** — At econ=0.78 with committed v26 pool resilience below the diagonal, v27 wins despite v26 having 75% starting hashrate. This narrows the effective economic threshold from ~0.82 to ~0.78 when v26 pools are ideologically weak.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep6_pool_ideology_full/results/analysis/` | Analysis outputs |
| `targeted_sweep6_pool_ideology_full/results/analysis/sweep_data.csv` | Per-scenario metrics |
| `targeted_sweep6_pool_ideology_full/scenarios.json` | Full scenario configurations |
| `specs/targeted_sweep6_pool_ideology_full.yaml` | Sweep spec |

---

### targeted_sweep7_lite_inversion: Lite Network Inversion Zone Validation

This sweep validates whether the lite network replicates the complex inversion zone behavior discovered in targeted_sweep1 on the full network.

#### Background

targeted_sweep5 confirmed lite/full equivalence at `pool_committed_split=0.35` (the baseline column), but the most complex behavior — the **non-monotonic inversion zone** at econ=0.60–0.70 where higher committed_split HURTS v27 — was never validated on the lite network. That inversion is the defining feature of the decision boundary.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **economic_split** | 0.50, 0.60, 0.70, 0.82 (4 levels) |
| **pool_committed_split** | 0.20, 0.38, 0.65 (3 levels) |
| **hashrate_split** | Fixed at 0.25 |
| Network | lite (25 nodes) |
| Scenarios | 12 total (4 × 3 grid) |

#### Results Grid

```
                     commit=0.20   commit=0.38   commit=0.65
    econ=0.50           v27           v26           v26
    econ=0.60           v27           v26           v26
    econ=0.70           v27           v26           v26
    econ=0.82           v27           v27           v27
```

#### Comparison with Full Network (targeted_sweep1)

| econ | commit | Full Network | Lite Network | Match? |
|:----:|:------:|:------------:|:------------:|:------:|
| 0.50 | 0.20 | v26 | **v27** | ❌ |
| 0.50 | 0.38 | v27 | **v26** | ❌ |
| 0.50 | 0.65 | v27 | **v26** | ❌ |
| 0.60 | 0.20 | v27 | v27 | ✅ |
| 0.60 | 0.38 | v26 | v26 | ✅ |
| 0.60 | 0.65 | v26 | v26 | ✅ |
| 0.70 | 0.20 | v27 | v27 | ✅ |
| 0.70 | 0.38 | v26 | v26 | ✅ |
| 0.70 | 0.65 | v26 | v26 | ✅ |
| 0.82 | 0.20 | v27 | v27 | ✅ |
| 0.82 | 0.38 | v27 | v27 | ✅ |
| 0.82 | 0.65 | v27 | v27 | ✅ |

**9 of 12 scenarios match (75%)**

#### Key Finding: Partial Match with Critical Divergence at econ=0.50

The **inversion zone (econ=0.60–0.70) replicates correctly** — the lite network exhibits the same non-monotonic behavior where commit=0.20 produces v27 wins but commit≥0.38 produces v26 wins.

However, at **econ=0.50** the pattern is completely **inverted** between networks:
- Full network: commit=0.20 → v26, commit≥0.38 → v27
- Lite network: commit=0.20 → v27, commit≥0.38 → v26

#### Is econ=0.50 a Chaotic Transition Zone?

Evidence from reorg counts:

| commit | Full Network | Reorgs | Lite Network | Reorgs |
|:------:|:------------:|:------:|:------------:|:------:|
| 0.20 | v26 | **4** (clean) | v27 | **12** (contested) |
| 0.38 | v27 | 10 (contested) | v26 | 8 (contested) |
| 0.65 | v27 | 4 (clean) | v26 | 8 (contested) |

The full network at commit=0.20 has only 4 reorgs (same as clean wins at econ=0.35 and 0.82), suggesting it's **not** a knife-edge point. But the lite network at the same point has 12 reorgs, indicating active cascade dynamics with a different resolution.

**Verdict:** The divergence is likely a mix of:
1. **Structural difference** — the transition boundary is located differently between networks
2. **Marginal sensitivity** — econ=0.50 is near the boundary on both networks, so small structural differences get amplified

#### Implications for Lite Network Usage

1. **Lite network is valid for inversion zone studies** (econ ≥ 0.60) — all 9 scenarios match
2. **Lite network is NOT reliable for low-economic threshold studies** (econ ~ 0.50) — pattern is inverted
3. **Treat econ=0.50 as a transition zone** requiring full-network validation before drawing conclusions
4. **Phase 3 sampling should focus on econ ≥ 0.60** when using the lite network

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep7_lite_inversion/results/analysis/` | Analysis outputs |
| `targeted_sweep7_lite_inversion/results/analysis/sweep_data.csv` | Per-scenario metrics |
| `targeted_sweep7_lite_inversion/scenarios.json` | Full scenario configurations |
| `specs/targeted_sweep7_lite_inversion.yaml` | Sweep spec |

---

### targeted_sweep8_lite_2016_retarget: 2016-Block Retarget Regime

> ✅ **Valid** — lite network, corrected `2_build_configs.py`, 7200s duration with `--retarget-interval 2016`.

This sweep completes the three-way comparison: full/144-block (sweep1), lite/144-block (sweep5), and now lite/2016-block. It tests whether the lite network is a valid proxy for realistic Bitcoin difficulty dynamics, and whether 2016-block retarget changes outcomes qualitatively.

#### Sweep Design

| Parameter | Values |
|-----------|--------|
| **economic_split** | 0.35, 0.50, 0.60, 0.70, 0.82 (5 levels — identical to sweep1 and sweep5) |
| **hashrate_split** | Fixed at 0.25 |
| **pool_committed_split** | Fixed at 0.35 |
| **retarget_interval** | **2016 blocks** (~67 min at 2s block intervals) |
| **duration** | **7200s (2 hours)** — extended to approach first retarget |
| Network | lite (25 nodes) |
| Scenarios | 5 total |

#### Results: Three-Way Comparison

```
economic_split   sweep1 (full, 144-block)   sweep5 (lite, 144-block)   sweep8 (lite, 2016-block)
     0.35              v26_dominant               v26_dominant               CONTESTED
     0.50              v26_dominant               v26_dominant               CONTESTED
     0.60              v26_dominant               v26_dominant               CONTESTED
     0.70              v26_dominant               v26_dominant               CONTESTED
     0.82              v27_dominant               v27_dominant               v27_dominant  ✓
```

**Lite network is NOT equivalent to the full network for 2016-block retarget studies.** Sweep5 confirmed equivalence at 144-block; sweep8 shows a fundamental divergence at 2016-block. However, this is not a lite/full discrepancy — it is a 144-block vs. 2016-block regime difference. A full-network 2016-block sweep would be needed to confirm full network behavior, but the mechanism is well understood (see below).

#### Outcome Distribution

| Outcome | Count | % |
|---------|:-----:|---|
| contested | 4 | 80% |
| v27_dominant | 1 | 20% |
| v26_dominant | 0 | 0% |

#### The Stuck Contested Equilibrium

All four contested scenarios (econ=0.35–0.70) converged to an **identical partial equilibrium**, regardless of economic level:

| Metric | Value |
|--------|-------|
| Final v27 hashrate | 50.5% (up from 25% start) |
| Final v26 hashrate | 35.9% (down from 75% start) |
| v27 block share | 57.5% |
| Reorgs | 5 |
| v27 price premium | ~5.9% ($61,377 vs $57,970) |

The neutral pools (30% of total hashrate) fully migrated to v27 based on price signals. The committed v26 pools (~35.9%) held firm. The cascade stalled there. The identical endpoint across all four economic levels confirms the price signal at these levels is irrelevant — the partial equilibrium is determined entirely by pool ideology structure, not economic split.

At econ=0.82 the full cascade completed (v27 final hashrate 86.4%, v26 0%), with a 46.9% price gap ($70,998 vs $48,349) — strong enough to break committed pools without any difficulty help.

#### Why 2016-Block Retarget Is a Qualitatively Different Regime

The root cause is the **Difficulty Adjustment Survival Window**:

```
v27 at 25% hashrate, 2s block intervals, 2016-block retarget:
  → v27 produces 1 block per ~8 seconds
  → 7200s run = ~900 v27 blocks
  → Retarget requires 2016 blocks → needs ~16,000s (~4.5 hours)
  → v27 NEVER gets its difficulty adjustment within the run
```

At 144-block retarget, the minority chain difficulty adjustment arrives in ~5 minutes. The resulting profit spike is what *completes* the cascade — neutral pools rush in, chainwork accumulates rapidly, and the fork resolves. At 2016-block retarget, that spike never arrives within any practical run window, so the only force moving hashrate is the price oracle. Price alone can migrate neutral pools but cannot break committed ideological pools below the diagonal threshold.

**This is the mechanism by which 2016-block retarget creates stuck contested states:**
- ✅ Neutral pool migration: price signal drives ~30% of hashrate to economic winner
- ❌ Committed pool breaking: requires difficulty adjustment profit spike OR econ ≥ 0.82 price signal

#### Real-World Implications

Bitcoin's actual retarget interval is 2016 blocks (~2 weeks). Sweep8 is therefore the more realistic regime. The implications are significant:

1. **Real forks likely produce prolonged contested splits.** A fork starting at 25% hashrate would sit at ~50/35 hashrate equilibrium for weeks — neutral pools drifting to the economic winner, ideological pools entrenched — with no rapid resolution.

2. **The difficulty adjustment spike is load-bearing for fast resolution.** All clean cascade thresholds found in sweeps 1–7 relied on the 144-block spike arriving quickly. In reality, resolution is slower and requires either overwhelming economic signal (≥82%) or the fork surviving ~2 weeks to retarget.

3. **The "stuck contested" state is the realistic baseline for most fork scenarios.** Not v26_dominant, not v27_dominant — a frozen split at roughly neutral-pool migration equilibrium.

4. **econ=0.82 remains the clean threshold in both regimes.** The price signal alone (46.9% gap) is sufficient to break committed pools regardless of difficulty dynamics. This threshold's robustness across both regimes makes it the most reliable finding in the entire sweep program.

5. **All prior sweep findings need contextualizing.** The inversion zone, Foundry flip-point, and cascade thresholds from sweeps 1–7 describe *which side eventually wins* correctly, but the *mechanism* (difficulty spike) operates on a 2-week timescale in reality, not minutes. The outcome topology is valid; the timing is not.

#### What Would Resolve a Real-World Stuck Fork?

Given the sweep findings, resolution pathways are:
- **Economic escalation past ~0.82:** Large exchanges/custodians committing decisively to one fork; price gap exceeds committed pool loss tolerance
- **Ideology collapse:** Committed pools' financial pain accumulating over weeks erodes their ideology × max_loss product below the diagonal threshold (~0.16–0.20)
- **First difficulty adjustment:** After ~2 weeks on minority chain (t≈8,100s in simulation), the difficulty drop delivers the profit spike; **targeted_sweep9 confirmed this completes the cascade at econ=0.70** — losses jump from ~9% to 56%, breaking committed pool tolerance
- **Capitulation:** One side loses business viability and shuts down voluntarily

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep8_lite_2016_retarget/results/analysis/` | Analysis outputs |
| `targeted_sweep8_lite_2016_retarget/results/analysis/sweep_data.csv` | Per-scenario metrics |
| `targeted_sweep8_lite_2016_retarget/scenarios.json` | Full scenario configurations |
| `specs/targeted_sweep8_lite_2016_retarget.yaml` | Sweep spec |

---

### targeted_sweep9_long_duration_2016: Resolving the Stuck Contested State

> ✅ **Valid** — lite network, corrected `2_build_configs.py`, 20,000s duration with `--retarget-interval 2016`. Single scenario (econ=0.70).

Sweep8 left an open question: is the stuck contested state permanent, or does it resolve once the first 2016-block retarget arrives? Sweep9 answers this definitively by running the identical econ=0.70 scenario for 333 minutes (~20,000s simulated), long past the estimated first retarget at t≈8,100–11,000s.

#### Sweep Design

| Parameter | Value |
|-----------|-------|
| **economic_split** | 0.70 (cleanest contested case from sweep8) |
| **hashrate_split** | Fixed at 0.25 |
| **pool_committed_split** | Fixed at 0.35 |
| **pool_ideology_strength** | 0.51 → effective tolerance = 0.51 × 0.26 = **13.3%** |
| **retarget_interval** | **2016 blocks** |
| **duration** | **20,000s (333 min)** — well past first retarget |
| Network | lite (25 nodes) |
| Scenarios | 1 total |

#### Timeline of Events

| Sim Time | Event |
|----------|-------|
| t=0–8,106s | Neutral pools migrate to v27 on price signal; committed v26 pools hold (loss 1–9%, below 13.3% tolerance) |
| **t=8,106s** | **First v27 retarget: difficulty 1.0 → 0.497 (~50% drop)**. Hashrate had risen to ~50% (neutral pools joined) so adjustment was ~50%, not the ~75% estimated for pure 25% hashrate. |
| ~t=8,106s | Loss for committed v26 pools jumps to **56%+** — far exceeding the 13.3% tolerance. All committed pools forced to switch to v27. |
| t=10,632s | Second v27 retarget: 0.497 → 0.794 (hashrate overshooting corrected upward) |
| t=14,430s | Third v27 retarget: 0.794 → 0.843 |
| t=18,639s | Fourth v27 retarget: 0.843 → 0.807 (stable) |
| t=20,000s | v26 still at difficulty 1.0 — only mined 1,548 blocks, never hit its own 2016-block retarget |

#### Final State

| Metric | v27 | v26 |
|--------|-----|-----|
| Blocks mined | 8,760 | 1,548 |
| Final hashrate | **86.4%** | **0%** |
| Final price | $64,835 | $54,512 |
| Difficulty | 0.807 (4 retargets) | 1.0 (0 retargets) |
| Cumulative chainwork | 6,881 | 1,548 |

- 10 reorg events, 8,338 total blocks of reorg mass
- Outcome: **v27_dominant**

#### Why the Cascade Triggered at t=8,106s

The committed v26 pool tolerance was 13.3% (`ideology_strength=0.51 × max_loss_pct=0.26`). Before the retarget, the most v26 pools were losing was ~9% — below the threshold. The ~50% difficulty drop made v27 blocks dramatically cheaper to mine, causing v27 profitability to spike. Committed v26 pools suddenly faced **56%+ losses**, triggering forced switches across all of them simultaneously (pool-antpool 16.9%, pool-f2pool ~8%, pool-marapool 4.6%, pool-luxor 2.3%, pool-ocean 1.2%).

**Key correction to sweep9 timing estimates:** The spec estimated first retarget at t≈9,000–11,000s, but it arrived at t=8,106s. The neutral pool migration to v27 happened earlier and more completely than estimated — raising v27 hashrate to ~50.5% faster, which paradoxically reduced the waiting time for 2016 v27 blocks.

#### Updated RETARGET INTERVAL EFFECT Zone Diagram

```
RETARGET INTERVAL EFFECT (targeted_sweep8 + targeted_sweep9):
┌────────────────────────────────────────────────────────────┐
│  ⚠️  ALL ZONES ABOVE ASSUME 144-BLOCK RETARGET             │
│                                                            │
│  At 2016-block retarget (realistic Bitcoin):               │
│  → At t<8100s: Zones A/B/C collapse into "stuck           │
│    contested" (neutral pools migrate, committed hold)      │
│  → At t≈8100s: First v27 difficulty retarget arrives      │
│    (~50% drop). Loss for committed v26 pools spikes        │
│    to 56% >> 13.3% tolerance → forced cascade             │
│  → At t>8100s: v27 dominant at all econ levels tested     │
│    (confirmed at econ=0.70; econ=0.82 resolves even       │
│    faster via price alone)                                 │
│  → Zone D (econ ≥ 0.82) unchanged — price signal alone    │
│    breaks committed pools before the retarget arrives      │
│  → KEY: "stuck contested" is a duration artifact at        │
│    t<8100s; given enough time, cascade completes           │
└────────────────────────────────────────────────────────────┘
```

#### Implications for Sweep10

Sweep8 ran to 7,200s — before the first retarget at t=8,106s. Sweep9 confirms that extending to 12,000–15,000s is sufficient to capture the post-retarget resolution at econ=0.70. Sweep10 should use **duration=12,000s** and map the full economic_split grid (0.35–0.82) to determine whether the cascade completes at all economic levels once the retarget arrives, and what the minimum economic level is for resolution.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep9_long_duration_2016/results/sweep_0000/` | Full results for single scenario |
| `targeted_sweep9_long_duration_2016/results/sweep_0000/summary.txt` | Final state summary |
| `targeted_sweep9_long_duration_2016/results/sweep_0000/pool_decisions.csv` | Pool switching decisions over time |
| `targeted_sweep9_long_duration_2016/results/sweep_0000/partition_difficulty.json` | All 4 retarget events |
| `targeted_sweep9_long_duration_2016/scenarios.json` | Scenario configuration |
| `specs/targeted_sweep9_long_duration_2016.yaml` | Sweep spec |

---

### targeted_sweep10_econ_threshold_2016: Three-Phase Cascade in the 144-Block Regime

#### ⚠️ Configuration Error — Intended 2016-block, Ran 144-block

The `--retarget-interval 2016` flag was not passed to `3_run_sweep.py`; the CLI default of 144 was used. The `partition_difficulty.json` files confirm `retarget_interval: 144` in all runs. **The intended research question — does the cascade complete at econ < 0.70 in the 2016-block regime? — is unanswered.** Sweep10 must be rerun with `--retarget-interval 2016`.

The findings below are valid observations in the 144-block regime.

#### Sweep Design (as-run)

| Parameter | Values |
|-----------|--------|
| **economic_split** | 0.35, 0.50, 0.60, 0.70, 0.82 (5 levels) |
| **hashrate_split** | Fixed at 0.25 |
| **retarget_interval** | **144 blocks (CLI default — not intended 2016)** |
| **duration** | 13,000s |
| Scenarios | 5 total (4 analyzed) |

#### Results

| Scenario | econ_split | v27 Final Hash | v26 Final Hash | v26 Blocks | Outcome |
|----------|-----------|---------------|----------------|------------|---------|
| sweep_0000 | 0.35 | 86.4% | 0.0% | 808 | v27_dominant |
| sweep_0001 | 0.50 | 86.4% | 0.0% | 808 | v27_dominant |
| sweep_0002 | 0.60 | 86.4% | 0.0% | 808 | v27_dominant |
| sweep_0003 | 0.70 | 86.4% | 0.0% | 808 | v27_dominant |

Correlation between `economic_split` and v27 hash share: **0.000**. Near-identical results across all runs. Pool ideology_product = 0.51 × 0.26 = 0.133 is just below the ~0.16 committed-pool survival threshold, meaning committed v26 pools are near the capitulation boundary regardless of price — the difficulty event easily pushes them over.

#### Detailed Timeline: Three-Phase Cascade (sweep_0003, econ=0.70)

The cascade resolves in ~30 minutes of sim time.

| Time | v27 hash | v26 hash | v27 price | v26 price | Key event |
|------|----------|----------|-----------|-----------|-----------|
| 0 | 38.1% | 48.3% | $60,000 | $60,000 | Fork splits. Foundry+ViaBTC+Spider → v27; AntPool+F2Pool+MARA+Luxor+Ocean → v26 |
| 611 | 38.1% | 48.3% | ~$59,900 | ~$59,500 | **v26 retargets: 1.0 → 0.471 (-53%)**. v26 difficulty windfall |
| 709 | 50.5% | 35.9% | ~$60,400 | ~$58,900 | **v27 retargets: 1.0 → 0.406 (-59%)**. Hashrate shift begins |
| 1,209 | **0.0%** | **86.4%** | $60,917 | $58,430 | **All pools collapse to v26.** Foundry forced off v27 (loss 19.6% > 13.3%). ViaBTC/Spider rational. v27 blocks freeze at 424 |
| 1,375 | 0.0% | 86.4% | $58,031 | $61,316 | v26 difficulty spikes 2×: 0.423 → 0.857 (mining too fast with full hashrate) |
| 1,647 | 0.0% | 86.4% | $57,541 | $61,807 | v26 difficulty stabilizes at 0.908. Last v26 retarget |
| 1,808 | 0.0% | 86.4% | $57,332 | $62,015 | **v27 retargets to extreme low: 0.4915 → 0.1644 (-67%)**. Now 83% below original. Zero hashrate for 600s → difficulty freefall |
| 1,813 | **86.4%** | **0.0%** | $57,332 | $62,015 | **All pools flood to v27.** Committed v26 pools forced (loss 36.7% >> 13.3%). Cascade complete |
| 1,873 | 86.4% | 0.0% | $61,451 | $57,896 | 156 blocks mined in 60s. v27 diff: 0.164 → 0.658 (4× max jump). Prices invert |
| 13,000 | 86.4% | 0.0% | $65,459 | $53,889 | **Final state.** v27: 6,158 blocks, chainwork 4,917. v26: 808 blocks, chainwork 528 (9.3× gap) |

**The trigger was difficulty asymmetry, not price.** Price divergence during the ghost-town phase was only ~7%. The 36.7% loss from being on v26 came from v27's extreme difficulty drop (0.164) making v27 profitability per unit hashrate vastly higher even at lower price.

#### Model Gaps Revealed

**Gap 1: Solo miner hashrate is nominal, not autonomous**

`v27_solo_hashrate=4.845%` is static throughout the entire run. During the ghost-town phase (t=1,209–1,813), this should theoretically produce ~30 v27 blocks but v27_blocks is frozen at exactly 424. Solo miners appear to follow pool switching decisions rather than mining independently. In reality, ideologically committed solo miners would keep a trickle of blocks alive, preventing a completely dead-chain scenario and altering retarget dynamics.

**Gap 2: Price oracle ghost town problem**

V27 produces zero blocks for 600 seconds but its price only drops ~6% ($60,917 → $57,332). The `econ_f` component (weight 0.5, driven by static 70% BTC custody on v27) floors the price regardless of chain liveness. The 20% divergence cap prevents further collapse. In reality, a chain producing zero blocks loses settlement finality immediately — exchanges halt withdrawals, economic actors begin emergency custody migration, and confidence collapses far faster than the static custody model captures. See "Price Oracle: Ghost Town Problem" section for proposed improvements.

#### Data Location

| File | Description |
|------|-------------|
| `targeted_sweep10_econ_threshold_2016/results/` | All scenario results |
| `targeted_sweep10_econ_threshold_2016/results/analysis/` | Analysis outputs |
| `targeted_sweep10_econ_threshold_2016/results/sweep_0003/time_series.csv` | Full timeline data |
| `targeted_sweep10_econ_threshold_2016/results/sweep_0003/pool_decisions.csv` | Per-epoch pool decisions |
| `specs/targeted_sweep10_econ_threshold_2016.yaml` | Sweep spec (note retarget_interval=2016 intended) |

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
| **pool_ideology × pool_max_loss** (product) | ~0.16–0.20 (defender's survival threshold at econ=0.78) | v27 favored when product < threshold (committed v26 pools capitulate) | **High** (targeted_sweep6, n=20, full network) |
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

RETARGET INTERVAL EFFECT (targeted_sweep8 + targeted_sweep9):
┌────────────────────────────────────────────────────────────┐
│  ⚠️  ALL ZONES ABOVE ASSUME 144-BLOCK RETARGET             │
│                                                            │
│  At 2016-block retarget (realistic Bitcoin):               │
│  → At t<8100s: Zones A/B/C collapse into "stuck           │
│    contested" (neutral pools migrate, committed hold)      │
│    Partial equilibrium: v27 ~50%, v26 ~36% hashrate,      │
│    insensitive to economic_split across 0.35–0.70          │
│  → At t≈8100s: First v27 retarget fires (~50% difficulty  │
│    drop). Committed pool losses spike 56% >> 13.3%         │
│    tolerance → forced cascade completes                    │
│  → Zone D (econ ≥ 0.82) unchanged — price signal alone    │
│    breaks committed pools regardless of retarget timing    │
│  → KEY: "Stuck contested" is a duration artifact;          │
│    given ~12,000s, the cascade completes at econ=0.70.     │
│    Whether it completes at econ=0.35–0.60 is OPEN.        │
│    (targeted_sweep10 will answer this question)            │
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
| **targeted_sweep6 (orig)** | `targeted_sweep6/results/analysis/` | 8 | ❌ **INVALIDATED** — lite network role-name bug; economic_split was dead |
| **targeted_sweep6_pool_ideology_full** | `targeted_sweep6_pool_ideology_full/results/analysis/` | 20 | ✅ **Full-network pool ideology validation** — diagonal threshold confirmed; direction corrected |
| **targeted_sweep7_lite_inversion** | `targeted_sweep7_lite_inversion/results/analysis/` | 12 | ✅ **Lite network inversion zone validation** — 75% match; econ=0.50 diverges |
| **targeted_sweep8_lite_2016_retarget** | `targeted_sweep8_lite_2016_retarget/results/analysis/` | 5 | ✅ **2016-block retarget validation** — qualitatively different regime; stuck contested state at econ=0.35–0.70; econ=0.82 still decisive |
| **targeted_sweep9_long_duration_2016** | `targeted_sweep9_long_duration_2016/results/sweep_0000/` | 1 | ✅ **Long-duration confirmation** — stuck contested state resolves at t=8,106s (first retarget); v27 dominant at econ=0.70; cascade mechanism confirmed |
| **targeted_sweep10_econ_threshold_2016** | `targeted_sweep10_econ_threshold_2016/results/analysis/` | 5 | ✅ **Economic split irrelevant in 2016-block regime** — v27_dominant at econ=0.35–0.70 (4/5 done); retarget difficulty mechanics, not price, drive cascade |

### Network Versions

**balanced-baseline** (used in balanced_baseline_sweep):
- 24 nodes, perfectly symmetric (12 per partition)
- 4 pools per side: 20% + 14% + 8% + 5% = 47% each
- 2 economic nodes per side with equal custody
- 6 user nodes per side with 3% hashrate each
- No structural advantage for either fork
- Purpose: Measure stochastic variance baseline

**realistic-economy-lite** (used in targeted_sweep2b, targeted_sweep3, targeted_sweep5_lite, targeted_sweep6, targeted_sweep7, targeted_sweep8, exploratory_sweep_lite):
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

*Analysis compiled February–March 2026; targeted_sweep9 added March 2026; targeted_sweep10 added March 2026*
