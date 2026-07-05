#!/usr/bin/env python3
"""
Generate all config files for the contested_fork_threshold sweep.

120 scenarios: 3 vr × 4 E × 5 C × 2 compositions
Research question: Where does "reorg pain" begin in the (vr, C, E) space?
                   What combination of violation rate, pool commitment, and
                   economic split maximizes fork depth and contested duration?

New metrics beyond chainsplit_persistence:
  - reorg_depth: minority_blocks at heal (how many blocks losing nodes must reorg)
  - fork_balance: min/max block ratio at heal (1.0=maximally contested, 0=one-sided)
  - pain_score: reorg_depth × fork_balance (composite)

Key design differences from chainsplit_persistence:
  - violation_rate: 3 values [0.20, 0.50, 1.00] — focused on the pain zone
  - economic_split: 4 values [0.30, 0.40, 0.50, 0.55] — extends into low-E territory
  - pool_committed_split: 5 values [0.15, 0.20, 0.25, 0.30, 0.35] — fine resolution
  - composition_seed: 2 random compositions per (vr, E, C) point — decouples pool
    identity from aggregate committed hashrate (arm_a style)
  - E=0.30-0.55: NEW territory — no prior sweep covered E < 0.55

Build pipeline:
  1. This script writes scenarios.json (flat format, all params at top level)
  2. This script calls 2_build_configs.py --input scenarios.json to:
       - Generate configs/ (network, pool, economic)
       - Generate networks/ (one network.yaml per scenario)
       - Write build_manifest.json
  3. This script reads back build_manifest.json and splits into server1/server2 versions
"""
import json
import random
import subprocess
import sys
from pathlib import Path

SWEEP_DIR = Path(__file__).parent
BASE_DIR = SWEEP_DIR.parent.parent.parent  # warnetScenarioDiscovery root

BASE_SEED = 2000

VIOLATION_RATES = [0.20, 0.50, 1.00]
E_VALUES        = [0.30, 0.40, 0.50, 0.55]
C_VALUES        = [0.15, 0.20, 0.25, 0.30, 0.35]
COMPOSITIONS    = 2

NAMESPACE_PREFIX    = "cft"   # contested fork threshold
SCENARIOS_PER_NS    = 10      # 120 scenarios / 12 namespaces = 10 each

# Fixed parameters (validated from prior sweeps)
FIXED_PARAMS = {
    "hashrate_split": 0.25,
    "pool_neutral_pct": 30.0,
    "pool_profitability_threshold": 0.16,
    "pool_ideology_strength": 0.51,
    "pool_max_loss_pct": 0.26,
    "econ_ideology_strength": 0.4,
    "econ_switching_threshold": 0.1,
    "econ_inertia": 0.05,
    "user_ideology_strength": 0.49,
    "user_switching_threshold": 0.12,
    "user_nodes_per_partition": 6,
    "economic_nodes_per_partition": 2,
    "transaction_velocity": 0.5,
    "solo_miner_hashrate": 0.085,
}

# Lite network pools — used to pre-compute committed_hashrate_actual.
# Must match what 2_build_configs.py extracts from the lite base network.
LITE_POOLS = [
    ("pool-foundryusa", "Foundry USA",  30.0, "v27"),
    ("pool-marapool",   "MARA Pool",     4.6, "v27"),
    ("pool-luxor",      "Luxor",         2.3, "v27"),
    ("pool-ocean",      "Ocean",         1.2, "v27"),
    ("pool-antpool",    "AntPool",      16.9, "v26"),
    ("pool-f2pool",     "F2Pool",       10.9, "v26"),
    ("pool-viabtc",     "ViaBTC",       11.2, "v26"),
    ("pool-spiderpool", "SpiderPool",    9.3, "v26"),
]
TOTAL_POOL_HR = sum(p[2] for p in LITE_POOLS)  # 86.4


