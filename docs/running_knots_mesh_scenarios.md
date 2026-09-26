# Running the Knots Mesh Fork Scenario

How to deploy and run `scenarios/knots_mesh_pilot.py`, in any of its three
modes, plus how to retrieve results and troubleshoot the environment issues
already hit once. Background/design: `docs/knots_mesh_fork_sweep_plan.md`.

## The modes (read this first)

`knots_mesh_pilot.py` is a derived copy of `scenarios/partition_miner_with_pools.py`
— every old mechanism is still in the file, gated behind flags that default
to the *new* behavior. This means **the same file runs either experiment**:

| | Real fork method (default) | Real fork + in-place switching | Manual network control (legacy) |
|---|---|---|---|
| What causes the split | Real Knots consensus code rejecting a real transaction | Same | Scripted `submitblock` bridging + probabilistic acceptance |
| What a pool/economic "switch" does | Accounting only: hashrate/weight moves, every node keeps its software | **The node itself changes rules** (RDTS on/off + restart), so relay and validation follow the choice | Manual peer rewiring (`switch_node_partition`) |
| Node classification | `getnetworkinfo()['subversion']` (Knots vs Core) | RDTS deployment status (`getdeploymentinfo`) | Image-tag substring match (`27.` vs `26.`) |
| Network needed | `networks/knots-mesh-pilot/` (Knots + Core v30.2 images) | `networks/knots-mesh-inplace/` (all Knots) + warnet patch | Any old-style network using real Core version tags, e.g. `networks/realistic-economy-v2/` unmodified |
| Key flags | defaults (nothing extra needed) | `--inplace-switching --bundled-network-yaml knots_mesh_inplace_network.yaml` | `--node-classification tag --enable-manual-repartition --enable-asymmetric-bridging --v26-acceptance-probability <0.0-1.0>` |

Use the same `--pool-scenario`/`--economic-scenario`/`--duration`/etc. for
both runs if you want the economic simulation to be comparable side by
side — only the fork-causing mechanism and network differ.

