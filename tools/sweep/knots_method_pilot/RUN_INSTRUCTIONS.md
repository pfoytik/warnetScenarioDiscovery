# Knots Method Pilot: Run Instructions

Spec: `tools/sweep/specs/knots_method_pilot.yaml` (purpose, design, what to
compare). Run config: `tools/sweep/configs/knots_method_pilot_run.yaml`.

**6 scenarios × 4 methods = 24 runs**, 60-node full network, 13000s each.

| Scenario | violation_rate | legacy p (= 1 − vr) | seed |
|---|---|---|---|
| sweep_0000 | 0.20 | 0.80 | 101 |
| sweep_0001 | 0.20 | 0.80 | 102 |
| sweep_0002 | 0.50 | 0.50 | 101 |
| sweep_0003 | 0.50 | 0.50 | 102 |
| sweep_0004 | 1.00 | 0.00 | 101 |
| sweep_0005 | 1.00 | 0.00 | 102 |

Fixed values: E=0.55, C=0.30, hashrate_split=0.25, `fork_links=5` (real-fork
methods), `fork_heal_exit` off.

This directory (manifest, networks, pool and economic configs) was generated
with:
```bash
cd tools/sweep
python3 1_generate_targeted.py --spec specs/knots_method_pilot.yaml --output knots_method_pilot/scenarios.json
python3 2_build_configs.py --input knots_method_pilot/scenarios.json --output-dir knots_method_pilot \
    --base-network ../../networks/realistic-economy-v2/network.yaml
```
It is committed so both machines run identical inputs. Don't regenerate unless
the spec changes.

## Prerequisites (server)

1. `git pull` in `warnetScenarioDiscovery`.
2. Warnet patch applied (needed by `inplace`). In the warnet checkout, run
   `git apply --check` on `docs/warnet_changes.patch`, then `git apply` it.
   See `docs/warnet_changes_required.md`.
3. Images available to the cluster:
   - `bitcoin-knots:29.4-local` (realfork, inplace)
   - `bitcoindevproject/bitcoin:30.2` (realfork)
   - `bitcoindevproject/bitcoin:26.0` and `27.0` (legacy)
   - `alpine:latest` (inplace seed init container)

   On k3s, import a locally built image with
   `docker save bitcoin-knots:29.4-local | sudo k3s ctr images import -`.
4. Enough pod capacity: 60 tanks + 1 commander per runner (`max-pods=600`
   per `PARALLEL_SWEEPS.md`).

## Run (from the repo root, one runner per method, own namespace and results dir)

```bash
cd ~/bitcoin/warnetScenarioDiscovery   # repo root; the runner finds scenarios/ from here
M=tools/sweep/knots_method_pilot
CFG=tools/sweep/configs/knots_method_pilot_run.yaml

# 1. legacy (prior studies' method)
nohup python3 tools/sweep/3_run_sweep.py --input $M/build_manifest.json --scenario-config $CFG \
  --method legacy --namespace kmp-legacy --results-dir $M/results_legacy --no-auto-restart \
  > $M/runner_legacy.log 2>&1 &

# 2. real fork, oracles fed mined-block counts (isolates the fork mechanism)
nohup python3 tools/sweep/3_run_sweep.py --input $M/build_manifest.json --scenario-config $CFG \
  --method realfork --oracle-chain-source mined --namespace kmp-realfork-mined \
  --results-dir $M/results_realfork_mined --no-auto-restart > $M/runner_realfork_mined.log 2>&1 &

# 3. real fork, oracles read observed chain state
nohup python3 tools/sweep/3_run_sweep.py --input $M/build_manifest.json --scenario-config $CFG \
  --method realfork --namespace kmp-realfork \
  --results-dir $M/results_realfork --no-auto-restart > $M/runner_realfork.log 2>&1 &

# 4. real fork + in-place node switching
nohup python3 tools/sweep/3_run_sweep.py --input $M/build_manifest.json --scenario-config $CFG \
  --method inplace --namespace kmp-inplace \
  --results-dir $M/results_inplace --no-auto-restart > $M/runner_inplace.log 2>&1 &
```

