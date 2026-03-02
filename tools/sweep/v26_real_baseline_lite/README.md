# Baseline Sweep: Center-Point Variance Test

## Purpose

This sweep establishes **baseline variance** by running 30 scenarios with identical parameters but different random seeds. By holding all inputs constant at their center points, we isolate the stochastic variance inherent in the simulation from the variance caused by parameter changes.

**Key question:** How much do outcomes vary due to randomness alone, when all parameters are fixed?

This baseline enables:
1. **Confidence intervals** for exploratory sweep results
2. **Effect size calibration** — is a parameter's effect larger than random noise?
3. **Reproducibility verification** — same seed should produce same outcome

---

## Test Design

### Fixed Parameters (Center Points)

All parameters are set to the midpoint of their defined ranges:

| Parameter | Value | Range | Description |
|-----------|:-----:|:-----:|-------------|
| economic_split | 0.50 | 0.0–1.0 | Fraction of economic custody on v27 |
| hashrate_split | 0.50 | 0.0–1.0 | Fraction of initial hashrate on v27 |
| pool_ideology_strength | 0.50 | 0.1–0.9 | How much pools sacrifice for ideology |
| pool_profitability_threshold | 0.16 | 0.02–0.30 | Min profit advantage to switch |
| pool_max_loss_pct | 0.26 | 0.02–0.50 | Max revenue loss for ideology |
| pool_committed_split | 0.50 | 0.0–1.0 | Committed pool hashrate preferring v27 |
| pool_neutral_pct | 30.0 | 10–50 | Percentage of neutral/rational pools |
| econ_ideology_strength | 0.40 | 0.0–0.8 | Economic node ideology strength |
| econ_switching_threshold | 0.135 | 0.02–0.25 | Min price advantage to switch |
| econ_inertia | 0.175 | 0.05–0.30 | Switching friction |
| user_ideology_strength | 0.50 | 0.1–0.9 | User ideology strength |
| user_switching_threshold | 0.125 | 0.05–0.20 | Min price advantage for users |
| transaction_velocity | 0.50 | 0.1–0.9 | Fee-generating transaction rate |
| user_nodes_per_partition | 6 | 2–10 | User nodes per partition |
| economic_nodes_per_partition | 2 | 1–3 | Economic nodes per partition |
| solo_miner_hashrate | 0.085 | 0.02–0.15 | Hashrate per solo miner |

### Variable: Random Seed

Each scenario gets a unique random seed (1–30) which controls:
- Miner selection (weighted random by hashrate)
- Price fluctuation noise
- Switching decision timing (inertia-based delays)
- Any other stochastic elements in the simulation

### Network Configuration

| Setting | Value |
|---------|-------|
| Base Network | realistic-economy-lite |
| Total Nodes | 25 |
| Duration | 1800s (30 min) per scenario |
| Block Interval | 2s |
| Difficulty Retarget | 144 blocks (~5 min) |

---

## Expected Outcomes

With parameters at center points (50/50 economic and hashrate split), we expect:

1. **Balanced competition** — neither fork has a structural advantage
2. **High variance in outcomes** — close to 50/50 starting conditions should produce variable results
3. **Outcome distribution** — approximately equal v27/v26 wins, some contested

### Metrics to Measure

| Metric | Description |
|--------|-------------|
| **Win rate variance** | Standard deviation of v27 win rate |
| **Hashrate share distribution** | Range and spread of final v27 hashrate |
| **Reorg count distribution** | How much reorg activity varies by seed |
| **Outcome consistency** | How often identical parameters produce same outcome |

---

## Analysis Plan

After running all 30 scenarios:

### 1. Outcome Distribution
```
Expected: ~15 v27 wins, ~15 v26 wins (±√n uncertainty)
Measure: Actual distribution and 95% confidence interval
```

### 2. Variance Metrics
- Standard deviation of `v27_hashrate_share`
- Range of `total_reorgs`
- Coefficient of variation for key outputs

### 3. Baseline Thresholds

These establish the "noise floor" for parameter effects:

| Output | Baseline σ | Interpretation |
|--------|-----------|----------------|
| v27_hashrate_share | ? | Parameter effect must exceed this to be meaningful |
| total_reorgs | ? | Natural variation in cascade activity |
| v27_block_share | ? | Mining outcome variance |

### 4. Comparison with Exploratory Sweeps

| Sweep | Parameter Variance | Outcome Variance | Ratio |
|-------|-------------------|------------------|-------|
| **Baseline** | 0 (fixed) | σ_baseline | 1.0 |
| exploratory_sweep_lite | High (LHS) | σ_exploratory | σ_exp/σ_base |

If exploratory variance >> baseline variance, parameter effects are real.
If exploratory variance ≈ baseline variance, parameters have minimal effect.

---

## Running the Sweep

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools/sweep

# Full run (~15 hours)
python 3_run_sweep.py \
    --input baseline_sweep_lite/build_manifest.json \
    --duration 1800 \
    --retarget-interval 144

# Quick test (5 scenarios, 10 min each)
python 3_run_sweep.py \
    --input baseline_sweep_lite/build_manifest.json \
    --duration 600 \
    --retarget-interval 144 \
    --max-scenarios 5

# Dry run
python 3_run_sweep.py \
    --input baseline_sweep_lite/build_manifest.json \
    --dry-run
```

## Analyzing Results

```bash
# Generate analysis report
python 4_analyze_results.py --input baseline_sweep_lite/results

# Results will be in:
# baseline_sweep_lite/results/analysis/
#   ├── report.txt
#   ├── summary.json
#   ├── sweep_data.csv
#   └── correlations.json (should show ~0 for all params)
```

---

## Hypotheses

### H1: Balanced Parameters → Variable Outcomes
With 50/50 splits, outcomes should be highly sensitive to random factors.
- **Prediction:** Win rate between 35-65% for either fork
- **Validation:** Check outcome distribution

### H2: Seed Determines Outcome
Given the same seed, identical outcomes should result.
- **Prediction:** Re-running seed=1 produces same result
- **Validation:** Run one scenario twice with same seed

### H3: Baseline Variance < Exploratory Variance
Parameter variation should explain more variance than randomness.
- **Prediction:** σ(exploratory) > 2 × σ(baseline)
- **Validation:** Compare variance ratios

---

## Files

| File | Description |
|------|-------------|
| `baseline_scenarios.json` | 30 scenarios with center-point parameters |
| `build_manifest.json` | Full build configuration |
| `configs/pools/sweep_pools_config.yaml` | Pool configurations (identical for all) |
| `configs/economic/sweep_economic_config.yaml` | Economic configs (identical for all) |
| `networks/baseline_*/network.yaml` | Generated networks (identical structure) |

---

## Related Sweeps

| Sweep | Purpose | Comparison |
|-------|---------|------------|
| **baseline_sweep_lite** | Establish variance floor | — |
| exploratory_sweep_lite | Parameter exploration (LHS) | Compare variance |
| realistic_sweep3_rapid | Fixed-code validation | Compare thresholds |

---

*Created: February 2026*
