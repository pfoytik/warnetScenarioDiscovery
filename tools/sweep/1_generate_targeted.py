#!/usr/bin/env python3
"""
Step 1b: Generate Targeted Grid Scenarios

Reads a YAML spec file defining fixed parameters and grid axes,
then generates all combinations (Cartesian product) as a scenarios.json
compatible with 2_build_configs.py.

Usage:
    python 1_generate_targeted.py --spec specs/targeted_sweep1_committed_threshold.yaml
    python 1_generate_targeted.py --spec specs/targeted_sweep1_committed_threshold.yaml --preview
    python 1_generate_targeted.py --spec specs/targeted_sweep1_committed_threshold.yaml --output my_sweep/scenarios.json

Output:
    scenarios.json (same format as 1_generate_scenarios.py output)

Spec file format (YAML):
    name: my_targeted_sweep
    description: "What this sweep is testing"

    fixed:
      hashrate_split: 0.25
      pool_neutral_pct: 30.0
      # ... all non-grid parameters

    grid:
      economic_split:       [0.35, 0.50, 0.60, 0.70, 0.82]
      pool_committed_split: [0.20, 0.30, 0.38, 0.43, 0.47, 0.52, 0.58, 0.65, 0.75]
"""

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


# All parameters required by 2_build_configs.py, with their valid ranges
# (used for validation warnings only — not enforced as hard errors)
REQUIRED_PARAMETERS = {
    "economic_split":              (0.0,  1.0,  "continuous"),
    "hashrate_split":              (0.0,  1.0,  "continuous"),
    "pool_ideology_strength":      (0.1,  0.9,  "continuous"),
    "pool_profitability_threshold":(0.02, 0.30, "continuous"),
    "pool_max_loss_pct":           (0.02, 0.50, "continuous"),
    "pool_committed_split":        (0.0,  1.0,  "continuous"),
    "pool_neutral_pct":            (10.0, 50.0, "continuous"),
    "econ_ideology_strength":      (0.0,  0.8,  "continuous"),
    "econ_switching_threshold":    (0.02, 0.25, "continuous"),
    "econ_inertia":                (0.05, 0.30, "continuous"),
    "user_ideology_strength":      (0.1,  0.9,  "continuous"),
    "user_switching_threshold":    (0.05, 0.20, "continuous"),
    "transaction_velocity":        (0.1,  0.9,  "continuous"),
    "user_nodes_per_partition":    (2,    10,   "discrete"),
    "economic_nodes_per_partition":(1,    3,    "discrete"),
    "solo_miner_hashrate":         (0.02, 0.15, "continuous"),
}


def load_spec(spec_path: Path) -> Dict:
    with open(spec_path) as f:
        return yaml.safe_load(f)


def validate_spec(spec: Dict) -> List[str]:
    """Validate spec and return list of warnings (not fatal errors)."""
    warnings = []

    fixed = spec.get("fixed", {})
    grid = spec.get("grid", {})

    # Check for overlap between fixed and grid
    overlap = set(fixed.keys()) & set(grid.keys())
    if overlap:
        warnings.append(f"Parameters in both fixed and grid sections: {overlap}")

    # Check all required parameters are covered
    covered = set(fixed.keys()) | set(grid.keys())
    missing = set(REQUIRED_PARAMETERS.keys()) - covered
    if missing:
        warnings.append(f"Required parameters not specified: {missing}")

    # Check for unknown parameters
    unknown = covered - set(REQUIRED_PARAMETERS.keys())
    if unknown:
        warnings.append(f"Unknown parameters (will be passed through): {unknown}")

    # Validate value ranges
    for param, value in fixed.items():
        if param not in REQUIRED_PARAMETERS:
            continue
        lo, hi, _ = REQUIRED_PARAMETERS[param]
        if not (lo <= float(value) <= hi):
            warnings.append(f"  {param}={value} is outside valid range [{lo}, {hi}]")

    for param, values in grid.items():
        if param not in REQUIRED_PARAMETERS:
            continue
        lo, hi, _ = REQUIRED_PARAMETERS[param]
        for v in values:
            if not (lo <= float(v) <= hi):
                warnings.append(f"  {param}={v} is outside valid range [{lo}, {hi}]")

    return warnings


def generate_scenarios(spec: Dict) -> List[Dict]:
    """Generate all Cartesian product combinations from the spec."""
    fixed = spec.get("fixed", {})
    grid = spec.get("grid", {})

    if not grid:
        # Edge case: no grid axes — single scenario with all fixed params
        scenario = {"scenario_id": "sweep_0000", **fixed}
        return [scenario]

    # Cartesian product of all grid axes
    grid_keys = list(grid.keys())
    grid_values = [grid[k] for k in grid_keys]

    scenarios = []
    for i, combo in enumerate(itertools.product(*grid_values)):
        scenario = {"scenario_id": f"sweep_{i:04d}"}
        # Fixed params first
        for k, v in fixed.items():
            scenario[k] = v
        # Then grid values (override if key collision — already warned in validate)
        for k, v in zip(grid_keys, combo):
            scenario[k] = v
        scenarios.append(scenario)

    return scenarios


