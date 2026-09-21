#!/bin/bash
# e097's batch (#109 step 1): the rung the ladder picked - `ring` 1 with `reach` 2, which relieves the
# jam most of the rungs that keep a child within two body lengths - on the six seeds of the control
# ladder, 100,000 steps, a census every 1,000 steps from 36,000 (the control ladder's own shape, e092).
#   (nohup bash experiments/e097_room/batch.sh > experiments/e097_room/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e097_room/results/batch
mkdir -p $out
for life in 9 10 11 12 13 14; do
  EVLOG_OUT=$out nohup bash experiments/e097_room/run.sh c1225 100000 $life ring2 reach=2 ring=1 \
    census=1000 census_from=36000 > $out/c1225_life${life}_ring2.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