def compute_c_eff(c_value, seed):
    """
    Compute the realized committed hashrate fraction for a given (C, seed).
    Uses the same random.Random shuffle as 2_build_configs.py:create_pool_scenario.
    Returns (c_eff_fraction, committed_pool_ids_list).
    """
    neutral_frac = FIXED_PARAMS["pool_neutral_pct"] / 100.0
    committed_frac = 1.0 - neutral_frac
    v27_pct = committed_frac * c_value

    pool_list = list(LITE_POOLS)
    rng = random.Random(seed)
    rng.shuffle(pool_list)

    cumulative = 0.0
    c_eff = 0.0
    committed_ids = []
    for pool_id, _name, hashrate, _initial in pool_list:
        midpoint = (cumulative + hashrate / 2.0) / TOTAL_POOL_HR
        if midpoint < v27_pct:
            c_eff += hashrate / TOTAL_POOL_HR
            committed_ids.append(pool_id.replace("pool-", ""))
        cumulative += hashrate

    return round(c_eff, 4), committed_ids


def build_scenarios():
    """
    Build flat scenario dicts suitable for 2_build_configs.py (all params at top level).

    Iteration order: vr (outer) → E → C → composition (inner)
    This places vr=0.20 in sweep_0000–0039, vr=0.50 in 0040–0079, vr=1.00 in 0080–0119.
    Server 1 handles sweep_0000–0059, Server 2 handles sweep_0060–0119.
    """
    scenarios = []
    sid = 0

    for vr_idx, vr in enumerate(VIOLATION_RATES):
        for e_idx, e in enumerate(E_VALUES):
            for c_idx, c in enumerate(C_VALUES):
                for comp_idx in range(COMPOSITIONS):
                    group_idx = (vr_idx * len(E_VALUES) * len(C_VALUES)
                                 + e_idx * len(C_VALUES)
                                 + c_idx)
                    seed = BASE_SEED + group_idx * COMPOSITIONS + comp_idx
                    c_eff, committed_ids = compute_c_eff(c, seed)
                    prob = round(1.0 - vr, 2)

                    # Flat dict — all params at top level (required by 2_build_configs.py)
                    s = dict(FIXED_PARAMS)
                    s.update({
                        "scenario_id": f"sweep_{sid:04d}",
                        # Grid axes
                        "violation_rate": vr,
                        "economic_split": e,
                        "pool_committed_split": c,
                        # Composition tracking
                        "composition_index": comp_idx,
                        "composition_seed": seed,
                        "committed_hashrate_actual": c_eff,
                        "committed_pool_ids_v27": committed_ids,
                        # Scenario script flags
                        "v26_acceptance_probability": prob,
                        "partition_mode": "unified",
                        "fork_heal_exit": True,
                    })
                    scenarios.append(s)
                    sid += 1

    return scenarios


def write_scenarios_json(scenarios):
    """Write scenarios.json in the flat format that 2_build_configs.py reads."""
    data = {
        "metadata": {
            "type": "contested_fork_threshold",
            "name": "contested_fork_threshold",
            "base_network": "lite",
            "description": (
                "Reorg pain threshold sweep: maps (vr, C, E) -> fork depth and duration. "
                "120 scenarios: 3 vr x 4 E x 5 C x 2 compositions. "
                "New metrics: reorg_depth, fork_balance, pain_score. "
                "E=0.30-0.55 extends into unexplored low-E territory. "
                "composition_seed decouples pool identity from aggregate C."
            ),
            "grid_axes": {
                "violation_rate": VIOLATION_RATES,
                "economic_split": E_VALUES,
                "pool_committed_split": C_VALUES,
                "compositions_per_point": COMPOSITIONS,
                "base_composition_seed": BASE_SEED,
            },
            "fixed_parameters": FIXED_PARAMS,
        },
        "scenarios": scenarios,
    }
    out = SWEEP_DIR / "scenarios.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Wrote scenarios.json ({len(scenarios)} scenarios)")
    return out


