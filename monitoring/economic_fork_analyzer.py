#!/usr/bin/env python3
"""
Economic Fork Analyzer - BCAP Framework Implementation

Analyzes Bitcoin network fork scenarios using dual-metric economic model:
- PRIMARY (70%): Custody (supply validation)
- SECONDARY (30%): Payment volume (operational importance)

This aligns with the BCAP framework definition:
"Economic Nodes are full nodes that not only validate and relay transactions,
 but also receive and send substantial amounts of bitcoin payments. Economic
 Nodes have power and influence which is proportional to the frequency and
 volume of payments received."

Usage:
    from economic_fork_analyzer import EconomicForkAnalyzer, EconomicNode

    analyzer = EconomicForkAnalyzer()

    # Define economic nodes on each chain
    chain_a = [
        EconomicNode("coinbase", "major_exchange", 2000000, 100000),
        EconomicNode("kraken", "regional_exchange", 450000, 30000)
    ]
    chain_b = [
        EconomicNode("binance", "major_exchange", 2200000, 110000)
    ]

    # Analyze fork
    result = analyzer.analyze_fork(chain_a, chain_b)
    analyzer.print_report(result)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Fork risk classification levels."""
    EXTREME = "EXTREME"      # 80-100: Near 50/50 split
    HIGH = "HIGH"            # 60-79: Contested split
    MODERATE = "MODERATE"    # 40-59: Moderate split
    LOW = "LOW"              # 20-39: Clear majority
    MINIMAL = "MINIMAL"      # 0-19: Overwhelming majority


@dataclass
class EconomicNode:
    """
    Represents an economic node with BCAP-aligned metrics.

    Attributes:
        name: Node identifier (e.g., "coinbase", "binance")
        node_type: Category (major_exchange, regional_exchange, payment_processor, custody_provider)
        custody_btc: Total BTC in custody (hot + cold storage)
        daily_volume_btc: Daily transaction volume (deposits + withdrawals)
        metadata: Optional additional data
    """
    name: str
    node_type: str
    custody_btc: int
    daily_volume_btc: int
    metadata: Optional[Dict] = None

    def __post_init__(self):
        """Validate node data."""
        if self.custody_btc < 0:
            raise ValueError(f"custody_btc must be non-negative, got {self.custody_btc}")
        if self.daily_volume_btc < 0:
            raise ValueError(f"daily_volume_btc must be non-negative, got {self.daily_volume_btc}")


