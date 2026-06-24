# Arm A: Pool Composition Decoupling — Run Instructions

168 scenarios, 84 per server, 6 parallel namespaces, ~50h wall-clock.

---

## Pre-flight (both servers)

```bash
cd ~/warnetScenarioDiscovery
git pull
warnet status   # verify cluster is healthy
```

---

## Server 1 — scenarios 0–83

```bash
cd ~/warnetScenarioDiscovery/tools/sweep
python 3_run_sweep.py \
  --input pool_composition_arm_a/build_manifest_server1.json \
  --results-dir pool_composition_arm_a/results \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --namespace arm-a-s1 --parallel 6
```

## Server 2 — scenarios 84–167

```bash
cd ~/warnetScenarioDiscovery/tools/sweep
python 3_run_sweep.py \
  --input pool_composition_arm_a/build_manifest_server2.json \
  --results-dir pool_composition_arm_a/results \
  --duration 13000 --retarget-interval 2016 --interval 2 \
  --namespace arm-a-s2 --parallel 6
```

---

## Collect results via git

When each server finishes, commit and push results:

```bash
cd ~/warnetScenarioDiscovery
git add tools/sweep/pool_composition_arm_a/results/
git commit -m "pool_composition_arm_a results server1"   # or server2
git push
```

On dev machine:
```bash
git pull
```

---

## Load into database

```bash
python tools/sweep/5_build_database.py \
  --results-dir tools/sweep/pool_composition_arm_a/results \
  --sweep-name pool_composition_arm_a \
  --db tools/sweep/sweep_results.db
```
