# Methodology: Bitcoin Fork Dynamics Simulation

This document describes how the simulation is constructed — from network topology
to entity modeling. It covers the Bitcoin network development, the warnet
simulation platform, and the behavioral models for each actor type.

For the experimental design (parameter sweeps, boundary fitting, Latin hypercube
sampling), see `tools/sweep/SCENARIO_DISCOVERY.md`.

---

## 1. Simulation Platform: Warnet

[Warnet](https://github.com/bitcoin-dev-tools/warnet) is a Kubernetes-based
framework for running controlled Bitcoin network experiments. It launches real
`bitcoind` nodes (not mocks) in pods on a cluster, connects them according to a
declared topology, and allows a Python *scenario script* to coordinate activity
across them.

### Architecture

```
network.yaml          → warnet build        → Kubernetes pods (one per node)
scenarios/<script>.py → warnet run <script> → commander pod
```

The **commander pod** runs the scenario script using the `Commander` base class.
It holds RPC handles to every node in the network and drives the simulation:
mining blocks, querying state, and applying behavioral logic.

### Scenario execution

The main scenario is `scenarios/partition_miner_with_pools.py`. It runs as a
commander that:

1. Loads network metadata from the `network.yaml` that was used to build the cluster
2. Partitions nodes into v27 and v26 sets by querying each node's `getnetworkinfo`
3. Initializes oracles (price, fee, difficulty, reorg)
4. Enters the main simulation loop, running for `--duration` seconds with
   `--interval`-second block intervals

### Configuration sources

The scenario reads behavioral parameters from two config files at runtime:

| Config file | Controls |
|-------------|----------|
| `scenarios/config/mining_pools_config.yaml` | Pool ideology, hashrate, loss tolerance |
| `scenarios/config/economic_nodes_config.yaml` | Economic and user node ideology, switching thresholds, inertia |

These files are overwritten by the sweep infrastructure at the start of each run.

---

## 2. Network Development

### Design principles

The networks model the Bitcoin ecosystem at a ~1:400 scale factor (calibrated
against bitnodes.io, mempool.space/mining, and exchange proof-of-reserve data as
of February 2026). Two networks are maintained:

| Network | File | Nodes | Purpose |
|---------|------|-------|---------|
| `realistic-economy-v2` | `networks/realistic-economy-v2/network.yaml` | 60 | Primary; full representation |
| `realistic-economy-lite` | `networks/realistic-economy-lite/network.yaml` | 25 | Memory-efficient; faster runs |

### Node structure

Each node in `network.yaml` has three sections:

- **`image.tag`** — the Bitcoin Core version string (`'27.0'` or `'26.0'`),
  which determines which partition the node belongs to
- **`bitcoin_config`** — `bitcoind` configuration (`maxconnections`,
  `maxmempool`, `txindex`)
- **`metadata`** — simulation parameters used by the scenario script (`role`,
  `fork_preference`, `ideology_strength`, `custody_btc`, etc.)
- **`addnode`** — explicit peer connections defining the intra-partition topology

### Full network (realistic-economy-v2, 60 nodes)

```
Partition  | Entity Type         | Count | Role label(s)
-----------+---------------------+-------+------------------------------------------
v27        | Mining pools        |   4   | mining_pool
v27        | Economic nodes      |  12   | major_exchange, exchange, institutional,
           |                     |       | payment_processor, merchant
v27        | User nodes          |  14   | power_user, casual_user
-----------+---------------------+-------+------------------------------------------
v26        | Mining pools        |   4   | mining_pool
v26        | Economic nodes      |  12   | major_exchange, exchange, institutional,
           |                     |       | payment_processor, merchant
v26        | User nodes          |  14   | power_user, casual_user
```

Each pool node starts on the partition matching its image tag (v27 or v26).
Economic and user node initial partitions are assigned by the sweep build script
based on the scenario's `economic_split` parameter (see Section 6).

### Lite network (realistic-economy-lite, 25 nodes)

The lite network preserves the mining layer exactly (same 8 pools, same hashrate
percentages) and consolidates economic and user nodes into aggregate cohorts:

```
Role                   | Represents
-----------------------+-----------------------------------------
economic_aggregate     | All exchanges, institutions, merchants
power_user_aggregate   | Power user cohorts
casual_user_aggregate  | Casual user cohorts
```

Aggregate nodes carry a `represents_count` field encoding the combined economic
weight of all consolidated entities. Behavioral parameters are applied identically
to aggregate nodes as to their full-network equivalents.

### Network calibration

Mining hashrate distribution (calibrated Feb 2026):
- Named pools: 86.4% of total hashrate (top 8 by blocks found)
- User node cohorts: 11.75% (solo miners, small pools)
- Measurement variance: ~1.85%

Economic weight (custody-based):
- Major exchanges, institutional holders: high `custody_btc`
- Payment processors, merchants: moderate `custody_btc` + high `daily_volume_btc`
- User nodes: low `custody_btc`

---

## 3. Soft Fork Topology: Asymmetric Partition

### Bitcoin consensus background

A soft fork tightens consensus rules. v27 nodes enforce stricter validation;
v26 nodes accept both v26-valid and v27-valid blocks (since v27 is a strict
subset). This asymmetry is the defining feature of soft fork dynamics.

### Network topology

The network is partitioned into two islands at startup. Nodes within each island
can communicate freely; cross-partition communication is blocked via disconnection
at the start of each run.

```
v27 partition (strict)      v26 partition (permissive)
  node-0000                   node-0030
  node-0001     X X X         node-0031
  ...          (no            ...
  node-0029    peering)       node-0059
```

### Asymmetric block propagation

v26 nodes accept v27 blocks — stricter rules are valid under looser rules. This
is modeled explicitly:

- v27 nodes: `accepts_foreign_blocks: false` — they will not accept v26 blocks
- v26 nodes: `accepts_foreign_blocks: true` — they accept v27 blocks

When a v27 block is mined, the scenario script calls `submitblock` on one
designated v26 bridge node. P2P propagation within the v26 island handles the
rest. This replicates the Bitcoin mainnet behavior where a soft-fork compliant
block is valid on both chains, but the reverse is not.

v26 blocks are never submitted to v27 nodes. v27 nodes maintain their own chain,
unaware of the v26 chain's progress.

### Fork resolution mechanics

If `--enable-reunion` is set, the scenario reconnects the two partitions at the
end of the run and lets Bitcoin's heaviest-chain rule resolve the dispute. The
fork with the most cumulative chainwork (proof-of-work) wins and the losing chain
reorganizes to it. The winning fork is determined by the difficulty oracle's
cumulative chainwork tracking (see Section 5).

---

## 4. Mining Pools

### Representation

Eight mining pools are modeled individually (Foundry USA, MARA Pool, AntPool,
ViaBTC, F2Pool, Binance Pool, SBI Crypto, Luxor). Each pool occupies one Bitcoin
node per partition (a pool node exists on the v27 side and a counterpart on the
v26 side) and is characterized by:

| Parameter | Meaning |
|-----------|---------|
| `hashrate_pct` | Pool's share of total network hashrate (0–100) |
| `fork_preference` | Ideological affiliation: `v27`, `v26`, or `neutral` |
| `ideology_strength` | Willingness to mine at a loss for ideology (0.0–1.0) |
| `profitability_threshold` | Minimum profit advantage required to switch (0.0–1.0) |
| `max_loss_pct` | Maximum revenue sacrifice the pool will accept (0.0–1.0) |
| `initial_fork` | Which partition the pool starts mining on |

### Pool decision process

Each pool independently evaluates which fork to mine every 10 minutes (cooldown).
The decision uses profitability comparison with an ideology override:

**Step 1 — Profitability calculation**

For each fork, expected hourly profit is:

```
blocks_per_hour = 6.0 * (pool.hashrate_pct / 100.0)
revenue_per_hour = blocks_per_hour * (block_subsidy + fee_revenue) * fork_price
profit_per_hour = revenue_per_hour - (blocks_per_hour * mining_cost)
```

Profitability is computed assuming 50% hashrate on each fork (a neutral counterfactual).
This prevents feedback loops where a fork's low current hashrate makes it appear
unprofitable, discouraging further mining.

**Step 2 — Rational choice**

The fork with higher `profit_per_hour` is the rational choice.

**Step 3 — Ideology override**

If the pool has a `fork_preference` and its preferred fork is less profitable:

```
max_acceptable_loss_pct = ideology_strength * max_loss_pct
loss_pct = (rational_profit - preferred_profit) / rational_profit
```

- If `loss_pct <= max_acceptable_loss_pct`: mine the preferred fork despite lower
  profit (ideology wins)
- If `loss_pct > max_acceptable_loss_pct`: switch to the rational choice (economics
  wins — "forced switch")

Committed pools (high `ideology_strength * max_loss_pct`) will hold their
preferred fork across substantial profitability gaps. Once forced to switch, they
rarely switch back because there is no mechanism that makes their preferred fork
more profitable again unless economic conditions reverse.

### Pool types

Three behavioral archetypes emerge from the parameter space:

| Archetype | `fork_preference` | Behavior |
|-----------|-------------------|---------|
| **Committed** | `v27` or `v26` | High ideology; mines preferred fork until economically unsustainable |
| **Neutral** | `neutral` | Pure profit maximization; always follows the more profitable fork |
| **Swing** | `v27` or `v26` | Moderate ideology; switches when profitability gap exceeds tolerance |

### Pool-to-node mapping

The scenario maps each pool to its corresponding network node. Pool decisions are
executed by mining on that node: the scenario selects the appropriate node, calls
`generatetoaddress`, and records the result.

---

## 5. Difficulty and Chainwork

### Why difficulty matters

After a fork, both chains inherit the same pre-fork difficulty. The minority
chain (lower hashrate) produces blocks much more slowly, increasing transaction
confirmation times and fee pressure. Difficulty retargets independently on each
chain, restoring a target block interval over time.

### Difficulty oracle

`scenarios/lib/difficulty_oracle.py` models per-fork difficulty dynamics:

- **Block production probability**: Each simulation tick, a block is mined with
  probability `tick_interval / expected_block_interval`, where
  `expected_block_interval = target_interval * (difficulty / hashrate_fraction)`
- **Retargeting**: Every `--retarget-interval` blocks, difficulty adjusts
  proportionally to actual vs. target block time (clamped to 4x adjustment)
- **Emergency Difficulty Adjustment (EDA)**: Optional BCH-style rapid downward
  adjustment if blocks are taking more than 6x the target time (disabled by default)
- **Chainwork**: Cumulative sum of difficulty across all mined blocks, matching
  Bitcoin's actual heaviest-chain selection rule

### Winning fork determination

The fork with higher cumulative chainwork wins a reunion event. Height alone is
insufficient — a chain that retargeted downward (lower difficulty, faster blocks)
may have more blocks but less chainwork than a chain that maintained high
difficulty.

---

## 6. Price Oracle

### Role

The price oracle tracks the market valuation of each fork's token over the course
of a simulation. Price divergence creates the profit differential that drives pool
and economic node decisions.

### Price model

Price only diverges after the fork becomes **sustained** (total blocks mined
across both chains since the split reaches a minimum depth threshold, default 6).
Natural chain splits that resolve quickly do not produce price divergence.

Once sustained, each fork's price is:

```
chain_factor   = 0.8 + (chain_weight   * 0.4)    # range [0.8, 1.2]
economic_factor = 0.8 + (economic_weight * 0.4)
hashrate_factor = 0.8 + (hashrate_weight * 0.4)

combined_factor = chain_factor*0.3 + economic_factor*0.5 + hashrate_factor*0.2

price = base_price * combined_factor
```

Where weights are fractions (0–1, with 0.5 meaning exactly even):
- `chain_weight`: Relative block production (blocks on this chain / total blocks)
  or chainwork fraction when difficulty oracle is active
- `economic_weight`: Fraction of economic node weight on this fork
- `hashrate_weight`: Fraction of total pool hashrate mining this fork

Price is capped at `base_price ± 20%` (max_divergence). The economic weight
component dominates (coefficient 0.5 vs. 0.3 for chain and 0.2 for hashrate),
reflecting Bitcoin's custody-driven valuation.

### Feedback loop

The price oracle is at the center of a feedback loop:

```
Pool hashrate → chain_weight → price → pool profitability → pool hashrate
Economic nodes → economic_weight → price → economic node decisions → economic_weight
```

This loop can amplify initial imbalances (a fork that gets slightly more hashrate
becomes more profitable, attracting more hashrate) or dampen them (a fork with
lower price triggers switching that redistributes hashrate).

---

## 7. Economic Nodes

### Representation and roles

Economic nodes represent Bitcoin holders and transactors whose custody and
transaction behavior determines market demand for each fork's token. In the full
network, 24 nodes cover six roles:

| Role | Entity type | `custody_btc` | `daily_volume_btc` |
|------|-------------|:-------------:|:-------------------:|
| `major_exchange` | Coinbase, Binance | Very high | Very high |
| `exchange` | Mid-tier exchanges | High | High |
| `institutional` | Corporate treasuries, ETF custodians | Very high | Low |
| `payment_processor` | Strike, BitPay | Moderate | High |
| `merchant` | Online retailers | Low–moderate | Moderate |

Each node starts on the partition specified by the sweep's `economic_split`
parameter. The build script (`tools/sweep/2_build_configs.py`) sorts all economic
nodes by `custody_btc` descending and assigns the top fraction to v27, meeting
the target `economic_split` (e.g., `economic_split=0.70` means 70% of total
custody weight starts on v27).

### Economic decision process

Each economic node independently evaluates which fork to participate in on a
configurable update interval (default every 5 minutes).

**Parameters governing decisions:**

| Parameter | Meaning |
|-----------|---------|
| `fork_preference` | Ideological affiliation (`v27`, `v26`, or `neutral`) |
| `ideology_strength` | Willingness to accept lower token price for ideology (0.0–1.0) |
| `switching_threshold` | Minimum price advantage required to consider switching |
| `inertia` | Additional resistance to switching beyond the threshold |
| `max_loss_pct` | Maximum price disadvantage tolerated for ideology |
| `switching_cooldown` | Minimum seconds between decisions |

**Decision pipeline:**

1. **Rational choice**: The fork with the higher token price is the rational
   choice. `price_advantage = |v27_price - v26_price| / lower_price`

2. **Ideology override**: If the node has a `fork_preference` and its preferred
   fork has a lower price:
   ```
   max_acceptable_loss = ideology_strength * max_loss_pct
   ```
   If `price_advantage <= max_acceptable_loss`, the node stays on its preferred
   fork despite lower price. If `price_advantage > max_acceptable_loss`, economics
   overrides ideology.

3. **Inertia check**: Even after ideology, the node must clear a switching barrier
   before changing forks:
   ```
   effective_threshold = switching_threshold + inertia
   ```
   If the price advantage does not exceed this threshold, the node stays put
   regardless of which fork is more profitable.

### Economic weight in the price model

A node's contribution to `economic_weight` is its `custody_btc` (or
`consensus_weight` if pre-computed). The aggregate weight on each fork is summed
across all nodes and normalized to a 0–1 fraction for the price oracle.

