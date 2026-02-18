#!/usr/bin/env python3
"""
Scenario-Based Network Generator for Fork Testing

Generates networks from YAML configuration files with support for:
- Paired-node architecture (pools in both partitions)
- Configurable user/economic node counts
- Random network generation with seeds
- Pool ideology overrides
- Custom topology options

Usage:
    # From config file
    python3 scenario_network_generator.py --config scenario.yaml

    # From CLI args (legacy mode)
    python3 scenario_network_generator.py --test-id 5.3 --v27-economic 70 --v27-hashrate 30

    # Random generation
    python3 scenario_network_generator.py --random --seed 42 --user-nodes 5
"""

import yaml
import argparse
import sys
import os
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field


# Real-world pool distribution (validated with R²≈0.98)
DEFAULT_POOL_DISTRIBUTION = [
    ("Foundry USA", 26.89),
    ("AntPool", 19.25),
    ("ViaBTC", 11.39),
    ("F2Pool", 11.25),
    ("Binance Pool", 10.04),
    ("MARA Pool", 8.25),
    ("SBI Crypto", 4.57),
    ("Luxor", 3.94),
    ("OCEAN", 1.42),
    ("Braiins Pool", 1.37),
]

# Network totals (realistic values)
TOTAL_CUSTODY_BTC = 4_000_000  # 4M BTC total custody
TOTAL_VOLUME_BTC_DAY = 420_000  # 420K BTC/day total volume


@dataclass
class PoolConfig:
    """Configuration for a mining pool"""
    pool_name: str
    hashrate_pct: float
    fork_preference: str = "neutral"  # "v27", "v26", or "neutral"
    ideology_strength: float = 0.3
    profitability_threshold: float = 0.05
    max_loss_pct: float = 0.10


@dataclass
class EconomicNodeConfig:
    """Configuration for an economic node"""
    role: str = "major_exchange"
    custody_btc: int = 0
    daily_volume_btc: int = 0
    fork_preference: str = "neutral"
    ideology_strength: float = 0.1
    switching_threshold: float = 0.03
    inertia: float = 0.15
    # Activity type for fee generation
    activity_type: str = "transactional"  # transactional, custodial, mixed
    transaction_velocity: float = 0.8  # 0.0 = pure custody, 1.0 = high volume
    # Optional mining capability
    hashrate_pct: float = 0.0  # Solo mining hashrate (0.0 = non-miner)


@dataclass
class UserNodeConfig:
    """Configuration for a user node"""
    custody_btc: float = 1.0
    daily_volume_btc: float = 0.1
    fork_preference: str = "neutral"
    ideology_strength: float = 0.3
    switching_threshold: float = 0.10
    inertia: float = 0.05
    # Activity type for fee generation
    activity_type: str = "mixed"  # transactional, custodial, mixed
    transaction_velocity: float = 0.3  # Users typically lower velocity than exchanges
    # Solo mining capability
    hashrate_pct: float = 0.0  # Solo mining hashrate (0.0 = non-miner)
    is_solo_miner: bool = False  # Convenience flag for enabling solo mining


@dataclass
class ScenarioConfig:
    """Complete scenario configuration"""
    name: str = "default"
    description: str = ""

    # Economic/hashrate split
    v27_economic_pct: float = 50.0
    v27_hashrate_pct: float = 50.0

    # Node counts per partition
    economic_nodes_per_partition: int = 1
    user_nodes_per_partition: int = 1

    # Pool configuration
    pools: List[PoolConfig] = field(default_factory=list)
    pool_overrides: Dict[str, Dict] = field(default_factory=dict)

    # Economic node overrides
    v27_economic: Optional[EconomicNodeConfig] = None
    v26_economic: Optional[EconomicNodeConfig] = None

    # User node configuration
    user_config: Optional[UserNodeConfig] = None

    # Topology
    partition_mode: str = "static"  # "static" or "dynamic"

    # Randomization
    random_seed: Optional[int] = None
    randomize_ideology: bool = False
    randomize_user_nodes: bool = False
    user_node_count_range: Tuple[int, int] = (1, 5)

    # Output
    fork_observer_enabled: bool = False


