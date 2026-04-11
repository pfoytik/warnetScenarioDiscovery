# Model Assumptions

This document catalogues every explicit assumption in the warnetScenarioDiscovery simulation.
Each assumption is stated with its current value, what it represents, the direction of its
likely bias (conservative/aggressive/neutral), and how it could be challenged or replaced.

The modeling philosophy is: **assumptions are not hidden tuning — they are documented priors**.
Any finding can be challenged by updating the relevant assumption, rerunning, and comparing.
No claim of ground truth is made; claims are of the form "under these stated assumptions,
the outcome is X."

---

## 1. Fork Model Assumptions

### 1.1 Only contentious soft-forks produce a persistent chain split
**Value:** Structural assumption (no parameter)
**Meaning:** A non-contentious soft-fork (near-universal miner/economic adoption) results
in clean convergence with no competing chain. This simulation only models the contentious
case where a significant fraction of miners and economic actors refuse to adopt the new rules.
**Bias:** Neutral — this is definitionally correct, not a simplification.
**Challenge:** Not applicable; this is a scope boundary, not a calibration choice.

### 1.2 Both chains inherit an identical UTXO set at the fork point
**Value:** Structural assumption
**Meaning:** At the moment of the fork, every pre-fork UTXO exists on both v26 and v27.
Every holder automatically has coins on both chains. Custody is therefore duplicated by
default and does not represent an active fork preference signal at t=0.
**Bias:** Understates v26 price pressure early in the fork (holders who intend to support
v27 have not yet acted on that preference through transactions or liquidation).
**Challenge:** Model the gradual unwinding of duplicate custody as economic actors make
their fork preference concrete through transactions.

### 1.3 Fork point is treated as height zero; pre-fork history is not simulated
**Value:** Structural assumption
**Meaning:** The simulation begins at the fork event. Pre-fork conditions (accumulated
chainwork, existing mempool, in-progress difficulty epoch) are treated as initial
conditions, not simulated history.
**Bias:** Neutral for outcome questions; could matter for reorg depth calculations
in Phase 2.
**Challenge:** Initialize from a real Bitcoin block height and carry forward actual
difficulty epoch progress.

### 1.4 v26 nodes are permissive; v27 nodes are strict
**Value:** `accepts_foreign_blocks: true` (v26), `accepts_foreign_blocks: false` (v27)
**Meaning:** v26 nodes accept v27 blocks submitted via `submitblock` (backward-compatible
soft-fork behavior). v27 nodes reject v26 blocks that do not meet the new rules.
**Bias:** Neutral — this is the definitional behavior of a soft-fork.
**Challenge:** Model asymmetric cases where some v26 nodes explicitly reject v27 blocks
(a harder fork posture than standard soft-fork behavior).

---

## 2. Price Oracle Assumptions

### 2.1 Both chains start at the same base price
**Value:** `base_price = $60,000` (configurable), price ratio = 1.0 at t=0
**Meaning:** Pre-fork, there is one Bitcoin price. At fork time, both chains inherit it.
Price divergence only begins after the fork is sustained (≥6 blocks deep, see 2.3).
**Bias:** Neutral — the absolute price level does not affect fork outcomes (only relative
price matters); the initial parity is correct for a contentious fork where the market
has not yet priced in the split.
**Challenge:** Introduce a pre-fork anticipation signal where futures markets begin
pricing in the split before it occurs.

### 2.2 Price oracle coefficients: chain=0.30, economic=0.50, hashrate=0.20
**Value:** `chain_weight_coef=0.3`, `economic_weight_coef=0.5`, `hashrate_weight_coef=0.2`
**Meaning:** The combined price factor is a weighted blend of three signals:
- **Chain weight (30%):** Block production rate relative to target. A slow chain loses
  chain factor support.
- **Economic weight (50%):** Fraction of economic/transaction activity on the chain
  (see assumption 2.6). The dominant signal.
- **Hashrate weight (20%):** Security premium for the chain with more hashing power.
**Bias:** The 50% economic weight dominates outcomes. Empirical calibration against
real fork price data could shift these coefficients.
**Challenge:** Calibrate against observed price data from BCH/BSV/BTC fork events.
Weights could also be time-varying (hashrate matters more early; economics matters
more long-term).

### 2.3 Price divergence only begins after the fork is sustained (≥6 blocks)
**Value:** `min_fork_depth = 6`
**Meaning:** Natural chain reorganizations (orphans, stale blocks) do not trigger price
divergence. Only when the fork persists for 6+ blocks does the oracle treat it as a
real competing chain and begin applying the divergence model.
**Bias:** Neutral — 6 confirmations is the standard Bitcoin finality threshold.
**Challenge:** Use a probabilistic model where price begins reacting to a fork
probability rather than a hard depth threshold.

