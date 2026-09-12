#!/bin/bash
# The runs of e057 (#56): `run.sh <foul> <threads> <steps> <seeds>` runs e056's world (e055's
# season world under the clock: relief 64, winter high 2, shade 2, spill 1, mutation 2/512,
# eyes 8, flesh 1, weight 1, side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2,
# flow 0, no ground store, k 1, reach 0, no thirst, store 5, strict 1, sat 1, hold 1, wear
# 3,000, corners hold, plant yield 1, motor 1, no stock, no band, no brain, flat food, clock
# 0.5, sun 1, patch 4,096) with <foul>: the waste a body lays per step on a whole world cell it
# covers (0 is e056 byte for byte).
# From the repo root:
#   (nohup bash experiments/e057_foul/run.sh 0.01 1 100000 9 10 11 12 13 14 > experiments/e057_foul/results/batch_foul0.01.log 2>&1 < /dev/null &)
set -e
foul=$1; threads=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e057_foul $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 0 0 1 1 1 3000 2 1 1 0 0 0.5 4096 $foul &
done
wait
echo DONE foul $foul steps $steps seeds "$@"
