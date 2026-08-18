# Building the Bitcoin Knots warnet image on another machine

Reproduces the local `bitcoin-knots:29.4-local` image built from
[bitcoinknots/bitcoin](https://github.com/bitcoinknots/bitcoin) for use as a
warnet tank image. The build is pinned to a specific commit, so it's fully
reproducible on any machine with the prerequisites below.

## Prerequisites

- Docker, with the `docker buildx` plugin installed
  (Ubuntu/Debian: `sudo apt install docker-buildx`)
- The `warnet` CLI available, e.g. via its venv:
  `/path/to/warnet/.venv/bin/warnet`
  (this doc assumes a sibling checkout of the
  [warnet](https://github.com/bitcoin-dev-project/warnet) source repo)

## Build command

```bash
warnet image build \
  --repo bitcoinknots/bitcoin \
  --commit-sha dd729e0d743042d925955ae07f10043762a8e979 \
  --tags bitcoin-knots:29.4-local \
  --build-args "-DBUILD_TESTS=OFF -DBUILD_GUI=OFF -DBUILD_BENCH=OFF -DBUILD_UTIL=ON -DBUILD_FUZZ_BINARY=OFF -DWITH_ZMQ=ON -DRDTS_CONSENT=RUNTIME_CHECK" \
  --action load
```

- `--commit-sha` is the commit for tag `v29.4.knots20260508`. Swap in a
  different Knots commit/tag to build another version.
- `--action load` loads the image into the local Docker daemon only. Use
  `--action push --arches amd64,arm64` instead to publish a multi-arch image
  to a registry (needed if tanks run in a remote/different-arch cluster
  rather than local Docker).

This runs a full C++ compile via `docker buildx` (CPU-bound, roughly a few
minutes depending on the machine).

## The RDTS_CONSENT gate

Bitcoin Knots 29.x+ implements the BIP-110 (RDTS) network upgrade, and its
CMake configure step **hard-fails** unless `-DRDTS_CONSENT=<mode>` is passed:

| Mode | Behavior |
|---|---|
| `IMPLICIT` | Bakes in acceptance of the upgrade. No runtime toggle. |
| `RUNTIME_CHECK` | Compiles either way. Exposes a `-consensusrules=rdts` bitcoind flag. On regtest, the node starts fine without it (the check is activation-gated, not enforced at startup) — set `consensusrules=rdts` per-tank to model an "accepting" node vs. leaving it unset for a "rejecting" node, using the *same* image. |
| `RUNTIME_WARN` | Runs regardless of the flag; logs an hourly warning if it's absent. |

The build command above uses `RUNTIME_CHECK` so a single image can model
mixed accept/reject node populations.

## Verifying the build

```bash
docker images bitcoin-knots
docker run --rm bitcoin-knots:29.4-local bitcoind -version
```

Expect: `Bitcoin Knots daemon version v29.4.0.knots20260508`.

## Referencing it in a network config

The default `repository: bitcoindevproject/bitcoin` in `node-defaults.yaml`
does not apply to this image, so override both fields per node:

```yaml
- name: tank-000X
  image:
    repository: bitcoin-knots
    tag: '29.4-local'
  # to model a node that explicitly accepts the RDTS/BIP-110 upgrade:
  # config: 'consensusrules=rdts'
```

## Moving the image without rebuilding

If the other machine is the same CPU architecture, you can skip a rebuild
entirely by exporting the image directly:

```bash
# on the machine that already built it:
docker save bitcoin-knots:29.4-local | gzip > bitcoin-knots-29.4-local.tar.gz
# copy the file over, then on the target machine:
gunzip -c bitcoin-knots-29.4-local.tar.gz | docker load
```

This only works for matching architectures. For a different architecture
(e.g. ARM), rebuild there instead, or push a multi-arch image to a registry
(see `--action push` above).

## Compatibility notes (verified against this commit)

- Both of warnet's carry-patches apply cleanly against this Knots commit
  (`isroutable.patch` on `src/netaddress.cpp`, `addrman.patch` on
  `src/netgroup.cpp` / `src/test/addrman_tests.cpp`), with only line-offset
  shifts, no conflicts.
- The `sed s:sys/fcntl.h:fcntl.h:` compat step in the Dockerfile is a no-op
  on this commit — Knots already includes `<fcntl.h>` directly.
- All six default CMake build flags warnet passes
  (`BUILD_TESTS`, `BUILD_GUI`, `BUILD_BENCH`, `BUILD_UTIL`,
  `BUILD_FUZZ_BINARY`, `WITH_ZMQ`) exist verbatim in Knots' `CMakeLists.txt`.
