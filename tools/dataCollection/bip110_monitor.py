#!/usr/bin/env python3
"""
BIP-110 Soft Fork Monitor
=========================
Collects signaling data for the BIP-110 (Reduced Data Temporary Softfork)
from your local Bitcoin Core node and public APIs.

BIP-110 uses version bit 4 (0x10) with BIP9 prefix (top 3 bits = 001).
Signaling blocks have nVersion & 0x10 set AND (nVersion & 0xE0000000) == 0x20000000.
Threshold: 55% of 2,016 blocks in a difficulty period.
Flag day: ~August 9, 2026.

Usage:
    python3 bip110_monitor.py               # Single snapshot
    python3 bip110_monitor.py --loop 600    # Poll every 600 seconds
    python3 bip110_monitor.py --history 10  # Fetch last N difficulty periods
"""

import argparse
import csv
import json
import os
import subprocess
import time
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    raise

# ── Configuration ────────────────────────────────────────────────────────────

RPC_USER     = os.environ.get("RPC_USER", "bitcoin")
RPC_PASSWORD = os.environ.get("RPC_PASSWORD", "password")
RPC_HOST     = os.environ.get("RPC_HOST", "127.0.0.1")
RPC_PORT     = int(os.environ.get("RPC_PORT", "8332"))

BIP9_TOP_MASK = 0xE0000000
BIP9_TOP_BITS = 0x20000000
BIP110_BIT    = 4              # bit 4 → 0x10
PERIOD_SIZE   = 2016
THRESHOLD_PCT = 55.0           # BIP-110 uses 55%, not 95%

OUTPUT_CSV  = "bip110_signaling_log.csv"
OUTPUT_JSON = "bip110_latest.json"

# ── RPC helpers ───────────────────────────────────────────────────────────────

def rpc(method, params=None):
    payload = {
        "jsonrpc": "1.0",
        "id": "bip110_monitor",
        "method": method,
        "params": params or [],
    }
    resp = requests.post(
        f"http://{RPC_HOST}:{RPC_PORT}/",
        auth=(RPC_USER, RPC_PASSWORD),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"RPC error: {data['error']}")
    return data["result"]


def is_bip9(nversion):
    return (nversion & BIP9_TOP_MASK) == BIP9_TOP_BITS


def is_signaling(nversion):
    return is_bip9(nversion) and bool(nversion & (1 << BIP110_BIT))


# ── Core analysis ─────────────────────────────────────────────────────────────

