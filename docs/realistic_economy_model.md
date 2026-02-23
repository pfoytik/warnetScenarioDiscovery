# Realistic Bitcoin Economy Network Model

## Overview

The `realistic-economy` network provides a comprehensive simulation of the Bitcoin ecosystem with realistic distributions of participants across mining, exchanges, institutions, and users. This model is designed for studying fork dynamics, consensus formation, and economic coordination.

## Network Composition

| Category | Count | % of Network | Description |
|----------|-------|--------------|-------------|
| Mining Pools | 8 | 13% | Professional mining operations |
| Major Exchanges | 4 | 7% | Top-tier global exchanges |
| Mid-tier Exchanges | 6 | 10% | Regional and specialized exchanges |
| Payment Processors | 3 | 5% | Bitcoin payment infrastructure |
| Merchants | 6 | 10% | Companies accepting Bitcoin |
| Institutional Holders | 5 | 8% | Corporate and fund holders |
| Power Users | 12 | 20% | Developers, node runners, enthusiasts |
| Casual Users | 16 | 27% | HODLers, occasional users |
| **Total** | **60** | **100%** | |

## Partition Split

- **v27 Partition (nodes 0-29)**: 30 nodes running Bitcoin Core 27.0
- **v26 Partition (nodes 30-59)**: 30 nodes running Bitcoin Core 26.0

The partition split is balanced by node count, but economic weight and hashrate distribution vary based on each node's metadata. Fork preferences are not fixed in the base network — they are configurable and will be set to different distributions depending on the test run scenario. See the Fork Preference Configuration section for details.

---

## Proportional Modeling Methodology

### Scale Factor

This 60-node network is calibrated against real-world Bitcoin network data to be proportionally representative rather than literally complete. As of February 2026, Bitnodes reports approximately **25,140 reachable full nodes** globally, with an estimated 3–5x more unreachable/behind-NAT nodes, putting total full nodes at roughly 75,000–100,000. Approximately **216 named centralized entities** hold over 30% of circulating supply.

The network operates at a **compression ratio of approximately 1:400** against the reachable node population:

| Real World | Count | Scale Factor | Model |
|---|---|---|---|
| Reachable full nodes | ~25,000 | ÷400 | 60 nodes |
| Named mining pools (>1% hashrate) | ~8–10 | 1:1 (individual) | 8 nodes |
| Named economic entities | ~216 | top entities only | 10–15 nodes |
| Power users / node runners | ~5,000 | ÷400 | 12 nodes |
| Casual users / HODLers | ~20,000 | ÷1,250 | 16 nodes* |

*Casual users are the most compressed category. If the network is expanded, this is where nodes should be added first.

### Two-Tier Modeling Approach

Nodes are modeled under one of two representation tiers:

**Tier 1 — Individual representation**: Each node represents exactly one real-world entity. This applies to named mining pools, major exchanges, and named institutional holders. Parameters (custody_btc, daily_volume_btc, hashrate_pct) reflect that entity's publicly reported figures.

**Tier 2 — Aggregate representation**: Each node represents a *cohort* of real-world participants at the network's scale factor. This applies to mid-tier exchanges, payment processors, merchants, power users, and casual users. Parameters reflect the *aggregate* of the cohort, not an individual participant. The `represents_count` metadata field documents how many real-world nodes or entities each Tier 2 node stands in for.

For example, a "Long-term HODLer" node at 1:1,250 compression representing HODLers each holding ~3–5 BTC should carry a `custody_btc` value of approximately 3,750–6,250 BTC — not 10 BTC. Individual-scale values understate cohort economic influence and will skew fork dynamics simulations.

### Calibration Sources

| Data Type | Source | Notes |
|---|---|---|
| Mining pool hashrate | mempool.space/mining, hashrateindex.com | Updated daily |
| Exchange custody | Exchange proof-of-reserves, defillama.com/cexs | Updated regularly |
| Node counts / version distribution | bitnodes.io | Live data, API available |
| Institutional holdings | bitcointreasuries.net | Regularly updated with citations |
| User wallet size cohorts | Glassnode, Coin Metrics | On-chain wallet cohort data |
| Full node geography | bitnodes.io/nodes/all/ | Country and ASN breakdown |

### Hashrate Coverage

