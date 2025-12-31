# Partition Network Testing - Complete Handoff Document

**Date**: December 30, 2025
**Status**: Test 5.3 Generated ✅ | Week 2 Tests Ready for Execution

---

## Executive Summary

This document provides complete instructions for executing the systematic Bitcoin network fork testing matrix. You now have:

✅ **Partition Network Generator** - Creates version-segregated networks
✅ **Test 5.3 Configuration** - Successfully generated and validated
⏳ **Remaining Infrastructure** - Scenarios and scripts needed for execution

**Goal**: Quantify Bitcoin network resilience by testing 15 scenarios varying version distribution and economic weight distribution.

---

## What Has Been Built

### 1. Partition Network Generator

**File**: `partition_network_generator.py`
**Location**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen/`

**Features**:
- Version-segregated topology (v27 ONLY connects to v27, v22 ONLY to v22)
- Smart pool distribution using real hashrate data
- Auto-calculated economic weight distribution
- Power-law distribution for economic nodes
- Test matrix naming convention

**Usage**:
```bash
python3 partition_network_generator.py \
    --test-id 5.3 \
    --v27-economic 70 \
    --v27-hashrate 30
```

**Output**: `../../test-networks/test-5.3-economic-70-hashrate-30/network.yaml`

### 2. Test 5.3 Configuration (Completed)

**Status**: ✅ Generated and validated

**Configuration**:
- Total nodes: 20 (10 v27, 10 v22)
- v27 partition: 70% economic weight, 31.46% hashrate
- v22 partition: 30% economic weight, 66.91% hashrate
- Cross-partition edges: 0 (isolated partitions)

**Files Created**:
```
test-networks/test-5.3-economic-70-hashrate-30/
└── network.yaml
```

### 3. Supporting Tools (Already Available)

**Economic Analysis**: `auto_economic_analysis.py`
- Fork depth threshold filtering (default: 3 blocks)
- Economic risk scoring
- Natural split vs sustained fork classification

**Network Generators** (Legacy):
- `configurable_network_generator.py` - YAML scenario-based
- Various pool distribution tools

---

## Testing Matrix Overview

### Week 2 - Foundation (3 Tests)

| Test ID | v27 Economic % | v27 Hashrate % | v22 Economic % | v22 Hashrate % | Status |
|---------|---------------|----------------|----------------|----------------|--------|
| 5.3 | 70% | 30% | 30% | 70% | ✅ Generated |
| 3.5 | 30% | 70% | 70% | 30% | ⏳ Pending |
| 4.4 | 50% | 50% | 50% | 50% | ⏳ Pending |

### Week 3 - Thresholds (6 Tests)

| Test ID | v27 Economic % | v27 Hashrate % | v22 Economic % | v22 Hashrate % |
|---------|---------------|----------------|----------------|----------------|
| 6.2 | 80% | 20% | 20% | 80% |
| 6.4 | 80% | 40% | 20% | 60% |
| 6.6 | 80% | 60% | 20% | 40% |
| 2.6 | 20% | 60% | 80% | 40% |
| 4.6 | 50% | 60% | 50% | 40% |

### Week 4 - Alignment (6 Tests)

| Test ID | v27 Economic % | v27 Hashrate % | v22 Economic % | v22 Hashrate % |
|---------|---------------|----------------|----------------|----------------|
| 2.2 | 20% | 20% | 80% | 80% |
| 3.3 | 30% | 30% | 70% | 70% |
| 5.5 | 70% | 70% | 30% | 30% |
| 2.5 | 20% | 70% | 80% | 30% |
| 5.2 | 70% | 20% | 30% | 80% |

---

## Test Execution Workflow

### Step 1: Generate Network Configuration

For each test (e.g., Test 3.5):

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen

python3 partition_network_generator.py \
    --test-id 3.5 \
    --v27-economic 30 \
    --v27-hashrate 70
```

**Verification**:
- Check output shows correct economic/hashrate percentages
- Verify 0 cross-partition edges
- Review `test-networks/test-3.5-economic-30-hashrate-70/network.yaml`

