# Exploratory Sweep Analysis: realistic_sweep3_rapid

## Configuration

| Parameter | Value |
|-----------|-------|
| Scenarios | 50 (Latin Hypercube Sampling, seed=42) |
| Duration | 1800s per scenario |
| Block interval | 2s |
| Difficulty retarget | 144 blocks (~288s, ~6 retargets per run) |
| Network | realistic-economy-v2 |
| Manifest | `../realistic_sweep3/build_manifest.json` |
| Total runtime | ~27 hours |

## Outcome Distribution

| Outcome | Count | % |
|---------|-------|---|
| v27_dominant | 25 | 50.0% |
| v26_dominant | 22 | 44.0% |
| contested | 3 | 6.0% |

Outcome classification: v27_dominant = final v27 hashrate share > 65%, v26_dominant < 35%, contested = 35–65%.

## Parameter Correlations

### With v27 final hashrate share (primary outcome proxy)

| Rank | Parameter | Correlation | Direction |
|------|-----------|:-----------:|-----------|
| 1 | `economic_split` | +0.666 | higher → v27 wins |
| 2 | `hashrate_split` | +0.554 | higher → v27 wins |
| 3 | `pool_committed_split` | +0.360 | higher → v27 wins |
| 4 | `econ_switching_threshold` | +0.330 | higher → easier cascade |
| 5 | `econ_inertia` | -0.324 | lower → faster switching |
| 6 | `economic_nodes_per_partition` | -0.244 | fewer nodes → stronger price signal |
| 7 | `pool_ideology_strength` | +0.179 | |
| 8 | `user_ideology_strength` | +0.163 | |
| 9–14 | remaining params | < ±0.15 | weak / noise |

**Key result**: `economic_split` surpasses `hashrate_split` as the top predictor. The economic cascade mechanism is functioning — economic majority can overcome hashrate minority.

### With v27 economic share (cascade mechanism quality check)

| Parameter | Correlation |
|-----------|:-----------:|
| `economic_split` | +0.949 |
| `pool_neutral_pct` | -0.356 |
| `econ_ideology_strength` | +0.327 |
| `econ_inertia` | -0.309 |

The near-perfect +0.949 confirms that `economic_split` is correctly driving final economic allocation.

### With total reorgs (cascade intensity)

| Parameter | Correlation |
|-----------|:-----------:|
| `hashrate_split` | +0.411 |
| `pool_committed_split` | +0.376 |
| `economic_split` | +0.313 |
| `economic_nodes_per_partition` | -0.318 |

## Zone Analysis

2×2 grid partitioned at economic_split = 0.5 and hashrate_split = 0.5.

| Zone | n | v27 wins | contested | v26 wins |
|------|:-:|:--------:|:---------:|:--------:|
| low_hash + low_econ | 12 | 0 (0%) | 1 | 11 (92%) |
| low_hash + high_econ | 12 | 6 (50%) | 2 | 4 (33%) |
| high_hash + low_econ | 12 | 6 (50%) | 0 | 6 (50%) |
| **high_hash + high_econ** | **13** | **13 (100%)** | 0 | 0 |

**Observations:**
- When both hash and econ favor v27, v27 wins 100% of the time.
- When both favor v26, v26 wins 92% (1 contested anomaly).
- The conflict zones (low_hash + high_econ and high_hash + low_econ) each split ~50/50, indicating both factors contribute roughly equally.

## Key Finding: pool_committed_split as Economic Cascade Gatekeeper

In the 9 cases where v27 economic majority (>55%) opposed v26 hashrate majority (<45%), outcome was entirely determined by `pool_committed_split`:

