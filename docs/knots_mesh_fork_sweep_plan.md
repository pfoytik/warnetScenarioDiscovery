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

Do not proceed to Phase 1b until one of these alternatives is validated.

## Phase 1b — Validate fork trigger (NOT YET STARTED)

Goal: confirm that a Knots-vs-Core consensus split actually occurs in the
pilot network before committing to sweep infrastructure.

1. Extend `scenarios/knots_mesh_pilot.py` to inject RDTS-violating
   transactions after the deployment reaches `ACTIVE` (Option A):
   - From Core node wallets, craft and broadcast transactions with OP_RETURN
     outputs > 80 bytes (e.g., `OP_RETURN <81-byte payload>`).
   - Have Core nodes mine blocks that include those transactions.
   - Poll per-node tip hashes; confirm Knots tips diverge from Core tips.
   - Confirm `bad-version-reduced_data` (or equivalent rejection error)
     appears in Knots debug logs.
2. Use the same `networks/knots-mesh-pilot/` network and `knots-pilot`
   namespace — no new infrastructure needed for this step.

Do not proceed to Phase 1c until tip divergence is observed.

## Phase 1c — Verify split behavior (NOT YET STARTED)

Goal: confirm the network behaves correctly *after* the fork fires — not
just that it fires once.

1. **Knots tip stability**: after rejecting a Core block, does the Knots camp
   hold its own tip and continue mining its chain independently? Confirm the
   Knots chain grows while the Core chain grows separately.
