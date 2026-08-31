#!/bin/bash
# The 128 runs of e021, one thread each. `run.sh <seeds>` runs the three worlds for each seed at
# relief 64, flow 0.1, shade 1: rain on the mountains (all of the breath to the air), half of the
# breath to the air, and rain on every cell alike. From the repo root:
#   nohup bash experiments/e021_canopy/run.sh 1 2 3 4 > experiments/e021_canopy/results/run.log 2>&1 &
set -e
cargo build --release -p e021_canopy 2>&1 | tail -1
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e021_canopy 1000000 $s 128 0 0.02 8 64 0.1 high &
  EVLOG_THREADS=1 ./target/release/e021_canopy 1000000 $s 128 0 0.02 8 64 0.1 high 0.5 &
  EVLOG_THREADS=1 ./target/release/e021_canopy 1000000 $s 128 0 0.02 8 64 0.1 flat &
done
wait
echo DONE "$@"
