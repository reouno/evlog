#!/bin/bash
# The runs of e033: `run.sh <rain> <winter> <amplitude> <threads> <steps> <seeds>` runs e032's season world (relief 64,
# flow 0.1, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, no digestion law, side grow, store 5) with
# the rain <rain> (high: on the mountains by height, e020; flat: on every cell alike, e021-e032) and the winter
# <winter> (high: the amplitude by height, e032; flat: the same everywhere) at the season's amplitude. From the repo root:
#   (nohup bash experiments/e033_wetridge/run.sh high high 2 1 300000 1 2 3 > experiments/e033_wetridge/results/run_high_high2.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e033_wetridge 2>&1 | tail -1
rain=$1; winter=$2; amp=$3; threads=$4; steps=$5; shift 5
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e033_wetridge $steps $s 128 0 0.02 8 64 0.1 $rain 1 2 1 0.00390625 8 1 1 season $amp 0 grow 5 0 0 $winter &
done
wait
echo DONE rain $rain winter $winter amp $amp steps $steps seeds "$@"