Each runner runs its 6 scenarios one after another: about 6 × 3.6h ≈ 22h.
All 4 in parallel is 240 tank pods.

To finish sooner, split a real-fork method over 2 namespaces with
`--scenarios sweep_0000 sweep_0001 sweep_0002` and
`--scenarios sweep_0003 sweep_0004 sweep_0005`. That takes about 11h, but
double the pods.

**Do not split `legacy` across namespaces in one checkout.** It reads the
single shared `scenarios/config/network_metadata.yaml`, which each runner
overwrites before deploying. Two concurrent legacy runners in one checkout can
bundle each other's metadata. Real-fork methods get a file per scenario and
method (`network_metadata__<scenario>__<method>.yaml`), so they are safe in
parallel.

Dry run first (prints commands, touches nothing):
```bash
python3 tools/sweep/3_run_sweep.py --input $M/build_manifest.json --scenario-config $CFG \
  --method inplace --dry-run --results-dir /tmp/kmp_dry
```
Expect, per scenario:
`Converted network (inplace): 60 nodes, v27=19 v26=41, fork links 8 -> 5 (target 5), islands 2 -> 1, pool nodes realigned to pool config: [node-0001, node-0002, node-0003 → v27]`.

## Check early in each real-fork run

In `kubectl logs -n <ns> <commander-pod>`:
- `Loading network metadata from bundled config: network_metadata__sweep_XXXX__<method>.yaml` and `60 nodes`.
- Classification: `inplace` shows `v27 (RDTS enforced) nodes: 19`; `realfork` shows `v27 (Knots) nodes: 19`.
- `Metadata camps match live classification for all 60 nodes`.
- `[violations] ... funded anyone-can-spend source`, then `[violations] ... mined N violating tx(s)` as Core blocks arrive.
- `inplace` only: no `IN-PLACE SWITCH (initial ...)` at t=0 (pool nodes already start on their pools' forks), and later `IN-PLACE SWITCH (pool decision|economic decision ...)` lines with each node's downtime.

## Outputs

`$M/results_<method>/sweep_XXXX/results.json` (all methods), plus for the
real-fork methods `network_conversion.json` (achieved fork links, bridges,
realigned pool nodes).

Compare across methods per scenario:
- `fork_convergence`: winner, heal time;
- reorg count and depth; orphaned blocks per camp;
- hashrate, economic and price time series; first pool switch time.

Real-fork runs add `chain_state`, `violations`, `outcomes` (per-node won/lost)
and, for `inplace`, `inplace_switching`.

## Known issues found while preparing this pilot (pre-existing, legacy left unchanged)

1. **`hashrate_split` does not set pools' starting fork in base-network builds.**
   From a base network, `2_build_configs.py` takes each pool's `initial_fork`
   from the base network's tags. For `realistic-economy-v2` that is Foundry,
   MARA, Luxor and Ocean on v27, 38.1% of hashrate. The generated network's
   pool nodes are re-tagged by `hashrate_split` (only Foundry). The
   simulation follows the pool config, so full-network sweeps started at 38.1%
   v27 pool hashrate regardless of `hashrate_split`.
   - Here: every method uses the same pool config, so the starting hashrate
     is identical across methods.
   - The real-fork conversion moves MARA, Luxor and Ocean's nodes to v27 to
     match the pool config.
2. **Pool IDs.** Sweep pool configs use `pool-<name>` IDs, while the scenarios
   map nodes to pools by the stripped `<name>`. So pools were never matched to
   their own nodes, and blocks were mined by a random node of the pool's camp.
   - Aggregate block rates were unaffected.
   - Per-pool block attribution was.
   - Fixed in `knots_mesh_pilot.py` (it matches either form). This was
     needed for in-place pool switching.
   - `partition_miner_with_pools.py` is unchanged.
3. **Shared `network_metadata.yaml`** across concurrent legacy runners in one
   checkout (above). Worth checking whether earlier parallel legacy sweeps
   bundled the metadata they intended. Each result's log shows which
   economic/pool camps it loaded.
