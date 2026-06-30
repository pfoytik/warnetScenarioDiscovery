# Softfork Rule Strength Sweep — Run Instructions

**96 scenarios — 6 namespaces per server, 8 scenarios per namespace**
**Server 1: namespaces srs-0 to srs-5 (sweep_0000–sweep_0047) — p = 0.00, 0.10, 0.25**
**Server 2: namespaces srs-6 to srs-11 (sweep_0048–sweep_0095) — p = 0.50, 0.75, 1.00**

Each namespace runs 8 scenarios sequentially. Stagger namespace launches by ~2 minutes.

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
for i in $(seq 0 5); do kubectl create namespace srs-$i; done
```

**Server 2:**
```bash
for i in $(seq 6 11); do kubectl create namespace srs-$i; done
```

---

## Server 1 (sweep_0000–sweep_0047) — p = 0.00, 0.10, 0.25

Start each in its own tmux pane. Wait ~2 minutes between launches.

**Namespace srs-0 — sweep_0000 to sweep_0007 (p=0.00, E=0.55–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server1/ns-0 \
    --namespace srs-0 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 0 7))
```

**Namespace srs-1 — sweep_0008 to sweep_0015 (p=0.00, E=0.65–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server1/ns-1 \
    --namespace srs-1 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 8 15))
```

**Namespace srs-2 — sweep_0016 to sweep_0023 (p=0.10, E=0.55–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server1/ns-2 \
    --namespace srs-2 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 16 23))
```

**Namespace srs-3 — sweep_0024 to sweep_0031 (p=0.10, E=0.65–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server1/ns-3 \
    --namespace srs-3 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 24 31))
```

**Namespace srs-4 — sweep_0032 to sweep_0039 (p=0.25, E=0.55–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server1/ns-4 \
    --namespace srs-4 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 32 39))
```

**Namespace srs-5 — sweep_0040 to sweep_0047 (p=0.25, E=0.65–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server1/ns-5 \
    --namespace srs-5 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 40 47))
```

---

## Server 2 (sweep_0048–sweep_0095) — p = 0.50, 0.75, 1.00

**Namespace srs-6 — sweep_0048 to sweep_0055 (p=0.50, E=0.55–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server2/ns-6 \
    --namespace srs-6 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 48 55))
```

**Namespace srs-7 — sweep_0056 to sweep_0063 (p=0.50, E=0.65–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server2/ns-7 \
    --namespace srs-7 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 56 63))
```

**Namespace srs-8 — sweep_0064 to sweep_0071 (p=0.75, E=0.55–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server2/ns-8 \
    --namespace srs-8 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 64 71))
```

**Namespace srs-9 — sweep_0072 to sweep_0079 (p=0.75, E=0.65–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server2/ns-9 \
    --namespace srs-9 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 72 79))
```

**Namespace srs-10 — sweep_0080 to sweep_0087 (p=1.00, E=0.55–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server2/ns-10 \
    --namespace srs-10 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 80 87))
```

**Namespace srs-11 — sweep_0088 to sweep_0095 (p=1.00, E=0.65–0.78, C=0.214–0.50)**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/softfork_rule_strength/build_manifest.json \
    --results-dir tools/sweep/softfork_rule_strength/results_server2/ns-11 \
    --namespace srs-11 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 88 95))
```

---

## Monitoring

```bash
# Watch all srs pods on current server
watch -n 30 'kubectl get pods --all-namespaces | grep srs | awk "{print \$1, \$4}" | sort | uniq -c'

# Progress across all namespaces
python3 -c "
import json, glob
for f in sorted(glob.glob('tools/sweep/softfork_rule_strength/results_server*/ns-*/sweep_progress.json')):
    p = json.load(open(f))
    print(f'{f}: completed={p[\"completed\"]} failed={p[\"failed\"]}')
"
```

---

## Collect via git

When each server finishes:
```bash
cd ~/warnetScenarioDiscovery
git add tools/sweep/softfork_rule_strength/results_server1/   # or results_server2
git commit -m "softfork_rule_strength results server1"
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
  --results-dir tools/sweep/softfork_rule_strength/results_server1 \
  --sweep-name softfork_rule_strength \
  --db tools/sweep/sweep_results.db

python tools/sweep/5_build_database.py \
  --results-dir tools/sweep/softfork_rule_strength/results_server2 \
  --sweep-name softfork_rule_strength \
  --db tools/sweep/sweep_results.db
```

---

## Analysis after collection

Primary analysis: plot v27 win rate as a function of p at each (E, C) point.

```python
# Quick check: at p=0.00, results should match arm_a at same E,C values
# Key questions:
# 1. Does the C=0.214 flip-point shift to lower C as p increases?
# 2. Is there a p* where even C=0.214 + E=0.55 produces v27 wins?
# 3. Does the contested region shrink monotonically with p?
```

---

## Notes

- **`--no-auto-restart`**: Required on k3s servers
- **`--interval 2`**: 2-second block interval, matching all prior 2016-block sweeps
- **`--duration 13000`**: One full 2016-block retarget cycle (~4032s) plus buffer
- **`--startup-wait 60`**: Lite network; 60s is sufficient
- **Stagger starts**: Wait ~2 minutes between namespace launches on the same server
- **Resume**: Re-run the same command if a worker stops — completed scenarios are skipped
- **Pod count**: 6 parallel namespaces × ~49 pods (lite) = ~294 pods per server
- **Timing**: 8 scenarios × ~3.6h each = ~29h wall-clock per server, both running simultaneously
- **v26_acceptance_probability** is passed per-scenario from the build manifest — no extra CLI flag needed when running via 3_run_sweep.py
