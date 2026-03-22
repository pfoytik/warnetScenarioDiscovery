# Warnet Fork Simulation

## Price Oracle Improvement Proposal

*Literature-grounded enhancements with empirical validation from parameter sweeps*

**Last Updated:** March 2026 (post-sweep11)

---

## Executive Summary

The current price oracle uses a three-factor weighted linear model to determine token price divergence after a sustained fork. This document proposes targeted improvements grounded in both peer-reviewed cryptocurrency economics literature and empirical observations from our parameter sweep campaigns.

**Key empirical finding:** In the 2016-block retarget regime, **difficulty mechanics dominate price signals** as the cascade trigger. Price oracle improvements matter most for:
1. The initial neutral pool decision (t=0-600s)
2. Scenarios near the economic threshold boundary
3. Ghost town scenarios where one chain stops producing blocks

---

## Current Model Summary

The existing price oracle computes:

```python
factor = 0.8 + (weight × 0.4)  # linear, range [0.8, 1.2]

combined_factor = (chain_factor × 0.30)
                + (economic_factor × 0.50)
                + (hashrate_factor × 0.20)

new_price = clamp(base_price × combined_factor,
                  base_price × (1 - 0.20),
                  base_price × (1 + 0.20))
```

**Structural issues identified:**

| Issue | Description | Empirical Evidence |
|-------|-------------|-------------------|
| Static custody | `econ_f` doesn't respond to chain liveness | sweep10: v27 at 0% hashrate for 600s, price only dropped 6% |
| Linear mapping | Minority-chain collapse is gradual, not abrupt | BCH/BSV historical outcomes show rapid bifurcation |
| Symmetric floor | ±20% cap applies equally to both chains | Hayes (2019): minority chain floor should be lower |
| No liveness penalty | Dead chains maintain price based on static custody | Ghost town problem (see below) |

---

## Empirical Observations from Sweeps

### The Ghost Town Problem (Critical)

**Observed in sweep10 (econ=0.70, 144-block):**

| Time | v27 Hashrate | v27 Blocks | v27 Price | Price Change |
|------|--------------|------------|-----------|--------------|
| 1,209s | 0.0% | 424 | $60,917 | — |
| 1,808s | 0.0% | 424 | $57,332 | **-6%** |

V27 produced **zero blocks for 600 seconds** but its price only dropped 6%. The `econ_f` component (weight 0.5, driven by static 70% BTC custody) floors the price regardless of chain liveness.

**Reality:** A chain producing zero blocks loses settlement finality immediately. Exchanges halt withdrawals, economic actors begin emergency custody migration, and confidence collapses far faster than the static custody model captures.

### When Does the Price Oracle Actually Matter?

Based on sweep9, sweep10, and sweep11:

| Phase | Price Oracle Importance | Reason |
|-------|------------------------|--------|
| Initial decision (t=0-600s) | **High** | Neutral pools choose which fork based on price parity/advantage |
| During cascade | **Medium** | Committed pools use profitability calculations (price × difficulty) |
| Ghost town | **Should be high, currently low** | Dead chain price doesn't collapse appropriately |
| Post-retarget | **Low** | Difficulty drop dominates — 36.7% losses >> any price signal |

### 144-block vs 2016-block Dynamics

| Regime | Price Oracle Role | Cascade Trigger |
|--------|-------------------|-----------------|
| 144-block | Secondary | Difficulty retarget every ~6 min rescues dead chains |
| 2016-block | More important | No resurrection mechanism; price signals matter for initial decision |

**Sweep11 finding:** At econ=0.50 with 2016-block, the cascade completes by t≈1200s WITHOUT any retarget. The initial neutral pool choice (based on price parity) determined the outcome. Price oracle accuracy matters here.

---

## Proposal 1: Liveness Penalty (NEW — Highest Priority)

### 1.1 Motivation

The ghost town problem is the most critical oracle failure. A chain producing zero blocks should experience rapid price collapse, not a 6% drift over 10 minutes.

### 1.2 Formula Change

**Option A: Multiplicative liveness penalty**

```python
# blocks_per_interval = blocks mined in last N seconds / expected blocks in N seconds
liveness_f = min(1.0, blocks_per_interval ** liveness_exponent)
# liveness_exponent controls steepness (e.g., 0.5 = square root, gentler)

combined_factor = (chain_f*0.3 + econ_f*0.5 + hash_f*0.2) * liveness_f
```

**Option B: Liveness-coupled econ_f (Recommended)**

```python
production_ratio = recent_blocks / target_blocks  # [0, 1]
confidence_decay = production_ratio ** confidence_exponent

# At production_ratio=1.0: effective_econ_f = econ_f (no change)
# At production_ratio=0.0: effective_econ_f = 1.0 (neutral — custody is contested)
effective_econ_f = 1.0 + (econ_f - 1.0) * confidence_decay

combined_factor = chain_f*0.3 + effective_econ_f*0.5 + hash_f*0.2
```

### 1.3 Numerical Comparison

Scenario: v27 stops producing blocks at t=1000s. Production window = 300s. Base price = $60,000, econ_split = 0.70.

