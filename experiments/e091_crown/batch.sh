#!/bin/bash
# The runs of e091 (#101, stage C), one thread each, all at once, into results/: the crown as a place
# (C1 crown_at, C2 fruit_fall, C3 hold) on seeds 9-11, 100,000 steps, a census every 1,000 steps from
# 36,000 (as e081's ladder, the controls).
#   (nohup bash experiments/e091_crown/batch.sh > experiments/e091_crown/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e091_crown/results
mkdir -p $out
at=${CROWN_AT:-1}
hold=${HOLD:-10}
fall=${FALL:-0.5}
common="census=1000 census_from=36000 crown_at=$at hold=$hold fruit_fall=$fall"
for life in 9 10 11; do
  EVLOG_OUT=$out nohup bash experiments/e091_crown/run.sh c1225 100000 $life crown $common \
    > $out/c1225_life${life}_crown.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
