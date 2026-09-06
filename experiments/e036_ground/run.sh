#!/bin/bash
# The runs of e036: `run.sh <root> <dig> <threads> <steps> <seeds>` runs e035's season world
# (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, side
# grow, store 5, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0) with the ground
# store (#36): a cell's ground holds <root> of the growth past the plant's cap (0: no store,
# e035 byte for byte) and a gut block digs <dig> of a bite out of it per step. From the repo root:
#   (nohup bash experiments/e036_ground/run.sh 4 0.5 1 100000 9 > experiments/e036_ground/results/pilot_root4_dig0.5.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e036_ground 2>&1 | tail -1
root=$1; dig=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e036_ground $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 $root $dig &
done
wait
echo DONE root $root dig $dig steps $steps seeds "$@"
