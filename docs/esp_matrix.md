# Economic Self-Sustaining Point (ESP) Analysis
## econ_committed_2016_grid + targeted_sweep7_esp

**March 2026 — DRAFT**

---

## 1. Background and Research Question

The Economic Self-Sustaining Point (ESP) is defined as the minimum `economic_split` at which a v27 upgrade becomes self-reinforcing: economic actors rationally support v27, that support creates enough price pressure to sustain pool switching, and the outcome is stable against small perturbations. Above the ESP, v27 wins without requiring any additional coordination. Below it, the upgrade fails regardless of how committed early adopters are.

This document synthesizes two completed sweeps that jointly map the ESP boundary:

- **`econ_committed_2016_grid`** (n=45, complete): Full 5×9 grid of `economic_split` × `pool_committed_split` at 2016-block retarget. Maps which (econ, committed) combinations produce v27 wins and where the boundary lies.
- **`targeted_sweep7_esp`** (4/9 per regime, partial): Holds `committed_split=0.214` (Foundry flip-point) and `hashrate_split=0.25`, sweeping `economic_split` from 0.28 to 0.85. Tests whether v27 can self-sustain with minimal committed support at varying economic levels.

Fixed parameters across both sweeps: `hashrate_split=0.25`, `pool_neutral_pct=30%`, `pool_ideology_strength=0.51`, `pool_max_loss_pct=0.26`.

---

## 2. The 2016-Block Grid: Full Outcome Matrix

### 2.1 Outcome Table

Full 5×9 grid results. Each cell shows winner (v27/v26), v27 block count, and v27 final economic share.

| econ \ committed | 0.20 | 0.30 | 0.38 | 0.43 | 0.47 | 0.52 | 0.58 | 0.65 | 0.75 |
|---|---|---|---|---|---|---|---|---|---|
| **0.35** | v26 (14) | v26 (117) | v26 (4) | v26 (40) | v26 (5) | v26 (118) | v26 (70) | v26 (18) | v26 (21) |
| **0.50** | v26 (117) | v26 (4) | v26 (14) | v26 (299) | v26 (18) | v26 (210) | v26 (178) | **v27** (142) | v26 (102) |
| **0.60** | **v27** (499) | v26 (122) | **v27** (167) | v26 (107) | **v27** (198) | v26 (69) | **v27** (4356) | **v27** (571) | **v27** (362) |
| **0.70** | v26 (13) | **v27** (388) | **v27** (545) | **v27** (1701) | v26 (169) | **v27** (425) | **v27** (408) | **v27** (1053) | **v27** (717) |
| **0.82** | **v27** (708) | **v27** (1240) | **v27** (2459) | **v27** (6031) | **v27** (1776) | **v27** (902) | **v27** (351) | **v27** (1631) | **v27** (1369) |

Numbers in parentheses are v27 blocks mined. All runs: 13,000s duration, 2016-block retarget interval.

### 2.2 Three Regimes

**Regime 1 — Cascade Impossible (econ ≤ 0.35):**
v26 wins all 9 cells. At 2016-block retarget, econ=0.35 is definitively below the lower cascade threshold. The minority fork (v27) mines 4–117 blocks before collapsing — the exact count varies by pool configuration but the outcome does not.

**Regime 2 — Transition Zone (econ = 0.50–0.70):**
Mixed outcomes, non-monotonic in `committed_split`. This is the ESP-relevant region. Three sub-zones are visible:

- *econ=0.50*: Near-complete v26 dominance. Only one v27 win (committed=0.65, and it is the closest margin in the dataset: 142 v27 vs 138 v26 blocks). The adjacent cell at committed=0.75 reverts to v26 — the win is non-monotonic, likely reflecting a pool assignment boundary effect near committed=0.65.
- *econ=0.60*: Checkerboard pattern in the low-committed zone (committed ≤ 0.52 alternates v27/v26); high-committed zone (committed ≥ 0.58) is solidly v27 (6 of 9 cells v27 overall). The checkerboard suggests that at econ=0.60, the outcome is highly sensitive to which specific pools land on which side — small changes in committed_split flip cells.
- *econ=0.70*: Mostly v27 (7 of 9 cells) but with two anomalous v26 cells: committed=0.20 (committed hashrate too thin to initiate cascade — only 13 v27 blocks despite 70% economic support) and committed=0.47 (the most extreme divergence in the dataset — see Section 2.3).

