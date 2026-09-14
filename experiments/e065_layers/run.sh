#!/bin/bash
# A run of e065 (#79): `run.sh <world> <steps> <life> <name> [key=value ...]` puts e064's bodies at
# scale 1/16 on e062's world <world> (c1225 or c1236, with e062's draw d11) for <steps> steps on one
# thread, with the keys given after the name: water=1 (the default) opens the water's two layers,
# water=0 is e064's sea wall, start=0 runs the world alone. The settled world is read from e063's cache.
# From the repo root:
#   (nohup bash experiments/e065_layers/run.sh c1225 100000 9 water > experiments/e065_layers/results/c1225_water.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
out=experiments/e065_layers/results
EVLOG_THREADS=1 ./target/release/e065_layers $out/${world}_life${life}_$name $params $d11 life=$life steps=$steps "$@"
echo DONE $world $name
