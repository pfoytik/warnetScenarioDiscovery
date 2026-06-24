#!/usr/bin/env python3
"""
split_manifest.py — Split a build_manifest.json into two halves for parallel server runs.

Usage:
    python tools/sweep/split_manifest.py pool_composition_arm_a/build_manifest.json

Output:
    pool_composition_arm_a/build_manifest_server1.json  (first half)
    pool_composition_arm_a/build_manifest_server2.json  (second half)
"""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python split_manifest.py <build_manifest.json>")
        sys.exit(1)

    manifest_path = Path(sys.argv[1])
    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    scenarios = manifest["scenarios"]
    n = len(scenarios)
    half = n // 2

    for server_num, (start, end) in enumerate([(0, half), (half, n)], start=1):
        chunk = scenarios[start:end]
        server_manifest = {
            **manifest,
            "scenarios": chunk,
            "metadata": {
                **manifest.get("metadata", {}),
                "server": server_num,
                "scenario_range": [start, end - 1],
                "n_scenarios_this_server": len(chunk),
            },
        }
        out_path = manifest_path.parent / f"build_manifest_server{server_num}.json"
        with open(out_path, "w") as f:
            json.dump(server_manifest, f, indent=2)
        print(f"Server {server_num}: {len(chunk)} scenarios ({start}–{end-1}) → {out_path}")

    print(f"\nTotal scenarios: {n}  ({half} + {n - half})")


if __name__ == "__main__":
    main()
