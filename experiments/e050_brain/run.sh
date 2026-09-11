#!/bin/bash
# The runs of e050 (#53): `run.sh <brain> <band> <thirst> <threads> <steps> <seeds>` runs e049's
# world (e048's season world under the motor: relief 64, winter high 2, shade 2, spill 1, mutation
# 2/512, eyes 8, flesh 1, weight 1, side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix
# 0.2, flow 0, no ground store, k 1, sun 1, reach 0, stock 0, store 5, strict 1, sat 1, hold 1,
# wear 3,000, corners hold, plant yield 1, motor 1) with <band> (e049: 0 the sky rains on every cell
# alike, N all the sky's rain on a band a quarter of the world wide that moves west one world cell
# every N steps), <thirst> (e040: the fill a body loses a step; 0: no body needs water) and <brain>:
# 0 e049's policy (e049 byte for byte), 1 the brain (hidden units in the sensor blocks, weights into
# the outputs that learn from the energy balance, the body ahead compared).
# From the repo root:
#   (nohup bash experiments/e050_brain/run.sh 1 25 0.005 1 100000 9 10 11 12 > experiments/e050_brain/results/batch.log 2>&1 < /dev/null &)
set -e
brain=$1; band=$2; thirst=$3; threads=$4; steps=$5; shift 5
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e050_brain $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 $thirst 0 1 1 1 3000 2 1 1 $band $brain &
done
wait
echo DONE brain $brain band $band thirst $thirst steps $steps seeds "$@"
