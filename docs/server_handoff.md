# Server Handoff Briefing
**Date:** 2026-03-16 (updated with hard-won infrastructure lessons)
**Purpose:** Context for running large-scale sweeps on the 80-core / 187.5 GiB server

---

## Project Overview

Bitcoin fork dynamics simulation using warnet (Kubernetes/minikube). Parameter sweeps over a
simulated Bitcoin network map conditions under which a soft fork (v27) wins vs the
incumbent chain (v26). Results feed a research paper.

**Repo:** `warnetScenarioDiscovery`
**Sibling repo:** `../warnet/` must exist (symlinks in repo root point there)
**Both patches in `docs/warnet_control_patch.diff` must be applied to `../warnet/` before running.**

---

## CRITICAL: Infrastructure Limits

### 1. Linux Bridge Port Limit (1024 max) ← most important

The default minikube CNI uses a single Linux bridge. Each pod = one bridge port.
**Hard kernel limit: 1024 ports.** Exceeding it silently fails all new pod creation with
`exchange full`. This is NOT tunable without rebuilding the kernel.

- grid2016 (9 ns × 61 pods = 549) + esp-144 all 9 (366) + system (~10) = ~925 → at the ceiling
- **Never launch all ESP scenarios while grid2016 is running simultaneously**
- Use `tools/launch_esp_batched.sh` which launches in capacity-aware batches

**Fix for future runs:** Use Flannel CNI (VXLAN — no bridge, no limit):
```bash
minikube start --cni=flannel --max-pods=1800 \
  --extra-config=kubelet.cgroup-driver=cgroupfs \
  --memory=180g --cpus=80
```

### 2. cgroupv2 + Docker systemd driver

Creating 500+ pods simultaneously overwhelms systemd D-Bus. Symptoms: `operation timeout:
context deadline exceeded` on pod sandbox creation.

**Fix:** Use cgroupfs driver. Add to `/etc/docker/daemon.json`:
```json
{"exec-opts": ["native.cgroupdriver=cgroupfs"]}
```
Then restart minikube with `--extra-config=kubelet.cgroup-driver=cgroupfs`.

### 3. warnet archive upload timeout

`warnet run` uploads the scenario `.pyz` archive to the commander init container. Default
timeout is 300s — under load, sandbox creation takes longer, upload silently fails,
commander stays `Init:0/1` forever.

**Fix:** Apply `docs/warnet_control_patch.diff` (increases timeout to 600s).

### 4. Namespace pre-creation required

`warnet deploy` does NOT create namespaces. Always pre-create before running:
```bash
kubectl create namespace <ns>
```

### 5. YAML race condition (parallel config injection)

9 parallel runners all write to `scenarios/config/mining_pools_config.yaml`.
**Fix already in `tools/sweep/3_run_sweep.py`:** `fcntl.flock` exclusive locking.

---

## Required Warnet Patches

Apply `docs/warnet_control_patch.diff` to `../warnet/src/warnet/control.py` before running.
Both patches are already applied on this server — verify with:
```bash
grep -n "wait_for_init\|\"lib/\"\|\"config/\"" ../warnet/src/warnet/control.py
```
Expected output:
- line ~363: `"lib/",` and `"config/",` in the archive filter list
- line ~438: `wait_for_init(name, namespace=namespace, timeout=600)`

---

## Sweep Infrastructure

```bash
# Step 1: generate scenarios (ALREADY DONE for both sweeps — skip)
python tools/sweep/1_generate_targeted.py --spec tools/sweep/specs/<name>.yaml

# Step 2: build configs (run once per sweep)
python tools/sweep/2_build_configs.py \
  --input tools/sweep/<name>/scenarios.json \
  --output-dir tools/sweep/<name> \
  --base-network networks/realistic-economy-v2/network.yaml

# Step 3: run sweep (see per-sweep instructions below)
python tools/sweep/3_run_sweep.py \
  --input tools/sweep/<name>/build_manifest.json \
  --namespace <ns> --scenarios <ids> \
  --results-dir <name>/results \
  --duration 13000 --retarget-interval <144|2016> --interval 2

# Step 4: analyze results
python tools/sweep/4_analyze_results.py \
  --input <name>/results \
  --manifest tools/sweep/<name>/build_manifest.json
```