### 2.4 Maximum price divergence cap: ±20%
**Value:** `max_divergence = 0.20` (0.50 when liveness penalty is enabled)
**Meaning:** No matter how extreme the fork fundamentals become, the model will not
price the two forks more than 20% apart (default). This reflects the assumption that
markets impose a ceiling on how far fork prices can diverge due to arbitrage pressure
and custodian behavior.
**Bias:** Conservative — real forks (BCH, BSV) have shown much larger divergences.
This understates price pressure on the losing chain and therefore overstates the
threshold required to trigger a cascade.
**Challenge:** Raise the cap (e.g., 50% or 80%) or remove it entirely. Calibrate
against observed fork price divergence data.

### 2.5 Price factor mapping: linear by default, sigmoid optional
**Value:** Linear mapping `f = 0.8 + weight×0.4` → range [0.8, 1.2]. Sigmoid mapping
available via `--use-sigmoid`.
**Meaning:** Under linear mapping, each unit of economic weight produces equal marginal
price effect. Under sigmoid (Biais et al. 2019 / Metcalfe), small advantages are
amplified at the extremes (near 0 or 1) and compressed in the middle.
**Bias:** Linear mapping understates early price divergence at extreme economic splits.
Sigmoid is the more theoretically motivated choice for network effects.
**Challenge:** Empirically fit the sigmoid steepness parameter against observed
exchange price behavior in past forks.

### 2.6 Economic weight reflects transaction routing preference, not raw custody
**Value:** `economic_weight = transactional_pct` (transaction volume on each fork)
**Meaning:** After a fork, custody is duplicated across both chains (see 1.2). The
active, unambiguous signal of fork preference is transaction routing — an exchange or
custodian that processes withdrawals and deposits on v27 is demonstrably supporting v27.
You cannot double-transact: transaction volume is fork-specific by construction.
**Bias:** Slightly more accurate than custody-based weighting, but the two are highly
correlated in the simulation since economic nodes commit fully to one fork.
**Challenge:** Model custody and transaction volume as independent signals that can
diverge (e.g., a custodian holds on both chains but routes transactions through only one).

### 2.7 Price responds instantaneously to economic weight changes (no EMA by default)
**Value:** EMA disabled by default (`--use-economic-ema` flag, alpha=0.15 when enabled)
**Meaning:** When an economic node switches forks, the price oracle updates immediately.
In reality, price discovery lags behind observable on-chain activity by hours or days.
**Bias:** Overstates the speed of price response. Cascades may trigger faster in the
model than in reality because prices react instantly to custody/transaction shifts.
**Challenge:** Enable `--use-economic-ema` with an empirically calibrated alpha value.
Kristoufek (2015) suggests Bitcoin price responds to on-chain metrics with a lag of
roughly 24–48 hours.

### 2.8 Liveness penalty is disabled by default
**Value:** `--enable-liveness-penalty` flag, default=False. Exponent=1.0 (linear decay).
**Meaning:** When disabled, a chain producing zero blocks still receives its full
economic weight in the price oracle (ghost town problem). When enabled, the economic
factor decays proportionally to block production rate: a dead chain collapses to neutral
economic factor (1.0), removing its price premium/discount.
**Bias:** Without liveness penalty, the model understates price collapse on a ghost-town
chain. A v27 chain producing 0 blocks/hour retains economic price support that is not
realistic.
**Challenge:** Enable by default; calibrate the `liveness_exponent` against observed
exchange delisting behavior when a fork chain stops producing blocks.

---

## 3. Mining Pool Assumptions

### 3.1 Pools evaluate profitability under assumed 50/50 hashrate split (fog of war)
**Value:** `assumed_fork_hashrate = 50.0`
**Meaning:** When deciding which fork to mine, a pool calculates profitability as if
hashrate were evenly split between forks, regardless of the actual current distribution.
This models the information uncertainty pools face — they cannot instantaneously observe
competitor allocations. The 50/50 prior is the neutral Bayesian assumption in the absence
of reliable real-time data.
**Bias:** Neutral at 50/50 starting hashrate. Understates the profit advantage of
the dominant fork once one side pulls ahead (feedback loop is not incorporated).
**Challenge:** Model hashrate observation with a lag (e.g., pools infer competitor
allocation from the last N block intervals with exponential decay).

### 3.2 Pool loss tolerance: `max_acceptable_loss = ideology_strength × max_loss_pct`
**Value:** Product formula; e.g., `ideology=0.51 × max_loss=0.26 = 13.3%` tolerance
**Meaning:**
- `ideology_strength` (0–1): Position on the spectrum from pure profit-maximizer (0)
  to maximally committed ideological miner (1).
