#!/bin/bash
# The six 256 runs of e014 (the world people watch), six at once, one thread each (run locally when the machine is free: the 6-core machine took 5 hours).
#   nohup bash experiments/e014_body_space/run_256.sh > experiments/e014_body_space/results/run_256.log 2>&1 &
set -e
cargo build --release -p e014_body_space 2>&1 | tail -1
for s in 1 2 3 4; do
  EVLOG_THREADS=1 ./target/release/e014_body_space 1000000 $s 256 8,1 &
done
for s in 1 2; do
  EVLOG_THREADS=1 ./target/release/e014_body_space 1000000 $s 256 8,2 &
done
wait
echo DONE