def get_current_period_info():
    """Return start height and block count of the current difficulty period."""
    tip_hash = rpc("getbestblockhash")
    tip      = rpc("getblock", [tip_hash])
    height   = tip["height"]
    period_start = (height // PERIOD_SIZE) * PERIOD_SIZE
    blocks_in_period = height - period_start + 1
    return period_start, blocks_in_period, height, tip_hash


def scan_period_from_node(period_start, num_blocks):
    """
    Scan `num_blocks` blocks starting at `period_start` via local RPC.
    Returns per-block records: height, version (hex+int), signaling, pool tag.
    """
    records = []
    print(f"  Scanning {num_blocks} blocks from height {period_start} via local node...")

    # Use REST batch header endpoint for speed when available;
    # fall back to individual getblockheader calls.
    for i in range(num_blocks):
        h = period_start + i
        bh = rpc("getblockhash", [h])
        blk = rpc("getblockheader", [bh, True])  # verbose=True

        nversion = blk["version"]
        signaling = is_signaling(nversion)

        # Identify pool via coinbase (best effort — requires getblock, slower)
        pool_tag = "unknown"
        try:
            full = rpc("getblock", [bh, 2])  # verbosity 2 = full tx
            coinbase_hex = full["tx"][0].get("hex", "")
            # Common pool tags embedded in coinbase ASCII
            for tag, pool in POOL_TAGS.items():
                if tag.encode().hex() in coinbase_hex:
                    pool_tag = pool
                    break
        except Exception:
            pass

        records.append({
            "height":    h,
            "hash":      bh,
            "version":   hex(nversion),
            "version_int": nversion,
            "signaling": signaling,
            "pool":      pool_tag,
            "timestamp": blk.get("time"),
        })

        if (i + 1) % 100 == 0:
            pct = sum(r["signaling"] for r in records) / len(records) * 100
            print(f"    ...{i+1}/{num_blocks} scanned  ({pct:.1f}% signaling so far)")

    return records


def scan_period_headers_only(period_start, num_blocks):
    """
    Lightweight period scan for --history: signal bit only, no pool tagging.
    Walks forward via `nextblockhash` so it costs 1 + num_blocks RPC calls
    instead of the ~3x per block that the full scan (with pool tags) makes.
    """
    records = []
    bh = rpc("getblockhash", [period_start])
    for i in range(num_blocks):
        blk = rpc("getblockheader", [bh, True])
        nversion = blk["version"]
        records.append({
            "height":    blk["height"],
            "version":   hex(nversion),
            "signaling": is_signaling(nversion),
            "timestamp": blk.get("time"),
        })
        bh = blk.get("nextblockhash")
        if not bh:
            break
        if (i + 1) % 500 == 0:
            print(f"    ...{i+1}/{num_blocks} blocks scanned")
    return records


def scan_history(n_periods):
    """
    Scan the last `n_periods` difficulty periods (current partial period
    counts as period 0) and return a per-period signal-rate summary.
    Headers-only — no pool breakdown, kept fast enough to run on demand.
    """
    period_start_cur, blocks_in_period, current_height, _ = get_current_period_info()

    results = []
    for k in range(n_periods):
        p_start = period_start_cur - PERIOD_SIZE * k
        if p_start < 0:
            print(f"  Stopping at period {k}: would scan below genesis.")
            break

        num_blocks = blocks_in_period if k == 0 else PERIOD_SIZE
        label = "current (partial)" if k == 0 else f"-{k}"
        print(f"  Scanning period {label}: start height {p_start}, {num_blocks} blocks...")

        recs = scan_period_headers_only(p_start, num_blocks)
        total = len(recs)
        signaling = sum(1 for r in recs if r["signaling"])
        pct = signaling / total * 100 if total else 0.0

        results.append({
            "period_index":        k,
            "period_start_height": p_start,
            "period_end_height":   p_start + total - 1,
            "blocks_scanned":      total,
            "signaling_blocks":    signaling,
            "signal_pct":          round(pct, 4),
            "above_threshold":     pct >= THRESHOLD_PCT,
            "is_current_period":   k == 0,
        })

    return results


def print_history(results):
    print(f"\n{'='*72}")
    print(f"BIP-110 Signal Rate — Last {len(results)} Difficulty Periods")
    print(f"{'='*72}")
    print(f"{'Period':>10}  {'Start':>10}  {'End':>10}  {'Blocks':>7}  {'Signal%':>8}  {'>=Thr?'}")
    print("-" * 72)
    for r in results:
        label = "current" if r["is_current_period"] else f"-{r['period_index']}"
        thr = "YES" if r["above_threshold"] else "no"
        print(f"{label:>10}  {r['period_start_height']:>10}  {r['period_end_height']:>10}  "
              f"{r['blocks_scanned']:>7}  {r['signal_pct']:>7.2f}%  {thr}")
    print(f"{'='*72}\n")


def save_history_csv(results, path="bip110_history.csv"):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()) if results else [])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"  Saved trend data to {path}")


# Known pool coinbase tag strings (hex substrings to search in coinbase)
POOL_TAGS = {
    "Foundry USA": "Foundry USA",
    "AntPool":     "AntPool",
    "ViaBTC":      "ViaBTC",
    "F2Pool":      "F2Pool",
    "Binance Pool": "Binance",
    "MARA Pool":   "MARA",
    "Luxor":       "Luxor",
    "SpiderPool":  "SpiderPool",
    "Braiins":     "Braiins",
    "BTC.com":     "BTC.com",
}


def compute_summary(records):
    total     = len(records)
    signaling = sum(1 for r in records if r["signaling"])
    pct       = signaling / total * 100 if total else 0

    pool_stats = {}
    for r in records:
        p = r["pool"]
        if p not in pool_stats:
            pool_stats[p] = {"total": 0, "signaling": 0}
        pool_stats[p]["total"] += 1
        if r["signaling"]:
            pool_stats[p]["signaling"] += 1

    return {
        "total_blocks":     total,
        "signaling_blocks": signaling,
        "non_signaling":    total - signaling,
        "signal_pct":       round(pct, 4),
        "threshold_pct":    THRESHOLD_PCT,
        "above_threshold":  pct >= THRESHOLD_PCT,
        "blocks_remaining_in_period": PERIOD_SIZE - total,
        "pool_breakdown":   pool_stats,
    }


# ── Public API fallback ───────────────────────────────────────────────────────

