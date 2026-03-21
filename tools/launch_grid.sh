#!/bin/bash
# Grid-only launcher — launches grid2016 chunks in 3 staggered groups.
# Does NOT launch esp scenarios (use launch_esp_safe.sh for those).
#
# Usage:
#   bash tools/launch_grid.sh        # all 9 chunks (c0-c8)
#   bash tools/launch_grid.sh --skip-c2-c6  # 7 chunks (skip c2 and c6)

cd "$(dirname "$0")/.."

GRID_MANIFEST="tools/sweep/econ_committed_2016_grid/build_manifest.json"
SKIP_C2_C6=0
[ "${1:-}" = "--skip-c2-c6" ] && SKIP_C2_C6=1

log() { echo "[$(date '+%H:%M:%S')] $*"; }

launch_chunk() {
    local chunk="$1"; shift
    log "  Launching grid2016-$chunk"
    python tools/sweep/3_run_sweep.py \
        --input "$GRID_MANIFEST" \
        --namespace "grid2016-$chunk" \
        --results-dir econ_committed_2016_grid/results \
        --duration 13000 \
        --retarget-interval 2016 \
        --interval 2 \
        "$@" \
        > "/tmp/sweep_${chunk}.log" 2>&1 &
}

log "Grid launcher starting (SKIP_C2_C6=$SKIP_C2_C6)"
log ""

log "=== Group 1: c0 c1 c2 ==="
launch_chunk c0 --scenarios sweep_0000 sweep_0009 sweep_0018 sweep_0027 sweep_0036
launch_chunk c1 --scenarios sweep_0001 sweep_0010 sweep_0019 sweep_0028 sweep_0037
if [ "$SKIP_C2_C6" -eq 0 ]; then
    launch_chunk c2 --scenarios sweep_0002 sweep_0011 sweep_0020 sweep_0029 sweep_0038
fi
log "  Group 1 launched. Waiting 120s..."
sleep 120

log "=== Group 2: c3 c4 c5 ==="
launch_chunk c3 --scenarios sweep_0003 sweep_0012 sweep_0021 sweep_0030 sweep_0039
launch_chunk c4 --scenarios sweep_0004 sweep_0013 sweep_0022 sweep_0031 sweep_0040
launch_chunk c5 --scenarios sweep_0005 sweep_0014 sweep_0023 sweep_0032 sweep_0041
log "  Group 2 launched. Waiting 120s..."
sleep 120

log "=== Group 3: c6 c7 c8 ==="
if [ "$SKIP_C2_C6" -eq 0 ]; then
    launch_chunk c6 --scenarios sweep_0006 sweep_0015 sweep_0024 sweep_0033 sweep_0042
fi
launch_chunk c7 --scenarios sweep_0007 sweep_0016 sweep_0025 sweep_0034 sweep_0043
launch_chunk c8 --scenarios sweep_0008 sweep_0017 sweep_0026 sweep_0035 sweep_0044
log "  Group 3 launched."

log ""
log "=== All grid chunks launched ==="
log "  Active runners: $(pgrep -f '3_run_sweep.*grid2016' | wc -l)"
log "  Monitor with: python tools/monitor_sweeps.py"
