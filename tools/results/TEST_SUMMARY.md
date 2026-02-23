# Fork Scenario Test Summary

Generated: 2026-02-22

This document summarizes all fork simulation tests conducted, organized by scenario type.

---

## Quick Reference

| Category | Tests | v27 Wins | v26 Wins | Key Finding |
|----------|-------|----------|----------|-------------|
| Softfork (UASF) | 7 | 2 | 5 | Retarget interval is decisive; 2016-block favors majority |
| Softfork (Other) | 6 | 2 | 4 | Economic commitment matters less than hashrate |
| Hardfork | 18 | 5 | 13 | Ideological war scenarios consistently favor v26 |

---

## Softfork Scenarios

### UASF Tests (User-Activated Soft Fork)

These tests simulate a time-limited soft fork enforcement with configurable expiry actions.

#### uasf_2016Interval_reunited
| Parameter | Value |
|-----------|-------|
| Duration | 60 min |
| UASF Duration | 30 min |
| Retarget Interval | 2016 blocks |
| Pool Scenario | v26_dominant_committed |
| Economic Scenario | strong_v26_resistance |

**Result: v26 WINS**
- Blocks: v27=544, v26=3,034
- Chainwork: v27=544.0, v26=2,765.28
- Final Hashrate: v27=0%, v26=100%
- Final Prices: v27=$55,789, v26=$64,211

**Key Insight**: With realistic 2016-block retarget, v27 never reached a difficulty adjustment (stuck at 544 blocks). v26 adjusted once (difficulty 0.736) and accelerated block production.

---

#### uasf_multiblock_reunited
| Parameter | Value |
|-----------|-------|
| Duration | 60 min |
| Retarget Interval | 144 blocks |
| Pool Scenario | v26_dominant_committed |
| Economic Scenario | strong_v26_resistance |

**Result: v27 WINS**
- Blocks: v27=3,166, v26=1,241
- Chainwork: v27=2,228.15, v26=744.57
- Final Hashrate: v27=100%, v26=0%
- Final Prices: v27=$64,788, v26=$55,212

**Key Insight**: Faster 144-block retarget allowed minority fork to adjust difficulty quickly and compete. Multi-block mining fix verified working.

---

#### uasf_test_30min / uasf_test_fixed
| Parameter | Value |
|-----------|-------|
| Duration | 60 min |
| Pool Scenario | v26_dominant_committed |
| Economic Scenario | strong_v26_resistance |

**Result: v26 WINS**
- Blocks: v27~108, v26~300
- Chainwork: v27~108, v26~250
- Final Hashrate: v27=26.9%, v26=71.5%

**Key Insight**: Without multi-block fix, v26 maintained dominance.

---

### v26 Dominant Scenarios

#### v26dominant_committed (120 min)
**Result: v26 WINS**
- Blocks: v27=1,975, v26=6,094
- Chainwork: v27=1,975, v26=4,738.71
- Final Hashrate: v27=26.9%, v26=71.5%
- Final Prices: v27=$58,010, v26=$61,912

---

#### v26dominant_committed_reunion (120 min)
**Result: v26 WINS**
- Blocks: v27=1,895, v26=5,745
- Chainwork: v27=1,895, v26=4,356.73
- Final Hashrate: v27=26.9%, v26=71.5%

---

#### v26dominant_full_suite (120 min)
**Result: v26 WINS**
- Blocks: v27=222, v26=6,758
- Chainwork: v27=222, v26=6,060.71
- Final Hashrate: v27=0%, v26=98.4%
- Final Prices: v27=$54,857, v26=$65,065

**Key Insight**: Non-committed v26 pools led to near-total v26 dominance.

---

### Other Softfork Scenarios

#### asymmetric_test_001 (15 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| asymmetric_softfork | asymmetric_softfork |

**Result: v26 WINS (marginal)**
- Blocks: v27=41, v26=43
- Final Hashrate: 50/50
- Final Economic: v27=70%, v26=30%
- Reorg Events: 0

---

#### balanced_4hr_test (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| asymmetric_balanced | asymmetric_balanced |

**Result: v27 WINS (decisive)**
- Blocks: v27=1,424, v26=41
- Chainwork: v27=1,406.02, v26=41.0
- Reorg Events: 4
- Reorg Mass: 107 blocks
- Orphan Rate: 2.73%

**Key Insight**: 4-hour run showed clear convergence toward v27 after initial uncertainty.

---

#### dynamic_switch_test_001 (30 min)
**Result: v26 WINS**
- Blocks: v27=55, v26=119
- Final Hashrate: v27=32.4%, v26=67.6%
- Reorg Events: 2
- Reorg Mass: 34 blocks
- Orphan Rate: 3.45%

