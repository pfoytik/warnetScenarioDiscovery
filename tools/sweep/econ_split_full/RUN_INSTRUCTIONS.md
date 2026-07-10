# econ_split_full — Run Instructions

**Research question:** How does economic split (E) influence fork outcomes when it can actually vary?
The contested_fork_threshold sweep established that E is invariant on the lite network across
[0.28, 0.78]. This sweep runs on the full network (realistic-economy, 60 nodes, 52 economic
nodes with graduated custody) where E produces 6 distinct topologies.

## Design Summary

| Parameter | Values |
|---|---|
| Network | realistic-economy (60 nodes, 88.2% pool hashrate) |
| economic_split (E) | 0.25, 0.45, 0.58, 0.68, 0.76, 0.82 |
| violation_rate (vr) | 0.20, 0.50, 1.00 |
| pool_committed_split (C) | 0.20, 0.25, 0.30 |
| compositions | 2 per (E, vr, C) point |
| Total scenarios | 108 |
| Duration | 13,000s |
| Block interval | 2s |
| Retarget period | 2,016 blocks |
| fork_heal_exit | True |
| Est. runtime | ~80–100h per namespace |

## Full Network E Step Boundaries

Each selected E value falls in a distinct topology interval. Raising E past a boundary tags
one additional economic node as v27, increasing the economic weight behind the softfork.

| E value | Nodes tagged v27 | Cumul custody | Boundary crossed |
|---|---|---|---|
| **0.25** | 1 — node-0034 (major exchange) | 28% | E ≥ 0.139 |
| **0.45** | 2 — +node-0004 (major exchange) | 47% | E ≥ 0.372 |
| **0.58** | 3 — +node-0043 (institutional) | 58% | E ≥ 0.522 |
| **0.68** | 4 — +node-0005 (major exchange) | 69% | E ≥ 0.636 |
| **0.76** | 5 — +node-0035 (major exchange) | 77% | E ≥ 0.729 |
| **0.82** | 6 — +node-0036 (exchange) | 82% | E ≥ 0.794 |

E=0.58 is comparable to the CSP/CFT baseline (lite network always had 56.7% custody on v27).

## Full Network Pool Landscape

| Pool | Hashrate | Initial fork | Committed when |
|---|---|---|---|
| Foundry USA | 26.89% | v27 | always starts v27 |
| AntPool | 19.25% | v26 | committed at higher C seeds |
| ViaBTC | 11.39% | v26 | committed at higher C seeds |
| F2Pool | 11.25% | v26 | committed at higher C seeds |
| Binance Pool | 10.04% | v26 | committed at higher C seeds |
| MARA Pool | 4.85% | v27 | always starts v27 |
| Luxor | 3.12% | v27 | always starts v27 |
| Ocean | 1.42% | v27 | always starts v27 |

**Total pool hashrate: 88.21%** (vs 86.4% on lite network)

Foundry USA (26.89%) remains the pivotal pool. On the full network, AntPool (19.25%) is
the largest single v26 pool — larger than any single pool in the lite network.

## Namespace — Scenario Mapping

### Server 1 (sweep_0000–0053, E=0.25/0.45/0.58)

| Namespace | Scenarios | E values | vr values |
|---|---|---|---|
| esf-0 | sweep_0000–0008 | 0.25 | 0.20, 0.50 |
| esf-1 | sweep_0009–0017 | 0.25 | 0.50, 1.00 |
| esf-2 | sweep_0018–0026 | 0.45 | 0.20, 0.50 |
| esf-3 | sweep_0027–0035 | 0.45 | 0.50, 1.00 |
| esf-4 | sweep_0036–0044 | 0.58 | 0.20, 0.50 |
| esf-5 | sweep_0045–0053 | 0.58 | 0.50, 1.00 |

### Server 2 (sweep_0054–0107, E=0.68/0.76/0.82)

| Namespace | Scenarios | E values | vr values |
|---|---|---|---|
| esf-0 | sweep_0054–0062 | 0.68 | 0.20, 0.50 |
| esf-1 | sweep_0063–0071 | 0.68 | 0.50, 1.00 |
| esf-2 | sweep_0072–0080 | 0.76 | 0.20, 0.50 |
| esf-3 | sweep_0081–0089 | 0.76 | 0.50, 1.00 |
| esf-4 | sweep_0090–0098 | 0.82 | 0.20, 0.50 |
| esf-5 | sweep_0099–0107 | 0.82 | 0.50, 1.00 |

## Run Commands

Copy the `econ_split_full/` directory to each server before running.

### Server 1

```bash
# esf-0: sweep_0000–0008
warnet run tools/sweep/econ_split_full/networks/sweep_0000/network.yaml --namespace esf-0 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server1 \
  --namespace esf-0 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 0 8))

# esf-1: sweep_0009–0017
warnet run tools/sweep/econ_split_full/networks/sweep_0009/network.yaml --namespace esf-1 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server1 \
  --namespace esf-1 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 9 17))

# esf-2: sweep_0018–0026
warnet run tools/sweep/econ_split_full/networks/sweep_0018/network.yaml --namespace esf-2 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server1 \
  --namespace esf-2 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 18 26))

# esf-3: sweep_0027–0035
warnet run tools/sweep/econ_split_full/networks/sweep_0027/network.yaml --namespace esf-3 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server1 \
  --namespace esf-3 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 27 35))

# esf-4: sweep_0036–0044
warnet run tools/sweep/econ_split_full/networks/sweep_0036/network.yaml --namespace esf-4 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server1 \
  --namespace esf-4 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 36 44))

# esf-5: sweep_0045–0053
warnet run tools/sweep/econ_split_full/networks/sweep_0045/network.yaml --namespace esf-5 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server1.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server1 \
  --namespace esf-5 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 45 53))
```

