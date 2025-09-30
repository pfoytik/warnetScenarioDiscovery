#!/usr/bin/env python3
"""
Warnet Network Topology Generator

Generates realistic Bitcoin network topologies for Warnet testing based on
measured network characteristics and theoretical models.

Usage:
    # Using command line arguments
    python generate_warnet_network.py --nodes 50 --output network.yaml
    
    # Using configuration file
    python generate_warnet_network.py --config topology_config.yaml
"""

import argparse
import yaml
import networkx as nx
import random
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import sys


class BitcoinNetworkGenerator:
    """Generate realistic Bitcoin network topologies"""
    
    # Bitcoin Core default connection parameters
    DEFAULT_OUTBOUND = 8
    MAX_CONNECTIONS = 125
    
    # Default version distribution (can be overridden)
    DEFAULT_VERSION_DISTRIBUTION = {
        '29.0': 0.35,
        '28.1': 0.30,
        '27.2': 0.20,
        '26.0': 0.10,
        '25.0': 0.05
    }
    
    def __init__(self, num_nodes: int, topology_type: str = 'scale_free',
                 version_distribution: Optional[Dict] = None,
                 seed: Optional[int] = None):
        """
        Initialize network generator
        
        Args:
            num_nodes: Total number of nodes to generate
            topology_type: Type of topology ('scale_free', 'small_world', 'random', 'hub_spoke')
            version_distribution: Custom version distribution dict
            seed: Random seed for reproducibility
        """
        self.num_nodes = num_nodes
        self.topology_type = topology_type
        self.version_distribution = version_distribution or self.DEFAULT_VERSION_DISTRIBUTION
        
        if seed is not None:
            random.seed(seed)
            
    def generate_topology(self, **kwargs) -> nx.Graph:
        """Generate network topology based on specified type"""
        
        if self.topology_type == 'scale_free':
            return self._generate_scale_free(**kwargs)
        elif self.topology_type == 'small_world':
            return self._generate_small_world(**kwargs)
        elif self.topology_type == 'hub_spoke':
            return self._generate_hub_spoke(**kwargs)
        elif self.topology_type == 'random':
            return self._generate_random(**kwargs)
        else:
            raise ValueError(f"Unknown topology type: {self.topology_type}")
    
    def _generate_scale_free(self, m: Optional[int] = None) -> nx.Graph:
        """
        Generate scale-free network using Barabási-Albert model
        Mimics Bitcoin's power-law degree distribution
        
        Args:
            m: Number of edges to attach from new node (default: DEFAULT_OUTBOUND)
        """
        m = m or self.DEFAULT_OUTBOUND
        G = nx.barabasi_albert_graph(self.num_nodes, m=m)
        self._enforce_degree_limits(G)
        return G
    
    def _generate_small_world(self, k: Optional[int] = None, 
                             p: float = 0.1) -> nx.Graph:
        """
        Generate small-world network using Watts-Strogatz model
        High clustering with short path lengths
        
        Args:
            k: Each node connected to k nearest neighbors (default: DEFAULT_OUTBOUND)
            p: Probability of rewiring each edge (default: 0.1)
        """
        k = k or self.DEFAULT_OUTBOUND
        G = nx.watts_strogatz_graph(self.num_nodes, k, p)
        self._enforce_degree_limits(G)
        return G
    
    def _generate_hub_spoke(self, hub_ratio: float = 0.1,
                           hub_connections: Tuple[int, int] = (2, 4),
                           spoke_connections: Tuple[int, int] = (4, 6)) -> nx.Graph:
        """
        Generate hub-and-spoke topology with designated hub nodes
        
        Args:
            hub_ratio: Proportion of nodes that are hubs (default: 0.1)
            hub_connections: (min, max) hub connections for spokes
            spoke_connections: (min, max) spoke-to-spoke connections
        """
        G = nx.Graph()
        G.add_nodes_from(range(self.num_nodes))
        
        num_hubs = max(2, int(self.num_nodes * hub_ratio))
        hubs = random.sample(range(self.num_nodes), num_hubs)
        
        # Connect hubs to each other (full mesh)
        for i, hub1 in enumerate(hubs):
            for hub2 in hubs[i+1:]:
                G.add_edge(hub1, hub2)
        
        spokes = [n for n in range(self.num_nodes) if n not in hubs]
        
        for spoke in spokes:
            # Connect to hubs
            num_hub_conn = random.randint(hub_connections[0], 
                                         min(hub_connections[1], num_hubs))
            connected_hubs = random.sample(hubs, num_hub_conn)
            
            for hub in connected_hubs:
                G.add_edge(spoke, hub)
            
            # Connect to other spokes
            num_spoke_conn = random.randint(spoke_connections[0], spoke_connections[1])
            available_spokes = [s for s in spokes if s != spoke and not G.has_edge(spoke, s)]
            
            if available_spokes:
                connected_spokes = random.sample(
                    available_spokes,
                    min(num_spoke_conn, len(available_spokes))
                )
                for other_spoke in connected_spokes:
                    G.add_edge(spoke, other_spoke)
        
        return G
    
    def _generate_random(self, p: Optional[float] = None) -> nx.Graph:
        """
        Generate Erdős-Rényi random graph
        
        Args:
            p: Edge probability (default: calculated for avg degree ~8)
        """
        if p is None:
            p = self.DEFAULT_OUTBOUND / self.num_nodes
        G = nx.erdos_renyi_graph(self.num_nodes, p)
        self._enforce_degree_limits(G)
        return G
    
    def _enforce_degree_limits(self, G: nx.Graph, max_degree: Optional[int] = None):
        """
        Ensure no node exceeds max degree
        
        Args:
            max_degree: Maximum degree allowed (default: MAX_CONNECTIONS)
        """
        max_degree = max_degree or self.MAX_CONNECTIONS
        
        for node in list(G.nodes()):
            degree = G.degree(node)
            if degree > max_degree:
                edges = list(G.edges(node))
                excess = degree - max_degree
                edges_to_remove = random.sample(edges, excess)
                G.remove_edges_from(edges_to_remove)
    
    def assign_versions(self, G: nx.Graph) -> Dict[int, str]:
        """Assign Bitcoin Core versions to nodes based on distribution"""
        versions = {}
        version_list = []
        
        for version, proportion in self.version_distribution.items():
            count = int(self.num_nodes * proportion)
            version_list.extend([version] * count)
        
        # Fill remaining slots with most common version
        if version_list:
            most_common = max(self.version_distribution.items(), key=lambda x: x[1])[0]
            while len(version_list) < self.num_nodes:
                version_list.append(most_common)
        
        random.shuffle(version_list)
        for node_id in range(self.num_nodes):
            versions[node_id] = version_list[node_id]
        
        return versions
    
    def assign_versions_clustered(self, G: nx.Graph, 
                                  clustering_factor: float = 0.3) -> Dict[int, str]:
        """
        Assign versions with clustering - similar versions tend to connect
        
        Args:
            clustering_factor: 0-1, higher = more clustering
        """
        versions = {}
        unassigned = set(G.nodes())
        
        # Start with random seed nodes for each version
        for version in self.version_distribution.keys():
            if unassigned:
                seed = random.choice(list(unassigned))
                versions[seed] = version
                unassigned.remove(seed)
        
        # Grow version clusters using BFS with probability
        while unassigned:
            assigned_nodes = [n for n in G.nodes() if n in versions]
            if not assigned_nodes:
                break
                
            current_node = random.choice(assigned_nodes)
            current_version = versions[current_node]
            
            neighbors = [n for n in G.neighbors(current_node) if n in unassigned]
            
            if neighbors:
                neighbor = random.choice(neighbors)
                if random.random() < clustering_factor:
                    versions[neighbor] = current_version
                else:
                    versions[neighbor] = random.choices(
                        list(self.version_distribution.keys()),
                        weights=list(self.version_distribution.values())
                    )[0]
                unassigned.remove(neighbor)
            else:
                if unassigned:
                    node = random.choice(list(unassigned))
                    versions[node] = random.choices(
                        list(self.version_distribution.keys()),
                        weights=list(self.version_distribution.values())
                    )[0]
                    unassigned.remove(node)
        
        return versions
    
    def assign_node_configurations(self, G: nx.Graph, 
                                   config_distribution: Optional[Dict] = None) -> Dict[int, Dict]:
        """
        Assign node-specific configurations (mempool, connection limits, etc.)
        
        Args:
            config_distribution: Distribution of different config types
        """
        if not config_distribution:
            return {}
        
        configs = {}
        for node_id in G.nodes():
            node_config = {}
            
            # Apply each configuration parameter
            for param, options in config_distribution.items():
                if isinstance(options, list):
                    # Random choice from list
                    node_config[param] = random.choice(options)
                elif isinstance(options, dict) and 'distribution' in options:
                    # Weighted distribution
                    choices = list(options['distribution'].keys())
                    weights = list(options['distribution'].values())
                    node_config[param] = random.choices(choices, weights=weights)[0]
                else:
                    # Fixed value
                    node_config[param] = options
            
            if node_config:
                configs[node_id] = node_config
        
        return configs
    
    def to_warnet_config(self, G: nx.Graph, versions: Dict[int, str],
                        node_configs: Optional[Dict[int, Dict]] = None,
                        name_prefix: str = "tank",
                        caddy_enabled: bool = True,
                        fork_observer_enabled: bool = True,
                        fork_observer_interval: int = 20) -> Dict:
        """
        Convert NetworkX graph to Warnet YAML configuration format
        
        Args:
            G: NetworkX graph
            versions: Dict mapping node_id to version string
            node_configs: Optional dict of node-specific configurations
            name_prefix: Prefix for node names
            caddy_enabled: Enable Caddy reverse proxy
            fork_observer_enabled: Enable fork observer
            fork_observer_interval: Fork observer query interval
        """
        nodes = []
        node_configs = node_configs or {}
        
        for node_id in G.nodes():
            neighbors = list(G.neighbors(node_id))
            addnode_list = [f"{name_prefix}-{n:04d}" for n in neighbors]
            
            node_config = {
                'name': f"{name_prefix}-{node_id:04d}",
                'image': {
                    'tag': versions.get(node_id, '29.0')
                }
            }
            
            # Add connections
            if addnode_list:
                node_config['addnode'] = addnode_list
            
            # Add node-specific configurations
            if node_id in node_configs:
                node_config['bitcoin_config'] = node_configs[node_id]
            
            nodes.append(node_config)
        
        # Create full configuration
        config = {
            'caddy': {
                'enabled': caddy_enabled
            },
            'fork_observer': {
                'enabled': fork_observer_enabled,
                'configQueryInterval': fork_observer_interval
            },
            'nodes': nodes
        }
        
        return config
    
    def generate_network_stats(self, G: nx.Graph) -> Dict:
        """Calculate and return network statistics"""
        stats = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
            'density': nx.density(G),
        }
        
        if nx.is_connected(G):
            stats['diameter'] = nx.diameter(G)
            stats['avg_path_length'] = nx.average_shortest_path_length(G)
        else:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            stats['diameter'] = nx.diameter(subgraph)
            stats['avg_path_length'] = nx.average_shortest_path_length(subgraph)
            stats['num_components'] = nx.number_connected_components(G)
        
        stats['clustering_coefficient'] = nx.average_clustering(G)
        stats['degree_assortativity'] = nx.degree_assortativity_coefficient(G)
        
        degrees = [d for n, d in G.degree()]
        if degrees:
            stats['min_degree'] = min(degrees)
            stats['max_degree'] = max(degrees)
            stats['median_degree'] = sorted(degrees)[len(degrees)//2]
        
        return stats


def load_config_file(config_path: str) -> Dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        sys.exit(1)


def generate_from_config(config: Dict) -> Dict:
    """Generate network from configuration dictionary"""
    
    # Extract parameters
    params = config.get('network_parameters', {})
    num_nodes = params.get('num_nodes', 20)
    topology_type = params.get('topology_type', 'scale_free')
    seed = params.get('seed')
    
    # Topology-specific parameters
    topology_params = params.get('topology_params', {})
    
    # Version configuration
    version_config = config.get('version_configuration', {})
    version_distribution = version_config.get('distribution')
    version_clustering = version_config.get('clustering_factor', 0.0)
    
    # Node configurations
    node_config_dist = config.get('node_configurations', {})
    
    # Output configuration
    output_config = config.get('output', {})
    name_prefix = output_config.get('name_prefix', 'tank')
    
    # Warnet settings
    warnet = config.get('warnet_settings', {})
    caddy_enabled = warnet.get('caddy_enabled', True)
    fork_observer = warnet.get('fork_observer', {})
    
    # Create generator
    generator = BitcoinNetworkGenerator(
        num_nodes=num_nodes,
        topology_type=topology_type,
        version_distribution=version_distribution,
        seed=seed
    )
    
    # Generate topology
    G = generator.generate_topology(**topology_params)
    
    # Assign versions
    if version_clustering > 0:
        versions = generator.assign_versions_clustered(G, version_clustering)
    else:
        versions = generator.assign_versions(G)
    
    # Assign node configurations
    node_configs = generator.assign_node_configurations(G, node_config_dist)
    
    # Convert to Warnet format
    warnet_config = generator.to_warnet_config(
        G, versions, node_configs, name_prefix,
        caddy_enabled=caddy_enabled,
        fork_observer_enabled=fork_observer.get('enabled', True),
        fork_observer_interval=fork_observer.get('interval', 20)
    )
    
    return warnet_config, generator, G, versions


def main():
    parser = argparse.ArgumentParser(
        description='Generate realistic Bitcoin network topologies for Warnet',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using configuration file
  python generate_warnet_network.py --config topology_config.yaml
  
  # Using command line arguments
  python generate_warnet_network.py --nodes 50 --topology scale_free --output network.yaml
  
  # With statistics and visualization
  python generate_warnet_network.py --config topology_config.yaml --stats --visualize network.png
        """
    )
    
    # Configuration file or command line
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to topology configuration YAML file'
    )
    
    # Command line arguments (override config file)
    parser.add_argument(
        '--nodes', '-n',
        type=int,
        help='Number of nodes to generate'
    )
    parser.add_argument(
        '--topology', '-t',
        choices=['scale_free', 'small_world', 'hub_spoke', 'random'],
        help='Network topology type'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output YAML file'
    )
    parser.add_argument(
        '--prefix', '-p',
        type=str,
        help='Node name prefix'
    )
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--version-clustering',
        type=float,
        help='Version clustering factor 0-1'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Print network statistics to stdout'
    )
    parser.add_argument(
        '--visualize',
        type=str,
        help='Save network visualization to file (e.g., network.png)'
    )
    
    args = parser.parse_args()
    
    # Load configuration or use command line args
    if args.config:
        print(f"Loading configuration from {args.config}...")
        config = load_config_file(args.config)
        
        # Command line args override config file
        if args.nodes:
            config.setdefault('network_parameters', {})['num_nodes'] = args.nodes
        if args.topology:
            config.setdefault('network_parameters', {})['topology_type'] = args.topology
        if args.seed is not None:
            config.setdefault('network_parameters', {})['seed'] = args.seed
        if args.version_clustering is not None:
            config.setdefault('version_configuration', {})['clustering_factor'] = args.version_clustering
        if args.prefix:
            config.setdefault('output', {})['name_prefix'] = args.prefix
        
        output_file = args.output or config.get('output', {}).get('file', 'network.yaml')
        
        warnet_config, generator, G, versions = generate_from_config(config)
        
    else:
        # Pure command line mode
        if not args.nodes or not args.topology:
            parser.error("--nodes and --topology are required when not using --config")
        
        print(f"Generating {args.topology} network with {args.nodes} nodes...")
        
        generator = BitcoinNetworkGenerator(
            num_nodes=args.nodes,
            topology_type=args.topology,
            seed=args.seed
        )
        
        G = generator.generate_topology()
        
        if args.version_clustering and args.version_clustering > 0:
            versions = generator.assign_versions_clustered(G, args.version_clustering)
        else:
            versions = generator.assign_versions(G)
        
        warnet_config = generator.to_warnet_config(
            G, versions, None, args.prefix or 'tank'
        )
        
        output_file = args.output or 'network.yaml'
    
    # Write YAML file
    with open(output_file, 'w') as f:
        yaml.dump(warnet_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Network configuration written to {output_file}")
    
    # Print statistics if requested
    if args.stats:
        print("\n=== Network Statistics ===")
        stats = generator.generate_network_stats(G)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key:.<30} {value:.3f}")
            else:
                print(f"{key:.<30} {value}")
        
        print("\n=== Version Distribution ===")
        version_counts = defaultdict(int)
        for v in versions.values():
            version_counts[v] += 1
        for version in sorted(version_counts.keys(), reverse=True):
            count = version_counts[version]
            percentage = (count / len(versions)) * 100
            print(f"v{version:.<25} {count:>4} ({percentage:>5.1f}%)")
    
    # Visualize if requested
    if args.visualize:
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 12))
            
            version_colors = {
                '29.0': '#2ecc71',
                '28.1': '#3498db',
                '27.2': '#f39c12',
                '26.0': '#e74c3c',
                '25.0': '#9b59b6'
            }
            
            node_colors = [version_colors.get(versions.get(n, '29.0'), '#95a5a6') 
                          for n in G.nodes()]
            
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
            
            nx.draw(G, pos,
                   node_color=node_colors,
                   node_size=100,
                   with_labels=False,
                   edge_color='#bdc3c7',
                   width=0.5,
                   alpha=0.7)
            
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=color, label=f'v{version}')
                             for version, color in version_colors.items()
                             if version in versions.values()]
            plt.legend(handles=legend_elements, loc='upper right')
            
            topology_name = generator.topology_type.replace("_", " ").title()
            plt.title(f'{topology_name} Network ({generator.num_nodes} nodes)')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(args.visualize, dpi=150, bbox_inches='tight')
            print(f"✓ Network visualization saved to {args.visualize}")
            
        except ImportError:
            print("⚠ matplotlib not installed, skipping visualization")


if __name__ == '__main__':
    main()