def fetch_bip110_monitor_api():
    """Pull current data from bip110monitor.com public JSON API."""
    try:
        resp = requests.get("https://bip110monitor.com/api", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [warn] bip110monitor.com API unavailable: {e}")
        return None


def fetch_mempool_blocks(n=2016):
    """
    Fetch recent blocks from mempool.space and compute signaling.
    Useful as a cross-check against local node.
    """
    print(f"  Fetching {n} recent blocks from mempool.space...")
    blocks = []
    url = "https://mempool.space/api/v1/blocks"
    last_seen_height = None

    while len(blocks) < n:
        params = {}
        if last_seen_height is not None:
            params["start_height"] = last_seen_height - 1
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            batch = resp.json()
        except Exception as e:
            print(f"  [warn] mempool.space fetch failed: {e}")
            break
        if not batch:
            break
        blocks.extend(batch)
        last_seen_height = batch[-1]["height"]
        time.sleep(0.3)  # be polite

    signaling = [
        b for b in blocks[:n]
        if is_signaling(b.get("version", 0))
    ]
    total = len(blocks[:n])
    return {
        "source":          "mempool.space",
        "total_blocks":    total,
        "signaling":       len(signaling),
        "signal_pct":      round(len(signaling) / total * 100, 4) if total else 0,
        "signaling_blocks": [b["height"] for b in signaling],
    }


# ── Node count fallback (bitnodes.io down) ───────────────────────────────────

def get_peer_version_distribution():
    """
    Use local node's getpeerinfo to get connected peer versions.
    Not a full network census (only your ~125 peers), but captures
    version diversity in your neighborhood of the network.
    """
    peers = rpc("getpeerinfo")
    version_counts = {}
    subversion_counts = {}

    for p in peers:
        v = p.get("version", "unknown")
        sv = p.get("subver", "unknown").strip("/")
        version_counts[str(v)]   = version_counts.get(str(v), 0) + 1
        subversion_counts[sv]    = subversion_counts.get(sv, 0) + 1

    return {
        "peer_count":           len(peers),
        "version_distribution": version_counts,
        "subver_distribution":  subversion_counts,
    }


# getchaintips returns every stale tip Bitcoin Core has ever recorded, including
# ancient one-block orphans from years ago -- those are permanent chainstate
# history, not a live fork. Only tips within this many blocks of the active tip
# are treated as "recent" for alerting/fork_count purposes.
RECENT_FORK_WINDOW = 20  # ~3.3 hours at 10 min/block


MEMPOOL_GUIDE_COMPARISON_CSV = "mempool_guide_comparison_log.csv"


def fetch_mempool_guide_tip():
    """
    mempool.guide appears to track a competing chain (confirmed 2026-08-08:
    its tip hash at a given height differs from myNode's hash at that same
    height, and myNode's getchaintips never showed this branch at all --
    a peering blind spot, not a detection bug). Polled as an independent
    cross-check myNode cannot provide on its own.
    """
    # Default python-requests User-Agent gets a 403 from this host's bot
    # filtering (confirmed 2026-08-08) -- a browser-like UA is needed.
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) bip110-monitor/1.0"}
    try:
        h = requests.get("https://mempool.guide/api/blocks/tip/height",
                          headers=headers, timeout=10)
        h.raise_for_status()
        height = int(h.text.strip())
        hh = requests.get("https://mempool.guide/api/blocks/tip/hash",
                           headers=headers, timeout=10)
        hh.raise_for_status()
        return {"height": height, "hash": hh.text.strip()}
    except Exception as e:
        print(f"  [warn] mempool.guide fetch failed: {e}")
        return None


def compare_against_mempool_guide(mg_tip):
    """
    Fetch myNode's hash at mempool.guide's tip height and compare directly --
    same-height, apples-to-apples, rather than comparing two different tip
    heights against each other.
    """
    if not mg_tip:
        return None
    try:
        my_hash_at_height = rpc("getblockhash", [mg_tip["height"]])
    except Exception as e:
        print(f"  [warn] could not fetch myNode hash at height {mg_tip['height']}: {e}")
        return None
    return {
        "height":            mg_tip["height"],
        "mempool_guide_hash": mg_tip["hash"],
        "mynode_hash":        my_hash_at_height,
        "diverged":           my_hash_at_height != mg_tip["hash"],
    }


