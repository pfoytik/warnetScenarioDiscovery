"""
Warnet Bitcoin Fork Testing Framework - Advanced Edition
Complete testing suite with visualization, analysis, and reporting
"""

import subprocess
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import yaml
from collections import defaultdict
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('warnet_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """Information about a Warnet node"""
    name: str
    ip: str
    version: str
    

@dataclass
class NetworkSnapshot:
    """Complete network state snapshot"""
    timestamp: str
    nodes: Dict[str, dict] = field(default_factory=dict)
    fork_detected: bool = False
    unique_tips: int = 0
    
    
@dataclass
class TestResult:
    """Test execution results"""
    test_name: str
    start_time: str
    end_time: str
    duration: float
    fork_detected: bool
    pre_snapshot: NetworkSnapshot
    post_snapshot: NetworkSnapshot
    metrics: Dict = field(default_factory=dict)
    error: Optional[str] = None


class WarnetRPC:
    """Wrapper for Warnet Bitcoin RPC calls with retry logic"""
    
    @staticmethod
    def call(node: str, command: str, *args, retries: int = 3) -> dict:
        """Execute a Bitcoin RPC command via Warnet with retry"""
        for attempt in range(retries):
            try:
                cmd = ["warnet", "bitcoin", "rpc", node, command] + list(args)
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
                
                if not result.stdout or not result.stdout.strip():
                    return {}
                
                # Try to parse as JSON
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError as e:
                    # If it's a simple value (like a number), try to handle it
                    output = result.stdout.strip()
                    
                    # Check if it's a number
                    if output.isdigit():
                        return int(output)
                    
                    # Check if it's a float
                    try:
                        return float(output)
                    except ValueError:
                        pass
                    
                    # Check if it's a boolean string
                    if output.lower() in ('true', 'false'):
                        return output.lower() == 'true'
                    
                    # If it looks like a hash (hex string), return as is
                    if all(c in '0123456789abcdef' for c in output.lower()) and len(output) == 64:
                        return output
                    
                    # Otherwise log the error and return the raw output
                    logger.debug(f"Non-JSON response from {node}.{command}: {output[:100]}")
                    return output
                    
            except subprocess.CalledProcessError as e:
                if attempt == retries - 1:
                    logger.error(f"RPC error for {node}.{command}: {e.stderr}")
                    return {}
                time.sleep(1)
            except subprocess.TimeoutExpired:
                logger.warning(f"RPC timeout for {node}.{command}, retrying...")
                continue
        return {}
    
    @staticmethod
    def get_block_count(node: str) -> int:
        result = WarnetRPC.call(node, "getblockcount")
        if isinstance(result, int):
            return result
        elif isinstance(result, str) and result.isdigit():
            return int(result)
        elif isinstance(result, dict):
            return 0
        return 0
    
    @staticmethod
    def get_best_block_hash(node: str) -> str:
        result = WarnetRPC.call(node, "getbestblockhash")
        if isinstance(result, str):
            return result
        return ""
    
    @staticmethod
    def get_block(node: str, block_hash: str) -> dict:
        return WarnetRPC.call(node, "getblock", block_hash)
    
    @staticmethod
    def get_blockchain_info(node: str) -> dict:
        return WarnetRPC.call(node, "getblockchaininfo")
    
    @staticmethod
    def get_mempool_info(node: str) -> dict:
        return WarnetRPC.call(node, "getmempoolinfo")
    
    @staticmethod
    def get_raw_mempool(node: str) -> list:
        result = WarnetRPC.call(node, "getrawmempool")
        return result if isinstance(result, list) else []
    
    @staticmethod
    def get_peer_info(node: str) -> list:
        result = WarnetRPC.call(node, "getpeerinfo")
        return result if isinstance(result, list) else []
    
    @staticmethod
    def get_network_info(node: str) -> dict:
        return WarnetRPC.call(node, "getnetworkinfo")
    
    @staticmethod
    def get_chain_tips(node: str) -> list:
        result = WarnetRPC.call(node, "getchaintips")
        return result if isinstance(result, list) else []
    
    @staticmethod
    def set_ban(node: str, ip: str, action: str, duration: int = 86400):
        return WarnetRPC.call(node, "setban", ip, action, str(duration))
    
    @staticmethod
    def clear_banned(node: str):
        return WarnetRPC.call(node, "clearbanned")
    
    @staticmethod
    def add_node(node: str, peer_ip: str):
        return WarnetRPC.call(node, "addnode", peer_ip, "add")


class NetworkState:
    """Manages the state of the Warnet network"""
    
    def __init__(self, nodes: List[str]):
        self.nodes = nodes
        self.node_info: Dict[str, NodeInfo] = {}
        self.discover_nodes()
    
    def discover_nodes(self):
        """Discover node IPs and versions"""
        logger.info("Discovering node information...")
        for node in self.nodes:
            try:
                network_info = WarnetRPC.get_network_info(node)
                if network_info:
                    ip = self._extract_ip(network_info)
                    version = network_info.get('subversion', 'unknown')
                    self.node_info[node] = NodeInfo(node, ip, version)
                    logger.info(f"{node}: {ip} ({version})")
                else:
                    logger.warning(f"Could not get network info for {node}")
            except Exception as e:
                logger.error(f"Error discovering {node}: {e}", exc_info=True)
    
    def _extract_ip(self, network_info: dict) -> str:
        """Extract IP address from network info"""
        addresses = network_info.get('localaddresses', [])
        for addr in addresses:
            ip = addr.get('address', '')
            if ip.startswith('10.244'):
                return ip
        return ""
    
    def snapshot(self) -> NetworkSnapshot:
        """Take a complete snapshot of network state"""
        snapshot = NetworkSnapshot(
            timestamp=datetime.now().isoformat(),
            nodes={}
        )
        
        for node in self.nodes:
            blockchain_info = WarnetRPC.get_blockchain_info(node)
            snapshot.nodes[node] = {
                'height': WarnetRPC.get_block_count(node),
                'best_hash': WarnetRPC.get_best_block_hash(node),
                'mempool': WarnetRPC.get_mempool_info(node),
                'peer_count': len(WarnetRPC.get_peer_info(node)),
                'chain_work': blockchain_info.get('chainwork', ''),
                'difficulty': blockchain_info.get('difficulty', 0)
            }
        
        # Detect fork
        unique_hashes = set(data['best_hash'] for data in snapshot.nodes.values())
        snapshot.fork_detected = len(unique_hashes) > 1
        snapshot.unique_tips = len(unique_hashes)
        
        return snapshot
    
    def get_chain_tips(self) -> Dict[str, Tuple[int, str]]:
        """Get chain tips for all nodes (height, hash)"""
        tips = {}
        for node in self.nodes:
            height = WarnetRPC.get_block_count(node)
            hash = WarnetRPC.get_best_block_hash(node)
            tips[node] = (height, hash)
        return tips
    
    def detect_fork(self) -> bool:
        """Check if network is forked"""
        tips = self.get_chain_tips()
        hashes = set(hash for _, hash in tips.values())
        return len(hashes) > 1
    
    def find_fork_point(self) -> Optional[int]:
        """Find the block height where chains diverged"""
        tips = self.get_chain_tips()
        if len(set(hash for _, hash in tips.values())) <= 1:
            return None
        
        # Get minimum height
        min_height = min(height for height, _ in tips.values())
        
        # Binary search for fork point
        left, right = 0, min_height
        fork_height = 0
        
        while left <= right:
            mid = (left + right) // 2
            # Check if all nodes agree on block at this height
            hashes_at_height = set()
            
            for node in self.nodes:
                try:
                    block_hash = WarnetRPC.call(node, "getblockhash", str(mid))
                    if isinstance(block_hash, str):
                        hashes_at_height.add(block_hash)
                except:
                    pass
            
            if len(hashes_at_height) == 1:
                fork_height = mid
                left = mid + 1
            else:
                right = mid - 1
        
        return fork_height


class NetworkPartition:
    """Handles network partitioning operations"""
    
    def __init__(self, state: NetworkState):
        self.state = state
        self.active_partitions = []
    
    def partition_by_version(self, version_a: str, version_b: str):
        """Partition network by Bitcoin Core version"""
        logger.info(f"Partitioning network: {version_a} vs {version_b}")
        
        group_a = [n for n, info in self.state.node_info.items() 
                   if version_a in info.version]
        group_b = [n for n, info in self.state.node_info.items() 
                   if version_b in info.version]
        
        self._partition_groups(group_a, group_b)
        self.active_partitions.append(('version', group_a, group_b))
    
    def partition_custom(self, group_a: List[str], group_b: List[str]):
        """Partition network into custom groups"""
        logger.info(f"Custom partition: {group_a} vs {group_b}")
        self._partition_groups(group_a, group_b)
        self.active_partitions.append(('custom', group_a, group_b))
    
    def _partition_groups(self, group_a: List[str], group_b: List[str]):
        """Ban connections between two groups"""
        for node_a in group_a:
            for node_b in group_b:
                if node_b in self.state.node_info:
                    ip_b = self.state.node_info[node_b].ip
                    WarnetRPC.set_ban(node_a, ip_b, "add")
        
        for node_b in group_b:
            for node_a in group_a:
                if node_a in self.state.node_info:
                    ip_a = self.state.node_info[node_a].ip
                    WarnetRPC.set_ban(node_b, ip_a, "add")
        
        logger.info("Partition complete")
    
    def reconnect_all(self):
        """Remove all bans and reconnect network"""
        logger.info("Reconnecting network...")
        for node in self.state.nodes:
            WarnetRPC.clear_banned(node)
        
        # Force some connections
        if len(self.state.nodes) >= 2:
            node_0 = self.state.nodes[0]
            node_1 = self.state.nodes[1]
            if node_1 in self.state.node_info:
                ip_1 = self.state.node_info[node_1].ip
                WarnetRPC.add_node(node_0, ip_1)
        
        self.active_partitions.clear()
        logger.info("Reconnection initiated")


class TimeSeriesCollector:
    """Collects time-series data during tests"""
    
    def __init__(self, state: NetworkState):
        self.state = state
        self.height_data = defaultdict(list)  # {node: [(timestamp, height)]}
        self.mempool_data = defaultdict(list)  # {node: [(timestamp, size, bytes)]}
        self.fork_events = []  # [(timestamp, fork_detected, unique_tips)]
    
    def collect_heights(self):
        """Collect current block heights"""
        timestamp = time.time()
        for node in self.state.nodes:
            height = WarnetRPC.get_block_count(node)
            self.height_data[node].append((timestamp, height))
    
    def collect_mempools(self):
        """Collect mempool data"""
        timestamp = time.time()
        for node in self.state.nodes:
            mempool = WarnetRPC.get_mempool_info(node)
            size = mempool.get('size', 0)
            bytes = mempool.get('bytes', 0)
            self.mempool_data[node].append((timestamp, size, bytes))
    
    def collect_fork_status(self):
        """Collect fork detection status"""
        timestamp = time.time()
        snapshot = self.state.snapshot()
        self.fork_events.append((timestamp, snapshot.fork_detected, snapshot.unique_tips))
    
    def get_summary_stats(self) -> dict:
        """Calculate summary statistics"""
        stats = {
            'height_progression': {},
            'mempool_stats': {},
            'fork_duration': 0
        }
        
        # Height stats
        for node, data in self.height_data.items():
            if data:
                heights = [h for _, h in data]
                stats['height_progression'][node] = {
                    'start': heights[0],
                    'end': heights[-1],
                    'blocks_produced': heights[-1] - heights[0]
                }
        
        # Mempool stats
        for node, data in self.mempool_data.items():
            if data:
                sizes = [s for _, s, _ in data]
                stats['mempool_stats'][node] = {
                    'avg_size': statistics.mean(sizes) if sizes else 0,
                    'max_size': max(sizes) if sizes else 0,
                    'min_size': min(sizes) if sizes else 0
                }
        
        # Fork duration
        fork_periods = []
        in_fork = False
        fork_start = None
        
        for timestamp, forked, _ in self.fork_events:
            if forked and not in_fork:
                in_fork = True
                fork_start = timestamp
            elif not forked and in_fork:
                in_fork = False
                if fork_start:
                    fork_periods.append(timestamp - fork_start)
        
        stats['fork_duration'] = sum(fork_periods)
        stats['fork_count'] = len(fork_periods)
        
        return stats


class Monitor:
    """Enhanced monitoring with time-series collection"""
    
    def __init__(self, state: NetworkState):
        self.state = state
        self.collector = TimeSeriesCollector(state)
        self.monitoring = False
    
    def start_monitoring(self, height_interval: int = 5, mempool_interval: int = 30):
        """Start background monitoring"""
        self.monitoring = True
        # In a real implementation, use threading for concurrent monitoring
        logger.info("Monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        logger.info("Monitoring stopped")
    
    def monitor_session(self, duration: int, height_interval: int = 5, mempool_interval: int = 30):
        """Monitor for a specific duration"""
        logger.info(f"Monitoring session for {duration}s")
        start_time = time.time()
        last_height_check = 0
        last_mempool_check = 0
        
        while time.time() - start_time < duration:
            current_time = time.time() - start_time
            
            # Collect heights
            if current_time - last_height_check >= height_interval:
                try:
                    self.collector.collect_heights()
                    self.collector.collect_fork_status()
                    last_height_check = current_time
                    
                    # Display current state
                    tips = self.state.get_chain_tips()
                    print(f"\n[{int(current_time)}s]")
                    for node, (height, hash) in tips.items():
                        print(f"  {node}: {height} ({hash[:12]}...)")
                except Exception as e:
                    logger.error(f"Error collecting heights: {e}")
            
            # Collect mempools
            if current_time - last_mempool_check >= mempool_interval:
                try:
                    self.collector.collect_mempools()
                    last_mempool_check = current_time
                except Exception as e:
                    logger.error(f"Error collecting mempools: {e}")
            
            time.sleep(1)
        
        logger.info("Monitoring session complete")


class Analyzer:
    """Advanced analysis of test results"""
    
    @staticmethod
    def calculate_reorg_depth(pre_snapshot: NetworkSnapshot, post_snapshot: NetworkSnapshot) -> dict:
        """Calculate reorganization depth for each node"""
        reorg_depths = {}
        
        for node in pre_snapshot.nodes.keys():
            pre_height = pre_snapshot.nodes[node]['height']
            post_height = post_snapshot.nodes[node]['height']
            pre_hash = pre_snapshot.nodes[node]['best_hash']
            post_hash = post_snapshot.nodes[node]['best_hash']
            
            if pre_hash != post_hash:
                # Simplified reorg depth (actual depth would require block comparison)
                reorg_depths[node] = {
                    'occurred': True,
                    'pre_height': pre_height,
                    'post_height': post_height,
                    'height_change': post_height - pre_height
                }
            else:
                reorg_depths[node] = {'occurred': False}
        
        return reorg_depths
    
    @staticmethod
    def compare_chain_work(nodes_data: dict) -> dict:
        """Compare cumulative chain work between nodes"""
        chain_works = {}
        for node, data in nodes_data.items():
            chain_work = data.get('chain_work', '0')
            chain_works[node] = int(chain_work, 16) if chain_work else 0
        
        return {
            'chain_works': chain_works,
            'winner': max(chain_works, key=chain_works.get) if chain_works else None,
            'max_work': max(chain_works.values()) if chain_works else 0
        }
    
    @staticmethod
    def analyze_mempool_divergence(collector: TimeSeriesCollector) -> dict:
        """Analyze how mempools diverged during test"""
        analysis = {}
        
        for node, data in collector.mempool_data.items():
            if data:
                timestamps, sizes, bytes_data = zip(*data)
                analysis[node] = {
                    'peak_size': max(sizes),
                    'peak_bytes': max(bytes_data),
                    'final_size': sizes[-1],
                    'final_bytes': bytes_data[-1]
                }
        
        return analysis


class TestScenario(ABC):
    """Base class for test scenarios"""
    
    def __init__(self, name: str, state: NetworkState, config: dict = None):
        self.name = name
        self.state = state
        self.config = config or {}
        self.partition = NetworkPartition(state)
        self.monitor = Monitor(state)
        self.result = None
    
    @abstractmethod
    def setup(self):
        """Setup the test scenario"""
        pass
    
    @abstractmethod
    def execute(self):
        """Execute the test"""
        pass
    
    @abstractmethod
    def teardown(self):
        """Clean up after test"""
        pass
    
    def run(self) -> TestResult:
        """Run the complete test scenario"""
        logger.info(f"{'='*60}")
        logger.info(f"Starting test: {self.name}")
        logger.info(f"{'='*60}")
        
        start_time = datetime.now()
        
        try:
            # Pre-test snapshot
            pre_snapshot = self.state.snapshot()
            logger.info(f"Pre-test snapshot: Fork={pre_snapshot.fork_detected}")
            
            # Setup
            self.setup()
            time.sleep(5)  # Stabilization
            
            # Execute with monitoring
            self.execute()
            
            # Post-test snapshot
            post_snapshot = self.state.snapshot()
            logger.info(f"Post-test snapshot: Fork={post_snapshot.fork_detected}")
            
            # Analyze
            metrics = self.analyze()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.result = TestResult(
                test_name=self.name,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=duration,
                fork_detected=post_snapshot.fork_detected,
                pre_snapshot=pre_snapshot,
                post_snapshot=post_snapshot,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Test {self.name} failed: {e}", exc_info=True)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.result = TestResult(
                test_name=self.name,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=duration,
                fork_detected=False,
                pre_snapshot=NetworkSnapshot(timestamp=start_time.isoformat()),
                post_snapshot=NetworkSnapshot(timestamp=end_time.isoformat()),
                metrics={},
                error=str(e)
            )
        
        finally:
            # Cleanup
            try:
                self.teardown()
            except Exception as e:
                logger.error(f"Teardown failed: {e}")
        
        logger.info(f"Test {self.name} complete")
        return self.result
    
    def analyze(self) -> dict:
        """Analyze test results"""
        metrics = {
            'fork_point': self.state.find_fork_point(),
            'reorg_analysis': Analyzer.calculate_reorg_depth(
                self.result.pre_snapshot if self.result else NetworkSnapshot(timestamp=""),
                self.state.snapshot()
            ),
            'summary_stats': self.monitor.collector.get_summary_stats(),
            'mempool_analysis': Analyzer.analyze_mempool_divergence(self.monitor.collector)
        }
        return metrics


# Test Scenario Implementations

class VersionPartitionTest(TestScenario):
    """Test: Version-based network partition"""
    
    def setup(self):
        logger.info("Setting up version partition test")
        self.partition.partition_by_version("29.0", "28.1")
    
    def execute(self):
        duration = self.config.get('duration', 180)
        monitor_interval = self.config.get('monitor_interval', 5)
        logger.info(f"Executing test - monitoring for {duration}s")
        self.monitor.monitor_session(duration, height_interval=monitor_interval)
    
    def teardown(self):
        logger.info("Tearing down - reconnecting network")
        self.partition.reconnect_all()
        time.sleep(30)  # Wait for reconnection


class AsymmetricSplitTest(TestScenario):
    """Test: Asymmetric network split"""
    
    def setup(self):
        majority_size = self.config.get('majority_size', 6)
        logger.info(f"Setting up asymmetric split ({majority_size} vs others)")
        majority = self.state.nodes[:majority_size]
        minority = self.state.nodes[majority_size:]
        self.partition.partition_custom(majority, minority)
    
    def execute(self):
        duration = self.config.get('duration', 180)
        logger.info(f"Executing asymmetric split test - {duration}s")
        self.monitor.monitor_session(duration)
    
    def teardown(self):
        logger.info("Reconnecting network")
        self.partition.reconnect_all()
        time.sleep(30)


class FlappingConnectionTest(TestScenario):
    """Test: Intermittent connectivity"""
    
    def setup(self):
        logger.info("Setting up flapping connection test")
    
    def execute(self):
        iterations = self.config.get('iterations', 5)
        disconnect_duration = self.config.get('disconnect_duration', 30)
        connect_duration = self.config.get('connect_duration', 30)
        
        logger.info(f"Flapping connections for {iterations} iterations")
        node_a = self.state.nodes[0]
        node_b = self.state.nodes[4]
        ip_b = self.state.node_info[node_b].ip
        
        for i in range(iterations):
            logger.info(f"Iteration {i+1}: Disconnecting")
            WarnetRPC.set_ban(node_a, ip_b, "add", disconnect_duration)
            self.monitor.collector.collect_heights()
            self.monitor.collector.collect_fork_status()
            time.sleep(disconnect_duration)
            
            logger.info(f"Iteration {i+1}: Reconnecting")
            WarnetRPC.set_ban(node_a, ip_b, "remove")
            self.monitor.collector.collect_heights()
            self.monitor.collector.collect_fork_status()
            time.sleep(connect_duration)
    
    def teardown(self):
        logger.info("Ensuring all connections restored")
        self.partition.reconnect_all()


class RollingIsolationTest(TestScenario):
    """Test: Sequential node isolation"""
    
    def setup(self):
        logger.info("Setting up rolling isolation test")
    
    def execute(self):
        isolation_duration = self.config.get('isolation_duration', 60)
        stabilization = self.config.get('stabilization_period', 30)
        
        logger.info("Starting rolling isolation")
        
        for node in self.state.nodes:
            logger.info(f"Isolating {node}")
            
            # Ban this node from all others
            for other_node in self.state.nodes:
                if other_node != node and other_node in self.state.node_info:
                    other_ip = self.state.node_info[other_node].ip
                    WarnetRPC.set_ban(node, other_ip, "add", isolation_duration)
            
            self.monitor.collector.collect_heights()
            self.monitor.collector.collect_fork_status()
            time.sleep(isolation_duration)
            
            # Restore
            WarnetRPC.clear_banned(node)
            logger.info(f"Reconnected {node}")
            time.sleep(stabilization)
    
    def teardown(self):
        logger.info("Ensuring full connectivity")
        self.partition.reconnect_all()


class StarTopologyTest(TestScenario):
    """Test: Hub-and-spoke network"""
    
    def setup(self):
        hub = self.config.get('hub_node', self.state.nodes[0])
        logger.info(f"Creating star topology with {hub} as hub")
        
        spokes = [n for n in self.state.nodes if n != hub]
        
        # Ban all spoke-to-spoke connections
        for i, spoke_a in enumerate(spokes):
            for spoke_b in spokes[i+1:]:
                if spoke_a in self.state.node_info and spoke_b in self.state.node_info:
                    ip_a = self.state.node_info[spoke_a].ip
                    ip_b = self.state.node_info[spoke_b].ip
                    WarnetRPC.set_ban(spoke_a, ip_b, "add")
                    WarnetRPC.set_ban(spoke_b, ip_a, "add")
    
    def execute(self):
        duration = self.config.get('duration', 180)
        logger.info(f"Monitoring star topology - {duration}s")
        self.monitor.monitor_session(duration)
    
    def teardown(self):
        logger.info("Restoring mesh network")
        self.partition.reconnect_all()
        time.sleep(30)


class CascadeFailureTest(TestScenario):
    """Test: Sequential node failures"""
    
    def setup(self):
        logger.info("Setting up cascade failure test")
        self.failed_nodes = []
    
    def execute(self):
        failure_interval = self.config.get('failure_interval', 45)
        recovery_interval = self.config.get('recovery_interval', 45)
        
        logger.info("Starting cascade failure")
        num_failures = len(self.state.nodes) // 2  # Fail half the nodes
        
        for i in range(num_failures):
            node = self.state.nodes[i]
            logger.info(f"Failing node {node}")
            
            # Isolate this node
            for other_node in self.state.nodes:
                if other_node != node and other_node in self.state.node_info:
                    other_ip = self.state.node_info[other_node].ip
                    WarnetRPC.set_ban(node, other_ip, "add")
            
            self.failed_nodes.append(node)
            self.monitor.collector.collect_heights()
            self.monitor.collector.collect_fork_status()
            time.sleep(failure_interval)
        
        # Recovery phase
        logger.info("Starting recovery phase")
        for node in self.failed_nodes:
            logger.info(f"Recovering node {node}")
            WarnetRPC.clear_banned(node)
            time.sleep(recovery_interval)
    
    def teardown(self):
        logger.info("Ensuring all nodes recovered")
        for node in self.failed_nodes:
            WarnetRPC.clear_banned(node)
        self.partition.reconnect_all()


class ConfigLoader:
    """Load and parse test configuration"""
    
    @staticmethod
    def load(config_file: str = "test_config.yaml") -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file {config_file} not found")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config: {e}")
            return {}
    
    @staticmethod
    def get_enabled_tests(config: dict) -> list:
        """Get list of enabled test configurations"""
        test_suite = config.get('test_suite', [])
        return [test for test in test_suite if test.get('enabled', True)]


class TestOrchestrator:
    """Orchestrates multiple test scenarios"""
    
    # Map test type strings to classes
    TEST_CLASSES = {
        'VersionPartitionTest': VersionPartitionTest,
        'AsymmetricSplitTest': AsymmetricSplitTest,
        'FlappingConnectionTest': FlappingConnectionTest,
        'RollingIsolationTest': RollingIsolationTest,
        'StarTopologyTest': StarTopologyTest,
        'CascadeFailureTest': CascadeFailureTest
    }
    
    def __init__(self, nodes: List[str], config: dict = None):
        self.state = NetworkState(nodes)
        self.config = config or {}
        self.test_results: List[TestResult] = []
        self.report_dir = Path(config.get('reporting', {}).get('output_dir', 'test_reports'))
        self.report_dir.mkdir(exist_ok=True)
    
    def run_test(self, test_class, name: str, config: dict = None) -> TestResult:
        """Run a single test scenario"""
        test = test_class(name=name, state=self.state, config=config or {})
        result = test.run()
        self.test_results.append(result)
        
        # Stabilization period between tests
        logger.info("Waiting for network stabilization...")
        time.sleep(60)
        
        return result
    
    def run_test_suite(self):
        """Run complete test suite from config"""
        logger.info("="*60)
        logger.info("STARTING WARNET TEST SUITE")
        logger.info("="*60)
        
        enabled_tests = ConfigLoader.get_enabled_tests(self.config)
        logger.info(f"Running {len(enabled_tests)} tests")
        
        for test_config in enabled_tests:
            test_name = test_config.get('name')
            test_type = test_config.get('type')
            test_params = test_config.get('config', {})
            
            test_class = self.TEST_CLASSES.get(test_type)
            if not test_class:
                logger.error(f"Unknown test type: {test_type}")
                continue
            
            logger.info(f"\nRunning: {test_name} ({test_type})")
            self.run_test(test_class, test_name, test_params)
        
        logger.info("="*60)
        logger.info("TEST SUITE COMPLETE")
        logger.info("="*60)
        
        return self.test_results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("WARNET TEST REPORT".center(80))
        print("="*80)
        print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Network: {len(self.state.nodes)} nodes")
        print("-"*80)
        
        for i, result in enumerate(self.test_results, 1):
            print(f"\n{i}. {result.test_name}")
            print(f"   Duration: {result.duration:.1f}s")
            print(f"   Fork Detected: {'✓' if result.fork_detected else '✗'}")
            
            if result.error:
                print(f"   Error: {result.error}")
            else:
                # Metrics summary
                metrics = result.metrics
                fork_point = metrics.get('fork_point')
                if fork_point:
                    print(f"   Fork Point: Block {fork_point}")
                
                # Reorg analysis
                reorg = metrics.get('reorg_analysis', {})
                reorgs_occurred = sum(1 for data in reorg.values() if data.get('occurred'))
                if reorgs_occurred > 0:
                    print(f"   Reorgs: {reorgs_occurred} nodes")
                
                # Summary stats
                stats = metrics.get('summary_stats', {})
                if stats.get('fork_duration'):
                    print(f"   Fork Duration: {stats['fork_duration']:.1f}s")
                if stats.get('fork_count'):
                    print(f"   Fork Events: {stats['fork_count']}")
                
                # Height progression
                height_prog = stats.get('height_progression', {})
                if height_prog:
                    total_blocks = sum(data['blocks_produced'] for data in height_prog.values())
                    print(f"   Total Blocks Produced: {total_blocks}")
        
        print("\n" + "="*80)
        
        # Save detailed report to file
        self._save_detailed_report()
    
    def _save_detailed_report(self):
        """Save detailed JSON report"""
        report_file = self.report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'network': {
                'nodes': self.state.nodes,
                'node_info': {name: {'ip': info.ip, 'version': info.version} 
                             for name, info in self.state.node_info.items()}
            },
            'tests': []
        }
        
        for result in self.test_results:
            test_data = {
                'name': result.test_name,
                'start_time': result.start_time,
                'end_time': result.end_time,
                'duration': result.duration,
                'fork_detected': result.fork_detected,
                'error': result.error,
                'metrics': result.metrics,
                'pre_snapshot': {
                    'timestamp': result.pre_snapshot.timestamp,
                    'fork_detected': result.pre_snapshot.fork_detected,
                    'unique_tips': result.pre_snapshot.unique_tips,
                    'nodes': result.pre_snapshot.nodes
                },
                'post_snapshot': {
                    'timestamp': result.post_snapshot.timestamp,
                    'fork_detected': result.post_snapshot.fork_detected,
                    'unique_tips': result.post_snapshot.unique_tips,
                    'nodes': result.post_snapshot.nodes
                }
            }
            report_data['tests'].append(test_data)
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Detailed report saved to {report_file}")


# Main execution
def main():
    """Main entry point"""
    import sys
    
    # Load configuration
    config_file = sys.argv[1] if len(sys.argv) > 1 else "test_config.yaml"
    config = ConfigLoader.load(config_file)
    
    if not config:
        logger.error("Failed to load configuration. Using defaults.")
        config = {}
    
    # Get nodes from config or use defaults
    nodes = config.get('network', {}).get('nodes', [f"tank-{i:04d}" for i in range(8)])
    
    # Create orchestrator
    orchestrator = TestOrchestrator(nodes, config)
    
    # Run test suite
    orchestrator.run_test_suite()
    
    # Generate report
    orchestrator.generate_report()


if __name__ == "__main__":
    main()
    