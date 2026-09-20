#!/bin/bash
# The runs of e092 (#102, the yardstick), one thread each, all at once, into results/ladder/: the default
# world with no law added, 100,000 steps, a census every 1,000 steps from 36,000 (e081's ladder exactly).
# Seeds 12, 13 and 14 widen the control ladder to six seeds; seed 9 is the check that this crate
# reproduces e081's control column for column (e081's ladder holds seeds 9-11).
#   (nohup bash experiments/e092_yardstick/batch.sh > experiments/e092_yardstick/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e092_yardstick/results/ladder
mkdir -p $out
for life in 12 13 14 9; do
  EVLOG_OUT=$out nohup bash experiments/e092_yardstick/run.sh c1225 100000 $life ctl \
    census=1000 census_from=36000 > $out/c1225_life${life}_ctl.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
