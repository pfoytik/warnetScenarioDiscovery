# BCAP Framework Alignment — Quantified Results

**Author:** Peter Foytik
**Date:** June 2026
**Status:** Draft — for BRI Workshop submission reference

This document maps the Blockchain Consensus Analysis Protocol (BCAP) framework to the quantified simulation findings from the Warnet fork scenario discovery project. Where BCAP identifies qualitative dynamics, governance risks, and stakeholder roles, this project provides the first structural quantification of the thresholds, parameter sensitivities, and causal mechanisms underlying those dynamics.

---

## 1. Economic Node Definition and Weight

**BCAP:** Economic nodes derive power and influence proportional to the frequency and volume of payments received. Key entities include cryptocurrency exchanges, payment processors, custody providers, and large merchants. Their governance powers include defining which fork is Bitcoin by choosing which software version to run, rejecting invalid blocks, listing or delisting fork markets, and selling fork coins on behalf of users without their permission.

**Simulation alignment:**

The model represents 24 economic nodes across five roles (`major_exchange`, `exchange`, `institutional`, `payment_processor`, `merchant`), calibrated to realistic Bitcoin custody and volume figures. Consensus weight is computed as `(0.7 × custody_btc + 0.3 × daily_volume_btc) / 10000`, reflecting custody as the primary governance signal.

The custody-first weighting is justified by BCAP's own power enumeration: the ability to "sell fork coins on behalf of users without their permission" is a pure custody function — an exchange determines which fork's coins to credit users based on which chain it validates, independent of transaction volume. Sensitivity analysis confirms that varying the custody/volume ratio from 1.0/0.0 to 0.0/1.0 does not change categorical weight shares or outcome thresholds, because major exchanges hold both the highest custody and the highest volume in the network (rank correlation ≈ 0.94).

**Quantified finding:** Economic nodes collectively hold 96.5% of total consensus weight (370.7 of 384.0 total weight), with the top 4 major exchange nodes alone controlling 66% of economic weight. This structural concentration means that fork outcomes are determined by a small number of large actors, not aggregate small-actor behavior — consistent with BCAP's emphasis on major exchanges as the decisive economic governance class.

---

## 2. Impact of Economic Node Adoption Rates on Chain Split Risk

**BCAP (qualitative):**
- Low adoption (minority): Highest chain split risk, re-orgs, miner flip-flopping
- Medium adoption (~50%): Moderate-high risk, two equal factions, market decides
- High adoption (vast majority): Lowest risk, strong consensus

**Simulation quantification:**

The `economic_split` parameter directly operationalizes BCAP's adoption rate concept, measuring the fraction of total economic custody weight initially supporting the new rules (v27).

| BCAP tier | economic_split range | Simulation finding |
|-----------|:-------------------:|-------------------|
| Low adoption | E < 0.50 | **Cascade floor** — v27 cannot win regardless of pool commitment. v26 wins structurally. Reorg risk is low because the fork fails decisively rather than sustaining. |
| Medium adoption | E ∈ [0.50, 0.82] | **Inversion zone** — contested outcomes cluster here. Pool commitment becomes the decisive variable. The PRIM uncertainty box [E: 0.28–0.78, C: 0.15–0.53] sits entirely within this zone. |
| Medium → High transition | E ≈ 0.74 | **Economic Self-Sustaining Point (ESP)** — price signal becomes self-reinforcing above this threshold. Below ESP, economic majority support can still fail; above it, the cascade completes. |
| High adoption | E > 0.82 | **Economic override threshold** — v27 wins regardless of pool commitment structure. RF probability surface becomes horizontally flat above this level. |

**Key refinement beyond BCAP:** The medium adoption zone is not monolithic. Below the ESP (E < 0.74), pool commitment (pool_committed_split) is the dominant discriminator — a single large pool's decision can determine the outcome. Above the ESP (E > 0.74), aggregate economic momentum takes over and pool structure becomes secondary. BCAP treats the medium zone as uniformly uncertain; the simulation subdivides it into two structurally distinct regimes with different causal mechanisms.

**BCAP caveat confirmed:** "High adoption does not necessarily mean investors will determine the Alternative Consensus Client is bitcoin." The model's economic override threshold (E ≈ 0.82) is a necessary but not sufficient condition — it predicts fork resolution within the simulation's economic weight model, but does not capture broader investor sentiment that BCAP identifies as a separate stakeholder class.

