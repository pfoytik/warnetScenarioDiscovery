# contested_fork_threshold — Run Instructions

**120 scenarios — Reorg Pain Threshold, lite network, 2016-block retarget**
**Research question: What (vr, C, E) combinations produce the most painful reorgs?**
**Server 1: namespaces cft-0 to cft-5 (sweep_0000–sweep_0059)**
**Server 2: namespaces cft-0 to cft-5 (sweep_0060–sweep_0119)**

---

## Design Summary

| Parameter | Value |
|---|---|
| Violation rates (vr) | 0.20, 0.50, 1.00 |
| C values (pool_committed_split) | 0.15, 0.20, 0.25, 0.30, 0.35 |
| E values (economic_split) | 0.30, 0.40, 0.50, 0.55 |
| Compositions per (vr, E, C) point | 2 (random pool-to-hashrate assignments) |
| Total scenarios | 120 |
| Network | lite (partition_mode=unified) |
| Duration | 13000s (exits early on fork convergence) |
| Retarget interval | 2016 blocks |
| Block interval | 2s |
| **Max wall-clock per namespace** | **~36h worst case** (10 scenarios × 3.6h); expected 10–20h |

**Key differences from chainsplit_persistence sweep:**
- Focus shifts from "does chainsplit persist?" to "how painful is the reorg before healing?"
- 3 vr values (focused on pain zone: vr ≥ 0.20) instead of 6 (which explored vr=0.05/0.10)
- 5 C values (finer resolution) instead of 3
- 4 E values (0.30–0.55) — new low-E territory; no prior sweep covered E < 0.55
- 2 compositions per point (arm_a style) — decouples pool identity from aggregate hashrate
- New analysis metrics: `reorg_depth`, `fork_balance`, `pain_score`

**New reorg pain metrics:**
- `reorg_depth` = minority_blocks at heal time (blocks the losing side must reorganize)
- `fork_balance` = min(v27_blocks, v26_blocks) / max(v27_blocks, v26_blocks) at heal (0=one-sided, 1=maximally contested)
- `pain_score` = reorg_depth × fork_balance (deep + balanced = maximum pain)

### Note on E Variation

**E is NOT an independent axis in the lite network for E ∈ [0.30, 0.55].**

The lite network's economic nodes (4 nodes, 4.987M BTC total custody) produce IDENTICAL
image tag and fork_preference assignments for all E in [0.284, 0.781]:

- node-0016 (2.830M BTC) → v27 tag (custody midpoint 1.415M < v27_target for any E ≥ 0.284)
- node-0004 (2.138M BTC) → v26 tag (custody midpoint 3.899M > v27_target for any E ≤ 0.781)
- node-0005 (9k BTC) → v26 tag
- node-0017 (9.450 BTC) → v26 tag

Result: for all 4 tested E values, the effective economic weight is identical — node-0016 alone
on v27 with 56.7% of total custody. E is recorded in parameters but the network topology does
not change across E values.

**Active axes are: vr × C × composition = 30 unique parameter points.**
The 4 E groups function as additional replications of the same underlying conditions.
When analyzing, group by (vr, C) and treat E × comp = 8 trials per (vr, C) point.

---

## Pool Landscape per C Value

Composition seeds randomly assign pools to v27-committed / neutral / v26-committed roles.
The `pool_neutral_pct=30%` ensures 30% of hashrate is always neutral; C controls what fraction
of the remaining 70% is committed v27. C_eff is the realized committed v27 fraction.

| C | C_eff range | Typical v27-committed pools | Foundryusa (30%) committed? |
|---|---|---|---|
| 0.15 | [0.000, 0.196] | 0–1 small/medium pool (marapool, luxor, ocean, spiderpool, f2pool, antpool) | Never |
| 0.20 | [0.000, 0.196] | 0–1 small/medium pool | Never |
| 0.25 | [0.014, 0.347] | 1–2 pools; foundryusa appears in ~some seeds | Rarely (~10% of seeds) |
| 0.30 | [0.126, 0.374] | 1–3 pools; foundryusa appears in ~some seeds | Sometimes (~20% of seeds) |
| 0.35 | [0.161, 0.401] | 1–4 pools; foundryusa appears in more seeds | More often (~30% of seeds) |

