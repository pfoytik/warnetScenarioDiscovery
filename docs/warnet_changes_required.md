# Changes Required in Warnet

Warnet (`/home/pfoytik/bitcoinTools/warnet/warnet`, fork `github.com/pfoytik/warnet`)
is a separate open-source project. This file lists every change this research
needs *in warnet itself*, so each can be applied to every install (local and
server) and possibly proposed upstream. Changes that only need network YAML
or scenario code in this repo are listed at the bottom for contrast. They are
**not** warnet changes.

Status key: **applied-local** = edited in the local warnet checkout, not
committed; **proposed** = designed, not yet made; **server?** = unknown
whether the server install has it.

## Applying on another install (e.g. the server)
All of W1–W3 are in **`docs/warnet_changes.patch`**, a `git diff` taken
against warnet commit `956ee67`. In the server's warnet checkout:
```bash
git apply --check /path/to/warnetScenarioDiscovery/docs/warnet_changes.patch  # dry run
git apply /path/to/warnetScenarioDiscovery/docs/warnet_changes.patch
```
If W1 is already present there (see below), `--check` reports a conflict in
`control.py`. Apply the rest with
`git apply --exclude=src/warnet/control.py ...`. The chart changes take effect
on the next `warnet deploy` (tanks) and `warnet run` (commander RBAC). An
editable install (`pip install -e`) needs no reinstall.

---

## W1. Scenario archive bundles `lib/` and `config/`
- **File:** `src/warnet/control.py`, `_run()` archive filter (~line 364).
- **Change:** add `"lib/"` and `"config/"` to the list of paths bundled into
  the commander `.pyz`. `zipapp` passes paths relative to the source root,
  so they have **no leading slash**. A first attempt with `"/lib/"` silently
  matched nothing.
- **Why:** `knots_mesh_pilot.py` imports `lib/*` (oracles) and loads
  `config/*.yaml` via `pkgutil`. Without this the commander pod crashes on
  import.
- **Status:** applied-local (2026-09-22, uncommitted in the warnet repo; the
  same edit was made to the untracked `scenDiscovery_control.py` copy).
  **server?** The server's successful runs suggest it has an equivalent fix.
  Confirm.

## W2. Commander RBAC: allow `pods/exec`
- **File:** `resources/charts/commander/templates/rbac.yaml`.
- **Change:** add a rule
  ```yaml
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create", "get"]
  ```
- **Why:** (1) `check_rdts_rejection()` self-confirms the rejection by
  grepping a Knots node's `debug.log`. Currently this fails and the scenario
  falls back to `getchaintips` only (known gap since 2026-09-23). (2) **Needed
  by in-place node switching:** the scenario must write each node's
  `switch.conf` in its data directory before restarting it.
- **Status:** applied-local (2026-09-26). Verified with `helm template`
  (rule renders). Not yet exercised in a cluster. **server?** no.

## W3. Optional init container hook in the bitcoincore chart (`extraInitContainers`)
- **Files:** `resources/charts/bitcoincore/templates/pod.yaml`, `values.yaml`.
- **Change:** add an optional `extraInitContainers: []` value rendered under
  `initContainers:`. This mirrors the chart's existing `extraContainers` hook,
  and must coexist with the `loadSnapshot` init container.
- **Why:** in-place switching uses `includeconf=switch.conf` (a file in the
  writable data directory). bitcoind **refuses to start if an included file
  is missing** (verified: `Failed to include configuration file switch.conf`).
  The file must exist before bitcoind's first boot, and nothing in the chart
  can create it today. The network YAML would then add an init container that
  writes the node's starting-camp `switch.conf` into the `data` volume.
- **Alternatives considered:**
  - A sidecar via the existing `extraContainers`: races bitcoind's first start.
  - Patching the Knots image entrypoint: also lives in warnet's
    `resources/images/`.
  - A ConfigMap mounted without `subPath`: kubelet sync delay of up to ~60s
    per switch, plus RBAC to patch ConfigMaps.
- **Implemented as:** `initContainers:` now renders when `loadSnapshot.enabled`
  **or** `extraInitContainers` is set. `download-blocks` comes first, then the
  extra containers. `values.yaml` documents the value (default `[]`).
- **Status:** applied-local (2026-09-26). Verified with `helm template`:
  - default values → no `initContainers` (unchanged);
  - `loadSnapshot` only → `download-blocks` as before;
  - a `networks/knots-mesh-inplace` node → the seed container renders.

  The rendered init command and `bitcoin.conf` were also run in Docker: the
  node booted with RDTS active. **server?** no.

---

## Not warnet changes (network/scenario config in this repo)
- `restartPolicy: Always` for tanks: already a chart value
  (`values.yaml: restartPolicy: Never`). Set it in the network's
  `node-defaults.yaml`. Needed so an RPC `stop` during a switch restarts
  bitcoind in the same pod, keeping the `emptyDir` chain data.
- `includeconf=switch.conf` in each node's `config:` string. Verified to
  work from inside the `[regtest]` section that warnet generates.