class ScenarioNetworkGenerator:
    """Generate networks from scenario configurations"""

    def __init__(self, config: ScenarioConfig):
        self.config = config
        self.rng = random.Random(config.random_seed)

        # Initialize pools from config or defaults
        if not config.pools:
            self.pools = [
                PoolConfig(name, hashrate)
                for name, hashrate in DEFAULT_POOL_DISTRIBUTION
            ]
        else:
            self.pools = config.pools

        # Apply pool overrides
        self._apply_pool_overrides()

        # Calculate node counts
        self._calculate_node_counts()

    def _apply_pool_overrides(self):
        """Apply pool-specific overrides from config"""
        for pool in self.pools:
            pool_id = pool.pool_name.lower().replace(' ', '').replace('.', '')

            # Check for override by pool_name or pool_id
            override = (
                self.config.pool_overrides.get(pool.pool_name) or
                self.config.pool_overrides.get(pool_id) or
                {}
            )

            if override:
                if 'fork_preference' in override:
                    pool.fork_preference = override['fork_preference']
                if 'ideology_strength' in override:
                    pool.ideology_strength = override['ideology_strength']
                if 'profitability_threshold' in override:
                    pool.profitability_threshold = override['profitability_threshold']
                if 'max_loss_pct' in override:
                    pool.max_loss_pct = override['max_loss_pct']

    def _calculate_node_counts(self):
        """Calculate total nodes per partition"""
        num_pools = len(self.pools)

        # Randomize user node count if enabled
        if self.config.randomize_user_nodes:
            min_users, max_users = self.config.user_node_count_range
            self.user_nodes_per_partition = self.rng.randint(min_users, max_users)
        else:
            self.user_nodes_per_partition = self.config.user_nodes_per_partition

        self.economic_nodes_per_partition = self.config.economic_nodes_per_partition

        # Total per partition: pools + economic + user
        self.nodes_per_partition = (
            num_pools +
            self.economic_nodes_per_partition +
            self.user_nodes_per_partition
        )

        print(f"  Node allocation per partition:")
        print(f"    Pool nodes: {num_pools}")
        print(f"    Economic nodes: {self.economic_nodes_per_partition}")
        print(f"    User nodes: {self.user_nodes_per_partition}")
        print(f"    Total: {self.nodes_per_partition}")

    def _randomize_pool_ideologies(self):
        """Randomize pool ideologies for random network generation"""
        preferences = ["v27", "v26", "neutral"]

        for pool in self.pools:
            pool.fork_preference = self.rng.choice(preferences)
            pool.ideology_strength = round(self.rng.uniform(0.1, 0.9), 2)
            pool.profitability_threshold = round(self.rng.uniform(0.02, 0.20), 2)
            pool.max_loss_pct = round(self.rng.uniform(0.05, 0.30), 2)

    def _create_economic_node(self, node_idx: int, version: str,
                               economic_pct: float, partition: str) -> Dict:
        """Create an economic node configuration"""
        # Get override config if available
        override = (
            self.config.v27_economic if partition == "v27"
            else self.config.v26_economic
        )

        # Calculate custody/volume based on economic percentage
        base_custody = int(TOTAL_CUSTODY_BTC * economic_pct)
        base_volume = int(TOTAL_VOLUME_BTC_DAY * economic_pct)

        # Divide among economic nodes in partition
        custody = base_custody // self.economic_nodes_per_partition
        volume = base_volume // self.economic_nodes_per_partition

        # Apply overrides or use defaults
        if override:
            fork_pref = override.fork_preference
            ideology = override.ideology_strength
            switch_thresh = override.switching_threshold
            inertia = override.inertia
            activity_type = override.activity_type
            transaction_velocity = override.transaction_velocity
            hashrate_pct = override.hashrate_pct
            role = override.role
        else:
            fork_pref = "neutral"
            ideology = 0.1
            switch_thresh = 0.03
            inertia = 0.15
            activity_type = "transactional"
            transaction_velocity = 0.8
            hashrate_pct = 0.0
            role = "major_exchange"

        metadata = {
            'role': role,
            'node_type': 'economic',
            'entity_id': f"econ-{partition}-{node_idx}",
            'custody_btc': custody,
            'daily_volume_btc': volume,
            'consensus_weight': round((0.7 * custody + 0.3 * volume) / 10000, 2),
            'fork_preference': fork_pref,
            'ideology_strength': ideology,
            'switching_threshold': switch_thresh,
            'inertia': inertia,
            'activity_type': activity_type,
            'transaction_velocity': transaction_velocity,
            # Asymmetric fork: v26 nodes accept v27 blocks; v27 nodes reject v26 blocks
            'accepts_foreign_blocks': partition == 'v26',
        }

        # Add hashrate if this node mines
        if hashrate_pct > 0:
            metadata['hashrate_pct'] = hashrate_pct

        return {
            'name': f"node-{node_idx:04d}",
            'image': {'tag': version},
            'bitcoin_config': {
                'maxconnections': 125,
                'maxmempool': 300,
                'txindex': 1
            },
            'metadata': metadata
        }

    def _create_pool_node(self, node_idx: int, version: str,
                          pool: PoolConfig) -> Dict:
        """Create a pool node configuration"""
        pool_id = pool.pool_name.lower().replace(' ', '').replace('.', '')
        entity_id = f"pool-{pool_id}"

        # Calculate pool economic values
        pool_custody = int(2000 * pool.hashrate_pct)
        pool_volume = int(200 * pool.hashrate_pct)

        return {
            'name': f"node-{node_idx:04d}",
            'image': {'tag': version},
            'bitcoin_config': {
                'maxconnections': 50,
                'maxmempool': 200,
                'txindex': 1
            },
            'metadata': {
                'role': 'mining_pool',
                'pool_name': pool.pool_name,
                'hashrate_pct': pool.hashrate_pct,
                'entity_id': entity_id,
                'entity_name': pool.pool_name,
                'node_type': 'mining_pool',
                'custody_btc': pool_custody,
                'daily_volume_btc': pool_volume,
                'consensus_weight': round((0.7 * pool_custody + 0.3 * pool_volume) / 10000, 2),
                'supply_percentage': round(pool_custody / 20500000, 2),
                'economic_influence': round(pool_custody / 1000, 0),
                'fork_preference': pool.fork_preference,
                'ideology_strength': pool.ideology_strength,
                'profitability_threshold': pool.profitability_threshold,
                'max_loss_pct': pool.max_loss_pct,
                # Asymmetric fork: v26 nodes accept v27 blocks; v27 nodes reject v26 blocks
                'accepts_foreign_blocks': version.startswith('26'),
            }
        }

    def _create_user_node(self, node_idx: int, version: str,
                          partition: str) -> Dict:
        """Create a user node configuration"""
        # Use config or randomize
        if self.config.user_config:
            custody = self.config.user_config.custody_btc
            volume = self.config.user_config.daily_volume_btc
            fork_pref = self.config.user_config.fork_preference
            ideology = self.config.user_config.ideology_strength
            switch_thresh = self.config.user_config.switching_threshold
            inertia = self.config.user_config.inertia
            activity_type = self.config.user_config.activity_type
            transaction_velocity = self.config.user_config.transaction_velocity
            hashrate_pct = self.config.user_config.hashrate_pct
            is_solo_miner = self.config.user_config.is_solo_miner
        else:
            # Randomize with seed for reproducibility
            self.rng.seed((self.config.random_seed or 0) + node_idx)
            custody = round(self.rng.uniform(0.5, 10.0), 1)
            volume = round(self.rng.uniform(0.05, 1.0), 2)
            fork_pref = "neutral"
            ideology = round(self.rng.uniform(0.1, 0.7), 2)
            switch_thresh = round(self.rng.uniform(0.05, 0.15), 2)
            inertia = round(self.rng.uniform(0.02, 0.10), 2)
            activity_type = "mixed"
            transaction_velocity = round(self.rng.uniform(0.1, 0.5), 2)
            hashrate_pct = 0.0
            is_solo_miner = False

        # If is_solo_miner flag is set but no hashrate specified, assign small random hashrate
        if is_solo_miner and hashrate_pct == 0:
            self.rng.seed((self.config.random_seed or 0) + node_idx + 1000)
            hashrate_pct = round(self.rng.uniform(0.01, 0.2), 3)

        metadata = {
            'node_type': 'user_node',
            'entity_id': f"user-{partition}-{node_idx}",
            'custody_btc': custody,
            'daily_volume_btc': volume,
            'consensus_weight': round((0.7 * custody + 0.3 * volume) / 10000, 4),
            'supply_percentage': round(custody / 20500000, 6),
            'economic_influence': round(custody / 10, 2),
            'fork_preference': fork_pref,
            'ideology_strength': ideology,
            'switching_threshold': switch_thresh,
            'inertia': inertia,
            'activity_type': activity_type,
            'transaction_velocity': transaction_velocity,
            # Asymmetric fork: v26 nodes accept v27 blocks; v27 nodes reject v26 blocks
            'accepts_foreign_blocks': partition == 'v26',
        }

        # Add hashrate if this node mines (solo miner)
        if hashrate_pct > 0:
            metadata['hashrate_pct'] = hashrate_pct

        return {
            'name': f"node-{node_idx:04d}",
            'image': {'tag': version},
            'bitcoin_config': {
                'maxconnections': 30,
                'maxmempool': 100,
                'txindex': 1
            },
            'metadata': metadata
        }

    def _generate_edges(self, v27_nodes: List[Dict], v26_nodes: List[Dict]) -> Dict[int, List[int]]:
        """Generate network topology edges"""
        adjacency = {}

        def add_edge(a: int, b: int):
            if a not in adjacency:
                adjacency[a] = []
            if b not in adjacency:
                adjacency[b] = []
            if b not in adjacency[a]:
                adjacency[a].append(b)
            if a not in adjacency[b]:
                adjacency[b].append(a)

        for partition_nodes in [v27_nodes, v26_nodes]:
            economic = [i for i, n in enumerate(partition_nodes)
                       if n['metadata'].get('node_type') == 'economic']
            pools = [i for i, n in enumerate(partition_nodes)
                    if n['metadata'].get('node_type') == 'mining_pool']
            users = [i for i, n in enumerate(partition_nodes)
                    if n['metadata'].get('node_type') == 'user_node']

            # Adjust indices for v26 partition
            if partition_nodes == v26_nodes:
                offset = len(v27_nodes)
                economic = [i + offset for i in economic]
                pools = [i + offset for i in pools]
                users = [i + offset for i in users]

            # 1. Economic nodes form full mesh
            for i, e1 in enumerate(economic):
                for e2 in economic[i+1:]:
                    add_edge(e1, e2)

            # 2. Pools connect to all economic nodes
            for p in pools:
                for e in economic:
                    add_edge(p, e)

            # 3. Pools connect to adjacent pools
            for i in range(len(pools) - 1):
                add_edge(pools[i], pools[i + 1])

            # 4. User nodes connect to economic nodes
            for u in users:
                for e in economic:
                    add_edge(u, e)

            # 5. User nodes form ring if 2+
            if len(users) >= 2:
                for i in range(len(users)):
                    add_edge(users[i], users[(i + 1) % len(users)])

        # Dynamic mode: add cross-partition bridges
        if self.config.partition_mode == 'dynamic':
            v27_econ = [i for i, n in enumerate(v27_nodes)
                       if n['metadata'].get('node_type') == 'economic']
            v26_econ = [i + len(v27_nodes) for i, n in enumerate(v26_nodes)
                       if n['metadata'].get('node_type') == 'economic']
            v27_pools = [i for i, n in enumerate(v27_nodes)
                        if n['metadata'].get('node_type') == 'mining_pool']
            v26_pools = [i + len(v27_nodes) for i, n in enumerate(v26_nodes)
                        if n['metadata'].get('node_type') == 'mining_pool']

            # Bridge economic nodes
            if v27_econ and v26_econ:
                add_edge(v27_econ[0], v26_econ[0])

            # Bridge largest pools
            if v27_pools and v26_pools:
                add_edge(v27_pools[0], v26_pools[0])
                if len(v27_pools) > 1 and len(v26_pools) > 1:
                    add_edge(v27_pools[1], v26_pools[1])

        return adjacency

    def generate(self) -> Dict:
        """Generate complete network configuration"""
        print(f"\nGenerating network: {self.config.name}")
        print(f"  v27: {self.config.v27_economic_pct:.0f}% economic, {self.config.v27_hashrate_pct:.0f}% hashrate")
        print(f"  v26: {100-self.config.v27_economic_pct:.0f}% economic, {100-self.config.v27_hashrate_pct:.0f}% hashrate")

        # Randomize if enabled
        if self.config.randomize_ideology:
            print("  Randomizing pool ideologies...")
            self._randomize_pool_ideologies()

        v27_nodes = []
        v26_nodes = []
        node_idx = 0

        v27_economic_pct = self.config.v27_economic_pct / 100.0
        v26_economic_pct = 1.0 - v27_economic_pct

        # Generate v27 partition
        print(f"\n  Generating v27 partition (nodes 0-{self.nodes_per_partition-1})...")

        # Economic nodes
        for _ in range(self.economic_nodes_per_partition):
            v27_nodes.append(self._create_economic_node(
                node_idx, "27.0", v27_economic_pct, "v27"
            ))
            node_idx += 1

        # Pool nodes
        for pool in self.pools:
            v27_nodes.append(self._create_pool_node(node_idx, "27.0", pool))
            node_idx += 1

        # User nodes
        for _ in range(self.user_nodes_per_partition):
            v27_nodes.append(self._create_user_node(node_idx, "27.0", "v27"))
            node_idx += 1

        # Generate v26 partition
        print(f"  Generating v26 partition (nodes {node_idx}-{node_idx + self.nodes_per_partition - 1})...")

        # Economic nodes
        for _ in range(self.economic_nodes_per_partition):
            v26_nodes.append(self._create_economic_node(
                node_idx, "26.0", v26_economic_pct, "v26"
            ))
            node_idx += 1

        # Pool nodes (same pools, paired architecture)
        for pool in self.pools:
            v26_nodes.append(self._create_pool_node(node_idx, "26.0", pool))
            node_idx += 1

        # User nodes
        for _ in range(self.user_nodes_per_partition):
            v26_nodes.append(self._create_user_node(node_idx, "26.0", "v26"))
            node_idx += 1

        # Generate topology
        adjacency = self._generate_edges(v27_nodes, v26_nodes)

        # Apply addnode to all nodes
        all_nodes = v27_nodes + v26_nodes
        for i, node in enumerate(all_nodes):
            if i in adjacency and adjacency[i]:
                node['addnode'] = [f"node-{n:04d}" for n in sorted(adjacency[i])]

        # Build network config
        network = {
            'caddy': {'enabled': True},
            'fork_observer': {
                'enabled': self.config.fork_observer_enabled,
                'configQueryInterval': 10
            },
            'nodes': all_nodes
        }

        # Print summary
        print(f"\n  Generated network:")
        print(f"    Total nodes: {len(all_nodes)}")
        print(f"    v27 partition: {len(v27_nodes)} nodes")
        print(f"    v26 partition: {len(v26_nodes)} nodes")
        print(f"    Partition mode: {self.config.partition_mode}")

        # Pool ideology summary
        v27_pools = [p for p in self.pools if p.fork_preference == "v27"]
        v26_pools = [p for p in self.pools if p.fork_preference == "v26"]
        neutral_pools = [p for p in self.pools if p.fork_preference == "neutral"]

        v27_hashrate = sum(p.hashrate_pct for p in v27_pools)
        v26_hashrate = sum(p.hashrate_pct for p in v26_pools)
        neutral_hashrate = sum(p.hashrate_pct for p in neutral_pools)

        print(f"\n  Pool ideologies:")
        print(f"    Pro-v27: {len(v27_pools)} pools ({v27_hashrate:.1f}% hashrate)")
        print(f"    Pro-v26: {len(v26_pools)} pools ({v26_hashrate:.1f}% hashrate)")
        print(f"    Neutral: {len(neutral_pools)} pools ({neutral_hashrate:.1f}% hashrate)")

        return network

    def write_network_yaml(self, output_path: str):
        """Generate and write network configuration"""
        network = self.generate()

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(network, f, default_flow_style=False, sort_keys=False)

        print(f"\n  ✓ Saved to: {output_path}")

        # Write node-defaults.yaml
        output_dir = os.path.dirname(output_path)
        if output_dir:
            node_defaults_path = os.path.join(output_dir, 'node-defaults.yaml')
            node_defaults = {
                'chain': 'regtest',
                'image': {
                    'repository': 'bitcoindevproject/bitcoin',
                    'pullPolicy': 'IfNotPresent'
                },
                'defaultConfig': (
                    'regtest=1\n'
                    'server=1\n'
                    'txindex=1\n'
                    'fallbackfee=0.00001\n'
                    'rpcuser=bitcoin\n'
                    'rpcpassword=bitcoin\n'
                    'rpcallowip=0.0.0.0/0\n'
                    'rpcbind=0.0.0.0\n'
                    'rpcport=18443\n'
                    'zmqpubrawblock=tcp://0.0.0.0:28332\n'
                    'zmqpubrawtx=tcp://0.0.0.0:28333\n'
                    'debug=rpc'
                ),
                'collectLogs': False,
                'metricsExport': False
            }

            with open(node_defaults_path, 'w') as f:
                yaml.dump(node_defaults, f, default_flow_style=False, sort_keys=False)

            print(f"  ✓ Created node-defaults.yaml")


