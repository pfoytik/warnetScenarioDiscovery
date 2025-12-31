# Configurable Bitcoin Network Generator

Generate custom Warnet network configurations for economic fork testing with full control over:
- Bitcoin Core versions per node
- Economic metadata (custody, volume, consensus weight)
- Pool-to-node connection mappings
- Network topology
- Pool hashrate distribution

---

## Quick Start

```bash
# Generate network from scenario config
python3 configurable_network_generator.py scenarios/baseline_pool_mining.yaml output.yaml

# Deploy and test
warnet deploy output.yaml
warnet run ~/bitcoinTools/warnet/warnet/scenarios/economic_miner.py --interval 10 --pools 10 --duration 600 --mature
```

---

## Features

### 1. **Node-Level Configuration**
- Set Bitcoin Core version per node (e.g., v26.0, v27.0)
- Configure economic metadata (custody BTC, daily volume)
- Customize connection limits and mempool sizes
- Add descriptive metadata for each node

### 2. **Pool-to-Node Mappings**
- Explicitly define which pools connect to which nodes
- Create realistic economic relationships
- Test specific fork scenarios (custody vs volume)

### 3. **Three-Tier Architecture**
- **Economic Nodes**: Major exchanges, payment processors (high influence)
- **Pool Nodes**: Mining pools with real-world hashrate distribution
- **Network Nodes**: Regular propagation nodes (optional economic weight)

### 4. **Flexible Topology**
- Full economic mesh
- Custom pool peering strategies
- Ring + strategic connections for network nodes

---

## Scenario Configuration Format

Create a YAML file defining your test scenario:

```yaml
name: "my-test-scenario"
description: "Description of what this scenario tests"

# Economic Nodes (exchanges, payment processors)
economic_nodes:
  - role: "major_exchange"
    version: "27.0"              # Bitcoin Core version
    custody_btc: 1900000         # BTC in custody
    daily_volume_btc: 15000      # Daily trading volume
    max_connections: 125         # Connection limit
    max_mempool_mb: 500          # Mempool size
    description: "Optional description"

  - role: "payment_processor"
    version: "27.0"
    custody_btc: 50000
    daily_volume_btc: 400000
    # ... more config ...

# Pool Nodes (mining infrastructure)
pool_nodes:
  - pool_name: "Foundry USA"
    hashrate_percent: 26.89      # Real hashrate percentage
    version: "27.0"
    connected_to: [0, 1, 2]      # Node indices this pool connects to
    max_connections: 50
    max_mempool_mb: 200

  - pool_name: "AntPool"
    hashrate_percent: 19.25
    version: "27.0"
    connected_to: [1, 2, 3]
    # ... more config ...

# Network Nodes (regular propagation)
network_nodes:
  - version: "27.0"
    custody_btc: 100              # Optional small economic weight
    daily_volume_btc: 500
    max_connections: 30
    max_mempool_mb: 100

  - version: "27.0"              # No economic weight
    max_connections: 30
    max_mempool_mb: 100
    # ... more nodes ...

# Network Topology
topology:
  type: "full_economic_mesh"         # Economic nodes fully connected
  pool_peering: "neighbors"           # Pools connect to neighbors
  network_topology: "ring_plus_economic"  # Network nodes in ring

# Optional: Test metadata for documentation
test_parameters:
  fork_trigger: "Description of what causes the fork"
  expected_chains: 2
  research_question: "What are we testing?"
```

---

## Example Scenarios

### 1. Baseline Pool Mining (No Fork)

**File**: `scenarios/baseline_pool_mining.yaml`

**Purpose**: Test normal pool mining behavior without fork conditions

**Configuration**:
- All nodes on same version (v27.0)
- 5 economic nodes with diverse custody/volume
- 10 pools with real hashrate distribution
- 10 network propagation nodes

**Use Case**: Validate pool hashrate distribution, measure natural fork frequency

```bash
python3 configurable_network_generator.py scenarios/baseline_pool_mining.yaml baseline.yaml
```

### 2. Custody vs Volume Fork

**File**: `scenarios/custody_vs_volume_fork.yaml`

**Purpose**: Test what happens when custody-heavy and volume-heavy nodes disagree

**Configuration**:
- Economic nodes split by version:
  - Nodes 0-1: v26.0 (custody-heavy exchanges, 2.75M BTC)
  - Nodes 2-4: v27.0 (volume-heavy processors, 1.14M BTC/day)
- Pools connected to mix of both groups
- 10 network nodes (mixed versions)

