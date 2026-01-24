# Dynamic Economic Models - Implementation Plan

## Executive Summary

Transform static 30-minute fork tests into dynamic multi-hour simulations where nodes respond to economic incentives. This will enable testing whether economic weight (custody/volume) can influence fork outcomes when given time to exert pressure through price signals, fee markets, and miner profitability.

**Current State:**
- ✅ 30-min tests, static partitions
- ✅ Hashrate perfectly predicts outcomes (r=0.96)
- ❌ Economic factors negligible (r=-0.07)
- ❌ No price model, no fees, no dynamic switching

**Target State:**
- Multi-hour tests (2-6 hours)
- Price divergence between forks
- Fee market dynamics per fork
- Miners switch chains based on profitability
- Users/exchanges prefer economically dominant chain

---

## Phase 1: Price Model Foundation
**Goal:** Implement basic price discovery mechanism for forked chains

### 1.1 Price Oracle Infrastructure (Week 1-2)

**Deliverables:**
- `price_oracle.py` - Price tracking service
- Price storage (SQLite or JSON time-series)
- Price query API for nodes

**Components:**
```python
class PriceOracle:
    """Tracks token prices for each fork"""

    def get_price(self, chain_id: str) -> float:
        """Returns current price for chain"""

    def update_price(self, chain_id: str, new_price: float):
        """Update price based on market signals"""

    def get_price_history(self, chain_id: str) -> List[Tuple[time, price]]:
        """Historical prices for analysis"""
```

**Implementation Details:**
- Start both chains at same price (e.g., $60,000)
- Store prices with timestamps
- Expose via REST API or RPC for node queries
- Integration point: Read by miner decision logic

**Testing:**
- Unit tests: Price storage/retrieval
- Integration: Query from scenario script
- Validation: Price persistence across test duration

### 1.2 Price Divergence Model (Week 2-3)

**Deliverables:**
- Price update algorithm based on chain fundamentals
- Configuration for divergence parameters
- Visualization of price evolution

**Model Options:**

**Option A: Supply/Demand Based (Simple)**
```python
def calculate_price_change(chain):
    """
    Price influenced by:
    - Chain weight (blocks behind = sell pressure)
    - Economic nodes on chain (buying support)
    - Custody concentration (holder confidence)
    """
    weight_factor = 1.0 - (blocks_behind / total_blocks) * 0.2
    economic_factor = (custody_pct / 100) * 1.1
    new_price = base_price * weight_factor * economic_factor
    return new_price
```

**Option B: Order Book Simulation (Complex)**
```python
class OrderBook:
    """Simulated exchange order book per chain"""

    def add_buy_order(amount_btc, price):
        """Economic nodes buying their chain"""

    def add_sell_order(amount_btc, price):
        """Miners selling for profitability"""

    def match_orders() -> float:
        """Return market clearing price"""
```

**Recommendation:** Start with Option A for Phase 1, upgrade to Option B in Phase 3.

**Configuration:**
```yaml
price_model:
  enabled: true
  update_interval: 60  # Update every 60 seconds
  divergence_rate: 0.05  # Max 5% price change per update
  base_price: 60000
  factors:
    chain_weight: 0.3
    economic_weight: 0.5
    hashrate_weight: 0.2
```

**Integration Points:**
- Called by scenario every minute
- Reads: block heights, economic distributions, hashrate
- Outputs: Updated prices stored in oracle

**Testing:**
- Scenario: Fork with 90% economic on Chain A, 90% hashrate on Chain B
- Expected: Chain A price increases, Chain B decreases over time
- Validation: Price ratio ~= economic ratio after 2 hours

### 1.3 Price API & Monitoring (Week 3)

**Deliverables:**
- Price query RPC for scenarios
- Price logging to test results
- Real-time price dashboard (optional)

**API:**
```python
# In partition_miner.py scenario
from price_oracle import PriceOracle

oracle = PriceOracle()
v27_price = oracle.get_price('v27')
v26_price = oracle.get_price('v26')
price_ratio = v27_price / v26_price

logger.info(f"Price ratio: {price_ratio:.2f} (v27/v26)")
```

**Data Export:**
```json
{
  "price_timeline": {
    "timestamps": [0, 60, 120, ...],
    "v27_prices": [60000, 60100, 60150, ...],
    "v26_prices": [60000, 59900, 59850, ...]
  }
}
```

