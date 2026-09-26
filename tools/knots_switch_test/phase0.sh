#!/bin/bash
# Phase 0: bring up A (rdts), B (core mode, will switch), C (core mode); check
# includeconf works and what RDTS status a Knots node has with no vbparams.
source "$(dirname "$0")/lib.sh"
cleanup
docker network create $NET >/dev/null
for n in A B C; do write_conf $n; docker volume create ks-$n-data >/dev/null; done
set_mode A rdts; set_mode B core; set_mode C core
for n in A B C; do start_node $n; done
for n in A B C; do wait_rpc $n || { docker logs ks-$n | tail -20; exit 1; }; done
for n in A B C; do echo "$n: version=$(cli $n getnetworkinfo | python3 -c 'import json,sys;print(json.load(sys.stdin)["subversion"])')  rdts(active,status)=$(rdts_status $n)"; done
echo "--- deployment names on B:"; cli B getdeploymentinfo | python3 -c "import json,sys; print(list(json.load(sys.stdin)['deployments']))"
cli A addnode ks-B onetry; cli B addnode ks-C onetry; cli C addnode ks-A onetry
sleep 2
for n in A B C; do echo "$n peers: $(cli $n getconnectioncount)"; done
