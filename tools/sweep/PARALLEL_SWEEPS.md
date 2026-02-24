# Running Two Parallel Sweeps

Guide for running two simultaneous parameter sweeps on the development machine using
Kubernetes namespace isolation.

## Machine Specs

- **RAM**: 64 GiB total
- **CPU**: 16 cores (minikube currently allocated 12)
- **Cluster**: single minikube node

## Why Parallelism Is Feasible

Each scenario uses approximately:
- ~49 pods (48 Bitcoin nodes + 1 commander)
- ~24 GiB RAM (actual usage; pods declare minimal resource requests)
- ~3.5 CPU cores at peak

The bottleneck is **not CPU** — it is pod count and RAM.

### Current minikube limits (as of first sweep)

| Limit | Value | Problem for 2 sweeps |
|---|---|---|
| `maxPods` | 110 | 2 scenarios need ~120 pods → **hard blocker** |
| Memory | ~62 GiB | Tight with other processes running |
| CPUs | 12 | Fine |

---

## Step 1 — Clear Other Processes

Before starting, free up RAM by stopping non-essential processes on the host.
Target: leave only the OS and minikube running. This frees ~20+ GiB and eliminates
swap pressure (swap was fully exhausted during the first sweep).

---

## Step 2 — Restart Minikube with Increased Resources

```bash
minikube stop

minikube start \
  --cpus=14 \
  --memory=57344 \
  --extra-config=kubelet.maxPods=220
```

- `--cpus=14`: leaves 2 cores for the OS
- `--memory=57344`: 56 GiB to minikube, leaves ~8 GiB for OS
- `--maxPods=220`: supports 2 concurrent scenarios (120 pods) with room for system pods

### Resource headroom at 2 parallel sweeps

| Resource | Budget | Used (2 sweeps) | Remaining |
|---|---|---|---|
| Pods | 220 | ~120 (2×49 + 21 system) | ~100 |
| RAM | 56 GiB | ~48 GiB (2×24 GiB) | ~8 GiB |
| CPU | 14 cores | ~7 cores | ~7 cores |

> **Note:** 3 parallel sweeps would require ~84 GiB RAM and is not feasible on this machine.

---

## Step 3 — Ensure Namespace Support in `3_run_sweep.py`

The sweep runner needs a `--namespace` flag before parallel runs are safe. Two changes
are required:

### 3a. Namespace-aware warnet/kubectl commands

`warnet deploy` and `warnet run` both accept `--namespace TEXT`. All `kubectl` commands
need `-n <namespace>` added. Since `warnet down` has no namespace flag, teardown of a
specific namespace must use kubectl directly:

```bash
# Instead of: warnet down --force
kubectl -n <namespace> delete pods --all --force --grace-period=0
```

### 3b. Config injection file lock

`3_run_sweep.py` writes to shared config files in `scenarios/config/` right before
calling `warnet run`. If two instances do this simultaneously, they overwrite each
other's configs before the scenario pods are deployed.

Fix: hold a `fcntl.flock` file lock from the moment configs are injected until
`warnet run` completes (a few seconds). The lock file lives at:
```
scenarios/config/.sweep_inject.lock
```

This serializes only the inject→deploy window; the rest of each scenario (~60 min)
runs fully in parallel.

---

## Step 4 — Build Two Separate Sweep Outputs

Each sweep needs its own output directory and `build_manifest.json`.

```bash
cd tools/sweep

# Sweep v1 — biased parameterization (already built, use existing)
# Output: tools/sweep/realistic_sweep/

# Sweep v2 — symmetric parameterization
python 1_generate_scenarios.py --samples 50 --seed 42 --output scenarios_v2.json
python 2_build_configs.py \
    --input scenarios_v2.json \
    --base-network ../../networks/realistic-economy/network.yaml \
    --output-dir realistic_sweep_v2
```

Use a different `--seed` if you want a fully independent sample:
```bash
python 1_generate_scenarios.py --samples 50 --seed 99 --output scenarios_v2.json
```

---

## Step 5 — Run Both Sweeps in Separate Terminals

Once `3_run_sweep.py` has namespace support:

**Terminal 1:**
```bash
cd tools/sweep
python 3_run_sweep.py \
    --input realistic_sweep_v2/build_manifest.json \
    --results-dir realistic_sweep_v2/results \
    --namespace sweep-v2 \
    --duration 3600
```

**Terminal 2** (start a few minutes after Terminal 1 to stagger deployments):
```bash
cd tools/sweep
python 3_run_sweep.py \
    --input realistic_sweep_v3/build_manifest.json \
    --results-dir realistic_sweep_v3/results \
    --namespace sweep-v3 \
    --duration 3600
```

> Staggering by a few minutes ensures the two instances are never simultaneously
> in the inject→deploy critical section, reducing lock contention.

---

## Step 6 — Monitor Both Sweeps

```bash
# Watch pods across both namespaces
kubectl get pods --all-namespaces -w

# Check progress files
watch -n 30 "cat tools/sweep/realistic_sweep_v2/results/sweep_progress.json | python3 -m json.tool"
watch -n 30 "cat tools/sweep/realistic_sweep_v3/results/sweep_progress.json | python3 -m json.tool"

# Analyze results mid-sweep (safe to run anytime)
python tools/sweep/4_analyze_results.py --input tools/sweep/realistic_sweep_v2/results
python tools/sweep/4_analyze_results.py --input tools/sweep/realistic_sweep_v3/results
```

---

## Time Estimate

With 2 sweeps running in parallel, wall-clock time for 50 scenarios each:

| Sequential (1 sweep) | Parallel (2 sweeps) |
|---|---|
| ~50 hours | ~50 hours |

Both sweeps complete in the same wall-clock time as one — the machine is doing twice
the work for the same elapsed time. A 50-scenario sweep at 1 hour each runs over a
weekend comfortably (~2 days).

---

## Checklist Before Starting

- [ ] Other processes cleared, swap pressure relieved
- [ ] Minikube restarted with `--cpus=14 --memory=57344 --extra-config=kubelet.maxPods=220`
- [ ] Namespace support added to `3_run_sweep.py` (`--namespace` flag + file lock)
- [ ] `scenarios_v2.json` generated with symmetric parameters
- [ ] `realistic_sweep_v2/` built with `2_build_configs.py`
- [ ] Tested with `--dry-run` in both namespaces before committing to full run
- [ ] Two terminals open and ready
