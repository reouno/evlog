#!/bin/bash
# A run of e079 (#91 step 2): `run.sh <world> <steps> <life> <name> [key=value ...]` puts stage C's default
# world - e072's sets at the rates #88 kept, e073's crown yield (wood_yield 3e-5) and e075's tear and
# frail line (flesh_bite 0.4, frail 0.5) - on e062's world <world> (c1225 or c1236, with e062's draw
# d11) for <steps> steps on one thread, with the keys given after the name. With crown_wet and wood_rest
# 0 the settled world is e078's (the same file) and the run is e078's exactly; `start=0` runs the world
# with no bodies (the producers alone).
#
# From the repo root:
#   (nohup bash experiments/e079_crown/run.sh c1225 23760 9 w1r1 start=0 cell_map=1 crown_wet=1 wood_rest=1 \
#     > experiments/e079_crown/results/c1225_life9_w1r1.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
kept="wood_yield=3e-5 wood_hard=3 day_temp=0 flesh_bite=0.4 frail=0.5"
out=${EVLOG_OUT:-experiments/e079_crown/results}
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e079_crown $out/${world}_life${life}_$name $params $d11 $sets $kept life=$life steps=$steps "$@"
echo DONE $world $name
