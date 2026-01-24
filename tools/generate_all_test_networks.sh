#!/bin/bash

###############################################################################
# Batch Network Generator for Tier 1 & 2 Tests
# Generates 17 test network configurations for systematic partition testing
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETWORK_GEN="$SCRIPT_DIR/../networkGen/partition_network_generator.py"
OUTPUT_BASE="$SCRIPT_DIR/../../test-networks"

echo "=========================================="
echo "Batch Network Generation - Tier 1 & 2"
echo "=========================================="
echo "Output directory: $OUTPUT_BASE"
echo ""

# Test configurations: test_id economic_pct hashrate_pct
declare -a TESTS=(
    # TIER 1: Edge Case Validation
    "test-1.1-E95-H10-dynamic 95 10"
    "test-1.2-E10-H95-dynamic 10 95"
    "test-1.3-E90-H90-dynamic 90 90"

    # TIER 2 - Series A: Economic Override Threshold
    "test-2.1-E50-H40-dynamic 50 40"
    "test-2.2-E60-H40-dynamic 60 40"
    "test-2.3-E70-H40-dynamic 70 40"
    "test-2.4-E80-H40-dynamic 80 40"
    "test-2.5-E90-H40-dynamic 90 40"

    # TIER 2 - Series B: Hashrate Resistance Threshold
    "test-2.6-E70-H20-dynamic 70 20"
    # test-2.7-E70-H30 SKIPPED (already completed as test-5.3)
    "test-2.8-E70-H40-dynamic 70 40"
    "test-2.9-E70-H45-dynamic 70 45"
    "test-2.10-E70-H49-dynamic 70 49"

    # TIER 2 - Series C: Critical Balance Zone
    "test-2.11-E50-H50-dynamic 50 50"
    "test-2.12-E52-H48-dynamic 52 48"
    "test-2.13-E48-H52-dynamic 48 52"
    "test-2.14-E55-H55-dynamic 55 55"
    "test-2.15-E45-H45-dynamic 45 45"
)

SUCCESS_COUNT=0
FAIL_COUNT=0

for test_config in "${TESTS[@]}"; do
    echo $test_config
    # Parse configuration
    read -r test_id economic hashrate <<< "$test_config"

    echo "=========================================="
    echo "Generating: $test_id"
    echo "  v27: ${economic}% economic, ${hashrate}% hashrate"
    echo "  v26: $((100-economic))% economic, $((100-hashrate))% hashrate"
    echo "=========================================="

    # Generate network
    if python3 "$NETWORK_GEN" \
        --test-id "$test_id" \
        --v27-economic "$economic" \
        --v27-hashrate "$hashrate" \
        --partition-mode dynamic \
        --output "$OUTPUT_BASE/$test_id"; then

        echo "✓ Generated: $OUTPUT_BASE/$test_id"
        ((SUCCESS_COUNT++))
    else
        echo "✗ FAILED: $test_id"
        ((FAIL_COUNT++))
    fi

    echo ""
done

echo "=========================================="
echo "Batch Generation Complete"
echo "=========================================="
echo "Success: $SUCCESS_COUNT"
echo "Failed:  $FAIL_COUNT"
echo "Total:   ${#TESTS[@]}"
echo ""
echo "Networks ready for testing!"
echo "=========================================="
