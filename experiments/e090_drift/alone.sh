#!/bin/bash
# e090's stage B check (#100 D): the producers alone on c1225, two years after the settled world, at
# seed_drift 0 (e088's world), 0.01, 0.02, 0.05 and 0.2, with e088's seed_share 0.2. Each builds its settled world
# (ten years of producers) or reads it, and writes a map of every cell (cell_map=1) to see where the
# seed lands.
#   (nohup bash experiments/e090_drift/alone.sh > experiments/e090_drift/results/alone.log 2>&1 < /dev/null &)
set -e
out=experiments/e090_drift/results/alone
mkdir -p $out
for d in 0 0.01 0.02 0.05 0.2; do
  EVLOG_OUT=$out nohup bash experiments/e090_drift/run.sh c1225 23760 9 d$d \
    start=0 seed_share=0.2 seed_drift=$d cell_map=1 > $out/c1225_life9_d$d.log 2>&1 < /dev/null &
done
wait
echo ALONE_DONE
