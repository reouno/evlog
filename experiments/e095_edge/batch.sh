#!/bin/bash
# The batch of e095 (#107), one thread each, all at once, into results/batch/: the pair at the rates the
# two ladders picked (spike 2, leg 1), on the six seeds of the control ladder, 100,000 steps, a census
# every 1,000 steps from 36,000 - the control ladder's own shape (e092).
#   (nohup bash experiments/e095_edge/batch.sh > experiments/e095_edge/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e095_edge/results/batch
mkdir -p $out
for life in 9 10 11 12 13 14; do
  EVLOG_OUT=$out nohup bash experiments/e095_edge/run.sh c1225 100000 $life pair \
    spike=2 leg=1 census=1000 census_from=36000 > $out/c1225_life${life}_pair.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
