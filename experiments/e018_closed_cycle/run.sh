#!/bin/bash
# The 128 runs of e018, one thread each: `run.sh <seeds>` runs the three worlds for each seed
# (three runs per seed): the drawn sun at e017's total (matter 8 per cell), the drawn sun at a
# scarce total (1 per cell), and the uniform sun at e017's total. Split between two machines
# from the repo root:
#   nohup bash experiments/e018_closed_cycle/run.sh 1 2 > experiments/e018_closed_cycle/results/run.log 2>&1 &
#   (seeds 3 4 on the other machine)
set -e
cargo build --release -p e018_closed_cycle 2>&1 | tail -1
for s in "$@"; do
  EVLOG_THREADS=1 ./target/release/e018_closed_cycle 1000000 $s 128 8,1 &
  EVLOG_THREADS=1 ./target/release/e018_closed_cycle 1000000 $s 128 8,1 0.02 1 &
  EVLOG_THREADS=1 ./target/release/e018_closed_cycle 1000000 $s 128 0 &
done
wait
echo DONE "$@"
