#!/bin/bash
# One run of e097 (#109), e092's run.sh with this crate: `run.sh <world> <steps> <life> <name> [key=value ...]`
# puts stage C's default world - e072's sets at the rates #88 kept, e073's crown yield (wood_yield 3e-5) and
# e075's tear and frail line (flesh_bite 0.4, frail 0.5) - on e062's world <world> (c1225, with e062's draw
# d11) for <steps> steps on one thread. With `probe` unset (0) nothing of e097 runs and the run is e092's
# control bit for bit: the world the probe measures.
#
# From the repo root (step 0, the instrumented run):
#   (nohup bash experiments/e097_room/run.sh c1225 40000 9 probe probe=0.02 \
#     > experiments/e097_room/results/c1225_life9_probe.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
kept="wood_yield=3e-5 wood_hard=3 day_temp=0 flesh_bite=0.4 frail=0.5"
out=${EVLOG_OUT:-experiments/e097_room/results}
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e097_room $out/${world}_life${life}_$name $params $d11 $sets $kept life=$life steps=$steps "$@"
echo DONE $world $life $name
