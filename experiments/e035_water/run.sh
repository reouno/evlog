#!/bin/bash
# The runs of e035: `run.sh <water> <leach> <flow> <rain> <threads> <steps> <seeds>` runs e032's season world (relief 64,
# winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, no digestion law, side grow, store 5)
# with the water running downhill at <water> of a cell's water per step (0: no water, e034), taking <leach> of the
# soil with it, e019's soil flow at <flow> (0.1 the old carrier; 0 the soil lies where laid) and the rain <rain>
# (flat: alike on every cell; high: by height); DEPTH=0.01 in the environment makes the water's surface count, MIX=0.05 mixes the soil of wet neighbors. From the repo root:
#   (nohup bash experiments/e035_water/run.sh 0.02 0.05 0 flat 1 100000 9 > experiments/e035_water/results/pilot_w0.02_l0.05_f0.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e035_water 2>&1 | tail -1
water=$1; leach=$2; flow=$3; rain=$4; threads=$5; steps=$6; depth=${DEPTH:-0}; mix=${MIX:-0}; shift 6
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e035_water $steps $s 128 0 0.02 8 64 $flow $rain 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high $water $leach $depth $mix &
done
wait
echo DONE water $water leach $leach flow $flow rain $rain steps $steps seeds "$@"
