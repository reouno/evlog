#!/bin/bash
# One run of e096 (#108, P3 step 3): `run.sh <world> <steps> <life> <name> [key=value ...]` puts stage C's
# default world - e072's sets at the rates #88 kept, e073's crown yield (wood_yield 3e-5) and e075's tear
# and frail line (flesh_bite 0.4, frail 0.5) - on e062's world <world> (c1225, with e062's draw d11) for
# <steps> steps on one thread. With `shade` and `light_gain` unset (0) no body develops a leaf block,
# the light is granted as it always was, and the run is e092's control bit for bit (checked against
# e093's crate): the six-seed ladder is the control of this experiment too.
#
# From the repo root:
#   (nohup bash experiments/e096_shade/run.sh c1225 40000 9 s2g0.016 shade=2 light_gain=0.016 \
#     census=1000 census_from=20000 > experiments/e096_shade/results/c1225_life9_s2g0.016.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
kept="wood_yield=3e-5 wood_hard=3 day_temp=0 flesh_bite=0.4 frail=0.5"
out=${EVLOG_OUT:-experiments/e096_shade/results}
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e096_shade $out/${world}_life${life}_$name $params $d11 $sets $kept life=$life steps=$steps "$@"
echo DONE $world $life $name
