#!/bin/bash
# Fork Formation Threshold Sweep — Run Commands
# Generated 2026-07-03
# 90 scenarios across 2 servers x 6 namespaces each
# Run each command in a separate terminal on the appropriate server

# ============================================================
# SERVER 1
# ============================================================

# fft-0 — 8 scenarios (sweep_0000–sweep_0007)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-0 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 0 7))

# fft-1 — 8 scenarios (sweep_0008–sweep_0015)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-1 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 8 15))

# fft-2 — 8 scenarios (sweep_0016–sweep_0023)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-2 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 16 23))

# fft-3 — 7 scenarios (sweep_0024–sweep_0030)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-3 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 24 30))

# fft-4 — 7 scenarios (sweep_0031–sweep_0037)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-4 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 31 37))

# fft-5 — 7 scenarios (sweep_0038–sweep_0044)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-5 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 38 44))

# ============================================================
# SERVER 2
# ============================================================

# fft-0 — 8 scenarios (sweep_0045–sweep_0052)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-0 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 45 52))

# fft-1 — 8 scenarios (sweep_0053–sweep_0060)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-1 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 53 60))

# fft-2 — 8 scenarios (sweep_0061–sweep_0068)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-2 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 61 68))

# fft-3 — 7 scenarios (sweep_0069–sweep_0075)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-3 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 69 75))

# fft-4 — 7 scenarios (sweep_0076–sweep_0082)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-4 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 76 82))

# fft-5 — 7 scenarios (sweep_0083–sweep_0089)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-5 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 83 89))
