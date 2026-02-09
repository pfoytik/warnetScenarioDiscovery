# Economic Node Modeling Capabilities Summary

## Complete Control Over Node Parameters

### 1. Bitcoin Core Version Control
**Capability:** Set different versions per node via `image` field

**Examples from economic-30-nodes.yaml:**
- Line 20: `image: "bitcoindevproject/bitcoin:27.0"` (latest)
- Line 274: `image: "bitcoindevproject/bitcoin:26.0"` (previous)
- Line 472: `image: "bitcoindevproject/bitcoin:25.0"` (older)
- Line 719: `image: "bitcoindevproject/bitcoin:24.0"` (very old)

**Use case:** Test consensus behavior across version splits

### 2. Mempool Policy Configuration
**Capability:** Full control over mempool parameters in `bitcoin_config` section

**Available parameters:**
- `maxmempool`: Size in MB (default: 300)
  - Exchange tier 1: 10000 MB (10GB)
  - Exchange tier 2: 5000 MB (5GB)
  - Payment processor: 2000 MB (2GB)
  - Constrained node: 50 MB
- `mempoolexpiry`: Hours before eviction (default: 72)
  - Payment processor example: 1 hour (line 145)
- `minrelaytxfee`: Minimum fee rate (not shown but supported)

**Use case:** Test fee market dynamics, mempool propagation differences

### 3. Peer Connection Topology
**Capability:** Explicit control via `connections` array

**Topology patterns:**
- **Hub nodes** (exchanges): 15-30 connections to other economic + relay nodes
- **Relay nodes**: 8-15 connections, at least 1 to economic node
- **Constrained nodes**: 2-5 connections only
- **Isolated groups**: Limit connections to specific subset

**Example (lines 44-57):**
```yaml
connections:
  - exchange-tier1-binance
  - exchange-tier2-kraken
  - payment-processor-bitpay
  - custody-fidelity
  - relay-node-1
  - relay-node-2
```

**Use case:** Test information propagation, network partitions

### 4. Node Isolation & Manual Peering
**Capability:** Disable network discovery for controlled peering

**Configuration:**
```yaml
bitcoin_config:
  listen: 1
  discover: 0  # Manual peer selection only
```

**Example:** Custody node (line 179) uses `discover: 0` for security

**Use case:** Test Byzantine scenarios, create network partitions

### 5. Economic Weight System
**Capability:** Assign influence weight via `metadata.weight`

**Weight distribution in 30-node network:**
- Exchange tier 1: weight 15 (2 nodes = 30)
- Exchange tier 2: weight 10 (1 node = 10)
- Payment processor: weight 8 (1 node = 8)
- Custody: weight 7 (1 node = 7)
- Relay: weight 1 (20 nodes = 20)
- Constrained: weight 0.5 (5 nodes = 2.5)
- **Total economic weight: 55 out of 77.5 = 71%**

**Use case:** BCAP modeling - measure economic node influence on consensus

### 6. Resource Allocation
**Capability:** Set CPU and memory per node for realistic constraints

**Tiers:**
- **Exchange tier 1:** 4-8 CPU cores, 16-32GB RAM
- **Exchange tier 2:** 2-4 CPU cores, 8-16GB RAM
- **Payment processor:** 2-4 CPU cores, 4-8GB RAM
- **Relay:** 0.5-1 CPU cores, 2-4GB RAM
- **Constrained:** 0.125-0.25 CPU cores, 512MB-1GB RAM

**Use case:** Test performance under resource constraints

### 7. Node Type Metadata
**Capability:** Tag nodes for tracking and analysis

**Available fields:**
```yaml
metadata:
  weight: 15
  node_type: exchange
  adoption_speed: fast  # fast, medium, slow
tags:
  - economic_node
  - exchange
  - tier_1
  - high_volume
```

**Use case:** Group analysis, scenario targeting

## Example Test Scenarios Enabled

### Scenario 1: Version Split Testing
- 50% economic nodes on v27.0 (support new feature)
- 50% economic nodes on v26.0 (don't support)
- Measure: Do transactions propagate? Is there a split?

### Scenario 2: Mempool Policy Divergence
- Exchange A: `maxmempool: 50` (tiny)
- Exchange B: `maxmempool: 10000` (huge)
- Measure: How do they handle fee spikes differently?

### Scenario 3: Network Partition
- Group 1: exchanges 1-2 + relays 1-10 (isolated)
- Group 2: exchanges 3-4 + relays 11-20 (isolated)
- Measure: How long until chain split? How does reorganization work?

### Scenario 4: Byzantine Economic Node
- Exchange with `discover: 0` and only malicious peers
- Measure: Can it influence network propagation?

## Comparison: EconomicNode Class vs Direct YAML

### Using EconomicNode Class (Limited)
```python
node = EconomicNode("exchange-1", "exchange_tier1", version="26.0")
# ✓ Can set: name, type (4 presets), version
# ✗ Cannot customize: mempool size, connections, policies
```

### Direct YAML (Full Control)
```yaml
- name: exchange-1-custom
  image: "bitcoindevproject/bitcoin:26.0"
  bitcoin_config:
    maxmempool: 50  # ✓ Custom value
    mempoolexpiry: 1  # ✓ Custom policy
    minrelaytxfee: 0.00001  # ✓ Any bitcoin.conf parameter
  connections:  # ✓ Explicit topology
    - exchange-2
    - relay-1
```

**Recommendation:** Use direct YAML for full control in your tests.

## How to Create Custom Networks

### Option 1: Direct YAML (Recommended for testing)
1. Copy `test-networks/custom-5-node.yaml` as template
2. Modify nodes, versions, policies as needed
3. Deploy with: `warnet deploy <your-network>.yaml`

### Option 2: Generator Script (For large networks)
```bash
cd warnet-economic-implementation/warnet-economic-examples/scripts/
python economic_network_utils.py generate --nodes 100 --economic-pct 0.20 --output my-network.yaml
# Then manually edit the YAML to customize specific nodes
```

### Option 3: Hybrid Approach
1. Generate base network with script
2. Manually edit specific economic nodes for custom scenarios
3. Use version control to track variations

## Key Takeaways

1. **✓ Different Bitcoin Core versions per node** - YES (image field)
2. **✓ Different mempool policies per node** - YES (bitcoin_config section)
3. **✓ Control peer connections** - YES (connections array)
4. **✓ Create isolated groups** - YES (discover: 0 + limited connections)

You have **complete control** over all parameters needed for consensus testing!