**Regime 3 — Cascade Universal (econ ≥ 0.82):**
v27 wins all 9 cells decisively. Block counts range from 351 to 6,031 — the variation reflects duration of the contested period, not outcome uncertainty. Above econ=0.82, pool switching is forced regardless of ideology or pool configuration.

### 2.3 Anomalous and Contested Cells

The following cells show a meaningful gap between chainwork winner and economic majority, or sit at non-monotonic positions in the grid:

| econ | committed | Winner | v27 blks | v27 econ | Reorg mass | Notes |
|------|-----------|--------|----------|----------|------------|-------|
| 0.50 | 0.43 | v26 | 299 | 50.1% | 66 | Near-50/50 econ; contested |
| 0.50 | 0.52 | v26 | 210 | 50.1% | 339 | Highest reorg mass at econ=0.50 |
| 0.50 | 0.58 | v26 | 178 | 50.1% | 124 | Prolonged contest |
| 0.50 | 0.65 | **v27** | 142 | 50.1% | 0 | Narrowest v27 win; non-monotonic |
| 0.60 | 0.30 | v26 | 122 | 62.1% | 21 | v27 holds 62% economics; v26 wins chain |
| 0.60 | 0.43 | v26 | 107 | 62.1% | 100 | Same pattern |
| 0.60 | 0.52 | v26 | 69 | 62.1% | 18 | Same pattern |
| 0.70 | 0.20 | v26 | 13 | 70.2% | 106 | Committed hashrate too thin; no cascade |
| **0.70** | **0.47** | **v26** | **169** | **95.6%** | **1,462** | **Most extreme divergence** |

**The econ=0.70, committed=0.47 cell** is the most striking result in the grid. v26 wins chainwork despite v27 holding 95.6% of final economic weight and accumulating 169 blocks. The reorg mass of 1,462 blocks is by far the largest in the dataset — indicating a prolonged, deeply contested period before v26's chainwork advantage stabilized. This cell represents a "chainwork vs. economy" stalemate: the committed=0.47 configuration traps enough hashrate on v26 to maintain chainwork dominance even while the economic oracle has almost entirely abandoned v26. In a real network, a scenario with this profile would be operationally catastrophic — confirmations unreliable for an extended period, while price signals point strongly toward one chain but chain weight points toward the other.

---

## 3. Regime Comparison: 144-Block vs. 2016-Block

The 144-block equivalent grid (targeted_sweep1, n=45) allows a direct comparison of how retarget interval shifts the outcome boundary. Table below shows win counts by regime:

| econ | 144-block v27 wins (of 9) | 2016-block v27 wins (of 9) | Shift |
|------|--------------------------|---------------------------|-------|
| 0.35 | 0 | 0 | None |
| 0.50 | 8 | 1 | −7 cells (major shift) |
| 0.60 | 1 | 6 | +5 cells (pattern inverts!) |
| 0.70 | 1 | 7 | +6 cells |
| 0.82 | 9 | 9 | None |

The regime boundary shifts are striking:

- At **econ=0.50**, the 144-block regime is nearly all v27 (8/9 cells); the 2016-block regime is nearly all v26 (8/9 cells). The entire econ=0.50 row flips.
- At **econ=0.60**, the 144-block shows v27 winning only at committed=0.20 (the clean Foundry flip-point inversion). The 2016-block shows a checkerboard where v27 wins 6/9 cells including the high-committed zone. The inversion structure is fundamentally different between regimes.
- The **upper threshold (econ=0.82) is invariant** — both regimes produce universal v27 dominance.
- The **lower threshold shifts from ~0.45–0.50 (144-block) to ~0.55–0.60 (2016-block)**.

The practical implication: 144-block results are liberal estimates of cascade ease in the middle range (econ=0.50–0.70). A v27 upgrade that would succeed under test-speed retargeting may fail under realistic Bitcoin timing at the same economic support level.

---

## 4. Targeted Sweep 7 ESP Results

### 4.1 Sweep Design

`targeted_sweep7_esp` holds `committed_split=0.214` (the Foundry flip-point — minimum committed hashrate for v27 to win at 144-block) and `hashrate_split=0.25`, sweeping `economic_split` across 9 values:

| Sweep | econ_split |
|-------|-----------|
| sweep_0000 | 0.28 |
| sweep_0001 | 0.35 |
| sweep_0002 | 0.45 |
| sweep_0003 | 0.55 |
| sweep_0004 | 0.60 |
| sweep_0005 | 0.65 |
| sweep_0006 | 0.70 |
| sweep_0007 | 0.78 |
| sweep_0008 | 0.85 |

Sweeps 0004–0008 (econ=0.60–0.85) have not yet been run. The ESP boundary is expected somewhere in this range.

### 4.2 Completed Results

| econ_split | 144-block winner | v27 blks (144) | Reorg mass (144) | 2016-block winner | v27 blks (2016) | Reorg mass (2016) |
|---|---|---|---|---|---|---|
| 0.28 | **v27** (anomalous) | 0 | 0 | v26 | 76 | 304 |
| 0.35 | v26 | 45 | 176 | v26 | 71 | 284 |
| 0.45 | v26 | 29 | 104 | v26 | 26 | 104 |
| 0.55 | v26 | 13 | 52 | v26 | 1 | 4 |
| 0.60–0.85 | *pending* | — | — | *pending* | — | — |

### 4.3 Observations

**econ=0.28, 144-block anomaly:** The 144-block run reports v27 as winner with 0 blocks mined and 6 reorg events. This appears to be an immediate economic cascade where all committed pools reallocated before any blocks were mined — the scenario stabilized on v27 at t=0 based on price oracle initialization. This is below the quantization threshold (the prior analysis places "0 economic nodes on v27" at econ < ~0.30), making the result unexpected. The 2016-block run at the same econ=0.28 correctly shows v26 winning with 76 v27 blocks. This anomaly should be investigated before drawing conclusions from the 144-block econ=0.28 data point.

**Declining v27 block counts as econ drops:** At 2016-block, v27 mines 76 blocks at econ=0.35, 26 at econ=0.45, and only 1 at econ=0.55. This monotonic decline reflects the 2016-block survival window pressure — with lower economic support, the minority fork collapses faster before any retarget opportunity arrives. At econ=0.55 the chain is essentially dead after one block.

**ESP boundary not yet located:** All four completed data points (econ=0.28–0.55) show v26 wins at 2016-block. The grid data from Section 2 (committed=0.20 column) provides an independent estimate: at committed≈0.20, the 2016-block grid shows v27 winning at econ=0.60 (499 v27 blocks) but losing at econ=0.70 with committed=0.20 (only 13 v27 blocks — committed too thin). At committed=0.214 (the ESP sweep fixed value), the ESP threshold is likely between econ=0.55 and econ=0.70 based on cross-referencing with the grid. The targeted sweep 0004–0008 runs are needed to pin this down.

---

## 5. Estimated ESP Boundary

Based on the completed data, the ESP boundary can be bounded:

| Parameter | 144-block ESP | 2016-block ESP |
|---|---|---|
| Lower bound (all-v26 confirmed) | econ ≤ 0.55 | econ ≤ 0.55 |
| Upper bound (v27 expected to win) | econ ~ 0.60–0.65 (grid suggests) | econ ~ 0.60–0.70 (grid suggests) |
| Committed_split at boundary | 0.214 (fixed) | 0.214 (fixed) |

The grid data at committed=0.20 (closest to the ESP sweep's committed=0.214) shows:
- 2016-block, committed=0.20: v27 wins at econ=0.60 (499 blocks), v27 loses at econ=0.70 (13 blocks — committed too thin at 0.20, the sweep uses 0.214 which is slightly above Foundry flip-point).

This suggests the ESP is in the econ=0.55–0.65 range for 2016-block timing. Completing ESP sweeps 0004–0008 will locate the exact threshold.

---

## 6. Remaining Work

| Run | Status | Key question answered |
|-----|--------|----------------------|
| targeted_sweep7_esp sweep_0004–0008 (144-block) | Pending | Does 144-block ESP sit at econ=0.60, 0.65, or higher? Is it sharp (quantization-driven) or gradual? |
| targeted_sweep7_esp sweep_0004–0008 (2016-block) | Pending | Does 2016-block ESP shift upward vs 144-block? By how much? |
| econ=0.28 144-block anomaly investigation | Pending | Is the v27 "win" with 0 blocks real (fast cascade) or an initialization artifact? |

The econ=0.60 runs (sweep_0004) are the most urgent — the grid data predicts this is near the boundary for both regimes, so the sweep_0004 result will immediately tell us whether the ESP is at or above 0.60.
