# Warnet Scenario Discovery — Bitcoin Fork Research

Independent research repository for studying Bitcoin soft fork governance using
realistic network simulations built on [Warnet](https://github.com/bitcoin-dev-tools/warnet).

---

## What This Is

This repository models a contested Bitcoin soft fork scenario — v27 (new rules,
strict) versus v26 (legacy, permissive) — and explores the conditions under which
neither side wins cleanly. Simulations run real `bitcoind` nodes on Kubernetes,
with agents representing mining pools, exchanges, institutions, and users making
independent, economically-motivated decisions.

---

## Key Documents

| Document | Purpose |
|----------|---------|
| **[Methodology.md](Methodology.md)** | How the simulation works: network design, entity models, decision processes, price oracle |
| **[tools/sweep/SCENARIO_DISCOVERY.md](tools/sweep/SCENARIO_DISCOVERY.md)** | Research plan: boundary mapping, boundary fitting, targeted LHS sampling |
| **[tools/sweep/SWEEP_FINDINGS.md](tools/sweep/SWEEP_FINDINGS.md)** | Results from completed parameter sweeps; decision boundary structure |
| **[docs/realistic_economy_model.md](docs/realistic_economy_model.md)** | Network calibration methodology and entity composition |
| **[docs/softfork_models.md](docs/softfork_models.md)** | Soft fork topology and asymmetric block propagation design |

---

## Repository Structure

```
warnetScenarioDiscovery/
├── Methodology.md                      # How the simulation works
├── scenarios/
│   ├── partition_miner_with_pools.py   # Main scenario script
│   ├── lib/                            # Oracles and strategy modules
│   │   ├── price_oracle.py
│   │   ├── fee_oracle.py
│   │   ├── mining_pool_strategy.py
│   │   ├── economic_node_strategy.py
│   │   ├── difficulty_oracle.py
│   │   └── reorg_oracle.py
│   └── config/
│       ├── mining_pools_config.yaml    # Pool scenarios
│       └── economic_nodes_config.yaml  # Economic/user node scenarios
│
├── networks/
│   ├── realistic-economy-v2/           # Full 60-node network (primary)
│   └── realistic-economy-lite/         # Lite 25-node network (faster runs)
│
├── networkGen/
│   └── scenario_network_generator.py   # Network YAML generator
│
├── tools/sweep/                        # Parameter sweep infrastructure
│   ├── SCENARIO_DISCOVERY.md           # Research plan (phases 1-4)
│   ├── SWEEP_FINDINGS.md               # Results and findings
│   ├── 1_generate_targeted.py          # Cartesian grid scenario generator
│   ├── 2_build_configs.py              # Build per-scenario configs
│   ├── 3_run_sweep.py                  # Execute sweep runs
│   ├── 4_analyze_results.py            # Analyze and summarize results
│   ├── 5_build_database.py             # Aggregate into SQLite database
│   └── specs/                          # Sweep specification files
│
└── docs/                               # Supporting documentation
```

---

## Running a Single Scenario

```bash
./run_scenario.sh scenarios/partition_miner_with_pools.py \
    --network-yaml networks/realistic-economy-v2/network.yaml \
    --pool-scenario realistic_current \
    --economic-scenario realistic_current \
    --duration 1800 \
    --enable-difficulty \
    --retarget-interval 20 \
    --results-id my-run-001
```

---

## Running a Parameter Sweep

```bash
# 1. Generate scenarios from a spec file
python3 tools/sweep/1_generate_targeted.py --spec tools/sweep/specs/<name>.yaml

# 2. Build per-scenario config files
python3 tools/sweep/2_build_configs.py \
    --input tools/sweep/<name>/scenarios.json \
    --output-dir tools/sweep/<name>

# 3. Run all scenarios sequentially
python3 tools/sweep/3_run_sweep.py \
    --input tools/sweep/<name>/build_manifest.json \
    --duration 1800 --interval 2

# 4. Analyze results
python3 tools/sweep/4_analyze_results.py \
    --input tools/sweep/<name>/results \
    --manifest tools/sweep/<name>/build_manifest.json

# 5. Add to database
python3 tools/sweep/5_build_database.py
```

---

## Current Research Status

See [tools/sweep/SCENARIO_DISCOVERY.md](tools/sweep/SCENARIO_DISCOVERY.md) for
the full three-phase research plan and current status.

| Phase | Status |
|-------|--------|
| Phase 1: Boundary mapping (targeted grid sweeps) | In progress |
| Phase 2: Boundary fitting (logistic, RF, PRIM) | Planned |
| Phase 3: Targeted LHS within transition zone | Planned |
| Phase 4: Analysis and reporting | Planned |

### Key findings so far

- **Primary driver**: `economic_split` (v27 custody fraction); threshold ~0.82 for clean v27 win
- **Gatekeeper**: `pool_committed_split`; non-monotonic interaction with `economic_split`
- **Non-causal**: `hashrate_split`, `pool_neutral_pct`, all user parameters — zero effect on outcomes
- **Inversion zone**: At `economic_split` = 0.60–0.70, v26 wins despite apparent v27 economic majority
- **Pool ideology**: Jointly determined by `ideology_strength × max_loss_pct`; diagonal threshold ~0.12

---

## Networks

Two networks are maintained. Both use identical mining pool configurations;
the lite network consolidates economic and user nodes into aggregate cohorts.

| Network | Nodes | Use case |
|---------|-------|----------|
| `realistic-economy-v2` | 60 | Primary; all sweeps |
| `realistic-economy-lite` | 25 | Faster iteration; equivalence validation |

---

## Requirements

- Warnet (Kubernetes-based Bitcoin testing framework)
- Python 3.8+
- `kubectl` with cluster access
- Bitcoin Core images: `27.0`, `26.0`
