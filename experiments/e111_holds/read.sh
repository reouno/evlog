#!/bin/bash
# One reading of e111 (#130) on the trial world: a 16 km world of 128 cells, producers sown in year 2, bodies in
# year 15, read to year 30. From the repo root:
#
#     experiments/e111_holds/read.sh <name> [key=value ...]
#
# Writes experiments/e111_holds/results/$OUT/<name>_* (OUT: `read`, the readings, unless it is set - `set` for the
# design's runs).
set -e
cd "$(dirname "$0")/../.."
OUT="experiments/e111_holds/results/${OUT:-read}"
mkdir -p "$OUT"
exec ./target/release/e111_holds "$OUT/$1" base/worlds/isles1.params \
    size=128 edge=24 grain=40 sow=2 years=30 maps_years=1 threads=3 \
    body_sow=15 bodies0=300 big_s=1000 "${@:2}" 2> "$OUT/$1.err"
