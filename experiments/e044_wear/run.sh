#!/bin/bash
# The runs of e044 (#47): `run.sh <wear> <threads> <steps> <seeds>` runs e043's season world
# (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, side
# grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground store, k 1,
# sun 1, reach 0, thirst 0, stock 0, store 5, strict 1, sat 1, hold 1) with wear (<wear>: a
# block's median life in steps; 0 is the fixed age, e043's sat + hold run byte for byte).
# From the repo root:
#   (nohup bash experiments/e044_wear/run.sh 3000 1 100000 9 10 > experiments/e044_wear/results/pilot_wear3000.log 2>&1 < /dev/null &)
set -e
wear=$1; threads=$2; steps=$3; shift 3
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e044_wear $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 0 0 1 1 1 $wear &
done
wait
echo DONE wear $wear steps $steps seeds "$@"
