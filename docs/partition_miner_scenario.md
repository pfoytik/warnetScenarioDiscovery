# Partition Miner with Pools Scenario

## Overview

`partition_miner_with_pools.py` is a comprehensive Bitcoin fork simulation scenario that models the dynamics of a network partition with competing chains (v27 and v26). It integrates multiple oracles and strategies to simulate realistic fork behavior:

- **Price Oracle**: Dynamic price discovery based on economic support and hashrate
- **Fee Oracle**: Fee market dynamics based on block throughput and congestion
- **Mining Pool Strategy**: Pools make fork decisions based on profitability and ideology
- **Economic Node Strategy**: Economic/user nodes choose which fork's economy to support
- **Difficulty Oracle**: Simulates difficulty adjustments and chainwork accumulation
- **Reorg Oracle**: Tracks reorganization events and orphaned blocks

## Key Concepts

### Fork Types

1. **Hard Fork**: Incompatible rule changes - both sides reject each other's blocks
   - v27 nodes: `accepts_foreign_blocks: false`
   - v26 nodes: `accepts_foreign_blocks: false`
   - Chains can never naturally reunify
   - Example: Bitcoin vs Bitcoin Cash split

2. **Contentious Soft Fork (UASF + URSF)**: Soft fork with active resistance
   - v27 nodes: `accepts_foreign_blocks: false` (UASF - enforce new stricter rules)
   - v26 nodes: `accepts_foreign_blocks: false` (URSF - actively reject new rules)
   - Functionally similar to a hard fork while URSF is active
   - If URSF nodes give up, they can accept v27 blocks (soft fork resolution)

3. **Non-Contentious Soft Fork (UASF only)**: New stricter rules, no active resistance
   - v27 nodes: `accepts_foreign_blocks: false` (enforce stricter rules)
   - v26 nodes: `accepts_foreign_blocks: true` (permissive - accept v27 blocks)
   - v27 blocks are valid under v26 rules (stricter is subset of looser)
   - Asymmetric propagation: v27 blocks flow to v26, but not vice versa
   - Example: SegWit activation

### Fork Type Summary

| Fork Type | v27 accepts v26 | v26 accepts v27 | Can Reunify Naturally |
|-----------|-----------------|-----------------|----------------------|
| Hard Fork | No | No | Never |
| Contentious Soft Fork (UASF+URSF) | No | No | Only if URSF stops |
| Non-Contentious Soft Fork (UASF) | No | Yes | Yes (v27 chain wins if longer) |

### Configuring Fork Type in network.yaml

Set `accepts_foreign_blocks` in each node's metadata:

```yaml
# Hard Fork - both partitions isolated
nodes:
  - name: node-v27
    image: { tag: '27.0' }
    metadata:
      accepts_foreign_blocks: false  # Rejects v26 blocks
  - name: node-v26
    image: { tag: '26.0' }
    metadata:
      accepts_foreign_blocks: false  # Rejects v27 blocks

# Non-Contentious Soft Fork - v26 accepts v27
nodes:
  - name: node-v27
    image: { tag: '27.0' }
    metadata:
      accepts_foreign_blocks: false  # Enforces strict rules
  - name: node-v26
    image: { tag: '26.0' }
    metadata:
      accepts_foreign_blocks: true   # Accepts v27 blocks (permissive)
```

### Dynamic Behavior

- **Hashrate allocation** changes as pools switch forks based on profitability
- **Economic weight** changes as users/exchanges choose which fork to support
- **Prices** respond to economic support and hashrate distribution
- **Difficulty** adjusts based on block production rate

---

## Command-Line Flags

### Required Flags

| Flag | Type | Description |
|------|------|-------------|
| `--network` | string | Path to network.yaml file (warnet standard flag) |

### Core Simulation Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--duration` | int | 7200 | Total simulation duration in seconds |
| `--interval` | int | 10 | Target block interval in seconds |
| `--start-height` | int | 101 | Starting block height for the fork |

