# Difficulty Adjustment Survival Window: Complexity Analysis

**Cross-reference:** `tools/sweep/SWEEP_FINDINGS.md` §"Difficulty Adjustment Survival Window"  
**Grounded by:** BIP-110 live event observations, `field_observations.md` entries 2026-08-08 through 2026-08-10  
**Simulation data:** `lhs_2016_full_6param` (692 scenarios), targeted sweeps 8, 9, 11

---

## What the mechanism is

A minority fork can win not by having more hashrate, but by surviving long enough to reach
a difficulty adjustment that makes its blocks dramatically cheap to mine, then attracting
a profit-seeking hashrate spike before the majority chain can respond.

The sweep findings establish the core formula:

```
survival_window ≈ retarget_interval / f
```

where `f` is the minority chain's hashrate fraction and the result is in wall-clock time to
the minority chain's first difficulty adjustment. If economic conditions remain viable
throughout that window, the adjustment triggers a cascade; if price collapses first, the
chain dies.

The sweep simulation confirmed this mechanism fires at 144-block retarget (targeted_sweep9:
retarget at t=8,106s, committed v26 pool losses jump from 9% to 56%, cascade completes
decisively). It does not fire at 2016-block retarget within any practical run window —
the "stuck contested" state at ~50/35 hashrate equilibrium is the realistic baseline.

---

## Three complexities the formula understates

### 1. Position within the difficulty period

The formula assumes the fork starts a fresh difficulty period — i.e., retarget_interval
blocks away from the minority chain's next adjustment. This is only true at the
worst-case timing (fork immediately after a retarget). In practice, position within the
period is a free variable that can reduce the required survival window by a factor of up
to retarget_interval.

**Formulation with position:**

```
survival_window = (retarget_interval - blocks_already_mined_in_period) / f
```

| Fork timing | Blocks remaining | Survival window at f=0.25 |
|---|---|---|
| Immediately after retarget (worst) | 2016 | 2016 / 0.25 × 10 min = 5.6 days |
| Mid-period | 1008 | 1008 / 0.25 × 10 min = 2.8 days |
| Near end of period (best) | 66 | 66 / 0.25 × 10 min = 4.4 hours |

For the BIP-110 event, the fork split at height 961632 — the exact retarget boundary
opening the new difficulty period. The minority chain faced a full 2016-block survival
window, the worst possible case. At f≈0.025–0.044, that translated to 87–206 days —
many orders of magnitude beyond what was observed (chain stalled after 2 blocks).

**Why this matters for the model:** the sweep simulation always initializes at the start
of a difficulty period, implicitly assuming worst-case timing. Survival windows measured
in simulation are therefore maximum estimates. Real forks splitting mid-period face
proportionally shorter windows, making the mechanism more plausible at hashrate fractions
slightly above the simulation's non-firing threshold.

**Practical implication:** a fork that splits 66 blocks before a retarget boundary at
f=0.10 would need only 110 minutes of survival — within the range where speculative
hashrate support could plausibly sustain it. The mechanism is not equally implausible
at all timings; timing within the period is a leverage parameter.

---

### 2. Two-phase hashrate dynamics (speculative → residual)

The model treats pool decisions as static transitions: a pool is either on fork A or fork B,
driven by a price oracle comparison. Real hashrate during the BIP-110 event showed a
two-phase structure not captured by this model:

**Phase 1 — speculative hashrate:** At fork inception, ~14.5 Eh/s (per Tone Vays report
on Ocean pool's BIP-110 side) supported the minority chain — a mix of ideologically
motivated hashrate and rented capacity "mining at a loss." This was sufficient to find the
two minority-chain blocks (961632 and 961633) at roughly normal speed.

**Phase 2 — collapse to residual:** Once rented/speculative hashrate withdrew (unprofitable),
the remaining committed minority hashrate dropped to ≤1.2 Eh/s — consistent with the
≤4.4% (95% CI) bound from the 679-minute zero-blocks statistical argument. The chain went
dark and never recovered.

The model's price oracle assumption (pools switch based on relative profitability, one
decision per pool) cannot represent this dynamic because:

1. It treats all hashrate as economically rational and persistent once committed
2. It has no concept of "rented" or "speculative" hashrate that is temporarily present
   regardless of oracle signals and then evaporates
3. It resolves pool membership as discrete (in / out), not as a continuous inflow/outflow

**Consequence for survival window analysis:** the formula's `f` implicitly assumes the
minority hashrate fraction is constant throughout the window. In reality, `f` is
time-varying: typically highest at fork inception (speculative pile-in) and declining as
speculative hashrate exits. The *effective* f for survival window purposes is the
sustained rate, not the peak. A chain that briefly shows f=0.17 (from speculative
support) but quickly settles to f=0.025 (residual committed) will follow the f=0.025
survival window, not f=0.17.

**The "false start" pattern:** the two-phase structure means a minority chain can produce
its first few blocks at near-normal speed (giving the appearance of viability), then stall
when speculative hashrate exits — before accumulating enough blocks to reach its difficulty
adjustment. The BIP-110 event is a clean example: two blocks found at normal difficulty,
then 11+ hours of silence.

