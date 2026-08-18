# Knots-vs-Core Mesh Fork LHS Sweep — Design Doc

Status: **designed, not yet implemented**. Written to be picked up on
another (larger) machine. Depends on `docs/building_knots_image.md`
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

## Mechanism (verified against `bitcoinknots/bitcoin` source)

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
- In the one-period window immediately before `max_activation_height`, any
  block **without** version-bit 4 set is **rejected live** by enforcing
  nodes, via `ContextualCheckBlockHeader` (`validation.cpp:4681`, error
  `bad-version-<deployment>`) — not just a startup rescan, a live rejection
  as blocks are relayed and connected.
- Knots' `reduced_data` deployment has `gbt_force = true`
  (`deploymentinfo.cpp`), so any Knots node automatically signals bit 4 on
  blocks it mines once `STARTED` — zero scenario-script involvement needed.
  Core v29 nodes have no knowledge of this deployment and never signal it.

**Net effect:** whichever camp mines a block during that one-period window
determines whether a live, protocol-level rejection (and thus a fork)
happens — purely from ordinary mining + block relay on a mesh topology. No
custom "oversized data" transaction injection is needed (there's a second,
weaker enforcement surface — a coinbase/generation-tx size limit that
applies after full `ACTIVE` state — but the mandatory-signaling window alone
is sufficient, deterministic, and needs no crafted transactions, so the plan
relies on it exclusively). This also means a separate "consent" axis (some
Knots nodes opting out of enforcement) isn't needed for a first sweep — all
Knots nodes always enforce; the real causal lever is *which nodes mine
during the window*, i.e. composition.

This mechanism has been verified by reading source only — **never run
end-to-end in a live warnet network.** Phase 1 below exists specifically to
confirm it actually behaves this way under real P2P timing/relay before
committing compute to a full LHS sweep.

## Phase 1 — Pilot (manual, not part of the LHS)

Goal: confirm the mandatory-signaling rejection actually fires in a live
warnet regtest network before spending compute on a full sweep.

1. **Network config**: small fixed network (~8-10 tanks), full mesh
   (`addnode` list = all other tanks — matches the `full_economic_mesh`
   default already implemented in
   `networkGen/configurable_network_generator.py:243-273`; reuse that
   generator rather than hand-writing `addnode` lists). Split roughly half
   Knots (`repository: bitcoin-knots`, `tag: '29.4-local'`, `config`
   including `consensusrules=rdts` and a `vbparams=reduced_data:...` line),
   half Core v29 (`repository: bitcoindevproject/bitcoin`, `tag: '29.0'`,
   unmodified).
2. **vbparams calibration**: choose `min_activation_height=0`,
   `nStartTime=0` (immediately eligible), and `max_activation_height` small
   enough that the mandatory-signaling window
   (`[max_activation_height-288, max_activation_height-144)`) falls inside
   however many blocks the pilot scenario mines (e.g.
   `max_activation_height=300` if mining ~400 blocks). Exact
   `-vbparams=` syntax to confirm against Knots'
   `chainparamsbase.cpp`/`init.cpp` arg parsing when implementing (deployment
   key confirmed as `reduced_data` in `src/deploymentinfo.cpp`).
3. **Scenario script**: new minimal script — do **not** reuse
   `scenarios/partition_miner_with_pools.py`, since its
   `switch_node_partition`/`reunite_forks`/`v26_acceptance_probability`
   logic is exactly the artificial control this test is meant to exclude.
   Just round-robin or random block generation across all mining nodes,
   letting normal P2P relay/reorg logic run with zero manual peer
   manipulation. Small mining/RPC helper functions may be borrowed from the
   existing script, but its partition-control functions must not be called.
4. **Verify**: watch per-node `getbestblockhash`/`getblockcount` diverge
   when a Core-mined block lands in the signaling window and gets rejected
   by Knots nodes (should show up in Knots node debug logs as
   `bad-version-reduced_data`, and as a tip-hash split between the two
   camps). Use `tools/dataCollection/decode_version.py` (already tracks bit
   4 signaling) to confirm which blocks did/didn't signal.

Do not proceed to Phase 2 until this is observed working.

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

## Prerequisites checklist (for the other machine)

- [ ] Build `bitcoin-knots:29.4-local` per `docs/building_knots_image.md`
      (or push it to a registry from this machine and just `docker pull` on
      the target machine, if same-arch — see that doc's "moving the image"
      section).
- [ ] `warnet` CLI + venv available.
- [ ] Docker + `docker buildx` if rebuilding the image there.

## Open items to confirm during implementation (not blocking this doc)

- Exact `-vbparams=` CLI/config string syntax and block-count budget for the
  pilot (first empirical step of Phase 1 itself).
- Whether existing base network templates (e.g.
  `networks/realistic-economy-lite/network.yaml`, used by `lhs_144_6param`)
  are suitable as the mesh base after topology override, or a fresh
  mesh-native template is cleaner to start from.
