# Warnet Network Topology Generator

A comprehensive toolkit for generating realistic Bitcoin network topologies for Warnet testing, with support for various network characteristics, node configurations, and test scenarios.

## Features

✅ **Multiple Topology Types**
- Scale-free (Barabási-Albert) - mimics Bitcoin's power-law distribution
- Small-world (Watts-Strogatz) - high clustering with short paths
- Hub-and-spoke - designated hub nodes with spoke connections
- Random (Erdős-Rényi) - baseline for comparison

✅ **Realistic Bitcoin Constraints**
- Default 8 outbound connections per node
- Maximum 125 total connections enforced
- Configurable version distributions
- Version clustering (similar versions connect together)

✅ **Node Configuration Parameters**
- Memory pool sizes (maxmempool)
- Connection limits (maxconnections)
- Mempool expiry times
- Minimum relay fees
- Blocks-only mode
- Custom Bitcoin Core parameters

✅ **Batch Scenario Generation**
- Pre-defined test scenarios for all 4 testing phases
- Baseline, single-variable, multi-variable, and stress test scenarios
- Automatic generation of configuration files

✅ **Network Analysis**
- Degree distribution statistics
- Network diameter and path lengths
- Clustering coefficients
- Degree assortativity
- Version distribution analysis

✅ **Visualization**
- Network graph visualization with version-based coloring
- Export to PNG format

## Installation

```bash
# Required dependencies
pip install networkx pyyaml

# Optional for visualization
pip install matplotlib
```

## Quick Start

### 1. Generate a Simple Network

```bash
# Generate 50-node scale-free network
python generate_warnet_network.py --nodes 50 --output network.yaml

# View statistics
python generate_warnet_network.py --nodes 50 --stats --output network.yaml

# With visualization
python generate_warnet_network.py --nodes 50 --stats --visualize network.png
```

### 2. Using Configuration Files

Create a `topology_config.yaml` file (see example provided):

```bash
# Generate from config
python generate_warnet_network.py --config topology_config.yaml

# Override config parameters
python generate_warnet_network.py --config topology_config.yaml --nodes 100 --seed 42
```

### 3. Generate Test Scenarios

```bash
# Generate all Phase 1 scenarios
python generate_test_scenarios.py --phase 1

# Generate all Phase 2 scenarios
python generate_test_scenarios.py --phase 2

# Generate all scenarios for all phases
python generate_test_scenarios.py --all

# Custom output directory
python generate_test_scenarios.py --all --output-dir ./my_scenarios
```

## File Structure

```
.
├── generate_warnet_network.py      # Main network generator
├── generate_test_scenarios.py      # Batch scenario generator
├── topology_config.yaml             # Example configuration file
├── README.md                        # This file
└── scenarios/                       # Generated scenarios (created by batch generator)
    ├── phase1_baseline_small_config.yaml
    ├── phase2_version_mix_10pct_config.yaml
    ├── phase3_version_clustered_config.yaml
    ├── phase4_legacy_versions_config.yaml
    └── SCENARIOS_SUMMARY.md         # Summary of all scenarios
```

## Usage Examples

### Example 1: Version Compatibility Testing

```bash
# Create network with version mix and clustering
python generate_warnet_network.py \
    --nodes 100 \
    --topology scale_free \
    --version-clustering 0.7 \
    --output version_test.yaml \
    --stats
```

### Example 2: Hub-and-Spoke Topology

```bash
# Create hub-and-spoke network
python generate_warnet_network.py \
    --nodes 80 \
    --topology hub_spoke \
    --output hub_network.yaml \
    --visualize hub_network.png
```

### Example 3: Custom Configuration

Create `my_config.yaml`:

```yaml
network_parameters:
  num_nodes: 60
  topology_type: small_world
  seed: 12345
  topology_params:
    k: 8
    p: 0.1

version_configuration:
  distribution:
    '29.0': 0.5
    '28.1': 0.5
  clustering_factor: 0.5

node_configurations:
  maxmempool:
    distribution:
      50: 0.3
      300: 0.5
      1000: 0.2
  maxconnections:
    distribution:
      8: 0.2
      125: 0.7
      1000: 0.1

output:
  file: my_network.yaml
  name_prefix: custom
```