- `max_loss_pct`: The loss ceiling a fully committed pool (ideology=1.0) would accept
  before being forced off its preferred fork.
- The product scales from zero tolerance (ideology=0, switches at any loss) to full
  ceiling (ideology=1.0, accepts up to max_loss_pct before forced switch).
**Bias:** Calibration uncertainty. Whether 13.3% or 26% is realistic for real-world
pools is empirically uncertain. Overstating tolerance makes cascades harder to trigger
(conservative for v27 win); understating makes them easier.
**Challenge:** Calibrate against observed miner behavior during BCH/BSV fork events.
Pool operators' public statements about fork loyalty provide qualitative bounds.

### 3.3 Pool decisions are independent — no coordination
**Value:** Structural assumption
**Meaning:** Each pool makes its fork decision based solely on price signals, its own
ideology, and its own loss tolerance. Pools do not observe or react to each other's
decisions in real time. There is no "follow the leader" coordination mechanism.
**Bias:** Likely underestimates cascade speed. In reality, large pool decisions are
publicly observable (block attribution on-chain) and other pools react to them,
creating faster coordination dynamics.
**Challenge:** Add a coordination signal: when a pool with >X% hashrate switches, other
pools with similar ideology update their prior toward switching.

### 3.4 Committed pools that are forced off their preferred fork rarely return
**Value:** Structural — no re-entry mechanism implemented
**Meaning:** Once a committed pool's loss exceeds its tolerance and it switches to the
other fork, the conditions that would make its preferred fork profitable again (retarget
on the preferred fork) are not modeled as a pull-back trigger.
**Bias:** Understates oscillation dynamics (committed pools flipping repeatedly).
In practice this may not matter much — once forced off, the preferred fork has
typically already lost so much hashrate that it cannot recover.
**Challenge:** Implement a re-entry condition: if the preferred fork retargets and
its profitability recovers above the switch threshold, the pool returns.

### 3.5 Block subsidy = 3.125 BTC; mining cost = $100,000/block (uniform)
**Value:** `block_subsidy=3.125`, `mining_cost_usd=100000.0`
**Meaning:** Post-4th-halving block reward. Mining cost is treated as uniform across
all pools regardless of hardware efficiency or electricity price. The absolute values
affect the USD profitability calculations that drive forced-switch decisions.
**Bias:** Uniform cost is a significant simplification. Real pools have heterogeneous
costs (energy, hardware vintage, location). Cheap-energy pools have higher loss
tolerance in absolute dollar terms.
**Challenge:** Parameterize per-pool mining costs based on publicly available data
(Cambridge Bitcoin Electricity Consumption Index, mining company filings).

### 3.6 Pools can shift hashrate instantaneously
**Value:** Structural assumption
**Meaning:** When a pool decides to switch forks, its full hashrate allocation moves
in the next decision interval (every 2 simulation seconds). There is no ramp-up period,
contract constraint, or hardware reconfiguration delay.
**Bias:** Overstates cascade speed. Real ASIC farms take hours to reconfigure pool
connections; some have contractual commitments to specific pools.
**Challenge:** Add a hashrate transition delay (e.g., exponential ramp-up over N
minutes after a switch decision).

---

## 4. Economic Node Assumptions

### 4.1 Economic nodes commit fully to one fork at a time
**Value:** Binary fork allocation per node
**Meaning:** Each economic node (exchange, custodian, merchant) is on either v27 or
v26 at any given time — no node splits its activity across both forks simultaneously.
**Bias:** Overstates the clarity of economic signals. Real exchanges often support
both chains simultaneously (dual wallet infrastructure, separate deposit addresses)
to serve all customers regardless of which fork they prefer.
**Challenge:** Allow economic nodes to maintain a fractional allocation across both
forks, with their transaction weight split proportionally.

### 4.2 Effective switching threshold: `switching_threshold × (1 + ideology_strength × 2.0)`
**Value:** Formula implemented in `economic_node_strategy.py`
**Meaning:** An economic node with ideology=0 (neutral) switches when the price gap
exceeds the base `switching_threshold`. An economic node with ideology=0.4 requires
a 1.8× larger gap before switching (effective threshold = base × 1.8). Ideology
represents preference inertia — the additional price gap required above the neutral
threshold before a committed node changes its active fork.
**Bias:** The multiplier coefficient (2.0) is an assumed parameter. Validated against
sweep results (ideology≈0.30–0.35 for switchover at observed gap levels) but not
calibrated against real exchange behavior.
**Challenge:** Calibrate against documented exchange delisting/relisting decisions
during past fork events (timing relative to price divergence).

