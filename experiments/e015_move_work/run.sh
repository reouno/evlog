#!/bin/bash
# The twelve 128 runs of e015, at once on one 12-core machine, one thread each (about 50 minutes). From the repo root:
#   nohup bash experiments/e015_move_work/run.sh > experiments/e015_move_work/results/run.log 2>&1 &
set -e
cargo build --release -p e015_move_work 2>&1 | tail -1
for s in 1 2 3 4; do
  EVLOG_THREADS=1 ./target/release/e015_move_work 1000000 $s 128 8,1 &
  EVLOG_THREADS=1 ./target/release/e015_move_work 1000000 $s 128 8,2 &
  EVLOG_THREADS=1 ./target/release/e015_move_work 1000000 $s 128 8,4 &
done
wait
echo DONE