### Economic Configuration

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--v27-economic` | float | 70.0 | Initial economic weight on v27 (0-100%) |
| `--v26-economic` | float | auto | Initial economic weight on v26 (defaults to 100 - v27) |
| `--economic-scenario` | string | "realistic_current" | Economic node scenario from `economic_nodes_config.yaml` |
| `--economic-update-interval` | int | 300 | How often economic nodes re-evaluate (seconds) |

### Pool Configuration

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--pool-scenario` | string | "realistic_current" | Pool scenario from `mining_pools_config.yaml` |
| `--initial-v27-hashrate` | float | None | Override initial v27 hashrate (if not using pools) |
| `--hashrate-update-interval` | int | 600 | How often pools re-evaluate fork choice (seconds) |

### Difficulty Oracle

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--enable-difficulty` | flag | False | Enable difficulty simulation with probability-per-tick mining |
| `--retarget-interval` | int | 144 | Blocks between difficulty adjustments |
| `--tick-interval` | float | 1.0 | Tick interval for mining probability calculation |
| `--enable-eda` | flag | False | Enable Emergency Difficulty Adjustment (BCH-style) |
| `--min-difficulty` | float | 0.0625 | Minimum difficulty floor (1/16) |

### Reorg and Partition Tracking

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--enable-reorg-metrics` | flag | False | Enable reorg tracking oracle |
| `--enable-dynamic-switching` | flag | False | Allow nodes to switch partitions at P2P level |

### Fork Reunion

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--enable-reunion` | flag | False | Reconnect partitions at end and let heavier chain win |
| `--reunion-timeout` | int | 120 | Seconds to wait for reorg convergence |

### Time-Limited UASF

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--uasf-duration` | int | None | UASF duration in seconds; after expiry, v27 accepts v26 blocks |
| `--uasf-expiry-action` | string | "reunion" | Action on UASF expiry: `reunion`, `accept`, or `continue` |

**UASF Expiry Actions:**
- `reunion`: Reconnect partitions, v27 nodes reorg to heavier chain
- `accept`: v27 nodes accept v26 blocks but partitions stay separate
- `continue`: Just log expiry, no behavior change

### Results and Debugging

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--results-id` | string | auto | Unique identifier for this run |
| `--snapshot-interval` | int | 60 | Interval for time series snapshots (seconds) |
| `--price-update-interval` | int | 60 | How often to update prices (seconds) |
| `--debug-prices` | flag | False | Enable verbose price calculation logging |
| `--network-yaml` | string | None | Explicit path to network.yaml (alternative to --network) |

---

## Available Scenarios

### Pool Scenarios (mining_pools_config.yaml)

| Scenario | Description |
|----------|-------------|
| `realistic_current` | Based on actual Bitcoin mining pool distribution |
| `ideological_war` | Strong ideological split with real pool names |
| `purely_rational` | All pools purely profit-driven (baseline) |
| `weak_resistance` | Large rational majority, small ideological minority |
| `close_battle` | Evenly matched factions, outcome uncertain |
| `asymmetric_softfork` | Non-contentious soft fork with v27 minority |
| `asymmetric_balanced` | Balanced battle with moderate ideology |
| `asymmetric_extreme` | Extreme divergence scenario |
| `v26_dominant` | v26 hashrate dominance |
| `v26_dominant_committed` | v26 dominance with committed v27 holdout (Foundry 1000% ideology) |

### Economic Scenarios (economic_nodes_config.yaml)

| Scenario | Description |
|----------|-------------|
| `realistic_current` | Exchanges mostly rational, users more ideological |
| `ideological_split` | Strong ideological division among all participants |
| `purely_rational` | All economic actors purely rational |
| `strong_v26_resistance` | Significant economic resistance to v27 upgrade |
| `asymmetric_balanced` | Balanced economic split with moderate ideology |
| `asymmetric_extreme` | Extreme v27 economic support |
| `asymmetric_softfork` | Non-contentious soft fork economic distribution |

---

## Examples

### Basic Test (30 minutes, default settings)

```bash
warnet run scenarios/partition_miner_with_pools.py \
    --network networks/12node/network.yaml \
    --duration 1800 \
    --results-id basic_test
