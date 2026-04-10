# Section 7 — Discussion

**Draft:** April 10, 2026  
**Status:** DRAFT — complete. Awaiting Phase 3b data to confirm two-layer finding references in §7.2.

---

## 7. Discussion

This section interprets the primary findings of the simulation program, situates them within the broader literature on Bitcoin governance and fork dynamics, and draws out their implications for protocol developers, governance actors, and network operators. We focus on three findings that together challenge the prevailing understanding of how contentious forks resolve: the game-theoretic structure of pool commitment, the two-layer separation of hashrate and economic outcomes, and the structural ceiling on user node influence.

---

### 7.1 Commitment Is Not the Same as Leverage

The central finding of the Phase 1 sweep program is not merely that economic weight matters more than hashrate — a claim that has been made qualitatively before — but that the *causal structure* of fork outcomes is counterintuitive in a precise, quantifiable way. The Foundry flip-point (§4.3.2) demonstrates that increasing pool commitment to the upgrading fork can *reverse* the fork outcome under intermediate economic conditions. This is not a marginal effect or a modeling artifact: a 4-percentage-point shift in `pool_committed_split` — from 0.20 to 0.30 — converts a v27 win into a v26 win at economic_split = 0.60–0.70, holding all other parameters constant.

The mechanism is game-theoretic and operates through a forced-exit dynamic that has a direct analogue in financial markets. Below the Foundry flip-point (~0.214), the largest pool — Foundry USA, representing approximately 30% of total hashrate — is assigned a v26-preferring ideology but finds itself *economically trapped*: the price premium on v27 coins exceeds Foundry's maximum acceptable loss tolerance, making continued mining on v26 increasingly unprofitable with every block. This accumulated opportunity cost functions like margin pressure on a leveraged position. When the loss crosses Foundry's tolerance threshold, the exit is involuntary — forced by economics rather than chosen by conviction.

This forced exit is cascade-generating in a way that voluntary commitment is not. The involuntary nature of the switch sends an observable signal to neutral pools: a large operator's pain threshold has been breached. This is precisely the signal that triggers reassessment among profit-maximizing neutral miners, who update their own profitability calculations based on Foundry's revealed threshold. The cascade follows not because neutral pools are followers in a social sense, but because Foundry's forced exit is informative — it reveals that the economic pressure has crossed a structural threshold, not merely a preference.

Above the flip-point, Foundry shifts to v27-committed ideology. It now holds v27 by conviction rather than necessity. But this apparently favorable development for the upgrading fork has a critical side effect: Foundry's departure from the v26-committed pool purifies and hardens the v26 defending block. AntPool and F2Pool — now the sole committed v26 defenders — are no longer diluted by Foundry's economically ambivalent presence. They are the genuinely committed defenders, and their combined ideology × max_loss product is sufficient to resist the 60–70% economic signal. The cascade mechanism is broken not because the economics changed, but because the forced-exit actor was removed from the position where its forced exit would have been informative and cascade-generating.

The governance implication is precise and non-obvious: **the upgrade coalition gains a committed ally but loses the economic pressure mechanism.** Foundry as an economically trapped v26 miner has more leverage over the fork outcome than Foundry as an ideologically committed v27 miner. A governance actor trying to maximize the probability of a successful upgrade should therefore be more concerned with whether the largest neutral-to-opposing pools are economically constrained on the minority chain than with whether they can be persuaded to publicly commit to the upgrading chain. Public commitment by large pools may, under intermediate economic conditions, be counterproductive.

This finding has a direct analogue to coordination dynamics in financial markets. A forced liquidation by a large leveraged participant is more market-moving than a voluntary position change of equal size, because the forced nature of the exit signals threshold breach rather than preference change. Similarly in fork dynamics: the governance actor should ask not "which large pools support us?" but "which large pools are *trapped* on the opposing chain and will be forced to switch?"

---

### 7.2 The Two-Layer Outcome Structure

Phase 3 results establish that fork outcomes operate on two independent causal layers that are governed by different parameters and resolve on different timescales (§4.10, pending Phase 3b full-network validation).

**Layer 1 — Hashrate outcome:** Determined primarily by `pool_committed_split` relative to the Foundry flip-point threshold (~0.214–0.296 across regimes). This layer resolves through the pool commitment cascade described in §7.1: which chain accumulates sufficient committed and neutral hashrate to dominate block production. At 2016-block retarget, this layer is the dominant causal factor (RF feature importance: 52.8% for `pool_committed_split` vs. 20.2% for `economic_split`).

**Layer 2 — Economic adoption:** Determined primarily by `pool_max_loss_pct` (r = −0.417 with final economic share, Phase 3 data). Even after the hashrate outcome resolves — one chain establishes clear block production dominance — the economic adoption layer determines whether the winning chain achieves full economic node migration or stabilizes in a persistent split. Scenarios where `pool_max_loss_pct` ≤ 0.217 produce full economic migration; above this threshold, economic nodes may remain split even after hashrate convergence.

