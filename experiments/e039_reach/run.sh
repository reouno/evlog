#!/bin/bash
# The runs of e039 (#41): `run.sh <reach> <reachfix> <threads> <steps> <seeds>` runs e038's
# season world (relief 64, winter high 2, shade 2, spill 1, mutation 2/512, eyes 8, flesh 1,
# weight 1, side grow, store 5, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0,
# no ground store, k 1, sun 1) with the reach of a bite (#41) at <reach> cells of height per
# world cell of a body's length front to back (0: no column is out of reach, e038 byte for
# byte), or, with <reachfix> above 0, the same reach in cells for every body (the knockout).
# From the repo root:
#   (nohup bash experiments/e039_reach/run.sh 1 0 1 100000 9 > experiments/e039_reach/results/pilot_reach1.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e039_reach 2>&1 | tail -1
reach=$1; fix=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e039_reach $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 $reach $fix &
done
wait
echo DONE reach $reach fix $fix steps $steps seeds "$@"
