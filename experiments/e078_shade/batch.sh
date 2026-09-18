#!/bin/bash
# The runs of e078 (#91 step 1), one thread each, all at once, into results/<set>.
#   bash experiments/e078_shade/batch.sh search <steps> <seed>     the control and ten (k, k2)
#   bash experiments/e078_shade/batch.sh ladder <steps> <k> <k2>   the centre on seeds 9, 10 and 11
# Every run takes a census every 1,000 steps from 36,000 (e077's), for the lines by season.
set -e
set_=$1; steps=$2
out=experiments/e078_shade/results/$set_
mkdir -p $out
launch() { # <seed> <name> <k> <k2>
  EVLOG_OUT=$out nohup bash experiments/e078_shade/run.sh c1225 "$steps" $1 $2 \
    census=1000 census_from=36000 shade_heat=$3 shade_dry=$4 > $out/c1225_life$1_$2.log 2>&1 < /dev/null &
}
if [ "$set_" = search ]; then
  seed=$3
  for kk in 0:0 1:0 2.5:0 5:0 0:2.5 0:5 1:1 2.5:2.5 5:5 1:5 5:1; do
    k=${kk%%:*}; k2=${kk#*:}
    launch $seed h${k}d${k2} $k $k2
  done
else
  for s in 9 10 11; do launch $s h$3d$4 $3 $4; done
fi
wait
echo BATCH_DONE $set_
