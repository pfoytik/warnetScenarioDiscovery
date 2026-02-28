# Parameter Sweep Findings

## Overview

This document summarizes findings from two parameter sweeps exploring Bitcoin fork dynamics:

| Sweep | Scenarios | Network | Duration | Block Interval | Retarget |
|-------|-----------|---------|----------|----------------|----------|
| realistic_sweep2 | 50 | 60 nodes | 30 min | 10s | 144 blocks |
| exploratory_sweep_lite | 50 | 25 nodes | 42 min | 2s | 144 blocks |

**Combined dataset: 100 scenarios**

### Known Limitations

Both sweeps had a bug where `economic_split` was sampled correctly but not applied to the network. All scenarios ran with 50/50 economic distribution regardless of the parameter value. Findings related to economic distribution should be validated with corrected code.

---

## Outcome Distribution

| Sweep | v27 Dominant | v26 Dominant | Contested |
|-------|--------------|--------------|-----------|
| realistic_sweep2 | 28 (56%) | 19 (38%) | 3 (6%) |
| exploratory_sweep_lite | 26 (52%) | 24 (48%) | 0 (0%) |
| **Combined** | **54 (54%)** | **43 (43%)** | **3 (3%)** |

The balanced outcome distribution indicates the parameter space was sampled without strong bias toward either fork.

---

## Key Correlations

### Parameters Correlated with v27 Success

| Parameter | realistic_sweep2 | exploratory_lite | Combined Avg | Interpretation |
|-----------|------------------|------------------|--------------|----------------|
| **hashrate_split** | +0.814 | +0.853 | **+0.83** | Higher initial hashrate strongly favors v27 |
| **user_ideology_strength** | +0.168 | +0.233 | **+0.20** | Committed users help v27 sustain |
| **pool_max_loss_pct** | +0.106 | +0.164 | **+0.14** | Pools willing to absorb losses help v27 |

### Parameters Correlated with v26 Success

| Parameter | realistic_sweep2 | exploratory_lite | Combined Avg | Interpretation |
|-----------|------------------|------------------|--------------|----------------|
| **econ_ideology_strength** | -0.141 | -0.154 | **-0.15** | Sticky institutions preserve v26 advantage |
| **pool_profitability_threshold** | -0.071 | -0.156 | **-0.11** | Higher thresholds slow pool switching |

### Parameters with Minimal Effect

| Parameter | Correlation | Notes |
|-----------|-------------|-------|
| pool_ideology_strength | ~0 | No significant effect detected |
| transaction_velocity | ~0 | Minimal impact on outcomes |
| economic_split | ~0.06 | Bug - parameter not applied |

---

## Critical Thresholds

These thresholds represent the approximate values where outcomes shift from v26-dominant to v27-dominant:

| Parameter | Threshold | v27 Favored When | Confidence |
|-----------|-----------|------------------|------------|
| **hashrate_split** | ~0.47-0.49 | Higher (>47%) | Very High |
| **pool_neutral_pct** | ~30% | Higher (>30%) | High |
| **user_ideology_strength** | ~0.50 | Higher (>0.50) | Medium-High |
| **econ_ideology_strength** | ~0.40 | Lower (<0.40) | Medium |
| **pool_committed_split** | ~0.50 | Higher (>0.50) | Medium |
| **pool_max_loss_pct** | ~0.25 | Higher (>25%) | Medium |

---

## Detailed Findings

### 1. Hashrate Dominance (Correlation: +0.83)

**The starting hashrate split is the single most important predictor of fork outcomes.**

- v27 dominant scenarios: mean hashrate_split = 0.72
- v26 dominant scenarios: mean hashrate_split = 0.23
- Threshold: ~47-49%

This finding is highly robust, replicating consistently across both sweeps with correlations of +0.814 and +0.853.

**Implication:** A fork needs roughly half the network hashrate to have a realistic chance of success. Below ~40%, success is unlikely regardless of other factors.

### 2. Pool Neutrality Effect (Threshold: ~30%)

**When more pools are profit-driven ("neutral"), the challenger fork benefits.**

- v27 dominant: mean pool_neutral_pct = 32%
- v26 dominant: mean pool_neutral_pct = 27%
- Separation: 4-5 percentage points

**Mechanism:** Neutral pools follow profitability signals. If v27 gains hashrate advantage, it becomes more profitable (faster blocks, difficulty adjustment), attracting rational pools. Ideologically committed pools resist switching regardless of profitability.

**Implication:** Fork success depends partly on the ideological composition of the mining ecosystem. A network with many profit-driven pools is more susceptible to hashrate-driven forks.

### 3. User Ideology Effect (Correlation: +0.20)

**Users with higher conviction help the challenger fork sustain through early disadvantage.**

- v27 dominant: mean user_ideology_strength = 0.55
- v26 dominant: mean user_ideology_strength = 0.44
- Threshold: ~0.50

**Mechanism:** Committed users maintain economic activity on v27 even when it's disadvantaged, providing price support and transaction fees. This helps pools justify staying on v27 during difficult periods.

