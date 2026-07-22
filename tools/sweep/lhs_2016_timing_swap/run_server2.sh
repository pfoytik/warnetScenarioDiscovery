#!/bin/bash
# Run lhs_2016_timing_swap — Server 2 (sweep_0150–sweep_0299, ns-6 through ns-11)
#
# TIMING SWAP: pool_decision_interval=1800s (was 600), econ_switching_cooldown=600s (was 1800)
# Tests whether the two-layer ordering (hashrate-first, econ-second) is a timing artifact.
#
# Prerequisites on this server:
#   kubectl create namespace ns-6
#   kubectl create namespace ns-7
#   kubectl create namespace ns-8
#   kubectl create namespace ns-9
#   kubectl create namespace ns-10
#   kubectl create namespace ns-11
#
# Rsync command (run from local machine before starting):
#   rsync -av tools/sweep/lhs_2016_timing_swap/ server2:~/warnetScenarioDiscovery/tools/sweep/lhs_2016_timing_swap/
#   rsync -av tools/sweep/configs/timing_swap_run.yaml server2:~/warnetScenarioDiscovery/tools/sweep/configs/

SWEEP_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SWEEP_DIR/../../.." && pwd)"
MANIFEST="$SWEEP_DIR/build_manifest.json"
CONFIG="$REPO_ROOT/tools/sweep/configs/timing_swap_run.yaml"
RESULTS="$SWEEP_DIR/results_server2"

BASE_CMD="python $REPO_ROOT/tools/sweep/3_run_sweep.py \
  --input $MANIFEST \
  --scenario-config $CONFIG \
  --results-dir $RESULTS"

mkdir -p "$RESULTS"

echo "=== lhs_2016_timing_swap — Server 2 ==="
echo "Manifest:  $MANIFEST"
echo "Config:    $CONFIG"
echo "Results:   $RESULTS"
echo "Scenarios: sweep_0150–sweep_0299 (6 namespaces × 25 scenarios)"
echo ""

# Launch all 6 namespaces in parallel (background)

echo "[ns-6] Launching sweep_0150–sweep_0174..."
$BASE_CMD --namespace ns-6 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(150,175)))") \
  > "$RESULTS/ns-6.log" 2>&1 &

echo "[ns-7] Launching sweep_0175–sweep_0199..."
$BASE_CMD --namespace ns-7 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(175,200)))") \
  > "$RESULTS/ns-7.log" 2>&1 &

echo "[ns-8] Launching sweep_0200–sweep_0224..."
$BASE_CMD --namespace ns-8 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(200,225)))") \
  > "$RESULTS/ns-8.log" 2>&1 &

echo "[ns-9] Launching sweep_0225–sweep_0249..."
$BASE_CMD --namespace ns-9 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(225,250)))") \
  > "$RESULTS/ns-9.log" 2>&1 &

echo "[ns-10] Launching sweep_0250–sweep_0274..."
$BASE_CMD --namespace ns-10 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(250,275)))") \
  > "$RESULTS/ns-10.log" 2>&1 &

echo "[ns-11] Launching sweep_0275–sweep_0299..."
$BASE_CMD --namespace ns-11 \
  --scenarios $(python3 -c "print(' '.join(f'sweep_{i:04d}' for i in range(275,300)))") \
  > "$RESULTS/ns-11.log" 2>&1 &

echo ""
echo "All 6 namespaces launched. Monitor with:"
echo "  tail -f $RESULTS/ns-*.log"
echo "  kubectl get pods -n ns-6"
echo ""
echo "Expected runtime: ~100 hours wall-clock (25 scenarios × ~4h per scenario)"
wait
echo "=== Server 2 complete ==="
