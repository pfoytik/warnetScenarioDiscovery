# pool_composition_arm_b — Run Instructions

**168 scenarios — Pool Composition Decoupling, full 60-node network, 2016-block retarget**
**Sensitivity replication of pool_composition_arm_a on the full network**
**Server 1: namespaces armb-0 to armb-5 (sweep_0000–sweep_0083)**
**Server 2: namespaces armb-6 to armb-11 (sweep_0084–sweep_0167)**

---

## Step 1: Generate Scenarios (dev machine, run once)

```bash
cd ~/warnetScenarioDiscovery

python tools/sweep/1_generate_compositional.py \
    --spec tools/sweep/specs/pool_composition_arm_b.yaml \
    --output tools/sweep/pool_composition_arm_b
```

Verify:
- `pool_composition_arm_b/scenarios.json` — 168 scenarios
- `pool_composition_arm_b/scenarios_server1.json` — scenarios 0–83
- `pool_composition_arm_b/scenarios_server2.json` — scenarios 84–167

Cross-check that composition seeds match arm_a (both use base_composition_seed=1000):
```bash
python3 -c "
import json
arm_a = json.load(open('tools/sweep/pool_composition_arm_a/scenarios.json'))['scenarios']
arm_b = json.load(open('tools/sweep/pool_composition_arm_b/scenarios.json'))['scenarios']
mismatches = [(a['results_id'], a['composition_seed'], b['composition_seed'])
              for a, b in zip(arm_a, arm_b) if a['composition_seed'] != b['composition_seed']]
print(f'Seed mismatches: {len(mismatches)} (should be 0)')
print(f'arm_a[0] committed_pool_ids_v27: {arm_a[0][\"committed_pool_ids_v27\"]}')
print(f'arm_b[0] committed_pool_ids_v27: {arm_b[0][\"committed_pool_ids_v27\"]}')
"
```

---

## Step 2: Build Configs (dev machine, run once)

```bash
python tools/sweep/2_build_configs.py \
    --input tools/sweep/pool_composition_arm_b/scenarios.json \
    --output-dir tools/sweep/pool_composition_arm_b \
    --base-network full
```

Generates `build_manifest.json` and `networks/` (168 × 60-node network yamls).

Verify node count in a generated network:
```bash
python3 -c "
import yaml
net = yaml.safe_load(open('tools/sweep/pool_composition_arm_b/networks/sweep_0000/network.yaml'))
roles = {}
for n in net['nodes']:
    r = n.get('metadata', {}).get('role', 'unknown')
    roles[r] = roles.get(r, 0) + 1
print('Total nodes:', len(net['nodes']), '(should be 60)')
print('Roles:', roles)
"
```

Expected: 60 nodes with roles: mining_pool(8), major_exchange(4), exchange(6),
payment_processor(3), merchant(6), institutional(5), power_user(12), casual_user(16)

---

## Step 3: Split Manifest (dev machine)

```bash
python tools/sweep/split_manifest.py tools/sweep/pool_composition_arm_b/build_manifest.json
```

Produces:
- `pool_composition_arm_b/build_manifest_server1.json` — scenarios 0–83
- `pool_composition_arm_b/build_manifest_server2.json` — scenarios 84–167

---

## Step 4: Sync to Servers (dev machine)

```bash
rsync -av tools/sweep/pool_composition_arm_b/ \
    server1:~/warnetScenarioDiscovery/tools/sweep/pool_composition_arm_b/

rsync -av tools/sweep/pool_composition_arm_b/ \
    server2:~/warnetScenarioDiscovery/tools/sweep/pool_composition_arm_b/
```

---

## Step 5: Verify Cluster Capacity (on each server)

```bash
kubectl get node -o jsonpath='{.items[0].status.allocatable.pods}'   # should be 600
kubectl get pods --all-namespaces --no-headers | wc -l               # current pod count
# Each 60-node scenario = ~61 pods.
# 6 namespaces × 1 active scenario = ~366 pods + system overhead. Within k3s limit.
```

---

## Step 6: Create Namespaces

**Server 1:**
```bash
for i in $(seq 0 5); do kubectl create namespace armb-$i; done
```