**Milestone:** End of Phase 1
- ✅ Price divergence working in test scenarios
- ✅ Prices logged and exportable
- ✅ Validated against expected behavior
- ⚠️ Not yet influencing node behavior (Phase 2)

---

## Phase 2: Fee Market Dynamics
**Goal:** Model mempool fees per fork, miners prefer higher-fee chain

### 2.1 Mempool Fee Tracker (Week 4-5)

**Deliverables:**
- `fee_tracker.py` - Tracks fee rates per chain
- Fee query API
- Integration with price model

**Components:**
```python
class FeeTracker:
    """Tracks mempool fee rates for each chain"""

    def get_median_fee(self, chain_id: str) -> float:
        """Returns median fee rate in sat/vB"""

    def update_fees(self, chain_id: str, transaction_volume: float):
        """Update fees based on congestion"""

    def get_fee_history(self, chain_id: str) -> List[Tuple[time, fee]]:
        """Historical fees"""
```

**Fee Model:**
```python
def calculate_fees(chain):
    """
    Fees influenced by:
    - Economic nodes on chain (more users = more txs = higher fees)
    - Block production rate (slower blocks = backlog = higher fees)
    - Chain preference (users paying more to transact on preferred chain)
    """
    tx_volume = sum(node.daily_volume_btc for node in economic_nodes_on_chain)
    blocks_per_hour = blocks_mined_last_hour
    congestion = tx_volume / (blocks_per_hour * block_capacity)

    base_fee = 10  # sat/vB
    fee = base_fee * (1 + congestion * 0.5)
    return fee
```

**Configuration:**
```yaml
fee_model:
  enabled: true
  update_interval: 60
  base_fee: 10  # sat/vB
  block_capacity: 3000  # transactions per block
  congestion_multiplier: 0.5
```

**Integration:**
- Reads: Economic node distributions, block production rate
- Outputs: Fee estimates per chain
- Used by: Miner profitability calculations

**Testing:**
- Scenario: Chain A has 80% economic nodes
- Expected: Chain A has higher fees due to more transaction demand
- Validation: Fee ratio ~= economic ratio

### 2.2 Miner Revenue Model (Week 5-6)

**Deliverables:**
- Miner profitability calculator
- Revenue comparison between chains
- Revenue logging

**Revenue Formula:**
```python
def calculate_miner_revenue(chain):
    """
    Revenue = (Block Reward + Fees) * Price

    Where:
    - Block Reward: 6.25 BTC (constant)
    - Fees: blocks_found * avg_fees_per_block
    - Price: Current chain price
    """
    block_reward_btc = 6.25
    fees_per_block_btc = median_fee * avg_tx_per_block / 100_000_000  # sat to BTC
    btc_per_block = block_reward_btc + fees_per_block_btc

    usd_per_block = btc_per_block * chain_price
    return usd_per_block
```

**Profitability Comparison:**
```python
def compare_profitability(v27_hashrate_pct):
    """
    Expected revenue if miner mines each chain

    Returns: (v27_revenue_per_hour, v26_revenue_per_hour)
    """
    v27_blocks_per_hour = 6 * (v27_hashrate_pct / 100)
    v26_blocks_per_hour = 6 * ((100 - v27_hashrate_pct) / 100)

    v27_revenue = v27_blocks_per_hour * calculate_miner_revenue('v27')
    v26_revenue = v26_blocks_per_hour * calculate_miner_revenue('v26')

    return v27_revenue, v26_revenue
```

**Data Export:**
```json
{
  "miner_profitability": {
    "timestamps": [0, 300, 600, ...],
    "v27_revenue_per_block": [375000, 378000, ...],
    "v26_revenue_per_block": [375000, 372000, ...],
    "profitability_ratio": [1.0, 1.016, ...]
  }
}
```

**Milestone:** End of Phase 2
- ✅ Fee markets modeled per chain
- ✅ Miner profitability calculable
- ✅ Revenue differentials tracked
- ⚠️ Still not affecting miner behavior (Phase 3)

---

## Phase 3: Dynamic Node Choice Model
**Goal:** Nodes switch chains based on economic incentives

### 3.1 Miner Switching Logic (Week 7-9)

