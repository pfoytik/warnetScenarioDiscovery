# Writing Plan: Quantifying Bitcoin Network Resilience Through Critical Scenario Discovery

**Created:** April 9, 2026  
**Workshop:** University of Wyoming BRI — July 13–17, 2026  
**Data lock:** April 14, 2026  
**Rough draft target:** May 2, 2026  
**Send to co-authors:** May 16, 2026

---

## Current Assets

| Document | Status |
|----------|--------|
| `docs/Results_Section_Skeleton_v4.md` | Detailed skeleton with numbers and partial prose throughout |
| `Methodology.md` | Full draft — needs minor updates |
| Abstract | Complete |
| `docs/Boundary_Fitting.md` | All Phase 2 numbers ready to transcribe |
| `docs/phase3_results.md` | Phase 3 lite-network findings |
| `tools/discovery/output/user_prim/user_prim_report.md` | User-PRIM analysis complete |

**Phase 3b (lhs_2016_full_phase3, 300 scenarios, full 60-node network):** currently running on large servers. Expected complete ~April 11. Results gate Sections 4.9–4.10.

---

## Section Writing Order

### Phase A — Now through April 11
*Write while Phase 3b computes. All sections below are fully data-locked.*

---

#### 1. Section 4.2 — Parameter Causality: Separating Signal from Confound
**Priority:** Start here. This is the spine — every later finding depends on the confound-elimination logic.  
**Data source:** Skeleton Tables 2 and 3 (filled), targeted_sweep2, targeted_sweep4, targeted_sweep5, lhs_2016_6param  
**What to write:** Narrative walking through the elimination sequence in chronological discovery order:
- Early LHS showed hashrate_split as dominant predictor (r=+0.83) — artifact of sampling
- Isolation grid (targeted_sweep2) showed identical outcomes across all hashrate levels
- User parameters (targeted_sweep5): zero correlation across full range
- Pool neutral fraction (targeted_sweep4): controls intensity only, not outcome
- pool_profitability_threshold and solo_miner_hashrate: confirmed non-causal at 2016-block (lhs_2016_6param)
- Result: three causal parameters remain — pool_committed_split, economic_split, pool_ideology_strength×pool_max_loss_pct interaction

**TODO tags to resolve:** Stochastic variance paragraph (balanced_baseline variance number needed)  
**Estimated time:** 1 day

---

#### 2. Section 4.3 — The Foundry Flip-point (pool_committed_split)
**Priority:** Core finding. Write immediately after 4.2; they share the pool-ideology-as-gatekeeper framing.  
**Data source:** targeted_sweep1, econ_committed_2016_grid, lhs_2016_6param threshold ~0.346, lhs_2016_full_parameter threshold ~0.25  
**What to write:**
- The non-convex decision boundary: pool_committed_split ~0.214 threshold at econ=0.78
- Mechanism: Foundry USA (30% hashrate, ideology=0.6, max_loss=12%) is the pivotal actor
- Below threshold: committed miners absorb losses; neutral pools follow price → v26 wins
- Above threshold: committed miners maintain v27 hashrate long enough for price oracle to cascade
- committed_split × econ interaction is synergistic (+1.231 logistic coefficient), not additive
- Inversion zone: high committed_split + low econ_split → v26 wins despite pool commitment (reverse cascade)

**Subsections to include:**
- 4.3.1 The committed pool threshold
- 4.3.2 Mechanism: ideology strength × loss tolerance interaction (`max_acceptable_loss = ideology × max_loss_pct`)
- 4.3.3 The inversion zone (non-convex boundary)
- 4.3.4 Economic override (econ ≥ 0.82: threshold becomes irrelevant, targeted_sweep6)

**Estimated time:** 1.5 days

---

