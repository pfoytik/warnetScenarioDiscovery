#!/usr/bin/env python3
"""
Drive knots_mesh_pilot.py's real --inplace-switching code against 3 Docker
Knots containers (no Kubernetes). Pod exec is replaced by `docker exec`, and
Docker's --restart always stands in for restartPolicy: Always.

  A = node-0000, pool "knotspool", starts v27 (RDTS)
  B = node-0001, economic node,     starts v26 (Core mode)
  C = node-0002, pool "corepool",  starts v26 (Core mode)

Run with warnet's venv python (needs the kubernetes module for the import):
  bash phase0.sh   # starts ks-A/B/C (only phase0 — this script does the rest)
  /home/pfoytik/bitcoinTools/warnet/warnet/.venv/bin/python3 scenario_harness.py
  source lib.sh && cleanup
"""
import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

sys.argv = sys.argv[:1]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scenarios'))
from test_framework.authproxy import AuthServiceProxy  # noqa: E402
import knots_mesh_pilot as kmp  # noqa: E402  (imports commander -> fresh-connection RPC patch)

logging.basicConfig(level=logging.INFO, format='%(message)s')
FAILS = []


def check(cond, msg):
    print(("  PASS " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


class DockerNode:
    """Just enough of warnet's TestNode for the scenario methods."""
    def __init__(self, index, container):
        self.index, self.tank, self.container = index, container, container
        ip = subprocess.check_output(
            ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}',
             container], text=True).strip()
        self.url = f"http://user:pw@{ip}:18443"
        self._rpc = AuthServiceProxy(self.url, timeout=30)

    def get_wallet_rpc(self, name):
        return AuthServiceProxy(f"{self.url}/wallet/{name}", timeout=30)

    def __getattr__(self, name):
        return getattr(self._rpc, name)


class Fake:
    def __init__(self, allocation):
        self.current_allocation = allocation
        self.pools = {k: None for k in allocation}


def make_scenario(nodes):
    A, B, C = nodes
    s = object.__new__(kmp.KnotsMeshPilot)
    s.options = argparse.Namespace(
        inplace_switching=True, switch_restart_timeout=90, rdts_injection=True,
        op_return_payload_size=81, node_classification='rdts', violation_rate=None)
    s.log = logging.getLogger('harness')
    s.nodes = nodes
    s.v27_nodes, s.v26_nodes = [], []
    s.node_metadata = {
        'node-0000': {'entity_id': 'pool-knotspool', 'node_type': 'mining_pool'},
        'node-0001': {'node_type': 'economic', 'image_tag': '26-core-mode'},
        'node-0002': {'entity_id': 'pool-corepool', 'node_type': 'mining_pool'},
    }
    s.pool_strategy = Fake({'knotspool': 'v27', 'corepool': 'v26'})
    s.economic_strategy = Fake({'node-0001': 'v26'})
    s.pool_nodes_v27, s.pool_nodes_v26 = {}, {}
    s.node_current_partition = {}
    s.inplace_switches, s._violating_blocks, s._violating_tx_hex = [], [], None
    s.rdts_rejection = {'injected': False, 'rejected': False}
    s.generatetoaddress = lambda node, n, addr, sync_fun=None: node.generatetoaddress(n, addr)
    s._exec_on_tank = lambda node, cmd: subprocess.run(
        ['docker', 'exec', node.container, 'sh', '-c', cmd],
        capture_output=True, text=True).stdout
    return s


def tip(n):
    return n.getbestblockhash()


def settle(seconds=4):
    time.sleep(seconds)


