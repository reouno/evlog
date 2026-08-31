#!/bin/bash
# The 128 runs of e019, one thread each. `run.sh uniform <seeds>` runs the three uniform-sun
# worlds for each seed (relief 64, 256 and 0, flow 0.1); `run.sh drawn <seeds>` runs the grass and
# trees world at relief 64. From the repo root:
#   nohup bash experiments/e019_terrain/run.sh uniform 1 2 3 4 > experiments/e019_terrain/results/run.log 2>&1 &
#   (drawn 1 2 3 4 on the other machine)
set -e
cargo build --release -p e019_terrain 2>&1 | tail -1
kind=$1
shift
for s in "$@"; do
  if [ "$kind" = uniform ]; then
    EVLOG_THREADS=1 ./target/release/e019_terrain 1000000 $s 128 0 0.02 8 64 0.1 &
    EVLOG_THREADS=1 ./target/release/e019_terrain 1000000 $s 128 0 0.02 8 256 0.1 &
    EVLOG_THREADS=1 ./target/release/e019_terrain 1000000 $s 128 0 0.02 8 0 0.1 &
  else
    EVLOG_THREADS=1 ./target/release/e019_terrain 1000000 $s 128 8,1 0.02 8 64 0.1 &
  fi
done
wait
echo DONE "$kind" "$@"
