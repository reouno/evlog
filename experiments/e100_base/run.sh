#!/bin/bash
# One run of e100 (#112): the new default world. `run.sh <world> <steps> <life> <name> [key=value ...]`.
#
# The world is e097's - e072's sets at the rates #88 kept, e073's crown yield (wood_yield 3e-5) and
# e075's tear and frail line - plus the three laws e099 found had been rejected for a difference
# smaller than the difference between two seeds of the same world, and the one kept for what it adds:
#
#   shade_heat 2.5, shade_dry 2.5  e078: a crown damps what a body's heat reads and cuts its drying
#   crown_wet 1, wood_rest 0.5     e079: a crown keeps the ground under it, wood rests in the cold
#   unit 9.4                       e081 (W1/W2): a body's water is part of the land's and is conserved
#
# The crate is e097's unchanged, so with `shade_heat` 0, `shade_dry` 0, `crown_wet` 0, `wood_rest` 0
# and `unit` 0 this reproduces e092's control bit for bit (checked; see the README).
#
# From the repo root:
#   (nohup bash experiments/e100_base/run.sh c1225 100000 9 ctl census=1000 census_from=36000 \
#     > experiments/e100_base/results/c1225_life9_ctl.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
kept="wood_yield=3e-5 wood_hard=3 day_temp=0 flesh_bite=0.4 frail=0.5"
back="shade_heat=2.5 shade_dry=2.5 crown_wet=1 wood_rest=0.5 unit=9.4"   # e099 (#112)
out=${EVLOG_OUT:-experiments/e100_base/results}
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e100_base $out/${world}_life${life}_$name $params $d11 $sets $kept $back life=$life steps=$steps "$@"
echo DONE $world $life $name
