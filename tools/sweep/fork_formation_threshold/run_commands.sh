#!/bin/bash
# Fork Formation Threshold Sweep — Run Commands
# Generated 2026-07-03
# 90 scenarios across 2 servers x 6 namespaces each
# Run each command in a separate terminal on the appropriate server

# ============================================================
# SERVER 1
# ============================================================

# fft-0 — 8 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-0 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0000 sweep_0006 sweep_0012 sweep_0018 sweep_0024 sweep_0030 sweep_0036 sweep_0042

# fft-1 — 8 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-1 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0001 sweep_0007 sweep_0013 sweep_0019 sweep_0025 sweep_0031 sweep_0037 sweep_0043

# fft-2 — 8 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-2 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0002 sweep_0008 sweep_0014 sweep_0020 sweep_0026 sweep_0032 sweep_0038 sweep_0044

# fft-3 — 7 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-3 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0003 sweep_0009 sweep_0015 sweep_0021 sweep_0027 sweep_0033 sweep_0039

# fft-4 — 7 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-4 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0004 sweep_0010 sweep_0016 sweep_0022 sweep_0028 sweep_0034 sweep_0040

# fft-5 — 7 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server1 \
  --namespace fft-5 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0005 sweep_0011 sweep_0017 sweep_0023 sweep_0029 sweep_0035 sweep_0041

# ============================================================
# SERVER 2
# ============================================================

# fft-0 — 8 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-0 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0045 sweep_0051 sweep_0057 sweep_0063 sweep_0069 sweep_0075 sweep_0081 sweep_0087

# fft-1 — 8 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-1 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0046 sweep_0052 sweep_0058 sweep_0064 sweep_0070 sweep_0076 sweep_0082 sweep_0088

# fft-2 — 8 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-2 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0047 sweep_0053 sweep_0059 sweep_0065 sweep_0071 sweep_0077 sweep_0083 sweep_0089

# fft-3 — 7 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-3 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0048 sweep_0054 sweep_0060 sweep_0066 sweep_0072 sweep_0078 sweep_0084

# fft-4 — 7 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-4 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0049 sweep_0055 sweep_0061 sweep_0067 sweep_0073 sweep_0079 sweep_0085

# fft-5 — 7 scenarios
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
  --duration 13000 \
  --interval 10 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/fork_formation_threshold/results_server2 \
  --namespace fft-5 \
  --startup-wait 60 \
  --cooldown 30 \
  --scenarios sweep_0050 sweep_0056 sweep_0062 sweep_0068 sweep_0074 sweep_0080 sweep_0086

