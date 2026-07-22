#!/bin/bash
# Run lhs_2016_timing_swap — Server 1 (sweep_0000–sweep_0149, ns-0 through ns-5)
#
# TIMING SWAP: pool_decision_interval=1800s (was 600), econ_switching_cooldown=600s (was 1800)
# Tests whether the two-layer ordering (hashrate-first, econ-second) is a timing artifact.
#
# Prerequisites on this server:
#   kubectl create namespace ns-0
#   kubectl create namespace ns-1
#   kubectl create namespace ns-2
#   kubectl create namespace ns-3
#   kubectl create namespace ns-4
#   kubectl create namespace ns-5
#
# Rsync command (run from local machine before starting):
#   rsync -av tools/sweep/lhs_2016_timing_swap/ server1:~/warnetScenarioDiscovery/tools/sweep/lhs_2016_timing_swap/
#   rsync -av tools/sweep/configs/timing_swap_run.yaml server1:~/warnetScenarioDiscovery/tools/sweep/configs/

set -e
SWEEP_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SWEEP_DIR/../../.." && pwd)"
MANIFEST="$SWEEP_DIR/build_manifest.json"
CONFIG="$REPO_ROOT/tools/sweep/configs/timing_swap_run.yaml"
RESULTS="$SWEEP_DIR/results_server1"

BASE_CMD="python $REPO_ROOT/tools/sweep/3_run_sweep.py \
  --input $MANIFEST \
  --scenario-config $CONFIG \
  --results-dir $RESULTS"

echo "=== lhs_2016_timing_swap — Server 1 ==="
echo "Manifest:  $MANIFEST"
echo "Config:    $CONFIG"
echo "Results:   $RESULTS"
echo "Scenarios: sweep_0000–sweep_0149 (6 namespaces × 25 scenarios)"
echo ""

# Launch all 6 namespaces in parallel (background)

echo "[ns-0] Launching sweep_0000–sweep_0024..."
$BASE_CMD --namespace ns-0 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(0,25)))") \
  > "$RESULTS/ns-0.log" 2>&1 &

echo "[ns-1] Launching sweep_0025–sweep_0049..."
$BASE_CMD --namespace ns-1 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(25,50)))") \
  > "$RESULTS/ns-1.log" 2>&1 &

echo "[ns-2] Launching sweep_0050–sweep_0074..."
$BASE_CMD --namespace ns-2 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(50,75)))") \
  > "$RESULTS/ns-2.log" 2>&1 &

echo "[ns-3] Launching sweep_0075–sweep_0099..."
$BASE_CMD --namespace ns-3 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(75,100)))") \
  > "$RESULTS/ns-3.log" 2>&1 &

echo "[ns-4] Launching sweep_0100–sweep_0124..."
$BASE_CMD --namespace ns-4 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(100,125)))") \
  > "$RESULTS/ns-4.log" 2>&1 &

echo "[ns-5] Launching sweep_0125–sweep_0149..."
$BASE_CMD --namespace ns-5 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(125,150)))") \
  > "$RESULTS/ns-5.log" 2>&1 &

echo ""
echo "All 6 namespaces launched. Monitor with:"
echo "  tail -f $RESULTS/ns-*.log"
echo "  kubectl get pods -n ns-0"
echo ""
echo "Expected runtime: ~100 hours wall-clock (25 scenarios × ~4h per scenario)"
wait
echo "=== Server 1 complete ==="
