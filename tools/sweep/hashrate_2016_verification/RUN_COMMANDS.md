# hashrate_2016_verification — Run Commands

**18 scenarios: 6 hashrate levels × 3 economic levels on full 60-node network**
**Purpose:** Verify hashrate_split non-causality at 2016-block retarget, near the committed_split transition boundary

All commands run from `tools/sweep/` directory.

---

## Layout: 6 namespaces × 3 scenarios each

Each namespace runs one hashrate level across all three economic levels sequentially.

| Namespace | Scenarios | hashrate_split | economic_split values |
|-----------|-----------|:--------------:|----------------------|
| hashrate2016-0 | sweep_0000–0002 | 0.15 (v26 has 100% initial hashrate) | 0.50, 0.60, 0.70 |
| hashrate2016-1 | sweep_0003–0005 | 0.25 (v26 has 65% initial hashrate) | 0.50, 0.60, 0.70 |
| hashrate2016-2 | sweep_0006–0008 | 0.35 | 0.50, 0.60, 0.70 |
| hashrate2016-3 | sweep_0009–0011 | 0.45 | 0.50, 0.60, 0.70 |
| hashrate2016-4 | sweep_0012–0014 | 0.55 | 0.50, 0.60, 0.70 |
| hashrate2016-5 | sweep_0015–0017 | 0.65 (near parity) | 0.50, 0.60, 0.70 |

**Wall-clock:** ~4.5h (3 scenarios × ~90 min each, all 6 namespaces run in parallel)

---

## Setup

```bash
# Create namespaces (run once before starting)
kubectl create namespace hashrate2016-0
kubectl create namespace hashrate2016-1
kubectl create namespace hashrate2016-2
kubectl create namespace hashrate2016-3
kubectl create namespace hashrate2016-4
kubectl create namespace hashrate2016-5

# Clear stale results from the previous (lite-network) run
rm -rf hashrate_2016_verification/results/sweep_*/
```

---

## Run Commands

Start each in its own terminal or tmux pane. Stagger by ~2 minutes between starts.

### Namespace hashrate2016-0 — sweep_0000–0002 (hashrate_split=0.15)

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input hashrate_2016_verification/build_manifest.json \
    --results-dir hashrate_2016_verification/results/ns-0 \
    --namespace hashrate2016-0 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0000 sweep_0001 sweep_0002
```

### Namespace hashrate2016-1 — sweep_0003–0005 (hashrate_split=0.25)

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input hashrate_2016_verification/build_manifest.json \
    --results-dir hashrate_2016_verification/results/ns-1 \
    --namespace hashrate2016-1 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0003 sweep_0004 sweep_0005
```

### Namespace hashrate2016-2 — sweep_0006–0008 (hashrate_split=0.35)

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input hashrate_2016_verification/build_manifest.json \
    --results-dir hashrate_2016_verification/results/ns-2 \
    --namespace hashrate2016-2 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0006 sweep_0007 sweep_0008
```

### Namespace hashrate2016-3 — sweep_0009–0011 (hashrate_split=0.45)

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input hashrate_2016_verification/build_manifest.json \
    --results-dir hashrate_2016_verification/results/ns-3 \
    --namespace hashrate2016-3 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0009 sweep_0010 sweep_0011
```

### Namespace hashrate2016-4 — sweep_0012–0014 (hashrate_split=0.55)

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input hashrate_2016_verification/build_manifest.json \
    --results-dir hashrate_2016_verification/results/ns-4 \
    --namespace hashrate2016-4 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0012 sweep_0013 sweep_0014
```

### Namespace hashrate2016-5 — sweep_0015–0017 (hashrate_split=0.65)

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep
python3 3_run_sweep.py \
    --input hashrate_2016_verification/build_manifest.json \
    --results-dir hashrate_2016_verification/results/ns-5 \
    --namespace hashrate2016-5 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2 \
    --startup-wait 60 \
    --cooldown 45 \
    --no-auto-restart \
    --scenarios sweep_0015 sweep_0016 sweep_0017
```

---

## Monitoring

```bash
# Watch all hashrate2016 pods
kubectl get pods --all-namespaces | grep hashrate2016

# Check progress per namespace
for ns in 0 1 2 3 4 5; do
    f="hashrate_2016_verification/results/ns-${ns}/sweep_progress.json"
    [ -f "$f" ] && echo "=== ns-${ns} ===" && python3 -c "
import json; p=json.load(open('$f'))
print(f'  completed={p[\"completed\"]} failed={p[\"failed\"]} current={p.get(\"current\",\"?\")}')"
done
```

---

## Collect and Analyze

Results land in `hashrate_2016_verification/results/ns-{0..5}/`. Merge into a flat results dir after all namespaces complete:

```bash
cd ~/bitcoin/warnetScenarioDiscovery/tools/sweep

# Symlink all sweep dirs into a flat results/ view for 4_analyze_results.py
mkdir -p hashrate_2016_verification/results_flat
for ns in 0 1 2 3 4 5; do
    for d in hashrate_2016_verification/results/ns-${ns}/sweep_*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        [ -e "hashrate_2016_verification/results_flat/$name" ] || \
            ln -s "$(pwd)/$d" "hashrate_2016_verification/results_flat/$name"
    done
done

python3 4_analyze_results.py \
    --input hashrate_2016_verification/results_flat \
    --manifest hashrate_2016_verification/build_manifest.json \
    --export both
```

**What to look for in results:** Each column (economic_split level) should be uniform across all 6 hashrate rows if hashrate is non-causal. Any column that flips outcome across hashrate levels is evidence that initial hashrate advantage matters at 2016-block retarget near the committed_split boundary (~0.35).

---

## Notes

- **`--no-auto-restart`**: Disables minikube restart logic (not applicable on this server)
- **`--interval 2`**: 2 seconds/block, consistent with all prior 2016-block sweeps
- **`--duration 13000`**: 3+ retarget cycles at 2016-block; full cascade window
- **Stagger starts**: Wait ~2 min between launching each namespace to avoid simultaneous `network_metadata.yaml` writes on first scenario
- **Resume**: Re-running the same command skips already-completed scenarios automatically
- **Results collision**: Each namespace writes to its own `results/ns-{N}/` directory — no cross-namespace collision possible
