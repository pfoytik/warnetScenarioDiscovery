#!/usr/bin/env python3

"""
Economic Node Strategy - Dynamic Fork Choice for All Non-Mining Nodes

Models realistic economic actor behavior with dual motivations:
1. Rational Economics - follow the higher-priced fork token
2. Ideology/Preference - support preferred fork even at economic cost
3. Inertia - resist switching due to infrastructure/switching costs

Economic actors "vote with their feet" by choosing which fork's economy
to participate in. Their aggregate choices determine the dynamic
v27_economic_pct that feeds into the price oracle.

This creates a feedback loop:
    Price changes -> Node decisions -> Economic weight shifts -> Price changes
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class NodeType(Enum):
    """Type of economic actor"""
    ECONOMIC = "economic"   # Exchanges, payment processors (high weight)
    USER = "user"           # Individual users / small operators (low weight)


class ActivityType(Enum):
    """
    Activity type determines fee generation behavior.

    Transactional nodes generate transaction fees through active use.
    Custodial nodes hold value but don't generate significant fees.
    """
    TRANSACTIONAL = "transactional"  # Exchanges, merchants, payment processors - high tx volume
    CUSTODIAL = "custodial"          # HODLers, cold storage, treasuries - low tx volume
    MIXED = "mixed"                  # Some of both


class ForkPreference(Enum):
    """Fork preference for economic actors"""
    V27 = "v27"
    V26 = "v26"
    NEUTRAL = "neutral"


@dataclass
class EconomicNodeProfile:
    """
    Profile for an economic or user node with ideology characteristics.

    Attributes:
        node_id: Unique identifier (e.g., "econ-0000", "user-0005")
        node_type: ECONOMIC or USER
        activity_type: TRANSACTIONAL, CUSTODIAL, or MIXED (affects fee generation)
        transaction_velocity: Fee generation multiplier (0.0 = pure custody, 1.0 = high volume)
        fork_preference: Which fork they prefer (v27, v26, or neutral)
        ideology_strength: How much they'll sacrifice for ideology (0.0-1.0)
        switching_threshold: Min price advantage to switch forks (0.0-1.0)
        custody_btc: BTC holdings (determines economic weight for price support)
        daily_volume_btc: Daily transaction volume (determines fee contribution)
        consensus_weight: Pre-computed economic influence weight
        switching_cooldown: Seconds between allowed switches
        max_loss_pct: Max acceptable price disadvantage for ideology (0.0-1.0)
        inertia: Resistance to switching (0.0 = none, 1.0 = maximum)
        role: Optional role descriptor (e.g., "major_exchange")
        initial_fork: Which partition this node starts on (v27 or v26)

    Economic Weight vs Transaction Velocity:
        - consensus_weight: Influences price (all holdings matter for market cap)
        - transaction_velocity: Influences fees (only active transactions generate fees)

        Example scenarios:
        - Exchange: high custody + high velocity = strong price support + high fees
        - HODLer whale: high custody + low velocity = strong price support + minimal fees
        - Active trader: low custody + high velocity = weak price support + high fees

    Solo Mining:
        - hashrate_pct: If > 0, this node is a solo miner
        - Solo miners follow their economic fork decision for mining
        - Highly ideological solo miners will mine losing fork stubbornly
    """
    node_id: str
    node_type: NodeType
    activity_type: ActivityType = ActivityType.MIXED
    transaction_velocity: float = 0.5  # 0.0 = pure custody, 1.0 = high volume
    fork_preference: ForkPreference = ForkPreference.NEUTRAL
    ideology_strength: float = 0.0
    switching_threshold: float = 0.05
    custody_btc: float = 0.0
    daily_volume_btc: float = 0.0
    consensus_weight: float = 0.0
    hashrate_pct: float = 0.0  # Solo mining hashrate (0.0 = non-miner)
    switching_cooldown: float = 1800.0  # 30 minutes default
    max_loss_pct: float = 0.10
    inertia: float = 0.10
    role: Optional[str] = None
    initial_fork: str = "v27"


@dataclass
class EconomicDecision:
    """
    Record of an economic node's fork choice at a point in time.
    """
    timestamp: float
    node_id: str
    node_type: str
    chosen_fork: str
    v27_price_usd: float
    v26_price_usd: float
    price_ratio: float           # v27/v26
    rational_choice: str         # Which fork has higher price
    ideology_override: bool      # True if staying on preferred fork despite lower price
    inertia_held: bool           # True if stayed due to inertia
    economic_weight: float       # This node's consensus weight
    reason: str                  # Human-readable explanation


class EconomicNodeStrategy:
    """
    Manages economic and user node fork choices.

    Each node independently decides which fork to support based on:
    1. Price advantage (rational: follow the more valuable token)
    2. Fork preference (ideology: support preferred fork at some cost)
    3. Inertia (switching costs: stay on current fork unless advantage is large)
    """

    def __init__(self, nodes: List[EconomicNodeProfile]):
        """
        Initialize with node profiles.

        Args:
            nodes: List of economic/user node profiles
        """
        self.nodes = {n.node_id: n for n in nodes}

        # Current fork allocation per node
        self.current_allocation: Dict[str, Optional[str]] = {}
        for n in nodes:
            self.current_allocation[n.node_id] = n.initial_fork

        # Decision history
        self.decision_history: List[EconomicDecision] = []

        # Last decision time per node (for cooldown)
        self.last_decision_time: Dict[str, float] = {n.node_id: 0.0 for n in nodes}

        # Tracking per node
        self.node_stats: Dict[str, Dict] = {
            n.node_id: {
                'switches': 0,
                'ideology_overrides': 0,
                'inertia_holds': 0,
            }
            for n in nodes
        }

    def _node_weight(self, node: 'EconomicNodeProfile') -> float:
        """
        Return the effective economic weight for a node.

        Uses consensus_weight when set; falls back to custody_btc for networks
        (e.g. realistic-economy-v2) that omit the pre-computed consensus_weight
        field and only carry raw custody_btc in node metadata.
        """
        return node.consensus_weight if node.consensus_weight > 0 else node.custody_btc

    def make_decision(
        self,
        node_id: str,
        current_time: float,
        price_oracle,
        force_decision: bool = False
    ) -> Tuple[str, Optional[EconomicDecision]]:
        """
        Node decides which fork to participate in.

        Decision pipeline:
        1. Check cooldown
        2. Get prices for both forks
        3. Determine rational choice (higher-priced fork)
        4. Apply ideology override if applicable
        5. Apply inertia (resist switching unless advantage exceeds threshold)

        Args:
            node_id: Which node is deciding
            current_time: Current timestamp
            price_oracle: PriceOracle instance for current prices
            force_decision: Ignore cooldown

        Returns:
            Tuple of (chosen_fork, decision_record or None if cooldown)
        """
        node = self.nodes[node_id]

        # Check cooldown
        if not force_decision:
            time_since_last = current_time - self.last_decision_time[node_id]
            if time_since_last < node.switching_cooldown:
                current = self.current_allocation[node_id]
                if current is None:
                    # First decision: use initial fork
                    current = node.initial_fork
                    self.current_allocation[node_id] = current
                return current, None

        # Get current prices
        v27_price = price_oracle.get_price('v27')
        v26_price = price_oracle.get_price('v26')
        price_ratio = v27_price / v26_price if v26_price > 0 else 1.0

        # Determine rational choice (higher-priced fork = more valuable economy)
        if v27_price >= v26_price:
            rational_choice = 'v27'
            price_advantage = (v27_price - v26_price) / v26_price if v26_price > 0 else 0.0
        else:
            rational_choice = 'v26'
            price_advantage = (v26_price - v27_price) / v27_price if v27_price > 0 else 0.0

        chosen_fork = rational_choice
        ideology_override = False
        inertia_held = False
        reason = "Rational: following higher-priced fork"

        # Apply ideology if node has preference
        if node.fork_preference != ForkPreference.NEUTRAL:
            preferred = node.fork_preference.value

            if preferred != rational_choice:
                # Preferred fork has lower price -- is ideology strong enough?
                max_acceptable_loss = node.ideology_strength * node.max_loss_pct

                if price_advantage <= max_acceptable_loss:
                    # Ideology wins: stay on preferred fork
                    chosen_fork = preferred
                    ideology_override = True
                    self.node_stats[node_id]['ideology_overrides'] += 1
                    reason = (f"Ideology: supporting {preferred} despite "
                              f"{price_advantage*100:.1f}% lower price "
                              f"(tolerance: {max_acceptable_loss*100:.1f}%)")
                else:
                    reason = (f"Forced rational: {price_advantage*100:.1f}% advantage "
                              f"exceeds ideology tolerance {max_acceptable_loss*100:.1f}%")
            else:
                # Preferred fork IS the rational choice
                reason = "Ideology and price aligned"

        # Apply inertia: resist switching unless advantage exceeds threshold + inertia
        current = self.current_allocation[node_id]
        if current is not None and chosen_fork != current:
            effective_threshold = node.switching_threshold + node.inertia
            if price_advantage < effective_threshold:
                # Inertia wins: stay on current fork
                chosen_fork = current
                inertia_held = True
                self.node_stats[node_id]['inertia_holds'] += 1
                reason = (f"Inertia: staying on {current} "
                          f"(advantage {price_advantage*100:.1f}% "
                          f"< threshold {effective_threshold*100:.1f}%)")

        # Track switches
        if current is not None and chosen_fork != current:
            self.node_stats[node_id]['switches'] += 1

        # Record decision
        decision = EconomicDecision(
            timestamp=current_time,
            node_id=node_id,
            node_type=node.node_type.value,
            chosen_fork=chosen_fork,
            v27_price_usd=v27_price,
            v26_price_usd=v26_price,
            price_ratio=price_ratio,
            rational_choice=rational_choice,
            ideology_override=ideology_override,
            inertia_held=inertia_held,
            economic_weight=node.consensus_weight,
            reason=reason
        )

        self.decision_history.append(decision)
        self.current_allocation[node_id] = chosen_fork
        self.last_decision_time[node_id] = current_time

        return chosen_fork, decision

    def calculate_economic_allocation(
        self,
        current_time: float,
        price_oracle
    ) -> Tuple[float, float]:
        """
        Calculate aggregate economic weight on each fork.

        Each node's consensus_weight contributes to the fork it has chosen.
        Returns percentages (0-100) for use in price_oracle.update_prices_from_state().

        Returns:
            Tuple of (v27_economic_pct, v26_economic_pct)
        """
        v27_weight = 0.0
        v26_weight = 0.0

        for node_id, node in self.nodes.items():
            chosen_fork, decision = self.make_decision(
                node_id, current_time, price_oracle
            )

            if chosen_fork == 'v27':
                v27_weight += self._node_weight(node)
            else:
                v26_weight += self._node_weight(node)

        total_weight = v27_weight + v26_weight
        if total_weight > 0:
            v27_pct = (v27_weight / total_weight) * 100.0
            v26_pct = (v26_weight / total_weight) * 100.0
        else:
            v27_pct = 50.0
            v26_pct = 50.0

        return v27_pct, v26_pct

    def get_allocation_breakdown(self) -> Dict:
        """Get detailed breakdown of current allocation by node type."""
        breakdown = {
            'economic': {'v27_weight': 0.0, 'v26_weight': 0.0, 'v27_count': 0, 'v26_count': 0},
            'user': {'v27_weight': 0.0, 'v26_weight': 0.0, 'v27_count': 0, 'v26_count': 0},
        }

        for node_id, node in self.nodes.items():
            fork = self.current_allocation[node_id]
            ntype = node.node_type.value

            if ntype not in breakdown:
                continue

            if fork == 'v27':
                breakdown[ntype]['v27_weight'] += self._node_weight(node)
                breakdown[ntype]['v27_count'] += 1
            else:
                breakdown[ntype]['v26_weight'] += self._node_weight(node)
                breakdown[ntype]['v26_count'] += 1

        return breakdown

    def calculate_transactional_weight(self) -> Tuple[float, float, float, float]:
        """
        Calculate transactional vs custodial economic weight on each fork.

        Returns breakdown of economic activity by type:
        - Transactional weight: Generates fees (exchanges, merchants, active users)
        - Custodial weight: Price support only (HODLers, cold storage)

        Returns:
            Tuple of (v27_transactional_pct, v26_transactional_pct,
                      v27_custodial_pct, v26_custodial_pct)

            Transactional pct is the portion of economic activity that generates fees.
            Custodial pct is the portion that only provides price support.
        """
        v27_transactional = 0.0
        v27_custodial = 0.0
        v26_transactional = 0.0
        v26_custodial = 0.0

        for node_id, node in self.nodes.items():
            fork = self.current_allocation[node_id]
            weight = self._node_weight(node)
            velocity = node.transaction_velocity

            # Split weight between transactional and custodial based on velocity
            transactional_portion = weight * velocity
            custodial_portion = weight * (1.0 - velocity)

            if fork == 'v27':
                v27_transactional += transactional_portion
                v27_custodial += custodial_portion
            else:
                v26_transactional += transactional_portion
                v26_custodial += custodial_portion

        # Convert to percentages
        total_transactional = v27_transactional + v26_transactional
        total_custodial = v27_custodial + v26_custodial

        if total_transactional > 0:
            v27_trans_pct = (v27_transactional / total_transactional) * 100.0
            v26_trans_pct = (v26_transactional / total_transactional) * 100.0
        else:
            v27_trans_pct = 50.0
            v26_trans_pct = 50.0

        if total_custodial > 0:
            v27_cust_pct = (v27_custodial / total_custodial) * 100.0
            v26_cust_pct = (v26_custodial / total_custodial) * 100.0
        else:
            v27_cust_pct = 50.0
            v26_cust_pct = 50.0

        return v27_trans_pct, v26_trans_pct, v27_cust_pct, v26_cust_pct

    def get_fee_generation_weight(self) -> Tuple[float, float]:
        """
        Get the fee-generating economic weight for each fork.

        This is the portion of economic activity that generates transaction fees,
        weighted by transaction_velocity. Use this for fee oracle calculations.

        Returns:
            Tuple of (v27_fee_weight_pct, v26_fee_weight_pct)
        """
        v27_trans_pct, v26_trans_pct, _, _ = self.calculate_transactional_weight()
        return v27_trans_pct, v26_trans_pct

    def get_mining_allocation(self) -> Tuple[float, float, List[Tuple[str, str, float]]]:
        """
        Get hashrate allocation from user/economic nodes that mine (solo miners).

        Solo miners follow their economic fork decision for mining.
        Their hashrate goes to whichever fork they've chosen economically.

        Returns:
            Tuple of (v27_hashrate_pct, v26_hashrate_pct, miner_list)
            where miner_list is [(node_id, fork, hashrate_pct), ...]
        """
        v27_hash = 0.0
        v26_hash = 0.0
        miners = []

        for node_id, node in self.nodes.items():
            if node.hashrate_pct > 0:
                fork = self.current_allocation[node_id]
                if fork == 'v27':
                    v27_hash += node.hashrate_pct
                else:
                    v26_hash += node.hashrate_pct
                miners.append((node_id, fork, node.hashrate_pct))

        return v27_hash, v26_hash, miners

    def get_solo_miners(self) -> List[Tuple[str, str, float]]:
        """
        Get list of solo miners and their current fork allocation.

        Returns:
            List of (node_id, current_fork, hashrate_pct) for nodes with hashrate
        """
        _, _, miners = self.get_mining_allocation()
        return miners

    def get_total_solo_hashrate(self) -> float:
        """Get total hashrate from all solo miners."""
        return sum(n.hashrate_pct for n in self.nodes.values() if n.hashrate_pct > 0)

    def print_allocation_summary(self):
        """Print current economic allocation summary."""
        print("\n" + "=" * 70)
        print("ECONOMIC NODE ALLOCATION")
        print("=" * 70)

        v27_total = 0.0
        v26_total = 0.0
        for node_id, node in self.nodes.items():
            fork = self.current_allocation[node_id]
            if fork == 'v27':
                v27_total += self._node_weight(node)
            else:
                v26_total += self._node_weight(node)

        total = v27_total + v26_total
        v27_pct = (v27_total / total * 100) if total > 0 else 50.0
        v26_pct = (v26_total / total * 100) if total > 0 else 50.0

        print(f"\nAggregate Economic Weight (price support):")
        print(f"  v27: {v27_pct:.1f}% (weight: {v27_total:.2f})")
        print(f"  v26: {v26_pct:.1f}% (weight: {v26_total:.2f})")

        # Transactional vs custodial breakdown
        v27_trans, v26_trans, v27_cust, v26_cust = self.calculate_transactional_weight()
        print(f"\nTransactional Weight (fee generation):")
        print(f"  v27: {v27_trans:.1f}%")
        print(f"  v26: {v26_trans:.1f}%")
        print(f"\nCustodial Weight (price support only):")
        print(f"  v27: {v27_cust:.1f}%")
        print(f"  v26: {v26_cust:.1f}%")

        # Solo miner breakdown
        v27_solo, v26_solo, solo_miners = self.get_mining_allocation()
        if solo_miners:
            print(f"\nSolo Miner Hashrate:")
            print(f"  v27: {v27_solo:.2f}%")
            print(f"  v26: {v26_solo:.2f}%")
            print(f"  Miners: {len(solo_miners)}")
            for node_id, fork, hashrate in solo_miners:
                print(f"    {node_id}: {hashrate:.3f}% on {fork}")

        # Breakdown by type
        breakdown = self.get_allocation_breakdown()
        for ntype, data in breakdown.items():
            type_total = data['v27_weight'] + data['v26_weight']
            if type_total == 0:
                continue
            print(f"\n  {ntype.upper()} nodes:")
            print(f"    v27: {data['v27_count']} nodes, weight {data['v27_weight']:.2f}")
            print(f"    v26: {data['v26_count']} nodes, weight {data['v26_weight']:.2f}")

        # Individual node details
        print(f"\nIndividual Node Decisions:")
        for node_id, node in self.nodes.items():
            fork = self.current_allocation[node_id]
            stats = self.node_stats[node_id]
            pref_str = ""
            if node.fork_preference != ForkPreference.NEUTRAL:
                pref_str = f" (prefers {node.fork_preference.value})"

            print(f"\n  {node_id} [{node.node_type.value}]{pref_str}:")
            print(f"    On: {fork} | Weight: {node.consensus_weight:.4f}")
            print(f"    Switches: {stats['switches']} | "
                  f"Ideology holds: {stats['ideology_overrides']} | "
                  f"Inertia holds: {stats['inertia_holds']}")

        print("\n" + "=" * 70)

    def export_to_json(self, output_path: str):
        """Export decision history and allocation to JSON."""
        # Calculate transactional vs custodial breakdown
        v27_trans, v26_trans, v27_cust, v26_cust = self.calculate_transactional_weight()

        # Get solo miner info
        solo_miners = self.get_solo_miners()
        v27_solo, v26_solo, _ = self.get_mining_allocation()

        export_data = {
            'nodes': {
                node_id: {
                    'profile': {
                        'node_id': node.node_id,
                        'node_type': node.node_type.value,
                        'activity_type': node.activity_type.value,
                        'transaction_velocity': node.transaction_velocity,
                        'fork_preference': node.fork_preference.value,
                        'ideology_strength': node.ideology_strength,
                        'switching_threshold': node.switching_threshold,
                        'custody_btc': node.custody_btc,
                        'daily_volume_btc': node.daily_volume_btc,
                        'consensus_weight': node.consensus_weight,
                        'hashrate_pct': node.hashrate_pct,
                        'inertia': node.inertia,
                        'role': node.role,
                    },
                    'current_allocation': self.current_allocation[node_id],
                    'stats': self.node_stats[node_id],
                }
                for node_id, node in self.nodes.items()
            },
            'solo_mining': {
                'total_hashrate_pct': self.get_total_solo_hashrate(),
                'v27_hashrate_pct': v27_solo,
                'v26_hashrate_pct': v26_solo,
                'miners': [
                    {'node_id': m[0], 'fork': m[1], 'hashrate_pct': m[2]}
                    for m in solo_miners
                ],
            },
            'allocation_breakdown': self.get_allocation_breakdown(),
            'transactional_breakdown': {
                'v27_transactional_pct': v27_trans,
                'v26_transactional_pct': v26_trans,
                'v27_custodial_pct': v27_cust,
                'v26_custodial_pct': v26_cust,
            },
            'decision_history': [asdict(d) for d in self.decision_history],
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)


def load_economic_nodes_from_network(
    node_metadata: Dict[str, Dict],
    config: Dict,
    scenario_name: str
) -> List[EconomicNodeProfile]:
    """
    Build EconomicNodeProfile list from network metadata + scenario config.

    Merges two data sources:
    - node_metadata (from network.yaml): economic data (custody_btc, volume, weight)
    - config (from economic_nodes_config.yaml): ideology parameters

    Args:
        node_metadata: Dict of node_name -> metadata from network.yaml
        config: Parsed economic_nodes_config.yaml
        scenario_name: Which scenario to load (e.g., 'realistic_current')

    Returns:
        List of EconomicNodeProfile for non-pool nodes
    """
    if scenario_name not in config:
        raise ValueError(f"Economic scenario '{scenario_name}' not found in config")

    scenario = config[scenario_name]
    economic_defaults = scenario.get('economic_defaults', {})
    user_defaults = scenario.get('user_defaults', {})
    overrides = scenario.get('overrides', {})
    distribution = scenario.get('distribution_pattern', None)

    profiles = []

    # Track node indices for distribution_pattern assignment
    economic_idx = 0
    user_idx = 0
    economic_nodes_list = []
    user_nodes_list = []

    # First pass: categorize nodes
    for node_name, metadata in node_metadata.items():
        node_type_str = metadata.get('node_type', metadata.get('role', ''))

        # Skip pool nodes (handled by MiningPoolStrategy)
        if node_type_str == 'mining_pool' or metadata.get('entity_id', '').startswith('pool-'):
            continue

        # Determine node type
        if node_type_str in ('economic', 'major_exchange', 'exchange', 'payment_processor'):
            economic_nodes_list.append((node_name, metadata))
        elif node_type_str == 'user_node' or node_type_str == 'network':
            user_nodes_list.append((node_name, metadata))
        else:
            # Unknown type -- treat as user node
            user_nodes_list.append((node_name, metadata))

    # Second pass: build profiles with ideology from config
    for node_name, metadata in economic_nodes_list:
        role = metadata.get('role', 'exchange')
        defaults = dict(economic_defaults)

        # Apply role-specific overrides
        if role in overrides:
            defaults.update(overrides[role])

        # Apply distribution pattern if present
        if distribution and 'economic' in distribution:
            pattern = distribution['economic']
            assigned = _assign_from_distribution(pattern, economic_idx, len(economic_nodes_list))
            if assigned:
                defaults.update(assigned)
            economic_idx += 1

        # Determine initial fork from the node's image tag (stored in metadata
        # by partition_miner_with_pools.py). Fall back to node index heuristic
        # only if tag is absent (backwards compatibility with old network YAMLs).
        image_tag = metadata.get('image_tag', '')
        if image_tag:
            initial_fork = 'v27' if '27' in image_tag else 'v26'
        else:
            node_idx = int(node_name.split('-')[1]) if '-' in node_name else 0
            initial_fork = 'v27' if node_idx < 10 else 'v26'

        # Determine activity type and transaction velocity based on role
        # Exchanges and payment processors are highly transactional
        # Custody services and treasuries are low velocity
        activity_type, transaction_velocity = _get_activity_profile(
            role, defaults, metadata
        )

        # Check for hashrate (economic nodes can also mine, e.g., mining pool with exchange)
        hashrate_pct = metadata.get('hashrate_pct', defaults.get('hashrate_pct', 0.0))

        profiles.append(EconomicNodeProfile(
            node_id=node_name,
            node_type=NodeType.ECONOMIC,
            activity_type=activity_type,
            transaction_velocity=transaction_velocity,
            fork_preference=ForkPreference(defaults.get('fork_preference', 'neutral')),
            ideology_strength=defaults.get('ideology_strength', 0.1),
            switching_threshold=defaults.get('switching_threshold', 0.03),
            custody_btc=metadata.get('custody_btc', 0),
            daily_volume_btc=metadata.get('daily_volume_btc', 0),
            consensus_weight=metadata.get('consensus_weight', 0.0),
            hashrate_pct=hashrate_pct,
            switching_cooldown=defaults.get('switching_cooldown', 1800),
            max_loss_pct=defaults.get('max_loss_pct', 0.05),
            inertia=defaults.get('inertia', 0.15),
            role=role,
            initial_fork=initial_fork,
        ))

    for node_name, metadata in user_nodes_list:
        defaults = dict(user_defaults)

        # Apply distribution pattern if present
        if distribution and 'user' in distribution:
            pattern = distribution['user']
            assigned = _assign_from_distribution(pattern, user_idx, len(user_nodes_list))
            if assigned:
                defaults.update(assigned)
            user_idx += 1

        image_tag = metadata.get('image_tag', '')
        if image_tag:
            initial_fork = 'v27' if '27' in image_tag else 'v26'
        else:
            node_idx = int(node_name.split('-')[1]) if '-' in node_name else 0
            initial_fork = 'v27' if node_idx < 10 else 'v26'

        # User nodes are typically mixed activity - some transactions, some holding
        activity_type = ActivityType(defaults.get('activity_type', 'mixed'))
        transaction_velocity = defaults.get('transaction_velocity', 0.3)

        # Check for solo miner hashrate (from network metadata or defaults)
        hashrate_pct = metadata.get('hashrate_pct', defaults.get('hashrate_pct', 0.0))

        profiles.append(EconomicNodeProfile(
            node_id=node_name,
            node_type=NodeType.USER,
            activity_type=activity_type,
            transaction_velocity=transaction_velocity,
            fork_preference=ForkPreference(defaults.get('fork_preference', 'neutral')),
            ideology_strength=defaults.get('ideology_strength', 0.3),
            switching_threshold=defaults.get('switching_threshold', 0.08),
            custody_btc=metadata.get('custody_btc', 0),
            daily_volume_btc=metadata.get('daily_volume_btc', 0),
            consensus_weight=metadata.get('consensus_weight', 0.0),
            hashrate_pct=hashrate_pct,
            switching_cooldown=defaults.get('switching_cooldown', 3600),
            max_loss_pct=defaults.get('max_loss_pct', 0.15),
            inertia=defaults.get('inertia', 0.05),
            role=None,
            initial_fork=initial_fork,
        ))

    return profiles


def _get_activity_profile(
    role: str,
    defaults: Dict,
    metadata: Dict
) -> Tuple[ActivityType, float]:
    """
    Determine activity type and transaction velocity based on node role.

    Role-based defaults:
    - major_exchange: Very high velocity (0.9) - constant trading
    - exchange: High velocity (0.8) - frequent trading
    - payment_processor: Very high velocity (0.95) - processing payments
    - merchant: High velocity (0.7) - regular sales
    - custody: Low velocity (0.1) - mostly holding
    - treasury: Very low velocity (0.05) - corporate reserve
    - hodler: Minimal velocity (0.02) - long-term holder

    Args:
        role: Node role string
        defaults: Default config values (may override)
        metadata: Node metadata from network.yaml

    Returns:
        Tuple of (ActivityType, transaction_velocity)
    """
    # Check for explicit overrides in config
    if 'activity_type' in defaults:
        activity_type = ActivityType(defaults['activity_type'])
    else:
        activity_type = None

    if 'transaction_velocity' in defaults:
        velocity = defaults['transaction_velocity']
    else:
        velocity = None

    # Role-based defaults if not specified
    role_profiles = {
        'major_exchange': (ActivityType.TRANSACTIONAL, 0.9),
        'exchange': (ActivityType.TRANSACTIONAL, 0.8),
        'payment_processor': (ActivityType.TRANSACTIONAL, 0.95),
        'merchant': (ActivityType.TRANSACTIONAL, 0.7),
        'custody': (ActivityType.CUSTODIAL, 0.1),
        'treasury': (ActivityType.CUSTODIAL, 0.05),
        'hodler': (ActivityType.CUSTODIAL, 0.02),
        'whale': (ActivityType.MIXED, 0.3),  # Whales occasionally move large amounts
        'default': (ActivityType.MIXED, 0.5),
    }

    role_lower = role.lower() if role else 'default'
    default_type, default_velocity = role_profiles.get(role_lower, role_profiles['default'])

    # Use computed defaults if not explicitly set
    if activity_type is None:
        activity_type = default_type
    if velocity is None:
        velocity = default_velocity

    # Can also infer from daily_volume_btc / custody_btc ratio if available
    daily_vol = metadata.get('daily_volume_btc', 0)
    custody = metadata.get('custody_btc', 1)  # Avoid div by zero
    if custody > 0 and daily_vol > 0:
        # If daily volume is high relative to custody, node is transactional
        vol_ratio = daily_vol / custody
        # vol_ratio of 0.1 = 10% daily turnover = very transactional
        # vol_ratio of 0.001 = 0.1% daily = very custodial
        if vol_ratio > 0.05:
            inferred_velocity = min(0.95, vol_ratio * 10)
        else:
            inferred_velocity = max(0.02, vol_ratio * 20)

        # Blend inferred with role-based (role takes priority)
        velocity = velocity * 0.7 + inferred_velocity * 0.3

    return activity_type, velocity


def _assign_from_distribution(
    pattern: List[Dict],
    index: int,
    total: int
) -> Optional[Dict]:
    """
    Assign ideology parameters from a distribution pattern.

    Pattern example:
        [
            {"pct": 40, "fork_preference": "v27", "ideology_strength": 0.7},
            {"pct": 40, "fork_preference": "v26", "ideology_strength": 0.7},
            {"pct": 20, "fork_preference": "neutral", "ideology_strength": 0.0}
        ]

    Args:
        pattern: List of {pct, fork_preference, ideology_strength, ...}
        index: Current node index (0-based)
        total: Total nodes of this type

    Returns:
        Dict of override parameters, or None
    """
    if not pattern or total == 0:
        return None

    # Calculate which bucket this node falls into
    position_pct = (index / total) * 100.0

    cumulative = 0.0
    for bucket in pattern:
        cumulative += bucket.get('pct', 0)
        if position_pct < cumulative:
            # This node belongs to this bucket
            result = {}
            for key in ('fork_preference', 'ideology_strength', 'switching_threshold',
                        'inertia', 'max_loss_pct', 'switching_cooldown'):
                if key in bucket:
                    result[key] = bucket[key]
            return result

    # Fallback to last bucket
    if pattern:
        bucket = pattern[-1]
        result = {}
        for key in ('fork_preference', 'ideology_strength', 'switching_threshold',
                    'inertia', 'max_loss_pct', 'switching_cooldown'):
            if key in bucket:
                result[key] = bucket[key]
        return result

    return None


if __name__ == "__main__":
    """Test the economic node strategy system."""

    print("=" * 70)
    print("ECONOMIC NODE STRATEGY TEST")
    print("=" * 70)

    # Create test profiles (simulating network nodes)
    test_nodes = [
        # Major exchange (high weight, rational)
        EconomicNodeProfile(
            node_id="econ-0000",
            node_type=NodeType.ECONOMIC,
            fork_preference=ForkPreference.NEUTRAL,
            ideology_strength=0.0,
            switching_threshold=0.02,
            custody_btc=1_527_272,
            daily_volume_btc=152_727,
            consensus_weight=111.72,
            switching_cooldown=1800,
            inertia=0.20,
            role="major_exchange",
            initial_fork="v27",
        ),
        # Secondary exchange
        EconomicNodeProfile(
            node_id="econ-0001",
            node_type=NodeType.ECONOMIC,
            fork_preference=ForkPreference.V26,
            ideology_strength=0.3,
            switching_threshold=0.05,
            custody_btc=763_636,
            daily_volume_btc=76_363,
            consensus_weight=55.86,
            switching_cooldown=1800,
            inertia=0.15,
            max_loss_pct=0.10,
            role="exchange",
            initial_fork="v27",
        ),
        # Payment processor (slight v26 preference)
        EconomicNodeProfile(
            node_id="econ-0002",
            node_type=NodeType.ECONOMIC,
            fork_preference=ForkPreference.V26,
            ideology_strength=0.4,
            switching_threshold=0.05,
            custody_btc=509_090,
            daily_volume_btc=50_909,
            consensus_weight=37.24,
            switching_cooldown=1800,
            inertia=0.10,
            max_loss_pct=0.15,
            role="payment_processor",
            initial_fork="v27",
        ),
        # User node (ideological, low weight)
        EconomicNodeProfile(
            node_id="user-0008",
            node_type=NodeType.USER,
            fork_preference=ForkPreference.V27,
            ideology_strength=0.8,
            switching_threshold=0.10,
            custody_btc=3.5,
            daily_volume_btc=0.5,
            consensus_weight=0.0003,
            switching_cooldown=3600,
            inertia=0.05,
            max_loss_pct=0.30,
            initial_fork="v27",
        ),
        # Another user node (neutral)
        EconomicNodeProfile(
            node_id="user-0018",
            node_type=NodeType.USER,
            fork_preference=ForkPreference.NEUTRAL,
            ideology_strength=0.0,
            switching_threshold=0.05,
            custody_btc=1.2,
            daily_volume_btc=0.2,
            consensus_weight=0.0001,
            switching_cooldown=3600,
            inertia=0.03,
            initial_fork="v26",
        ),
    ]

    strategy = EconomicNodeStrategy(test_nodes)

    # Mock price oracle
    class MockPriceOracle:
        def __init__(self):
            self.prices = {'v27': 60000, 'v26': 60000}

        def get_price(self, chain_id):
            return self.prices[chain_id]

    oracle = MockPriceOracle()

    print("\nPhase 1: Equal prices ($60,000 each)")
    v27_pct, v26_pct = strategy.calculate_economic_allocation(time.time(), oracle)
    print(f"  Economic allocation: v27={v27_pct:.1f}%, v26={v26_pct:.1f}%")

    print("\nPhase 2: v27 price advantage ($63,000 vs $57,000)")
    oracle.prices = {'v27': 63000, 'v26': 57000}
    # Force decisions by setting cooldown to 0
    for node in test_nodes:
        strategy.last_decision_time[node.node_id] = 0.0
    v27_pct, v26_pct = strategy.calculate_economic_allocation(time.time(), oracle)
    print(f"  Economic allocation: v27={v27_pct:.1f}%, v26={v26_pct:.1f}%")

    print("\nPhase 3: Large v27 advantage ($66,000 vs $54,000)")
    oracle.prices = {'v27': 66000, 'v26': 54000}
    for node in test_nodes:
        strategy.last_decision_time[node.node_id] = 0.0
    v27_pct, v26_pct = strategy.calculate_economic_allocation(time.time(), oracle)
    print(f"  Economic allocation: v27={v27_pct:.1f}%, v26={v26_pct:.1f}%")

    strategy.print_allocation_summary()
    print(f"\nTotal decisions recorded: {len(strategy.decision_history)}")
    print("=" * 70)
