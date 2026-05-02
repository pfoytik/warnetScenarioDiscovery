# Section 4.5 — The Difficulty Adjustment Survival Window

**Draft:** May 2, 2026
**Status:** DRAFT — complete. Numbers from §4.2.1 (Table 3b), hashrate_2016_verification (n=18), pool decision logs.

---

## 4.5 The Difficulty Adjustment Survival Window

The non-causality of hashrate in fork outcomes — the central surprising result of Phase 1 — does not arise from hashrate being unimportant to mining economics. It arises from a specific mechanism in Bitcoin's difficulty adjustment algorithm that neutralizes the starting hashrate advantage of the dominant chain before the economic price cascade resolves. This mechanism, which we term the **Difficulty Adjustment Survival Window**, is the unifying explanation for findings across Sections 4.2, 4.3, and 4.4, and produces an additional counter-intuitive result: acquiring *moderate* hashrate support for a minority fork can be strictly worse than acquiring none at all.

---

### 4.5.1 The Mechanism

When a contentious fork creates two competing chains, the minority chain begins mining at a hashrate deficit relative to its full pre-fork difficulty target. It produces blocks more slowly than the majority chain. However, Bitcoin's difficulty adjustment algorithm periodically recalibrates each chain's target independently: when a chain's block production rate falls below target, difficulty adjusts downward in proportion to the shortfall, restoring the target block rate regardless of how much hashrate the chain retains.

The **survival window** is the period between fork inception and the minority chain's first difficulty retarget. During this window:

1. The minority chain mines slowly at full pre-fork difficulty.
2. The majority chain builds a chain-length lead.
3. Miners on the minority chain accumulate opportunity costs (mining at lower revenue than they could achieve on the majority chain).
4. Economic price signals respond to block production differentials, diverging in favor of the majority chain.

When the retarget fires, the minority chain's difficulty drops proportionally to its hashrate deficit. Block production equalizes — both chains now produce blocks at approximately the target rate regardless of their relative hashrate. From this point forward, the *revenue per block* on each chain depends on price and fees, not on hashrate. The starting hashrate advantage of the majority chain has been neutralized.

The critical observation is that the survival window must close — the retarget must fire — before the economic cascade can fully resolve. If the price cascade completes first, the fork outcome is determined by economic dynamics. If the retarget fires first, the minority chain stabilizes its block rate and the economic dynamics then operate on a more level playing field. In either case, the initial hashrate split does not determine the winner; it only influences the timing and trajectory of the resolution.

---

### 4.5.2 Window Length as a Function of Retarget Interval

The survival window length is directly proportional to the retarget interval and inversely proportional to the minority chain's block production rate during the window.

At **144-block retarget**, the window spans approximately 24 hours at normal block rates. Under a 25% minority hashrate (v27 holding 25% of total), the minority chain produces blocks at roughly 25% of the target rate — six times slower than the majority chain. At this rate, the 144-block retarget epoch takes approximately 144 × (10 minutes / 0.25) ≈ 96 hours to complete. However, in practice the window effectively closes when the price cascade resolves — typically within hours of fork inception at the economic levels tested. The survival window at 144-block is short relative to the cascade timescale, meaning retarget relief arrives quickly enough that pool losses rarely accumulate to a forcing threshold.

At **2016-block retarget**, the window spans approximately 14 days at normal block rates. Under minority hashrate conditions, it extends further: a 25% minority hashrate chain takes approximately 2016 × (10 min / 0.25) ≈ 56 days in real time before its difficulty adjusts. Even in the accelerated simulation environment (2-second intervals, 13,000-second runs), the 2016-block window is wide enough that pool opportunity costs accumulate substantially before any retarget relief arrives. Committed pools must sustain losses through the entire epoch — and whether they can do so is governed by the `ideology_strength × max_loss_pct` product established in Section 4.3.3.

This is the mechanistic basis for the causal rank reversal documented in Section 4.4: the survival window length determines which signal — economic price dynamics or pool ideological endurance — becomes the binding constraint on the fork outcome.

---

### 4.5.3 The Hashrate Parity Danger Window

The survival window mechanism produces a second counter-intuitive result at the 2016-block retarget interval and economic parity (econ=0.50): intermediate v27 hashrate (35–45%) is strictly worse for v27 than either low (15–25%) or high (55–65%) hashrate. Table 3b (reproduced from §4.2.1) shows this pattern.

**Table 3b. hashrate_2016_verification results at econ=0.50 (2016-block retarget). Non-monotonic pattern: intermediate hashrate (35–45%) produces v26_dominant outcomes while lower (15–25%) and higher (55–65%) hashrate produce persistent splits.**