The two layers are largely independent: the parameter that governs which chain wins the hash war (`pool_committed_split`) is not the same as the parameter that governs whether the economic infrastructure fully migrates to the winning chain (`pool_max_loss_pct`). A fork can resolve cleanly at the hashrate layer while remaining contested at the economic layer, or vice versa.

This two-layer structure has practical implications for fork monitoring. Observing that one chain has established hashrate dominance does not imply that economic resolution is complete or imminent. The hashrate arbitrage mechanism (§4.5, `result_hashrateArbitrage.md`) adds a third temporal dimension: even after Layer 1 resolves, the minority chain's approaching difficulty adjustment creates a brief profitability spike that may temporarily attract neutral hashrate back, reopening Layer 1 uncertainty even when the trend appears settled. The period immediately preceding the minority chain's first difficulty adjustment is therefore the highest-risk interval for rapid outcome reversal — and is publicly observable from block production rates.

The historical parallel to the 2017 Bitcoin Cash fork is instructive. BCH launched with approximately 5–10% of total Bitcoin hashrate. The survival window at realistic difficulty was weeks. BCH's maintenance of token value through that window — supported in part by Emergency Difficulty Adjustment algorithm modifications that compressed the survival window artificially — illustrates how the three-variable interaction (token valuation, hashrate deficit, retarget proximity) plays out in practice. The model does not capture dynamic difficulty algorithm changes, but the underlying arbitrage logic is identical to what the simulation produces under standard 2016-block retarget dynamics.

---

### 7.3 The Structural Ceiling on User Node Influence

The User-PRIM analysis (§4.11) produces a structural null result: across 598 scenarios and 15 sweeps at 2016-block retarget, no parameter configuration was found in which user nodes are near-pivotal in determining fork outcomes. The bias ratio of 1.256 — only modestly above the 0.975 baseline — indicates that the discovered parameter box concentrates user-pivotal scenarios only marginally better than random selection. A bias ratio of 2.0 or higher would be required to claim meaningful concentration.

This result is not a failure of the methodology. The Scenario Potential framework correctly identifies a structural ceiling imposed by the economic weight ratio: user nodes collectively hold W_users/W_total = 0.169/370.90 (a 2197:1 ratio against the full economic network). At this ratio, even the most favorable conceivable parameter configuration — contested outcome, both forks at exact parity, user nodes as the nominal tie-breaker — cannot produce user-node pivotality, because the economic weight controlled by exchanges, custodians, and payment processors is structurally dominant. The null result is the correct output for this weight ratio, and finding it validates the framework as a null-result detector as well as a discovery tool.

The governance implication bears directly on UASF (User-Activated Soft Fork) theory. The UASF argument — advanced most prominently during the BIP 148 campaign preceding the 2017 SegWit activation — holds that user nodes enforcing new consensus rules creates economic pressure on miners: if miners' blocks are rejected by economic infrastructure, those blocks are worth less. This mechanism is real, but the simulation identifies precisely *where* its leverage lies. User nodes enforcing new rules create economic pressure only insofar as they *are* the economic infrastructure, or control it. Individual full node operators running updated software are not exchanges, custodians, or payment processors; they do not set the prices that determine miner revenue. The 2197:1 weight ratio quantifies this gap.

The practical implication is that UASF campaigns succeed when they persuade exchanges, custodians, and payment processors to enforce new rules — not when they increase the count of individual full node operators running updated software. The 2017 SegWit activation involved credible commitments from major economic actors, not merely a large count of individual full nodes. The simulation confirms this reading of that history: the causal pathway runs through economic node behavior, and user nodes are not in that pathway under any parameter configuration tested.

This does not mean user nodes are irrelevant to Bitcoin governance. They serve important functions in propagating transactions, enforcing policy-layer rules, and providing a distributed verification layer. But the specific claim that user nodes can be *pivotal* in a contested soft fork — that running strict-validation software as an individual operator can shift the outcome — is not supported by the simulation evidence. The scenario potential framework provides the first quantitative bound on this claim.

---

### 7.4 Implications for Protocol Developers and Governance Actors

The three findings together suggest a reframing of how contentious fork risk should be assessed. The conventional monitoring questions — "what fraction of hashrate supports the upgrade?" and "how many nodes are running the new software?" — are poor predictors of outcomes. The simulation-grounded monitoring questions are:

**1. Is economic_split above ~0.50?**  
Below this threshold, the upgrading fork cannot win regardless of mining configuration or user node behavior. Economic activity below majority is a necessary failure condition — the cascade mechanism has no signal to propagate.

