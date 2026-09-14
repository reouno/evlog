#!/bin/bash
# The runs of e064 (#78): `run.sh <world> <steps> <life> <scales...>` puts e063's bodies, every
# matter quantity of a body times `scale`, on e062's world <world> (c1225 or c1236, with e062's draw
# d11) for <steps> steps, one run per scale, each on one thread. The settled world is read from
# e063's cache (and built there first if it is missing).
# From the repo root:
#   (nohup bash experiments/e064_scale/run.sh c1225 100000 9 0.25 0.0625 > experiments/e064_scale/results/c1225_run.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; shift 3
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
bin=./target/release/e064_scale
out=experiments/e064_scale/results
$bin $out/${world}_world $params $d11 steps=0
for s in "$@"; do
  EVLOG_THREADS=1 $bin $out/${world}_life${life}_s$s $params $d11 life=$life scale=$s steps=$steps > $out/${world}_life${life}_s$s.log 2>&1 &
done
wait
echo DONE $world steps $steps life $life scales "$@"