**Deliverables:**
- `miner_strategy.py` - Rational miner behavior
- Switching thresholds configuration
- Hashrate reallocation mechanism

**Miner Decision Model:**
```python
class MinerStrategy:
    """Decides which chain to mine based on profitability"""

    def __init__(self, switching_threshold=0.05):
        """
        switching_threshold: Minimum profit advantage to switch (5% default)
        """
        self.threshold = switching_threshold
        self.current_chain = None
        self.switch_cooldown = 600  # 10 minutes before re-evaluating
        self.last_switch_time = 0

    def decide_chain(self, current_time) -> str:
        """
        Returns: 'v27' or 'v26' based on profitability

        Algorithm:
        1. Calculate expected revenue on each chain
        2. If other chain is >threshold% more profitable, switch
        3. Else, stay on current chain (switching has costs)
        4. Cooldown period prevents rapid oscillation
        """
        if current_time - self.last_switch_time < self.switch_cooldown:
            return self.current_chain

        v27_revenue, v26_revenue = compare_profitability(current_hashrate_split)

        if self.current_chain == 'v27':
            if v26_revenue > v27_revenue * (1 + self.threshold):
                self.current_chain = 'v26'
                self.last_switch_time = current_time
                logger.info(f"Miner switching to v26: {v26_revenue/v27_revenue:.2%} more profitable")
        else:
            if v27_revenue > v26_revenue * (1 + self.threshold):
                self.current_chain = 'v27'
                self.last_switch_time = current_time
                logger.info(f"Miner switching to v27: {v27_revenue/v26_revenue:.2%} more profitable")

        return self.current_chain
```

**Switching Mechanics:**

**Option A: Individual Pool Switching (Realistic)**
```python
# Each mining pool independently evaluates profitability
pools = [
    {'name': 'foundry', 'hashrate_pct': 28, 'strategy': MinerStrategy(threshold=0.03)},
    {'name': 'antpool', 'hashrate_pct': 18, 'strategy': MinerStrategy(threshold=0.05)},
    # ... more pools
]

for pool in pools:
    preferred_chain = pool['strategy'].decide_chain(current_time)
    allocate_hashrate(pool['name'], preferred_chain, pool['hashrate_pct'])
```

**Option B: Aggregate Hashrate Reallocation (Simple)**
```python
# Single aggregate decision
total_switching_hashrate = 50.0  # 50% of hashrate is "rational" and switches
rational_miner = MinerStrategy(threshold=0.05)
preferred_chain = rational_miner.decide_chain(current_time)

if preferred_chain == 'v27':
    new_v27_hashrate = base_v27_hashrate + total_switching_hashrate
    new_v26_hashrate = base_v26_hashrate - total_switching_hashrate
else:
    # vice versa
```

**Recommendation:** Start with Option B for simplicity, evolve to Option A for realism.

**Configuration:**
```yaml
miner_switching:
  enabled: true
  evaluation_interval: 600  # Re-evaluate every 10 minutes
  switching_threshold: 0.05  # Must be 5% more profitable to switch
  switching_hashrate_pct: 50  # How much hashrate is "rational"
  sticky_hashrate_pct: 50  # How much stays on initial chain (ideology, etc.)
```

**Integration with Partition Miner:**
```python
# In partition_miner.py scenario

# Instead of static hashrate split:
# OLD: v27_hashrate = 50.0, v26_hashrate = 50.0

# NEW: Dynamic reallocation every 10 minutes
v27_hashrate, v26_hashrate = calculate_dynamic_hashrate_split(
    current_time,
    price_oracle,
    fee_tracker,
    miner_strategy
)

# Update mining probabilities based on new split
update_mining_distribution(v27_hashrate, v26_hashrate)
```

**Testing:**
- Scenario: v27 has 90% economic, 10% initial hashrate
- Expected: Over 2 hours, hashrate shifts toward v27 as price/fees rise
- Validation: Final hashrate correlates with profitability

### 3.2 User/Exchange Choice Model (Week 9-10)

**Deliverables:**
- Transaction preference model
- Exchange listing decisions
- Economic node migration