### Step 2: Deploy Network

```bash
cd ~/bitcoinTools/warnet/test-networks/test-3.5-economic-30-hashrate-70

warnet deploy network.yaml
warnet status
```

**Wait for**: All nodes running and connected (check peer counts)

### Step 3: Create Common History (Blocks 0-101)

**Critical**: Both partitions must start from identical genesis

```bash
# Generate 101 blocks on ONE node (e.g., node-0000 from v27 partition)
for i in {1..101}; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 bcrt1q...
    sleep 0.5
done

# Wait for propagation to all nodes
sleep 30

# Verify all nodes at height 101
warnet bitcoin rpc node-0000 getblockcount
warnet bitcoin rpc node-0010 getblockcount  # v22 partition node
```

### Step 4: Enforce Partition (Network Segmentation)

**Method 1: Kubernetes Network Policies** (Recommended)
```bash
# Apply network policy to block cross-partition traffic
kubectl apply -f partition-network-policy.yaml
```

**Method 2: Manual Disconnection** (If needed)
```bash
# Disconnect all v27-v22 peer connections
# (Script needed: disconnect_partitions.sh)
```

### Step 5: Run Partition Mining

**File Needed**: `partition_miner.py` (see implementation section below)

```bash
warnet run partition_miner.py \
    --v27-hashrate 30 \
    --v22-hashrate 70 \
    --interval 10 \
    --duration 1800 \
    --start-height 101
```

**What This Does**:
- Mines blocks on BOTH partitions simultaneously
- Respects configured hashrate percentages
- Each partition develops independent chain from height 102+

### Step 6: Monitor Fork Development

**File Needed**: `monitor_dual_partition.sh` (see implementation section below)

```bash
# In separate terminal
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools

./monitor_dual_partition.sh \
    --network test-3.5 \
    --interval 30 \
    --duration 1800
```

**Output**: Time series of v27_height, v22_height, fork_depth

### Step 7: Economic Analysis

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring

python3 auto_economic_analysis.py \
    --network-config ../../test-networks/test-3.5-economic-30-hashrate-70/network.yaml \
    --live-query \
    --fork-depth-threshold 3 \
    --output-json results/test-3.5-results.json
```

**Captures**:
- Fork depth progression
- Economic risk scores
- Chain weight distribution
- Pool behavior

### Step 8: Cleanup

```bash
warnet down
```

---

## Implementation Needed

### 1. Partition Mining Scenario (CRITICAL)

**File**: `~/bitcoinTools/warnet/warnet/scenarios/partition_miner.py`

**Purpose**: Mine blocks on both partitions independently with hashrate-weighted probability

**Key Features**:
- NO fork choice logic (each partition mines its own chain)
- Hashrate-weighted block production
- Tracks both partition heights
- Simple alternating strategy

**Pseudocode**:
```python
class PartitionMiner:
    def __init__(self, v27_hashrate_pct, v22_hashrate_pct):
        self.v27_nodes = [nodes 0-9]
        self.v22_nodes = [nodes 10-19]
        self.v27_prob = v27_hashrate_pct / 100.0

    async def run(self):
        while duration_remaining:
            # Weighted random selection
            if random() < self.v27_prob:
                mine_block_on_partition(self.v27_nodes)
            else:
                mine_block_on_partition(self.v22_nodes)

            await asyncio.sleep(interval)

    def mine_block_on_partition(self, nodes):
        # Pick random node from partition
        miner = random.choice(nodes)
        miner.rpc("generatetoaddress", 1, address)
```

**Implementation Notes**:
- Each partition has pool nodes with hashrate_percent metadata
- Within partition, use pool hashrate for node selection
- Across partitions, use v27_hashrate vs v22_hashrate for partition selection

### 2. Dual-Partition Monitoring Script

**File**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/tools/monitor_dual_partition.sh`

**Purpose**: Track fork development in real-time

