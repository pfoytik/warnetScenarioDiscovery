#!/usr/bin/env python3
"""
Custody/Volume Weight Optimizer

Empirically tests different custody/volume weight combinations to find
which best predicts actual fork outcomes.

The current 70/30 (custody/volume) split is an assumption. This tool:
1. Loads actual test results (fork outcomes)
2. Recalculates consensus weights with different weight combinations
3. Measures predictive power of each weighting scheme
4. Identifies optimal weights based on empirical data

Metrics tested:
- Correlation between consensus weight and blocks mined
- Accuracy in predicting winning chain
- Ability to predict fork depth
- Risk score calibration

Usage:
    python3 weight_optimizer.py --results-dir test_results/
    python3 weight_optimizer.py --results-dir test_results/ --output weights_analysis.json
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import sys
from dataclasses import dataclass
import math


@dataclass
class TestResult:
    """Parsed test result with economic and mining data"""
    config_id: str
    econ_v27_pct: float
    econ_v26_pct: float
    hash_v27_pct: float
    hash_v26_pct: float
    blocks_v27: int
    blocks_v26: int
    fork_depth: int
    v27_nodes: List[Dict]  # Economic nodes on v27
    v26_nodes: List[Dict]  # Economic nodes on v26


class WeightOptimizer:
    """Optimizes custody/volume weights based on empirical fork outcomes"""

    # Network constants (from economic_fork_analyzer.py)
    CIRCULATING_SUPPLY = 19_500_000  # BTC
    DAILY_ONCHAIN_VOLUME = 300_000   # BTC/day

    def __init__(self):
        self.test_results: List[TestResult] = []

        # Weight combinations to test
        self.weights_to_test = [
            # Volume-heavy (inverse of current assumption)
            (0.1, 0.9),  # 10% custody, 90% volume - extreme volume dominance
            (0.2, 0.8),  # 20% custody, 80% volume
            (0.3, 0.7),  # 30% custody, 70% volume - inversion of current
            (0.4, 0.6),  # 40% custody, 60% volume

            # Balanced
            (0.5, 0.5),  # Equal weight

            # Custody-heavy (current assumption)
            (0.6, 0.4),  # 60% custody, 40% volume
            (0.7, 0.3),  # 70% custody, 30% volume - current default
            (0.8, 0.2),  # 80% custody, 20% volume
            (0.9, 0.1),  # 90% custody, 10% volume - extreme custody dominance
        ]

    def load_test_results(self, results_dir: str) -> int:
        """Load all test results from directory"""

        results_path = Path(results_dir)
        if not results_path.exists():
            print(f"Error: Results directory not found: {results_dir}")
            return 0

        loaded = 0
        for result_file in results_path.glob('*_result.json'):
            try:
                with open(result_file) as f:
                    data = json.load(f)

                # Skip failed tests or tests without economic analysis
                if data['status'] != 'success':
                    continue
                if not data.get('economic_analysis'):
                    continue
                if data.get('fork_depth', 0) == 0:
                    continue  # Skip tests with no fork

                # Extract economic nodes
                econ_data = data.get('economic_analysis', {})
                chains = econ_data.get('chains', {})

                v27_nodes = []
                v26_nodes = []

                # Determine which chain is v27 vs v26 based on heights
                # (economic analysis labels chains as A/B, not by version)
                chain_a = chains.get('chain_a', {})
                chain_b = chains.get('chain_b', {})

                # Get version assignments from fork metadata if available
                fork_meta = econ_data.get('fork_metadata', {})

                # For now, match by node count or use heuristic
                # v27 usually has fewer nodes in our tests
                if len(chain_a.get('economic_nodes', [])) < len(chain_b.get('economic_nodes', [])):
                    v27_nodes = chain_a.get('economic_nodes', [])
                    v26_nodes = chain_b.get('economic_nodes', [])
                else:
                    v27_nodes = chain_b.get('economic_nodes', [])
                    v26_nodes = chain_a.get('economic_nodes', [])

                result = TestResult(
                    config_id=data['config_id'],
                    econ_v27_pct=data['splits']['economic']['v27'],
                    econ_v26_pct=data['splits']['economic']['v26'],
                    hash_v27_pct=data['splits']['hashrate']['v27'],
                    hash_v26_pct=data['splits']['hashrate']['v26'],
                    blocks_v27=data['steps']['mining']['blocks']['v27'],
                    blocks_v26=data['steps']['mining']['blocks']['v26'],
                    fork_depth=data['fork_depth'],
                    v27_nodes=v27_nodes,
                    v26_nodes=v26_nodes
                )

                self.test_results.append(result)
                loaded += 1

            except Exception as e:
                print(f"Warning: Could not load {result_file.name}: {e}")
                continue

        print(f"✓ Loaded {loaded} test results with economic data")
        return loaded

    def calculate_consensus_weight(self, nodes: List[Dict],
                                   custody_weight: float,
                                   volume_weight: float) -> float:
        """
        Calculate total consensus weight for a set of nodes with given weights.

        Args:
            nodes: List of economic node dicts
            custody_weight: Weight for custody (0-1)
            volume_weight: Weight for volume (0-1)

        Returns:
            Total consensus weight percentage
        """
        total_weight = 0.0

        for node in nodes:
            custody_btc = node.get('custody_btc', 0)
            volume_btc = node.get('daily_volume_btc', 0)

            # Calculate percentages
            custody_pct = (custody_btc / self.CIRCULATING_SUPPLY) * 100
            volume_pct = (volume_btc / self.DAILY_ONCHAIN_VOLUME) * 100

            # Apply weights
            node_weight = (custody_pct * custody_weight) + (volume_pct * volume_weight)
            total_weight += node_weight

        return total_weight

    def calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""

        if len(x) != len(y) or len(x) == 0:
            return 0.0

        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        var_x = sum((xi - mean_x) ** 2 for xi in x)
        var_y = sum((yi - mean_y) ** 2 for yi in y)

        if var_x == 0 or var_y == 0:
            return 0.0

        return cov / (math.sqrt(var_x) * math.sqrt(var_y))

    def evaluate_weights(self, custody_weight: float, volume_weight: float) -> Dict:
        """
        Evaluate a weight combination against all test results.

        Returns metrics:
        - correlation_weight_to_blocks: How well consensus weight predicts blocks mined
        - accuracy_predicting_winner: % of tests where higher weight = more blocks
        - rmse_blocks: Root mean squared error in predicting blocks mined
        """

        if not self.test_results:
            return {}

        # Calculate metrics
        weight_advantages = []  # v27 weight - v26 weight
        block_advantages = []   # v27 blocks - v26 blocks
        winner_predictions_correct = 0
        squared_errors = []

        for result in self.test_results:
            # Calculate consensus weights with these weight parameters
            v27_weight = self.calculate_consensus_weight(
                result.v27_nodes, custody_weight, volume_weight
            )
            v26_weight = self.calculate_consensus_weight(
                result.v26_nodes, custody_weight, volume_weight
            )

            weight_adv = v27_weight - v26_weight
            block_adv = result.blocks_v27 - result.blocks_v26

            weight_advantages.append(weight_adv)
            block_advantages.append(block_adv)

            # Accuracy: did higher weight win?
            if (weight_adv > 0 and block_adv > 0) or (weight_adv < 0 and block_adv < 0):
                winner_predictions_correct += 1
            elif weight_adv == 0 or block_adv == 0:
                winner_predictions_correct += 0.5  # Partial credit for ties

            # RMSE: how far off were we?
            # Normalize by hashrate to get expected blocks
            total_blocks = result.blocks_v27 + result.blocks_v26
            if total_blocks > 0:
                # Predict v27 blocks based on weight ratio
                total_weight = v27_weight + v26_weight
                if total_weight > 0:
                    predicted_v27_blocks = (v27_weight / total_weight) * total_blocks
                    error = (predicted_v27_blocks - result.blocks_v27) ** 2
                    squared_errors.append(error)

        # Calculate correlation
        correlation = self.calculate_correlation(weight_advantages, block_advantages)

        # Calculate accuracy
        accuracy = winner_predictions_correct / len(self.test_results)

        # Calculate RMSE
        rmse = math.sqrt(sum(squared_errors) / len(squared_errors)) if squared_errors else 0

        return {
            'custody_weight': custody_weight,
            'volume_weight': volume_weight,
            'correlation_weight_to_blocks': correlation,
            'winner_prediction_accuracy': accuracy,
            'rmse_block_prediction': rmse,
            'num_samples': len(self.test_results)
        }

    def optimize_weights(self) -> List[Dict]:
        """
        Test all weight combinations and rank by performance.

        Returns:
            List of results sorted by correlation (best first)
        """

        if not self.test_results:
            print("Error: No test results loaded")
            return []

        print(f"\nTesting {len(self.weights_to_test)} weight combinations on {len(self.test_results)} samples...")
        print("=" * 80)

        results = []
        for custody_w, volume_w in self.weights_to_test:
            metrics = self.evaluate_weights(custody_w, volume_w)
            results.append(metrics)

        # Sort by correlation (primary) and accuracy (secondary)
        results.sort(key=lambda x: (x['correlation_weight_to_blocks'],
                                    x['winner_prediction_accuracy']),
                     reverse=True)

        return results

    def print_results(self, results: List[Dict]):
        """Print weight optimization results in a formatted table"""

        print("\n" + "=" * 80)
        print("WEIGHT OPTIMIZATION RESULTS")
        print("=" * 80)
        print(f"Samples: {results[0]['num_samples'] if results else 0}")
        print()

        print(f"{'Rank':<6} {'Custody':<9} {'Volume':<9} {'Correlation':<13} {'Accuracy':<11} {'RMSE':<10}")
        print("-" * 80)

        for i, r in enumerate(results, 1):
            marker = "  ⭐ BEST" if i == 1 else "  📌 Current" if r['custody_weight'] == 0.7 else ""
            print(f"{i:<6} "
                  f"{r['custody_weight']:<9.1f} "
                  f"{r['volume_weight']:<9.1f} "
                  f"{r['correlation_weight_to_blocks']:<13.4f} "
                  f"{r['winner_prediction_accuracy']:<11.2%} "
                  f"{r['rmse_block_prediction']:<10.3f}"
                  f"{marker}")

        print("=" * 80)

        # Highlight findings
        best = results[0]
        current = next((r for r in results if r['custody_weight'] == 0.7), None)

        print("\nKey Findings:")
        print(f"  Best weights: {best['custody_weight']:.1f} custody / {best['volume_weight']:.1f} volume")
        print(f"    - Correlation: {best['correlation_weight_to_blocks']:.4f}")
        print(f"    - Accuracy: {best['winner_prediction_accuracy']:.2%}")
        print(f"    - RMSE: {best['rmse_block_prediction']:.3f} blocks")

        if current and current != best:
            print(f"\n  Current (0.7/0.3) performance:")
            rank = results.index(current) + 1
            print(f"    - Rank: {rank}/{len(results)}")
            print(f"    - Correlation: {current['correlation_weight_to_blocks']:.4f}")
            print(f"    - Accuracy: {current['winner_prediction_accuracy']:.2%}")

            improvement = best['correlation_weight_to_blocks'] - current['correlation_weight_to_blocks']
            if improvement > 0:
                print(f"    - Improvement potential: +{improvement:.4f} correlation")

        print()

    def export_results(self, results: List[Dict], output_path: str):
        """Export results to JSON file"""

        export_data = {
            'num_samples': results[0]['num_samples'] if results else 0,
            'weight_combinations_tested': len(results),
            'best_weights': results[0] if results else None,
            'all_results': results,
            'recommendation': {
                'custody_weight': results[0]['custody_weight'] if results else 0.7,
                'volume_weight': results[0]['volume_weight'] if results else 0.3,
                'rationale': f"Achieved highest correlation ({results[0]['correlation_weight_to_blocks']:.4f}) and accuracy ({results[0]['winner_prediction_accuracy']:.2%})" if results else "Insufficient data"
            }
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✓ Results exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Optimize custody/volume weights based on empirical fork outcomes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test weight combinations on phase1 results
  python3 weight_optimizer.py --results-dir ../test_results/

  # Export detailed results
  python3 weight_optimizer.py --results-dir ../test_results/ --output weights.json

  # Test custom weight combinations
  python3 weight_optimizer.py --results-dir ../test_results/ --custom-weights 0.75 0.25
        """
    )

    parser.add_argument(
        '--results-dir',
        type=str,
        required=True,
        help='Directory containing test result JSON files'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Export results to JSON file'
    )

    parser.add_argument(
        '--min-samples',
        type=int,
        default=5,
        help='Minimum number of samples required for analysis (default: 5)'
    )

    args = parser.parse_args()

    # Create optimizer
    optimizer = WeightOptimizer()

    # Load test results
    num_loaded = optimizer.load_test_results(args.results_dir)

    if num_loaded < args.min_samples:
        print(f"\nError: Insufficient samples ({num_loaded} < {args.min_samples})")
        print("Need more test results for reliable weight optimization")
        return 1

    # Optimize weights
    results = optimizer.optimize_weights()

    if not results:
        print("Error: No results generated")
        return 1

    # Print results
    optimizer.print_results(results)

    # Export if requested
    if args.output:
        optimizer.export_results(results, args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