**User Transaction Preference:**
```python
class UserTransactionChoice:
    """Users prefer to transact on economically dominant chain"""

    def choose_chain(self, price_ratio, fee_ratio, economic_weight_ratio):
        """
        Returns probability of choosing v27 vs v26

        Factors:
        - Higher price = more legitimate (security assumption)
        - Lower fees = cheaper to use (cost sensitivity)
        - Economic network effect (where are other users?)

        Weighting:
        - Price: 40% (legitimacy/security)
        - Fees: 30% (cost)
        - Network: 30% (where are exchanges/merchants?)
        """
        price_score = price_ratio / (price_ratio + 1)  # Normalize to 0-1
        fee_score = 1 / (fee_ratio + 1)  # Lower fees = higher score
        network_score = economic_weight_ratio / (economic_weight_ratio + 1)

        v27_preference = (price_score * 0.4 +
                         fee_score * 0.3 +
                         network_score * 0.3)

        return v27_preference  # 0-1 probability
```

**Exchange Listing Decisions:**
```python
class ExchangeStrategy:
    """Exchanges decide which chain(s) to list"""

    def __init__(self, dual_listing_threshold=0.3):
        """
        dual_listing_threshold: List both if minority chain >30% value
        """
        self.threshold = dual_listing_threshold

    def listing_decision(self, price_ratio, hashrate_ratio):
        """
        Returns: 'v27_only', 'v26_only', or 'both'

        Logic:
        - If one chain clearly dominant (>70% price), list only that
        - If split is close, list both (capture both markets)
        - Consider hashrate for security (won't list 51%-attackable chain)
        """
        minority_chain_value = min(price_ratio, 1/price_ratio)
        minority_chain_hashrate = min(hashrate_ratio, 1/hashrate_ratio)

        # Security check: Need at least 20% hashrate for listing
        if minority_chain_hashrate < 0.2:
            return 'dominant_only'

        # Value check: If minority >30% value, list both
        if minority_chain_value > self.threshold:
            return 'both'
        else:
            return 'dominant_only'
```

**Economic Node Migration:**
```python
def migrate_economic_weight(current_time):
    """
    Economic nodes gradually shift preference to dominant chain

    This affects:
    - Fee generation (more users = higher fees)
    - Price support (more buyers = higher price)
    - Network effect (more users attract more users)
    """
    v27_preference = user_choice.choose_chain(price_ratio, fee_ratio, econ_ratio)

    # Gradual migration (1% per hour can shift)
    migration_rate = 0.01  # 1% per hour
    time_hours = current_time / 3600
    migrated_pct = migration_rate * time_hours * (v27_preference - 0.5)

    new_v27_economic = base_v27_economic + migrated_pct * 100
    new_v26_economic = base_v26_economic - migrated_pct * 100

    return new_v27_economic, new_v26_economic
```

**Configuration:**
```yaml
user_choice:
  enabled: true
  migration_rate: 0.01  # 1% per hour
  price_weight: 0.4
  fee_weight: 0.3
  network_weight: 0.3

exchange_strategy:
  enabled: true
  dual_listing_threshold: 0.3
  min_hashrate_for_listing: 0.2
```

**Milestone:** End of Phase 3
- ✅ Miners switch chains based on profitability
- ✅ Users prefer economically dominant chain
- ✅ Exchanges make listing decisions
- ✅ Full economic feedback loops operational

---

## Phase 4: Integration & Long-Duration Tests
**Goal:** Run multi-hour tests with all economic models active

### 4.1 Enhanced Partition Miner Scenario (Week 11)

**Deliverables:**
- Extended partition_miner with dynamic models
- 2-6 hour test capability
- Comprehensive logging

