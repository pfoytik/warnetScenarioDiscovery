# Field Observations — BIP-110 Flag Day

Narrative/interpretive notes captured during live monitoring, supplementing
the raw CSV logs (`bip110_signaling_log.csv`, `bip110_history.csv`,
`mempool_guide_comparison_log.csv`, `economic_signals_log.csv`). Raw data
lives in those files; this file is for dated observations and interpretation
that the CSVs don't capture on their own.

---

## 2026-08-08T23:12 UTC — Confirmed live chain split; minority chain stalled

**What was confirmed:**
- `myNode`'s own `getchaintips` never showed the competing chain at any point
  overnight or this morning (`fork_count` stayed 0 continuously since the
  2026-08-08 ~03:11 UTC restart) — a genuine peering blind spot, not a
  detection bug. `myNode`'s peers never relayed the competing branch.
- External cross-check via mempool.guide (independently tracking what
  appears to be the BIP-110/v27 side) confirmed a real divergence:
  - Height 961633
  - `myNode` hash:        `00000000000000000002022e1d17f86131559d0e3707a1a25852d9ccf0130437`
  - mempool.guide hash:   `0000000000000000000139eda19858a84b2ed80cb6056ba8449f0792d13d0968`
  - Confirmed via direct same-height `getblockhash` comparison, not just
    differing tip heights.

**Pattern observed since (four consecutive 3-min cycles, ~23:01–23:11 UTC):**
- mempool.guide's tip has not moved from height 961633 the entire time.
- `myNode`'s chain has continued climbing normally over the same window:
  961646 → 961647 (per `bip110_signaling_log.csv`).

**Interpretation:** consistent with the Difficulty Adjustment Survival
Window mechanism (Section sec:window of the paper) playing out live. Given
the observed ~2.6% pool-side signaling rate for BIP-110 (see
`bip110_history.csv`), the minority chain's implied hashrate would put its
expected block time on the order of hours rather than minutes, until its
first difficulty retarget lowers the target to match its actual hashrate.
A chain that's been stalled for 10+ minutes while the majority chain
proceeds at a normal ~3 blocks per 10-11 min pace is directly consistent
with that mechanism, not merely "the API is stale" (same-height hash
mismatch already rules that out).

**Caveat:** this is a live, single real-world event, not a controlled
replication — worth continuing to log rather than treating this single
snapshot as confirmatory. If/when the minority chain produces its next
block, worth noting the actual wall-clock gap between it and its
predecessor as a direct real-world data point for comparison against the
simulation's survival-window timing.

---

## 2026-08-08T23:12 UTC — No new economic-side support observed

Checked again as of this timestamp: no new exchange, custodian, or other
economic-node support for BIP-110 beyond what's already in
`economic_signals_log.csv` (still just the single small supporter, `start9`,
logged 2026-08-08T03:01 UTC). Binance/Coinbase/Kraken re-confirmed silent
as of 15:56 UTC. No further movement since. Consistent with the pool-side
picture: this activation attempt looks to be failing on both the hashrate
side and the economic side simultaneously, not just one or the other —
directly relevant to the paper's two-layer outcome structure finding
(hashrate resolution and economic adoption as independent axes that can
each fail or succeed on their own).

---

## 2026-08-09T10:16 UTC — Closing summary: clean legacy-chain win, monitoring stopped

**Final state, confirmed before stopping the recording systems:**

- **Minority (BIP-110/v27) chain: permanently stalled at height 961633.**
  Every mempool.guide check from 2026-08-08T23:01 UTC through
  2026-08-09T10:14 UTC (11h13m, ~225 consecutive 3-min cycles) returned the
  identical tip hash. Zero new blocks found on that chain in over 11 hours —
  effective abandonment, not a temporary slowdown.
- **Majority (legacy/v26) chain: progressed normally throughout.**
  `myNode` climbed from height 961647 (2026-08-08T23:10 UTC) to 961719
  (2026-08-09T10:14 UTC) — 72 blocks in ~11h4m, ~9.2 min/block, consistent
  with undisturbed normal operation.