**2. Is economic_split above ~0.82?**  
Above this threshold, the outcome is determined regardless of pool ideology or commitment structure. The remaining question is only how disruptive the transition will be, governed by the ideology × max_loss product (§4.3.4).

**3. In the intermediate range (0.50–0.82): which side is the largest pool on, and is it there by economic entrapment or ideological commitment?**  
This is the decisive question in the contested zone. A large pool that is economically trapped on the opposing chain — whose loss tolerance is near or below the price differential — is a cascade trigger. A large pool that is ideologically committed to the upgrading chain is a committed ally but simultaneously a purifier of the opposition. Governance actors should assess the *nature* of large pool alignment, not merely its direction.

**4. How far is the minority chain from its first difficulty adjustment, and what is the current token price differential?**  
The retarget calendar is publicly observable. The period before the first adjustment is the highest-risk window for outcome reversal regardless of the apparent trend in hashrate distribution.

These four questions can in principle be monitored in real time during a contentious fork from publicly observable data: exchange pricing (for economic_split proxy), mining pool block attribution (for pool_committed_split), and block production rates (for retarget proximity). The simulation establishes that these are the *right* variables to monitor — not hashrate majority, not node count, not social consensus signals.

---

### 7.5 Limitations

Several model limitations should inform how these findings are applied.

**Economic weight ratio as a fixed parameter.** The 2197:1 user-to-economic-infrastructure weight ratio reflects a specific calibration of the Bitcoin economic landscape. Different calibrations — for example, a scenario where large individual holders coordinate to represent a meaningful fraction of custodied BTC — could produce a different structural ceiling for user node influence. The null result is robust within the tested parameterization but should not be extrapolated to configurations with substantially different weight distributions.

**The ±20% price divergence cap.** All scenarios are bounded by a ±20% maximum price differential between forks. This cap was chosen to reflect realistic short-term price dynamics during a contested fork, but it does not capture the extreme divergence observed in cases like Bitcoin/Bitcoin Cash, where the minority chain token eventually traded at a small fraction of the majority chain price. At larger price differentials, the economic override threshold (~0.82) may shift, and the arbitrage mechanism may be suppressed by token value collapse rather than accelerated by a profitability spike. Extending the model to uncapped or larger-cap price divergence is a priority for future work.

**Static network topology.** The simulation uses a fixed network of 60 nodes with predetermined economic role assignments. Real Bitcoin forks involve dynamic network conditions: new economic actors entering the market, existing actors changing positions mid-fork, and strategic behavior by participants who observe the fork dynamics and adjust accordingly. The static topology means the simulation does not capture second-order strategic effects — for example, a large exchange publicly announcing its fork support position in order to influence other actors' calculations.

**Pool strategy as mechanical threshold-crossing.** Committed pool switching in the model is governed by a deterministic threshold (ideology × max_loss). Real pool operators exercise judgment that may deviate from this model — switching earlier to signal support, switching later to extract concessions, or splitting their hashrate across both chains. The threshold model captures the central tendency but not the strategic variance in pool behavior.

---

### 7.6 Future Work

The most immediate extension of this work is the Phase 3b full-network validation of the two-layer finding (§7.2). The Phase 3 results establishing the two-layer structure were produced on a 25-node lite network; Phase 3b deploys the same LHS design on the full 60-node network with genuine `economic_split` variation. Confirming that `pool_max_loss_pct` ≤ 0.217 governs full economic migration on the full network would substantially strengthen the paper's central claim.

Beyond Phase 3b, three targeted extensions would address the most important limitations:

**Sub-10% hashrate regime testing.** The hashrate non-causality finding holds across `hashrate_split` ∈ [0.15, 0.65], but the survival window argument predicts a failure boundary below approximately 10%: at very low hashrate, the minority chain may not produce blocks fast enough to maintain token value through the pre-retarget period. A targeted sweep at `hashrate_split` ∈ [0.02, 0.12] would establish the lower threshold for non-causality and identify the conditions under which hashrate *does* become decisive.

**Dynamic pool strategy.** Extending the model to allow pools to observe the retarget calendar and anticipate the arbitrage window — timing their hashrate switches strategically relative to the minority chain's difficulty adjustment — would quantify the strategic value of retarget timing. The current model's conservative assumption (pools do not anticipate the arbitrage) means the simulation likely underestimates the speed and sharpness of real-world cascades near retarget epochs.

**Scenario archetype clustering.** Phase 3 produced a rich dataset of 300 scenarios concentrated in the transition zone. Unsupervised clustering of these scenarios by their full dynamic trajectory — not just their final outcome — would identify qualitatively distinct fork archetypes: fast-resolving cascades, prolonged contested periods, oscillating outcomes. These archetypes would provide a more complete typology of fork risk than the binary v27/v26 classification used in the current analysis.

---

*Section 7 ends. Next: Section 8 — Conclusion.*
