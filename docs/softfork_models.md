# Soft Fork Simulation Models

This document describes two simulation models for Bitcoin soft fork scenarios: **contentious soft forks** (symmetric partitions) and **non-contentious soft forks** (asymmetric block propagation).

---

## Overview

| Aspect | Contentious Soft Fork | Non-Contentious Soft Fork |
|--------|----------------------|---------------------------|
| **Activation Mechanism** | UASF + URSF (mutual rejection) | UASF only (no resistance) |
| Block Propagation | Symmetric (neither accepts the other's blocks) | Asymmetric (old nodes accept new blocks) |
| Network Partition | Hard partition, no cross-communication | Soft partition, one-way block flow |
| Real-World Example | SegWit2x, Bitcoin Cash split | SegWit activation, Taproot |
| Reorg Behavior | Pools reorg when switching forks | No reorgs (old chain stays heavier) |
| Chain Relationship | Two independent chains | New chain is a subset of old chain's valid blocks |

---

## Contentious Soft Fork (Symmetric Partition)

### Activation Mechanism: UASF + URSF

A contentious soft fork occurs when **both sides actively reject the other's blocks**:

- **v27 (UASF - User Activated Soft Fork)**: Nodes enforce new stricter rules and reject blocks that don't comply. Users and economic nodes demand the new rules be followed.

- **v26 (URSF - User Resisted Soft Fork)**: Nodes actively resist the soft fork by rejecting blocks that signal support for or comply with the new rules. This is a deliberate counter-movement to prevent activation.

The combination of UASF + URSF creates mutual incompatibility - a true network split where neither side accepts the other's blocks.

### Model Description

In a contentious soft fork, the network splits into two incompatible factions:

```
v27 partition                    v26 partition
┌─────────────────┐              ┌─────────────────┐
│  v27 nodes      │     ✗        │  v26 nodes      │
│  (new rules)    │◄────────────►│  (old rules)    │
│                 │  No blocks   │                 │
│  Rejects v26    │  cross       │  Rejects v27    │
└─────────────────┘              └─────────────────┘
```

**Characteristics:**
- Both partitions reject blocks from the other
- Complete network isolation between factions
- Each chain grows independently
- Miners who switch forks must reorganize their chain
- Creates two competing currencies with separate market prices

### When This Applies

- **UASF meets URSF**: Users activate new rules while others actively resist
- **Hard forks**: Block size increase, PoW change, or other incompatible changes
- **Political splits**: Ideological disagreements leading to mutual rejection
- **Historical examples**: Bitcoin Cash (2017), SegWit2x opposition

### Implementation

Standard partition mode with no cross-partition communication:

```yaml
# networkGen/scenarios/contentious_fork.yaml
partition_mode: "static"
# No accepts_foreign_blocks - complete isolation
```

### Metrics of Interest

- **Reorg events**: Pools switching forks must reorganize
- **Orphan rate**: Blocks mined on abandoned fork become orphans
- **Fork volatility**: Frequency and depth of chain switches
- **Price divergence**: Market valuation of competing chains

---

## Non-Contentious Soft Fork (Asymmetric Propagation)

### Activation Mechanism: UASF Only (No URSF)

A non-contentious soft fork occurs when **only the upgrading side enforces new rules**:

- **v27 (UASF - User Activated Soft Fork)**: Nodes enforce new stricter rules. Blocks must comply with the new consensus rules to be accepted.

- **v26 (No URSF - Passive Old Nodes)**: Nodes have simply not upgraded yet. They are **not actively resisting** - they just continue running old software. Since v27 blocks follow stricter rules that are a subset of v26's valid blocks, v26 nodes accept them as valid.

The absence of a URSF means v26 nodes don't reject v27 blocks. They see them as valid (if perhaps unusual) blocks and store them in their chain. This is the natural state of soft fork activation - old nodes don't need to upgrade to accept blocks from upgraded miners.

### Model Description

In a non-contentious soft fork, the upgrade introduces stricter rules that are backward-compatible:

```
v27 partition (strict)           v26 partition (permissive)
┌─────────────────┐              ┌─────────────────┐
│  v27 nodes      │              │  v26 nodes      │
│  (new rules)    │─────────────►│  (old rules)    │
│                 │  v27 blocks  │                 │
│  Rejects v26    │  accepted    │  Accepts v27    │
│  blocks         │              │  blocks         │
└─────────────────┘              └─────────────────┘
        │                                │
        │         ✗ No v26 blocks        │
        └────────────────────────────────┘
```

**Characteristics:**
- v27 (new rules) blocks are valid under v26 (old rules)
- v26 nodes accept and store v27 blocks but follow their own heavier chain
- v27 nodes never see v26 blocks (would reject them as invalid)
- No reorgs occur - each partition stays on its own chain tip
- Single currency with unified price discovery (eventually)

### When This Applies

- Soft fork activations (SegWit, Taproot, CheckSequenceVerify)
- Tightening of consensus rules
- New script opcodes that old nodes treat as OP_SUCCESS/anyone-can-spend
- Miner-activated soft forks (MASF) during activation period

### Implementation

#### Network Metadata

Each node has an `accepts_foreign_blocks` flag in its metadata:

```yaml
# network.yaml node metadata
node-0003:
  partition: "v26"
  accepts_foreign_blocks: true   # v26 accepts v27 blocks

node-0000:
  partition: "v27"
  accepts_foreign_blocks: false  # v27 rejects v26 blocks
```

#### Network Generator

The `scenario_network_generator.py` automatically sets this flag based on partition:

```python
# v26 nodes accept v27 blocks; v27 nodes reject v26 blocks
'accepts_foreign_blocks': partition == 'v26'
```

#### Scenario Runner

The `partition_miner_with_pools.py` implements asymmetric propagation:

```python
def build_foreign_accepting_nodes(self):
    """Identify v26 nodes that accept foreign (v27) blocks."""
    self.foreign_accepting_nodes = []
    for node in self.v26_nodes:
        metadata = self.node_metadata.get(node_name, {})
        if metadata.get('accepts_foreign_blocks', False):
            self.foreign_accepting_nodes.append(node)

def propagate_to_foreign_accepting(self, miner, fork_id: str):
    """After mining a v27 block, submit it to v26 nodes."""
    if fork_id != 'v27' or not self.foreign_accepting_nodes:
        return

    block_hash = miner.getbestblockhash()
    raw_block = miner.getblock(block_hash, 0)
    bridge_node = self.foreign_accepting_nodes[0]
    result = bridge_node.submitblock(raw_block)
    # result is None on success
```

#### Block Flow

1. v27 miner creates block following strict new rules
2. Block propagates within v27 partition via P2P
3. Scenario runner calls `submitblock` on a v26 bridge node
4. v26 bridge node accepts block (valid under old rules)
5. Block propagates within v26 partition via P2P
6. v26 nodes store block but stay on their own chain tip (more cumulative work)

### Metrics of Interest

- **Block acceptance rate**: Verify v26 nodes store v27 blocks
- **Chain height delta**: v26 should stay ahead (majority hashrate)
- **Price convergence**: Eventually should converge to single price
- **Miner migration**: Economic incentives may pull miners to stricter chain

---

## Test Results Comparison

### Contentious Soft Fork (Example: `close_battle`)

```
Blocks Mined: v27=156, v26=152
Reorg Events: 12
Total Blocks Orphaned: 47
Fork Volatility Index: 0.089
Pool Switches: 8 (pools changed forks based on profitability)
```

Pools actively switched between forks, causing reorgs and orphaned blocks.

### Non-Contentious Soft Fork (Example: `asymmetric_softfork`)

```
Blocks Mined: v27=41, v26=43
Reorg Events: 0
Total Blocks Orphaned: 0
Fork Volatility Index: 0.0
Pool Behavior: Mined on both chains without reorgs
```

Zero reorgs because:
- v26 accepts v27 blocks but stays on its heavier chain
- Pools mining v27 blocks have them accepted by both partitions
- No chain reorganization needed when "switching" - both chains have the blocks

---

## Scenario Configuration

### Creating a Non-Contentious Soft Fork Test

```yaml
# networkGen/scenarios/taproot_activation.yaml
name: "taproot-activation-test"
description: "Non-contentious soft fork: Taproot activation with minority signaling"

# Hashrate split - majority hasn't upgraded yet
v27_economic_pct: 30
v27_hashrate_pct: 25

# v27 = Taproot-enforcing nodes (strict)
# v26 = Pre-Taproot nodes (permissive, accept Taproot blocks as valid)

pool_overrides:
  # Early adopters - committed to new rules
  - pool_name: "Foundry USA"
    fork_preference: "v27"
    ideology_strength: 0.9

  # Hasn't upgraded yet - follows old rules but accepts new blocks
  - pool_name: "AntPool"
    fork_preference: "v26"
    ideology_strength: 0.3  # Will switch if profitable

partition_mode: "static"
# accepts_foreign_blocks is set automatically by generator
```

### Running the Test

```bash
# Generate network
python networkGen/scenario_network_generator.py \
    --scenario networkGen/scenarios/taproot_activation.yaml \
    --output networks/taproot_activation

# Deploy and run
warnet deploy networks/taproot_activation
warnet run scenarios/partition_miner_with_pools.py \
    --pool-scenario=taproot_activation \
    --economic-scenario=taproot_activation \
    --enable-difficulty \
    --enable-reorg-metrics \
    --duration=1800
```

---

## Key Observations from Testing

### Non-Contentious Soft Fork Dynamics

1. **No Wasted Work**: Unlike contentious forks, miners don't orphan blocks when the network eventually converges. v27 blocks are already in v26's block database.

2. **Economic Pull**: Even with minority hashrate, the v27 chain can attract miners if it has economic advantages (higher fees, price premium). In our test, v27 achieved 70% economic activity despite ~35% hashrate.

3. **Smooth Activation Path**: The asymmetric model shows how soft forks can activate smoothly - old nodes continue operating normally while new nodes enforce stricter rules.

4. **Reunion is Clean**: If/when v26 nodes upgrade to v27 rules, they already have all v27 blocks. No massive reorg needed - they just start enforcing the new rules.

### Contentious Soft Fork Dynamics

1. **High Reorg Cost**: Pools switching forks must reorganize, orphaning previously mined blocks.

2. **Market Fragmentation**: Two separate prices emerge, creating arbitrage opportunities and uncertainty.

3. **Hashrate Wars**: Each faction tries to attract hashrate to make their chain "win."

4. **Permanent Split Risk**: If neither chain dies, both continue indefinitely as separate currencies.

---

## Dynamic Partition Switching

### Overview

Nodes can dynamically switch between partitions during the simulation based on economic conditions and ideology. This models real-world behavior where users and businesses may change which fork they support based on price, network effects, and conviction.

### Enabling Dynamic Switching

```bash
warnet run scenarios/partition_miner_with_pools.py \
    --enable-dynamic-switching \
    --pool-scenario=asymmetric_softfork \
    ...
```

### How It Works

1. **Periodic Evaluation**: At each hashrate update interval, economic and user nodes evaluate whether to switch partitions.

2. **Decision Factors**:
   - **Price Ratio**: If the other fork's price exceeds threshold, consider switching
   - **Ideology Strength**: High ideology nodes resist switching despite economics
   - **Switching Threshold**: Minimum price differential to trigger consideration
   - **Inertia**: Random delay factor to prevent oscillation

3. **P2P Reconnection**: When a node switches:
   - Disconnects from current partition peers
   - Connects to new partition peers
   - Syncs to new chain (may involve reorg)
   - Updates partition tracking

### Example Switch Logic

```python
# Node on v27 considers switching to v26:
if fork_preference == 'v26' and ideology_strength > 0.7:
    # Ideological switch - committed to v26
    switch = True
elif price_ratio < (1 - switching_threshold) and ideology_strength < 0.3:
    # Economic switch - v27 price too low, low ideology
    switch = True
```

### Metrics Captured

- Total partition switches during simulation
- Direction of switches (v27→v26 vs v26→v27)
- Final partition distribution
- Per-switch details: node, reason, height change

### Research Questions This Enables

- **Fork Reunification**: Can economic pressure cause a losing fork to collapse?
- **Ideology Threshold**: What ideology strength prevents economic-driven switching?
- **Hysteresis**: Do nodes oscillate between forks or reach stable equilibrium?
- **Network Effects**: Does losing nodes to the other fork create cascading switches?

---

## Future Extensions

1. **Gradual Activation**: Model MASF signaling where v27 hashrate grows over time until threshold is reached.

2. **Mixed Propagation**: Some v26 nodes upgrade mid-simulation, changing the network topology.

3. **Transaction Compatibility**: Model transactions that are valid on one chain but not the other (e.g., using new opcodes).

4. **Fee Market Divergence**: Different fee markets on each chain affecting miner incentives.

5. **Replay Protection**: Model scenarios where transactions can be replayed across forks.

---

## Files Reference

| File | Purpose |
|------|---------|
| `networkGen/scenario_network_generator.py` | Sets `accepts_foreign_blocks` per node |
| `scenarios/partition_miner_with_pools.py` | Implements `propagate_to_foreign_accepting()` |
| `scenarios/config/network_metadata.yaml` | Stores node metadata including foreign block acceptance |
| `networkGen/scenarios/asymmetric_softfork_test.yaml` | Example non-contentious scenario |

---

## Terminology

| Term | Definition |
|------|------------|
| **UASF (User Activated Soft Fork)** | Activation method where users/nodes enforce new stricter rules regardless of miner signaling |
| **URSF (User Resisted Soft Fork)** | Counter-movement where users/nodes actively reject blocks that comply with a proposed soft fork |
| **Contentious Soft Fork** | Fork where both sides actively reject the other's blocks (UASF + URSF) |
| **Non-Contentious Soft Fork** | Fork where old nodes accept new blocks as valid (UASF only, no URSF) |
| **Asymmetric Propagation** | One-way block flow from strict (v27) to permissive (v26) nodes |
| **Foreign Block** | Block from the other partition |
| **Bridge Node** | Node that accepts foreign blocks via submitblock |
| **accepts_foreign_blocks** | Metadata flag indicating node accepts cross-partition blocks |
