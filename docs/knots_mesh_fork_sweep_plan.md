# Knots-vs-Core Mesh Fork Test — Design Doc

Status: **Phase 1b CONFIRMED LIVE (2026-09-23), full run complete.**
Deployed to a real 60-node minikube cluster and observed the actual fork: a
Core-mined block carrying the injected 81-byte-`OP_RETURN` tx was rejected
live by all 30 Knots nodes (`bad-txns-vout-script-toolarge`, confirmed
directly in `debug.log` against the exact injected txid), while all 30 Core
nodes accepted it. The fork never healed for the rest of the 10-minute run:
final tally **v27 (Knots) = 16 blocks, v26 (Core) = 11 blocks**, fork status
`[SUSTAINED]` throughout, `fork_convergence.healed = false`. Full results
(structured JSON + raw commander log) saved at
`results/knots_mesh_pilot_20260923_001852/`. Three real infra bugs were
found and fixed to get here (see "Deployment findings" below). Depends on
`docs/building_knots_image.md` (building the `bitcoin-knots:29.4-local`
image) as a prerequisite.

## Deployment findings (2026-09-23) — three real bugs fixed to get a live run

1. **`node-defaults.yaml` duplicate-config regression.** Copying
   `realistic-economy-v2/node-defaults.yaml` verbatim reintroduced a bug
   already documented from the original Phase 1 pilot: the warnet Helm
   chart's own `baseConfig`/`configmap.yaml` already inject
   `rpcuser`/`rpcallowip`/`rpcbind`/`rpcport`/`rpcpassword`/`fallbackfee`/
   `zmqpubrawblock`/`zmqpubrawtx`/`regtest=1` — our `defaultConfig`
   duplicated all of them. Core silently tolerates the duplicate `rpcbind`;
   Knots hard-crashes on it (`Address in use (98)`), so all 30 Knots pods
   went `Error` on first deploy. Fixed by trimming `defaultConfig` down to
   only the fields the chart doesn't already provide (`server=1`,
   `txindex=1`, `debug=rpc`).
2. **`warnet run`'s archive bundler never included `scenarios/lib/*.py` or
   `scenarios/config/*.yaml`.** Its `filter()` (in the installed warnet's
   `src/warnet/control.py`, also duplicated in `scenDiscovery_control.py`)
   only allowlists paths containing `__init__.py`/`commander.py`/
   `test_framework`/`ln_framework`/the scenario's own filename — meaning
   `partition_miner_with_pools.py`'s own `lib.price_oracle` etc. imports
   could never have worked via `warnet run` either. Fixed by adding
   `lib/` and `config/` (relative-path substrings, since `zipapp`'s filter
   receives paths already relative to the source root — an initial fix
   using `/lib/`/`/config/` with a leading slash silently matched nothing).
   This is a fix to the installed `warnet` tool itself (editable install,
   takes effect immediately), not to this repo.
3. **`realistic-economy-v2`'s topology is two fully disconnected 30-node
   islands**, not one connected mesh — verified by BFS over the `addnode`
   graph (30 nodes reachable from `node-0000`, the other 30 completely
   unreachable). The original sweep design relied entirely on
   `propagate_to_foreign_accepting`'s `submitblock` bridging to cross
   between them — with that gated off by default (this session's whole
   point), the two camps could never reach each other at all, and
   `sync_all()` during maturity-block mining failed outright (some nodes
   never left height 0). Fixed by adding 5 genuine cross-camp `addnode`
   edges directly in `networks/knots-mesh-pilot/network.yaml` (real P2P
   bridges — `node-0000↔node-0030`, `node-0010↔node-0045`,
   `node-0020↔node-0059`, `node-0029↔node-0031`, `node-0015↔node-0050`),
   verified fully connected via the same BFS check before redeploying.

