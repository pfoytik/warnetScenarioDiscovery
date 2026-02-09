# BCAP Economic Node Model - Quick Reference

## TL;DR

Economic nodes matter because they **validate which chain holds real economic value**.

Power = **Custody (PRIMARY)** + **Payment Flow (SECONDARY)**

---

## Economic Node Categories

| Category | Custody (BTC) | % Supply | Daily Volume | Weight | Example |
|----------|---------------|----------|--------------|--------|---------|
| **Major Exchange** | 1.8M - 2.5M | 9-13% | 80k-120k | 9-13 | Coinbase, Binance |
| **Regional Exchange** | 300k - 600k | 1.5-3% | 20k-40k | 2-3 | Kraken, Gemini |
| **Payment Processor** | 10k - 50k | 0.05-0.25% | 5k-15k | 0.5-1.5 | BitPay, Strike |
| **Custody Provider** | 400k - 1M | 2-5% | 1k-5k | 2-5 | Fidelity Digital |

---

## YAML Template

```yaml
- name: "my-exchange"
  type: "economic"
  image: "bitcoin:27.0"

  metadata:
    node_type: "major_exchange"
    entity_name: "My Exchange"

    # PRIMARY: Custody
    custody_btc: 2000000
    supply_percentage: 10.3

    # SECONDARY: Payment Flow
    daily_deposits_btc: 100000
    daily_withdrawals_btc: 95000
    daily_volume_btc: 100000

    # DERIVED: Weight
    consensus_weight: 10.3
    economic_influence: "critical"

  bitcoin_config:
    maxmempool: 10000
    maxconnections: 2000
```

---

## Economic Weight Calculation

```
consensus_weight = (custody_btc / 19_500_000) × 100

Examples:
- 2M BTC custody → 10.3 weight
- 450k BTC custody → 2.3 weight
- 30k BTC custody → 0.15 weight (+ operational bonus → 1.0)
```

---

## Test Networks Available

### 1. economic-30-nodes.yaml
- **5 economic nodes** (28.5 total weight)
  - 2 major exchanges (Coinbase, Binance): 10.3 + 11.3 = 21.6
  - 1 regional exchange (Kraken): 2.3
  - 1 payment processor (BitPay): 1.0
  - 1 custody provider (Fidelity): 3.6
- **20 relay nodes** (20 weight)
- **5 constrained nodes** (2.5 weight)
- **Total weight**: 51.0

### 2. custom-5-node.yaml
- **3 economic nodes** (22.6 total weight)
  - Exchange 1 (v26.0, 50MB mempool): 10.3
  - Exchange 2 (v27.0, 10GB mempool): 11.3
  - Payment processor (v27.0, 1hr expiry): 1.0
- **2 relay nodes** (2 weight)
- **Total weight**: 24.6

**Test Focus**: Version mixing + mempool policy differences

---

## Key Metrics Explained

### custody_btc
Total BTC in hot + cold storage
- **Why it matters**: Determines which chain holds "real" value
- **Example**: Coinbase holds 2M BTC → if they choose chain A, 2M BTC worth of users follow

### daily_volume_btc
Daily transaction flow (deposits + withdrawals)
- **Why it matters**: Operational chokepoints control payment acceptance
- **Example**: BitPay processes 10k BTC/day → merchants follow their chain choice

### consensus_weight
Numerical influence in consensus scenarios
- **Calculation**: Primarily custody-based, with operational bonuses
- **Range**: 0.01 (mining pool) to 13 (major exchange)

### economic_influence
Qualitative assessment of importance
- **critical**: ≥5.0 weight (major exchanges, large custodians)
- **significant**: 2.0-5.0 weight (regional exchanges, custody providers)
- **moderate**: 0.5-2.0 weight (payment processors, small custodians)
- **minor**: <0.5 weight (mining pools, small entities)

---

## Common Test Scenarios

### Scenario 1: Chain Split
```
Question: Which chain wins?
Answer: Chain with highest economic_weight + operational chokepoints

Example:
- Chain A: Coinbase (10.3) + Kraken (2.3) + BitPay (1.0) = 13.6
- Chain B: Binance (11.3) = 11.3
- Result: Chain A wins (higher weight + payment processor)
```

