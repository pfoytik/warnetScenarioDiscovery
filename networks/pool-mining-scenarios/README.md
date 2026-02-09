# Pool Mining Scenarios

This directory contains network configurations for realistic pool-based mining scenarios.

## Three-Tier Network Architecture

### Tier 1: Economic Nodes (nodes 0-4)
- **Purpose**: Represent major economic actors (exchanges, payment processors)
- **Characteristics**:
  - High connection limits (125 connections)
  - Large mempools (500 MB)
  - Economic metadata (custody, volume, consensus weight)
  - Fully meshed with each other
- **Split**: 40% v26.0 (custody-heavy), 60% v27.0 (volume-heavy)

### Tier 2: Pool Nodes (nodes 5-14)
- **Purpose**: Mining pool infrastructure nodes
- **Characteristics**:
  - Medium connection limits (50 connections)
  - Standard mempools (200 MB)
  - Pool metadata (name, hashrate percentage)
  - Connected to 2-4 economic nodes each
  - Peered with adjacent pools

**Pool Distribution** (based on real Bitcoin network data):
| Node | Pool Name | Hashrate % |
|------|-----------|------------|
| 5 | Foundry USA | 26.89% |
| 6 | AntPool | 19.25% |
| 7 | ViaBTC | 11.39% |
| 8 | F2Pool | 11.25% |
| 9 | SpiderPool | 9.09% |
| 10 | MARA Pool | 5.00% |
| 11 | SECPOOL | 4.18% |
| 12 | Luxor | 3.21% |
| 13 | Binance Pool | 2.49% |
| 14 | OCEAN | 1.42% |

### Tier 3: Network Nodes (nodes 15-24)
- **Purpose**: Regular network participants (hobbyists, small services)
- **Characteristics**:
  - Lower connection limits (30 connections)
  - Small mempools (100 MB)
  - No economic metadata
  - Form ring topology with some connections to economic nodes
- **Role**: Block propagation and network decentralization

## Network Topology

**Total Nodes**: 25
**Total Connections**: 74

**Connection Strategy**:
- Economic layer: Fully meshed (all pairs connected)
- Pool layer: Each pool connects to 2-4 economic nodes + neighboring pools
- Network layer: Ring topology + strategic economic node connections

## Usage

### Deploying the Network

```bash
cd /home/pfoytik/bitcoinTools/warnet/test-networks/pool-mining-scenarios
warnet deploy .
```

### Running Realistic Mining

Use the `economic_miner.py` scenario to simulate pool-based mining:

```bash
# Run for 1 hour with 10-second mining intervals
warnet run ~/bitcoinTools/warnet/warnet/scenarios/economic_miner.py \
    --interval 10 \
    --pools 10 \
    --duration 3600 \
    --mature
```

**Parameters**:
- `--interval`: Seconds between mining attempts across all pools (default: 10)
- `--pools`: Number of top pools to simulate (default: 10, max: 10 for this network)
- `--duration`: How long to run in seconds (0 = indefinite)
- `--mature`: Generate 101 mature blocks at startup

### Monitoring Forks and Economic Analysis

Use the `pool_mining_test.sh` script for automated fork detection and economic analysis:

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/tools

# Run 1-hour test with fork monitoring
./pool_mining_test.sh \
    --duration 3600 \
    --interval 10 \
    --pools 10 \
    --network /home/pfoytik/bitcoinTools/warnet/test-networks/pool-mining-scenarios \
    --fork-check 30
```

**Features**:
- Automatic fork detection every 30 seconds
- Economic analysis when forks occur
- Complete logging of mining activity
- Pool statistics at completion

## Scenario: Custody vs Volume Conflict

This network is designed to test:

**Fork Trigger**: Version split (v26.0 vs v27.0) causes chain divergence

**Economic Split**:
- **Chain A** (v26.0): Custody-heavy exchanges (2M BTC custody, low volume)
- **Chain B** (v27.0): Volume-heavy payment processors (100K BTC custody, high volume)

**Pool Behavior**:
- Pools query their connected economic nodes
- Choose which fork to mine based on economic node distribution
- Hashrate follows economic influence through network connections

**Research Questions**:
1. Do pools follow custody or volume signals?
2. How does network topology affect fork persistence?
3. What hashrate distribution leads to consensus?
4. How long do forks persist with realistic mining?

## Regenerating the Network

To regenerate with different random economic values:

```bash
python3 generate_pool_network.py
```

This creates a new `network.yaml` with fresh economic metadata while maintaining the same topology.

## Expected Behavior

**Fork Formation**:
- Economic nodes split between v26 and v27
- Pool nodes must choose which fork to follow
- Network nodes propagate both chains

**Fork Resolution**:
- Pools with higher hashrate dominate
- Economic influence flows through connections
- Network converges to chain with economic majority

**Metrics to Track**:
- Fork frequency and duration
- Economic risk scores
- Pool distribution across forks
- Time to consensus
