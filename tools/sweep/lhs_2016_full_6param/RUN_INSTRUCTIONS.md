# lhs_2016_full_6param — Run Instructions

**720 scenarios — unbiased 6-parameter LHS, 2016-block retarget, full 60-node network**
**Server 1: namespaces lhs26-0 to lhs26-5 (sweep_0000–sweep_0359)**
**Server 2: namespaces lhs26-6 to lhs26-11 (sweep_0360–sweep_0719)**

---

## Step 1: Generate Scenarios (dev machine, run once)

```bash
cd ~/bitcoin/warnetScenarioDiscovery

python tools/sweep/1_generate_scenarios.py \
    --spec tools/sweep/specs/lhs_2016_full_6param.yaml \
    --output tools/sweep/lhs_2016_full_6param/scenarios.json
```

Verify: `scenarios.json` should contain 720 entries with 6 LHS parameters + 10 fixed.

---

## Step 2: Build Configs (dev machine, run once)

```bash
python tools/sweep/2_build_configs.py \
    --input tools/sweep/lhs_2016_full_6param/scenarios.json \
    --output-dir tools/sweep/lhs_2016_full_6param \
    --network full
```

Generates `build_manifest.json` and `configs/` (720 network yamls).

---

## Step 3: Sync to Servers (dev machine)

```bash
rsync -av tools/sweep/lhs_2016_full_6param/ \
    server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_full_6param/

rsync -av tools/sweep/lhs_2016_full_6param/ \
    server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_full_6param/
```

---

## Step 4: Verify Cluster Capacity (on each server)

```bash
kubectl get node -o jsonpath='{.items[0].status.allocatable.pods}'   # should be 600
kubectl get pods --all-namespaces --no-headers | wc -l               # current pod count
# Each 60-node scenario = ~61 pods. 6 parallel namespaces = ~366 pods + system overhead.
# Well within k3s maxPods=600.
```

---

## Step 5: Create Namespaces

**Server 1:**
```bash
for i in $(seq 0 5); do kubectl create namespace lhs26-$i; done
```

**Server 2:**
```bash
for i in $(seq 6 11); do kubectl create namespace lhs26-$i; done
```

---

## Step 6: Run Scenarios

Start each namespace in its own tmux pane. Stagger launches by ~2 minutes between
namespaces on the same server to avoid simultaneous `network_metadata.yaml` injection
on the first scenario of each namespace.

All commands run from `~/bitcoin/warnetScenarioDiscovery/`.

### Server 1 (sweep_0000–sweep_0359)

**Namespace lhs26-0 — sweep_0000 to sweep_0059**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server1/ns-0 \
    --namespace lhs26-0 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 0 59))
```

**Namespace lhs26-1 — sweep_0060 to sweep_0119**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server1/ns-1 \
    --namespace lhs26-1 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 60 119))
```

**Namespace lhs26-2 — sweep_0120 to sweep_0179**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server1/ns-2 \
    --namespace lhs26-2 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 120 179))
```

**Namespace lhs26-3 — sweep_0180 to sweep_0239**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server1/ns-3 \
    --namespace lhs26-3 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 180 239))
```

**Namespace lhs26-4 — sweep_0240 to sweep_0299**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server1/ns-4 \
    --namespace lhs26-4 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 240 299))
```

**Namespace lhs26-5 — sweep_0300 to sweep_0359**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server1/ns-5 \
    --namespace lhs26-5 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 300 359))
```

---

### Server 2 (sweep_0360–sweep_0719)

**Namespace lhs26-6 — sweep_0360 to sweep_0419**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server2/ns-6 \
    --namespace lhs26-6 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 360 419))
```

**Namespace lhs26-7 — sweep_0420 to sweep_0479**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server2/ns-7 \
    --namespace lhs26-7 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 420 479))
```

**Namespace lhs26-8 — sweep_0480 to sweep_0539**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server2/ns-8 \
    --namespace lhs26-8 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 480 539))
```

**Namespace lhs26-9 — sweep_0540 to sweep_0599**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server2/ns-9 \
    --namespace lhs26-9 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 540 599))
```

**Namespace lhs26-10 — sweep_0600 to sweep_0659**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server2/ns-10 \
    --namespace lhs26-10 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 600 659))
```

**Namespace lhs26-11 — sweep_0660 to sweep_0719**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_6param/results_server2/ns-11 \
    --namespace lhs26-11 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 660 719))
```

---

## Monitoring

```bash
# Watch all lhs26 pods on current server
watch -n 30 'kubectl get pods --all-namespaces | grep lhs26 | awk "{print \$1, \$4}" | sort | uniq -c'

# Progress across all namespaces
python3 -c "
import json, glob
for f in sorted(glob.glob('tools/sweep/lhs_2016_full_6param/results_server*/ns-*/sweep_progress.json')):
    p = json.load(open(f))
    print(f'{f}: completed={p[\"completed\"]} failed={p[\"failed\"]}')
"
```

---

## Step 7: Collect Results (dev machine)

After both servers complete:

```bash
rsync -av server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_full_6param/results_server1/ \
    tools/sweep/lhs_2016_full_6param/results/

rsync -av server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_full_6param/results_server2/ \
    tools/sweep/lhs_2016_full_6param/results/
```

---

## Step 8: Analyze

```bash
# Analyze results
python tools/sweep/4_analyze_results.py \
    --results-dir tools/sweep/lhs_2016_full_6param/results \
    --output-dir tools/sweep/lhs_2016_full_6param/analysis

# Add to database
python tools/sweep/5_build_database.py

# Fit full-network 2016-block boundary — RF, logistic, PRIM
python tools/discovery/fit_boundary.py \
    --regime 2016 \
    --network full \
    --output-dir tools/discovery/output/2016_full_6param

# Derive new full-network PRIM uncertainty box for Phase 3c
# Target econ ∈ [0.50, 0.65] per section_4_10.md §4.10.3
python tools/discovery/fit_boundary.py \
    --regime 2016 \
    --network full \
    --mode uncertainty \
    --econ-range 0.50 0.65 \
    --output-dir tools/discovery/output/2016_full_phase3c_bounds
```

---

## Notes

- **`--no-auto-restart`**: Required on k3s servers
- **`--interval 2`**: 2-second block interval, matching all prior 2016-block sweeps
- **`--duration 13000`**: Consistent with all prior 2016-block sweeps for direct comparability
- **`--startup-wait 60`**: Full 60-node networks need longer pod startup time than lite
- **Stagger starts**: Wait ~2 minutes between namespace launches on the same server
- **Resume**: Re-run the same command if a worker stops — completed scenarios are skipped
- **Pod count**: 6 parallel namespaces × ~61 pods = ~366 pods per server. Within k3s maxPods=600.
- **Follow-on**: After analysis, use `tools/discovery/output/2016_full_phase3c_bounds/` as
  input bounds for the Phase 3c spec (lhs_2016_full_phase3c). See section_4_10.md §4.10.3.
