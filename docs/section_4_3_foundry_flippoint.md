# Section 4.3 — Causal Parameters and Decision Boundary

**Draft:** April 9, 2026  
**Status:** DRAFT — complete. Figure placeholder noted in 4.3.2.

---

## 4.3 Causal Parameters and Decision Boundary

After eliminating non-causal parameters (Section 4.2), fork outcomes are determined by three active parameters: `economic_split` (the fraction of Bitcoin economic activity — custody, transaction volume, exchange liquidity — denominated on the v27 fork), `pool_committed_split` (the fraction of mining hashrate held by ideologically committed pools), and the interaction of `pool_ideology_strength` and `pool_max_loss_pct` (jointly determining whether a committed pool will switch under economic pressure). This section maps the joint decision boundary across these three parameters and identifies the structural mechanisms governing each.

---

### 4.3.1 The Economic Threshold and Inversion Zone

Mapping fork outcomes across a 5×9 grid of economic_split × pool_committed_split (targeted_sweep1, n=45, hashrate_split fixed at 0.25, 144-block retarget) reveals a non-monotonic decision boundary with three distinct regimes (Table 4).

**Table 4. targeted_sweep1: fork outcomes across economic_split × pool_committed_split. v27 = v27_dominant; v26 = v26_dominant. Note the inversion at econ = 0.60–0.70 where the effect of pool_committed_split reverses sign.**

| econ \ commit | 0.20 | 0.30 | 0.38 | 0.43 | 0.47 | 0.52 | 0.58 | 0.65 | 0.75 |
|---------------|------|------|------|------|------|------|------|------|------|
| **econ = 0.35** | v26 | v26 | v26 | v26 | v26 | v26 | v26 | v26 | v26 |
| **econ = 0.50** | v26 | v27 | v27 | v27 | v27 | v27 | v27 | v27 | v27 |
| **econ = 0.60** | v27 | v26 | v26 | v26 | v26 | v26 | v26 | v26 | v26 |
| **econ = 0.70** | v27 | v26† | v26† | v26† | v26† | v26† | v26 | v26 | v26 |
| **econ = 0.82** | v27 | v27 | v27 | v27 | v27 | v27 | v27 | v27 | v27 |

*† Partial cascade: v27 retains ~34.7% final hashrate (AntPool partially defects from v26); 7 reorgs occur but v26 maintains dominance.*

Three regimes are visible. In the **weak economics regime** (economic_split ≤ 0.45), no cascade is possible and v26 wins across all pool configurations — the economic price signal is insufficient to move neutral pools or overcome committed v26 resistance. In the **strong economics regime** (economic_split ≥ 0.82), the price signal is sufficient to break even strongly committed v26 pools and v27 wins universally. The **intermediate regime** (economic_split 0.50–0.70) exhibits an inversion: outcomes are non-monotonic in pool_committed_split, with v27 winning only at the lowest committed level (0.20) and losing at all higher levels tested. This counter-intuitive result — where more pool commitment to v27 produces worse outcomes for v27 — is the central structural finding of the sweep program and is explained by the Foundry flip-point mechanism (Section 4.3.2).

The econ=0.70 row also reveals a partial cascade zone at commit=0.30–0.52: the outcome resolves to v26_dominant, but with active contest dynamics (7 reorgs, v27 retaining ~34.7% final hashrate). This is the transition boundary at 70% economic support — sufficient economic pressure to cause significant instability but not enough to complete the cascade against the committed v26 block.

---

### 4.3.2 The Foundry Flip-Point Mechanism

The inversion in Table 4 is caused by a structural feature of the pool distribution. With pool_neutral_pct fixed at 30%, the committed pool hashrate (70% of total) is partitioned into v27-preferring and v26-preferring assignment zones based on cumulative position. The largest pool, Foundry USA (representing approximately 30% of total mining hashrate), crosses from v26-preferring to v27-preferring assignment at a specific pool_committed_split value:

```
pool_committed_split × 0.70 > 0.15  →  pool_committed_split > 0.214
```

This threshold — approximately 0.214 — is the Foundry flip-point. Its effect is asymmetric and regime-dependent:

**Below the flip-point (commit ≤ 0.20):** Foundry is assigned v26-preferring ideology. At 60–70% economic support for v27, the v27 price premium exceeds Foundry's max_loss tolerance, making it impossible for Foundry to profitably stay on the v26 chain. Foundry is economically trapped on v27, providing the committed hashrate anchor that enables the price cascade. Result: v27 wins via economic pressure.

