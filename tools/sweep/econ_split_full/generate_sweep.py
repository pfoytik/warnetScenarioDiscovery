#!/usr/bin/env python3
"""
Generate all config files for the econ_split_full sweep.

108 scenarios: 6 E × 3 vr × 3 C × 2 compositions
Research question: How does economic split (E) influence fork outcomes on the full network?
                   Does higher economic support lower the C_eff threshold needed for v27 to win?

Builds on contested_fork_threshold findings:
  - C_eff ≥ 0.30 (foundryusa) is a hard threshold on the lite network regardless of vr
  - C_eff 0.20–0.30 is the soft zone where vr matters
  - Lite network E invariance: all E in [0.28, 0.78] produce identical topology
  - Full network has 6 meaningful E steps between 0.14 and 0.79

Full network E step boundaries (realistic-economy, 52 non-pool nodes):
  E ≥ 0.139 → node-0034 tagged (major_exchange, 28% cumul custody)
  E ≥ 0.372 → node-0004 tagged (major_exchange, 47% cumul custody)
  E ≥ 0.522 → node-0043 tagged (institutional,  58% cumul custody)
  E ≥ 0.636 → node-0005 tagged (major_exchange, 69% cumul custody)
  E ≥ 0.729 → node-0035 tagged (major_exchange, 77% cumul custody)
  E ≥ 0.794 → node-0036 tagged (exchange,       82% cumul custody)

Selected E values place one point per interval between step boundaries:
  E=0.25  → 1 node tagged (28% custody)
  E=0.45  → 2 nodes tagged (47% custody)
  E=0.58  → 3 nodes tagged (58% custody) — comparable to CSP/CFT baseline
  E=0.68  → 4 nodes tagged (69% custody)
  E=0.76  → 5 nodes tagged (77% custody)
  E=0.82  → 6 nodes tagged (82% custody)

Build pipeline:
  1. This script writes scenarios.json (flat format)
  2. This script calls 2_build_configs.py to generate configs/ and networks/
  3. This script splits build_manifest.json into server1/server2 versions
"""
import json
import random
import subprocess
import sys
from pathlib import Path

SWEEP_DIR = Path(__file__).parent
BASE_DIR  = SWEEP_DIR.parent.parent.parent   # warnetScenarioDiscovery root

BASE_SEED = 3000

E_VALUES        = [0.25, 0.45, 0.58, 0.68, 0.76, 0.82]
VIOLATION_RATES = [0.20, 0.50, 1.00]
C_VALUES        = [0.20, 0.25, 0.30]
COMPOSITIONS    = 2

NAMESPACE_PREFIX    = "esf"   # econ split full
SCENARIOS_PER_NS    = 9       # 108 scenarios / 12 namespaces = 9 each

# Fixed parameters — identical to contested_fork_threshold for comparability
FIXED_PARAMS = {
    "hashrate_split":                0.25,
    "pool_neutral_pct":              30.0,
    "pool_profitability_threshold":  0.16,
    "pool_ideology_strength":        0.51,
    "pool_max_loss_pct":             0.26,
    "econ_ideology_strength":        0.4,
    "econ_switching_threshold":      0.1,
    "econ_inertia":                  0.05,
    "user_ideology_strength":        0.49,
    "user_switching_threshold":      0.12,
    "user_nodes_per_partition":      6,
    "economic_nodes_per_partition":  2,
    "transaction_velocity":          0.5,
    "solo_miner_hashrate":           0.085,
}

# Full network pools — realistic-economy/network.yaml
# Must match what 2_build_configs.py extracts from the base network.
FULL_POOLS = [
    ("pool-foundryusa",   "Foundry USA",   26.89, "v27"),
    ("pool-marapool",     "MARA Pool",      4.85, "v27"),
    ("pool-luxor",        "Luxor",          3.12, "v27"),
    ("pool-ocean",        "Ocean",          1.42, "v27"),
    ("pool-antpool",      "AntPool",       19.25, "v26"),
    ("pool-f2pool",       "F2Pool",        11.25, "v26"),
    ("pool-viabtc",       "ViaBTC",        11.39, "v26"),
    ("pool-binancepool",  "Binance Pool",  10.04, "v26"),
]
TOTAL_POOL_HR = sum(p[2] for p in FULL_POOLS)  # 88.21