**Output Format** (CSV):
```
timestamp,v27_height,v22_height,fork_depth
2025-12-30T10:00:00,102,102,2
2025-12-30T10:00:30,104,103,5
2025-12-30T10:01:00,106,105,9
...
```

**Fork Depth Calculation**:
```
fork_depth = v27_height + v22_height - 202
```
(202 = 2 × 101 common history height)

**Pseudocode**:
```bash
#!/bin/bash
NETWORK=$1
INTERVAL=${2:-30}
DURATION=${3:-1800}

start_time=$(date +%s)
echo "timestamp,v27_height,v22_height,fork_depth"

while true; do
    v27_height=$(warnet bitcoin rpc node-0000 getblockcount)
    v22_height=$(warnet bitcoin rpc node-0010 getblockcount)
    fork_depth=$((v27_height + v22_height - 202))

    timestamp=$(date -Iseconds)
    echo "$timestamp,$v27_height,$v22_height,$fork_depth"

    elapsed=$(($(date +%s) - start_time))
    [[ $elapsed -ge $DURATION ]] && break

    sleep $INTERVAL
done
```

### 3. Test Automation Script

**File**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/tools/run_partition_test.sh`

**Purpose**: Execute complete test from generation to results

**Usage**:
```bash
./run_partition_test.sh 3.5 30 70
# Args: test_id, v27_economic%, v27_hashrate%
```

**Workflow**:
1. Generate network config
2. Deploy network
3. Create common history (101 blocks)
4. Enforce partition
5. Run partition miner (30 minutes)
6. Monitor fork depth
7. Run economic analysis
8. Save results
9. Cleanup

**Pseudocode**:
```bash
#!/bin/bash
TEST_ID=$1
V27_ECON=$2
V27_HASH=$3

# Generate network
python3 partition_network_generator.py \
    --test-id $TEST_ID \
    --v27-economic $V27_ECON \
    --v27-hashrate $V27_HASH

# Deploy
cd ../../test-networks/test-$TEST_ID-economic-$V27_ECON-hashrate-$V27_HASH
warnet deploy network.yaml
sleep 60

# Common history
for i in {1..101}; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 $ADDRESS
    sleep 0.5
done
sleep 30

# Enforce partition (network policy or manual disconnection)
kubectl apply -f ../partition-network-policy.yaml

# Mine and monitor (parallel)
warnet run partition_miner.py --v27-hashrate $V27_HASH --duration 1800 &
MINER_PID=$!

monitor_dual_partition.sh --network test-$TEST_ID --duration 1800 > results/test-$TEST_ID-timeline.csv &
MONITOR_PID=$!

wait $MINER_PID $MONITOR_PID

# Analyze
cd ../../monitoring
python3 auto_economic_analysis.py \
    --network-config ../test-networks/test-$TEST_ID.../network.yaml \
    --output-json ../results/test-$TEST_ID-analysis.json

# Cleanup
warnet down
```

### 4. Results Aggregation Script

**File**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/tools/aggregate_results.py`

**Purpose**: Analyze all 15 tests and identify thresholds

**Output**:
- Results matrix (CSV/JSON)
- Threshold identification
- Visualization-ready data

**Key Metrics Per Test**:
- Final fork depth
- Economic majority chain
- Hashrate majority chain
- Convergence time (if applicable)
- Economic risk score

**Pseudocode**:
```python
def aggregate_results():
    results = []

    for test_id in ["5.3", "3.5", "4.4", ...]:
        data = load_json(f"results/test-{test_id}-analysis.json")
        timeline = load_csv(f"results/test-{test_id}-timeline.csv")

        results.append({
            'test_id': test_id,
            'final_fork_depth': timeline[-1]['fork_depth'],
            'economic_majority_chain': data['economic_majority'],
            'hashrate_majority_chain': data['hashrate_majority'],
            'converged': check_convergence(timeline),
            'risk_score': data['risk_score']
        })

    # Identify thresholds
    threshold = identify_economic_threshold(results)

    # Export
    export_matrix(results, "results/test_matrix.csv")
    export_thresholds(threshold, "results/thresholds.json")
```