**Research Question**: Will pools follow custody weight or volume weight?

**Expected Behavior**:
- Fork at incompatible consensus rule change
- Pools must choose which chain to mine
- Economic analysis shows which chain has majority

```bash
python3 configurable_network_generator.py scenarios/custody_vs_volume_fork.yaml fork_test.yaml
```

---

## Configuration Fields

### Economic Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | No | Node role (exchange, payment_processor, etc.) |
| `version` | string | No | Bitcoin Core version (default: 27.0) |
| `custody_btc` | number | **Yes** | BTC in custody |
| `daily_volume_btc` | number | **Yes** | Daily trading volume in BTC |
| `max_connections` | number | No | Max peers (default: 125) |
| `max_mempool_mb` | number | No | Mempool size in MB (default: 500) |
| `description` | string | No | Human-readable description |

### Pool Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pool_name` | string | **Yes** | Pool name (e.g., "Foundry USA") |
| `hashrate_percent` | number | **Yes** | Hashrate percentage |
| `version` | string | No | Bitcoin Core version (default: 27.0) |
| `connected_to` | list[int] | No | Node indices to connect to |
| `max_connections` | number | No | Max peers (default: 50) |
| `max_mempool_mb` | number | No | Mempool size in MB (default: 200) |

### Network Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | No | Bitcoin Core version (default: 27.0) |
| `custody_btc` | number | No | Optional small custody amount |
| `daily_volume_btc` | number | No | Optional small volume |
| `max_connections` | number | No | Max peers (default: 30) |
| `max_mempool_mb` | number | No | Mempool size in MB (default: 100) |

---

## Consensus Weight Calculation

Economic nodes are assigned a **consensus weight** based on:

```python
consensus_weight = (0.7 × custody_btc + 0.3 × daily_volume_btc) / 10000
```

This dual-metric model balances:
- **70% custody**: BTC holdings (security, skin in the game)
- **30% volume**: Daily transactions (network usage, economic activity)

**Example**:
- Node with 1M BTC custody + 100K BTC/day volume:
  - Weight = (0.7 × 1,000,000 + 0.3 × 100,000) / 10,000
  - Weight = (700,000 + 30,000) / 10,000
  - Weight = 73.0

---

## Network Topology Options

### Economic Mesh (`type: "full_economic_mesh"`)
All economic nodes connected to each other. Best for:
- Ensuring economic nodes stay synchronized
- Realistic inter-exchange connectivity

### Pool Peering Strategies

**`neighbors`** (default):
- Each pool connects to next pool in sequence
- Forms chain: Pool 0 → Pool 1 → Pool 2 → ...

**`full_mesh`**:
- All pools connected to all other pools
- Higher connectivity, more bandwidth

### Network Topology Strategies

**`ring_plus_economic`** (default):
- Network nodes form ring (each connects to next)
- Every 3rd network node connects to an economic node
- Good for propagation testing

---

## Usage Workflow

### 1. Create Scenario Config

```yaml
# my_scenario.yaml
name: "test-fork"
description: "Test version conflict"

economic_nodes:
  - version: "26.0"
    custody_btc: 1000000
    daily_volume_btc: 10000
  # ... more nodes ...

pool_nodes:
  - pool_name: "Test Pool"
    hashrate_percent: 50.0
    connected_to: [0]
  # ... more pools ...

network_nodes:
  - version: "27.0"
  # ... more nodes ...

topology:
  type: "full_economic_mesh"
```

### 2. Generate Network

```bash
python3 configurable_network_generator.py my_scenario.yaml network.yaml
```

Output:
```
✓ Validated scenario: test-fork
... (configuration summary) ...
✓ Generated network configuration:
  Scenario: test-fork
  Economic nodes: 2
  Pool nodes: 2
  Network nodes: 5
  Total nodes: 9
  Total connections: 15

  Saved to: network.yaml
```

### 3. Review Generated Config

```bash
cat network.yaml
```

Verify:
- Node versions are correct
- Pool connections match expectations
- Economic metadata is present

### 4. Deploy Network

```bash
warnet deploy network.yaml
warnet status
```

### 5. Run Pool Mining

```bash
# Run mining with configured pools
warnet run ~/bitcoinTools/warnet/warnet/scenarios/economic_miner.py \
    --interval 10 \
    --pools 10 \
    --duration 600 \
    --mature
```

**Note**: The `economic_miner.py` scenario will automatically:
- Detect pool metadata in network config
- Use configured pool-to-node connections
- Fall back to random connections if no metadata found

