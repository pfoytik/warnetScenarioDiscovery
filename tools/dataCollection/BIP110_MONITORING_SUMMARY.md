# BIP-110 Flag Day — Data Collection Summary

Generated: 2026-08-09T11:49 UTC (data collection window: 2026-08-08T02:46 UTC
– 2026-08-09T10:20 UTC, ~31.6 hours)

This summarizes what was actually collected during the live BIP-110 UASF
flag-day event and the findings drawn from it, pulling together
`bip110_signaling_log.csv`, `bip110_history.csv`,
`mempool_guide_comparison_log.csv`, `economic_signals_log.csv`, and the
interpretive notes in `field_observations.md`. This is a summary of the
**live real-world event**, not the earlier simulation/sweep research
program (`../results/TEST_SUMMARY.md`, `../sweep/SWEEP_FINDINGS.md`).

---

## Data collected

| Source | Coverage | Notes |
|---|---|---|
| `bip110_signaling_log.csv` | 628 snapshots, ~3 min cadence, heights 961518–961721, 2026-08-08T02:46 UTC – 2026-08-09T10:20 UTC | Local node polling: height, period signaling counts, `fork_count`, peer count, external API signal %. Local block-by-block pool-tag signal scan (`signal_pct` column) was never populated in this run — 0 of 628 rows have it — so pool-level `signal_pct` comes only from the external API column and `bip110_history.csv`, not a local full-period scan. |
| `bip110_history.csv` | 1 period recorded (period 0, heights 961632–961719) | `--history` was only captured once, post-split: 0 of 88 blocks signaling. No pre-split period-level baseline was captured this way (see `ext_api_signal_pct` in the signaling log for that instead). |
| `mempool_guide_comparison_log.csv` | 225 snapshots, ~3 min cadence, 2026-08-08T23:01 UTC – 2026-08-09T10:20 UTC | External cross-check against mempool.guide's view of the BIP-110/v27 side. Only ever recorded a single height (961633) — this file's window starts *after* the split, not from block 961633's actual mine time. |
| `economic_signals_log.csv` | 8 entities, 15 logged observations, 2026-08-08T02:51 UTC – 2026-08-09T01:19 UTC | Manual weighted tracker for exchange/custodian stances (Binance, Coinbase, Kraken, Grayscale, Fidelity Digital, MicroStrategy, a mid-tier-exchange aggregate placeholder, and start9). |
| `field_observations.md` | 6 dated entries, 2026-08-08T23:12 UTC – 2026-08-09T11:49 UTC | Narrative/interpretive layer: chain-split confirmation, closing summary, Ocean/Roughnecks intra-pool split, BarefootMining/Ocean-DATUM X-post analysis, post-hoc hashrate estimate. |

**Not collected:** raw hashrate or difficulty (`getnetworkhashps` /
`getmininginfo` were never called — confirmed by source inspection).
Any hashrate figures below are inferred from block-interval timing, not
measured directly.

---

## Key findings

1. **A real chain split occurred at height 961633**, confirmed via
   same-height hash mismatch between the local node and mempool.guide
   (`mempool_guide_hash` ≠ `mynode_hash`), not merely differing tip
   heights.

2. **Clean legacy-chain win.** The minority (BIP-110/v27) chain produced
   its last block at height 961633 and then stalled permanently — zero
   new blocks in a confirmed 11h19m window before monitoring stopped. The
   legacy chain climbed normally from 961632 to 961721 (89 blocks) over
   the same ~14.7 h.

3. **Pool signaling collapsed to 0% after the split**, per
   `bip110_history.csv` (0 of 88 blocks in the post-split difficulty
   period), down from a steady ~2.5–2.7% (external API) through the prior
   period.

4. **Local node had a total peering blind spot on the losing chain.**
   `fork_count` never registered the real split (stayed 0 throughout the
   monitored window post-restart) — the only reason the split was
   detected at all was the mempool.guide cross-check. Early `fork_count`
   readings of 48 at the very start of the run (02:46–03:10 UTC) were
   stale orphan-tip accumulation from before a node restart, unrelated to
   the actual BIP-110 split, which happened later.

