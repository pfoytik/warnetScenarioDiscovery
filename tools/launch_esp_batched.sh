#!/bin/bash
# Batched ESP launcher — respects the 1024 Linux bridge port limit.
# Waits for each batch to fully complete (results.json present) before
# launching the next. Run in a screen/tmux session overnight.
#
# Usage:
#   bash tools/launch_esp_batched.sh           # full run, wait for esp-144-0..5 first
#   bash tools/launch_esp_batched.sh --batch 2 # skip to batch 2 (1 already done)
#   bash tools/launch_esp_batched.sh --batch 3 # skip to batch 3

cd "$(dirname "$0")/.."
ESP_MANIFEST="tools/sweep/targeted_sweep7_esp/build_manifest.json"
START_BATCH=1
[ "$2" != "" ] && START_BATCH="$2"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# Wait until all expected results.json files exist
wait_for_results() {
    local dir="$1"; shift
    local scenarios=("$@")
    while true; do
        local n=0
        for s in "${scenarios[@]}"; do [ -f "$dir/$s/results.json" ] && ((n++)); done
        log "  Results: $n/${#scenarios[@]} in $dir"
        [ "$n" -eq "${#scenarios[@]}" ] && return
        sleep 120
    done
}

# Wait until no 3_run_sweep.py processes remain for given namespaces
wait_for_runners() {
    while true; do
        local alive=0
        for ns in "$@"; do
            ps aux | grep 3_run_sweep | grep -qv grep && \
            ps aux | grep 3_run_sweep | grep -v grep | grep -q "namespace $ns" && ((alive++))
        done
        [ "$alive" -eq 0 ] && return
        log "  $alive runner(s) still active, waiting..."
        sleep 60
    done
}

# Launch a group of scenarios with a small intra-group stagger
launch_group() {
    local retarget="$1"; local results_dir="$2"; shift 2
    for ns in "$@"; do
        local i="${ns##*-}"
        local scenario="sweep_$(printf '%04d' "$i")"
        log "  Launching $ns → $scenario (retarget=$retarget)"
        python tools/sweep/3_run_sweep.py \
            --input "$ESP_MANIFEST" \
            --scenarios "$scenario" \
            --namespace "$ns" \
            --results-dir "$results_dir" \
            --duration 13000 \
            --retarget-interval "$retarget" \
            --interval 2 \
            > "/tmp/sweep_${ns//-/_}.log" 2>&1 &
        sleep 8
    done
}

# Check bridge port headroom before launching
check_ports() {
    local used
    used=$(minikube ssh "ls /sys/class/net/bridge/brif/ 2>/dev/null | wc -l" 2>/dev/null | tr -d '\r\n ')
    local needed="$1"
    log "Bridge ports: $used used, need $needed more (limit 1024)"
    if (( used + needed > 1000 )); then
        log "ERROR: Not enough bridge port headroom. Aborting."
        exit 1
    fi
}

log "ESP Batched Launcher starting (START_BATCH=$START_BATCH)"
log "Batches:"
log "  1: esp-144-6/7/8 + esp-2016-0/1/2  (366 pods)  — after esp-144-0..5 finishes"
log "  2: esp-2016-3/4/5                   (183 pods)  — after batch 1 finishes"
log "  3: esp-2016-6/7/8                   (183 pods)  — after batch 2 finishes"
log ""

# ── Batch 1 ──────────────────────────────────────────────────────────────────
if (( START_BATCH <= 1 )); then
    log "=== Waiting for esp-144-0..5 to complete ==="
    wait_for_results "targeted_sweep7_esp/results_144" \
        sweep_0000 sweep_0001 sweep_0002 sweep_0003 sweep_0004 sweep_0005
    wait_for_runners esp-144-0 esp-144-1 esp-144-2 esp-144-3 esp-144-4 esp-144-5
    log "esp-144-0..5 done. Sleeping 180s for bridge port cleanup..."
    sleep 180

    log "=== Launching Batch 1 ==="
    check_ports 366
    # Pre-create namespaces (warnet deploy doesn't create them)
    for ns in esp-144-6 esp-144-7 esp-144-8 esp-2016-0 esp-2016-1 esp-2016-2; do
        kubectl get namespace "$ns" &>/dev/null || kubectl create namespace "$ns"
    done
    launch_group 144  targeted_sweep7_esp/results_144  esp-144-6 esp-144-7 esp-144-8
    sleep 30
    launch_group 2016 targeted_sweep7_esp/results_2016 esp-2016-0 esp-2016-1 esp-2016-2
    log "Batch 1 launched. Waiting for completion..."
    wait_for_results "targeted_sweep7_esp/results_144"  sweep_0006 sweep_0007 sweep_0008
    wait_for_results "targeted_sweep7_esp/results_2016" sweep_0000 sweep_0001 sweep_0002
    wait_for_runners esp-144-6 esp-144-7 esp-144-8 esp-2016-0 esp-2016-1 esp-2016-2
    log "Batch 1 complete. Sleeping 180s..."
    sleep 180
fi

# ── Batch 2 ──────────────────────────────────────────────────────────────────
if (( START_BATCH <= 2 )); then
    log "=== Launching Batch 2 ==="
    check_ports 183
    for ns in esp-2016-3 esp-2016-4 esp-2016-5; do
        kubectl get namespace "$ns" &>/dev/null || kubectl create namespace "$ns"
    done
    launch_group 2016 targeted_sweep7_esp/results_2016 esp-2016-3 esp-2016-4 esp-2016-5
    log "Batch 2 launched. Waiting for completion..."
    wait_for_results "targeted_sweep7_esp/results_2016" sweep_0003 sweep_0004 sweep_0005
    wait_for_runners esp-2016-3 esp-2016-4 esp-2016-5
    log "Batch 2 complete. Sleeping 180s..."
    sleep 180
fi

# ── Batch 3 ──────────────────────────────────────────────────────────────────
if (( START_BATCH <= 3 )); then
    log "=== Launching Batch 3 ==="
    check_ports 183
    for ns in esp-2016-6 esp-2016-7 esp-2016-8; do
        kubectl get namespace "$ns" &>/dev/null || kubectl create namespace "$ns"
    done
    launch_group 2016 targeted_sweep7_esp/results_2016 esp-2016-6 esp-2016-7 esp-2016-8
    log "Batch 3 launched. Waiting for completion..."
    wait_for_results "targeted_sweep7_esp/results_2016" sweep_0006 sweep_0007 sweep_0008
    wait_for_runners esp-2016-6 esp-2016-7 esp-2016-8
    log "Batch 3 complete."
fi

log ""
log "=== All ESP batches complete! ==="
log "Run: python tools/monitor_sweeps.py to check final results."
