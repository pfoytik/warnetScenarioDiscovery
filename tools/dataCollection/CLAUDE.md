# BIP-110 Soft Fork Monitor — Claude Code Instructions

## Context

This directory contains two Python scripts for monitoring the BIP-110
(Reduced Data Temporary Softfork) live signaling event. The UASF flag day
is approximately August 9, 2026. These tools collect data to support a
Bitcoin network resilience research project using the Warnet testing framework.

**Research goal:** Capture real-world soft fork signaling data (pool
commitment split, version distribution, chain tip divergence) as ground
truth to validate a simulation framework. See the broader project at:
https://github.com/bitcoin-dev-project/warnet

---

## Files in This Directory

| File | Purpose |
|---|---|
| `bip110_monitor.py` | Main logger — polls local node + APIs, writes CSV + JSON |
| `decode_version.py` | Ad-hoc nVersion bit decoder and signaling checker |
| `economic_signal_log.py` | Manual, weighted tracker for exchange/custodian positions — the `economic_split` analog |
| `bip110_signaling_log.csv` | Time-series output (created on first run) |
| `bip110_latest.json` | Full snapshot output (created on first run) |
| `bip110_history.csv` | Per-period signal-rate trend (created by `--history`) |
| `economic_signals_log.csv` | Logged economic-side observations (created on first `add`) |

---

## Setup

### 1. Install the dependency

```bash
pip install requests
```

### 2. Configure RPC credentials

The scripts read RPC credentials from environment variables. Set them to
match your Bitcoin Core `bitcoin.conf`:

```bash
export RPC_USER=your_rpc_username
export RPC_PASSWORD=your_rpc_password
export RPC_HOST=<IP of your full node on the local network>
export RPC_PORT=8332
```

If the full node is on the same machine, `RPC_HOST` defaults to
`127.0.0.1` and can be omitted.

To make these persist across sessions, add them to `~/.bashrc` or
`~/.zshrc` and run `source ~/.profile`.

### 3. Verify RPC connectivity

```bash
curl --user "$RPC_USER:$RPC_PASSWORD" \
     --data-binary '{"jsonrpc":"1.0","id":"test","method":"getblockchaininfo","params":[]}' \
     -H 'content-type: text/plain;' \
     http://$RPC_HOST:$RPC_PORT/
```

You should see JSON with `"chain": "main"` and a current block height.
If you get a connection refused error, check that `rpcallowip` in
`bitcoin.conf` permits connections from this machine's IP.

---

## Running the Monitor

### Quick sanity check — decode specific block versions

Run this first to confirm the bit-4 detection logic matches what you observed:

```bash
python3 decode_version.py 0x23532010 0x20086000 0x2e000000 0x238f8000
```

Expected output: `0x23532010` shows `✓ BIP-110`, the others show `✗ no BIP-110`.

### Decode the last N blocks from your local node

```bash
python3 decode_version.py --rpc-recent 50
```

This is the fastest way to get a live feel for current signal rate without
running the full period scan.

### Single full snapshot

```bash
python3 bip110_monitor.py
```

This scans all blocks in the current difficulty period (up to 2,016 blocks)
via local RPC, cross-checks against `bip110monitor.com/api`, samples peer
version distribution, checks chain tips, and prints a summary.

**Note:** A full period scan makes one RPC call per block, so for a nearly
complete period this can take several minutes. Run `--fast` to skip it:

```bash
python3 bip110_monitor.py --fast
```

### Continuous polling — recommended for overnight data collection

```bash
# Poll every 10 minutes, fast mode (API data + chain tips only)
python3 bip110_monitor.py --loop 600 --fast

# Poll every 10 minutes, full local scan each time (slower but richer data)
python3 bip110_monitor.py --loop 600
```

Leave this running in a `tmux` or `screen` session. It appends one row to
`bip110_signaling_log.csv` per snapshot and overwrites `bip110_latest.json`.

### Historical trend — last N difficulty periods

```bash
python3 bip110_monitor.py --history 10
```

Headers-only scan (no pool tagging, so it's much faster than a full-period
snapshot) covering the last N difficulty periods, current partial period
included as period 0. Prints a signal-rate-by-period table and writes
`bip110_history.csv`. Useful for seeing whether the signal rate is trending
up or down heading into the flag day, not just where it stands right now.

---

## What to Watch For

### High-priority events (check immediately)

- **`fork_count > 0` in the output** — chain tips have diverged. This is
  the most important signal. Run `bitcoin-cli getchaintips` on the local
  node to get details. Record the height, hash, and `branchlen` of any
  `valid-fork` entries.

- **Signal rate crosses 55%** — lock-in threshold met. The difficulty
  period is 2,016 blocks (~2 weeks), so the per-snapshot signal percentage
  tells you where you are relative to the threshold.

