# Section 4.4 — Regime Comparison: The Causal Rank Reversal Between 144-Block and 2016-Block Retarget

**Draft:** May 2, 2026
**Status:** DRAFT — complete, all numbers from Phase 2 RF analysis (Table 7, §4.8.1)

---

## 4.4 Regime Comparison: The Causal Rank Reversal Between 144-Block and 2016-Block Retarget

The preceding sections established the causal structure of fork outcomes at the 2016-block retarget interval. A second, equally important finding emerges from comparing this structure to the 144-block regime: the dominant causal parameter changes entirely depending on which retarget interval is active. `economic_split` controls outcomes at 144-block; `pool_committed_split` controls them at 2016-block. The same fork, with identical actor configurations, produces different outcome logic depending only on how quickly the minority chain's difficulty adjusts.

---

### 4.4.1 The Rank Reversal

Random Forest classification was fitted separately on the full-network 144-block dataset (n=268) and the full-network 2016-block dataset (n=298), using the same four active parameters in both cases. Table 7 (reproduced from Section 4.8) reports the results.

**Table 7. Random Forest feature importance by retarget regime.**

| Parameter | 144-block (n=268) | 2016-block (n=298) | Rank change |
|-----------|:-----------------:|:------------------:|:-----------:|
| `economic_split` | **77.2%** | 20.2% | #1 → #2 |
| `pool_committed_split` | 11.3% | **52.8%** | #2 → #1 |
| `pool_max_loss_pct` | 5.5% | 17.1% | #4 → #3 |
| `pool_ideology_strength` | 6.0% | 9.9% | #3 → #4 |
| **RF OOB accuracy** | **80.0%** | **83.2%** | |

The reversal is not marginal. At 144-block, `economic_split` accounts for 77.2% of predictive importance — approximately four times the contribution of the next-best parameter (`pool_committed_split` at 11.3%). At 2016-block, `pool_committed_split` displaces it entirely, accounting for 52.8% while `economic_split` falls to 20.2%. The two parameters swap rank positions, and neither holds even a plurality in the other's dominant regime.

Two secondary observations follow from Table 7. First, the 2016-block outcomes are *more predictable* — OOB accuracy is 83.2% versus 80.0% at 144-block. A longer retarget window creates harder, more deterministic constraints around pool commitment structure; the RF extracts a cleaner signal accordingly. Second, `pool_max_loss_pct` rises from near-zero importance at 144-block (5.5%) to a meaningful secondary factor at 2016-block (17.1%). When the retarget interval is long enough that committed pools must sustain losses through an entire 2016-block epoch, how much loss they can absorb before switching becomes an independent causal factor in the outcome.

---

### 4.4.2 Mechanism: The Survival Window

The rank reversal is a consequence of the Difficulty Adjustment Survival Window — the time between fork inception and the minority chain's first difficulty retarget. During this window, the minority chain is mining at reduced hashrate against full difficulty, producing fewer blocks per hour than the majority chain. Once the retarget fires, difficulty drops proportionally, equalizing block production rates regardless of the starting hashrate split.

The survival window length is a direct function of the retarget interval:

- **144-block retarget:** Approximately 24 hours at normal block rates; under minority hashrate conditions, the window may compress to 8–16 hours depending on the initial hashrate deficit. The economic price signal — which responds to exchange activity, custodial weight migration, and fee market dynamics — operates on the same timescale. The price cascade *resolves before the retarget fires*, making economic alignment the binding constraint on which fork wins.

- **2016-block retarget:** Approximately 14 days at normal block rates; under minority conditions, the window extends further. The economic price signal still fires within hours or days, but the committed pool structure must hold through weeks of sustained losses before any difficulty relief arrives. The binding constraint is whether committed pools have sufficient loss tolerance to absorb the full epoch — making `pool_committed_split` and the `ideology_strength × max_loss_pct` interaction the operative parameters.

The 144-block regime therefore operates as an *economic auction*: whichever fork retains sufficient price support wins because the minority chain's survival window is short enough that economic weight alone determines cascade direction before pool ideology can be tested to exhaustion. The 2016-block regime operates as an *endurance contest*: economic signals still operate, but pool ideological commitment — specifically the product of how many committed pools are on which side and how long they can sustain losses — determines whether the minority chain survives long enough to reach the difficulty adjustment that equalizes competitive dynamics.

---

### 4.4.3 The 144-Block Economic Threshold

