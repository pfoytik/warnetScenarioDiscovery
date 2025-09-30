#!/usr/bin/env python3
"""
Batch Generator for Warnet Test Scenarios

Generates multiple network configurations for different test phases and scenarios.
Maps to the testing plan phases defined in the research plan.

Usage:
    python generate_test_scenarios.py --phase 1
    python generate_test_scenarios.py --phase 2 --output-dir ./scenarios
    python generate_test_scenarios.py --all
"""

import argparse
import os
import yaml
from pathlib import Path
from typing import List, Dict


class ScenarioGenerator:
    """Generate test scenario configurations"""
    
    def __init__(self, output_dir: str = "./scenarios"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_phase1_baseline(self) -> List[Dict]:
        """
        Phase 1: Baseline Establishment
        Homogeneous networks with default settings
        """
        scenarios = []
        
        # Baseline scenario - all nodes identical
        scenarios.append({
            'name': 'phase1_baseline_small',
            'description': 'Small baseline network (20 nodes, all v29.0, default config)',
            'config': {
                'network_parameters': {
                    'num_nodes': 20,
                    'topology_type': 'scale_free',
                    'seed': 1000,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'warnet_settings': {
                    'caddy_enabled': True,
                    'fork_observer': {'enabled': True, 'interval': 20},
                },
                'output': {
                    'file': 'phase1_baseline_small.yaml',
                    'name_prefix': 'base-small',
                }
            }
        })
        
        # Medium baseline
        scenarios.append({
            'name': 'phase1_baseline_medium',
            'description': 'Medium baseline network (50 nodes)',
            'config': {
                'network_parameters': {
                    'num_nodes': 50,
                    'topology_type': 'scale_free',
                    'seed': 1001,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'warnet_settings': {
                    'caddy_enabled': True,
                    'fork_observer': {'enabled': True, 'interval': 20},
                },
                'output': {
                    'file': 'phase1_baseline_medium.yaml',
                    'name_prefix': 'base-med',
                }
            }
        })
        
        # Large baseline
        scenarios.append({
            'name': 'phase1_baseline_large',
            'description': 'Large baseline network (100 nodes)',
            'config': {
                'network_parameters': {
                    'num_nodes': 100,
                    'topology_type': 'scale_free',
                    'seed': 1002,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'warnet_settings': {
                    'caddy_enabled': True,
                    'fork_observer': {'enabled': True, 'interval': 20},
                },
                'output': {
                    'file': 'phase1_baseline_large.yaml',
                    'name_prefix': 'base-large',
                }
            }
        })
        
        return scenarios
    
    def generate_phase2_single_variable(self) -> List[Dict]:
        """
        Phase 2: Single-Variable Perturbation
        Test one variable at a time
        """
        scenarios = []
        base_size = 50
        
        # Scenario 2.1: Version Mix (90% latest + 10% previous)
        scenarios.append({
            'name': 'phase2_version_mix_10pct',
            'description': '90% v29.0 + 10% v28.1',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 2001,
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.9,
                        '28.1': 0.1,
                    },
                    'clustering_factor': 0.0,
                },
                'output': {
                    'file': 'phase2_version_mix_10pct.yaml',
                    'name_prefix': 'v-mix-10',
                }
            }
        })
        
        # Scenario 2.2: Version Mix (80% + 20%)
        scenarios.append({
            'name': 'phase2_version_mix_20pct',
            'description': '80% v29.0 + 20% v28.1',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 2002,
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.8,
                        '28.1': 0.2,
                    },
                    'clustering_factor': 0.0,
                },
                'output': {
                    'file': 'phase2_version_mix_20pct.yaml',
                    'name_prefix': 'v-mix-20',
                }
            }
        })
        
        # Scenario 2.3: Memory Constraints (80% default + 20% low memory)
        scenarios.append({
            'name': 'phase2_memory_constrained',
            'description': '80% default memory + 20% low memory (50MB)',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 2003,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'maxmempool': {
                        'distribution': {
                            300: 0.8,
                            50: 0.2,
                        }
                    }
                },
                'output': {
                    'file': 'phase2_memory_constrained.yaml',
                    'name_prefix': 'mem-low',
                }
            }
        })
        
        # Scenario 2.4: Connection Limits
        scenarios.append({
            'name': 'phase2_connection_limited',
            'description': '80% default + 20% high connection limit',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 2004,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'maxconnections': {
                        'distribution': {
                            125: 0.8,
                            1000: 0.2,
                        }
                    }
                },
                'output': {
                    'file': 'phase2_connection_limited.yaml',
                    'name_prefix': 'conn-high',
                }
            }
        })
        
        # Scenario 2.5: Fee Policy Variation
        scenarios.append({
            'name': 'phase2_high_min_relay_fee',
            'description': '80% default + 20% high minimum relay fee',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 2005,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'minrelaytxfee': {
                        'distribution': {
                            0.001: 0.8,
                            0.01: 0.2,
                        }
                    }
                },
                'output': {
                    'file': 'phase2_high_min_relay_fee.yaml',
                    'name_prefix': 'fee-high',
                }
            }
        })
        
        # Scenario 2.6: Blocks-only nodes
        scenarios.append({
            'name': 'phase2_blocksonly_nodes',
            'description': '80% full relay + 20% blocks-only',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 2006,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'blocksonly': {
                        'distribution': {
                            'false': 0.8,
                            'true': 0.2,
                        }
                    }
                },
                'output': {
                    'file': 'phase2_blocksonly_nodes.yaml',
                    'name_prefix': 'blocks-only',
                }
            }
        })
        
        return scenarios
    
    def generate_phase3_multi_variable(self) -> List[Dict]:
        """
        Phase 3: Multi-Variable Combinations
        Test interactions between variables
        """
        scenarios = []
        base_size = 60
        
        # Scenario 3.1: Low-resource nodes + Version mix
        scenarios.append({
            'name': 'phase3_low_resource_version_mix',
            'description': 'Low memory + version mix + connection limits',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 3001,
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.6,
                        '28.1': 0.3,
                        '27.2': 0.1,
                    },
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'maxmempool': {
                        'distribution': {
                            50: 0.3,
                            300: 0.5,
                            1000: 0.2,
                        }
                    },
                    'maxconnections': {
                        'distribution': {
                            8: 0.2,
                            125: 0.7,
                            1000: 0.1,
                        }
                    }
                },
                'output': {
                    'file': 'phase3_low_resource_version_mix.yaml',
                    'name_prefix': 'multi-low-res',
                }
            }
        })
        
        # Scenario 3.2: Version mix + Clustered deployment
        scenarios.append({
            'name': 'phase3_version_clustered',
            'description': 'Version mix with high clustering (version segregation)',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 3002,
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.5,
                        '28.1': 0.3,
                        '27.2': 0.2,
                    },
                    'clustering_factor': 0.8,  # High clustering
                },
                'output': {
                    'file': 'phase3_version_clustered.yaml',
                    'name_prefix': 'v-clustered',
                }
            }
        })
        
        # Scenario 3.3: Hub-spoke + Mixed policies
        scenarios.append({
            'name': 'phase3_hub_spoke_mixed_policy',
            'description': 'Hub-and-spoke topology with mixed relay policies',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'hub_spoke',
                    'seed': 3003,
                    'topology_params': {
                        'hub_ratio': 0.15,
                        'hub_connections': [3, 5],
                        'spoke_connections': [3, 5],
                    }
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.6,
                        '28.1': 0.4,
                    },
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'blocksonly': {
                        'distribution': {
                            'false': 0.7,
                            'true': 0.3,
                        }
                    },
                    'maxmempool': {
                        'distribution': {
                            50: 0.2,
                            300: 0.6,
                            1000: 0.2,
                        }
                    }
                },
                'output': {
                    'file': 'phase3_hub_spoke_mixed_policy.yaml',
                    'name_prefix': 'hub-mixed',
                }
            }
        })
        
        # Scenario 3.4: Memory pressure + Fee variations
        scenarios.append({
            'name': 'phase3_memory_fee_pressure',
            'description': 'Low memory nodes with varied fee policies',
            'config': {
                'network_parameters': {
                    'num_nodes': base_size,
                    'topology_type': 'scale_free',
                    'seed': 3004,
                },
                'version_configuration': {
                    'distribution': {'29.0': 1.0},
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'maxmempool': {
                        'distribution': {
                            50: 0.4,
                            300: 0.4,
                            1000: 0.2,
                        }
                    },
                    'minrelaytxfee': {
                        'distribution': {
                            0.00001: 0.2,
                            0.001: 0.5,
                            0.01: 0.3,
                        }
                    },
                    'mempoolexpiry': {
                        'distribution': {
                            1: 0.3,
                            72: 0.5,
                            336: 0.2,
                        }
                    }
                },
                'output': {
                    'file': 'phase3_memory_fee_pressure.yaml',
                    'name_prefix': 'mem-fee',
                }
            }
        })
        
        return scenarios
    
    def generate_phase4_stress_test(self) -> List[Dict]:
        """
        Phase 4: Stress Testing
        Extreme scenarios to find breaking points
        """
        scenarios = []
        
        # Scenario 4.1: Very old versions in modern network
        scenarios.append({
            'name': 'phase4_legacy_versions',
            'description': 'Mix of very old and new versions',
            'config': {
                'network_parameters': {
                    'num_nodes': 80,
                    'topology_type': 'scale_free',
                    'seed': 4001,
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.3,
                        '27.2': 0.2,
                        '26.0': 0.2,
                        '25.0': 0.2,
                        '24.0': 0.1,
                    },
                    'clustering_factor': 0.7,  # Old versions cluster
                },
                'output': {
                    'file': 'phase4_legacy_versions.yaml',
                    'name_prefix': 'stress-legacy',
                }
            }
        })
        
        # Scenario 4.2: Extreme resource constraints
        scenarios.append({
            'name': 'phase4_extreme_constraints',
            'description': 'Majority of nodes with severe resource limits',
            'config': {
                'network_parameters': {
                    'num_nodes': 100,
                    'topology_type': 'scale_free',
                    'seed': 4002,
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.5,
                        '28.1': 0.5,
                    },
                    'clustering_factor': 0.0,
                },
                'node_configurations': {
                    'maxmempool': {
                        'distribution': {
                            50: 0.6,   # 60% very low memory
                            300: 0.3,
                            1000: 0.1,
                        }
                    },
                    'maxconnections': {
                        'distribution': {
                            8: 0.5,    # 50% minimal connections
                            125: 0.4,
                            1000: 0.1,
                        }
                    },
                    'mempoolexpiry': {
                        'distribution': {
                            1: 0.4,    # 40% expire quickly
                            72: 0.5,
                            336: 0.1,
                        }
                    }
                },
                'output': {
                    'file': 'phase4_extreme_constraints.yaml',
                    'name_prefix': 'stress-extreme',
                }
            }
        })
        
        # Scenario 4.3: Conflicting policy combinations
        scenarios.append({
            'name': 'phase4_policy_conflicts',
            'description': 'Nodes with highly conflicting policies',
            'config': {
                'network_parameters': {
                    'num_nodes': 80,
                    'topology_type': 'hub_spoke',
                    'seed': 4003,
                    'topology_params': {
                        'hub_ratio': 0.1,
                        'hub_connections': [2, 4],
                        'spoke_connections': [4, 6],
                    }
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.5,
                        '27.2': 0.5,
                    },
                    'clustering_factor': 0.6,
                },
                'node_configurations': {
                    'blocksonly': {
                        'distribution': {
                            'false': 0.5,
                            'true': 0.5,   # 50% blocks-only
                        }
                    },
                    'minrelaytxfee': {
                        'distribution': {
                            0.00001: 0.3,  # Very low
                            0.001: 0.3,
                            0.01: 0.4,     # Very high
                        }
                    },
                    'maxmempool': {
                        'distribution': {
                            50: 0.4,
                            5000: 0.6,     # Extreme variance
                        }
                    }
                },
                'output': {
                    'file': 'phase4_policy_conflicts.yaml',
                    'name_prefix': 'stress-conflict',
                }
            }
        })
        
        # Scenario 4.4: Large network stress test
        scenarios.append({
            'name': 'phase4_large_network',
            'description': 'Large network with mixed everything',
            'config': {
                'network_parameters': {
                    'num_nodes': 200,
                    'topology_type': 'scale_free',
                    'seed': 4004,
                },
                'version_configuration': {
                    'distribution': {
                        '29.0': 0.25,
                        '28.1': 0.25,
                        '27.2': 0.25,
                        '26.0': 0.15,
                        '25.0': 0.1,
                    },
                    'clustering_factor': 0.5,
                },
                'node_configurations': {
                    'maxmempool': {
                        'distribution': {
                            50: 0.3,
                            300: 0.4,
                            1000: 0.2,
                            5000: 0.1,
                        }
                    },
                    'maxconnections': {
                        'distribution': {
                            8: 0.2,
                            125: 0.6,
                            1000: 0.2,
                        }
                    },
                    'blocksonly': {
                        'distribution': {
                            'false': 0.7,
                            'true': 0.3,
                        }
                    }
                },
                'output': {
                    'file': 'phase4_large_network.yaml',
                    'name_prefix': 'stress-large',
                }
            }
        })
        
        return scenarios
    
    def save_scenario(self, scenario: Dict):
        """Save a single scenario configuration"""
        config_file = self.output_dir / f"{scenario['name']}_config.yaml"
        
        # Add metadata to config
        full_config = {
            'metadata': {
                'name': scenario['name'],
                'description': scenario['description'],
            },
            **scenario['config']
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(full_config, f, default_flow_style=False, sort_keys=False)
        
        return config_file
    
    def generate_all_scenarios(self, phases: List[int] = None):
        """Generate scenarios for specified phases"""
        if phases is None:
            phases = [1, 2, 3, 4]
        
        all_scenarios = []
        
        if 1 in phases:
            print("Generating Phase 1 scenarios (Baseline)...")
            phase1 = self.generate_phase1_baseline()
            all_scenarios.extend(phase1)
        
        if 2 in phases:
            print("Generating Phase 2 scenarios (Single-Variable)...")
            phase2 = self.generate_phase2_single_variable()
            all_scenarios.extend(phase2)
        
        if 3 in phases:
            print("Generating Phase 3 scenarios (Multi-Variable)...")
            phase3 = self.generate_phase3_multi_variable()
            all_scenarios.extend(phase3)
        
        if 4 in phases:
            print("Generating Phase 4 scenarios (Stress Test)...")
            phase4 = self.generate_phase4_stress_test()
            all_scenarios.extend(phase4)
        
        # Save all scenarios
        saved_files = []
        for scenario in all_scenarios:
            config_file = self.save_scenario(scenario)
            saved_files.append(config_file)
            print(f"  ✓ {scenario['name']}: {scenario['description']}")
        
        # Generate summary document
        self.generate_summary(all_scenarios)
        
        return saved_files
    
    def generate_summary(self, scenarios: List[Dict]):
        """Generate a summary markdown document"""
        summary_file = self.output_dir / "SCENARIOS_SUMMARY.md"
        
        with open(summary_file, 'w') as f:
            f.write("# Warnet Test Scenarios Summary\n\n")
            f.write("## Overview\n\n")
            f.write(f"Total scenarios generated: {len(scenarios)}\n\n")
            
            # Group by phase
            phases = {
                1: [s for s in scenarios if s['name'].startswith('phase1')],
                2: [s for s in scenarios if s['name'].startswith('phase2')],
                3: [s for s in scenarios if s['name'].startswith('phase3')],
                4: [s for s in scenarios if s['name'].startswith('phase4')],
            }
            
            for phase_num, phase_scenarios in phases.items():
                if not phase_scenarios:
                    continue
                
                f.write(f"## Phase {phase_num}\n\n")
                
                phase_names = {
                    1: "Baseline Establishment",
                    2: "Single-Variable Perturbation",
                    3: "Multi-Variable Combinations",
                    4: "Stress Testing"
                }
                
                f.write(f"**{phase_names[phase_num]}**\n\n")
                f.write(f"Scenarios: {len(phase_scenarios)}\n\n")
                
                for scenario in phase_scenarios:
                    f.write(f"### {scenario['name']}\n\n")
                    f.write(f"**Description:** {scenario['description']}\n\n")
                    
                    config = scenario['config']
                    params = config['network_parameters']
                    
                    f.write(f"- **Nodes:** {params['num_nodes']}\n")
                    f.write(f"- **Topology:** {params['topology_type']}\n")
                    f.write(f"- **Seed:** {params.get('seed', 'random')}\n")
                    
                    if 'version_configuration' in config:
                        versions = config['version_configuration']['distribution']
                        f.write(f"- **Versions:** {', '.join([f'{v}({p*100:.0f}%)' for v, p in versions.items()])}\n")
                    
                    f.write(f"- **Config file:** `{scenario['name']}_config.yaml`\n")
                    f.write(f"- **Output file:** `{config['output']['file']}`\n\n")
                
                f.write("\n")
            
            # Usage instructions
            f.write("## Usage\n\n")
            f.write("To generate network from a scenario configuration:\n\n")
            f.write("```bash\n")
            f.write("python generate_warnet_network.py --config scenarios/<scenario_name>_config.yaml\n")
            f.write("```\n\n")
            f.write("With statistics and visualization:\n\n")
            f.write("```bash\n")
            f.write("python generate_warnet_network.py \\\n")
            f.write("    --config scenarios/<scenario_name>_config.yaml \\\n")
            f.write("    --stats \\\n")
            f.write("    --visualize <scenario_name>.png\n")
            f.write("```\n")
        
        print(f"\n✓ Summary document created: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate batch test scenarios for Warnet testing phases'
    )
    
    parser.add_argument(
        '--phase', '-p',
        type=int,
        choices=[1, 2, 3, 4],
        action='append',
        help='Generate scenarios for specific phase (can specify multiple times)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Generate all scenarios for all phases'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./scenarios',
        help='Output directory for scenario configs (default: ./scenarios)'
    )
    
    args = parser.parse_args()
    
    generator = ScenarioGenerator(output_dir=args.output_dir)
    
    if args.all:
        phases = [1, 2, 3, 4]
    elif args.phase:
        phases = args.phase
    else:
        print("Error: Must specify --phase or --all")
        parser.print_help()
        return
    
    print(f"Output directory: {generator.output_dir}")
    print("=" * 60)
    
    saved_files = generator.generate_all_scenarios(phases=phases)
    
    print("\n" + "=" * 60)
    print(f"✓ Generated {len(saved_files)} scenario configurations")
    print(f"✓ Saved to: {generator.output_dir}")
    print("\nNext steps:")
    print("  1. Review scenario configurations in the output directory")
    print("  2. Generate networks using: python generate_warnet_network.py --config <config_file>")
    print("  3. Review SCENARIOS_SUMMARY.md for details on all scenarios")


if __name__ == '__main__':
    main()
