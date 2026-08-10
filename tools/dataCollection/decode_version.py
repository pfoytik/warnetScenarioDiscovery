#!/usr/bin/env python3
"""
Bitcoin block nVersion decoder
================================
Decodes BIP9 version bits and shows which soft forks are being signaled.

Usage:
    python3 decode_version.py 0x23532010
    python3 decode_version.py 0x20086000 0x2e000000 0x238f8000 0x23532010
    python3 decode_version.py --rpc-recent 20   # decode last N blocks from local node
"""

import argparse
import os
import sys

try:
    import requests
except ImportError:
    requests = None

BIP9_TOP_MASK = 0xE0000000
BIP9_TOP_BITS = 0x20000000

# Known BIP deployments (add new ones here as they appear)
KNOWN_BITS = {
    4: "BIP-110 (Reduced Data Temporary Softfork)",
    # Add others as needed, e.g.:
    # 1: "BIP-XXX (SomeOtherFork)",
}

RPC_USER     = os.environ.get("RPC_USER", "bitcoin")
RPC_PASSWORD = os.environ.get("RPC_PASSWORD", "password")
RPC_HOST     = os.environ.get("RPC_HOST", "127.0.0.1")
RPC_PORT     = int(os.environ.get("RPC_PORT", "8332"))


def decode(nversion):
    if isinstance(nversion, str):
        nversion = int(nversion, 16) if nversion.startswith("0x") else int(nversion)

    is_bip9 = (nversion & BIP9_TOP_MASK) == BIP9_TOP_BITS
    signaled_bits = []
    for bit in range(29):
        if nversion & (1 << bit):
            signaled_bits.append(bit)

    return {
        "hex":          hex(nversion),
        "dec":          nversion,
        "bin":          f"{nversion:032b}",
        "is_bip9":      is_bip9,
        "top_3_bits":   f"{(nversion >> 29):03b}",
        "signaled_bits": signaled_bits,
        "known_forks":  [KNOWN_BITS[b] for b in signaled_bits if b in KNOWN_BITS],
        "bip110_signal": is_bip9 and bool(nversion & (1 << 4)),
    }


def print_decode(nversion_raw):
    d = decode(nversion_raw)
    tag = "✓ BIP-110" if d["bip110_signal"] else "✗ no BIP-110"
    bip9_tag = "BIP9 valid" if d["is_bip9"] else "NOT BIP9"
    print(f"\n  {d['hex']:14s}  [{bip9_tag}]  {tag}")
    print(f"  Binary: {d['bin']}")
    if d["signaled_bits"]:
        bits_str = ", ".join(
            f"bit {b} ({KNOWN_BITS.get(b, 'unknown')})"
            for b in d["signaled_bits"]
        )
        print(f"  Signaled bits: {bits_str}")
    else:
        print(f"  Signaled bits: none")


def rpc(method, params=None):
    if requests is None:
        print("requests not installed")
        sys.exit(1)
    payload = {"jsonrpc": "1.0", "id": "decode", "method": method, "params": params or []}
    resp = requests.post(
        f"http://{RPC_HOST}:{RPC_PORT}/",
        auth=(RPC_USER, RPC_PASSWORD),
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["result"]


def decode_recent_blocks(n):
    tip_hash = rpc("getbestblockhash")
    tip = rpc("getblockheader", [tip_hash, True])
    height = tip["height"]

    print(f"\nDecoding last {n} blocks (tip = {height})")
    print(f"{'Height':>8}  {'Version':>12}  {'BIP9?':>8}  {'BIP-110':>8}  {'Bits'}")
    print("-" * 60)

    signaling = 0
    h = tip_hash
    for i in range(n):
        blk = rpc("getblockheader", [h, True])
        nv  = blk["version"]
        d   = decode(nv)
        bip9_s   = "yes" if d["is_bip9"] else "no"
        bip110_s = "✓" if d["bip110_signal"] else "✗"
        bits_s   = str(d["signaled_bits"]) if d["signaled_bits"] else "[]"
        if d["bip110_signal"]:
            signaling += 1
        print(f"{blk['height']:>8}  {hex(nv):>12}  {bip9_s:>8}  {bip110_s:>8}  {bits_s}")
        h = blk.get("previousblockhash")
        if not h:
            break

    print(f"\nBIP-110 signaling: {signaling}/{n} = {signaling/n*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Bitcoin nVersion decoder")
    parser.add_argument("versions", nargs="*",
                        help="One or more nVersion values (hex or decimal)")
    parser.add_argument("--rpc-recent", type=int, metavar="N",
                        help="Decode last N blocks via local node RPC")
    args = parser.parse_args()

    if args.rpc_recent:
        decode_recent_blocks(args.rpc_recent)
    elif args.versions:
        print(f"\nnVersion decoder — BIP-110 uses bit 4 (0x{1<<4:08X})")
        for v in args.versions:
            print_decode(v)
        print()
    else:
        # Demo with the user's example versions
        examples = ["0x23532010", "0x20086000", "0x2e000000", "0x238f8000"]
        print(f"\nnVersion decoder — example from your observation:")
        for v in examples:
            print_decode(v)
        print()


if __name__ == "__main__":
    main()