**New Scenario Structure:**
```python
# partition_miner_dynamic.py

class DynamicPartitionMiner(PartitionMiner):
    """Extended scenario with economic dynamics"""

    def __init__(self, duration=7200):  # 2 hours default
        self.price_oracle = PriceOracle()
        self.fee_tracker = FeeTracker()
        self.miner_strategy = MinerStrategy()
        self.user_choice = UserTransactionChoice()
        self.duration = duration

        # Update intervals
        self.price_update_interval = 60  # 1 minute
        self.hashrate_update_interval = 600  # 10 minutes
        self.econ_update_interval = 3600  # 1 hour

    def run(self):
        """Main test loop with dynamic updates"""

        # Initialize common history
        self.generate_common_history()

        # Start partition
        self.partition_network()

        # Dynamic mining phase
        start_time = time.time()
        last_price_update = start_time
        last_hashrate_update = start_time
        last_econ_update = start_time

        while time.time() - start_time < self.duration:
            current_time = time.time() - start_time

            # Update prices (every minute)
            if current_time - last_price_update >= self.price_update_interval:
                self.update_prices()
                last_price_update = current_time

            # Update hashrate allocation (every 10 minutes)
            if current_time - last_hashrate_update >= self.hashrate_update_interval:
                self.update_hashrate_distribution()
                last_hashrate_update = current_time

            # Update economic weights (every hour)
            if current_time - last_econ_update >= self.econ_update_interval:
                self.update_economic_weights()
                last_econ_update = current_time

            # Mine blocks with current distribution
            self.mine_blocks(interval=60)

            # Log state
            self.log_state(current_time)

        # Final analysis
        self.generate_report()
```

**Enhanced Logging:**
```python
def log_state(self, current_time):
    """Log comprehensive state every minute"""

    state = {
        'timestamp': current_time,
        'blocks': {
            'v27_height': self.get_height('v27'),
            'v26_height': self.get_height('v26'),
        },
        'hashrate': {
            'v27_pct': self.current_v27_hashrate,
            'v26_pct': self.current_v26_hashrate,
        },
        'prices': {
            'v27_usd': self.price_oracle.get_price('v27'),
            'v26_usd': self.price_oracle.get_price('v26'),
        },
        'fees': {
            'v27_sat_per_vb': self.fee_tracker.get_median_fee('v27'),
            'v26_sat_per_vb': self.fee_tracker.get_median_fee('v26'),
        },
        'economic': {
            'v27_pct': self.current_v27_economic,
            'v26_pct': self.current_v26_economic,
        },
        'profitability': {
            'v27_usd_per_block': self.calculate_revenue('v27'),
            'v26_usd_per_block': self.calculate_revenue('v26'),
        }
    }

    self.state_log.append(state)

    # Real-time console output
    logger.info(f"[{current_time:5.0f}s] "
                f"Heights: v27={state['blocks']['v27_height']} v26={state['blocks']['v26_height']} | "
                f"Hash: {state['hashrate']['v27_pct']:.1f}%/{state['hashrate']['v26_pct']:.1f}% | "
                f"Price: ${state['prices']['v27_usd']:.0f}/${state['prices']['v26_usd']:.0f}")
```

**Testing:**
- 2-hour test: 90% economic on v27, 10% hashrate on v27 initially
- Expected progression:
  - t=0: v27 price stable, v26 mining faster
  - t=30min: v27 price rising (economic support), fees rising
  - t=1h: Miners start switching to v27 (more profitable)
  - t=2h: Hashrate ~60% v27, price premium sustained

### 4.2 Result Analysis Tools (Week 12)

**Deliverables:**
- Dynamic state analyzer
- Economic impact visualizations
- Model validation metrics

**Enhanced Temporal Analyzer:**
```python
# Add to temporal_analyzer.py

def plot_dynamic_state(state_log_json):
    """
    Create comprehensive visualization of dynamic test

    Plots:
    1. Block heights over time
    2. Hashrate allocation over time (showing switches)
    3. Price evolution (showing divergence)
    4. Fee evolution
    5. Economic weight migration
    6. Profitability ratio (why miners switched)
    """

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))

    # Plot 1: Block heights
    axes[0,0].plot(timestamps, v27_heights, 'b-', label='v27')
    axes[0,0].plot(timestamps, v26_heights, 'r-', label='v26')

    # Plot 2: Hashrate allocation
    axes[0,1].stackplot(timestamps, v27_hashrate, v26_hashrate,
                        labels=['v27', 'v26'], colors=['blue', 'red'])
    axes[0,1].set_ylabel('Hashrate %')

    # Plot 3: Price evolution
    axes[1,0].plot(timestamps, v27_prices, 'b-', label='v27')
    axes[1,0].plot(timestamps, v26_prices, 'r-', label='v26')
    axes[1,0].set_ylabel('Price (USD)')

    # Plot 4: Fee evolution
    axes[1,1].plot(timestamps, v27_fees, 'b-', label='v27')
    axes[1,1].plot(timestamps, v26_fees, 'r-', label='v26')
    axes[1,1].set_ylabel('Fees (sat/vB)')

    # Plot 5: Economic weight
    axes[2,0].stackplot(timestamps, v27_economic, v26_economic,
                        labels=['v27', 'v26'], colors=['blue', 'red'])
    axes[2,0].set_ylabel('Economic Weight %')

    # Plot 6: Profitability ratio
    profitability_ratio = v27_profitability / v26_profitability
    axes[2,1].plot(timestamps, profitability_ratio, 'purple')
    axes[2,1].axhline(y=1.0, color='gray', linestyle='--', label='Parity')
    axes[2,1].set_ylabel('v27/v26 Profit Ratio')
```