### Transaction velocity and fees

In addition to price support, economic nodes generate fee demand. A node's
`transaction_velocity` parameter (0.0–1.0) scales its contribution to the fee
oracle's transaction volume estimate. Transactional nodes (exchanges, payment
processors) have high velocity; custodial nodes (institutions, HODLers) have
low velocity. This distinction matters because slower chains accumulate mempool
backlog, driving up fees on the minority chain as a partial economic compensator.

---

## 8. User Nodes

### Representation and role

User nodes represent individual Bitcoin participants — retail users, small
operators, and solo miners. In the full network, 28 nodes are divided into two
cohort types:

| Role | Entity type | Economic weight | Hashrate |
|------|-------------|:---------------:|:--------:|
| `power_user` | Technically sophisticated users | Low-moderate | Small (solo mining) |
| `casual_user` | Retail holders | Very low | None |

User nodes collectively represent ~11.75% of total hashrate through solo mining
activity. This hashrate scales with the user node's `hashrate_pct` field and
follows the node's fork decision.

### User decision process

User node decisions use the same ideology-inertia pipeline as economic nodes,
with typically higher ideology strength and higher switching inertia (users
are more resistant to price signals than institutions). User ideology parameters
have been empirically shown to have no causal effect on fork outcomes in the
parameter ranges tested — the small economic weight and small hashrate contribution
mean that even large shifts in user behavior do not change which fork wins. See
`targeted_sweep4` findings in `tools/sweep/SWEEP_FINDINGS.md`.

