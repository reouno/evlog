#!/bin/bash
# A run of e073 (#89): `run.sh <world> <steps> <life> <name> [key=value ...]` puts stage C's default
# world (e072's sets at the rates #88 kept) on e062's world <world> (c1225 or c1236, with e062's draw
# d11) for <steps> steps on one thread, with the keys given after the name: e073's two laws
# (wood_yield, day_temp), both 0 being e072. The settled world is read from e063's cache.
# From the repo root:
#   (nohup bash experiments/e073_forest/run.sh c1225 100000 9 yield wood_yield=3e-4 day_temp=1 \
#     > experiments/e073_forest/results/c1225_life9_yield.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0.04 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
out=experiments/e073_forest/results
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e073_forest $out/${world}_life${life}_$name $params $d11 $sets life=$life steps=$steps "$@"
echo DONE $world $name
