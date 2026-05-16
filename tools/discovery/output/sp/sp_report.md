# Scenario Potential Report — SP_pools and SP_economic

**Dataset:** n=590 scenarios, 15 sweeps, 2016-block retarget
**RF OOB accuracy:** 79.8%

## Score Distributions

| Score | Mean | Median | Max | Std |
|-------|:----:|:------:|:---:|:---:|
| sp_pools | 0.102 | 0.039 | 1.000 | 0.163 |
| sp_economic | 0.064 | 0.003 | 1.000 | 0.124 |
| z_joint | 0.333 | 0.282 | 1.912 | 0.280 |
| surprise | 0.086 | 0.027 | 1.045 | 0.141 |

## Mean SP by Outcome

| Outcome | n | Mean SP_pools | Mean SP_economic | Mean Z_joint |
|---------|:-:|:-------------:|:----------------:|:------------:|
| v27_dominant | 271 | 0.100 | 0.082 | 0.499 |
| v26_dominant | 264 | 0.106 | 0.038 | 0.182 |
| contested | 55 | 0.094 | 0.101 | 0.244 |

## Top-10 Scenarios by Joint Governance Leverage (Z_joint)

| Rank | Sweep | Scenario | E | C | I | M | Outcome | SP_pools | SP_econ | Z_joint |
|:----:|-------|----------|:-:|:-:|:-:|:-:|---------|:--------:|:-------:|:-------:|
| 1 | targeted_sweep7_esp_2016 | sweep_0007 | 0.780 | 0.214 | 0.510 | 0.260 | v27_dominant | 0.868 | 0.812 | 1.912 |
| 2 | lhs_2016_full_phase3_merged | sweep_0161 | 0.696 | 0.248 | 0.522 | 0.272 | v27_dominant | 0.908 | 0.384 | 1.553 |
| 3 | lhs_2016_full_phase3_merged | sweep_0294 | 0.693 | 0.252 | 0.653 | 0.176 | v26_dominant | 1.000 | 0.480 | 1.508 |
| 4 | lhs_2016_full_phase3_merged | sweep_0117 | 0.761 | 0.247 | 0.582 | 0.196 | v26_dominant | 0.801 | 0.484 | 1.337 |
| 5 | econ_committed_2016_grid | sweep_0018 | 0.600 | 0.200 | 0.510 | 0.260 | v27_dominant | 0.647 | 0.438 | 1.302 |
| 6 | lhs_2016_full_phase3_merged | sweep_0242 | 0.772 | 0.234 | 0.753 | 0.260 | v27_dominant | 0.051 | 1.000 | 1.280 |
| 7 | committed_2016_high_econ | sweep_0000 | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.848 | 0.316 | 1.254 |
| 8 | committed_2016_sigmoid | sweep_0000 | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.848 | 0.316 | 1.254 |
| 9 | lhs_2016_full_phase3_merged | sweep_0215 | 0.666 | 0.348 | 0.721 | 0.174 | v27_dominant | 0.044 | 0.917 | 1.232 |
| 10 | lhs_2016_6param | sweep_0026 | 0.426 | 0.261 | 0.655 | 0.117 | v27_dominant | 0.868 | 0.000 | 1.224 |

## Top-10 Surprise Scenarios (high leverage, clean resolution)

These scenarios had high governance leverage available but resolved
decisively anyway — the 'least expected' outcomes.

| Rank | Sweep | Scenario | E | C | Outcome | Z_joint | Surprise |
|:----:|-------|----------|:-:|:-:|---------|:-------:|:--------:|
| 1 | targeted_sweep7_esp_2016 | sweep_0007 | 0.780 | 0.214 | v27_dominant | 1.912 | 1.045 |
| 2 | lhs_2016_full_phase3_merged | sweep_0161 | 0.696 | 0.248 | v27_dominant | 1.553 | 0.964 |
| 3 | econ_committed_2016_grid | sweep_0018 | 0.600 | 0.200 | v27_dominant | 1.302 | 0.894 |
| 4 | lhs_2016_full_phase3_merged | sweep_0242 | 0.772 | 0.234 | v27_dominant | 1.280 | 0.772 |
| 5 | lhs_2016_full_phase3_merged | sweep_0218 | 0.733 | 0.158 | v27_dominant | 1.213 | 0.695 |
| 6 | lhs_2016_6param | sweep_0092 | 0.495 | 0.159 | v27_dominant | 0.889 | 0.688 |
| 7 | lhs_2016_full_phase3_merged | sweep_0294 | 0.693 | 0.252 | v26_dominant | 1.508 | 0.657 |
| 8 | lhs_2016_full_phase3_merged | sweep_0025 | 0.656 | 0.346 | contested | 0.964 | 0.635 |
| 9 | lhs_2016_full_phase3_merged | sweep_0021 | 0.709 | 0.164 | v27_dominant | 0.877 | 0.625 |
| 10 | lhs_2016_full_phase3_merged | sweep_0117 | 0.761 | 0.247 | v26_dominant | 1.337 | 0.606 |

## Structural Notes

**SP_pools** peaks near pool_committed_split ≈ 0.296 (Phase 3 transition threshold)
and ≈ 0.214 (Foundry flip-point). It is computed as the RF probability gradient
|dP(v27_win)/d(pool_committed_split)| — how rapidly the predicted outcome changes
with a small shift in committed pool hashrate.

**SP_economic** is gated to zero outside the inversion zone [0.50, 0.82].
Outside this range the outcome is structurally determined regardless of exchange
or custodian custody decisions. Within the zone it peaks near the ESP (≈0.74),
where a small shift in economic custody crosses the self-sustaining threshold.

**Surprise** = Z_joint × (1 - outcome_certainty). High surprise identifies
scenarios where governance leverage was structurally available but dynamics
resolved cleanly — counterintuitive outcomes from the actor leverage perspective.