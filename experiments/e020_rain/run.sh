#!/bin/bash
# The 128 runs of e020, one thread each. `run.sh <seeds>` runs the three worlds for each seed at
# relief 64, flow 0.1: rain on the mountains (all of the breath to the air), half of the breath to
# the air and half to the soil under the body, and rain on every cell alike. From the repo root:
#   nohup bash experiments/e020_rain/run.sh 1 2 3 4 > experiments/e020_rain/results/run.log 2>&1 &
set -e
cargo build --release -p e020_rain 2>&1 | tail -1
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e020_rain 1000000 $s 128 0 0.02 8 64 0.1 high &
  EVLOG_THREADS=1 ./target/release/e020_rain 1000000 $s 128 0 0.02 8 64 0.1 high 0.5 &
  EVLOG_THREADS=1 ./target/release/e020_rain 1000000 $s 128 0 0.02 8 64 0.1 flat &
done
wait
echo DONE "$@"
