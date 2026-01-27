#!/bin/bash
#
# Complete Fork Test Runner
#
# Runs the full 4-step fork testing workflow:
#   1. Generate network
#   2. Deploy to warnet
#   3. Run mining scenario
#   4. Analyze fork
#
# Usage:
#   ./run_fork_test.sh TEST_NAME V27_ECONOMIC V27_HASHRATE [DURATION]
#
# Example:
#   ./run_fork_test.sh test-001 70 30 1800
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
DURATION=${4:-1800}  # Default 30 minutes
POOL_SCENARIO="realistic_current"

# Check arguments
if [ $# -lt 3 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo ""
    echo "Usage: $0 TEST_NAME V27_ECONOMIC V27_HASHRATE [DURATION]"
    echo ""
    echo "Arguments:"
    echo "  TEST_NAME      Unique test identifier (e.g., test-001)"
    echo "  V27_ECONOMIC   Economic weight on v27 (0-100)"
    echo "  V27_HASHRATE   Initial hashrate on v27 (0-100)"
    echo "  DURATION       Test duration in seconds (default: 1800)"
    echo ""
    echo "Example:"
    echo "  $0 test-001 70 30 1800"
    exit 1
fi

TEST_NAME="$1"
V27_ECONOMIC="$2"
V27_HASHRATE="$3"

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}Fork Test Runner - Complete Workflow${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo "Test: $TEST_NAME"
echo "Economic: v27=$V27_ECONOMIC%, v26=$((100-V27_ECONOMIC))%"
echo "Hashrate: v27=$V27_HASHRATE%, v26=$((100-V27_HASHRATE))%"
echo "Duration: ${DURATION}s"
echo ""

# Step 1: Generate Network
echo -e "${YELLOW}Step 1/4: Generating Network${NC}"
echo "----------------------------------------"
cd "$SCRIPT_DIR/networkGen"
python3 partition_network_generator.py \
    --test-id "$TEST_NAME" \
    --v27-economic "$V27_ECONOMIC" \
    --v27-hashrate "$V27_HASHRATE"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Network generation failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Network generated${NC}"
echo ""

# Derive network directory name
NETWORK_DIR="$SCRIPT_DIR/../test-networks/test-$TEST_NAME-economic-$V27_ECONOMIC-hashrate-$V27_HASHRATE"

if [ ! -d "$NETWORK_DIR" ]; then
    echo -e "${RED}✗ Network directory not found: $NETWORK_DIR${NC}"
    exit 1
fi

# Step 2: Deploy Network
echo -e "${YELLOW}Step 2/4: Deploying Network${NC}"
echo "----------------------------------------"
cd "$SCRIPT_DIR/.."
warnet deploy "$NETWORK_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Network deployment failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Network deployed${NC}"
echo ""

# Wait for nodes to sync
echo "Waiting 90 seconds for nodes to sync..."
sleep 90
echo -e "${GREEN}✓ Nodes synced${NC}"
echo ""

# Step 3: Run Mining Scenario
echo -e "${YELLOW}Step 3/4: Running Mining Scenario${NC}"
echo "----------------------------------------"
NETWORK_YAML="$NETWORK_DIR/network.yaml"

echo "Running scenario for ${DURATION}s..."
echo "(This will take $((DURATION/60)) minutes)"
echo ""

cd "$SCRIPT_DIR"
./run_scenario.sh partition_miner_with_pools.py \
    --network-yaml "$NETWORK_YAML" \
    --pool-scenario "$POOL_SCENARIO" \
    --v27-economic "$V27_ECONOMIC.0" \
    --duration "$DURATION"

SCENARIO_EXIT=$?
echo ""

if [ $SCENARIO_EXIT -ne 0 ]; then
    echo -e "${YELLOW}⚠ Scenario exited with code $SCENARIO_EXIT${NC}"
    echo "This may be normal if the scenario completed successfully"
fi

# Step 4: Analyze Fork
echo -e "${YELLOW}Step 4/4: Analyzing Fork${NC}"
echo "----------------------------------------"
cd "$SCRIPT_DIR/monitoring"

# Check if pool decisions file exists
if [ ! -f "/tmp/partition_pools.json" ]; then
    echo -e "${YELLOW}⚠ Pool decisions file not found${NC}"
    echo "Running analysis without pool decisions..."
    python3 enhanced_fork_analysis.py \
        --network-config "$NETWORK_DIR" \
        --live-query \
        --fork-depth-threshold 6
else
    echo "Analyzing with pool decisions..."
    python3 enhanced_fork_analysis.py \
        --network-config "$NETWORK_DIR" \
        --pool-decisions /tmp/partition_pools.json \
        --live-query \
        --fork-depth-threshold 6
fi

ANALYSIS_EXIT=$?
echo ""

if [ $ANALYSIS_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ Analysis complete${NC}"
else
    echo -e "${YELLOW}⚠ Analysis exited with code $ANALYSIS_EXIT${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}Test Complete: $TEST_NAME${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo "Results:"
echo "  - Pool decisions: /tmp/partition_pools.json"
echo "  - Price history:  /tmp/partition_prices.json"
echo "  - Fee history:    /tmp/partition_fees.json"
echo ""
echo "To stop the network:"
echo "  warnet stop"
echo ""
