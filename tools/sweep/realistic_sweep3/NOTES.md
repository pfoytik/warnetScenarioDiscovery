# Sweep 3 Notes

## Configuration
- Base network: `realistic-economy-v2`
- Scenarios: 50 (same LHS sample as sweep1/sweep2, seed=42)
- Block interval: 2s
- Difficulty retarget interval: 2016 blocks (matches real Bitcoin protocol)
- Duration: 8064s (~2.25 hrs per scenario) = 2 full retargets per run
- Estimated total runtime: ~5 days

## Key Improvements Over Sweep 2

### 1. Economic Split Now Active
Sweep2 had the economic split stuck at ~55% v27 / 45% v26 due to discrete custody
granularity in the base network. The `economic_split` parameter should now vary
meaningfully across scenarios.

**What to look for:**
- `economic_split` should appear in the top correlations (was ~0 in sweep2)
- Does economic weight override hashrate dominance at extreme values?
- What is the threshold where economic split starts determining the outcome?

### 2. Proper 2016-Block Difficulty Dynamics
Sweep2 used the default 144-block retarget, meaning difficulty adjusted roughly
every 5 min at 2s intervals — far too reactive. With 2016-block retargets, one
adjustment cycle takes ~67 min, matching Bitcoin's actual design.

**What to look for:**
- More pronounced revenue divergence before difficulty catches up on the losing fork
- Fee counter-pressure sustained longer (slower fork = higher fees per block for ~67 min)
- EDA (Emergency Difficulty Adjustment) events in `partition_difficulty.json` for
  scenarios where one fork loses a large fraction of hashrate suddenly
- Whether the `hashrate_split` threshold shifts from sweep2's ~0.46

### 3. Realistic-Economy-v2 Base Network
Key changes from v1:
- Power user hashrates now meaningful (e.g., node-0048: 0.05% -> 7.8%)
- All nodes have `representation_tier` (1=direct actors, 2=aggregated populations)
- User nodes have `represents_count` (power_user=400 real users, casual_user=1250)
- Binance Pool replaced by SpiderPool
- node-0043 institutional custody: 620K -> 230K BTC

**What to look for:**
- `solo_miner_hashrate` parameter may show higher correlation now that power user
  hashrate is non-trivial
- Represents_count metadata is interpretable for population-scale analysis

## Key Metrics to Examine

### Run analyzer on partial results as scenarios complete:
```bash
cd tools/sweep
python 4_analyze_results.py --input realistic_sweep3/results
```

### Correlations (check against sweep2 baselines):
| Parameter | Sweep2 Correlation | Expected Sweep3 Direction |
|---|---|---|
| hashrate_split | +0.814 | Still dominant, may shift slightly |
| economic_split | ~0 (dead) | Should appear, positive |
| user_ideology_strength | +0.168 | Similar |
| econ_ideology_strength | -0.141 | Similar |
| solo_miner_hashrate | low | May rise (v2 power user hashrate) |

### Outcome distribution (sweep2 baseline):
- v27_dominant: 56%
- v26_dominant: 38%
- contested: 6%

If economic_split is truly live, this distribution should shift based on the
sampled economic_split values across scenarios.

### Threshold estimates (sweep2 baselines):
- pool_neutral_pct threshold: ~29.5%
- hashrate_split threshold: ~0.46

## Red Flags
- If `economic_split` correlation is still ~0 -> economic split fix still broken
- If all scenarios show identical difficulty curve shapes -> retarget not responding to hashrate
- If no EDA events appear in any extreme hashrate_split scenario -> difficulty oracle not firing
- If contested rate stays at 6% -> fee counter-pressure not extending fork persistence