**Fixed (2026-09-23, same day):** `load_network_metadata()` was falling
back to the generic bundled 25-node `scenarios/config/network_metadata.yaml`
rather than our real 60-node network — `--network-yaml` can't resolve a
path inside the .pyz archive at runtime (`Path.exists()` checks the real
filesystem, not the zip), so the only way to ship real network metadata
into the commander pod is via the same `pkgutil`-bundled-data mechanism.
Fixed by copying `networks/knots-mesh-pilot/network.yaml` to
`scenarios/config/knots_mesh_pilot_network.yaml` and adding a new
`--bundled-network-yaml` flag (default: that file) that
`load_network_metadata()`'s fallback now reads instead of the hardcoded
`network_metadata.yaml` name — old generic behavior stays available by
passing `--bundled-network-yaml network_metadata.yaml`. Verified live: log
now reads `✓ Loaded metadata for 60 nodes` (not 25), and pool distribution
shows real per-node mapping (`foundryusa→node-0000`, `antpool→node-0030`,
etc.) instead of the generic example's fictional data. **Remember to
re-copy `scenarios/config/knots_mesh_pilot_network.yaml` if
`networks/knots-mesh-pilot/network.yaml` is edited later — nothing keeps
them in sync automatically.**

Still open: commander pod's ServiceAccount lacks `pods/exec` RBAC
permission, so `check_rdts_rejection()`'s own debug.log-grep confirmation
step fails (403 Forbidden). The RPC-based `getchaintips` signal still fires
correctly regardless, and the debug.log can be confirmed manually instead
(`kubectl logs <node> -c bitcoincore`, which needs no special RBAC). A
`Role`/`RoleBinding` granting the commander SA `pods/exec` would fix this
for future unattended runs — see `docs/running_knots_mesh_scenarios.md`'s
troubleshooting section.

**Full runbook**: `docs/running_knots_mesh_scenarios.md` — covers both this
real-fork mode and how to run the same script in its legacy
manual-network-control mode for direct comparison (per user's stated future
plan to compare the two methods), plus all of the above troubleshooting.

## Starting-allocation fixes (2026-09-24)

Found while reviewing how starting hashrate/economic weight are assigned
(neither affected the RDTS rejection itself):

1. **Every economic/user node started on v26 (Core).**
   `economic_node_strategy.py` picks a node's starting fork with
   `'27' in image_tag`; neither `29.4-local` nor `30.2` contains "27".
   Result as run: economic weight 0.0/100.0 Knots/Core. Fixed in
   `load_network_metadata()`: under `--node-classification subversion` the
   `image_tag` passed to the library is a camp label from the image
   repository (`27-knots`/`26-core`); `check_metadata_camps()` logs any
   disagreement with the live subversion classification. Tag mode is
   unchanged. Now 43.0/57.0.
2. **`realistic_current` pools didn't match the network.** Three config
   pools had no node, spiderpool had a node but no config entry, and
   neutral pools were alternately assigned to camps regardless of where
   their node was (f2pool/marapool assigned to the camp they have no node
   in). New pool scenario `knots_mesh_current` in
   `mining_pools_config.yaml`, generated from the network's pool nodes
   (hashrate/preference/ideology from node metadata, `initial_fork` = the
   camp its node runs), now the default `--pool-scenario`.
   Starting pool hashrate: **Knots 38.1% / Core 48.3%** (sums to 86.4%;
   solo-miner hashrate 2.85/8.90 is not part of the block-rate split,
   same as prior sweeps) — Knots is now the *minority* chain, unlike the
   pilot's 52.5/45.9.

Also: the saved `knots_mesh_pilot_20260923_001852` run predates the
bundled-network fix (its log shows `Loaded metadata for 25 nodes`), so its
pool/economic numbers come from the generic 25-node example; only its RDTS
rejection result is valid.

Remaining limitation: each pool has one node in one camp. If a pool's
strategy switches camps, its hashrate moves in the block-rate split, but
its blocks are mined by other nodes in that camp (it has no node there).
Paired per-pool nodes would fix attribution — a network redesign, deferred
to Phase 2.

## Goal

