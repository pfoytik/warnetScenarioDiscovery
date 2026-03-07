# Dynamic Network Partitioning Guide

## Overview

This guide explains how to create Bitcoin network scenarios with **dynamic topology changes** - allowing you to partition and reconnect networks at specific times or based on network events.

## Architecture

The dynamic partitioning system consists of:

1. **partition_utils.sh** - Bash utilities for network topology control
2. **partition_miner.py** - Enhanced Python scenario (future enhancement)
3. **Timeline YAML** - Declarative scenario definitions
4. **run_partition_test.sh** - Test automation wrapper

## Quick Start

### Option 1: Static Partition (Current - No Changes)

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools
./run_partition_test.sh 5.3 70 30 --duration 300
```

**What happens:**
- Network deploys with ZERO cross-partition edges (defined in network.yaml)
- Common history generated on v27 nodes only
- Both partitions mine independently
- No reconnection

### Option 2: Dynamic Partition (Future - With Timeline)

```bash
# Deploy network with connected topology
warnet deploy test-networks/test-5.3-connected/

# Run scenario with timeline
warnet run partition_miner.py --timeline scenarios/example_timeline.yaml
```

**What happens:**
- Network starts fully connected
- Common history propagates to ALL nodes
- Partition created dynamically at t=120s using `setban`
- Independent mining t=150s to t=450s
- Reconnection at t=450s using `clearbanned` + `addnode`
- Reorg monitoring t=480s to t=600s

## Partition Utilities Reference

### partition_by_version()

Creates bidirectional partition between Bitcoin versions:

```bash
source partition_utils.sh
partition_by_version \
    "/path/to/network.yaml" \
    "27.0" \    # v27 version
    "26.0" \    # v26 version
    86400       # Ban duration (seconds)
```

**How it works:**
1. Extracts node lists from network.yaml based on `image.tag`
2. Gets pod IPs via kubectl
3. Bidirectional `setban` between version groups
4. Verifies ban count

### reconnect_all()

Removes all partitions and forces reconnections:

```bash
reconnect_all "/path/to/network.yaml"
```

**Steps:**
1. `clearbanned` on all nodes
2. `addnode <ip> onetry` for all peer pairs
3. Wait 10 seconds for connections
4. Verify peer counts with `getconnectioncount`

### verify_partition_isolation()

Checks that no cross-partition connections exist:

```bash
verify_partition_isolation \
    "/path/to/network.yaml" \
    "27.0" \
    "26.0"
```

**Verification:**
- Gets `getpeerinfo` from all nodes
- Checks peer IPs against version groups
- Reports any cross-partition connections

## Timeline YAML Format

### Structure

```yaml
scenario:
  name: "Scenario Name"
  description: "What this tests"
  duration: 600  # Total seconds

  network:
    v27_hashrate: 30
    v26_hashrate: 70
    v27_version: "27.0"
    v26_version: "26.0"
    block_interval: 10

timeline:
  - time: 0
    action: generate_common_history
    description: "Human-readable description"
    params:
      blocks: 101
      verify_all_nodes: true

  - time: 120
    action: partition_network
    params:
      method: version
      verify_isolation: true
```

### Supported Actions

#### generate_common_history
```yaml
- time: 0
  action: generate_common_history
  params:
    blocks: 101                  # Number of blocks to mine
    miner_version: "27.0"        # Which version mines
    wait_for_propagation: 60     # Seconds to wait
    verify_all_nodes: true       # Check all nodes at height
```

#### partition_network
```yaml
- time: 120
  action: partition_network
  params:
    method: version              # Partition by version
    ban_duration: 86400          # Seconds (24h default)
    verify_isolation: true       # Check no cross-partition peers
```

#### start_partition_mining
```yaml
- time: 150
  action: start_partition_mining
  params:
    duration: 300                # Mining duration
    v27_hashrate: 30             # Percentage
    v26_hashrate: 70
    monitor_interval: 30         # Fork depth monitoring
```

#### reconnect_network
```yaml
- time: 450
  action: reconnect_network
  params:
    clear_bans: true             # Run clearbanned
    force_connections: true      # Run addnode
    verify_reconnection: true    # Check peer counts
```

#### monitor_reorg
```yaml
- time: 480
  action: monitor_reorg
  params:
    duration: 120                # How long to monitor
    interval: 10                 # Sample every N seconds
    track_changes: true          # Log reorg events
```

#### economic_analysis
```yaml
- time: 600
  action: economic_analysis
  params:
    fork_depth_threshold: 3
    save_results: true
```

## Network Configuration Requirements

### For Static Partition (Current)

**network.yaml** must have zero cross-partition edges:

```yaml
nodes:
  # v27 nodes (0-9) - only connect within group
  - name: node-0000
    image:
      tag: '27.0'
    edges:
      - target: node-0001  # v27 node only
      - target: node-0002  # v27 node only

  # v26 nodes (10-19) - only connect within group
  - name: node-0010
    image:
      tag: '26.0'
    edges:
      - target: node-0011  # v26 node only
      - target: node-0012  # v26 node only
```

### For Dynamic Partition (Future)

**network-connected.yaml** must have edges BETWEEN partitions:

```yaml
nodes:
  # v27 nodes - connect to both v27 and v26
  - name: node-0000
    image:
      tag: '27.0'
    edges:
      - target: node-0001  # v27 node
      - target: node-0010  # v26 node (cross-partition!)
      - target: node-0011  # v26 node (cross-partition!)

  # v26 nodes - connect to both v26 and v27
  - name: node-0010
    image:
      tag: '26.0'
    edges:
      - target: node-0011  # v26 node
      - target: node-0000  # v27 node (cross-partition!)
      - target: node-0001  # v27 node (cross-partition!)
