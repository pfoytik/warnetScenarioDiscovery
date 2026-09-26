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
- **Status:** proposed.

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
- **Status:** proposed.

---

## Not warnet changes (network/scenario config in this repo)
- `restartPolicy: Always` for tanks: already a chart value
  (`values.yaml: restartPolicy: Never`). Set it in the network's
  `node-defaults.yaml`. Needed so an RPC `stop` during a switch restarts
  bitcoind in the same pod, keeping the `emptyDir` chain data.
- `includeconf=switch.conf` in each node's `config:` string. Verified to
  work from inside the `[regtest]` section that warnet generates.
