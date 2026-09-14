#!/bin/bash
# A run of e067 (#81): `run.sh <world> <steps> <life> <name> [key=value ...]` puts e066's bodies (scale
# 1/16, the water's two layers, dry air at 0.004) on e062's world <world> (c1225 or c1236, with e062's
# draw d11) for <steps> steps on one thread, with the keys given after the name: breath=<rate> prices
# the closed body in the water (0, the default, is e066 at dry 0.004), inhale=<rate> is what a block
# over land breathes, dry=<rate> the dry air. The settled world is read from e063's cache.
# From the repo root:
#   (nohup bash experiments/e067_breath/run.sh c1225 100000 9 breath0.01 breath=0.01 > experiments/e067_breath/results/c1225_breath0.01.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
out=experiments/e067_breath/results
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e067_breath $out/${world}_life${life}_$name $params $d11 life=$life steps=$steps "$@"
echo DONE $world $name
