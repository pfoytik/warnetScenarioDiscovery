#!/usr/bin/env python3
"""
Temporal Analysis Tool for Warnet Fork Tests

Parses block timestamps from scenario logs, generates time-series data,
and creates visualizations to understand fork dynamics over time.

Features:
- Block mining timeline (blocks over time)
- Mining rate analysis (blocks/min in rolling windows)
- Fork depth evolution
- Height divergence tracking
- Per-version mining rate comparison

Usage:
    python3 temporal_analyzer.py --log scenario.log --output analysis/
    python3 temporal_analyzer.py --test-log test_run.log --config test-config
"""

import re
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sys

# Try to import matplotlib, but make it optional
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Visualizations will be skipped.")
    print("Install with: pip install matplotlib")


@dataclass
class BlockEvent:
    """Represents a block mining event"""
    timestamp_sec: float
    version: str  # 'v27' or 'v26'
    node: str
    height_v27: int
    height_v26: int
    fork_depth: int
    cumulative_v27: int
    cumulative_v26: int


class TemporalAnalyzer:
    """Analyzes temporal dynamics of fork tests"""

    def __init__(self):
        self.events: List[BlockEvent] = []
        self.test_duration: Optional[float] = None
        self.start_height: int = 101  # Default common history height

    def parse_scenario_log(self, log_path: str) -> bool:
        """
        Parse partition_miner scenario log for block events.

        Format: [  12s] v26 block by node-8 | Heights: v27=102 v26=101 | Fork depth: 1 | Mined: v27=1 v26=1
        """
        try:
            with open(log_path, 'r') as f:
                content = f.read()

            # Pattern to match block mining lines
            pattern = r'\[\s*(\d+)s\]\s+(v2[67])\s+block by (node-\d+)\s+\|\s+Heights:\s+v27=(\d+)\s+v26=(\d+)\s+\|\s+Fork depth:\s+(\d+)\s+\|\s+Mined:\s+v27=\s*(\d+)\s+v26=\s*(\d+)'

            matches = re.findall(pattern, content)

            if not matches:
                print(f"Warning: No block events found in {log_path}")
                return False

            for match in matches:
                timestamp, version, node, h_v27, h_v26, fork_depth, mined_v27, mined_v26 = match

                event = BlockEvent(
                    timestamp_sec=float(timestamp),
                    version=version,
                    node=node,
                    height_v27=int(h_v27),
                    height_v26=int(h_v26),
                    fork_depth=int(fork_depth),
                    cumulative_v27=int(mined_v27),
                    cumulative_v26=int(mined_v26)
                )
                self.events.append(event)

            # Detect test duration from log
            duration_match = re.search(r'Duration:\s+(\d+)\.?\d*\s+minutes', content)
            if duration_match:
                self.test_duration = float(duration_match.group(1)) * 60

            print(f"✓ Parsed {len(self.events)} block events")
            if self.test_duration:
                print(f"  Test duration: {self.test_duration/60:.1f} minutes")

            return True

        except Exception as e:
            print(f"Error parsing log: {e}")
            return False

    def generate_time_series_data(self) -> Dict:
        """Generate structured time-series data from events"""

        if not self.events:
            return {}

        # Sort events by timestamp
        sorted_events = sorted(self.events, key=lambda e: e.timestamp_sec)

        time_series = {
            'timestamps': [],
            'v27_cumulative_blocks': [],
            'v26_cumulative_blocks': [],
            'v27_height': [],
            'v26_height': [],
            'height_difference': [],
            'fork_depth': [],
            'mining_version': []  # Which version mined each block
        }

        for event in sorted_events:
            time_series['timestamps'].append(event.timestamp_sec)
            time_series['v27_cumulative_blocks'].append(event.cumulative_v27)
            time_series['v26_cumulative_blocks'].append(event.cumulative_v26)
            time_series['v27_height'].append(event.height_v27)
            time_series['v26_height'].append(event.height_v26)
            time_series['height_difference'].append(abs(event.height_v27 - event.height_v26))
            time_series['fork_depth'].append(event.fork_depth)
            time_series['mining_version'].append(event.version)

        return time_series

    def calculate_mining_rates(self, window_sec: float = 60.0) -> Dict:
        """
        Calculate mining rates in rolling time windows.

        Args:
            window_sec: Window size in seconds for rate calculation

        Returns:
            Dict with timestamps and mining rates (blocks/min)
        """
        if not self.events:
            return {}

        sorted_events = sorted(self.events, key=lambda e: e.timestamp_sec)

        rates = {
            'timestamps': [],
            'v27_rate': [],  # blocks per minute
            'v26_rate': [],
            'total_rate': []
        }

        # Calculate rate at each event timestamp
        for i, event in enumerate(sorted_events):
            t = event.timestamp_sec

            # Count blocks in window [t - window_sec, t]
            v27_count = sum(1 for e in sorted_events
                           if t - window_sec <= e.timestamp_sec <= t and e.version == 'v27')
            v26_count = sum(1 for e in sorted_events
                           if t - window_sec <= e.timestamp_sec <= t and e.version == 'v26')

            # Convert to blocks per minute
            window_min = window_sec / 60.0
            v27_rate = v27_count / window_min
            v26_rate = v26_count / window_min

            rates['timestamps'].append(t)
            rates['v27_rate'].append(v27_rate)
            rates['v26_rate'].append(v26_rate)
            rates['total_rate'].append(v27_rate + v26_rate)

        return rates

    def generate_summary_statistics(self) -> Dict:
        """Generate summary statistics from the time series"""

        if not self.events:
            return {}

        sorted_events = sorted(self.events, key=lambda e: e.timestamp_sec)
        last_event = sorted_events[-1]

        v27_blocks = last_event.cumulative_v27
        v26_blocks = last_event.cumulative_v26
        total_blocks = v27_blocks + v26_blocks

        # Calculate average time between blocks
        v27_events = [e for e in sorted_events if e.version == 'v27']
        v26_events = [e for e in sorted_events if e.version == 'v26']

        v27_avg_time = None
        v26_avg_time = None

        if len(v27_events) > 1:
            v27_times = [e.timestamp_sec for e in v27_events]
            v27_intervals = [v27_times[i+1] - v27_times[i] for i in range(len(v27_times)-1)]
            v27_avg_time = sum(v27_intervals) / len(v27_intervals) if v27_intervals else None

        if len(v26_events) > 1:
            v26_times = [e.timestamp_sec for e in v26_events]
            v26_intervals = [v26_times[i+1] - v26_times[i] for i in range(len(v26_times)-1)]
            v26_avg_time = sum(v26_intervals) / len(v26_intervals) if v26_intervals else None

        stats = {
            'total_duration_sec': last_event.timestamp_sec,
            'total_blocks_mined': total_blocks,
            'v27_blocks': v27_blocks,
            'v26_blocks': v26_blocks,
            'v27_percentage': (v27_blocks / total_blocks * 100) if total_blocks > 0 else 0,
            'v26_percentage': (v26_blocks / total_blocks * 100) if total_blocks > 0 else 0,
            'final_fork_depth': last_event.fork_depth,
            'final_v27_height': last_event.height_v27,
            'final_v26_height': last_event.height_v26,
            'v27_avg_block_time_sec': v27_avg_time,
            'v26_avg_block_time_sec': v26_avg_time,
            'v27_blocks_per_min': (v27_blocks / (last_event.timestamp_sec / 60)) if last_event.timestamp_sec > 0 else 0,
            'v26_blocks_per_min': (v26_blocks / (last_event.timestamp_sec / 60)) if last_event.timestamp_sec > 0 else 0
        }

        return stats

    def plot_cumulative_blocks(self, output_path: str):
        """Plot cumulative blocks mined over time"""

        if not HAS_MATPLOTLIB:
            print("  Skipping plot: matplotlib not available")
            return

        ts = self.generate_time_series_data()
        if not ts:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Convert timestamps to minutes
        times_min = [t/60 for t in ts['timestamps']]

        ax.plot(times_min, ts['v27_cumulative_blocks'], 'b-o', label='v27 blocks', linewidth=2, markersize=6)
        ax.plot(times_min, ts['v26_cumulative_blocks'], 'r-o', label='v26 blocks', linewidth=2, markersize=6)

        ax.set_xlabel('Time (minutes)', fontsize=12)
        ax.set_ylabel('Cumulative Blocks Mined', fontsize=12)
        ax.set_title('Block Production Over Time', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved cumulative blocks plot: {output_path}")

    def plot_mining_rates(self, output_path: str, window_sec: float = 120.0):
        """Plot mining rates over time with rolling window"""

        if not HAS_MATPLOTLIB:
            print("  Skipping plot: matplotlib not available")
            return

        rates = self.calculate_mining_rates(window_sec)
        if not rates:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Convert timestamps to minutes
        times_min = [t/60 for t in rates['timestamps']]

        ax.plot(times_min, rates['v27_rate'], 'b-', label='v27 rate', linewidth=2, alpha=0.7)
        ax.plot(times_min, rates['v26_rate'], 'r-', label='v26 rate', linewidth=2, alpha=0.7)
        ax.plot(times_min, rates['total_rate'], 'g--', label='Total rate', linewidth=2, alpha=0.5)

        # Add expected rate line (6 blocks/hour = 0.1 blocks/min in Bitcoin)
        expected_rate = 0.1
        ax.axhline(y=expected_rate, color='gray', linestyle=':', linewidth=1.5,
                  label=f'Expected (regtest)')

        ax.set_xlabel('Time (minutes)', fontsize=12)
        ax.set_ylabel(f'Mining Rate (blocks/min, {window_sec}s window)', fontsize=12)
        ax.set_title('Mining Rate Over Time', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved mining rates plot: {output_path}")

    def plot_fork_evolution(self, output_path: str):
        """Plot fork depth and height difference evolution"""

        if not HAS_MATPLOTLIB:
            print("  Skipping plot: matplotlib not available")
            return

        ts = self.generate_time_series_data()
        if not ts:
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Convert timestamps to minutes
        times_min = [t/60 for t in ts['timestamps']]

        # Plot 1: Heights over time
        ax1.plot(times_min, ts['v27_height'], 'b-o', label='v27 height', linewidth=2, markersize=5)
        ax1.plot(times_min, ts['v26_height'], 'r-o', label='v26 height', linewidth=2, markersize=5)
        ax1.axhline(y=self.start_height, color='gray', linestyle='--', linewidth=1,
                   label=f'Common ancestor (height {self.start_height})')

        ax1.set_xlabel('Time (minutes)', fontsize=12)
        ax1.set_ylabel('Block Height', fontsize=12)
        ax1.set_title('Chain Heights Over Time', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Fork depth over time
        ax2.plot(times_min, ts['fork_depth'], 'purple', linewidth=2.5, marker='o', markersize=5)
        ax2.fill_between(times_min, 0, ts['fork_depth'], alpha=0.3, color='purple')

        ax2.set_xlabel('Time (minutes)', fontsize=12)
        ax2.set_ylabel('Fork Depth (blocks)', fontsize=12)
        ax2.set_title('Fork Depth Evolution', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved fork evolution plot: {output_path}")

    def plot_height_difference(self, output_path: str):
        """Plot absolute height difference over time"""

        if not HAS_MATPLOTLIB:
            print("  Skipping plot: matplotlib not available")
            return

        ts = self.generate_time_series_data()
        if not ts:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Convert timestamps to minutes
        times_min = [t/60 for t in ts['timestamps']]

        ax.plot(times_min, ts['height_difference'], 'orange', linewidth=2.5, marker='s', markersize=5)
        ax.fill_between(times_min, 0, ts['height_difference'], alpha=0.2, color='orange')

        ax.set_xlabel('Time (minutes)', fontsize=12)
        ax.set_ylabel('|Height(v27) - Height(v26)|', fontsize=12)
        ax.set_title('Chain Height Difference Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved height difference plot: {output_path}")

    def export_time_series_json(self, output_path: str):
        """Export time series data as JSON for further analysis"""

        ts = self.generate_time_series_data()
        stats = self.generate_summary_statistics()

        export_data = {
            'summary_statistics': stats,
            'time_series': ts,
            'events': [
                {
                    'timestamp_sec': e.timestamp_sec,
                    'version': e.version,
                    'node': e.node,
                    'height_v27': e.height_v27,
                    'height_v26': e.height_v26,
                    'fork_depth': e.fork_depth,
                    'cumulative_v27': e.cumulative_v27,
                    'cumulative_v26': e.cumulative_v26
                }
                for e in self.events
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✓ Exported time series data: {output_path}")

    def print_summary(self):
        """Print summary statistics to console"""

        stats = self.generate_summary_statistics()
        if not stats:
            print("No data to summarize")
            return

        print("\n" + "="*70)
        print("TEMPORAL ANALYSIS SUMMARY")
        print("="*70)
        print(f"Test Duration: {stats['total_duration_sec']:.1f}s ({stats['total_duration_sec']/60:.1f} min)")
        print(f"Total Blocks Mined: {stats['total_blocks_mined']}")
        print()
        print(f"v27 Performance:")
        print(f"  Blocks: {stats['v27_blocks']} ({stats['v27_percentage']:.1f}%)")
        print(f"  Final Height: {stats['final_v27_height']}")
        print(f"  Mining Rate: {stats['v27_blocks_per_min']:.3f} blocks/min")
        if stats['v27_avg_block_time_sec']:
            print(f"  Avg Time Between Blocks: {stats['v27_avg_block_time_sec']:.1f}s")
        print()
        print(f"v26 Performance:")
        print(f"  Blocks: {stats['v26_blocks']} ({stats['v26_percentage']:.1f}%)")
        print(f"  Final Height: {stats['final_v26_height']}")
        print(f"  Mining Rate: {stats['v26_blocks_per_min']:.3f} blocks/min")
        if stats['v26_avg_block_time_sec']:
            print(f"  Avg Time Between Blocks: {stats['v26_avg_block_time_sec']:.1f}s")
        print()
        print(f"Fork Metrics:")
        print(f"  Final Fork Depth: {stats['final_fork_depth']} blocks")
        print(f"  Height Difference: {abs(stats['final_v27_height'] - stats['final_v26_height'])} blocks")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Temporal Analysis Tool for Warnet Fork Tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze scenario log and create visualizations
  python3 temporal_analyzer.py --log /tmp/scenario_logs.log --output ./analysis/

  # Export time series data only (no plots)
  python3 temporal_analyzer.py --log scenario.log --export-json timeline.json --no-plots

  # Analyze with custom window for rate calculation
  python3 temporal_analyzer.py --log scenario.log --rate-window 180
        """
    )

    parser.add_argument(
        '--log',
        type=str,
        required=True,
        help='Path to scenario log file (partition_miner output)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='./temporal_analysis',
        help='Output directory for plots and data (default: ./temporal_analysis)'
    )

    parser.add_argument(
        '--export-json',
        type=str,
        help='Export time series data to JSON file'
    )

    parser.add_argument(
        '--rate-window',
        type=int,
        default=120,
        help='Window size in seconds for mining rate calculation (default: 120)'
    )

    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Skip generating plots (only export data)'
    )

    parser.add_argument(
        '--start-height',
        type=int,
        default=101,
        help='Common ancestor height (default: 101)'
    )

    args = parser.parse_args()

    # Create analyzer
    analyzer = TemporalAnalyzer()
    analyzer.start_height = args.start_height

    # Parse log file
    print(f"Parsing log file: {args.log}")
    if not analyzer.parse_scenario_log(args.log):
        print("Failed to parse log file")
        return 1

    # Print summary
    analyzer.print_summary()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export JSON if requested
    if args.export_json:
        analyzer.export_time_series_json(args.export_json)
    else:
        # Default JSON export
        default_json = output_dir / 'time_series_data.json'
        analyzer.export_time_series_json(str(default_json))

    # Generate plots if not disabled
    if not args.no_plots:
        print("\nGenerating visualizations...")
        analyzer.plot_cumulative_blocks(str(output_dir / 'cumulative_blocks.png'))
        analyzer.plot_mining_rates(str(output_dir / 'mining_rates.png'), window_sec=args.rate_window)
        analyzer.plot_fork_evolution(str(output_dir / 'fork_evolution.png'))
        analyzer.plot_height_difference(str(output_dir / 'height_difference.png'))

    print(f"\n✓ Analysis complete! Results saved to: {output_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
