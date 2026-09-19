#!/bin/bash
# The runs of e079 (#91 step 2), one thread each, all at once, into results/<set>.
#   bash experiments/e079_crown/batch.sh alone     the producers alone: the control and four (crown_wet, wood_rest)
#   bash experiments/e079_crown/batch.sh alone2    two more between them: a half rest, and a floor between 1 and 2
# Each builds its settled world (or reads it) and runs two years of c1225 with no bodies.
set -e
set_=$1
out=experiments/e079_crown/results/$set_
mkdir -p $out
launch() { # <name> <crown_wet> <wood_rest> [key=value ...]
  name=$1; w=$2; r=$3; shift 3
  EVLOG_OUT=$out nohup bash experiments/e079_crown/run.sh c1225 23760 9 $name \
    start=0 cell_map=1 crown_wet=$w wood_rest=$r "$@" > $out/c1225_life9_$name.log 2>&1 < /dev/null &
}
if [ "$set_" = alone ]; then
  for wr in 0:0 0:1 1:0 1:1 2:1; do
    w=${wr%%:*}; r=${wr#*:}
    launch w${w}r${r} $w $r
  done
elif [ "$set_" = alone2 ]; then
  out=experiments/e079_crown/results/alone
  for wr in 1:0.5 1.5:1; do
    w=${wr%%:*}; r=${wr#*:}
    launch w${w}r${r} $w $r
  done
fi
wait
echo BATCH_DONE $set_