---

## 9. Fee Oracle

`scenarios/lib/fee_oracle.py` models the fee market on each fork independently.
The key dynamic: when a fork has lower hashrate (slower blocks), transaction
volume accumulates in the mempool, driving up fee rates. Higher fees partially
compensate miners on the minority chain and are factored into pool profitability
calculations.

Fee revenue per block is estimated as:
```
fee_btc = (fee_rate_sats_per_vbyte * 1_000_000_vbytes) / 100_000_000
```

This provides a counter-pressure mechanism: the chain that is losing hashrate
produces slower blocks, accumulates more fees, which makes it somewhat more
attractive to mine. In practice this effect is small relative to the price
differential in most tested scenarios.

---

## 10. Simulation Loop

The scenario runs on a tick-based loop. In each iteration:

1. **Block production**: Using the difficulty oracle, determine probabilistically
   whether a block should be mined on each fork this tick. If so, call
   `generatetoaddress` on the appropriate pool node and propagate v27 blocks to
   the v26 island via `submitblock`.

2. **State collection**: Query both chains for block height, chainwork, mempool
   size, and fee rates.

3. **Price update** (every `--price-update-interval` seconds): Call
   `update_prices_from_state()` with current chain weights, economic weights, and
   hashrate fractions.

4. **Pool decisions** (every `--hashrate-update-interval` seconds): Each pool
   evaluates its profitability on both forks and may switch its mining target.