def load_config_from_yaml(config_path: str) -> ScenarioConfig:
    """Load scenario configuration from YAML file"""
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)

    config = ScenarioConfig()

    # Basic settings
    config.name = data.get('name', 'unnamed')
    config.description = data.get('description', '')
    config.v27_economic_pct = data.get('v27_economic_pct', 50.0)
    config.v27_hashrate_pct = data.get('v27_hashrate_pct', 50.0)

    # Node counts
    config.economic_nodes_per_partition = data.get('economic_nodes_per_partition', 1)
    config.user_nodes_per_partition = data.get('user_nodes_per_partition', 1)

    # Pool overrides
    if 'pool_overrides' in data:
        for override in data['pool_overrides']:
            pool_name = override.get('pool_name') or override.get('pool_id')
            if pool_name:
                config.pool_overrides[pool_name] = override

    # Custom pools (replaces default distribution)
    if 'pools' in data:
        config.pools = [
            PoolConfig(
                pool_name=p['pool_name'],
                hashrate_pct=p['hashrate_pct'],
                fork_preference=p.get('fork_preference', 'neutral'),
                ideology_strength=p.get('ideology_strength', 0.3),
                profitability_threshold=p.get('profitability_threshold', 0.05),
                max_loss_pct=p.get('max_loss_pct', 0.10)
            )
            for p in data['pools']
        ]

    # Economic node overrides
    if 'v27_economic' in data:
        e = data['v27_economic']
        config.v27_economic = EconomicNodeConfig(
            role=e.get('role', 'major_exchange'),
            fork_preference=e.get('fork_preference', 'neutral'),
            ideology_strength=e.get('ideology_strength', 0.1),
            switching_threshold=e.get('switching_threshold', 0.03),
            inertia=e.get('inertia', 0.15),
            activity_type=e.get('activity_type', 'transactional'),
            transaction_velocity=e.get('transaction_velocity', 0.8),
            hashrate_pct=e.get('hashrate_pct', 0.0),
        )

    if 'v26_economic' in data:
        e = data['v26_economic']
        config.v26_economic = EconomicNodeConfig(
            role=e.get('role', 'major_exchange'),
            fork_preference=e.get('fork_preference', 'neutral'),
            ideology_strength=e.get('ideology_strength', 0.1),
            switching_threshold=e.get('switching_threshold', 0.03),
            inertia=e.get('inertia', 0.15),
            activity_type=e.get('activity_type', 'transactional'),
            transaction_velocity=e.get('transaction_velocity', 0.8),
            hashrate_pct=e.get('hashrate_pct', 0.0),
        )

    # User node configuration
    if 'user_config' in data:
        u = data['user_config']
        config.user_config = UserNodeConfig(
            custody_btc=u.get('custody_btc', 1.0),
            daily_volume_btc=u.get('daily_volume_btc', 0.1),
            fork_preference=u.get('fork_preference', 'neutral'),
            ideology_strength=u.get('ideology_strength', 0.3),
            switching_threshold=u.get('switching_threshold', 0.10),
            inertia=u.get('inertia', 0.05),
            activity_type=u.get('activity_type', 'mixed'),
            transaction_velocity=u.get('transaction_velocity', 0.3),
            hashrate_pct=u.get('hashrate_pct', 0.0),
            is_solo_miner=u.get('is_solo_miner', False),
        )

    # Topology
    config.partition_mode = data.get('partition_mode', 'static')

    # Randomization
    config.random_seed = data.get('random_seed')
    config.randomize_ideology = data.get('randomize_ideology', False)
    config.randomize_user_nodes = data.get('randomize_user_nodes', False)
    if 'user_node_count_range' in data:
        config.user_node_count_range = tuple(data['user_node_count_range'])

    # Output
    config.fork_observer_enabled = data.get('fork_observer_enabled', False)

    return config


