#!/bin/bash
# The runs of e056 (#65): `run.sh <sun> <threads> <steps> <seeds>` runs e055's world (the season
# world under the clock, as e055 kept it: relief 64, winter high 2, shade 2, spill 1, mutation
# 2/512, eyes 8, flesh 1, weight 1, side grow, rain flat, water 0.1, leach 0.01, depth 0.01,
# mix 0.2, flow 0, no ground store, k 1, reach 0, no thirst, store 5, strict 1, sat 1, hold 1,
# wear 3,000, corners hold, plant yield 1, motor 1, no stock, no band, no brain, flat food,
# clock 0.5) with <sun>: the factor on the regrowth of every cell and on the rain's cap with it
# (1 is e055's world; 2 and 4 are e038's richer suns).
# From the repo root:
#   (nohup bash experiments/e056_sun/run.sh 2 1 100000 9 10 11 12 > experiments/e056_sun/results/batch_sun2.log 2>&1 < /dev/null &)
set -e
sun=$1; threads=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e056_sun $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 $sun 0 0 0 0 1 1 1 3000 2 1 1 0 0 0.5 &
done
wait
echo DONE sun $sun steps $steps seeds "$@"