def wait_until(pred, timeout=90):
    """Poll pred() — a restarted node's inbound peers come back on their
    addnode retry cycle (~60s), so convergence after a switch can lag."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if pred():
            return round(time.time() - t0, 1)
        time.sleep(2)
    return None


def main():
    A, B, C = DockerNode(0, 'ks-A'), DockerNode(1, 'ks-B'), DockerNode(2, 'ks-C')
    s = make_scenario([A, B, C])

    print("\n[1] classify_nodes_by_rdts")
    s.classify_nodes_by_rdts()
    check(s.v27_nodes == [A] and s.v26_nodes == [B, C], "A=v27, B,C=v26")
    s.build_pool_node_mapping()

    print("\n[2] common history + held injection")
    B.generatetoaddress(101, s._ensure_miner(B).getnewaddress())
    settle()
    s.inject_rdts_violation()
    check(s._violating_tx_hex is not None and s.rdts_rejection['injected'], "tx signed and held")
    check(s._injected_tx_state()[0] == 'pending', "tx state 'pending' before any Core-mode block")

    print("\n[3] Core-mode pool mines -> violating block via generateblock")
    addr_c = s._ensure_miner(C).getnewaddress()
    v1 = s._mine_block(C, 'v26', addr_c)[0]
    check(s._violating_blocks == [v1], "violating block recorded")
    s._mine_block(C, 'v26', addr_c)
    check(len(s._violating_blocks) == 1, "not re-included while already on C's chain")
    s._mine_block(C, 'v26', addr_c)
    waited = wait_until(lambda: tip(B) == tip(C), timeout=90)
    print(f"    (B synced to C after {waited}s)")
    check(any(t['hash'] == v1 and t['status'] == 'invalid' for t in A.getchaintips())
          or A.getblockheader(v1).get('confirmations', -1) < 0, "A (RDTS) rejects violating block")
    check(tip(B) == tip(C), "B follows C (Core mode accepts)")
    check(s._injected_tx_state()[0] == 'confirmed', "tx state 'confirmed' on Core camp")
    addr_a = s._ensure_miner(A).getnewaddress()
    s._mine_block(A, 'v27', addr_a)  # A's own short branch
    settle()

    print("\n[4] economic decision: B v26 -> v27 (in place)")
    s.economic_strategy.current_allocation['node-0001'] = 'v27'
    s.reconcile_node_modes(10, 'economic decision')
    ev = s.inplace_switches[-1]
    check(ev['success'] and ev['to'] == 'v27' and ev.get('invalidated', 0) >= 1,
          f"B switched, invalidated={ev.get('invalidated')}, downtime={ev.get('downtime_s')}s")
    check(B in s.v27_nodes and s._rdts_active(B), "B tracked and enforcing RDTS")
    waited = wait_until(lambda: tip(B) == tip(A))
    check(waited is not None,
          f"B now on A's (RDTS) chain although Core chain is heavier (converged after {waited}s)")

    print("\n[5] pool decision: corepool v26 -> v27; its own node C switches")
    s.pool_strategy.current_allocation['corepool'] = 'v27'
    s.reconcile_node_modes(20, 'pool decision')
    ev = s.inplace_switches[-1]
    check(ev['success'] and ev['node'] == 'node-0002' and ev['to'] == 'v27', "C switched")
    check(s.pool_nodes_v27.get('corepool') == [C] and 'corepool' not in s.pool_nodes_v26,
          "pool mapping rebuilt: corepool mines from its own node on v27")
    check("miner" in C.listwallets(), "C's miner wallet reloaded after restart")
    for _ in range(4):
        s._mine_block(C, 'v27', s._ensure_miner(C).getnewaddress())
    settle()
    check(tip(A) == tip(B) == tip(C), "all three on the RDTS chain, which is now heaviest")

    print("\n[6] pool decision: corepool back to v26; wipe-out re-mine")
    s.pool_strategy.current_allocation['corepool'] = 'v26'
    s.reconcile_node_modes(30, 'pool decision')
    ev = s.inplace_switches[-1]
    check(ev['success'] and ev['to'] == 'v26' and ev.get('reconsidered', 0) >= 1,
          f"C switched back, reconsidered={ev.get('reconsidered')}")
    check(s._violation_in_chain(C) is None, "C sits on the heavier RDTS chain (Core branch wiped out)")
    v2 = s._mine_block(C, 'v26', s._ensure_miner(C).getnewaddress())[0]
    check(len(s._violating_blocks) == 2 and s._violating_blocks[-1] == v2,
          "C re-mines the violating tx on top (as a Core miner would)")
    settle()
    check(tip(A) != tip(C) and tip(B) == tip(A), "A and B (RDTS) reject it; split re-forms")

    print("\n[7] results payload")
    ok = sum(e['success'] for e in s.inplace_switches)
    check(ok == 3 and len(s.inplace_switches) == 3, f"{ok}/3 switch events recorded as success")
    for e in s.inplace_switches:
        print(f"    {e['node']} {e['role']}: {e['from']}->{e['to']} ({e['trigger']}) "
              f"downtime={e.get('downtime_s')}s h {e.get('height_before')}->{e.get('height_after')}")

    print(f"\n{'ALL PASSED' if not FAILS else f'{len(FAILS)} FAILED: {FAILS}'}")
    sys.exit(1 if FAILS else 0)


if __name__ == '__main__':
    main()
