#!/usr/bin/env python3

"""
Knots-vs-Core Mesh Fork Pilot — derived from partition_miner_with_pools.py

Same economic simulation apparatus as the file this is derived from (price
oracle, fee oracle, pool strategy, economic-node switching, difficulty
oracle, reorg oracle) — unchanged, see that file's original docstring below
for the feedback-loop description. What's different here:

- 'v27'/'v26' are kept as internal bookkeeping labels (oracles/time-series
  hardcode these strings), but now mean Knots-enforcing (v27) vs Core-v30
  (v26) camps, classified by getnetworkinfo()['subversion'] rather than
  image-tag comparison (see classify_nodes_by_subversion()).
- The mechanisms that previously FAKED partitioning/rejection
  (propagate_v26_to_v27's coin-flip, switch_node_partition/reunite_forks'
  manual addnode/disconnectnode calls, propagate_to_foreign_accepting's
  submitblock bridging) are all still present and still fully functional —
  nothing removed — but the two that were active by default
  (switch_node_partition's call in evaluate_economic_node_switches, and
  propagate_to_foreign_accepting's call in the mining loop) are now gated
  behind new off-by-default flags (--enable-manual-repartition,
  --enable-asymmetric-bridging). An old-style v27/v26 run is still fully
  reproducible from this same file by passing the old flags.
- New: RDTS fork trigger (inject_rdts_violation/check_rdts_rejection) — a
  real oversized-OP_RETURN transaction that real Knots consensus code
  (Consensus::CheckOutputSizes) rejects, once mined, with
  bad-txns-vout-script-toolarge. RDTS is configured ALWAYS_ACTIVE from
  genesis (see networks/knots-mesh-pilot's vbparams), so this needs no BIP9
  state machine wait.
- New: observe_chain_state — samples real node tips from each camp every
  --chain-state-interval seconds (tip relation / LCA / branch lengths,
  reorgs, injected-tx confirmation state, Knots invalid-branch count),
  exported under chain_state. blocks_mined and the [SUSTAINED] label are
  mining-loop bookkeeping, not observed chain state; because Core accepts
  Knots blocks, a longer Knots chain reorgs Core nodes onto it, which only
  chain_state shows. Observation only — never mines or touches peers.
- New: --oracle-chain-source observed (default in subversion mode) — the
  price oracle's chain weight/fork depth and pool profitability use observed
  surviving blocks per camp instead of blocks_mined, so orphaned blocks earn
  nothing (SurvivalAdjustedDifficulty, observed_price_inputs).

Original docstring (partition_miner_with_pools.py), still accurate for the
economic-simulation portion of this file:

Integration of:
- Phase 1: Price Oracle (price tracking)
- Phase 2: Fee Oracle (fee market dynamics)
- Phase 3: Mining Pool Strategy (ideology + profitability)
- Phase 4: Economic Node Strategy (all nodes have ideology, dynamic economic weight)

Key changes:
- Hashrate allocation is DYNAMIC (pools switch based on profitability + ideology)
- Economic weight is DYNAMIC (economic/user nodes switch based on price + ideology)
- Network topology stays STATIC (v27 nodes isolated from v26 nodes)
- Both MINING PROBABILITY and ECONOMIC WEIGHT change over time

Feedback loop:
  Price Oracle → Pool decisions (hashrate changes)
       ↑          Economic/User decisions (economic weight changes)
       └──────────────────────┘

Network stays partitioned:
  v27 nodes ✗✗✗ v26 nodes (can't communicate)

But actors can switch which fork they support:
  Pools: choose which partition to mine on
  Economic nodes: choose which fork's economy to participate in
  User nodes: choose which fork to use
"""

from collections import Counter
from time import sleep, time
from random import random, choices
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from commander import Commander

# Import from lib modules (bundled with scenario)
import os
from lib.price_oracle import PriceOracle
from lib.fee_oracle import FeeOracle
from lib.mining_pool_strategy import (
    ForkPreference,
    PoolProfile,
    MiningPoolStrategy,
    load_pools_from_config,
)
from lib.economic_node_strategy import (
    EconomicNodeStrategy,
    EconomicNodeProfile,
    load_economic_nodes_from_network,
)
from lib.difficulty_oracle import DifficultyOracle
from lib.reorg_oracle import ReorgOracle


class SurvivalAdjustedDifficulty:
    """
    DifficultyOracle proxy handed to MiningPoolStrategy under
    --oracle-chain-source=observed: get_blocks_per_hour() is scaled by the
    fraction of that camp's recent blocks still in its observed active chain,
    so pool revenue counts only blocks that weren't orphaned. Everything else
    passes through to the real oracle unchanged.
    """

    def __init__(self, oracle, survival_ratio):
        self._oracle = oracle
        self._survival_ratio = survival_ratio

    def get_blocks_per_hour(self, fork_id: str, hashrate_pct: float) -> float:
        return self._oracle.get_blocks_per_hour(fork_id, hashrate_pct) * self._survival_ratio(fork_id)

    def __getattr__(self, name):
        return getattr(self._oracle, name)


