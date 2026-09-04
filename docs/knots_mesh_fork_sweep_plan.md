# Knots-vs-Core Mesh Fork LHS Sweep — Design Doc

Status: **Phase 1 COMPLETE (2026-09-04). Phase 2 design revised — see
Phase 1 findings below.** Depends on `docs/building_knots_image.md`
(building the `bitcoin-knots:29.4-local` image) as a prerequisite.

## Goal

Test whether Knots (RDTS/BIP-110) and Core v29 nodes, running on an ordinary
fully-connected mesh with **no artificial network partitioning**, will
organically fork purely from consensus-rule divergence propagated through
normal P2P block relay — as opposed to earlier sweeps (chainsplit
persistence, contested fork threshold) which used a *scripted* runtime
mechanism (`v26_acceptance_probability` in
`scenarios/partition_miner_with_pools.py`) to probabilistically suppress
cross-version block propagation, plus explicit `addnode`/
`switch_node_partition` calls to manually reconnect/disconnect peers
mid-run. That scripted layer is itself a form of artificial network
control — this sweep removes it entirely and tests whether the fork happens
anyway, from mesh topology + normal messaging alone.

## Mechanism (verified against `bitcoinknots/bitcoin` source; Phase 1 live results below)

Confirmed by reading `versionbits.cpp`, `validation.cpp`,
`deploymentinfo.cpp` in the Knots repo directly (not from documentation —
read the actual consensus code):

- On regtest, the `reduced_data` (RDTS/BIP-110) deployment defaults to
  `nStartTime = NEVER_ACTIVE` and must be made reachable via a
  `vbparams=reduced_data:start:timeout:min_height:max_height:duration:threshold`
  config override (`chainparams.cpp` regtest constructor takes
  `opts.version_bits_parameters`).
- `max_activation_height` forces `LOCKED_IN` one confirmation period (144
  blocks on regtest) before that height, **regardless of miner signaling
  threshold** (`versionbits.cpp:99-101`) — a real UASF-style forced
  activation, not a 75%-threshold-dependent one.
- In the one-period window immediately before `max_activation_height`, Knots
  nodes log `warning='Miner violated version bit protocol'` (via `UpdateTip`)
  for Core blocks that don't set bit 4. **This is an advisory warning only —
  NOT a hard consensus rejection for pure coinbase mining.** The error
  `bad-version-<deployment>` from `ContextualCheckBlockHeader` was not
  observed to fire in live testing. Pure coinbase blocks are accepted even
  within the signaling window.
- Knots' `reduced_data` deployment has `gbt_force = true`
  (`deploymentinfo.cpp`), so any Knots node automatically signals bit 4 on
  blocks it mines once `STARTED` — zero scenario-script involvement needed.
  Core v29 nodes have no knowledge of this deployment and never signal it.
- The `bad-version-reduced_data` hard rejection **does** exist in the binary
  but fires on RDTS-violating **transactions** (e.g., OP_RETURN outputs
  exceeding 80 bytes) when the deployment is `ACTIVE`, not on coinbase blocks
  that lack the version bit.

**Net effect (revised after Phase 1 live testing):** the mandatory-signaling
window alone is **NOT sufficient** to produce a fork with pure coinbase-only
mining. Triggering hard block rejection requires injecting RDTS-violating
transactions into Core-mined blocks once the deployment is `ACTIVE`. The
"no crafted transactions needed" claim in the original design was wrong — it
was based on a misreading of which code path fires for which violation type.
See Phase 1 findings below for the full empirical record.

## Phase 1 — Pilot (COMPLETE — 2026-09-04)

### What was built and tested

- **Network**: `networks/knots-mesh-pilot/` — 9 nodes (5 Knots, 4 Core), full
  mesh, namespace `knots-pilot` on minikube.
  - Knots: `bitcoin-knots:29.4-local`, `consensusrules=rdts`,
    `vbparams=reduced_data:0:9223372036854775807:0:300:144:100`
  - Core: `bitcoindevproject/bitcoin:29.0`, unmodified.
