#!/bin/bash
# The runs of e080 (#91 step 3), one thread each, all at once, into results/<set>, on e079's world at
# crown_wet 1 and wood_rest 0.5. Every run takes a census every 1,000 steps from 36,000 (e078's).
#   bash experiments/e080_cool/batch.sh search <steps> <seed>        the control and three crown_cool
#   bash experiments/e080_cool/batch.sh ladder <steps> <c3>          the control and c3 on seeds 9, 10 and 11
set -e
set_=$1; steps=$2
out=experiments/e080_cool/results/$set_
mkdir -p $out
world="crown_wet=1 wood_rest=0.5"
launch() { # <seed> <c3>
  EVLOG_OUT=$out nohup bash experiments/e080_cool/run.sh c1225 "$steps" $1 c$2 \
    census=1000 census_from=36000 $world crown_cool=$2 > $out/c1225_life$1_c$2.log 2>&1 < /dev/null &
}
if [ "$set_" = search ]; then
  for c3 in 0 0.1 0.2 0.4; do launch $3 $c3; done
else
  for s in 9 10 11; do launch $s 0; launch $s $3; done
fi
wait
echo BATCH_DONE $set_
