#!/bin/bash
# The invasion runs of e076 (#92): `batch.sh <steps> <seed> [seed ...]` starts four runs a seed - two
# one-kind worlds times two draws of the injection (`inject_seed` 1 and 2) - from the pools `pick.py`
# wrote. Both lines go into each world at once, a hundred bodies each at step 10,000: mark 1 is the
# grazer's genomes, mark 2 the hunter's.
#
#   oA  a world of the grazer alone: mark 2 (the hunter) is the invader, mark 1 the neutral control
#   oB  a world of the hunter alone: mark 1 (the grazer) is the invader, mark 2 the neutral control
#
# Four runs a seed, so two seeds at a time keep 8 of the 12 cores.
#   bash experiments/e076_pair/batch.sh 40000 9 10
set -e
steps=$1; shift
out=experiments/e076_pair/results/invade
pools=experiments/e076_pair/results/pools
mkdir -p $out
for s in "$@"; do
  for one in A B; do
    for draw in 1 2; do
      name=o${one}_s${draw}
      (EVLOG_OUT=$out EVLOG_POOL=$pools/life${s}_${one}.csv \
        EVLOG_INJECT=$pools/life${s}_A.csv:$pools/life${s}_B.csv \
        nohup bash experiments/e076_pair/run.sh c1225 "$steps" "$s" $name \
        seed_n=9000 inject_at=10000 inject_n=100 inject_seed=$draw \
        > $out/life${s}_$name.log 2>&1 < /dev/null &)
    done
  done
done
sleep 2
echo "$(pgrep -x e075_hunt | wc -l) runs going"