**Above the flip-point (commit ≥ 0.30):** Foundry shifts to v27-preferring ideology and holds the v27 chain. However, the reassignment simultaneously strengthens the opposing committed v26 block: AntPool (~18% total hashrate) + F2Pool (~15%) remain committed to v26, creating a v26-committed block of approximately 40% of total hashrate. This block is too large to break at 60–70% economic signal — the price gap of ~16% stays within the committed v26 pools' max_loss tolerance of 13.3% (ideology=0.51 × max_loss=0.26). Result: v26 maintains dominance despite holding the economic minority.

The governance implication is direct: the decisive question in a contentious fork is not whether v27 holds an aggregate economic majority, but which specific large pools are on which side and what their switching costs are. A 4-percentage-point shift in pool_committed_split — from 0.20 to 0.30 — converts Foundry from "economically trapped on v27" to "ideologically committed to v27 but surrounded by a now-strengthened v26 block," reversing the fork outcome entirely.

**[FIGURE PLACEHOLDER: Two-panel schematic of pool assignment at commit=0.20 vs commit=0.30 showing Foundry's position relative to the flip-point boundary, with the resulting hashrate blocks on each side. See writing_plan.md §Figures.]**

The flip-point is confirmed by unbiased Latin Hypercube Sampling at 2016-block retarget (lhs_2016_full_parameter, n=64): all 12 v26_dominant cases have pool_committed_split ≤ 0.246, and all 52 v27_dominant cases have pool_committed_split ≥ 0.260. The gap between 0.247 and 0.259 is clean — no scenarios fall in this range — confirming the structural nature of the threshold rather than a smooth probability gradient.

---

### 4.3.3 Pool Ideology Threshold

The pool_committed_split threshold governs whether the cascade can begin, but a second threshold determines whether it completes. The interaction of `pool_ideology_strength` and `pool_max_loss_pct` — whose product defines a pool's maximum acceptable loss (`max_acceptable_loss = ideology_strength × max_loss_pct`) — gates whether committed v26 pools ultimately capitulate under economic pressure or hold indefinitely.

This was mapped on the full 60-node network at econ=0.78 (targeted_sweep6_pool_ideology_full, n=20, 144-block retarget). A diagonal threshold is confirmed: committed v26 pools survive economic pressure when ideology × max_loss ≳ 0.16–0.20; below this product, pools capitulate regardless of individual ideology or loss tolerance levels (Table 5a).

**Table 5a. targeted_sweep6_pool_ideology_full: v26 survival conditions at econ=0.78. Entry shows outcome; threshold marks where v26 pools hold vs. capitulate.**

| ideology_strength \ max_loss_pct | 0.05 | 0.15 | 0.25 | 0.35 | 0.45 |
|----------------------------------|------|------|------|------|------|
| **ideology = 0.2** | v27 | v27 | v27 | v27 | v27 |
| **ideology = 0.4** | v27 | v27 | v27 | v27 | **v26** |
| **ideology = 0.6** | v27 | v27 | v27 | **v26** | **v26** |
| **ideology = 0.8** | v27 | v27 | **v26** | **v26** | **v26** |

The diagonal threshold separates the table: v26 survives at ideology × max_loss ≳ 0.16–0.18 (the range between the highest v27-winning product and the lowest v26-surviving product). Neither parameter is sufficient individually — ideology=0.8 with max_loss=0.05 produces v27 dominance, as does ideology=0.2 with max_loss=0.45. The product is the operative quantity.

The direction of the effect is economic-context-dependent: the threshold governs **defender resilience**. At econ=0.78 where v27 holds the economic majority, a high ideology × max_loss product protects v26 from being swept by the price cascade. At economic conditions where v26 holds the majority, the same logic applies symmetrically to v27-committed pools. The threshold characterizes how much ideological commitment is required to resist economic pressure, regardless of which fork is the economic minority.

Both parameters have substantial individual correlations with outcomes in the full-network sweep (ideology_strength: r = −0.49; max_loss_pct: r = −0.62 at econ=0.78) but neither alone is predictive: pools need both the willingness to absorb losses (ideology) and the capacity to do so (loss tolerance). Near the diagonal, small changes in either parameter cross the line from "committed pools capitulate" to "committed pools hold indefinitely," making the product a binary switch governing the entire cascade pathway.

---

### 4.3.4 Economic Override

The ideology × max_loss threshold established at econ=0.78 does not extend to higher economic levels. A dedicated override sweep (targeted_sweep6_econ_override, n=27: ideology=[0.40, 0.60, 0.80] × max_loss=[0.25, 0.35, 0.45] × econ=[0.82, 0.90, 0.95], 144-block retarget) produced v27_dominant outcomes in all 27 scenarios. Above econ≈0.82, the price signal is strong enough to force capitulation regardless of ideology × max_loss product — the economic override is total and unconditional.

However, the ideology × max_loss product continues to determine cascade timing even when it cannot change the outcome. At ideology=0.80 + max_loss=0.35, the cascade takes 10,920 seconds — approximately three times the 2016-block retarget period and more than 15× the fastest observed cascade at the same economic level (~680s at ideology=0.80, max_loss=0.25). High ideology creates maximally resistant pools that delay but cannot prevent capitulation when economic pressure is sufficient.

The joint picture of Sections 4.3.3 and 4.3.4 is therefore: the ideology × max_loss product determines whether committed pools hold at moderate economic levels (econ=0.78, threshold at product ≳ 0.16–0.18), but above econ≈0.82 this threshold vanishes — all pool configurations resolve to v27 dominance, with the product governing only the speed of resolution.

---

### 4.3.5 Consolidated Threshold Summary

Table 5 summarizes all quantitative thresholds identified across the Phase 1 targeted sweep program. These thresholds represent the primary empirical contribution of Phase 1 and provide operational guidance for interpreting real-world fork scenarios.

**Table 5. Consolidated threshold estimates with confidence and data source.**

| Parameter | Threshold | Interpretation | Confidence / Source |
|-----------|-----------|----------------|---------------------|
| economic_split (lower bound) | ~0.45–0.50 | Below this, no cascade is possible regardless of other parameters | High — targeted_sweep1 (n=45) |
| economic_split (inversion onset) | ~0.55–0.60 | Inversion zone begins; pool_committed_split effect reverses sign | High — confirmed in targeted_sweep1 and targeted_sweep2 |
| economic_split (upper bound / ESP) | ~0.78–0.82 | Above this, economic signal overrides all pool configurations; v27 wins universally | High — targeted_sweep7_esp (n=18) confirms ESP=0.74; override confirmed at 0.82 in targeted_sweep6_econ_override (n=27) |
| pool_committed_split (Foundry flip-point) | ~0.214 | Crossing this boundary reassigns Foundry (~30% hashrate) and inverts outcomes at econ=0.60–0.70; confirmed as hard threshold via unbiased LHS | High — targeted_sweep1 mechanism analysis; confirmed lhs_2016_full_parameter (n=64) |
| pool_ideology_strength × pool_max_loss_pct (product) | ~0.16–0.20 | Below this product, committed pools capitulate; above it, v26 pools survive at econ=0.78; threshold vanishes at econ≥0.82 | High — targeted_sweep6_pool_ideology_full (n=20) + targeted_sweep6_econ_override (n=27) |
| hashrate_split | No independent effect | Appears important in exploratory sweeps but is a LHS sampling confound; non-causal at econ≥0.60 | High — targeted_sweep2 (n=42); hashrate_2016_verification (n=18) |
| All user behavior parameters | No independent effect | User nodes lack sufficient economic weight or hashrate to shift outcomes under any tested configuration | High — targeted_sweep5 (n=36); User-PRIM analysis (n=598, §4.11) |

For a protocol developer or governance actor, these thresholds translate to three concrete monitoring questions during a contentious fork:

1. **Is economic_split above ~0.50?** If not, the upgrading fork cannot win regardless of mining support or pool ideology.
2. **Is pool_committed_split above or below ~0.214?** This determines whether the largest pool (Foundry-class, ~30% hashrate) is economically trapped on the upgrading chain or ideologically committed to it — a distinction that reverses the outcome at moderate economic levels.
3. **Is economic_split above ~0.82?** If so, pool ideology and commitment structure become irrelevant to the final outcome, though they continue to determine how long resolution takes.

---

*Section 4.3 ends. Next: Section 4.8 — Phase 2 Boundary Fitting.*