Test whether Knots (RDTS/BIP-110) and Core v30 nodes, connected on an
ordinary network with **no artificial network partitioning**, will fork
purely from consensus-rule divergence propagated through normal P2P block
relay — as opposed to earlier sweeps (chainsplit persistence, contested
fork threshold) which used a *scripted* runtime mechanism
(`v26_acceptance_probability` in `scenarios/partition_miner_with_pools.py`)
to probabilistically suppress cross-version block propagation, plus
explicit `addnode`/`disconnectnode`/`submitblock` calls to manually
reconnect/disconnect peers or bridge blocks mid-run.

**Scope correction (2026-09-22, superseding earlier drafts of this doc):**
this is not a from-scratch minimal script on a full mesh. It reuses nearly
all of `partition_miner_with_pools.py` (price/fee/pool/economic-node
oracles, difficulty oracle, reorg oracle, time-series recording) and the
same sparse/clustered topology prior sweeps used
(`networks/realistic-economy-v2/network.yaml`, 60 nodes, avg `addnode`
degree ~2.0) — for fidelity to prior methodology, not a full mesh. The only
thing that changes is *how* the "partition" manifests: instead of a
scripted probabilistic coin-flip and manual peer rewiring, it's now real
Knots consensus code rejecting a real transaction. Every old mechanism
(`propagate_v26_to_v27`, `switch_node_partition`, `reunite_forks`,
`propagate_to_foreign_accepting`) is still present in
`scenarios/knots_mesh_pilot.py`, **not deleted** — the two that were active
by default are now gated behind new off-by-default flags
(`--enable-manual-repartition`, `--enable-asymmetric-bridging`), so an
old-style v27/v26 simulated-partition run is still fully reproducible from
this same file.

## Mechanism (verified against `bitcoinknots/bitcoin` source directly)

Two independent RDTS enforcement paths exist in Knots — confirmed by
reading `versionbits.cpp`, `validation.cpp`, `deploymentstatus.h`,
`consensus/tx_verify.cpp` directly, not from documentation:

1. **Mandatory pre-activation signaling window** (`DeploymentMustSignalAfter`,
   `deploymentstatus.h:61`) — active only while BIP9 `state == STARTED`,
   rejects any block lacking version-bit 4, content-independent. Requires a
   multi-period wait through `DEFINED→STARTED→LOCKED_IN→ACTIVE` and is
   sensitive to `nMinerConfirmationWindow` period-boundary quantization
   (144 blocks on regtest, hardcoded, no CLI override exists).
2. **Post-`ACTIVE` output-size limit** (`Consensus::CheckOutputSizes`,
   `consensus/tx_verify.cpp:164`) — rejects any non-coinbase tx output over
   34 bytes (regular) or 83 bytes (`OP_RETURN`) with
   `bad-txns-vout-script-toolarge`.

**Decision: only mechanism 2 is modeled, with RDTS `ACTIVE` from genesis.**
Prior sweeps in this repo always assumed fork activation had already
occurred at simulation start (their economic models don't cover
pre-activation dynamics — futures markets, influencer effects). Matching
that assumption: `nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE`
(sentinel value `-1`) makes `GetStateFor` return `ThresholdState::ACTIVE`
unconditionally and permanently from genesis (`versionbits.cpp:20-22`, the
very first check in the function, unconditional on height). Since
`DeploymentMustSignalAfter` requires `state == STARTED`, mechanism 1 never
fires in this mode — it doesn't need to be modeled at all. This also
eliminates the entire `min_height`/`max_height`/`active_duration`/
`threshold`/period-quantization complexity that occupied earlier drafts of
this doc.

**vbparams**: `vbparams=reduced_data:-1:9223372036854775807` (`-1` =
`ALWAYS_ACTIVE`; `9223372036854775807` = `INT64_MAX`, the `NO_TIMEOUT`
sentinel, kept only because the parser requires a minimum of 3 fields —
`src/chainparams.cpp:78`). `consensusrules=rdts` is still set on Knots
nodes but only affects a startup log message — confirmed zero effect on
`GetStateFor`.

