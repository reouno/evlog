#!/bin/bash
# The runs of e081 (#94), one thread each, all at once, into results/<set>, on the default world (S1-S3 at 0).
# Every run takes a census every 1,000 steps from 36,000 (e078's).
#   bash experiments/e081_drink/batch.sh search <steps> <seed>        unit 0 (the control), 4.7, 9.4 and 28 mm
#   bash experiments/e081_drink/batch.sh ladder <steps> <unit>        the control and <unit> on seeds 9, 10 and 11
set -e
set_=$1; steps=$2
out=experiments/e081_drink/results/$set_
mkdir -p $out
launch() { # <seed> <unit>
  EVLOG_OUT=$out nohup bash experiments/e081_drink/run.sh c1225 "$steps" $1 u$2 \
    census=1000 census_from=36000 unit=$2 > $out/c1225_life$1_u$2.log 2>&1 < /dev/null &
}
if [ "$set_" = search ]; then
  for u in 0 4.7 9.4 28; do launch $3 $u; done
else
  for s in 9 10 11; do launch $s 0; launch $s $3; done
fi
wait
echo BATCH_DONE $set_