def print_preview(spec: Dict, scenarios: List[Dict]):
    """Print a human-readable summary of the grid."""
    grid = spec.get("grid", {})
    fixed = spec.get("fixed", {})
    grid_keys = list(grid.keys())

    print(f"\nName:        {spec.get('name', '(unnamed)')}")
    print(f"Description: {spec.get('description', '')}")
    print(f"Scenarios:   {len(scenarios)} ({' × '.join(str(len(grid[k])) for k in grid_keys)})")
    print(f"Duration:    ~{len(scenarios) * 32 // 60}h {len(scenarios) * 32 % 60}m at 32 min/scenario")

    print(f"\nGrid axes:")
    for k in grid_keys:
        vals_str = ", ".join(str(v) for v in grid[k])
        print(f"  {k:<30} [{vals_str}]")

    print(f"\nFixed parameters:")
    for k, v in sorted(fixed.items()):
        print(f"  {k:<30} {v}")

    if len(grid_keys) == 2 and len(scenarios) <= 100:
        # Print a visual grid for 2D sweeps
        k1, k2 = grid_keys
        v1_vals = grid[k1]
        v2_vals = grid[k2]

        print(f"\nGrid layout ({k1} × {k2}):")
        header = f"  {'':6}" + "".join(f"{v:>8.3f}" for v in v2_vals)
        print(f"  {k1} \\ {k2}")
        print(header)
        print("  " + "-" * len(header))
        for v1 in v1_vals:
            row = f"  {v1:6.3f} "
            for v2 in v2_vals:
                # Find matching scenario
                match = next((s for s in scenarios
                              if abs(s[k1] - v1) < 1e-9 and abs(s[k2] - v2) < 1e-9), None)
                row += f"  {match['scenario_id'].replace('sweep_',''):>6}" if match else "       ?"
            print(row)


def main():
    parser = argparse.ArgumentParser(
        description="Generate targeted grid scenarios for parameter sweep",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--spec", "-s", required=True,
                        help="Path to YAML spec file")
    parser.add_argument("--output", "-o", default=None,
                        help="Output scenarios.json path (default: <spec_dir>/<name>/scenarios.json)")
    parser.add_argument("--preview", action="store_true",
                        help="Print preview without saving")

    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: Spec file not found: {spec_path}")
        sys.exit(1)

    print(f"Loading spec from {spec_path}...")
    spec = load_spec(spec_path)

    # Validate
    warnings = validate_spec(spec)
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  ! {w}")
        # Only fatal if required params are missing
        fixed_and_grid = set(spec.get("fixed", {}).keys()) | set(spec.get("grid", {}).keys())
        missing = set(REQUIRED_PARAMETERS.keys()) - fixed_and_grid
        if missing:
            print(f"\nError: Missing required parameters: {missing}")
            sys.exit(1)

    # Generate
    scenarios = generate_scenarios(spec)
    print(f"\nGenerated {len(scenarios)} scenarios")

    # Preview
    print_preview(spec, scenarios)

    if args.preview:
        print("\n(Preview only — use without --preview to save)")
        return

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        sweep_name = spec.get("name", spec_path.stem)
        output_path = spec_path.parent.parent / sweep_name / "scenarios.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "type": "targeted_grid",
            "name": spec.get("name", spec_path.stem),
            "description": spec.get("description", ""),
            "spec_file": str(spec_path),
            "n_samples": len(scenarios),
            "n_parameters": len(REQUIRED_PARAMETERS),
            "grid_axes": {k: list(v) for k, v in spec.get("grid", {}).items()},
            "fixed_parameters": spec.get("fixed", {}),
            "parameters": [
                {"name": k, "min": lo, "max": hi, "type": t, "role": "grid" if k in spec.get("grid", {}) else "fixed"}
                for k, (lo, hi, t) in REQUIRED_PARAMETERS.items()
            ],
        },
        "scenarios": scenarios,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved {len(scenarios)} scenarios to: {output_path}")
    sweep_dir = output_path.parent
    print(f"\nNext steps:")
    print(f"  python 2_build_configs.py --input {output_path} --output-dir {sweep_dir} --base-network <network.yaml>")
    print(f"  python 3_run_sweep.py --input {sweep_dir}/build_manifest.json --duration 1800 --interval 2")


if __name__ == "__main__":
    main()
