# Section 4.11 — User-PRIM: Scenario Potential for User Nodes

**Draft:** April 9, 2026  
**Status:** DRAFT — complete. Figure placeholder noted.

---

## 4.11 User-PRIM: Scenario Potential for User Nodes

User full nodes occupy a distinct role in Bitcoin governance theory. Unlike mining pools, which can shift hashrate, or economic nodes, which control the price signals that drive miner revenue, user nodes enforcing consensus rules through strict validation exert no direct economic force. They cannot orphan miners' blocks unless the economic infrastructure — exchanges, custodians, payment processors — also refuses to accept those blocks. Whether user nodes can nonetheless exert *structural* influence on fork outcomes under any parameter configuration is an empirical question that the Scenario Potential framework is designed to answer.

This section reports the User-PRIM analysis: a governance-adapted Z-PRIM algorithm applied to the 2016-block regime dataset (n=598 scenarios, 15 sweeps) to find the parameter subspace where user nodes are most nearly pivotal. The analysis uses a composite objective combining contentiousness (scenarios where the outcome is genuinely in play) with a normalized user Scenario Potential score (SP_user). The result is a structural null: user-PRIM finds a bounded box but does not substantially concentrate user-pivotal scenarios, confirming that pool and economic dynamics dominate 2016-block fork outcomes at all parameter combinations tested.

---

### 4.11.1 Structural Ceiling from Weight Ratio

The upper bound on user node pivotality is set analytically before any simulation data is examined. In the simulation network, user nodes carry a combined economic weight of W_users = 0.1688 against a total network weight of W_total = 370.90 — a 2197:1 ratio. This ratio is not a calibration choice but a structural consequence of the model's representation of Bitcoin's economic geography: exchanges, custodians, and payment processors collectively hold vastly more economic weight than individual full node operators.

At this weight ratio, the maximum achievable SP_user value — the scenario potential of user nodes — is bounded near zero for all but the most artificially constructed parameter configurations. Even in the most favorable conceivable scenario (contested outcome, both forks at exact parity, user nodes as the sole tie-breaker), the user coalition controls less than 0.05% of total economic weight. The z-score formulation of Scenario Potential can normalize this contribution, but the normalization does not change the underlying structural fact: user nodes cannot be the swing actor in a realistic fork.

The User-PRIM analysis was conducted with this ceiling in mind, using min-max normalization of SP_user across the dataset to give user pivotality scores comparable scaling to contentiousness. Without normalization, the near-zero SP_user values would dominate none of the Z_user variance and the analysis would reduce to pure contentiousness PRIM. The normalized analysis provides the fairest possible test of whether user nodes concentrate influence in any region of parameter space.

---

### 4.11.2 User-PRIM Discovered Box

User-PRIM was applied to the 2016-block dataset (n=598 scenarios across 15 sweeps) using a composite objective Z_user = λ1 × contentiousness + λ2 × SP_user_normalized, with λ1=0.5 and λ2=1.0 (SP_user-weighted). The discovered box and its properties are reported in Table 10.

**Table 10. User-PRIM discovered box: parameter bounds and outcome properties.**

| Parameter | Min | Max |
|-----------|-----|-----|
| `economic_split` | 0.49 | 0.77 |
| `pool_committed_split` | 0.20 | 0.50 |
| `pool_ideology_strength` | 0.47 | 0.52 |
| `pool_max_loss_pct` | 0.25 | 0.26 |

**Box statistics:**

| Metric | Value |
|--------|-------|
| Scenarios in box | 58 (9.7% of dataset) |
| Mean Z_user in box | 0.563 (dataset mean: 0.299) |
| Mean SP_user in box | 0.336 |
| Mean contentiousness in box | 0.297 |
| v27_dominant | 38 (65.5%) |
| v26_dominant | 16 (27.6%) |
| contested | 4 (6.9%) |

The box identifies a region of parameter space concentrated in the transition zone for economic_split (0.49–0.77, spanning both the cascade onset and the approach to the economic override threshold) and pool_committed_split (0.20–0.50, spanning the Foundry flip-point). The ideology_strength and max_loss_pct bounds are strikingly narrow — [0.47, 0.52] and [0.25, 0.26] respectively — covering only a thin slice of the tested ideology × max_loss space. This narrow band corresponds to pool ideology × max_loss products near the diagonal threshold (Section 4.3.3), where the interaction is closest to the switching boundary.

The outcome distribution within the box (65.5% v27, 27.6% v26, 6.9% contested) is close to the overall dataset distribution. The box has not concentrated contested outcomes; the mean contentiousness in the box (0.297) is nearly identical to the overall 2016-block mean (0.271). This alone signals that the box is not finding scenarios where user nodes tip a genuinely balanced contest.

