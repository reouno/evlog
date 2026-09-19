#!/bin/bash
# The runs of e088 (#99 S, stage B), one thread each, all at once, into results/alone: the producers alone
# at seed_share 0 (the control), 0.1, 0.2 and 0.4. Each builds its settled world (or reads it) and runs
# two years of c1225 with no bodies.
#   (nohup bash experiments/e088_seed/batch.sh > experiments/e088_seed/results/batch.log 2>&1 < /dev/null &)
set -e
out=experiments/e088_seed/results/alone
mkdir -p $out
for s in 0 0.1 0.2 0.4; do
  EVLOG_OUT=$out nohup bash experiments/e088_seed/run.sh c1225 23760 9 s$s \
    start=0 seed_share=$s > $out/c1225_life9_s$s.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE
