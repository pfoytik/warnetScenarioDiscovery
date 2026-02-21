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

The partition split is balanced by node count, but economic weight and hashrate distribution vary based on each node's metadata.

---

## Category Details

### Mining Pools (8 nodes)

Mining pools control the hashrate and produce blocks. Their fork decisions are driven by profitability calculations that factor in price, difficulty, and ideology.

| Pool | Hashrate | Fork Pref | Ideology | Max Loss | Notes |
|------|----------|-----------|----------|----------|-------|
| Foundry USA | 26.89% | v27 | 0.95 | 50% | True believer, committed |
| MARA Pool | 4.85% | v27 | 0.70 | 30% | Strong v27 preference |
| Luxor | 3.12% | v27 | 0.65 | 25% | Moderate v27 |
| Ocean | 1.42% | v27 | 0.85 | 40% | Ideological, decentralization focus |
| AntPool | 19.25% | v26 | 0.65 | 40% | Strong v26 preference |
| F2Pool | 11.25% | v26 | 0.55 | 28% | Moderate v26 |
| ViaBTC | 11.39% | v26 | 0.60 | 35% | Moderate v26 |
| Binance Pool | 10.04% | v26 | 0.45 | 22% | More rational, follows profit |

**Total Hashrate Distribution:**
- v27: ~36.28% (Foundry + MARA + Luxor + Ocean)
- v26: ~51.93% (AntPool + F2Pool + ViaBTC + Binance Pool)
- User/Solo: ~0.09% (power users with small hashrate)

### Major Exchanges (4 nodes)

Major exchanges are mostly neutral and highly responsive to price signals. They have enormous custody and volume, making them critical for price discovery.

| Exchange | Custody BTC | Daily Volume | Fork Pref | Ideology | Inertia |
|----------|-------------|--------------|-----------|----------|---------|
| Coinbase | 1,000,000 | 150,000 | neutral | 0.10 | 0.20 |
| Kraken | 600,000 | 80,000 | neutral | 0.15 | 0.18 |
| Binance | 1,500,000 | 250,000 | neutral | 0.05 | 0.22 |
| Bitfinex | 400,000 | 60,000 | neutral | 0.12 | 0.18 |

**Key Characteristics:**
- Low ideology (0.05-0.15) - follow market signals
- High inertia (0.18-0.22) - switching costs are significant
- Low max_loss_pct (0.04-0.06) - won't tolerate large disadvantages

### Mid-tier Exchanges (6 nodes)

Regional and specialized exchanges with moderate volume. Slightly more ideological than major exchanges.

| Exchange | Custody BTC | Daily Volume | Fork Pref | Ideology |
|----------|-------------|--------------|-----------|----------|
| Gemini | 200,000 | 25,000 | v27 | 0.30 |
| River | 80,000 | 10,000 | v27 | 0.50 |
| Swan Bitcoin | 50,000 | 8,000 | v27 | 0.60 |
| OKX | 300,000 | 45,000 | v26 | 0.25 |
| Bybit | 150,000 | 30,000 | v26 | 0.20 |
| Huobi | 100,000 | 20,000 | v26 | 0.22 |

### Payment Processors (3 nodes)

Payment infrastructure that enables Bitcoin commerce. Higher transaction velocity, moderate ideology.

| Processor | Custody BTC | Daily Volume | Fork Pref | Ideology |
|-----------|-------------|--------------|-----------|----------|
| BTCPay Server | 5,000 | 15,000 | v27 | 0.75 |
| OpenNode | 3,000 | 5,000 | v27 | 0.65 |
| BitPay | 8,000 | 20,000 | v26 | 0.35 |

### Merchants (6 nodes)

Companies accepting Bitcoin for goods/services. Lower custody, focused on transaction flow.

| Merchant | Custody BTC | Daily Volume | Fork Pref | Ideology |
|----------|-------------|--------------|-----------|----------|
| Tech Retailer | 500 | 200 | v27 | 0.40 |
| E-commerce | 300 | 150 | neutral | 0.20 |
| Travel Agency | 200 | 100 | v27 | 0.35 |
| Overstock | 800 | 300 | v26 | 0.30 |
| Newegg | 400 | 180 | neutral | 0.18 |
| AT&T | 250 | 120 | v26 | 0.15 |

### Institutional Holders (5 nodes)

Corporate treasuries and funds. High custody, low velocity (HODLing strategy).

| Institution | Custody BTC | Daily Volume | Fork Pref | Ideology |
|-------------|-------------|--------------|-----------|----------|
| MicroStrategy | 190,000 | 500 | v27 | 0.85 |
| Tesla | 10,000 | 100 | neutral | 0.20 |
| Block Inc | 8,000 | 200 | v27 | 0.70 |
| Grayscale | 620,000 | 2,000 | neutral | 0.15 |
| Fidelity Digital | 150,000 | 800 | neutral | 0.12 |

**Key Characteristics:**
- Very low transaction velocity (0.02-0.08)
- High inertia - institutional processes are slow
- Mixed ideology - some true believers, some purely financial

### Power Users (12 nodes)

Developers, node runners, miners, and enthusiasts. High ideology, small individual holdings, some contribute hashrate.

| User Type | Custody BTC | Hashrate | Fork Pref | Ideology |
|-----------|-------------|----------|-----------|----------|
| Developer | 100 | 0.001% | v27 | 0.90 |
| Node Runner | 50 | 0.002% | v27 | 0.85 |
| Bitcoin Educator | 25 | 0.0005% | v27 | 0.80 |
| Active Trader | 200 | 0% | neutral | 0.15 |
| Mining Hobbyist | 15 | 0.01% | v27 | 0.75 |
| Privacy Advocate | 30 | 0.0005% | v27 | 0.88 |
| BCH Supporter | 80 | 0.002% | v26 | 0.88 |
| Big Blocker | 40 | 0.001% | v26 | 0.82 |
| Exchange Arbitrageur | 150 | 0% | neutral | 0.05 |
| Mining Farm Operator | 500 | 0.05% | v26 | 0.55 |
| OTC Desk Operator | 1,000 | 0% | neutral | 0.10 |
| Lightning Node Op | 20 | 0.0005% | v26 | 0.45 |

**Key Characteristics:**
- Small individual holdings but high collective influence
- Some contribute mining hashrate (solo mining)
- High ideology variance - from arbitrageurs (0.05) to advocates (0.90)

### Casual Users (16 nodes)

General Bitcoin holders with varying engagement levels. Represent the "long tail" of Bitcoin ownership.

| User Type | Custody BTC | Daily Volume | Fork Pref | Ideology |
|-----------|-------------|--------------|-----------|----------|
| Long-term HODLer (x2) | 8-10 | 0.01 | v27/v26 | 0.55-0.70 |
| DCA Investor (x2) | 4-5 | 0.04-0.05 | neutral | 0.25-0.30 |
| Occasional Spender (x2) | 1.5-2 | 0.08-0.1 | neutral/v26 | 0.15-0.20 |
| Newbie (x2) | 0.3-0.5 | 0.01-0.02 | neutral | 0.03-0.05 |
| Remittance User (x2) | 0.15-0.2 | 0.4-0.5 | neutral/v26 | 0.10-0.12 |
| Savings Account (x2) | 2.5-3 | 0.008-0.01 | v27/v26 | 0.38-0.45 |
| Gift Recipient (x2) | 0.08-0.1 | 0.003-0.005 | neutral | 0.02 |
| Speculator | 1 | 0.5 | neutral | 0.08 |
| Curious Experimenter | 0.05 | 0.01 | v26 | 0.15 |

**Key Characteristics:**
- Low individual holdings but ~25% of total supply collectively
- Low transaction velocity (mostly HODLing)
- Low-to-moderate ideology
- One user has tiny hashrate (0.0001%) - the "curious experimenter"

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
| Casual Users | ~38 | <0.01% |

*Based on ~19.5M total BTC supply

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
| Casual Users | ~1.7 | <0.01% |

---

## Fork Preference Summary

### Initial Distribution

| Fork | Nodes | Hashrate | Economic Weight |
|------|-------|----------|-----------------|
| v27 preference | 22 | 36.3% | ~47% of custody |
| v26 preference | 21 | 51.9% | ~35% of custody |
| Neutral | 17 | 0% | ~18% of custody |

### Ideology Distribution

| Ideology Range | Description | Count |
|----------------|-------------|-------|
| 0.80 - 1.00 | True believers | 8 |
| 0.60 - 0.79 | Strong preference | 9 |
| 0.40 - 0.59 | Moderate preference | 10 |
| 0.20 - 0.39 | Weak preference | 12 |
| 0.00 - 0.19 | Rational/follows profit | 21 |

---

## Node Metadata Schema

Each node includes the following metadata fields:

```yaml
metadata:
  # Identity
  role: mining_pool | major_exchange | exchange | payment_processor | merchant | institutional | power_user | casual_user
  node_type: mining_pool | economic | user
  entity_id: unique identifier

  # Economic weight
  hashrate_pct: 0.0 - 100.0  # Mining power (pools and some users)
  custody_btc: float         # BTC holdings
  daily_volume_btc: float    # Transaction activity

  # Fork behavior
  fork_preference: v27 | v26 | neutral
  ideology_strength: 0.0 - 1.0      # Commitment to preference
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

## Future Enhancements

- [ ] Add more casual user nodes to represent the long tail
- [ ] Add mining pool "sub-nodes" representing individual miners
- [ ] Add geographic distribution metadata
- [ ] Add Lightning Network node topology
- [ ] Add fee sensitivity parameters
- [ ] Add time-varying ideology (commitment decay)
