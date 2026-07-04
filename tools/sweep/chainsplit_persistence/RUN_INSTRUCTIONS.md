# chainsplit_persistence — Run Instructions

**36 scenarios — Chainsplit Persistence, lite network, 2016-block retarget**
**Research question: What is the minimum violation rate for a persistent chainsplit?**
**Server 1: namespaces csp-0 to csp-5 (sweep_0000–sweep_0017)**
**Server 2: namespaces csp-0 to csp-5 (sweep_0018–sweep_0035)**

---

## Design Summary

| Parameter | Value |
|---|---|
| Violation rates | 0.05, 0.10, 0.20, 0.30, 0.50, 1.00 |
| C values (pool_committed_split) | 0.15, 0.30, 0.60 |
| Economic split (v27 %) | **55%** (vs 65% in prior sweeps — minimum to create cascade pressure) |
| Replications per point | 2 |
| Total scenarios | 36 |
| Network | lite (partition_mode=unified) |
| Duration | 13000s (exits early on fork convergence) |
| Retarget interval | 2016 blocks |
| Block interval | 2s |
| **Max wall-clock** | **10.8h** (3 scenarios/namespace × 3.6h worst case) |

**Key differences from fork_formation_threshold sweep:**
- `economic_split=0.55` (was 0.65): weaker cascade pressure → v26 better chance to sustain
- Pool switching chain-state leak **fixed**: switching pool now runs `invalidateblock` before `addnode`, preventing v26 chain from leaking into v27 P2P island
- 6 violation rates instead of 10, 2 reps instead of 3 → fits 12h budget

**Pool ideological landscape per C:**

| C | v27-committed pools | v26-committed pools | Neutral |
|---|---|---|---|
| 0.15 | none (0%) | Foundry+MARA+Luxor+Ocean+AntPool+F2Pool (65.9%) | ViaBTC+SpiderPool (20.5%) |
| 0.30 | Foundry (30%) | MARA+Luxor+Ocean+AntPool+F2Pool (35.9%) | ViaBTC+SpiderPool (20.5%) |
| 0.60 | Foundry+MARA+Luxor (36.9%) | Ocean+AntPool+F2Pool (29.0%) | ViaBTC+SpiderPool (20.5%) |

**Persistence threshold reasoning:**
- At C=0.15, no committed pool supports v27. The only v27 hashrate comes from neutral pools
  that switch economically. With economic_split=0.55 (weak), neutral pools switch slowly.
  This is the regime most favorable to a sustained v26 chainsplit.
- At C=0.30, Foundry (the largest pool, 30%) is committed to v27. The cascade is stronger.
  Persistent splits are less likely here.
- At C=0.60, Foundry+MARA+Luxor support v27. Very strong cascade — splits should heal.
  This serves as a reference point showing the cascade working correctly.

---

## Pre-flight: Configs Already Generated

All configs are pre-generated in this repo — no generation or build step needed.

Verify the expected files exist:
```bash
ls tools/sweep/chainsplit_persistence/configs/network/ | wc -l   # should be 36
ls tools/sweep/chainsplit_persistence/configs/pools/              # sweep_pools_config.yaml
ls tools/sweep/chainsplit_persistence/configs/economic/           # sweep_economic_config.yaml
ls tools/sweep/chainsplit_persistence/build_manifest_server1.json
ls tools/sweep/chainsplit_persistence/build_manifest_server2.json
```

Spot-check a few scenarios to confirm parameters are correct:
```bash
python3 -c "
import json
with open('tools/sweep/chainsplit_persistence/build_manifest.json') as f:
    m = json.load(f)
for s in [m['scenarios'][0], m['scenarios'][6], m['scenarios'][18], m['scenarios'][30]]:
    p = s['parameters']
    print(f\"{s['scenario_id']}: vr={p['violation_rate']} C={p['pool_committed_split']} rep={p['replication']} econ={p['economic_split']}\")
"
# Expected:
# sweep_0000: vr=0.05 C=0.15 rep=0 econ=0.55
# sweep_0006: vr=0.1  C=0.15 rep=0 econ=0.55
# sweep_0018: vr=0.3  C=0.15 rep=0 econ=0.55
# sweep_0030: vr=1.0  C=0.15 rep=0 econ=0.55
```

---

## Step 1: Sync to Servers (dev machine)

```bash
rsync -av tools/sweep/chainsplit_persistence/ \
    server1:~/warnetScenarioDiscovery/tools/sweep/chainsplit_persistence/

rsync -av tools/sweep/chainsplit_persistence/ \
    server2:~/warnetScenarioDiscovery/tools/sweep/chainsplit_persistence/
```

Also sync the updated scenario file (contains the pool switching fix):
```bash
rsync -av scenarios/partition_miner_with_pools.py \
    server1:~/warnetScenarioDiscovery/scenarios/

rsync -av scenarios/partition_miner_with_pools.py \
    server2:~/warnetScenarioDiscovery/scenarios/
```

---

## Step 2: Verify Cluster Capacity (on each server)

```bash
kubectl get node -o jsonpath='{.items[0].status.allocatable.pods}'   # should be 600
kubectl get pods --all-namespaces --no-headers | wc -l               # current pod count
# Each lite scenario = ~26 pods.
# 6 namespaces x 1 active scenario = ~156 pods + system overhead.
```

---

## Step 3: Create Namespaces (on each server)

```bash
for i in $(seq 0 5); do kubectl create namespace csp-$i; done
```

---

## Step 4: Run Scenarios

Launch each namespace in its own tmux pane. Stagger launches by ~2 minutes between
panes to avoid simultaneous startup collisions.

All commands run from `~/warnetScenarioDiscovery/`.

### Server 1

