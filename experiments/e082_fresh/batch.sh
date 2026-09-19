#!/bin/bash
# The runs of e082 (#95), one thread each, all at once, into results/<set>, on the default world (S1-S3 at 0)
# with a body's water part of the land's at unit 9.4. Every run takes a census every 1,000 steps from 36,000.
#   bash experiments/e082_fresh/batch.sh search <steps> <seed> <fresh> ...    unit 9.4 at each <fresh>
#   bash experiments/e082_fresh/batch.sh ladder <steps> <fresh>                <fresh> on seeds 9, 10 and 11
# fresh 0.05 at unit 9.4 and the control (unit 0) are e081's runs.
set -e
set_=$1; steps=$2
out=experiments/e082_fresh/results/$set_
mkdir -p $out
launch() { # <seed> <fresh>
  EVLOG_OUT=$out nohup bash experiments/e082_fresh/run.sh c1225 "$steps" $1 u9.4_f$2 \
    census=1000 census_from=36000 unit=9.4 fresh=$2 > $out/c1225_life$1_u9.4_f$2.log 2>&1 < /dev/null &
}
if [ "$set_" = search ]; then
  seed=$3; shift 3
  for f in "$@"; do launch $seed $f; done
else
  for s in 9 10 11; do launch $s $3; done
fi
wait
echo BATCH_DONE $set_