At 144-block, the decision boundary is approximately one-dimensional. The targeted_sweep1 grid (Table 4, Section 4.3.1) shows clean horizontal bands: `economic_split` at ≤0.45 always produces v26_dominant outcomes; at ≥0.82 always produces v27_dominant outcomes; the transition zone spans 0.50–0.70, where pool configuration has some secondary influence. The 11.3% RF importance for `pool_committed_split` at 144-block reflects only this secondary influence within the transition band — outside that band, the economic threshold operates as a near-binary switch.

This one-dimensional structure is also visible in the 144-block logistic regression: cross-validated accuracy is 59.8% — only 10 percentage points above chance (50%), and substantially weaker than the 77.5% achieved at 2016-block. The logistic model cannot usefully fit the 144-block boundary because the boundary is approximately a single step function of `economic_split` that does not benefit from the interaction terms the model includes. For 144-block inference, the RF feature importance scores are more informative than any regression-derived decision surface.

---

### 4.4.4 Quantization Caveat for Lite-Network 144-Block Data

One important methodological limitation applies specifically to 144-block sweeps conducted on the lite network (25-node configurations). On the lite network, economic nodes are assigned in whole-number increments: with 2 economic nodes per partition, the network has either 0, 1, or 2 economic nodes supporting v27 — corresponding to economic weights of approximately 0%, 50%, and 100% respectively. Economic weight is not continuous on the lite network; it is effectively a 3-level discrete variable.

This quantization means that the full-range economic_split variation sampled in LHS sweeps on the lite network (`lhs_144_6param`, n=129) does not correspond to genuine variation in economic weight — scenarios with `economic_split` anywhere in [0.30, 0.80] are all assigned the same 1 economic node on v27, producing identical economic dynamics. For this reason, `lhs_144_6param` is excluded from the 144-block RF fit (the 268-scenario dataset uses full-network sweeps only), and any 144-block economic_split effect observed on lite-network data should not be interpreted as a real finding.

All 144-block conclusions in this section and in Section 4.8 are drawn exclusively from full 60-node network scenarios where economic weight assignment is genuinely continuous.

---

### 4.4.5 Regime Dependence as a Governance Finding

The rank reversal has direct implications for Bitcoin governance analysis. The retarget interval is a fixed protocol parameter — Bitcoin's 2016-block (~14-day) retarget is the operationally relevant regime for any real contentious fork. Under this regime, the dominant causal parameter is not economic weight but pool committed structure: specifically, whether committed pool hashrate exceeds approximately 0.296 of total hashrate (Phase 3 transition zone threshold, Section 4.9).

This finding reframes the question governance actors should be asking during a contentious fork. The conventional framing — "which fork has more economic support?" — is the dominant question at short retarget intervals where economic signals resolve the fork before pool ideology is tested. At the 2016-block interval that governs real Bitcoin forks, the more consequential question is: "which large pools are committed to which fork, and can they sustain those losses through a full 14-day epoch?" Economic support remains relevant as a secondary amplifier and as the mechanism that forces pool switching once committed hashrate falls short — but it is not the first-order signal.

The two regimes are compared in Table 10.

**Table 10. Regime comparison summary.**

| Dimension | 144-block retarget | 2016-block retarget |
|-----------|-------------------|---------------------|
| Dominant parameter | `economic_split` (77.2% RF importance) | `pool_committed_split` (52.8% RF importance) |
| Secondary parameter | `pool_committed_split` (11.3%) | `economic_split` (20.2%) |
| Decision boundary shape | ~1-dimensional (economic threshold) | 2-dimensional (E×C interaction dominant) |
| Outcome predictability (OOB accuracy) | 80.0% | 83.2% |
| LR model strength (CV accuracy) | 59.8% — unreliable | 77.5% ± 2.9% |
| PRIM boundary resolution | Near-degenerate (92.5% support after 3 steps) | Well-resolved (51.0% uncertainty box) |
| Contentiousness (mean) | 0.132 | 0.271 (2.1× higher) |
| Governing mechanism | Economic price cascade resolves before retarget | Pool endurance through epoch before retarget |
| Primary governance question | "Which fork has economic majority?" | "Which large pools can sustain losses for 14 days?" |

The higher contentiousness at 2016-block (2.1×) reflects that longer survival windows allow more extended competitive mining, more chain reorganizations, and larger economic uncertainty periods before resolution. The same fork is approximately twice as disruptive under the operationally relevant retarget regime than under the shorter one.

---

*Section 4.4 ends. Next: Section 4.5 — The Difficulty Adjustment Survival Window.*
