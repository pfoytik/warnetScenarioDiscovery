# Knots in-place RDTS switch test

Small Docker-only test (3 regtest containers, no Kubernetes), safe to run on a
workstation. It verifies that a Knots node can switch between RDTS-enforcing
and Core-compatible in place. See `docs/knots_mesh_fork_sweep_plan.md`,
"In-place node switching".

Requires the `bitcoin-knots:29.4-local` image and `alpine`.

    bash phase0.sh   # start A (rdts), B (core mode, switcher), C (core mode)
    bash phase1.sh   # shared history, C mines a violating block, A rejects
    bash phase2.sh   # switch B -> rdts in place, invalidateblock, verify
    source lib.sh && cleanup

phase1 and phase2 write state files (`violating_block*`) next to the scripts.
The fresh-violating-block check and the switch back to core mode
(`reconsiderblock`) were run by hand. See the plan doc for the steps and results.

## Scenario harness (Step 2)

`scenario_harness.py` runs `knots_mesh_pilot.py`'s real `--inplace-switching`
methods (classification, held injection, `_mine_block`,
`reconcile_node_modes` / `switch_nodes_inplace`) against the same 3
containers. `docker exec` stands in for pod exec, and Docker's
`--restart always` stands in for `restartPolicy: Always`.

    bash phase0.sh
    /home/pfoytik/bitcoinTools/warnet/warnet/.venv/bin/python3 scenario_harness.py
    source lib.sh && cleanup

Peers are set with `addnode=` in each node's conf, as warnet does, so they
survive the switch restarts.

## Violation rate + outcomes harness

`violation_harness.py` (same containers) checks `--violation-rate`:
- 0.0: no split;
- 1.0: a violation in every Core block;
- after a wipe-out, pending violations are re-included;
- an in-place switch into RDTS invalidates multiple violating blocks;
- `compute_outcomes` (blocks mined/orphaned per pool, value change, time on
  each fork, regret).

    bash phase0.sh
    /home/pfoytik/bitcoinTools/warnet/warnet/.venv/bin/python3 violation_harness.py
    source lib.sh && cleanup
