#!/bin/bash
# Phase 2: switch B core -> rdts in place (rewrite switch.conf, RPC stop, restart
# policy brings it back). Then invalidateblock V to leave the Core branch.
# Then C mines a NEW violating block; B must now reject it by consensus.
source "$(dirname "$0")/lib.sh"
V=$(cat "$DIR/violating_block")
echo "before: B h=$(height B) tip=$(tip B) rdts=$(rdts_status B)"
set_mode B rdts
T0=$(date +%s); restart_via_stop B; echo "restart took $(( $(date +%s) - T0 ))s"
echo "after restart: B h=$(height B) tip=$(tip B) rdts=$(rdts_status B)  peers=$(cli B getconnectioncount)"
echo "(expected: still on Core branch — old blocks are not re-validated)"
cli B invalidateblock $V
sleep 2
echo "after invalidateblock V: B h=$(height B) tip=$(tip B)   A tip=$(tip A)"
# B's peers after restart: re-add (warnet addnode entries are in bitcoin.conf, so they'd persist; here they were RPC-added)
cli B addnode ks-A onetry; cli B addnode ks-C onetry; sleep 2
AADDR=$(cli A getnewaddress); cli A generatetoaddress 1 $AADDR >/dev/null
wait_sync "$(cli A getbestblockhash)" A B && echo "B follows A's new block: OK (h=$(height B))" || echo "B did NOT follow A"
# New violating block from C
ADDR=$(cli C getnewaddress); DATA=$(python3 -c "print('cd'*81)")
RAW=$(cli C createrawtransaction '[]' "{\"data\":\"$DATA\"}")
F=$(cli C fundrawtransaction $RAW | python3 -c "import json,sys;print(json.load(sys.stdin)['hex'])")
S=$(cli C signrawtransactionwithwallet $F | python3 -c "import json,sys;print(json.load(sys.stdin)['hex'])")
V2=$(cli C generateblock $ADDR "[\"$S\"]" | python3 -c "import json,sys;print(json.load(sys.stdin)['hash'])")
echo "$V2" > "$DIR/violating_block2"
# Make C's branch clearly heaviest so B would follow it if it didn't enforce
cli C generatetoaddress 5 $ADDR >/dev/null; sleep 4
echo "C h=$(height C); B h=$(height B) tip=$(tip B)  A tip=$(tip A)"
echo "B's view of C's branch:"; cli B getchaintips | python3 -c "import json,sys;[print(' ',t['height'],t['hash'][:12],t['status']) for t in json.load(sys.stdin)]"
echo "B debug.log rejection lines: $(docker exec ks-B grep -c 'bad-txns-vout-script-toolarge' /root/.bitcoin/regtest/debug.log)"