#### 3. Section 4.8 — Phase 2: Boundary Fitting
**Priority:** Mechanical — mostly transcribing numbers from `docs/Boundary_Fitting.md`. Good momentum section.  
**Data source:** `tools/discovery/fit_boundary.py` output, `tools/discovery/output/2016/`, `docs/Boundary_Fitting.md`  
**What to write:**
- RF importance table: 144-block (econ=77.2%, committed=11.3%) vs 2016-block (committed=52.8%, econ=20.2%)
- RF OOB accuracy: 80.0% (144-block), 83.2% (2016-block)
- Logistic regression equation with interaction term
- PRIM uncertainty box: econ [0.28, 0.78], committed [0.15, 0.53], ideology [0.44, 0.80], max_loss [0.16, 0.40]
- Contentiousness: 2× higher at 2016-block (mean 0.271 vs 0.132)
- High-chaos PRIM box: committed [0.25, 0.57], econ [0.34, 0.78]

**Estimated time:** 1 day

---

#### 4. Section 4.11 — User-PRIM: Scenario Potential for User Nodes
**Priority:** Write now while methodology is fresh. Small section, data complete. Most cuttable if schedule slips — finish it early so cutting it later costs nothing.  
**Data source:** `tools/discovery/output/user_prim/user_prim_report.md`, `user_prim_results.json`  
**What to write:**
- Weight ratio: W_users/W_total = 0.1688/370.90 (2197:1) sets a structural ceiling on user pivotality
- User-PRIM box: econ [0.49, 0.77], committed [0.20, 0.50], ideology [0.47, 0.52], max_loss [0.25, 0.26] — 58 scenarios (9.7%)
- Bias ratio: 1.256 — near unity, does NOT strongly concentrate user-pivotal scenarios
- Comparison: standard PRIM bias ratio 0.975 (baseline)
- Interpretation: null result. User nodes cannot be structurally pivotal at any tested parameter combination. Pool and economic actors dominate 2016-block outcomes regardless of user ideology or switching behavior.
- Frame positively: validates the Scenario Potential framework — correctly identifies a structural null rather than generating false positives. Also has governance implications for UASF narratives.

**Estimated time:** 0.5 days

---

### Phase B — April 12–18
*After Phase 3b data arrives (~April 11). Analyze first, then write.*

**Analysis steps before writing:**
1. Rsync results from both servers (commands in `tools/sweep/lhs_2016_phase3/RUN_COMMANDS.md`)
2. Run `4_analyze_results.py` and `5_build_database.py`
3. Run `fit_boundary.py --regime 2016` on combined Phase 3 + Phase 3b dataset
4. Key questions to answer before drafting:
   - Does pool_committed_split threshold hold at ~0.296 on full network?
   - Does pool_max_loss_pct ≤ 0.217 adoption threshold shift?
   - Does the 81% no-switch rate within v27-dominant replicate?
   - Does the two-layer decoupling persist?

---

#### 5. Section 4.9 — Phase 3: The Two-Layer Outcome Structure
**Priority:** Headline result of the paper. Needs careful prose — this is what workshop attendees remember.  
**Data source:** lhs_2016_phase3 (300 scenarios, lite), Phase 3b cross-network validation  
**What to write:**
- Layer 1: Hashrate war outcome — controlled by pool_committed_split (threshold ~0.296 lite net, TBD full net)
- Layer 2: Economic adoption — controlled by pool_max_loss_pct (≤ 0.217 → full_switch); independent of Layer 1
- Decoupling: 81% no-switch within v27-dominant scenarios shows hash-war and economic migration are not coupled
- Economic switch lag: ~1914s after cascade completes at 2016-block
- Full_switch rate: 46% of scenarios at 2016-block; econ switch lag ~1914s post-cascade
- Contested scenarios (18.6%): characterize parameter space — what makes outcomes indeterminate?

**Subsection structure:**
- 4.9.1 The two-layer structure: definition and evidence
- 4.9.2 Layer 1 decision boundary (pool_committed_split threshold)
- 4.9.3 Layer 2 economic adoption threshold (pool_max_loss_pct ≤ 0.217)
- 4.9.4 Decoupling evidence: Layer 1 outcome does not predict Layer 2 outcome

**Estimated time:** 1.5 days

---

#### 6. Section 4.10 — Phase 3b: Cross-Network Validation
**Priority:** Closes the main methodological gap (lite vs full network equivalence).  
**Data source:** Phase 3b results (full 60-node network, 300 scenarios)  
**What to write:**
- Does the two-layer finding replicate on the full network?
- Quantitative comparison: threshold values, switch rates, cascade timing (lite vs full)
- If thresholds shift: characterize how and why (individual entity representation vs aggregate)
- If thresholds hold: state that two-layer structure is network-scale invariant