**The trigger**: from a Core (v26-labeled) node's wallet, broadcast a
transaction with one `OP_RETURN <81-byte payload>` output (81 bytes because
`MAX_OUTPUT_DATA_SIZE=83` includes the `OP_RETURN` opcode + `PUSHDATA1`
prefix, so 81+ bytes of payload pushes the total over 83). Once mined into
any block, Knots (v27) nodes reject that block outright
(`bad-txns-vout-script-toolarge`); Core (v26) nodes accept it normally,
since Core has no knowledge of this rule.

**Core version: 29.0 → 30.2.** Confirmed directly in `bitcoin/bitcoin`
source at both tags: `v29.0`'s `MAX_OP_RETURN_RELAY` is a fixed 83-byte
constant (`policy.h`); `v30.0`'s is
`MAX_STANDARD_TX_WEIGHT/WITNESS_SCALE_FACTOR` = 100,000 bytes (Core's real
"relax OP_RETURN limits" policy change). On `29.0`, the 81-byte injection
payload would itself be non-standard by Core's own *policy* (separate from
RDTS's *consensus* rule), requiring `-datacarriersize`/`-acceptnonstdtxn`
overrides on the Core miner — conflating "policy we tuned" with "the thing
under test." On `30.2`, it's standard by default: zero special config on
the Core side, a stock node vs. a stock node disagreeing purely by default.
`bitcoindevproject/bitcoin:30.2` is a prebuilt Docker Hub tag — confirmed to
exist, no custom build needed.

## Prior finding this doc previously got wrong (2026-09-04 pilot)

An earlier 9-node full-mesh pilot mined ~400 blocks through a full BIP9
cycle (`STARTED→LOCKED_IN(288)→ACTIVE(432)`, with the *old*
non-`ALWAYS_ACTIVE` vbparams) and observed no fork — only an advisory
`UpdateTip` warning, never a hard rejection. At the time this was
attributed to "the mandatory-signaling window is advisory-only, not a hard
rejection." Later same-session re-reading of `ContextualCheckBlockHeaderVolatile`
(`validation.cpp:4672-4691`, called unconditionally from `AcceptBlockHeader`
at `validation.cpp:2760`) showed mechanism 1 *is* a genuine hard
`BLOCK_CONSENSUS` rejection in source — the live pilot's negative result was
most likely a narrow-window sampling miss (BIP9 state only updates at
period boundaries, so the *effective* enforcement window with that specific
vbparams config was ~12 blocks, not the ~144 originally assumed), not proof
mechanism 1 doesn't work. This is now moot — the design no longer uses
mechanism 1 at all (see above), but it's recorded here since it explains
several reversals earlier in this doc's history.

## Reuse boundary: what's kept vs. gated off (not removed)

Derived from `scenarios/partition_miner_with_pools.py` — every function,
flag, and default is present in `scenarios/knots_mesh_pilot.py`. Checked
each mechanism's *existing* default against "must an old-style run still be
reproducible from this file":

| Mechanism | Existing default | Change needed |
|---|---|---|
| `propagate_v26_to_v27` (coin-flip, `--v26-acceptance-probability`) | `0.0` (inert) | None — already off |
| `reunite_forks` (end-of-run trigger, `--enable-reunion`) | `False` (inert) | None — already off |
| `reunite_forks` (UASF-expiry trigger, `--uasf-duration`) | `None`/never expires (inert) | None — already off |
| `switch_node_partition` (called from `evaluate_economic_node_switches`) | unconditional, **not gated** | **New flag**: `--enable-manual-repartition` (default `False`) |
| `propagate_to_foreign_accepting` (called from mining loop, both branches) | unconditional whenever `accepts_foreign_blocks` metadata is `True` for some nodes — confirmed **30/30 split** in `realistic-economy-v2`, i.e. genuinely active by default, not inert | **New flag**: `--enable-asymmetric-bridging` (default `False`) |

