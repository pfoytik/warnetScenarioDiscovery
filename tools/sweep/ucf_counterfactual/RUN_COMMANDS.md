# ucf_counterfactual — Run Commands

30 scenarios, 6 namespaces (5 scenarios each), 1 server.
~18 hours wall-clock (2016-block retarget, duration=13000s).

**Purpose:** Counterfactual baseline — re-run every user_split value that
produced a v26 win in the user-weight sweeps, but with UCF=0.001 (negligible
user weight). Determines which of the 34 original v26 wins are user-caused
vs. PRIM-zone baseline effects.

---

## Create Namespaces

```bash
kubectl create namespace ns-0
kubectl create namespace ns-1
kubectl create namespace ns-2
kubectl create namespace ns-3
kubectl create namespace ns-4
kubectl create namespace ns-5
```

## Run (one terminal per namespace)

```bash
# ns-0 — sweep_0000–0004
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/ucf_counterfactual/build_manifest.json \
    --results-dir tools/sweep/ucf_counterfactual/results \
    --namespace ns-0 \
    --scenarios sweep_0000 sweep_0001 sweep_0002 sweep_0003 sweep_0004 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-1 — sweep_0005–0009
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/ucf_counterfactual/build_manifest.json \
    --results-dir tools/sweep/ucf_counterfactual/results \
    --namespace ns-1 \
    --scenarios sweep_0005 sweep_0006 sweep_0007 sweep_0008 sweep_0009 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-2 — sweep_0010–0014
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/ucf_counterfactual/build_manifest.json \
    --results-dir tools/sweep/ucf_counterfactual/results \
    --namespace ns-2 \
    --scenarios sweep_0010 sweep_0011 sweep_0012 sweep_0013 sweep_0014 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-3 — sweep_0015–0019
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/ucf_counterfactual/build_manifest.json \
    --results-dir tools/sweep/ucf_counterfactual/results \
    --namespace ns-3 \
    --scenarios sweep_0015 sweep_0016 sweep_0017 sweep_0018 sweep_0019 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-4 — sweep_0020–0024
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/ucf_counterfactual/build_manifest.json \
    --results-dir tools/sweep/ucf_counterfactual/results \
    --namespace ns-4 \
    --scenarios sweep_0020 sweep_0021 sweep_0022 sweep_0023 sweep_0024 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

```bash
# ns-5 — sweep_0025–0029
python tools/sweep/3_run_sweep.py \
    --input tools/sweep/ucf_counterfactual/build_manifest.json \
    --results-dir tools/sweep/ucf_counterfactual/results \
    --namespace ns-5 \
    --scenarios sweep_0025 sweep_0026 sweep_0027 sweep_0028 sweep_0029 \
    --retarget-interval 2016 \
    --duration 13000 \
    --interval 2
```

---

## Collect & Analyze

```bash
# If running on a remote server, rsync first:
rsync -av server1:~/bitcoin/warnetScenarioDiscovery/tools/sweep/ucf_counterfactual/results/ \
    tools/sweep/ucf_counterfactual/results/

# Analyze
python tools/sweep/4_analyze_results.py \
    --input tools/sweep/ucf_counterfactual/results \
    --manifest tools/sweep/ucf_counterfactual/build_manifest.json
```

---

## Cross-Reference Analysis (after collection)

After analysis completes, add `ucf_counterfactual` to `5_build_database.py`
`SWEEP_METADATA` and rebuild the DB, then run the comparison:

```bash
python tools/discovery/summarize_user_weight.py \
    --db tools/sweep/sweep_results.db \
    --output-dir tools/discovery/output/user_weight
```

The summary script will cross-reference counterfactual results against the
34 original v26 wins to produce a causal classification table:

| Original UCF | user_split | Counterfactual (UCF=0.001) | Classification |
|---|---|---|---|
| 0.531 | 0.601 | v27 | user-caused |
| 0.010 | 0.500 | v26 | PRIM baseline |
| ... | ... | ... | ... |

---

## Scenario → user_split Mapping

| scenario_id | user_split | original v26-win source |
|-------------|------------|------------------------|
| sweep_0000  | 0.2608     | lhs sweep_0052 (ucf=0.499) |
| sweep_0001  | 0.2881     | lhs sweep_0003 (ucf=0.221) |
| sweep_0002  | 0.2975     | lhs sweep_0058 (ucf=0.376) |
| sweep_0003  | 0.3000     | grid (ucf=0.10, 0.35, 0.65) |
| sweep_0004  | 0.3163     | lhs sweep_0043 (ucf=0.548, collapse) |
| sweep_0005  | 0.3213     | lhs sweep_0041 (ucf=0.416) |
| sweep_0006  | 0.3401     | lhs sweep_0034 (ucf=0.319) |
| sweep_0007  | 0.3458     | lhs sweep_0018 (ucf=0.692, collapse) |
| sweep_0008  | 0.3717     | lhs sweep_0022 (ucf=0.599) |
| sweep_0009  | 0.3940     | lhs sweep_0017 (ucf=0.483) |
| sweep_0010  | 0.4000     | grid sweep_0021 (ucf=0.50) |
| sweep_0011  | 0.4030     | lhs sweep_0033 (ucf=0.518) |
| sweep_0012  | 0.4047     | lhs sweep_0027 (ucf=0.226) |
| sweep_0013  | 0.4101     | lhs sweep_0029 (ucf=0.628) |
| sweep_0014  | 0.4226     | lhs sweep_0028 (ucf=0.637, collapse) |
| sweep_0015  | 0.4242     | lhs sweep_0037 (ucf=0.353) |
| sweep_0016  | 0.4408     | lhs sweep_0054 (ucf=0.407) |
| sweep_0017  | 0.4554     | lhs sweep_0016 (ucf=0.147) |
| sweep_0018  | 0.4628     | lhs sweep_0012 (ucf=0.575) |
| sweep_0019  | 0.4689     | lhs sweep_0047 (ucf=0.591) |
| sweep_0020  | 0.4828     | lhs sweep_0049 (ucf=0.189) |
| sweep_0021  | 0.4887     | lhs sweep_0045 (ucf=0.426) |
| sweep_0022  | 0.5000     | grid (ucf=0.01, 0.35, 0.65) |
| sweep_0023  | 0.5094     | lhs sweep_0053 (ucf=0.680, collapse) |
| sweep_0024  | 0.5142     | lhs sweep_0038 (ucf=0.193) |
| sweep_0025  | 0.5217     | lhs sweep_0040 (ucf=0.452) |
| sweep_0026  | 0.5299     | lhs sweep_0057 (ucf=0.611) |
| sweep_0027  | 0.5407     | lhs sweep_0055 (ucf=0.373) |
| sweep_0028  | 0.5482     | lhs sweep_0048 (ucf=0.171) |
| sweep_0029  | 0.6012     | lhs sweep_0013 (ucf=0.531) — safe-zone falsification |
