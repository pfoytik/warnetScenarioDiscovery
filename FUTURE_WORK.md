# Future Work

Tracks candidate extensions to the fork-resolution research program
(arXiv:2608.05461, *"Quantifying Bitcoin Network Resilience Through
Critical Scenario Discovery"*), informed by the paper's own stated
extensions (`docs/section_7_discussion.md` §7.6, and the paper's closing
Future Work paragraph) plus what the live BIP-110 flag-day monitoring
(`tools/dataCollection/`) has since confirmed or ruled out empirically.

---

## Priority: Difficulty Adjustment Survival Window deep-dive

The current paper introduces the survival window mechanism (§`sec:window`)
as one finding among several. A dedicated follow-up study focused
specifically on this mechanism has the most unresolved, genuinely open
questions of any extension currently identified.

### 1. Hashrate Parity Danger Window — precise boundary mapping

`docs/section_4_5_survival_window.md` §4.5.3 identifies a non-monotonic
zone at 2016-block retarget, economic parity: intermediate v27 hashrate
(35–45%) is *worse* for v27 than either lower or higher hashrate, because
it accumulates a decisive v26 block-length lead fast enough to break
Foundry's loss tolerance, but not fast enough to resist that lead itself.
§4.5.4 confirms this is a 2016-block-only phenomenon (the window closes
before loss accumulation matters at 144-block).

**Open:** the danger window's edges (35–45% hashrate, `econ ≥ 0.55`) have
only been located approximately. A dense LHS or targeted grid inside
`hashrate_split ∈ [0.25, 0.55] × economic_split ∈ [0.45, 0.65]` at
2016-block retarget would pin down the actual boundary shape — is it a
sharp cliff or a gradient, and does it hold across different
`pool_committed_split` / ideology configurations?

### 2. Reversal-risk / hashrate-arbitrage window — currently just a claim

The paper states: *"the interval immediately preceding the first
difficulty adjustment [is] the highest-risk window for rapid reversal...
publicly observable from block-production rates."* This has never
actually been tested against data — it's a mechanism-derived hypothesis,
not a validated result.

**Open:** design scenarios that specifically probe this window — does
neutral/opportunistic hashrate actually flow back toward a chain in the
run-up to its retarget, and is the effect detectable from
publicly-observable block-production-rate data alone (i.e., without
knowing the underlying pool-decision parameters)? This is the piece most
directly testable against real monitoring data going forward, since it's
framed as an operationally observable signal.

### 3. Uncapped / larger price-divergence cap

Flagged in both the paper's Limitations and §7.6 as a priority: the
current ±20% cap "does not capture the extreme divergence of real events
(BCH/BTC, BCH/BSV reached 80–95% over months)," and under larger
divergence "hashrate suddenly [becomes] causal in a way the model does
not capture."

**Open:** rerun key survival-window scenarios (sweep9/11-style
configurations) with the cap relaxed toward the real BCH/BSV range, to
test whether — and at what divergence level — hashrate stops being
non-causal.

### 4. Dynamic / anticipatory pool strategy

§7.6: replacing the current conservative assumption (pools do not
anticipate the retarget arbitrage window) with pools that explicitly time
switches around it. The paper's own assessment: *"the simulation likely
underestimates the speed and sharpness of real-world cascades near
retarget epochs."*

**New since the paper:** the live BIP-110 event gives a real, if
single-source, calibration point for this — the Tone Vays/Ocean report
(`field_observations.md`, 2026-08-09T13:20 UTC entry) showing ~13 Eh/s of
rented hashpower actively mining the minority side at a loss before
withdrawing once it stopped paying off. That's real opportunistic-hashrate
behavior, not price-oracle-mediated — a concrete target to calibrate a
dynamic pool-strategy model against, where the current work only had the
144-vs-2016-block simulation contrast to reason from.

### Deprioritized: sub-10% hashrate sweep

§7.6 originally listed this as a priority ("the survival window argument
predicts a failure boundary below approximately 10%"). **Recommend
dropping it from the priority list.** Two independent lines of evidence
now bracket this question from both sides without requiring more
simulation:

- `targeted_sweep11` (sweep data): 20.5% hashrate, dies at 197/2016 blocks,
  no resurrection, deterministic v26 win.
- Live BIP-110 event: ≤4.4% hashrate (95% CI), dies at 1 block past the
  fork point, permanently stalled — `BIP110_MONITORING_SUMMARY.md`.

Both converge on "decisively non-contentious" from opposite ends of the
sub-25% range. Running dedicated sub-10% sweeps would very likely just
reconfirm this rather than surface a new contentious regime — the
research value isn't there. Worth stating as an already-answered question
(citing sweep11 + the live event as converging evidence) rather than
re-running it.

---

## Priority: Richer price-formation model — influencer/FUD sentiment and futures markets

Motivation for treating this as a priority rather than a minor add-on:
`economic_split` is the single most important causal parameter found
anywhere in this research program (52.8% RF importance in the BCAP
checklist ranking, up to 60% in the full-network 2016-block LHS —
`docs/BCAP_Alignment.md` §9.1). The current model's treatment of the
*price* that underlies that parameter is comparatively thin, so
strengthening it bears directly on the finding that matters most.

**Current limitation (`docs/BCAP_Alignment.md` §9.5):** in the existing
model, fork price divergence is a pure *output* of the economic cascade,
not an input to it — the causal chain is fixed as
`economic node adoption → price divergence → pool profitability signal →
pool switching`. Derivative/futures market prices are explicitly
characterized as a "lagging confirmation signal," reflecting decisions
already made rather than shaping them. The one documented exception is
at the ESP (E≈0.74), where the price signal becomes self-reinforcing —
but that's an emergent property of the existing custody-weighted model,
not a distinct sentiment or speculative channel. There's currently no
mechanism by which sentiment, hype, or speculative positioning could move
price *ahead of* actual custody-holder decisions.

**Proposed extensions:**

1. **Influencer/media sentiment actor.** BCAP describes an influencer
   stakeholder class (in the spirit of the media-sentiment signal already
   referenced in §9.5) whose output — FUD or hype — isn't currently
   represented as its own channel at all; the model only has the static,
   custody-weighted `economic_split` term. Adding an exogenous,
   time-varying sentiment shock (independent of actual custody movement)
   would let the study ask: can a sentiment shock alone trigger or delay
   a cascade that the underlying custody fundamentals wouldn't have
   produced on their own? That's a genuinely different question from
   anything the current price model can answer, since sentiment and
   custody-weighted adoption are conflated into a single static term
   today.

2. **Futures/derivatives market as a price-discovery mechanism.**
   Model a forward-looking futures price for each fork's token,
   separate from the spot/custody-weighted price, that can itself feed
   back into pool profitability calculations and economic-node switching
   thresholds. This directly tests whether futures markets can convert
   price from the "lagging confirmation" role §9.5 currently assigns it
   into a genuine leading indicator — effectively asking whether the
   ESP self-reinforcing transition (currently an emergent, fundamentals-
   only phenomenon) can be pulled earlier, delayed, or falsely triggered
   by speculative positioning ahead of real custody decisions.

**Calibration target:** real futures/derivative markets existed on major
exchanges during the 2017 BCH/BTC split, giving an empirical precedent
for both magnitude and timing — comparable in spirit to how the uncapped
price-divergence item above uses the real BCH/BSV divergence record as a
calibration target.

**Relationship to other items in this document:** complementary to, not
overlapping with, the survival-window and consensus-code priorities
above — this one is about *how price itself forms*, not about hashrate
or connectivity dynamics. Given `economic_split`'s outsized causal weight
throughout the existing findings, a sentiment/futures-aware price model
is arguably the highest-leverage single change available for a second
iteration of this work, since it strengthens the input that already
drives most of the outcome variance rather than adding a new peripheral
mechanism.

---

## Secondary: Scenario archetype clustering

§7.6: unsupervised clustering of the Phase 3 dataset (300 scenarios) by
full dynamic trajectory rather than final outcome, to identify qualitative
fork archetypes (fast-resolving, prolonged-contested, oscillating) beyond
the binary v27/v26 classification. Lower priority than the survival-window
items above — doesn't depend on new data collection, could be run directly
against existing Phase 3 output whenever there's bandwidth.

---

## Program-level: the two already-announced follow-up studies

The paper's closing section states this is "the first of three planned
contributions in a Warnet-based critical-scenario-discovery program":

- **Second study:** apply the same PRIM-based methodology to the full
  space of Bitcoin node configuration — version mix, mempool policy,
  network policy, resource constraints — to discover which combinations
  produce critical network behavior independent of fork governance.
  Unchanged by anything in this document — listed here for completeness,
  not re-scoped.
- **Third study:** real consensus-code fork implementation — see below.

### Third study, expanded: implement the fork in node software, not the orchestrator

**Current limitation (`Methodology.md` §3):** the "soft fork" in every
sweep so far is commander-scripted, not consensus-enforced. Nodes are
split into two disconnected islands at startup (cross-partition P2P
connections blocked at launch); the asymmetric validation rule that
defines a soft fork (v26 accepts v27 blocks, v27 rejects v26 blocks) is
asserted via a config flag (`accepts_foreign_blocks: true/false`), and
v27 blocks are relayed to the v26 island by the commander explicitly
calling `submitblock` on a designated bridge node. Every node runs real
`bitcoind`, but the fork topology and the block-acceptance asymmetry are
both imposed from outside the node software, not produced by it.

**Proposed direction (your framing):** implement the actual differing
validation rules directly in the full node software — a real soft-fork
rule change (in the spirit of an actual BIP-9/version-bits deployment,
not a boolean flag) built into the `bitcoind` codebase itself — and run
all nodes on one real, unpartitioned P2P network. Let the fork (or its
absence) emerge from genuine block validation and gossip propagation,
rather than from the commander deciding who talks to whom and which
blocks get forwarded where.

**What this changes mechanically:**

| | Current (commander-orchestrated) | Proposed (consensus-enforced) |
|---|---|---|
| Fork topology | Two islands, disconnected at launch | Single connected network, no artificial partition |
| Rule asymmetry | `accepts_foreign_blocks` config flag | Real validation code path in the node |
| v27→v26 block relay | Commander calls `submitblock` explicitly | Organic P2P gossip |
| Divergence emerges from | Script logic | Actual peer-to-peer consensus behavior |
| Connectivity/topology | Fixed, clean two-island graph | Tunable — a genuine input variable |

**Why this matters beyond realism for its own sake:** with topology
fixed and clean in the current model, gossip-network structure can't be
studied as a variable at all — there's no eclipse attack, no propagation
delay heterogeneity, no orphan-race sensitivity to peer graph shape, none
of what the Erlay and eclipse-attack literature is actually about. A real
P2P implementation makes connectivity graph shape (peer count, topology,
latency distribution) a first-class input alongside the existing
economic/pool parameters — this is what the paper's own roadmap line
means by "connecting these fork-resolution findings to the
connectivity–security questions the Erlay and eclipse-attack literature
identifies as open." It's not possible to ask those questions in the
current partition-controlled setup regardless of how many more sweeps run.

It would also let the **survival-window and danger-window findings above
be re-tested under real propagation dynamics** rather than the commander's
instantaneous, idealized block relay — a natural second phase once the
consensus-code implementation exists, not a separate effort.

**Why this is its own study, not a sweep extension:** it requires patching
`bitcoind`'s actual validation logic (a real soft-fork deployment
mechanism, not a config flag), rebuilding node images around that patch,
and removing fork/partition control from the commander entirely — a
different order of engineering effort than adding sweep parameters,
consistent with the paper treating it as the third, separate contribution
rather than an extension of this one.

---

## What's already in hand for the survival-window follow-up

- `tools/sweep/SWEEP_FINDINGS.md` — sweep8 (duration artifact), sweep9
  (mechanism firing, t=8,106s), sweep11 (mechanism failing, 197/2016
  blocks) as the core threshold comparison.
- `tools/dataCollection/field_observations.md` and
  `BIP110_MONITORING_SUMMARY.md` — the live real-world validation case,
  including the Ocean/DATUM pool-split mechanism and the Tone Vays
  pool-level Eh/s figures, both useful as calibration targets for item 4
  above.
- `docs/section_4_5_survival_window.md` — the detailed technical writeup
  behind the paper's condensed §`sec:window`, including the danger-window
  derivation to build item 1 on.