### 4. Economic Ideology Effect (Correlation: -0.15)

**Higher economic node ideology correlates with v26 success.**

- v27 dominant: mean econ_ideology_strength = 0.37
- v26 dominant: mean econ_ideology_strength = 0.44
- Threshold: ~0.40

**Mechanism:** The base network has more economic weight on v26 (larger exchanges like Binance). When economic nodes are ideologically committed (high ideology strength), this advantage is preserved. When they're rational (low ideology strength), they may shift toward the more secure/profitable chain.

**Implication:** A challenger fork can attract economic support IF:
1. It has hashrate advantage (security)
2. Economic actors are profit-driven rather than ideologically committed

### 5. Pool Loss Tolerance (Correlation: +0.14)

**Pools willing to absorb larger losses for ideology help the challenger.**

- v27 dominant: mean pool_max_loss_pct = 0.28
- v26 dominant: mean pool_max_loss_pct = 0.23

**Mechanism:** Higher loss tolerance allows committed pools to stay on v27 during temporary disadvantages, preventing cascade effects where pools abandon ship at the first sign of trouble.

---

## Fork Dynamics Model

Based on these findings, fork outcomes follow this general pattern:

```
CHALLENGER (v27) VICTORY CONDITIONS:
┌────────────────────────────────────────────────────────────┐
│  1. hashrate_split > 47%        [REQUIRED - most important]│
│  2. pool_neutral_pct > 30%      [Helps - pools follow $]   │
│  3. user_ideology > 0.50        [Helps - sustained support]│
│  4. econ_ideology < 0.40        [Helps - flexible exchanges│
│  5. pool_max_loss > 25%         [Helps - pools can hold]   │
└────────────────────────────────────────────────────────────┘

INCUMBENT (v26) VICTORY CONDITIONS:
┌────────────────────────────────────────────────────────────┐
│  1. hashrate_split < 47%        [REQUIRED - majority stays]│
│  2. pool_neutral_pct < 30%      [Helps - committed pools]  │
│  3. econ_ideology > 0.40        [Helps - sticky exchanges] │
└────────────────────────────────────────────────────────────┘

CONTESTED SCENARIOS (rare, 3% of outcomes):
┌────────────────────────────────────────────────────────────┐
│  hashrate_split ≈ 0.37-0.47     [Near threshold]           │
│  + high pool_max_loss_pct       [Pools willing to fight]   │
│  + moderate pool_neutral_pct    [Mixed commitment levels]  │
└────────────────────────────────────────────────────────────┘
```

---

## Confidence Assessment

| Finding | Confidence | Rationale |
|---------|------------|-----------|
| Hashrate dominance | **Very High** | +0.83 correlation, consistent across 100 scenarios |
| Pool neutrality threshold ~30% | **High** | Consistent threshold, 4-5pt separation |
| User ideology effect | **Medium-High** | Consistent direction, +0.20 correlation |
| Economic ideology effect | **Medium** | Consistent direction, but economic_split bug limits interpretation |
| Pool loss tolerance effect | **Medium** | Smaller effect size, but consistent |
| Contested scenario conditions | **Low** | Only 3 examples in dataset |

---

## Recommendations for Future Work

### 1. Fix Economic Split Bug
The `economic_split` parameter was not properly applied. A corrected sweep would reveal whether economic distribution can overcome hashrate disadvantage.

### 2. Longer Duration Sweeps
With 2016-block retarget intervals (realistic Bitcoin), explore whether minority forks can survive long enough for difficulty adjustment to improve their competitiveness.

### 3. Targeted Scenarios
Run focused scenarios around the identified thresholds:
- hashrate_split: 0.40-0.55 range
- pool_neutral_pct: 25-35% range

### 4. Reorg Analysis
Deeper analysis of reorg patterns in contested scenarios could reveal the "cost" of sustained fork competition.

---

## Data Sources

- `realistic_sweep2/results/analysis/` - 50 scenarios, 60-node network
- `exploratory_sweep_lite/results/analysis/` - 50 scenarios, 25-node network
- Combined analysis performed February 2026

## Appendix: Parameter Definitions

| Parameter | Range | Description |
|-----------|-------|-------------|
| economic_split | 0-1 | Fraction of economic custody starting on v27 |
| hashrate_split | 0-1 | Fraction of initial pool hashrate on v27 |
| pool_ideology_strength | 0.1-0.9 | How much pools sacrifice for ideology |
| pool_profitability_threshold | 2-30% | Min profit advantage for pools to switch |
| pool_max_loss_pct | 2-50% | Max revenue loss pools tolerate for ideology |
| pool_committed_split | 0-1 | Fraction of committed pool hashrate preferring v27 |
| pool_neutral_pct | 10-50% | Percentage of pools that are neutral/rational |
| econ_ideology_strength | 0-0.8 | How much economic nodes sacrifice for ideology |
| user_ideology_strength | 0.1-0.9 | How much users sacrifice for ideology |
| transaction_velocity | 0.1-0.9 | Fee-generating transaction rate |
