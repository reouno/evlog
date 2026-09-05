#!/bin/bash
# The runs of e030: `run.sh <side> <store> <amplitude> <threads> <steps> <seeds>` runs e026's season world
# (rain on every cell alike, relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1,
# weight 1, no digestion law) at the season's amplitude, with the body's grid side <side> (8, or grow)
# and the store law at <store> (fat per unit of mass; 0 is e029 byte for byte). From the repo root:
#   (nohup bash experiments/e030_store/run.sh grow 5 0.75 1 300000 1 2 3 > experiments/e030_store/results/run_grow5.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e030_store 2>&1 | tail -1
side=$1; store=$2; amp=$3; threads=$4; steps=$5; shift 5
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e030_store $steps $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season $amp 0 $side $store &
done
wait
echo DONE side $side store $store amp $amp steps $steps seeds "$@"