5. **Economic node decisions** (every `--economic-update-interval` seconds): Each
   economic and user node evaluates its fork choice and may switch partitions.

6. **Snapshot** (every `--snapshot-interval` seconds): Append current state to
   the time series for analysis.

7. **Results export**: At the end of the run, all time series, pool decision
   records, oracle states, and partition summaries are written to `/tmp/` in the
   commander pod, base64-encoded and extractable from `kubectl logs`.

---

## 11. Scenario Configuration

### Pool scenarios (`mining_pools_config.yaml`)

Named scenarios define sets of pool parameters:

| Scenario | Description |
|----------|-------------|
| `realistic_current` | Calibrated against 2024-2025 pool landscape; mostly neutral pools |
| `ideological_war` | Strong ideological split; committed pools on both sides |
| `ideological_standoff` | Engineered persistent fork; both sides hold indefinitely |

### Economic scenarios (`economic_nodes_config.yaml`)

Named scenarios define economic and user node behavioral defaults with optional
per-role overrides:

| Scenario | Description |
|----------|-------------|
| `realistic_current` | Exchanges rational; users mildly ideological |
| `ideological_split` | Strong ideological division across all participants |
| `purely_rational` | No ideology anywhere; all actors follow price |
| `ideological_standoff` | Nodes locked to their initial fork by extreme inertia |

In sweep runs, scenario parameters are overwritten programmatically by the build
script before each run — the named scenarios serve as baselines and documentation
anchors.

---

## 12. Key Model Assumptions and Limitations

| Assumption | Implication |
|------------|-------------|
| Pool profitability uses `assumed_fork_hashrate=50.0` | Pool decisions are not affected by the fork's current hashrate share, only by price and fees. Prevents circular dependency. |
| Max price divergence capped at ±20% | Extreme scenarios (one fork near-worthless) are not modeled. |
| Block subsidy fixed at 3.125 BTC | Post-halving regime; no halving event during a run. |
| Mining cost fixed at $100,000/block | Same cost on both forks; does not vary with difficulty. |
| Once committed pools are forced to switch, they rarely switch back | No mechanism makes the preferred fork more profitable after a forced switch without an external price reversal. |
| User node parameters have zero measured causal effect on outcomes | See `targeted_sweep4`. User ideology and thresholds do not change which fork wins. |
| Network topology is static during the simulation | Partition membership is fixed; dynamic switching requires `--enable-dynamic-switching`. |
