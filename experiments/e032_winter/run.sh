#!/bin/bash
# The runs of e032: `run.sh <winter> <amplitude> <threads> <steps> <seeds>` runs e031's season world (rain on
# every cell alike, relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, no
# digestion law, side grow, store 5, no yolk, breeding at the threshold) at the season's amplitude with the
# winter <winter>: flat (the same amplitude on every cell, e031) or high (the cell's amplitude by height).
# From the repo root:
#   (nohup bash experiments/e032_winter/run.sh high 2 1 300000 1 2 3 > experiments/e032_winter/results/run_high2.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e032_winter 2>&1 | tail -1
winter=$1; amp=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e032_winter $steps $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season $amp 0 grow 5 0 0 $winter &
done
wait
echo DONE winter $winter amp $amp steps $steps seeds "$@"