def log_mempool_guide_comparison(row: dict, path=MEMPOOL_GUIDE_COMPARISON_CSV):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def get_chain_tips():
    """Check for any chain tip divergence (fork detection)."""
    tips = rpc("getchaintips")
    active = [t for t in tips if t["status"] == "active"]
    valid_fork = [t for t in tips if t["status"] == "valid-fork"]
    valid_headers = [t for t in tips if t["status"] == "valid-headers"]

    active_tip = active[0] if active else None
    active_height = active_tip["height"] if active_tip else None

    if active_height is not None:
        recent_valid_fork = [
            t for t in valid_fork
            if active_height - t["height"] <= RECENT_FORK_WINDOW
        ]
    else:
        recent_valid_fork = valid_fork  # can't tell recency without a known tip

    return {
        "active_tip":          active_tip,
        "valid_forks":         recent_valid_fork,      # recent only -- drives alerts
        "valid_forks_all_time": valid_fork,             # full history, for reference
        "valid_headers":       valid_headers,
        "fork_count":          len(recent_valid_fork),
        "fork_count_all_time": len(valid_fork),
    }


def trigger_fork_alert(fork_count, tips):
    """
    Best-effort audible + desktop alert for a RECENT fork (already filtered
    to RECENT_FORK_WINDOW by get_chain_tips). Alerting must never crash the
    monitor loop, so every channel is wrapped and failures are silent.
    """
    heights = ", ".join(str(t["height"]) for t in tips[:5])
    message = f"{fork_count} recent valid-fork tip(s) near current height: {heights}"

    try:
        print("\a\a\a", end="", flush=True)  # terminal bell
    except Exception:
        pass
    try:
        subprocess.run(
            ["notify-send", "-u", "critical", "BIP-110 Monitor: FORK DETECTED", message],
            timeout=5, check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    try:
        subprocess.run(
            ["paplay", "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"],
            timeout=5, check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def get_softfork_state():
    """Read getblockchaininfo softfork deployments."""
    info = rpc("getblockchaininfo")
    return info.get("softforks", {})


# ── Output ────────────────────────────────────────────────────────────────────

def append_csv(row: dict, path=OUTPUT_CSV):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def save_json(data: dict, path=OUTPUT_JSON):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def print_summary(data: dict):
    ts    = data.get("timestamp", "?")
    s     = data.get("current_period", {})
    ext   = data.get("external_api", {})
    peers = data.get("peer_versions", {})
    chain = data.get("chain_tips", {})

    print(f"\n{'='*60}")
    print(f"BIP-110 Monitor Snapshot — {ts}")
    print(f"{'='*60}")
    print(f"  Period start height  : {data.get('period_start_height', '?')}")
    print(f"  Current height       : {data.get('current_height', '?')}")
    print(f"  Blocks in period     : {s.get('total_blocks', '?')} / {PERIOD_SIZE}")
    print(f"  Signaling            : {s.get('signaling_blocks', '?')} blocks")
    print(f"  Signal rate          : {s.get('signal_pct', '?')}%")
    print(f"  Threshold            : {THRESHOLD_PCT}%")
    print(f"  Above threshold?     : {'YES ✓' if s.get('above_threshold') else 'NO ✗'}")
    print(f"  Blocks remaining     : {s.get('blocks_remaining_in_period', '?')}")

    if ext:
        print(f"\n  [bip110monitor.com API]")
        print(f"  {json.dumps(ext, indent=4)}")

    print(f"\n  [Peer Version Sample — {peers.get('peer_count', '?')} peers]")
    for sv, cnt in sorted(peers.get("subver_distribution", {}).items(),
                          key=lambda x: -x[1])[:10]:
        print(f"    {cnt:3d}  {sv}")

    if chain.get("fork_count", 0) > 0:
        print(f"\n  ⚠️  CHAIN TIPS: {chain['fork_count']} RECENT valid fork(s) "
              f"(within {RECENT_FORK_WINDOW} blocks of tip) -- ALERT TRIGGERED!")
        for f in chain["valid_forks"]:
            print(f"     height={f['height']}  hash={f['hash'][:16]}...  "
                  f"branchlen={f['branchlen']}")
    else:
        print(f"\n  Chain tips: clean, no recent forks "
              f"(within {RECENT_FORK_WINDOW} blocks)")

    all_time = chain.get("fork_count_all_time", 0)
    if all_time:
        print(f"  (for reference: {all_time} valid-fork tip(s) exist further back "
              f"in this node's chainstate history -- normal, not alerted on)")

    mg = data.get("mempool_guide")
    if mg:
        if mg["diverged"]:
            print(f"\n  ⚠️  MEMPOOL.GUIDE DIVERGENCE at height {mg['height']}:")
            print(f"     myNode        : {mg['mynode_hash']}")
            print(f"     mempool.guide : {mg['mempool_guide_hash']}")
        else:
            print(f"\n  mempool.guide cross-check: matches myNode at height {mg['height']}")

    print(f"{'='*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def snapshot(skip_full_scan=False):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n[{ts}] Running BIP-110 snapshot...")

    period_start, blocks_in_period, current_height, tip_hash = get_current_period_info()

    # Scan blocks — full scan from local node, or lighter API fallback
    if skip_full_scan:
        local_records = []
        print("  [--fast mode] skipping full local scan, using API data only")
        period_summary = {}
    else:
        local_records  = scan_period_from_node(period_start, blocks_in_period)
        period_summary = compute_summary(local_records)

    # External API cross-check
    ext_api = fetch_bip110_monitor_api()

    # Peer version distribution (bitnodes.io substitute)
    peer_versions = get_peer_version_distribution()

    # Chain tip check (fork detection)
    chain_tips = get_chain_tips()
    if chain_tips.get("fork_count", 0) > 0:
        trigger_fork_alert(chain_tips["fork_count"], chain_tips["valid_forks"])

    # mempool.guide cross-check -- myNode's own getchaintips has a confirmed
    # blind spot (its peers never relayed the competing chain), so this
    # external same-height hash comparison is the only way to catch it.
    mg_tip = fetch_mempool_guide_tip()
    mg_comparison = compare_against_mempool_guide(mg_tip)
    if mg_comparison:
        log_mempool_guide_comparison({"timestamp": ts, **mg_comparison})
        if mg_comparison["diverged"]:
            trigger_fork_alert(
                1, [{"height": mg_comparison["height"],
                     "hash": mg_comparison["mempool_guide_hash"], "branchlen": "?"}]
            )

    # Softfork state from getblockchaininfo
    sf_state = get_softfork_state()

    data = {
        "timestamp":           ts,
        "period_start_height": period_start,
        "current_height":      current_height,
        "tip_hash":            tip_hash,
        "current_period":      period_summary,
        "external_api":        ext_api,
        "peer_versions":       peer_versions,
        "chain_tips":          chain_tips,
        "mempool_guide":       mg_comparison,
        "softfork_state":      sf_state,
    }

    # Flat CSV row for time-series logging
    csv_row = {
        "timestamp":           ts,
        "height":              current_height,
        "period_start":        period_start,
        "blocks_in_period":    blocks_in_period,
        "signaling":           period_summary.get("signaling_blocks", ""),
        "signal_pct":          period_summary.get("signal_pct", ""),
        "above_threshold":     period_summary.get("above_threshold", ""),
        "fork_count":          chain_tips.get("fork_count", 0),
        "peer_count":          peer_versions.get("peer_count", 0),
        "ext_api_signal_pct":  ext_api.get("pct", "") if ext_api else "",
    }

    save_json(data, OUTPUT_JSON)
    append_csv(csv_row)
    print_summary(data)

    return data


def main():
    parser = argparse.ArgumentParser(description="BIP-110 Soft Fork Monitor")
    parser.add_argument("--loop",    type=int, default=0,
                        help="Poll interval in seconds (0 = single snapshot)")
    parser.add_argument("--fast",    action="store_true",
                        help="Skip full local block scan (API data only)")
    parser.add_argument("--history", type=int, metavar="N", default=0,
                        help="Fetch signal-rate trend for the last N difficulty "
                             "periods (headers-only, no pool breakdown) and exit")
    args = parser.parse_args()

    print("BIP-110 Soft Fork Monitor")
    print(f"  Local node  : {RPC_HOST}:{RPC_PORT}")
    print(f"  Signal bit  : 4  (0x{1 << 4:08X})")
    print(f"  Threshold   : {THRESHOLD_PCT}%")
    print(f"  Output CSV  : {OUTPUT_CSV}")
    print(f"  Output JSON : {OUTPUT_JSON}")

    if args.history:
        print(f"  Mode        : history scan, last {args.history} period(s)\n")
        results = scan_history(args.history)
        print_history(results)
        save_history_csv(results)
    elif args.loop:
        print(f"  Mode        : polling every {args.loop}s  (Ctrl-C to stop)\n")
        while True:
            try:
                snapshot(skip_full_scan=args.fast)
            except Exception as e:
                print(f"[error] {e}")
            time.sleep(args.loop)
    else:
        snapshot(skip_full_scan=args.fast)


if __name__ == "__main__":
    main()