The eight modeled mining pools account for approximately **88.21%** of total network hashrate. The remaining **~11.79%** represents diffuse solo miners, home miners, small regional pools, and unidentified hashrate not attributable to named pools. This gap is distributed across non-pool nodes as follows:

| Node Type | Hashrate | Rationale |
|---|---|---|
| Mining Farm Operator | 3.50% | Aggregated small farms not in named pools |
| Mining Hobbyist | 0.50% | Home ASIC mining |
| Node Runner | 0.30% | Some run ASICs alongside their node |
| Developer | 0.20% | Testing/dev mining setups |
| BCH Supporter | 0.20% | Ideological solo miners |
| Privacy Advocate | 0.20% | Solo mining for censorship resistance |
| Big Blocker | 0.15% | Ideological miners |
| Bitcoin Educator | 0.10% | Small home mining |
| Lightning Node Operator | 0.10% | Some run ASICs |
| Curious Experimenter | 0.05% | Minimal test mining |
| **Unmodeled remainder** | **~6.49%** | Explicitly unmodeled diffuse hashrate |
| **Total user/non-pool** | **~11.79%** | |

The unmodeled remainder is intentional and academically defensible: there genuinely exists hashrate in the real network that does not map to any identifiable pool or actor. Documenting it explicitly is preferable to distributing it arbitrarily.

---

## Category Details

### Mining Pools (8 nodes)

Mining pools control the hashrate and produce blocks. Their fork decisions are driven by profitability calculations that factor in price, difficulty, and ideology. All pool nodes are **Tier 1** (individual representation).

| Pool | Hashrate | Ideology | Max Loss | Notes |
|------|----------|----------|----------|-------|
| Foundry USA | 26.89% | 0.95 | 50% | Highly committed |
| MARA Pool | 4.85% | 0.70 | 30% | Strong preference |
| Luxor | 3.12% | 0.65 | 25% | Moderate preference |
| Ocean | 1.42% | 0.85 | 40% | Ideological, decentralization focus |
| AntPool | 19.25% | 0.65 | 40% | Strong preference |
| F2Pool | 11.25% | 0.55 | 28% | Moderate preference |
| ViaBTC | 11.39% | 0.60 | 35% | Moderate preference |
| Binance Pool | 10.04% | 0.45 | 22% | More rational, follows profit |

**Total Hashrate Distribution:**
- v27 pools: ~36.28% (Foundry + MARA + Luxor + Ocean)
- v26 pools: ~51.93% (AntPool + F2Pool + ViaBTC + Binance Pool)
- Non-pool nodes: ~5.30% (distributed across user categories, see above)
- Unmodeled diffuse: ~6.49%

### Major Exchanges (4 nodes)

Major exchanges are mostly neutral and highly responsive to price signals. They have enormous custody and volume, making them critical for price discovery. All are **Tier 1** (individual representation).

| Exchange | Custody BTC | Daily Volume | Ideology | Inertia |
|----------|-------------|--------------|----------|---------|
| Coinbase | 1,000,000 | 150,000 | 0.10 | 0.20 |
| Kraken | 600,000 | 80,000 | 0.15 | 0.18 |
| Binance | 1,500,000 | 250,000 | 0.05 | 0.22 |
| Bitfinex | 400,000 | 60,000 | 0.12 | 0.18 |

**Key Characteristics:**
- Low ideology (0.05–0.15) — follow market signals
- High inertia (0.18–0.22) — switching costs are significant
- Low max_loss_pct (0.04–0.06) — won't tolerate large disadvantages

> **Note on custody figures**: Exchange custody values are approximate. Binance's publicly reported proof-of-reserves shows ~575,000 BTC; the 1,500,000 figure here may include assets held across affiliated entities and cold storage not captured in PoR snapshots. Treat these as order-of-magnitude anchors, not audited balances.

### Mid-tier Exchanges (6 nodes)

Regional and specialized exchanges with moderate volume. Slightly more ideological than major exchanges. **Tier 1** for named entities; parameters reflect individual exchange figures.

| Exchange | Custody BTC | Daily Volume | Ideology |
|----------|-------------|--------------|----------|
| Gemini | 200,000 | 25,000 | 0.30 |
| River | 80,000 | 10,000 | 0.50 |
| Swan Bitcoin | 50,000 | 8,000 | 0.60 |
| OKX | 300,000 | 45,000 | 0.25 |
| Bybit | 150,000 | 30,000 | 0.20 |
| Huobi | 100,000 | 20,000 | 0.22 |