**Server 2:**
```bash
for i in $(seq 6 11); do kubectl create namespace armb-$i; done
```

---

## Step 7: Run Scenarios

Launch each namespace in its own tmux pane. Stagger launches by ~2 minutes between
panes on the same server to avoid simultaneous `network_metadata.yaml` injection on
the first scenario of each namespace.

All commands run from `~/warnetScenarioDiscovery/`.

### Server 1

**Pane 0 — namespace armb-0 (sweep_0000–sweep_0013):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server1.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server1/ns-0 \
    --namespace armb-0 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 0 13))
```

**Pane 1 — namespace armb-1 (sweep_0014–sweep_0027):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server1.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server1/ns-1 \
    --namespace armb-1 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 14 27))
```

**Pane 2 — namespace armb-2 (sweep_0028–sweep_0041):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server1.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server1/ns-2 \
    --namespace armb-2 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 28 41))
```

**Pane 3 — namespace armb-3 (sweep_0042–sweep_0055):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server1.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server1/ns-3 \
    --namespace armb-3 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 42 55))
```

**Pane 4 — namespace armb-4 (sweep_0056–sweep_0069):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server1.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server1/ns-4 \
    --namespace armb-4 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 56 69))
```

**Pane 5 — namespace armb-5 (sweep_0070–sweep_0083):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server1.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server1/ns-5 \
    --namespace armb-5 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 70 83))
```

---

### Server 2

**Pane 0 — namespace armb-6 (sweep_0084–sweep_0097):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server2.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server2/ns-6 \
    --namespace armb-6 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 84 97))
```

**Pane 1 — namespace armb-7 (sweep_0098–sweep_0111):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server2.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server2/ns-7 \
    --namespace armb-7 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 98 111))
```

**Pane 2 — namespace armb-8 (sweep_0112–sweep_0125):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server2.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server2/ns-8 \
    --namespace armb-8 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 112 125))
```

**Pane 3 — namespace armb-9 (sweep_0126–sweep_0139):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server2.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server2/ns-9 \
    --namespace armb-9 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 126 139))
```

**Pane 4 — namespace armb-10 (sweep_0140–sweep_0153):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server2.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server2/ns-10 \
    --namespace armb-10 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 140 153))
```

**Pane 5 — namespace armb-11 (sweep_0154–sweep_0167):**
```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/pool_composition_arm_b/build_manifest_server2.json \
    --results-dir tools/sweep/pool_composition_arm_b/results_server2/ns-11 \
    --namespace armb-11 \
    --duration 13000 --retarget-interval 2016 --interval 2 \
    --startup-wait 60 --cooldown 45 \
    --no-auto-restart \
    --scenarios $(printf "sweep_%04d " $(seq 154 167))
```

---

## Monitoring

```bash
# Watch all armb pods on current server
watch -n 30 'kubectl get pods --all-namespaces | grep armb | awk "{print \$1, \$4}" | sort | uniq -c'

# Count completed results
find tools/sweep/pool_composition_arm_b/results_server1 -name "summary.txt" | wc -l
find tools/sweep/pool_composition_arm_b/results_server2 -name "summary.txt" | wc -l
# Should reach 84 each (168 total)

# Check for failures (missing results vs expected)
python3 -c "
from pathlib import Path
import json
with open('tools/sweep/pool_composition_arm_b/scenarios.json') as f:
    scenarios = json.load(f)['scenarios']
completed = set()
for p in Path('tools/sweep/pool_composition_arm_b').rglob('summary.txt'):
    completed.add(p.parent.name)
missing = [s['results_id'] for s in scenarios if s['results_id'] not in completed]
print(f'Completed: {len(completed)}/168')
if missing: print(f'Missing: {missing[:10]}...' if len(missing) > 10 else f'Missing: {missing}')
"
```

---

## Step 8: Collect Results (dev machine)

After both servers complete:

```bash
rsync -av server1:~/warnetScenarioDiscovery/tools/sweep/pool_composition_arm_b/results_server1/ \
    tools/sweep/pool_composition_arm_b/results_server1/

