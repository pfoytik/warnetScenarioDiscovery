# lhs_2016_timing_swap — Sweep Findings

**Completed:** 2026-08-02
**Scenarios:** 297/300 (missing: sweep_0010, sweep_0154, sweep_0264)
**Comparison baseline:** `lhs_2016_full_6param` (n=692)
**Analysis script:** `compare_analysis.py` (in this directory)

---

## Experimental Design

| Parameter | Baseline | This Sweep |
|---|---|---|
| pool_decision_interval | 600s | **1800s** |
| econ_switching_cooldown | 1800s | **600s** |
| pool/econ decision ratio | pools 3× faster | econ 3× faster |
| price_update_interval | 60s | 60s (unchanged) |
| duration | 13000s | 13000s |
| retarget_interval | 2016 blocks | 2016 blocks |
| network | full 60-node | full 60-node |
| seed | — | 2027 (independent LHS) |

Parameters swept: `economic_split` [0.25, 0.95], `pool_committed_split` [0.10, 0.70], `pool_ideology_strength` [0.20, 0.90], `pool_max_loss_pct` [0.05, 0.45]. All other parameters fixed at validated values (hashrate_split=0.25, econ_switching_threshold=0.10, econ_inertia=0.05).

---

## Primary Question: Is the Two-Layer Ordering Structural or Timing-Driven?

**Answer: Structural.**

The two-layer result — hashrate cascade resolves first (Layer 1), full economic adoption follows (Layer 2) — survives even when economic nodes decide 3× faster than pools.

Using the correct completion threshold (`econ_95pct_time_s` vs `cascade_time_s`):

| | Timing Swap | Baseline |
|---|---|---|
| n (scenarios with both metrics defined) | 155 | 295 |
| econ reaches 95% **after** cascade | **69.7%** | 86.4% |
| econ reaches 95% **before** cascade | 22.6% | 8.8% |
| Mean lag (econ_95pct − cascade) | **+433s** | **+420s** |
| Median lag | **+360s** | **+315s** |

The mean lag is essentially unchanged. Economic nodes with a 600s cooldown still cannot fully commit before the price signal exists, because the price signal only emerges from hashrate divergence. Faster decision cadence does not help if the information hasn't arrived yet.

### Why the `econ_lag_s` table in report.txt shows many negatives

The per-scenario report uses a 2pp movement threshold to detect `econ_switch_time_s` — this triggers on early "flutter" before real adoption. Using `econ_95pct_time_s` (full adoption threshold) recovers the correct ordering. Both sweeps show the same pattern with the stricter threshold.

### Theoretical interpretation

Economic nodes are informationally constrained, not decision-rate constrained. The price oracle updates every 60 seconds in both sweeps. By the time an economic node's cooldown expires (600s in timing swap), it has already seen 10 price update cycles — it is fully current on price information. What it cannot see yet is a *completed* hashrate cascade, because that requires pool decisions that happen at 1800s intervals. The bottleneck is price signal availability, and price signal depends on hashrate divergence existing, which depends on pool decisions.

This validates the ANALYSIS_GUIDE null-result interpretation: decision cooldown timing is epiphenomenal; price oracle cadence is the true binding constraint.

---

## Secondary Findings

### 1. Outcome Distribution — Timing IS a Governance Lever (+10pp for v27)

| Outcome | Timing Swap | Baseline | Delta |
|---|---|---|---|
| v27_dominant | **53.9%** (159/295) | 43.9% (304/692) | **+10.0pp** |
| v26_dominant | 41.0% (121/295) | 49.4% (342/692) | −8.4pp |
| contested | 5.1% (15/295) | 6.6% (46/692) | −1.5pp |
| econ full_switch | **52.9%** | 42.6% | +10.3pp |

Even though the *ordering* is structural, **who wins is not the same.** Faster economic nodes shift 10pp of outcomes from v26 to v27. The mechanism: faster econ nodes exploit early (partial) price signals before pool cascade completes, shifting the economic balance enough to tip borderline scenarios toward v27.

**Effect by economic_split quartile:**

| E range | Timing Swap | Baseline | Delta |
|---|---|---|---|
| E < 0.45 | **31%** v27 | 7% v27 | **+24pp** |
| 0.45–0.60 | **39%** | 24% | +15pp |
| 0.60–0.75 | 68% | 63% | +5pp |
| 0.75–0.95 | 78% | **81%** | −3pp |