---

#### standoff_4hr_test (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| ideological_standoff | ideological_standoff |

**Result: v27 WINS (by chainwork)**
- Blocks: v27=1,037, v26=1,000
- Chainwork: v27=758.79, v26=680.93
- Final Hashrate: v27=31.3%, v26=68.7%
- Final Prices: v27=$59,897, v26=$60,103

**Key Insight**: Despite v26 having more hashrate, v27's difficulty adjustments led to higher chainwork accumulation.

---

#### idwar_reunion_test (15 min)
**Result: v26 WINS**
- Blocks: v27=18, v26=80
- Final Hashrate: v27=0%, v26=98.4%

---

## Hardfork Scenarios

### Close Battle Series

These scenarios test tight competition between forks.

#### close_battle_test (120 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| close_battle | realistic_current |

**Result: v27 WINS**
- Blocks: v27=681, v26=86
- Final Hashrate: v27=98.4%, v26=0%
- Reorg Events: 7
- Reorg Mass: 571 blocks
- Orphan Rate: 15.25%

---

#### close_battle_021326 (120 min)
**Result: v27 WINS**
- Blocks: v27=658, v26=123
- Final Hashrate: v27=79.1%, v26=19.2%
- Reorg Events: 6
- Reorg Mass: 954 blocks
- Orphan Rate: 25.38%

---

#### close_battle_null (120 min)
**Result: v27 WINS**
- Blocks: v27=657, v26=125
- Final Hashrate: v27=98.4%, v26=0%
- Reorg Events: 7
- Reorg Mass: 736 blocks
- Orphan Rate: 20.20%

---

#### close_idSplit_021326 (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| close_battle | ideological_split |

**Result: v27 WINS**
- Blocks: v27=1,302, v26=507
- Final Hashrate: v27=98.4%, v26=0%
- Reorg Events: 31
- Reorg Mass: 17,089 blocks
- **Orphan Rate: 78.04%** (highest recorded)

**Key Insight**: Extreme volatility with ideological split economics led to massive reorg activity.

---

### Ideological War Series

These scenarios test entrenched opposition between forks.

#### ideological_war_120min_test
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| ideological_war | realistic_current |

**Result: v26 WINS (by chainwork)**
- Blocks: v27=417, v26=554
- Chainwork: v27=346.85, v26=373.81
- Final Hashrate: v27=59.5%, v26=38.9%
- Reorg Events: 22
- Reorg Mass: 7,378 blocks
- **Orphan Rate: 76.43%**

**Key Insight**: High volatility scenario with frequent pool switching.

---

#### det_idWar_021226 / det_idWar_021326 (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| ideological_war | ideological_split |

**Result: v26 WINS (both runs)**
- Blocks: v27~89, v26~1,409
- Final Hashrate: v27=0%, v26=98.4%
- Reorg Events: 9
- Reorg Mass: 1,950 blocks
- Orphan Rate: 10.45%

**Key Insight**: Deterministic outcome; ideological war with split economics consistently favors v26.

---

#### idWar_seed_021326 / idWar_seed_0213261 / idWar_seed0213262 / idWar_seed0213263 (240 min)
Multiple seed variations testing reproducibility.

**Result: v26 WINS (all runs)**
- Blocks: v27=99-117, v26=1,397-1,435
- Final Hashrate: v27=0%, v26=98.4%
- Reorg Events: 7-11
- Orphan Rate: 11-15%

**Key Insight**: Consistent v26 victory across different random seeds.

---

#### idWar_close_021426 (240 min)
**Result: v26 WINS**
- Blocks: v27=110, v26=1,414
- Reorg Events: 11
- Reorg Mass: 1,892 blocks
- Orphan Rate: 11.88%

---

#### idWar_strongv27_021326 (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| ideological_war | strong_v26_resistance |

**Result: v26 WINS**
- Blocks: v27=110, v26=1,413
- Reorg Events: 11
- Orphan Rate: 10.94%

**Key Insight**: Even with "strong v27" label, v26 wins due to pool dynamics.

---

### Purely Rational Scenarios

These test behavior when economic incentives dominate.

#### purely_rational_021326 (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| purely_rational | purely_rational |

**Result: v27 WINS**
- Blocks: v27=1,433, v26=33
- Final Hashrate: v27=100%, v26=0%
- Final Economic: v27=100%, v26=0%
- Final Prices: v27=$71,829, v26=$48,171
- Reorg Events: 2
- Orphan Rate: 0%