### 4.3 Switching cooldown: 300s for economic nodes, 600s for user nodes
**Value:** `switching_cooldown=300` (economic), `switching_cooldown=600` (user)
**Meaning:** After switching forks, a node cannot switch again for the cooldown period.
This prevents rapid oscillation and models the operational friction of changing
infrastructure.
**Bias:** Arbitrary values with no empirical calibration. Could be too short
(exchanges take days to switch wallet infrastructure) or too long (automated systems
could switch faster).
**Challenge:** Calibrate against observed exchange response times during past forks.

### 4.4 Custody liquidation of unpreferred fork is NOT modeled
**Value:** Omission (not implemented)
**Meaning:** When an economic node switches from v26 to v27, the model does not
simulate the sale of their duplicate v26 holdings. In reality, high-ideology nodes
may sell their unpreferred-fork tokens to reinforce their fork commitment (one-way
bet). Low-ideology nodes may hold both chains as a hedge against their own prediction
being wrong.
**Directional bias:** Conservative — missing sell pressure on v26 means the model
understates price decline on the losing chain. The cascade threshold is overstated
(easier to trigger in reality than modeled).
**Proposed implementation:** Scale liquidation by ideology:
`liquidation_fraction = ideology_strength`
- ideology=0.0 → holds all duplicate tokens (full hedge, no sell pressure)
- ideology=0.5 → liquidates 50% of unpreferred-fork holdings over time
- ideology=1.0 → liquidates all unpreferred-fork holdings (full conviction bet)
**Challenge:** Implement as optional flag (`--enable-custody-liquidation`) with
`liquidation_rate` parameter controlling the speed of sell execution.

### 4.5 Transaction volume and custody weight are treated as equivalent
**Value:** In the simulation, economic nodes move both simultaneously when switching
**Meaning:** When a node switches forks, both its transaction routing AND its effective
custody weight move to the new fork. In the real world these can diverge: an exchange
might route transactions on v27 while retaining v26 custodial holdings indefinitely.
**Bias:** Neutral within the simulation (the two are structurally identical). Relevant
for interpretation — the parameter `economic_split` is correctly interpreted as
"fraction of transaction volume on v27," not "fraction of BTC custody on v27."
**Challenge:** Separate custody and transaction activity into independent node-level
attributes that can diverge over time.

---

## 5. Network and Infrastructure Assumptions

### 5.1 Block propagation window: 30 seconds
**Value:** `propagation_window=30.0` seconds
**Meaning:** The reorg oracle treats blocks propagated within 30 seconds of each other
as potentially competing (natural variance, not a sustained fork). This is the grace
window before a block height difference is counted as a fork event.
**Bias:** Reasonable for a well-connected global network; may understate propagation
delay for geographically distributed miners.
**Challenge:** Use empirically measured propagation delay distributions from Bitcoin
network monitoring (e.g., dsn.kastel.kit.edu propagation data).

### 5.2 Solo miner hashrate is nominal — solo miners follow pool decisions
**Value:** Structural limitation (not a tunable parameter)
**Meaning:** The `v27_solo_hashrate` time series column is static. Solo miners (user
and economic nodes that mine independently) do not make independent fork decisions —
they follow pool allocation. A ghost-town v27 chain with 0 pool hashrate produces 0
blocks even though solo hashrate shows non-zero.
**Bias:** Understates the "true believer" trickle of blocks that would keep a
minority chain alive indefinitely. In reality, ideologically committed solo miners
would continue producing occasional blocks even after all major pools abandon a fork.
**Challenge:** Give solo miners independent decision-making: they mine their preferred
fork regardless of pool behavior, providing a minimum block production floor.

### 5.3 Network topology is a partition model, not a full p2p mesh
**Value:** Structural assumption
**Meaning:** The simulation models two network partitions (v26 and v27) with a bridge
node for cross-partition block submission. It does not simulate individual peer
connections, routing delays, or eclipse attacks.
**Bias:** Simplifies real network dynamics. Partition borders are clean in the model;
real Bitcoin networks have fuzzy consensus boundaries with nodes in various states
of partial upgrade.
**Challenge:** Model individual peer connections with heterogeneous upgrade status.

### 5.4 Block size = 1MB for fee calculations
**Value:** `(fee_rate * 1_000_000) / 100_000_000` (1MB block assumed in fee oracle)
**Meaning:** Fee revenue per block is calculated assuming 1MB blocks fully utilized.
SegWit weight units are not modeled.
**Bias:** May overstate fee revenue slightly (blocks are not always full) or understate
it (SegWit blocks can carry more economic weight than 1MB base size implies).
**Challenge:** Use empirical mempool data for fee rate and block utilization.