**Critical threshold**: When foundryusa (30% hashrate) is committed v27, C_eff jumps to 0.347+.
Expect discontinuous behavior when foundryusa crosses from neutral/v26 to v27-committed.

**Lite pool hashrate shares** (of total pool hashrate = 86.4% of network):

| Pool | Share | Starting side |
|---|---|---|
| Foundry USA | 30.0% | v27 |
| AntPool | 16.9% | v26 |
| ViaBTC | 11.2% | v26 |
| F2Pool | 10.9% | v26 |
| SpiderPool | 9.3% | v26 |
| MARA Pool | 4.6% | v27 |
| Luxor | 2.3% | v27 |
| Ocean | 1.2% | v27 |

---

## Scenario-to-Namespace Mapping

**Iteration order: vr (outer) → E → C → composition (inner)**

| Server | Namespace | Scenarios | vr | E |
|---|---|---|---|---|
| 1 | cft-0 | sweep_0000–0009 | 0.20 | 0.30 |
| 1 | cft-1 | sweep_0010–0019 | 0.20 | 0.40 |
| 1 | cft-2 | sweep_0020–0029 | 0.20 | 0.50 |
| 1 | cft-3 | sweep_0030–0039 | 0.20 | 0.55 |
| 1 | cft-4 | sweep_0040–0049 | 0.50 | 0.30 |
| 1 | cft-5 | sweep_0050–0059 | 0.50 | 0.40 |
| 2 | cft-0 | sweep_0060–0069 | 0.50 | 0.50 |
| 2 | cft-1 | sweep_0070–0079 | 0.50 | 0.55 |
| 2 | cft-2 | sweep_0080–0089 | 1.00 | 0.30 |
| 2 | cft-3 | sweep_0090–0099 | 1.00 | 0.40 |
| 2 | cft-4 | sweep_0100–0109 | 1.00 | 0.50 |
| 2 | cft-5 | sweep_0110–0119 | 1.00 | 0.55 |

---

## Pre-flight: Configs Already Generated

All configs are pre-generated in this repo — no generation or build step needed.

Verify the expected files exist:
```bash
ls tools/sweep/contested_fork_threshold/configs/network/ | wc -l   # should be 120
ls tools/sweep/contested_fork_threshold/configs/pools/              # sweep_pools_config.yaml
ls tools/sweep/contested_fork_threshold/configs/economic/           # sweep_economic_config.yaml
ls tools/sweep/contested_fork_threshold/networks/ | wc -l           # should be 120
ls tools/sweep/contested_fork_threshold/build_manifest_server1.json
ls tools/sweep/contested_fork_threshold/build_manifest_server2.json
```

Spot-check scenarios:
```bash
python3 -c "
import json
with open('tools/sweep/contested_fork_threshold/build_manifest.json') as f:
    m = json.load(f)
for sid in [0, 10, 40, 80]:
    s = m['scenarios'][sid]
    p = s['parameters']
    print(f\"{s['scenario_id']}: vr={p['violation_rate']} E={p['economic_split']} C={p['pool_committed_split']} comp={p['composition_index']} C_eff={p['committed_hashrate_actual']:.3f}\")
"
# Expected:
# sweep_0000: vr=0.2  E=0.30 C=0.15 comp=0 C_eff=...
# sweep_0010: vr=0.2  E=0.40 C=0.15 comp=0 C_eff=...
# sweep_0040: vr=0.5  E=0.30 C=0.15 comp=0 C_eff=...
# sweep_0080: vr=1.0  E=0.30 C=0.15 comp=0 C_eff=...
```

---

## Step 1: Sync to Servers (dev machine)

```bash
rsync -av tools/sweep/contested_fork_threshold/ \
    server1:~/warnetScenarioDiscovery/tools/sweep/contested_fork_threshold/

rsync -av tools/sweep/contested_fork_threshold/ \
    server2:~/warnetScenarioDiscovery/tools/sweep/contested_fork_threshold/
```

Also sync the scenario script (pool switching fix is included):
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
for i in $(seq 0 5); do kubectl create namespace cft-$i; done
```

---

## Step 4: Run Scenarios

Launch each namespace in its own tmux pane. Stagger launches by ~2 minutes between
panes to avoid simultaneous startup collisions.

All commands run from `~/warnetScenarioDiscovery/`.

### Server 1

**Pane 0 — namespace cft-0 (sweep_0000–0009 | vr=0.20 E=0.30):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server1 \
  --namespace cft-0 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 0 9))
```

