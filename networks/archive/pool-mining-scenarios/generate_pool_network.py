#!/usr/bin/env python3

"""
Generate a 25-node three-tier network for pool-based mining scenarios

Three-Tier Architecture:
- Nodes 0-4:   Economic nodes (exchanges, payment processors)
- Nodes 5-14:  Pool nodes (mining pool infrastructure)
- Nodes 15-24: Network nodes (regular propagation nodes)
"""

import yaml
import random

# Economic metadata for nodes 0-4
ECONOMIC_ROLES = {
    "major_exchange": {
        "custody_btc": [1800000, 2200000],
        "daily_volume_btc": [10000, 30000]
    },
    "payment_processor": {
        "custody_btc": [50000, 150000],
        "daily_volume_btc": [200000, 400000]
    }
}

# Pool information for nodes 5-14
POOLS = [
    {"name": "Foundry USA", "hashrate": 26.89},
    {"name": "AntPool", "hashrate": 19.25},
    {"name": "ViaBTC", "hashrate": 11.39},
    {"name": "F2Pool", "hashrate": 11.25},
    {"name": "SpiderPool", "hashrate": 9.09},
    {"name": "MARA Pool", "hashrate": 5.00},
    {"name": "SECPOOL", "hashrate": 4.18},
    {"name": "Luxor", "hashrate": 3.21},
    {"name": "Binance Pool", "hashrate": 2.49},
    {"name": "OCEAN", "hashrate": 1.42},
]

# Connection topology (custom edges)
CUSTOM_EDGES = [
    # Economic layer fully meshed (0-4)
    [0, 1], [0, 2], [0, 3], [0, 4],
    [1, 2], [1, 3], [1, 4],
    [2, 3], [2, 4],
    [3, 4],

    # Pool layer connections (5-14)
    # Foundry USA (5)
    [5, 0], [5, 1], [5, 2], [5, 6], [5, 15],

    # AntPool (6)
    [6, 1], [6, 2], [6, 3], [6, 7], [6, 16],

    # ViaBTC (7)
    [7, 2], [7, 3], [7, 4], [7, 8], [7, 17],

    # F2Pool (8)
    [8, 0], [8, 3], [8, 4], [8, 9], [8, 18],

    # SpiderPool (9)
    [9, 0], [9, 2], [9, 4], [9, 10], [9, 19],

    # MARA Pool (10)
    [10, 1], [10, 3], [10, 11], [10, 20],

    # SECPOOL (11)
    [11, 0], [11, 4], [11, 12], [11, 21],

    # Luxor (12)
    [12, 2], [12, 3], [12, 13], [12, 22],

    # Binance Pool (13)
    [13, 1], [13, 4], [13, 14], [13, 23],

    # OCEAN (14)
    [14, 0], [14, 2], [14, 24],

    # Network layer (15-24)
    [15, 16], [15, 20], [16, 17], [16, 21],
    [17, 18], [17, 22], [18, 19], [18, 23],
    [19, 20], [19, 24], [20, 21], [21, 22],
    [22, 23], [23, 24], [24, 15],

    # Network nodes to economic nodes
    [15, 0], [17, 2], [19, 4], [22, 1], [24, 3],
]


def generate_economic_metadata(role):
    """Generate random economic metadata for a given role"""
    role_config = ECONOMIC_ROLES[role]
    custody = random.randint(*role_config["custody_btc"])
    volume = random.randint(*role_config["daily_volume_btc"])

    # Calculate consensus weight (70% custody, 30% volume)
    consensus_weight = 0.7 * custody + 0.3 * volume
    consensus_weight = round(consensus_weight / 10000, 2)

    return {
        "role": role,
        "custody_btc": custody,
        "daily_volume_btc": volume,
        "consensus_weight": consensus_weight
    }


def create_node_config(node_id, node_type, addnodes, bitcoin_version="26.0"):
    """Create configuration for a single node"""

    config = {
        "name": f"node-{node_id:04d}",
        "image": {"tag": bitcoin_version},
        "addnode": [f"node-{n:04d}" for n in addnodes],
    }

    # Type-specific configurations
    if node_type == "economic":
        config["bitcoin_config"] = {
            "maxconnections": 125,
            "maxmempool": 500,
            "rpcthreads": 16,
            "txindex": 1
        }
        # Assign economic metadata
        role = "major_exchange" if random.random() < 0.4 else "payment_processor"
        config["metadata"] = generate_economic_metadata(role)

    elif node_type == "pool":
        config["bitcoin_config"] = {
            "maxconnections": 50,
            "maxmempool": 200,
            "rpcthreads": 8,
            "txindex": 0
        }
        # Pool metadata (for scenario reference)
        pool_info = POOLS[node_id - 5]
        config["metadata"] = {
            "role": "mining_pool",
            "pool_name": pool_info["name"],
            "hashrate": pool_info["hashrate"]
        }

    elif node_type == "network":
        config["bitcoin_config"] = {
            "maxconnections": 30,
            "maxmempool": 100,
            "rpcthreads": 4,
            "txindex": 0
        }
        # No metadata for regular network nodes

    return config


def main():
    random.seed(42)  # For reproducibility

    # Build adjacency list from edges
    adjacency = {i: set() for i in range(25)}
    for edge in CUSTOM_EDGES:
        adjacency[edge[0]].add(edge[1])
        adjacency[edge[1]].add(edge[0])

    # Generate nodes
    nodes = []

    # Economic nodes (0-4)
    for i in range(5):
        node_type = "economic"
        version = "26.0" if i < 2 else "27.0"  # Split versions
        addnodes = sorted(adjacency[i])
        nodes.append(create_node_config(i, node_type, addnodes, version))

    # Pool nodes (5-14)
    for i in range(5, 15):
        node_type = "pool"
        version = "26.0" if i < 10 else "27.0"  # Split versions
        addnodes = sorted(adjacency[i])
        nodes.append(create_node_config(i, node_type, addnodes, version))

    # Network nodes (15-24)
    for i in range(15, 25):
        node_type = "network"
        version = "26.0" if i < 20 else "27.0"  # Split versions
        addnodes = sorted(adjacency[i])
        nodes.append(create_node_config(i, node_type, addnodes, version))

    # Create full configuration
    network_config = {
        "caddy": {"enabled": True},
        "fork_observer": {
            "enabled": True,
            "configQueryInterval": 10
        },
        "nodes": nodes
    }

    # Write to file
    output_file = "network.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(network_config, f, default_flow_style=False, sort_keys=False)

    print(f"Generated {len(nodes)}-node network configuration:")
    print(f"  - Economic nodes (0-4): 5 nodes with economic metadata")
    print(f"  - Pool nodes (5-14): 10 nodes with pool metadata")
    print(f"  - Network nodes (15-24): 10 nodes (regular propagation)")
    print(f"  - Total connections: {len(CUSTOM_EDGES)}")
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