---

## Network Configuration Details

### Partition Structure

**Total Nodes**: 20 per test
- **v27 partition**: Nodes 0-9 (version 27.0)
- **v22 partition**: Nodes 10-19 (version 22.0)

**Node Allocation Within Partition**:
- Economic nodes: ~3 (power-law distributed weight)
- Pool nodes: Variable (based on hashrate assignment)
- Network nodes: Remaining (propagation only)

### Economic Weight Distribution

**Total Network**:
- Total custody: 4,000,000 BTC
- Total volume: 420,000 BTC/day

**Test 5.3 Example** (70% v27, 30% v22):
- v27 partition: 2,800,000 BTC custody, 294,000 BTC/day volume
- v22 partition: 1,200,000 BTC custody, 126,000 BTC/day volume

**Power-Law Distribution** (within partition):
- Node 0: Gets largest share (harmonic weight: 1.0)
- Node 1: Second largest (harmonic weight: 0.5)
- Node 2: Third (harmonic weight: 0.33)
- Etc.

### Pool Distribution

**Real-World Hashrate**:
```python
POOL_DISTRIBUTION = [
    ("Foundry USA", 26.89),
    ("AntPool", 19.25),
    ("ViaBTC", 11.39),
    ("F2Pool", 11.25),
    ("Binance Pool", 10.04),
    ("MARA Pool", 8.25),
    ("SBI Crypto", 4.57),
    ("Luxor", 3.94),
    ("OCEAN", 1.42),
    ("Braiins Pool", 1.37),
]
```

**Test 5.3 Pool Assignment**:
- v27 partition (target 30%): Foundry USA (26.89%), OCEAN (1.42%), Braiins (1.37%) = 31.46%
- v22 partition (target 70%): Remaining 7 pools = 66.91%

**Greedy Assignment Algorithm**:
```python
for pool in POOL_DISTRIBUTION:
    if adding to v27 gets closer to target:
        assign to v27
    else:
        assign to v22
```

### Topology Rules

**Within Each Partition**:
1. Economic nodes: Full mesh (all connected to all)
2. Pool nodes: Connected to all economic nodes in partition
3. Pool nodes: Chain connection (each to next pool)
4. Network nodes: Ring topology
5. Network nodes: Every 2nd connects to an economic node

**Cross-Partition**:
- **ZERO edges** between v27 and v22 nodes
- Complete network isolation
- This is the critical feature enabling version-based fork testing

### Consensus Weight Formula

```
consensus_weight = (0.7 × custody_btc + 0.3 × daily_volume_btc) / 10000
```

**Example** (major exchange in Test 5.3 v27 partition):
- custody_btc: 1,533,333
- daily_volume_btc: 161,333
- consensus_weight = (0.7 × 1,533,333 + 0.3 × 161,333) / 10000 = 112.13

---

## Fork Mechanics

### Common History Phase

**Blocks 0-101**:
- Generated on single node before partition enforcement
- Propagates to all 20 nodes
- Both partitions share identical blockchain state
- Establishes common ancestor for fork depth calculation

### Fork Trigger

**At Block 102**:
- Network partition enforced (v27 isolated from v22)
- Both partitions begin independent mining
- No consensus mechanism to reconcile chains
- Fork is immediate and persistent

### Fork Depth Evolution

**Definition**:
```
fork_depth = v27_height + v22_height - 202
```

**Timeline Example** (Test 5.3):
```
Time    v27   v22   Depth   Notes
0:00    101   101     0     Common history
0:30    102   102     2     Fork initiated
1:00    104   103     5     v27 mining faster (30% hashrate)
5:00    115   125    38     v22 pulling ahead (70% hashrate)
10:00   127   152    77     Significant divergence
30:00   165   255   218     Deep sustained fork
```

**Key Insight**: Fork depth grows continuously since partitions are isolated

### Expected Outcomes by Test Type

