#!/bin/bash
# The flat runs of e024, one thread each: `run.sh <flesh> <seeds>` runs the flat world (rain on every cell alike) at
# relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, for 500,000 steps. From the repo root:
#   (nohup bash experiments/e024_flesh/run.sh 1 1 2 3 4 > experiments/e024_flesh/results/run_flesh1.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e024_flesh 2>&1 | tail -1
fl=$1; shift
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e024_flesh 500000 $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 $fl &
done
wait
echo DONE flesh $fl seeds "$@"
