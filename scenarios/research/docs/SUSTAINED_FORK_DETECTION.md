# Sustained Fork Detection

**Date**: 2026-01-25
**Status**: ✅ Implemented and Validated
**Priority**: Critical

---

## Problem Statement

**Original Issue**: Price oracle was applying divergence **immediately** when partition mining started, even for natural chain splits.

**Why This Is Wrong**:

Bitcoin experiences natural chain splits frequently:
- Two miners find blocks simultaneously
- Brief network partitions
- Race conditions in block propagation

These resolve within 1-6 blocks and **should NOT create separate tokens**. Only **intentional, sustained protocol forks** (like Bitcoin Cash, Ethereum Classic) create separate tokens with independent valuations.

---

## Solution: Sustained Fork Threshold

### Implementation

Price divergence now only occurs when fork is **sustained**:

```python
# Sustained fork criteria
fork_depth = (v27_height + v26_height) - (2 × common_ancestor_height)

if fork_depth >= 6:
    # Fork is SUSTAINED → separate token valuation
    prices_diverge_based_on_fundamentals()
else:
    # Natural chain split → prices remain equal
    v27_price = v26_price = base_price
```

### Threshold Values

**Fork Depth >= 6 blocks**
- Matches Bitcoin's "6 confirmations" security standard
- Example: v27 mines 3 blocks, v26 mines 3 blocks → depth = 6
- Both chains contribute to depth calculation

**Why NOT time-based**:
- Scenarios need to run fast for research
- Block count is more deterministic
- Time-based thresholds better for production

---

## Fork Depth Calculation

### Formula

```
fork_depth = (v27_height + v26_height) - (2 × common_ancestor_height)
```

### Examples

**Common ancestor at block 100**:

| v27 Height | v26 Height | Fork Depth | Status |
|------------|------------|------------|--------|
| 101 | 101 | 2 | Natural split |
| 102 | 101 | 3 | Natural split |
| 103 | 103 | **6** | **SUSTAINED** |
| 105 | 102 | 7 | SUSTAINED |
| 110 | 110 | 20 | SUSTAINED |

### Asymmetric Forks

Fork depth accounts for **total blocks** on both chains:

| v27 Height | v26 Height | Fork Depth | Notes |
|------------|------------|------------|-------|
| 102 | 101 | 3 | v27 mining faster |
| 104 | 102 | 6 | SUSTAINED |
| 106 | 103 | 9 | Still sustained |

---

## Behavior Changes

### Before Sustained Fork Detection

```
Block 101: v27=$60,100, v26=$59,900 ❌ WRONG
Block 102: v27=$60,200, v26=$59,800 ❌ WRONG
Block 103: v27=$62,880, v26=$57,120 ❌ TOO EARLY
```

Price divergence starts immediately, treating every chain split as a protocol fork.

### After Sustained Fork Detection

```
Block 101: v27=$60,000, v26=$60,000 ✓ Equal (depth=2)
Block 102: v27=$60,000, v26=$60,000 ✓ Equal (depth=4)
Block 103: v27=$62,880, v26=$57,120 ✓ SUSTAINED (depth=6)
Block 104: v27=$62,880, v26=$57,120 ✓ Continues diverging
```

Natural splits keep prices equal until fork proves sustained.

---

## Implementation Details

### Modified Files

**1. `price_oracle.py`** (core implementation)

Added state variables:
```python
self.min_fork_depth = 6
self.fork_sustained = False
self.fork_start_height = None
self.fork_sustained_at = None
```

Added method:
```python
def check_fork_sustained(
    v27_height, v26_height, common_ancestor_height
) -> bool
```

Modified methods:
- `update_price()` - only diverge if `self.fork_sustained`
- `update_prices_from_state()` - check fork status before updating
- `print_summary()` - display fork status

**2. `price_model_config.yaml`**

```yaml
sustained_fork_detection:
  enabled: true
  min_fork_depth: 6
```

**3. `partition_miner_price_test.py`**

- Added `common_ancestor_height` parameter to `update_prices_from_state()`
- Uses `start_height` as common ancestor
- Displays `[SUSTAINED]` or `[natural split]` indicator in logs

**4. Test Suite: `test_sustained_fork_detection.py`**

Comprehensive validation:
- Natural chain splits (depth < 6)
- Sustained forks (depth >= 6)
- Asymmetric forks (one chain faster)
- Fork depth calculation accuracy

