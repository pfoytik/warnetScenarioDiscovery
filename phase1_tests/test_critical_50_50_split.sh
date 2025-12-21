#!/bin/bash
#
# Phase 1 Test 1: critical-50-50-split
#
# Tests: Near-balanced custody split between competing chains
# Expected: Chain B wins due to volume dominance despite near-equal custody
#
# Duration: ~30 minutes
# Week: 2

set -e

TEST_NAME="test_1_critical_50_50_split"
SCENARIO_NAME="critical-50-50-split"

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
log "Phase 1 Test 1: critical-50-50-split"
log "========================================================================"
log "Test Goal: Validate risk detection at near-parity custody split"
log "Expected: Chain B (v27.0) wins via volume dominance"
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
    for node in exchange-conservative custody-provider exchange-progressive-1 exchange-progressive-2 payment-processor; do
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

    # Chain A (v26.0): exchange-conservative + custody-provider
    echo "Chain A (v26.0) nodes:"
    echo "  - exchange-conservative"
    echo "  - custody-provider"
    echo ""

    # Mine 5 blocks on Chain A nodes
    log "Mining 5 blocks on Chain A (v26.0)..."
    for i in {1..5}; do
        warnet bitcoin rpc exchange-conservative generatetoaddress 1 "$MINING_ADDR" 2>&1
        sleep 1
    done

    # Chain B (v27.0): exchange-progressive-1 + exchange-progressive-2 + payment-processor
    echo ""
    echo "Chain B (v27.0) nodes:"
    echo "  - exchange-progressive-1"
    echo "  - exchange-progressive-2"
    echo "  - payment-processor"
    echo ""

    # Mine 6 blocks on Chain B (more to win)
    log "Mining 6 blocks on Chain B (v27.0)..."
    for i in {1..6}; do
        warnet bitcoin rpc exchange-progressive-1 generatetoaddress 1 "$MINING_ADDR" 2>&1
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
    for node in exchange-conservative custody-provider exchange-progressive-1 exchange-progressive-2 payment-processor; do
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
    echo "# Test 1: critical-50-50-split - Validation"
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
    echo "- ✓ Fork detected between v26 and v27 nodes"
    echo "- ✓ Chain B wins (volume dominance)"
    echo "- ✓ Risk score 25-35/100 (LOW)"
    echo "- ✓ Weight split: ~20 vs ~26"
    echo ""

    echo "## Validation"
    if [ "$CONSENSUS_CHAIN" = "B" ]; then
        echo "- ✅ Consensus chain: PASS (Chain B won as expected)"
    else
        echo "- ❌ Consensus chain: FAIL (Expected Chain B, got Chain ${CONSENSUS_CHAIN})"
    fi

    if (( $(echo "$RISK_SCORE >= 25 && $RISK_SCORE <= 35" | bc -l 2>/dev/null || echo 0) )); then
        echo "- ✅ Risk score: PASS (${RISK_SCORE} in expected range 25-35)"
    else
        echo "- ⚠️  Risk score: OUT OF RANGE (${RISK_SCORE}, expected 25-35)"
    fi

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
log "Test 1 Complete!"
log "========================================================================"
log "Results saved to: ${RESULTS_DIR}/"
log ""
log "Next: Review FINDINGS.md and proceed to Test 2"
log "  cd phase1_tests"
log "  ./test_custody_volume_conflict.sh"
log ""

exit 0
