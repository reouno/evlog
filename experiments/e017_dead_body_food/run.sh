#!/bin/bash
# The 128 runs of e017: `run.sh law <seeds>` runs the three worlds with the law for each seed
# (three runs per seed), `run.sh cell <seeds>` the trees world with a cell made of five times
# the matter (0.1; one run per seed), one thread each. Split between two machines from the repo root:
#   nohup bash -c 'bash experiments/e017_dead_body_food/run.sh law 1 2 && bash experiments/e017_dead_body_food/run.sh cell 1 2' > experiments/e017_dead_body_food/results/run.log 2>&1 &
#   (seeds 3 4 on the other machine)
set -e
mode=$1; shift
cargo build --release -p e017_dead_body_food 2>&1 | tail -1
for s in "$@"; do
  if [ "$mode" = law ]; then
    EVLOG_THREADS=1 ./target/release/e017_dead_body_food 1000000 $s 128 8,1 &
    EVLOG_THREADS=1 ./target/release/e017_dead_body_food 1000000 $s 128 8,2 &
    EVLOG_THREADS=1 ./target/release/e017_dead_body_food 1000000 $s 128 8,4 &
  else
    EVLOG_THREADS=1 ./target/release/e017_dead_body_food 1000000 $s 128 8,1 0.1 &
  fi
done
wait
echo DONE $mode "$@"