**Validation Metrics:**
```python
def validate_economic_model(test_result):
    """
    Verify economic models behaving as expected

    Checks:
    1. Price divergence correlates with economic weight
    2. Hashrate follows profitability with lag
    3. Fees correlate with economic node concentration
    4. Final outcome differs from initial conditions
    """

    # Check 1: Price-Economic correlation
    price_ratio_final = result['prices']['v27'][-1] / result['prices']['v26'][-1]
    econ_ratio_final = result['economic']['v27'][-1] / result['economic']['v26'][-1]
    price_econ_correlation = calculate_correlation(price_ratios, econ_ratios)

    assert price_econ_correlation > 0.5, "Price should follow economic weight"

    # Check 2: Hashrate lags profitability
    hashrate_changes = detect_hashrate_switches(result['hashrate'])
    profitability_changes = detect_profitability_crossovers(result['profitability'])

    for hash_switch in hashrate_changes:
        # Find preceding profitability crossover
        preceding_profit_changes = [p for p in profitability_changes
                                    if p['time'] < hash_switch['time']
                                    and hash_switch['time'] - p['time'] < 1800]  # Within 30 min
        assert len(preceding_profit_changes) > 0, "Hashrate switches should follow profit signals"

    # Check 3: Economic impact matters
    initial_outcome = predict_winner_by_hashrate(initial_hashrate_split)
    final_outcome = get_actual_winner(result)

    if initial_outcome != final_outcome:
        print(f"✓ Economic factors changed outcome: {initial_outcome} → {final_outcome}")
    else:
        # Check if economic factors at least influenced the margin
        margin_change = calculate_margin_change(result)
        assert abs(margin_change) > 2, "Economic factors should at least affect fork depth"
```

### 4.3 Configuration & Tuning (Week 12)

**Deliverables:**
- Model parameter configuration system
- Sensitivity analysis tools
- Recommended parameter sets

**Configuration System:**
```yaml
# dynamic_fork_config.yaml

test:
  duration: 7200  # 2 hours
  initial_v27_hashrate: 10.0
  initial_v27_economic: 90.0

models:
  price:
    enabled: true
    update_interval: 60
    base_price: 60000
    max_divergence: 0.20  # Max 20% price difference
    factors:
      chain_weight: 0.3      # Block height ratio
      economic_weight: 0.5   # Custody + volume
      hashrate_weight: 0.2   # Security premium

  fees:
    enabled: true
    update_interval: 60
    base_fee: 10
    congestion_multiplier: 0.5

  miner_switching:
    enabled: true
    evaluation_interval: 600
    switching_threshold: 0.05
    switching_hashrate_pct: 50

  user_choice:
    enabled: true
    migration_rate: 0.01
    price_weight: 0.4
    fee_weight: 0.3
    network_weight: 0.3
```

**Sensitivity Analysis:**
```python
def run_sensitivity_analysis(base_config, param_to_vary, range_values):
    """
    Test how varying one parameter affects outcomes

    Example: Vary switching_threshold from 0.01 to 0.20
             Does this change how quickly hashrate migrates?
    """

    results = []
    for value in range_values:
        config = base_config.copy()
        config[param_to_vary] = value

        result = run_dynamic_test(config)
        results.append({
            'param_value': value,
            'hashrate_switches': count_switches(result),
            'final_hashrate_v27': result['hashrate']['v27'][-1],
            'final_price_ratio': result['prices']['v27'][-1] / result['prices']['v26'][-1],
            'winner': get_winner(result)
        })

    return results
```

