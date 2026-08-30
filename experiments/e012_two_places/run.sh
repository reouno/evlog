#!/bin/bash
# The twelve runs of e012, at once on one 12-core machine, one thread each. From the repo root:
#   nohup bash experiments/e012_two_places/run.sh > experiments/e012_two_places/results/run.log 2>&1 &
set -e
cargo build --release -p e012_two_places 2>&1 | tail -1
for s in 1 2 3 4; do
  EVLOG_THREADS=1 ./target/release/e012_two_places 1000000 $s 128 8,1 &
  EVLOG_THREADS=1 ./target/release/e012_two_places 1000000 $s 128 8,2 &
  EVLOG_THREADS=1 ./target/release/e012_two_places 1000000 $s 256 8,1 &
done
wait
echo DONE