### Scenario 2: Mempool Divergence
```
Question: Which transactions propagate?
Answer: Depends on node mempool policies

Example:
- Exchange with 50MB mempool: Drops low-fee txs
- Exchange with 10GB mempool: Keeps all txs
- Result: Different tx sets, user fragmentation
```

### Scenario 3: Version Split
```
Question: Can old version nodes maintain consensus?
Answer: Yes if they have sufficient economic weight

Example:
- v26.0 nodes: Coinbase (10.3) + Fidelity (3.6) = 13.9
- v27.0 nodes: Binance (11.3) + BitPay (1.0) = 12.3
- Result: v26.0 has slight edge, depends on feature compatibility
```

---

## How to Create Custom Networks

### Method 1: Use EconomicNode Class
```python
from economic_network_utils import EconomicNode

node = EconomicNode(
    name="my-exchange",
    node_type="major_exchange",  # or regional_exchange, payment_processor, custody_provider
    version="27.0",
    custody_btc=1500000,  # Optional override
    daily_volume_btc=80000  # Optional override
)

config = node.to_dict()
```

### Method 2: Direct YAML (Recommended)
```yaml
# Copy custom-5-node.yaml as template
# Modify custody_btc, daily_volume_btc, bitcoin_config
# Deploy with: warnet deploy my-network.yaml
```

---

## Files & Documentation

```
warnet-economic-implementation/
├── BCAP_FRAMEWORK.md              ← Full framework documentation
├── networks/
│   └── economic-30-nodes.yaml     ← 30-node reference network
└── scripts/
    └── economic_network_utils.py  ← EconomicNode class

test-networks/
├── custom-5-node.yaml             ← Minimal test network
├── BCAP_QUICK_REFERENCE.md        ← This file
└── ECONOMIC_NODE_CAPABILITIES.md  ← Technical capabilities guide
```

---

## Decision Tree: Which Node Type?

```
Does it hold >1M BTC in custody?
├─ YES → Is it an exchange or custody provider?
│   ├─ Exchange → MAJOR_EXCHANGE (weight 9-13)
│   └─ Custody → CUSTODY_PROVIDER (weight 2-5)
└─ NO → What's the primary function?
    ├─ Exchange → REGIONAL_EXCHANGE (weight 2-3)
    └─ Payment processing → PAYMENT_PROCESSOR (weight 0.5-1.5)
```

---

## Quick Validation Checklist

When creating economic nodes, ensure:

- [ ] `custody_btc` is realistic for node type
- [ ] `supply_percentage = (custody_btc / 19_500_000) × 100`
- [ ] `consensus_weight ≈ supply_percentage`
- [ ] `daily_volume_btc` matches entity type (high for exchanges, very high for processors)
- [ ] `bitcoin_config` matches operational needs (mempool size, connections)
- [ ] `economic_influence` matches weight tier (critical/significant/moderate/minor)

---

## Common Mistakes

### ❌ Arbitrary Weights
```yaml
weight: 15  # What does this mean?
```

### ✅ BCAP-Aligned Weights
```yaml
custody_btc: 2000000
supply_percentage: 10.3
consensus_weight: 10.3
```

### ❌ Ignoring Payment Flow
```yaml
# Payment processor with only custody metric
custody_btc: 10000  # Too low to matter
```

### ✅ Including Operational Importance
```yaml
# Payment processor with custody + flow
custody_btc: 30000
daily_volume_btc: 10000  # High flow → operational chokepoint
consensus_weight: 1.0  # Boosted from 0.15
```

---

## Next Steps

1. **Read**: `BCAP_FRAMEWORK.md` for full framework explanation
2. **Explore**: `economic-30-nodes.yaml` to see realistic network
3. **Test**: `custom-5-node.yaml` for quick experiments
4. **Build**: Create your own scenarios using the templates

---

**Version**: 1.0 (BCAP-aligned)
**Last Updated**: 2024-11-26