### 5.5 No miner-extractable value (MEV)
**Value:** Omission
**Meaning:** The model does not include any value miners can extract beyond block
subsidy and fees (e.g., front-running, sandwich attacks, liquidations). In the
context of a contentious fork, MEV opportunities on one chain vs. the other are
not modeled as a profitability signal.
**Bias:** Neutral for current research questions (Phase 1 is about fork outcomes,
not detailed revenue structure).
**Challenge:** Add chain-specific MEV estimates as a component of pool profitability.

### 5.6 No halving events during simulation
**Value:** `block_subsidy=3.125` (constant)
**Meaning:** The block subsidy does not change during a simulation run. For runs of
≤20,000 seconds this is approximately correct (a halving takes ~4 years of real time).
**Bias:** Negligible for current run durations.
**Challenge:** Not applicable for current research scope.

### 5.7 Hashrate can shift instantaneously (no hardware constraints)
**Value:** Structural assumption (same as 3.6, applies to solo miners and user nodes)
**Meaning:** See assumption 3.6. Also applies to user-nodes that mine — they can
shift their small hashrate contribution immediately upon deciding to switch forks.
**Bias:** See 3.6.

---

## 6. Threshold Calibration Assumptions

### 6.1 144-block retarget threshold numbers are not real-world calibrated
**Value:** Methodological note
**Meaning:** The 144-block retarget regime is not Bitcoin's actual difficulty adjustment
schedule. Threshold values derived from 144-block runs (e.g., economic threshold ≈ 0.29)
reflect the fast-retarget rescue mechanism and should not be cited as real-world
Bitcoin fork thresholds. They are valid for studying which parameters matter and
directional sensitivity, but not for calibrated threshold claims.
**Bias:** Understates the economic support required for a minority fork to survive
(fast retarget rescues chains that would die under 2016-block timing).
**Use:** Use 2016-block regime results for any real-world threshold claims.

### 6.2 Pool ideology and max_loss parameters are not empirically calibrated
**Value:** Default pool config: `ideology_strength` ranges 0.0–0.8 across pools,
`max_loss_pct` ranges 0.10–0.30
**Meaning:** These values are theoretically motivated but not derived from observed
mining pool behavior during real forks. The diagonal threshold (`ideology × max_loss
≳ 0.16–0.18`) is validated internally across sweeps but not against real-world data.
**Bias:** Direction uncertain. If real pools have lower ideology × loss products,
cascades are easier to trigger. If higher, they're harder.
**Challenge:** Use public statements and observed behavior from BCH, BSV, and
SegWit2x fork events to bound plausible ideology and loss tolerance ranges.

---

## 7. Summary Table

| # | Assumption | Current Value | Bias Direction | Priority to Address |
|---|-----------|:-------------:|:--------------:|:-------------------:|
| 2.4 | Price divergence cap | ±20% | Conservative | High |
| 2.8 | Liveness penalty off by default | disabled | Conservative | High |
| 4.4 | No custody liquidation | omitted | Conservative | Medium |
| 3.1 | Fog of war at 50/50 | 50.0% | Neutral | Low |
| 3.3 | No pool coordination | omitted | Conservative (speed) | Low |
| 3.4 | No committed pool re-entry | omitted | Unknown | Low |
| 3.5 | Uniform mining cost | $100k/block | Neutral | Low |
| 3.6 | Instant hashrate shifts | instantaneous | Conservative (speed) | Low |
| 4.1 | Binary fork allocation | binary | Overstates clarity | Low |
| 4.3 | Switching cooldown | 300s/600s | Uncalibrated | Low |
| 5.2 | Solo miners nominal | structural | Conservative | Low |
| 6.2 | Pool ideology uncalibrated | theoretical | Uncertain | Medium |

**Conservative** = assumption makes fork outcomes harder to trigger than in reality,
so reported thresholds are upper bounds.
**Neutral** = bias direction unclear or effect is symmetric.

---

## 8. Phase 2 Findings: Confirmed Emergent Behavior

Phase 2 scenario discovery analysis (n=268 144-block, n=298 2016-block, full 60-node
network) confirmed or explained the emergent behavior noted in earlier preliminary work.

### 8.1 The Inversion Zone — Confirmed and Mechanistically Explained

**Observation:** At `economic_split` ≈ 0.60–0.70, increasing `pool_committed_split`
in favor of v27 *reduces* v27's win probability (Table 4, §4.3.1). A 4-percentage-point
shift from `pool_committed_split=0.20` to `0.30` converts a v27 win to a v26 win at
these economic levels.

**Status: CONFIRMED — mechanism identified.** This is not a model artifact. The
inversion is caused by the Foundry flip-point (§4.3.2): below `pool_committed_split ≈
0.214`, Foundry USA (~30% hashrate) is assigned v26-committed ideology and is
*economically trapped* by the v27 price premium. Its forced exit triggers a neutral
pool cascade. Above the flip-point, Foundry shifts to v27-committed ideology, which
simultaneously purifies the v26 defending block (AntPool + F2Pool, ~33% combined
hashrate) and removes the cascade trigger. The mechanism is confirmed by pool decision
logs showing forced-switch threshold crossings.

