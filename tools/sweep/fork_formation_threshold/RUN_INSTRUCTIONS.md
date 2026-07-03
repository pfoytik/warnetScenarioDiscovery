# fork_formation_threshold — Run Instructions

**90 scenarios — Fork Formation Threshold, lite network, 2016-block retarget**
**Research question: At what violation rate does a chainsplit form and sustain?**
**Server 1: namespaces fft-0 to fft-5 (sweep_0000–sweep_0044)**
**Server 2: namespaces fft-0 to fft-5 (sweep_0045–sweep_0089)**

---

## Design Summary

| Parameter | Value |
|---|---|
| Violation rates | 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.00 |
| C values (pool_committed_split) | 0.15, 0.30, 0.60 |
| Replications per point | 3 |
| Total scenarios | 90 |
| Network | lite (partition_mode=unified) |
| Duration | 13000s (exits early on fork convergence) |
| Retarget interval | 2016 blocks |
| Block interval | 2s |

**Pool ideological landscape per C:**

| C | v27-committed pools | v26-committed pools | Neutral |
|---|---|---|---|
| 0.15 | none | Foundry + AntPool + ViaBTC + F2Pool (67.8%) | 6 pools |
| 0.30 | Foundry (26.9%) | AntPool + ViaBTC + F2Pool (41.9%) | 6 pools |
| 0.60 | Foundry + AntPool (46.1%) | ViaBTC + F2Pool (22.6%) | 6 pools |

**Key new behaviors vs prior sweeps:**
- `partition_mode=unified`: both partitions start on the same chain tip before mining begins
- `--fork-heal-exit`: scenario exits immediately when `v27_tip == v26_tip` (chains converged)
- Primary outcome: `fork_convergence.healed` (True/False) and `heal_time_s`

---

## Pre-flight: Configs Already Generated

All configs are pre-generated in this repo — no generation or build step needed.

Verify the expected files exist:
```bash
ls tools/sweep/fork_formation_threshold/configs/network/ | wc -l   # should be 90
ls tools/sweep/fork_formation_threshold/configs/pools/              # sweep_pools_config.yaml
ls tools/sweep/fork_formation_threshold/configs/economic/           # sweep_economic_config.yaml
ls tools/sweep/fork_formation_threshold/build_manifest_server1.json
ls tools/sweep/fork_formation_threshold/build_manifest_server2.json
```

Spot-check a few scenarios to confirm C values are correct:
```bash
python3 -c "
import json
with open('tools/sweep/fork_formation_threshold/build_manifest.json') as f:
    m = json.load(f)
for s in m['scenarios'][:9]:
    p = s['parameters']
    print(f\"{s['scenario_id']}: viol={p['violation_rate']} C={p['pool_committed_split']} rep={p['replication']}\")
"
# Expected:
# sweep_0000: viol=0.05 C=0.15 rep=0
# sweep_0001: viol=0.05 C=0.15 rep=1
# sweep_0002: viol=0.05 C=0.15 rep=2
# sweep_0003: viol=0.05 C=0.3  rep=0
# sweep_0006: viol=0.05 C=0.6  rep=0
```

---

## Step 1: Sync to Servers (dev machine)

```bash
rsync -av tools/sweep/fork_formation_threshold/ \
    server1:~/warnetScenarioDiscovery/tools/sweep/fork_formation_threshold/

rsync -av tools/sweep/fork_formation_threshold/ \
    server2:~/warnetScenarioDiscovery/tools/sweep/fork_formation_threshold/
```

---

## Step 2: Verify Cluster Capacity (on each server)

```bash
kubectl get node -o jsonpath='{.items[0].status.allocatable.pods}'   # should be 600
kubectl get pods --all-namespaces --no-headers | wc -l               # current pod count
# Each lite scenario = ~26 pods.
# 6 namespaces x 1 active scenario = ~156 pods + system overhead. Well within k3s limit.
```

---

## Step 3: Create Namespaces (on each server)

```bash
for i in $(seq 0 5); do kubectl create namespace fft-$i; done
```

---

## Step 4: Run Scenarios

Launch each namespace in its own tmux pane. Stagger launches by ~2 minutes between
panes on the same server to avoid simultaneous startup collisions on the first scenario.

All commands run from `~/warnetScenarioDiscovery/`.

### Server 1

**Pane 0 — namespace fft-0 (sweep_0000,0006,…,0042):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server1 \
    --namespace fft-0 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 0 6 42))
```

**Pane 1 — namespace fft-1 (sweep_0001,0007,…,0043):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server1 \
    --namespace fft-1 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 1 6 43))
```

**Pane 2 — namespace fft-2 (sweep_0002,0008,…,0044):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server1 \
    --namespace fft-2 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 2 6 44))
```

**Pane 3 — namespace fft-3 (sweep_0003,0009,…,0039):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server1 \
    --namespace fft-3 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 3 6 39))
```

**Pane 4 — namespace fft-4 (sweep_0004,0010,…,0040):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server1 \
    --namespace fft-4 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 4 6 40))
```

**Pane 5 — namespace fft-5 (sweep_0005,0011,…,0041):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server1.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server1 \
    --namespace fft-5 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 5 6 41))
```