| hash \ econ | econ = 0.50 | econ = 0.60 | econ = 0.70 |
|-------------|:-----------:|:-----------:|:-----------:|
| hash = 0.15 | SPLIT | v27 | v27 |
| hash = 0.25 | SPLIT | SPLIT† | v27 |
| hash = 0.35 | **v26** | v27 | v27 |
| hash = 0.45 | **v26** | v27 | v27 |
| hash = 0.55 | SPLIT | v27 | v27 |
| hash = 0.65 | SPLIT | v27 | v27 |

*† Anomalous: 62% economic support produces a persistent split at hash=0.25. Adjacent econ=0.70 cell resolves cleanly.*

The mechanism operates through Foundry USA's loss accumulation at the 2016-block interval. With `pool_committed_split` fixed at 0.50 and `pool_ideology_strength=0.51`, `pool_max_loss_pct=0.26`, Foundry's maximum acceptable loss is `0.51 × 0.26 = 13.3%` of potential revenue.

At **intermediate v27 hashrate (35–45%):** The v26 chain builds a moderate chain-length lead quickly — fast enough that Foundry's accumulated mining loss on v27 reaches the 13.3% tolerance threshold within approximately one retarget cycle (~3,600 simulation seconds). Pool decision logs confirm the forced-switch event: *"Forced switch: loss 12.0% exceeds tolerance 12.0%."* Once Foundry crosses the threshold and exits v27, the remaining v27 hashrate collapses. The post-switch v26 profitability premium grows to 58%, trapping all subsequent neutral pool decisions on v26. The outcome is v26_dominant.

At **low v27 hashrate (15–25%):** The v26 chain's lead grows slowly because v26 mining itself is only slightly faster than target rate (it holds 75–85% of total hashrate, not dramatically above target at these economic levels). Foundry's loss accumulates at a slower rate, staying below the 13.3% threshold through the 13,000-second simulation window. Neither chain achieves dominance — the outcome is a persistent split.

At **high v27 hashrate (55–65%):** The v26 chain has only 35–45% of total hashrate — itself near or below the minority zone. The competitive dynamics are more symmetric. Neutral pool migration partially offsets early v26 hashrate advantage. Foundry's losses again remain below threshold. The outcome is again a persistent split.

The danger window exists in the intermediate zone because it is precisely fast enough to accumulate decisive losses against Foundry before the simulation ends, but not fast enough that Foundry's preferred chain (v27) can resist the growing v26 lead. At low hashrate, the accumulation is too slow to cross the threshold; at high hashrate, the accumulation is slow enough or offset enough by neutral pool behavior that the threshold is never reached in the simulation window.

---

### 4.5.4 Regime Dependence of the Danger Window

The hashrate parity danger window exists only at the 2016-block retarget interval. At 144-block retarget, the same hashrate levels tested in targeted_sweep2 (Table 3, §4.2.1) produce identical outcomes across all six hashrate values — the survival window closes before loss accumulation reaches any committed pool's tolerance threshold. The danger window is a 2016-block phenomenon, driven specifically by the long epoch during which committed pools absorb losses without any retarget relief.

This regime-dependence adds a further dimension to the causal rank reversal finding of Section 4.4. Not only does the dominant causal parameter switch between regimes — at 2016-block, the survival window is long enough to create a non-monotonic hazard zone in hashrate space that does not exist at 144-block. A governance actor relying on 144-block intuitions about hashrate neutrality could incorrectly conclude that acquiring moderate minority-fork hashrate is harmless. Under 2016-block dynamics, it can actively invert the outcome.

---

### 4.5.5 Governance Implications

The survival window mechanism has three concrete implications for Bitcoin governance actors during a contentious fork.

**First**, hashrate acquisition strategy is non-linear at 2016-block retarget and economic parity. Acquiring minority hashrate in the 35–45% range without sufficient economic support (econ ≥ 0.55) is worse than acquiring either less hashrate or more. The governance question is not "how much hashrate can we acquire?" but "is our economic support sufficient to avoid the parity danger window?"

**Second**, the retarget interval is the protocol parameter that determines which signal — economic alignment or pool ideological endurance — governs the fork outcome. This is not a tunable parameter for governance actors; it is fixed at 2016 blocks in Bitcoin. But it means that experience from faster-retarget chains (Bitcoin Cash's Emergency Difficulty Adjustment, for example) does not transfer directly to Bitcoin governance scenarios. The economic-dominant intuitions from shorter retarget regimes are systematically misleading for the 2016-block world.

**Third**, the survival window provides a natural monitoring indicator during a real contentious fork. The question "has the minority chain reached its first retarget epoch?" marks a qualitative transition: before the retarget, committed pools are accumulating losses against full difficulty; after it, the playing field levels and the remaining question is purely economic. If the fork has not resolved before the minority chain's first retarget, the dynamics shift and a fork that appeared to be dying may stabilize.

---

*Section 4.5 ends. Next: Section 4.6–4.7 — Cascade Dynamics and Real-World Implications.*
