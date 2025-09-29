#!/usr/bin/env python3
"""
Warnet Visualizer - Generate charts and graphs from test results
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import statistics


class ASCIIGraph:
    """Generate ASCII graphs for terminal display"""
    
    @staticmethod
    def line_chart(data: Dict[str, List[tuple]], title: str, width: int = 80, height: int = 20):
        """
        Generate ASCII line chart
        data: {series_name: [(x, y), (x, y), ...]}
        """
        if not data:
            return "No data to display"
        
        # Find min/max values
        all_values = []
        for series in data.values():
            all_values.extend([y for x, y in series])
        
        if not all_values:
            return "No data to display"
        
        min_val = min(all_values)
        max_val = max(all_values)
        
        # Avoid division by zero
        if max_val == min_val:
            max_val = min_val + 1
        
        # Build chart
        lines = [title]
        lines.append("=" * width)
        
        # Y-axis labels and data points
        for row in range(height, -1, -1):
            # Calculate the value this row represents
            value = min_val + (max_val - min_val) * (row / height)
            
            # Y-axis label
            line = f"{value:8.1f} │"
            
            # Plot points for this row
            char_line = [' '] * (width - 12)
            
            for series_name, series_data in data.items():
                symbol = '*' if len(data) == 1 else series_name[0].upper()
                
                for i, (x, y) in enumerate(series_data):
                    # Map y value to row
                    y_normalized = (y - min_val) / (max_val - min_val)
                    y_row = int(y_normalized * height)
                    
                    # Map x to column
                    x_col = int((i / max(len(series_data) - 1, 1)) * (width - 13))
                    
                    if y_row == row and 0 <= x_col < len(char_line):
                        char_line[x_col] = symbol
            
            line += ''.join(char_line)
            lines.append(line)
        
        # X-axis
        lines.append(" " * 9 + "└" + "─" * (width - 12))
        
        # Legend
        if len(data) > 1:
            lines.append("\nLegend:")
            for name in data.keys():
                lines.append(f"  {name[0].upper()} = {name}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def bar_chart(data: Dict[str, float], title: str, width: int = 60):
        """
        Generate ASCII bar chart
        data: {label: value}
        """
        if not data:
            return "No data to display"
        
        lines = [title]
        lines.append("=" * width)
        
        max_val = max(data.values()) if data.values() else 1
        max_label_len = max(len(label) for label in data.keys())
        
        for label, value in data.items():
            bar_width = int((value / max_val) * (width - max_label_len - 10))
            bar = "█" * bar_width
            lines.append(f"{label:>{max_label_len}} │ {bar} {value:.1f}")
        
        return '\n'.join(lines)


class ReportGenerator:
    """Generate comprehensive reports from test results"""
    
    def __init__(self, report_file: str):
        with open(report_file, 'r') as f:
            self.data = json.load(f)
        self.timestamp = self.data.get('timestamp', 'Unknown')
        self.tests = self.data.get('tests', [])
        self.network = self.data.get('network', {})
    
    def generate_text_report(self) -> str:
        """Generate detailed text report"""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("WARNET TEST RESULTS - DETAILED REPORT".center(80))
        lines.append("=" * 80)
        lines.append(f"\nGenerated: {self.timestamp}")
        lines.append(f"Network: {len(self.network.get('nodes', []))} nodes")
        lines.append(f"Total Tests: {len(self.tests)}")
        
        # Summary statistics
        lines.append("\n" + "=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        
        forks_detected = sum(1 for test in self.tests if test.get('fork_detected'))
        errors = sum(1 for test in self.tests if test.get('error'))
        total_duration = sum(test.get('duration', 0) for test in self.tests)
        
        lines.append(f"\nTests with Forks:  {forks_detected}/{len(self.tests)}")
        lines.append(f"Tests with Errors: {errors}/{len(self.tests)}")
        lines.append(f"Total Duration:    {total_duration:.1f}s ({total_duration/60:.1f}m)")
        
        # Test durations bar chart
        if self.tests:
            lines.append("\n" + "-" * 80)
            lines.append("Test Durations")
            lines.append("-" * 80)
            durations = {test['name']: test.get('duration', 0) for test in self.tests}
            lines.append(ASCIIGraph.bar_chart(durations, "", width=70))
        
        # Detailed test results
        lines.append("\n" + "=" * 80)
        lines.append("DETAILED TEST RESULTS")
        lines.append("=" * 80)
        
        for i, test in enumerate(self.tests, 1):
            lines.append(f"\n{i}. {test['name']}")
            lines.append("-" * 80)
            lines.append(f"Duration:      {test.get('duration', 0):.1f}s")
            lines.append(f"Start Time:    {test.get('start_time', 'N/A')}")
            lines.append(f"End Time:      {test.get('end_time', 'N/A')}")
            lines.append(f"Fork Detected: {'✓ YES' if test.get('fork_detected') else '✗ NO'}")
            
            if test.get('error'):
                lines.append(f"ERROR:         {test['error']}")
                continue
            
            # Metrics
            metrics = test.get('metrics', {})
            
            # Fork information
            if test.get('fork_detected'):
                fork_point = metrics.get('fork_point')
                if fork_point:
                    lines.append(f"Fork Point:    Block {fork_point}")
                
                summary = metrics.get('summary_stats', {})
                if summary.get('fork_duration'):
                    lines.append(f"Fork Duration: {summary['fork_duration']:.1f}s")
                if summary.get('fork_count'):
                    lines.append(f"Fork Events:   {summary['fork_count']}")
            
            # Block production
            height_prog = metrics.get('summary_stats', {}).get('height_progression', {})
            if height_prog:
                lines.append("\nBlock Production:")
                total_blocks = 0
                for node, data in height_prog.items():
                    blocks = data.get('blocks_produced', 0)
                    total_blocks += blocks
                    lines.append(f"  {node}: {blocks} blocks ({data.get('start', 0)} → {data.get('end', 0)})")
                lines.append(f"  TOTAL: {total_blocks} blocks")
            
            # Mempool stats
            mempool_stats = metrics.get('summary_stats', {}).get('mempool_stats', {})
            if mempool_stats:
                lines.append("\nMempool Statistics:")
                for node, stats in list(mempool_stats.items())[:4]:  # Show first 4
                    avg = stats.get('avg_size', 0)
                    max_size = stats.get('max_size', 0)
                    lines.append(f"  {node}: avg={avg:.0f}, max={max_size}")
            
            # Reorg analysis
            reorg = metrics.get('reorg_analysis', {})
            reorgs = [node for node, data in reorg.items() if data.get('occurred')]
            if reorgs:
                lines.append(f"\nReorganizations: {len(reorgs)} nodes")
                for node in reorgs[:5]:  # Show first 5
                    data = reorg[node]
                    lines.append(f"  {node}: {data.get('pre_height', 0)} → {data.get('post_height', 0)}")
            
            # Pre/Post snapshots
            pre_snap = test.get('pre_snapshot', {})
            post_snap = test.get('post_snapshot', {})
            
            if pre_snap.get('unique_tips') != post_snap.get('unique_tips'):
                lines.append(f"\nChain Tips: {pre_snap.get('unique_tips', 0)} → {post_snap.get('unique_tips', 0)}")
        
        # Network information
        lines.append("\n" + "=" * 80)
        lines.append("NETWORK CONFIGURATION")
        lines.append("=" * 80)
        
        node_info = self.network.get('node_info', {})
        if node_info:
            lines.append(f"\n{'Node':<15} {'IP Address':<20} {'Version':<20}")
            lines.append("-" * 80)
            for node, info in node_info.items():
                lines.append(f"{node:<15} {info.get('ip', 'N/A'):<20} {info.get('version', 'N/A'):<20}")
        
        lines.append("\n" + "=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return '\n'.join(lines)
    
    def generate_height_progression_chart(self, test_name: str = None):
        """Generate height progression chart for a specific test"""
        if test_name:
            test = next((t for t in self.tests if t['name'] == test_name), None)
            if not test:
                return f"Test '{test_name}' not found"
            tests_to_chart = [test]
        else:
            tests_to_chart = self.tests
        
        for test in tests_to_chart:
            print(f"\nHeight Progression: {test['name']}")
            print("=" * 80)
            
            metrics = test.get('metrics', {})
            height_prog = metrics.get('summary_stats', {}).get('height_progression', {})
            
            if not height_prog:
                print("No height progression data available")
                continue
            
            # Create chart data (simplified - would need time series for real chart)
            data = {}
            for node, prog in height_prog.items():
                start = prog.get('start', 0)
                end = prog.get('end', 0)
                blocks = prog.get('blocks_produced', 0)
                # Create simple progression
                data[node] = [(0, start), (1, end)]
            
            chart = ASCIIGraph.line_chart(data, f"Block Heights - {test['name']}", height=15)
            print(chart)
            print()
    
    def generate_comparison_chart(self):
        """Generate comparison chart across all tests"""
        print("\n" + "=" * 80)
        print("TEST COMPARISON")
        print("=" * 80)
        
        # Fork detection comparison
        fork_data = {}
        for test in self.tests:
            fork_data[test['name']] = 1.0 if test.get('fork_detected') else 0.0
        
        print("\nFork Detection (1=Yes, 0=No):")
        print(ASCIIGraph.bar_chart(fork_data, "", width=70))
        
        # Duration comparison
        duration_data = {test['name']: test.get('duration', 0) for test in self.tests}
        print("\nTest Durations (seconds):")
        print(ASCIIGraph.bar_chart(duration_data, "", width=70))
        
        # Block production comparison
        blocks_data = {}
        for test in self.tests:
            metrics = test.get('metrics', {})
            height_prog = metrics.get('summary_stats', {}).get('height_progression', {})
            total_blocks = sum(data.get('blocks_produced', 0) for data in height_prog.values())
            if total_blocks > 0:
                blocks_data[test['name']] = total_blocks
        
        if blocks_data:
            print("\nTotal Blocks Produced:")
            print(ASCIIGraph.bar_chart(blocks_data, "", width=70))
    
    def save_text_report(self, output_file: str):
        """Save text report to file"""
        report = self.generate_text_report()
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Warnet Visualizer")
        print("\nUsage: python warnet_visualizer.py <report_file.json> [command]")
        print("\nCommands:")
        print("  text              - Generate text report (default)")
        print("  save <file>       - Save text report to file")
        print("  heights [test]    - Show height progression chart")
        print("  compare           - Show comparison across tests")
        print("\nExamples:")
        print("  python warnet_visualizer.py test_reports/test_report_20250929_103000.json")
        print("  python warnet_visualizer.py report.json save output.txt")
        print("  python warnet_visualizer.py report.json heights version_partition")
        print("  python warnet_visualizer.py report.json compare")
        sys.exit(1)
    
    report_file = sys.argv[1]
    
    if not Path(report_file).exists():
        print(f"Error: Report file '{report_file}' not found")
        sys.exit(1)
    
    generator = ReportGenerator(report_file)
    
    command = sys.argv[2].lower() if len(sys.argv) > 2 else "text"
    
    if command == "text":
        print(generator.generate_text_report())
    
    elif command == "save":
        if len(sys.argv) < 4:
            print("Error: save requires output filename")
            print("Usage: python warnet_visualizer.py report.json save output.txt")
            sys.exit(1)
        output_file = sys.argv[3]
        generator.save_text_report(output_file)
    
    elif command == "heights":
        test_name = sys.argv[3] if len(sys.argv) > 3 else None
        generator.generate_height_progression_chart(test_name)
    
    elif command == "compare":
        generator.generate_comparison_chart()
    
    else:
        print(f"Unknown command: {command}")
        print("Run without arguments to see usage")
        sys.exit(1)


if __name__ == "__main__":
    main()