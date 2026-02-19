#!/bin/bash
#
# Overnight Test Runner - Market Dynamics Validation
#
# Purpose: Run extended test to validate:
#   1. Markets are forming (price/fee evolution)
#   2. Pools make decisions based on dynamic markets
#   3. System is stable for long runs
#
# Usage: ./run_overnight_test.sh [TEST_ID] [V27_ECONOMIC] [V27_HASHRATE] [DURATION_HOURS]
#
# Example: ./run_overnight_test.sh overnight-001 70 30 8
#   - Runs for 8 hours
#   - 70% economic on v27, 30% hashrate initially
#   - Logs all market changes and pool decisions
#
# Environment variables (optional):
#   POOL_DECISION_INTERVAL - seconds between pool decisions (default: 600 = 10 min)
#   PRICE_UPDATE_INTERVAL  - seconds between price updates (default: 60 = 1 min)
#   LOG_INTERVAL           - seconds between status log updates (default: 300 = 5 min)

set -e  # Exit on error

# Configuration
TEST_ID=${1:-"overnight-$(date +%Y%m%d-%H%M)"}
V27_ECONOMIC=${2:-70}
V27_HASHRATE=${3:-30}
DURATION_HOURS=${4:-8}
# Use bc for floating-point arithmetic (bash $(()) only handles integers)
DURATION_SECONDS=$(echo "$DURATION_HOURS * 3600" | bc | cut -d'.' -f1)

# Ensure we have a valid duration
if [ -z "$DURATION_SECONDS" ] || [ "$DURATION_SECONDS" -eq 0 ]; then
    echo "ERROR: Invalid duration. DURATION_HOURS=$DURATION_HOURS resulted in DURATION_SECONDS=$DURATION_SECONDS"
    echo "Please provide a valid duration (e.g., 0.1 for 6 minutes, 1 for 1 hour)"
    exit 1
fi

# Intervals (in seconds) - can be overridden via environment variables for testing
POOL_DECISION_INTERVAL=${POOL_DECISION_INTERVAL:-600}    # 10 minutes - how often pools reconsider
PRICE_UPDATE_INTERVAL=${PRICE_UPDATE_INTERVAL:-60}       # 1 minute - price evolution
LOG_INTERVAL=${LOG_INTERVAL:-300}                        # 5 minutes - status updates

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NETWORKS_DIR="$SCRIPT_DIR/../test-networks"
RESULTS_DIR="$SCRIPT_DIR/results"
LOG_DIR="$RESULTS_DIR/logs"

# Create results directory
mkdir -p "$RESULTS_DIR"
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="$LOG_DIR/${TEST_ID}.log"
SUMMARY_FILE="$RESULTS_DIR/${TEST_ID}-summary.txt"

# Network path
NETWORK_DIR="$TEST_NETWORKS_DIR/test-${TEST_ID}-economic-${V27_ECONOMIC}-hashrate-${V27_HASHRATE}"
NETWORK_YAML="$NETWORK_DIR/network.yaml"

# Output files
POOL_DECISIONS="/tmp/partition_pools.json"
PRICE_HISTORY="/tmp/partition_prices.json"
FEE_HISTORY="/tmp/partition_fees.json"

echo "======================================================================" | tee "$LOG_FILE"
echo "OVERNIGHT TEST - MARKET DYNAMICS VALIDATION" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Test ID:         $TEST_ID" | tee -a "$LOG_FILE"
echo "Duration:        $DURATION_HOURS hours ($DURATION_SECONDS seconds)" | tee -a "$LOG_FILE"
echo "v27 Economic:    $V27_ECONOMIC%" | tee -a "$LOG_FILE"
echo "v27 Hashrate:    $V27_HASHRATE% (initial)" | tee -a "$LOG_FILE"
echo "Pool Decisions:  Every $POOL_DECISION_INTERVAL seconds ($(($POOL_DECISION_INTERVAL / 60)) minutes)" | tee -a "$LOG_FILE"
echo "Price Updates:   Every $PRICE_UPDATE_INTERVAL seconds" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Start Time:      $(date)" | tee -a "$LOG_FILE"
echo "Expected End:    $(date -d "+${DURATION_HOURS} hours" 2>/dev/null || date -v+${DURATION_HOURS}H)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"

# STEP 1: Generate Network
echo "" | tee -a "$LOG_FILE"
echo "[STEP 1/4] Generating network..." | tee -a "$LOG_FILE"
echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR/networkGen"
python3 partition_network_generator.py \
    --test-id "$TEST_ID" \
    --v27-economic "$V27_ECONOMIC" \
    --v27-hashrate "$V27_HASHRATE" | tee -a "$LOG_FILE"