class KnotsMeshPilot(Commander):
    """
    Knots-vs-Core mesh fork pilot, with dynamic pool + economic strategy.

    All actors make independent fork decisions:
    - Mining pools: choose which fork to mine (hashrate allocation)
    - Economic nodes: choose which fork's economy to support (economic weight)
    - User nodes: choose which fork to use (economic weight, small contribution)

    Decisions are based on:
    1. Profitability / Price advantage (rational economics)
    2. Ideology (fork preference)
    3. Loss tolerance / Inertia (switching costs)
    """

    def set_test_params(self):
        """Initialize test parameters"""
        self.num_nodes = 0
        self.v27_nodes = []
        self.v26_nodes = []
        self.blocks_mined = {'v27': 0, 'v26': 0}

        # Oracles
        self.price_oracle = None
        self.fee_oracle = None
        self.pool_strategy = None
        self.economic_strategy = None
        self.difficulty_oracle = None
        self.reorg_oracle = None

        # Difficulty mode tick interval
        self.tick_interval = 1.0

        # Current hashrate allocation (dynamic - from pool decisions)
        self.current_v27_hashrate = 0.0
        self.current_v26_hashrate = 0.0

        # Current economic allocation (dynamic - from economic/user node decisions)
        self.current_v27_economic = 0.0
        self.current_v26_economic = 0.0

        # Transactional economic allocation (fee-generating activity only)
        # Distinguishes exchanges/merchants (high velocity) from HODLers (low velocity)
        self.current_v27_transactional = 0.0
        self.current_v26_transactional = 0.0

        # Solo miner hashrate (user/economic nodes that mine)
        self.current_v27_solo_hashrate = 0.0
        self.current_v26_solo_hashrate = 0.0

        # Pool-to-node mappings (per partition)
        self.pool_nodes_v27 = {}  # pool_id -> list of v27 nodes
        self.pool_nodes_v26 = {}  # pool_id -> list of v26 nodes

        # Node metadata from network.yaml
        self.node_metadata = {}  # node_name -> metadata dict

        # Asymmetric fork: nodes that accept blocks from the foreign fork
        # v26 nodes have accepts_foreign_blocks=True and receive v27 blocks via submitblock
        self.foreign_accepting_nodes = []

        # Dynamic partition switching: track peer lists and node partition assignments
        self.v27_peer_addresses = []  # List of v27 node addresses for reconnection
        self.v26_peer_addresses = []  # List of v26 node addresses for reconnection
        self.node_current_partition = {}  # node_name -> current partition ('v27' or 'v26')
        self.partition_switch_history = []  # Track all partition switches for analysis

        # Time-limited UASF: v27 nodes enforce strict rules for a limited time
        self.uasf_active = True  # Whether UASF is currently active
        self.uasf_start_time = None  # When UASF started (simulation time)
        self.uasf_expiry_time = None  # When UASF expires (simulation time)
        self.uasf_expired = False  # Whether UASF has expired
        self.uasf_expiry_data = None  # Snapshot of state at expiry

        # Reunion state: after reunion, all hashrate goes to winning fork
        self.reunion_completed = False  # Whether reunion has successfully completed
        self.reunion_winner = None  # Winning fork after reunion ('v27' or 'v26')

        # RDTS fork trigger tracking: did the injected OP_RETURN tx actually
        # get rejected by v27 (Knots) nodes once mined?
        self.rdts_injection_txid = None
        self.rdts_rejection = {
            'injected': False,
            'txid': None,
            'rejected': False,
            'rejected_at_elapsed_s': None,
            'rejecting_nodes': [],
            'log_confirmed': False,
        }

        # Fork convergence tracking (--fork-heal-exit): did the v27/v26 islands
        # organically reconverge to the same tip during the run?
        self.fork_convergence = {
            'enabled': False,
            'diverged': False,
            'healed': False,
            'heal_time_s': None,
            'v27_blocks_at_heal': None,
            'v26_blocks_at_heal': None,
        }

        # Observed chain state (observe_chain_state): real node tips, sampled
        # from each camp, independent of the blocks_mined bookkeeping counters.
        # Kept separate from self.time_series because it has its own cadence
        # (--chain-state-interval) and its own timestamps array.
        self.chain_state = {
            'enabled': False,
            'interval_s': None,
            'sample_nodes': {'v27': [], 'v26': []},
            'relation_changes': [],     # [{elapsed, relation, prev_relation}]
            'reorg_events': [],         # unique per (camp, disconnected tip)
            'reorg_count': {'v27': 0, 'v26': 0},
            'max_reorg_depth': {'v27': 0, 'v26': 0},
            'max_invalid_tips': 0,      # distinct invalid branches seen by a Knots node
            'final': None,
            'time_series': {
                'timestamps': [],
                'relation': [],             # same_tip / diverged / *_ahead_on_*_chain / unknown
                'v27_height': [],
                'v26_height': [],
                'v27_tip': [],
                'v26_tip': [],
                'fork_height': [],          # LCA height when diverged, else None
                'v27_branch_len': [],       # blocks above LCA on the Knots tip
                'v26_branch_len': [],       # blocks above LCA on the Core tip
                'v27_distinct_tips': [],    # within the sampled Knots nodes (propagation lag)
                'v26_distinct_tips': [],
                'injected_tx_state': [],    # confirmed / mempool / unconfirmed / conflicted / unknown
                'injected_tx_height': [],
                'v27_invalid_tips': [],
            },
        }
        self._chain_last_tip = {}           # node_name -> (height, hash)
        self._chain_seen_reorgs = {}        # (camp, disconnected_tip) -> index into reorg_events
        # Block survival (feeds the oracles under --oracle-chain-source=observed):
        # which blocks each camp mined, and each camp's active chain above
        # start_height as last observed.
        self.oracle_chain_source = 'mined'              # resolved in run_test
        # --inplace-switching: blocks the scenario mined carrying the RDTS-
        # violating tx (so switching nodes can invalidate/reconsider them), the
        # signed tx itself, and every node mode switch performed.
        self._violating_blocks = []
        self._violating_tx_hex = None
        self.inplace_switches = []
        self._mined_blocks = {'v27': [], 'v26': []}     # block hashes, mining order
        self._active_chain = {'v27': {}, 'v26': {}}     # height -> hash
        self.chain_state['survival'] = {
            camp: {'mined': 0, 'surviving': 0, 'orphaned': 0, 'window_ratio': 1.0}
            for camp in ('v27', 'v26')
        }
        for key in ('v27_surviving', 'v26_surviving', 'v27_survival_ratio', 'v26_survival_ratio'):
            self.chain_state['time_series'][key] = []

        # Time series data for charting
        self.time_series = {
            'timestamps': [],           # elapsed seconds
            'v27_price': [],
            'v26_price': [],
            'v27_hashrate': [],
            'v26_hashrate': [],
            'v27_economic': [],
            'v26_economic': [],
            'v27_blocks': [],
            'v26_blocks': [],
            'v27_difficulty': [],
            'v26_difficulty': [],
            'v27_chainwork': [],
            'v26_chainwork': [],
            # Fee market metrics
            'v27_fee_rate': [],         # sats/vbyte
            'v26_fee_rate': [],
            'v27_fee_revenue_btc': [],  # fee revenue per block
            'v26_fee_revenue_btc': [],
            'v27_congestion': [],       # tx_volume / throughput ratio
            'v26_congestion': [],
            'v27_mempool_mb': [],       # estimated mempool size
            'v26_mempool_mb': [],
            # Transactional vs custodial activity
            'v27_transactional': [],    # fee-generating economic activity %
            'v26_transactional': [],
            # Solo miner hashrate (user nodes that mine)
            'v27_solo_hashrate': [],
            'v26_solo_hashrate': [],
            # Measured block time (rolling window between snapshots, sim-seconds per block)
            # Scale to real-world: multiply by (600 / target_block_interval)
            'v27_block_time_s': [],
            'v26_block_time_s': [],
        }

    def add_options(self, parser: argparse.ArgumentParser):
        """Add command-line arguments"""
        # ── Config file pre-load (must come first) ───────────────────────────
        # Pre-parse just --config-file so we can load it before setting defaults.
        import sys as _sys
        _pre = argparse.ArgumentParser(add_help=False)
        _pre.add_argument('--config-file', type=str, default=None)
        _pre_args, _ = _pre.parse_known_args(_sys.argv[1:])
        if _pre_args.config_file:
            import yaml as _yaml
            with open(_pre_args.config_file) as _f:
                _cfg = _yaml.safe_load(_f) or {}
            # set_defaults uses dest names (underscores); filter out nulls
            _defaults = {k: v for k, v in _cfg.items() if v is not None}
            if _defaults:
                parser.set_defaults(**_defaults)

        parser.add_argument('--config-file', type=str, default=None,
                            help='YAML file whose keys set parameter defaults '
                                 '(CLI flags override). Keys use underscores matching '
                                 'argparse dest names.')
        parser.add_argument('--v27-economic', type=float, default=70.0,
                          help='Economic weight on v27 (0-100)')
        parser.add_argument('--v26-economic', type=float, default=None)
        parser.add_argument('--interval', type=int, default=10,
                          help='Block mining interval (seconds)')
        parser.add_argument('--duration', type=int, default=7200,
                          help='Test duration (seconds), default 2 hours')
        parser.add_argument('--start-height', type=int, default=101)

        # Pool configuration
        parser.add_argument('--pool-scenario', type=str, default='knots_mesh_current',
                          help='Pool scenario from mining_pools_config.yaml. Default: '
                               'knots_mesh_current (generated from networks/knots-mesh-pilot pool '
                               'nodes, so every pool starts on the camp its node runs). '
                               "partition_miner_with_pools.py's default realistic_current lists "
                               'pools that have no node, or only a node in the other camp, on this network.')
        parser.add_argument('--initial-v27-hashrate', type=float, default=None,
                          help='Initial v27 hashrate (if not using pools)')

        # Network configuration
        parser.add_argument('--network-yaml', type=str, default=None,
                          help='Path to network.yaml file with node metadata')

        # Economic node configuration
        parser.add_argument('--economic-scenario', type=str, default='realistic_current',
                          help='Economic node scenario from economic_nodes_config.yaml')
        parser.add_argument('--economic-update-interval', type=int, default=300,
                          help='Economic node decision interval (seconds), default 5min')

        # Update intervals
        parser.add_argument('--hashrate-update-interval', type=int, default=600,
                          help='Pool decision interval (seconds), default 10min')
        parser.add_argument('--pool-decision-interval', type=int, default=600,
                          help='Pool internal decision cooldown (seconds), default 10min. '
                               'Minimum time between each pool re-evaluating its fork choice.')
        parser.add_argument('--price-update-interval', type=int, default=60,
                          help='Price update interval (seconds)')

        # Difficulty oracle configuration
        parser.add_argument('--enable-difficulty', action='store_true', default=False,
                          help='Enable difficulty simulation (probability-per-tick mining)')
        parser.add_argument('--retarget-interval', type=int, default=144,
                          help='Blocks between difficulty adjustments (default 144)')
        parser.add_argument('--tick-interval', type=float, default=1.0,
                          help='Tick interval in seconds for difficulty mode (default 1.0)')
        parser.add_argument('--enable-eda', action='store_true', default=False,
                          help='Enable Emergency Difficulty Adjustment (BCH-style)')
        parser.add_argument('--min-difficulty', type=float, default=0.0625,
                          help='Minimum difficulty floor (default 0.0625 = 1/16)')

        # Reorg metrics
        parser.add_argument('--enable-reorg-metrics', action='store_true', default=False,
                          help='Enable reorg tracking oracle for fork impact metrics')
        parser.add_argument('--enable-dynamic-switching', action='store_true', default=True,
                          help='Enable dynamic partition switching for economic/user nodes (default: True)')

        # Fork reunion
        parser.add_argument('--enable-reunion', action='store_true', default=False,
                          help='At end of duration, reconnect partitions and let the heavier chain reorg the loser')
        parser.add_argument('--reunion-timeout', type=int, default=120,
                          help='Seconds to wait for reorg convergence after reconnection (default 120)')

        # Probabilistic v26 block acceptance by v27 nodes
        parser.add_argument('--v26-acceptance-probability', type=float, default=0.0,
                          help='Probability that a v26 block is accepted by v27 nodes (0.0=strict, '
                               '1.0=fully permissive). Models softfork rules that only apply to a '
                               'subset of transactions — blocks not containing violating transactions '
                               'are valid on both chains. E.g., 0.75 = 75%% of v26 blocks comply '
                               'with v27 rules and propagate to the v27 partition. (default: 0.0)')

        # Time-limited UASF (User Activated Soft Fork)
        parser.add_argument('--uasf-duration', type=int, default=None,
                          help='UASF duration in seconds. After this time, v27 nodes stop enforcing strict rules '
                               'and accept v26 blocks. If not set, UASF runs indefinitely.')
        parser.add_argument('--uasf-expiry-action', type=str, default='reunion',
                          choices=['reunion', 'accept', 'continue'],
                          help='Action when UASF expires: '
                               'reunion=reconnect partitions and reorg to heavier chain, '
                               'accept=v27 nodes accept v26 blocks but stay partitioned, '
                               'continue=just log expiry and continue (default: reunion)')

        # Results management
        parser.add_argument('--results-id', type=str, default=None,
                          help='Unique identifier for this run (default: auto-generated timestamp)')
        parser.add_argument('--snapshot-interval', type=int, default=60,
                          help='Interval in seconds for time series snapshots (default: 60)')

        # Price model options
        parser.add_argument('--enable-liveness-penalty', action='store_true', default=False,
                          help='Enable Option B liveness penalty: decay economic factor by block '
                               'production rate. Dead chains (0 blocks/hr) lose their economic '
                               'premium/discount. Raises max_divergence cap to 50%%.')
        parser.add_argument('--use-economic-ema', action='store_true', default=False,
                          help='Proposal 1 (Kristoufek 2015): Apply EMA lag to economic weight. '
                               'Price responds gradually to custody shifts rather than instantly.')
        parser.add_argument('--economic-ema-alpha', type=float, default=0.15,
                          help='EMA smoothing factor for economic weight (default: 0.15). '
                               '0=no update, 1=no lag. Half-life ~4.3 cycles at 0.15.')
        parser.add_argument('--use-sigmoid', action='store_true', default=False,
                          help='Proposal 2 (Biais et al. 2019): Replace linear factor mapping '
                               'with logistic sigmoid. Produces sharper minority-chain collapse '
                               'at extreme economic weights. Applied to economic factor only.')
        parser.add_argument('--sigmoid-steepness', type=float, default=6.0,
                          help='Sigmoid steepness k (default: 6.0). k=4 gentle, k=6 moderate, k=10 near-step.')
        parser.add_argument('--use-cost-floor', action='store_true', default=False,
                          help='Proposal 3 (Hayes 2019): Replace symmetric price floor with '
                               'per-fork cost-of-production floor scaled by hashrate share. '
                               'Minority chains at low hashrate face proportionally lower price floors.')
        parser.add_argument('--cost-floor-margin-buffer', type=float, default=0.05,
                          help='Safety buffer below breakeven for cost floor (default: 0.05 = 5%%).')
        parser.add_argument('--max-price-divergence', type=float, default=None,
                          help='Max price divergence cap (e.g., 0.20 for ±20%%). Overrides default oracle cap.')

        # Debug options
        parser.add_argument('--debug-prices', action='store_true', default=False,
                          help='Enable verbose price calculation debugging')

        # Fork formation / convergence
        parser.add_argument('--partition-mode', type=str, default='static',
                          choices=['static', 'unified'],
                          help='static=structural partition assumed from block 0 (default). '
                               'unified=both partitions start on the same chain tip — this is '
                               'informational/logging only, since both islands already share a '
                               'common ancestor at --start-height before mining begins.')
        parser.add_argument('--fork-heal-exit', action='store_true', default=False,
                          help='Exit the mining loop early once the v27 and v26 islands converge '
                               'to the same tip block hash (organic fork healing). Records '
                               'fork_convergence.{healed,heal_time_s,v27_blocks_at_heal,v26_blocks_at_heal} '
                               'in the results.')

        # Knots-vs-Core real-rejection mode. All of the mechanisms these gate
        # (switch_node_partition, propagate_to_foreign_accepting) remain fully
        # present and functional — these flags default OFF so this file's new
        # behavior is opt-in, not a removal of the old behavior. Pass them to
        # reproduce an old-style simulated-partition run from this same file.
        parser.add_argument('--node-classification', type=str, default='subversion',
                          choices=['tag', 'subversion', 'rdts'],
                          help="'tag'=partition_nodes_by_version's original image-tag "
                               "comparison (v27/v26 numeric tags). 'subversion'=classify by "
                               "getnetworkinfo()['subversion'] instead (Knots vs Core), for "
                               "networks that don't use those tags. 'rdts'=classify by whether "
                               "the node's RDTS deployment is active (getdeploymentinfo), for "
                               "all-Knots networks; forced by --inplace-switching. "
                               "Default: subversion.")
        parser.add_argument('--inplace-switching', action='store_true', default=False,
                          help='When a pool or economic/user node switches fork, change what '
                               'its node actually enforces: rewrite <datadir>/switch.conf '
                               '(RDTS vbparams on/off), RPC stop, let the pod restart bitcoind, '
                               'then invalidateblock/reconsiderblock to reconcile its chain. '
                               'Requires an all-Knots network built for it '
                               '(networks/knots-mesh-inplace, tools/make_inplace_network.py) '
                               'and commander pods/exec RBAC. Forces --node-classification rdts. '
                               'Core-mode miners include the pending RDTS-violating tx via '
                               'generateblock, standing in for a Core mempool (Knots policy caps '
                               'datacarriersize at 83, so no Knots node relays it). '
                               'Default: False (switches are accounting only).')
        parser.add_argument('--switch-restart-timeout', type=int, default=180,
                          help='Seconds to wait for a switching node to come back with the new '
                               'RDTS mode (covers the kubelet restart back-off). Default: 180.')
        parser.add_argument('--enable-manual-repartition', action='store_true', default=False,
                          help='Allow evaluate_economic_node_switches to actually call '
                               'switch_node_partition (manual invalidateblock/disconnectnode/'
                               'addnode rewiring) when a node decides to defect. Default: False '
                               '— nodes stay on a real, always-connected mesh; only real '
                               'consensus validation (not manual peer rewiring) determines '
                               'which blocks propagate.')
        parser.add_argument('--enable-asymmetric-bridging', action='store_true', default=False,
                          help='Allow propagate_to_foreign_accepting to submitblock v27 blocks '
                               'directly to a designated bridge node, bypassing normal P2P '
                               'relay. Default: False — blocks propagate only via real P2P '
                               'relay across the mesh.')
        parser.add_argument('--rdts-injection', action='store_true', default=True,
                          help='Inject one oversized-OP_RETURN transaction from a v26 (Core) '
                               'node shortly after startup, to exercise RDTS\'s real '
                               'Consensus::CheckOutputSizes rejection on v27 (Knots) nodes. '
                               'Default: True (this is the actual fork trigger for this '
                               'scenario). Pass --no-rdts-injection to disable for a pure '
                               'economic-simulation run with no real-consensus divergence.')
        parser.add_argument('--no-rdts-injection', dest='rdts_injection', action='store_false')
        parser.add_argument('--op-return-payload-size', type=int, default=81,
                          help="Bytes of OP_RETURN data to inject (default: 81 — RDTS's "
                               "MAX_OUTPUT_DATA_SIZE is 83 bytes total scriptPubKey; 81 bytes "
                               "of payload plus the OP_RETURN opcode and PUSHDATA1 prefix "
                               "pushes it to 84, just over the limit).")
        parser.add_argument('--rdts-check-interval', type=int, default=30,
                          help='Seconds between checks for RDTS rejection evidence '
                               '(getchaintips polling + debug.log grep). Default: 30.')
        parser.add_argument('--chain-state-interval', type=int, default=10,
                          help='Seconds between observations of real node chain tips '
                               '(tip relation between camps, reorgs on sampled nodes, '
                               'injected-tx confirmation state, Knots invalid-branch count). '
                               'Observation only — never changes mining or topology. '
                               'Exported under chain_state. 0 disables. Default: 10.')
        parser.add_argument('--chain-state-sample', type=int, default=3,
                          help='Nodes sampled per camp for chain-state observation, evenly '
                               'spaced across the camp (0 = all nodes). Default: 3.')
        parser.add_argument('--oracle-chain-source', choices=['observed', 'mined'], default=None,
                          help="What the price and pool oracles treat as each camp's chain. "
                               "'observed': blocks each camp mined that are still in its "
                               "observed active chain (orphaned blocks count for nothing) — "
                               "price chain weight, fork depth, and pool revenue use this. "
                               "'mined': the blocks_mined counters / difficulty-oracle "
                               "chainwork, as partition_miner_with_pools.py did. Default: "
                               "observed with --node-classification subversion, mined with tag "
                               "(so legacy runs reproduce). Requires --chain-state-interval > 0.")
        parser.add_argument('--economic-switching-cooldown', type=float, default=None,
                          help='Override switching_cooldown (seconds) for economic-type nodes. '
                               'Config default is 1800s for realistic_current, which is >= a '
                               'typical run length, so economic nodes decide once at t=0 and '
                               'never re-decide — set this lower (e.g. 60) to exercise economic '
                               'switching in a short run. Default: None (use the config value).')
        parser.add_argument('--user-switching-cooldown', type=float, default=None,
                          help='Same as --economic-switching-cooldown, for user-type nodes '
                               '(realistic_current default 3600s). Default: None (use config).')
        parser.add_argument('--survival-window', type=int, default=30,
                          help="Pool revenue under --oracle-chain-source=observed is scaled by "
                               "the fraction of a camp's last N mined blocks still in its active "
                               "chain (1.0 until 5 blocks mined). Default: 30.")
        parser.add_argument('--bundled-network-yaml', type=str, default='knots_mesh_pilot_network.yaml',
                          help='Filename (under scenarios/config/, loaded via pkgutil since '
                               '--network-yaml cannot resolve a path inside the .pyz archive '
                               'at runtime) used as the network-metadata fallback when '
                               '--network-yaml is not set or not found. Default: this '
                               "scenario's own real 60-node network "
                               '(knots_mesh_pilot_network.yaml, a copy of '
                               'networks/knots-mesh-pilot/network.yaml) rather than '
                               "partition_miner_with_pools.py's generic 25-node example "
                               '(network_metadata.yaml) — pass that name to restore the old '
                               'generic behavior.')

    def load_network_metadata(self):
        """Load node metadata from network.yaml file or bundled config"""
        network_config = None

        # Try loading from specified path first
        if self.options.network_yaml:
            network_yaml_path = Path(self.options.network_yaml)
            if network_yaml_path.exists():
                self.log.info(f"Loading network metadata from {network_yaml_path}")
                try:
                    with open(network_yaml_path, 'r') as f:
                        network_config = yaml.safe_load(f)
                except Exception as e:
                    self.log.warning(f"Error loading network YAML from path: {e}")

        # Fallback: try loading from bundled config. --network-yaml can't
        # resolve a path inside the .pyz archive at runtime (Path.exists()
        # checks the real filesystem, not the zip), so this bundled-data
        # path is the only way to ship the real deployed network's metadata
        # into the commander pod. --bundled-network-yaml defaults to this
        # scenario's own real network (scenarios/config/knots_mesh_pilot_network.yaml,
        # a full copy of networks/knots-mesh-pilot/network.yaml) rather than
        # the generic 25-node example partition_miner_with_pools.py uses —
        # keep that original filename available via the flag for anyone who
        # wants the old generic-example behavior back.
        if network_config is None:
            try:
                import pkgutil
                bundled_data = pkgutil.get_data('config', self.options.bundled_network_yaml)
                if bundled_data:
                    network_config = yaml.safe_load(bundled_data.decode('utf-8'))
                    self.log.info(f"Loading network metadata from bundled config: {self.options.bundled_network_yaml}")
            except Exception as e:
                self.log.debug(f"No bundled network metadata: {e}")

        # If we loaded config, check for accepts_foreign_blocks and infer from version if missing
        if network_config:
            nodes = network_config.get('nodes', [])
            foreign_blocks_set = any(
                n.get('metadata', {}).get('accepts_foreign_blocks') is not None
                for n in nodes
            )
            if not foreign_blocks_set:
                self.log.info("Inferring accepts_foreign_blocks from node versions (v26 nodes accept v27 blocks)")
                for node_config in nodes:
                    image_tag = node_config.get('image', {}).get('tag', '')
                    metadata = node_config.get('metadata', {})
                    # v26 nodes accept v27 blocks (non-contentious soft fork model)
                    if '26' in str(image_tag):
                        metadata['accepts_foreign_blocks'] = True
                    else:
                        metadata['accepts_foreign_blocks'] = False
                    node_config['metadata'] = metadata

        if network_config is None:
            self.log.warning("No network metadata available, pool/economic mapping will be limited")
            return

        try:
            # Build node name -> metadata mapping
            for node_config in network_config.get('nodes', []):
                node_name = node_config.get('name')
                metadata = node_config.get('metadata', {})
                # Preserve image tag so economic_node_strategy can determine
                # initial fork from version rather than a hardcoded index threshold
                image = node_config.get('image', {})
                image_tag = image.get('tag', '')
                if self.options.node_classification == 'subversion':
                    # economic_node_strategy infers a node's starting camp via
                    # "'27' in image_tag". Neither Knots (29.4-local) nor Core
                    # (30.2) tags contain '27', so every economic/user node
                    # would start on v26. Substitute a camp label derived from
                    # the image repository (checked against the live
                    # subversion classification in check_metadata_camps()).
                    image_tag = ('27-knots' if 'knots' in str(image.get('repository', '')).lower()
                                 else '26-core')
                elif self.options.node_classification == 'rdts':
                    # All-Knots network: the starting camp is the seeded
                    # switch.conf, recorded as metadata.initial_camp by
                    # tools/make_inplace_network.py.
                    initial_camp = metadata.get('initial_camp')
                    if initial_camp not in ('v27', 'v26'):
                        self.log.warning(f"  {node_name}: no metadata.initial_camp; assuming v26")
                    image_tag = '27-rdts' if initial_camp == 'v27' else '26-core-mode'
                metadata['image_tag'] = image_tag

                if node_name:
                    self.node_metadata[node_name] = metadata

            self.log.info(f"✓ Loaded metadata for {len(self.node_metadata)} nodes")

            # Under tag classification, economic/user starting camps come from
            # "'27' in image_tag". If the loaded metadata is the Knots network
            # (29.4-local / 30.2 tags), every node silently starts on v26 —
            # e.g. a legacy run that forgot --bundled-network-yaml.
            if self.options.node_classification == 'tag':
                tags = {str(m.get('image_tag', '')) for m in self.node_metadata.values()}
                if not any('26' in t or '27' in t for t in tags):
                    self.log.warning(f"  --node-classification tag but loaded metadata has no "
                                     f"26/27 image tags ({sorted(tags)}); economic/user nodes "
                                     f"will all start on v26. For legacy runs pass "
                                     f"--bundled-network-yaml realistic_economy_v2_network.yaml")

        except Exception as e:
            self.log.error(f"Error loading network YAML: {e}")

    def partition_nodes_by_version(self):
        """Separate nodes into v27 and v26 partitions"""
        self.log.info("Partitioning nodes by version...")

        for node in self.nodes:
            try:
                network_info = node.getnetworkinfo()
                version_string = network_info.get('subversion', '')

                is_v27 = '27.' in version_string or ':27.' in version_string
                is_v26 = '26.' in version_string or ':26.' in version_string

                if is_v27:
                    self.v27_nodes.append(node)
                elif is_v26:
                    self.v26_nodes.append(node)

            except Exception as e:
                self.log.error(f"  Error querying node {node.index}: {e}")

        self.log.info(f"\nPartition summary:")
        self.log.info(f"  v27 nodes: {len(self.v27_nodes)}")
        self.log.info(f"  v26 nodes: {len(self.v26_nodes)}")

    def classify_nodes_by_subversion(self):
        """
        Separate nodes into v27 (Knots-enforcing) and v26 (Core-v30) camps by
        getnetworkinfo()['subversion'], instead of partition_nodes_by_version's
        numeric-tag matching (which would match neither Knots' "29.4.0" nor
        Core's "30.2.0" — Knots reports .../Knots:<date>/, Core does not).

        Kept as a separate method from partition_nodes_by_version rather than
        modifying it, so an old-style v27/v26 tag-based run still works
        unchanged via --node-classification=tag.
        """
        self.log.info("Classifying nodes by subversion (Knots vs Core)...")

        for node in self.nodes:
            try:
                subversion = node.getnetworkinfo().get('subversion', '')
                if 'Knots' in subversion:
                    self.v27_nodes.append(node)
                else:
                    self.v26_nodes.append(node)
            except Exception as e:
                self.log.error(f"  Error querying node {node.index}: {e}")

        self.log.info(f"\nClassification summary:")
        self.log.info(f"  v27 (Knots) nodes: {len(self.v27_nodes)}")
        self.log.info(f"  v26 (Core) nodes:  {len(self.v26_nodes)}")
        self.check_metadata_camps()

    @staticmethod
    def _ensure_miner(node):
        """Commander.ensure_miner, but loads an existing 'miner' wallet that an
        in-place switch restart unloaded instead of failing to re-create it."""
        if "miner" not in node.listwallets():
            try:
                node.loadwallet("miner")
            except Exception:
                pass
        return Commander.ensure_miner(node)

    @staticmethod
    def _rdts_active(node) -> bool:
        """True if the node enforces RDTS. A Knots node without the RDTS vbparams
        doesn't list the reduced_data deployment at all."""
        deployments = node.getdeploymentinfo().get('deployments', {})
        return bool(deployments.get('reduced_data', {}).get('active'))

    def classify_nodes_by_rdts(self):
        """
        Separate nodes into v27 (RDTS enforced) and v26 (RDTS inactive, i.e.
        Core-compatible consensus) for all-Knots networks, where subversion
        can't tell the camps apart. Used by --inplace-switching, where a node's
        camp changes during the run.
        """
        self.log.info("Classifying nodes by RDTS deployment status...")

        for node in self.nodes:
            try:
                if self._rdts_active(node):
                    self.v27_nodes.append(node)
                else:
                    self.v26_nodes.append(node)
            except Exception as e:
                self.log.error(f"  Error querying node {node.index}: {e}")

        self.log.info(f"\nClassification summary:")
        self.log.info(f"  v27 (RDTS enforced) nodes: {len(self.v27_nodes)}")
        self.log.info(f"  v26 (Core-mode) nodes:     {len(self.v26_nodes)}")
        self.check_metadata_camps()

    def check_metadata_camps(self):
        """
        Warn if the camp load_network_metadata() derived from the network YAML's
        image repository (used for economic/user nodes' starting fork) disagrees
        with the live subversion classification (used for mining).
        """
        mismatched = []
        for camp, nodes in (('v27', self.v27_nodes), ('v26', self.v26_nodes)):
            for node in nodes:
                name = f"node-{node.index:04d}"
                tag = self.node_metadata.get(name, {}).get('image_tag')
                if tag is None:
                    continue
                meta_camp = 'v27' if '27' in tag else 'v26'
                if meta_camp != camp:
                    mismatched.append((name, meta_camp, camp))
        if mismatched:
            self.log.warning(f"  {len(mismatched)} node(s) have a metadata camp that differs from "
                             f"their live subversion camp (metadata, live): {mismatched}")
        else:
            self.log.info(f"  Metadata camps match live classification for all "
                          f"{len(self.v27_nodes) + len(self.v26_nodes)} nodes")

    def build_foreign_accepting_nodes(self):
        """
        Identify nodes that accept blocks from the foreign fork (accepts_foreign_blocks=True).

        In the asymmetric fork model:
          - v27 (strict): rejects v26 blocks — accepts_foreign_blocks=False
          - v26 (permissive): accepts v27 blocks — accepts_foreign_blocks=True

        When a v27 block is mined, it is submitted to the first foreign-accepting node
        via submitblock. P2P propagation within the v26 island handles the rest.

        Note: v26 nodes automatically accept v27 blocks in non-contentious soft fork model,
        so we treat all v26 nodes as foreign-accepting by default.
        """
        self.foreign_accepting_nodes = []

        for node in self.v26_nodes:
            node_name = f"node-{node.index:04d}"
            metadata = self.node_metadata.get(node_name, {})

            # Check explicit flag first
            accepts_foreign = metadata.get('accepts_foreign_blocks', None)

            # If not explicitly set, v26 nodes accept v27 blocks by default
            # (non-contentious soft fork model)
            if accepts_foreign is None:
                # v26 nodes accept v27 blocks (stricter rules are valid under looser rules)
                accepts_foreign = True
                self.log.debug(f"  {node_name}: accepts_foreign_blocks not set, defaulting to True (v26 node)")

            if accepts_foreign:
                self.foreign_accepting_nodes.append(node)

        if self.foreign_accepting_nodes:
            self.log.info(
                f"\nAsymmetric fork mode: {len(self.foreign_accepting_nodes)} foreign-accepting node(s). "
                f"v27 blocks will be submitted to node-{self.foreign_accepting_nodes[0].index:04d} "
                f"for v26-island propagation."
            )
        else:
            self.log.info(
                "\nAsymmetric fork mode: no foreign-accepting nodes found "
                "(accepts_foreign_blocks not set in metadata). "
                "Running as standard symmetric partition."
            )

    def propagate_to_foreign_accepting(self, miner, fork_id: str):
        """
        After mining a v27 block, push it to the v26 island via submitblock.

        Only acts when fork_id=='v27' and foreign-accepting nodes exist.
        Submits to one bridge node only — P2P handles intra-island propagation.
        """
        if fork_id != 'v27' or not self.foreign_accepting_nodes:
            return

        try:
            block_hash = miner.getbestblockhash()
            raw_block = miner.getblock(block_hash, 0)
            bridge_node = self.foreign_accepting_nodes[0]
            result = bridge_node.submitblock(raw_block)
            if result is not None:
                # submitblock returns None on success; any other value is a rejection reason
                self.log.warning(
                    f"  [asymmetric] submitblock to node-{bridge_node.index:04d} returned: {result}"
                )
        except Exception as e:
            self.log.error(f"  [asymmetric] Failed to propagate v27 block to v26 island: {e}")

    def propagate_v26_to_v27(self, miner) -> bool:
        """
        After mining a v26 block, probabilistically submit it to the v27 partition.

        Models a softfork where the new rules apply to a specific transaction type
        rather than all blocks. A v26 block is invalid under v27 rules only if it
        contains a transaction violating the new constraint. Blocks that happen to
        contain only compliant transactions are valid on both chains.

        --v26-acceptance-probability controls the fraction of v26 blocks that are
        compatible (0.0 = strict UASF, all v26 blocks rejected; 1.0 = fully
        permissive, every v26 block propagates to v27).

        Returns True if the block was accepted by the v27 partition.
        """
        p = getattr(self.options, 'v26_acceptance_probability', 0.0)
        if p <= 0.0 or not self.v27_nodes:
            return False

        import random as _random
        if _random.random() > p:
            # This block contains a transaction violating v27 rules — rejected
            return False

        # Block is compatible — submit to one v27 bridge node; P2P handles the rest
        try:
            block_hash = miner.getbestblockhash()
            raw_block = miner.getblock(block_hash, 0)
            bridge_node = self.v27_nodes[0]
            result = bridge_node.submitblock(raw_block)
            if result is not None:
                self.log.debug(
                    f"  [v26→v27] submitblock returned: {result} "
                    f"(block {block_hash[:12]})"
                )
                return False
            self.log.debug(f"  [v26→v27] accepted v26 block {block_hash[:12]}")
            return True
        except Exception as e:
            self.log.error(f"  [v26→v27] propagation failed: {e}")
            return False

    def ensure_common_history(self):
        """
        Mine 101 maturity blocks if the network doesn't already have them, so
        the RDTS injection tx has a spendable (matured) coinbase input.

        partition_miner_with_pools.py itself never mines maturity blocks — it
        assumes the network already has common history from a prior timeline
        step (see scenarios/example_timeline.yaml's generate_common_history
        action). This scenario can't assume that step ran, so it checks and
        mines its own if needed. Idempotent: skipped if height already >=101.
        """
        if not self.nodes:
            return
        try:
            height = self.nodes[0].getblockcount()
        except Exception as e:
            self.log.warning(f"  Could not read starting height: {e}")
            height = 0

        if height >= 101:
            self.log.info(f"  Common history already present (height={height}), skipping maturity mining")
            return

        funding_node = self.v26_nodes[0] if self.v26_nodes else self.nodes[0]
        self.log.info(f"  Mining 101 maturity blocks via node-{funding_node.index:04d} "
                      f"(funds the RDTS injection tx)...")
        wallet = self._ensure_miner(funding_node)
        addr = wallet.getnewaddress()
        self.generatetoaddress(funding_node, 101, addr, sync_fun=self.sync_all)
        self.log.info(f"  Mined 101 blocks, height now {funding_node.getblockcount()}")

    def inject_rdts_violation(self):
        """
        Broadcast one transaction with an oversized OP_RETURN output from a
        v26 (Core) node's wallet. No special flags needed — Core 30.2's
        default -datacarriersize policy (~100,000 bytes) treats this as
        standard. Once mined into a block, real Knots consensus code
        (Consensus::CheckOutputSizes, RDTS ALWAYS_ACTIVE from genesis) rejects
        that block on v27 (Knots) nodes with bad-txns-vout-script-toolarge —
        this is the actual fork trigger for this scenario. Runs once, early,
        independent of and alongside the untouched economic simulation.
        """
        self.rdts_rejection['injected'] = False
        if not self.options.rdts_injection:
            self.log.info("  RDTS injection disabled (--no-rdts-injection)")
            return
        if not self.v26_nodes:
            self.log.warning("  RDTS injection skipped: no v26 (Core) nodes available")
            return

        node = self.v26_nodes[0]
        try:
            wallet = self._ensure_miner(node)
            payload_size = self.options.op_return_payload_size
            payload_hex = ('00' * payload_size)
            raw = wallet.createrawtransaction([], {'data': payload_hex})
            funded = wallet.fundrawtransaction(raw)
            signed = wallet.signrawtransactionwithwallet(funded['hex'])
            if self.options.inplace_switching:
                # Every node runs Knots, whose policy caps datacarriersize at
                # 83, so no mempool would take this tx. Hold it; Core-mode
                # miners include it via generateblock (_mine_block).
                txid = node.decoderawtransaction(signed['hex'])['txid']
                self._violating_tx_hex = signed['hex']
            else:
                txid = node.sendrawtransaction(signed['hex'])

            self.rdts_injection_txid = txid
            self._rdts_wallet = wallet  # for observe_chain_state's confirmation tracking
            self.rdts_rejection['injected'] = True
            self.rdts_rejection['txid'] = txid
            self.log.info(
                f"  [RDTS] Injected OP_RETURN tx {txid} "
                f"({payload_size}-byte payload) via node-{node.index:04d} (v26/Core)"
            )
        except Exception as e:
            self.log.error(f"  [RDTS] Injection failed: {e}")

    def _violation_in_chain(self, node) -> Optional[int]:
        """Height of a scenario-mined RDTS-violating block in node's active
        chain, or None. (confirmations is -1 for a block off the active chain;
        getblockheader raises for a block the node doesn't have.)"""
        for block_hash in self._violating_blocks:
            try:
                header = node.getblockheader(block_hash)
            except Exception:
                continue
            if header.get('confirmations', -1) > 0:
                return header['height']
        return None

    def _mine_block(self, miner, fork_id: str, address: str) -> list:
        """
        Mine one block on miner. Under --inplace-switching a Core-mode (v26)
        miner whose chain lacks the RDTS-violating tx mines it via
        generateblock, as a real Core miner would from its mempool, including
        re-mining it after its chain was reorged onto the Knots chain. No
        Knots node's mempool takes the tx (datacarriersize is capped at 83),
        so this is the one place the scenario models mempool contents.
        """
        if (self.options.inplace_switching and fork_id == 'v26' and self._violating_tx_hex
                and self._violation_in_chain(miner) is None):
            block_hash = miner.generateblock(address, [self._violating_tx_hex])['hash']
            self._violating_blocks.append(block_hash)
            self.log.info(f"  [RDTS] node-{miner.index:04d} (Core-mode) mined violating tx "
                          f"in block {block_hash[:16]} (violating block #{len(self._violating_blocks)})")
            return [block_hash]
        return self.generatetoaddress(miner, 1, address, sync_fun=self.no_op)

    def check_rdts_rejection(self, elapsed: int):
        """
        Check whether v27 (Knots) nodes have rejected a block containing the
        injected RDTS-violating transaction.

        Two signals, cheapest first:
        1. getchaintips() on v27 nodes — a rejected block shows up with
           status: "invalid". Cheap, checked every call.
        2. pod-exec grep of debug.log for bad-txns-vout-script-toolarge — the
           definitive confirmation of the exact rejection reason (not just
           "some block was invalid for some reason"). Only run once, the
           first time signal 1 fires, to avoid repeated pod-exec calls.

        No-ops once already confirmed (self.rdts_rejection['rejected']).
        """
        if self.rdts_rejection['rejected'] or not self.rdts_rejection['injected']:
            return
        if not self.v27_nodes:
            return

        newly_rejecting = []
        for node in self.v27_nodes:
            node_name = f"node-{node.index:04d}"
            try:
                tips = node.getchaintips()
            except Exception as e:
                self.log.debug(f"  [RDTS check] getchaintips failed on {node_name}: {e}")
                continue
            if any(t.get('status') == 'invalid' for t in tips):
                newly_rejecting.append((node, node_name))

        if not newly_rejecting:
            return

        self.rdts_rejection['rejected'] = True
        self.rdts_rejection['rejected_at_elapsed_s'] = elapsed
        self.rdts_rejection['rejecting_nodes'] = [name for _, name in newly_rejecting]

        self.log.info(
            f"\n{'='*70}\n"
            f"RDTS REJECTION DETECTED at {elapsed}s: {len(newly_rejecting)} v27 (Knots) "
            f"node(s) show an invalid chain tip: {[n for _, n in newly_rejecting]}\n"
            f"{'='*70}"
        )

        # Definitive confirmation: grep the first rejecting node's debug.log
        # for the exact RDTS rejection reason, via the same pod-exec pattern
        # commander.py already uses (kubernetes.stream.stream). Imported
        # lazily (not at module level) since commander.sclient/NAMESPACE are
        # only set when actually running in-cluster — a top-level import
        # would break local/--help invocation outside a cluster.
        try:
            import commander as _commander_module
            from kubernetes.stream import stream as k8s_stream
            sclient = _commander_module.sclient
            NAMESPACE = _commander_module.NAMESPACE

            node, node_name = newly_rejecting[0]
            cmd = [
                "sh", "-c",
                "grep -c bad-txns-vout-script-toolarge "
                "/root/.bitcoin/regtest/debug.log || true"
            ]
            result = k8s_stream(
                sclient.connect_get_namespaced_pod_exec,
                name=node.tank,
                container="bitcoincore",
                namespace=NAMESPACE,
                command=cmd,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )
            match_count = (result or "0").strip().splitlines()[-1] if result else "0"
            if match_count.isdigit() and int(match_count) > 0:
                self.rdts_rejection['log_confirmed'] = True
                self.log.info(
                    f"  [RDTS] Confirmed in {node_name}'s debug.log: "
                    f"{match_count} occurrence(s) of bad-txns-vout-script-toolarge"
                )
            else:
                self.log.warning(
                    f"  [RDTS] getchaintips showed invalid, but debug.log grep on "
                    f"{node_name} found no bad-txns-vout-script-toolarge — "
                    f"rejection may be for a different reason, investigate."
                )
        except Exception as e:
            self.log.warning(f"  [RDTS] debug.log confirmation failed (pod-exec): {e}")

    def check_fork_healed(self, elapsed: int) -> bool:
        """
        Check whether the v27 and v26 islands have organically diverged and then
        reconverged to the same chain tip (used by --fork-heal-exit).

        A tip match only counts as a "heal" if the two islands were previously
        observed on different tips — otherwise a scenario that hasn't split yet
        (e.g. the very first block under partition_mode=unified) would trigger
        a false-positive heal at elapsed=0.

        Returns True (and records fork_convergence state) the first time the
        two islands' best block hashes match again after having diverged.
        """
        if self.fork_convergence['healed'] or not self.v27_nodes or not self.v26_nodes:
            return self.fork_convergence['healed']

        try:
            v27_tip = self.v27_nodes[0].getbestblockhash()
            v26_tip = self.v26_nodes[0].getbestblockhash()
        except Exception as e:
            self.log.warning(f"  Could not check fork convergence: {e}")
            return False

        if v27_tip != v26_tip:
            self.fork_convergence['diverged'] = True
            return False

        if not self.fork_convergence['diverged']:
            # Tips still match because the islands never split yet — not a heal.
            return False

        self.fork_convergence['healed'] = True
        self.fork_convergence['heal_time_s'] = elapsed
        self.fork_convergence['v27_blocks_at_heal'] = self.blocks_mined['v27']
        self.fork_convergence['v26_blocks_at_heal'] = self.blocks_mined['v26']
        self.log.info(
            f"\n{'='*70}\n"
            f"FORK HEALED at {elapsed}s: v27 and v26 islands converged to {v27_tip[:16]}\n"
            f"  Blocks at heal: v27={self.blocks_mined['v27']}, v26={self.blocks_mined['v26']}\n"
            f"{'='*70}"
        )
        return True

    def _chain_state_sample(self, nodes: list) -> list:
        """Evenly spaced subset of a camp's nodes (all of them if sample size is 0)."""
        k = self.options.chain_state_sample
        if k <= 0 or k >= len(nodes):
            return list(nodes)
        step = len(nodes) / k
        return [nodes[int(i * step)] for i in range(k)]

    def _detect_reorg(self, node, node_name: str, camp: str, height: int, tip: str, elapsed: int):
        """
        Compare a node's current tip against its last observed tip. If the old
        tip is no longer in the node's active chain, record a reorg event
        (deduplicated per camp by the disconnected tip hash, so the same reorg
        seen on several sampled nodes counts once).
        """
        prev = self._chain_last_tip.get(node_name)
        self._chain_last_tip[node_name] = (height, tip)
        if prev is None or prev[1] == tip:
            return
        prev_height, prev_tip = prev

        # Plain extension: the old tip is still in the active chain.
        if height >= prev_height:
            try:
                if node.getblockhash(prev_height) == prev_tip:
                    return
            except Exception:
                pass

        key = (camp, prev_tip)
        if key in self._chain_seen_reorgs:
            event = self.chain_state['reorg_events'][self._chain_seen_reorgs[key]]
            if node_name not in event['observed_on']:
                event['observed_on'].append(node_name)
            return

        # Reorg. getchaintips lists the disconnected branch as a valid-fork
        # tip with its branchlen — one RPC, no header walk needed.
        fork_height = None
        try:
            for t in node.getchaintips():
                if t.get('hash') == prev_tip:
                    fork_height = t['height'] - t.get('branchlen', 0)
                    break
        except Exception:
            pass
        if fork_height is None:
            # Old tip was itself extended before being disconnected; walk back.
            try:
                cur, cur_h = prev_tip, prev_height
                for _ in range(500):
                    if cur_h <= height and node.getblockhash(cur_h) == cur:
                        break
                    cur = node.getblockheader(cur)['previousblockhash']
                    cur_h -= 1
                fork_height = cur_h
            except Exception as e:
                self.log.debug(f"  [chain-state] fork-point walk failed on {node_name}: {e}")

        depth = prev_height - fork_height if fork_height is not None else None
        event = {
            'elapsed_s': elapsed,
            'camp': camp,
            'old_tip': prev_tip,
            'old_height': prev_height,
            'new_tip': tip,
            'new_height': height,
            'fork_height': fork_height,
            'depth': depth,
            'observed_on': [node_name],
        }
        self._chain_seen_reorgs[key] = len(self.chain_state['reorg_events'])
        self.chain_state['reorg_events'].append(event)
        self.chain_state['reorg_count'][camp] += 1
        if depth is not None:
            self.chain_state['max_reorg_depth'][camp] = max(
                self.chain_state['max_reorg_depth'][camp], depth)
        label = 'Knots' if camp == 'v27' else 'Core'
        self.log.info(
            f"  [chain-state {elapsed:>5}s] REORG on {camp} ({label}) {node_name}: "
            f"height {prev_height} -> {height}, depth={depth}, fork point={fork_height}"
        )

    def _injected_tx_state(self) -> Tuple[str, Optional[int]]:
        """Confirmation state of the RDTS injection tx, from the injecting Core node's wallet."""
        txid = self.rdts_rejection.get('txid')
        wallet = getattr(self, '_rdts_wallet', None)
        if not txid or wallet is None:
            return 'none', None
        if self.options.inplace_switching:
            # Judged against the current Core camp's chain: the injecting
            # node's own wallet may have switched to the Knots camp since.
            height = self._violation_in_chain(self.v26_nodes[0]) if self.v26_nodes else None
            return ('confirmed', height) if height is not None else ('pending', None)
        try:
            wtx = wallet.gettransaction(txid)
        except Exception:
            return 'unknown', None
        confs = wtx.get('confirmations', 0)
        if confs > 0:
            return 'confirmed', wtx.get('blockheight')
        if confs < 0:
            return 'conflicted', None
        try:
            self.v26_nodes[0].getmempoolentry(txid)
            return 'mempool', None
        except Exception:
            return 'unconfirmed', None

    def _update_active_chain(self, camp: str, node, tip_height: int, tip: str):
        """
        Refresh the cached active chain (height -> hash above start_height) for a
        camp from one of its nodes. Walks back from the tip via previousblockhash
        until it meets the cache, so the walk is consistent even if the node
        reorgs mid-walk, and costs ~(new blocks + reorg depth) RPCs.
        """
        cache = self._active_chain[camp]
        for h in [h for h in cache if h > tip_height]:
            del cache[h]
        floor = self.options.start_height
        h, block = tip_height, tip
        while h > floor and cache.get(h) != block:
            cache[h] = block
            block = node.getblockheader(block)['previousblockhash']
            h -= 1

    def _update_survival(self):
        """Mined vs still-in-active-chain block counts per camp."""
        window = max(1, self.options.survival_window)
        for camp in ('v27', 'v26'):
            active = set(self._active_chain[camp].values())
            mined = self._mined_blocks[camp]
            surviving = sum(1 for b in mined if b in active)
            recent = mined[-window:]
            ratio = (sum(1 for b in recent if b in active) / len(recent)) if len(recent) >= 5 else 1.0
            self.chain_state['survival'][camp] = {
                'mined': len(mined),
                'surviving': surviving,
                'orphaned': len(mined) - surviving,
                'window_ratio': ratio,
            }

    def survival_ratio(self, camp: str) -> float:
        return self.chain_state['survival'][camp]['window_ratio']

    def observed_price_inputs(self):
        """
        (v27_height, v26_height, common_ancestor_height, v27_chain_weight,
        v26_chain_weight) for the price oracle from observed chain state, or
        None if nothing observed yet. Chain weight is each camp's share of
        surviving self-mined blocks; fork depth uses observed heights and the
        observed LCA (tips on one chain => the lower tip is the ancestor).
        """
        final = self.chain_state.get('final')
        if not final or final.get('v27_height') is None or final.get('v26_height') is None:
            return None
        v27_h, v26_h = final['v27_height'], final['v26_height']
        if final.get('fork_height') is not None:
            ancestor = final['fork_height']
        elif final.get('relation') in ('same_tip', 'v26_ahead_on_v27_chain', 'v27_ahead_on_v26_chain'):
            ancestor = min(v27_h, v26_h)
        else:
            ancestor = self.options.start_height
        s27 = self.chain_state['survival']['v27']['surviving']
        s26 = self.chain_state['survival']['v26']['surviving']
        total = s27 + s26
        w27 = s27 / total if total else 0.5
        return v27_h, v26_h, ancestor, w27, 1.0 - w27

    def observe_chain_state(self, elapsed: int):
        """
        Observation only: record what the nodes actually report, as opposed to
        the blocks_mined counters (which only count which camp the mining loop
        picked). Captures:
          - each camp's majority tip among sampled nodes, and how the two
            relate (same tip, one camp's tip in the other's active chain, or
            diverged with LCA + branch lengths)
          - reorgs on sampled nodes (e.g. Core nodes switching to a longer
            Knots chain, which Core considers valid)
          - whether the injected RDTS tx is in the Core chain, back in the
            mempool after a reorg, or conflicted
          - how many distinct invalid branches a Knots node has seen (each
            re-mining of the injected tx after a Core reorg adds one)
        Never mines, submits blocks, or touches peers.
        """
        if not self.chain_state['enabled'] or not self.v27_nodes or not self.v26_nodes:
            return

        camp_tips = {}
        for camp, nodes in (('v27', self.v27_nodes), ('v26', self.v26_nodes)):
            observed = []
            for node in self._chain_state_sample(nodes):
                node_name = f"node-{node.index:04d}"
                try:
                    tip = node.getbestblockhash()
                    height = node.getblockcount()
                except Exception as e:
                    self.log.debug(f"  [chain-state] tip query failed on {node_name}: {e}")
                    continue
                observed.append((node, height, tip))
                self._detect_reorg(node, node_name, camp, height, tip, elapsed)
            camp_tips[camp] = observed

        ts = self.chain_state['time_series']
        relation, fork_height, v27_branch, v26_branch = 'unknown', None, None, None
        v27_height = v26_height = v27_tip = v26_tip = None

        if camp_tips['v27'] and camp_tips['v26']:
            def majority(observed):
                counts = Counter(tip for _, _, tip in observed)
                tip = counts.most_common(1)[0][0]
                node, height, _ = next(o for o in observed if o[2] == tip)
                return node, height, tip
            k_node, v27_height, v27_tip = majority(camp_tips['v27'])
            c_node, v26_height, v26_tip = majority(camp_tips['v26'])
            try:
                if v27_tip == v26_tip:
                    relation = 'same_tip'
                elif v26_height > v27_height and c_node.getblockhash(v27_height) == v27_tip:
                    relation = 'v26_ahead_on_v27_chain'
                elif v27_height > v26_height and k_node.getblockhash(v26_height) == v26_tip:
                    relation = 'v27_ahead_on_v26_chain'
                else:
                    relation = 'diverged'
                    fork_height = self._find_lca_height(k_node, [c_node])
                    v27_branch = v27_height - fork_height
                    v26_branch = v26_height - fork_height
            except Exception as e:
                self.log.debug(f"  [chain-state] relation check failed: {e}")
                relation = 'unknown'

            try:
                self._update_active_chain('v27', k_node, v27_height, v27_tip)
                self._update_active_chain('v26', c_node, v26_height, v26_tip)
                self._update_survival()
            except Exception as e:
                self.log.debug(f"  [chain-state] active-chain update failed: {e}")

        tx_state, tx_height = self._injected_tx_state()

        invalid_tips = None
        if camp_tips['v27']:
            try:
                invalid_tips = sum(1 for t in camp_tips['v27'][0][0].getchaintips()
                                   if t.get('status') == 'invalid')
                self.chain_state['max_invalid_tips'] = max(
                    self.chain_state['max_invalid_tips'], invalid_tips)
            except Exception:
                pass

        ts['timestamps'].append(elapsed)
        ts['relation'].append(relation)
        ts['v27_height'].append(v27_height)
        ts['v26_height'].append(v26_height)
        ts['v27_tip'].append(v27_tip)
        ts['v26_tip'].append(v26_tip)
        ts['fork_height'].append(fork_height)
        ts['v27_branch_len'].append(v27_branch)
        ts['v26_branch_len'].append(v26_branch)
        ts['v27_distinct_tips'].append(len({t for _, _, t in camp_tips['v27']}))
        ts['v26_distinct_tips'].append(len({t for _, _, t in camp_tips['v26']}))
        ts['injected_tx_state'].append(tx_state)
        ts['injected_tx_height'].append(tx_height)
        ts['v27_invalid_tips'].append(invalid_tips)
        survival = self.chain_state['survival']
        ts['v27_surviving'].append(survival['v27']['surviving'])
        ts['v26_surviving'].append(survival['v26']['surviving'])
        ts['v27_survival_ratio'].append(survival['v27']['window_ratio'])
        ts['v26_survival_ratio'].append(survival['v26']['window_ratio'])

        prev_relation = ts['relation'][-2] if len(ts['relation']) > 1 else None
        if relation != prev_relation:
            self.chain_state['relation_changes'].append(
                {'elapsed_s': elapsed, 'relation': relation, 'prev_relation': prev_relation})
            detail = (f" (LCA={fork_height}, Knots branch={v27_branch}, Core branch={v26_branch})"
                      if relation == 'diverged' else "")
            self.log.info(
                f"  [chain-state {elapsed:>5}s] tips: {prev_relation} -> {relation}{detail} | "
                f"Knots h={v27_height} Core h={v26_height} | injected tx: {tx_state}"
            )

        self.chain_state['final'] = {
            'elapsed_s': elapsed,
            'relation': relation,
            'v27_height': v27_height,
            'v26_height': v26_height,
            'v27_tip': v27_tip,
            'v26_tip': v26_tip,
            'fork_height': fork_height,
            'v27_branch_len': v27_branch,
            'v26_branch_len': v26_branch,
            'injected_tx_state': tx_state,
            'injected_tx_height': tx_height,
            'v27_invalid_tips': invalid_tips,
        }

    def build_partition_peer_lists(self):
        """
        Build lists of peer addresses for each partition.
        Used for dynamic partition switching - nodes can reconnect to a different partition.
        """
        self.log.info("\nBuilding partition peer lists for dynamic switching...")

        # Get addresses from nodes in each partition
        for node in self.v27_nodes:
            try:
                # Get the node's address that other nodes can connect to
                node_name = f"node-{node.index:04d}"
                # In warnet, nodes are addressable by their service name
                self.v27_peer_addresses.append(node_name)
                self.node_current_partition[node_name] = 'v27'
            except Exception as e:
                self.log.warning(f"  Could not get address for v27 node {node.index}: {e}")

        for node in self.v26_nodes:
            try:
                node_name = f"node-{node.index:04d}"
                self.v26_peer_addresses.append(node_name)
                self.node_current_partition[node_name] = 'v26'
            except Exception as e:
                self.log.warning(f"  Could not get address for v26 node {node.index}: {e}")

        self.log.info(f"  v27 peers: {len(self.v27_peer_addresses)} nodes")
        self.log.info(f"  v26 peers: {len(self.v26_peer_addresses)} nodes")

    def get_node_peers(self, node) -> list:
        """Get list of currently connected peer addresses for a node."""
        try:
            peer_info = node.getpeerinfo()
            return [p.get('addr', '').split(':')[0] for p in peer_info]
        except Exception as e:
            self.log.warning(f"  Could not get peers for node {node.index}: {e}")
            return []

    def _find_lca_height(self, node, dest_nodes: list) -> int:
        """
        Binary-search for the last common ancestor height between node's chain and dest_nodes'.

        Returns the LCA height, falling back to self.options.start_height if search fails.
        O(log N) RPC calls where N is the chain length difference.
        """
        fallback = getattr(self.options, 'start_height', 0)
        if not dest_nodes:
            return fallback
        dest_node = dest_nodes[0]
        try:
            node_height = node.getblockcount()
            dest_height = dest_node.getblockcount()
            lo = fallback
            hi = min(node_height, dest_height)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                try:
                    if node.getblockhash(mid) == dest_node.getblockhash(mid):
                        lo = mid
                    else:
                        hi = mid - 1
                except Exception:
                    hi = mid - 1
            return lo
        except Exception as e:
            self.log.warning(f"  LCA search failed ({e}), falling back to start_height={fallback}")
            return fallback

    def switch_node_partition(self, node, old_partition: str, new_partition: str, reason: str = "") -> bool:
        """
        Switch a node from one partition to another by changing P2P connections.

        Steps:
        1. Abandon old chain state (invalidateblock at fork point so old chain does not
           leak into the new island via P2P after addnode)
        2. Disconnect from old partition peers
        3. Connect to new partition peers
        4. Wait for sync to new chain
        5. Update tracking

        Args:
            node: The node to switch
            old_partition: Current partition ('v27' or 'v26')
            new_partition: Target partition ('v27' or 'v26')
            reason: Why the switch is happening (for logging)

        Returns:
            True if switch was successful
        """
        if old_partition == new_partition:
            return True  # No switch needed

        node_name = f"node-{node.index:04d}"
        self.log.info(f"\n  PARTITION SWITCH: {node_name} {old_partition} -> {new_partition}")
        if reason:
            self.log.info(f"    Reason: {reason}")

        old_peers = self.v27_peer_addresses if old_partition == 'v27' else self.v26_peer_addresses
        new_peers = self.v26_peer_addresses if new_partition == 'v26' else self.v27_peer_addresses

        try:
            # Step 1: Get current height before switch
            old_height = node.getblockcount()
            old_hash = node.getbestblockhash()

            # Step 1.5: Abandon the old partition's chain state so it does not propagate
            # into the new island when addnode fires.  Find the last block both chains
            # share (LCA) and invalidate the first block unique to this node's chain.
            # After invalidateblock the node reorgs to the LCA; the new island then
            # provides its own chain via P2P and the node adopts it.
            dest_nodes_list = self.v27_nodes if new_partition == 'v27' else self.v26_nodes
            lca_height = self._find_lca_height(node, dest_nodes_list)
            if lca_height < old_height:
                divergent_hash = node.getblockhash(lca_height + 1)
                try:
                    node.invalidateblock(divergent_hash)
                    self.log.info(f"    Chain abandoned: rolled back from height {old_height} to LCA={lca_height}")
                except Exception as e:
                    self.log.warning(f"    invalidateblock failed ({e}); chain state may leak")
            else:
                self.log.info(f"    No chain divergence detected at LCA={lca_height}, no rollback needed")

            # Step 2: Disconnect from old partition peers
            current_peers = self.get_node_peers(node)
            disconnected = 0
            for peer_addr in current_peers:
                # Check if this peer is in the old partition
                for old_peer in old_peers:
                    if old_peer in peer_addr:
                        try:
                            node.disconnectnode(peer_addr)
                            disconnected += 1
                        except Exception:
                            pass  # May already be disconnected
                        break

            self.log.info(f"    Disconnected from {disconnected} {old_partition} peers")

            # Step 3: Connect to new partition peers
            connected = 0
            # Connect to a subset of new peers (not all, to avoid overwhelming)
            peers_to_add = new_peers[:min(8, len(new_peers))]
            for peer_name in peers_to_add:
                if peer_name != node_name:  # Don't connect to self
                    try:
                        node.addnode(peer_name, "onetry")
                        connected += 1
                    except Exception as e:
                        self.log.warning(f"    Could not connect to {peer_name}: {e}")

            self.log.info(f"    Connected to {connected} {new_partition} peers")

            # Step 4: Wait briefly for connection establishment
            import time
            time.sleep(2)

            # Step 5: Check if we synced to new chain
            new_height = node.getblockcount()
            new_hash = node.getbestblockhash()

            if new_hash != old_hash:
                self.log.info(f"    Chain changed: height {old_height} -> {new_height}")
                self.log.info(f"    Old tip: {old_hash[:16]}...")
                self.log.info(f"    New tip: {new_hash[:16]}...")

            # Step 6: Update tracking
            self.node_current_partition[node_name] = new_partition

            # Move node between partition lists
            if old_partition == 'v27' and node in self.v27_nodes:
                self.v27_nodes.remove(node)
                self.v26_nodes.append(node)
            elif old_partition == 'v26' and node in self.v26_nodes:
                self.v26_nodes.remove(node)
                self.v27_nodes.append(node)

            # Record the switch
            self.partition_switch_history.append({
                'node': node_name,
                'from': old_partition,
                'to': new_partition,
                'reason': reason,
                'old_height': old_height,
                'new_height': new_height,
                'timestamp': time.time()
            })

            self.log.info(f"    Switch complete: {node_name} is now on {new_partition}")
            return True

        except Exception as e:
            self.log.error(f"    Switch failed for {node_name}: {e}")
            return False

    def reunite_forks(self, force: bool = False) -> dict:
        """
        Reconnect the two fork partitions and wait for the losing fork to reorg
        to the heavier chain.

        The winning fork is determined by cumulative chainwork (difficulty oracle)
        or by block count if difficulty tracking is disabled.

        Steps:
        1. Determine the winning fork by chainwork / block count
        2. Connect each losing-fork node to several winning-fork peers via addnode
        3. Poll until all losing-fork nodes converge to the winning tip (or timeout)
        4. Report reorg depth, orphaned blocks, and convergence metrics

        Args:
            force: If True, run reunion even if --enable-reunion flag is not set.
                   Used by UASF expiry to trigger reunion regardless of flag.

        Returns:
            dict with reunion metrics (included in the results export)
        """
        if not force and not self.options.enable_reunion:
            return {'enabled': False}

        self.log.info(f"\n{'='*70}")
        self.log.info("FORK REUNION")
        self.log.info(f"{'='*70}")

        # Determine winning and losing forks
        if self.difficulty_oracle:
            winner_id, winner_cw, loser_cw = self.difficulty_oracle.get_winning_fork()
        else:
            winner_id = 'v27' if self.blocks_mined['v27'] >= self.blocks_mined['v26'] else 'v26'
            winner_cw = float(self.blocks_mined[winner_id])
            loser_cw = float(self.blocks_mined['v26' if winner_id == 'v27' else 'v27'])

        loser_id = 'v26' if winner_id == 'v27' else 'v27'
        winning_nodes = self.v27_nodes if winner_id == 'v27' else self.v26_nodes
        losing_nodes = self.v26_nodes if winner_id == 'v27' else self.v27_nodes
        winning_peers = self.v27_peer_addresses if winner_id == 'v27' else self.v26_peer_addresses

        if not winning_nodes or not losing_nodes:
            self.log.warning("  Cannot reunite: one partition has no nodes")
            return {'enabled': True, 'skipped': True, 'reason': 'empty_partition'}

        # Snapshot pre-reorg state
        try:
            winning_tip_hash = winning_nodes[0].getbestblockhash()
            winning_tip_height = winning_nodes[0].getblockcount()
        except Exception as e:
            self.log.error(f"  Cannot read winning fork tip: {e}")
            return {'enabled': True, 'skipped': True, 'reason': 'rpc_error'}

        pre_reorg_heights = {}
        for node in losing_nodes:
            node_name = f"node-{node.index:04d}"
            try:
                pre_reorg_heights[node_name] = node.getblockcount()
            except Exception as e:
                self.log.warning(f"  Could not get height for {node_name}: {e}")
                pre_reorg_heights[node_name] = 0

        losing_tip_height = max(pre_reorg_heights.values(), default=0)
        self.log.info(f"  Winning fork: {winner_id}  height={winning_tip_height}  chainwork={winner_cw:.4f}")
        self.log.info(f"  Losing fork:  {loser_id}  height={losing_tip_height}  chainwork={loser_cw:.4f}")
        self.log.info(f"  Connecting {len(losing_nodes)} {loser_id} nodes to {winner_id} peers...")

        # Connect each losing-fork node to up to 4 winning-fork peers
        peers_to_add = winning_peers[:min(4, len(winning_peers))]
        connected_count = 0
        for node in losing_nodes:
            node_name = f"node-{node.index:04d}"
            for peer_name in peers_to_add:
                if peer_name != node_name:
                    try:
                        node.addnode(peer_name, "onetry")
                        connected_count += 1
                    except Exception as e:
                        self.log.debug(f"  Could not connect {node_name} -> {peer_name}: {e}")

        self.log.info(f"  Added {connected_count} cross-partition connections")
        self.log.info(f"  Waiting up to {self.options.reunion_timeout}s for reorg convergence...")

        # Poll for convergence
        poll_interval = 2.0
        reunion_start = time()
        converged_nodes = set()
        wait_elapsed = 0.0

        while True:
            wait_elapsed = time() - reunion_start
            if wait_elapsed >= self.options.reunion_timeout:
                break

            # Refresh winning tip in case mining is still active
            try:
                winning_tip_hash = winning_nodes[0].getbestblockhash()
                winning_tip_height = winning_nodes[0].getblockcount()
            except Exception:
                pass

            for node in losing_nodes:
                node_name = f"node-{node.index:04d}"
                if node_name in converged_nodes:
                    continue
                try:
                    best_hash = node.getbestblockhash()
                    if best_hash == winning_tip_hash:
                        post_h = node.getblockcount()
                        self.log.info(f"  {node_name} converged at height {post_h} ({wait_elapsed:.1f}s)")
                        converged_nodes.add(node_name)
                except Exception as e:
                    self.log.debug(f"  Polling {node_name}: {e}")

            if len(converged_nodes) >= len(losing_nodes):
                break

            sleep(poll_interval)

        # Final heights after waiting
        post_reorg_heights = {}
        for node in losing_nodes:
            node_name = f"node-{node.index:04d}"
            try:
                post_reorg_heights[node_name] = node.getblockcount()
            except Exception:
                post_reorg_heights[node_name] = pre_reorg_heights.get(node_name, 0)

        # Metrics
        fork_point_height = self.options.start_height
        losing_fork_depth = losing_tip_height - fork_point_height
        orphaned_blocks = self.blocks_mined[loser_id]
        nodes_converged = len(converged_nodes)
        nodes_total = len(losing_nodes)
        timed_out = nodes_converged < nodes_total

        self.log.info(f"\n  REUNION RESULTS:")
        self.log.info(f"  Winner:          {winner_id} (height {winning_tip_height})")
        self.log.info(f"  Reorg depth:     {losing_fork_depth} blocks ({loser_id} fork above fork point)")
        self.log.info(f"  Orphaned blocks: {orphaned_blocks}")
        self.log.info(f"  Nodes converged: {nodes_converged}/{nodes_total} in {wait_elapsed:.1f}s")
        if timed_out:
            self.log.warning(f"  WARNING: {nodes_total - nodes_converged} nodes did not converge within timeout")

        return {
            'enabled': True,
            'winner': winner_id,
            'loser': loser_id,
            'winner_chainwork': winner_cw,
            'loser_chainwork': loser_cw,
            'winning_tip_height': winning_tip_height,
            'winning_tip_hash': winning_tip_hash,
            'fork_point_height': fork_point_height,
            'losing_fork_depth': losing_fork_depth,
            'orphaned_blocks': orphaned_blocks,
            'nodes_converged': nodes_converged,
            'nodes_total': nodes_total,
            'timed_out': timed_out,
            'wait_elapsed_seconds': round(wait_elapsed, 1),
            'pre_reorg_heights': pre_reorg_heights,
            'post_reorg_heights': post_reorg_heights,
        }

    def handle_uasf_expiry(self, elapsed: float, current_time: float):
        """
        Handle UASF expiration.

        When the time-limited UASF expires:
        1. Log the expiry event with full state snapshot
        2. Change v27 nodes to accept v26 blocks (accepts_foreign_blocks=True)
        3. Based on --uasf-expiry-action:
           - 'reunion': Reconnect partitions and let heavier chain win
           - 'accept': v27 accepts v26 blocks but partitions stay separate
           - 'continue': Just log and continue (no behavior change)

        This simulates miners/nodes who committed to running UASF for a limited
        period and then "give up" if the soft fork hasn't activated.
        """
        self.log.info(f"\n{'='*70}")
        self.log.info(f"UASF EXPIRED at {elapsed}s ({elapsed/3600:.2f} hours)")
        self.log.info(f"{'='*70}")

        # Snapshot state at expiry
        v27_blocks = self.blocks_mined['v27']
        v26_blocks = self.blocks_mined['v26']
        v27_price = self.price_oracle.get_price('v27') if self.price_oracle else 0
        v26_price = self.price_oracle.get_price('v26') if self.price_oracle else 0

        if self.difficulty_oracle:
            v27_chainwork = self.difficulty_oracle.get_cumulative_chainwork('v27')
            v26_chainwork = self.difficulty_oracle.get_cumulative_chainwork('v26')
            v27_difficulty = self.difficulty_oracle.forks['v27'].current_difficulty
            v26_difficulty = self.difficulty_oracle.forks['v26'].current_difficulty
        else:
            v27_chainwork = float(v27_blocks)
            v26_chainwork = float(v26_blocks)
            v27_difficulty = 1.0
            v26_difficulty = 1.0

        # Determine winning fork at expiry
        winning_fork = 'v27' if v27_chainwork >= v26_chainwork else 'v26'
        losing_fork = 'v26' if winning_fork == 'v27' else 'v27'

        self.uasf_expiry_data = {
            'expiry_elapsed_seconds': elapsed,
            'expiry_timestamp': current_time,
            'uasf_duration_seconds': self.options.uasf_duration,
            'expiry_action': self.options.uasf_expiry_action,
            'state_at_expiry': {
                'v27_blocks': v27_blocks,
                'v26_blocks': v26_blocks,
                'v27_chainwork': v27_chainwork,
                'v26_chainwork': v26_chainwork,
                'v27_difficulty': v27_difficulty,
                'v26_difficulty': v26_difficulty,
                'v27_price': v27_price,
                'v26_price': v26_price,
                'v27_hashrate': self.current_v27_hashrate,
                'v26_hashrate': self.current_v26_hashrate,
                'v27_economic': self.current_v27_economic,
                'v26_economic': self.current_v26_economic,
                'winning_fork_at_expiry': winning_fork,
            },
            'reunion_triggered': False,
            'reunion_results': None,
        }

        self.log.info(f"  State at expiry:")
        self.log.info(f"    v27: {v27_blocks} blocks, chainwork={v27_chainwork:.2f}, price=${v27_price:,.0f}")
        self.log.info(f"    v26: {v26_blocks} blocks, chainwork={v26_chainwork:.2f}, price=${v26_price:,.0f}")
        self.log.info(f"    Hashrate: v27={self.current_v27_hashrate:.1f}%, v26={self.current_v26_hashrate:.1f}%")
        self.log.info(f"    Winning fork at expiry: {winning_fork}")

        # Mark UASF as expired
        self.uasf_expired = True
        self.uasf_active = False

        # Handle expiry action
        if self.options.uasf_expiry_action == 'reunion':
            self.log.info(f"\n  Expiry action: REUNION - reconnecting partitions...")

            # Change v27 nodes to accept v26 blocks
            self._enable_v27_foreign_acceptance()

            # Trigger reunion (force=True to bypass --enable-reunion check)
            reunion_results = self.reunite_forks(force=True)
            self.uasf_expiry_data['reunion_triggered'] = True
            self.uasf_expiry_data['reunion_results'] = reunion_results

            if reunion_results.get('timed_out'):
                self.log.warning(f"  Reunion timed out - some nodes may not have converged")
            elif reunion_results.get('enabled'):
                # Successful reunion - all hashrate now goes to winning fork
                self.reunion_completed = True
                self.reunion_winner = reunion_results.get('winner')

                if self.reunion_winner == 'v27':
                    self.current_v27_hashrate = 100.0
                    self.current_v26_hashrate = 0.0
                else:
                    self.current_v27_hashrate = 0.0
                    self.current_v26_hashrate = 100.0

                # Update all pool allocations to winning fork
                if self.pool_strategy:
                    for pool_id in self.pool_strategy.current_allocation:
                        self.pool_strategy.current_allocation[pool_id] = self.reunion_winner
                        # Also update pool's current_fork tracking
                        if pool_id in self.pool_strategy.pools:
                            self.pool_strategy.pools[pool_id].current_fork = self.reunion_winner

                self.log.info(f"  Post-reunion hashrate: {self.reunion_winner}=100%, other=0%")
                self.log.info(f"  All pools now mining on {self.reunion_winner}")

        elif self.options.uasf_expiry_action == 'accept':
            self.log.info(f"\n  Expiry action: ACCEPT - v27 nodes now accept v26 blocks")
            self.log.info(f"  (Partitions remain separate, but cross-chain blocks are now valid)")

            # Change v27 nodes to accept v26 blocks
            self._enable_v27_foreign_acceptance()

        else:  # 'continue'
            self.log.info(f"\n  Expiry action: CONTINUE - logging expiry only, no behavior change")
            self.log.info(f"  (v27 nodes continue to reject v26 blocks)")

        # Calculate opportunity cost for UASF supporters
        if winning_fork == 'v26':
            # v27 lost - calculate cost of supporting losing fork
            orphaned_blocks = v27_blocks
            wasted_chainwork = v27_chainwork
            self.log.info(f"\n  UASF FAILED - v27 chain will be orphaned")
            self.log.info(f"    Orphaned blocks: {orphaned_blocks}")
            self.log.info(f"    Wasted chainwork: {wasted_chainwork:.2f}")

            self.uasf_expiry_data['uasf_outcome'] = 'failed'
            self.uasf_expiry_data['orphaned_blocks'] = orphaned_blocks
            self.uasf_expiry_data['wasted_chainwork'] = wasted_chainwork
        else:
            # v27 won - UASF was successful (though expired, the chain is still dominant)
            self.log.info(f"\n  UASF SUCCEEDED - v27 chain is dominant")
            self.log.info(f"    v27 chainwork lead: {v27_chainwork - v26_chainwork:.2f}")

            self.uasf_expiry_data['uasf_outcome'] = 'succeeded'
            self.uasf_expiry_data['chainwork_lead'] = v27_chainwork - v26_chainwork

        self.log.info(f"{'='*70}\n")

    def _enable_v27_foreign_acceptance(self):
        """
        Change v27 nodes to accept v26 blocks (accepts_foreign_blocks=True).

        This simulates UASF nodes "giving up" and accepting the old rules again.
        After this, v27 nodes will accept blocks from v26 and can reorg to
        the longer chain if v26 has more chainwork.
        """
        self.log.info(f"  Changing v27 nodes to accept v26 blocks...")

        changed_count = 0
        for node in self.v27_nodes:
            node_name = f"node-{node.index:04d}"
            metadata = self.node_metadata.get(node_name, {})

            # Update metadata to accept foreign blocks
            old_value = metadata.get('accepts_foreign_blocks', False)
            metadata['accepts_foreign_blocks'] = True
            self.node_metadata[node_name] = metadata

            if not old_value:
                changed_count += 1
                self.log.debug(f"    {node_name}: accepts_foreign_blocks = True")

        # Add v27 nodes to foreign_accepting_nodes list
        for node in self.v27_nodes:
            if node not in self.foreign_accepting_nodes:
                self.foreign_accepting_nodes.append(node)

        self.log.info(f"  Changed {changed_count} v27 nodes to accept foreign blocks")

    # ------------------------------------------------------------------
    # In-place switching (--inplace-switching)
    # ------------------------------------------------------------------

    RDTS_VBPARAMS = 'vbparams=reduced_data:-1:9223372036854775807'

    def _exec_on_tank(self, node, shell_cmd: str) -> str:
        """Run a shell command in a tank's bitcoind container (needs commander
        pods/exec RBAC). Imported lazily for the same reason as in
        check_rdts_rejection."""
        import commander as _commander_module
        from kubernetes.stream import stream as k8s_stream
        return k8s_stream(
            _commander_module.sclient.connect_get_namespaced_pod_exec,
            name=node.tank,
            container="bitcoincore",
            namespace=_commander_module.NAMESPACE,
            command=["sh", "-c", shell_cmd],
            stderr=True, stdin=False, stdout=True, tty=False,
        ) or ""

    def _desired_camps(self) -> dict:
        """node -> (camp, role) the pool / economic strategy currently puts
        that node's owner on. Other nodes (relays) keep their starting camp."""
        desired = {}
        for node in self.v27_nodes + self.v26_nodes:
            node_name = f"node-{node.index:04d}"
            pool_id = self.get_node_pool_id(node)
            if pool_id and self.pool_strategy and pool_id in self.pool_strategy.current_allocation:
                desired[node] = (self.pool_strategy.current_allocation[pool_id], f"pool {pool_id}")
            elif self.economic_strategy and self.economic_strategy.current_allocation.get(node_name):
                node_type = self.node_metadata.get(node_name, {}).get('node_type', 'economic')
                desired[node] = (self.economic_strategy.current_allocation[node_name], node_type)
        return desired

    def reconcile_node_modes(self, elapsed: int, trigger: str):
        """Switch every node whose enforced rules differ from its owner's
        current fork choice (no-op unless --inplace-switching)."""
        if not self.options.inplace_switching:
            return
        pending = []
        for node, (camp, role) in self._desired_camps().items():
            current = 'v27' if node in self.v27_nodes else 'v26'
            if camp in ('v27', 'v26') and camp != current:
                pending.append((node, current, camp, role))
        if pending:
            self.switch_nodes_inplace(pending, elapsed, trigger)

    def switch_nodes_inplace(self, pending: list, elapsed: int, trigger: str):
        """
        Change what each node enforces, as a real operator changing software
        on an existing datadir would, for a batch of (node, old, new, role):
          1. rewrite <datadir>/switch.conf (RDTS vbparams on for v27, off for v26)
          2. RPC stop; restartPolicy Always relaunches bitcoind in the same pod,
             so peers (addnode config) and chain data (emptyDir) are kept
          3. wait until the node answers with the new RDTS status
          4. reconcile the chain, since old blocks are not re-validated on
             restart: entering v27 -> invalidateblock the violating blocks;
             entering v26 -> reconsiderblock every invalid tip (the invalid
             flags persist across restart)
        All nodes in the batch restart concurrently. Verified in Docker:
        tools/knots_switch_test/, docs/knots_mesh_fork_sweep_plan.md.
        """
        import time as _time
        self.log.info(f"\n  IN-PLACE SWITCH ({trigger}, {elapsed}s): {len(pending)} node(s): "
                      f"{[f'node-{n.index:04d}:{o}->{c}' for n, o, c, _ in pending]}")

        stopping = []
        for node, old, new, role in pending:
            node_name = f"node-{node.index:04d}"
            event = {'node': node_name, 'role': role, 'from': old, 'to': new,
                     'trigger': trigger, 'elapsed_s': elapsed, 'success': False}
            try:
                event['height_before'] = node.getblockcount()
                event['tip_before'] = node.getbestblockhash()
                body = '[regtest]\\n' + (self.RDTS_VBPARAMS + '\\n' if new == 'v27' else '')
                out = self._exec_on_tank(
                    node, f"printf '{body}' > /root/.bitcoin/switch.conf && cat /root/.bitcoin/switch.conf")
                if (self.RDTS_VBPARAMS in out) != (new == 'v27'):
                    raise RuntimeError(f"switch.conf not written as expected: {out!r}")
                node.stop()
                stopping.append((node, event, _time.time()))
            except Exception as e:
                event['error'] = f"stop phase: {e}"
                self.log.error(f"    {node_name}: switch aborted before restart: {e}")
                self.inplace_switches.append(event)

        waiting = list(stopping)
        deadline = _time.time() + self.options.switch_restart_timeout
        back = []
        while waiting and _time.time() < deadline:
            _time.sleep(2)
            for item in list(waiting):
                node, event, t_stop = item
                try:
                    if self._rdts_active(node) == (event['to'] == 'v27'):
                        event['downtime_s'] = round(_time.time() - t_stop, 1)
                        back.append(item)
                        waiting.remove(item)
                except Exception:
                    pass  # still stopping / restarting / warming up
        for node, event, _ in waiting:
            event['error'] = f"did not come back with the new mode within {self.options.switch_restart_timeout}s"
            self.log.error(f"    {event['node']}: {event['error']}")
            self.inplace_switches.append(event)

        for node, event, _ in back:
            node_name = event['node']
            try:
                if event['to'] == 'v27':
                    invalidated = 0
                    for block_hash in self._violating_blocks:
                        try:
                            node.invalidateblock(block_hash)
                            invalidated += 1
                        except Exception:
                            pass  # block unknown to this node
                    event['invalidated'] = invalidated
                else:
                    reconsidered = 0
                    for tip in node.getchaintips():
                        if tip.get('status') == 'invalid':
                            node.reconsiderblock(tip['hash'])
                            reconsidered += 1
                    event['reconsidered'] = reconsidered
                if "miner" not in node.listwallets():
                    try:
                        node.loadwallet("miner")
                    except Exception:
                        pass  # node never had a miner wallet
                event['height_after'] = node.getblockcount()
                event['tip_after'] = node.getbestblockhash()
                event['success'] = True
            except Exception as e:
                event['error'] = f"reconcile phase: {e}"
                self.log.error(f"    {node_name}: chain reconcile failed: {e}")

            # The node now enforces the new rules either way; track it there.
            (self.v27_nodes if event['from'] == 'v27' else self.v26_nodes).remove(node)
            (self.v27_nodes if event['to'] == 'v27' else self.v26_nodes).append(node)
            self.node_current_partition[node_name] = event['to']
            self.inplace_switches.append(event)
            self.log.info(
                f"    {node_name} ({event['role']}): {event['from']} -> {event['to']} "
                f"in {event['downtime_s']}s, height {event['height_before']} -> "
                f"{event.get('height_after')}"
                + (f", invalidated {event['invalidated']}" if 'invalidated' in event else "")
                + (f", reconsidered {event['reconsidered']}" if 'reconsidered' in event else ""))

        if back and self.pool_strategy:
            self.pool_nodes_v27.clear()
            self.pool_nodes_v26.clear()
            self.build_pool_node_mapping(verbose=False)

    def evaluate_economic_node_switches(self, elapsed: float):
        """
        Evaluate whether economic/user nodes should switch partitions based on
        economic conditions (price, fees, ideology).

        Called periodically during simulation to allow dynamic partition changes.
        """
        if not self.economic_strategy:
            return

        switches = []

        # Get current prices and conditions
        v27_price = self.price_oracle.get_price('v27') if self.price_oracle else 60000
        v26_price = self.price_oracle.get_price('v26') if self.price_oracle else 60000
        price_ratio = v27_price / v26_price if v26_price > 0 else 1.0

        # Evaluate each economic node
        for node in list(self.v27_nodes) + list(self.v26_nodes):
            node_name = f"node-{node.index:04d}"
            metadata = self.node_metadata.get(node_name, {})

            # Skip pool nodes - they have their own switching logic
            if metadata.get('node_type') == 'mining_pool':
                continue

            # Only evaluate economic and user nodes
            node_type = metadata.get('node_type', '')
            if node_type not in ['economic', 'user']:
                continue

            current_partition = self.node_current_partition.get(node_name, 'v27')
            fork_preference = metadata.get('fork_preference', 'neutral')
            ideology_strength = metadata.get('ideology_strength', 0.0)
            switching_threshold = metadata.get('switching_threshold', 0.10)
            inertia = metadata.get('inertia', 0.05)

            # Determine if node should switch
            should_switch = False
            reason = ""

            # Ideology scales the effective switching threshold.
            # Low ideology (0.0) → switches at base threshold (purely rational).
            # High ideology (1.0) → needs 3× the base threshold to switch.
            # This replaces the old hard cutoffs (< 0.3 / > 0.7) which created
            # a dead zone where nodes with ideology 0.3–0.7 could never switch.
            effective_threshold = switching_threshold * (1 + ideology_strength * 2.0)

            if current_partition == 'v27':
                # Ideological pull: strong preference for v26 overrides price
                if fork_preference == 'v26' and ideology_strength > 0.5:
                    should_switch = True
                    reason = f"ideological preference for v26 (strength={ideology_strength:.2f})"
                # Rational: v26 price advantage exceeds ideology-adjusted threshold
                elif price_ratio < (1 - effective_threshold):
                    should_switch = True
                    reason = (f"economic: v27/v26 ratio {price_ratio:.3f} below "
                              f"threshold {1 - effective_threshold:.3f} "
                              f"(ideology={ideology_strength:.2f})")

            else:  # current_partition == 'v26'
                # Ideological pull: strong preference for v27 overrides price
                if fork_preference == 'v27' and ideology_strength > 0.5:
                    should_switch = True
                    reason = f"ideological preference for v27 (strength={ideology_strength:.2f})"
                # Rational: v27 price advantage exceeds ideology-adjusted threshold
                elif price_ratio > (1 + effective_threshold):
                    should_switch = True
                    reason = (f"economic: v27/v26 ratio {price_ratio:.3f} above "
                              f"threshold {1 + effective_threshold:.3f} "
                              f"(ideology={ideology_strength:.2f})")

            # Apply inertia - random chance to delay switch
            if should_switch:
                import random
                if random.random() < inertia:
                    should_switch = False
                    self.log.debug(f"  {node_name} switch delayed by inertia")

            if should_switch:
                new_partition = 'v26' if current_partition == 'v27' else 'v27'
                switches.append((node, current_partition, new_partition, reason))

        # Execute switches. Gated behind --enable-manual-repartition (default
        # False): on a real, always-connected mesh there's nothing to
        # manually rewire — real consensus validation, not addnode/
        # disconnectnode calls, determines which blocks propagate where. The
        # decision logic above (which fork a node *would* prefer) still runs
        # and logs either way; only the manual peer rewiring is gated.
        if self.options.enable_manual_repartition:
            for node, old_part, new_part, reason in switches:
                self.switch_node_partition(node, old_part, new_part, reason)
        elif switches:
            self.log.info(
                f"  {len(switches)} node(s) would switch partition "
                f"(--enable-manual-repartition not set, no manual rewiring performed): "
                f"{[f'{n.index}:{o}->{p}' for n, o, p, _ in switches]}"
            )

    def build_pool_node_mapping(self, verbose: bool = True):
        """
        Build mapping from pool IDs to nodes in each partition.

        Architecture:
        - Each pool has ONE node per partition (if present)
        - Same entity_id appears in both partitions (paired nodes)
        - Pool decides which fork to mine → uses corresponding node
        """
        if verbose:
            self.log.info("\nBuilding pool-to-node mappings...")

        # Track unmapped nodes
        v27_unmapped = 0
        v26_unmapped = 0

        # Read node metadata to extract pool assignments
        for node in self.v27_nodes:
            pool_id = self.get_node_pool_id(node)
            if pool_id:
                if pool_id not in self.pool_nodes_v27:
                    self.pool_nodes_v27[pool_id] = []
                self.pool_nodes_v27[pool_id].append(node)
            else:
                v27_unmapped += 1

        for node in self.v26_nodes:
            pool_id = self.get_node_pool_id(node)
            if pool_id:
                if pool_id not in self.pool_nodes_v26:
                    self.pool_nodes_v26[pool_id] = []
                self.pool_nodes_v26[pool_id].append(node)
            else:
                v26_unmapped += 1

        if not verbose:  # in-place switch rebuild; the switch itself is logged
            return

        # Log pool distribution
        self.log.info("\nPool node distribution (1 node per partition per pool):")

        # Get all unique pool IDs from both partitions
        all_pools = set(self.pool_nodes_v27.keys()) | set(self.pool_nodes_v26.keys())

        for pool_id in sorted(all_pools):
            v27_nodes = self.pool_nodes_v27.get(pool_id, [])
            v26_nodes = self.pool_nodes_v26.get(pool_id, [])

            v27_str = f"node-{v27_nodes[0].index:04d}" if v27_nodes else "none"
            v26_str = f"node-{v26_nodes[0].index:04d}" if v26_nodes else "none"

            # Warn if pool has multiple nodes in one partition (unexpected)
            if len(v27_nodes) > 1:
                self.log.warning(f"  {pool_id:15s}: MULTIPLE v27 nodes ({len(v27_nodes)}) - expected 1")
            if len(v26_nodes) > 1:
                self.log.warning(f"  {pool_id:15s}: MULTIPLE v26 nodes ({len(v26_nodes)}) - expected 1")

            self.log.info(f"  {pool_id:15s}: v27={v27_str:12s} v26={v26_str:12s}")

        if v27_unmapped > 0:
            self.log.info(f"\n  {v27_unmapped} v27 nodes without pool assignment (economic/user nodes)")

        if v26_unmapped > 0:
            self.log.info(f"  {v26_unmapped} v26 nodes without pool assignment (economic/user nodes)")

    def get_node_pool_id(self, node) -> Optional[str]:
        """Extract pool ID from node metadata (read from network.yaml)"""
        try:
            # Get node name from tank_index
            # Warnet nodes are typically named "node-XXXX"
            node_name = f"node-{node.index:04d}"

            # Look up metadata from network.yaml
            if node_name in self.node_metadata:
                metadata = self.node_metadata[node_name]
                entity_id = metadata.get('entity_id', None)

                if entity_id and entity_id.startswith('pool-'):
                    # Convert pool-antpool -> antpool
                    pool_id = entity_id.replace('pool-', '')
                    return pool_id

            return None

        except Exception as e:
            self.log.debug(f"Could not extract pool ID from node {node.index}: {e}")
            return None

    def select_mining_node(self) -> Tuple[Optional[object], Optional[str]]:
        """
        Select a mining node based on pool decisions and hashrate weights.

        Architecture (Simple Binary Allocation):
        1. Each pool chooses ONE fork to mine ('v27' or 'v26')
        2. Pool's full hashrate goes to chosen fork
        3. Weighted random selection based on hashrate
        4. Selected pool's node on chosen partition mines the block
        """
        if not self.pool_strategy:
            # Fallback: random selection from aggregate hashrate
            rand_val = random() * 100.0
            if rand_val < self.current_v27_hashrate:
                partition = 'v27'
                nodes = self.v27_nodes
            else:
                partition = 'v26'
                nodes = self.v26_nodes

            if not nodes:
                return None, None
            return choices(nodes, k=1)[0], partition

        # Pool-based selection with binary allocation
        # Build weighted list of (pool_id, partition) based on pool decisions
        pool_choices = []
        pool_weights = []

        for pool_id, allocation in self.pool_strategy.current_allocation.items():
            pool = self.pool_strategy.pools[pool_id]
            hashrate_weight = pool.hashrate_pct

            # Binary allocation: pool chooses one fork
            chosen_fork = allocation  # 'v27' or 'v26'

            # Check if pool has a node in the chosen partition
            if chosen_fork == 'v27':
                if pool_id in self.pool_nodes_v27 and self.pool_nodes_v27[pool_id]:
                    pool_choices.append((pool_id, 'v27'))
                    pool_weights.append(hashrate_weight)
                else:
                    self.log.debug(f"Pool {pool_id} chose v27 but has no v27 node")
            elif chosen_fork == 'v26':
                if pool_id in self.pool_nodes_v26 and self.pool_nodes_v26[pool_id]:
                    pool_choices.append((pool_id, 'v26'))
                    pool_weights.append(hashrate_weight)
                else:
                    self.log.debug(f"Pool {pool_id} chose v26 but has no v26 node")

        if not pool_choices:
            # No pool nodes mapped, fallback to random selection based on hashrate
            rand_val = random() * 100.0
            if rand_val < self.current_v27_hashrate:
                partition = 'v27'
                nodes = self.v27_nodes
            else:
                partition = 'v26'
                nodes = self.v26_nodes

            if not nodes:
                return None, None
            return choices(nodes, k=1)[0], partition

        # Weighted random selection by hashrate
        selected_pool_id, partition = choices(pool_choices, weights=pool_weights, k=1)[0]

        # Get the pool's node on the chosen partition (should be exactly 1 node)
        if partition == 'v27':
            nodes = self.pool_nodes_v27.get(selected_pool_id, [])
        else:
            nodes = self.pool_nodes_v26.get(selected_pool_id, [])

        if not nodes:
            self.log.warning(f"No nodes for pool {selected_pool_id} in {partition}")
            return None, None

        # Return the pool's node (first/only node in list)
        selected_node = nodes[0]
        return selected_node, partition

    def _select_miner_for_fork(self, fork_id: str) -> Optional[object]:
        """
        Select a mining node for a specific fork (used in difficulty mode).

        In difficulty mode, we already know WHICH fork gets a block. This method
        selects which pool/node mines it, weighted by hashrate of pools AND solo
        miners allocated to that fork.

        Args:
            fork_id: 'v27' or 'v26'

        Returns:
            A node object to mine on, or None if no node available
        """
        nodes = self.v27_nodes if fork_id == 'v27' else self.v26_nodes
        if not nodes:
            return None

        if not self.pool_strategy:
            # No pool strategy: random node from partition
            return choices(nodes, k=1)[0]

        # Build weighted list of pools allocated to this fork
        miner_choices = []
        miner_weights = []

        # Add pools
        for pool_id, allocation in self.pool_strategy.current_allocation.items():
            if allocation != fork_id:
                continue

            pool = self.pool_strategy.pools[pool_id]
            pool_node_map = self.pool_nodes_v27 if fork_id == 'v27' else self.pool_nodes_v26

            if pool_id in pool_node_map and pool_node_map[pool_id]:
                miner_choices.append(pool_node_map[pool_id][0])
                miner_weights.append(pool.hashrate_pct)

        # Add solo miners (user/economic nodes with hashrate)
        if self.economic_strategy:
            solo_miners = self.economic_strategy.get_solo_miners()
            for node_id, miner_fork, hashrate in solo_miners:
                if miner_fork != fork_id or hashrate <= 0:
                    continue

                # Find the actual node object by node_id
                node_obj = self._get_node_by_id(node_id, fork_id)
                if node_obj:
                    miner_choices.append(node_obj)
                    miner_weights.append(hashrate)

        if not miner_choices:
            # Fallback: random node from partition
            return choices(nodes, k=1)[0]

        return choices(miner_choices, weights=miner_weights, k=1)[0]

    def _get_node_by_id(self, node_id: str, fork_id: str) -> Optional[object]:
        """
        Get a node object by its node_id string.

        Args:
            node_id: Node identifier (e.g., "node-0008")
            fork_id: Which fork partition to look in ('v27' or 'v26')

        Returns:
            Node object or None if not found
        """
        nodes = self.v27_nodes if fork_id == 'v27' else self.v26_nodes

        for node in nodes:
            # Node names are typically "node-XXXX" format
            node_name = f"node-{node.index:04d}"
            if node_name == node_id:
                return node

        return None

    def capture_time_series_snapshot(self, elapsed: int):
        """
        Capture a snapshot of current state for time series charting.

        Args:
            elapsed: Seconds since simulation start
        """
        # Compute rolling block time before appending current values
        if len(self.time_series['timestamps']) > 0:
            delta_t = elapsed - self.time_series['timestamps'][-1]
            delta_v27 = self.blocks_mined['v27'] - self.time_series['v27_blocks'][-1]
            delta_v26 = self.blocks_mined['v26'] - self.time_series['v26_blocks'][-1]
            v27_block_time = delta_t / delta_v27 if delta_v27 > 0 else None
            v26_block_time = delta_t / delta_v26 if delta_v26 > 0 else None
        else:
            v27_block_time = None  # no previous snapshot to compare against
            v26_block_time = None

        self.time_series['timestamps'].append(elapsed)
        self.time_series['v27_price'].append(self.price_oracle.get_price('v27'))
        self.time_series['v26_price'].append(self.price_oracle.get_price('v26'))
        self.time_series['v27_hashrate'].append(self.current_v27_hashrate)
        self.time_series['v26_hashrate'].append(self.current_v26_hashrate)
        self.time_series['v27_economic'].append(self.current_v27_economic)
        self.time_series['v26_economic'].append(self.current_v26_economic)
        self.time_series['v27_blocks'].append(self.blocks_mined['v27'])
        self.time_series['v26_blocks'].append(self.blocks_mined['v26'])

        if self.difficulty_oracle:
            v27_state = self.difficulty_oracle.forks.get('v27')
            v26_state = self.difficulty_oracle.forks.get('v26')
            self.time_series['v27_difficulty'].append(
                v27_state.current_difficulty if v27_state else 1.0)
            self.time_series['v26_difficulty'].append(
                v26_state.current_difficulty if v26_state else 1.0)
            self.time_series['v27_chainwork'].append(
                v27_state.cumulative_chainwork if v27_state else 0.0)
            self.time_series['v26_chainwork'].append(
                v26_state.cumulative_chainwork if v26_state else 0.0)
        else:
            self.time_series['v27_difficulty'].append(1.0)
            self.time_series['v26_difficulty'].append(1.0)
            self.time_series['v27_chainwork'].append(float(self.blocks_mined['v27']))
            self.time_series['v26_chainwork'].append(float(self.blocks_mined['v26']))

        # Fee market metrics
        if self.fee_oracle:
            # Fee rates
            self.time_series['v27_fee_rate'].append(self.fee_oracle.get_fee('v27'))
            self.time_series['v26_fee_rate'].append(self.fee_oracle.get_fee('v26'))

            # Fee revenue per block (miner incentive from fees)
            self.time_series['v27_fee_revenue_btc'].append(
                self.fee_oracle.get_fee_revenue_per_block('v27'))
            self.time_series['v26_fee_revenue_btc'].append(
                self.fee_oracle.get_fee_revenue_per_block('v26'))

            # Mempool/congestion estimates
            # Get blocks per hour for congestion calculation
            if self.difficulty_oracle:
                v27_bph = self.difficulty_oracle.get_blocks_per_hour('v27', self.current_v27_hashrate)
                v26_bph = self.difficulty_oracle.get_blocks_per_hour('v26', self.current_v26_hashrate)
            else:
                # Estimate from hashrate (normal rate = 6 blocks/hour)
                v27_bph = 6.0 * (self.current_v27_hashrate / 100.0) if self.current_v27_hashrate > 0 else 0.1
                v26_bph = 6.0 * (self.current_v26_hashrate / 100.0) if self.current_v26_hashrate > 0 else 0.1

            v27_mempool = self.fee_oracle.estimate_mempool_size(
                'v27', v27_bph, self.current_v27_economic)
            v26_mempool = self.fee_oracle.estimate_mempool_size(
                'v26', v26_bph, self.current_v26_economic)

            self.time_series['v27_congestion'].append(v27_mempool['congestion_ratio'])
            self.time_series['v26_congestion'].append(v26_mempool['congestion_ratio'])
            self.time_series['v27_mempool_mb'].append(v27_mempool['estimated_mempool_mb'])
            self.time_series['v26_mempool_mb'].append(v26_mempool['estimated_mempool_mb'])
        else:
            # Default values if no fee oracle
            self.time_series['v27_fee_rate'].append(1.0)
            self.time_series['v26_fee_rate'].append(1.0)
            self.time_series['v27_fee_revenue_btc'].append(0.01)
            self.time_series['v26_fee_revenue_btc'].append(0.01)
            self.time_series['v27_congestion'].append(1.0)
            self.time_series['v26_congestion'].append(1.0)
            self.time_series['v27_mempool_mb'].append(0.0)
            self.time_series['v26_mempool_mb'].append(0.0)

        # Transactional weight (fee-generating economic activity)
        self.time_series['v27_transactional'].append(self.current_v27_transactional)
        self.time_series['v26_transactional'].append(self.current_v26_transactional)

        # Solo miner hashrate
        self.time_series['v27_solo_hashrate'].append(self.current_v27_solo_hashrate)
        self.time_series['v26_solo_hashrate'].append(self.current_v26_solo_hashrate)

        # Measured block time (rolling window)
        self.time_series['v27_block_time_s'].append(v27_block_time)
        self.time_series['v26_block_time_s'].append(v26_block_time)

    def run_test(self):
        """Main mining loop with dynamic pool strategy"""

        # Calculate complementary economic weight
        if self.options.v26_economic is None:
            self.options.v26_economic = 100.0 - self.options.v27_economic

        # In-place switching runs on an all-Knots network, where only RDTS
        # status tells the camps apart.
        if self.options.inplace_switching and self.options.node_classification != 'rdts':
            self.log.info(f"--inplace-switching: node classification "
                          f"{self.options.node_classification} -> rdts")
            self.options.node_classification = 'rdts'

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining with Dynamic Pool Strategy")
        self.log.info(f"{'='*70}")
        self.log.info(f"Initial economic weights: v27={self.options.v27_economic}%, v26={self.options.v26_economic}%")
        self.log.info(f"Duration: {self.options.duration}s ({self.options.duration/60:.0f} minutes)")
        self.log.info(f"Pool scenario: {self.options.pool_scenario}")
        self.log.info(f"Economic scenario: {self.options.economic_scenario}")
        self.log.info(f"Partition mode: {self.options.partition_mode}")
        self.log.info(f"{'='*70}\n")

        self.fork_convergence['enabled'] = self.options.fork_heal_exit

        # Initialize oracles
        price_oracle_kwargs = {
            'base_price': 60000,
            'min_fork_depth': 6,
            'debug': self.options.debug_prices,
            'liveness_penalty': self.options.enable_liveness_penalty,
            'use_economic_ema': self.options.use_economic_ema,
            'economic_ema_alpha': self.options.economic_ema_alpha,
            'use_sigmoid': self.options.use_sigmoid,
            'sigmoid_steepness_k': self.options.sigmoid_steepness,
            'use_cost_floor': self.options.use_cost_floor,
            'cost_floor_margin_buffer': self.options.cost_floor_margin_buffer,
        }
        # Override max divergence if specified via command line
        if self.options.max_price_divergence is not None:
            price_oracle_kwargs['max_divergence'] = self.options.max_price_divergence
        self.price_oracle = PriceOracle(**price_oracle_kwargs)
        divergence_msg = f", max_divergence=±{self.options.max_price_divergence*100:.0f}%" if self.options.max_price_divergence else ""
        self.log.info(f"✓ Price oracle initialized (debug={self.options.debug_prices}{divergence_msg})")

        self.fee_oracle = FeeOracle()
        self.log.info("✓ Fee oracle initialized")

        # Initialize pool strategy
        try:
            # Load config from bundled package (works inside .pyz archive)
            import pkgutil
            import yaml
            config_data = pkgutil.get_data('config', 'mining_pools_config.yaml')
            config = yaml.safe_load(config_data.decode('utf-8'))

            scenario_name = self.options.pool_scenario
            if scenario_name not in config:
                raise ValueError(f"Scenario '{scenario_name}' not found in config")

            scenario = config[scenario_name]
            pools = []
            for pool_data in scenario.get('pools', []):
                pools.append(PoolProfile(
                    pool_id=pool_data['pool_id'],
                    hashrate_pct=pool_data['hashrate_pct'],
                    fork_preference=ForkPreference(pool_data.get('fork_preference', 'neutral')),
                    ideology_strength=pool_data.get('ideology_strength', pool_data.get('ideology_score', 0.5)),
                    profitability_threshold=pool_data.get('profitability_threshold', pool_data.get('switch_threshold_pct', 5.0) / 100.0),
                    max_loss_usd=pool_data.get('max_loss_usd'),
                    max_loss_pct=pool_data.get('max_loss_pct', 0.10),
                    initial_fork=pool_data.get('initial_fork'),
                ))
            self.pool_strategy = MiningPoolStrategy(
                pools,
                decision_interval=self.options.pool_decision_interval,
            )
            self.log.info(f"✓ Pool strategy initialized ({len(pools)} pools)")

            # Set initial hashrate from pool scenario.
            # If a pool has an explicit initial_fork, use that; otherwise fall
            # back to fork_preference (neutral pools split evenly).
            initial_v27 = 0.0
            initial_v26 = 0.0
            for pool in pools:
                if pool.initial_fork is not None:
                    start = pool.initial_fork
                elif pool.fork_preference == ForkPreference.V27:
                    start = 'v27'
                elif pool.fork_preference == ForkPreference.V26:
                    start = 'v26'
                else:
                    start = None  # Neutral — split below

                if start == 'v27':
                    initial_v27 += pool.hashrate_pct
                elif start == 'v26':
                    initial_v26 += pool.hashrate_pct
                else:
                    initial_v27 += pool.hashrate_pct / 2
                    initial_v26 += pool.hashrate_pct / 2

            self.current_v27_hashrate = initial_v27
            self.current_v26_hashrate = initial_v26

            # Set initial allocation in pool strategy.
            # Neutral pools with no initial_fork alternate to approximate 50/50.
            neutral_toggle = True
            for pool in pools:
                if pool.initial_fork is not None:
                    self.pool_strategy.current_allocation[pool.pool_id] = pool.initial_fork
                elif pool.fork_preference == ForkPreference.V27:
                    self.pool_strategy.current_allocation[pool.pool_id] = 'v27'
                elif pool.fork_preference == ForkPreference.V26:
                    self.pool_strategy.current_allocation[pool.pool_id] = 'v26'
                else:
                    # Neutral pools alternate between forks
                    self.pool_strategy.current_allocation[pool.pool_id] = 'v27' if neutral_toggle else 'v26'
                    neutral_toggle = not neutral_toggle

        except Exception as e:
            self.log.warning(f"Could not load pool config: {e}")
            self.log.info("Using static hashrate allocation")

            if self.options.initial_v27_hashrate is not None:
                self.current_v27_hashrate = self.options.initial_v27_hashrate
                self.current_v26_hashrate = 100.0 - self.options.initial_v27_hashrate
            else:
                self.current_v27_hashrate = 50.0
                self.current_v26_hashrate = 50.0

            self.pool_strategy = None

        self.log.info(f"\nInitial hashrate: v27={self.current_v27_hashrate:.1f}%, v26={self.current_v26_hashrate:.1f}%\n")

        # Load node metadata from network.yaml
        self.load_network_metadata()

        # Initialize economic node strategy (dynamic economic weight)
        try:
            import pkgutil
            econ_config_data = pkgutil.get_data('config', 'economic_nodes_config.yaml')
            econ_config = yaml.safe_load(econ_config_data.decode('utf-8'))

            economic_profiles = load_economic_nodes_from_network(
                self.node_metadata,
                econ_config,
                self.options.economic_scenario
            )

            # Optional cooldown overrides. Config defaults (1800s economic /
            # 3600s user in realistic_current) are >= a typical run length, so
            # each node decides once at t=0 and the economic layer never moves;
            # lowering these is how a short run exercises economic switching.
            # Both default to None, leaving the config values untouched.
            cooldown_overrides = {
                'economic': self.options.economic_switching_cooldown,
                'user': self.options.user_switching_cooldown,
            }
            if any(v is not None for v in cooldown_overrides.values()):
                counts = {}
                for profile in economic_profiles:
                    node_type = getattr(profile.node_type, 'value', profile.node_type)
                    override = cooldown_overrides.get(node_type)
                    if override is not None:
                        profile.switching_cooldown = override
                        counts[node_type] = counts.get(node_type, 0) + 1
                for node_type, n in sorted(counts.items()):
                    self.log.info(f"  Overrode switching_cooldown={cooldown_overrides[node_type]}s "
                                  f"for {n} {node_type} node(s)")

            # Read user_custody_fraction from per-scenario config entry if present.
            # Omitting it (None) leaves user node weights at their calibrated values,
            # reproducing all prior sweep results exactly.
            scenario_cfg = econ_config.get(self.options.economic_scenario, {})
            user_custody_fraction = scenario_cfg.get('user_custody_fraction', None)

            if economic_profiles:
                self.economic_strategy = EconomicNodeStrategy(
                    economic_profiles,
                    user_custody_fraction=user_custody_fraction,
                )

                # Calculate initial economic allocation (nodes start on their partition's fork)
                self.current_v27_economic, self.current_v26_economic = \
                    self.economic_strategy.calculate_economic_allocation(
                        time(), self.price_oracle
                    )

                # Calculate transactional weights (fee-generating activity)
                self.current_v27_transactional, self.current_v26_transactional = \
                    self.economic_strategy.get_fee_generation_weight()

                # Calculate solo miner hashrate
                self.current_v27_solo_hashrate, self.current_v26_solo_hashrate, solo_miners = \
                    self.economic_strategy.get_mining_allocation()

                econ_count = len(economic_profiles)
                econ_types = {}
                solo_miner_count = 0
                for p in economic_profiles:
                    t = p.node_type.value
                    econ_types[t] = econ_types.get(t, 0) + 1
                    if p.hashrate_pct > 0:
                        solo_miner_count += 1

                self.log.info(f"✓ Economic strategy initialized ({econ_count} nodes: {econ_types})")
                self.log.info(f"  Initial economic weight: v27={self.current_v27_economic:.1f}%, v26={self.current_v26_economic:.1f}%")
                self.log.info(f"  Initial transactional weight: v27={self.current_v27_transactional:.1f}%, v26={self.current_v26_transactional:.1f}%")
                if solo_miner_count > 0:
                    total_solo = self.current_v27_solo_hashrate + self.current_v26_solo_hashrate
                    self.log.info(f"  Solo miners: {solo_miner_count} nodes with {total_solo:.2f}% hashrate")
                    self.log.info(f"    v27: {self.current_v27_solo_hashrate:.2f}%, v26: {self.current_v26_solo_hashrate:.2f}%")
                self.log.info(f"  Update interval: {self.options.economic_update_interval}s")
            else:
                self.log.info("No economic/user nodes found in metadata, using static economic weight")
                self.current_v27_economic = self.options.v27_economic
                self.current_v26_economic = self.options.v26_economic
                # Without economic strategy, assume 50/50 transactional split
                self.current_v27_transactional = self.options.v27_economic
                self.current_v26_transactional = self.options.v26_economic
                self.economic_strategy = None

        except Exception as e:
            self.log.warning(f"Could not load economic config: {e}")
            self.log.info("Using static economic allocation from --v27-economic")
            self.current_v27_economic = self.options.v27_economic
            self.current_v26_economic = self.options.v26_economic
            self.current_v27_transactional = self.options.v27_economic
            self.current_v26_transactional = self.options.v26_economic
            self.economic_strategy = None

        # Initialize difficulty oracle (if enabled)
        if self.options.enable_difficulty:
            self.tick_interval = self.options.tick_interval
            self.difficulty_oracle = DifficultyOracle(
                target_block_interval=float(self.options.interval),
                retarget_interval=self.options.retarget_interval,
                pre_fork_difficulty=1.0,
                max_adjustment_factor=4.0,
                min_difficulty=self.options.min_difficulty,
                enable_eda=self.options.enable_eda,
            )
            self.difficulty_oracle.initialize_fork('v27', initial_height=self.options.start_height)
            self.difficulty_oracle.initialize_fork('v26', initial_height=self.options.start_height)
            self.log.info(f"Difficulty oracle initialized:")
            self.log.info(f"  Target interval: {self.options.interval}s, Retarget every {self.options.retarget_interval} blocks")
            self.log.info(f"  Tick interval: {self.tick_interval}s, Min difficulty: {self.options.min_difficulty}")
            self.log.info(f"  EDA: {'enabled' if self.options.enable_eda else 'disabled'}")

        # Partition nodes. --node-classification default 'subversion' (Knots
        # vs Core detection); 'tag' reproduces the original numeric-tag
        # matching for an old-style v27/v26 run.
        if self.options.node_classification == 'subversion':
            self.classify_nodes_by_subversion()
        elif self.options.node_classification == 'rdts':
            self.classify_nodes_by_rdts()
        else:
            self.partition_nodes_by_version()

        # Ensure the network has spendable common history before the RDTS
        # injection tx needs it (no-op if the network already has it).
        self.ensure_common_history()

        # Identify foreign-accepting nodes for asymmetric fork propagation
        self.build_foreign_accepting_nodes()

        # Build partition peer lists for dynamic switching
        self.build_partition_peer_lists()

        # Build pool-to-node mapping
        if self.pool_strategy:
            self.build_pool_node_mapping()

        # Auto-detect starting height BEFORE reorg oracle initialization
        # This ensures lca_height matches the actual fork point
        if self.options.start_height == 101:  # Default value, auto-detect instead
            detected_heights = []
            for node in (self.v27_nodes + self.v26_nodes)[:3]:  # Sample first few nodes
                try:
                    h = node.getblockcount()
                    detected_heights.append(h)
                except:
                    pass
            if detected_heights:
                # Use minimum as common ancestor (conservative)
                self.options.start_height = min(detected_heights)
                self.log.info(f"Auto-detected start_height={self.options.start_height} from nodes")

        # Initialize reorg oracle (if enabled) - AFTER auto-detection so lca_height is correct
        if self.options.enable_reorg_metrics:
            # Get initial fork height (LCA = starting height before fork diverges)
            lca_height = self.options.start_height

            # Determine total nodes from pool strategy if available
            total_pool_nodes = len(self.pool_strategy.pools) if self.pool_strategy else 8

            self.reorg_oracle = ReorgOracle(
                lca_height=lca_height,
                lca_hash="fork-point",
                propagation_window=30.0,
                total_nodes=total_pool_nodes
            )
            # Initialize both forks from the LCA
            self.reorg_oracle.initialize_fork('v27', lca_height)
            self.reorg_oracle.initialize_fork('v26', lca_height)

            self.log.info(f"✓ Reorg oracle initialized (LCA height={lca_height})")

            # Register pool nodes with reorg oracle
            if self.pool_strategy:
                for pool_id, pool in self.pool_strategy.pools.items():
                    initial_fork = self.pool_strategy.current_allocation.get(pool_id, 'v27')
                    self.reorg_oracle.register_node(pool_id, initial_fork)
                    # Also set current_fork on pool profile for tracking
                    pool.current_fork = initial_fork
                self.log.info(f"  Registered {len(self.pool_strategy.pools)} pools with reorg oracle")

        # Main mining loop
        start_time = time()
        last_hashrate_update = start_time
        last_price_update = start_time
        last_economic_update = start_time
        last_snapshot = start_time
        fork_heal_triggered = False

        # Initialize time-limited UASF tracking
        if self.options.uasf_duration is not None:
            self.uasf_start_time = start_time
            self.uasf_expiry_time = start_time + self.options.uasf_duration
            self.uasf_active = True
            self.uasf_expired = False
            uasf_hours = self.options.uasf_duration / 3600
            self.log.info(f"\n{'='*70}")
            self.log.info(f"TIME-LIMITED UASF ENABLED")
            self.log.info(f"{'='*70}")
            self.log.info(f"  Duration: {self.options.uasf_duration}s ({uasf_hours:.1f} hours)")
            self.log.info(f"  Expiry action: {self.options.uasf_expiry_action}")
            self.log.info(f"  v27 nodes will enforce strict rules until UASF expires")
            self.log.info(f"{'='*70}\n")

        # Capture initial snapshot
        self.capture_time_series_snapshot(0)

        # RDTS fork trigger: inject the oversized-OP_RETURN tx once, early —
        # RDTS is ALWAYS_ACTIVE from genesis, so no BIP9 wait needed. It sits
        # in v26 (Core) mempools and gets included whenever the ongoing
        # mining selection (difficulty-oracle or legacy) next picks a v26
        # node, same as any other transaction would.
        self.inject_rdts_violation()
        last_rdts_check = start_time

        # Real-tip observation (independent of blocks_mined bookkeeping).
        self.chain_state['enabled'] = self.options.chain_state_interval > 0
        self.chain_state['interval_s'] = self.options.chain_state_interval

        # What the price/pool oracles treat as each camp's chain.
        source = self.options.oracle_chain_source or (
            'observed' if self.options.node_classification in ('subversion', 'rdts') else 'mined')
        if source == 'observed' and not self.chain_state['enabled']:
            self.log.warning("  --oracle-chain-source=observed needs --chain-state-interval > 0; "
                             "falling back to mined")
            source = 'mined'
        self.oracle_chain_source = source
        self.chain_state['oracle_chain_source'] = source
        self.log.info(f"  Oracle chain source: {source}"
                      + (f" (pool revenue scaled by survival over last {self.options.survival_window} "
                         f"blocks per camp)" if source == 'observed' else ""))
        for camp, nodes in (('v27', self.v27_nodes), ('v26', self.v26_nodes)):
            self.chain_state['sample_nodes'][camp] = [
                f"node-{n.index:04d}" for n in self._chain_state_sample(nodes)]
        if self.chain_state['enabled']:
            self.log.info(f"  Chain-state observation every {self.options.chain_state_interval}s on "
                          f"{self.chain_state['sample_nodes']}")
        self.observe_chain_state(0)
        last_chain_state_check = start_time

        # Bring each node's enforced rules in line with its owner's starting
        # fork choice (normally already matching the seeded switch.conf).
        self.reconcile_node_modes(0, 'initial')

        self.log.info(f"\n{'='*70}")
        if self.difficulty_oracle:
            self.log.info(f"Starting partition mining (DIFFICULTY MODE)...")
        else:
            self.log.info(f"Starting partition mining (LEGACY MODE)...")
        self.log.info(f"{'='*70}\n")

        while time() - start_time < self.options.duration:
            current_time = time()
            elapsed = int(current_time - start_time)

            # Check for UASF expiry
            if (self.uasf_active and not self.uasf_expired and
                self.uasf_expiry_time is not None and
                current_time >= self.uasf_expiry_time):
                self.handle_uasf_expiry(elapsed, current_time)

            # Update economic node allocation (every 5 minutes by default)
            if self.economic_strategy and (current_time - last_economic_update >= self.options.economic_update_interval):
                old_v27_econ = self.current_v27_economic
                old_v26_econ = self.current_v26_economic

                self.current_v27_economic, self.current_v26_economic = \
                    self.economic_strategy.calculate_economic_allocation(
                        current_time, self.price_oracle
                    )

                # Update transactional weights (for fee calculations)
                self.current_v27_transactional, self.current_v26_transactional = \
                    self.economic_strategy.get_fee_generation_weight()

                # Update solo miner hashrate allocation
                old_v27_solo = self.current_v27_solo_hashrate
                old_v26_solo = self.current_v26_solo_hashrate
                self.current_v27_solo_hashrate, self.current_v26_solo_hashrate, _ = \
                    self.economic_strategy.get_mining_allocation()

                econ_change = abs(self.current_v27_economic - old_v27_econ)
                solo_change = abs(self.current_v27_solo_hashrate - old_v27_solo)

                if econ_change > 0.5:  # More than 0.5% change
                    self.log.info(f"\n ECONOMIC REALLOCATION at {elapsed}s:")
                    self.log.info(f"   v27: {old_v27_econ:.1f}% -> {self.current_v27_economic:.1f}%")
                    self.log.info(f"   v26: {old_v26_econ:.1f}% -> {self.current_v26_economic:.1f}%")
                    self.log.info(f"   Transactional: v27={self.current_v27_transactional:.1f}%, v26={self.current_v26_transactional:.1f}%")

                    # Log solo miner changes if any
                    if solo_change > 0.01:
                        self.log.info(f"   Solo miners: v27={old_v27_solo:.2f}%->{self.current_v27_solo_hashrate:.2f}%, "
                                      f"v26={old_v26_solo:.2f}%->{self.current_v26_solo_hashrate:.2f}%")

                    # Log notable node decisions
                    recent = [d for d in self.economic_strategy.decision_history[-30:]
                              if d.timestamp >= last_economic_update]
                    for decision in recent:
                        if decision.ideology_override:
                            self.log.info(f"   {decision.node_id}: staying on {decision.chosen_fork} (ideology)")
                        elif decision.inertia_held:
                            self.log.info(f"   {decision.node_id}: staying on {decision.chosen_fork} (inertia)")

                last_economic_update = current_time

                self.reconcile_node_modes(elapsed, 'economic decision')

            # Capture time series snapshot at regular intervals
            if current_time - last_snapshot >= self.options.snapshot_interval:
                self.capture_time_series_snapshot(elapsed)
                last_snapshot = current_time

            # Check for RDTS rejection evidence at regular intervals (no-ops
            # once already confirmed, or if injection is disabled/failed)
            if current_time - last_rdts_check >= self.options.rdts_check_interval:
                self.check_rdts_rejection(elapsed)
                last_rdts_check = current_time

            if (self.chain_state['enabled'] and
                    current_time - last_chain_state_check >= self.options.chain_state_interval):
                self.observe_chain_state(elapsed)
                last_chain_state_check = current_time

            # Update prices (every minute by default)
            if current_time - last_price_update >= self.options.price_update_interval:
                # Use blocks_mined counters for reliable fork depth calculation
                # (node getblockcount() can be unreliable in partitioned networks)
                fork_depth = self.blocks_mined['v27'] + self.blocks_mined['v26']

                # Still get heights for price oracle (but fork_depth is what matters for sustained check)
                v27_height = self.options.start_height + self.blocks_mined['v27']
                v26_height = self.options.start_height + self.blocks_mined['v26']

                # Chainwork-based chain weights if difficulty oracle available
                v27_cw_override = None
                v26_cw_override = None
                if self.difficulty_oracle:
                    v27_cw_override = self.difficulty_oracle.get_chain_weight('v27')
                    v26_cw_override = self.difficulty_oracle.get_chain_weight('v26')
                common_ancestor_height = self.options.start_height

                # Observed chain state instead: heights/LCA from real tips, chain
                # weight from surviving (non-orphaned) self-mined blocks.
                observed = self.observed_price_inputs() if self.oracle_chain_source == 'observed' else None
                if observed:
                    (v27_height, v26_height, common_ancestor_height,
                     v27_cw_override, v26_cw_override) = observed
                    fork_depth = v27_height + v26_height - 2 * common_ancestor_height

                # Debug: log price update inputs
                if self.options.debug_prices:
                    self.log.info(f"  [PRICE UPDATE] fork_depth={fork_depth}, sustained={self.price_oracle.fork_sustained}")
                    self.log.info(f"  [PRICE UPDATE] chain_weights: v27={v27_cw_override}, v26={v26_cw_override}")
                    self.log.info(f"  [PRICE UPDATE] econ: v27={self.current_v27_economic}%, v26={self.current_v26_economic}%")
                    self.log.info(f"  [PRICE UPDATE] hash: v27={self.current_v27_hashrate}%, v26={self.current_v26_hashrate}%")

                old_v27_price = self.price_oracle.get_price('v27')
                old_v26_price = self.price_oracle.get_price('v26')

                # Liveness penalty: compute each chain's block production rate
                # relative to the simulation target (1 block per --interval seconds).
                # production_ratio = 1.0 means on-target; 0.0 means ghost town.
                v27_rate_ratio = None
                v26_rate_ratio = None
                if self.options.enable_liveness_penalty and self.difficulty_oracle:
                    target_bph = 3600.0 / self.difficulty_oracle.target_block_interval
                    v27_bph = self.difficulty_oracle.get_blocks_per_hour(
                        'v27', self.current_v27_hashrate
                    )
                    v26_bph = self.difficulty_oracle.get_blocks_per_hour(
                        'v26', self.current_v26_hashrate
                    )
                    v27_rate_ratio = min(1.0, v27_bph / target_bph)
                    v26_rate_ratio = min(1.0, v26_bph / target_bph)
                    if self.options.debug_prices:
                        self.log.info(
                            f"  [PRICE UPDATE] liveness: target={target_bph:.1f} bph, "
                            f"v27={v27_bph:.2f} bph (ratio={v27_rate_ratio:.3f}), "
                            f"v26={v26_bph:.2f} bph (ratio={v26_rate_ratio:.3f})"
                        )

                self.price_oracle.update_prices_from_state(
                    v27_height=v27_height,
                    v26_height=v26_height,
                    v27_economic_pct=self.current_v27_economic,
                    v26_economic_pct=self.current_v26_economic,
                    v27_hashrate_pct=self.current_v27_hashrate,
                    v26_hashrate_pct=self.current_v26_hashrate,
                    common_ancestor_height=common_ancestor_height,
                    v27_chain_weight_override=v27_cw_override,
                    v26_chain_weight_override=v26_cw_override,
                    v27_block_rate_ratio=v27_rate_ratio,
                    v26_block_rate_ratio=v26_rate_ratio,
                )

                new_v27_price = self.price_oracle.get_price('v27')
                new_v26_price = self.price_oracle.get_price('v26')

                if self.options.debug_prices:
                    self.log.info(f"  [PRICE UPDATE] prices: v27=${old_v27_price:,.0f}->${new_v27_price:,.0f}, v26=${old_v26_price:,.0f}->${new_v26_price:,.0f}")

                # Update fees based on network state
                if self.difficulty_oracle:
                    v27_blocks_per_hour = self.difficulty_oracle.get_blocks_per_hour('v27', self.current_v27_hashrate)
                    v26_blocks_per_hour = self.difficulty_oracle.get_blocks_per_hour('v26', self.current_v26_hashrate)
                else:
                    v27_blocks_per_hour = (self.blocks_mined['v27'] / max(1, elapsed/3600))
                    v26_blocks_per_hour = (self.blocks_mined['v26'] / max(1, elapsed/3600))

                self.fee_oracle.update_fees_from_state(
                    v27_blocks_per_hour=v27_blocks_per_hour,
                    v26_blocks_per_hour=v26_blocks_per_hour,
                    v27_economic_pct=self.current_v27_economic,
                    v26_economic_pct=self.current_v26_economic,
                    price_oracle=self.price_oracle,
                    difficulty_oracle=self.difficulty_oracle,
                    v27_hashrate_pct=self.current_v27_hashrate,
                    v26_hashrate_pct=self.current_v26_hashrate,
                    # Pass transactional weights for fee calculation
                    # Fees are driven by transaction activity, not custody holdings
                    v27_transactional_pct=self.current_v27_transactional,
                    v26_transactional_pct=self.current_v26_transactional,
                )

                last_price_update = current_time

            # Update hashrate allocation (every 10 minutes by default)
            # Skip if reunion has completed - all hashrate is already on winning fork
            if self.reunion_completed:
                pass  # Hashrate locked to winning fork after reunion
            elif self.pool_strategy and (current_time - last_hashrate_update >= self.options.hashrate_update_interval):

                # Pools make decisions
                old_v27_hash = self.current_v27_hashrate
                old_v26_hash = self.current_v26_hashrate

                pool_difficulty = self.difficulty_oracle
                if self.oracle_chain_source == 'observed' and self.difficulty_oracle:
                    pool_difficulty = SurvivalAdjustedDifficulty(self.difficulty_oracle, self.survival_ratio)
                self.current_v27_hashrate, self.current_v26_hashrate = \
                    self.pool_strategy.calculate_hashrate_allocation(
                        current_time, self.price_oracle, self.fee_oracle,
                        difficulty_oracle=pool_difficulty,
                    )

                # Ensure fork heights are current before detecting reorgs
                if self.reorg_oracle:
                    self.reorg_oracle.update_fork_heights(
                        v27_height=self.options.start_height + self.blocks_mined['v27'],
                        v26_height=self.options.start_height + self.blocks_mined['v26']
                    )

                # Detect fork switches and record reorgs
                if self.reorg_oracle:
                    for pool_id, pool in self.pool_strategy.pools.items():
                        old_fork = pool.current_fork
                        new_fork = self.pool_strategy.current_allocation.get(pool_id, old_fork)

                        if old_fork != new_fork:
                            # Pool is switching forks - this causes a reorg!
                            reorg_event = self.reorg_oracle.record_fork_switch(
                                node_id=pool_id,
                                old_fork=old_fork,
                                new_fork=new_fork,
                                sim_time=elapsed
                            )
                            self.log.info(f"  REORG: {pool_id} switched {old_fork}->{new_fork}, "
                                          f"depth={reorg_event.depth}, orphaned={len(reorg_event.blocks_invalidated)} blocks")

                        # Update pool's current_fork tracking
                        pool.current_fork = new_fork

                # Log significant changes
                hash_change = abs(self.current_v27_hashrate - old_v27_hash)
                if hash_change > 1.0:  # More than 1% change
                    self.log.info(f"\n HASHRATE REALLOCATION at {elapsed}s:")
                    self.log.info(f"   v27: {old_v27_hash:.1f}% -> {self.current_v27_hashrate:.1f}%")
                    self.log.info(f"   v26: {old_v26_hash:.1f}% -> {self.current_v26_hashrate:.1f}%")

                    # Log pool switches
                    recent_decisions = [d for d in self.pool_strategy.decision_history[-20:]
                                      if d.timestamp >= last_hashrate_update]

                    for decision in recent_decisions:
                        if decision.ideology_override:
                            self.log.info(f"   {decision.pool_id}: mining {decision.chosen_fork} "
                                        f"despite ${decision.opportunity_cost_usd:,.0f} loss (ideology)")
                        elif decision.chosen_fork != decision.rational_choice:
                            self.log.info(f"   {decision.pool_id}: forced to switch to {decision.chosen_fork}")

                last_hashrate_update = current_time

                self.reconcile_node_modes(elapsed, 'pool decision')

                # Evaluate economic/user node partition switches
                # These nodes may switch partitions based on price, ideology, etc.
                # Not under --inplace-switching: there economic/user nodes follow
                # EconomicNodeStrategy (the allocation that drives price) via
                # reconcile_node_modes, not this separate threshold model.
                if self.options.enable_dynamic_switching and not self.options.inplace_switching:
                    self.evaluate_economic_node_switches(elapsed)

            # === BLOCK PRODUCTION ===
            if self.difficulty_oracle:
                # DIFFICULTY MODE: per-tick probability for each fork independently
                # Supports multiple blocks per tick when block times are faster than tick interval
                sim_elapsed = elapsed  # Use wall-clock elapsed as sim_time

                for fork_id in ['v27', 'v26']:
                    hashrate_pct = self.current_v27_hashrate if fork_id == 'v27' else self.current_v26_hashrate

                    # Get number of blocks to mine this tick (can be 0, 1, or more)
                    blocks_to_mine = self.difficulty_oracle.get_blocks_to_mine(fork_id, hashrate_pct, self.tick_interval)

                    for block_num in range(blocks_to_mine):
                        miner = self._select_miner_for_fork(fork_id)
                        if not miner:
                            continue

                        try:
                            miner_wallet = self._ensure_miner(miner)
                            address = miner_wallet.getnewaddress()
                            mined_hashes = self._mine_block(miner, fork_id, address)
                            self._mined_blocks[fork_id].extend(mined_hashes or [])

                            # Asymmetric fork: push v27 blocks into the v26 island.
                            # Gated (default off) — real P2P relay across the mesh
                            # handles propagation; this bypasses it via submitblock.
                            if self.options.enable_asymmetric_bridging:
                                self.propagate_to_foreign_accepting(miner, fork_id)

                            # Probabilistic softfork: some v26 blocks comply with v27 rules.
                            # Already inert by default (--v26-acceptance-probability=0.0).
                            if fork_id == 'v26':
                                self.propagate_v26_to_v27(miner)

                            self.blocks_mined[fork_id] += 1
                            new_height = (self.v27_nodes[0].getblockcount() if fork_id == 'v27' and self.v27_nodes
                                          else self.v26_nodes[0].getblockcount() if fork_id == 'v26' and self.v26_nodes
                                          else self.options.start_height + self.blocks_mined[fork_id])

                            if self.options.fork_heal_exit and self.check_fork_healed(elapsed):
                                fork_heal_triggered = True
                                break

                            # Record block with reorg oracle
                            if self.reorg_oracle:
                                pool_id = self.get_node_pool_id(miner)
                                if pool_id:
                                    self.reorg_oracle.record_block_mined(pool_id, fork_id, new_height)
                                # Update fork heights
                                self.reorg_oracle.update_fork_heights(
                                    v27_height=self.options.start_height + self.blocks_mined['v27'],
                                    v26_height=self.options.start_height + self.blocks_mined['v26']
                                )

                            retarget_event = self.difficulty_oracle.record_block(fork_id, sim_elapsed, new_height)

                            if retarget_event:
                                eda_str = " (EDA)" if retarget_event.is_eda else ""
                                self.log.info(
                                    f"  >> {fork_id} RETARGET{eda_str} at {elapsed}s: "
                                    f"difficulty {retarget_event.old_difficulty:.6f} -> {retarget_event.new_difficulty:.6f} "
                                    f"(factor={retarget_event.adjustment_factor:.3f})"
                                )

                            # Log the block (show multi-block indicator if applicable)
                            v27_price = self.price_oracle.get_price('v27')
                            v26_price = self.price_oracle.get_price('v26')
                            fork_status = "SUSTAINED" if self.price_oracle.fork_sustained else "natural split"
                            diff_state = self.difficulty_oracle.forks[fork_id]
                            pool_id = self.get_node_pool_id(miner)
                            pool_str = f"({pool_id})" if pool_id else ""
                            multi_str = f" [{block_num+1}/{blocks_to_mine}]" if blocks_to_mine > 1 else ""

                            self.log.info(
                                f"[{elapsed:4d}s] {fork_id} block {pool_str:15s}{multi_str} | "
                                f"Blks: v27={self.blocks_mined['v27']:3d} v26={self.blocks_mined['v26']:3d} | "
                                f"Diff: {diff_state.current_difficulty:.4f} | "
                                f"Hash: {self.current_v27_hashrate:4.1f}%/{self.current_v26_hashrate:4.1f}% | "
                                f"Price: ${v27_price:,.0f}/${v26_price:,.0f} [{fork_status}]"
                            )

                        except Exception as e:
                            self.log.error(f"Error mining {fork_id} block: {e}")

                    if fork_heal_triggered:
                        break

                if fork_heal_triggered:
                    break

                sleep(self.tick_interval)

            else:
                # LEGACY MODE: one block per interval, probabilistic fork selection
                miner, partition = self.select_mining_node()

                if not miner:
                    self.log.warning("No miner available, skipping block")
                    sleep(self.options.interval)
                    continue

                try:
                    miner_wallet = self._ensure_miner(miner)
                    address = miner_wallet.getnewaddress()
                    mined_hashes = self._mine_block(miner, partition, address)
                    self._mined_blocks[partition].extend(mined_hashes or [])

                    # Asymmetric fork: push v27 blocks into the v26 island.
                    # Gated (default off), same reasoning as the difficulty-mode branch.
                    if self.options.enable_asymmetric_bridging:
                        self.propagate_to_foreign_accepting(miner, partition)

                    self.blocks_mined[partition] += 1

                    if self.options.fork_heal_exit and self.check_fork_healed(elapsed):
                        fork_heal_triggered = True

                    v27_height = self.v27_nodes[0].getblockcount() if self.v27_nodes else 0
                    v26_height = self.v26_nodes[0].getblockcount() if self.v26_nodes else 0
                    fork_depth = v27_height + v26_height - (2 * self.options.start_height)

                    # Record block with reorg oracle
                    if self.reorg_oracle:
                        pool_id = self.get_node_pool_id(miner)
                        if pool_id:
                            block_height = v27_height if partition == 'v27' else v26_height
                            self.reorg_oracle.record_block_mined(pool_id, partition, block_height)
                        # Update fork heights
                        self.reorg_oracle.update_fork_heights(v27_height, v26_height)

                    # Get current state
                    v27_price = self.price_oracle.get_price('v27')
                    v26_price = self.price_oracle.get_price('v26')
                    price_ratio = v27_price / v26_price if v26_price > 0 else 1.0

                    fork_status = "SUSTAINED" if self.price_oracle.fork_sustained else "natural split"

                    # Get pool name for logging
                    pool_id = self.get_node_pool_id(miner)
                    pool_str = f"({pool_id})" if pool_id else ""

                    self.log.info(
                        f"[{elapsed:4d}s] {partition} block {pool_str:15s} | "
                        f"Heights: v27={v27_height:3d} v26={v26_height:3d} | "
                        f"Hash: {self.current_v27_hashrate:4.1f}%/{self.current_v26_hashrate:4.1f}% | "
                        f"Econ: {self.current_v27_economic:4.1f}%/{self.current_v26_economic:4.1f}% | "
                        f"Price: ${v27_price:,.0f}/${v26_price:,.0f} [{fork_status}]"
                    )

                except Exception as e:
                    self.log.error(f"Error mining block: {e}")

                if fork_heal_triggered:
                    break

                sleep(self.options.interval)

        # Final RDTS rejection check (in case the periodic interval didn't
        # catch it before the loop ended)
        self.check_rdts_rejection(int(time() - start_time))

        self.log.info("")
        self.log.info("=" * 50)
        self.log.info("RDTS FORK TRIGGER SUMMARY")
        self.log.info("=" * 50)
        self.log.info(f"  Injection: {'sent' if self.rdts_rejection['injected'] else 'not sent'}"
                      + (f" (txid={self.rdts_rejection['txid']})" if self.rdts_rejection['txid'] else ""))
        if self.rdts_rejection['rejected']:
            self.log.info(f"  Rejection: CONFIRMED at {self.rdts_rejection['rejected_at_elapsed_s']}s "
                          f"on {self.rdts_rejection['rejecting_nodes']}")
            self.log.info(f"  debug.log confirmation: "
                          f"{'yes (bad-txns-vout-script-toolarge)' if self.rdts_rejection['log_confirmed'] else 'no (getchaintips only)'}")
        elif self.rdts_rejection['injected']:
            self.log.info(f"  Rejection: not observed during this run")
        else:
            self.log.info(f"  Rejection: n/a (injection not sent)")

        # Final observed chain state (real node tips, not blocks_mined counters)
        self.observe_chain_state(int(time() - start_time))
        if self.chain_state['enabled']:
            cs = self.chain_state
            final = cs['final'] or {}
            self.log.info("")
            self.log.info("OBSERVED CHAIN STATE (real node tips)")
            self.log.info(f"  Final relation: {final.get('relation')} | "
                          f"Knots h={final.get('v27_height')} Core h={final.get('v26_height')}"
                          + (f" | LCA={final.get('fork_height')}, branches Knots={final.get('v27_branch_len')} "
                             f"Core={final.get('v26_branch_len')}" if final.get('relation') == 'diverged' else ""))
            self.log.info(f"  Reorgs observed: Knots={cs['reorg_count']['v27']} "
                          f"(max depth {cs['max_reorg_depth']['v27']}), "
                          f"Core={cs['reorg_count']['v26']} (max depth {cs['max_reorg_depth']['v26']})")
            self.log.info(f"  Tip relation changes: {len(cs['relation_changes'])}")
            self.log.info(f"  Injected tx: {final.get('injected_tx_state')}"
                          + (f" at height {final.get('injected_tx_height')}" if final.get('injected_tx_height') else ""))
            self.log.info(f"  Knots invalid branches (max seen): {cs['max_invalid_tips']}")
            for camp, label in (('v27', 'Knots'), ('v26', 'Core')):
                sv = cs['survival'][camp]
                self.log.info(f"  {label} blocks: mined={sv['mined']} surviving={sv['surviving']} "
                              f"orphaned={sv['orphaned']} (recent survival {sv['window_ratio']:.2f})")
            self.log.info(f"  Oracle chain source: {self.oracle_chain_source}")

        # Fork reunion (before final summary so we can log it inline)
        reunion_results = self.reunite_forks()

        # Final summary
        elapsed_min = (time() - start_time) / 60.0
        total_blocks = self.blocks_mined['v27'] + self.blocks_mined['v26']

        self.log.info(f"\n{'='*70}")
        self.log.info(f"Partition Mining Complete")
        self.log.info(f"{'='*70}")
        self.log.info(f"Duration: {elapsed_min:.2f} minutes")
        self.log.info(f"Blocks mined: v27={self.blocks_mined['v27']}, v26={self.blocks_mined['v26']}, total={total_blocks}")

        # Final prices
        v27_price = self.price_oracle.get_price('v27')
        v26_price = self.price_oracle.get_price('v26')

        self.log.info(f"\nFinal State:")
        self.log.info(f"  Prices: v27=${v27_price:,.0f}, v26=${v26_price:,.0f}")
        self.log.info(f"  Hashrate: v27={self.current_v27_hashrate:.1f}%, v26={self.current_v26_hashrate:.1f}%")
        self.log.info(f"  Economic: v27={self.current_v27_economic:.1f}%, v26={self.current_v26_economic:.1f}%")

        # Difficulty oracle summary
        if self.difficulty_oracle:
            self.log.info("")
            winner_id, winner_cw, loser_cw = self.difficulty_oracle.get_winning_fork()
            self.log.info(f"  Difficulty Model:")
            self.log.info(f"    Winning fork: {winner_id} (chainwork: {winner_cw:.4f} vs {loser_cw:.4f})")
            for fid, state in self.difficulty_oracle.forks.items():
                self.log.info(f"    {fid}: difficulty={state.current_difficulty:.6f}, "
                            f"chainwork={state.cumulative_chainwork:.4f}, "
                            f"chain_weight={self.difficulty_oracle.get_chain_weight(fid):.4f}")
            adj_count = len(self.difficulty_oracle.adjustment_history)
            eda_count = sum(1 for e in self.difficulty_oracle.adjustment_history if e.is_eda)
            self.log.info(f"    Retargets: {adj_count} (EDA: {eda_count})")

        # Pool strategy summary
        if self.pool_strategy:
            self.log.info("")
            self.pool_strategy.print_allocation_summary()

        # Economic strategy summary
        if self.economic_strategy:
            self.log.info("")
            self.economic_strategy.print_allocation_summary()

        # Dynamic partition switching summary
        if self.partition_switch_history:
            self.log.info("")
            self.log.info("=" * 50)
            self.log.info("DYNAMIC PARTITION SWITCHES")
            self.log.info("=" * 50)
            self.log.info(f"  Total switches: {len(self.partition_switch_history)}")

            # Count by direction
            v27_to_v26 = sum(1 for s in self.partition_switch_history if s['from'] == 'v27')
            v26_to_v27 = sum(1 for s in self.partition_switch_history if s['from'] == 'v26')
            self.log.info(f"  v27 -> v26: {v27_to_v26}")
            self.log.info(f"  v26 -> v27: {v26_to_v27}")

            # Final partition distribution
            v27_count = sum(1 for p in self.node_current_partition.values() if p == 'v27')
            v26_count = sum(1 for p in self.node_current_partition.values() if p == 'v26')
            self.log.info(f"  Final distribution: v27={v27_count} nodes, v26={v26_count} nodes")

            # List recent switches
            self.log.info("\n  Recent switches:")
            for switch in self.partition_switch_history[-10:]:
                self.log.info(f"    {switch['node']}: {switch['from']} -> {switch['to']} ({switch['reason']})")

        # Reorg oracle summary
        if self.reorg_oracle:
            # Calculate reunion analysis
            if self.difficulty_oracle:
                v27_chainwork = self.difficulty_oracle.get_cumulative_chainwork('v27')
                v26_chainwork = self.difficulty_oracle.get_cumulative_chainwork('v26')
            else:
                v27_chainwork = float(self.blocks_mined['v27'])
                v26_chainwork = float(self.blocks_mined['v26'])

            reunion = self.reorg_oracle.calculate_reunion_reorg(v27_chainwork, v26_chainwork)

            self.log.info("")
            self.reorg_oracle.print_summary()

            self.log.info(f"\nReunion Analysis (hypothetical partition merge):")
            self.log.info(f"  Winning fork: {reunion['winning_fork']}")
            self.log.info(f"  Losing fork depth: {reunion['losing_fork_depth']} blocks")
            self.log.info(f"  Nodes on losing fork: {reunion['num_nodes_on_losing_fork']}")
            self.log.info(f"  Reunion reorg mass: {reunion['reunion_reorg_mass']}")
            self.log.info(f"  Additional orphans on reunion: {reunion['additional_orphans']}")

        # UASF summary
        if self.options.uasf_duration is not None:
            self.log.info("")
            self.log.info("=" * 50)
            self.log.info("TIME-LIMITED UASF SUMMARY")
            self.log.info("=" * 50)
            self.log.info(f"  Duration configured: {self.options.uasf_duration}s ({self.options.uasf_duration/3600:.2f} hours)")
            self.log.info(f"  Expiry action: {self.options.uasf_expiry_action}")

            if self.uasf_expired and self.uasf_expiry_data:
                self.log.info(f"  UASF EXPIRED at {self.uasf_expiry_data['expiry_elapsed_seconds']}s")
                self.log.info(f"  Outcome: {self.uasf_expiry_data.get('uasf_outcome', 'unknown')}")

                state = self.uasf_expiry_data.get('state_at_expiry', {})
                self.log.info(f"  State at expiry:")
                self.log.info(f"    v27: {state.get('v27_blocks', 0)} blocks, chainwork={state.get('v27_chainwork', 0):.2f}")
                self.log.info(f"    v26: {state.get('v26_blocks', 0)} blocks, chainwork={state.get('v26_chainwork', 0):.2f}")
                self.log.info(f"    Winning fork: {state.get('winning_fork_at_expiry', 'unknown')}")

                if self.uasf_expiry_data.get('uasf_outcome') == 'failed':
                    self.log.info(f"  Orphaned blocks (v27): {self.uasf_expiry_data.get('orphaned_blocks', 0)}")
                    self.log.info(f"  Wasted chainwork: {self.uasf_expiry_data.get('wasted_chainwork', 0):.2f}")
            else:
                remaining = self.options.duration - (self.options.uasf_duration or 0)
                self.log.info(f"  UASF DID NOT EXPIRE (simulation ended before expiry)")
                self.log.info(f"  Remaining time before expiry: {remaining}s")

        # Export results
        try:
            import json
            import base64
            from datetime import datetime

            # Generate results ID if not provided
            results_id = self.options.results_id
            if not results_id:
                results_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Build consolidated results object
            consolidated_results = {
                'metadata': {
                    'results_id': results_id,
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': self.options.duration,
                    'pool_scenario': self.options.pool_scenario,
                    'economic_scenario': self.options.economic_scenario,
                    'difficulty_enabled': self.options.enable_difficulty,
                    'reorg_metrics_enabled': self.options.enable_reorg_metrics,
                    'interval': self.options.interval,
                    'start_height': self.options.start_height,
                    'partition_mode': self.options.partition_mode,
                    'fork_heal_exit': self.options.fork_heal_exit,
                    'uasf_duration': self.options.uasf_duration,
                    'uasf_expiry_action': self.options.uasf_expiry_action if self.options.uasf_duration else None,
                    'uasf_expired': self.uasf_expired,
                    'node_classification': self.options.node_classification,
                    'enable_manual_repartition': self.options.enable_manual_repartition,
                    'enable_asymmetric_bridging': self.options.enable_asymmetric_bridging,
                    'rdts_injection_enabled': self.options.rdts_injection,
                    'op_return_payload_size': self.options.op_return_payload_size,
                    'inplace_switching': self.options.inplace_switching,
                },
                'summary': {
                    'blocks_mined': dict(self.blocks_mined),
                    'total_blocks': self.blocks_mined['v27'] + self.blocks_mined['v26'],
                    'final_hashrate': {
                        'v27': self.current_v27_hashrate,
                        'v26': self.current_v26_hashrate,
                    },
                    'final_economic': {
                        'v27': self.current_v27_economic,
                        'v26': self.current_v26_economic,
                    },
                    'final_prices': {
                        'v27': self.price_oracle.get_price('v27'),
                        'v26': self.price_oracle.get_price('v26'),
                    },
                },
                'time_series': self.time_series,  # For charting
                'partition_switches': {
                    'total_switches': len(self.partition_switch_history),
                    'switches': self.partition_switch_history,
                    'final_partition_state': dict(self.node_current_partition),
                },
                'fork_convergence': dict(self.fork_convergence),
                'rdts_rejection': dict(self.rdts_rejection),
                'chain_state': self.chain_state,
                'inplace_switching': {
                    'enabled': self.options.inplace_switching,
                    'total_switches': sum(1 for e in self.inplace_switches if e['success']),
                    'failed_switches': sum(1 for e in self.inplace_switches if not e['success']),
                    'switches': self.inplace_switches,
                    'violating_blocks': list(self._violating_blocks),
                    'final_camps': {f"node-{n.index:04d}": camp
                                    for camp, nodes in (('v27', self.v27_nodes), ('v26', self.v26_nodes))
                                    for n in nodes},
                },
            }

            # Capture final snapshot
            self.capture_time_series_snapshot(int(time() - start_time))

            # Add oracle exports
            if self.pool_strategy:
                self.pool_strategy.export_to_json('/tmp/partition_pools.json')
                # Read back for consolidated export
                with open('/tmp/partition_pools.json', 'r') as f:
                    consolidated_results['pools'] = json.load(f)

            if self.economic_strategy:
                self.economic_strategy.export_to_json('/tmp/partition_economic.json')
                with open('/tmp/partition_economic.json', 'r') as f:
                    consolidated_results['economic'] = json.load(f)

            self.price_oracle.export_to_json('/tmp/partition_prices.json')
            with open('/tmp/partition_prices.json', 'r') as f:
                consolidated_results['prices'] = json.load(f)

            self.fee_oracle.export_to_json('/tmp/partition_fees.json')
            with open('/tmp/partition_fees.json', 'r') as f:
                consolidated_results['fees'] = json.load(f)

            if self.difficulty_oracle:
                self.difficulty_oracle.export_to_json('/tmp/partition_difficulty.json')
                with open('/tmp/partition_difficulty.json', 'r') as f:
                    consolidated_results['difficulty'] = json.load(f)

            if self.reorg_oracle:
                reorg_export = self.reorg_oracle.export_to_json()
                if self.difficulty_oracle:
                    v27_cw = self.difficulty_oracle.get_cumulative_chainwork('v27')
                    v26_cw = self.difficulty_oracle.get_cumulative_chainwork('v26')
                else:
                    v27_cw = float(self.blocks_mined['v27'])
                    v26_cw = float(self.blocks_mined['v26'])
                reorg_export['reunion_analysis'] = self.reorg_oracle.calculate_reunion_reorg(v27_cw, v26_cw)
                consolidated_results['reorg'] = reorg_export
                with open('/tmp/partition_reorg.json', 'w') as f:
                    json.dump(reorg_export, f, indent=2)

            # Fork reunion results
            consolidated_results['reunion'] = reunion_results

            # UASF expiry data
            if self.uasf_expiry_data is not None:
                consolidated_results['uasf'] = self.uasf_expiry_data
            elif self.options.uasf_duration is not None:
                # UASF was configured but didn't expire during simulation
                consolidated_results['uasf'] = {
                    'configured': True,
                    'duration_seconds': self.options.uasf_duration,
                    'expiry_action': self.options.uasf_expiry_action,
                    'expired': False,
                    'reason': 'simulation_ended_before_uasf_expiry'
                }

            # Save consolidated results to file
            with open('/tmp/partition_results.json', 'w') as f:
                json.dump(consolidated_results, f, indent=2)

            self.log.info(f"\n Results exported to /tmp/partition_*.json")
            self.log.info(f" Results ID: {results_id}")

            # Output base64-encoded results to logs for extraction
            # This survives pod termination since it's in the logs
            results_json = json.dumps(consolidated_results)
            results_b64 = base64.b64encode(results_json.encode()).decode()

            self.log.info(f"\n{'='*70}")
            self.log.info("RESULTS_EXPORT_START")
            self.log.info(f"RESULTS_ID:{results_id}")
            # Split into chunks for readability (some log systems have line limits)
            chunk_size = 1000
            for i in range(0, len(results_b64), chunk_size):
                self.log.info(f"RESULTS_DATA:{results_b64[i:i+chunk_size]}")
            self.log.info("RESULTS_EXPORT_END")
            self.log.info(f"{'='*70}")

        except Exception as e:
            self.log.error(f"Error exporting results: {e}")
            import traceback
            self.log.error(traceback.format_exc())

        self.log.info(f"{'='*70}\n")


def main():
    """Entry point for the Knots-vs-Core mesh fork pilot"""
    KnotsMeshPilot("").main()


if __name__ == "__main__":
    main()
