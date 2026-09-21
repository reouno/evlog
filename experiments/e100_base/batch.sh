#!/bin/bash
# e100 (#112): the control ladder of the new default world - e092's ladder again, on the world e099
# put three rejected laws back into (shade, the crown's ground and wood's rest, the body's water).
# Six seeds, 100,000 steps, a census every 1,000 from 36,000: the shape every later judgement is read
# against. Six cores, about 1.5 hours.
#   (nohup bash experiments/e100_base/batch.sh > experiments/e100_base/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e100_base/results/ladder
mkdir -p $out
for life in 9 10 11 12 13 14; do
  EVLOG_OUT=$out nohup bash experiments/e100_base/run.sh c1225 100000 $life ctl \
    census=1000 census_from=36000 > $out/c1225_life${life}_ctl.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