if [ ! -f "$NETWORK_YAML" ]; then
    echo "❌ ERROR: Network file not found: $NETWORK_YAML" | tee -a "$LOG_FILE"
    exit 1
fi

echo "✓ Network generated: $NETWORK_YAML" | tee -a "$LOG_FILE"

# STEP 2: Deploy Network
echo "" | tee -a "$LOG_FILE"
echo "[STEP 2/4] Deploying network to warnet..." | tee -a "$LOG_FILE"
echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR/.."
warnet deploy "$NETWORK_DIR" 2>&1 | tee -a "$LOG_FILE"

echo "✓ Network deployed" | tee -a "$LOG_FILE"
echo "  Waiting 90 seconds for nodes to sync..." | tee -a "$LOG_FILE"
sleep 90

# STEP 3: Run Mining Scenario (in background)
echo "" | tee -a "$LOG_FILE"
echo "[STEP 3/4] Starting mining scenario..." | tee -a "$LOG_FILE"
echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"
echo "  Duration: $DURATION_SECONDS seconds ($DURATION_HOURS hours)" | tee -a "$LOG_FILE"
echo "  Pool decisions: Every $POOL_DECISION_INTERVAL seconds" | tee -a "$LOG_FILE"
echo "  Price updates: Every $PRICE_UPDATE_INTERVAL seconds" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"

# Run scenario in background, redirect output to log
nohup ./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml "$NETWORK_YAML" \
    --pool-scenario realistic_current \
    --v27-economic "$V27_ECONOMIC.0" \
    --duration "$DURATION_SECONDS" \
    --hashrate-update-interval "$POOL_DECISION_INTERVAL" \
    --price-update-interval "$PRICE_UPDATE_INTERVAL" \
    >> "$LOG_FILE" 2>&1 &

SCENARIO_PID=$!
echo "✓ Mining scenario started (PID: $SCENARIO_PID)" | tee -a "$LOG_FILE"
echo "  Log file: $LOG_FILE" | tee -a "$LOG_FILE"

# STEP 4: Monitor Market Dynamics
echo "" | tee -a "$LOG_FILE"
echo "[STEP 4/4] Monitoring market dynamics..." | tee -a "$LOG_FILE"
echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"
echo "  Will check every $LOG_INTERVAL seconds ($(($LOG_INTERVAL / 60)) minutes)" | tee -a "$LOG_FILE"
echo "  Press Ctrl+C to stop monitoring (scenario continues in background)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Create monitoring script
cat > /tmp/monitor_overnight_test.sh << 'EOF'
#!/bin/bash
LOG_FILE="$1"
LOG_INTERVAL="$2"
POOL_DECISIONS="$3"
PRICE_HISTORY="$4"

while true; do
    echo "" | tee -a "$LOG_FILE"
    echo "[$(date)] Market Status Check" | tee -a "$LOG_FILE"
    echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"

    # Check if files exist
    if [ -f "$POOL_DECISIONS" ]; then
        echo "Pool Decisions:" | tee -a "$LOG_FILE"
        cat "$POOL_DECISIONS" | jq -r '.pools | to_entries | .[] | "  \(.key): mining \(.value.current_allocation) (hashrate: \(.value.profile.hashrate_pct)%)"' 2>/dev/null | head -10 | tee -a "$LOG_FILE" || echo "  (parsing error)" | tee -a "$LOG_FILE"
    else
        echo "  Pool decisions file not yet created" | tee -a "$LOG_FILE"
    fi

    echo "" | tee -a "$LOG_FILE"

    if [ -f "$PRICE_HISTORY" ]; then
        echo "Latest Prices:" | tee -a "$LOG_FILE"
        cat "$PRICE_HISTORY" | jq -r '.history[-1] | "  Time: \(.timestamp)s\n  v27: $\(.v27_price)\n  v26: $\(.v26_price)"' 2>/dev/null | tee -a "$LOG_FILE" || echo "  (parsing error)" | tee -a "$LOG_FILE"
    else
        echo "  Price history file not yet created" | tee -a "$LOG_FILE"
    fi

    echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"

    sleep "$LOG_INTERVAL"
done
EOF

chmod +x /tmp/monitor_overnight_test.sh
/tmp/monitor_overnight_test.sh "$LOG_FILE" "$LOG_INTERVAL" "$POOL_DECISIONS" "$PRICE_HISTORY" &
MONITOR_PID=$!

