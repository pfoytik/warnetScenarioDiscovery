# lhs_user_weight_prim — Run Commands

60 scenarios, 12 namespaces (6 per server), 5 scenarios per namespace.  
~18 hours wall-clock. Identical fixed params to `user_weight_threshold` for direct comparability.

Results go into separate `results_server1/` and `results_server2/` directories to
avoid rsync collisions when collecting.

---

## Server 1 — sweep_0000 through sweep_0029 (ns-0 → ns-5)

### Create namespaces

```bash
kubectl create namespace ns-0
kubectl create namespace ns-1
kubectl create namespace ns-2
kubectl create namespace ns-3
kubectl create namespace ns-4
kubectl create namespace ns-5
```

### Run (one terminal per namespace)

```bash
# ns-0 — sweep_0000–0004
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server1 \
    --namespace ns-0 \
    --scenarios sweep_0000 sweep_0001 sweep_0002 sweep_0003 sweep_0004 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-1 — sweep_0005–0009
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server1 \
    --namespace ns-1 \
    --scenarios sweep_0005 sweep_0006 sweep_0007 sweep_0008 sweep_0009 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-2 — sweep_0010–0014
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server1 \
    --namespace ns-2 \
    --scenarios sweep_0010 sweep_0011 sweep_0012 sweep_0013 sweep_0014 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-3 — sweep_0015–0019
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server1 \
    --namespace ns-3 \
    --scenarios sweep_0015 sweep_0016 sweep_0017 sweep_0018 sweep_0019 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-4 — sweep_0020–0024
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server1 \
    --namespace ns-4 \
    --scenarios sweep_0020 sweep_0021 sweep_0022 sweep_0023 sweep_0024 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-5 — sweep_0025–0029
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server1 \
    --namespace ns-5 \
    --scenarios sweep_0025 sweep_0026 sweep_0027 sweep_0028 sweep_0029 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

---

## Server 2 — sweep_0030 through sweep_0059 (ns-6 → ns-11)

### Create namespaces

```bash
kubectl create namespace ns-6
kubectl create namespace ns-7
kubectl create namespace ns-8
kubectl create namespace ns-9
kubectl create namespace ns-10
kubectl create namespace ns-11
```

### Run (one terminal per namespace)

```bash
# ns-6 — sweep_0030–0034
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server2 \
    --namespace ns-6 \
    --scenarios sweep_0030 sweep_0031 sweep_0032 sweep_0033 sweep_0034 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-7 — sweep_0035–0039
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server2 \
    --namespace ns-7 \
    --scenarios sweep_0035 sweep_0036 sweep_0037 sweep_0038 sweep_0039 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-8 — sweep_0040–0044
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server2 \
    --namespace ns-8 \
    --scenarios sweep_0040 sweep_0041 sweep_0042 sweep_0043 sweep_0044 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-9 — sweep_0045–0049
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server2 \
    --namespace ns-9 \
    --scenarios sweep_0045 sweep_0046 sweep_0047 sweep_0048 sweep_0049 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-10 — sweep_0050–0054
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server2 \
    --namespace ns-10 \
    --scenarios sweep_0050 sweep_0051 sweep_0052 sweep_0053 sweep_0054 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-11 — sweep_0055–0059
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_user_weight_prim/build_manifest.json \
    --results-dir tools/sweep/lhs_user_weight_prim/results_server2 \
    --namespace ns-11 \
    --scenarios sweep_0055 sweep_0056 sweep_0057 sweep_0058 sweep_0059 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

---

## Collecting Results

Run from the dev machine after both servers finish. Results land in separate
directories so partial collection is safe mid-run.

```bash
rsync -av server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_user_weight_prim/results_server1/ \
    tools/sweep/lhs_user_weight_prim/results_server1/

rsync -av server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_user_weight_prim/results_server2/ \
    tools/sweep/lhs_user_weight_prim/results_server2/
```

Then merge into a single `results/` directory for analysis:

```bash
cp -r tools/sweep/lhs_user_weight_prim/results_server1/. \
      tools/sweep/lhs_user_weight_prim/results/
cp -r tools/sweep/lhs_user_weight_prim/results_server2/. \
      tools/sweep/lhs_user_weight_prim/results/
```

---

## Analysis

```bash
python tools/sweep/4_analyze_results.py \
    --input tools/sweep/lhs_user_weight_prim/results \
    --manifest tools/sweep/lhs_user_weight_prim/build_manifest.json
```

Boundary fitting (combined with threshold grid, n=88 total):

```bash
python tools/discovery/fit_boundary.py \
    --db tools/sweep/sweep_results.db \
    --sweep lhs_user_weight_prim user_weight_threshold
```

---

## Progress Monitoring

```bash
# Per-server progress (run on each server or after rsync)
cat tools/sweep/lhs_user_weight_prim/results_server1/sweep_progress.json
cat tools/sweep/lhs_user_weight_prim/results_server2/sweep_progress.json

# Pod status on each server
kubectl get pods --all-namespaces | grep -E "ns-[0-5]"   # server 1
kubectl get pods --all-namespaces | grep -E "ns-(6|7|8|9|10|11)"  # server 2
```

---

## Scenario Distribution Summary

| Namespace | Server | Scenarios         | UCF range (approx) | Split range (approx) |
|-----------|--------|-------------------|--------------------|----------------------|
| ns-0      | 1      | 0000–0004         | mixed LHS          | mixed LHS            |
| ns-1      | 1      | 0005–0009         | mixed LHS          | mixed LHS            |
| ns-2      | 1      | 0010–0014         | mixed LHS          | mixed LHS            |
| ns-3      | 1      | 0015–0019         | mixed LHS          | mixed LHS            |
| ns-4      | 1      | 0020–0024         | mixed LHS          | mixed LHS            |
| ns-5      | 1      | 0025–0029         | mixed LHS          | mixed LHS            |
| ns-6      | 2      | 0030–0034         | mixed LHS          | mixed LHS            |
| ns-7      | 2      | 0035–0039         | mixed LHS          | mixed LHS            |
| ns-8      | 2      | 0040–0044         | mixed LHS          | mixed LHS            |
| ns-9      | 2      | 0045–0049         | mixed LHS          | mixed LHS            |
| ns-10     | 2      | 0050–0054         | mixed LHS          | mixed LHS            |
| ns-11     | 2      | 0055–0059         | mixed LHS          | mixed LHS            |

LHS sampling means scenarios are not ordered by parameter value — each namespace
gets a representative cross-section of the (ucf, split) space rather than a slice.