def compute_c_eff(c_value, seed):
    """
    Compute realized committed hashrate fraction for a given (C, seed).
    Uses the same random.Random shuffle as 2_build_configs.py:create_pool_scenario.
    Returns (c_eff_fraction, committed_pool_ids_list).
    """
    neutral_frac   = FIXED_PARAMS["pool_neutral_pct"] / 100.0
    committed_frac = 1.0 - neutral_frac
    v27_pct        = committed_frac * c_value

    pool_list = list(FULL_POOLS)
    rng = random.Random(seed)
    rng.shuffle(pool_list)

    cumulative = 0.0
    c_eff      = 0.0
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
    Build flat scenario dicts.

    Iteration order: E (outer) → vr → C → comp (inner)
    E=0.25/0.45/0.58 in sweep_0000–0053 → Server 1
    E=0.68/0.76/0.82 in sweep_0054–0107 → Server 2
    """
    scenarios = []
    sid = 0

    for e_idx, e in enumerate(E_VALUES):
        for vr_idx, vr in enumerate(VIOLATION_RATES):
            for c_idx, c in enumerate(C_VALUES):
                for comp_idx in range(COMPOSITIONS):
                    group_idx = (e_idx * len(VIOLATION_RATES) * len(C_VALUES)
                                 + vr_idx * len(C_VALUES)
                                 + c_idx)
                    seed = BASE_SEED + group_idx * COMPOSITIONS + comp_idx
                    c_eff, committed_ids = compute_c_eff(c, seed)
                    prob = round(1.0 - vr, 2)

                    s = dict(FIXED_PARAMS)
                    s.update({
                        "scenario_id":               f"sweep_{sid:04d}",
                        "violation_rate":            vr,
                        "economic_split":            e,
                        "pool_committed_split":      c,
                        "composition_index":         comp_idx,
                        "composition_seed":          seed,
                        "committed_hashrate_actual": c_eff,
                        "committed_pool_ids_v27":    committed_ids,
                        "v26_acceptance_probability": prob,
                        "partition_mode":            "unified",
                        "fork_heal_exit":            True,
                    })
                    scenarios.append(s)
                    sid += 1

    return scenarios


def write_scenarios_json(scenarios):
    data = {
        "metadata": {
            "type":         "econ_split_full",
            "name":         "econ_split_full",
            "base_network": "realistic-economy",
            "description": (
                "Full-network E sweep: maps economic_split → fork outcomes with proper "
                "E variation. 108 scenarios: 6 E × 3 vr × 3 C × 2 compositions. "
                "Extends contested_fork_threshold findings to the full network where "
                "E produces 6 distinct economic node topologies between 0.14 and 0.79."
            ),
            "grid_axes": {
                "economic_split":          E_VALUES,
                "violation_rate":          VIOLATION_RATES,
                "pool_committed_split":    C_VALUES,
                "compositions_per_point":  COMPOSITIONS,
                "base_composition_seed":   BASE_SEED,
            },
            "e_step_boundaries": {
                "0.139": "node-0034 tagged (major_exchange, 28% cumul custody)",
                "0.372": "node-0004 tagged (major_exchange, 47% cumul custody)",
                "0.522": "node-0043 tagged (institutional,  58% cumul custody)",
                "0.636": "node-0005 tagged (major_exchange, 69% cumul custody)",
                "0.729": "node-0035 tagged (major_exchange, 77% cumul custody)",
                "0.794": "node-0036 tagged (exchange,       82% cumul custody)",
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
    build_script  = BASE_DIR / "tools" / "sweep" / "2_build_configs.py"
    full_network  = (BASE_DIR / "networks" / "realistic-economy" / "network.yaml").resolve()

    cmd = [
        sys.executable, str(build_script),
        "--input",        str(scenarios_json_path),
        "--output-dir",   str(SWEEP_DIR),
        "--base-network", str(full_network),
    ]
    print(f"\nRunning 2_build_configs.py...")
    print(f"  Base network: {full_network}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print(f"\nERROR: 2_build_configs.py exited with code {result.returncode}")
        sys.exit(1)
    print("  Build complete.")


def split_manifests():
    manifest_path = SWEEP_DIR / "build_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    all_scenarios = manifest["scenarios"]
    assert len(all_scenarios) == 108, f"Expected 108 scenarios, got {len(all_scenarios)}"

    for suffix, subset in [("_server1", all_scenarios[:54]), ("_server2", all_scenarios[54:])]:
        out = dict(manifest)
        out["scenarios"] = subset
        out["metadata"]  = dict(manifest["metadata"])
        server_num = suffix.replace("_server", "")
        out["metadata"]["server"]     = f"server{server_num}"
        out["metadata"]["namespaces"] = (
            f"{NAMESPACE_PREFIX}-0 to {NAMESPACE_PREFIX}-5 (server{server_num})"
        )
        out_path = SWEEP_DIR / f"build_manifest{suffix}.json"
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2)

    print(f"  Wrote build_manifest_server1.json (sweep_0000–0053, E=0.25/0.45/0.58)")
    print(f"  Wrote build_manifest_server2.json (sweep_0054–0107, E=0.68/0.76/0.82)")


if __name__ == "__main__":
    print("Generating econ_split_full sweep...")
    print(f"  Grid: {len(E_VALUES)} E × {len(VIOLATION_RATES)} vr × "
          f"{len(C_VALUES)} C × {COMPOSITIONS} comp = "
          f"{len(E_VALUES)*len(VIOLATION_RATES)*len(C_VALUES)*COMPOSITIONS} scenarios")
    print(f"  Network: realistic-economy (full, 60 nodes)")
    print(f"  Namespace prefix: {NAMESPACE_PREFIX}-0 to {NAMESPACE_PREFIX}-11")

    scenarios = build_scenarios()
    assert len(scenarios) == 108

    print(f"\nScenario grid (C_eff spot-check, first 12):")
    for s in scenarios[:12]:
        print(f"  {s['scenario_id']}: E={s['economic_split']} vr={s['violation_rate']} "
              f"C={s['pool_committed_split']} comp={s['composition_index']} "
              f"seed={s['composition_seed']} "
              f"C_eff={s['committed_hashrate_actual']:.3f} "
              f"pools={s['committed_pool_ids_v27']}")

    print(f"\nServer split:")
    print(f"  Server 1: {scenarios[0]['scenario_id']} – {scenarios[53]['scenario_id']} "
          f"(E=0.25, 0.45, 0.58)")
    print(f"  Server 2: {scenarios[54]['scenario_id']} – {scenarios[107]['scenario_id']} "
          f"(E=0.68, 0.76, 0.82)")

    print("\nWriting scenarios.json...")
    scenarios_json = write_scenarios_json(scenarios)

    build_networks(scenarios_json)

    print("\nSplitting manifests by server...")
    split_manifests()

    net_count = len(list((SWEEP_DIR / "networks").glob("*/network.yaml")))
    cfg_count = len(list((SWEEP_DIR / "configs" / "network").glob("*.yaml")))
    print(f"\nVerification:")
    print(f"  Network YAMLs: {net_count}/108")
    print(f"  Config YAMLs:  {cfg_count}/108")
    print(f"\nDone.")