Results land in **repo root** (e.g. `econ_committed_2016_grid/results/`), not inside `tools/sweep/`.

---

## Monitoring

```bash
python tools/monitor_sweeps.py            # one-shot status
python tools/monitor_sweeps.py --watch    # live refresh every 60s
tmux attach -t esp_batched                # watch batched ESP launcher
tail -f /tmp/launch_esp_batched.log       # same, without attaching
```

Per-namespace pod check:
```bash
kubectl get pods --all-namespaces | grep commander   # see all commander states
minikube ssh "ls /sys/class/net/bridge/brif/ | wc -l"  # bridge port count (keep <950)
```

---

## Sweep 1: `econ_committed_2016_grid` — HIGHEST PRIORITY

**45 scenarios** (5 econ × 9 committed_split), full 60-node network, 2016-block
retarget, baseline oracle. Fills §4.5 Table 6 — the full 2D decision boundary.

### Scenario layout

```
economic_split \ pool_committed_split:
         0.20  0.30  0.38  0.43  0.47  0.52  0.58  0.65  0.75
econ=0.35: 0000  0001  0002  0003  0004  0005  0006  0007  0008
econ=0.50: 0009  0010  0011  0012  0013  0014  0015  0016  0017
econ=0.60: 0018  0019  0020  0021  0022  0023  0024  0025  0026
econ=0.70: 0027  0028  0029  0030  0031  0032  0033  0034  0035
econ=0.82: 0036  0037  0038  0039  0040  0041  0042  0043  0044
```

### Run (9 namespaces × 5 scenarios, ~18h wall-clock)

Use `tools/launch_staggered.sh` or run manually. Pre-create namespaces first.

```bash
for ns in grid2016-c0 grid2016-c1 grid2016-c2 grid2016-c3 grid2016-c4 \
          grid2016-c5 grid2016-c6 grid2016-c7 grid2016-c8; do
  kubectl create namespace $ns
done

# Launch 3 at a time, 90s between groups to avoid cgroup burst
python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0000 sweep_0009 sweep_0018 sweep_0027 sweep_0036 \
  --namespace grid2016-c0 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &
# ... (repeat for c1-c8, see tools/launch_staggered.sh)
```

---

## Sweep 2: `targeted_sweep7_esp` — HIGH PRIORITY

**9 scenarios**, full 60-node network. Economic Self-Sustaining Point (ESP) sweep —
maps the minimum economic majority at which v27 becomes self-reinforcing. Run at
**both** 144-block and 2016-block retarget.

`econ_split` grid: [0.28, 0.35, 0.45, 0.55, 0.60, 0.65, 0.70, 0.78, 0.85]
`pool_committed_split` fixed at 0.214 (Foundry flip-point), `hashrate_split` = 0.25

### ⚠️ Bridge port constraint — use batched launcher

**Do NOT launch all 18 ESP namespaces at once while grid2016 is running.**
The combined pod count will exceed the 1024 bridge port limit.

**Correct approach** (automated):
```bash
# Run in a tmux/screen session — handles all batches automatically
bash tools/launch_esp_batched.sh

# Resume from a specific batch if needed:
bash tools/launch_esp_batched.sh --batch 2
bash tools/launch_esp_batched.sh --batch 3
```

Batch schedule (while grid2016 is running):
| Batch | Namespaces | ~When |
|-------|------------|-------|
| 1 | esp-144-6/7/8 + esp-2016-0/1/2 | after esp-144-0..5 finishes |
| 2 | esp-2016-3/4/5 | after batch 1 finishes |
| 3 | esp-2016-6/7/8 | after batch 2 finishes |

esp-144-0..5 can run **simultaneously** with grid2016 (within the port budget).

### Manual run (if grid2016 is NOT running, or using Flannel CNI)