- **Scenario**: `scenarios/knots_mesh_pilot.py` — minimal round-robin mining,
  no partition control, per-node tip polling every N blocks.
- **Blocks mined**: ~400 (plus 101 maturity blocks), passing through full
  BIP9 cycle: STARTED→LOCKED_IN(288)→ACTIVE(432).

### vbparams syntax (empirically verified)

`vbparams=reduced_data:0:9223372036854775807:0:300:144:100`

- `timeout=9223372036854775807` (INT64_MAX) is the NO_TIMEOUT sentinel —
  the **only** value accepted alongside `max_activation_height`. Any other
  non-zero value triggers "Cannot specify both timeout (X) and
  max_activation_height (Y)".
- Field order: `deployment:start:timeout:min_height:max_height:period:threshold`
- Knots subversion string: `/Satoshi:29.4.0/Knots:20260508/`

### What was confirmed working

- `bitcoin-knots:29.4-local` image builds and runs in Kubernetes (minikube) ✅
- `consensusrules=rdts` parsed and logged at startup ✅
- `vbparams` accepted; `getdeploymentinfo` shows correct state progression ✅
- BIP9 state machine: STARTED→LOCKED_IN(forced at 288)→ACTIVE(432) ✅
- Node classification (Knots/Core via subversion string) works ✅
- Round-robin mining across 9 nodes works ✅

### Key finding: mandatory-signaling window does NOT produce hard block rejection

**The fork never occurred.** All 9 nodes stayed in consensus through the full
run (heights 0–490+, past ACTIVE at 432).

What was observed during the mandatory-signaling window and ACTIVE state:
- Knots nodes log `warning='Miner violated version bit protocol'` (via
  `UpdateTip`) for Core-mined blocks that don't set bit 4
- This is an advisory `UpdateTip` message, **not a consensus rejection**
- `bad-version-reduced_data` was never logged and never caused a rejected block
- Core-mined coinbase-only blocks were accepted and propagated by Knots nodes
  throughout the window and after ACTIVE

**Root cause:** `bad-version-reduced_data` fires on RDTS-violating
**transactions** inside a block, not on blocks that merely lack the version
bit. In regtest round-robin mining with no mempool transactions, all blocks
are effectively coinbase-only — no RDTS payload rules are ever exercised.
The mandatory-signaling warning path and the transaction-rejection path are
separate code paths; the original design conflated them.

### Infrastructure issues encountered and resolved

- **Duplicate rpcbind**: Knots fails if `rpcbind=0.0.0.0` appears twice in
  `bitcoin.conf` (helm base injects it; `defaultConfig` must not repeat it).
  Bitcoin Core silently ignores duplicates; Knots throws "Address in use (98)".
- **minikube image loading**: `warnet image build --action load` only loads
  into host Docker. Must also run `minikube image load bitcoin-knots:29.4-local`.
- **Pod lifecycle**: warnet uses standalone Pods (not Deployments). `helm
  upgrade` updates ConfigMaps but does not restart running pods. Full cleanup
  via `helm uninstall -n knots-pilot $(helm list -n knots-pilot -q)` +
  `kubectl delete namespace knots-pilot` is the reliable approach.
- **Commander.generatetoaddress()**: first argument is `node` (not `wallet`).
  See `miner_std.py`: `self.generatetoaddress(miner.node, num, miner.addr, ...)`.

### Revised fork trigger

The mandatory-signaling window is insufficient alone. To observe hard block
rejection, the scenario must inject RDTS-violating transactions when ACTIVE:

**Option A (recommended):** After reaching ACTIVE state, use Core nodes to
broadcast transactions with OP_RETURN outputs > 80 bytes. Knots will reject
blocks containing those transactions. This requires:
1. Mine to ACTIVE state (height 432+ with current vbparams).
2. From Core wallet, create and broadcast transactions with large OP_RETURN
   outputs (e.g., `OP_RETURN <81-byte payload>`).
