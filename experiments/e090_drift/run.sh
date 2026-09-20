#!/bin/bash
# A run of e090 (#100), e082's line: `run.sh <world> <steps> <life> <name> [key=value ...]` puts stage C's default
# world - e072's sets at the rates #88 kept, e073's crown yield (wood_yield 3e-5) and e075's tear and
# frail line (flesh_bite 0.4, frail 0.5) - on e062's world <world> (c1225 or c1236, with e062's draw
# d11) for <steps> steps on one thread, with the keys given after the name (a later key wins, so
# `fresh=0.2` overrides the default world's 0.05). The crate is e089's with e090's drift (seed_drift).
#
# From the repo root:
#   (nohup bash experiments/e090_drift/run.sh c1225 100000 9 dbf seed_share=0.2 seed_drift=0.05 \
#     > experiments/e090_drift/results/c1225_life9_dbf.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
kept="wood_yield=3e-5 wood_hard=3 day_temp=0 flesh_bite=0.4 frail=0.5"
out=${EVLOG_OUT:-experiments/e090_drift/results}
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e090_drift $out/${world}_life${life}_$name $params $d11 $sets $kept life=$life steps=$steps "$@"
echo DONE $world $name
