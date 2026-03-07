#!/bin/bash
# Run both lite network sweeps sequentially
# Sweep 5: Economic threshold mapping (8 scenarios)
# Sweep 6: User node behavior (9 scenarios)

set -e  # Exit on error

echo "=========================================="
echo "Starting Lite Network Sweep Sequence"
echo "=========================================="
echo ""

# Sweep 5: Economic Threshold
echo "[1/2] Running targeted_sweep5_lite_econ_threshold (8 scenarios)"
echo "     Testing economic_split: 0.50 -> 0.85"
echo ""
python 3_run_sweep.py --input targeted_sweep5_lite_econ_threshold/build_manifest.json --duration 1800 --interval 2

echo ""
echo "[1/2] Analyzing sweep 5 results..."
python 4_analyze_results.py --input targeted_sweep5_lite_econ_threshold/results

echo ""
echo "=========================================="
echo ""

# Sweep 6: User Behavior
echo "[2/2] Running targeted_sweep6_lite_user_behavior (9 scenarios)"
echo "     Testing user_ideology × user_threshold grid"
echo ""
python 3_run_sweep.py --input targeted_sweep6_lite_user_behavior/build_manifest.json --duration 1800 --interval 2

echo ""
echo "[2/2] Analyzing sweep 6 results..."
python 4_analyze_results.py --input targeted_sweep6_lite_user_behavior/results

echo ""
echo "=========================================="
echo "Updating database..."
python 5_build_database.py

echo ""
echo "=========================================="
echo "All sweeps complete!"
echo "=========================================="
echo ""
echo "Results:"
echo "  targeted_sweep5_lite_econ_threshold/results/analysis/"
echo "  targeted_sweep6_lite_user_behavior/results/analysis/"
echo ""
echo "Database updated: sweep_results.db"