---

### Server 2

**Pane 0 — namespace fft-0 (sweep_0045,0051,…,0087):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server2 \
    --namespace fft-0 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 45 6 87))
```

**Pane 1 — namespace fft-1 (sweep_0046,0052,…,0088):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server2 \
    --namespace fft-1 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 46 6 88))
```

**Pane 2 — namespace fft-2 (sweep_0047,0053,…,0089):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server2 \
    --namespace fft-2 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 47 6 89))
```

**Pane 3 — namespace fft-3 (sweep_0048,0054,…,0084):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server2 \
    --namespace fft-3 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 48 6 84))
```

**Pane 4 — namespace fft-4 (sweep_0049,0055,…,0085):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server2 \
    --namespace fft-4 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 49 6 85))
```

**Pane 5 — namespace fft-5 (sweep_0050,0056,…,0086):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/fork_formation_threshold/build_manifest_server2.json \
    --results-dir tools/sweep/fork_formation_threshold/results_server2 \
    --namespace fft-5 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 30 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 50 6 86))
```

---

## Monitoring

```bash
# Watch all fft pods on current server
watch -n 30 'kubectl get pods --all-namespaces | grep fft | awk "{print \$1, \$4}" | sort | uniq -c'

# Count completed results (each completed scenario writes results.json)
find tools/sweep/fork_formation_threshold/results_server1 -name "results.json" | wc -l
find tools/sweep/fork_formation_threshold/results_server2 -name "results.json" | wc -l
# Should reach 45 each (90 total)

# Check for healed vs sustained forks as results arrive
python3 -c "
from pathlib import Path
import json

results = list(Path('tools/sweep/fork_formation_threshold').rglob('results.json'))
healed, sustained, total = 0, 0, 0
for p in results:
    try:
        r = json.load(open(p))
        fc = r.get('fork_convergence', {})
        if fc.get('healed'):
            healed += 1
        else:
            sustained += 1
        total += 1
    except Exception:
        pass
print(f'Completed: {total}/90')
print(f'  Fork healed:    {healed}')
print(f'  Fork sustained: {sustained}')
"

# Check for missing scenarios
python3 -c "
from pathlib import Path
import json
with open('tools/sweep/fork_formation_threshold/build_manifest.json') as f:
    m = json.load(f)
completed = {p.parent.name for p in Path('tools/sweep/fork_formation_threshold').rglob('results.json')}
missing = [s['scenario_id'] for s in m['scenarios'] if s['scenario_id'] not in completed]
print(f'Completed: {len(completed)}/90')
if missing:
    print(f'Missing ({len(missing)}): {missing[:10]}' + ('...' if len(missing) > 10 else ''))
"
```

---

## Step 5: Collect Results (dev machine)

After both servers complete:

```bash
rsync -av server1:~/warnetScenarioDiscovery/tools/sweep/fork_formation_threshold/results_server1/ \
    tools/sweep/fork_formation_threshold/results_server1/

rsync -av server2:~/warnetScenarioDiscovery/tools/sweep/fork_formation_threshold/results_server2/ \
    tools/sweep/fork_formation_threshold/results_server2/
```

---

## Step 6: Analyze

```bash
python tools/sweep/4_analyze_results.py \
    --sweep fork_formation_threshold \
    --results tools/sweep/fork_formation_threshold/results_server1 \
               tools/sweep/fork_formation_threshold/results_server2 \
    --manifest tools/sweep/fork_formation_threshold/build_manifest.json \
    --output tools/sweep/fork_formation_threshold/results/analysis
```

Key fields to examine in results.json per scenario:
- `fork_convergence.healed` — primary outcome (True=fork healed, False=fork sustained)
- `fork_convergence.heal_time_s` — elapsed seconds at convergence (null if sustained)
- `fork_convergence.v27_blocks_at_heal` / `v26_blocks_at_heal` — chain lengths at convergence
- `fork_convergence.v26_acceptance_probability` — cross-check of the scenario's p value

---

## Notes

- **`--interval 2`**: 2-second block interval, matches all prior 2016-block sweeps. At interval=10 the retarget never fires within 13000s — do not change this.
- **`--duration 13000`**: Maximum run time per scenario. With `--fork-heal-exit`, healing scenarios exit early (typically 1–2h). Non-healing scenarios run the full ~3.6h.
- **`--no-auto-restart`**: Required on k3s servers.
- **`partition_mode=unified`**: Encoded in each scenario's parameters — no extra CLI flag needed.
- **`fork_heal_exit=True`**: Also encoded in scenario parameters and injected by the runner.
- **Stagger starts**: Wait ~2 minutes between namespace launches on the same server.
- **Resume**: Re-run the same namespace command if interrupted — completed scenarios are skipped.
- **Pod budget**: 6 parallel namespaces × ~26 pods = ~156 pods per server (well within k3s maxPods=600).
- **Timing**: Up to 3.6h per scenario × 8 scenarios = ~29h worst case per namespace. Healing scenarios exit early, so expect 20–25h total wall-clock.
- **Results location**: `results_server1/sweep_XXXX/` and `results_server2/sweep_XXXX/`