```bash
# Pre-create all namespaces first
for i in 0 1 2 3 4 5 6 7 8; do
  kubectl create namespace esp-144-$i
  kubectl create namespace esp-2016-$i
done

# 144-block (~3.6h)
for i in 0 1 2 3 4 5 6 7 8; do
  python tools/sweep/3_run_sweep.py \
    --input tools/sweep/targeted_sweep7_esp/build_manifest.json \
    --scenarios sweep_000$i --namespace esp-144-$i \
    --results-dir targeted_sweep7_esp/results_144 \
    --duration 13000 --retarget-interval 144 --interval 2 &
  sleep 8
done

# 2016-block (~3.6h, can overlap with 144-block)
for i in 0 1 2 3 4 5 6 7 8; do
  python tools/sweep/3_run_sweep.py \
    --input tools/sweep/targeted_sweep7_esp/build_manifest.json \
    --scenarios sweep_000$i --namespace esp-2016-$i \
    --results-dir targeted_sweep7_esp/results_2016 \
    --duration 13000 --retarget-interval 2016 --interval 2 &
  sleep 8
done
```

---

## Key Context for Interpreting Results

**Economic node quantization:** The network has ~4 econ nodes with skewed custody
(56.7% / 43.3%). Node assignment is discrete — not a smooth variable:
- `econ_split < ~0.30` → 0 nodes on v27 → **v26 always wins**
- `econ_split ≥ ~0.30` → 1 node (56.7% custody) → v27 can win
- `econ_split ~0.82+` → 2 nodes (99.6%) → very fast cascade

**committed_split threshold:** ∈(0.20, 0.30) — below this v27 has insufficient
committed hashrate to accumulate 2016 blocks before v26 retargets. This threshold
is the same in both 144-block and 2016-block regimes.

**pool_committed_split semantics:**
`v27_pct = (1 - neutral_pct/100) * committed_split`
e.g. split=0.35, neutral=30%: v27=24.5%, v26=45.5%

**2016-block cascade timing (baseline oracle):**
- 1-node econ (56.7%): cascade_t ≈ 8426s, peak_gap ≈ 16%
- 2-node econ (99.6%): cascade_t ≈ 607s, peak_gap ≈ 47%
- Duration=13000s is calibrated to capture the full cascade with margin

**Econ switching threshold (validated params):**
`effective_threshold = 0.10 * (1 + 0.40 * 2.0) = 0.18` (18%)
Baseline oracle peak_gap ≈ 16% → below threshold → econ nodes never switch
Sigmoid oracle peak_gap ≈ 40% → above threshold → full econ switch possible

---

## Debugging Common Failures

### Commander stuck in `Init:0/1`

Either the archive upload failed or the pod sandbox never created.
Check: `cat <results_dir>/<scenario_id>/scenario.log`

- `"Timeout waiting for initContainer"` + `"container not found (init)"` → archive upload failed
  - Fix: archive will never arrive. Kill runner, delete namespace, relaunch.
- `"namespace not found"` → namespace wasn't pre-created before warnet run
  - Fix: `kubectl create namespace <ns>`, then relaunch runner.
- `"exchange full"` on pods → bridge port limit hit (see above)
- `"operation timeout: context deadline exceeded"` → cgroup pressure (see above)

### Checking scenario logs (runner output is buffered)

`/tmp/sweep_*.log` is often empty while running — Python stdout is fully buffered when
redirected to file. Check per-scenario logs instead:
```bash
cat targeted_sweep7_esp/results_144/sweep_0006/scenario.log
```

### Killing and relaunching stuck runners

```bash
# Find PIDs
ps aux | grep 3_run_sweep | grep "namespace esp-144-6" | awk '{print $2}'

# Kill, delete namespace, pre-create, relaunch
kill <pid>
kubectl delete namespace esp-144-6 --wait=false
sleep 120   # wait for pods to terminate
kubectl create namespace esp-144-6
python tools/sweep/3_run_sweep.py --input ... --namespace esp-144-6 ... &
```
