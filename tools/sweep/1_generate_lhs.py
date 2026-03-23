#!/usr/bin/env python3
"""
Step 1c: Generate LHS Parameter Scenarios with Fixed Parameters

Generates Latin Hypercube Sampling scenarios that vary specified parameters
while keeping others fixed. This is useful when you want proportional coverage
of a subset of parameters (e.g., for feature importance analysis).

Usage:
    # Generate from spec file
    python 1_generate_lhs.py --spec specs/lhs_2016_full_parameter.yaml

    # Preview without saving
    python 1_generate_lhs.py --spec specs/lhs_2016_full_parameter.yaml --preview

    # Override number of samples
    python 1_generate_lhs.py --spec specs/lhs_2016_full_parameter.yaml --samples 100

    # Custom output directory
    python 1_generate_lhs.py --spec specs/lhs_2016_full_parameter.yaml --output my_lhs_sweep

Spec file format (YAML):
    name: my_lhs_sweep
    description: "What this sweep is testing"
    network: lite  # 'lite', 'full', or explicit path
    n_samples: 64  # Number of LHS samples
    seed: 42       # Random seed for reproducibility (optional)

    # Parameters to vary via LHS
    parameters:
      economic_split:
        min: 0.30
        max: 0.80
      pool_committed_split:
        min: 0.15
        max: 0.70

    # Parameters to keep fixed
    fixed:
      hashrate_split: 0.25
      pool_neutral_pct: 30.0

Output:
    <output_dir>/scenarios.json - Array of parameter combinations
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import yaml

try:
    from scipy.stats import qmc
except ImportError:
    print("Error: scipy is required. Install with: pip install scipy")
    sys.exit(1)


# All parameters that 2_build_configs.py expects
REQUIRED_PARAMETERS = {
    "economic_split",
    "hashrate_split",
    "pool_ideology_strength",
    "pool_profitability_threshold",
    "pool_max_loss_pct",
    "pool_committed_split",
    "pool_neutral_pct",
    "econ_ideology_strength",
    "econ_switching_threshold",
    "econ_inertia",
    "user_ideology_strength",
    "user_switching_threshold",
    "transaction_velocity",
    "user_nodes_per_partition",
    "economic_nodes_per_partition",
    "solo_miner_hashrate",
}

# Default fixed values (can be overridden in spec)
DEFAULT_FIXED = {
    'hashrate_split': 0.25,
    'pool_neutral_pct': 30.0,
    'pool_profitability_threshold': 0.16,
    'econ_ideology_strength': 0.40,
    'econ_switching_threshold': 0.10,
    'econ_inertia': 0.05,
    'user_ideology_strength': 0.49,
    'user_switching_threshold': 0.12,
    'user_nodes_per_partition': 6,
    'economic_nodes_per_partition': 2,
    'transaction_velocity': 0.5,
    'solo_miner_hashrate': 0.085,
}


def load_spec(spec_path: Path) -> Dict:
    """Load and validate spec file."""
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    # Validate required fields
    if 'parameters' not in spec:
        raise ValueError("Spec must have 'parameters' section with min/max ranges")

    if 'name' not in spec:
        spec['name'] = spec_path.stem

    return spec


def validate_spec(spec: Dict) -> List[str]:
    """Validate spec and return list of warnings."""
    warnings = []

    lhs_params = set(spec.get('parameters', {}).keys())
    fixed_params = set(spec.get('fixed', {}).keys())

    # Check for overlap
    overlap = lhs_params & fixed_params
    if overlap:
        warnings.append(f"Parameters in both 'parameters' and 'fixed': {overlap}")

    # Check coverage of required parameters
    covered = lhs_params | fixed_params | set(DEFAULT_FIXED.keys())
    missing = REQUIRED_PARAMETERS - covered
    if missing:
        warnings.append(f"Missing parameters (will use defaults): {missing}")

    # Check parameter ranges
    for param, config in spec.get('parameters', {}).items():
        if 'min' not in config or 'max' not in config:
            warnings.append(f"Parameter '{param}' missing min/max")
        elif config['min'] >= config['max']:
            warnings.append(f"Parameter '{param}' has invalid range: [{config['min']}, {config['max']}]")

    return warnings


def generate_lhs_scenarios(
    lhs_params: Dict[str, Tuple[float, float]],
    fixed_params: Dict[str, Any],
    n_samples: int,
    seed: int = 42
) -> List[Dict]:
    """Generate LHS scenarios."""

    # Generate LHS samples
    sampler = qmc.LatinHypercube(d=len(lhs_params), seed=seed)
    samples = sampler.random(n=n_samples)

    # Scale to parameter ranges
    param_names = list(lhs_params.keys())
    scenarios = []

    for i, sample in enumerate(samples):
        scenario = {
            'scenario_id': f'sweep_{i:04d}',
        }

        # Add LHS-sampled parameters
        for j, param in enumerate(param_names):
            lo, hi = lhs_params[param]
            scenario[param] = round(lo + sample[j] * (hi - lo), 4)

        # Add fixed parameters
        scenario.update(fixed_params)

        scenarios.append(scenario)

    return scenarios


def main():
    parser = argparse.ArgumentParser(
        description="Generate LHS parameter scenarios with fixed parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--spec", "-s", type=str, required=True,
                        help="Path to YAML spec file")
    parser.add_argument("--samples", "-n", type=int, default=None,
                        help="Override number of samples from spec")
    parser.add_argument("--seed", type=int, default=None,
                        help="Override random seed from spec")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output directory (default: <spec_name>/)")
    parser.add_argument("--preview", action="store_true",
                        help="Preview scenarios without saving")

    args = parser.parse_args()

    # Load spec
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

    # Extract LHS parameters
    lhs_params = {}
    for param, config in spec.get('parameters', {}).items():
        lhs_params[param] = (config['min'], config['max'])

    # Build fixed parameters (defaults + spec overrides)
    fixed_params = DEFAULT_FIXED.copy()
    fixed_params.update(spec.get('fixed', {}))

    # Remove any LHS params from fixed (in case of overlap)
    for param in lhs_params:
        fixed_params.pop(param, None)

    # Get sample count and seed
    n_samples = args.samples or spec.get('n_samples', 64)
    seed = args.seed or spec.get('seed', 42)

    print(f"\nGenerating {n_samples} LHS scenarios...")
    print(f"  LHS parameters: {list(lhs_params.keys())}")
    print(f"  Fixed parameters: {len(fixed_params)}")
    print(f"  Seed: {seed}")

    # Generate scenarios
    scenarios = generate_lhs_scenarios(lhs_params, fixed_params, n_samples, seed)

    # Show parameter coverage
    print(f"\nParameter coverage:")
    for param in lhs_params:
        values = [s[param] for s in scenarios]
        print(f"  {param}: [{min(values):.3f}, {max(values):.3f}]")

    # Preview
    print(f"\nFirst 5 scenarios:")
    for s in scenarios[:5]:
        lhs_str = ", ".join(f"{k}={s[k]:.2f}" for k in lhs_params)
        print(f"  {s['scenario_id']}: {lhs_str}")

    if args.preview:
        print("\n[Preview mode - not saving]")
        return

    # Create output structure
    output = {
        'metadata': {
            'type': 'lhs',
            'name': spec['name'],
            'description': spec.get('description', ''),
            'spec_file': str(spec_path),
            'base_network': spec.get('network', 'lite'),
            'n_samples': n_samples,
            'n_parameters': len(lhs_params) + len(fixed_params),
            'seed': seed,
            'lhs_params': {k: list(v) for k, v in lhs_params.items()},
            'fixed_parameters': fixed_params,
            'parameters': [
                {'name': k, 'min': v[0], 'max': v[1], 'type': 'continuous', 'role': 'lhs'}
                for k, v in lhs_params.items()
            ] + [
                {'name': k, 'value': v, 'role': 'fixed'}
                for k, v in fixed_params.items()
            ]
        },
        'scenarios': scenarios
    }

    # Determine output path
    output_dir = Path(args.output) if args.output else Path(spec['name'])
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'scenarios.json'

    # Save
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {n_samples} scenarios to: {output_path}")
    print(f"\nNext step: python 2_build_configs.py --input {output_path} --output-dir {output_dir}")


if __name__ == "__main__":
    main()
