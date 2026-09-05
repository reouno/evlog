#!/bin/bash
# The runs of e031: `run.sh <side> <yolk> <breed> <amplitude> <threads> <steps> <seeds>` runs e030's season world
# (rain on every cell alike, relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1,
# no digestion law, store 5) at the season's amplitude with the body's grid side <side> (8, or grow), the yolk
# share <yolk> (0: e030) and breeding as a decision <breed> (0: at the threshold, e030; 1: the policy's fifth
# output). From the repo root:
#   (nohup bash experiments/e031_breed/run.sh grow 0.5 1 1 1 300000 1 2 3 > experiments/e031_breed/results/run_both.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e031_breed 2>&1 | tail -1
side=$1; yolk=$2; breed=$3; amp=$4; threads=$5; steps=$6; shift 6
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e031_breed $steps $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season $amp 0 $side 5 $yolk $breed &
done
wait
echo DONE side $side yolk $yolk breed $breed amp $amp steps $steps seeds "$@"
