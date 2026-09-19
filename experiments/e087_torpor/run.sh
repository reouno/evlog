#!/bin/bash
# A run of e087 (#93): `run.sh <world> <steps> <life> <name> [key=value ...]` puts stage C's default world
# (e082's: e072's sets at #88's rates, e073's crown yield, e075's tear and frail line, fresh 0.05, unit 0)
# on e062's world <world> with e062's draw d11, for <steps> steps on one thread, with the keys given after
# the name (a later key wins). The year and Q are keys: `year=1200 q10=2.5` is Y+Q, `year=1200` Y alone.
# With `places_y<year>.bin` in results (places.py) the run writes `_months.csv` and `_grown.csv`.
#
# From the repo root:
#   (nohup bash experiments/e087_torpor/run.sh c1225 30000 9 yq year=1200 q10=2.5 \
#     > experiments/e087_torpor/results/c1225_life9_yq.log 2>&1 < /dev/null &)
set -e
world=$1; steps=$2; life=$3; name=$4; shift 4
params=experiments/e062_producers/results/worlds/$world.params
d11="grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
sets="heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
kept="wood_yield=3e-5 wood_hard=3 day_temp=0 flesh_bite=0.4 frail=0.5"
out=${EVLOG_OUT:-experiments/e087_torpor/results}
mkdir -p $out
EVLOG_THREADS=1 ./target/release/e087_torpor $out/${world}_life${life}_$name $params $d11 $sets $kept life=$life steps=$steps "$@"
echo DONE $world $name
