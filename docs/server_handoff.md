# Server Handoff Briefing
**Date:** 2026-03-16
**Purpose:** Context for Claude instance on large server (80 cores, 250GB RAM)

---

## Project Overview

Bitcoin fork dynamics simulation using warnet (Kubernetes). Parameter sweeps over a
simulated Bitcoin network map conditions under which a soft fork (v27) wins vs the
incumbent chain (v26). Results feed a research paper.

**Repo:** `warnetScenarioDiscovery`
**Sibling repo:** `../warnet/` must exist (symlinks in repo root point there)

---

## Sweep Infrastructure

```bash
# Step 1: generate scenarios (ALREADY DONE for both sweeps below — skip)
python tools/sweep/1_generate_targeted.py --spec tools/sweep/specs/<name>.yaml

# Step 2: build configs (run this on the server)
python tools/sweep/2_build_configs.py \
  --input tools/sweep/<name>/scenarios.json \
  --output-dir tools/sweep/<name> \
  --base-network networks/realistic-economy-v2/network.yaml

# Step 3: run sweep
python tools/sweep/3_run_sweep.py \
  --input tools/sweep/<name>/build_manifest.json \
  --namespace <ns> --scenarios <ids> \
  --results-dir <name>/results \
  --duration 13000 --retarget-interval <144|2016> --interval 2

# Step 4: analyze results
python tools/sweep/4_analyze_results.py \
  --input <name>/results \
  --manifest tools/sweep/<name>/build_manifest.json
```

**Parallelization:** use `--scenarios sweep_000X` + `--namespace <ns>` to pin one
scenario per namespace. Create namespaces first: `kubectl create namespace <ns>`.
Results land in the **repo root** (e.g. `econ_committed_2016_grid/results/`), not
inside `tools/sweep/`.

---

## Sweep 1: `econ_committed_2016_grid` — HIGHEST PRIORITY

**45 scenarios** (5 econ × 9 committed_split), full 60-node network, 2016-block
retarget, baseline oracle. Fills §4.5 Table 6 — the full 2D decision boundary.

### Scenario layout

```
economic_split \ pool_committed_split:
         0.20  0.30  0.38  0.43  0.47  0.52  0.58  0.65  0.75
econ=0.35: 0000  0001  0002  0003  0004  0005  0006  0007  0008
econ=0.50: 0009  0010  0011  0012  0013  0014  0015  0016  0017
econ=0.60: 0018  0019  0020  0021  0022  0023  0024  0025  0026
econ=0.70: 0027  0028  0029  0030  0031  0032  0033  0034  0035
econ=0.82: 0036  0037  0038  0039  0040  0041  0042  0043  0044
```

### Build

```bash
python tools/sweep/2_build_configs.py \
  --input tools/sweep/econ_committed_2016_grid/scenarios.json \
  --output-dir tools/sweep/econ_committed_2016_grid \
  --base-network networks/realistic-economy-v2/network.yaml
```

### Run (9 namespaces × 5 scenarios, one per committed_split column, ~18h wall-clock)

```bash
for ns in grid2016-c0 grid2016-c1 grid2016-c2 grid2016-c3 grid2016-c4 \
          grid2016-c5 grid2016-c6 grid2016-c7 grid2016-c8; do
  kubectl create namespace $ns
done

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0000 sweep_0009 sweep_0018 sweep_0027 sweep_0036 \
  --namespace grid2016-c0 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0001 sweep_0010 sweep_0019 sweep_0028 sweep_0037 \
  --namespace grid2016-c1 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0002 sweep_0011 sweep_0020 sweep_0029 sweep_0038 \
  --namespace grid2016-c2 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0003 sweep_0012 sweep_0021 sweep_0030 sweep_0039 \
  --namespace grid2016-c3 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0004 sweep_0013 sweep_0022 sweep_0031 sweep_0040 \
  --namespace grid2016-c4 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0005 sweep_0014 sweep_0023 sweep_0032 sweep_0041 \
  --namespace grid2016-c5 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0006 sweep_0015 sweep_0024 sweep_0033 sweep_0042 \
  --namespace grid2016-c6 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0007 sweep_0016 sweep_0025 sweep_0034 sweep_0043 \
  --namespace grid2016-c7 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &

python tools/sweep/3_run_sweep.py --input tools/sweep/econ_committed_2016_grid/build_manifest.json \
  --scenarios sweep_0008 sweep_0017 sweep_0026 sweep_0035 sweep_0044 \
  --namespace grid2016-c8 --results-dir econ_committed_2016_grid/results \
  --duration 13000 --retarget-interval 2016 --interval 2 &
```