- **Pool signaling collapsed to 0% in the new difficulty period**
  (period starting 961632): 0 of 88 blocks scanned so far, down from the
  ~2.5-2.7% that had held steady through the prior period. Miners appear to
  have dropped BIP-110 signaling entirely post-resolution, not merely
  leveled off.
- **Economic side: no support ever materialized beyond the single small
  supporter (`start9`) logged at the outset.** Final weighted estimate:
  100% "active" (meaningless given zero oppose entries were ever logged),
  3.3% "conservative" (support weight over all tracked weight) — see
  `economic_signals_log.csv` / `economic_signal_log.py summary` for the
  full breakdown.

**Overall read:** a clean, decisive legacy-chain win. Both the hashrate
layer and the economic layer failed to build toward activation
simultaneously and by a wide margin, not a close contest that could have
gone the other way with slightly different conditions. `myNode` itself
never had visibility into the losing chain at any point (confirmed peering
blind spot, `fork_count` stayed 0 throughout) — the only way this was
observable at all was the mempool.guide cross-check added specifically in
response to that gap.

**Data collection stopped 2026-08-09T10:16 UTC.** Final files:
`bip110_signaling_log.csv` (626 rows), `bip110_history.csv`,
`mempool_guide_comparison_log.csv`, `economic_signals_log.csv`,
this file.

---

## 2026-08-09T10:56 UTC — Ocean Pool mined blocks on BOTH sides of the split

**Observed (post-hoc, from the historical record after the fact):**

| Chain | Height | Pool | Sub-name |
|---|---|---|---|
| BIP-110 (losing chain) | 961632 | Ocean | Roughnecks |
| BIP-110 (losing chain) | 961633 | Ocean | Roughnecks |
| Legacy (winning chain) | 961634 | Ocean | Simple Mining |

Note height 961633 is the exact tip height the losing chain stalled at
permanently (see the 2026-08-09T10:16 UTC entry above) — Ocean/Roughnecks
mined the last block that chain ever produced.

**Why this matters:** this does not fit any of the three pool archetypes
the paper's mining-pool behavioral model assumes (committed / neutral
profit-maximizer / swing) -- all three assume a pool resolves to mining
*one* fork based on an ideology-vs-loss-tolerance calculation. A single
pool operator producing blocks on both chains within the same short window
is a distinct behavior: either a deliberate hedge, or -- more likely given
how Ocean is publicly known to operate -- a consequence of Ocean's
permissionless/decentralized template-selection design, where individual
sub-pools or miners connected through Ocean's infrastructure can each
choose their own block-construction policy independently. The differing
sub-names (Roughnecks vs. Simple Mining) support the latter reading: this
may not be one operator strategically hedging, but two independent
sub-groups under the same pool umbrella making genuinely different,
uncoordinated choices.

**Research implication:** the paper's pool-level unit of analysis (one
ideology/commitment per named pool) may be too coarse for pools with this
kind of internal architecture. Worth flagging explicitly as a limitation /
future-work item rather than folding silently into the existing
committed/neutral/swing typology -- this is a fourth, structurally
different behavior (intra-pool divergence) that the current model doesn't
represent at all.

---

## 2026-08-09T11:17 UTC — Ocean/DATUM client self-selection mechanism confirmed; BarefootMining fully non-signaling

**Source:** X post by `@boomer_btc` (self-identified as BarefootMining's
decision-maker), posted 2026-08-08T21:37 ET / **2026-08-09T01:37 UTC** —
i.e. shortly after the split at height 961632, well before the closing
summary logged above. First-person, self-reported statement, not
independently confirmed on-chain data — treat accordingly, unlike the
Ocean/Roughnecks entry above which was confirmed via direct coinbase-tag
comparison.

**What the post states:**
- Confirms the mechanism behind the intra-Ocean divergence noted in the
  entry above: Ocean's DATUM infrastructure lets each of its clients pick
  a side independently. Two parallel pools were stood up
  (`bip110.ocean.xyz` and `ocean.xyz`), and "each client is making their
  own decision" through DATUM.
- Per the poster, "slightly over half" of Ocean's aggregate client
  hashrate was directed at the BIP-110 side as of the post time —
  i.e. Ocean's client base was roughly split, and BIP-110-leaning, at that
  moment.
