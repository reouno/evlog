#!/bin/bash
# The runs of e028, one thread each: `run.sh <digest> <steps> <seeds>` runs e026's season world (rain on every
# cell alike, relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, season 0.5) with
# the digestion law on (1) or off (0: e026 byte for byte). From the repo root:
#   (nohup bash experiments/e028_gut/run.sh 1 500000 1 2 3 4 > experiments/e028_gut/results/run_digest1.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e028_gut 2>&1 | tail -1
digest=$1; steps=$2; shift 2
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e028_gut $steps $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5 $digest &
done
wait
echo DONE digest $digest steps $steps seeds "$@"