2. **Core tip stability**: Core nodes accept all blocks (theirs and Knots'), so
   they should follow the longest chain. Confirm Core nodes don't reorg onto
   the Knots chain if the Knots chain is shorter.
3. **Async propagation**: with round-robin mining, blocks arrive at all peers
   asynchronously. Confirm that a Knots-rejected Core block does not cause
   Knots nodes to stall, disconnect peers, or log unexpected errors beyond the
   expected rejection message.
4. **Chain length divergence**: mine enough blocks past `ACTIVE` that both
   camps accumulate 20+ blocks on their respective chains. Confirm the split
   is stable (not a transient reorg artifact).

Do not proceed to Phase 2 until all four are observed cleanly.

## Phase 2 — LHS sweep

**All sweep infrastructure for this phase needs to be written from scratch.**
Nothing in `tools/sweep/` currently supports Knots mesh experiments. The
existing scripts (`3_run_sweep.py`, `2_build_configs.py`, etc.) drive
`scenarios/partition_miner_with_pools.py` with a completely different result
schema — they must not be modified. All new code goes in a self-contained
directory: `tools/sweep/knots_mesh_fork/`.

### Backwards compatibility requirement

The Knots mesh sweep infrastructure must be **strictly additive**. Prior sweep
results must remain fully reproducible without any changes to existing code:

- `scenarios/partition_miner_with_pools.py` — do not touch
- `tools/sweep/1_generate_*.py`, `2_build_configs.py`, `3_run_sweep.py`,
  `4_analyze_results.py`, `5_build_database.py` — do not touch
- `networkGen/configurable_network_generator.py` — additive only (new
  flags/options must be backward-compatible; existing defaults unchanged)
- All existing network YAML templates — do not modify

Any Knots node support added to the network generator must be opt-in (e.g.,
a new `--knots-fraction` flag that defaults to 0, leaving existing behavior
unchanged). Running the old pipeline on old network configs must produce
identical results.

### New sweep directory: `tools/sweep/knots_mesh_fork/`

Follows the `spec.yaml` + `RUN_INSTRUCTIONS.md` convention used by
`chainsplit_persistence`/`contested_fork_threshold`. Files to write:

- `spec.yaml` — LHS parameter bounds
- `1_generate_lhs.py` — generate LHS sample set
- `2_build_configs.py` — build per-scenario network YAMLs with Knots/Core
  node assignment
- `3_run_sweep.py` — drive the new scenario script, collect results
- `4_analyze_results.py` — parse tip-divergence metrics, produce outputs
- `RUN_INSTRUCTIONS.md`

### Fixed (not swept), same for every sample

- Topology: full mesh (`addnode` list = all other nodes), no partition control.
- `vbparams`/`max_activation_height` held constant (calibrated in Phase 1b).
- `consensusrules=rdts` on all Knots nodes — all enforce, no consent-fraction axis.
- Scenario script: extended `knots_mesh_pilot.py` with RDTS tx injection.

### Swept (LHS) axes

1. `knots_fraction` — fraction of nodes running Knots vs Core v29 (0–1).
2. `knots_hashrate_share` — fraction of block-producing weight assigned to
   Knots nodes, decoupled from node count (mirrors the `economic_split` /
   `hashrate_split` decoupling in existing sweeps).

Node assignment follows the weighted cumulative-split pattern in existing
`2_build_configs.py`, extended to set `{repository, tag, config}` per node.

### Result schema (new — does not conflict with existing schema)

Per-scenario output in `results/<scenario_id>/`:
- `tip_series.json` — per-node `{height, hash, timestamp}` at each poll
- `divergence_events.json` — list of `{block, knots_tips, core_tips}` records
- `metadata.json` — scenario parameters
- `summary.json` — `{fork_occurred, first_divergence_block, final_knots_height,
  final_core_height, split_duration_blocks}`

### Metrics

Track per-node best-block-hash/height over the run:
- (a) whether a Knots-vs-Core tip split occurs at all
- (b) which block height it first appears
- (c) how long it persists / whether it resolves before run end

Sample count: ~50 samples to start; extend once Phase 1b/1c show the parameter
space is well-behaved.

## Verification

- Phase 1: manual run, confirmed by log inspection
  (`bad-version-reduced_data` rejections) and per-node tip divergence — no
  automated pass/fail needed, this is a feasibility check.
- Phase 2: `3_run_sweep.py`-style runner per existing convention; results
  analyzed via the new tip-divergence metrics script; sanity-check a handful
  of individual scenario logs against the aggregate metrics before trusting
  the full sweep output.

## Prerequisites checklist

### Phase 1b gate (fork trigger validation)
- [x] Build `bitcoin-knots:29.4-local` per `docs/building_knots_image.md` ✅
- [x] `warnet` CLI + venv available ✅
- [x] Docker + minikube working ✅
- [x] vbparams syntax verified empirically ✅
- [ ] RDTS tx injection implemented in `knots_mesh_pilot.py`
- [ ] Live tip divergence observed between Knots and Core camps
- [ ] `bad-version-reduced_data` (or equivalent) confirmed in Knots debug logs

### Phase 1c gate (split behavior validation)
- [ ] Knots camp holds stable tip after rejecting Core block
- [ ] Core camp follows longest chain independently
- [ ] No unexpected peer disconnects or stalls under async propagation
- [ ] Both camps accumulate 20+ blocks on their own chains stably

### Phase 2 gate (sweep infrastructure)
- [ ] `tools/sweep/knots_mesh_fork/` directory and all scripts written
- [ ] `2_build_configs.py` implements `knots_fraction` + `knots_hashrate_share` axes
- [ ] Network generator changes are additive (old pipelines unaffected)
- [ ] Result schema defined and `4_analyze_results.py` written
- [ ] Backwards compatibility verified: existing sweep pipeline produces same
      results on old network configs after any generator changes

## Open items

- Which fork trigger to use for Phase 1b: Option A (RDTS tx injection) is
  preferred — exercises the actual RDTS rule; Option B (different
  `consensusrules=` flag) is a fallback if Option A proves unreliable.
- Whether `networks/knots-mesh-pilot/` is reused as-is for Phase 2 or
  regenerated via `configurable_network_generator.py` (preferred if the
  generator gets Knots support, for consistency with sweep tooling).