```

### Realistic Fork Simulation with Difficulty

```bash
warnet run scenarios/partition_miner_with_pools.py \
    --network networks/asymmetric_softfork_test/network.yaml \
    --pool-scenario asymmetric_softfork \
    --economic-scenario asymmetric_softfork \
    --v27-economic 55 \
    --enable-difficulty \
    --retarget-interval 2016 \
    --interval 10 \
    --duration 7200 \
    --results-id realistic_fork_2hr
```

### Ideological War with Reorg Tracking

```bash
warnet run scenarios/partition_miner_with_pools.py \
    --network networks/ideological-war/network.yaml \
    --pool-scenario ideological_war \
    --economic-scenario ideological_split \
    --enable-difficulty \
    --enable-reorg-metrics \
    --hashrate-update-interval 300 \
    --duration 14400 \
    --results-id idwar_4hr
```

### Time-Limited UASF Test

```bash
warnet run scenarios/partition_miner_with_pools.py \
    --network networks/v26-dominant/network.yaml \
    --pool-scenario v26_dominant_committed \
    --economic-scenario strong_v26_resistance \
    --enable-difficulty \
    --retarget-interval 2016 \
    --interval 1 \
    --duration 3600 \
    --uasf-duration 1800 \
    --uasf-expiry-action reunion \
    --reunion-timeout 300 \
    --results-id uasf_30min_expiry
```

### Fork Reunion Test

```bash
warnet run scenarios/partition_miner_with_pools.py \
    --network networks/v26-dominant/network.yaml \
    --pool-scenario v26_dominant_committed \
    --economic-scenario strong_v26_resistance \
    --enable-difficulty \
    --enable-reunion \
    --reunion-timeout 300 \
    --duration 7200 \
    --results-id reunion_test
```

### Close Battle with Dynamic Switching

```bash
warnet run scenarios/partition_miner_with_pools.py \
    --network networks/close-battle/network.yaml \
    --pool-scenario close_battle \
    --economic-scenario ideological_split \
    --enable-difficulty \
    --enable-reorg-metrics \
    --enable-dynamic-switching \
    --hashrate-update-interval 180 \
    --economic-update-interval 300 \
    --duration 14400 \
    --results-id close_battle_4hr
```

---

## Output Files

Results are exported to `/tmp/` and can be extracted using the results extraction tool:

| File | Description |
|------|-------------|
| `partition_results.json` | Consolidated results with all data |
| `partition_pools.json` | Pool strategy decisions and history |
| `partition_economic.json` | Economic node decisions |
| `partition_prices.json` | Price oracle history |
| `partition_fees.json` | Fee oracle history |
| `partition_difficulty.json` | Difficulty adjustments and chainwork |
| `partition_reorg.json` | Reorg events and metrics |

### Extracting Results

```bash
# Extract results to local directory
python tools/extract_results.py <results_id> --output-dir tools/results/<results_id>
```

---

## Key Metrics

### Final State
- Blocks mined per fork
- Final hashrate distribution
- Final economic weight distribution
- Final prices

### Difficulty/Chainwork
- Winning fork (by chainwork)
- Difficulty per fork
- Total chainwork accumulated

### Reorg Metrics
- Total reorg events
- Total reorg mass (blocks invalidated)
- Orphan rate
- Consensus stress score

### UASF Metrics (if enabled)
- UASF outcome (succeeded/failed)
- State at expiry
- Orphaned blocks (if failed)
- Wasted chainwork

### Reunion Metrics (if enabled)
- Winning fork
- Losing fork depth
- Nodes converged
- Convergence time

---

## Network Requirements

The scenario expects a network with:

1. **Two partitions**: v27 nodes and v26 nodes (identified by Bitcoin Core version)
2. **Node metadata** in network.yaml with:
   - `fork_preference`: v27, v26, or neutral
   - `ideology_strength`: 0.0 to 1.0
   - `accepts_foreign_blocks`: true/false (for asymmetric forks)
   - Pool nodes: `entity_id` matching pool config (e.g., `pool-foundryusa`)
   - Economic nodes: `node_type`, `custody_btc`, `daily_volume_btc`

See `networks/` directory for example network configurations.