---

## Test Results

```
======================================================================
TEST 1: Natural Chain Split (depth < 6)
======================================================================

Block 101: Fork depth = 2
  Sustained: False
  v27 price: $60,000.00
  v26 price: $60,000.00
  ✓ Prices remain equal (natural split)

Block 102: Fork depth = 4
  Sustained: False
  v27 price: $60,000.00
  v26 price: $60,000.00
  ✓ Prices remain equal (natural split)

Block 103: Fork depth = 6
  Sustained: True
  v27 price: $62,880.00
  v26 price: $57,120.00
  ✓ Fork now sustained - prices can diverge

✓ Natural chain split test PASSED
```

---

## Configuration

### Default Settings

```yaml
price_model:
  sustained_fork_detection:
    enabled: true
    min_fork_depth: 6
```

### Customization

```python
# More conservative (longer confirmation)
oracle = PriceOracle(min_fork_depth=12)

# Less conservative (faster detection)
oracle = PriceOracle(min_fork_depth=3)

# Disable (for testing only)
oracle = PriceOracle(min_fork_depth=0)  # Immediate divergence
```

---

## Real-World Analogs

### Bitcoin Protocol Forks (Sustained)

**Bitcoin Cash (BCH) - 2017**
- Fork depth: Thousands of blocks
- Separate token created immediately
- Independent price discovery

**Bitcoin SV (BSV) - 2018**
- Fork from BCH at block 556766
- Sustained fork with separate valuation

**Ethereum Classic (ETC) - 2016**
- Fork from ETH at block 1920000
- Both chains persist with independent prices

### Natural Chain Splits (NOT Sustained)

**Common Bitcoin Events**:
- Two miners find blocks within seconds
- Temporary network partition
- Resolve within 1-6 blocks
- No separate tokens created
- Price remains unified

---

## Impact on Fee Oracle

**Fees manipulate immediately** (no sustained fork requirement):

```python
# Fee oracle can manipulate from block 1
fee_oracle.apply_manipulation('v26', btc_spent=1.0, blocks=1)

# But price oracle waits until fork is sustained
# Fees respond to manipulation immediately
# Prices respond after fork proves sustained
```

**Why**:
- Manipulation happens in real-time (trying to influence which chain wins)
- Price discovery happens after market recognizes sustained fork
- This models actual market behavior

---

## Key Insights

### 1. Natural Splits Are Common

Bitcoin averages ~1-2 natural chain splits per day. These resolve quickly and don't create separate tokens.

### 2. 6-Block Threshold Is Standard

Bitcoin community considers 6 confirmations as "final" for large transactions. Using same threshold for fork sustainability.

### 3. Both Chains Contribute to Depth

Fork depth = total blocks mined on BOTH chains since split. This prevents gaming by one chain mining very slowly.

### 4. Time Not Used (For Testing)

Production systems might add:
```yaml
min_fork_time: 3600  # 1 hour in seconds
```

But for fast scenario testing, we only use block depth.

---

## Future Enhancements

### Potential Additions

1. **Reorg Detection**
   - If chains reconverge within N blocks, mark as "resolved split"
   - Reset fork detection

2. **Gradual Divergence**
   - Instead of instant divergence at block 6, gradually increase over blocks 6-12

3. **Time-Based Threshold**
   - Add optional time requirement for production use
   - `min_fork_time: 3600  # 1 hour`

4. **Configurable per Network**
   - Testnet: 3 blocks
   - Mainnet: 6 blocks
   - Regtest: 1 block

---

## Validation

✅ **All tests passing**:
- `test_sustained_fork_detection.py` - Comprehensive unit tests
- `price_oracle.py` - Built-in validation
- `partition_miner_price_test.py` - Integration test scenario

✅ **Behavior correct**:
- Natural splits keep prices equal
- Sustained forks enable divergence
- Fork depth calculated accurately
- Status displayed in logs

---

## Summary

**Problem**: Price oracle diverged immediately, treating all chain splits as protocol forks

**Solution**: Only diverge prices for sustained forks (depth >= 6 blocks)

**Impact**: More realistic modeling of Bitcoin fork economics

**Status**: ✅ Complete and validated

---

**Document Version**: 1.0
**Created**: 2026-01-25
**Author**: Phase 1-2 Integration Team
**Next Review**: Phase 3 Implementation
