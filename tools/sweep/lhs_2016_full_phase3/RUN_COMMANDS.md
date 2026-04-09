# Full Phase 3 LHS — Run Commands

**300 scenarios targeting the PRIM uncertainty zone (2016-block regime, full 60-node network)**
**Source bounds:** `tools/discovery/output/2016/uncertainty_bounds.yaml`

Full network (60 nodes, 24 economic nodes) gives ~4% `economic_split` resolution vs 25% on lite.
Same seed and bounds as `lhs_2016_phase3` — matched pairs enable lite-vs-full equivalence validation.

---

## Cluster Setup

### Option A: k3s bare-metal servers (primary)

The two large servers run k3s with `maxPods=600`. No IP exhaustion or bridge port issues.
Each server can comfortably run 6 parallel 60-node scenarios (~61 pods each = ~366 pods + ~12 system).

**Verify capacity before starting:**

```bash
kubectl get node -o jsonpath='{.items[0].status.allocatable.pods}'   # should be 600
kubectl get pods --all-namespaces --no-headers | wc -l               # current pod count
```

### Option B: minikube (single-node, requires reconfiguration)

The default minikube Flannel setup assigns a `/24` subnet to the single node (254 usable IPs).
Six parallel 60-node scenarios need ~378 pods — this exceeds the default limit and will leave
namespaces stuck in `ContainerCreating` with:
```
plugin type="flannel" failed (add): failed to allocate for range 0: no IP addresses available
```

**Fix: delete and restart minikube with a larger per-node subnet:**

```bash
minikube delete

minikube start \
  --driver=docker \
  --cpus=no-limit \
  --memory=no-limit \
  --extra-config=kubelet.maxPods=1800 \
  --pod-network-cidr=10.244.0.0/16 \
  --extra-config=controller-manager.node-cidr-mask-size=20 \
  --extra-config=kubelet.cgroup-driver=cgroupfs \
  --cni=flannel
```

Key flags:
- `--pod-network-cidr=10.244.0.0/16` — global pool for the cluster
- `--extra-config=controller-manager.node-cidr-mask-size=20` — gives the single node a `/20`
  subnet (4094 usable IPs) instead of the default `/24` (254 IPs)
- `--max-pods=1800` — raises the per-node pod limit from the default 110
- `--extra-config=kubelet.cgroup-driver=cgroupfs` — prevents systemd D-Bus overload when
  creating 300+ pods simultaneously (avoids `operation timeout: context deadline exceeded`)

**Verify after restart:**

```bash
kubectl get node minikube -o jsonpath='{.spec.podCIDR}'     # should be 10.244.0.0/20
kubectl get node minikube -o jsonpath='{.status.allocatable.pods}'  # should be 1800
```

**Note on parallel limit with minikube:** Even with the above fix, minikube is a single-node
cluster sharing one machine's RAM. Monitor actual memory usage — 6 × 60-node scenarios
consume roughly 15–20 GiB RAM. If your machine has less, reduce to 3–4 parallel namespaces.

---

## Required warnet Patches

Apply to `../warnet/src/warnet/control.py` before running (idempotent — safe to re-apply):

**Patch 1 — include `lib/` and `config/` in scenario archive** (prevents `ModuleNotFoundError`):

```bash
grep -n '"lib/"' ../warnet/src/warnet/control.py || echo "PATCH NEEDED"
```

**Patch 2 — increase `wait_for_init` timeout from 300s to 600s** (prevents silent archive failure
under heavy cluster load where pod sandbox creation takes >300s):

```bash
grep -n "wait_for_init" ../warnet/src/warnet/control.py
# Should show: wait_for_init(name, namespace=namespace, timeout=600)
```

See `docs/warnet_control_patch.diff` for the full diff.

---

## Namespace Setup

Create namespaces before launching. Namespaces must exist before `warnet deploy` is called.

**Server 1:**

```bash
for i in $(seq 0 5); do kubectl create namespace fp3-$i; done
```

**Server 2:**

```bash
for i in $(seq 6 11); do kubectl create namespace fp3-$i; done
```

---

## Monitoring

```bash
# Watch all fp3 pods
kubectl get pods --all-namespaces | grep fp3

# Live pod status across all namespaces
watch -n 30 'kubectl get pods --all-namespaces | grep fp3 | awk "{print \$1, \$4}" | sort | uniq -c'

# Check scenario progress for a namespace
cat lhs_2016_full_phase3/results_server1/ns-0/sweep_progress.json | python3 -m json.tool

# Quick progress overview across all namespaces
for f in lhs_2016_full_phase3/results_server*/ns-*/sweep_progress.json; do
  echo "=== $f ==="
  python3 -c "import json; p=json.load(open('$f')); print(f'  completed={p[\"completed\"]} failed={p[\"failed\"]} current={p[\"current\"]}')"
done 2>/dev/null
```

