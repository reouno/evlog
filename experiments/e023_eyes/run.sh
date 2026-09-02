#!/bin/bash
# The flat runs of e023, two threads each (four runs on eight cores): `run.sh <seeds>` runs the flat world (rain on every
# cell alike) at relief 64, flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8. From the repo root:
#   (nohup bash experiments/e023_eyes/run.sh 1 2 3 4 > experiments/e023_eyes/results/run.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e023_eyes 2>&1 | tail -1
for s in "$@"; do
  EVLOG_THREADS=2 ./target/release/e023_eyes 1000000 $s 128 0 0.02 8 64 0.1 flat &
done
wait
echo DONE "$@"