- **Signal rate drops suddenly** — a pool that was signaling stopped.
  Cross-reference with the pool breakdown in the output.

### Secondary signals to log manually

- Any exchange or custodian announcements about BIP-110 support or
  opposition — these are your `economic_split` analog. Log them with
  `economic_signal_log.py` (see below) rather than as free-form notes, so
  they produce a weighted number comparable to the paper's thresholds
  instead of an unstructured impression.
- Pool public statements about signaling or not signaling.
- Any Bitcoin Core developer responses.

### Logging economic-side signals

`bip110_monitor.py` has no way to observe exchange/custodian positions —
there's no API for it. `economic_signal_log.py` is the structured, manual
counterpart: each observation gets a rough 1–5 size-weight tier and a
stance, collapsed to each entity's *latest* position (so a stance change
doesn't get double-counted) and rolled up into an estimated `economic_split`.

```bash
python3 economic_signal_log.py add --entity "Coinbase" --type exchange \
    --weight 5 --stance oppose --source "https://..." --notes "..."

python3 economic_signal_log.py list       # current stance per entity
python3 economic_signal_log.py summary    # weighted economic_split estimate
```

`summary` reports two numbers: an "active" split (support weight over
support+oppose weight only) and a "conservative" split (support weight over
*all* tracked weight, treating silence as not-yet-v27 — since unclaimed
custody stays on the incumbent chain by default). The conservative number
is the closer analog to the simulation's `economic_split`, since the model
doesn't have an "undecided" state either.

---

## Output Files

### `bip110_signaling_log.csv`

One row per snapshot. Columns:

| Column | Description |
|---|---|
| `timestamp` | UTC ISO timestamp |
| `height` | Current block height |
| `period_start` | Height of current difficulty period start |
| `blocks_in_period` | Blocks mined so far this period |
| `signaling` | Count of signaling blocks this period |
| `signal_pct` | Percentage signaling |
| `above_threshold` | True/False (threshold = 55%) |
| `fork_count` | Number of valid-fork chain tips detected |
| `peer_count` | Number of connected peers sampled |
| `ext_api_signal_pct` | Signal rate from bip110monitor.com API |

### `bip110_latest.json`

Full nested snapshot. Contains pool-level breakdown, per-peer version
distribution, full chain tip list, and `getblockchaininfo` softfork state.
Useful for post-hoc analysis.

---

## Mapping Collected Data to the Research Model

| Collected metric | Research parameter |
|---|---|
| `signal_pct` (by pool) | `pool_committed_split` |
| `economic_signal_log.py summary` output | `economic_split` |
| `fork_count > 0` | Fork detection event (100-pt criticality score) |
| Peer `subver` distribution | Version mix input variable |
| Chain tip `branchlen` | Reorg depth metric |

The primary research question is whether the live `pool_committed_split`
and estimated `economic_split` land inside or outside the inversion zone
(economic split roughly 0.50–0.82). If they're in the inversion zone,
pool commitment becomes the decisive factor — watch the Foundry USA and
Antpool coinbase tags closely.

---

## Troubleshooting

**`Connection refused` on RPC call**
- Check `RPC_HOST` is correct for your network topology
- Verify `rpcallowip=<this machine's IP>` is in `bitcoin.conf`
- Confirm bitcoind is running: `bitcoin-cli getnetworkinfo`

**`401 Unauthorized`**
- `RPC_USER` or `RPC_PASSWORD` env vars don't match `bitcoin.conf`
- If using cookie auth, set `RPC_USER` to the cookie file content

**Full period scan is very slow**
- Use `--fast` flag; it skips block-by-block RPC and uses the external API
- Alternatively, only run full scan once per difficulty period and poll
  with `--fast` in between

**Pool tags showing `unknown`**
- The coinbase pool-tag scan requires `getblock` with verbosity 2 (full tx)
  which is slow. Most blocks will show `unknown` unless the pool embeds a
  recognizable ASCII string in the coinbase. This is best-effort.
- For authoritative pool identification, cross-reference block heights
  against mempool.space's pool labels manually.

**bip110monitor.com API unavailable**
- The script continues normally without it; local node data is primary.
- Try https://mempool.space/api/v1/blocks as an alternative — the
  `decode_version.py` bit-check logic works on any block's `version` field.

---

## Quick Reference: BIP-110 Signal Detection Logic

```python
BIP9_TOP_MASK = 0xE0000000
BIP9_TOP_BITS = 0x20000000
BIP110_BIT    = 4  # → 0x10

def is_signaling(nversion):
    is_bip9 = (nversion & BIP9_TOP_MASK) == BIP9_TOP_BITS
    bit_set  = bool(nversion & (1 << BIP110_BIT))
    return is_bip9 and bit_set
```

`0x23532010 & 0x10 = 0x10` → **signaling**
`0x20086000 & 0x10 = 0x00` → **not signaling**