**Milestone:** End of Phase 4
- ✅ Full dynamic tests running end-to-end
- ✅ Comprehensive logging and visualization
- ✅ Model validation passing
- ✅ Parameter sensitivity understood

---

## Phase 5: Validation & Production Readiness
**Goal:** Validate models against expectations, prepare for large-scale runs

### 5.1 Model Validation Suite (Week 13)

**Test Scenarios:**

**Test 1: Economic Dominance Scenario**
- Initial: v27 = 90% economic, 10% hashrate
- Expected: Hashrate migrates to v27 over 2 hours
- Success criteria: Final v27 hashrate >50%

**Test 2: Hashrate Dominance Scenario**
- Initial: v27 = 10% economic, 90% hashrate
- Expected: v26 price falls, but hashrate stays
- Success criteria: v27 maintains mining despite low economic weight

**Test 3: Balanced Scenario**
- Initial: v27 = 50% economic, 50% hashrate
- Expected: Minor fluctuations, relative stability
- Success criteria: Final split within 10% of initial

**Test 4: Threshold Testing**
- Test: How much economic advantage needed to flip hashrate?
- Method: Vary economic split from 55% to 95%
- Measure: At what point does hashrate majority switch?

**Test 5: Duration Testing**
- Test: How long for equilibrium?
- Method: Run 1h, 2h, 4h, 6h tests
- Measure: Time to hashrate stabilization

### 5.2 Integration with Batch Runner (Week 13)

**Deliverables:**
- Extended batch runner supporting dynamic tests
- Mixed test campaigns (short + long)
- Results aggregation

```python
# run_dynamic_batch.py

def run_dynamic_test_campaign(n_samples=20, duration=7200):
    """
    Run batch of dynamic tests

    Test matrix:
    - Economic splits: 10%, 30%, 50%, 70%, 90%
    - Initial hashrate splits: 10%, 50%, 90%
    - Durations: 2h, 4h (long enough for dynamics to matter)

    Generates: 5 × 3 = 15 core scenarios × 2 durations = 30 tests
    """

    configs = []

    for econ_split in [10, 30, 50, 70, 90]:
        for hash_split in [10, 50, 90]:
            for duration in [7200, 14400]:  # 2h, 4h
                configs.append({
                    'economic_v27': econ_split,
                    'hashrate_v27': hash_split,
                    'duration': duration,
                    'models_enabled': True
                })

    return configs
```

### 5.3 Documentation & Handoff (Week 14)

**Deliverables:**
- User guide for dynamic tests
- Model documentation
- Example configurations
- Troubleshooting guide

---

## Implementation Timeline

| Phase | Weeks | Dependencies | Risk |
|-------|-------|-------------|------|
| Phase 1: Price Model | 1-3 | None | Low - Independent component |
| Phase 2: Fee Market | 4-6 | Phase 1 | Low - Uses price data |
| Phase 3: Node Choice | 7-10 | Phase 1, 2 | Medium - Complex behavior |
| Phase 4: Integration | 11-12 | Phase 1-3 | Medium - Integration complexity |
| Phase 5: Validation | 13-14 | Phase 4 | Low - Testing phase |

**Total: 14 weeks (~3.5 months)**

---

## Incremental Development Path

### Milestone 1 (Week 3): Price Divergence Demo
**Goal:** Show price changing based on chain fundamentals
**Demo:** 30-min test where v27 price rises with 90% economic weight
**Validation:** Price ratio matches economic ratio within 20%

### Milestone 2 (Week 6): Fee Market Working
**Goal:** Fees differ between chains based on usage
**Demo:** Chain with more economic nodes has higher fees
**Validation:** Fee ratio correlates with transaction volume

### Milestone 3 (Week 10): Hashrate Switching
**Goal:** Miners change chains mid-test
**Demo:** 2-hour test where hashrate flips from v26 to v27
**Validation:** Hashrate switches when profitability crosses threshold

### Milestone 4 (Week 12): Full Dynamic Test
**Goal:** All models working together
**Demo:** Economic weight influences outcome vs pure hashrate
**Validation:** Final winner differs from initial hashrate prediction

### Milestone 5 (Week 14): Production Ready
**Goal:** Batch testing capability
**Demo:** 20-test campaign with analysis
**Validation:** Results inform economic weight optimization

---

## Success Criteria

