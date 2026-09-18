#!/bin/bash
# A run of e077 (#91): `run.sh <world> <steps> <life> <name> [key=value ...]` puts stage C's default
# world - e072's sets at the rates #88 kept, e073's crown yield (wood_yield 3e-5) and e075's tear and
# frail line (flesh_bite 0.4, frail 0.5) - on e062's world <world> (c1225 or c1236, with e062's draw
# d11) for <steps> steps on one thread, with the keys given after the name. It runs e075's binary:
# with no pool in the environment the run is e075's kept run (`ladder/*_both`) exactly.
#
# The pools of #72's test come by their own names, since they are files and not numbers:
#   EVLOG_POOL=<file>    the genomes the world is seeded with (with seed_n=<how many>)
#   EVLOG_INJECT=<file>  the genomes put in at inject_at (with inject_n and inject_seed)
#
# From the repo root:
#   (nohup bash experiments/e077_refuge/run.sh c1225 100000 9 donor genomes=1 \
#     > experiments/e077_refuge/results/c1225_life9_donor.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
kept="wood_yield=3e-5 wood_hard=3 day_temp=0 flesh_bite=0.4 frail=0.5"
out=${EVLOG_OUT:-experiments/e077_refuge/results}
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e077_refuge $out/${world}_life${life}_$name $params $d11 $sets $kept life=$life steps=$steps "$@"
echo DONE $world $name
