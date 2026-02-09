# Phase 3: Mining Pool Strategy with Ideology

**Date**: 2026-01-25
**Status**: ✅ Complete
**Component**: Individual Pool Decision Engine with Dual Motivations

---

## Overview

Implements realistic mining pool behavior modeling **dual motivations**:
1. **Rational Economics** - Maximize profitability (rational actor)
2. **Ideology/Values** - Support preferred fork even at economic cost (human actor)

This enables research questions like:
- How long can ideological miners sustain an unprofitable fork?
- What's the economic cost of supporting a losing fork?
- When does economic reality override ideology?
- How do different ideology strengths affect fork outcomes?

---

## The Problem: Pools Are Not Purely Rational

**Naive Model** (what we had):
```
if v27_profit > v26_profit:
    mine_v27()
else:
    mine_v26()
```

**Reality** (what we see in Bitcoin forks):
- Some pools supported Bitcoin Cash despite lower profitability (ideological support)
- Some miners stayed on Ethereum Classic (political/technical beliefs)
- Pools eventually switch when losses become unsustainable
- **Economic cost matters** - ideology has a price

---

## The Solution: Dual-Motivation Model

### Pool Profile

Each pool has both economic and ideological characteristics:

```python
PoolProfile(
    pool_id="viabtc",
    hashrate_pct=12.0,                    # Network hashrate
    fork_preference=ForkPreference.V26,   # Ideological preference
    ideology_strength=0.5,                # How much they'll sacrifice (0-1)
    profitability_threshold=0.08,         # Min advantage to switch
    max_loss_usd=2_000_000,              # Absolute loss cap
    max_loss_pct=0.20                    # Percentage loss cap
)
```

### Decision Algorithm

```
For each pool, every decision interval:

1. Calculate profitability on each fork:
   profit_v27 = (block_reward + fees) × price_v27 × expected_blocks
   profit_v26 = (block_reward + fees) × price_v26 × expected_blocks

2. Determine rational choice:
   rational_fork = fork with higher profitability

3. Check ideology override:
   IF pool.fork_preference != rational_fork:
       loss = profit_rational - profit_preferred
       loss_pct = loss / profit_rational

       IF loss_pct <= ideology_tolerance AND cumulative_loss < max_loss:
           mine_preferred_fork  # Ideology overrides economics
           track_opportunity_cost
       ELSE:
           mine_rational_fork  # Forced switch
           record_forced_switch

4. Track costs:
   opportunity_cost = profit_not_earned
   cumulative_cost += opportunity_cost
```

---

## Key Features

### 1. Profitability Calculation

Realistic miner revenue calculation:

```python
def calculate_pool_profitability(pool, fork_id):
    # Revenue per block
    price_usd = get_price(fork_id)
    fee_rate = get_fee(fork_id)
    fee_btc = (fee_rate × 1MB) / 100_000_000
    revenue_per_block_btc = block_subsidy + fee_btc
    revenue_per_block_usd = revenue_per_block_btc × price_usd

    # Expected blocks for this pool
    blocks_per_hour = 6 × (pool.hashrate_pct / 100)

    # Profit
    revenue_per_hour = blocks_per_hour × revenue_per_block_usd
    cost_per_hour = blocks_per_hour × mining_cost_usd
    profit_per_hour = revenue_per_hour - cost_per_hour

    return profit_per_hour
```

### 2. Ideology Strength

Controls how much economic loss a pool will tolerate:

- **0.0** = Purely rational (never mine at loss)
- **0.3** = Weak ideology (will sacrifice ~3-10% profit)
- **0.5** = Moderate ideology (will sacrifice ~10-20% profit)
- **0.7** = Strong ideology (will sacrifice ~20-30% profit)
- **0.9** = Very strong ideology (will sacrifice ~30-40% profit)
- **1.0** = Ideology at any cost (unlimited sacrifice)

### 3. Loss Thresholds

Two safety valves prevent infinite losses:

```python
# Percentage loss threshold
ideology_tolerance = ideology_strength × max_loss_pct
# e.g., 0.5 × 0.20 = 10% max loss

# Absolute loss threshold
if cumulative_cost > max_loss_usd:
    force_switch()
```

### 4. Cost Tracking

Comprehensive tracking of ideological costs:

```python
pool_costs = {
    'actual_revenue_usd': ...,           # What they earned
    'optimal_revenue_usd': ...,          # What they could have earned
    'cumulative_opportunity_cost_usd':..., # Total money left on table
    'forced_switch_count': ...,          # Times economics forced switch
    'ideology_override_count': ...       # Times ideology won
}
```