**Test 5.3** (Economic v27 70%, Hashrate v27 30%):
- v27 chain: Economic majority, hashrate minority
- v22 chain: Economic minority, hashrate majority
- **Expected**: v22 chain longer (more hashrate)
- **Question**: Does economic weight matter when chains can't communicate?

**Test 3.5** (Economic v27 30%, Hashrate v27 70%):
- v27 chain: Economic minority, hashrate majority
- v22 chain: Economic majority, hashrate minority
- **Expected**: v27 chain longer (more hashrate)
- **Question**: Inverse of 5.3 - confirms hashrate dominance?

**Test 4.4** (Economic v27 50%, Hashrate v27 50%):
- v27 chain: Economic parity, hashrate parity
- v22 chain: Economic parity, hashrate parity
- **Expected**: Similar chain lengths (random walk)
- **Question**: Baseline control test

---

## Data Collection and Analysis

### Timeline Data

**File**: `results/test-X.Y-timeline.csv`

**Format**:
```csv
timestamp,v27_height,v22_height,fork_depth
2025-12-30T10:00:00,101,101,0
2025-12-30T10:00:30,102,102,2
2025-12-30T10:01:00,104,103,5
...
```

**Visualizations**:
- Line plot: Heights over time (v27 vs v22)
- Line plot: Fork depth over time
- Slope comparison: Mining rate per partition

### Economic Analysis Data

**File**: `results/test-X.Y-analysis.json`

**Key Fields**:
```json
{
  "test_id": "5.3",
  "timestamp": "2025-12-30T10:30:00",
  "fork_depth": 218,
  "chains": {
    "v27": {
      "height": 165,
      "economic_weight": 2800000,
      "economic_pct": 70.0,
      "hashrate_pct": 30.0,
      "consensus_weight": 112.13
    },
    "v22": {
      "height": 255,
      "economic_weight": 1200000,
      "economic_pct": 30.0,
      "hashrate_pct": 70.0,
      "consensus_weight": 48.05
    }
  },
  "economic_majority": "v27",
  "hashrate_majority": "v22",
  "length_majority": "v22",
  "risk_score": 75.3,
  "analysis": "Economic weight concentrated on shorter chain"
}
```

### Aggregated Matrix

**File**: `results/test_matrix.csv`

**Format**:
```csv
test_id,v27_econ%,v27_hash%,v22_econ%,v22_hash%,final_depth,econ_majority,hash_majority,length_winner,risk_score
5.3,70,30,30,70,218,v27,v22,v22,75.3
3.5,30,70,70,30,245,v22,v27,v27,68.7
4.4,50,50,50,50,198,tie,tie,v27,45.2
...
```

**Analysis Goals**:
1. **Identify thresholds**: At what % does economic weight overcome hashrate deficit?
2. **Quantify risk**: How much economic exposure in worst-case scenarios?
3. **Validate assumptions**: Does 51% hashrate always win in isolated networks?

---

## Quick Reference Commands

### Generate All Week 2 Tests

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen

# Test 5.3 (already done)
python3 partition_network_generator.py --test-id 5.3 --v27-economic 70 --v27-hashrate 30

# Test 3.5
python3 partition_network_generator.py --test-id 3.5 --v27-economic 30 --v27-hashrate 70

# Test 4.4
python3 partition_network_generator.py --test-id 4.4 --v27-economic 50 --v27-hashrate 50
```

### Run Single Test (Manual)

```bash
# 1. Deploy
cd ~/bitcoinTools/warnet/test-networks/test-5.3-economic-70-hashrate-30
warnet deploy network.yaml

# 2. Common history
for i in {1..101}; do warnet bitcoin rpc node-0000 generatetoaddress 1 bcrt1q...; sleep 0.5; done

# 3. Enforce partition
kubectl apply -f ../partition-network-policy.yaml

# 4. Mine (once scenario is created)
warnet run partition_miner.py --v27-hashrate 30 --duration 1800