rsync -av server2:~/warnetScenarioDiscovery/tools/sweep/pool_composition_arm_b/results_server2/ \
    tools/sweep/pool_composition_arm_b/results_server2/
```

---

## Step 9: Analyze

First, create the arm_b analysis script by copying arm_a's and updating the three
path constants at the top:

```bash
cp tools/sweep/pool_composition_arm_a/analyze_arm_a.py \
   tools/sweep/pool_composition_arm_b/analyze_arm_b.py

# Update the three hardcoded path constants (lines ~19-21)
sed -i \
    -e 's|pool_composition_arm_a/scenarios.json|pool_composition_arm_b/scenarios.json|' \
    -e 's|= SWEEP_DIR / "results_server1"|= SWEEP_DIR / "results_server1"  # arm_b collects both servers here|' \
    -e 's|= SWEEP_DIR / "analysis_arm_a"|= SWEEP_DIR / "analysis_arm_b"|' \
    tools/sweep/pool_composition_arm_b/analyze_arm_b.py
```

After collecting results from both servers into results_server1/ and results_server2/,
run the analysis (the script traverses ns-*/sweep_*/ within RESULTS_DIR, so point it
at the combined results or run twice and merge):

```bash
python tools/sweep/pool_composition_arm_b/analyze_arm_b.py
```

# Cross-comparison (arm_a vs arm_b outcome agreement)
python3 -c "
import json
from pathlib import Path

arm_a_results = {}
for p in Path('tools/sweep/pool_composition_arm_a/results_server1').rglob('results.json'):
    sid = p.parent.name
    arm_a_results[sid] = json.load(open(p)).get('winner', 'unknown')

arm_b_results = {}
for base in ['tools/sweep/pool_composition_arm_b/results_server1',
             'tools/sweep/pool_composition_arm_b/results_server2']:
    for p in Path(base).rglob('results.json'):
        sid = p.parent.name
        arm_b_results[sid] = json.load(open(p)).get('winner', 'unknown')

common = set(arm_a_results) & set(arm_b_results)
agree = sum(1 for sid in common if arm_a_results[sid] == arm_b_results[sid])
print(f'Common scenarios: {len(common)}')
print(f'Agreement rate: {agree}/{len(common)} = {agree/len(common)*100:.1f}%')
flips = [(sid, arm_a_results[sid], arm_b_results[sid])
         for sid in common if arm_a_results[sid] != arm_b_results[sid]]
print(f'Flips (lite→full): {len(flips)}')
for sid, a, b in sorted(flips)[:20]:
    print(f'  {sid}: {a} → {b}')
"
```

---

## Notes

- **`--startup-wait 60`**: Full 60-node networks need longer pod startup than lite (25-node)
- **`--interval 2`**: 2-second block interval — matches all prior 2016-block sweeps
- **`--duration 13000`**: Same as arm_a — enables direct scenario-level comparison
- **`--no-auto-restart`**: Required on k3s servers
- **Stagger starts**: Wait ~2 minutes between namespace launches on the same server
- **Resume**: Re-run the same namespace command if interrupted — completed scenarios are skipped
- **Pod budget**: 6 parallel namespaces × ~61 pods = ~366 pods per server (within k3s maxPods=600)
- **Timing**: ~216.7 min per scenario × 14 scenarios = ~50 hours per namespace wall-clock
- **Results location**: All results in `results_server1/ns-{0..5}/` and `results_server2/ns-{6..11}/`
  (matching arm_a's structure — ns-0 through ns-5 on server 1, ns-6 through ns-11 on server 2)

## Comparison to Arm A

| Parameter | Arm A | Arm B |
|---|---|---|
| Network | lite (25 nodes, 4 econ) | **full (60 nodes, 24 econ)** |
| Economic resolution | ~25% per partition | ~4% per partition |
| E × C grid | 4 × 7 = 28 points | same |
| Compositions per point | 6 | same |
| Total scenarios | 168 | same |
| Composition seeds | base_seed=1000 | same (direct comparison) |
| Duration | 13000s | same |
| Retarget interval | 2016 | same |
| Expected wall-clock | ~50h per server | ~50h per server |
