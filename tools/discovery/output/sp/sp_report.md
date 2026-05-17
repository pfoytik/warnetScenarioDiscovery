# Scenario Potential Report — SP_pools and SP_economic

**Dataset:** n=590 scenarios, 15 sweeps, 2016-block retarget
**RF OOB accuracy:** 79.8%

## Score Distributions

| Score | Mean | Median | Max | Std |
|-------|:----:|:------:|:---:|:---:|
| sp_pools | 0.130 | 0.053 | 1.000 | 0.191 |
| sp_economic | 0.066 | 0.005 | 1.000 | 0.140 |
| z_joint | 0.364 | 0.308 | 1.918 | 0.303 |
| surprise | 0.091 | 0.029 | 1.048 | 0.144 |

## Mean SP by Outcome

| Outcome | n | Mean SP_pools | Mean SP_economic | Mean Z_joint |
|---------|:-:|:-------------:|:----------------:|:------------:|
| v27_dominant | 271 | 0.124 | 0.073 | 0.514 |
| v26_dominant | 264 | 0.138 | 0.054 | 0.229 |
| contested | 55 | 0.121 | 0.095 | 0.266 |

## Top-10 Scenarios by Joint Governance Leverage (Z_joint)

| Rank | Sweep | Scenario | E | C | I | M | Outcome | SP_pools | SP_econ | Z_joint |
|:----:|-------|----------|:-:|:-:|:-:|:-:|---------|:--------:|:-------:|:-------:|
| 1 | targeted_sweep7_esp_2016 | sweep_0007 | 0.780 | 0.214 | 0.510 | 0.260 | v27_dominant | 0.719 | 0.966 | 1.918 |
| 2 | lhs_2016_full_phase3_merged | sweep_0117 | 0.761 | 0.247 | 0.582 | 0.196 | v26_dominant | 0.948 | 0.903 | 1.902 |
| 3 | committed_2016_high_econ | sweep_0000 | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.696 | 1.000 | 1.785 |
| 4 | committed_2016_sigmoid | sweep_0000 | 0.780 | 0.200 | 0.510 | 0.260 | v26_dominant | 0.696 | 1.000 | 1.785 |
| 5 | lhs_2016_full_phase3_merged | sweep_0026 | 0.753 | 0.245 | 0.696 | 0.327 | v26_dominant | 0.553 | 0.862 | 1.455 |
| 6 | lhs_2016_full_phase3_merged | sweep_0101 | 0.671 | 0.260 | 0.520 | 0.240 | v27_dominant | 1.000 | 0.194 | 1.439 |
| 7 | lhs_2016_full_phase3_merged | sweep_0242 | 0.772 | 0.234 | 0.753 | 0.260 | v27_dominant | 0.156 | 0.917 | 1.301 |
| 8 | lhs_2016_6param | sweep_0101 | 0.647 | 0.260 | 0.409 | 0.131 | v27_dominant | 0.916 | 0.036 | 1.296 |
| 9 | lhs_2016_full_phase3_merged | sweep_0161 | 0.696 | 0.248 | 0.522 | 0.272 | v27_dominant | 0.813 | 0.209 | 1.283 |
| 10 | lhs_2016_full_phase3_merged | sweep_0215 | 0.666 | 0.348 | 0.721 | 0.174 | v27_dominant | 0.103 | 0.904 | 1.278 |

## Top-10 Surprise Scenarios (high leverage, clean resolution)

These scenarios had high governance leverage available but resolved
decisively anyway — the 'least expected' outcomes.

| Rank | Sweep | Scenario | E | C | Outcome | Z_joint | Surprise |
|:----:|-------|----------|:-:|:-:|---------|:-------:|:--------:|
| 1 | targeted_sweep7_esp_2016 | sweep_0007 | 0.780 | 0.214 | v27_dominant | 1.918 | 1.048 |
| 2 | lhs_2016_full_phase3_merged | sweep_0117 | 0.761 | 0.247 | v26_dominant | 1.902 | 0.862 |
| 3 | lhs_2016_full_phase3_merged | sweep_0021 | 0.709 | 0.164 | v27_dominant | 1.132 | 0.808 |
| 4 | lhs_2016_full_phase3_merged | sweep_0161 | 0.696 | 0.248 | v27_dominant | 1.283 | 0.796 |
| 5 | lhs_2016_full_phase3_merged | sweep_0242 | 0.772 | 0.234 | v27_dominant | 1.301 | 0.785 |
| 6 | econ_committed_2016_grid | sweep_0018 | 0.600 | 0.200 | v27_dominant | 0.993 | 0.682 |
| 7 | lhs_2016_full_phase3_merged | sweep_0218 | 0.733 | 0.158 | v27_dominant | 1.135 | 0.651 |
| 8 | targeted_sweep10_econ_threshold_2016 | sweep_0001 | 0.500 | 0.350 | v27_dominant | 0.865 | 0.616 |
| 9 | targeted_sweep10_econ_threshold_2016 | sweep_0000 | 0.350 | 0.350 | v27_dominant | 0.877 | 0.611 |
| 10 | lhs_2016_6param | sweep_0092 | 0.495 | 0.159 | v27_dominant | 0.768 | 0.594 |

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