# 5. Analyze
cd ../../monitoring
python3 auto_economic_analysis.py --network-config ../test-networks/test-5.3.../network.yaml
```

### Monitor Live

```bash
# Watch fork depth development
watch -n 30 'echo "v27: $(warnet bitcoin rpc node-0000 getblockcount) | v22: $(warnet bitcoin rpc node-0010 getblockcount)"'
```

### Check Results

```bash
# View timeline
cat ~/bitcoinTools/warnet/warnetScenarioDiscovery/results/test-5.3-timeline.csv | tail -20

# View analysis
cat ~/bitcoinTools/warnet/warnetScenarioDiscovery/results/test-5.3-analysis.json | jq
```

---

## File Structure Overview

```
warnetScenarioDiscovery/
├── networkGen/
│   ├── partition_network_generator.py          ✅ Complete
│   ├── configurable_network_generator.py       ✅ Complete (legacy)
│   ├── scenarios/                              ✅ Complete (legacy)
│   ├── README.md                               ✅ Complete
│   ├── CONFIGURABLE_NETWORK_GENERATOR.md       ✅ Complete
│   └── PARTITION_NETWORK_TESTING_HANDOFF.md    ✅ This document
│
├── monitoring/
│   ├── auto_economic_analysis.py               ✅ Complete (with fork depth)
│   └── economic_fork_analyzer.py               ✅ Complete
│
├── tools/                                       ⏳ TO CREATE
│   ├── monitor_dual_partition.sh               ⏳ Needed
│   ├── run_partition_test.sh                   ⏳ Needed
│   ├── aggregate_results.py                    ⏳ Needed
│   └── disconnect_partitions.sh                ⏳ Optional (if network policy not used)
│
├── results/                                     📊 Will be created during tests
│   ├── test-5.3-timeline.csv
│   ├── test-5.3-analysis.json
│   ├── test-3.5-timeline.csv
│   ├── test-3.5-analysis.json
│   └── test_matrix.csv
│
└── test-networks/                               ✅ Test configs generated here
    ├── test-5.3-economic-70-hashrate-30/
    │   └── network.yaml                        ✅ Complete
    ├── test-3.5-economic-30-hashrate-70/       ⏳ To generate
    └── test-4.4-economic-50-hashrate-50/       ⏳ To generate