5. **Estimated hashrate split (inferred, not measured):** naive block-time
   ratio on the legacy chain (10.56 → 12.10 min/block pre/post-split)
   suggests ~17% of hashrate went to the minority chain, but that's not
   statistically reliable at n=73 and is contradicted by the "zero blocks
   in 11+ hours" observation. Solving from the stall duration instead
   gives a tighter, more credible bound: **minority chain hashrate ≤ ~4.4%
   of pre-fork network hashrate (95% confidence)**, consistent with the
   ~2.6–2.7% pool-signaling rate. Best estimate: legacy chain retained
   roughly 95%+ of pre-fork network hashrate, not ~83%.

   **Pool-level Eh/s numbers (single-source, self-reported — Tone Vays,
   X post 2026-08-09T12:32 UTC, citing `@ocean_mining` stats)** give a
   concrete, if unverifiable, sense of scale for one pool's contribution:

   | Phase | Legacy side | BIP-110 side |
   |---|---|---|
   | Pre-split | 34 Eh/s (peak 38) | — |
   | During-split | 15.5 Eh/s | 14.5 Eh/s (mostly rented, `@Roughnecks110`) |
   | Post-split | 16 Eh/s | 1.2 Eh/s ("Dead Endpoint," ~0% reward chance) |

   These are Ocean-only figures, not total network hashrate, so they
   don't independently verify the ≤4.4% network-wide bound above — but
   the during-split → post-split collapse (14.5 Eh/s → 1.2 Eh/s, as
   rented hash left once it stopped finding blocks) is a plausible
   mechanism for exactly the transition from "still occasionally finding
   blocks" (last one at 961633) to "zero blocks for 11+ hours" that bound
   was derived from. Qualitative corroboration of the story, not a
   quantitative check of the 95% CI figure.

6. **Ocean pool showed intra-pool divergence, not a single decision.**
   Post-hoc coinbase-tag inspection found Ocean/Roughnecks mining on the
   *losing* chain (961632, 961633) and Ocean/Simple Mining on the
   *winning* chain (961634) within the same short window — doesn't fit
   the paper's committed/neutral/swing pool typology, which assumes one
   ideology per named pool.

