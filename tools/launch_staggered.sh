#!/bin/bash
# Staggered sweep launcher — 3 namespaces per group, 120s between groups.
# Prevents systemd cgroup creation timeouts from 1600+ simultaneous pod creations.
# Groups are ordered by priority: grid2016 first, then ESP sweeps.

set -e
cd "$(dirname "$0")/.."

GRID_MANIFEST="tools/sweep/econ_committed_2016_grid/build_manifest.json"
ESP_MANIFEST="tools/sweep/targeted_sweep7_esp/build_manifest.json"
STAGGER=120  # seconds between groups

launch_group() {
    local label="$1"
    echo ""
    echo "========================================"
    echo "  Launching group: $label  ($(date '+%H:%M:%S'))"
    echo "========================================"
}

wait_group() {
    echo "  Waiting ${STAGGER}s for systemd to settle before next group..."
    sleep $STAGGER
}

# ── Group 1: grid2016 c0/c1/c2 ───────────────────────────────────────────────
launch_group "grid2016 c0/c1/c2"
python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0000 sweep_0009 sweep_0018 sweep_0027 sweep_0036 \
  --namespace grid2016-c0 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c0.log 2>&1 &

python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0001 sweep_0010 sweep_0019 sweep_0028 sweep_0037 \
  --namespace grid2016-c1 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c1.log 2>&1 &

python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0002 sweep_0011 sweep_0020 sweep_0029 sweep_0038 \
  --namespace grid2016-c2 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c2.log 2>&1 &

wait_group

# ── Group 2: grid2016 c3/c4/c5 ───────────────────────────────────────────────
launch_group "grid2016 c3/c4/c5"
python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0003 sweep_0012 sweep_0021 sweep_0030 sweep_0039 \
  --namespace grid2016-c3 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c3.log 2>&1 &

python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0004 sweep_0013 sweep_0022 sweep_0031 sweep_0040 \
  --namespace grid2016-c4 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c4.log 2>&1 &

python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0005 sweep_0014 sweep_0023 sweep_0032 sweep_0041 \
  --namespace grid2016-c5 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c5.log 2>&1 &

wait_group

# ── Group 3: grid2016 c6/c7/c8 ───────────────────────────────────────────────
launch_group "grid2016 c6/c7/c8"
python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0006 sweep_0015 sweep_0024 sweep_0033 sweep_0042 \
  --namespace grid2016-c6 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c6.log 2>&1 &

python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0007 sweep_0016 sweep_0025 sweep_0034 sweep_0043 \
  --namespace grid2016-c7 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c7.log 2>&1 &

python tools/sweep/3_run_sweep.py --input $GRID_MANIFEST \
  --scenarios sweep_0008 sweep_0017 sweep_0026 sweep_0035 sweep_0044 \
  --namespace grid2016-c8 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_c8.log 2>&1 &

wait_group

# ── Group 4: esp-144 0/1/2 ───────────────────────────────────────────────────
launch_group "esp-144 0/1/2"
for i in 0 1 2; do
  python tools/sweep/3_run_sweep.py --input $ESP_MANIFEST \
    --scenarios sweep_000$i --namespace esp-144-$i \
    --results-dir targeted_sweep7_esp/results_144 \
    --duration 13000 --retarget-interval 144 --interval 2 > /tmp/sweep_esp144_$i.log 2>&1 &
done

wait_group

# ── Group 5: esp-144 3/4/5 ───────────────────────────────────────────────────
launch_group "esp-144 3/4/5"
for i in 3 4 5; do
  python tools/sweep/3_run_sweep.py --input $ESP_MANIFEST \
    --scenarios sweep_000$i --namespace esp-144-$i \
    --results-dir targeted_sweep7_esp/results_144 \
    --duration 13000 --retarget-interval 144 --interval 2 > /tmp/sweep_esp144_$i.log 2>&1 &
done

wait_group

# ── Group 6: esp-144 6/7/8 ───────────────────────────────────────────────────
launch_group "esp-144 6/7/8"
for i in 6 7 8; do
  python tools/sweep/3_run_sweep.py --input $ESP_MANIFEST \
    --scenarios sweep_000$i --namespace esp-144-$i \
    --results-dir targeted_sweep7_esp/results_144 \
    --duration 13000 --retarget-interval 144 --interval 2 > /tmp/sweep_esp144_$i.log 2>&1 &
done

wait_group

# ── Group 7: esp-2016 0/1/2 ──────────────────────────────────────────────────
launch_group "esp-2016 0/1/2"
for i in 0 1 2; do
  python tools/sweep/3_run_sweep.py --input $ESP_MANIFEST \
    --scenarios sweep_000$i --namespace esp-2016-$i \
    --results-dir targeted_sweep7_esp/results_2016 \
    --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_esp2016_$i.log 2>&1 &
done

wait_group

# ── Group 8: esp-2016 3/4/5 ──────────────────────────────────────────────────
launch_group "esp-2016 3/4/5"
for i in 3 4 5; do
  python tools/sweep/3_run_sweep.py --input $ESP_MANIFEST \
    --scenarios sweep_000$i --namespace esp-2016-$i \
    --results-dir targeted_sweep7_esp/results_2016 \
    --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_esp2016_$i.log 2>&1 &
done

wait_group

# ── Group 9: esp-2016 6/7/8 ──────────────────────────────────────────────────
launch_group "esp-2016 6/7/8"
for i in 6 7 8; do
  python tools/sweep/3_run_sweep.py --input $ESP_MANIFEST \
    --scenarios sweep_000$i --namespace esp-2016-$i \
    --results-dir targeted_sweep7_esp/results_2016 \
    --duration 13000 --retarget-interval 2016 --interval 2 > /tmp/sweep_esp2016_$i.log 2>&1 &
done

echo ""
echo "========================================"
echo "  All 9 groups launched! ($(date '+%H:%M:%S'))"
echo "  Total processes: $(ps aux | grep 3_run_sweep | grep -v grep | wc -l)"
echo "========================================"
