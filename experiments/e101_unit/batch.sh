#!/bin/bash
# e101 (#113): the body's water alone - e100's world with `unit` 9.4 and the crown's four laws at 0,
# on the control ladder's own shape: six seeds, 100,000 steps, a census every 1,000 from 36,000.
# No crate of its own: e100's binary and run.sh, with the four laws set back to 0 after its `back=`
# (a later key=value overrides an earlier one). Six cores, about 1.2 hours.
#   (nohup bash experiments/e101_unit/batch.sh > experiments/e101_unit/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e101_unit/results/ladder
mkdir -p $out
for life in 9 10 11 12 13 14; do
  EVLOG_OUT=$out nohup bash experiments/e100_base/run.sh c1225 100000 $life unit \
    shade_heat=0 shade_dry=0 crown_wet=0 wood_rest=0 \
    census=1000 census_from=36000 > $out/c1225_life${life}_unit.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
