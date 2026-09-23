# Running the Knots Mesh Fork Scenario

How to deploy and run `scenarios/knots_mesh_pilot.py`, in either of its two
modes, plus how to retrieve results and troubleshoot the environment issues
already hit once. Background/design: `docs/knots_mesh_fork_sweep_plan.md`.

## The two modes (read this first)

`knots_mesh_pilot.py` is a derived copy of `scenarios/partition_miner_with_pools.py`
— every old mechanism is still in the file, gated behind flags that default
to the *new* behavior. This means **the same file runs either experiment**:

| | Real fork method (default) | Manual network control (legacy) |
|---|---|---|
| What causes the split | Real Knots consensus code rejecting a real transaction | Scripted `submitblock` bridging + probabilistic acceptance |
| Node classification | `getnetworkinfo()['subversion']` (Knots vs Core) | Image-tag substring match (`27.` vs `26.`) |
| Network needed | `networks/knots-mesh-pilot/` (Knots + Core v30.2 images) | Any old-style network using real Core version tags, e.g. `networks/realistic-economy-v2/` unmodified |
| Key flags | defaults (nothing extra needed) | `--node-classification tag --enable-manual-repartition --enable-asymmetric-bridging --v26-acceptance-probability <0.0-1.0>` |

Use the same `--pool-scenario`/`--economic-scenario`/`--duration`/etc. for
both runs if you want the economic simulation to be comparable side by
side — only the fork-causing mechanism and network differ.

## Prerequisites

- `bitcoin-knots:29.4-local` image built — see `docs/building_knots_image.md`.
- `kubectl` and `helm` on `PATH` (installed to `~/.local/bin` in this
  environment; if missing elsewhere, install per each tool's docs — the
  installed `warnet` CLI shells out to both by literal name).
- `minikube` with **at least ~8GB memory** allocated. A years-old profile
  can be capped much lower (3.8GB was too small and caused apiserver
  TLS-handshake timeouts under 60 pods) — check with `docker stats minikube`;
  if it's maxed out, `minikube delete && minikube start --cpus=6 --memory=9000`
  (docker driver; this is a disposable dev cluster, safe to recreate).
- `warnet` CLI available (`/home/pfoytik/bitcoinTools/warnet/warnet/.venv/bin/warnet`
  in this environment — an editable install, so any patches to its source
  take effect immediately without reinstalling).

## One-time per-cluster setup

```bash
minikube image load bitcoin-knots:29.4-local
minikube image pull bitcoindevproject/bitcoin:30.2
kubectl create namespace knots-pilot
kubectl config set-context --current --namespace=knots-pilot
```

## Deploy the network

**Real fork method:**
```bash
cd /path/to/warnetScenarioDiscovery
warnet deploy networks/knots-mesh-pilot --namespace knots-pilot
```

**Manual network control (legacy comparison):**
```bash
warnet deploy networks/realistic-economy-v2 --namespace <some-other-namespace>
```
(use a separate namespace/cluster if running both at once, or tear down
and redeploy the same namespace between runs)

Wait for all pods ready:
```bash
until [ "$(kubectl get pods -n knots-pilot --no-headers | grep -Ec 'ContainerCreating|Pending')" -eq 0 ] \
   && [ "$(kubectl get pods -n knots-pilot --no-headers | wc -l)" -ge 60 ]; do sleep 3; done
kubectl get pods -n knots-pilot --no-headers | awk '{print $2" "$3}' | sort | uniq -c
```
Expect `60 1/1 Running`.

## Run the scenario

**Real fork method** (RDTS injection, real consensus rejection, no scripted
partitioning):
```bash
warnet run scenarios/knots_mesh_pilot.py --namespace knots-pilot \
  -- --duration 600 --enable-difficulty --retarget-interval 2016 \
     --rdts-check-interval 15
```

**Manual network control** (reproduces the original
`partition_miner_with_pools.py`-style simulated partition, for comparison):
```bash
warnet run scenarios/knots_mesh_pilot.py --namespace <legacy-namespace> \
  -- --duration 600 --enable-difficulty --retarget-interval 2016 \
     --node-classification tag \
     --enable-manual-repartition --enable-asymmetric-bridging \
     --v26-acceptance-probability 0.0 \
     --no-rdts-injection
```
(`--v26-acceptance-probability 0.0` = strict UASF-style partition, matching
`chainsplit_persistence`'s baseline; raise it to model partial
softfork-rule compliance, per that flag's own `--help` text.
`--no-rdts-injection` since RDTS is meaningless without Knots nodes.)

Get the commander pod name and watch it:
```bash
kubectl get pods -n knots-pilot | grep commander
kubectl logs -n knots-pilot <commander-pod-name> --all-containers -f
```

## What to watch for (real fork method)

In order, roughly:
1. `Classifying nodes by subversion... v27 (Knots) nodes: 30 / v26 (Core) nodes: 30`
2. `Mining 101 maturity blocks...` / `Mined 101 blocks, height now ...`
3. `[RDTS] Injected OP_RETURN tx <txid> (81-byte payload) via node-XXXX (v26/Core)`
4. Eventually: `RDTS REJECTION DETECTED at <N>s: 30 v27 (Knots) node(s) show an invalid chain tip`
5. Both camps keep logging `v27 block`/`v26 block` lines independently
   afterward, fork status flips to `[SUSTAINED]` — confirms the split
   persists rather than healing.

If step 4 never appears within the run duration, something's wrong — check
Troubleshooting below (topology connectivity is the most likely culprit).

## Retrieving results

The scenario prints a base64-encoded JSON blob at the end, bracketed by
`RESULTS_EXPORT_START`/`RESULTS_EXPORT_END`. Extract it:

```bash
kubectl logs -n knots-pilot <commander-pod-name> --all-containers > commander.log

sed -n '/RESULTS_EXPORT_START/,/RESULTS_EXPORT_END/p' commander.log \
  | sed -E 's/\x1b\[[0-9;]*m//g' \
  | grep "RESULTS_DATA:" \
  | sed -E 's/^.*RESULTS_DATA:([A-Za-z0-9+\/=]*).*$/\1/' \
  | tr -d '\n' > results_b64.txt

python3 -c "
import base64, json
b64 = open('results_b64.txt').read().strip()
data = json.loads(base64.b64decode(b64))
json.dump(data, open('results.json', 'w'), indent=2)
print('keys:', list(data.keys()))
print(json.dumps(data['rdts_rejection'], indent=2))
"
```
(The `sed -E 's/\x1b\[[0-9;]*m//g'` step is required — raw `kubectl logs`
output has ANSI color codes wrapping each line, which corrupts the base64
stream if not stripped first.)

Save results under `results/<scenario_name>_<timestamp>/` in the repo (see
`results/knots_mesh_pilot_20260923_001852/` for the first confirmed run) —
`results.json` (the decoded blob above) plus `commander.log` (the raw log).

Key fields: `rdts_rejection` (injection txid, rejection confirmation,
rejecting node list), `fork_convergence` (did it heal), `summary.blocks_mined`,
`time_series` (for charting price/hashrate/economic weight over time —
identical schema to the legacy mode's output, so real-fork vs
manual-network-control runs are directly comparable here).

## Cleanup

```bash
kubectl delete pod -n knots-pilot -l mission=commander --ignore-not-found
for r in $(helm list -n knots-pilot -q); do helm uninstall -n knots-pilot "$r"; done
kubectl delete namespace knots-pilot --wait=true
# or, to tear down everything including the cluster itself:
minikube delete
```

## Troubleshooting (all previously hit, now fixed — but useful if they recur)

**Knots pods go straight to `Error`, log `Address in use (98)`.**
`node-defaults.yaml`'s `defaultConfig` duplicates fields the warnet Helm
chart's own `baseConfig`/`configmap.yaml` already inject (`rpcuser`,
`rpcallowip`, `rpcbind`, `rpcport`, `rpcpassword`, `fallbackfee`,
`zmqpubrawblock`, `zmqpubrawtx`, `regtest=1`). Core silently tolerates the
duplicate; Knots crashes on the duplicate `rpcbind`. Fix: `defaultConfig`
should only contain fields the chart doesn't already provide — currently
just `server=1`, `txindex=1`, `debug=rpc`. Check
`resources/charts/bitcoincore/values.yaml`'s `baseConfig` and
`templates/configmap.yaml` in the warnet source if this needs re-deriving
for a different network.

**`ModuleNotFoundError: No module named 'lib.price_oracle'` (or similar) in
the commander pod.** The installed `warnet` CLI's archive bundler
(`src/warnet/control.py`, and `scenDiscovery_control.py` at the warnet repo
root) only includes files whose path contains `__init__.py`, `commander.py`,
`test_framework`, `ln_framework`, or the scenario's own filename — it never
bundled `scenarios/lib/*.py` or `scenarios/config/*.yaml` by default. Fixed
by adding `"lib/"` and `"config/"` (no leading slash — `zipapp`'s filter
receives paths already relative to the source root) to that allowlist in
both files. This is a fix to the installed `warnet` tool itself; if working
from a fresh `warnet` checkout, re-apply it.

**Scenario crashes with `AssertionError`/timeout during `sync_all()`, or
mining just seems to hang with some nodes stuck at height 0.** The base
network's `addnode` graph may not be fully connected — check with:
```python
import yaml
from collections import deque
d = yaml.safe_load(open('networks/knots-mesh-pilot/network.yaml'))
adj = {n['name']: set(n.get('addnode', [])) for n in d['nodes']}
for n, peers in list(adj.items()):
    for p in peers:
        adj.setdefault(p, set()).add(n)
seen, q = {next(iter(adj))}, deque([next(iter(adj))])
while q:
    cur = q.popleft()
    for nb in adj[cur]:
        if nb not in seen:
            seen.add(nb); q.append(nb)
print(len(seen), '/', len(adj))
```
`realistic-economy-v2`-derived networks are specifically **two fully
disconnected 30-node islands** by construction (the original design relied
on scripted `submitblock` bridging to cross them) — real P2P bridging
requires adding a handful of genuine cross-camp `addnode` edges directly to
the network YAML (already done in `networks/knots-mesh-pilot/network.yaml`
— 5 bridge pairs, search for `node-0029` to find them). Re-run the
connectivity check above after editing before redeploying.

**`[RDTS] debug.log confirmation failed (pod-exec): ... 403 Forbidden`.**
The commander pod's ServiceAccount lacks `pods/exec` RBAC in the namespace.
The primary signal (`getchaintips` showing `status: invalid`) still works
without this — confirm the exact rejection reason manually instead:
```bash
kubectl logs -n knots-pilot <a-knots-node> -c bitcoincore | grep -i "bad-txns-vout-script-toolarge\|reduced_data"
```
To fix properly for unattended runs, add a `Role`/`RoleBinding` granting
the commander ServiceAccount `get`/`create` on `pods/exec` in the namespace.

**Pool/economic percentages look wrong or every pool shows only one side
(`v27=... v26=none`).** Confirm `--bundled-network-yaml` resolved to the
real network — log line `Loading network metadata from bundled config:
knots_mesh_pilot_network.yaml` and `✓ Loaded metadata for 60 nodes` (not
`25 nodes`, the generic example's count). If it's still 25, check
`scenarios/config/knots_mesh_pilot_network.yaml` exists and is a current
copy of `networks/knots-mesh-pilot/network.yaml` (re-copy if the network
was edited since).