7. **Mechanism behind #6, per a self-reported X post (single source, not
   independently verified):** Ocean's DATUM infrastructure let individual
   clients pick a side independently via two parallel pools
   (`bip110.ocean.xyz` / `ocean.xyz`). The poster claimed "slightly over
   half" of Ocean's aggregate client hashrate went to BIP-110 — which, if
   accurate, makes Ocean's client base a concentrated outlier relative to
   the ~2.6% network-wide signal rate, not representative of it.
   BarefootMining itself (the poster's own company) was **not** split —
   it mined the non-signaling side exclusively.

8. **No economic-side support materialized.** Of 8 tracked entities
   (weight 30 total), only `start9` (weight 1) ever logged support; every
   major exchange/custodian checked (Binance, Coinbase, Kraken) remained
   silent through re-checks made during the live split itself. Weighted
   `economic_split`: 100% "active" (meaningless with zero oppose entries
   ever logged) / **3.3% "conservative"** (support weight over all
   tracked weight — the closer analog to the simulation's parameter).

**Overall read:** both layers — pool/hashrate commitment and economic
adoption — failed to build toward activation, and by a wide margin on
both axes simultaneously. This was not a close contest.

---

## Mapping to the research model

| Research parameter | Observed value | Source |
|---|---|---|
| `pool_committed_split` (signal rate) | ~2.5–2.7% pre-split → 0% post-split | `bip110_history.csv`, external API column in `bip110_signaling_log.csv` |
| `economic_split` (conservative) | 3.3% | `economic_signal_log.py summary` |
| Fork detection event | Yes — height 961633, confirmed via hash mismatch | `mempool_guide_comparison_log.csv`, field_observations.md 2026-08-08T23:12 UTC entry |
| Reorg / minority chain depth | 0 further blocks after the fork point (permanent stall, not a reorg) | `mempool_guide_comparison_log.csv` |
| Implied minority hashrate share | ≤ ~4.4% (95% CI), ≤ ~6.8% (99% CI) | field_observations.md 2026-08-09T11:49 UTC entry |
| Version mix / pool-level divergence | Ocean split across sub-pools (Roughnecks vs. Simple Mining); not representable in current committed/neutral/swing typology | field_observations.md 2026-08-09T10:56 UTC entry |

Both `pool_committed_split` and `economic_split` landed well below the
paper's inversion zone (~0.50–0.82) — this event sits in the
"clean legacy win" region, not the contested zone where pool commitment
becomes decisive.

---

## Simulation validation

`simData_ForkConfigure.png` is a screenshot of the decision-boundary
dashboard (1,048 scenarios, 76.0% CV accuracy) with its Economic Split /
Pool Committed Split sliders set as close as possible to the observed
values above.

**Slider values used: Pool Committed Split = 0.10, Economic Split =
0.25 — the floor of both sliders, not the true observed values
(~0.026 / ~0.033).** The dashboard's parameter grid doesn't extend that
low by design: the underlying sweep was constructed to explore
*contentious* fork scenarios, so it doesn't bother sampling the extreme
low-low corner where the outcome is trivially one-sided. The screenshot
is therefore the nearest point the model's explored grid can express, not
a direct plot of the real observed values — an important distinction for
how this validation claim should be read.

**Model output at that floor position:** v26 Dominant, 60% confidence
(v27 Dominant 28%, Contested 13%); nearest-scenario metrics show v27
Final HR 0.0%, Cascade Time none, Econ Switch No, Peak Price Gap 0.0%.

**Reading the result:** the model correctly predicted the actual outcome
(clean legacy/v26 win) even at its floor corner. Since both observed
values sit *below* the grid's floor in the same direction the model
already favors v26 (and, per the sweep design, going lower would only
push the prediction further toward v26 dominance, not reverse it), 60%
confidence at the floor is best read as a **lower bound** on what the
model would have predicted at the true observed values, not the model's
actual confidence at the real operating point. This is directional
validation — right outcome, right monotonic trend — not a precise
quantitative match, because the true observed point falls outside the
range the simulation was built to resolve.

---

## Data quality / limitations

- No raw hashrate/difficulty ever captured — all hashrate figures here are
  inferred from block-interval timing, with wide statistical uncertainty
  on the legacy-chain side (n=73 blocks) and no timestamp at all for the
  minority chain's last block (only a same-height hash comparison).
- Local `signal_pct` (full block-by-block pool-tag scan) was never
  populated in the CSV — every figure above relies on the external API or
  `--history`'s headers-only scan instead.
- `fork_count` from the local node is not trustworthy as a detection
  signal for this event — it had a confirmed peering blind spot on the
  actual losing chain the entire time.
- The Ocean/DATUM split-hashrate figures ("slightly over half") are
  single-source, self-reported (a company owner's X post), not
  independently confirmed the way the Roughnecks/Simple Mining coinbase
  tags were.
- `mempool_guide_comparison_log.csv` monitoring began after the split had
  already happened, so the true mine time (and thus true stall duration)
  of the minority chain's last block is a lower bound, not exact.
- The simulation dashboard's parameter grid floor (0.10 / 0.25) is above
  the true observed values (~0.026 / ~0.033), since the sweep was
  designed to explore contentious scenarios rather than one-sided
  blowouts — the validation screenshot is the nearest expressible grid
  point, not a direct plot of the real numbers.
- The Ocean pool-level Eh/s figures (finding #5) are single-source,
  self-reported commentary (Tone Vays quoting `@ocean_mining` stats), not
  an Ocean official statement or on-chain-verifiable data, and cannot be
  converted to "% of total network hashrate" since total network Eh/s was
  never captured.