| Time Since Last Block | Current Price | Option B Price | Change |
|-----------------------|---------------|----------------|--------|
| 0s | $63,600 | $63,600 | — |
| 60s | $63,600 | $62,880 | -1.1% |
| 120s | $63,600 | $61,920 | -2.6% |
| 300s | $63,600 | $60,000 | -5.7% |
| 600s | $63,600 | $58,080 | -8.7% |

With the liveness penalty, price decline accelerates as the chain remains dead, modeling custody flight with realistic inertia.

### 1.4 Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `liveness_window` | 300s | Time window for measuring block production |
| `confidence_exponent` | 1.0 | Decay steepness (1.0 = linear) |
| `enable_liveness_penalty` | True | Disable for backward compatibility |

### 1.5 Why This is Highest Priority

- **Fixes the most unrealistic oracle behavior** observed in sweeps
- **Simple to implement** — single new parameter
- **Bounded effect** — only activates when block production actually stalls
- **Preserves existing behavior** for normal operation (both chains producing blocks)

---

## Proposal 2: Lagged Economic Weight (EMA)

### 2.1 Academic Motivation

Kristoufek (2015) "What are the main drivers of the Bitcoin price?" uses wavelet coherence to show that transaction volume and custody signals lead price changes by days to weeks. Using contemporaneous economic weight creates unrealistically tight coupling.

### 2.2 Formula Change

```python
# CURRENT
economic_weight = economic_pct / 100.0
economic_factor = 0.8 + (economic_weight × 0.4)

# PROPOSED
ema_alpha = 0.15  # configurable
ema_economic = prev_ema × (1 - alpha) + economic_weight × alpha
economic_factor = 0.8 + (ema_economic × 0.4)
```

### 2.3 Empirical Assessment

**Priority: Low**

From sweep11, the cascade at econ=0.50 completed in ~1200s. The EMA smoothing would slow price response by ~4 minutes (at alpha=0.15, 60s updates). This would:
- Slightly delay the neutral pool decision signal
- Not change equilibrium outcomes
- Add realism to timing dynamics

**Verdict:** Nice to have, but doesn't fix any observed model failures.

### 2.4 Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `economic_ema_alpha` | 0.15 | EMA smoothing factor (0=no update, 1=no lag) |
| `use_economic_ema` | False | Enable lagged economic weight |

---

## Proposal 3: Nonlinear (Sigmoid) Factor Mapping

### 3.1 Academic Motivation

Biais et al. (2019) "The Blockchain Folk Theorem" proves that fork games have a coordination tipping point: once a fork achieves critical adoption, economic actors rationally abandon the minority chain rapidly. Linear mapping cannot reproduce this.

### 3.2 Formula Change

```python
# CURRENT (linear)
factor = 0.8 + (weight × 0.4)

# PROPOSED (sigmoid)
k = 6.0  # steepness
sig = 1 / (1 + exp(-k × (weight - 0.5)))
factor = 0.8 + (sig × 0.4)
```

### 3.3 Numerical Comparison

| Econ Weight | Linear Factor | Sigmoid Factor | Price Difference |
|-------------|---------------|----------------|------------------|
| 50% | 1.000 | 1.000 | $0 |
| 70% | 1.080 | 1.095 | +$900 |
| 90% | 1.160 | 1.181 | +$1,260 |
| 30% | 0.960 | 0.908 | -$3,120 |
| 10% | 0.880 | 0.819 | -$3,660 |

### 3.4 Empirical Assessment

**Priority: Medium**

The sigmoid would accelerate minority-chain price collapse, which could:
- Make neutral pool decisions more decisive at moderate economic splits
- Speed up committed pool capitulation in borderline scenarios
- Better match historical BCH/BSV price dynamics

However, sweep11 showed that at econ=0.50, the cascade was already decisive without sigmoid mapping. The benefit would be most visible in the 0.55-0.65 economic range.

### 3.5 Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `factor_mapping` | "linear" | "sigmoid" for new behavior |
| `sigmoid_steepness_k` | 6.0 | Higher = sharper tipping point |
| `apply_sigmoid_to` | ["economic"] | Factors to apply sigmoid to |

---

## Proposal 4: Asymmetric Price Floor (Cost-of-Production)

### 4.1 Academic Motivation

Hayes (2019) derives that BTC price converges toward marginal cost of mining. The minority chain has lower difficulty and therefore a lower cost floor. The current symmetric ±20% cap is structurally incorrect.

### 4.2 Formula Change

```python
# CURRENT (symmetric)
min_price = base_price × (1 - 0.20)  # $48,000 for both forks

# PROPOSED (cost-floor)
hashrate_pct = fork_hashrate / total_hashrate
difficulty_ratio = hashrate_pct
fork_cost = base_mining_cost × difficulty_ratio
fork_floor = (fork_cost / base_mining_cost) × base_price × (1 - margin_buffer)
```

### 4.3 Numerical Comparison

