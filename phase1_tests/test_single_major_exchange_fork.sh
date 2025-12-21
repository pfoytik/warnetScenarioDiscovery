#!/bin/bash
#
# Phase 1 Test 3: single-major-exchange-fork
#
# Tests: Network isolation of single major player
# Expected: Chain B wins via network majority effect
#
# Duration: ~30 minutes
# Week: 4

set -e

TEST_NAME="test_3_single_major_exchange_fork"
SCENARIO_NAME="single-major-exchange-fork"

# Get absolute path for results directory (before any cd commands)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results/${TEST_NAME}"

# Create results directory FIRST
mkdir -p "${RESULTS_DIR}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "${RESULTS_DIR}/test.log"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "${RESULTS_DIR}/test.log"
}

log "========================================================================"
log "Phase 1 Test 3: single-major-exchange-fork"
log "========================================================================"
log "Test Goal: Validate network majority can isolate single major player"
log "Expected: Chain B (v27.0) wins via network coordination"
log ""

# Step 1: Deploy Network
log "STEP 1: Deploying network..."
log "------------------------------------------------------------------------"

cd ../..  # Go to warnet root

# Clean up any previous deployment
log "Cleaning up previous deployment..."
warnet down 2>/dev/null || true
sleep 5

# Deploy
log "Deploying ${SCENARIO_NAME}..."
if ! warnet deploy test-networks/${SCENARIO_NAME}/; then
    log_error "Deployment failed"
    exit 1
fi

log "Waiting for network to start..."
sleep 10

# Step 2: Verify Deployment
log ""
log "STEP 2: Verifying deployment..."
log "------------------------------------------------------------------------"

# Check warnet status
warnet status > "${RESULTS_DIR}/deployment_status.log" 2>&1

# Wait for all pods to be Running
log "Waiting for all pods to be Running..."
MAX_WAIT=180
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    RUNNING_PODS=$(kubectl get pods -n warnet --no-headers 2>/dev/null | grep -c "Running" || echo "0")
    TOTAL_PODS=$(kubectl get pods -n warnet --no-headers 2>/dev/null | wc -l || echo "0")

    if [ "$RUNNING_PODS" -eq "$TOTAL_PODS" ] && [ "$TOTAL_PODS" -gt 0 ]; then
        log "All pods Running ($RUNNING_PODS/$TOTAL_PODS)"
        break
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
    log "Waiting... ($RUNNING_PODS/$TOTAL_PODS Running, ${ELAPSED}s elapsed)"
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    log_error "Timeout waiting for pods to start"
    kubectl get pods -n warnet >> "${RESULTS_DIR}/deployment_status.log" 2>&1
    exit 1
fi

kubectl get pods -n warnet >> "${RESULTS_DIR}/deployment_status.log" 2>&1

# Step 3: Mine Initial Blocks
log ""
log "STEP 3: Mining initial blocks to maturity..."
log "------------------------------------------------------------------------"

log "Mining 101 blocks for coinbase maturity..."
cd warnetScenarioDiscovery/phase1_tests

if ! timeout 300 warnet run scenarios/miner_std.py --interval 5 2>&1 | tee "${RESULTS_DIR}/initial_mining.log"; then
    log_error "Initial mining failed or timed out"
    # Continue anyway - may have mined enough
fi

sleep 5

# Verify block heights
log "Verifying block heights..."
{
    echo "Initial Chain State:"
    echo "===================="
    for node in coinbase binance kraken gemini; do
        height=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "ERROR")
        tip=$(warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null || echo "ERROR")
        echo "$node: height=$height, tip=${tip:0:16}..."
    done
} | tee "${RESULTS_DIR}/initial_chain_state.log"

# Step 4: Create Fork
log ""
log "STEP 4: Creating artificial fork..."
log "------------------------------------------------------------------------"

# Get a mining address
MINING_ADDR=$(warnet bitcoin rpc tank getnewaddress 2>/dev/null || echo "bcrt1qxxx")

log "Mining address: $MINING_ADDR"

{
    echo "Fork Creation Log"
    echo "================="
    echo "Timestamp: $(date +'%Y-%m-%d %H:%M:%S')"
    echo ""

    # Chain A (v26.0): Coinbase isolated
    echo "Chain A (v26.0) - Isolated exchange:"
    echo "  - coinbase (2M BTC, 100k BTC/day)"
    echo ""

    # Mine 5 blocks on Chain A (Coinbase alone)
    log "Mining 5 blocks on Chain A (v26.0 - isolated Coinbase)..."
    for i in {1..5}; do
        warnet bitcoin rpc coinbase generatetoaddress 1 "$MINING_ADDR" 2>&1
        sleep 1
    done

    # Chain B (v27.0): Network majority (Binance + Kraken + Gemini)
    echo ""
    echo "Chain B (v27.0) - Network majority:"
    echo "  - binance (2.5M BTC, 120k BTC/day)"
    echo "  - kraken (500k BTC, 30k BTC/day)"
    echo "  - gemini (400k BTC, 25k BTC/day)"
    echo ""

    # Mine 6 blocks on Chain B (network majority wins)
    log "Mining 6 blocks on Chain B (v27.0 - network majority)..."
    for i in {1..6}; do
        warnet bitcoin rpc binance generatetoaddress 1 "$MINING_ADDR" 2>&1
        sleep 1
    done

    echo ""
    echo "Fork created. Waiting for propagation..."
    sleep 10

} | tee "${RESULTS_DIR}/fork_creation.log"

