#!/bin/bash
# The runs of e090 (#100, stage C), one thread each, all at once, into results/: D+B+Fb' on seeds 9-11,
# 100,000 steps, a census every 1,000 steps from 36,000 (as e081's ladder, the controls). DRIFT is the
# rate the stage B check (alone.sh) chose.
#   (nohup bash experiments/e090_drift/batch.sh > experiments/e090_drift/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e090_drift/results
mkdir -p $out
drift=${DRIFT:-0.02}
common="census=1000 census_from=36000 seed_share=0.2 seed_drift=$drift seed_hard=1 ferment=0.005 pass=0.02"
for life in 9 10 11; do
  EVLOG_OUT=$out nohup bash experiments/e090_drift/run.sh c1225 100000 $life dbf $common \
    > $out/c1225_life${life}_dbf.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