**Pane 0 — namespace csp-0 (sweep_0000–sweep_0002):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-0 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 0 2))
```

**Pane 1 — namespace csp-1 (sweep_0003–sweep_0005):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-1 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 3 5))
```

**Pane 2 — namespace csp-2 (sweep_0006–sweep_0008):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-2 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 6 8))
```

**Pane 3 — namespace csp-3 (sweep_0009–sweep_0011):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-3 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 9 11))
```

**Pane 4 — namespace csp-4 (sweep_0012–sweep_0014):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-4 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 12 14))
```

**Pane 5 — namespace csp-5 (sweep_0015–sweep_0017):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server1 \
  --namespace csp-5 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 15 17))
```

---

### Server 2

**Pane 0 — namespace csp-0 (sweep_0018–sweep_0020):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-0 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 18 20))
```

**Pane 1 — namespace csp-1 (sweep_0021–sweep_0023):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-1 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 21 23))
```

**Pane 2 — namespace csp-2 (sweep_0024–sweep_0026):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-2 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 24 26))
```

**Pane 3 — namespace csp-3 (sweep_0027–sweep_0029):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-3 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 27 29))
```

**Pane 4 — namespace csp-4 (sweep_0030–sweep_0032):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-4 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 30 32))
```

**Pane 5 — namespace csp-5 (sweep_0033–sweep_0035):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/chainsplit_persistence/results_server2 \
  --namespace csp-5 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 33 35))
```

---

## Monitoring

```bash
# Count completed results (each completed scenario writes results.json)
find tools/sweep/chainsplit_persistence/results_server1 -name "results.json" | wc -l
find tools/sweep/chainsplit_persistence/results_server2 -name "results.json" | wc -l
# Should reach 18 each (36 total)

# Check healed vs sustained as results arrive
python3 -c "
from pathlib import Path
import json

results = list(Path('tools/sweep/chainsplit_persistence').rglob('results.json'))
healed, sustained, total = 0, 0, 0
for p in results:
    try:
        r = json.load(open(p))
        fc = r.get('fork_convergence', {})
        params = r.get('parameters', {})
        vr = params.get('violation_rate', '?')
        c  = params.get('pool_committed_split', '?')
        rep = params.get('replication', '?')
        status = 'HEALED' if fc.get('healed') else 'SUSTAINED'
        print(f\"  {p.parent.name}: vr={vr} C={c} rep={rep} → {status}\")
        if fc.get('healed'): healed += 1
        else: sustained += 1
        total += 1
    except Exception as e:
        pass
print(f'\\nCompleted: {total}/36 | Healed: {healed} | Sustained (persistent): {sustained}')
"

# Check for missing scenarios
python3 -c "
from pathlib import Path
import json
with open('tools/sweep/chainsplit_persistence/build_manifest.json') as f:
    m = json.load(f)
completed = {p.parent.name for p in Path('tools/sweep/chainsplit_persistence').rglob('results.json')}
missing = [s['scenario_id'] for s in m['scenarios'] if s['scenario_id'] not in completed]
print(f'Completed: {len(completed)}/36')
if missing:
    print(f'Missing ({len(missing)}): {missing}')
"
```

---

## Step 5: Collect Results (dev machine)

```bash
rsync -av server1:~/warnetScenarioDiscovery/tools/sweep/chainsplit_persistence/results_server1/ \
    tools/sweep/chainsplit_persistence/results_server1/

rsync -av server2:~/warnetScenarioDiscovery/tools/sweep/chainsplit_persistence/results_server2/ \
    tools/sweep/chainsplit_persistence/results_server2/
```

---

## Step 6: Analyze

```bash
python tools/sweep/4_analyze_results.py \
    --sweep chainsplit_persistence \
    --results tools/sweep/chainsplit_persistence/results_server1 \
               tools/sweep/chainsplit_persistence/results_server2 \
    --manifest tools/sweep/chainsplit_persistence/build_manifest.json \
    --output tools/sweep/chainsplit_persistence/results/analysis
```

**Key analysis targets:**
- `fork_convergence.healed=False` rows → the persistent chainsplits we're looking for
- What is the minimum `violation_rate` where `healed=False` appears? (primary question)
- Does that threshold differ between C=0.15 and C=0.30? (secondary question)
- For vr=1.00, does C=0.15 show more persistence than C=0.30 or C=0.60? (cascade validation)

**Expected pattern** (hypothesis):
- C=0.60 (Foundry+MARA+Luxor on v27): cascade wins, all forks heal regardless of vr
- C=0.30 (Foundry on v27): cascade works above some vr threshold, some persistence at low vr
- C=0.15 (all pools v26): cascade weakest, persistence appears at lower vr thresholds

---

## Notes

- **Pool switching fix**: `_find_lca_height` + `invalidateblock` in `switch_node_partition` ensures
  switching pools abandon their old chain before joining the new partition. Prevents the chain-state
  leak that contaminated FFT sweep results.
- **`--interval 2`**: 2-second block interval. Do NOT change — at interval=10 the 2016-block
  retarget never fires within 13000s.
- **`--duration 13000`**: ~3.6h max. With `--fork-heal-exit`, healing scenarios exit early (30 min–2h).
  Non-healing (persistent) scenarios run full duration.
- **Namespace prefix `csp-`**: "chainsplit persistence" — distinct from `fft-` and `poolarma-` namespaces.
- **Resume**: Re-run the same namespace command if interrupted — completed scenarios are skipped.
- **Stagger starts**: Wait ~2 minutes between namespace launches on the same server.
- **Results location**: `results_server1/sweep_XXXX/` and `results_server2/sweep_XXXX/`
- **Scenario file sync**: The pool switching fix is in `scenarios/partition_miner_with_pools.py`.
  Confirm the updated file is synced to both servers before launching.