**Pane 1 — namespace cft-1 (sweep_0010–0019 | vr=0.20 E=0.40):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server1 \
  --namespace cft-1 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 10 19))
```

**Pane 2 — namespace cft-2 (sweep_0020–0029 | vr=0.20 E=0.50):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server1 \
  --namespace cft-2 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 20 29))
```

**Pane 3 — namespace cft-3 (sweep_0030–0039 | vr=0.20 E=0.55):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server1 \
  --namespace cft-3 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 30 39))
```

**Pane 4 — namespace cft-4 (sweep_0040–0049 | vr=0.50 E=0.30):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server1 \
  --namespace cft-4 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 40 49))
```

**Pane 5 — namespace cft-5 (sweep_0050–0059 | vr=0.50 E=0.40):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server1 \
  --namespace cft-5 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 50 59))
```

---

### Server 2

**Pane 0 — namespace cft-0 (sweep_0060–0069 | vr=0.50 E=0.50):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server2 \
  --namespace cft-0 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 60 69))
```

**Pane 1 — namespace cft-1 (sweep_0070–0079 | vr=0.50 E=0.55):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server2 \
  --namespace cft-1 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 70 79))
```

**Pane 2 — namespace cft-2 (sweep_0080–0089 | vr=1.00 E=0.30):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server2 \
  --namespace cft-2 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 80 89))
```

**Pane 3 — namespace cft-3 (sweep_0090–0099 | vr=1.00 E=0.40):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server2 \
  --namespace cft-3 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 90 99))
```

**Pane 4 — namespace cft-4 (sweep_0100–0109 | vr=1.00 E=0.50):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server2 \
  --namespace cft-4 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 100 109))
```

**Pane 5 — namespace cft-5 (sweep_0110–0119 | vr=1.00 E=0.55):**
```bash
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/contested_fork_threshold/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/contested_fork_threshold/results_server2 \
  --namespace cft-5 \
  --startup-wait 60 --cooldown 30 \
  --no-auto-restart \
  --scenarios $(printf "sweep_%04d " $(seq 110 119))
```

---

## Monitoring

```bash
# Count completed results (each completed scenario writes results.json)
find tools/sweep/contested_fork_threshold/results_server1 -name "results.json" | wc -l
find tools/sweep/contested_fork_threshold/results_server2 -name "results.json" | wc -l
# Should reach 60 each (120 total)

# Incrementally view pain metrics as results arrive
python3 -c "
from pathlib import Path
import json

SWEEP = 'tools/sweep/contested_fork_threshold'
results = sorted(Path(SWEEP).rglob('results.json'))
rows = []
for p in results:
    try:
        r = json.load(open(p))
        fc = r.get('fork_convergence', {})
        params = r.get('parameters', {})
        vr  = params.get('violation_rate', '?')
        c   = params.get('pool_committed_split', '?')
        e   = params.get('economic_split', '?')
        c_eff = params.get('committed_hashrate_actual', 0)
        comp = params.get('composition_index', '?')
        healed = fc.get('healed', False)
        v27b = fc.get('v27_blocks', 0) or 0
        v26b = fc.get('v26_blocks', 0) or 0
        heal_s = fc.get('heal_time_s', 0) or 0
        if healed and max(v27b, v26b) > 0:
            reorg_depth = min(v27b, v26b)
            fork_balance = round(min(v27b, v26b) / max(v27b, v26b), 3)
            pain_score = round(reorg_depth * fork_balance, 1)
        else:
            reorg_depth = fork_balance = pain_score = 0
        rows.append((pain_score, vr, c, e, comp, c_eff, reorg_depth, fork_balance, heal_s, p.parent.name))
    except Exception:
        pass
rows.sort(key=lambda x: -x[0])
print(f'{'scenario':<12} {'vr':>5} {'C':>5} {'E':>5} {'C_eff':>6} {'comp':>4} {'depth':>6} {'bal':>5} {'pain':>6} {'heal_s':>7}')
for pain, vr, c, e, comp, c_eff, depth, bal, heal_s, sid in rows[:30]:
    print(f'{sid:<12} {vr:>5} {c:>5} {e:>5} {c_eff:>6.3f} {comp:>4} {depth:>6} {bal:>5.3f} {pain:>6.1f} {heal_s:>7.0f}')
print(f'\nCompleted: {len(rows)}/120')
"

# Check for missing scenarios
python3 -c "
from pathlib import Path
import json
with open('tools/sweep/contested_fork_threshold/build_manifest.json') as f:
    m = json.load(f)
completed = {p.parent.name for p in Path('tools/sweep/contested_fork_threshold').rglob('results.json')}
missing = [s['scenario_id'] for s in m['scenarios'] if s['scenario_id'] not in completed]
print(f'Completed: {len(completed)}/120')
if missing:
    print(f'Missing ({len(missing)}): {missing[:20]}')
"
```