### 6. Monitor Forks

```bash
# In another terminal, monitor for forks
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring

python3 auto_economic_analysis.py \
    --network-config /path/to/network.yaml \
    --live-query \
    --fork-depth-threshold 3
```

---

## Real-World Pool Hashrate Data

The generator includes real Bitcoin network pool distribution:

| Rank | Pool | Hashrate % |
|------|------|------------|
| 1 | Foundry USA | 26.89% |
| 2 | AntPool | 19.25% |
| 3 | ViaBTC | 11.39% |
| 4 | F2Pool | 11.25% |
| 5 | SpiderPool | 9.09% |
| 6 | MARA Pool | 5.00% |
| 7 | SECPOOL | 4.18% |
| 8 | Luxor | 3.21% |
| 9 | Binance Pool | 2.49% |
| 10 | OCEAN | 1.42% |

Source: 1-month Bitcoin network sample (4,302 blocks)

---

## Advanced Usage

### Custom Topology

Override automatic topology with custom edges:

```yaml
topology:
  custom_edges:
    - [0, 1]    # Node 0 connects to node 1
    - [0, 2]    # Node 0 connects to node 2
    - [1, 2]    # Node 1 connects to node 2
    # ... define all connections manually ...
```

### Mixed Economic Weight

Give network nodes small economic weight:

```yaml
network_nodes:
  - version: "27.0"
    custody_btc: 100        # Small custody
    daily_volume_btc: 500   # Small volume
    # Still a propagation node, but has tiny economic influence
```

### Version-Based Forks

Create incompatibility-based forks:

```yaml
economic_nodes:
  - version: "26.0"    # Old version (conservative)
    custody_btc: 2000000

  - version: "27.0"    # New version (progressive)
    custody_btc: 500000
```

When v27.0 introduces consensus rule change:
- Fork occurs automatically
- Pools must choose which chain to mine
- Economic analysis shows majority

---

## Testing Checklist

### Before Deploying

- [ ] Reviewed scenario configuration
- [ ] Verified pool connections make sense
- [ ] Checked version assignments (fork conditions)
- [ ] Validated economic metadata (realistic values)
- [ ] Confirmed total hashrate ~= 100%

### After Deploying

- [ ] All nodes running (`warnet status`)
- [ ] Correct peer counts
- [ ] Mining scenario starts successfully
- [ ] Fork monitoring detecting expected behavior
- [ ] Economic analysis calculates risk scores

### Data Collection

- [ ] Record fork frequency
- [ ] Measure fork depth distribution
- [ ] Track pool behavior during forks
- [ ] Analyze economic risk scores
- [ ] Document time to consensus

---

## Troubleshooting

### "Missing required field in scenario"
- Check YAML syntax
- Ensure all required fields present (custody_btc, daily_volume_btc, pool_name, hashrate_percent)

### "No pool metadata found, using random connection distribution"
- Expected if network not generated by this tool
- Pool connections will be random (30-70% of nodes)
- To fix: Regenerate network with this tool

### Forks not occurring
- Check that nodes have different versions AND incompatible consensus rules
- Verify network is properly connected
- Try longer test duration

### Economic analysis shows unexpected results
- Verify economic metadata in network.yaml
- Check consensus weight calculations
- Review pool-to-node connections

---

## Files Created

```
warnetScenarioDiscovery/networkGen/
├── configurable_network_generator.py    # Main generator script
├── scenarios/
│   ├── baseline_pool_mining.yaml        # No-fork baseline
│   ├── custody_vs_volume_fork.yaml      # Fork scenario
│   └── (your custom scenarios)
└── README.md                             # This file
```

---

## Future Enhancements

**Planned**:
- [ ] Support for multiple pool-to-node connection strategies
- [ ] Network segmentation scenarios (partition testing)
- [ ] Time-based version upgrades (simulate gradual rollout)
- [ ] Randomized economic metadata generation (for Monte Carlo testing)
- [ ] Template-based scenario generation (fill in the blanks)

**Ideas**:
- GUI for scenario creation
- Scenario validation against historical forks
- Auto-generation from real-world network topology data

---

## Examples

See `scenarios/` directory for complete examples:
- `baseline_pool_mining.yaml` - Normal operation test
- `custody_vs_volume_fork.yaml` - Economic conflict test

---

**Version**: 1.0
**Date**: 2025-12-29
**Status**: Production-ready