def build_networks(scenarios_json_path):
    """
    Call 2_build_configs.py to generate configs/ and networks/ from the flat scenarios.json.
    2_build_configs.py also writes build_manifest.json to the output directory.
    """
    build_script = BASE_DIR / "tools" / "sweep" / "2_build_configs.py"
    lite_network = (
        BASE_DIR / "networks" / "realistic-economy-lite" / "network.yaml"
    ).resolve()

    cmd = [
        sys.executable,
        str(build_script),
        "--input", str(scenarios_json_path),
        "--output-dir", str(SWEEP_DIR),
        "--base-network", str(lite_network),
    ]
    print(f"\nRunning 2_build_configs.py...")
    print(f"  Base network: {lite_network}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print(f"\nERROR: 2_build_configs.py exited with code {result.returncode}")
        sys.exit(1)
    print("  Build complete.")


def split_manifests():
    """
    Read build_manifest.json (written by 2_build_configs.py) and produce
    build_manifest_server1.json (sweep_0000-0059) and build_manifest_server2.json
    (sweep_0060-0119).
    """
    manifest_path = SWEEP_DIR / "build_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    all_scenarios = manifest["scenarios"]
    assert len(all_scenarios) == 120, f"Expected 120 scenarios, got {len(all_scenarios)}"

    for suffix, subset in [("_server1", all_scenarios[:60]), ("_server2", all_scenarios[60:])]:
        out = dict(manifest)
        out["scenarios"] = subset
        out["metadata"] = dict(manifest["metadata"])
        server_num = suffix.replace("_server", "")
        out["metadata"]["server"] = f"server{server_num}"
        out["metadata"]["namespaces"] = (
            f"{NAMESPACE_PREFIX}-0 to {NAMESPACE_PREFIX}-5 (server{server_num})"
        )
        out_path = SWEEP_DIR / f"build_manifest{suffix}.json"
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2)

    print(f"  Wrote build_manifest_server1.json (sweep_0000-0059)")
    print(f"  Wrote build_manifest_server2.json (sweep_0060-0119)")


if __name__ == "__main__":
    print("Generating contested_fork_threshold sweep...")
    print(f"  Grid: {len(VIOLATION_RATES)} vr × {len(E_VALUES)} E × "
          f"{len(C_VALUES)} C × {COMPOSITIONS} comp = "
          f"{len(VIOLATION_RATES)*len(E_VALUES)*len(C_VALUES)*COMPOSITIONS} scenarios")

    scenarios = build_scenarios()
    assert len(scenarios) == 120

    print(f"\nScenario grid (C_eff spot-check, first 12):")
    for s in scenarios[:12]:
        print(f"  {s['scenario_id']}: vr={s['violation_rate']} E={s['economic_split']} "
              f"C={s['pool_committed_split']} comp={s['composition_index']} "
              f"seed={s['composition_seed']} "
              f"C_eff={s['committed_hashrate_actual']:.3f} "
              f"pools={s['committed_pool_ids_v27']}")

    print(f"\nServer split:")
    print(f"  Server 1: {scenarios[0]['scenario_id']} – {scenarios[59]['scenario_id']}")
    print(f"  Server 2: {scenarios[60]['scenario_id']} – {scenarios[119]['scenario_id']}")

    print("\nWriting scenarios.json...")
    scenarios_json = write_scenarios_json(scenarios)

    build_networks(scenarios_json)

    print("\nSplitting manifests by server...")
    split_manifests()

    # Verify output
    net_count = len(list((SWEEP_DIR / "networks").glob("*/network.yaml")))
    cfg_count = len(list((SWEEP_DIR / "configs" / "network").glob("*.yaml")))
    print(f"\nVerification:")
    print(f"  Network YAMLs:  {net_count}/120")
    print(f"  Config YAMLs:   {cfg_count}/120")
    print(f"\nDone.")