| pool_committed_split | economic_split | reorgs | outcome |
|:--------------------:|:--------------:|:------:|---------|
| 0.138 | 0.885 | 0 | v26 wins — NO CASCADE |
| 0.327 | 0.641 | 0 | v26 wins — NO CASCADE |
| 0.425 | 0.581 | 0 | v26 wins — NO CASCADE |
| 0.508 | 0.623 | 7 | **CONTESTED** |
| 0.531 | 0.789 | 9 | v27 wins — CASCADE |
| 0.575 | 0.699 | 6 | v27 wins — CASCADE |
| 0.596 | 0.926 | 9 | v27 wins — CASCADE |
| 0.702 | 0.742 | 9 | v27 wins — CASCADE |
| 0.934 | 0.726 | 8 | v27 wins — CASCADE |

**Threshold: committed_split < ~0.43 blocks the cascade; > ~0.53 enables it.**

This held even when v27 had 88–93% economic majority — without enough committed v27 pools to hold the chain during price divergence, the economic signal cannot translate into hashrate control.

## Reorg Cascade Analysis

| Reorg level | Scenarios | v27 wins | v26 wins | contested |
|-------------|:---------:|:--------:|:--------:|:---------:|
| ≥ 5 reorgs (cascade) | 21 | 18 (86%) | 2 | 1 |
| 0 reorgs (no cascade) | 10 | 1 | 8 (80%) | 1 |

Cascade scenarios averaged: hashrate_split=0.574, economic_split=0.627. Absence of reorgs strongly predicts v26 dominance.

## Estimated Decision Thresholds

| Parameter | Threshold | v27 favored when |
|-----------|:---------:|------------------|
| `economic_split` | ~0.48 | higher |
| `hashrate_split` | ~0.50 | higher |
| `pool_committed_split` | ~0.49 | higher |
| `econ_inertia` | ~0.18 | lower |
| `econ_switching_threshold` | ~0.13 | higher |

## Notable Anomalies

### sweep_0007 — Reverse cascade (hash=0.90 v27, econ=0.07 v27 → v26 wins)
- v26 held 93% economic majority, driving neutral pools away from v27
- 7 reorgs, 437 orphans — largest orphan count in dataset
- Final state: v26 takes 100% hashrate despite v27 starting with 90%
- Mechanism: v26 economic cascade overwhelmed v27 hashrate advantage

### sweep_0045 — Clean hashrate win (hash=0.985 v27, econ=0.19 → v27 wins, 0 reorgs)
- Overwhelming starting hashrate dominance; no cascade needed
- v26 economic majority (81%) was insufficient to trigger reverse cascade at this hash ratio

### sweep_0020 — Maximum chaos (hash=0.84 v27, econ=0.24 → v26 wins, 13 reorgs)
- Most reorgs in dataset; econ_inertia=0.29 (high), economic_nodes_per_partition=1
- pool_committed_split=0.485 (near threshold) → prolonged instability
- v27 block share 55.5% but v26 wins final hashrate (71.5% v26)

## Parameter Means by Outcome

| Parameter | v27_dominant | contested | v26_dominant | separation |
|-----------|:------------:|:---------:|:------------:|:----------:|
| economic_split | 0.680 | 0.535 | 0.285 | 0.396 |
| hashrate_split | 0.654 | 0.368 | 0.335 | 0.319 |
| pool_committed_split | 0.599 | 0.559 | 0.385 | 0.214 |
| econ_inertia | 0.154 | 0.166 | 0.199 | 0.045 |
| economic_nodes_per_partition | 1.840 | 2.000 | 2.238 | 0.398 |

## Next Steps

This exploratory sweep established the key drivers and an estimated cascade threshold. Two follow-up sweeps are planned:

1. **targeted_sweep1_committed_threshold** *(running)*
   - Grid: `economic_split` [0.35, 0.50, 0.60, 0.70, 0.82] × `pool_committed_split` [0.20–0.75]
   - Fixed: `hashrate_split=0.25` (v26 hash dominant throughout)
   - Goal: precisely map the 2D cascade decision boundary

2. **Verification sweep** *(planned)*
   - Same config as this sweep but with longer duration (2016-block difficulty, realistic timing)
   - Goal: confirm findings hold at equilibrium, not just in short-run dynamics
