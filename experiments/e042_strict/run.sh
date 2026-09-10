#!/bin/bash
# The runs of e042 (#46): `run.sh <strict> <store> <threads> <steps> <seeds>` runs e041's season
# world (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1,
# side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground store, k 1,
# sun 1, reach 0, thirst 0, stock 0) with the store at <store> (5: e030's law, kept) and a body
# that pays what it owes (<strict> 1: a body that cannot pay its upkeep or its moves in full dies
# at the end of the step; 0: what it cannot pay is dropped, e041 byte for byte).
# From the repo root:
#   (nohup bash experiments/e042_strict/run.sh 1 5 1 100000 9 10 > experiments/e042_strict/results/pilot_strict1_store5.log 2>&1 < /dev/null &)
set -e
strict=$1; store=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e042_strict $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow $store 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 0 0 $strict &
done
wait
echo DONE strict $strict store $store steps $steps seeds "$@"
