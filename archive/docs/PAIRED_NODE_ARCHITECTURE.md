# Paired-Node Architecture for Pool Mining

**Date**: 2026-01-25
**Status**: ✅ Implemented and Tested

---

## Overview

This document describes the **paired-node architecture** for modeling mining pool behavior across blockchain forks in warnet.

### Key Principle

**Each mining pool = ONE entity with TWO nodes (one per partition)**

This accurately represents real-world mining pools:
- Mining pools are single economic entities
- They can allocate hashrate across multiple forks
- Each fork requires separate infrastructure (full node + block template generation)
- Pool makes strategic decision about hashrate allocation

---

## Real-World Analogy

### Bitcoin Cash Fork (2017)

When Bitcoin forked into BTC and BCH:
- **Pool entity**: ViaBTC (single company, one decision-maker)
- **Infrastructure**:
  - BTC node running Bitcoin Core 0.15
  - BCH node running Bitcoin ABC
- **Strategy**: Initially split hashrate 50/50, later shifted to 80/20 based on profitability
- **Implementation**:
  - Miners connected to pool
  - Pool decided which chain to mine
  - Block template came from appropriate node

### Our Model

```
Pool: ViaBTC (12% total hashrate)
│
├── v27 node (node-viabtc-v27) ← Infrastructure for v27 fork
│   └── Ready to mine v27 blocks
│
└── v26 node (node-viabtc-v26) ← Infrastructure for v26 fork
    └── Ready to mine v26 blocks

Decision: Mine v26 (ideology)
Action: generatetoaddress() on node-viabtc-v26
Probability: 12% of next block
```

---

## Architecture Details

### Network Structure

#### Paired Nodes

Each pool has **2 nodes** with the **same `entity_id`**:

```yaml
# v27 partition
- name: node-foundry-v27
  image: {tag: '27.0'}
  metadata:
    entity_id: pool-foundry    # ← Same entity_id
    entity_name: Foundry USA
    hashrate_pct: 28.0         # Pool's TOTAL hashrate

# v26 partition
- name: node-foundry-v26
  image: {tag: '26.0'}
  metadata:
    entity_id: pool-foundry    # ← Same entity_id
    entity_name: Foundry USA
    hashrate_pct: 28.0         # Pool's TOTAL hashrate
```

**Critical point**: The `hashrate_pct` represents the pool's **total capacity**, not per-node capacity.

#### Pool-to-Node Mapping

```python
# After loading network.yaml:
self.pool_nodes_v27 = {
    'foundry': [node-foundry-v27],  # Single node
    'antpool': [node-antpool-v27],
    'viabtc': [node-viabtc-v27],
}

self.pool_nodes_v26 = {
    'foundry': [node-foundry-v26],  # Single node
    'antpool': [node-antpool-v26],
    'viabtc': [node-viabtc-v26],
}
```

**Each pool has exactly ONE node per partition** (if present).

---

## Binary Pool Allocation (Simple Solution)

### Decision Model

Pools make a **binary choice** each decision interval (10 minutes):

```python
# Pool decides which fork to mine
chosen_fork = make_decision()  # Returns 'v27' or 'v26'

# This means:
# - 100% of pool's hashrate goes to chosen fork
# - 0% to the other fork

# Examples:
foundry → 'v27'  # 28% hashrate to v27
viabtc → 'v26'   # 12% hashrate to v26
```

### Mining Selection

When it's time to mine a block:

```python
def select_mining_node():
    # Build weighted list of (pool_id, partition)
    for pool_id, chosen_fork in pool_allocations.items():
        pool = pools[pool_id]

        if chosen_fork == 'v27':
            add_to_list(pool_id, 'v27', weight=pool.hashrate_pct)
        else:
            add_to_list(pool_id, 'v26', weight=pool.hashrate_pct)

    # Weighted random selection
    selected_pool, partition = weighted_choice(list, weights)

    # Get that pool's node on chosen partition
    if partition == 'v27':
        node = pool_nodes_v27[selected_pool][0]  # First (only) node
    else:
        node = pool_nodes_v26[selected_pool][0]

    return node, partition
```

### Example Scenario

**Pools**:
- foundry: 28% hashrate, rational
- antpool: 18% hashrate, rational
- viabtc: 12% hashrate, prefers v26 (ideology)
- f2pool: 15% hashrate, prefers v27

**Market State**: v27 more profitable ($62k vs $58k)

**Pool Decisions**:
```
foundry → v27 (28% hash) - Rational choice
antpool → v27 (18% hash) - Rational choice
viabtc  → v26 (12% hash) - Ideology override (losing $50k/hour)
f2pool  → v27 (15% hash) - Ideology aligns with profit
```

**Hashrate Allocation**:
- v27: 61% (foundry 28% + antpool 18% + f2pool 15%)
- v26: 12% (viabtc only)

**Mining Probabilities**:
- Next block has 61% chance of being mined on v27
- If v27 selected:
  - 28/61 = 45.9% chance it's foundry node
  - 18/61 = 29.5% chance it's antpool node
  - 15/61 = 24.6% chance it's f2pool node