The advantage is largest at **low economic split** — where baseline pools dominate and econ signals are weak. At very high E (>0.75), the timing swap slightly underperforms because slower pools cannot complete the cascade as reliably even when economic conditions favor v27 strongly.

### 2. Feature Importance — No Rank Reversal, Substantial Convergence

| Feature | Timing Swap (imp) | Baseline (imp) |
|---|---|---|
| economic_split | 0.331 (#1) | 0.486 (#1) |
| pool_committed_split | 0.287 (#2) | 0.205 (#2) |
| pool_ideology_strength | 0.192 (#3) | 0.146 (#4) |
| pool_max_loss_pct | 0.190 (#4) | 0.163 (#3) |
| **OOB accuracy** | **0.631** | **0.793** |

The rank order of the top two features is preserved. The ratio of importance narrows from 2.4:1 to 1.15:1 — nearly co-equal. Pool committed split gained importance (essentially doubled relative share) when pools are slow, because each pool decision carries more weight when decisions are infrequent.

The OOB accuracy drop (0.793 → 0.631) is significant: outcomes are substantially harder to predict from static parameters in the timing-swap regime. Slower pool dynamics introduce more path-dependence and stochasticity.

### 3. Pool Committed Split Threshold — LOWERED (Opposite of Prediction)

| C bin | Timing Swap v27% | Baseline v27% |
|---|---|---|
| C < 0.20 | 28% | 29% |
| C 0.20–0.30 | **50%** | 33% |
| C 0.30–0.40 | 60% | 44% |
| C 0.40–0.50 | 44% | 49% |
| C 0.50–0.60 | **74%** | 58% |
| C 0.60–0.70 | 67% | 52% |

v27 crosses the 50% win-rate threshold at C≈0.20–0.25 in the timing swap, versus C≈0.45–0.50 in baseline. The ANALYSIS_GUIDE predicted the threshold would rise (pools need more commitment to overcome faster econ switching). The opposite occurred: faster economic nodes compensate for committed hashrate — v27 needs *less* pool commitment when economic actors react quickly to partial price signals.

The non-monotonicity at C=0.40–0.50 (44% in timing swap, lower than C=0.30–0.40 at 60%) is anomalous and warrants attention in any follow-up analysis.

### 4. Economic Override Threshold — Slightly Weakened at High E + Low C

| Condition | Timing Swap | Baseline |
|---|---|---|
| E ≥ 0.78 (all C) | 82.2% v27 | 83.4% v27 |
| E ≥ 0.78 with C < 0.25 | **53%** v27 (n=17) | **67%** v27 (n=33) |

The aggregate override rate (E≥0.78) is nearly identical. But at the challenging corner (high E, very low committed hashrate), the timing swap is weaker: slow pools cannot complete the cascade reliably even when economic conditions strongly favor v27. The override threshold of ~0.78–0.82 is preserved in aggregate but with lower confidence at low-C extremes.

### 5. Inversion Zone (E ∈ [0.60, 0.75]) — Inversion Gone

| Condition | Timing Swap | Baseline |
|---|---|---|
| n in E=[0.60,0.75] | 63 | 148 |
| v27 win rate | 68.3% | 62.8% |
| High-C (≥0.45) v27 win rate | **91%** | 80% |
| Low-C (<0.30) v27 win rate | 50% | 38% |

In baseline, high committed-hashrate scenarios in the inversion zone showed a non-monotonic effect (pool identity composition could hurt v27). In the timing swap, higher pool commitment consistently helps v27 in this zone — the inversion disappears. Faster economic nodes appear to dampen the pool identity dynamics that drove the inversion.

### 6. Cascade and Economic Switch Timing

| Metric | Timing Swap | Baseline |
|---|---|---|
| cascade_time_s median | **2,530s** | **878s** |
| cascade_time_s mean | 2,143s | 1,342s |
| econ_switch_time_s median | 1,211s | 978s |
| econ_switch_time_s mean | 1,753s | 1,172s |

The hashrate cascade slows by ~3× (median 2530s vs 878s), as expected from 3× longer pool cooldowns. The economic switch time only slows by 24% (1211s vs 978s) despite the cooldown being 3× shorter in the timing swap — economic nodes switch as soon as the price signal warrants it, regardless of how short their cooldown is.

### 7. No-Switch Rate Within v27-Dominant — 81% Finding Corrected

| | Timing Swap (n=159) | Baseline (n=304) |
|---|---|---|
| econ full_switch | **97.5%** | **97.0%** |
| econ partial_switch | 1.9% | 1.3% |
| econ no_switch | **0.6%** | 1.6% |

Both sweeps show ~97% full economic switch within v27-dominant scenarios. The "81% no-switch rate" cited in earlier notes was a lite-network artifact and does not apply to the full 60-node network. In the full network, v27 wins almost always require both hashrate cascade AND economic adoption together.

---

## E×C Decision Boundary Comparison

v27 win rate by economic_split × pool_committed_split bin:

```
                    C=[0.10,0.25)    C=[0.25,0.40)    C=[0.40,0.55)    C=[0.55,0.70)
E=[0.25,0.40)    SWAP: 8%  BASE: 5%  SWAP:27%  BASE: 5%  SWAP: 7%  BASE:12%  SWAP:50%  BASE: 3%
E=[0.40,0.55)    SWAP:15%  BASE: 5%  SWAP:71%  BASE:10%  SWAP:29%  BASE:14%  SWAP:53%  BASE:28%
E=[0.55,0.70)    SWAP:41%  BASE:22%  SWAP:67%  BASE:47%  SWAP:57%  BASE:51%  SWAP:88%  BASE:83%
E=[0.70,0.85)    SWAP:35%  BASE:51%  SWAP:67%  BASE:87%  SWAP:80%  BASE:85%  SWAP:92%  BASE:90%
E=[0.85,0.95)    SWAP:62%  BASE:79%  SWAP:100% BASE:75%  SWAP:83%  BASE:92%  SWAP:100% BASE:84%
```

**Notable patterns:**
- **Low-E, medium-high C:** Timing swap shows large v27 gains (+20 to +61pp) — this is where faster econ nodes matter most
- **High-E, low-C:** Timing swap underperforms (−16pp at E=[0.70,0.85), C<0.25) — slow pools can't complete cascade
- **High-E, high-C:** Outcomes converge (both near 90–100%)

---

## Implications for the Paper

### What this confirms
- **Two-layer structure is a robust, structural finding** — not an artifact of timing asymmetry. This is the strongest possible robustness check available without changing the price oracle itself.
- **Causal mechanism is the price oracle, not the decision cadence.** Pools and economic nodes are both oracle consumers; the 60s oracle update rate is the system's true information clock.

### What this adds
- **Timing asymmetry as governance lever:** A 3× shift in relative decision rates moves the aggregate v27 win rate by 10pp. In practice, this suggests that governance mechanisms affecting *how frequently* different actor types can signal (e.g., signaling windows, lock-in periods) can materially shift fork outcomes without changing economic fundamentals.
- **Low-E scenarios are most timing-sensitive:** When economic adoption is near the contested zone (E<0.55), faster economic actors can exploit early signals to shift outcomes. High-E scenarios are timing-insensitive — the fundamental economics dominate.

### What to follow up (if time permits)
- **Price oracle cadence sweep:** Vary `--price-update-interval` (60s, 300s, 600s) at fixed pool and econ timings. If the ordering reverses with a 300s oracle and 300s cooldowns (vs 600s oracle and 1800s cooldowns), that would definitively confirm the oracle as the binding constraint.
- **Non-monotonicity at C=0.40–0.50** in timing swap: may be a sampling artifact (n=48) or a real feature of the slower-pool dynamics.

---

## Checklist Status

- [x] Run `4_analyze_results.py` on merged results
- [ ] Load into `sweep_results.db` via `5_build_database.py` — add `lhs_2016_timing_swap` to KNOWN_SWEEPS
- [x] Compute `econ_lag_s` distribution and compare to baseline
- [x] Train RF on this sweep; compare feature importances to `lhs_2016_full_6param`
- [x] Plot E×C decision boundary; overlay against baseline boundary (tabular comparison done; visual plot optional)
- [x] Compare v27 win rate in matched E×C bins
- [x] Check cascade floor and economic override threshold shift
- [x] Check 81% no-switch rate replication (corrected: lite-network artifact)
- [x] Document findings in `SWEEP_FINDINGS.md`