**Estimated time:** 1 day (after data is in hand)

---

#### 7. Section 4.4 — Regime Comparison: economic_split at 144-block
**Note:** Write after Phase 3b because you can cross-reference 4.9/4.10 results directly.  
**Data source:** Phase 2 RF importance (77.2% at 144-block), lhs_144_6param, targeted_sweep1 vs econ_committed_2016_grid  
**What to write:**
- At 144-block: economic_split is dominant (77.2% RF importance); pool_committed_split secondary (11.3%)
- At 2016-block: rank reversal — pool_committed_split dominant (52.8%), economic_split drops to 20.2%
- Mechanism: survival window length determines which signal locks in first
- Quantization caveat for lite network (all econ [0.30, 0.80] → same 1 econ node on lite net — not a real finding)
- Regime comparison is valid only on full-network data (696 scenarios from Phase 2)

**Estimated time:** 1 day

---

#### 8. Section 4.5 — The Difficulty Adjustment Survival Window
**Note:** Can be drafted earlier (mechanism doesn't change), but write after 4.3 and 4.4 so you can forward-reference the dynamics correctly.  
**Data source:** Conceptual (from scenario script logic) + hashrate_2016_verification timing data  
**What to write:**
- Mechanism: minority chain's difficulty adjusts down, equalizing block rate before economic cascade resolves
- Survival window length = f(retarget_interval, initial_hashrate_deficit) — longer at 2016-block
- Why hashrate is non-causal: difficulty oracle eliminates the initial advantage before price cascade settles
- Hashrate parity danger window: intermediate v27 hashrate (35–45%) is WORSE than low or high at econ=0.50 at 2016-block
  - At 35–45%: Foundry's accumulated loss crosses 12% tolerance within one retarget cycle → forced switch to v26
  - At 15–25% and 55–65%: loss accumulates more slowly or is offset by neutral miners → persistent split
- Governance implication: acquiring moderate v27 hashrate (35–45%) without sufficient economic support is worse than not acquiring it at all

**Estimated time:** 1 day

---

### Phase C — April 19 – May 2
*Complete rough draft of all remaining sections.*

---

#### 9. Section 4.6–4.7 — Cascade Dynamics and Real-World Implications
**Data source:** Cascade timing data across sweeps, price divergence sensitivity sweep  
**What to write:**
- Cascade signatures: what does a pool cascade look like in the simulation? Timing, reorg patterns.
- Price divergence dynamics: ±10% cap binds (3 v26 wins), ±30% maximum stall, ±40% hardware artifact
- Three monitoring questions for real-world governance: what indicators predict fork resolution?
- The econ_lag (~1914s at 2016-block, ~4300–5000s at 144-block) as observable signal

**Estimated time:** 2 days

---

#### 10. Section 5 — Discussion
**Data source:** `result_hashrateArbitrage.md` + full results picture  
**Write after:** All Section 4 subsections are drafted  
**What to write:**
- Two-layer structure and its implications for UASF narratives: "economic majority" and "hashrate majority" are independent conditions requiring separate analysis
- Hashrate arbitrage and the difficulty adjustment as the unifying mechanism across all findings
- User-PRIM null result: structural implications for governance — individual retail behavior doesn't shift outcomes
- Model limitations: ±20% price cap conservatism, static topology (no peer-to-peer topology effects), fog-of-war (actors have imperfect information), custody duplication in econ_f
- Future work: dynamic topology, better price models, full-network user node variation

**Estimated time:** 3 days

---

#### 11. Section 2 — Background
**Write after:** Results and Discussion are drafted (so you know what to motivate)  
**What to write:**
- Bitcoin consensus basics: PoW, longest chain, orphan blocks
- Soft fork activation: BIP process, UASF history, the 2017 SegWit activation as reference case
- Related work: ~5–10 citations (Nakamoto 2008, BIP docs, Bryant & Lempert 2010, Foytik et al. TRB 2026, relevant game theory / fork dynamics literature)
- Scenario discovery methodology: Z-PRIM / Scenario Potential framework origin

**Estimated time:** 2 days

---

#### 12. Section 6 — Conclusion
**Write after:** Discussion  
**What to write:**
- Summary of three contributions: (1) causal variable identification, (2) two-layer outcome structure, (3) Scenario Potential as null-result validator
- What this means for Bitcoin governance practitioners
- Future work agenda

**Estimated time:** 1 day

---

#### 13. Section 1 — Introduction
**Write last.** The intro makes a promise the paper keeps — only write it once you know exactly what the paper delivers.  
**What to write:**
- Problem: Bitcoin governance is contested; fork outcomes appear unpredictable
- Research gap: no quantitative simulation-based analysis of parameter sensitivity across governance actors
- Contributions: list the three locked findings
- Paper organization: one sentence per section

**Estimated time:** 2 days

---

#### 14. Section 3 — Methodology (updates only)
**Status:** Full draft exists in `Methodology.md`  
**Updates needed:**
- Add regime separation motivation: why two retarget intervals? (Currently missing — should appear in experimental design subsection)
- Add lite-network quantization caveat: economic node assignment is discrete on 25-node lite network; economic_split is effectively constant across 87% of lite-network Phase 3 scenarios
- Update Section 3.8 to match actual pipeline as executed (steps 1–4 + 5_build_database.py + fit_boundary.py)
- Interleave these updates as breaks between longer writing sessions rather than treating as a standalone block

**Estimated time:** 1 day total (spread across multiple sessions)

---

## Full Schedule

| Date | Task |
|------|------|
| April 9–10 | Section 4.2 (Parameter Causality) |
| April 10–11 | Section 4.3 (Foundry Flip-point) |
| April 11 | Section 4.8 (Boundary Fitting) |
| April 11 | Section 4.11 (User-PRIM null result) |
| April 11–12 | Collect + analyze Phase 3b results |
| April 12–13 | Section 4.9 (Two-Layer Structure) |
| April 13–14 | Section 4.10 (Phase 3b Cross-Network) |
| April 14–15 | Section 4.4 (Regime Comparison) |
| April 15–16 | Section 4.5 (Survival Window + Danger Window) |
| April 16–18 | Section 3 updates; buffer |
| April 19–20 | Section 4.6–4.7 (Cascade Dynamics) |
| April 21–23 | Section 5 (Discussion) — 3 days |
| April 24–25 | Section 2 (Background) |
| April 26 | Section 6 (Conclusion) |
| April 27–28 | Section 1 (Introduction) |
| April 29 – May 2 | Buffer + light revision pass |
| **May 2** | **Rough draft complete** |
| May 3–9 | Generate all figures |
| May 10–16 | First full revision pass |
| **May 16** | **Send to co-authors** |

---

## Figures Needed (generate May 3–9)

| Figure | Data source | Section |
|--------|-------------|---------|
| P(v27_wins) heatmap — economic_split × pool_committed_split | Phase 1 + Phase 3b combined | 4.10 — primary result |
| Foundry flip-point schematic (two-panel: commit=0.20 vs 0.30) | Conceptual | 4.3.2 |
| Decision surface peeling trajectory (PRIM) | `tools/discovery/output/2016/` | 4.8.3 |
| Two-layer outcome diagram | Conceptual + Phase 3 data | 4.9 |
| Contentiousness score distribution by outcome type | Phase 3 sweep_data.csv | 4.9 |
| Survival window timeline (144-block vs 2016-block) | Conceptual | 4.5.1 |
| User-PRIM SP_user distribution + box | `tools/discovery/output/user_prim/` | 4.11 |

---

## What Gets Cut If Schedule Slips

**Cut first:**
- Section 4.11 (User-PRIM) → 1 paragraph in Discussion
- Section 4.7 (Real-world implications) → merge into Discussion

**Cut second:**
- Scenario archetype clustering → cite as future work
- Full sensitivity table with ∂P/∂param values

**Never cut:**
- Section 4.3 (Foundry flip-point and inversion zone)
- Section 4.9 (two-layer finding from Phase 3)
- Section 4.5 (difficulty adjustment survival window + hashrate parity danger window)
- P(v27_wins) heatmap figure

---

*Last updated: April 9, 2026*
