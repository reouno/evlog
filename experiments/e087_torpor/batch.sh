#!/bin/bash
# The batch of e087 (#93), one thread each, all at once, into results/batch: Y+Q (year 1,200, q10 2.5) on
# seeds 9, 10 and 11 and Y alone (year 1,200, set A's warming kept) on seed 9, <steps> steps, a census
# every 1,000 steps from 36,000. The controls are e081's ladder (year 11,880).
#   (nohup bash experiments/e087_torpor/batch.sh 100000 > experiments/e087_torpor/results/batch.log 2>&1 < /dev/null &)
set -e
steps=$1
out=experiments/e087_torpor/results/batch
mkdir -p $out
launch() { # <seed> <name> [key=value ...]
  local seed=$1 name=$2; shift 2
  EVLOG_OUT=$out nohup bash experiments/e087_torpor/run.sh c1225 "$steps" $seed $name \
    census=1000 census_from=36000 year=1200 "$@" > $out/c1225_life${seed}_$name.log 2>&1 < /dev/null &
}
for s in 9 10 11; do launch $s yq q10=2.5; done
launch 9 y
wait
echo BATCH_DONE
