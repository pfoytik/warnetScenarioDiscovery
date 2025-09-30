#!/usr/bin/env python3
"""
Warnet Utilities - Helper scripts for common operations
"""

import sys
import json
from warnet_test_framework import (
    NetworkState, WarnetRPC, NetworkPartition, 
    Monitor, ConfigLoader, logger
)


def list_nodes(nodes):
    """List all nodes with their info"""
    print("\n" + "="*80)
    print("WARNET NETWORK STATUS")
    print("="*80)
    
    state = NetworkState(nodes)
    
    print(f"\nTotal Nodes: {len(state.nodes)}")
    print("-"*80)
    print(f"{'Node':<15} {'IP Address':<20} {'Version':<20} {'Height':<10} {'Peers':<10}")
    print("-"*80)
    
    for node in state.nodes:
        info = state.node_info.get(node)
        if info:
            height = WarnetRPC.get_block_count(node)
            peers = len(WarnetRPC.get_peer_info(node))
            print(f"{node:<15} {info.ip:<20} {info.version:<20} {height:<10} {peers:<10}")
    
    print("="*80)


def check_network_health(nodes):
    """Check if network is healthy"""
    print("\n" + "="*80)
    print("NETWORK HEALTH CHECK")
    print("="*80)
    
    state = NetworkState(nodes)
    snapshot = state.snapshot()
    
    print(f"\nTimestamp: {snapshot.timestamp}")
    print(f"Fork Detected: {'⚠️  YES' if snapshot.fork_detected else '✓ NO'}")
    print(f"Unique Chain Tips: {snapshot.unique_tips}")
    
    if snapshot.fork_detected:
        print("\n⚠️  WARNING: Network is forked!")
        print("\nChain tips:")
        tips = {}
        for node, data in snapshot.nodes.items():
            tip = (data['height'], data['best_hash'][:12])
            if tip not in tips:
                tips[tip] = []
            tips[tip].append(node)
        
        for (height, hash_prefix), node_list in tips.items():
            print(f"\n  Height {height} ({hash_prefix}...):")
            for node in node_list:
                print(f"    - {node}")
        
        fork_point = state.find_fork_point()
        if fork_point:
            print(f"\nFork Point: Block {fork_point}")
    else:
        print("\n✓ Network is healthy - all nodes on same chain")
        height = list(snapshot.nodes.values())[0]['height']
        print(f"  Current height: {height}")
    
    print("\nConnection Status:")
    print("-"*80)
    for node, data in snapshot.nodes.items():
        peer_count = data['peer_count']
        status = "✓" if peer_count > 0 else "⚠️ "
        print(f"  {status} {node}: {peer_count} peers")
    
    print("="*80)


def show_mempool_status(nodes):
    """Show mempool status for all nodes"""
    print("\n" + "="*80)
    print("MEMPOOL STATUS")
    print("="*80)
    
    state = NetworkState(nodes)
    
    print(f"\n{'Node':<15} {'Transactions':<15} {'Size (bytes)':<15} {'Fee Rate':<15}")
    print("-"*80)
    
    total_txs = 0
    total_bytes = 0
    
    for node in state.nodes:
        mempool = WarnetRPC.get_mempool_info(node)
        size = mempool.get('size', 0)
        bytes_size = mempool.get('bytes', 0)
        min_fee = mempool.get('mempoolminfee', 0)
        
        total_txs += size
        total_bytes += bytes_size
        
        print(f"{node:<15} {size:<15} {bytes_size:<15} {min_fee:<15.8f}")
    
    print("-"*80)
    print(f"{'TOTAL':<15} {total_txs:<15} {total_bytes:<15}")
    print("="*80)


def force_reconnect(nodes):
    """Force reconnect all nodes"""
    print("\n" + "="*80)
    print("RECONNECTING NETWORK")
    print("="*80)
    
    state = NetworkState(nodes)
    partition = NetworkPartition(state)
    
    print("\nClearing all bans...")
    for node in nodes:
        WarnetRPC.clear_banned(node)
        print(f"  ✓ Cleared bans on {node}")
    
    print("\nForcing connections...")
    # Connect first node to several others
    if len(nodes) > 1:
        node_0 = nodes[0]
        for node in nodes[1:4]:  # Connect to 3 others
            if node in state.node_info:
                ip = state.node_info[node].ip
                WarnetRPC.add_node(node_0, ip)
                print(f"  ✓ Connected {node_0} to {node}")
    
    print("\nReconnection initiated. Wait 30s for network to stabilize...")
    print("="*80)


def partition_network(nodes, group1_indices, group2_indices):
    """Partition network into two groups"""
    print("\n" + "="*80)
    print("PARTITIONING NETWORK")
    print("="*80)
    
    state = NetworkState(nodes)
    partition = NetworkPartition(state)
    
    group1 = [nodes[i] for i in group1_indices if i < len(nodes)]
    group2 = [nodes[i] for i in group2_indices if i < len(nodes)]
    
    print(f"\nGroup 1: {', '.join(group1)}")
    print(f"Group 2: {', '.join(group2)}")
    
    print("\nApplying partition...")
    partition.partition_custom(group1, group2)
    
    print("✓ Partition complete")
    print("="*80)


