#!/bin/bash
# The runs of e038 (#40): `run.sh <k> <sun> <threads> <steps> <seeds>` runs e037's season world
# (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, side
# grow, store 5, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground store)
# with the upkeep's exponent <k> (e037; 1 is today's law) and the sun's rate per cell times <sun>
# (1: today's 0.01 a cell a step, e037 byte for byte). From the repo root:
#   (nohup bash experiments/e038_income/run.sh 1 2 1 100000 9 > experiments/e038_income/results/pilot_k1_sun2.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e038_income 2>&1 | tail -1
k=$1; sun=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e038_income $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew $k $sun &
done
wait
echo DONE k $k sun $sun steps $steps seeds "$@"