**Key Insight**: Purely rational actors converge quickly to majority fork with minimal disruption.

---

#### close_purely_ideological (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| purely_rational | ideological_split |

**Result: v27 WINS**
- Blocks: v27=1,440, v26=31
- Final Hashrate: v27=100%, v26=0%
- Final Economic: v27=100%, v26=0%
- Reorg Events: 2
- Orphan Rate: 0%

---

#### close_ideological_purely (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| ideological_war | purely_rational |

**Result: v26 WINS**
- Blocks: v27=97, v26=1,405
- Final Hashrate: v27=0%, v26=98.4%
- Final Economic: v27=0%, v26=100%
- Reorg Events: 5
- Orphan Rate: 6.27%

**Key Insight**: Pool ideology (ideological_war) matters more than economic scenario.

---

### User-Heavy Scenarios

#### userHeavy_ideological_ideological (240 min)
**Result: v26 WINS**
- Blocks: v27=110, v26=1,413
- Reorg Events: 11
- Orphan Rate: 10.94%

---

#### userHeavy_weakResist_realistic_current (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| weak_resistance | realistic_current |

**Result: v26 WINS**
- Blocks: v27=21, v26=1,435
- Final Hashrate: v27=0%, v26=100%
- Reorg Events: 2
- Orphan Rate: 0%

**Key Insight**: Weak resistance leads to rapid v26 dominance.

---

### Realistic Scenarios

#### custodyVvolume_realistic_realistic (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| realistic_current | realistic_current |

**Result: v27 WINS**
- Blocks: v27=1,435, v26=38
- Final Hashrate: v27=98.4%, v26=0%
- Final Economic: v27=100%, v26=0%
- Reorg Events: 3
- Orphan Rate: 2.24%

**Key Insight**: Realistic current conditions favor v27 adoption.

---

#### flawed_idWar (240 min)
| Pool Scenario | Economic Scenario |
|---------------|-------------------|
| realistic_current | realistic_current |

**Result: TIE (stalemate)**
- Blocks: v27=1,292, v26=1,282
- Chainwork: v27=755.06, v26=714.21
- Final Hashrate: 50/50
- Final Economic: v27=70%, v26=30%
- Reorg Events: 0

**Key Insight**: Perfect balance scenario with no pool switching.

---

## Key Findings

### 1. Retarget Interval is Decisive
- **2016-block retarget** (realistic): Strongly favors the hashrate-majority fork
- **144-block retarget** (test mode): Allows minority forks to compete via faster difficulty adjustment

### 2. Pool Ideology Dominates Economics
- When pools are ideologically committed, economic incentives have limited effect
- `ideological_war` pool scenario consistently produces v26 victories regardless of economic scenario

### 3. Purely Rational Behavior Minimizes Disruption
- `purely_rational` scenarios show rapid convergence with minimal reorgs (0-2% orphan rate)
- Ideological scenarios show high volatility (10-78% orphan rates)

### 4. Reorg Metrics Correlate with Uncertainty
- Close battles: 15-25% orphan rates
- Ideological standoffs: 10-15% orphan rates
- Ideological splits with close hashrate: Up to 78% orphan rates

### 5. Price Divergence Reflects Outcome
- Winning fork typically reaches $64,000-72,000
- Losing fork typically falls to $48,000-56,000
- Equal splits hover around $57,000-62,000 each

---

## Test Parameters Reference

### Pool Scenarios
| Name | Description |
|------|-------------|
| `v26_dominant` | v26 has hashrate majority, pools follow profit |
| `v26_dominant_committed` | v26 majority with ideological commitment |
| `ideological_war` | Pools split by ideology, resist switching |
| `ideological_standoff` | Entrenched positions, high switching cost |
| `close_battle` | Near-equal hashrate split |
| `purely_rational` | All pools follow profit maximization |
| `weak_resistance` | Minimal opposition to change |
| `realistic_current` | Based on current pool distribution |

### Economic Scenarios
| Name | Description |
|------|-------------|
| `strong_v26_resistance` | Economic actors prefer v26 |
| `ideological_split` | Economic actors divided by ideology |
| `purely_rational` | Economic actors follow price signals |
| `realistic_current` | Based on current market conditions |

---

## Files Per Test

Each test directory contains:
- `summary.txt` - Human-readable summary
- `metadata.json` - Configuration and parameters
- `time_series.csv` - Tick-by-tick simulation data
- `pool_decisions.csv` - Pool switching decisions with costs
- `partition_difficulty.json` - Difficulty adjustment history (if enabled)
- `reorg_metrics.json` - Reorg tracking data (if enabled)