---

## Sweep 2: `targeted_sweep7_esp` — HIGH PRIORITY

**9 scenarios**, full 60-node network. Economic Self-Sustaining Point (ESP) sweep —
maps the minimum economic majority at which v27 becomes self-reinforcing. Run at
**both** 144-block and 2016-block retarget.

`econ_split` grid: [0.28, 0.35, 0.45, 0.55, 0.60, 0.65, 0.70, 0.78, 0.85]
`pool_committed_split` fixed at 0.214 (Foundry flip-point), `hashrate_split` = 0.25

### Build

```bash
python tools/sweep/2_build_configs.py \
  --input tools/sweep/targeted_sweep7_esp/scenarios.json \
  --output-dir tools/sweep/targeted_sweep7_esp \
  --base-network networks/realistic-economy-v2/network.yaml
```

### Run 144-block (~3.6h wall-clock)

```bash
for i in 0 1 2 3 4 5 6 7 8; do
  kubectl create namespace esp-144-$i
done

for i in 0 1 2 3 4 5 6 7 8; do
  python tools/sweep/3_run_sweep.py \
    --input tools/sweep/targeted_sweep7_esp/build_manifest.json \
    --scenarios sweep_000$i --namespace esp-144-$i \
    --results-dir targeted_sweep7_esp/results_144 \
    --duration 13000 --retarget-interval 144 --interval 2 &
done
```

### Run 2016-block (~3.6h wall-clock, can overlap with 144-block if namespaces allow)

```bash
for i in 0 1 2 3 4 5 6 7 8; do
  kubectl create namespace esp-2016-$i
done

for i in 0 1 2 3 4 5 6 7 8; do
  python tools/sweep/3_run_sweep.py \
    --input tools/sweep/targeted_sweep7_esp/build_manifest.json \
    --scenarios sweep_000$i --namespace esp-2016-$i \
    --results-dir targeted_sweep7_esp/results_2016 \
    --duration 13000 --retarget-interval 2016 --interval 2 &
done
```

---

## Key Context for Interpreting Results

**Economic node quantization:** The network has ~4 econ nodes with skewed custody
(56.7% / 43.3%). Node assignment is discrete — not a smooth variable:
- `econ_split < ~0.30` → 0 nodes on v27 → **v26 always wins**
- `econ_split ≥ ~0.30` → 1 node (56.7% custody) → v27 can win
- `econ_split ~0.82+` → 2 nodes (99.6%) → very fast cascade

**committed_split threshold:** ∈(0.20, 0.30) — below this v27 has insufficient
committed hashrate to accumulate 2016 blocks before v26 retargets. This threshold
is the same in both 144-block and 2016-block regimes.

**pool_committed_split semantics:**
`v27_pct = (1 - neutral_pct/100) * committed_split`
e.g. split=0.35, neutral=30%: v27=24.5%, v26=45.5%

**2016-block cascade timing (baseline oracle):**
- 1-node econ (56.7%): cascade_t ≈ 8426s, peak_gap ≈ 16%
- 2-node econ (99.6%): cascade_t ≈ 607s, peak_gap ≈ 47%
- Duration=13000s is calibrated to capture the full cascade with margin

**Econ switching threshold (validated params):**
`effective_threshold = 0.10 * (1 + 0.40 * 2.0) = 0.18` (18%)
Baseline oracle peak_gap ≈ 16% → below threshold → econ nodes never switch
Sigmoid oracle peak_gap ≈ 40% → above threshold → full econ switch possible

**Monitoring parallel runs:**
```bash
# Check pod status per namespace
for ns in grid2016-c0 grid2016-c1 grid2016-c2 grid2016-c3 grid2016-c4 \
          grid2016-c5 grid2016-c6 grid2016-c7 grid2016-c8; do
  pending=$(kubectl get pods -n $ns 2>/dev/null | grep Pending | wc -l)
  running=$(kubectl get pods -n $ns 2>/dev/null | grep Running | wc -l)
  echo "$ns: $running running, $pending pending"
done
```
