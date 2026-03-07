# Running Parallel Sweeps

---

## Part 1: Production Servers (PRIM/CART Dataset)

Guide for running large-scale parallel sweeps across two dedicated Ubuntu servers for
scenario discovery using PRIM and CART methods.

### Server Specs

- **2 × servers**: 64 cores, 250 GiB RAM each
- **OS**: Ubuntu (bare metal)
- **Cluster**: k3s (one independent k3s instance per server — not minikube)

### Why k3s, Not Minikube

Minikube is a development tool designed for laptops. For bare metal Ubuntu servers,
k3s is the correct choice: single-command install, production-grade, same kubectl/namespace
interface, no VM overhead.

```bash
# Install k3s on each server
curl -sfL https://get.k3s.io | sh -

# Set maxPods (default 110 is too low for parallel scenarios)
# Add to /etc/rancher/k3s/config.yaml:
kubelet-arg:
  - "max-pods=600"

# Restart k3s
sudo systemctl restart k3s

# Verify
kubectl get nodes
```

### Resource Budget Per Server

Each scenario uses approximately:
- ~49 pods (48 Bitcoin nodes + 1 commander)
- ~24 GiB RAM
- ~3.5 CPU cores at peak

| Resource | Per scenario | 5 parallel | Server budget | Headroom |
|---|---|---|---|---|
| RAM | 24 GiB | 120 GiB | 250 GiB | ~130 GiB ✓ |
| Pods | 49 | 245 | 600 (maxPods) | ~355 ✓ |
| CPU | 3.5 cores | 17.5 | 64 cores | ~46 cores ✓ |

**5 parallel scenarios per server is the safe target.** RAM headroom is generous; could
push to 8 if needed but 5 is conservative and reliable.

### Warnet Installation on Bare Metal

```bash
# Clone repos on each server
git clone <warnet-repo> ~/warnet
git clone <warnetScenarioDiscovery-repo> ~/bitcoin/warnetScenarioDiscovery

# Install warnet (follow warnet's own install docs for k3s target)
cd ~/warnet
# ... warnet helm/kubectl deployment steps ...

# Verify warnet is running
warnet status
```

### Namespace Support in `3_run_sweep.py` (NOT YET IMPLEMENTED)

The sweep runner currently has no `--namespace` flag. Before running parallel sweeps
on the production servers, two changes are required:

**Change 1 — Namespace flag and worker pool**

Add `--namespace` and `--parallel` flags to `3_run_sweep.py`. Replace the sequential
scenario loop with a `concurrent.futures.ThreadPoolExecutor` worker pool. Each worker:
1. Acquires the config injection file lock
2. Writes scenario configs to `scenarios/config/`
3. Calls `warnet deploy --namespace <ns>` and `warnet run --namespace <ns>`
4. Releases the lock (rest of the ~90 min scenario runs fully in parallel)
5. Collects results and writes to the results directory

```python
# Sketch of the parallel runner pattern
from concurrent.futures import ThreadPoolExecutor
import fcntl

LOCK_FILE = "scenarios/config/.sweep_inject.lock"

def run_scenario(scenario, namespace, results_dir):
    # Critical section: inject configs and deploy
    with open(LOCK_FILE, 'w') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        inject_configs(scenario)
        deploy(namespace)
    # Non-critical: wait for completion and collect results (~90 min)
    wait_for_completion(namespace)
    collect_results(namespace, results_dir)

with ThreadPoolExecutor(max_workers=5) as pool:
    for i, scenario in enumerate(scenarios):
        ns = f"sweep-worker-{i % 5}"
        pool.submit(run_scenario, scenario, ns, results_dir)
```

**Change 2 — Namespace-aware teardown**

`warnet down` has no namespace flag. Use kubectl directly for teardown:

```bash
kubectl -n <namespace> delete pods --all --force --grace-period=0
```

### Distributing Work Across Two Servers

Each server runs its own independent sweep runner against its own half of the scenario
batch. No coordination between servers is needed during the run.

```bash
# On server 1 — first half of scenarios
python 3_run_sweep.py \
    --input prim_cart_sweep/build_manifest.json \
    --results-dir prim_cart_sweep/results \
    --namespace-prefix sweep \
    --parallel 5 \
    --duration 5400

# On server 2 — second half of scenarios (use --offset flag or separate manifest)
python 3_run_sweep.py \
    --input prim_cart_sweep/build_manifest_server2.json \
    --results-dir prim_cart_sweep/results \
    --namespace-prefix sweep \
    --parallel 5 \
    --duration 5400
```

Splitting the manifest into two halves is done at build time — generate two separate
`build_manifest.json` files (scenarios 0–149 and 150–299) or add an `--offset` and
`--count` flag to the runner.

### Collecting Results

After both servers finish, rsync results back to the development machine:

```bash
rsync -av server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/prim_cart_sweep/results/ \
    tools/sweep/prim_cart_sweep/results/

rsync -av server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/prim_cart_sweep/results/ \
    tools/sweep/prim_cart_sweep/results/

# Then run combined analysis
python 4_analyze_results.py \
    --input tools/sweep/prim_cart_sweep/results \
    --manifest tools/sweep/prim_cart_sweep/build_manifest_combined.json
```

### Time Estimates (300 scenarios, 5 parallel per server)

| Scenario duration | Wall-clock time | Notes |
|---|---|---|
| 1800s (current rapid) | ~15 hours | No 2016-block retarget |
| 5400s (~90 min) | ~45 hours | 1 full 2016-block retarget cycle |
| 7200s (120 min) | ~60 hours | ~1.5 retarget cycles |

**Recommended duration for PRIM/CART dataset: 5400s** — enough for one full 2016-block
retarget cycle (4032 seconds at 2s/block) with buffer for cascade dynamics to resolve.

### Checklist Before Starting (Production Servers)

- [ ] k3s installed on both servers with `maxPods=600`
- [ ] Warnet deployed and verified on both servers
- [ ] Repos cloned and symlinks set up on both servers
- [ ] `--namespace` and `--parallel` flags implemented in `3_run_sweep.py`
- [ ] Config injection file lock (`fcntl.flock`) implemented
- [ ] PRIM/CART LHS generated (`scenarios.json`, 300 scenarios, 4–5 parameters)
- [ ] Manifests built and split into server1/server2 halves
- [ ] Tested with `--dry-run` on both servers before committing to full run
- [ ] rsync target directory prepared on dev machine

---

## Part 2: Development Machine (Two Parallel Sweeps)

Guide for running two simultaneous parameter sweeps on the development machine using
Kubernetes namespace isolation.

### Machine Specs

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