def monitor_live(nodes, duration=300):
    """Monitor network live"""
    print("\n" + "="*80)
    print(f"LIVE MONITORING ({duration}s)")
    print("="*80)
    
    state = NetworkState(nodes)
    monitor = Monitor(state)
    
    print("\nMonitoring started. Press Ctrl+C to stop early.\n")
    
    try:
        monitor.monitor_session(duration, height_interval=5, mempool_interval=30)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    
    print("\nGenerating summary...")
    stats = monitor.collector.get_summary_stats()
    
    print("\n" + "="*80)
    print("MONITORING SUMMARY")
    print("="*80)
    
    if stats.get('height_progression'):
        print("\nBlock Production:")
        for node, data in stats['height_progression'].items():
            blocks = data['blocks_produced']
            print(f"  {node}: {blocks} blocks ({data['start']} → {data['end']})")
    
    if stats.get('fork_count', 0) > 0:
        print(f"\nFork Events: {stats['fork_count']}")
        print(f"Total Fork Duration: {stats['fork_duration']:.1f}s")
    
    print("="*80)


def compare_versions(nodes, version_a_prefix, version_b_prefix):
    """Compare behavior between two version groups"""
    print("\n" + "="*80)
    print("VERSION COMPARISON")
    print("="*80)
    
    state = NetworkState(nodes)
    
    group_a = [n for n, info in state.node_info.items() if version_a_prefix in info.version]
    group_b = [n for n, info in state.node_info.items() if version_b_prefix in info.version]
    
    print(f"\nVersion A ({version_a_prefix}): {len(group_a)} nodes")
    print(f"Version B ({version_b_prefix}): {len(group_b)} nodes")
    
    print("\n" + "-"*80)
    print("HEIGHTS")
    print("-"*80)
    
    heights_a = [WarnetRPC.get_block_count(n) for n in group_a]
    heights_b = [WarnetRPC.get_block_count(n) for n in group_b]
    
    print(f"Version A: {heights_a}")
    print(f"Version B: {heights_b}")
    
    print("\n" + "-"*80)
    print("MEMPOOLS")
    print("-"*80)
    
    for group_name, group_nodes in [("Version A", group_a), ("Version B", group_b)]:
        total_txs = 0
        for node in group_nodes:
            mempool = WarnetRPC.get_mempool_info(node)
            total_txs += mempool.get('size', 0)
        avg_txs = total_txs / len(group_nodes) if group_nodes else 0
        print(f"{group_name}: avg {avg_txs:.0f} transactions per node")
    
    print("="*80)


def debug_rpc(nodes, command="getblockcount"):
    """Debug RPC calls to see raw output"""
    print("\n" + "="*80)
    print(f"DEBUG: Testing RPC command '{command}'")
    print("="*80)
    
    import subprocess
    
    for node in nodes[:3]:  # Test first 3 nodes
        print(f"\n{node}:")
        print("-"*80)
        
        cmd = ["warnet", "bitcoin", "rpc", node, command]
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            print(f"Return code: {result.returncode}")
            print(f"STDOUT: '{result.stdout}'")
            print(f"STDERR: '{result.stderr}'")
            
            # Try to parse
            if result.stdout:
                try:
                    import json
                    parsed = json.loads(result.stdout)
                    print(f"Parsed as JSON: {parsed}")
                except json.JSONDecodeError as e:
                    print(f"JSON parse error: {e}")
                    print(f"Raw output type: {type(result.stdout)}")
                    print(f"Raw output repr: {repr(result.stdout)}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "="*80)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Warnet Utilities")
        print("\nUsage: python warnet_utils.py <command> [args]")
        print("\nCommands:")
        print("  list                        - List all nodes with status")
        print("  health                      - Check network health")
        print("  mempool                     - Show mempool status")
        print("  reconnect                   - Force reconnect all nodes")
        print("  partition <g1> <g2>         - Partition network (e.g., '0,1,2' '3,4,5')")
        print("  monitor [duration]          - Monitor live (default 300s)")
        print("  compare <v1> <v2>           - Compare versions (e.g., '29.0' '28.1')")
        print("  debug [command]             - Debug RPC calls (default: getblockcount)")
        print("\nExamples:")
        print("  python warnet_utils.py list")
        print("  python warnet_utils.py health")
        print("  python warnet_utils.py partition '0,1,2,3' '4,5,6,7'")
        print("  python warnet_utils.py monitor 600")
        print("  python warnet_utils.py compare '29.0' '28.1'")
        print("  python warnet_utils.py debug")
        sys.exit(1)
    
    # Load config to get nodes
    config = ConfigLoader.load("test_config.yaml")
    nodes = config.get('network', {}).get('nodes', [f"tank-{i:04d}" for i in range(8)])
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_nodes(nodes)
    
    elif command == "health":
        check_network_health(nodes)
    
    elif command == "mempool":
        show_mempool_status(nodes)
    
    elif command == "reconnect":
        force_reconnect(nodes)
    
    elif command == "partition":
        if len(sys.argv) < 4:
            print("Error: partition requires two groups")
            print("Usage: python warnet_utils.py partition '0,1,2' '3,4,5'")
            sys.exit(1)
        
        group1_str = sys.argv[2]
        group2_str = sys.argv[3]
        
        group1_indices = [int(x.strip()) for x in group1_str.split(',')]
        group2_indices = [int(x.strip()) for x in group2_str.split(',')]
        
        partition_network(nodes, group1_indices, group2_indices)
    
    elif command == "monitor":
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        monitor_live(nodes, duration)
    
    elif command == "compare":
        if len(sys.argv) < 4:
            print("Error: compare requires two version strings")
            print("Usage: python warnet_utils.py compare '29.0' '28.1'")
            sys.exit(1)
        
        version_a = sys.argv[2]
        version_b = sys.argv[3]
        compare_versions(nodes, version_a, version_b)
    
    elif command == "debug":
        rpc_command = sys.argv[2] if len(sys.argv) > 2 else "getblockcount"
        debug_rpc(nodes, rpc_command)
    
    else:
        print(f"Unknown command: {command}")
        print("Run without arguments to see usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
    