#!/bin/bash
# One reading of e111 (#130) on the trial world: a 16 km world of 128 cells, producers sown in year 2, bodies in
# year 15, read to year 30. From the repo root:
#
#     experiments/e111_holds/read.sh <name> [key=value ...]
#
# Writes experiments/e111_holds/results/read/<name>_*.
set -e
cd "$(dirname "$0")/../.."
mkdir -p experiments/e111_holds/results/read
exec ./target/release/e111_holds "experiments/e111_holds/results/read/$1" base/worlds/isles1.params \
    size=128 edge=24 grain=40 sow=2 years=30 maps_years=1 threads=3 \
    body_sow=15 bodies0=300 big_s=1000 "${@:2}" 2> "experiments/e111_holds/results/read/$1.err"