**Phase 1 Success:**
- [ ] Prices diverge between chains
- [ ] Price correlates with economic weight (r > 0.7)
- [ ] Prices logged and exportable

**Phase 2 Success:**
- [ ] Fees differ based on usage
- [ ] Miner revenue calculable
- [ ] Revenue differences trackable

**Phase 3 Success:**
- [ ] Miners switch chains at least once in 2-hour test
- [ ] Switches correlate with profitability crossovers
- [ ] Economic nodes show chain preference

**Phase 4 Success:**
- [ ] 2-hour dynamic test completes successfully
- [ ] All metrics logged comprehensively
- [ ] Visualizations show expected patterns

**Phase 5 Success:**
- [ ] Validation tests pass
- [ ] Economic factors measurably affect outcomes
- [ ] Batch testing operational

---

## Risk Mitigation

**Risk 1: Models too complex, hard to debug**
- Mitigation: Build incrementally, test each component independently
- Each model has unit tests before integration

**Risk 2: Performance issues with long tests**
- Mitigation: Start with 1-2 hour tests, optimize before scaling
- Profile code, use efficient data structures

**Risk 3: Model parameters hard to tune**
- Mitigation: Sensitivity analysis in Phase 4
- Document parameter effects, provide recommended values

**Risk 4: Economic effects still negligible even with models**
- Mitigation: Test scenarios should be extreme (90/10 splits)
- If still no effect, may need even longer durations or stronger incentives

**Risk 5: Integration breaks existing tests**
- Mitigation: Maintain backward compatibility
- New dynamic scenario separate from original partition_miner.py

---

## Next Actions (Start of Phase 1)

1. **Create price_oracle.py skeleton** (Day 1)
   - Define PriceOracle class
   - Implement basic storage (JSON or SQLite)
   - Write unit tests

2. **Implement simple price model** (Day 2-3)
   - Option A: Supply/demand based
   - Test with mock data

3. **Integrate with partition_miner** (Day 4-5)
   - Add price updates to scenario
   - Log prices during test
   - Verify price storage

4. **Run validation test** (Day 6-7)
   - 30-min test with 90/10 economic split
   - Verify price diverges
   - Document results

5. **Review & iterate** (Day 8-14)
   - Tune divergence parameters
   - Add visualizations
   - Prepare for Phase 2

---

## Questions for Consideration

1. **Price Model Complexity**
   - Start with simple supply/demand or go straight to order book?
   - Recommendation: Simple first, can upgrade later

2. **Miner Switching Granularity**
   - Individual pools or aggregate hashrate?
   - Recommendation: Aggregate for Phase 3, individual for future enhancement

3. **Test Duration**
   - 2 hours sufficient or need 6+ hours?
   - Recommendation: Start with 2h, extend if dynamics too slow

4. **Economic Node Behavior**
   - Should users/exchanges actively transact or just provide weight?
   - Recommendation: Start passive (weight only), add transactions in future phase

5. **Validation Approach**
   - What outcomes prove economic models working?
   - Recommendation: Look for hashrate migration correlating with profitability

---

## Resource Requirements

**Development:**
- 1 developer, 3-4 months part-time
- OR 2 developers, 1.5-2 months part-time

**Testing:**
- Kubernetes cluster (existing)
- 2-6 hour test windows (longer than current 30-min)
- ~50 test runs for validation (one per week during development)

**Storage:**
- Detailed state logs (~10-50MB per 2-hour test)
- 20 tests × 50MB = 1GB storage (manageable)

---

## Conclusion

This plan transforms static partition tests into dynamic economic simulations. By incrementally adding price models, fee markets, and node choice mechanisms, we can test whether economic weight can influence fork outcomes when given time to exert pressure through market forces.

**Key Insight:** Current tests show hashrate dominates (r=0.96) because there's no mechanism for economic factors to matter in 30 minutes. Dynamic models provide those mechanisms.

**Expected Outcome:** After Phase 5, we'll have empirical data on:
- How long economic pressure takes to affect miners
- What economic advantage is needed to flip hashrate
- Optimal custody/volume weights for predicting long-term outcomes
- Whether BCAP framework correctly models real-world fork dynamics

This work will significantly advance understanding of Bitcoin fork economics and provide a unique testing platform for governance scenarios.