Node classification: `partition_nodes_by_version()` (original, image-tag
matching) is kept unchanged; a new `classify_nodes_by_subversion()` method
is added alongside it (`getnetworkinfo()['subversion']` — Knots reports
`/Satoshi:29.4.0/Knots:20260508/`, Core reports plain `/Satoshi:30.2.0/`).
Selected via `--node-classification {tag,subversion}` (default
`subversion`). Note: the original `tag`-based method would classify *zero*
nodes for this network — neither "29.4.0" nor "30.2.0" contains "27." or
"26." as a substring — so `subversion` is required for this use case.

Oracle libraries (`PriceOracle`, `FeeOracle`, `MiningPoolStrategy`,
`EconomicNodeStrategy`, `ReorgOracle`) are **not edited** — they hardcode
`'v27'`/`'v26'` as internal bookkeeping labels; those strings are kept as
arbitrary internal identifiers (`'v27'` = Knots camp, `'v26'` = Core camp)
rather than touching well-tested library code for a cosmetic rename.

## What's new in `scenarios/knots_mesh_pilot.py`

- `classify_nodes_by_subversion()` — see above.
- `ensure_common_history()` — mines 101 maturity blocks if the network
  doesn't already have them (idempotent, checked via `getblockcount()`),
  funding a v26 (Core) node's wallet so the injection tx has a spendable
  input. `partition_miner_with_pools.py` itself never mines maturity blocks
  (it assumes a prior timeline step did — see
  `scenarios/example_timeline.yaml`'s `generate_common_history` action);
  this scenario can't assume that step ran, so it checks and mines its own.
- `inject_rdts_violation()` — builds and `sendrawtransaction`s the
  81-byte-`OP_RETURN` tx from a v26 node, once, shortly after maturity (no
  BIP9 wait needed — RDTS is `ALWAYS_ACTIVE`). Gated by `--rdts-injection`
  (default `True` — this is the actual point of this script) /
  `--no-rdts-injection`. Payload size via `--op-return-payload-size`
  (default 81).
- `check_rdts_rejection()` — polls `getchaintips()` on v27 (Knots) nodes for
  `status: "invalid"`, then (once, on first detection) confirms via
  pod-exec grep (`kubernetes.stream.stream`, reusing the exact pattern
  `commander.py` already uses for its `bitcoin-util grind` call) of the
  first rejecting node's `debug.log` for the literal string
  `bad-txns-vout-script-toolarge`. Runs every `--rdts-check-interval`
  seconds (default 30) plus once more at end of run. Results recorded in
  `self.rdts_rejection` and exported in the JSON results under
  `rdts_rejection`.

- `observe_chain_state()` (added 2026-09-24) — observation-only sampling of
  real node tips per camp: tip relation/LCA/branch lengths, reorgs, injected
  tx confirmation state, Knots invalid-branch count. Exported as
  `chain_state`. Added because the 2026-09-23 run's `v27=16 / v26=11` and
  `[SUSTAINED]` were mining-loop counters, never checked against the nodes:
  Core accepts Knots blocks, so once the Knots chain pulled ahead (~527s)
  the Core nodes most likely reorged onto it — unobserved. Verified against
  a mock chain simulation only; not yet run live.

## Network config: `networks/knots-mesh-pilot/`

Rebuilt (2026-09-22) from `networks/realistic-economy-v2/network.yaml` (the
confirmed base template for the `partition_miner_with_pools.py`-family
sweeps this session traced — 60 nodes, avg `addnode` degree 2.03, per-node
`metadata` schema matching what the pool/economic-node oracles read). The
transform, applied via a one-off Python script (not committed, output
verified programmatically — see checklist below):

- `addnode` graph: **unchanged**.
- `metadata` (including the 30/30 `accepts_foreign_blocks` split):
  **unchanged**.
- `bitcoin_config` (a dict key present in the source template —
  `maxconnections`/`maxmempool`/`txindex` per node) is **not a real warnet
  schema field** (confirmed: zero references anywhere in the `warnet`
  source or its Helm charts). Converted to the real `config:` string field
  instead, one `key=value` line per entry, so these per-node settings
  actually take effect on deploy (previously would have been silently
  ignored).
- `image`: nodes tagged `27.0` in the source → `{repository: bitcoin-knots,
  tag: 29.4-local}`, plus `config:` gets `consensusrules=rdts` and
  `vbparams=reduced_data:-1:9223372036854775807` appended. Nodes tagged
  `26.0` → `{tag: '30.2'}` (repository stays the `node-defaults.yaml`
  default, `bitcoindevproject/bitcoin`).
- Result: 30 Knots / 30 Core nodes (verified programmatically).

`networks/knots-mesh-pilot/node-defaults.yaml` is unchanged — confirmed
byte-identical to `realistic-economy-v2/node-defaults.yaml`.

## Verification (not yet performed)

- Deploy `networks/knots-mesh-pilot/` to a fresh namespace, run
  `scenarios/knots_mesh_pilot.py` with a modest `--duration` first.
- Confirm: node classification via subversion works (30/30 split observed
  live, not just in the config), maturity/injection succeed, and — the
  actual pass condition — `bad-txns-vout-script-toolarge` shows up in a
  Knots node's `debug.log` with a corresponding `getchaintips()` /
  `getbestblockhash()` split.
- Sanity-check that gating `switch_node_partition` (via
  `--enable-manual-repartition`, default off) and
  `propagate_to_foreign_accepting` (via `--enable-asymmetric-bridging`,
  default off) didn't silently break the rest of
  `evaluate_economic_node_switches`'s decision logic or the mining loop —
  both should still run and log normally, just without the gated actions.
- Confirm an old-style run (`--node-classification=tag`,
  `--enable-manual-repartition`, `--v26-acceptance-probability=<nonzero>`,
  pointed at an old v27/v26-tagged network) still behaves as before — this
  is the actual backward-compatibility claim, unverified until tested.

## Prerequisites checklist

### Phase 1b gate (fork trigger validation)
- [x] Build `bitcoin-knots:29.4-local` per `docs/building_knots_image.md`
- [x] `warnet` CLI + venv available
- [x] Docker + minikube working
- [x] Exact RDTS output-size rule confirmed in source
      (`Consensus::CheckOutputSizes`, `bad-txns-vout-script-toolarge`)
- [x] `ALWAYS_ACTIVE` mechanism confirmed in source (`versionbits.cpp:20-22`)
- [x] Core on `30.2` in `networks/knots-mesh-pilot/network.yaml`
- [x] `scenarios/knots_mesh_pilot.py` written (derived from
      `partition_miner_with_pools.py`, all mechanisms preserved/gated)
- [x] `networks/knots-mesh-pilot/network.yaml` rebuilt from
      `realistic-economy-v2` (60 nodes, 30/30 Knots/Core, topology + metadata
      preserved, `bitcoin_config`→`config` converted, `vbparams`/
      `consensusrules` added to Knots nodes)
- [x] Actually deployed and run — 60-node minikube cluster, 2026-09-23
- [x] Live tip divergence observed between Knots and Core camps — all 30
      Knots nodes showed `getchaintips` status `invalid` at t=46s
- [x] `bad-txns-vout-script-toolarge` confirmed in Knots debug logs (live) —
      exact injected txid `8b55d63c7fcfc78478957f4038ca5160138fff39cb1ad6ddcc03b42f08039954`
      named in the error

### Phase 1c gate (split behavior validation) — partially observed live
- [x] Knots camp holds stable tip and continues mining after rejecting a
      Core block (v27: 3→6 blocks over the following ~4 minutes)
- [x] Core camp continues mining independently (v26: 3→5 blocks)
- [x] No peer disconnects/crashes from the rejection itself (occasional
      unrelated "Error mining: timed out" transient RPC hiccups under
      cluster load, scenario recovered on its own both times)
- [ ] Longer/quieter run (not sharing the box with repeated `kubectl exec`
      debugging) to confirm stability over 20+ blocks per camp without the
      transient timeouts observed this run
- [x] Confirm whether the split actually persists on the nodes — **yes, with
      Knots as the hashrate minority** (2026-09-24, 1800s run,
      `results/knots_mesh_pilot_20260924_163848/`, `knots_mesh_current` pools
      38.1/48.3, economic 43.0/57.0). Observed tips: diverged from 102s to
      end, LCA 104, final Knots h=148 (branch 44) vs Core h=168 (branch 64),
      matching `blocks_mined` 47/64 (incl. 3 pre-split). Zero reorgs on
      either camp, one invalid branch, injected tx confirmed at 105 on Core
      throughout. `bad-txns-vout-script-toolarge` for the injected txid
      confirmed in node-0010's log. No pool or economic reallocations over
      the run (ideology held everyone). 6 transient mining RPC errors
      (1 timeout, 5 `No route to host`), recovered.
- [x] Knots-majority case — **confirmed** (2026-09-24, 1800s, fresh
      deploy, `--randomseed 20260924`, pool scenario
      `knots_mesh_knots_majority` = knots_mesh_current with camp totals
      mirrored to 48.3/38.1; `results/knots_mesh_pilot_20260924_174116_knots_majority/`).
      Repeated wipe-out cycle: 10 Core reorgs onto the Knots chain (depth
      1–10), 10 distinct invalid branches on Knots (the injected tx re-mined
      after each reorg and rejected again), 0 Knots reorgs. Final: Knots
      h=155 = 101 + all 54 Knots blocks; Core h=156 = the Knots chain + 1
      fresh bad block — i.e. 42 of 43 Core-mined blocks were orphaned.
      Tip relation over 150 samples: diverged 93, Core-one-bad-block-ahead
      36, same tip 21.
      **Model gap exposed:** `blocks_mined` credits Core with 43 blocks and
      the price/fee/pool oracles run off those counters, so Core's price
      stayed ≈ Knots' ($59.8k vs $59.5k) and nobody switched — the
      economic layer doesn't know Core's chain is being orphaned.
      **Addressed 2026-09-25:** `--oracle-chain-source observed` (default in
      subversion mode) feeds surviving-block chain weight + observed fork
      depth into the price oracle and survival-scaled blocks/hour into pool
      profitability (see runbook). Mock-tested only (6 wipe-out cycles: Core
      survival 0.08, AntPool's Core-side profit $5.36M/h → $0.41M/h);
      **Live-confirmed 2026-09-25** (`--randomseed 20260925`, fresh deploy,
      `results/knots_mesh_pilot_20260925_093746_knots_majority_observed/`):
      Core's branch led for the first ~1000s (35 blocks deep); at 1068s
      Core reorged onto Knots (depth 35), recent Core survival → ~0. At the
      ~1206s pool decision all four Core pools force-switched to Knots
      ("loss 79.9% exceeds tolerance"), hashrate 48.3/38.1 → 86.4/0. One
      more Core reorg (1342s, depth 7), then Core stopped mining; network
      converged on the Knots chain (same tip h=175 at end), injected tx left
      in Core mempools (Knots policy won't relay/mine it). Totals: Knots
      74/74 blocks survived, Core 0/42. Price moved to $64.5k / $54.8k.
      Economic weight stayed 43/57 all run — not a bug: `realistic_current`
      switching cooldowns (1800s economic, 3600s user) are ≥ the run length,
      so nodes decided only once at t=0. Longer runs or shorter cooldowns
      are needed to see economic nodes move. Also: each run needs a fresh deploy — the
      chain persists across `warnet run`s on the same network.

### Phase 2 — not started
No LHS sweep infrastructure exists yet. Given how much this session's
reuse-vs-rewrite decision changed the shape of Phase 1b, Phase 2's design
(sweep axes, `tools/sweep/knots_mesh_fork/` scaffolding) should be
revisited fresh once Phase 1b/1c are confirmed working live, rather than
planned further in the abstract now.

## Open items

- Phase 1b has never been run. Everything above is implementation +
  source-verification, not empirical confirmation.
- Whether `--node-classification=tag` / old-flag reproducibility actually
  works end-to-end is asserted by code inspection, not tested.