### Payment Processors (3 nodes)

Payment infrastructure that enables Bitcoin commerce. Higher transaction velocity, moderate ideology. **Tier 1** for named entities.

| Processor | Custody BTC | Daily Volume | Ideology |
|-----------|-------------|--------------|----------|
| BTCPay Server | 5,000 | 15,000 | 0.75 |
| OpenNode | 3,000 | 5,000 | 0.65 |
| BitPay | 8,000 | 20,000 | 0.35 |

### Merchants (6 nodes)

Companies accepting Bitcoin for goods/services. Lower custody, focused on transaction flow. **Tier 1** for named entities; parameters reflect individual company figures.

| Merchant | Custody BTC | Daily Volume | Ideology |
|----------|-------------|--------------|----------|
| Tech Retailer | 500 | 200 | 0.40 |
| E-commerce | 300 | 150 | 0.20 |
| Travel Agency | 200 | 100 | 0.35 |
| Overstock | 800 | 300 | 0.30 |
| Newegg | 400 | 180 | 0.18 |
| AT&T | 250 | 120 | 0.15 |

### Institutional Holders (5 nodes)

Corporate treasuries and funds. High custody, low velocity (HODLing strategy). All are **Tier 1** (individual representation).

| Institution | Custody BTC | Daily Volume | Ideology |
|-------------|-------------|--------------|----------|
| MicroStrategy | 190,000 | 500 | 0.85 |
| Tesla | 10,000 | 100 | 0.20 |
| Block Inc | 8,000 | 200 | 0.70 |
| Grayscale | 620,000 | 2,000 | 0.15 |
| Fidelity Digital | 150,000 | 800 | 0.12 |

**Key Characteristics:**
- Very low transaction velocity (0.02–0.08)
- High inertia — institutional processes are slow
- Mixed ideology — some true believers, some purely financial

> **Note on custody figures**: MicroStrategy has continued accumulating since this model was calibrated and now holds substantially more than 190,000 BTC. Grayscale experienced significant outflows following the GBTC ETF conversion and currently holds closer to 220,000–250,000 BTC rather than 620,000. These figures should be updated from bitcointreasuries.net before publication.

### Power Users (12 nodes)

Developers, node runners, miners, and enthusiasts. High ideology, small individual holdings, some contribute hashrate. **Tier 2** nodes — each represents approximately 400 real-world participants of that type (`represents_count: 400`). Custody and volume figures reflect individual-scale values; see the Proportional Modeling section for cohort-scale adjustment guidance.

| User Type | Custody BTC | Hashrate | Ideology |
|-----------|-------------|----------|----------|
| Developer | 100 | 0.20% | 0.90 |
| Node Runner | 50 | 0.30% | 0.85 |
| Bitcoin Educator | 25 | 0.10% | 0.80 |
| Active Trader | 200 | 0% | 0.15 |
| Mining Hobbyist | 15 | 0.50% | 0.75 |
| Privacy Advocate | 30 | 0.20% | 0.88 |
| BCH Supporter | 80 | 0.20% | 0.88 |
| Big Blocker | 40 | 0.15% | 0.82 |
| Exchange Arbitrageur | 150 | 0% | 0.05 |
| Mining Farm Operator | 500 | 3.50% | 0.55 |
| OTC Desk Operator | 1,000 | 0% | 0.10 |
| Lightning Node Op | 20 | 0.10% | 0.45 |

**Key Characteristics:**
- Small individual holdings but high collective influence
- Some contribute mining hashrate (solo mining / small farms)
- High ideology variance — from arbitrageurs (0.05) to advocates (0.90)

### Casual Users (16 nodes)

General Bitcoin holders with varying engagement levels. Represent the "long tail" of Bitcoin ownership. **Tier 2** nodes — each represents approximately **1,250 real-world participants** (`represents_count: 1250`), reflecting the higher compression ratio of this category relative to the 1:400 network average. Custody and volume figures in the YAML are currently individual-scale and should be multiplied by ~1,250 when used in economic weight calculations.

