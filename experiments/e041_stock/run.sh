#!/bin/bash
# The runs of e041 (#43): `run.sh <stock> <thirst> <threads> <steps> <seeds>` runs e040's season
# world (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1, weight 1,
# side grow, store 5, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, no ground
# store, k 1, sun 1, reach 0) with a plant that grows from what stands (#43): a cell holding
# <stock> or more grows at the full rate, one grazed below it by the share it stands of it, never
# under STOCK_FLOOR (0: the growth does not follow the stock, e040 byte for byte), and with a
# body that needs water (<thirst>, e040; 0: no body needs water).
# From the repo root:
#   (nohup bash experiments/e041_stock/run.sh 1 0.002 1 100000 9 > experiments/e041_stock/results/pilot_stock1_thirst0.002.log 2>&1 < /dev/null &)
set -e
stock=$1; thirst=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e041_stock $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 $thirst $stock &
done
wait
echo DONE stock $stock thirst $thirst steps $steps seeds "$@"
