# Phase 3 LHS — Run Commands

**300 scenarios targeting the PRIM uncertainty zone (2016-block regime)**
**Source bounds:** `tools/discovery/output/2016/uncertainty_bounds.yaml`

Run each command below in a **separate terminal** (or tmux pane) on the appropriate server.
All commands run from `tools/sweep/` directory.

## Setup (both servers)

```bash
# Clone/sync repo to each server, then:
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep

# Create namespaces before starting
kubectl create namespace phase3-0
kubectl create namespace phase3-1
kubectl create namespace phase3-2
kubectl create namespace phase3-3
kubectl create namespace phase3-4
kubectl create namespace phase3-5
# (Server 2 only)
kubectl create namespace phase3-6
kubectl create namespace phase3-7
kubectl create namespace phase3-8
kubectl create namespace phase3-9
kubectl create namespace phase3-10
kubectl create namespace phase3-11
```

## Monitoring

```bash
# Watch all phase3 pods
kubectl get pods --all-namespaces | grep phase3

# Check progress per namespace
cat lhs_2016_phase3/results_server1/ns-0/sweep_progress.json | python3 -m json.tool

# Watch all progress files at once
watch -n 120 'for f in lhs_2016_phase3/results_server*/ns-*/sweep_progress.json; do echo "=== $f ==="; python3 -c "import json; p=json.load(open(\"$f\")); print(f\"  completed={p[\"completed\"]} failed={p[\"failed\"]} current={p[\"current\"]}\")"; done 2>/dev/null'
```

## Collect Results

After both servers complete, rsync results to dev machine:

```bash
# Run on dev machine
rsync -av server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_phase3/results_server1/ \
    tools/sweep/lhs_2016_phase3/results/

rsync -av server2:~/bitcoin/warnetScenarioDiscovery/tools/sweep/lhs_2016_phase3/results_server2/ \
    tools/sweep/lhs_2016_phase3/results/

# Add to database
cd tools/sweep
python3 5_build_database.py

# Re-run boundary analysis with expanded dataset
cd tools/discovery
python3 fit_boundary.py --regime 2016 --output-dir output/2016_phase3
```

---

## Server 1 Commands (sweep_0000–sweep_0149)

Start each in its own terminal. Stagger by ~2 minutes between starts to avoid simultaneous config injection on the first scenario.

### Namespace phase3-0 — sweep_0000 to sweep_0024

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server1/ns-0 \
    --namespace phase3-0 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0000 sweep_0001 sweep_0002 sweep_0003 sweep_0004 sweep_0005 sweep_0006 sweep_0007 sweep_0008 sweep_0009 sweep_0010 sweep_0011 sweep_0012 sweep_0013 sweep_0014 sweep_0015 sweep_0016 sweep_0017 sweep_0018 sweep_0019 sweep_0020 sweep_0021 sweep_0022 sweep_0023 sweep_0024
```

### Namespace phase3-1 — sweep_0025 to sweep_0049

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server1/ns-1 \
    --namespace phase3-1 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0025 sweep_0026 sweep_0027 sweep_0028 sweep_0029 sweep_0030 sweep_0031 sweep_0032 sweep_0033 sweep_0034 sweep_0035 sweep_0036 sweep_0037 sweep_0038 sweep_0039 sweep_0040 sweep_0041 sweep_0042 sweep_0043 sweep_0044 sweep_0045 sweep_0046 sweep_0047 sweep_0048 sweep_0049
```

### Namespace phase3-2 — sweep_0050 to sweep_0074

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server1/ns-2 \
    --namespace phase3-2 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0050 sweep_0051 sweep_0052 sweep_0053 sweep_0054 sweep_0055 sweep_0056 sweep_0057 sweep_0058 sweep_0059 sweep_0060 sweep_0061 sweep_0062 sweep_0063 sweep_0064 sweep_0065 sweep_0066 sweep_0067 sweep_0068 sweep_0069 sweep_0070 sweep_0071 sweep_0072 sweep_0073 sweep_0074
```

### Namespace phase3-3 — sweep_0075 to sweep_0099

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server1/ns-3 \
    --namespace phase3-3 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0075 sweep_0076 sweep_0077 sweep_0078 sweep_0079 sweep_0080 sweep_0081 sweep_0082 sweep_0083 sweep_0084 sweep_0085 sweep_0086 sweep_0087 sweep_0088 sweep_0089 sweep_0090 sweep_0091 sweep_0092 sweep_0093 sweep_0094 sweep_0095 sweep_0096 sweep_0097 sweep_0098 sweep_0099
```

