#!/bin/bash
# The runs of e058: `run.sh <sun> <threads> <steps> <seeds>` runs e057's world with the law off
# (`foul` 0, which is e056 and e055 byte for byte) at <sun>: the factor on every cell's regrowth
# and on the rain's cap with it. 1 is the world of e055-e057; below 1 the ground grows less per
# cell, so a body must gather from more cells than it stands on.
# From the repo root:
#   (nohup bash experiments/e058_thin/run.sh 0.1 1 100000 9 10 11 12 13 14 > experiments/e058_thin/results/batch_sun0.1.log 2>&1 < /dev/null &)
set -e
sun=$1; threads=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e058_thin $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 $sun 0 0 0 0 1 1 1 3000 2 1 1 0 0 0.5 4096 0 &
done
wait
echo DONE sun $sun steps $steps seeds "$@"
