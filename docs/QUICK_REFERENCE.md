# Fork Testing - Quick Reference Card

**Last Updated**: 2026-01-26
**Status**: All metrics implemented ✅ (Updated for new repository structure)

---

## 4-Step Test Procedure

### 1️⃣ Generate Network
```bash
cd warnetScenarioDiscovery/networkGen
python3 partition_network_generator.py --test-id TEST-NAME --v27-economic 70 --v27-hashrate 30
```

### 2️⃣ Deploy
```bash
cd ../../
warnet deploy test-networks/test-TEST-NAME-economic-70-hashrate-30/
sleep 90  # Wait for nodes to sync
```

### 3️⃣ Run Mining Scenario
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml /home/pfoytik/bitcoinTools/warnet/test-networks/test-TEST-NAME-economic-70-hashrate-30/network.yaml \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 1800
```

### 4️⃣ Analyze Fork
```bash
cd ../../../warnetScenarioDiscovery/monitoring
python3 enhanced_fork_analysis.py \
    --network-config ../../test-networks/test-TEST-NAME-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query
```

---

## What You Get

```
FORK ANALYSIS OUTPUT:

FORK_0:
  Hashrate: 67.3%        ← Which pools mine this fork
  Custody: 70.0%         ← BTC held by entities
  Volume: 68.5%          ← Daily transaction volume
  Consensus Weight: 70.1%
  Pools: foundry, antpool, f2pool, ...

FORK_1:
  Hashrate: 32.7%
  Custody: 30.0%
  Volume: 31.5%
  Consensus Weight: 29.9%
  Pools: viabtc, luxor, ocean, ...

COMPARISON TABLE:
  Shows winner for each metric
```

---

## Common Test Scenarios

| Scenario | v27-economic | v27-hashrate | Description |
|----------|--------------|--------------|-------------|
| **Aligned** | 70 | 70 | Economic & hashrate favor same fork |
| **Conflict** | 70 | 30 | Economic favors v27, hashrate v26 |
| **Balanced** | 50 | 50 | Even split |
| **Extreme** | 95 | 10 | Overwhelming economic dominance |

---

## Pool Scenarios

| Scenario | Ideology | Behavior |
|----------|----------|----------|
| `realistic_current` | Low (0.1-0.3) | Mostly profit-focused |
| `ideological_fork_war` | High (0.5-0.8) | Willing to mine at loss |
| `pure_profit` | None (0.0) | Switch immediately |

---

## Timeline

| Step | Duration |
|------|----------|
| Generate | 10 seconds |
| Deploy | 90 seconds |
| Sync | 90 seconds |
| Mine (30 min) | 1800 seconds |
| Analyze | 10 seconds |
| **Total** | **~35 minutes** |

---

## Monitoring

### Check Pool Decisions
```bash
cat /tmp/partition_pools.json | jq '.pools | to_entries | .[] | {pool: .key, allocation: .value.current_allocation}'
```

### Watch Price Evolution
```bash
tail -f /tmp/partition_prices.json
```

### Continuous Analysis (every 60s)
```bash
watch -n 60 'cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring && python3 enhanced_fork_analysis.py --network-config ../../test-networks/test-TEST-NAME-economic-70-hashrate-30/ --pool-decisions /tmp/partition_pools.json --live-query'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No fork detected | Wait longer or lower `--fork-depth-threshold 3` |
| Pool decisions not found | Ensure Step 3 running with `--network-yaml` |
| Network exists error | `warnet stop` first |
| Hashrate shows 0% | Add `--pool-decisions /tmp/partition_pools.json` |

---

## Key Files

| File | Purpose |
|------|---------|
| `network.yaml` | Network configuration (pools, users, economic data) |
| `/tmp/partition_pools.json` | Pool decisions and allocations |
| `/tmp/partition_prices.json` | Price evolution history |
| `/tmp/partition_fees.json` | Fee evolution history |

---

## Documentation

- **Complete Workflow**: `COMPLETE_TESTING_WORKFLOW.md`
- **Current Status**: `TESTING_FLOW_AND_GAPS.md`
- **Hashrate Implementation**: `HASHRATE_TRACKING_COMPLETE.md`
- **Paired Nodes**: `PAIRED_NODE_ARCHITECTURE.md`

---

## All Implemented Metrics ✅

1. ✅ **Hashrate per fork** (shows which pools mine which fork)
2. ✅ **Custody per fork** (BTC held by entities)
3. ✅ **Volume per fork** (daily transaction volume)
4. ✅ **Consensus weight** (combines custody + volume)
5. ✅ **Node count per fork**
6. ✅ **Pool attribution** (pool-by-pool breakdown)
7. ✅ **Fork depth** (blocks diverged)
8. ✅ **Pool decisions** (profitability + ideology tracking)
9. ✅ **Price evolution** (fork value over time)
10. ✅ **Fee evolution** (transaction fees)

---

**Status**: Production ready! 🚀
