#!/bin/bash
# Safe ESP launcher — runs scenarios 2 at a time (1×144-block + 1×2016-block),
# waits for runner processes to exit before launching the next pair.
# Safe to run alongside the econ_committed_2016_grid sweep.
#
# Usage:
#   bash tools/launch_esp_safe.sh              # run all 9 pairs (0-8)
#   bash tools/launch_esp_safe.sh --start 3   # resume from pair index 3
#
# Each pair takes ~4.2 hours (13000s scenario + 1800s buffer + overhead).
# Total for all 9 pairs: ~38 hours unattended.

set -uo pipefail
cd "$(dirname "$0")/.."

ESP_MANIFEST="tools/sweep/targeted_sweep7_esp/build_manifest.json"
START_PAIR=0
[ "${2:-}" != "" ] && START_PAIR="$2"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# Check results.json exists for a scenario, log warning if not.
check_result() {
    local dir="$1" scenario="$2"
    if [ -f "$dir/$scenario/results.json" ]; then
        log "  ✓ $scenario: results.json present"
    else
        log "  ✗ $scenario: results.json MISSING — extraction may have failed"
    fi
}

# Check bridge port headroom (user must be able to run minikube ssh).
check_ports() {
    local needed="$1"
    local used
    used=$(minikube ssh "ls /sys/class/net/bridge/brif/ 2>/dev/null | wc -l" 2>/dev/null | tr -d '\r\n ') || {
        log "  WARNING: Could not check bridge ports (minikube ssh failed) — proceeding anyway"
        return 0
    }
    log "Bridge ports: $used used, need ~$needed more (limit 1024)"
    if (( used + needed > 1000 )); then
        log "ERROR: Not enough bridge port headroom ($used + $needed > 1000). Aborting."
        exit 1
    fi
}

# Ensure namespace exists.
ensure_ns() {
    kubectl get namespace "$1" &>/dev/null || kubectl create namespace "$1"
}

# Launch a single scenario in the background.
# Caller must capture $! immediately after calling this function.
launch_one() {
    local ns="$1" retarget="$2" results_dir="$3" scenario="$4"
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
}

log "ESP Safe Launcher — running pairs of (144-block, 2016-block), 2 at a time"
log "START_PAIR=$START_PAIR  (pairs 0-8, each ~4.2 hours)"
log ""

for i in $(seq "$START_PAIR" 8); do
    scenario="sweep_$(printf '%04d' "$i")"
    ns144="esp-144-$i"
    ns2016="esp-2016-$i"

    log "════════════════════════════════════════"
    log "=== Pair $i: $ns144 + $ns2016 → $scenario ==="
    log "════════════════════════════════════════"

    # Skip if both already have results
    has144=0; has2016=0
    [ -f "targeted_sweep7_esp/results_144/$scenario/results.json" ] && has144=1 || true
    [ -f "targeted_sweep7_esp/results_2016/$scenario/results.json" ] && has2016=1 || true
    if [ "$has144" -eq 1 ] && [ "$has2016" -eq 1 ]; then
        log "  Both results.json already present — skipping pair $i"
        continue
    fi

    # Bridge port check: 2 networks × ~61 pods = ~122 additional ports
    check_ports 122

    ensure_ns "$ns144"
    ensure_ns "$ns2016"

    pids=()

    if [ "$has144" -eq 0 ]; then
        launch_one "$ns144" 144  "targeted_sweep7_esp/results_144"  "$scenario"
        pids+=("$!")
        sleep 30  # stagger to avoid simultaneous commander deploys
    else
        log "  Skipping $ns144 — results.json already present"
    fi

    if [ "$has2016" -eq 0 ]; then
        launch_one "$ns2016" 2016 "targeted_sweep7_esp/results_2016" "$scenario"
        pids+=("$!")
    else
        log "  Skipping $ns2016 — results.json already present"
    fi

    log "  Pair $i launched (PIDs: ${pids[*]}). Waiting for runners to exit..."
    wait "${pids[@]}" || true

    # Check results
    check_result "targeted_sweep7_esp/results_144"  "$scenario"
    check_result "targeted_sweep7_esp/results_2016" "$scenario"

    if (( i < 8 )); then
        log "  Sleeping 180s for bridge port cleanup before next pair..."
        sleep 180
    fi
done

log ""
log "=== All ESP pairs complete! ==="
log "Run: python tools/monitor_sweeps.py to check final results."
