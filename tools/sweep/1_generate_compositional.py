#!/usr/bin/env python3
"""
Step 1 (Arm A): Generate Pool Composition Decoupling Scenarios

Generates a grid of (economic_split, pool_committed_split) parameter points,
with multiple random pool compositions per point. The composition is controlled
by a per-scenario `composition_seed` that shuffles pool order before the
cumulative hashrate assignment in 2_build_configs.py.

This decouples pool IDENTITY from the aggregate hashrate scalar, enabling the
research question: does outcome depend on WHICH pools commit, or only on HOW
MUCH hashrate commits?

Usage:
    python tools/sweep/1_generate_compositional.py \
        --spec specs/pool_composition_arm_a.yaml \
        --output pool_composition_arm_a

    # Preview without saving
    python tools/sweep/1_generate_compositional.py \
        --spec specs/pool_composition_arm_a.yaml --preview

Output:
    pool_composition_arm_a/
    ├── scenarios.json               — all 168 scenarios
    ├── scenarios_server1.json       — scenarios 0-83  (for server 1)
    └── scenarios_server2.json       — scenarios 84-167 (for server 2)
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

# Default pool list matching DEFAULT_POOLS in 2_build_configs.py
DEFAULT_POOLS = [
    ("foundryusa",  "Foundry USA",   26.89),
    ("antpool",     "AntPool",       19.25),
    ("viabtc",      "ViaBTC",        11.39),
    ("f2pool",      "F2Pool",        11.25),
    ("binancepool", "Binance Pool",  10.04),
    ("marapool",    "MARA Pool",      8.25),
    ("sbicrypto",   "SBI Crypto",     4.57),
    ("luxor",       "Luxor",          3.94),
    ("ocean",       "OCEAN",          1.42),
    ("braiinspool", "Braiins Pool",   1.37),
]
TOTAL_HASHRATE = sum(p[2] for p in DEFAULT_POOLS)


def resolve_committed_pools(pools, committed_split, neutral_pct, composition_seed=None):
    """
    Assign pool fork preferences given a committed_split scalar and a composition_seed.

    If composition_seed is None, uses the deterministic hashrate order (original behavior).
    If composition_seed is provided, shuffles pool order before assignment.

    Returns:
        pool_order  — list of (pool_id, pool_name, hashrate) in assignment order
        assignments — dict: pool_id → 'v27' | 'v26' | 'neutral'
        v27_pool_ids — list of pool_ids assigned to v27
        realized_v27_hashrate — actual v27 committed hashrate fraction
    """
    neutral_frac   = neutral_pct / 100.0
    committed_frac = 1.0 - neutral_frac
    v27_frac       = committed_frac * committed_split
    v26_frac       = committed_frac * (1.0 - committed_split)

    pool_order = list(pools)
    if composition_seed is not None:
        rng = np.random.default_rng(composition_seed)
        idx = rng.permutation(len(pool_order))
        pool_order = [pool_order[i] for i in idx]

    total = sum(p[2] for p in pool_order)
    cumulative = 0.0
    assignments = {}
    v27_pool_ids = []
    realized_v27 = 0.0

    for pool_id, pool_name, hashrate in pool_order:
        midpoint = (cumulative + hashrate / 2) / total
        if midpoint < v27_frac:
            assignments[pool_id] = 'v27'
            v27_pool_ids.append(pool_id)
            realized_v27 += hashrate
        elif midpoint < v27_frac + v26_frac:
            assignments[pool_id] = 'v26'
        else:
            assignments[pool_id] = 'neutral'
        cumulative += hashrate

    return pool_order, assignments, v27_pool_ids, realized_v27 / total


def load_spec(spec_path: Path) -> dict:
    with open(spec_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Generate pool composition decoupling scenarios (Arm A)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--spec", "-s", type=str,
                        default="specs/pool_composition_arm_a.yaml",
                        help="Path to YAML spec file")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output directory (default: spec name)")
    parser.add_argument("--preview", action="store_true",
                        help="Preview without saving")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: spec not found: {spec_path}")
        sys.exit(1)

    spec = load_spec(spec_path)
    print(f"Loaded spec: {spec['name']}")

    e_values    = spec["economic_split_values"]
    c_values    = spec["pool_committed_split_values"]
    n_comp      = spec["compositions_per_point"]
    base_seed   = spec.get("base_composition_seed", 1000)
    fixed       = spec.get("fixed", {})
    neutral_pct = fixed.get("pool_neutral_pct", 30.0)

    n_total = len(e_values) * len(c_values) * n_comp
    print(f"  {len(e_values)} E values × {len(c_values)} C values × {n_comp} compositions = {n_total} scenarios")

    scenarios = []
    scenario_idx = 0

    for e in e_values:
        for c in c_values:
            for comp_idx in range(n_comp):
                # Unique seed per (e, c, composition_index)
                seed = base_seed + scenario_idx

                # Resolve which pools end up committed to v27
                _, assignments, v27_ids, realized_v27 = resolve_committed_pools(
                    DEFAULT_POOLS, c, neutral_pct, composition_seed=seed
                )

                scenario = {
                    "scenario_id": f"sweep_{scenario_idx:04d}",
                    "economic_split": round(e, 4),
                    "pool_committed_split": round(c, 4),
                    "composition_seed": seed,
                    "composition_index": comp_idx,
                    "committed_pool_ids_v27": v27_ids,
                    "committed_hashrate_actual": round(realized_v27, 4),
                }
                # Add fixed parameters
                scenario.update(fixed)
                scenarios.append(scenario)
                scenario_idx += 1

    # Preview
    print(f"\nFirst 8 scenarios:")
    for s in scenarios[:8]:
        print(
            f"  {s['scenario_id']}: E={s['economic_split']:.2f}  "
            f"C={s['pool_committed_split']:.3f}  "
            f"comp={s['composition_index']}  "
            f"seed={s['composition_seed']}  "
            f"v27_pools={s['committed_pool_ids_v27']}  "
            f"realized={s['committed_hashrate_actual']:.3f}"
        )

    print(f"\nComposition variance at C=0.214 (Foundry flip-point):")
    flip_scenarios = [s for s in scenarios if abs(s['pool_committed_split'] - 0.214) < 0.001]
    for s in flip_scenarios:
        print(
            f"  comp={s['composition_index']}  "
            f"v27_pools={s['committed_pool_ids_v27']}  "
            f"realized={s['committed_hashrate_actual']:.3f}"
        )

    if args.preview:
        print("\n[Preview mode — not saving]")
        return

    # Build output
    output_dir = Path(args.output) if args.output else Path(spec["name"])
    output_dir.mkdir(exist_ok=True)

    full_output = {
        "metadata": {
            "type": "compositional_grid",
            "name": spec["name"],
            "description": spec.get("description", ""),
            "spec_file": str(spec_path),
            "base_network": spec.get("network", "lite"),
            "n_scenarios": n_total,
            "e_values": e_values,
            "c_values": c_values,
            "compositions_per_point": n_comp,
            "base_composition_seed": base_seed,
            "fixed_parameters": fixed,
        },
        "scenarios": scenarios,
    }

    # Full scenarios.json
    full_path = output_dir / "scenarios.json"
    with open(full_path, "w") as f:
        json.dump(full_output, f, indent=2)
    print(f"\nSaved {n_total} scenarios to {full_path}")

    # Split in half for two servers
    half = n_total // 2
    for server_num, (start, end) in enumerate([(0, half), (half, n_total)], start=1):
        server_scenarios = scenarios[start:end]
        # Renumber scenario_ids to keep them unique but indicate server
        server_output = dict(full_output)
        server_output = {**full_output, "scenarios": server_scenarios}
        server_output["metadata"] = {
            **full_output["metadata"],
            "server": server_num,
            "scenario_range": [start, end - 1],
        }
        server_path = output_dir / f"scenarios_server{server_num}.json"
        with open(server_path, "w") as f:
            json.dump(server_output, f, indent=2)
        print(f"  Server {server_num}: {len(server_scenarios)} scenarios ({start}–{end-1}) → {server_path}")

    print(f"\nNext step:")
    print(f"  python tools/sweep/2_build_configs.py \\")
    print(f"    --input {full_path} \\")
    print(f"    --output-dir {output_dir} \\")
    print(f"    --base-network lite")
    print(f"\n  # Then split the build manifest:")
    print(f"  python tools/sweep/split_manifest.py {output_dir}/build_manifest.json")


if __name__ == "__main__":
    main()
