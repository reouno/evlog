#!/bin/bash
# The runs of e037: `run.sh <k> <threads> <steps> <seeds>` runs e035's season world (relief 64,
# winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, side grow, store 5,
# rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground store) with the cost
# of a body (#39): the upkeep of the cells scales as (size / 16)^<k> (1: today's linear law,
# e036 byte for byte). From the repo root:
#   (nohup bash experiments/e037_upkeep/run.sh 0.75 1 100000 9 > experiments/e037_upkeep/results/pilot_k0.75.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e037_upkeep 2>&1 | tail -1
k=$1; threads=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e037_upkeep $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew $k &
done
wait
echo DONE k $k steps $steps seeds "$@"
