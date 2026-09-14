#!/bin/bash
# A run of e071 (#86): `run.sh <world> <steps> <life> <name> [key=value ...]` puts e070's bodies (scale
# 1/16, the water's two layers, dry air at 0.004, breath at 0.01, the values of a life constant, senses
# through sensor blocks) on e062's world <world> (c1225 or c1236, with e062's draw d11) for <steps> steps
# on one thread, with the keys given after the name: cold=0.000125 prices the cold (0, the default, is
# e070 at senses 1). The settled world is read from e063's cache.
# From the repo root:
#   (nohup bash experiments/e071_cold/run.sh c1225 100000 9 cold cold=0.000125 > experiments/e071_cold/results/c1225_life9_cold.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
out=experiments/e071_cold/results
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e071_cold $out/${world}_life${life}_$name $params $d11 life=$life steps=$steps "$@"
echo DONE $world $name