### Namespace phase3-4 — sweep_0100 to sweep_0124

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server1/ns-4 \
    --namespace phase3-4 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0100 sweep_0101 sweep_0102 sweep_0103 sweep_0104 sweep_0105 sweep_0106 sweep_0107 sweep_0108 sweep_0109 sweep_0110 sweep_0111 sweep_0112 sweep_0113 sweep_0114 sweep_0115 sweep_0116 sweep_0117 sweep_0118 sweep_0119 sweep_0120 sweep_0121 sweep_0122 sweep_0123 sweep_0124
```

### Namespace phase3-5 — sweep_0125 to sweep_0149

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server1/ns-5 \
    --namespace phase3-5 \
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

### Namespace phase3-6 — sweep_0150 to sweep_0174

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server2/ns-6 \
    --namespace phase3-6 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0150 sweep_0151 sweep_0152 sweep_0153 sweep_0154 sweep_0155 sweep_0156 sweep_0157 sweep_0158 sweep_0159 sweep_0160 sweep_0161 sweep_0162 sweep_0163 sweep_0164 sweep_0165 sweep_0166 sweep_0167 sweep_0168 sweep_0169 sweep_0170 sweep_0171 sweep_0172 sweep_0173 sweep_0174
```

### Namespace phase3-7 — sweep_0175 to sweep_0199

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server2/ns-7 \
    --namespace phase3-7 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0175 sweep_0176 sweep_0177 sweep_0178 sweep_0179 sweep_0180 sweep_0181 sweep_0182 sweep_0183 sweep_0184 sweep_0185 sweep_0186 sweep_0187 sweep_0188 sweep_0189 sweep_0190 sweep_0191 sweep_0192 sweep_0193 sweep_0194 sweep_0195 sweep_0196 sweep_0197 sweep_0198 sweep_0199
```

### Namespace phase3-8 — sweep_0200 to sweep_0224

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server2/ns-8 \
    --namespace phase3-8 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0200 sweep_0201 sweep_0202 sweep_0203 sweep_0204 sweep_0205 sweep_0206 sweep_0207 sweep_0208 sweep_0209 sweep_0210 sweep_0211 sweep_0212 sweep_0213 sweep_0214 sweep_0215 sweep_0216 sweep_0217 sweep_0218 sweep_0219 sweep_0220 sweep_0221 sweep_0222 sweep_0223 sweep_0224
```

### Namespace phase3-9 — sweep_0225 to sweep_0249

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server2/ns-9 \
    --namespace phase3-9 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0225 sweep_0226 sweep_0227 sweep_0228 sweep_0229 sweep_0230 sweep_0231 sweep_0232 sweep_0233 sweep_0234 sweep_0235 sweep_0236 sweep_0237 sweep_0238 sweep_0239 sweep_0240 sweep_0241 sweep_0242 sweep_0243 sweep_0244 sweep_0245 sweep_0246 sweep_0247 sweep_0248 sweep_0249
```

### Namespace phase3-10 — sweep_0250 to sweep_0274

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server2/ns-10 \
    --namespace phase3-10 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0250 sweep_0251 sweep_0252 sweep_0253 sweep_0254 sweep_0255 sweep_0256 sweep_0257 sweep_0258 sweep_0259 sweep_0260 sweep_0261 sweep_0262 sweep_0263 sweep_0264 sweep_0265 sweep_0266 sweep_0267 sweep_0268 sweep_0269 sweep_0270 sweep_0271 sweep_0272 sweep_0273 sweep_0274
```

### Namespace phase3-11 — sweep_0275 to sweep_0299

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input lhs_2016_phase3/build_manifest.json \
    --results-dir lhs_2016_phase3/results_server2/ns-11 \
    --namespace phase3-11 \
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
- **`--duration 13000`**: 3+ retarget cycles, matching lhs_2016_6param for directly comparable results
- **Stagger starts**: If launching multiple namespaces on the same server simultaneously, wait ~2 minutes between each start. This avoids two workers simultaneously writing `scenarios/config/network_metadata.yaml` before their first scenario deploys (the pools/economic config injection is already lock-protected; network metadata is not).
- **Resume**: If a namespace worker stops partway through, re-run the same command — it will skip already-completed scenarios automatically.
- **Results location**: Each namespace writes to its own `results_server{N}/ns-{idx}/` directory to avoid any cross-namespace collision.