| User Type | Individual Custody BTC | Cohort Custody BTC* | Daily Volume | Ideology |
|-----------|------------------------|---------------------|--------------|----------|
| Long-term HODLer (x2) | 8–10 | 10,000–12,500 | 0.01 | 0.55–0.70 |
| DCA Investor (x2) | 4–5 | 5,000–6,250 | 0.04–0.05 | 0.25–0.30 |
| Occasional Spender (x2) | 1.5–2 | 1,875–2,500 | 0.08–0.1 | 0.15–0.20 |
| Newbie (x2) | 0.3–0.5 | 375–625 | 0.01–0.02 | 0.03–0.05 |
| Remittance User (x2) | 0.15–0.2 | 188–250 | 0.4–0.5 | 0.10–0.12 |
| Savings Account (x2) | 2.5–3 | 3,125–3,750 | 0.008–0.01 | 0.38–0.45 |
| Gift Recipient (x2) | 0.08–0.1 | 100–125 | 0.003–0.005 | 0.02 |
| Speculator | 1 | 1,250 | 0.5 | 0.08 |
| Curious Experimenter | 0.05 | 62.5 | 0.01 | 0.15 |

*Cohort custody = individual custody × 1,250 (represents_count). Use cohort figures for fork economic weight calculations.

**Key Characteristics:**
- Low individual holdings; significant aggregate economic weight at cohort scale
- Low transaction velocity (mostly HODLing)
- Low-to-moderate ideology
- Casual user category is the most compressed in the network (1:1,250 vs. 1:400 average) — a known modeling limitation

---

## Economic Weight Distribution

### By Custody (BTC Holdings)

| Category | Total BTC | % of Supply* |
|----------|-----------|--------------|
| Major Exchanges | 3,500,000 | 17.9% |
| Institutional | 978,000 | 5.0% |
| Mid-tier Exchanges | 880,000 | 4.5% |
| Mining Pools | 183,000 | 0.9% |
| Power Users | 2,210 | 0.01% |
| Payment Processors | 16,000 | 0.08% |
| Merchants | 2,450 | 0.01% |
| Casual Users | ~38 (individual) / ~47,500 (cohort-scaled) | <0.01% / ~0.24% |

*Based on ~19.5M total BTC supply. Casual user figures shown at both individual-node and cohort-scaled values to illustrate the difference in economic weight depending on modeling approach.

### By Daily Volume (Transaction Activity)

| Category | Daily Volume BTC | % of Total |
|----------|------------------|------------|
| Major Exchanges | 540,000 | 75.8% |
| Mid-tier Exchanges | 138,000 | 19.4% |
| Payment Processors | 40,000 | 5.6% |
| Mining Pools | 14,000 | 2.0% |
| Institutional | 3,600 | 0.5% |
| Merchants | 1,050 | 0.1% |
| Power Users | ~322 | <0.1% |
| Casual Users | ~1.7 (individual) / ~2,125 (cohort-scaled) | <0.01% |

---

## Fork Preference Configuration

Fork preferences (`fork_preference`, `ideology_strength`, `switching_threshold`, `inertia`, `max_loss_pct`) are **not fixed in the base network definition**. They are treated as configurable parameters set per test run, allowing the same network topology and economic weights to be reused across a wide range of experimental scenarios.

Each test run specifies a fork preference distribution scenario — for example, a hashrate-majority/custody-minority split, a geographically-aligned split, or a random assignment weighted by ideology. This separation keeps the base network a stable, reusable artifact while the experimental variables live in scenario configuration files.

Example scenario distributions that may be tested:

| Scenario | Description |
|---|---|
| Hashrate vs. custody | Majority hashrate on one fork, majority custody on the other |
| Geographic split | US/EU-aligned nodes on one fork, Asia-Pacific on the other |
| Neutral majority | Most nodes neutral; small committed minorities on each side |
| Uniform preference | All nodes prefer the same fork (baseline/control) |
| Random weighted | Fork preference assigned probabilistically by ideology strength |

The `ideology_strength` values in the node metadata reflect each entity's *susceptibility* to holding a strong fork preference — they remain stable across scenarios even as the `fork_preference` assignment changes. High ideology nodes will hold their assigned preference under greater economic pressure; low ideology nodes will follow price signals regardless of assignment.

---

## Node Metadata Schema

Each node includes the following metadata fields:

