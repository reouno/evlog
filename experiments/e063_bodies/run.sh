#!/bin/bash
# The runs of e063 (#76): `run.sh <world> <steps> <lives...>` puts e059's bodies on e062's world
# <world> (c1225 or c1236, with e062's draw d11) for <steps> steps, one run per seed of life, each
# on one thread. The settled world is built first, once (a few minutes), and every run reads it.
# From the repo root:
#   (nohup bash experiments/e063_bodies/run.sh c1225 100000 9 > experiments/e063_bodies/results/c1225_run.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; shift 2
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
bin=./target/release/e063_bodies
out=experiments/e063_bodies/results
$bin $out/${world}_world $params $d11 steps=0
for life in "$@"; do
  EVLOG_THREADS=1 $bin $out/${world}_life$life $params $d11 life=$life steps=$steps > $out/${world}_life$life.log 2>&1 &
done
wait
echo DONE $world steps $steps lives "$@"