# Wait for scenario to complete
echo "Waiting for scenario to complete..." | tee -a "$LOG_FILE"
echo "(This will take $DURATION_HOURS hours)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

wait $SCENARIO_PID
SCENARIO_EXIT_CODE=$?

# Stop monitoring
kill $MONITOR_PID 2>/dev/null || true

# Record completion
echo "" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "SCENARIO COMPLETED" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "End Time:     $(date)" | tee -a "$LOG_FILE"
echo "Exit Code:    $SCENARIO_EXIT_CODE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run final analysis
echo "Running final fork analysis..." | tee -a "$LOG_FILE"
echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR/monitoring"
python3 enhanced_fork_analysis.py \
    --network-config "$NETWORK_DIR" \
    --pool-decisions "$POOL_DECISIONS" \
    --live-query \
    2>&1 | tee -a "$LOG_FILE"

# Copy output files to results
echo "" | tee -a "$LOG_FILE"
echo "Saving results..." | tee -a "$LOG_FILE"

# Check and copy each file, reporting status
COPY_SUCCESS=0
if [ -f "$POOL_DECISIONS" ]; then
    cp "$POOL_DECISIONS" "$RESULTS_DIR/${TEST_ID}-pool-decisions.json"
    echo "  ✓ ${TEST_ID}-pool-decisions.json" | tee -a "$LOG_FILE"
    COPY_SUCCESS=$((COPY_SUCCESS + 1))
else
    echo "  ⚠️  Pool decisions file not found: $POOL_DECISIONS" | tee -a "$LOG_FILE"
fi

if [ -f "$PRICE_HISTORY" ]; then
    cp "$PRICE_HISTORY" "$RESULTS_DIR/${TEST_ID}-price-history.json"
    echo "  ✓ ${TEST_ID}-price-history.json" | tee -a "$LOG_FILE"
    COPY_SUCCESS=$((COPY_SUCCESS + 1))
else
    echo "  ⚠️  Price history file not found: $PRICE_HISTORY" | tee -a "$LOG_FILE"
fi

if [ -f "$FEE_HISTORY" ]; then
    cp "$FEE_HISTORY" "$RESULTS_DIR/${TEST_ID}-fee-history.json"
    echo "  ✓ ${TEST_ID}-fee-history.json" | tee -a "$LOG_FILE"
    COPY_SUCCESS=$((COPY_SUCCESS + 1))
else
    echo "  ⚠️  Fee history file not found: $FEE_HISTORY" | tee -a "$LOG_FILE"
fi

echo "  - logs/${TEST_ID}.log" | tee -a "$LOG_FILE"

if [ "$COPY_SUCCESS" -eq 3 ]; then
    echo "✓ All results saved to: $RESULTS_DIR/" | tee -a "$LOG_FILE"
elif [ "$COPY_SUCCESS" -gt 0 ]; then
    echo "⚠️  Partial results saved to: $RESULTS_DIR/" | tee -a "$LOG_FILE"
else
    echo "❌ No result files were generated by the scenario" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "TEST COMPLETE" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"

# Run market dynamics analysis
echo "" | tee -a "$LOG_FILE"
echo "Analyzing market dynamics..." | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"
# Check if required files exist before running analysis
if [ -f "$RESULTS_DIR/${TEST_ID}-pool-decisions.json" ] && \
   [ -f "$RESULTS_DIR/${TEST_ID}-price-history.json" ] && \
   [ -f "tools/analyze_market_dynamics.py" ]; then
    python3 tools/analyze_market_dynamics.py \
        --pool-decisions "$RESULTS_DIR/${TEST_ID}-pool-decisions.json" \
        --price-history "$RESULTS_DIR/${TEST_ID}-price-history.json" \
        --output "$SUMMARY_FILE" \
        2>&1 | tee -a "$LOG_FILE"

    echo "" | tee -a "$LOG_FILE"
    echo "✓ Market dynamics analysis saved to: $SUMMARY_FILE" | tee -a "$LOG_FILE"
elif [ ! -f "tools/analyze_market_dynamics.py" ]; then
    echo "⚠️  Market dynamics analyzer not found (optional)" | tee -a "$LOG_FILE"
else
    echo "⚠️  Skipping market dynamics analysis - result files not generated" | tee -a "$LOG_FILE"
    echo "   This may indicate the scenario exited before completing." | tee -a "$LOG_FILE"
    echo "   Check the log above for errors during mining." | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "All logs saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