**Assumptions that modulate the threshold value (but not the mechanism):** 2.2
(oracle weights), 3.1 (fog-of-war at 50%), and pool calibration all affect the
specific `pool_committed_split` value at which the flip occurs, not the structural
existence of the inversion.

### 8.2 Hashrate Non-Causality — Confirmed with Qualified Exception

**Observation:** `hashrate_split` shows zero independent causal effect at `economic_split
≥ 0.60` across both retarget regimes (targeted_sweep2, n=42, 144-block; hashrate_2016_
verification, n=12/12 cells at econ≥0.60, 2016-block). Identical columns across all
hashrate levels in targeted_sweep2 Table 3 confirm the non-causality result cleanly.

**Exception:** At `economic_split = 0.50` under 2016-block retarget, hashrate is
conditionally causal with a non-monotonic pattern (Table 3b). The mechanism: at
economic parity, intermediate hashrate levels (35–45%) cause Foundry's accumulated
mining losses to cross its tolerance threshold before the simulation ends, forcing a
switch that the low- and high-hashrate cases do not trigger within the same window.

**Assumption dependence:** See §9.2 — assumption 3.1 (fog-of-war) strengthens this
finding; with an actual-hashrate feedback loop, some residual hashrate causality may
persist above `economic_split = 0.60`.

### 8.3 Causal Rank Reversal — Confirmed on Full Network (n=566 total)

**Observation:** `pool_committed_split` importance rises from 11.3% (144-block,
dominant parameter: `economic_split` at 77.2%) to 52.8% (2016-block, dominant
parameter: `pool_committed_split`; `economic_split` drops to 20.2%). RF OOB accuracy:
80.0% (144-block), 83.2% (2016-block). Contentiousness 2× higher at 2016-block
(mean 0.271 vs. 0.132).

**Status: CONFIRMED** on full 60-node network with no quantization artifact. The
rank reversal is the direction-of-dominance change; the specific importance percentages
carry the oracle-weight caveat in §9.1.

---

## 9. Bias Assessment

This section classifies the primary findings by their vulnerability to modeling bias
(artifacts of simulation design choices) and sampling bias (artifacts of how the
parameter space was explored). This is distinct from the assumption catalogue above:
assumptions document what the model does; this section assesses whether the findings
derived from it could be artefacts of those choices.

---

### 9.1 Modeling Bias Risks

#### MB-1: User node null result is partially tautological

**Finding at risk:** "User nodes have no causal influence on fork outcomes."

**Bias mechanism:** The price oracle (`combined_factor`) computes `economic_weight`
exclusively from exchange and institutional `custody_btc` values. User node custody is
not included in the formula by design. Consequently, the finding that user nodes cannot
shift the economic price signal is guaranteed by the oracle structure before any sweep
runs — it is not discovered from simulation data.

**What is genuinely discovered:** That user nodes cannot shift outcomes through their
hashrate contribution (~11.75% of total) under any tested parameter configuration.
This result is not tautological — it depends on the hashrate being insufficient to
change block production enough to reverse the cascade, and is confirmed by an exact
null (zero variation across all 36 scenarios in targeted_sweep5).

**How to frame it:** The hashrate-pathway null is fully defensible. The economic-weight-
pathway null should be framed as a structural consequence of the weight ratio (2197:1),
not as an independently discovered fact. The User-PRIM result quantifies the ceiling;
it does not test whether the ceiling is correctly placed.

---

#### MB-2: Assumed 50/50 hashrate strengthens hashrate non-causality

**Finding at risk:** "Hashrate_split has no causal effect on fork outcomes at econ ≥ 0.60."

**Bias mechanism:** Assumption 3.1 computes pool profitability at an assumed 50%
hashrate on each fork regardless of actual distribution. This prevents the direct
feedback loop (minority hashrate → lower revenue → pool switches → further minority
hashrate) from activating. In a model where pools used actual observed hashrate,
some residual hashrate causality would persist even above the cascade threshold because
each pool's profitability signal would include information about the current distribution.

**Degree of risk:** Moderate. The difficulty adjustment survival window mechanism
(§4.5.1) provides an independent, model-agnostic reason for hashrate non-causality:
difficulty equalizes block rates before the economic cascade resolves at any hashrate
split above approximately 10%. The fog-of-war assumption amplifies this but does not
create it. The conditional causality at `econ=0.50` under 2016-block retarget — where
the survival window is long — confirms that the residual causality exists in the right
conditions.

