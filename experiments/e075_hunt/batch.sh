#!/bin/bash
# The batch of e075 (#90): the centre of the search on three seeds, against e073's kept runs.
#   bash experiments/e075_hunt/batch.sh <steps> <name> <key=value ...>
# e.g. bash experiments/e075_hunt/batch.sh 100000 set flesh_bite=0.15 frail=0.75
# Runs seeds 9, 10 and 11 at once, one thread each, into results/ladder.
set -e
steps=$1; name=$2; shift 2
for s in 9 10 11; do
  EVLOG_OUT=experiments/e075_hunt/results/ladder \
    nohup bash experiments/e075_hunt/run.sh c1225 "$steps" $s "$name" "$@" \
    > experiments/e075_hunt/results/ladder/c1225_life${s}_${name}.log 2>&1 < /dev/null &
done
wait
echo BATCH_DONE $name
