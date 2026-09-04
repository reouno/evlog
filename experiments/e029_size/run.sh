#!/bin/bash
# The runs of e029, one thread each: `run.sh <side> <steps> <seeds>` runs e026's season world (rain on every
# cell alike, relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, season 0.5,
# no digestion law) with the body's grid side fixed at <side> (8: e028 byte for byte) or expressed by the
# genome (grow, 4 to 16). From the repo root:
#   (nohup bash experiments/e029_size/run.sh grow 500000 1 2 3 4 > experiments/e029_size/results/run_grow.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e029_size 2>&1 | tail -1
side=$1; steps=$2; shift 2
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e029_size $steps $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5 0 $side &
done
wait
echo DONE side $side steps $steps seeds "$@"