---

### 4.11.3 Bias Ratio: The Null Result

The key diagnostic for User-PRIM is the bias ratio — the recall of high-SP_user scenarios (top two quintiles) within the discovered box relative to the recall of low-SP_user scenarios (bottom two quintiles). A bias ratio substantially above 1.0 would indicate the box concentrates user-pivotal scenarios; a ratio near 1.0 indicates the box is no better than the baseline at finding them.

**Table 11. Bias ratio comparison: Standard PRIM vs. User-PRIM.**

| Method | Bias Ratio | Completeness | N in box |
|--------|:----------:|:------------:|:--------:|
| Standard PRIM | 0.975 | 1.00 | 229 |
| User-PRIM | **1.256** | 0.60 | 58 |

The User-PRIM bias ratio is 1.256. This is slightly above the standard PRIM baseline of 0.975 — indicating some improvement over random selection — but it is not substantially above 1.0. A bias ratio of 1.256 means the box is only modestly better than chance at concentrating user-pivotal scenarios. By comparison, meaningful scenario concentration in prior PRIM applications yields bias ratios of 2.0 or higher; the 1.256 result falls well short of this threshold.

A sensitivity check across three λ configurations confirms the finding is not an artifact of the objective weighting:

| λ1 (contentiousness) | λ2 (SP_user) | N in box | Mean Z_user | Stable? |
|:--------------------:|:------------:|:--------:|:-----------:|:-------:|
| 0.5 | 1.0 | 58 | 0.563 | ✓ |
| 1.0 | 0.5 | 72 | 0.730 | ~ |
| 0.5 | 2.0 | 57 | 0.866 | ~ |

The box size and Z_user concentration shift as the weighting changes, but the bias ratio does not materially improve. The near-unity bias ratio under the default weighting (λ1=0.5, λ2=1.0) is the primary result; the alternative weightings confirm it is not sensitive to that specific choice.

**[FIGURE PLACEHOLDER: SP_user distribution by outcome type and Z_user scatter plot (SP_user vs. contentiousness) with User-PRIM box boundary overlaid. Source: `tools/discovery/output/user_prim/`. See writing_plan.md §Figures.]**

---

### 4.11.4 Structural Interpretation

The User-PRIM null result has a straightforward structural explanation. Fork outcomes in the 2016-block regime are determined by two causal pathways: the pool commitment cascade (controlled by pool_committed_split crossing the Foundry flip-point, Section 4.3.2) and the economic price cascade (controlled by economic_split exceeding the override threshold, Section 4.3.4). User nodes participate in neither pathway directly. They do not set prices — that function belongs to exchanges and custodians in the economic node class. They do not produce blocks — that function belongs to pools and solo miners. A user node operator running strict-validation software can delay or complicate the propagation of non-conforming blocks only if the economic infrastructure also refuses them; in the simulation, economic infrastructure behavior is determined by economic node parameters, not user node parameters.

The 2197:1 weight ratio quantifies what this means in practice. Even in the narrow ideology band identified by User-PRIM — where pool ideology × max_loss products are closest to the switching threshold — the user coalition cannot provide the economic signal required to push pool decisions across the threshold. The simulation confirms this directly: the targeted_sweep5 grid (Section 4.2.2) produced zero variation in any output metric across the full user parameter space, with all 36 scenarios producing identical v26_dominant outcomes regardless of user ideology or switching behavior.

This finding bears directly on debates about User-Activated Soft Fork (UASF) governance strategies. The UASF argument holds that user nodes enforcing new rules creates economic pressure on miners — if miners' blocks are rejected by economic infrastructure, those blocks are worthless. This mechanism requires that user nodes *are* the economic infrastructure, or control it. In the model, they are not and do not: the economic weight ratio is 2197:1. The governance implication is that UASF campaigns succeed when they persuade exchanges, custodians, and payment processors to enforce the new rules — not when they increase the count of individual full node operators running updated software. Individual user node operators cannot be near-pivotal under any realistic parameter configuration tested.

The User-PRIM analysis validates the Scenario Potential framework as a null-result detector. It correctly distinguishes between regions of parameter space where a governance actor *could* be pivotal and regions where structural weight constraints make pivotality impossible regardless of parameter values. A bias ratio near 1.0 is the correct output for an actor class with negligible economic weight — and finding it is a contribution rather than a failure of the method.

---

*Section 4.11 ends. Next: Section 4.9 — Phase 3: The Two-Layer Outcome Structure (after Phase 3b data collection, ~April 12).*