---

## 3. Impact of Bounty Size on Chain Split Risk

**BCAP (qualitative):**
- Small bounty: Low miner incentive to claim, network resists disruption
- Medium bounty: Moderate risk, opportunistic smaller miners, temporary disruptions
- Large bounty: Highest risk, attractive to large operations, sustained splits possible

**Simulation quantification:**

The "bounty" in BCAP terminology corresponds to `peak_price_gap_pct` in the simulation — the maximum price divergence between chains that creates a profitability differential incentivizing pool switching. The `pool_max_loss_pct` parameter captures pool-level bounty sensitivity: how large a price gap a pool requires before switching chains.

**Crucially, bounty size is endogenous in the simulation — it is an output of the economic cascade, not an independent input.** Higher `economic_split` generates larger price gaps, which generate the effective bounty that incentivizes pool switching. BCAP treats bounty size as an external threat parameter; the simulation shows it emerges from the interaction of economic support level and pool commitment structure.

| BCAP tier | peak_price_gap_pct | Simulation outcomes (n=530, 2016-block) |
|-----------|--------------------|----------------------------------------|
| Small bounty | < 10% | 289 scenarios: 245 v26 wins, 40 contested, 4 v27 wins. Pools do not switch; incumbent (v26) wins by default. |
| Medium bounty | 10–30% | 60 scenarios: mixed outcomes, elevated reorg_mass (avg 6,995 blocks for v27 wins), high cascade times. Consistent with BCAP's "temporary disruptions." |
| Large bounty | > 30% | 181 scenarios: 181 v27 wins, zero v26 wins or contested. Clean cascade completion in every case. |

**Pool max_loss_pct as bounty threshold:** The `pool_max_loss_pct` parameter directly represents BCAP's pool-level bounty sensitivity. At max_loss = 0.10–0.16, pools switch at moderate price gaps (avg 16–46%) — these are low-threshold operations responding to small bounties. At max_loss = 0.33–0.40, contested outcomes spike (up to 35% of scenarios), consistent with BCAP's "opportunistic smaller operations" surviving in the medium bounty regime without triggering full cascades.

**BCAP prediction confirmed:** "A mining pool could fund the chain split and pay out the bounty to participating miners." The Foundry flip-point finding (C ≈ 0.214) identifies the specific committed hashrate threshold where one large pool's decision cascades to the rest of the network — the structural mechanism by which a coordinated pool-funded split would operate.

---

## 4. Measuring Consensus — BCAP Metrics vs. Simulation Parameters

**BCAP identifies observable consensus signals by stakeholder class:**

| BCAP stakeholder | BCAP observable signals | Simulation parameter |
|-----------------|------------------------|---------------------|
| Economic Nodes | Transaction policies, product announcements, client version | `economic_split` (synthetic version of unobservable client version data) |
| Investors | Fork price divergence on derivative markets | `peak_price_gap_pct`, price oracle output |
| Miners | Version bit signaling, press statements | `pool_committed_split`, `pool_ideology_strength` |
| Users | Product announcements, usage patterns | `user_ideology_strength`, `user_switching_threshold` (shown to have no causal effect) |

**Direct response to BCAP's measurement gap:** BCAP explicitly identifies as a future improvement: *"Transparency from Economic Nodes on their client versions."* The `economic_split` parameter is a synthetic operationalization of exactly this unobservable quantity — it parameterizes the distribution of client versions across economic nodes and sweeps across all possible configurations to identify which distributions produce which outcomes. The sweep methodology answers the question BCAP poses but cannot currently measure empirically.

**Synthetic prediction market:** BCAP proposes *"prediction markets for bitcoin protocol changes"* as a future improvement. The Random Forest probability surface computed from simulation data is functionally a synthetic prediction market: given a parameter configuration (economic_split, pool_committed_split, pool_ideology_strength, pool_max_loss_pct), it outputs P(v27 win) — the exact quantity a real prediction market would price. The PRIM uncertainty box defines the parameter region where that synthetic market would be near 50/50, identifying where real prediction market prices would carry the most information.

