#!/bin/bash
# The runs of e055 (#60): `run.sh <clock> <threads> <steps> <seeds>` runs e048's world (the season
# world under the motor, as e052-e054: relief 64, winter high 2, shade 2, spill 1, mutation 2/512,
# eyes 8, flesh 1, weight 1, side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2,
# flow 0, no ground store, k 1, sun 1, reach 0, no thirst, store 5, strict 1, sat 1, hold 1,
# wear 3,000, corners hold, plant yield 1, motor 1, no stock, no band, no brain, flat food) with
# <clock>: the exponent of a body's own time (0.5, 1: a clock that spans the sizes of this world;
# 0.25: e052's; a negative value is the flat-pace control, |clock| turns a step whatever the mass).
# From the repo root:
#   (nohup bash experiments/e055_span/run.sh 0.5 1 100000 9 10 11 12 > experiments/e055_span/results/batch.log 2>&1 < /dev/null &)
set -e
clock=$1; threads=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e055_span $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 0 0 1 1 1 3000 2 1 1 0 0 $clock &
done
wait
echo DONE clock $clock steps $steps seeds "$@"