```yaml
metadata:
  # Identity
  role: mining_pool | major_exchange | exchange | payment_processor | merchant | institutional | power_user | casual_user
  node_type: mining_pool | economic | user
  entity_id: unique identifier

  # Representation tier (new)
  representation_tier: 1 | 2          # 1 = individual entity, 2 = cohort aggregate
  represents_count: integer            # Number of real-world participants this node models (Tier 2 only)

  # Economic weight
  hashrate_pct: 0.0 - 100.0  # Mining power (pools and some users)
  custody_btc: float          # BTC holdings (individual for Tier 1; individual-scale for Tier 2 — multiply by represents_count for cohort weight)
  daily_volume_btc: float     # Transaction activity (same scaling note as custody_btc)

  # Fork behavior (fork_preference is set per test run scenario, not in the base network)
  fork_preference: v27 | v26 | neutral  # configured by scenario, not hardcoded
  ideology_strength: 0.0 - 1.0      # Commitment to preference — stable across scenarios
  switching_threshold: 0.0 - 1.0    # Min advantage to consider switching
  inertia: 0.0 - 1.0                # Resistance to switching
  max_loss_pct: 0.0 - 1.0           # Max disadvantage before forced switch

  # For mining pools
  profitability_threshold: 0.0 - 1.0  # Min profit difference to switch

  # Activity classification
  activity_type: transactional | custody | mixed
  transaction_velocity: 0.0 - 1.0   # How actively they transact

  # Fork acceptance
  accepts_foreign_blocks: true | false  # For asymmetric soft forks
```

---

## Usage

### Deploy the network:
```bash
warnet deploy networks/realistic-economy/network.yaml
```

### Run a fork simulation:
```bash
warnet run scenarios/partition_miner_with_pools.py \
    --network networks/realistic-economy/network.yaml \
    --pool-scenario realistic_current \
    --economic-scenario realistic_current \
    --enable-difficulty \
    --duration 7200 \
    --results-id realistic_test
```

---

## Parameter Sweep Dimensions

This network is designed for parameter sweep analysis across:

1. **Ideology thresholds**: What ideology strength is needed to sustain a minority fork?
2. **Max loss tolerance**: How much loss can committed actors endure?
3. **Hashrate distribution**: Can a minority hashrate win through persistence?
4. **Economic distribution**: How does exchange support affect fork outcomes?
5. **User participation**: Do user nodes matter for fork selection?
6. **Difficulty dynamics**: How does difficulty adjustment affect fork competition?

### Key Scenarios to Explore

1. **Minority Persistence**: Can v27's committed 36% hashrate outlast v26's larger but less committed hashrate?

2. **Exchange Kingmaker**: If major exchanges (neutral) tip toward one fork, does that decide the outcome?

3. **User Last Stand**: If all professional miners leave, can ideological users sustain a chain through difficulty adjustment?

4. **Economic Consensus**: Does custody (HODLers) or volume (traders) have more influence on fork selection?

---

## Known Limitations and Future Enhancements

### Known Limitations

- **Casual user compression**: The 1:1,250 ratio for casual users vs. 1:400 for the broader network means their collective economic influence is underrepresented at the individual node level. Cohort-scaled custody figures should be used for economic weight calculations.
- **Custody figure staleness**: MicroStrategy and Grayscale figures in particular require updating. Use bitcointreasuries.net and exchange proof-of-reserves data before any publication.
- **Hashrate gap**: ~6.49% of network hashrate is explicitly unmodeled. This is intentional but should be noted in any analysis.
- **No cross-partition edges**: The two partitions are fully isolated by design. Pre-fork peering between the partitions is not modeled.
- **Static ideology**: `ideology_strength` values do not decay or evolve over simulation time — commitment is treated as fixed for the duration of a run.

### Future Enhancements

- [ ] Add `represents_count` and `representation_tier` fields to all Tier 2 nodes in network.yaml
- [ ] Update Tier 2 `custody_btc` values to cohort-scaled figures
- [ ] Add cross-partition edges to model pre-fork connected state
- [ ] Add more casual user nodes to reduce compression ratio toward the network average
- [ ] Add mining pool sub-nodes representing individual miners within pools
- [ ] Add geographic distribution metadata (US, EU, Asia-Pacific) to enable geographic partition scenarios
- [ ] Add Lightning Network node topology
- [ ] Add fee sensitivity parameters
- [ ] Add time-varying ideology (commitment decay over simulation rounds)
- [ ] Refresh custody and hashrate figures from live data sources on a regular cadence