**Composite measurement principle confirmed:** BCAP states: *"The benefit of not having a single metric of consensus is that it is harder to game or optimize for."* The contentiousness score uses equal 0.25 weights across four components (total_reorgs, reorg_mass, cascade_time_s, econ_lag_s) — a direct implementation of this principle. Sensitivity analysis (Pearson r = 0.985 between equal and prior unequal weights) confirms the composite is robust to weighting choices, consistent with BCAP's intent.

**Absence of opposition → contested outcome category:** BCAP observes that *"absence of press statements suggests apathy or unawareness."* The `contested` outcome category in the simulation is the structural equivalent — scenarios where neither fork achieves a decisive price signal, neither economic cascade completes, and the fork persists without resolution. Contested outcomes cluster in the PRIM uncertainty box, identifying the specific parameter region where real-world stakeholder apathy or ambivalence would produce sustained unresolved splits.

---

## 5. Two-Layer Governance Structure

**BCAP (implicit):** Different stakeholder classes have different mechanisms of influence and operate on different timescales. Miners respond to profitability signals; economic nodes respond to rule validity and market signals; these are separate decision processes.

**Simulation quantification:**

The simulation confirms a **two-layer outcome structure** that maps directly to BCAP's stakeholder separation:

- **Layer 1 (Pool/Hashrate layer):** Controlled by `pool_committed_split` crossing the Foundry flip-point (C ≈ 0.214). The pool cascade fires first (mean t = 3,298 simulation-seconds, ~1,649 blocks at 2016-block retarget). This is BCAP's miner signaling layer.

- **Layer 2 (Economic layer):** Controlled by `economic_split` relative to the cascade floor, ESP, and override threshold. Economic nodes respond approximately 3,506 simulation-seconds (~1,753 blocks) after pool cascade completion. This is BCAP's economic node adoption layer.

The two layers are largely decoupled: `pool_committed_split` has near-zero Spearman correlation with `v27_econ_share` (r = +0.02), confirming that which pools commit does not determine which economic nodes adopt. This validates BCAP's implicit assumption that miner and economic node governance operate through independent mechanisms — miners follow profitability, economic nodes follow rule validity and price signals, and the two processes resolve sequentially rather than simultaneously.

**Causal direction confirmed:** The simulation establishes the causal chain as Economics → Price → Profitability → Hashrate, not Hashrate → Economics. This directly supports BCAP's framing of economic nodes as the primary governance actors whose decisions miners ultimately follow, rather than miners as the primary decision-makers.

---

## 6. User Node Governance — BCAP vs. Simulation

**BCAP:** Users and application developers have influence through press statements, product announcements, and usage. Their impact is difficult to track due to nascent and fragmented application landscape.

**Simulation quantification:**

User nodes in the simulation hold 0.04% of total consensus weight (2,248 BTC across 28 nodes vs. 4,986,450 BTC across 24 economic nodes — a 2,197:1 ratio). The User-PRIM analysis (n=598 scenarios) confirms a structural null result: user ideology and switching parameters produce zero variation in fork outcomes across the full parameter space tested (targeted_sweep4, 36 scenarios, identical v26_dominant outcomes regardless of user behavior).

User nodes can have measurable effects only under four simultaneous conditions:
1. `economic_split` ∈ [0.50, 0.82] (inversion zone)
2. `pool_committed_split` near the transition threshold (~0.296)
3. `user_custody_fraction` > 0.14 (above the weight ratio threshold)
4. `user_split` sufficiently asymmetric (< 0.45 or > 0.55)

This aligns with BCAP's observation that user impact is "difficult to track" — it is not merely difficult to observe, but structurally negligible under realistic weight ratios. The simulation provides a quantitative basis for this: the 2,197:1 economic weight ratio means individual user nodes cannot bridge the marginal economic gap in any realistic parameter configuration.

**BCAP governance implication confirmed:** The UASF mechanism (users enforcing new rules to pressure miners) requires that user nodes *are* the economic infrastructure or control it. The simulation confirms this: user nodes are not the economic infrastructure (the 2,197:1 ratio), and UASF campaigns succeed when they persuade exchanges and custodians — not when they increase the count of individual full node operators. A coordinated user coalition large enough to act as a unified economic actor would be functionally indistinguishable from an economic node in the model, and would be captured by the `economic_split` parameter directly.

---

## 7. Cross-Network Coordination Regimes

**BCAP (implicit):** Economic node coordination — whether actors make decisions independently or in blocs — affects consensus dynamics, though BCAP does not model this distinction quantitatively.

