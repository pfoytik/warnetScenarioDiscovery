#!/usr/bin/env python3
"""
Drive knots_mesh_pilot.py's --violation-rate and per-node outcome code against
the 3 Docker Knots containers from phase0.sh (see scenario_harness.py):

  A = node-0000, pool "knotspool", v27 (RDTS)
  B = node-0001, economic node (custody 100 BTC), v26 (Core mode)
  C = node-0002, pool "corepool", v26 (Core mode)

  bash phase0.sh
  /home/pfoytik/bitcoinTools/warnet/warnet/.venv/bin/python3 violation_harness.py
  source lib.sh && cleanup
"""
import sys
import time
from types import SimpleNamespace

from scenario_harness import DockerNode, Fake, check, make_scenario, tip, settle, wait_until, FAILS


class FakePools(Fake):
    def __init__(self, allocation):
        super().__init__(allocation)
        self.pools = {p: SimpleNamespace() for p in allocation}

    def get_pool_summary(self, pool_id):
        return {'hashrate_pct': 50.0, 'fork_preference': 'neutral',
                'cumulative_opportunity_cost_usd': 0.0,
                'ideology_override_count': 0, 'forced_switch_count': 0}


class FakeEcon(Fake):
    def __init__(self, allocation, profiles):
        super().__init__(allocation)
        self.nodes = profiles