warnet/scenarios/
├── economic_miner.py                           ✅ Complete (reads metadata)
└── partition_miner.py                          ⏳ TO CREATE (critical for testing)
```

---

## Troubleshooting Guide

### Issue: Nodes not connecting after deployment

**Symptom**: `warnet status` shows 0 peers

**Check**:
```bash
kubectl get pods
kubectl logs <pod-name>
```

**Fix**: Wait 60-90 seconds for network initialization

---

### Issue: Fork not occurring

**Symptom**: Both partitions stay at same height

**Check**:
```bash
# Verify network partition is enforced
warnet bitcoin rpc node-0000 getpeerinfo | grep "10.0.0.10"  # Should be empty
```

**Fix**: Ensure network policy applied or manual disconnection completed

---

### Issue: Pool distribution doesn't match target

**Symptom**: Generator shows hashrate far from target (>5% error)

**Cause**: Greedy algorithm limitation with discrete pool sizes

**Solution**: This is expected. Algorithmic limit due to real pool sizes. Document actual percentages.

---

### Issue: Economic analysis fails

**Symptom**: `auto_economic_analysis.py` crashes or shows errors

**Check**:
```bash
# Verify network config has metadata
cat network.yaml | grep custody_btc
```

**Fix**: Ensure network generated by partition_network_generator.py (not legacy tools)

---

### Issue: Common history not propagating

**Symptom**: Some nodes stuck at height 0 after generating 101 blocks

**Check**:
```bash
# Check individual node heights
for i in {0..19}; do echo "node-$(printf '%04d' $i): $(warnet bitcoin rpc node-$(printf '%04d' $i) getblockcount)"; done
```

**Fix**: Increase wait time after block generation (60-90 seconds)

---

## Critical Implementation: Partition Miner

### Detailed Specification

**File**: `~/bitcoinTools/warnet/warnet/scenarios/partition_miner.py`

**Core Logic**:
```python
class PartitionMiner(Scenario):
    def __init__(self):
        super().__init__()

        # Read network config to identify partitions
        self.v27_nodes = []
        self.v22_nodes = []
        self.v27_pools = []  # {node: hashrate_pct}
        self.v22_pools = {}  # {node: hashrate_pct}

        # Parse command line args
        self.v27_hashrate_total = args.v27_hashrate
        self.v22_hashrate_total = args.v22_hashrate
        self.interval = args.interval
        self.duration = args.duration

    def partition_nodes_by_version(self):
        """Separate nodes into v27 and v22 partitions"""
        for node in self.nodes:
            version = node.version  # Read from node metadata
            if version.startswith("27"):
                self.v27_nodes.append(node)
                if hasattr(node, 'metadata') and 'hashrate_percent' in node.metadata:
                    self.v27_pools[node] = node.metadata['hashrate_percent']
            elif version.startswith("22"):
                self.v22_nodes.append(node)
                if hasattr(node, 'metadata') and 'hashrate_percent' in node.metadata:
                    self.v22_pools[node] = node.metadata['hashrate_percent']

    def select_miner_in_partition(self, pools_dict):
        """Select miner within partition based on pool hashrate"""
        if not pools_dict:
            # No pool metadata, random selection
            return random.choice(list of all nodes in partition)

        # Weighted random selection
        total_hashrate = sum(pools_dict.values())
        rand = random.uniform(0, total_hashrate)
        cumulative = 0

        for node, hashrate in pools_dict.items():
            cumulative += hashrate
            if rand <= cumulative:
                return node

        return list(pools_dict.keys())[0]  # Fallback

    async def run(self):
        self.partition_nodes_by_version()

        start_time = time.time()
        blocks_mined = {'v27': 0, 'v22': 0}

        while time.time() - start_time < self.duration:
            # Decide which partition mines this block
            if random.random() < (self.v27_hashrate_total / 100.0):
                # v27 partition mines
                miner = self.select_miner_in_partition(self.v27_pools)
                partition = 'v27'
            else:
                # v22 partition mines
                miner = self.select_miner_in_partition(self.v22_pools)
                partition = 'v22'

            # Mine block
            address = await miner.rpc("getnewaddress")
            await miner.rpc("generatetoaddress", 1, address)

            blocks_mined[partition] += 1

            self.log.info(f"Block mined on {partition} partition (total: v27={blocks_mined['v27']}, v22={blocks_mined['v22']})")

            await asyncio.sleep(self.interval)

        self.log.info(f"Mining complete. v27: {blocks_mined['v27']} blocks, v22: {blocks_mined['v22']} blocks")
