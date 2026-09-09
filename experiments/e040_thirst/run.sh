#!/bin/bash
# The runs of e040 (#37): `run.sh <thirst> <threads> <steps> <seeds>` runs e039's season world
# (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, side
# grow, store 5, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground
# store, k 1, sun 1, reach 0) with a body that needs water (#37): every body dries by <thirst>
# of its fill a step and drinks where water stands (0: no body needs water, e039 byte for byte).
# From the repo root:
#   (nohup bash experiments/e040_thirst/run.sh 0.002 1 100000 9 > experiments/e040_thirst/results/pilot_thirst0.002.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e040_thirst 2>&1 | tail -1
thirst=$1; threads=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e040_thirst $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 $thirst &
done
wait
echo DONE thirst $thirst steps $steps seeds "$@"
