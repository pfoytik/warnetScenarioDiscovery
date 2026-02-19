#!/bin/bash
#
# Pre-Flight Check for Overnight Test
#
# Runs a quick 5-minute test to validate everything works before overnight run
#

set -e

echo "======================================================================="
echo "PRE-FLIGHT CHECK - Overnight Test Validation"
echo "======================================================================="
echo ""
echo "This will run a 5-minute test to ensure everything is working."
echo "If successful, you can run the full overnight test with confidence."
echo ""
echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
sleep 5

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "Running quick test (5 minutes)..."
echo ""

# Use shorter intervals for preflight test so we see pool decisions within 5 minutes
# - Pool decisions every 60 seconds (instead of 10 minutes)
# - Price updates every 15 seconds (instead of 1 minute)
# - Log updates every 60 seconds (instead of 5 minutes)
export POOL_DECISION_INTERVAL=60
export PRICE_UPDATE_INTERVAL=15
export LOG_INTERVAL=60

"$SCRIPT_DIR/run_overnight_test.sh" preflight-test 70 30 0.083  # 0.083 hours = 5 minutes

echo ""
echo "======================================================================="
echo "PRE-FLIGHT CHECK COMPLETE"
echo "======================================================================="
echo ""

# Check if results exist
if [ -f "$SCRIPT_DIR/results/preflight-test-pool-decisions.json" ] && \
   [ -f "$SCRIPT_DIR/results/preflight-test-price-history.json" ]; then
    echo "✓ All output files created successfully"
    echo ""
    echo "📊 Quick Results:"
    echo ""

    # Show market dynamics
    if [ -f "$SCRIPT_DIR/tools/analyze_market_dynamics.py" ]; then
        python3 "$SCRIPT_DIR/tools/analyze_market_dynamics.py" \
            --pool-decisions "$SCRIPT_DIR/results/preflight-test-pool-decisions.json" \
            --price-history "$SCRIPT_DIR/results/preflight-test-price-history.json" \
            2>/dev/null | tail -20 || echo "(analysis error - check manually)"
    fi

    echo ""
    echo "======================================================================="
    echo "✅ PRE-FLIGHT SUCCESSFUL"
    echo "======================================================================="
    echo ""
    echo "You're ready to run the overnight test!"
    echo ""
    echo "Command:"
    echo "  ./run_overnight_test.sh overnight-001 70 30 8"
    echo ""
    echo "Or see OVERNIGHT_TEST_GUIDE.md for more options."
    echo ""
else
    echo "⚠️  Warning: Some output files missing"
    echo "Check results/logs/preflight-test.log for details"
    echo ""
fi
