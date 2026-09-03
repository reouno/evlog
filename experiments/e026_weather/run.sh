#!/bin/bash
# The runs of e026, one thread each: `run.sh <weather> <amplitude> <steps> <seeds>` runs e025's flat world (rain on
# every cell alike, relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1) with the
# weather given (0, cloud or season). From the repo root:
#   (nohup bash experiments/e026_weather/run.sh cloud 1 500000 1 2 3 4 > experiments/e026_weather/results/run_cloud1.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e026_weather 2>&1 | tail -1
weather=$1; amp=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e026_weather $steps $s 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 $weather $amp &
done
wait
echo DONE weather $weather $amp steps $steps seeds "$@"
