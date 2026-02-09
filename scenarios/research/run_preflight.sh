#!/bin/bash
#
# Quick preflight test from warnet research directory
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WARNET_ROOT="$SCRIPT_DIR/../../.."

echo "Running preflight test from warnet research directory..."
echo ""

# Use shorter intervals for preflight test
export POOL_DECISION_INTERVAL=60
export PRICE_UPDATE_INTERVAL=15

# Run the scenario directly
warnet run "$SCRIPT_DIR/scenarios/partition_miner_with_pools.py" \
    --source_dir "$SCRIPT_DIR" \
    -- \
    --network-yaml "$WARNET_ROOT/../test-networks/test-preflight-test-economic-70-hashrate-30/network.yaml" \
    --pool-scenario realistic_current \
    --v27-economic 70.0 \
    --duration 298 \
    --hashrate-update-interval 60 \
    --price-update-interval 15 \
    --debug