| v26 Hashrate | Current Floor | Proposed Floor | Difference |
|--------------|---------------|----------------|------------|
| 50% | $48,000 | $28,500 | -41% |
| 30% | $48,000 | $17,100 | -64% |
| 10% | $48,000 | $5,700 | -88% |
| 5% | $48,000 | $2,850 | -94% |

### 4.4 Empirical Assessment

**Priority: Medium-High**

In sweep11, v27 ended at 0% hashrate with price still at ~$55,000 (constrained by the 20% cap). With asymmetric floor:
- Terminal price would drop to near-zero
- This would more realistically model "dead chain" economics
- But it wouldn't change outcomes since cascade was already complete

**Best combined with Proposal 1 (liveness penalty)** — together they model both:
1. Price collapse from block production stopping (liveness)
2. Lower equilibrium floor for minority chains (cost basis)

### 4.5 Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_cost_floor` | False | Enable asymmetric floor |
| `mining_cost_per_block_usd` | 100000 | Shared with fee oracle |
| `cost_floor_margin_buffer` | 0.05 | Safety buffer below breakeven |

---

## Proposal 5: Raise Divergence Cap for Extreme Scenarios

### 5.1 Motivation

The 20% divergence cap artificially constrains price movements in extreme scenarios. When one chain has 0% hashrate and 0% blocks, a 20% discount is not realistic.

### 5.2 Formula Change

```python
# CURRENT
max_divergence = 0.20  # Fixed

# PROPOSED
liveness_ratio = recent_bpr / target_bpr
effective_cap = base_cap + (1.0 - liveness_ratio) × extended_cap
# e.g., base_cap=0.20, extended_cap=0.40 → up to 60% divergence for dead chains
```

### 5.3 Empirical Assessment

**Priority: Low (if Proposal 1 implemented)**

This is a symptom fix, not a root cause fix. If Proposal 1 (liveness penalty) is implemented, the cap becomes less binding because price naturally collapses before hitting the cap.

---

## Recommended Implementation Order

Based on empirical findings from sweeps:

| Priority | Proposal | Rationale |
|----------|----------|-----------|
| **1 (Critical)** | Liveness Penalty | Fixes ghost town problem — most unrealistic current behavior |
| **2 (High)** | Asymmetric Price Floor | Structurally correct; complements liveness penalty |
| **3 (Medium)** | Sigmoid Factor Mapping | Improves realism near economic threshold boundary |
| **4 (Low)** | Raise Divergence Cap | Only needed if Proposals 1-2 not implemented |
| **5 (Low)** | Lagged Economic Weight | Timing polish; doesn't change outcomes |

### Combined Effect: Recommended Configuration

```yaml
# price_oracle.yaml — recommended new defaults
enable_liveness_penalty: true
liveness_window: 300
confidence_exponent: 1.0

use_cost_floor: true
mining_cost_per_block_usd: 100000
cost_floor_margin_buffer: 0.05

factor_mapping: sigmoid
sigmoid_steepness_k: 6.0
apply_sigmoid_to: ["economic"]

max_divergence: 0.40  # Raised from 0.20

use_economic_ema: false  # Optional
```

### Backward Compatibility Mode

```yaml
# price_oracle.yaml — full backward compatibility
enable_liveness_penalty: false
use_cost_floor: false
factor_mapping: linear
max_divergence: 0.20
use_economic_ema: false
```

---

## Validation Plan

After implementing Proposals 1-3:

1. **Re-run sweep11** (econ=0.50, commit=0.20, 2016-block) — verify cascade still completes but with more realistic price dynamics
2. **Re-run sweep10** (econ=0.35-0.70, 2016-block) — map threshold with new oracle
3. **Create ghost town test** — scenario where one chain loses all hashrate early; verify price collapse
4. **Compare to BCH/BSV historical data** — calibrate sigmoid_k and liveness parameters

---

## References

- Kristoufek, L. (2015). What are the main drivers of the Bitcoin price? Evidence from wavelet coherence analysis. PLOS ONE, 10(4).
- Biais, B., Bisi, C., Bouvard, M., & Casamatta, C. (2019). The Blockchain Folk Theorem. Review of Financial Studies, 32(5), 1662-1715.
- Hayes, A. S. (2019). Bitcoin price and its marginal cost of production: support for a fundamental value. Applied Economics Letters, 26(7), 554-560.
- Peterson, T. (2018). Metcalfe's Law as a Model for Bitcoin's Value. Ledger, 3, 1-8.
- Wheatley, S., et al. (2019). Are Bitcoin bubbles predictable? Royal Society Open Science, 6(6).

---

## Appendix: Sweep Evidence Summary

| Sweep | Key Oracle Finding |
|-------|-------------------|
| sweep10 (144-block) | Ghost town: 0% hashrate for 600s, price only -6% |
| sweep11 (2016-block) | Cascade at econ=0.50 completes by t≈1200s; initial price parity matters |
| sweep9 (2016-block) | Difficulty retarget, not price, triggers committed pool capitulation |

*Document updated March 2026 based on targeted_sweep9, targeted_sweep10, and targeted_sweep11 findings*
