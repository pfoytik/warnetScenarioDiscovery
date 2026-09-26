#!/bin/bash
# Phase 1: shared history, then C (core mode) mines a block with an 81-byte
# OP_RETURN. Expect: A rejects (bad-txns-vout-script-toolarge), B and C accept.
# Then the Core branch (B+C) is made longer than A's branch.
source "$(dirname "$0")/lib.sh"
cli C createwallet w >/dev/null
ADDR=$(cli C getnewaddress)
cli C generatetoaddress 101 $ADDR >/dev/null
wait_sync "$(cli C getbestblockhash)" A B C && echo "shared history synced at h=$(height A)"

DATA=$(python3 -c "print('ab'*81)")
RAW=$(cli C createrawtransaction '[]' "{\"data\":\"$DATA\"}")
FUNDED=$(cli C fundrawtransaction $RAW | python3 -c "import json,sys;print(json.load(sys.stdin)['hex'])")
SIGNED=$(cli C signrawtransactionwithwallet $FUNDED | python3 -c "import json,sys;print(json.load(sys.stdin)['hex'])")
echo "--- mempool policy (core-mode C / core-mode B / rdts A):"
for n in C B A; do echo "$n: $(cli $n testmempoolaccept "[\"$SIGNED\"]" | python3 -c "import json,sys;r=json.load(sys.stdin)[0];print(r['allowed'], r.get('reject-reason',''))")"; done
TXID=$(cli C sendrawtransaction $SIGNED 2>&1) || true
echo "sendrawtransaction on C: $TXID"
if ! cli C getmempoolentry "$TXID" >/dev/null 2>&1; then
  echo "(policy rejected it — mining it directly with generateblock)"
  V=$(cli C generateblock $ADDR "[\"$SIGNED\"]" | python3 -c "import json,sys;print(json.load(sys.stdin)['hash'])")
  TXID=$(cli C decoderawtransaction $SIGNED | python3 -c "import json,sys;print(json.load(sys.stdin)['txid'])")
else
  V=$(cli C generatetoaddress 1 $ADDR | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
fi
echo "$V" > "$DIR/violating_block"; echo "$TXID" > "$DIR/violating_tx"
echo "violating block V=${V:0:12} contains tx: $(cli C getblock $V | grep -c $TXID)"
sleep 3
echo "--- A's view of V:"; cli A getchaintips | python3 -c "import json,sys;[print(' ',t['height'],t['hash'][:12],t['status']) for t in json.load(sys.stdin)]"
echo "A debug.log: $(docker exec ks-A grep -c 'bad-txns-vout-script-toolarge' /root/.bitcoin/regtest/debug.log) rejection line(s)"
# Core branch longer: C mines 5 more; A mines 2 on its own branch
cli C generatetoaddress 5 $ADDR >/dev/null
cli A createwallet w >/dev/null; AADDR=$(cli A getnewaddress)
cli A generatetoaddress 2 $AADDR >/dev/null
sleep 3
for n in A B C; do echo "$n: h=$(height $n) tip=$(tip $n)"; done
