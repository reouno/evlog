#!/bin/bash
# The flat runs of e025, one thread each: `run.sh <weight> <seeds>` runs the flat world (rain on every cell alike) at
# relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, for 500,000 steps. From the repo root:
#   (nohup bash experiments/e025_weight/run.sh 1 1 2 3 4 > experiments/e025_weight/results/run_w1.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e025_weight 2>&1 | tail -1
w=$1; shift
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e025_weight 500000 $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 $w &
done
wait
echo DONE weight $w seeds "$@"
