# lhs_144_full_6param — Run Instructions

**360 scenarios — unbiased 6-parameter LHS, 144-block retarget, full 60-node network**
**Server 1: namespaces lhs14-0 to lhs14-2 (sweep_0000–sweep_0179)**
**Server 2: namespaces lhs14-3 to lhs14-5 (sweep_0180–sweep_0359)**

Run this sweep simultaneously with lhs_2016_full_6param on the same two servers
(each server handles 3 namespaces of each sweep in parallel, or alternate if memory
is a constraint — see pod count note below).

---

## Step 1: Generate Scenarios (dev machine, run once)

```bash
cd ~/bitcoin/warnetScenarioDiscovery

python tools/sweep/1_generate_scenarios.py \
    --spec tools/sweep/specs/lhs_144_full_6param.yaml \
    --output tools/sweep/lhs_144_full_6param/scenarios.json
```

Verify output: `scenarios.json` should contain 360 entries. Same seed (2026) as
lhs_2016_full_6param — the LHS sample structure is identical; only retarget differs.

---

## Step 2: Build Configs (dev machine, run once)

```bash
python tools/sweep/2_build_configs.py \
    --input tools/sweep/lhs_144_full_6param/scenarios.json \
    --output-dir tools/sweep/lhs_144_full_6param \
    --network full
```

---

## Step 3: Sync to Servers (dev machine)

```bash
rsync -av tools/sweep/lhs_144_full_6param/ server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_144_full_6param/
rsync -av tools/sweep/lhs_144_full_6param/ server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_144_full_6param/
```

---

## Step 4: Verify Cluster Capacity

144-block scenarios complete faster (~20 min/scenario vs ~35 min for 2016-block).
If running both sweeps simultaneously on the same servers, pod count doubles:
- 3 namespaces lhs26-* + 3 namespaces lhs14-* = ~366 pods per server
- Still within k3s maxPods=600 — safe to run both sweeps in parallel

```bash
kubectl get pods --all-namespaces --no-headers | wc -l
```

---

## Step 5: Create Namespaces

**Server 1:**
```bash
for i in 0 1 2; do kubectl create namespace lhs14-$i; done
```

**Server 2:**
```bash
for i in 3 4 5; do kubectl create namespace lhs14-$i; done
```

---

## Step 6: Run Scenarios

Start each namespace in its own tmux pane. Stagger launches by ~2 minutes.
All commands run from `~/bitcoin/warnetScenarioDiscovery/`.

### Server 1

**Namespace lhs14-0 — sweep_0000 to sweep_0059**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_144_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_144_full_6param/results_server1/ns-0 \
    --namespace lhs14-0 \
    --retarget-interval 144 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 0 59))
```

**Namespace lhs14-1 — sweep_0060 to sweep_0119**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_144_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_144_full_6param/results_server1/ns-1 \
    --namespace lhs14-1 \
    --retarget-interval 144 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 60 119))
```

**Namespace lhs14-2 — sweep_0120 to sweep_0179**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_144_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_144_full_6param/results_server1/ns-2 \
    --namespace lhs14-2 \
    --retarget-interval 144 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 120 179))
```

### Server 2

**Namespace lhs14-3 — sweep_0180 to sweep_0239**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_144_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_144_full_6param/results_server2/ns-3 \
    --namespace lhs14-3 \
    --retarget-interval 144 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 180 239))
```

**Namespace lhs14-4 — sweep_0240 to sweep_0299**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_144_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_144_full_6param/results_server2/ns-4 \
    --namespace lhs14-4 \
    --retarget-interval 144 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 240 299))
```

**Namespace lhs14-5 — sweep_0300 to sweep_0359**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_144_full_6param/build_manifest.json \
    --results-dir tools/sweep/lhs_144_full_6param/results_server2/ns-5 \
    --namespace lhs14-5 \
    --retarget-interval 144 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 300 359))
```

---

## Monitoring

```bash
watch -n 30 'kubectl get pods --all-namespaces | grep lhs14 | awk "{print \$1, \$4}" | sort | uniq -c'

python3 -c "
import json, glob
for f in sorted(glob.glob('tools/sweep/lhs_144_full_6param/results_server*/ns-*/sweep_progress.json')):
    p = json.load(open(f))
    print(f'{f}: completed={p[\"completed\"]} failed={p[\"failed\"]}')
"
```

---

## Step 7: Collect Results (dev machine)

```bash
rsync -av server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_144_full_6param/results_server1/ \
    tools/sweep/lhs_144_full_6param/results/

rsync -av server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_144_full_6param/results_server2/ \
    tools/sweep/lhs_144_full_6param/results/
```

---

## Step 8: Analyze

```bash
python tools/sweep/4_analyze_results.py \
    --results-dir tools/sweep/lhs_144_full_6param/results \
    --output-dir tools/sweep/lhs_144_full_6param/analysis

python tools/sweep/5_build_database.py

# Fit 144-block boundary on clean full-network data (removes quantization caveat)
python tools/discovery/fit_boundary.py \
    --regime 144 \
    --network full \
    --output-dir tools/discovery/output/144_full_6param

# Regime comparison on matched full-network pair
python tools/discovery/fit_boundary.py \
    --compare-regimes \
    --network full \
    --output-dir tools/discovery/output/full_network_regime_comparison
```

---

## Notes

- **`--cooldown 30`**: Shorter than 2016-block (45s) — 144-block scenarios finish faster
  and pods release sooner, so less cooldown needed before next scenario in the namespace
- **`--retarget-interval 144`**: Critical — this is the only flag that differs from
  lhs_2016_full_6param; everything else is identical for direct comparison
- **Parallel with lhs_2016_full_6param**: If running both sweeps simultaneously, each
  server handles 3 namespaces of each sweep (6 total namespaces, ~366 pods). Safe within
  k3s maxPods=600. If memory pressure is observed, run sweeps sequentially instead.
- **144-block finishes first**: ~20 hr runtime vs ~35 hr for 2016-block. Both namespaces
  on a server can proceed to analysis while 2016-block is still running.