---

## Collect Results

After both servers complete, rsync results to dev machine:

```bash
rsync -av server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_full_phase3/results_server1/ \
    tools/sweep/lhs_2016_full_phase3/results/

rsync -av server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_full_phase3/results_server2/ \
    tools/sweep/lhs_2016_full_phase3/results/

# Run analysis
python tools/sweep/4_analyze_results.py \
    --results-dir tools/sweep/lhs_2016_full_phase3/results \
    --output-dir tools/sweep/lhs_2016_full_phase3/results/analysis

# Add to database
python tools/sweep/5_build_database.py

# Re-fit boundary with expanded full-network dataset
python tools/discovery/fit_boundary.py --regime 2016 --output-dir tools/discovery/output/2016_phase3
```

---

## Server 1 Commands (sweep_0000–sweep_0149)

Start each in its own terminal or tmux pane. Stagger by ~2 minutes between starts to avoid
simultaneous `network_metadata.yaml` injection on the first scenario of each namespace.

All commands run from `~/bitcoin/warnetScenarioDiscovery/`.

### Namespace fp3-0 — sweep_0000 to sweep_0024

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server1/ns-0 \
    --namespace fp3-0 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0000 sweep_0001 sweep_0002 sweep_0003 sweep_0004 sweep_0005 sweep_0006 sweep_0007 sweep_0008 sweep_0009 sweep_0010 sweep_0011 sweep_0012 sweep_0013 sweep_0014 sweep_0015 sweep_0016 sweep_0017 sweep_0018 sweep_0019 sweep_0020 sweep_0021 sweep_0022 sweep_0023 sweep_0024
```

### Namespace fp3-1 — sweep_0025 to sweep_0049

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server1/ns-1 \
    --namespace fp3-1 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0025 sweep_0026 sweep_0027 sweep_0028 sweep_0029 sweep_0030 sweep_0031 sweep_0032 sweep_0033 sweep_0034 sweep_0035 sweep_0036 sweep_0037 sweep_0038 sweep_0039 sweep_0040 sweep_0041 sweep_0042 sweep_0043 sweep_0044 sweep_0045 sweep_0046 sweep_0047 sweep_0048 sweep_0049
```

### Namespace fp3-2 — sweep_0050 to sweep_0074

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server1/ns-2 \
    --namespace fp3-2 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0050 sweep_0051 sweep_0052 sweep_0053 sweep_0054 sweep_0055 sweep_0056 sweep_0057 sweep_0058 sweep_0059 sweep_0060 sweep_0061 sweep_0062 sweep_0063 sweep_0064 sweep_0065 sweep_0066 sweep_0067 sweep_0068 sweep_0069 sweep_0070 sweep_0071 sweep_0072 sweep_0073 sweep_0074
```

### Namespace fp3-3 — sweep_0075 to sweep_0099

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server1/ns-3 \
    --namespace fp3-3 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0075 sweep_0076 sweep_0077 sweep_0078 sweep_0079 sweep_0080 sweep_0081 sweep_0082 sweep_0083 sweep_0084 sweep_0085 sweep_0086 sweep_0087 sweep_0088 sweep_0089 sweep_0090 sweep_0091 sweep_0092 sweep_0093 sweep_0094 sweep_0095 sweep_0096 sweep_0097 sweep_0098 sweep_0099
```

### Namespace fp3-4 — sweep_0100 to sweep_0124

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server1/ns-4 \
    --namespace fp3-4 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0100 sweep_0101 sweep_0102 sweep_0103 sweep_0104 sweep_0105 sweep_0106 sweep_0107 sweep_0108 sweep_0109 sweep_0110 sweep_0111 sweep_0112 sweep_0113 sweep_0114 sweep_0115 sweep_0116 sweep_0117 sweep_0118 sweep_0119 sweep_0120 sweep_0121 sweep_0122 sweep_0123 sweep_0124
```

### Namespace fp3-5 — sweep_0125 to sweep_0149

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server1/ns-5 \
    --namespace fp3-5 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0125 sweep_0126 sweep_0127 sweep_0128 sweep_0129 sweep_0130 sweep_0131 sweep_0132 sweep_0133 sweep_0134 sweep_0135 sweep_0136 sweep_0137 sweep_0138 sweep_0139 sweep_0140 sweep_0141 sweep_0142 sweep_0143 sweep_0144 sweep_0145 sweep_0146 sweep_0147 sweep_0148 sweep_0149
```

---

## Server 2 Commands (sweep_0150–sweep_0299)