### Server 2

```bash
# esf-0: sweep_0054–0062
warnet run tools/sweep/econ_split_full/networks/sweep_0054/network.yaml --namespace esf-0 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server2 \
  --namespace esf-0 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 54 62))

# esf-1: sweep_0063–0071
warnet run tools/sweep/econ_split_full/networks/sweep_0063/network.yaml --namespace esf-1 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server2 \
  --namespace esf-1 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 63 71))

# esf-2: sweep_0072–0080
warnet run tools/sweep/econ_split_full/networks/sweep_0072/network.yaml --namespace esf-2 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server2 \
  --namespace esf-2 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 72 80))

# esf-3: sweep_0081–0089
warnet run tools/sweep/econ_split_full/networks/sweep_0081/network.yaml --namespace esf-3 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server2 \
  --namespace esf-3 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 81 89))

# esf-4: sweep_0090–0098
warnet run tools/sweep/econ_split_full/networks/sweep_0090/network.yaml --namespace esf-4 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server2 \
  --namespace esf-4 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 90 98))

# esf-5: sweep_0099–0107
warnet run tools/sweep/econ_split_full/networks/sweep_0099/network.yaml --namespace esf-5 && \
python3 tools/sweep/3_run_sweep.py \
  --input tools/sweep/econ_split_full/build_manifest_server2.json \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --results-dir tools/sweep/econ_split_full/results_server2 \
  --namespace esf-5 --startup-wait 60 --cooldown 30 \
  --scenarios $(printf "sweep_%04d " $(seq 99 107))
```

## Monitoring

Check progress as results arrive:

```bash
python3 - << 'EOF'
import json
from pathlib import Path
from collections import defaultdict

SWEEP = Path("tools/sweep/econ_split_full")
with open(SWEEP / "scenarios.json") as f:
    params = {s["scenario_id"]: s for s in json.load(f)["scenarios"]}

results = []
for rj in sorted(SWEEP.rglob("results.json")):
    sid = rj.parent.name
    if sid not in params: continue
    p = params[sid]
    r = json.load(open(rj))
    fc   = r.get("fork_convergence", {})
    summ = r.get("summary", {})
    reu  = r.get("reorg", {}).get("reunion_analysis", {})

    heal_s  = fc.get("heal_time_s")
    v27_blk = fc.get("v27_blocks_at_heal")
    v26_blk = fc.get("v26_blocks_at_heal")
    total   = summ.get("total_blocks")
    v27hr   = summ.get("final_hashrate", {}).get("v27")
    winner  = reu.get("winning_fork")

    pain = None
    if v27_blk and v26_blk:
        rd   = min(v27_blk, v26_blk)
        fb   = rd / max(v27_blk, v26_blk)
        pain = round(rd * fb, 1)

    startup = heal_s is not None and heal_s <= 30 and total is not None and total <= 10
    results.append({"sid": sid, "E": p["economic_split"], "vr": p["violation_rate"],
                    "C": p["pool_committed_split"], "C_eff": p["committed_hashrate_actual"],
                    "winner": winner, "pain": pain, "startup": startup,
                    "heal_s": heal_s, "v27hr": v27hr})

genuine = [r for r in results if not r["startup"] and r["winner"]]
print(f"Complete: {len(results)}/108  Genuine: {len(genuine)}  "
      f"Failures: {sum(1 for r in results if r['startup'])}")

# Win rate by E
print("\nv27 win rate by E:")
for e in [0.25, 0.45, 0.58, 0.68, 0.76, 0.82]:
    sub = [r for r in genuine if r["E"] == e]
    if not sub: print(f"  E={e}: —"); continue
    v27c = sum(1 for r in sub if r["winner"] == "v27")
    print(f"  E={e}: {v27c}/{len(sub)} v27 wins ({v27c/len(sub)*100:.0f}%)")
EOF
```

## Collecting Results

```bash
# From local machine — collect server1 results
rsync -avz server1:~/warnetScenarioDiscovery/tools/sweep/econ_split_full/results_server1/ \
  tools/sweep/econ_split_full/results_server1/

# From local machine — collect server2 results
rsync -avz server2:~/warnetScenarioDiscovery/tools/sweep/econ_split_full/results_server2/ \
  tools/sweep/econ_split_full/results_server2/
```

## Analysis Targets

**Primary question:** Does v27 win rate increase monotonically with E at fixed (vr, C)?
- If yes: E provides a meaningful continuous lever alongside C_eff
- If not: economic support above a threshold doesn't help further

**Secondary questions:**
- Does the C_eff hard threshold (foundryusa at ~0.30) persist at all E values, or does high
  E reduce the threshold needed for v27 to win?
- Does vr suppression of v27 (observed in CFT) diminish at high E?
- Where is the pain-maximizing (E, C_eff) combination?

**Key comparison:** E=0.58 results here should be comparable to CFT results at E=0.55
(same approximate custody level, different network topology due to more graduated nodes).
Differences indicate full vs. lite network effects beyond just E variation.
