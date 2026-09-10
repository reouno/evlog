#!/bin/bash
# The runs of e043 (#45): `run.sh <sat> <hold> <threads> <steps> <seeds>` runs e042's season
# world (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1,
# side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground store, k 1,
# sun 1, reach 0, thirst 0, stock 0, store 5, strict 1) with the canopy's saturation under the
# fall (<sat> 1: a column claims by its room, a full crown nothing) and a held column's rest
# (<hold> 1: a column under a body claims nothing). 0 and 0 are e042's strict run byte for byte.
# From the repo root:
#   (nohup bash experiments/e043_crown/run.sh 1 0 1 100000 9 > experiments/e043_crown/results/pilot_sat1_hold0.log 2>&1 < /dev/null &)
set -e
sat=$1; hold=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e043_crown $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 0 0 1 $sat $hold &
done
wait
echo DONE sat $sat hold $hold steps $steps seeds "$@"