- If v26 selected:
  - 100% chance it's viabtc node (only pool on v26)

**Node Calls**:
```
Block 1: Weighted random → v27 (61% prob)
         Pool selection → foundry (28% weight)
         generatetoaddress(node-foundry-v27, ...)

Block 2: Weighted random → v27 (61% prob)
         Pool selection → f2pool (15% weight)
         generatetoaddress(node-f2pool-v27, ...)

Block 3: Weighted random → v26 (12% prob)
         Pool selection → viabtc (12% weight)
         generatetoaddress(node-viabtc-v26, ...)
```

---

## Implementation Details

### 1. Loading Network Metadata

```python
def load_network_metadata(self):
    """Load node metadata from network.yaml"""
    with open(self.options.network_yaml, 'r') as f:
        network_config = yaml.safe_load(f)

    # Build node name → metadata mapping
    for node_config in network_config.get('nodes', []):
        node_name = node_config.get('name')
        metadata = node_config.get('metadata', {})

        if node_name:
            self.node_metadata[node_name] = metadata
```

### 2. Building Pool Mappings

```python
def build_pool_node_mapping(self):
    """Map pool IDs to their nodes in each partition"""
    for node in self.v27_nodes:
        pool_id = self.get_node_pool_id(node)
        if pool_id:
            if pool_id not in self.pool_nodes_v27:
                self.pool_nodes_v27[pool_id] = []
            self.pool_nodes_v27[pool_id].append(node)

    # Same for v26_nodes...

    # Expected: Each pool has exactly 1 node per partition
    for pool_id in all_pools:
        assert len(self.pool_nodes_v27[pool_id]) == 1
        assert len(self.pool_nodes_v26[pool_id]) == 1
```

### 3. Pool ID Extraction

```python
def get_node_pool_id(self, node):
    """Extract pool ID from node metadata"""
    node_name = f"node-{node.index:04d}"

    if node_name in self.node_metadata:
        entity_id = self.node_metadata[node_name].get('entity_id')

        if entity_id and entity_id.startswith('pool-'):
            # Convert pool-foundry → foundry
            return entity_id.replace('pool-', '')

    return None
```

### 4. Mining Node Selection

```python
def select_mining_node(self):
    """Select node based on pool decisions"""
    pool_choices = []
    pool_weights = []

    # Binary allocation: each pool chose one fork
    for pool_id, chosen_fork in self.pool_strategy.current_allocation.items():
        pool = self.pool_strategy.pools[pool_id]

        if chosen_fork == 'v27' and pool_id in self.pool_nodes_v27:
            pool_choices.append((pool_id, 'v27'))
            pool_weights.append(pool.hashrate_pct)
        elif chosen_fork == 'v26' and pool_id in self.pool_nodes_v26:
            pool_choices.append((pool_id, 'v26'))
            pool_weights.append(pool.hashrate_pct)

    # Weighted random selection
    selected_pool, partition = choices(pool_choices, weights=pool_weights, k=1)[0]

    # Get the pool's single node on that partition
    if partition == 'v27':
        node = self.pool_nodes_v27[selected_pool][0]
    else:
        node = self.pool_nodes_v26[selected_pool][0]

    return node, partition
```

---

## Validation Tests

### Test: Paired-Node Architecture

**File**: `test_paired_node_architecture.py`

**Test Results**: ✓ PASSED

```
Pool Configuration:
  foundry   :  28.0% hashrate, preference=neutral, ideology=0.0
  antpool   :  18.0% hashrate, preference=neutral, ideology=0.0
  viabtc    :  12.0% hashrate, preference=v26, ideology=0.5
  f2pool    :  15.0% hashrate, preference=v27, ideology=0.3

SCENARIO 1: v27 More Profitable
  Prices: v27=$62,000, v26=$58,000

  Pool Decisions:
    foundry    → v27 ( 28.0% hash) | ✓ Rational
    antpool    → v27 ( 18.0% hash) | ✓ Rational
    viabtc     → v27 ( 12.0% hash) | ✓ Rational
    f2pool     → v27 ( 15.0% hash) | ✓ Rational

  Hashrate: v27=73.0%, v26=0.0%
  ✓ All pools mine rationally when no ideology conflict

SCENARIO 2: v26 More Profitable
  Prices: v27=$58,000, v26=$62,000

  Pool Decisions:
    foundry    → v26 ( 28.0% hash) | ✓ Rational [SWITCHED from v27]
    antpool    → v26 ( 18.0% hash) | ✓ Rational [SWITCHED from v27]
    viabtc     → v26 ( 12.0% hash) | ✓ Rational [SWITCHED from v27]
    f2pool     → v26 ( 15.0% hash) | ✓ Rational [SWITCHED from v27]

  Hashrate: v27=0.0%, v26=73.0%
  ✓ Pools switch when profitability reverses
```

**Validations**:
- ✅ All pools have binary allocation (v27 or v26)
- ✅ Hashrate allocation matches pool decisions
- ✅ Total hashrate sums correctly
- ✅ Pools switch when incentives change