### Namespace fp3-6 — sweep_0150 to sweep_0174

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server2/ns-6 \
    --namespace fp3-6 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0150 sweep_0151 sweep_0152 sweep_0153 sweep_0154 sweep_0155 sweep_0156 sweep_0157 sweep_0158 sweep_0159 sweep_0160 sweep_0161 sweep_0162 sweep_0163 sweep_0164 sweep_0165 sweep_0166 sweep_0167 sweep_0168 sweep_0169 sweep_0170 sweep_0171 sweep_0172 sweep_0173 sweep_0174
```

### Namespace fp3-7 — sweep_0175 to sweep_0199

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server2/ns-7 \
    --namespace fp3-7 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0175 sweep_0176 sweep_0177 sweep_0178 sweep_0179 sweep_0180 sweep_0181 sweep_0182 sweep_0183 sweep_0184 sweep_0185 sweep_0186 sweep_0187 sweep_0188 sweep_0189 sweep_0190 sweep_0191 sweep_0192 sweep_0193 sweep_0194 sweep_0195 sweep_0196 sweep_0197 sweep_0198 sweep_0199
```

### Namespace fp3-8 — sweep_0200 to sweep_0224

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server2/ns-8 \
    --namespace fp3-8 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0200 sweep_0201 sweep_0202 sweep_0203 sweep_0204 sweep_0205 sweep_0206 sweep_0207 sweep_0208 sweep_0209 sweep_0210 sweep_0211 sweep_0212 sweep_0213 sweep_0214 sweep_0215 sweep_0216 sweep_0217 sweep_0218 sweep_0219 sweep_0220 sweep_0221 sweep_0222 sweep_0223 sweep_0224
```

### Namespace fp3-9 — sweep_0225 to sweep_0249

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server2/ns-9 \
    --namespace fp3-9 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0225 sweep_0226 sweep_0227 sweep_0228 sweep_0229 sweep_0230 sweep_0231 sweep_0232 sweep_0233 sweep_0234 sweep_0235 sweep_0236 sweep_0237 sweep_0238 sweep_0239 sweep_0240 sweep_0241 sweep_0242 sweep_0243 sweep_0244 sweep_0245 sweep_0246 sweep_0247 sweep_0248 sweep_0249
```

### Namespace fp3-10 — sweep_0250 to sweep_0274

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server2/ns-10 \
    --namespace fp3-10 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0250 sweep_0251 sweep_0252 sweep_0253 sweep_0254 sweep_0255 sweep_0256 sweep_0257 sweep_0258 sweep_0259 sweep_0260 sweep_0261 sweep_0262 sweep_0263 sweep_0264 sweep_0265 sweep_0266 sweep_0267 sweep_0268 sweep_0269 sweep_0270 sweep_0271 sweep_0272 sweep_0273 sweep_0274
```

### Namespace fp3-11 — sweep_0275 to sweep_0299

```bash
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/lhs_2016_full_phase3/build_manifest.json \
    --results-dir tools/sweep/lhs_2016_full_phase3/results_server2/ns-11 \
    --namespace fp3-11 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0275 sweep_0276 sweep_0277 sweep_0278 sweep_0279 sweep_0280 sweep_0281 sweep_0282 sweep_0283 sweep_0284 sweep_0285 sweep_0286 sweep_0287 sweep_0288 sweep_0289 sweep_0290 sweep_0291 sweep_0292 sweep_0293 sweep_0294 sweep_0295 sweep_0296 sweep_0297 sweep_0298 sweep_0299
```

---

## Notes

- **`--no-auto-restart`**: Required on k3s servers (minikube restart logic doesn't apply)
- **`--interval 2`**: 2 seconds per block, matching all prior 2016-block sweeps
- **`--duration 13000`**: consistent with `lhs_2016_phase3` and `lhs_2016_6param` for directly comparable results
- **`--startup-wait 60`**: gives pods 60s to settle before the scenario script starts; important for 60-node networks where pod startup is slower than lite
- **Stagger starts**: Wait ~2 minutes between launching each namespace on the same server to avoid simultaneous writes to `scenarios/config/network_metadata.yaml` on the first scenario. The pool/economic config injection is lock-protected (`fcntl.flock`) but network metadata is not.
- **Resume**: Re-run the same command if a namespace worker stops mid-run — completed scenarios are skipped automatically.
- **Results location**: Each namespace writes to its own `results_server{N}/ns-{idx}/` directory to prevent cross-namespace collision.
- **Pod count**: Each 60-node scenario deploys ~61 pods. Six parallel namespaces = ~366 pods + ~12 system = ~378 total. Well within k3s `maxPods=600`. On minikube requires the `/20` subnet fix above.