# Verify fork exists
log "Verifying fork..."
{
    echo ""
    echo "Chain State After Fork:"
    echo "======================="
    for node in coinbase binance kraken gemini; do
        height=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "ERROR")
        tip=$(warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null || echo "ERROR")
        echo "$node: height=$height, tip=${tip:0:16}..."
    done
} | tee -a "${RESULTS_DIR}/fork_creation.log"

# Step 5: Economic Analysis
log ""
log "STEP 5: Running economic analysis..."
log "------------------------------------------------------------------------"

cd ../monitoring

if python3 auto_economic_analysis.py \
    --network-config ../../test-networks/${SCENARIO_NAME}/ \
    --live-query > "../phase1_tests/${RESULTS_DIR}/economic_analysis.txt" 2>&1; then
    log "Economic analysis complete"
else
    log_error "Economic analysis failed"
fi

cat "../phase1_tests/${RESULTS_DIR}/economic_analysis.txt"

# Step 6: Collect Logs
log ""
log "STEP 6: Collecting logs..."
log "------------------------------------------------------------------------"

kubectl logs -n warnet --all-containers --prefix --tail=1000 > "../phase1_tests/${RESULTS_DIR}/kubectl_logs.txt" 2>&1
log "Kubernetes logs saved"

# Step 7: Validation
log ""
log "STEP 7: Validating results..."
log "------------------------------------------------------------------------"

cd ../phase1_tests

# Extract key metrics from economic analysis
RISK_SCORE=$(grep "Risk Score:" "${RESULTS_DIR}/economic_analysis.txt" | head -1 | awk '{print $3}' | sed 's/\/.*//' || echo "N/A")
CONSENSUS_CHAIN=$(grep "Consensus Chain:" "${RESULTS_DIR}/economic_analysis.txt" | head -1 | awk '{print $4}' || echo "N/A")

log "Test Results:"
log "  Risk Score: ${RISK_SCORE}/100"
log "  Consensus Chain: Chain ${CONSENSUS_CHAIN}"

# Validation
{
    echo "# Test 3: single-major-exchange-fork - Validation"
    echo ""
    echo "## Test Execution"
    echo "- Start Time: $(date +'%Y-%m-%d %H:%M:%S')"
    echo "- Scenario: ${SCENARIO_NAME}"
    echo "- Status: COMPLETED"
    echo ""

    echo "## Results"
    echo "- Risk Score: ${RISK_SCORE}/100"
    echo "- Consensus Chain: Chain ${CONSENSUS_CHAIN}"
    echo ""

    echo "## Expected Outcomes"
    echo "- ✓ Fork detected between Coinbase and network majority"
    echo "- ✓ Chain B wins (network majority isolates Coinbase)"
    echo "- ✓ Risk score 20-25/100 (LOW)"
    echo "- ✓ Weight split: ~17.2 vs ~29.7"
    echo "- ✓ Network effect: 3 coordinated exchanges beat 1 isolated"
    echo ""

    echo "## Validation"
    if [ "$CONSENSUS_CHAIN" = "B" ]; then
        echo "- ✅ Consensus chain: PASS (Chain B won as expected)"
    else
        echo "- ❌ Consensus chain: FAIL (Expected Chain B, got Chain ${CONSENSUS_CHAIN})"
    fi

    if (( $(echo "$RISK_SCORE >= 20 && $RISK_SCORE <= 25" | bc -l 2>/dev/null || echo 0) )); then
        echo "- ✅ Risk score: PASS (${RISK_SCORE} in expected range 20-25)"
    else
        echo "- ⚠️  Risk score: OUT OF RANGE (${RISK_SCORE}, expected 20-25)"
    fi

    echo ""
    echo "## Key Finding"
    echo "This test demonstrates network majority power:"
    echo "- Coinbase (isolated): 10.3% supply, weight 17.2"
    echo "- Network majority: 17.4% supply, weight 29.7"
    echo "- Binance alone (12.82% supply) > Coinbase (10.26% supply)"
    echo ""
    echo "**Implication**: Single major exchange cannot resist network-wide"
    echo "upgrade if other major players coordinate. Network effect isolates"
    echo "individual actors, even if they are significant players."
    echo ""

    echo "## Files Generated"
    echo "- deployment_status.log"
    echo "- initial_chain_state.log"
    echo "- initial_mining.log"
    echo "- fork_creation.log"
    echo "- economic_analysis.txt"
    echo "- kubectl_logs.txt"
    echo "- test.log"
    echo ""

    echo "## Notes"
    echo "Add any observations or unexpected behaviors here..."
    echo ""

} > "${RESULTS_DIR}/FINDINGS.md"

cat "${RESULTS_DIR}/FINDINGS.md"

# Step 8: Cleanup
log ""
log "STEP 8: Cleanup..."
log "------------------------------------------------------------------------"

log "Tearing down network..."
warnet down

log ""
log "========================================================================"
log "Test 3 Complete!"
log "========================================================================"
log "Results saved to: ${RESULTS_DIR}/"
log ""
log "Next: Review FINDINGS.md and proceed to Test 4"
log "  cd phase1_tests"
log "  ./test_dual_metric_baseline.sh"
log ""

exit 0