---

## Step 5: Collect Results (dev machine)

Pull incrementally as namespaces complete — no need to wait for all 120:
```bash
rsync -av server1:~/warnetScenarioDiscovery/tools/sweep/contested_fork_threshold/results_server1/ \
    tools/sweep/contested_fork_threshold/results_server1/

rsync -av server2:~/warnetScenarioDiscovery/tools/sweep/contested_fork_threshold/results_server2/ \
    tools/sweep/contested_fork_threshold/results_server2/
```

---

## Step 6: Analyze

```bash
python3 tools/sweep/4_analyze_results.py \
    --sweep contested_fork_threshold \
    --results tools/sweep/contested_fork_threshold/results_server1 \
               tools/sweep/contested_fork_threshold/results_server2 \
    --manifest tools/sweep/contested_fork_threshold/build_manifest.json \
    --output tools/sweep/contested_fork_threshold/results/analysis
```

**Key analysis targets:**

- **pain_score = reorg_depth × fork_balance** — primary metric; higher = more painful reorg
- **reorg_depth** = minority chain length at heal — how many blocks the losing side must orphan
- **fork_balance** = min/max block ratio at heal — 1.0 is maximally contested (equal sides)
- **What C_eff threshold makes foundryusa commit?** Compositions with foundryusa in v27-committed
  show discontinuous behavior relative to those without it
- **Does vr=0.20 produce meaningfully painful reorgs, or does pain only begin at vr≥0.50?**
- **What is the (vr, C) combination that maximizes pain_score?** (primary research question)
- **E analysis**: Since E does not vary network topology in [0.30, 0.55], treat E × comp = 8 trials
  per (vr, C) point. Aggregate across E to estimate true variance from composition effects.

**Expected pattern (hypothesis):**
- vr=0.20: forks heal quickly, reorg_depth low, pain_score low
- vr=0.50: meaningful fork depths, pain_score rises with C
- vr=1.00 + high C: maximum pain — deepest forks before economic cascade resolves them
- C=0.15: no committed v27 pool → v26 dominates, fast resolution, low pain
- C=0.35 with foundryusa committed: highest C_eff (0.35–0.40) → deep v27 fork before cascade

---

## Notes

- **E invariance**: All E ∈ [0.30, 0.55] produce identical lite network topologies (see Design Summary).
  E is recorded per-scenario but does not drive variation. Analyze as vr × C × comp (30 unique points).
- **Composition effects**: C_eff varies substantially within each nominal C value (e.g. C=0.30 ranges
  from 0.126 to 0.374). The foundryusa-committed compositions at high C are qualitatively different
  from small-pool compositions at the same nominal C. Consider splitting analysis by C_eff quartile.
- **`--interval 2`**: 2-second block interval. Do NOT change — retarget at interval=10 never fires.
- **`--duration 13000`**: ~3.6h max per scenario. With `--fork-heal-exit`, healing scenarios exit early.
  vr=0.20 scenarios may heal in <30 min; vr=1.00 + high C may run the full 3.6h.
- **Namespace prefix `cft-`**: distinct from `csp-`, `fft-`, `poolarma-` namespaces.
- **Resume**: Re-run the same namespace command if interrupted — completed scenarios are skipped.
- **Stagger starts**: Wait ~2 minutes between namespace launches on the same server.
- **Results location**: `results_server1/sweep_XXXX/` and `results_server2/sweep_XXXX/`
- **Scenario file sync**: Confirm `scenarios/partition_miner_with_pools.py` is synced before launching.