- **BarefootMining itself was not split.** The post states BarefootMining
  "has been mining on the non-signaling side" (legacy chain) in full —
  a single committed choice by one Ocean client, not a hedge across both
  chains. (Initial framing of this event as "Barefoot Mining split their
  hashrate across both forks" does not match the source; correcting that
  here.)

**Why this matters / tension with the closing-summary numbers:** the
2026-08-09T10:16 UTC entry above recorded network-wide pool signaling
collapsing toward ~0% by the new difficulty period. This post's claim of
"slightly over half" of *Ocean's* client hashrate on BIP-110, at a point
before that collapse, suggests Ocean's client base may have been a
concentrated outlier relative to the rest of the network's miners rather
than representative of the aggregate signal-rate trend — worth keeping in
mind when reading the network-wide `signal_pct` figures as a proxy for
"how miners in general felt" about BIP-110; at least one major pool's
client base looked very different from the aggregate at this point in the
timeline.

**Caveat:** single self-reported source, not cross-checked against
on-chain coinbase tags the way the Roughnecks/Simple Mining split was.
The "slightly over half" figure in particular is the poster's own
characterization of internal Ocean client data not independently
observable from outside. Treat as a economic/operator-statement data
point (comparable in evidentiary weight to an exchange announcement in
`economic_signals_log.csv`), not as confirmed on-chain fact.

---

## 2026-08-09T11:49 UTC — Post-hoc hashrate estimate for each chain (inferred, not directly measured)