---

### 3. Intra-pool divergence (DATUM-style pools)

The model's pool behavioral typology (committed / neutral profit-maximizer / swing)
assigns one decision per named pool. The BIP-110 event introduced a structurally
different actor: pools with client-level independent chain selection.

Ocean pool's DATUM infrastructure allowed each connected client to independently choose
their block template, resulting in:
- `bip110.ocean.xyz` (Roughnecks sub-pool): mined the last two BIP-110 blocks
- `ocean.xyz` (Simple Mining sub-pool): continued uninterrupted on the legacy chain

These are not separate pools in the conventional sense — they share infrastructure,
branding, and operator — but they made genuinely independent chain commitments. The
`@boomer_btc` / BarefootMining post confirmed this is the intended DATUM design: "each
client is making their own decision."

**Why none of the three model archetypes captures this:**

| Archetype | Prediction | Observed Ocean behavior |
|---|---|---|
| Committed (v27) | All hashrate to v27, sustained | Some hashrate to v27, some to v26 simultaneously |
| Neutral profit-maximizer | Follow price signal, migrate to winner | Roughnecks mined BIP-110 at a loss |
| Swing | Threshold-based flip, one decision | No unified pool-level decision at all |

The correct unit of analysis for a DATUM-style pool is the **individual client operator**,
not the pool umbrella. When a large pool uses permissionless template selection, the pool's
effective pool_committed_split is not a fixed parameter — it is the aggregate of its
clients' individual commitments, which may themselves be heterogeneous.

**Consequence for committed_split measurement:** a pool counted as "neutral" (not signaling
BIP-110 as a pool) may nonetheless have committed clients within it who would direct
hashrate to a minority chain. This means:
- The model may undercount effective v27-committed hashrate when DATUM-style pools are present
- Pool-level signaling rates (like the 2.5% measured during BIP-110) are a lower bound on
  client-level commitment, not the full picture
- The Foundry flip-point mechanism (a concentrated large pool committing as a single discrete
  event) does not apply to pools that fragment internally

**Research implication:** the paper's pool-level unit of analysis should be qualified for
pools with internal client delegation. The committed/neutral/swing typology applies cleanly
to vertically integrated pools but requires decomposition for DATUM-architecture pools.

---

## Conditions required for the mechanism to fire

Synthesising the three complexities, the survival mechanism fires only when all of the
following hold simultaneously:

| Condition | Threshold | BIP-110 event |
|---|---|---|
| Minority hashrate (sustained) | f ≥ ~0.10–0.15 (from sweep data) | f ≤ 0.044 (95% CI) — FAILED |
| Position within difficulty period | Ideally < 500 blocks remaining | Fork at boundary (2016 remaining) — WORST CASE |
| Economic conditions viable through window | No price collapse during survival window | Irrelevant (chain died in hours) |
| Sustained committed hashrate (not speculative) | Must be maintained throughout window | Speculative hashrate exited — FAILED |

The BIP-110 event failed on all conditions simultaneously, making it a clean but
non-constraining negative result. It confirms the mechanism doesn't fire at extreme
low hashrate + worst timing, but says nothing about the moderate-hashrate cases the
simulation identifies as genuinely contested.

---

## What the simulation data says about when it does fire

From sweep findings:

- **targeted_sweep9 (2016-block, econ=0.70, f=0.25):** retarget fires at t=8,106s,
  losses jump 9%→56%, cascade completes. Mechanism fires when f is high enough for the
  minority chain to mine 2016 blocks within a ~8,000s simulation window (in simulation
  seconds; actual chain time is longer).
- **targeted_sweep11 (2016-block, f≈0.20, econ=0.50):** v27 collapses by t≈1200s (197
  blocks), never reaches retarget — no resurrection. Mechanism fails.
- **lhs_2016_full_6param:** "contested" outcome (mechanism plausibly firing or stalling)
  occurs in 46/692 scenarios (6.6%), concentrated at economic_split ∈ [0.28, 0.78] and
  pool_committed_split ∈ [0.15, 0.53].

The practical threshold from sweep data is approximately f ≥ 0.25 at econ ≥ 0.70 for the
mechanism to fire reliably in the 2016-block regime. At lower f or lower econ, the chain
collapses before accumulating the blocks needed for relief.

---

## Model limitations this analysis identifies

1. **Position-within-period not parameterised.** All simulations start at a difficulty
   period boundary. Real forks can split mid-period, reducing the required survival
   window significantly.

2. **Static pool hashrate commitment.** No representation of speculative or rented
   hashrate that temporarily inflates f at fork inception then rapidly exits.

3. **Pool-level unit of analysis.** DATUM-style pools with client-level template
   selection cannot be modelled with a single committed/neutral/swing assignment per
   named pool.

4. **Fog of war understates cascade sensitivity.** The assumed_fork_hashrate=50.0
   assumption means the model's pools do not respond to the actual difficulty drop
   directly — they see it only indirectly via the price oracle. Real opportunistic
   hashrate may respond faster and more aggressively to a visible difficulty drop than
   the price-oracle model predicts.