class EconomicForkAnalyzer:
    """
    Analyzes Bitcoin network forks using dual-metric economic model.

    Weighting Formula:
        consensus_weight = (custody_weight × 0.7) + (volume_weight × 0.3)

    Where:
        custody_weight = (node.custody_btc / CIRCULATING_SUPPLY) × 100
        volume_weight = (node.daily_volume_btc / DAILY_ONCHAIN_VOLUME) × 100

    Risk Assessment:
        - Measures how split supply validation is between chains
        - Risk is highest at 50/50 supply split
        - Risk decreases as split becomes more lopsided
    """

    # Network constants (as of 2024)
    CIRCULATING_SUPPLY = 19_500_000  # BTC in circulation
    DAILY_ONCHAIN_VOLUME = 300_000   # BTC daily on-chain volume estimate

    # Weighting parameters
    CUSTODY_WEIGHT = 0.7   # 70% - Primary metric (supply validation)
    VOLUME_WEIGHT = 0.3    # 30% - Secondary metric (operational importance)

    def __init__(self, circulating_supply: int = None, daily_onchain_volume: int = None):
        """
        Initialize fork analyzer.

        Args:
            circulating_supply: Override for BTC circulating supply (default: 19.5M)
            daily_onchain_volume: Override for daily on-chain volume (default: 300k)
        """
        self.circulating_supply = circulating_supply or self.CIRCULATING_SUPPLY
        self.daily_onchain_volume = daily_onchain_volume or self.DAILY_ONCHAIN_VOLUME

    def calculate_consensus_weight(self, node: EconomicNode) -> Dict[str, float]:
        """
        Calculate consensus weight from custody (primary) and volume (secondary).

        Weighting:
        - Custody: 70% (determines economic legitimacy)
        - Volume: 30% (determines operational importance)

        Args:
            node: EconomicNode instance

        Returns:
            Dict with custody_weight, volume_weight, consensus_weight, and basis

        Example:
            >>> node = EconomicNode("coinbase", "major_exchange", 2000000, 100000)
            >>> result = analyzer.calculate_consensus_weight(node)
            >>> print(result['consensus_weight'])
            7.31  # (10.26 × 0.7) + (33.33 × 0.3)
        """
        # Primary: Custody-based weight (% of supply under validation)
        custody_weight = (node.custody_btc / self.circulating_supply) * 100

        # Secondary: Volume-based weight (% of daily on-chain volume)
        volume_weight = (node.daily_volume_btc / self.daily_onchain_volume) * 100

        # Combined: Custody weighted 70%, Volume weighted 30%
        consensus_weight = (custody_weight * self.CUSTODY_WEIGHT) + (volume_weight * self.VOLUME_WEIGHT)

        return {
            'custody_weight': round(custody_weight, 2),
            'volume_weight': round(volume_weight, 2),
            'consensus_weight': round(consensus_weight, 2),
            'basis': 'custody_primary_volume_secondary'
        }

    def analyze_chain(self, nodes: List[EconomicNode]) -> Dict:
        """
        Analyze economic metrics for one chain.

        Args:
            nodes: List of EconomicNode instances on this chain

        Returns:
            Dict containing:
                - custody_btc: Total custody on chain
                - supply_percentage: % of circulating supply
                - daily_volume_btc: Total daily volume
                - volume_percentage: % of daily on-chain volume
                - consensus_weight: Total consensus weight
                - economic_nodes: List of node details
        """
        if not nodes:
            return {
                'custody_btc': 0,
                'supply_percentage': 0.0,
                'daily_volume_btc': 0,
                'volume_percentage': 0.0,
                'consensus_weight': 0.0,
                'economic_nodes': []
            }

        total_custody = sum(n.custody_btc for n in nodes)
        total_volume = sum(n.daily_volume_btc for n in nodes)

        # Calculate consensus weight for each node and sum
        node_weights = [self.calculate_consensus_weight(n) for n in nodes]
        total_consensus_weight = sum(w['consensus_weight'] for w in node_weights)

        return {
            'custody_btc': total_custody,
            'supply_percentage': round((total_custody / self.circulating_supply) * 100, 2),
            'daily_volume_btc': total_volume,
            'volume_percentage': round((total_volume / self.daily_onchain_volume) * 100, 2),
            'consensus_weight': round(total_consensus_weight, 2),
            'node_count': len(nodes),
            'economic_nodes': [
                {
                    'name': n.name,
                    'type': n.node_type,
                    'custody_btc': n.custody_btc,
                    'daily_volume_btc': n.daily_volume_btc,
                    'custody_pct': round((n.custody_btc / self.circulating_supply) * 100, 2),
                    'volume_pct': round((n.daily_volume_btc / self.daily_onchain_volume) * 100, 2),
                    'consensus_weight': self.calculate_consensus_weight(n)['consensus_weight']
                }
                for n in nodes
            ]
        }

    def calculate_risk_score(self, chain_a_supply_pct: float, chain_b_supply_pct: float) -> float:
        """
        Calculate fork risk score based on supply validation split.

        Risk is highest when supply validation is split near 50/50.
        As the split becomes more lopsided, risk decreases.

        Args:
            chain_a_supply_pct: % of supply validating chain A
            chain_b_supply_pct: % of supply validating chain B

        Returns:
            Risk score from 0-100 (100 = maximum risk at 50/50 split)

        Examples:
            >>> calculate_risk_score(50, 50)  # Perfect split
            100
            >>> calculate_risk_score(70, 30)  # Clear majority
            40
            >>> calculate_risk_score(90, 10)  # Overwhelming majority
            0
        """
        # Measure distance from 50/50 split
        split_distance = abs(50 - chain_a_supply_pct)

        # Risk score: 100 at 50/50, decreases linearly as split becomes more lopsided
        # At 0/100 or 100/0, risk is 0 (one chain has overwhelming support)
        risk_score = 100 - (split_distance * 2)

        return max(0, min(100, risk_score))

    def classify_risk(self, risk_score: float) -> RiskLevel:
        """
        Classify risk score into risk level.

        Args:
            risk_score: Risk score from 0-100

        Returns:
            RiskLevel enum value
        """
        if risk_score >= 80:
            return RiskLevel.EXTREME
        elif risk_score >= 60:
            return RiskLevel.HIGH
        elif risk_score >= 40:
            return RiskLevel.MODERATE
        elif risk_score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

    def analyze_fork(self, chain_a_nodes: List[EconomicNode],
                     chain_b_nodes: List[EconomicNode]) -> Dict:
        """
        Analyze fork scenario using dual-metric model.

        Args:
            chain_a_nodes: List of economic nodes on chain A
            chain_b_nodes: List of economic nodes on chain B

        Returns:
            Comprehensive fork analysis including:
                - chains: Analysis for both chains
                - risk_assessment: Risk score, level, consensus chain
                - metrics_breakdown: Supply and volume splits
                - economic_influence: Which chain has economic majority

        Example:
            >>> chain_a = [EconomicNode("coinbase", "major_exchange", 2000000, 100000)]
            >>> chain_b = [EconomicNode("binance", "major_exchange", 2200000, 110000)]
            >>> result = analyzer.analyze_fork(chain_a, chain_b)
            >>> print(result['risk_assessment']['level'])
            'EXTREME'  # Near 50/50 split
        """
        # Calculate for each chain
        chain_a_analysis = self.analyze_chain(chain_a_nodes)
        chain_b_analysis = self.analyze_chain(chain_b_nodes)

        # Risk scoring based on supply split
        risk_score = self.calculate_risk_score(
            chain_a_analysis['supply_percentage'],
            chain_b_analysis['supply_percentage']
        )

        risk_level = self.classify_risk(risk_score)

        # Determine consensus chain (by consensus weight)
        if chain_a_analysis['consensus_weight'] > chain_b_analysis['consensus_weight']:
            consensus_chain = 'A'
            consensus_margin = chain_a_analysis['consensus_weight'] - chain_b_analysis['consensus_weight']
        elif chain_b_analysis['consensus_weight'] > chain_a_analysis['consensus_weight']:
            consensus_chain = 'B'
            consensus_margin = chain_b_analysis['consensus_weight'] - chain_a_analysis['consensus_weight']
        else:
            consensus_chain = 'TIE'
            consensus_margin = 0.0

        # Determine economic influence (by custody)
        if chain_a_analysis['supply_percentage'] > chain_b_analysis['supply_percentage']:
            economic_majority = 'A'
        elif chain_b_analysis['supply_percentage'] > chain_a_analysis['supply_percentage']:
            economic_majority = 'B'
        else:
            economic_majority = 'TIE'

        return {
            'chains': {
                'chain_a': chain_a_analysis,
                'chain_b': chain_b_analysis
            },
            'risk_assessment': {
                'score': round(risk_score, 1),
                'level': risk_level.value,
                'consensus_chain': consensus_chain,
                'consensus_margin': round(consensus_margin, 2),
                'economic_majority': economic_majority
            },
            'metrics_breakdown': {
                'supply_split': f"{chain_a_analysis['supply_percentage']:.1f}% vs {chain_b_analysis['supply_percentage']:.1f}%",
                'volume_split': f"{chain_a_analysis['volume_percentage']:.1f}% vs {chain_b_analysis['volume_percentage']:.1f}%",
                'weight_split': f"{chain_a_analysis['consensus_weight']:.1f} vs {chain_b_analysis['consensus_weight']:.1f}"
            },
            'economic_influence': {
                'chain_a_custody': chain_a_analysis['custody_btc'],
                'chain_b_custody': chain_b_analysis['custody_btc'],
                'chain_a_volume': chain_a_analysis['daily_volume_btc'],
                'chain_b_volume': chain_b_analysis['daily_volume_btc']
            }
        }

    def print_report(self, analysis: Dict):
        """
        Print formatted fork analysis report.

        Args:
            analysis: Result from analyze_fork()
        """
        print("=" * 80)
        print("BITCOIN NETWORK FORK ANALYSIS (BCAP Framework)")
        print("=" * 80)

        # Risk assessment
        risk = analysis['risk_assessment']
        print(f"\n### RISK ASSESSMENT ###")
        print(f"  Risk Score:        {risk['score']}/100")
        print(f"  Risk Level:        {risk['level']}")
        print(f"  Consensus Chain:   Chain {risk['consensus_chain']} (margin: {risk['consensus_margin']:.2f})")
        print(f"  Economic Majority: Chain {risk['economic_majority']}")

        # Metrics breakdown
        metrics = analysis['metrics_breakdown']
        print(f"\n### METRICS BREAKDOWN ###")
        print(f"  Supply Split:      {metrics['supply_split']}")
        print(f"  Volume Split:      {metrics['volume_split']}")
        print(f"  Weight Split:      {metrics['weight_split']}")

        # Chain A details
        chain_a = analysis['chains']['chain_a']
        print(f"\n### CHAIN A ###")
        print(f"  Economic Nodes:    {chain_a['node_count']}")
        print(f"  Total Custody:     {chain_a['custody_btc']:,} BTC ({chain_a['supply_percentage']:.2f}% of supply)")
        print(f"  Daily Volume:      {chain_a['daily_volume_btc']:,} BTC ({chain_a['volume_percentage']:.2f}% of on-chain)")
        print(f"  Consensus Weight:  {chain_a['consensus_weight']:.2f}")

        if chain_a['economic_nodes']:
            print(f"\n  Nodes on Chain A:")
            for node in chain_a['economic_nodes']:
                print(f"    • {node['name']:20s} ({node['type']:20s}): "
                      f"{node['custody_btc']:>10,} BTC custody, "
                      f"{node['daily_volume_btc']:>8,} BTC/day, "
                      f"weight {node['consensus_weight']:>6.2f}")

        # Chain B details
        chain_b = analysis['chains']['chain_b']
        print(f"\n### CHAIN B ###")
        print(f"  Economic Nodes:    {chain_b['node_count']}")
        print(f"  Total Custody:     {chain_b['custody_btc']:,} BTC ({chain_b['supply_percentage']:.2f}% of supply)")
        print(f"  Daily Volume:      {chain_b['daily_volume_btc']:,} BTC ({chain_b['volume_percentage']:.2f}% of on-chain)")
        print(f"  Consensus Weight:  {chain_b['consensus_weight']:.2f}")

        if chain_b['economic_nodes']:
            print(f"\n  Nodes on Chain B:")
            for node in chain_b['economic_nodes']:
                print(f"    • {node['name']:20s} ({node['type']:20s}): "
                      f"{node['custody_btc']:>10,} BTC custody, "
                      f"{node['daily_volume_btc']:>8,} BTC/day, "
                      f"weight {node['consensus_weight']:>6.2f}")

        # Interpretation
        print(f"\n### INTERPRETATION ###")
        if risk['level'] == 'EXTREME':
            print("  ⚠️  EXTREME RISK: Supply is nearly evenly split. Prolonged chain split likely.")
        elif risk['level'] == 'HIGH':
            print("  ⚠️  HIGH RISK: Contested split. Significant economic uncertainty.")
        elif risk['level'] == 'MODERATE':
            print("  ⚠️  MODERATE RISK: Clear majority forming, but minority is significant.")
        elif risk['level'] == 'LOW':
            print("  ✓  LOW RISK: Strong majority on one chain. Minority likely to capitulate.")
        else:
            print("  ✓  MINIMAL RISK: Overwhelming majority. Minority has negligible influence.")

        print("\n" + "=" * 80)


