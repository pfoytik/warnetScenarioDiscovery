#!/bin/bash
# Fork Outcome Parameter Sweep Runner
# Generated 5 scenarios
# Duration per scenario: 1800s (30 min)

set -e

# Get absolute path of script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SWEEP_DIR="$SCRIPT_DIR"
RESULTS_DIR="$SWEEP_DIR/results"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIOS_DIR="$PROJECT_DIR/scenarios"
TOOLS_DIR="$PROJECT_DIR/tools"

mkdir -p "$RESULTS_DIR"

echo "Starting fork outcome sweep with 5 scenarios"
echo "Results will be saved to $RESULTS_DIR"
echo ""

START_TIME=$(date +%s)
COMPLETED=0
FAILED=0

# Scenario 1/5: fork_sweep_0000
echo "[1/5] Running fork_sweep_0000..."
if [ -f "$RESULTS_DIR/fork_sweep_0000/results.json" ]; then
  echo "  Skipping (already completed)"
  ((COMPLETED++)) || true
else
  # Deploy network (warnet expects a directory containing network.yaml)
  if warnet deploy "$SWEEP_DIR/networks/fork_sweep_0000" 2>&1; then
    sleep 30  # Wait for network to stabilize

    # Run scenario
    if warnet run "$SCENARIOS_DIR/partition_miner_with_pools.py" \
        --network "$SWEEP_DIR/networks/fork_sweep_0000/network.yaml" \
        --enable-difficulty \
        --retarget-interval 144 \
        --interval 1 \
        --duration 1800 \
        --results-id "fork_sweep_0000" \
        2>&1 | tee "$RESULTS_DIR/fork_sweep_0000.log"; then

      # Extract results
      python "$TOOLS_DIR/extract_results.py" fork_sweep_0000 \
        --output-dir "$RESULTS_DIR/fork_sweep_0000" 2>/dev/null || true
      ((COMPLETED++)) || true
    else
      echo "  FAILED: Scenario fork_sweep_0000"
      ((FAILED++)) || true
    fi

    # Cleanup
    warnet down --force 2>/dev/null || true
    sleep 10
  else
    echo "  FAILED: Could not deploy network for fork_sweep_0000"
    ((FAILED++)) || true
  fi
fi
echo ""

# Scenario 2/5: fork_sweep_0001
echo "[2/5] Running fork_sweep_0001..."
if [ -f "$RESULTS_DIR/fork_sweep_0001/results.json" ]; then
  echo "  Skipping (already completed)"
  ((COMPLETED++)) || true
else
  # Deploy network (warnet expects a directory containing network.yaml)
  if warnet deploy "$SWEEP_DIR/networks/fork_sweep_0001" 2>&1; then
    sleep 30  # Wait for network to stabilize

    # Run scenario
    if warnet run "$SCENARIOS_DIR/partition_miner_with_pools.py" \
        --network "$SWEEP_DIR/networks/fork_sweep_0001/network.yaml" \
        --enable-difficulty \
        --retarget-interval 144 \
        --interval 1 \
        --duration 1800 \
        --results-id "fork_sweep_0001" \
        2>&1 | tee "$RESULTS_DIR/fork_sweep_0001.log"; then

      # Extract results
      python "$TOOLS_DIR/extract_results.py" fork_sweep_0001 \
        --output-dir "$RESULTS_DIR/fork_sweep_0001" 2>/dev/null || true
      ((COMPLETED++)) || true
    else
      echo "  FAILED: Scenario fork_sweep_0001"
      ((FAILED++)) || true
    fi

    # Cleanup
    warnet down --force 2>/dev/null || true
    sleep 10
  else
    echo "  FAILED: Could not deploy network for fork_sweep_0001"
    ((FAILED++)) || true
  fi
fi
echo ""

# Scenario 3/5: fork_sweep_0002
echo "[3/5] Running fork_sweep_0002..."
if [ -f "$RESULTS_DIR/fork_sweep_0002/results.json" ]; then
  echo "  Skipping (already completed)"
  ((COMPLETED++)) || true
