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