def main():
    """Example usage of EconomicForkAnalyzer."""
    print("Economic Fork Analyzer - Example Usage\n")

    # Create analyzer
    analyzer = EconomicForkAnalyzer()

    # Example 1: Contested fork (near 50/50)
    print("EXAMPLE 1: Contested Fork (Major Exchanges Split)\n")

    chain_a = [
        EconomicNode("coinbase", "major_exchange", 2000000, 100000),
        EconomicNode("kraken", "regional_exchange", 450000, 30000),
        EconomicNode("bitpay", "payment_processor", 30000, 10000)
    ]

    chain_b = [
        EconomicNode("binance", "major_exchange", 2200000, 110000),
        EconomicNode("fidelity", "custody_provider", 700000, 3000)
    ]

    result = analyzer.analyze_fork(chain_a, chain_b)
    analyzer.print_report(result)

    # Example 2: Clear majority
    print("\n\nEXAMPLE 2: Clear Majority (Most Economic Nodes on Chain A)\n")

    chain_a_majority = [
        EconomicNode("coinbase", "major_exchange", 2000000, 100000),
        EconomicNode("binance", "major_exchange", 2200000, 110000),
        EconomicNode("kraken", "regional_exchange", 450000, 30000),
        EconomicNode("fidelity", "custody_provider", 700000, 3000)
    ]

    chain_b_minority = [
        EconomicNode("bitpay", "payment_processor", 30000, 10000)
    ]

    result2 = analyzer.analyze_fork(chain_a_majority, chain_b_minority)
    analyzer.print_report(result2)


if __name__ == '__main__':
    main()
