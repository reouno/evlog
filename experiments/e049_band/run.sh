#!/bin/bash
# The runs of e049 (#14): `run.sh <band> <thirst> <threads> <steps> <seeds>` runs e048's season
# world (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1,
# side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground store, k 1,
# sun 1, reach 0, stock 0, store 5, strict 1, sat 1, hold 1, wear 3,000, corners hold, plant
# yield 1, motor 1) with <band>: 0 the sky rains on every cell alike (e048's motor run byte for
# byte), N all the sky's rain on a band a quarter of the world wide that moves west one world cell
# every N steps; and <thirst> (e040): the fill a body loses a step (0: no body needs water).
# From the repo root:
#   (nohup bash experiments/e049_band/run.sh 25 0.005 1 100000 9 10 11 12 13 14 > experiments/e049_band/results/batch.log 2>&1 < /dev/null &)
set -e
band=$1; thirst=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e049_band $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 $thirst 0 1 1 1 3000 2 1 1 $band &
done
wait
echo DONE band $band thirst $thirst steps $steps seeds "$@"