**Simulation quantification:**

The cross-network validation (§4.10) identifies two distinct economic coordination regimes that BCAP does not distinguish:

| Regime | Network configuration | Dominant parameter | Mechanism |
|--------|----------------------|-------------------|-----------|
| **Coordinated bloc** | Lite network (2 aggregate nodes, ~25% weight each) | `pool_committed_split` (RF importance 46.5%) | Single bloc decision creates discrete large price signal; pool commitment determines if that signal crosses switching threshold |
| **Fragmented independent** | Full network (24 nodes, ~4% each) | `economic_split` (RF importance 52.8%) | Cascade assembles incrementally from many small decisions; aggregate adoption level controls how far cascade propagates |

**Governance implication:** Pool operators are pivotal when economic decisions are made in coordinated blocs; aggregate economic support is pivotal when economic decisions are fragmented and independent. The leverage of each actor class depends on how organized the other is. This is a structural finding BCAP does not anticipate but which follows directly from its stakeholder framework: the same total economic weight produces different governance dynamics depending on whether it is concentrated in few coordinated actors or distributed across many independent ones.

---

## 8. Summary — BCAP Qualitative → Simulation Quantitative

| BCAP concept | Simulation quantification |
|---|---|
| Low economic adoption → highest split risk | E < 0.50: cascade floor, v27 structurally fails |
| Medium adoption → market decides | E ∈ [0.50, 0.82]: inversion zone, PRIM uncertainty box |
| High adoption → strong consensus | E > 0.82: economic override, v27 wins regardless of pool structure |
| Economic self-sustaining cascade | ESP ≈ 0.74: price signal becomes self-reinforcing |
| Small bounty → low miner incentive | peak_price_gap < 10%: 85% v26 wins, 14% contested |
| Large bounty → sustained splits | peak_price_gap > 30%: 100% v27 wins, clean cascade |
| Bounty as external threat | **Corrected:** bounty is endogenous — emerges from economic_split × pool dynamics |
| Miner signaling precedes economic adoption | Layer 1 (pools) resolves ~1,749 blocks before Layer 2 (economic nodes) |
| Economics → Hashrate causation | Spearman r confirms: economic_split drives outcomes, pool_committed_split is secondary at high E |
| User influence difficult to measure | Structural null: 2,197:1 weight ratio, effect only at ucf > 0.14 under four simultaneous conditions |
| Coordinated vs. fragmented economic actors | Two regimes: bloc decisions (pool-dominated) vs. independent decisions (economic-dominated) |
| Composite consensus measurement | Contentiousness score: equal 0.25 weights, r=0.985 sensitivity, robust composite |

---

## 9. Determining Consensus — A Causal Hierarchy for BCAP's Indicator Checklist

**BCAP:** Consensus is gauged through a checklist of observable signals — miner signaling, economic node statements, node adoption rates, market sentiment, user activation, testnet implementation, and community sentiment. BCAP treats these as roughly co-equal inputs to be weighed collectively.

**What the simulation adds:**

BCAP's checklist is correct but flat — it does not tell practitioners which signals matter most, in what order they resolve, or what threshold values distinguish a fork that will succeed from one that will fail. The simulation provides a causal hierarchy and quantitative thresholds that transform the checklist into a structured assessment framework.

### 9.1 Signal Priority — Not All Indicators Are Equal

The Random Forest feature importance analysis across 590 full-network 2016-block scenarios establishes the following causal ranking:

| Rank | BCAP indicator | Simulation parameter | RF importance | Threshold |
|:----:|----------------|---------------------|:-------------:|-----------|
| 1 | **Economic Node statements / adoption** | `economic_split` | 52.8% | Cascade floor E≈0.50, ESP E≈0.74, override E≈0.82 |
| 2 | **Miner signaling** | `pool_committed_split` | 20.2% | Foundry flip-point C≈0.214, transition zone C≈0.296 |
| 3 | **Miner ideology / loss tolerance** | `pool_ideology_strength` × `pool_max_loss_pct` | 14.2% / 12.8% | Interaction term — neither operates independently |
| 4 | **User activation (UASF)** | `user_ideology_strength`, `user_switching_threshold` | ~0% | Structural null — no causal effect at realistic weight ratios |