---

## Future Enhancement: Split Allocation

While currently using **binary allocation** (all-in on one fork), the architecture supports **split allocation** for future enhancements:

### Split Allocation Model

```python
# Pool can split hashrate across forks
allocation = {
    'v27': 0.7,  # 70% of hashrate
    'v26': 0.3   # 30% of hashrate
}

# Example: Foundry with 28% total hashrate
# Allocates: 19.6% to v27, 8.4% to v26

# Mining selection uses effective hashrate:
v27_effective = 28.0 * 0.7 = 19.6%
v26_effective = 28.0 * 0.3 = 8.4%
```

### Use Cases for Split Allocation

1. **Hedging Strategy**: Mine majority fork but "test the waters" on minority
2. **Gradual Migration**: Slowly shift hashrate during uncertain periods
3. **Dual Commitment**: Pool has both ideological and economic motivations
4. **Risk Management**: Diversify in case fork outcome is unclear

**Status**: Architecture supports this, but **not implemented yet**. Current version uses binary (all-or-nothing) allocation for simplicity.

---

## Network Generation Requirements

To use this architecture, network generation must create **paired nodes**:

### Example Network Generation

```python
def generate_paired_pool_network(pools, v27_count, v26_count):
    """Generate network with paired pool nodes"""

    nodes = []

    for pool_id, hashrate_pct in pools.items():
        # Create v27 node for this pool
        nodes.append({
            'name': f'node-{pool_id}-v27',
            'image': {'tag': '27.0'},
            'metadata': {
                'role': 'mining_pool',
                'entity_id': f'pool-{pool_id}',
                'entity_name': pool_names[pool_id],
                'hashrate_pct': hashrate_pct
            },
            'addnode': [...],  # v27 partition connections
        })

        # Create v26 node for this pool (same entity!)
        nodes.append({
            'name': f'node-{pool_id}-v26',
            'image': {'tag': '26.0'},
            'metadata': {
                'role': 'mining_pool',
                'entity_id': f'pool-{pool_id}',  # Same entity_id!
                'entity_name': pool_names[pool_id],
                'hashrate_pct': hashrate_pct     # Same total hashrate!
            },
            'addnode': [...],  # v26 partition connections
        })

    return nodes
```

### Naming Convention

**Option 1**: Entity ID suffix
```
node-foundry-v27  (entity_id: pool-foundry)
node-foundry-v26  (entity_id: pool-foundry)
```

**Option 2**: Sequential numbering
```
node-0000 (entity_id: pool-foundry, version: 27.0)
node-0050 (entity_id: pool-foundry, version: 26.0)
```

**Recommendation**: Option 1 (explicit naming) for clarity during testing.

---

## Usage

### Running with Paired-Node Network

```bash
warnet run partition_miner_with_pools.py \
  --network-yaml /path/to/paired_nodes_network.yaml \
  --pool-scenario realistic_current \
  --v27-economic 70.0 \
  --duration 7200 \
  --hashrate-update-interval 600
```

### Expected Output

```
Loading network metadata from paired_nodes_network.yaml
✓ Loaded metadata for 16 nodes

Building pool-to-node mappings...

Pool node distribution (1 node per partition per pool):
  antpool        : v27=node-0001    v26=node-0009
  binance        : v27=node-0002    v26=node-0010
  f2pool         : v27=node-0003    v26=node-0011
  foundry        : v27=node-0000    v26=node-0008

Starting partition mining...

[  10s] v27 block (foundry)      | Heights: v27=102 v26=101 | ...
[  20s] v27 block (antpool)      | Heights: v27=103 v26=101 | ...
[  30s] v26 block (viabtc)       | Heights: v27=103 v26=102 | ...

⚡ HASHRATE REALLOCATION at 600s:
   v27: 46.0% → 67.0%
   v26: 54.0% → 33.0%

   💰 viabtc: mining v26 despite $50,000 loss (ideology)

[610s] v27 block (foundry)       | Heights: v27=112 v26=108 | ...
```

---

## Summary

### Architecture

- **Each pool = 1 economic entity with 2 nodes (one per partition)**
- Pools make **binary allocation** decisions ('v27' or 'v26')
- Pool's full hashrate goes to chosen fork
- Correct node is selected based on pool's decision

### Benefits

✅ **Realistic**: Matches real-world pool infrastructure
✅ **Simple**: Binary decisions are easy to understand
✅ **Extensible**: Can add split allocation later
✅ **Testable**: Clear one-to-one mapping

### Key Files

| File | Purpose |
|------|---------|
| `partition_miner_with_pools.py` | Main scenario with paired-node support |
| `mining_pool_strategy.py` | Pool decision engine (binary allocation) |
| `test_paired_node_architecture.py` | Validation tests |
| `PAIRED_NODE_ARCHITECTURE.md` | This document |

---

**Document Version**: 1.0
**Created**: 2026-01-25
**Status**: ✅ Implemented and tested