Generate:

```bash
python generate_warnet_network.py --config my_config.yaml --stats
```

## Configuration File Reference

### Network Parameters

```yaml
network_parameters:
  num_nodes: 50              # Total nodes in network
  topology_type: scale_free  # scale_free | small_world | hub_spoke | random
  seed: 42                   # Random seed (optional)
  
  # Topology-specific parameters
  topology_params:
    # For scale_free:
    m: 8                     # Edges to attach from new node
    
    # For small_world:
    k: 8                     # Neighbors per node
    p: 0.1                   # Rewiring probability
    
    # For hub_spoke:
    hub_ratio: 0.1           # Proportion of hub nodes
    hub_connections: [2, 4]  # Min/max hub connections
    spoke_connections: [4, 6] # Min/max spoke connections
```

### Version Configuration

```yaml
version_configuration:
  # Version distribution (values sum to ~1.0)
  distribution:
    '29.0': 0.35
    '28.1': 0.30
    '27.2': 0.20
    '26.0': 0.10
    '25.0': 0.05
  
  # Version clustering factor (0.0 - 1.0)
  # 0.0 = random, 1.0 = highly clustered
  clustering_factor: 0.3
```

### Node Configurations

```yaml
node_configurations:
  # Memory pool size in MB
  maxmempool:
    distribution:
      50: 0.2     # 20% with 50MB
      300: 0.6    # 60% with 300MB (default)
      1000: 0.2   # 20% with 1GB
  
  # Connection limits
  maxconnections:
    distribution:
      8: 0.1      # 10% minimal
      125: 0.8    # 80% default
      1000: 0.1   # 10% high
  
  # Mempool expiry (hours)
  mempoolexpiry:
    distribution:
      1: 0.1      # 1 hour
      72: 0.8     # 72 hours (default)
      336: 0.1    # 2 weeks
  
  # Minimum relay fee (BTC/kB)
  minrelaytxfee:
    distribution:
      0.00001: 0.3
      0.001: 0.6
      0.01: 0.1
  
  # Blocks-only mode
  blocksonly:
    distribution:
      false: 0.8
      true: 0.2
```

### Output Configuration

```yaml
output:
  file: network.yaml     # Output filename
  name_prefix: tank      # Node name prefix

warnet_settings:
  caddy_enabled: true
  fork_observer:
    enabled: true
    interval: 20         # Query interval in seconds
```

## Generated Network Format

The tool generates Warnet-compatible YAML files:

```yaml
caddy:
  enabled: true
fork_observer:
  enabled: true
  configQueryInterval: 20
nodes:
  - name: tank-0000
    image:
      tag: '29.0'
    addnode:
      - tank-0001
      - tank-0004
    bitcoin_config:
      maxmempool: 300
      maxconnections: 125
  - name: tank-0001
    image:
      tag: '28.1'
    addnode:
      - tank-0002
    bitcoin_config:
      maxmempool: 50
      maxconnections: 8
```

## Test Scenarios

The batch generator creates scenarios for 4 testing phases:

### Phase 1: Baseline Establishment
- Homogeneous networks with default settings
- Small (20), medium (50), and large (100) node networks
- All nodes same version and configuration

### Phase 2: Single-Variable Perturbation
- Version mix (10%, 20% legacy versions)
- Memory constraints (low mempool)
- Connection limits
- High minimum relay fees
- Blocks-only nodes

### Phase 3: Multi-Variable Combinations
- Low-resource + version mix
- Version clustering (network segregation)
- Hub-spoke + mixed policies
- Memory pressure + fee variations

### Phase 4: Stress Testing
- Legacy versions (v24-v29 mix)
- Extreme resource constraints
- Conflicting policy combinations
- Large networks (200+ nodes)

### Using Pre-Generated Scenarios

```bash
# Generate all scenarios
python generate_test_scenarios.py --all

# Review scenarios
cat scenarios/SCENARIOS_SUMMARY.md

# Generate network from scenario
python generate_warnet_network.py \
    --config scenarios/phase2_version_mix_10pct_config.yaml \
    --stats \
    --visualize phase2_viz.png
```

## Command-Line Reference

### generate_warnet_network.py

