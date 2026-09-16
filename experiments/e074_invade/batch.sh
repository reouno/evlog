#!/bin/bash
# The invasion runs of e074 (#72): `batch.sh <steps> <seed> [seed ...]` starts four runs a seed - two
# worlds (the community without the grazer, the community without the browser) times two injections
# (the grazer, the browser) - each from the pools `pick.py` wrote. Four runs a seed, so two seeds at a
# time keep 8 of the 12 cores.
#
# From the repo root:
#   bash experiments/e074_invade/batch.sh 40000 9 10
set -e
steps=$1; shift
out=experiments/e074_invade/results/invade
pools=experiments/e074_invade/results/pools
mkdir -p $out
for s in "$@"; do
  for world in A B; do
    for inj in A B; do
      name=m${world}_inj${inj}
      (EVLOG_OUT=$out EVLOG_POOL=$pools/life${s}_minus${world}.csv EVLOG_INJECT=$pools/life${s}_${inj}.csv \
        nohup bash experiments/e074_invade/run.sh c1225 "$steps" "$s" $name \
        seed_n=8000 inject_at=10000 inject_n=100 \
        > $out/life${s}_$name.log 2>&1 < /dev/null &)
    done
  done
done
sleep 2
echo "$(pgrep -x e074_invade | wc -l) runs going"