**How to frame it:** Report the non-causality with the 50/50 assumption stated as a
condition. The finding is: "Under the fog-of-war profitability model, hashrate is non-
causal at econ ≥ 0.60." Not: "Hashrate is non-causal in Bitcoin fork dynamics."

---

#### MB-3: Oracle weights structurally privilege economic_split

**Finding at risk:** "Economic_split is the dominant predictor of fork outcomes (77.2%
RF importance at 144-block)."

**Bias mechanism:** The price oracle assigns a fixed 0.5 coefficient to economic weight
versus 0.3 for chain weight and 0.2 for hashrate weight. By structural construction,
economic_split has the largest leverage over price, and price drives all pool and economic
node decisions. The high RF importance of `economic_split` is partially produced by
this design choice, not solely by the underlying fork dynamics.

**Degree of risk:** Low for the direction (economic factors dominate), moderate for
the magnitude (77.2% specifically). The oracle weights were calibrated against
Bitcoin's custody-driven valuation, not chosen to produce a desired result. The
finding that economic factors dominate is consistent across both retarget regimes
and multiple analytical methods.

**How to frame it:** "Under a custody-weighted price oracle calibrated to 2026
Bitcoin market structure, economic alignment is the dominant predictor at 144-block
retarget." Not: "Economic alignment is unconditionally dominant in Bitcoin fork
outcomes."

---

#### MB-4: Specific threshold values are calibration-specific

**Finding at risk:** Foundry flip-point (~0.214), economic override threshold (~0.82),
ideology×max_loss product diagonal (~0.16–0.20).

**Bias mechanism:** These threshold values derive from specific calibration choices:
Foundry holding ~30% total hashrate, `pool_neutral_pct = 30%`, block subsidy at
3.125 BTC, mining cost at $100k/block, and price oracle weights as above. The Foundry
flip-point formula is `pool_committed_split × 0.70 > 0.15`, which is entirely
determined by the Foundry hashrate share (30%) and the neutral pool fraction (30%).
A consolidation event placing one pool at 40% hashrate shifts the flip-point without
changing the mechanism.

**How to frame it:** Threshold values apply to the modeled 2026 Bitcoin pool
landscape. The mechanisms that produce the thresholds are general; the specific
numbers are not. Both must be stated in any public claim.

---

#### MB-5: ±20% divergence cap bounds all findings

**Finding at risk:** All threshold findings — they all operate within the ±20%
maximum price differential.

**Bias mechanism:** Real fork events (BCH/BTC) have produced price divergences of
80–95% over months. At larger divergences, the dynamics change qualitatively: the
losing chain's token may collapse before its difficulty adjustment fires, making
hashrate suddenly causal (no token value = no mining incentive before the survival
window closes). The ±20% cap may exclude the regime most relevant to long-run fork
survival.

**How to frame it:** All findings are bounded to the short-to-medium-run regime
(weeks to months post-fork, before extreme divergence). Long-run dynamics under
larger divergences are not modeled.

---

### 9.2 Sampling Bias Risks

#### SB-1: Economic friction parameters confirmed non-causal on n=4 (weakest null result)

**Finding at risk:** "`econ_inertia` and `econ_switching_threshold` are non-causal."

**Bias mechanism:** The full-network confirmation of this null result rests on
`targeted_sweep3b` with only 4 scenarios. The earlier lite-network sweep (n=16) was
invalidated by a role-name parameter bug. No sweep has tested these parameters across
a range of `pool_committed_split` values or under 2016-block retarget. The non-
causality claim is thin: 4 data points at one specific parameter combination.

**Risk level:** High. This is the least well-supported null result in the paper.
If these parameters were re-tested at 2016-block retarget or near the Foundry
flip-point boundary, they could show conditional causality analogous to the
`hashrate_split` finding at `econ=0.50`.

**How to frame it:** "Not confirmed causal in initial full-network testing; full
validation at 2016-block retarget pending." Should not appear in the confirmed
non-causal parameter table without this caveat.

---

#### SB-2: pool_max_loss_pct ≤ 0.217 threshold derived from lite network

**Finding at risk:** "Full economic migration occurs when `pool_max_loss_pct ≤ 0.217`."

**Bias mechanism:** This threshold was established from Phase 3 lite-network data,
which has the documented economic node quantization artifact (~4 nodes, step-function
thresholds rather than smooth variation). Phase 3b (full 60-node network, currently
running) is the validation test. Until Phase 3b results are incorporated, this
threshold is a working estimate, not a confirmed result.

**Risk level:** Medium. The Phase 3b design specifically targets this finding's
validation. The quantization artifact is documented and its direction is understood
(creates sharper thresholds than the continuous full-network response).

---

