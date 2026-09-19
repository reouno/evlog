#!/bin/bash
# The runs of e089 (#99, stage C), one thread each, all at once, into results/: S+Fb on seeds 9-11 and S
# alone on seed 9, 100,000 steps, a census every 1,000 steps from 36,000 (as e081's ladder, the controls).
#   (nohup bash experiments/e089_fiber/batch.sh > experiments/e089_fiber/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e089_fiber/results
mkdir -p $out
common="census=1000 census_from=36000 seed_share=0.2 seed_hard=2"
for life in 9 10 11; do
  EVLOG_OUT=$out nohup bash experiments/e089_fiber/run.sh c1225 100000 $life sfb $common ferment=0.02 pass=0.02 \
    > $out/c1225_life${life}_sfb.log 2>&1 < /dev/null &
done
EVLOG_OUT=$out nohup bash experiments/e089_fiber/run.sh c1225 100000 9 s $common > $out/c1225_life9_s.log 2>&1 < /dev/null &
wait
echo BATCH_DONE