else
  # Deploy network (warnet expects a directory containing network.yaml)
  if warnet deploy "$SWEEP_DIR/networks/fork_sweep_0002" 2>&1; then
    sleep 30  # Wait for network to stabilize

    # Run scenario
    if warnet run "$SCENARIOS_DIR/partition_miner_with_pools.py" \
        --network "$SWEEP_DIR/networks/fork_sweep_0002/network.yaml" \
        --enable-difficulty \
        --retarget-interval 144 \
        --interval 1 \
        --duration 1800 \
        --results-id "fork_sweep_0002" \
        2>&1 | tee "$RESULTS_DIR/fork_sweep_0002.log"; then

      # Extract results
      python "$TOOLS_DIR/extract_results.py" fork_sweep_0002 \
        --output-dir "$RESULTS_DIR/fork_sweep_0002" 2>/dev/null || true
      ((COMPLETED++)) || true
    else
      echo "  FAILED: Scenario fork_sweep_0002"
      ((FAILED++)) || true
    fi

    # Cleanup
    warnet down --force 2>/dev/null || true
    sleep 10
  else
    echo "  FAILED: Could not deploy network for fork_sweep_0002"
    ((FAILED++)) || true
  fi
fi
echo ""

# Scenario 4/5: fork_sweep_0003
echo "[4/5] Running fork_sweep_0003..."
if [ -f "$RESULTS_DIR/fork_sweep_0003/results.json" ]; then
  echo "  Skipping (already completed)"
  ((COMPLETED++)) || true
else
  # Deploy network (warnet expects a directory containing network.yaml)
  if warnet deploy "$SWEEP_DIR/networks/fork_sweep_0003" 2>&1; then
    sleep 30  # Wait for network to stabilize

    # Run scenario
    if warnet run "$SCENARIOS_DIR/partition_miner_with_pools.py" \
        --network "$SWEEP_DIR/networks/fork_sweep_0003/network.yaml" \
        --enable-difficulty \
        --retarget-interval 144 \
        --interval 1 \
        --duration 1800 \
        --results-id "fork_sweep_0003" \
        2>&1 | tee "$RESULTS_DIR/fork_sweep_0003.log"; then

      # Extract results
      python "$TOOLS_DIR/extract_results.py" fork_sweep_0003 \
        --output-dir "$RESULTS_DIR/fork_sweep_0003" 2>/dev/null || true
      ((COMPLETED++)) || true
    else
      echo "  FAILED: Scenario fork_sweep_0003"
      ((FAILED++)) || true
    fi

    # Cleanup
    warnet down --force 2>/dev/null || true
    sleep 10
  else
    echo "  FAILED: Could not deploy network for fork_sweep_0003"
    ((FAILED++)) || true
  fi
fi
echo ""

# Scenario 5/5: fork_sweep_0004
echo "[5/5] Running fork_sweep_0004..."
if [ -f "$RESULTS_DIR/fork_sweep_0004/results.json" ]; then
  echo "  Skipping (already completed)"
  ((COMPLETED++)) || true
else
  # Deploy network (warnet expects a directory containing network.yaml)
  if warnet deploy "$SWEEP_DIR/networks/fork_sweep_0004" 2>&1; then
    sleep 30  # Wait for network to stabilize

    # Run scenario
    if warnet run "$SCENARIOS_DIR/partition_miner_with_pools.py" \
        --network "$SWEEP_DIR/networks/fork_sweep_0004/network.yaml" \
        --enable-difficulty \
        --retarget-interval 144 \
        --interval 1 \
        --duration 1800 \
        --results-id "fork_sweep_0004" \
        2>&1 | tee "$RESULTS_DIR/fork_sweep_0004.log"; then

      # Extract results
      python "$TOOLS_DIR/extract_results.py" fork_sweep_0004 \
        --output-dir "$RESULTS_DIR/fork_sweep_0004" 2>/dev/null || true
      ((COMPLETED++)) || true
    else
      echo "  FAILED: Scenario fork_sweep_0004"
      ((FAILED++)) || true
    fi

    # Cleanup
    warnet down --force 2>/dev/null || true
    sleep 10
  else
    echo "  FAILED: Could not deploy network for fork_sweep_0004"
    ((FAILED++)) || true
  fi
fi
echo ""

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "========================================"
echo "Fork outcome sweep complete!"
echo "========================================"
echo "Total scenarios: 5"
echo "Completed: $COMPLETED"
echo "Failed: $FAILED"
echo "Total time: $((ELAPSED / 3600))h $((ELAPSED % 3600 / 60))m $((ELAPSED % 60))s"
echo "Results saved to: $RESULTS_DIR"