#!/bin/bash
# The invasion runs of e074 (#72): `batch.sh <steps> <minus|only> <seed> [seed ...]` starts four runs
# a seed - two worlds times two draws of the injection (`inject_seed` 1 and 2) - from the pools
# `pick.py` wrote. Both lines go into each world at once: mark 1 is the grazer's genomes, mark 2 is
# the browser's, a hundred bodies each.
#
#   minus  the community with a way of living taken out (`minusA`, `minusB`): in the world without
#          the browsers, mark 2 is the invader and mark 1 the neutral control, and the other way
#          round in the world without the land's grass eaters.
#   only   a world of one kind alone (`A`, `B`), #72's own wording: in the grazer's world mark 2 is
#          the invader, in the browser's world mark 1 is.
#
# Four runs a seed, so two seeds at a time keep 8 of the 12 cores.
#   bash experiments/e074_invade/batch.sh 40000 minus 9 10
set -e
steps=$1; kind=$2; shift 2
out=experiments/e074_invade/results/invade
pools=experiments/e074_invade/results/pools
mkdir -p $out
for s in "$@"; do
  for one in A B; do
    case $kind in
      minus) pool=$pools/life${s}_minus${one}.csv; tag=m$one ;;
      only)  pool=$pools/life${s}_${one}.csv;      tag=o$one ;;
      *) echo "usage: batch.sh <steps> <minus|only> <seed> ..."; exit 1 ;;
    esac
    for draw in 1 2; do
      name=${tag}_s${draw}
      (EVLOG_OUT=$out EVLOG_POOL=$pool \
        EVLOG_INJECT=$pools/life${s}_A.csv:$pools/life${s}_B.csv \
        nohup bash experiments/e074_invade/run.sh c1225 "$steps" "$s" $name \
        seed_n=8000 inject_at=10000 inject_n=100 inject_seed=$draw \
        > $out/life${s}_$name.log 2>&1 < /dev/null &)
    done
  done
done
sleep 2
echo "$(pgrep -x e074_invade | wc -l) runs going"