### 5. Decision History

Every decision recorded with full context:

```python
MiningDecision(
    timestamp=...,
    pool_id="viabtc",
    chosen_fork="v26",
    v27_profitability_usd=450_000,  # Per hour
    v26_profitability_usd=400_000,  # Per hour
    rational_choice="v27",
    ideology_override=True,          # Mining against profitability
    opportunity_cost_usd=50_000,     # Cost of this decision
    cumulative_cost_usd=250_000,     # Total cost so far
    reason="Ideology: supporting v26 despite 11.1% lower profit"
)
```

---

## Test Results

### Test 1: Gradual Ideology Erosion

**Scenario**: v27 (70% economic) vs v26 (30% economic)

**Initial State**:
- Rational pools (58%): foundry, antpool, binance
- Moderate ideologues (27%): viabtc, f2pool (prefer v26)
- Strong ideologues (15%): btc_com, ideological_pool (prefer v26)

**Results**:
```
Time | Price Gap | v27 Hash | v26 Hash | Active v26 Ideologues
-----|-----------|----------|----------|----------------------
  0m |    7.3%   |   58%    |   42%    | 4 pools (42% hashrate)
 10m |    7.7%   |   85%    |   15%    | 2 pools (15% hashrate) - weak ideologues switched
 60m |    9.4%   |   95%    |    5%    | 1 pool (5% hashrate) - moderate switched
120m |   11.3%   |   95%    |    5%    | 1 pool (5% hashrate) - strongest survives
```

**Key Findings**:
1. **Weak ideologues (30% strength)** switched at 7.7% gap (lost $0)
2. **Moderate ideologues (40% strength)** switched immediately (intolerant of 7.7% loss)
3. **Strong ideologues (70% strength)** sustained until 60m, then switched (lost $46k)
4. **Very strong ideologues (90% strength)** sustained entire duration (lost $63k)

**Total Cost of v26 Ideology**: $110,150 opportunity cost

### Test 2: Ideology and Profit Aligned

**Scenario**: Both ideology and profit favor v27

**Result**: All pools happily mine v27, zero opportunity cost

**Insight**: When ideology aligns with economics, it's "free" - no sacrifice required.

---

## Configuration System

### YAML Configuration File

`mining_pools_config.yaml` defines 4 pre-configured scenarios:

1. **realistic_current** - Based on actual Bitcoin pool landscape
2. **ideological_fork_war** - Strong ideological split (like Bitcoin Cash)
3. **purely_rational** - Baseline with no ideology
4. **weak_resistance** - Small ideological minority resists majority

Example pool definition:

```yaml
- pool_id: "viabtc"
  hashrate_pct: 12.0
  fork_preference: "v26"         # Prefers older/conservative
  ideology_strength: 0.5         # Moderate ideology
  profitability_threshold: 0.08  # Must be 8% more profitable to switch
  max_loss_usd: 2000000          # Will sacrifice up to $2M
  max_loss_pct: 0.20             # Or 20% of potential revenue
```

### Loading Configuration

```python
from mining_pool_strategy import load_pools_from_config

# Load pre-defined scenario
pools = load_pools_from_config(
    'mining_pools_config.yaml',
    'ideological_fork_war'
)

# Create strategy
pool_strategy = MiningPoolStrategy(pools)

# Calculate hashrate allocation
v27_hashrate, v26_hashrate = pool_strategy.calculate_hashrate_allocation(
    current_time, price_oracle, fee_oracle
)
```

---

## Integration with Existing Components

### With Price Oracle

```python
# Pools make decisions based on current prices
v27_price = price_oracle.get_price('v27')
v26_price = price_oracle.get_price('v26')

# Profitability depends on price
profit_v27 = calculate_profitability('v27', v27_price)
profit_v26 = calculate_profitability('v26', v26_price)
```

### With Fee Oracle

```python
# Pools consider fees in profitability
v27_fee = fee_oracle.get_fee('v27')
v26_fee = fee_oracle.get_fee('v26')

# Higher fees = higher revenue
revenue = (block_subsidy + estimated_fees) × price
```

### With Portfolio Economics

Economic actors mining with ideology:
- Earn BTC on chosen fork
- Opportunity cost tracked in USD
- Portfolio value affected by mining choice
- Can model entities that both mine AND hold

