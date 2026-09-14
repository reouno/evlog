#!/bin/bash
# A run of e066 (#80): `run.sh <world> <steps> <life> <name> [key=value ...]` puts e065's bodies (scale
# 1/16, the water's two layers) on e062's world <world> (c1225 or c1236, with e062's draw d11) for
# <steps> steps on one thread, with the keys given after the name: dry=<rate> prices the dry air on
# soft blocks (0, the default, is e065), drink=<rate> is what a block in water drinks, start=0 runs
# the world alone. The settled world is read from e063's cache.
# From the repo root:
#   (nohup bash experiments/e066_dry/run.sh c1225 100000 9 dry0.004 dry=0.004 > experiments/e066_dry/results/c1225_dry0.004.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
out=experiments/e066_dry/results
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e066_dry $out/${world}_life${life}_$name $params $d11 life=$life steps=$steps "$@"
echo DONE $world $name
