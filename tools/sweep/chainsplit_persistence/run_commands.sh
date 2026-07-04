#!/bin/bash
# Chainsplit Persistence Sweep — Run Commands
# 36 scenarios across 2 servers x 6 namespaces each (3 scenarios per namespace)
# Worst case: 3 x 3.6h = 10.8h per namespace (under 12h)

# ============================================================
# SERVER 1 (sweep_0000–sweep_0017)
# ============================================================

# csp-0 — 3 scenarios (sweep_0000–sweep_0002)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-0 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 0 2))

# csp-1 — 3 scenarios (sweep_0003–sweep_0005)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-1 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 3 5))

# csp-2 — 3 scenarios (sweep_0006–sweep_0008)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-2 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 6 8))

# csp-3 — 3 scenarios (sweep_0009–sweep_0011)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-3 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 9 11))

# csp-4 — 3 scenarios (sweep_0012–sweep_0014)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-4 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 12 14))

# csp-5 — 3 scenarios (sweep_0015–sweep_0017)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-5 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 15 17))

# ============================================================
# SERVER 2 (sweep_0018–sweep_0035)
# ============================================================

# csp-0 — 3 scenarios (sweep_0018–sweep_0020)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-0 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 18 20))

# csp-1 — 3 scenarios (sweep_0021–sweep_0023)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-1 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 21 23))

# csp-2 — 3 scenarios (sweep_0024–sweep_0026)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-2 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 24 26))

# csp-3 — 3 scenarios (sweep_0027–sweep_0029)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-3 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 27 29))

# csp-4 — 3 scenarios (sweep_0030–sweep_0032)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-4 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 30 32))

# csp-5 — 3 scenarios (sweep_0033–sweep_0035)
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 \
  --interval 2 \
  --retarget-interval 2016 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-5 \
  --startup-wait 60 \
  --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 33 35))