def create_random_config(seed: int, user_nodes: int = 2) -> ScenarioConfig:
    """Create a random scenario configuration"""
    rng = random.Random(seed)

    config = ScenarioConfig()
    config.name = f"random-{seed:04d}"
    config.description = f"Randomly generated scenario (seed={seed})"
    config.random_seed = seed

    # Random economic/hashrate split
    config.v27_economic_pct = rng.randint(20, 80)
    config.v27_hashrate_pct = rng.randint(20, 80)

    # Node counts
    config.economic_nodes_per_partition = rng.randint(1, 3)
    config.user_nodes_per_partition = user_nodes

    # Randomize pool ideologies
    config.randomize_ideology = True

    # Random partition mode
    config.partition_mode = rng.choice(['static', 'dynamic'])

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Generate networks from scenario configurations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From config file
  python3 scenario_network_generator.py --config scenarios/close_battle.yaml

  # From CLI args (legacy mode)
  python3 scenario_network_generator.py --test-id 5.3 --v27-economic 70 --v27-hashrate 30

  # Random generation
  python3 scenario_network_generator.py --random --seed 42 --user-nodes 5

  # Random batch generation
  python3 scenario_network_generator.py --random-batch 10 --seed 1000
        """
    )

    # Config file mode
    parser.add_argument('--config', '-c', help='Path to scenario config YAML file')

    # Legacy CLI mode
    parser.add_argument('--test-id', help='Test identifier')
    parser.add_argument('--v27-economic', type=float, help='v27 economic percentage')
    parser.add_argument('--v27-hashrate', type=float, help='v27 hashrate percentage')

    # Random mode
    parser.add_argument('--random', action='store_true', help='Generate random network')
    parser.add_argument('--random-batch', type=int, help='Generate N random networks')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')

    # Node configuration
    parser.add_argument('--user-nodes', type=int, default=2,
                        help='User nodes per partition (default: 2)')
    parser.add_argument('--economic-nodes', type=int, default=1,
                        help='Economic nodes per partition (default: 1)')

    # Solo miner configuration
    parser.add_argument('--solo-miners', action='store_true',
                        help='Enable solo mining for user nodes')
    parser.add_argument('--solo-hashrate', type=float, default=0.1,
                        help='Hashrate per solo miner (default: 0.1%%)')
    parser.add_argument('--user-velocity', type=float, default=0.3,
                        help='User node transaction velocity (default: 0.3)')
    parser.add_argument('--user-activity-type', choices=['transactional', 'custodial', 'mixed'],
                        default='mixed', help='User node activity type (default: mixed)')

    # Topology
    parser.add_argument('--partition-mode', choices=['static', 'dynamic'],
                        default='static', help='Partition mode')

    # Output
    parser.add_argument('--output', '-o', help='Output path')
    parser.add_argument('--output-dir', help='Output directory for batch generation')

    args = parser.parse_args()

    # Determine mode and generate
    if args.config:
        # Config file mode
        print(f"Loading config from: {args.config}")
        config = load_config_from_yaml(args.config)

        generator = ScenarioNetworkGenerator(config)

        output_path = args.output or f"../../test-networks/{config.name}/network.yaml"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        generator.write_network_yaml(output_path)

    elif args.random_batch:
        # Batch random generation
        output_dir = args.output_dir or "../../test-networks"

        for i in range(args.random_batch):
            seed = args.seed + i
            config = create_random_config(seed, args.user_nodes)
            config.economic_nodes_per_partition = args.economic_nodes
            config.partition_mode = args.partition_mode

            # Apply solo miner configuration if specified
            if args.solo_miners or args.solo_hashrate > 0:
                config.user_config = UserNodeConfig(
                    is_solo_miner=True,
                    hashrate_pct=args.solo_hashrate,
                    transaction_velocity=args.user_velocity,
                    activity_type=args.user_activity_type,
                )

            generator = ScenarioNetworkGenerator(config)

            output_path = f"{output_dir}/random-{seed:04d}/network.yaml"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            generator.write_network_yaml(output_path)

        print(f"\n✓ Generated {args.random_batch} random networks")

    elif args.random:
        # Single random generation
        config = create_random_config(args.seed, args.user_nodes)
        config.economic_nodes_per_partition = args.economic_nodes
        config.partition_mode = args.partition_mode

        # Apply solo miner configuration if specified
        if args.solo_miners or args.solo_hashrate > 0:
            config.user_config = UserNodeConfig(
                is_solo_miner=True,
                hashrate_pct=args.solo_hashrate,
                transaction_velocity=args.user_velocity,
                activity_type=args.user_activity_type,
            )

        generator = ScenarioNetworkGenerator(config)

        output_path = args.output or f"../../test-networks/random-{args.seed:04d}/network.yaml"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        generator.write_network_yaml(output_path)

    elif args.test_id and args.v27_economic is not None and args.v27_hashrate is not None:
        # Legacy CLI mode
        config = ScenarioConfig()
        config.name = f"test-{args.test_id}-economic-{int(args.v27_economic)}-hashrate-{int(args.v27_hashrate)}"
        config.v27_economic_pct = args.v27_economic
        config.v27_hashrate_pct = args.v27_hashrate
        config.user_nodes_per_partition = args.user_nodes
        config.economic_nodes_per_partition = args.economic_nodes
        config.partition_mode = args.partition_mode

        # Apply solo miner configuration
        if args.solo_miners or args.solo_hashrate > 0:
            config.user_config = UserNodeConfig(
                is_solo_miner=True,
                hashrate_pct=args.solo_hashrate,
                transaction_velocity=args.user_velocity,
                activity_type=args.user_activity_type,
            )

        generator = ScenarioNetworkGenerator(config)

        output_path = args.output or f"../../test-networks/{config.name}/network.yaml"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        generator.write_network_yaml(output_path)

    else:
        parser.print_help()
        sys.exit(1)

    print("\n✓ Network generation complete!")


if __name__ == "__main__":
    main()
