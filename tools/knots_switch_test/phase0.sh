#!/bin/bash
# Phase 0: bring up A (rdts), B (core mode, will switch), C (core mode); check
# includeconf works and what RDTS status a Knots node has with no vbparams.
source "$(dirname "$0")/lib.sh"
cleanup
docker network create $NET >/dev/null
write_conf A B; write_conf B C; write_conf C A   # ring: A->B->C->A
for n in A B C; do docker volume create ks-$n-data >/dev/null; done
set_mode A rdts; set_mode B core; set_mode C core
for n in A B C; do start_node $n; done
for n in A B C; do wait_rpc $n || { docker logs ks-$n | tail -20; exit 1; }; done
for n in A B C; do echo "$n: version=$(cli $n getnetworkinfo | python3 -c 'import json,sys;print(json.load(sys.stdin)["subversion"])')  rdts(active,status)=$(rdts_status $n)"; done
echo "--- deployment names on B:"; cli B getdeploymentinfo | python3 -c "import json,sys; print(list(json.load(sys.stdin)['deployments']))"
sleep 3
for n in A B C; do echo "$n peers: $(cli $n getconnectioncount)"; done