```
Options:
  -c, --config FILE          Configuration YAML file
  -n, --nodes NUM            Number of nodes
  -t, --topology TYPE        Topology type (scale_free|small_world|hub_spoke|random)
  -o, --output FILE          Output YAML file
  -p, --prefix PREFIX        Node name prefix
  --seed NUM                 Random seed
  --version-clustering NUM   Version clustering factor (0-1)
  --stats                    Print network statistics
  --visualize FILE           Save visualization to PNG
```

### generate_test_scenarios.py

```
Options:
  -p, --phase NUM            Generate specific phase (1-4, can repeat)
  -a, --all                  Generate all phases
  -o, --output-dir DIR       Output directory for scenarios
```

## Network Statistics Explained

When using `--stats`, you'll see:

- **num_nodes**: Total nodes in network
- **num_edges**: Total connections
- **avg_degree**: Average connections per node
- **density**: How connected the network is (0-1)
- **diameter**: Longest shortest path between any two nodes
- **avg_path_length**: Average hops between random node pairs
- **clustering_coefficient**: How interconnected neighbors are
- **degree_assortativity**: Whether high-degree nodes connect to each other
- **min/max/median_degree**: Degree distribution statistics

## Integrating with Warnet

### 1. Generate Network
```bash
python generate_warnet_network.py \
    --config topology_config.yaml \
    --output my_network.yaml
```

### 2. Deploy to Warnet
```bash
# Use standard Warnet commands deploy needs to point to a directory with network.yaml and node-defaults.yaml for example a directory my_network:
warnet deploy my_network

# Monitor the network
warnet status

# View fork observer
# Navigate to fork observer dashboard
```

### 3. Run Tests
```bash
# Generate transactions, blocks, etc.
# Monitor for forks and network issues
# Collect metrics from fork_observer
```

## Advanced Topics

### Matching Real Bitcoin Network Characteristics

To update version distributions from Bitnodes data:

```python
# Fetch latest Bitnodes snapshot
import requests
response = requests.get('https://bitnodes.io/api/v1/snapshots/latest/')
data = response.json()

# Count versions
from collections import defaultdict
version_counts = defaultdict(int)
for node_info in data['nodes'].values():
    user_agent = node_info[1]  # e.g., "/Satoshi:29.0.0/"
    # Parse and count versions
    # Update your topology_config.yaml distribution
```

### Custom Topology Algorithms

Extend the `BitcoinNetworkGenerator` class:

```python
def _generate_custom_topology(self) -> nx.Graph:
    """Your custom topology algorithm"""
    G = nx.Graph()
    # Your logic here
    return G
```

### Node-Specific Configurations

Target specific nodes by ID:

```python
# In your config processing
def assign_specific_configs(G: nx.Graph):
    configs = {}
    # Assign low memory to first 10 nodes
    for i in range(10):
        configs[i] = {'maxmempool': 50}
    # Assign high connections to hub nodes
    hub_nodes = identify_hubs(G)
    for hub in hub_nodes:
        configs[hub] = {'maxconnections': 1000}
    return configs
```

## Troubleshooting

### Issue: Network not connected
- Increase number of edges (m parameter for scale_free)
- Check that num_nodes is sufficient for topology type
- Some random graphs may be disconnected by design

### Issue: Degree limit violations
- The generator automatically enforces max_connections
- Check topology_params if seeing unexpected degrees

### Issue: Version distribution doesn't match
- Ensure distribution values sum to ~1.0
- With small networks, discrete assignment may not match exactly
- Use larger networks for more accurate distributions

## Contributing

To add new topology types:

1. Add method to `BitcoinNetworkGenerator` class
2. Update `generate_topology()` to handle new type
3. Document parameters in config file reference
4. Add test scenarios

## License

[Include your license information]

## References

- [Warnet Project](https://github.com/bitcoin-dev-project/warnet)
- [Bitnodes API](https://bitnodes.io/api/)
- [NetworkX Documentation](https://networkx.org/)
- [Bitcoin Core](https://github.com/bitcoin/bitcoin)

## Support

For issues and questions:
- Check existing GitHub issues
- Review SCENARIOS_SUMMARY.md for scenario details
- Consult Warnet documentation for deployment issues