Default `--pool-scenario` is `knots_mesh_current` (generated from this
network's pool nodes: Knots 38.1% / Core 48.3% starting pool hashrate). If
`networks/knots-mesh-pilot/network.yaml` is edited, regenerate it along with
`scenarios/config/knots_mesh_pilot_network.yaml`. Economic/user nodes start
on the camp their image runs (43.0/57.0 Knots/Core economic weight) — look
for `Metadata camps match live classification for all 60 nodes` in the log.

**Block production** (`--enable-difficulty`): each 1s tick, each camp mines
a block with probability `tick / (target × difficulty / hashrate_fraction)`
(target = `--interval`, default 10s), using that camp's current pool
hashrate. Pools re-decide every `--pool-decision-interval` (600s), which
changes those rates. Solo-miner hashrate only affects which node mines a
camp's block, not how often.

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

**Real fork + in-place switching** (needs the warnet patch — see
"In-place switching mode" below):
```bash
warnet deploy networks/knots-mesh-inplace --namespace knots-pilot
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

**Real fork + in-place switching** (node-runner and pool choices change
what their nodes enforce):
```bash
warnet run scenarios/knots_mesh_pilot.py --namespace knots-pilot \
  -- --duration 3600 --enable-difficulty --retarget-interval 2016 \
     --rdts-check-interval 15 \
     --inplace-switching \
     --bundled-network-yaml knots_mesh_inplace_network.yaml \
     --economic-switching-cooldown 300 --user-switching-cooldown 300
```
(The cooldown flags are optional, but without them economic/user nodes
won't move in a short run. See "Economic-node switching".)

**Manual network control** (reproduces the original
`partition_miner_with_pools.py`-style simulated partition, for comparison):
```bash
warnet run scenarios/knots_mesh_pilot.py --namespace <legacy-namespace> \
  -- --duration 600 --enable-difficulty --retarget-interval 2016 \
     --node-classification tag \
     --bundled-network-yaml realistic_economy_v2_network.yaml \
     --enable-manual-repartition --enable-asymmetric-bridging \
     --v26-acceptance-probability 0.0 \
     --no-rdts-injection
```
(`--v26-acceptance-probability 0.0` = strict UASF-style partition, matching
`chainsplit_persistence`'s baseline; raise it to model partial
softfork-rule compliance, per that flag's own `--help` text.
`--no-rdts-injection` since RDTS is meaningless without Knots nodes.
`--bundled-network-yaml realistic_economy_v2_network.yaml` is required: the
default is the Knots network's metadata, whose 29.4-local/30.2 tags make every
economic/user node start on v26 under tag classification. The scenario logs a
warning if this is missed. `scenarios/config/realistic_economy_v2_network.yaml`
is a copy of `networks/realistic-economy-v2/network.yaml` — re-copy it if that
network changes. Do not use `network_metadata.yaml`; the sweep generator
rewrites it.)

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
   afterward and fork status flips to `[SUSTAINED]` — but **these are
   mining-loop bookkeeping, not observed chain state**. Use the
   `[chain-state ...]` lines (step 6) to see what the nodes actually hold.
6. `[chain-state Ns] tips: <prev> -> <relation>` whenever the real tip
   relation between camps changes, and `[chain-state Ns] REORG on v26 (Core)
   ...` when sampled nodes switch chains. Core accepts Knots blocks, so a
   longer Knots chain reorgs Core nodes onto it; the injected tx then returns
   to the Core mempool, gets re-mined, and Knots rejects it again (a new
   invalid branch). Relations: `same_tip`, `diverged` (with LCA and branch
   lengths), `v26_ahead_on_v27_chain` (Core tip builds on Knots' tip —
   typically a freshly re-mined bad block Knots won't follow),
   `v27_ahead_on_v26_chain`, `unknown` (RPC failure).
   An `OBSERVED CHAIN STATE` block at the end summarizes it.

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
rejecting node list), `chain_state` (observed real tips — see below),
`fork_convergence` (did it heal; only populated with `--fork-heal-exit`),
`summary.blocks_mined` (mining-loop counter, not chain state),
`time_series` (for charting price/hashrate/economic weight over time —
identical schema to the legacy mode's output, so real-fork vs
manual-network-control runs are directly comparable here).

`chain_state` (from `observe_chain_state()`, every `--chain-state-interval`
seconds, default 10, on `--chain-state-sample` evenly spaced nodes per camp,
default 3; `--chain-state-interval 0` disables):
- `time_series` — its own `timestamps` plus per-observation `relation`,
  `v27_height`/`v26_height`, tips, `fork_height` (LCA when diverged),
  `v27_branch_len`/`v26_branch_len`, `v27_distinct_tips`/`v26_distinct_tips`
  (disagreement within a camp's sample = propagation lag),
  `injected_tx_state` (`mempool`/`confirmed`/`unconfirmed`/`conflicted`) and
  `injected_tx_height`, `v27_invalid_tips` (distinct invalid branches a
  Knots node has seen).
- `reorg_events` — one per (camp, disconnected tip): old/new height and tip,
  `fork_height`, `depth`, and which sampled nodes observed it.
- `reorg_count`, `max_reorg_depth`, `max_invalid_tips`, `relation_changes`,
  `final`.

Runs before 2026-09-24 (including `knots_mesh_pilot_20260923_001852`) have
no `chain_state` — their post-rejection chain state was never observed.

### Oracles read observed chain state (`--oracle-chain-source`)
Default `observed` under `--node-classification subversion` (`mined` under
`tag`, so legacy runs reproduce). With `observed`:
- **Price oracle:** chain weight = each camp's share of *surviving* blocks
  it mined (still in its observed active chain); fork depth / sustained
  check use observed heights and the observed LCA instead of
  `start_height + blocks_mined`.
- **Pool decisions:** each camp's blocks-per-hour is scaled by its recent
  survival ratio (last `--survival-window` blocks it mined, default 30;
  1.0 until 5 mined), so orphaned blocks earn nothing.
- **Not changed:** fee oracle (Core users sit on the Knots chain between
  wipe-outs, so their tx throughput isn't actually reduced), difficulty
  oracle (still sets block *rates* from hashrate), reorg oracle,
  economic-node strategy (reacts through price).
- `chain_state.survival` (`mined`/`surviving`/`orphaned`/`window_ratio` per
  camp) and `time_series.{v27,v26}_surviving` / `_survival_ratio` record it;
  `summary.blocks_mined` is still the raw mining counter.

### Economic-node switching (`--economic-switching-cooldown`, `--user-switching-cooldown`)
`realistic_current` sets `switching_cooldown` to 1800s (economic) and 3600s
(user). In runs up to ~1800s each node decides once at t=0, while prices are
still equal, and the economic weight never moves (it stayed 43/57 in every run
through 2026-09-25). To exercise economic switching in a short run, lower the
cooldowns, e.g. `--economic-switching-cooldown 300 --user-switching-cooldown 300`.
Decisions are only evaluated every `--economic-update-interval` (default 300s),
so that is the effective floor. Lower both if you want finer resolution.
Both flags default to the config values, so existing runs are unchanged. The
log line `Overrode switching_cooldown=...` confirms they took effect.

Expect all-or-nothing swings. 80.8% of economic custody is in 6 nodes, 5 of
them `neutral` with 2–4% switching thresholds. v26-ideological holders do stay
put (verified offline: node-0045/0046 keep v26 through ideology overrides), but
together they hold only ~628 BTC. An offline check with a 17.7% price gap and
60s cooldown moved economic weight 43/57 → 100/0. That is a property of the
network's custody distribution, not a bug.

### In-place switching mode (`--inplace-switching`)
**What it models:** a pool or node runner changing software. When the pool
strategy moves a pool to the other fork, or the economic strategy moves an
economic/user node, the scenario changes what **that node** enforces:
1. It rewrites `/root/.bitcoin/switch.conf` via pod exec. The RDTS `vbparams`
   line is present for the Knots camp and absent for Core mode.
2. RPC `stop`; `restartPolicy: Always` relaunches bitcoind in the same pod,
   so it keeps its peers (`addnode` config) and chain.
3. It waits for the node to report the new RDTS status.
4. It reconciles the chain, as a real operator would after swapping software
   on an existing datadir. Joining Knots: `invalidateblock` the violating
   blocks. Joining Core: `reconsiderblock` every invalid tip.

Pools then mine from their own node on the new side. Relay nodes (no pool
or economic role) keep their starting camp.

**Setup, once per warnet install:** apply `docs/warnet_changes.patch` (see
`docs/warnet_changes_required.md`: W2 commander `pods/exec` RBAC, W3
`extraInitContainers` chart hook). Also make `alpine:latest` available to
the cluster (`minikube image pull alpine:latest`); the seed init container
uses it. The network is generated, so edit `knots-mesh-pilot` and rerun
`python3 tools/make_inplace_network.py`, which rewrites both
`networks/knots-mesh-inplace/` and the bundled
`scenarios/config/knots_mesh_inplace_network.yaml`.

**Every node runs Knots.** Core mode = Knots with RDTS inactive. This was
verified to accept the violating blocks (consensus-compatible with Core).
Relay policy is still Knots', and Knots caps `datacarriersize` at 83, so no
mempool holds the violating tx. The scenario stands in for the Core
mempool: whenever a Core-mode pool mines and its chain lacks the tx, it
includes it via `generateblock`. That includes re-mining it after a
wipe-out. `injected_tx_state` reads `pending` until a Core-mode block
carries it.

**What to watch in the log:**
- `Classifying nodes by RDTS deployment status` → 30/30.
- `IN-PLACE SWITCH (pool decision|economic decision, <t>s): N node(s)`,
  then one line per node with its downtime and `invalidated`/`reconsidered`
  counts.
- `[RDTS] node-XXXX (Core-mode) mined violating tx in block ... (violating
  block #N)`. N > 1 means Core re-mined it after its chain was reorged away.

**Results:** `inplace_switching.{switches, total_switches, failed_switches,
violating_blocks, final_camps}`. Each switch records role, trigger,
from/to, downtime, heights and tips before/after, and reconcile counts.

**Expected timing effects (real behaviour, not bugs):**
- **Restart downtime.** About 2s in Docker. In Kubernetes, kubelet
  restart back-off adds roughly 10s at first, and doubles if the same
  container restarts again within 10 minutes (up to 5 min).
  `--switch-restart-timeout` (default 180s) bounds the wait. A node that
  misses it is logged as a failed switch and keeps its old camp in tracking.
- **Re-sync lag.** A switched node's *outbound* peers reconnect at startup,
  but inbound peers only come back on their own addnode retry, about a
  60s cycle. If all of a node's outbound peers are on the other side, it
  can trail its new camp's tip until then. The Docker test saw about 26s.
- Switches in one decision round run concurrently (all stop, then all wait),
  so a big economic swing doesn't stall the loop node by node.

Offline test of this code path (no Kubernetes):
`tools/knots_switch_test/scenario_harness.py`.

**Every run needs a fresh deploy** — chains persist across `warnet run`s on
the same network, so a second run starts from the previous run's split.
Uninstall the helm releases (see Cleanup) and `warnet deploy` again.
Pass `--randomseed <N>` per run — `scenarios/commander.py` defaults it to a
constant, so otherwise every run makes identical random draws.

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