This ranking directly answers the implicit question behind BCAP's checklist: if signals are mixed — if some indicators point toward consensus and others do not — economic node adoption is the primary arbiter. Miner signaling is decisive only within the inversion zone (E ∈ [0.50, 0.82]) where economic support is neither sufficient nor insufficient on its own.

### 9.2 Miner Signaling — Interpret With the Foundry Flip-Point in Mind

**BCAP:** "For changes that use miner signaling, monitor the percentage of blocks signaling readiness."

**Simulation finding:** Block percentage is a noisy proxy for the parameter that actually matters — the committed hashrate fraction relative to the Foundry flip-point (C ≈ 0.214). The simulation shows that miner signaling is only decisive when `economic_split` is in the inversion zone [0.50, 0.82]. Outside this zone:
- Below E=0.50: miner signaling is irrelevant — economic support is insufficient for v27 to win regardless of which pools commit
- Above E=0.82: miner signaling is irrelevant — economic support is sufficient for v27 to win regardless of which pools commit

**Practical implication:** A practitioner observing 60% of blocks signaling readiness should ask first where economic node adoption stands. If economic adoption is below the cascade floor, strong miner signaling is misleading — the fork will fail. If economic adoption is above the override threshold, weak miner signaling is also misleading — the fork will succeed. Miner signaling carries maximum information content only when economic adoption is in the inversion zone.

### 9.3 Economic Node Statements — The Primary Signal, With Threshold Structure

**BCAP:** "Look for public statements or announcements from major exchanges, wallet providers, and other Economic Nodes."

**Simulation finding:** Economic node statements are the highest-importance signal (52.8% RF importance), but the relationship between adoption fraction and outcome is non-linear with three distinct threshold zones:

- **E < 0.50 (cascade floor):** Economic node majority support for v27 is insufficient — v26 wins regardless. Statements of support from a minority of economic nodes are weak consensus signals.
- **E ∈ [0.50, 0.74] (inversion zone, below ESP):** Economic majority support exists but is not yet self-sustaining. Pool commitment is the swing variable. Statements from large pools in this zone carry high information content.
- **E ∈ [0.74, 0.82] (inversion zone, above ESP):** Economic cascade becomes self-reinforcing. Statements of support from remaining holdouts are the critical observable — each additional economic node crossing the switching threshold pushes others closer.
- **E > 0.82 (override threshold):** Consensus is structurally determined. Additional statements of support are confirmatory but not causal.

A practitioner can use these thresholds to calibrate how much weight to give economic node statements: early statements from major exchanges (high custody) carry more weight than late statements from merchants (low custody), because custody rank determines assignment order and thus which thresholds are crossed first.

### 9.4 Node Adoption Rate — Non-Linear, Not Monotonic

**BCAP:** "Track the adoption rate of new node versions that implement the proposed change."

**Simulation finding:** Node adoption rate (`economic_split`) has a non-linear relationship with consensus probability. The outcome is not simply "more adoption = more likely to succeed." Three adoption regimes exist with qualitatively different dynamics:

1. **Below cascade floor (E < 0.50):** Additional adoption does not increase v27's probability of winning. The structural constraint is binding regardless of adoption progress.
2. **In the inversion zone (0.50 < E < 0.82):** Each additional economic node that adopts changes both the price signal and the pool profitability calculation — adoption is self-reinforcing but not yet guaranteed. This is where monitoring adoption rate provides the highest information value.
3. **Above override threshold (E > 0.82):** Outcome is structurally determined. Additional adoption monitoring provides diminishing information.

**Practical implication:** Adoption rate monitoring is most valuable when the network is in the inversion zone. Practitioners should not extrapolate linearly — crossing the cascade floor and the ESP represent qualitative phase transitions, not incremental progress.

### 9.5 Market Sentiment and Derivative Prices — Lagging Confirmation, Not Leading Signal

**BCAP:** "Derivative markets, including futures contracts on proposed changes or forks, can provide insight into investor sentiment. Prices for these contracts can show whether there is a preference for or against a specific proposal."

**Simulation finding:** The price divergence between chains (`peak_price_gap_pct`, `final_v27_price` vs. `final_v26_price`) is an *output* of the economic cascade, not an input. It emerges from and reflects economic node adoption decisions rather than driving them. The causal chain is:

> Economic node adoption → price divergence → pool profitability signal → pool switching → further price divergence

