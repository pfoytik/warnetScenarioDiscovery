#!/bin/bash
# Shared helpers for the Knots in-place RDTS switch test.
# Mirrors warnet: read-only bitcoin.conf (ConfigMap subPath), writable datadir
# volume (emptyDir), restart-always container (restartPolicy: Always).
DIR="$(cd "$(dirname "$0")" && pwd)"
IMG=bitcoin-knots:29.4-local
NET=knots-switch-test
RDTS_VB='vbparams=reduced_data:-1:9223372036854775807'

cli() { local n=$1; shift; docker exec "ks-$n" bitcoin-cli -regtest -rpcuser=user -rpcpassword=pw "$@"; }

write_conf() {  # name [peer...] — addnode goes in the conf, as warnet does, so peers survive restarts
  local name=$1; shift
  cat > "$DIR/$name.conf" <<EOF
regtest=1
includeconf=switch.conf
[regtest]
checkmempool=0
debuglogfile=debug.log
fallbackfee=0.00001000
listen=1
server=1
txindex=1
rpcuser=user
rpcpassword=pw
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0
consensusrules=rdts
EOF
  for p in "$@"; do echo "addnode=ks-$p" >> "$DIR/$name.conf"; done
}

set_mode() {  # name rdts|core   (writes datadir/switch.conf inside the container volume)
  local body="[regtest]"
  [ "$2" = rdts ] && body="[regtest]
$RDTS_VB"
  docker run --rm -v "ks-$1-data:/d" alpine sh -c "printf '%s\n' '$body' > /d/switch.conf"
}

start_node() {  # name
  docker run -d --name "ks-$1" --network $NET --restart always \
    -v "ks-$1-data:/root/.bitcoin" -v "$DIR/$1.conf:/root/.bitcoin/bitcoin.conf:ro" \
    $IMG bitcoind >/dev/null
}

wait_rpc() { for i in $(seq 60); do cli "$1" getblockcount >/dev/null 2>&1 && return 0; sleep 1; done; echo "RPC timeout $1"; return 1; }

restart_via_stop() {  # name — RPC stop, let restart policy bring it back (like k8s Always)
  cli "$1" stop >/dev/null; sleep 3; wait_rpc "$1"
}

rdts_status() { cli "$1" getdeploymentinfo | python3 -c "import json,sys; d=json.load(sys.stdin)['deployments']; r=[v for k,v in d.items() if 'reduced' in k or 'rdts' in k.lower()]; print(r[0].get('active'), r[0].get('bip9',{}).get('status'))" 2>/dev/null || echo "no-deployment-info"; }

tip() { cli "$1" getbestblockhash | cut -c1-12; }
height() { cli "$1" getblockcount; }

wait_sync() {  # expected_hash nodes...
  local h=$1; shift
  for i in $(seq 30); do ok=1; for n in "$@"; do [ "$(cli $n getbestblockhash)" = "$h" ] || ok=0; done; [ $ok = 1 ] && return 0; sleep 1; done
  return 1
}

cleanup() {
  docker rm -f ks-A ks-B ks-C >/dev/null 2>&1
  docker volume rm ks-A-data ks-B-data ks-C-data >/dev/null 2>&1
  docker network rm $NET >/dev/null 2>&1
}