```

**Arguments**:
```python
parser.add_argument('--v27-hashrate', type=float, required=True, help='v27 partition hashrate %')
parser.add_argument('--v22-hashrate', type=float, required=True, help='v22 partition hashrate %')
parser.add_argument('--interval', type=int, default=10, help='Seconds between blocks')
parser.add_argument('--duration', type=int, default=1800, help='Total test duration in seconds')
```

---

## Next Steps Priority Order

### Immediate (Proof of Concept)

1. **Create partition_miner.py** (~15 min)
   - Enables Test 5.3 execution
   - Core functionality for all 15 tests

2. **Create monitor_dual_partition.sh** (~5 min)
   - Real-time visibility
   - Data collection for analysis

3. **Generate Test 3.5 and 4.4 configs** (~2 min)
   - Complete Week 2 test suite
   - Ready for deployment

4. **Run Test 5.3 end-to-end** (~45 min)
   - Validate workflow
   - Identify issues
   - Document lessons learned

### Short-term (Week 2)

5. **Create run_partition_test.sh** (~20 min)
   - Automates manual workflow
   - Reduces human error

6. **Run all 3 Week 2 tests** (~2-3 hours)
   - Test 5.3, 3.5, 4.4
   - Validate infrastructure
   - Initial results analysis

7. **Create aggregate_results.py** (~30 min)
   - Structured results format
   - Enables comparison

### Medium-term (Weeks 3-4)

8. **Generate all 15 test configs** (~10 min)
   - Batch generation script
   - Verify all configs valid

9. **Run complete test suite** (~8-10 hours)
   - Sequential execution
   - Overnight job candidate

10. **Analyze results and identify thresholds** (~2-4 hours)
    - Statistical analysis
    - Threshold identification
    - Visualization

### Documentation

11. **Document findings** (~4-6 hours)
    - Results interpretation
    - Methodology description
    - Publication-ready format

---

## Expected Timeline

**Week 2 (Current)**: Foundation
- Day 1-2: Implement partition_miner.py and monitoring
- Day 3-4: Run 3 baseline tests
- Day 5: Analyze results, iterate on tooling

**Week 3**: Thresholds
- Day 1: Generate 6 threshold test configs
- Day 2-4: Run threshold tests
- Day 5: Analyze for threshold patterns

**Week 4**: Alignment
- Day 1: Generate 6 alignment test configs
- Day 2-4: Run alignment tests
- Day 5: Comprehensive analysis

**Week 5**: Publication
- Aggregate all results
- Statistical analysis
- Paper draft

---

## Research Questions Being Answered

### Primary Question
**"What is the resilience threshold of the Bitcoin network when economic weight and hashrate are misaligned?"**

### Specific Hypotheses

**H1**: Economic weight has minimal impact in isolated partitions
- Test: Compare 5.3 vs 3.5 (inverted economic/hashrate)
- Expected: Hashrate majority chain always longest

**H2**: There exists a critical hashrate threshold (~51%)
- Test: Threshold tests (6.2, 6.4, 6.6, etc.)
- Expected: Clear threshold where majority hashrate dominates

**H3**: Alignment amplifies chain strength
- Test: Alignment tests (2.2, 3.3, 5.5)
- Expected: Aligned tests show faster divergence

**H4**: Economic weight matters in reconnection scenarios
- Test: (Future) Run tests, then reconnect partitions
- Expected: Economic majority chain wins after reconnection

### Metrics for Success

- ✅ 15 tests completed successfully
- ✅ Clear hashrate threshold identified (± 5%)
- ✅ Economic weight impact quantified
- ✅ Publication-ready dataset
- ✅ Reproducible methodology documented

---

## Validation Checklist

### Before Running Each Test

- [ ] Network config generated successfully
- [ ] Pool distribution within 5% of target
- [ ] Economic weight within 2% of target
- [ ] 0 cross-partition edges verified
- [ ] Deployment successful (all pods running)
- [ ] Common history created (all nodes at height 101)
- [ ] Network partition enforced

### During Test

- [ ] Monitoring script capturing data
- [ ] Fork depth increasing
- [ ] Block production on both partitions
- [ ] No errors in logs

### After Test

- [ ] Timeline CSV complete
- [ ] Economic analysis JSON complete
- [ ] Fork depth >= 100 (sufficient divergence)
- [ ] Results documented
- [ ] Network torn down cleanly

---

## Conclusion

You now have:

✅ **Partition network generator** - Creates version-segregated test networks
✅ **Test 5.3 configuration** - First of 15 tests ready
✅ **Economic analysis framework** - Fork depth and risk scoring
✅ **Complete documentation** - Workflow, specifications, troubleshooting

**What's needed to run Test 5.3**:

⏳ `partition_miner.py` - Core mining scenario (~15 min implementation)
⏳ `monitor_dual_partition.sh` - Data collection (~5 min implementation)
⏳ Network partition enforcement - Kubernetes policy or manual disconnection

**Once these are complete**: Full systematic testing of Bitcoin network resilience thresholds is possible.

---

**Document Version**: 1.0
**Last Updated**: 2025-12-30
**Status**: Ready for implementation phase
**Next Session**: Implement partition_miner.py and run Test 5.3
