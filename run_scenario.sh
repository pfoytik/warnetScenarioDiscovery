#!/bin/bash
#
# Helper script to run warnet scenarios from warnetScenarioDiscovery repo
#
# Usage:
#   ./run_scenario.sh partition_miner_with_pools.py [scenario args...]
#
# Example:
#   ./run_scenario.sh partition_miner_with_pools.py \
#       --network-yaml /path/to/network.yaml \
#       --pool-scenario realistic_current \
#       --v27-economic 70.0 \
#       --duration 1800
#

# Get absolute path to scenarios directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENARIO_DIR="$SCRIPT_DIR/scenarios"

# Check if scenario file provided
if [ $# -eq 0 ]; then
    echo "Error: No scenario file specified"
    echo ""
    echo "Usage: $0 SCENARIO_FILE [ARGS...]"
    echo ""
    echo "Available scenarios:"
    ls -1 "$SCENARIO_DIR"/*.py 2>/dev/null | xargs -n1 basename
    exit 1
fi

SCENARIO_FILE="$1"
shift  # Remove first argument

# Check if file exists in scenarios directory
if [ ! -f "$SCENARIO_DIR/$SCENARIO_FILE" ]; then
    echo "Error: Scenario file not found: $SCENARIO_DIR/$SCENARIO_FILE"
    echo ""
    echo "Available scenarios:"
    ls -1 "$SCENARIO_DIR"/*.py 2>/dev/null | xargs -n1 basename
    exit 1
fi

# Run with warnet
echo "Running scenario: $SCENARIO_FILE"
echo "Scenario dir: $SCENARIO_DIR"
echo ""

warnet run "$SCENARIO_DIR/$SCENARIO_FILE" \
    --source_dir "$SCENARIO_DIR" \
    "$@"