3. Have Core nodes mine blocks including those transactions.
4. Knots nodes reject those blocks → tip divergence.

**Option B:** Use a different fork mechanism entirely — e.g., a rule that
fires purely on block-header fields (e.g., block version, nTime) rather than
transaction content. Check Knots' other `consensusrules=` options.

Do not proceed to Phase 2 until one of these alternatives is validated.

## Phase 2 — LHS sweep

New sweep directory: `tools/sweep/knots_mesh_fork/` (matches the
`generate_sweep.py` + `spec.yaml` + `RUN_INSTRUCTIONS.md` convention used by
the `chainsplit_persistence`/`contested_fork_threshold` sweeps).

**Fixed (not swept), same for every sample:**
- Topology: full mesh via `configurable_network_generator.py`'s existing
  `full_economic_mesh`/`pool_peer_strategy: full_mesh` option — this is the
  control condition the whole sweep is designed around, so it does not vary.
- `vbparams`/`max_activation_height` calibrated per Phase 1, held constant
  so every sample has a comparable-position signaling window.
- `consensusrules=rdts` on all Knots nodes — single axis, all Knots nodes
  always enforce, no separate consent-fraction axis.
- Scenario script: the Phase-1 minimal mining script, no partition control.

**Swept (LHS) axes:**
1. `knots_fraction` — fraction of nodes running Knots vs Core v29 (0-1).
2. `knots_hashrate_share` — fraction of block-producing weight assigned to
   Knots nodes, decoupled from `knots_fraction` the same way
   `economic_split`/`hashrate_split` are already decoupled from
   `composition_seed` in `tools/sweep/lhs_144_6param/2_build_configs.py` —
   this matters because it's specifically *who mines during the window*,
   not raw node count, that determines whether the rejection fires.

Both axes reuse the existing weighted cumulative-split node-assignment
pattern in `2_build_configs.py:259-260,348-441`
(`apply_scenario_to_base_network`), extended to assign
`{repository, tag, config}` per node instead of just `tag` — same shape of
change, new field.

**Metrics** (new, following the `contested_fork_threshold` pattern of
`reorg_depth`/`fork_balance`/`pain_score` computed from per-node tip
tracking): track per-node best-block-hash/height over the run, detect (a)
whether a Knots-vs-Core tip split occurs at all, (b) how long it persists
before one side reorgs onto the other's chain or the network fully splits
by run end. Reuse `decode_version.py` for signaling confirmation.

Sample count: default to a modest pilot-sized LHS (suggest ~50 samples) to
start — extend later once Phase 1/early Phase 2 results show whether the
parameter space needs finer sampling.

## Verification

- Phase 1: manual run, confirmed by log inspection
  (`bad-version-reduced_data` rejections) and per-node tip divergence — no
  automated pass/fail needed, this is a feasibility check.
- Phase 2: `3_run_sweep.py`-style runner per existing convention; results
  analyzed via the new tip-divergence metrics script; sanity-check a handful
  of individual scenario logs against the aggregate metrics before trusting
  the full sweep output.

## Prerequisites checklist

- [x] Build `bitcoin-knots:29.4-local` per `docs/building_knots_image.md` ✅
- [x] `warnet` CLI + venv available ✅
- [x] Docker + minikube working ✅
- [ ] Validate fork trigger (Option A or B above) before Phase 2.

## Open items

- Which fork trigger to use for Phase 2: Option A (RDTS transaction injection)
  or Option B (different Knots `consensusrules=` option). Option A is preferred
  because it exercises the actual RDTS rule; Option B avoids transaction crafting
  but may not test the same mechanism.
- Whether existing base network template (`networks/knots-mesh-pilot/`) is
  reused as-is or regenerated via `configurable_network_generator.py` for Phase 2.