**Important limitation up front:** neither `bip110_monitor.py` nor
`bip110_latest.json` ever captured raw hashrate or difficulty
(`getnetworkhashps` / `getmininginfo` were never called — confirmed by
grep of the monitor source and the JSON snapshot's key set). Everything
below is inferred after the fact from block-height timestamps in
`bip110_signaling_log.csv` (mynode, ~3 min polling) and
`mempool_guide_comparison_log.csv` (BIP-110 side, same-height hash
cross-check only, no `mediantime` captured), not measured directly. This
is estimation, not logged data.

**Legacy (majority) chain — `bip110_signaling_log.csv`:**

| | blocks | span | avg block time |
|---|---|---|---|
| Pre-fork (heights 961519-961631, same period) | 94 | 993 min | 10.56 min/block |
| Post-fork (heights 961632-961721) | 73 | 14.7 h | 12.10 min/block |

Naively, 12.10 vs 10.56 min/block implies the legacy chain retained only
~83% of pre-fork total network hashrate (i.e. ~17% went to the minority
chain). Statistical caveat: block intervals are exponentially distributed
(high variance, CV=1); against the null of "no hashrate lost" this slowdown
is only z ~= -1.6 (n=73) -- suggestive, not conclusive on its own.

**Minority (BIP-110) chain — `mempool_guide_comparison_log.csv`:** never
observed to move. Stuck at height 961633 continuously from the first
cross-check (2026-08-08T23:01:24 UTC) through the last
(2026-08-09T10:20:31 UTC) -- a confirmed **679-minute (11h19m) window with
zero blocks**, and the block may already have been sitting there when
logging started (no way to know its actual mine time from the data we
captured).

**Reconciling the two:** these are in tension if the naive legacy-chain
estimate (~17% to minority) is taken at face value -- that would predict a
minority block roughly every 58 minutes, making 11+ hours with zero blocks
a ~1-in-100,000 coincidence. Not plausible; the 17% figure is almost
certainly sampling noise from a small n. Solving the problem the other
way -- what hashrate fraction makes "zero blocks in a confirmed 679 min"
itself only a 5%/1% coincidence -- gives a tighter, more credible bound:

- **Minority chain hashrate <= ~4.4% of pre-fork total network hashrate at
  95% confidence, <= ~6.8% at 99%** (derived from
  `exp(-T*f/10) <= alpha` solved for `f`, `T` = 679 min).
- This is consistent with the ~2.6-2.7% pool-signaling rate already
  recorded in the 2026-08-09T10:16 UTC closing-summary entry, and *not*
  consistent with the naive 17% implied by the legacy-chain block-time
  ratio alone.

**Conclusion:** best estimate is that the legacy chain retained roughly
95%+ of pre-fork network hashrate post-fork, not ~83% -- the observed
12.10 min/block figure is more likely explained by ordinary Poisson
sampling noise over 73 blocks than by a large real hashrate loss. The
"zero blocks in 11+ hours" constraint is statistically far more powerful
than the legacy-chain block-time ratio for bounding the minority chain's
hashrate share, because exponential tail probabilities shrink fast --
worth remembering as a method note for any future live/simulated fork
where one side's block-discovery data is sparse: absence of blocks over a
known duration bounds the minority hashrate tighter than the majority
side's timing noise does.

---

## 2026-08-09T13:20 UTC — Ocean pool-level Eh/s figures corroborate the stall-phase mechanism

**Source:** X post by Tone Vays, posted 2026-08-09T08:32 ET /
**2026-08-09T12:32 UTC**, quoting/discussing `@ocean_mining` stats.
First-person social-media commentary, not on-chain data or an Ocean
official statement — same evidentiary tier as the BarefootMining entry
above, treat accordingly.

**Figures reported (Ocean pool only, not total network hashrate):**

| Phase | Legacy (Bitcoin) side | BIP-110 side |
|---|---|---|
| Pre-split | 34 Eh/s (peak 38) | — |
| During-split | 15.5 Eh/s | 14.5 Eh/s |
| Post-split | 16 Eh/s | 1.2 Eh/s ("Dead Endpoint") |

Poster's conclusions: ~6-8 Eh/s left the pool entirely between pre- and
during-split; the 14.5 Eh/s during-split BIP-110 figure was mostly rented
hashpower (attributed to `@Roughnecks110`) "mining at a loss"; the
remaining 1.2 Eh/s post-split continues mining the dead chain with zero
chance of reward.

**Why this matters — reconciling with the 2026-08-09T11:49 UTC entry
above:** these are Ocean-specific figures, not total network hashrate, so
they can't be directly converted to the same "% of pre-fork total network
hashrate" units used in that entry. But the *shape* of the two phases
maps cleanly onto what was statistically inferred there:

- **"During-split" (14.5 Eh/s on Ocean's BIP-110 side)** is presumably
  the window in which the minority chain was still occasionally finding
  blocks, up through height 961633.
- **"Post-split" (1.2 Eh/s, "Dead Endpoint")** is presumably the same
  window as the confirmed 679-minute, zero-new-blocks stretch recorded in
  `mempool_guide_comparison_log.csv` (2026-08-08T23:01 UTC onward) and
  used to derive the ≤~4.4% (95% CI) network-wide minority-hashrate bound.

If that phase mapping holds, this independently corroborates the
mechanism behind that bound: a large chunk of rented hashpower
(~13+ Eh/s per this report) walked away once it stopped finding blocks
profitably, which is exactly the kind of collapse that would turn
"occasionally finding blocks" into "zero blocks for 11+ hours." It does
not independently verify the *percentage* bound itself, since total
network hashrate in Eh/s was never captured (see the no-raw-hashrate
limitation noted throughout this file) — there's no way to convert 1.2
Eh/s into "% of network" without that denominator. Treat this as
qualitative corroboration of the story, not a quantitative check of the
95% CI figure.

**Caveat:** single-source, self-reported commentary (not an Ocean
official statement), no way to independently verify the Eh/s figures
against on-chain data with the tools in this directory.

---

## 2026-08-10 — Survival mechanism: full complexity analysis

This entry synthesises the analysis from multiple prior entries and maps it
against the sweep findings' theoretical treatment of the Difficulty Adjustment
Survival Window (SWEEP_FINDINGS.md §"Difficulty Adjustment Survival Window").
It documents three complexities that the sweep findings' formula understates,
all of which are illuminated by the live BIP-110 event.

### Recap of the mechanism (from sweep findings)

A minority fork can win not by having superior hashrate but by surviving long
enough to reach a difficulty adjustment that makes its blocks dramatically
cheaper to mine, then attracting a wave of opportunistic hashrate before the
majority chain can respond:

```
t=0  Fork splits at minority hashrate fraction f.  Blocks arrive at 1/f the
     target rate (e.g. f=0.25 → 4× slower).
t=1  Price begins to diverge but does not yet break committed pools.
t=2  After retarget_interval minority blocks, difficulty drops by ~(1-f).
     Block rate restored to target.
t=3  PROFIT SPIKE: opportunistic hashrate floods in, blocks arrive faster
     than target, chainwork accumulates rapidly.
t=4  If the spike arrives before the majority chain's next retarget, the
     minority fork overtakes cumulative chainwork and wins.
```

The survival window formula:

```
survival_window ≈ retarget_interval / f     (wall-clock time to first adjustment)
```

At f=0.044 (95th-percentile bound from the 679-minute zero-blocks observation)
and retarget_interval=2016 (Bitcoin mainnet):

```
survival_window ≈ 2016 / 0.044 × 10 min ≈ 458,000 min ≈ 318 days
```

Even at the 99th-percentile bound (f≤0.068):

```
survival_window ≈ 2016 / 0.068 × 10 min ≈ 296,000 min ≈ 206 days
```

The BIP-110 minority chain stalled permanently at height 961633 — one block
past the retarget boundary that began the new difficulty period. It never had
any realistic prospect of reaching its own first difficulty adjustment. This
event is a clean, if extreme, confirmation of the sweep findings' conclusion
that the survival mechanism does not fire in the realistic 2016-block regime
at low hashrate fractions.

### Complexity 1: position within difficulty period as a hidden parameter

The survival window formula assumes the fork starts a full retarget_interval
away from the minority chain's next difficulty adjustment. This is only true
if the fork occurs exactly at a retarget boundary — the worst possible case.

The BIP-110 fork split at height 961632, which **was itself a retarget
boundary**: the new difficulty period began at 961632, meaning the minority
chain started a full 2016 blocks from its next adjustment. This is the
maximum possible survival window for a given f, not a typical one.

Had the fork instead occurred near block 1950 within a difficulty period
(only 66 blocks remaining), the minority chain would have needed only 66
minority-chain blocks before difficulty relief — 30.6× less survival time
required. At f=0.044, that would be approximately:

```
66 / 0.044 × 10 min ≈ 15,000 min ≈ 10.4 days
```

Still long by operational standards, but qualitatively different from 318
days. Position within the difficulty period is effectively a hidden second
parameter in the survival window calculation, with a leverage factor of up to
2016 between best case (fork just before a retarget) and worst case (fork just
after a retarget).

**Implication for the model:** the sweep simulation always starts fresh, which
implicitly assumes the fork occurs at the beginning of a difficulty period —
the worst case for the minority chain. The survival window measured in
simulation is therefore a conservative (long) estimate of what a real fork
would face. Real forks that happen to split mid-period would have shorter
windows, making the mechanism more plausible at marginally higher hashrate
fractions.

**Implication for the real event:** the fork occurring immediately after a
retarget boundary was among the worst possible timings for the survival
mechanism to fire. It is not representative of expected timing.

### Complexity 2: two-phase hashrate collapse (speculative vs committed)

The sweep model treats pool decisions as static transitions from one fork to
another, driven by a price oracle comparison. The real event showed a
structurally different two-phase dynamic:

- **Phase 1 — speculative hashrate:** During the split (~14.5 Eh/s on
  Ocean's BIP-110 side per the Tone Vays report), a large fraction of the
  minority-chain hashrate was rented or ideologically motivated (attributed
  to Roughnecks/~13 Eh/s, characterised as "mining at a loss"). This
  hashrate was sufficient to find the two minority-chain blocks (heights
  961632 and 961633) but was economically unsustainable.
- **Phase 2 — collapse:** Once the rented/speculative hashrate withdrew, the
  remaining committed minority hashrate was ≤1.2 Eh/s (from the Tone Vays
  report), consistent with the ≤4.4% (95% CI) bound from the 679-minute
  zero-blocks window. The minority chain went dark.

The model's price oracle treats all pools as responding monotonically to
relative profitability. It does not represent the distinction between:
- speculative hashrate that briefly supports the minority chain regardless of
  economics (ideology + rented capacity), then evaporates
- residual committed hashrate that persists unprofitably

This two-phase pattern has a specific consequence for the survival mechanism:
a minority chain can receive a brief burst of high hashrate that produces its
first few blocks at near-normal speed, then collapse to near-zero before the
sustained rate needed to complete retarget_interval blocks is ever achieved.
The mechanism can appear to "start" (first blocks found quickly) while never
having a realistic path to completion.

**Implication for the model:** the survival window formula implicitly assumes
constant f throughout the window. Real hashrate is not constant; it typically
starts higher (speculative pile-in) and falls faster than the price oracle
predicts. The effective f for survival window purposes is the *sustained*
minority hashrate, not the peak.

### Complexity 3: intra-pool divergence as an unmodeled actor class

The model's pool behavioral typology (committed / neutral profit-maximizer /
swing) assigns one ideology and one chain commitment per named pool. The
Ocean/DATUM observation (see 2026-08-09T10:56 UTC and 2026-08-09T11:17 UTC
entries) introduces a fourth structural type: **pools with independent
client-level chain selection**.

Ocean's DATUM infrastructure allowed each connected client to choose their own
block template independently, resulting in two simultaneous sub-pools
(`bip110.ocean.xyz` and `ocean.xyz`) operating as genuine separate pools under
the same umbrella. The Roughnecks sub-pool mined the last two minority-chain
blocks; the Simple Mining sub-pool continued on the legacy chain without
interruption.

This behavior does not map onto any of the three modeled archetypes:
- It is not "committed to v27" (Ocean also produced legacy blocks)
- It is not "neutral profit-maximizer" (Roughnecks mined BIP-110 at a loss)
- It is not "swing" (the decision was not made at the pool level)

The real structural unit for a DATUM-style pool is the individual client
operator, not the pool umbrella. Hashrate that appears as a single named pool
in the model may in reality fragment along ideological lines within the pool's
client base, producing a pattern where the same pool produces blocks on both
forks simultaneously — something none of the three archetypes can represent.

**Implication for the model:** the pool-level unit of analysis is too coarse
for any large pool with permissionless or client-delegated template selection.
The current model's committed/neutral/swing typology should include a note
that it may undercount effective v27 committed hashrate (since some fraction of
nominally neutral pools may have committed clients within them), and may
overcount the discrete nature of pool switching decisions.

### What the live event confirms and does not confirm

| Question | Verdict | Evidence |
|---|---|---|
| Survival mechanism is real in model at 144-block retarget | Confirmed | sweep9 at t=8,106s |
| Survival mechanism fails at 2016-block retarget with f≈0.025 | Confirmed | minority chain stalled 11h+ |
| Position-within-period affects window width | Confirmed (analytically) | Fork at retarget boundary = worst case |
| Two-phase hashrate collapse (speculative→residual) | Observed qualitatively | Roughnecks 13 Eh/s → 1.2 Eh/s |
| Intra-pool divergence as a distinct actor class | Observed | Ocean Roughnecks vs Simple Mining |
| Fog-of-war assumption understates real cascade speed | Plausible, untested | Speculative hashrate present; mechanism never fired to test it |

The event did not test cases where the survival mechanism could plausibly
fire (f≥0.15, mid-period timing, sustained committed hashrate). It is
therefore strong negative evidence for the extreme-low-hashrate case but
does not constrain the moderate-hashrate cases that the sweep model
identifies as genuinely contested (pool_committed_split ∈ [0.20, 0.50],
economic_split ∈ [0.28, 0.78]).

### Cross-reference

- `SWEEP_FINDINGS.md` §"Difficulty Adjustment Survival Window": mechanism and formula
- `SWEEP_FINDINGS.md` §"Fog of War: Pool Information Uncertainty": assumed_fork_hashrate=50.0
- `tools/dataCollection/survival_mechanism_complexity.md`: extended analysis document
- `field_observations.md` 2026-08-09T11:49 UTC: hashrate bound derivation
- `field_observations.md` 2026-08-09T10:56 UTC: Ocean/DATUM intra-pool divergence
- `field_observations.md` 2026-08-09T13:20 UTC: Tone Vays Eh/s figures