Derivative market prices observe the fork price divergence after it has already emerged from economic node decisions. This makes market sentiment a **lagging confirmation signal** rather than a leading indicator. The simulation confirms BCAP's caveat that "sentiment can be lagging and reactive in markets with low liquidity" — the price divergence that drives the cascade is generated by custody-weighted chain selection, not by speculative market positioning.

**Exception:** At the ESP (E ≈ 0.74), the price signal becomes self-reinforcing. At this point, market prices do begin to carry forward-looking information — a price gap that crosses the ESP boundary signals that the cascade will complete, making derivative prices predictive rather than merely reflective.

### 9.6 User Activation (UASF) — Structural Null Confirmed

**BCAP:** "User-driven mechanisms like the UASF can signal a grassroots movement in support of a proposal, but UASF clients historically have failed to gain adoption from Economic Nodes and their impact has been minimal."

**Simulation finding:** This is the one BCAP conclusion that the simulation confirms most directly and quantitatively. User ideology parameters (`user_ideology_strength`, `user_switching_threshold`) produce zero variation in fork outcomes across the full parameter space tested. The structural cause is the 2,197:1 economic weight ratio between exchange nodes and user nodes collectively.

The simulation also confirms BCAP's historical observation about why UASF campaigns that *did* succeed (BIP148/SegWit in 2017) worked: they succeeded by persuading exchanges and economic infrastructure to enforce the new rules — not by accumulating individual full node operators. In the model, this is the `economic_split` mechanism, not the user node mechanism. UASF is most accurately understood as a coordination campaign targeting economic nodes, not a direct governance mechanism of user nodes themselves.

### 9.7 Testnet and Signet Implementation — Warnet as Structural Consensus Testing

**BCAP:** "Monitor the implementation and testing of proposed changes on Bitcoin's testnet and signet. Look for reports of any issues or unexpected behaviors during testing."

**Simulation contribution:** This research project *is* a testnet-based structural consensus analysis. Warnet provides a controlled simulation environment where parameter configurations are swept systematically across the governance parameter space — economic adoption levels, pool commitment structures, ideology strengths, and loss tolerances — to identify the conditions under which unexpected behaviors (contested outcomes, cascade failures, reorg cascades) occur. The PRIM uncertainty box [E: 0.28–0.78, C: 0.15–0.53] defines the parameter region where unexpected behaviors concentrate, which could inform where testnet monitoring should be most intensive during a real upgrade.

### 9.8 Synthesis — A Structured Consensus Assessment Protocol

BCAP's checklist becomes a structured assessment framework when the simulation thresholds are applied:

**Step 1 — Establish economic adoption level (primary signal)**
Estimate `economic_split` from public exchange statements and client version reports.
- E < 0.50: Fork will fail regardless of other signals. Do not proceed.
- E ∈ [0.50, 0.74]: Fork is in the contested zone. Proceed to Step 2.
- E > 0.74: Fork has self-sustaining economic momentum. Monitor for completion.
- E > 0.82: Fork outcome is structurally determined. Confirmatory monitoring only.

**Step 2 — Assess pool commitment (decisive only in inversion zone)**
Estimate `pool_committed_split` from miner signaling and pool announcements.
- C < 0.214 (below Foundry flip-point): Pool layer will not cascade. Fork likely fails even with economic majority.
- C ∈ [0.214, 0.296]: Transition zone — outcome is sensitive to individual large pool decisions.
- C > 0.296: Pool commitment is sufficient for cascade given adequate economic support.

**Step 3 — Evaluate pool loss tolerance (modulates cascade speed)**
- Low `pool_max_loss_pct` pools (opportunistic): Will flip quickly when profitability gap emerges — accelerates cascade.
- High `pool_max_loss_pct` pools (committed ideology): Will absorb losses longer — either slows cascade or produces contested outcome if economic support is insufficient to maintain price gap.

**Step 4 — Discount user activation signals**
UASF campaigns and individual full node adoption are structurally negligible at realistic economic weight ratios. Weight these signals only as indicators of coordinated economic node pressure, not as direct governance mechanisms.

**Step 5 — Interpret market prices as cascade phase indicators**
Fork derivative prices below the ESP price gap threshold indicate the cascade has not yet become self-sustaining. Prices crossing the ESP threshold indicate cascade completion is likely. Use as confirmation of Steps 1–3, not as independent leading signal.