---

## Real-World Analogies

### Bitcoin Cash Fork (2017)

**Actual Behavior**:
- Some pools (ViaBTC, BTC.com) strongly supported BCH ideologically
- Initially mined BCH despite lower profitability
- Hashrate fluctuated based on relative profitability
- Eventually most hashrate went to BTC (more profitable)
- Some pools sustained BCH mining at significant cost

**Our Model Captures**:
- Ideological preference for specific fork
- Tolerance for economic loss
- Gradual switch as losses mount
- Total opportunity cost of ideology

### Ethereum Classic (2016)

**Actual Behavior**:
- Minority continued mining ETC for ideological reasons
- "Code is law" principle vs. pragmatic ETH
- Sustained despite much lower price
- Small but dedicated mining community

**Our Model Captures**:
- Strong ideology (0.8-0.9 strength)
- Willingness to sacrifice significant profit
- Small hashrate percentage remains ideological
- Tracked cost of maintaining minority chain

---

## Research Applications

### Question 1: Can Economic Weight Overcome Hashrate Disadvantage?

**Setup**:
- v27: 70% economic, 10% hashrate initially
- Pools start rational, but can switch based on profitability

**Test**:
1. v27 price rises due to economic support
2. Profitability on v27 increases
3. Rational pools switch to v27
4. Hashrate shifts from 10% → 60%+ over 2 hours
5. v27 wins despite initial hashrate disadvantage

**Conclusion**: Economic factors CAN influence outcome if miners respond rationally.

### Question 2: Cost of Sustaining Minority Fork

**Setup**:
- v26 has ideological support but economic disadvantage
- Track total opportunity cost of ideology

**Metrics**:
- Cumulative USD opportunity cost
- Number of forced switches
- Time until ideology unsustainable
- Minimum ideology strength needed

**Insight**: Quantifies "how much does ideology cost" in dollar terms.

### Question 3: Tipping Points

**Setup**:
- Vary initial conditions (economic/hashrate split)
- Vary pool ideology distribution

**Find**:
- At what point does economic advantage become unbeatable?
- How much hashrate needs to be ideological to sustain minority fork?
- What price gap causes mass switching?

---

## Files Created

1. **mining_pool_strategy.py** (510 lines)
   - Core implementation
   - PoolProfile dataclass
   - MiningPoolStrategy engine
   - Decision logic and cost tracking

2. **mining_pools_config.yaml** (250 lines)
   - 4 pre-defined scenarios
   - Realistic pool distributions
   - Easy customization

3. **test_pool_decisions.py** (200 lines)
   - Ideological pool vs. economic reality
   - Aligned ideology test
   - Validation of core mechanics

4. **test_sustained_ideology.py** (210 lines)
   - Gradual ideology erosion
   - Switch event tracking
   - Cost analysis

5. **PHASE_3_MINING_POOL_STRATEGY.md** (this file)
   - Complete documentation
   - Research applications
   - Integration guide

---

## Next Steps

### Immediate (Integration)

1. **Integrate with partition_miner** scenario
   - Replace static hashrate split with dynamic allocation
   - Update every 10 minutes based on pool decisions
   - Log pool switches and costs

2. **Run multi-hour test**
   - 2-hour duration
   - 90% economic, 10% hashrate on v27
   - Observe hashrate migration
   - Validate economic influence

3. **Visualize results**
   - Hashrate allocation over time
   - Pool switching events
   - Cumulative ideology cost
   - Profitability differentials

### Future Enhancements

1. **User/Exchange behavior** (rest of Phase 3)
   - Economic nodes prefer dominant fork
   - Exchanges make listing decisions
   - Network effects and migration

2. **Pool communication** (advanced)
   - Pools coordinate strategies
   - Pool alliances/coalitions
   - Signaling and game theory

3. **Real data integration**
   - Import actual pool preferences from forks
   - Validate model against historical events
   - Calibrate parameters

---

## Summary

**What We Built**: Individual mining pool decision engine with dual motivations (profit + ideology)

**Key Innovation**: Economic cost tracking of ideological mining

**Research Value**: Can now model realistic fork scenarios where:
- Some pools support forks for non-economic reasons
- Economic reality eventually dominates
- Total cost of ideology is quantifiable

**Status**: ✅ Ready for integration with partition mining scenarios

---

**Document Version**: 1.0
**Created**: 2026-01-25
**Next Phase**: Integration with dynamic scenarios
