# Balanced Baseline Network

A perfectly symmetric network for measuring stochastic variance at the decision boundary. Neither v27 nor v26 has any structural advantage.

## Purpose

The realistic-economy-lite network has structural biases favoring v26:
- **Hashrate**: V26 has 57.2% vs V27's 40.95%
- **Economic weight**: V26 exchanges have more custody (2.83M vs 2.14M BTC)

This balanced network eliminates these biases so that:
1. Parameter sweeps test behavioral dynamics, not network structure
2. Outcomes at center-point parameters should be truly 50/50
3. Stochastic variance can be measured without structural confounds

## Network Structure

| Component | V27 | V26 | Notes |
|-----------|:---:|:---:|-------|
| Mining Pools | 4 | 4 | Symmetric distribution |
| Pool Hashrate | 47% | 47% | 20% + 14% + 8% + 5% each |
| Economic Nodes | 2 | 2 | Identical custody amounts |
| User Nodes | 6 | 6 | Mirror structure |
| User Hashrate | 3% | 3% | 1.5% + 1.5% + 0% each |
| **Total Hashrate** | **50%** | **50%** | Perfect balance |

### Mining Pool Distribution

Each side has 4 pools with identical hashrate allocation:

| Pool | Hashrate | Ideology | Profitability Threshold |
|------|:--------:|:--------:|:-----------------------:|
| Large (Alpha/Epsilon) | 20% | 0.60 | 0.16 |
| Medium (Beta/Zeta) | 14% | 0.55 | 0.14 |
| Small (Gamma/Eta) | 8% | 0.50 | 0.12 |
| Tiny (Delta/Theta) | 5% | 0.45 | 0.10 |

### Economic Node Distribution

Each side has 2 economic aggregates:

| Node | Custody | Volume | Ideology |
|------|:-------:|:------:|:--------:|
| Exchanges & Institutions | 1.8M BTC | 200K/day | 0.40 |
| Merchants & Payments | 200K BTC | 20K/day | 0.40 |

### User Distribution

Each side has 6 user nodes:

| Role | Hashrate | Ideology | Fork Preference |
|------|:--------:|:--------:|:---------------:|
| Developers & Node Runners | 1.5% | 0.50 | partisan |
| Mining Hobbyists | 1.5% | 0.50 | partisan |
| Active Traders | 0% | 0.15 | neutral |
| HODLers | 0% | 0.50 | partisan |
| Spenders | 0% | 0.15 | neutral |
| Newbies | 0% | 0.10 | neutral |

## Behavioral Parameters

All behavioral parameters are set at center-point values:

| Parameter | Value |
|-----------|:-----:|
| pool_ideology_strength | 0.45-0.60 range |
| pool_profitability_threshold | 0.10-0.16 range |
| econ_ideology_strength | 0.40 |
| econ_switching_threshold | 0.135 |
| econ_inertia | 0.175 |
| user_ideology_strength | 0.10-0.50 range |
| user_switching_threshold | 0.03-0.125 range |

## Usage

### Running a baseline sweep

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery/tools/sweep

# Generate baseline scenarios with center-point parameters
python 1_generate_baseline.py \
    --network balanced-baseline \
    --output balanced_baseline_sweep \
    --seeds 30

# Build configurations
python 2_build_configs.py \
    --input balanced_baseline_sweep/baseline_scenarios.json \
    --network balanced-baseline

# Run the sweep
python 3_run_sweep.py \
    --input balanced_baseline_sweep/build_manifest.json \
    --duration 1800 \
    --retarget-interval 144
```

## Comparison with Realistic Network

| Metric | realistic-economy-lite | balanced-baseline |
|--------|:----------------------:|:-----------------:|
| Total Nodes | 25 | 24 |
| V27 Hashrate | 40.95% | 50% |
| V26 Hashrate | 57.2% | 50% |
| V27 Economic Share | ~43% | 50% |
| Expected Outcome (center-point) | 100% v26 | 50/50 |

## Files

| File | Description |
|------|-------------|
| `network.yaml` | Network definition with 24 symmetric nodes |

---

*Created: March 2026*