#### SB-3: 144-block logistic regression is structurally unreliable

**Finding at risk:** Any interaction-based mechanistic claims derived from 144-block
logistic regression.

**Bias mechanism:** The 144-block LR has cross-validated accuracy of 59.8% (only 10%
above chance) and inverted coefficient signs for several terms relative to the 2016-
block fit. The 144-block dataset also contains the lite-network quantization artifact
in some sweeps. The RF importance scores at 144-block are valid (80.0% OOB accuracy);
the LR is not. No regression-based mechanism claims should be applied to 144-block
dynamics.

---

#### SB-4: Phase 3 LHS concentrated in transition zone — accuracy may not generalize

**Finding at risk:** "83.2% RF OOB accuracy at 2016-block" as a characterization of
model predictability.

**Bias mechanism:** The Phase 3 LHS samples were drawn from within the PRIM
uncertainty bounds — the parameter region specifically identified as having close to
50/50 outcomes. An RF evaluated on data concentrated in the uncertain transition zone
will report lower accuracy than one evaluated on uniformly distributed data (where
most scenarios have unambiguous outcomes). The 83.2% figure is an accurate
characterization of transition-zone predictability; it does not represent full-
parameter-space predictability, which is likely higher.

---

#### SB-5: Early LHS hashrate confound was identified and corrected — but signals general risk

**Finding at risk:** Any result from pre-correction LHS sweeps (these have been
excluded from the analysis).

**Bias mechanism:** The hashrate confound (apparent r=0.83 in early LHS, shown to
be a sampling artifact by targeted sweeps) was caught because targeted sweeps were
run specifically to verify. Parameters that only show effects in combination with
other parameters that were fixed early in the elimination sequence could be invisible
to subsequent LHS analysis. The elimination program was thorough but sequentially
constructed.

**Note:** This is a historical risk, not a current one. The confound was identified
and the affected data excluded. It is documented here because the same risk applies
to any parameter fixed based on LHS correlations without independent targeted
verification.

---

### 9.3 Bias Summary and Defensibility Assessment

| Finding | Modeling Bias | Sampling Bias | Defensibility |
|---------|:-------------:|:-------------:|---------------|
| Inversion zone / non-monotonic boundary | Low | None | **Full** — mechanism confirmed in logs, LHS gap clean |
| Causal rank reversal (direction) | Moderate (oracle weights) | None | **Full with oracle caveat** |
| Importance percentages (77.2%, 52.8%) | Moderate | Some (LHS concentration) | Qualified |
| Hashrate non-causality at econ ≥ 0.60 | Moderate (assumption 3.1) | None | **Full with fog-of-war caveat** |
| Conditional hashrate causality at econ=0.50 | Moderate | Moderate (small grid) | Qualified |
| ideology × max_loss product structure | None | None | **Full** |
| Specific threshold values (0.214, 0.82, 0.16–0.20) | **High** (calibration-specific) | None | Mechanism full; values qualified |
| Economic override above ~0.82 | Moderate (oracle weights) | None | **Full within ±20% cap** |
| Contentiousness 2× higher at 2016-block | None | None | **Full** |
| User node hashrate pathway null | None | None | **Full** |
| User node economic pathway null | **High** (partially tautological) | None | Structural ceiling only |
| econ friction params non-causal | None | **High** (n=4) | Weak — needs 2016-block retest |
| pool_max_loss_pct ≤ 0.217 threshold | None | **High** (lite network) | Pending Phase 3b |
| 144-block logistic regression | None | **High** (unreliable fit) | Not defensible |
| Framework as null-result detector | None | None | **Full** |

**Defensibility key:**
- **Full** — supported by multiple independent lines of evidence, mechanism confirmed, not sensitive to contested modeling choices
- **Full with [caveat]** — finding is robust but the stated condition limits its scope
- **Qualified** — finding is likely correct but the specific value or magnitude could shift with different assumptions or more data
- **Pending** — awaiting Phase 3b full-network validation
- **Not defensible** — should not be cited; methodology insufficient

---

## 10. Cross-References

| Document | Purpose |
|----------|---------|
| `docs/section_3_methodology.md` | Complete methodology including Phase 2 Section 13 |
| `docs/section_4_2_parameter_causality.md` | Parameter elimination program; hashrate confound; non-causal parameter table |
| `docs/section_4_3_foundry_flippoint.md` | Inversion zone mechanism; threshold summary table |
| `docs/section_4_8_boundary_fitting.md` | RF feature importance; logistic regression; PRIM bounds |
| `docs/section_4_11_user_prim.md` | User-PRIM null result; weight ratio ceiling |
| `tools/sweep/SWEEP_FINDINGS.md` | Phase 1 sweep results and parameter elimination detail |
