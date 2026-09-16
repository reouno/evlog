#!/bin/bash
# The invasion runs of e074 (#72): `batch.sh <steps> <seed> [seed ...]` starts four runs a seed - two
# worlds (the community without the grazer, the community without the browser) times two draws of the
# injection (`inject_seed` 1 and 2) - from the pools `pick.py` wrote. Both lines go into each world at
# once: mark 1 is the grazer's genomes, mark 2 is the browser's, a hundred bodies each. In the world
# without the browser, mark 2 is the invader and mark 1 the neutral control; in the world without the
# grazer it is the other way round.
#
# Four runs a seed, so two seeds at a time keep 8 of the 12 cores.
#   bash experiments/e074_invade/batch.sh 40000 9 10
set -e
steps=$1; shift
out=experiments/e074_invade/results/invade
pools=experiments/e074_invade/results/pools
mkdir -p $out
for s in "$@"; do
  for world in A B; do
    for draw in 1 2; do
      name=m${world}_s${draw}
      (EVLOG_OUT=$out EVLOG_POOL=$pools/life${s}_minus${world}.csv \
        EVLOG_INJECT=$pools/life${s}_A.csv:$pools/life${s}_B.csv \
        nohup bash experiments/e074_invade/run.sh c1225 "$steps" "$s" $name \
        seed_n=8000 inject_at=10000 inject_n=100 inject_seed=$draw \
        > $out/life${s}_$name.log 2>&1 < /dev/null &)
    done
  done
done
sleep 2
echo "$(pgrep -x e074_invade | wc -l) runs going"
