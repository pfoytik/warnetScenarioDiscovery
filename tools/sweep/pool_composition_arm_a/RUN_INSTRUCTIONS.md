# Arm A: Pool Composition Decoupling — Run Instructions

**168 scenarios — 6 namespaces per server, manually launched**
**Server 1: namespaces arma-0 to arma-5 (sweep_0000–sweep_0083)**
**Server 2: namespaces arma-6 to arma-11 (sweep_0084–sweep_0167)**

Each namespace runs 14 scenarios sequentially. Stagger namespace launches by ~2 minutes.

---

## Pre-flight (both servers)

```bash
cd ~/warnetScenarioDiscovery
git pull
warnet status
kubectl get node -o jsonpath='{.items[0].status.allocatable.pods}'  # should be 600
kubectl get pods --all-namespaces --no-headers | wc -l              # current pod count
```

---

## Create Namespaces

**Server 1:**
```bash
for i in $(seq 0 5); do kubectl create namespace arma-$i; done
```

**Server 2:**
```bash
for i in $(seq 6 11); do kubectl create namespace arma-$i; done
```

---

## Server 1 (sweep_0000–sweep_0083)

Start each in its own tmux pane. Wait ~2 minutes between launches.

**Namespace arma-0 — sweep_0000 to sweep_0013**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server1/ns-0 \
    --namespace arma-0 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 0 13))
```

**Namespace arma-1 — sweep_0014 to sweep_0027**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server1/ns-1 \
    --namespace arma-1 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 14 27))
```

**Namespace arma-2 — sweep_0028 to sweep_0041**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server1/ns-2 \
    --namespace arma-2 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 28 41))
```

**Namespace arma-3 — sweep_0042 to sweep_0055**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server1/ns-3 \
    --namespace arma-3 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 42 55))
```

**Namespace arma-4 — sweep_0056 to sweep_0069**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server1/ns-4 \
    --namespace arma-4 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 56 69))
```

**Namespace arma-5 — sweep_0070 to sweep_0083**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server1/ns-5 \
    --namespace arma-5 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 70 83))
```

---

## Server 2 (sweep_0084–sweep_0167)

Start each in its own tmux pane. Wait ~2 minutes between launches.

**Namespace arma-6 — sweep_0084 to sweep_0097**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server2/ns-6 \
    --namespace arma-6 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 84 97))
```

**Namespace arma-7 — sweep_0098 to sweep_0111**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server2/ns-7 \
    --namespace arma-7 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 98 111))
```

**Namespace arma-8 — sweep_0112 to sweep_0125**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server2/ns-8 \
    --namespace arma-8 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 112 125))
```

**Namespace arma-9 — sweep_0126 to sweep_0139**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server2/ns-9 \
    --namespace arma-9 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 126 139))
```

**Namespace arma-10 — sweep_0140 to sweep_0153**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server2/ns-10 \
    --namespace arma-10 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 140 153))
```

**Namespace arma-11 — sweep_0154 to sweep_0167**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_a/build_manifest.json \
    --results-dir tools/sweep/pool_composition_arm_a/results_server2/ns-11 \
    --namespace arma-11 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 154 167))
```

---

## Monitoring

```bash
# Watch all arma pods on current server
watch -n 30 'kubectl get pods --all-namespaces | grep arma | awk "{print \$1, \$4}" | sort | uniq -c'

# Progress across all namespaces
python3 -c "
import json, glob
for f in sorted(glob.glob('tools/sweep/pool_composition_arm_a/results_server*/ns-*/sweep_progress.json')):
    p = json.load(open(f))
    print(f'{f}: completed={p[\"completed\"]} failed={p[\"failed\"]}')
"
```

---

## Collect via git

When each server finishes:
```bash
cd ~/warnetScenarioDiscovery
git add tools/sweep/pool_composition_arm_a/results_server1/   # or results_server2
git commit -m "pool_composition_arm_a results server1"
git push
```

Dev machine:
```bash
git pull
```

---

## Load into database

```bash
python tools/sweep/5_build_database.py \
  --results-dir tools/sweep/pool_composition_arm_a/results_server1 \
  --sweep-name pool_composition_arm_a \
  --db tools/sweep/sweep_results.db

python tools/sweep/5_build_database.py \
  --results-dir tools/sweep/pool_composition_arm_a/results_server2 \
  --sweep-name pool_composition_arm_a \
  --db tools/sweep/sweep_results.db
```

---

## Notes

- **`--no-auto-restart`**: Required on k3s servers
- **`--interval 2`**: 2-second block interval, matching all prior 2016-block sweeps
- **`--duration 13000`**: One full 2016-block retarget cycle (~4032s) plus buffer
- **`--startup-wait 60`**: Lite network; 60s is sufficient (full network needs longer)
- **Stagger starts**: Wait ~2 minutes between namespace launches on the same server
- **Resume**: Re-run the same command if a worker stops — completed scenarios are skipped
- **Pod count**: 6 parallel namespaces × ~49 pods (lite) = ~294 pods per server. Well within k3s maxPods=600.
- **Timing**: 14 scenarios × 3.6h each = ~50h wall-clock per server, both running simultaneously
