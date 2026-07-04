#!/usr/bin/env python3
"""
Generate all config files for the chainsplit_persistence sweep.

36 scenarios: 6 violation_rates × 3 C values × 2 replications
Research question: minimum violation_rate for persistent chainsplit under weakest cascade conditions
"""
import json
import os
from pathlib import Path
import yaml

SWEEP_DIR = Path(__file__).parent
CONFIGS_NET = SWEEP_DIR / "configs" / "network"
CONFIGS_POOL = SWEEP_DIR / "configs" / "pools"
CONFIGS_ECON = SWEEP_DIR / "configs" / "economic"

VIOLATION_RATES = [0.05, 0.10, 0.20, 0.30, 0.50, 1.00]
C_VALUES       = [0.15, 0.30, 0.60]
REPLICATIONS   = [0, 1]

ECONOMIC_SPLIT = 0.55   # key change vs FFT (was 0.65)
HASHRATE_SPLIT = 0.25
POOL_NEUTRAL_PCT = 30.0
POOL_IDEOLOGY = 0.51
POOL_MAX_LOSS = 0.26
POOL_PROFITABILITY = 0.16

# Lite network pools in network order (determines fork_preference via midpoint logic)
LITE_POOLS = [
    ("pool-foundryusa", "Foundry USA",  30.0, "v27"),
    ("pool-marapool",   "MARA Pool",     4.6, "v27"),
    ("pool-luxor",      "Luxor",          2.3, "v27"),
    ("pool-ocean",      "Ocean",          1.2, "v27"),
    ("pool-antpool",    "AntPool",       16.9, "v26"),
    ("pool-f2pool",     "F2Pool",        10.9, "v26"),
    ("pool-viabtc",     "ViaBTC",        11.2, "v26"),
    ("pool-spiderpool", "SpiderPool",     9.3, "v26"),
]
TOTAL_POOL_HR = sum(p[2] for p in LITE_POOLS)  # 86.4


def pool_config_for_c(c_value):
    """Generate pool list for a given C value using 2_build_configs.py midpoint logic."""
    neutral_pct = POOL_NEUTRAL_PCT / 100.0
    committed_pct = 1.0 - neutral_pct
    v27_pct = committed_pct * c_value
    v26_pct = committed_pct * (1.0 - c_value)

    pools = []
    cumulative = 0.0
    for pool_id, pool_name, hashrate, initial_fork in LITE_POOLS:
        midpoint = (cumulative + hashrate / 2.0) / TOTAL_POOL_HR
        if midpoint < v27_pct:
            pref = "v27"
        elif midpoint < v27_pct + v26_pct:
            pref = "v26"
        else:
            pref = "neutral"

        ideology = 0.1 if pref == "neutral" else POOL_IDEOLOGY
        max_loss  = 0.02 if pref == "neutral" else POOL_MAX_LOSS

        pools.append({
            "pool_id": pool_id,
            "pool_name": pool_name,
            "hashrate_pct": hashrate,
            "fork_preference": pref,
            "initial_fork": initial_fork,
            "ideology_strength": round(ideology, 3),
            "profitability_threshold": POOL_PROFITABILITY,
            "max_loss_pct": round(max_loss, 3),
        })
        cumulative += hashrate
    return pools


def build_scenarios():
    scenarios = []
    idx = 0
    for vr in VIOLATION_RATES:
        for c in C_VALUES:
            for rep in REPLICATIONS:
                sid = f"sweep_{idx:04d}"
                prob = round(1.0 - vr, 2)
                scenarios.append({
                    "scenario_id": sid,
                    "violation_rate": vr,
                    "pool_committed_split": c,
                    "replication": rep,
                    "v26_acceptance_probability": prob,
                })
                idx += 1
    return scenarios


