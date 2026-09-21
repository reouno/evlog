#!/bin/bash
# The batch of e093 (#103), one thread each, all at once, into results/batch/: the light at the rate the
# ladder picked (light_gain 0.016), on the six seeds of the control ladder, 100,000 steps, a census every
# 1,000 steps from 36,000 - the control ladder's own shape (e092).
#   (nohup bash experiments/e093_leaf/batch.sh > experiments/e093_leaf/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e093_leaf/results/batch
mkdir -p $out
for life in 9 10 11 12 13 14; do
  EVLOG_OUT=$out nohup bash experiments/e093_leaf/run.sh c1225 100000 $life g0.016 \
    light_gain=0.016 census=1000 census_from=36000 > $out/c1225_life${life}_g0.016.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
