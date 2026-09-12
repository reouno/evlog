#!/bin/bash
# The runs of e059 (#69): `run.sh <sigma> <patch> <sun> <threads> <steps> <seeds>` runs e058's
# thin world (e055's season world: relief 64, winter high 2, shade 2, spill 1, mutation 2/512,
# eyes 8, flesh 1, weight 1, side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2,
# flow 0, k 1, store 5, strict 1, sat 1, hold 1, wear 3,000, corners hold, motor 1, clock 0.5,
# no thirst, no band, no brain, no fouling) with:
#   <sigma>  the width of a food patch in cells (0: the uniform sun of e019-e058)
#   <patch>  the cells of the world per patch, so the grain of the food (4096 since e011)
#   <sun>    the factor on every cell's regrowth and on the rain's cap (1: the world of e055-e057)
# From the repo root:
#   (nohup bash experiments/e059_places/run.sh 12 1810 0.2 1 300000 9 10 11 12 > experiments/e059_places/results/batch.log 2>&1 < /dev/null &)
set -e
sigma=$1; patch=$2; sun=$3; threads=$4; steps=$5; shift 5
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e059_places $steps $s 128 $sigma 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 $sun 0 0 0 0 1 1 1 3000 2 1 1 0 0 0.5 $patch 0 &
done
wait
echo DONE sigma $sigma patch $patch sun $sun steps $steps seeds "$@"