def write_network_yamls(scenarios):
    for s in scenarios:
        sid = s["scenario_id"]
        vr  = s["violation_rate"]
        c   = s["pool_committed_split"]
        rep = s["replication"]
        cfg = {
            "name": sid,
            "description": (
                f"Chainsplit persistence sweep {sid} "
                f"(violation_rate={vr}, C={c}, rep={rep}, economic_split={ECONOMIC_SPLIT})"
            ),
            "v27_economic_pct": round(ECONOMIC_SPLIT * 100, 1),
            "v27_hashrate_pct": round(HASHRATE_SPLIT * 100, 1),
            "economic_nodes_per_partition": 2,
            "user_nodes_per_partition": 6,
            "econ_neutral_fraction": 0.0,
            "v27_economic": {
                "fork_preference": "v27",
                "ideology_strength": 0.4,
                "switching_threshold": 0.1,
                "inertia": 0.05,
                "activity_type": "transactional",
                "transaction_velocity": 0.5,
            },
            "v26_economic": {
                "fork_preference": "v26",
                "ideology_strength": 0.4,
                "switching_threshold": 0.1,
                "inertia": 0.05,
                "activity_type": "transactional",
                "transaction_velocity": 0.5,
            },
            "user_config": {
                "fork_preference": "neutral",
                "ideology_strength": 0.49,
                "switching_threshold": 0.12,
                "inertia": 0.05,
                "activity_type": "mixed",
                "transaction_velocity": 0.5,
                "is_solo_miner": True,
                "hashrate_pct": 0.085,
            },
            "partition_mode": "static",
            "fork_observer_enabled": False,
        }
        out = CONFIGS_NET / f"{sid}.yaml"
        with open(out, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
    print(f"  Wrote {len(scenarios)} network YAMLs")


def write_pool_config(scenarios):
    pool_data = {}
    for s in scenarios:
        sid = s["scenario_id"]
        c   = s["pool_committed_split"]
        pools = pool_config_for_c(c)
        pool_data[sid] = {
            "description": f"Pool scenario for {sid}",
            "pools": pools,
        }
    out = CONFIGS_POOL / "sweep_pools_config.yaml"
    with open(out, "w") as f:
        yaml.dump(pool_data, f, default_flow_style=False, sort_keys=False)
    print(f"  Wrote pool config ({len(pool_data)} entries)")


def write_economic_config(scenarios):
    econ_data = {}
    for s in scenarios:
        sid = s["scenario_id"]
        econ_data[sid] = {
            "description": f"Economic scenario for {sid}",
            "v27_economic_pct": ECONOMIC_SPLIT * 100,
            "v26_economic_pct": (1.0 - ECONOMIC_SPLIT) * 100,
        }
    out = CONFIGS_ECON / "sweep_economic_config.yaml"
    with open(out, "w") as f:
        yaml.dump(econ_data, f, default_flow_style=False, sort_keys=False)
    print(f"  Wrote economic config")


FIXED_PARAMS = {
    "economic_split": ECONOMIC_SPLIT,
    "hashrate_split": HASHRATE_SPLIT,
    "pool_neutral_pct": POOL_NEUTRAL_PCT,
    "pool_profitability_threshold": POOL_PROFITABILITY,
    "pool_ideology_strength": POOL_IDEOLOGY,
    "pool_max_loss_pct": POOL_MAX_LOSS,
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


def make_manifest_scenarios(scenarios, sweep_name):
    result = []
    for s in scenarios:
        sid = s["scenario_id"]
        vr  = s["violation_rate"]
        c   = s["pool_committed_split"]
        rep = s["replication"]
        prob = s["v26_acceptance_probability"]
        params = dict(FIXED_PARAMS)
        params.update({
            "scenario_id": sid,
            "v26_acceptance_probability": prob,
            "pool_committed_split": c,
            "replication": rep,
            "violation_rate": vr,
            "partition_mode": "unified",
            "fork_heal_exit": True,
            "description": (
                f"Chainsplit persistence sweep {sid} "
                f"(violation_rate={vr} C={c} rep={rep})"
            ),
        })
        result.append({
            "scenario_id": sid,
            "parameters": params,
            "network_config": f"tools/sweep/{sweep_name}/configs/network/{sid}.yaml",
            "network_path": f"networks/{sid}/network.yaml",
        })
    return result


DESCRIPTION = """Chainsplit Persistence Sweep

PURPOSE: Determine the minimum fraction of v26 blocks that must violate v27 rules
to cause a persistent chainsplit, under the weakest possible cascade conditions.

Prior sweeps (softfork_rule_strength, fork_formation_threshold) used economic_split=0.65
and found zero sustained chainsplits. This sweep reduces economic_split to 0.55 (minimum
interesting) to weaken the cascade mechanism and give v26 its best chance of sustaining
a split. The pool switching chain-state leak bug has also been fixed (invalidateblock
before addnode), eliminating spurious healing events.

RESEARCH QUESTIONS:
  1. Primary: At what violation_rate does a chainsplit form AND persist (never heals)?
  2. Secondary: How does C (pool committed split) affect that persistence threshold?
     At C=0.15 (all major pools v26), is persistence easier than at C=0.30 (Foundry v27)?
  3. If persistence occurs at some C + vr, what does that imply about minimum
     hashrate and economic support needed for a real-world sustained fork?

KEY DESIGN CHANGES vs fork_formation_threshold:
  - economic_split: 0.55 (vs 0.65) → weaker cascade; v26 has better shot at holding
  - violation_rates: 6 values (0.05–1.00) focused on threshold zone
  - replications: 2 (vs 3); scenarios: 36 (vs 90) → fits in 12h
  - Pool switching bug FIXED: switching node now abandons old chain before re-connecting

POOL LANDSCAPE (same lite network, same C thresholds):
  C=0.15: All major pools (Foundry+MARA+Luxor+Ocean+AntPool+F2Pool) prefer v26
  C=0.30: Foundry (30%) prefers v27; all others prefer v26/neutral
  C=0.60: Foundry+MARA+Luxor (36.9%) prefer v27; Ocean+AntPool+F2Pool prefer v26

TIMING: 3 scenarios/namespace x 3.6h max = 10.8h worst case (under 12h).
Healing scenarios exit early via --fork-heal-exit, shortening typical run.

SERVER SPLIT:
  Server 1: namespaces csp-0 to csp-5 (sweep_0000–sweep_0017)
  Server 2: namespaces csp-0 to csp-5 (sweep_0018–sweep_0035)
"""


def write_manifests(scenarios, sweep_name):
    manifest_scenarios = make_manifest_scenarios(scenarios, sweep_name)

    full_manifest = {
        "metadata": {
            "type": "targeted_grid",
            "name": sweep_name,
            "description": DESCRIPTION,
            "base_network": "lite",
            "n_samples": len(scenarios),
            "server": "all",
            "namespaces": "csp-0 to csp-5 (both servers)",
            "grid_axes": {
                "violation_rate": VIOLATION_RATES,
                "pool_committed_split": C_VALUES,
                "replications": len(REPLICATIONS),
            },
            "fixed_parameters": FIXED_PARAMS,
            "new_scenario_flags": [
                "--partition-mode=unified",
                "--fork-heal-detection",
                "--fork-heal-exit",
            ],
        },
        "scenarios": manifest_scenarios,
    }

    with open(SWEEP_DIR / "build_manifest.json", "w") as f:
        json.dump(full_manifest, f, indent=2)

    # Server 1: scenarios 0–17
    s1 = dict(full_manifest)
    s1 = json.loads(json.dumps(full_manifest))
    s1["metadata"]["server"] = "server1"
    s1["metadata"]["namespaces"] = "csp-0 to csp-5 (server1)"
    s1["scenarios"] = manifest_scenarios[:18]
    with open(SWEEP_DIR / "build_manifest_server1.json", "w") as f:
        json.dump(s1, f, indent=2)

    # Server 2: scenarios 18–35
    s2 = json.loads(json.dumps(full_manifest))
    s2["metadata"]["server"] = "server2"
    s2["metadata"]["namespaces"] = "csp-0 to csp-5 (server2)"
    s2["scenarios"] = manifest_scenarios[18:]
    with open(SWEEP_DIR / "build_manifest_server2.json", "w") as f:
        json.dump(s2, f, indent=2)

    print(f"  Wrote build_manifest.json, build_manifest_server1.json, build_manifest_server2.json")


def write_run_commands(scenarios):
    """Write run_commands.sh with 3 scenarios per namespace, 12 namespaces."""
    lines = [
        "#!/bin/bash",
        "# Chainsplit Persistence Sweep — Run Commands",
        "# 36 scenarios across 2 servers x 6 namespaces each (3 scenarios per namespace)",
        "# Worst case: 3 x 3.6h = 10.8h per namespace (under 12h)",
        "",
        "# ============================================================",
        "# SERVER 1 (sweep_0000–sweep_0017)",
        "# ============================================================",
        "",
    ]

    # Server 1: 6 namespaces, 3 scenarios each, sweeps 0-17
    ns_ranges_s1 = [
        (0, 0, 2),
        (1, 3, 5),
        (2, 6, 8),
        (3, 9, 11),
        (4, 12, 14),
        (5, 15, 17),
    ]
    for ns_idx, start, end in ns_ranges_s1:
        ids = [f"sweep_{i:04d}" for i in range(start, end + 1)]
        comment = f"# csp-{ns_idx} — 3 scenarios (sweep_{start:04d}–sweep_{end:04d})"
        cmd = (
            f"python3 tools/sweep/3_run_sweep.py \\\n"
            f"  --input tools/sweep/chainsplit_persistence/build_manifest_server1.json \\\n"
            f"  --duration 13000 \\\n"
            f"  --interval 2 \\\n"
            f"  --retarget-interval 2016 \\\n"
            f"  --results-dir tools/sweep/chainsplit_persistence/results_server1 \\\n"
            f"  --namespace csp-{ns_idx} \\\n"
            f"  --startup-wait 60 \\\n"
            f"  --cooldown 30 \\\n"
            f"  --no-auto-restart \\\n"
            f"  --scenarios $(printf \"sweep_%04d \" $(seq {start} {end}))"
        )
        lines.extend([comment, cmd, ""])

    lines += [
        "# ============================================================",
        "# SERVER 2 (sweep_0018–sweep_0035)",
        "# ============================================================",
        "",
    ]

    # Server 2: 6 namespaces, 3 scenarios each, sweeps 18-35
    ns_ranges_s2 = [
        (0, 18, 20),
        (1, 21, 23),
        (2, 24, 26),
        (3, 27, 29),
        (4, 30, 32),
        (5, 33, 35),
    ]
    for ns_idx, start, end in ns_ranges_s2:
        comment = f"# csp-{ns_idx} — 3 scenarios (sweep_{start:04d}–sweep_{end:04d})"
        cmd = (
            f"python3 tools/sweep/3_run_sweep.py \\\n"
            f"  --input tools/sweep/chainsplit_persistence/build_manifest_server2.json \\\n"
            f"  --duration 13000 \\\n"
            f"  --interval 2 \\\n"
            f"  --retarget-interval 2016 \\\n"
            f"  --results-dir tools/sweep/chainsplit_persistence/results_server2 \\\n"
            f"  --namespace csp-{ns_idx} \\\n"
            f"  --startup-wait 60 \\\n"
            f"  --cooldown 30 \\\n"
            f"  --no-auto-restart \\\n"
            f"  --scenarios $(printf \"sweep_%04d \" $(seq {start} {end}))"
        )
        lines.extend([comment, cmd, ""])

    out = SWEEP_DIR / "run_commands.sh"
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    out.chmod(0o755)
    print(f"  Wrote run_commands.sh")


if __name__ == "__main__":
    print("Generating chainsplit_persistence sweep...")
    scenarios = build_scenarios()

    print(f"\n{len(scenarios)} scenarios:")
    for s in scenarios:
        print(f"  {s['scenario_id']}: vr={s['violation_rate']} C={s['pool_committed_split']} rep={s['replication']}")

    print("\nPool configs (spot check):")
    for c in C_VALUES:
        pools = pool_config_for_c(c)
        v27 = [p["pool_name"] for p in pools if p["fork_preference"] == "v27"]
        v26 = [p["pool_name"] for p in pools if p["fork_preference"] == "v26"]
        neutral = [p["pool_name"] for p in pools if p["fork_preference"] == "neutral"]
        v27_hr = sum(p["hashrate_pct"] for p in pools if p["fork_preference"] == "v27")
        v26_hr = sum(p["hashrate_pct"] for p in pools if p["fork_preference"] == "v26")
        print(f"  C={c}: v27=[{', '.join(v27)}]({v27_hr:.1f}%) v26=[{', '.join(v26)}]({v26_hr:.1f}%) neutral={neutral}")

    print("\nWriting files...")
    write_network_yamls(scenarios)
    write_pool_config(scenarios)
    write_economic_config(scenarios)
    write_manifests(scenarios, "chainsplit_persistence")
    write_run_commands(scenarios)

    print("\nDone.")
