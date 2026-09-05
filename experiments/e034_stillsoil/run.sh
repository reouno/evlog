#!/bin/bash
# The runs of e034: `run.sh <flow> <rain> <winter> <amplitude> <threads> <steps> <seeds>` runs e032's season world
# (relief 64, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1, no digestion law, side grow, store 5) with
# the soil running downhill at <flow> of the drop per step (0.1 since e019; 0 nothing flows; 0.001 the tiny flow),
# the rain <rain> (high: on the mountains by height, e020; flat: on every cell alike) and the winter <winter>
# (high: the amplitude by height, e032; flat: the same everywhere) at the season's amplitude. From the repo root:
#   (nohup bash experiments/e034_stillsoil/run.sh 0.001 flat high 2 1 100000 9 > experiments/e034_stillsoil/results/pilot_f0.001_flat.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e034_stillsoil 2>&1 | tail -1
flow=$1; rain=$2; winter=$3; amp=$4; threads=$5; steps=$6; shift 6
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e034_stillsoil $steps $s 128 0 0.02 8 64 $flow $rain 1 2 1 0.00390625 8 1 1 season $amp 0 grow 5 0 0 $winter &
done
wait
echo DONE flow $flow rain $rain winter $winter amp $amp steps $steps seeds "$@"