def main():
    A, B, C = DockerNode(0, 'ks-A'), DockerNode(1, 'ks-B'), DockerNode(2, 'ks-C')
    s = make_scenario([A, B, C])
    s.options.violation_rate = 0.0
    s.options.start_height = 101
    s.pool_strategy = FakePools({'knotspool': 'v27', 'corepool': 'v26'})
    s.economic_strategy = FakeEcon({'node-0001': 'v26'}, {'node-0001': SimpleNamespace(
        custody_btc=100.0, daily_volume_btc=1.0, node_type='economic', fork_preference='neutral',
        ideology_strength=0.0, initial_fork='v26')})
    s._vtxs, s._vtx_blocks, s._vsource, s._violation_block_log = [], {}, None, []
    s._mined_by_node, s._alloc_timeline = {}, {}
    s._active_chain = {'v27': {}, 'v26': {}}
    s.chain_state = {'final': {'relation': 'diverged'}}
    s.current_v27_hashrate, s.current_v26_hashrate = 50.0, 50.0
    s.current_v27_economic, s.current_v26_economic = 0.0, 100.0

    s.classify_nodes_by_rdts()
    s.build_pool_node_mapping(verbose=False)
    s._record_allocations(0)
    B.generatetoaddress(101, s._ensure_miner(B).getnewaddress())
    settle()

    print("\n[1] fund_violation_source")
    s.fund_violation_source()
    check(s._vsource is not None and s.rdts_rejection['injected'], "anyone-can-spend source funded")
    check(tip(A) == tip(B) == tip(C), "funding block in shared history on all nodes")
    check(s._injected_tx_state() == ('none', None), "state 'none' before any violation")

    def mine(node, camp, n=1):
        addr = s._ensure_miner(node).getnewaddress()
        for _ in range(n):
            s._record_mined(node, s._mine_block(node, camp, addr))

    print("\n[2] violation_rate=0: Core blocks stay valid to Knots (no split)")
    mine(C, 'v26', 3)
    settle()
    check(len(s._vtxs) == 0, "no violating txs created")
    check(tip(A) == tip(C), "A (RDTS) follows Core-mode blocks")

    print("\n[3] violation_rate=1: every Core block adds a violation")
    s.options.violation_rate = 1.0
    mine(C, 'v26', 2)
    settle()
    check(len(s._vtxs) == 2 and len(s._violating_blocks) == 2, "2 txs in 2 blocks")
    check([e['txs'] for e in s._violation_block_log] == [1, 1], "one new tx per block")
    check(tip(A) != tip(C) and tip(B) == tip(C), "A rejects, B follows C: split")
    state, k = s._injected_tx_state()
    check(state == 'confirmed' and k == 2, f"state 'confirmed', 2 on Core chain (got {state}, {k})")
    bad = [t for t in A.getchaintips() if t['status'] == 'invalid']
    reason = B.getblock(s._violating_blocks[0])  # exists on Core chain
    check(len(bad) >= 1, "A has an invalid tip")

    print("\n[4] wipe-out, then violation_rate=0: earlier txs still re-included")
    mine(A, 'v27', 5)
    waited = wait_until(lambda: tip(C) == tip(A) and tip(B) == tip(A))
    check(waited is not None, f"Core-mode B, C reorg onto heavier RDTS chain ({waited}s)")
    state, k = s._injected_tx_state()
    check(state == 'pending' and k == 0, f"after wipe-out: 'pending', 0 on chain (got {state}, {k})")
    s.options.violation_rate = 0.0
    mine(C, 'v26')
    check(s._violation_block_log[-1]['txs'] == 2 and len(s._vtxs) == 2,
          "next Core block re-includes both pending txs, no new one")
    settle()
    check(tip(A) != tip(C), "split re-forms")
    mine(C, 'v26')
    check(len(s._violation_block_log) == 3, "following Core block (vr=0, nothing pending) is clean")

    print("\n[5] in-place switch into RDTS invalidates multiple violating blocks")
    s.economic_strategy.current_allocation['node-0001'] = 'v27'
    s.reconcile_node_modes(60, 'economic decision')
    s._record_allocations(60)
    ev = s.inplace_switches[-1]
    check(ev['success'] and ev.get('invalidated', 0) >= 1, f"B switched, invalidated={ev.get('invalidated')}")
    waited = wait_until(lambda: tip(B) == tip(A))
    check(waited is not None, f"B on the RDTS chain ({waited}s)")

    print("\n[6] compute_outcomes")
    s.price_oracle = SimpleNamespace(base_price=60000,
                                     get_price=lambda c: {'v27': 66000, 'v26': 54000}[c])
    time.sleep(1)
    out = s.compute_outcomes(120)
    nodes = out['nodes']
    check(out['winner']['by_price'] == 'v27', "winner by price = v27")
    a, b, c = nodes['node-0000'], nodes['node-0001'], nodes['node-0002']
    check(a['role'] == 'pool' and a['blocks_mined'] == 5 and a['blocks_orphaned'] == 0,
          f"knotspool: 5 mined, 0 orphaned (got {a.get('blocks_mined')}, {a.get('blocks_orphaned')})")
    check(c['role'] == 'pool' and c['blocks_mined'] == 7,
          f"corepool: 7 mined (got {c.get('blocks_mined')})")
    check(c['blocks_on_winning_chain'] == 3,
          f"corepool: only the 3 pre-violation blocks are on the winning chain "
          f"(got {c['blocks_on_winning_chain']})")
    check(b['role'] == 'economic' and b['initial_camp'] == 'v26' and b['final_camp'] == 'v27'
          and b['fork_changes'] == 1, "B: v26 -> v27, 1 change")
    check(b['time_on_v26_s'] == 60 and b['time_on_v27_s'] == 60, "B: 60s on each fork")
    check(abs(b['value_change_usd'] - 100 * 6000) < 1e-6 and b['on_winning_fork'] and b['regret_usd'] == 0,
          f"B: +$600k, on winner, no regret (got {b['value_change_usd']})")
    check(abs(b['value_if_stayed_usd'] - 100 * 54000) < 1e-6, "B: value if stayed = 100 x $54k")
    check(b['inplace_switches'] == 1, "B: 1 in-place switch recorded")
    print(f"    summary: {out['summary']}")

    print(f"\n{'ALL PASSED' if not FAILS else f'{len(FAILS)} FAILED: {FAILS}'}")
    sys.exit(1 if FAILS else 0)


if __name__ == '__main__':
    main()
