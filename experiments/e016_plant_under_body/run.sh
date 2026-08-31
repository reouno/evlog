#!/bin/bash
# The 128 runs of e016: `run.sh any <seeds>` runs the three worlds with the strict reading for
# each seed (three runs per seed), `run.sh free <seeds>` the trees world with the free-sub-cells
# reading (one run per seed), one thread each. Split between two machines from the repo root:
#   nohup bash -c 'bash experiments/e016_plant_under_body/run.sh any 1 2 && bash experiments/e016_plant_under_body/run.sh free 1 2' > experiments/e016_plant_under_body/results/run.log 2>&1 &
#   (seeds 3 4 on the other machine)
set -e
mode=$1; shift
cargo build --release -p e016_plant_under_body 2>&1 | tail -1
for s in "$@"; do
  if [ "$mode" = any ]; then
    EVLOG_THREADS=1 ./target/release/e016_plant_under_body 1000000 $s 128 8,1 any &
    EVLOG_THREADS=1 ./target/release/e016_plant_under_body 1000000 $s 128 8,2 any &
    EVLOG_THREADS=1 ./target/release/e016_plant_under_body 1000000 $s 128 8,4 any &
  else
    EVLOG_THREADS=1 ./target/release/e016_plant_under_body 1000000 $s 128 8,1 free &
  fi
done
wait
echo DONE $mode "$@"