```

**Why?** Because `setban` only disconnects EXISTING connections. If nodes never had cross-partition edges, `setban` does nothing.

## Implementation Roadmap

### Phase 1: Bash Integration (Immediate)

Enhance `run_partition_test.sh` to support dynamic partitioning:

```bash
# Add options
--partition-mode [static|dynamic]
--reconnect-at <seconds>

# Example usage
./run_partition_test.sh 5.3 70 30 \
    --duration 600 \
    --partition-mode dynamic \
    --reconnect-at 450
```

**What changes:**
1. Deploy network-connected.yaml
2. Generate common history with verification
3. Call `partition_by_version()` at start of mining
4. Call `reconnect_all()` at specified time
5. Monitor reorg after reconnection

### Phase 2: Python Timeline Support (Next)

Enhance `partition_miner.py` with timeline execution:

```python
class PartitionMiner(Commander):
    def add_options(self, parser):
        parser.add_argument('--timeline', type=str,
                          help='Path to YAML timeline file')

    def run_test(self):
        if self.options.timeline:
            self.execute_timeline()
        else:
            self.run_simple_test()
```

### Phase 3: Event-Driven Triggers (Future)

Add conditional triggers based on network state:

```yaml
events:
  - trigger: fork_depth_threshold
    condition: "fork_depth >= 20"
    action: reconnect_network

  - trigger: height_difference
    condition: "abs(v27_height - v26_height) > 50"
    action: trigger_emergency_reconnect
```

## Example Scenarios

### Scenario 1: Delayed Reconnect Test

**Question:** Does economic weight matter when chains diverge then reconnect?

```yaml
timeline:
  - time: 0: Generate common history (101 blocks)
  - time: 120: Partition by version
  - time: 150: Mine independently (5 min)
    - v27: 30% hashrate, 70% economic weight
    - v26: 70% hashrate, 30% economic weight
  - time: 450: Reconnect
  - time: 480: Monitor reorg (2 min)
  - time: 600: Economic analysis
```

**Expected:** v26 has longer chain (more hashrate), wins reorg despite less economic weight.

### Scenario 2: Mid-Fork Reconnect

**Question:** What happens if we reconnect before fork gets deep?

```yaml
timeline:
  - time: 0: Common history
  - time: 120: Partition
  - time: 150: Start mining
  - time: 240: Reconnect after only 90s of divergence
  - time: 270: Continue monitoring
```

**Expected:** Quick reorg, minimal disruption.

### Scenario 3: Event-Triggered Reconnect (Future)

**Question:** Can we automatically reconnect when fork depth threshold is reached?

```yaml
events:
  - trigger: fork_depth_threshold
    condition: "fork_depth >= 10"
    action: reconnect_network
```

**Expected:** Reconnection happens whenever fork reaches 10 blocks deep, regardless of time.

## Debugging Tips

### Check Partition State

```bash
# From v27 node, check peers
warnet bitcoin rpc node-0000 getpeerinfo | jq -r '.[].addr'

# From v26 node, check peers
warnet bitcoin rpc node-0010 getpeerinfo | jq -r '.[].addr'

# Check ban list
warnet bitcoin rpc node-0000 listbanned
```

### Verify Common History Propagation

```bash
# Check all nodes at expected height
for node in node-{0000..0019}; do
    height=$(warnet bitcoin rpc $node getblockcount 2>/dev/null)
    hash=$(warnet bitcoin rpc $node getbestblockhash 2>/dev/null)
    echo "$node: height=$height hash=${hash:0:16}..."
done
```

### Monitor Reorg in Real-Time

```bash
# Watch tip changes
watch -n 2 'warnet bitcoin rpc node-0000 getblockcount; warnet bitcoin rpc node-0010 getblockcount'
```

## Future Extensions

### 1. Multiple Partitions

Support more than 2 partitions:

```yaml
partitions:
  - name: v27_majority
    version: "27.0"
    nodes: [node-0000, node-0001, ...]
    hashrate: 40

  - name: v26_majority
    version: "26.0"
    nodes: [node-0010, node-0011, ...]
    hashrate: 35

  - name: legacy
    version: "25.0"
    nodes: [node-0020, node-0021, ...]
    hashrate: 25
```

### 2. Gradual Reconnection

Reconnect nodes one-by-one instead of all-at-once:

```yaml
- time: 450
  action: reconnect_gradual
  params:
    rate: 1  # Reconnect 1 node per second
    order: random
```

### 3. Asymmetric Partitions

Different connectivity patterns:

```yaml
- time: 120
  action: partition_custom
  params:
    # v27 nodes fully connected to each other
    # v26 nodes have limited connectivity
    topology: "v27_mesh_v26_star"
```

## Summary

You now have:

✅ **partition_utils.sh** - Ready to use for bash-based dynamic partitioning
✅ **example_timeline.yaml** - Template for declarative scenarios
✅ **Documentation** - This guide

Next steps:
1. Test partition_utils.sh functions manually
2. Integrate into run_partition_test.sh (bash approach)
3. Later: Add timeline support to partition_miner.py (Python approach)

This foundation opens doors to sophisticated scenarios including event-driven triggers based on network state!
