#!/usr/bin/env python3
"""
Market Dynamics Analyzer

Validates that:
1. Markets are forming (prices/fees evolving)
2. Pools make decisions based on dynamic market conditions
3. Pool reallocations correlate with market changes

Usage:
    python3 analyze_market_dynamics.py \
        --pool-decisions results/test-001-pool-decisions.json \
        --price-history results/test-001-price-history.json \
        --output results/test-001-market-analysis.txt
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


def load_json(filepath: str) -> dict:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_price_evolution(price_history: dict) -> dict:
    """
    Analyze price evolution over time.

    Returns:
        {
            'total_updates': int,
            'v27_start': float,
            'v27_end': float,
            'v27_change_pct': float,
            'v26_start': float,
            'v26_end': float,
            'v26_change_pct': float,
            'price_volatility': float,
            'market_forming': bool
        }
    """
    history = price_history.get('history', [])

    if len(history) < 2:
        return {
            'total_updates': len(history),
            'market_forming': False,
            'error': 'Insufficient price history'
        }

    first = history[0]
    last = history[-1]

    v27_start = first['v27_price']
    v27_end = last['v27_price']
    v26_start = first['v26_price']
    v26_end = last['v26_price']

    v27_change_pct = ((v27_end - v27_start) / v27_start) * 100 if v27_start > 0 else 0
    v26_change_pct = ((v26_end - v26_start) / v26_start) * 100 if v26_start > 0 else 0

    # Calculate volatility (max price swing)
    v27_prices = [h['v27_price'] for h in history]
    v26_prices = [h['v26_price'] for h in history]

    v27_volatility = (max(v27_prices) - min(v27_prices)) / v27_start * 100 if v27_start > 0 else 0
    v26_volatility = (max(v26_prices) - min(v26_prices)) / v26_start * 100 if v26_start > 0 else 0

    # Market is forming if prices changed by more than 1%
    market_forming = abs(v27_change_pct) > 1.0 or abs(v26_change_pct) > 1.0

    return {
        'total_updates': len(history),
        'v27_start': v27_start,
        'v27_end': v27_end,
        'v27_change_pct': v27_change_pct,
        'v27_volatility': v27_volatility,
        'v26_start': v26_start,
        'v26_end': v26_end,
        'v26_change_pct': v26_change_pct,
        'v26_volatility': v26_volatility,
        'market_forming': market_forming,
        'duration_seconds': last['timestamp'] - first['timestamp']
    }


def analyze_pool_decisions(pool_decisions: dict) -> dict:
    """
    Analyze pool decision patterns.

    Returns:
        {
            'total_pools': int,
            'decisions_tracked': int,
            'pools_switched': list,
            'v27_pools': list,
            'v26_pools': list,
            'v27_hashrate': float,
            'v26_hashrate': float,
            'ideology_active': bool,
            'profitability_driven': bool
        }
    """
    pools = pool_decisions.get('pools', {})

    total_pools = len(pools)
    v27_pools = []
    v26_pools = []
    pools_switched = []
    ideology_pools = []

    v27_hashrate = 0.0
    v26_hashrate = 0.0

    for pool_name, pool_data in pools.items():
        current_allocation = pool_data.get('current_allocation', 'unknown')
        profile = pool_data.get('profile', {})
        hashrate = profile.get('hashrate_pct', 0.0)
        ideology = profile.get('ideology', {})

        if current_allocation == 'v27':
            v27_pools.append(pool_name)
            v27_hashrate += hashrate
        elif current_allocation == 'v26':
            v26_pools.append(pool_name)
            v26_hashrate += hashrate

        # Check for switches
        decision_history = pool_data.get('decision_history', [])
        if len(decision_history) > 1:
            allocations = [d['allocation'] for d in decision_history]
            if len(set(allocations)) > 1:
                pools_switched.append({
                    'pool': pool_name,
                    'switches': len(set(allocations)) - 1,
                    'hashrate': hashrate
                })

        # Check for ideological behavior
        if ideology.get('strength', 0.0) > 0.0:
            ideology_pools.append(pool_name)

    # Profitability driven if pools switched based on price changes
    profitability_driven = len(pools_switched) > 0

    # Ideology active if ideological pools exist
    ideology_active = len(ideology_pools) > 0

    return {
        'total_pools': total_pools,
        'decisions_tracked': sum(len(p.get('decision_history', [])) for p in pools.values()),
        'pools_switched': pools_switched,
        'v27_pools': v27_pools,
        'v26_pools': v26_pools,
        'v27_hashrate': round(v27_hashrate, 2),
        'v26_hashrate': round(v26_hashrate, 2),
        'ideology_active': ideology_active,
        'ideology_pools': ideology_pools,
        'profitability_driven': profitability_driven
    }


def correlate_decisions_with_prices(pool_decisions: dict, price_history: dict) -> dict:
    """
    Check if pool decisions correlate with price changes.

    Returns:
        {
            'correlation_found': bool,
            'evidence': list of examples
        }
    """
    pools = pool_decisions.get('pools', {})
    price_hist = price_history.get('history', [])

    evidence = []

    # Look for pools that switched when prices changed
    for pool_name, pool_data in pools.items():
        decision_history = pool_data.get('decision_history', [])

        if len(decision_history) < 2:
            continue

        for i in range(1, len(decision_history)):
            prev_decision = decision_history[i-1]
            curr_decision = decision_history[i]

            # Did allocation change?
            if prev_decision['allocation'] != curr_decision['allocation']:
                timestamp = curr_decision['timestamp']

                # Find closest price data
                closest_price = None
                min_time_diff = float('inf')
                for price_point in price_hist:
                    time_diff = abs(price_point['timestamp'] - timestamp)
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_price = price_point

                if closest_price:
                    # Check if price ratio favored the new allocation
                    v27_price = closest_price['v27_price']
                    v26_price = closest_price['v26_price']

                    more_profitable = 'v27' if v27_price > v26_price else 'v26'
                    switched_to = curr_decision['allocation']

                    market_driven = (more_profitable == switched_to)

                    evidence.append({
                        'pool': pool_name,
                        'timestamp': timestamp,
                        'switched_from': prev_decision['allocation'],
                        'switched_to': switched_to,
                        'v27_price': v27_price,
                        'v26_price': v26_price,
                        'more_profitable': more_profitable,
                        'market_driven': market_driven,
                        'reason': curr_decision.get('reason', 'unknown')
                    })

    correlation_found = any(e['market_driven'] for e in evidence)

    return {
        'correlation_found': correlation_found,
        'total_switches': len(evidence),
        'market_driven_switches': sum(1 for e in evidence if e['market_driven']),
        'evidence': evidence
    }


def generate_report(price_analysis: dict, pool_analysis: dict, correlation: dict) -> str:
    """Generate human-readable report."""

    lines = []
    lines.append("=" * 80)
    lines.append("MARKET DYNAMICS ANALYSIS")
    lines.append("=" * 80)
    lines.append("")

    # Price Evolution
    lines.append("1. PRICE EVOLUTION")
    lines.append("-" * 80)

    if price_analysis.get('market_forming'):
        lines.append("✓ Markets are FORMING - prices evolved over time")
    else:
        lines.append("✗ Markets NOT forming - prices static")

    lines.append("")
    lines.append(f"  Total price updates:  {price_analysis.get('total_updates', 0)}")
    lines.append(f"  Duration:             {price_analysis.get('duration_seconds', 0)} seconds")
    lines.append("")
    lines.append("  v27 Fork:")
    lines.append(f"    Start price:        ${price_analysis.get('v27_start', 0):,.2f}")
    lines.append(f"    End price:          ${price_analysis.get('v27_end', 0):,.2f}")
    lines.append(f"    Change:             {price_analysis.get('v27_change_pct', 0):+.2f}%")
    lines.append(f"    Volatility:         {price_analysis.get('v27_volatility', 0):.2f}%")
    lines.append("")
    lines.append("  v26 Fork:")
    lines.append(f"    Start price:        ${price_analysis.get('v26_start', 0):,.2f}")
    lines.append(f"    End price:          ${price_analysis.get('v26_end', 0):,.2f}")
    lines.append(f"    Change:             {price_analysis.get('v26_change_pct', 0):+.2f}%")
    lines.append(f"    Volatility:         {price_analysis.get('v26_volatility', 0):.2f}%")
    lines.append("")

    # Pool Decisions
    lines.append("2. POOL DECISION-MAKING")
    lines.append("-" * 80)

    if pool_analysis.get('profitability_driven'):
        lines.append("✓ Pools ARE making dynamic decisions - reallocations detected")
    else:
        lines.append("✗ Pools NOT making dynamic decisions - no reallocations")

    lines.append("")
    lines.append(f"  Total pools:          {pool_analysis.get('total_pools', 0)}")
    lines.append(f"  Decisions tracked:    {pool_analysis.get('decisions_tracked', 0)}")
    lines.append(f"  Pools that switched:  {len(pool_analysis.get('pools_switched', []))}")
    lines.append("")
    lines.append("  Current allocation:")
    lines.append(f"    v27: {pool_analysis.get('v27_hashrate', 0):.1f}% hashrate ({len(pool_analysis.get('v27_pools', []))} pools)")
    lines.append(f"    v26: {pool_analysis.get('v26_hashrate', 0):.1f}% hashrate ({len(pool_analysis.get('v26_pools', []))} pools)")
    lines.append("")

    if pool_analysis.get('pools_switched'):
        lines.append("  Pool switches:")
        for switch in pool_analysis['pools_switched'][:5]:  # Top 5
            lines.append(f"    - {switch['pool']}: {switch['switches']} switch(es) (hashrate: {switch['hashrate']:.1f}%)")

    if pool_analysis.get('ideology_active'):
        lines.append("")
        lines.append(f"  Ideological pools:    {len(pool_analysis.get('ideology_pools', []))} pools")
        for pool in pool_analysis.get('ideology_pools', [])[:5]:
            lines.append(f"    - {pool}")

    lines.append("")

    # Market-Driven Decisions
    lines.append("3. MARKET-DRIVEN BEHAVIOR")
    lines.append("-" * 80)

    if correlation.get('correlation_found'):
        lines.append("✓ Pool decisions CORRELATED with market conditions")
    else:
        lines.append("✗ No clear correlation between decisions and markets")

    lines.append("")
    lines.append(f"  Total switches:       {correlation.get('total_switches', 0)}")
    lines.append(f"  Market-driven:        {correlation.get('market_driven_switches', 0)}")

    if correlation.get('market_driven_switches', 0) > 0:
        pct = (correlation['market_driven_switches'] / correlation['total_switches']) * 100
        lines.append(f"  Market-driven rate:   {pct:.1f}%")

    lines.append("")

    if correlation.get('evidence'):
        lines.append("  Examples of market-driven decisions:")
        lines.append("")

        for i, ev in enumerate(correlation['evidence'][:5], 1):  # Top 5 examples
            lines.append(f"  Example {i}: {ev['pool']}")
            lines.append(f"    Time:        {ev['timestamp']}s")
            lines.append(f"    Switched:    {ev['switched_from']} → {ev['switched_to']}")
            lines.append(f"    Prices:      v27=${ev['v27_price']:,.2f}, v26=${ev['v26_price']:,.2f}")
            lines.append(f"    Profitable:  {ev['more_profitable']}")
            lines.append(f"    Market-driven: {'✓ YES' if ev['market_driven'] else '✗ NO (ideology?)'}")
            lines.append(f"    Reason:      {ev['reason']}")
            lines.append("")

    lines.append("=" * 80)
    lines.append("VALIDATION SUMMARY")
    lines.append("=" * 80)
    lines.append("")

    # Overall assessment
    markets_working = price_analysis.get('market_forming', False)
    decisions_working = pool_analysis.get('profitability_driven', False)
    correlation_working = correlation.get('correlation_found', False)

    lines.append(f"Markets forming:             {'✓ YES' if markets_working else '✗ NO'}")
    lines.append(f"Pools making decisions:      {'✓ YES' if decisions_working else '✗ NO'}")
    lines.append(f"Decisions market-driven:     {'✓ YES' if correlation_working else '✗ NO'}")
    lines.append("")

    if markets_working and decisions_working and correlation_working:
        lines.append("🎉 SUCCESS: All systems operational!")
        lines.append("   - Markets are evolving dynamically")
        lines.append("   - Pools are responding to market signals")
        lines.append("   - Economic incentives are working as designed")
    elif markets_working and decisions_working:
        lines.append("⚠️  PARTIAL: Markets and decisions working, correlation unclear")
        lines.append("   - May need longer test duration")
        lines.append("   - Ideology may be dominating profitability")
    elif markets_working:
        lines.append("⚠️  WARNING: Markets working but pools not responding")
        lines.append("   - Check pool decision logic")
        lines.append("   - Verify profitability calculations")
    else:
        lines.append("❌ ISSUE: Markets not forming properly")
        lines.append("   - Check price oracle configuration")
        lines.append("   - Verify economic weight settings")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Analyze market dynamics and pool decisions')
    parser.add_argument('--pool-decisions', required=True, help='Path to pool decisions JSON')
    parser.add_argument('--price-history', required=True, help='Path to price history JSON')
    parser.add_argument('--output', help='Output file for report (default: stdout)')

    args = parser.parse_args()

    # Load data
    print("Loading data...")
    pool_decisions = load_json(args.pool_decisions)
    price_history = load_json(args.price_history)

    # Analyze
    print("Analyzing price evolution...")
    price_analysis = analyze_price_evolution(price_history)

    print("Analyzing pool decisions...")
    pool_analysis = analyze_pool_decisions(pool_decisions)

    print("Correlating decisions with prices...")
    correlation = correlate_decisions_with_prices(pool_decisions, price_history)

    # Generate report
    print("Generating report...")
    report = generate_report(price_analysis, pool_analysis, correlation)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\n✓ Report saved to: {args.output}")

    print("\n" + report)


if __name__ == '__main__':
    main()
