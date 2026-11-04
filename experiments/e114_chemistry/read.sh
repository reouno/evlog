#!/bin/bash
# One run of e114 (#133) on e111's trial world: a 16 km world of 128 cells, producers sown in year 2, bodies in
# year 15, with e113's `all` on. From the repo root:
#
#     experiments/e114_chemistry/read.sh <name> [key=value ...]
#
# Writes experiments/e114_chemistry/results/$OUT/<name>_* (OUT: `read`, unless it is set).
set -e
cd "$(dirname "$0")/../.."
OUT="experiments/e114_chemistry/results/${OUT:-read}"
mkdir -p "$OUT"
exec ./target/release/e114_chemistry "$OUT/$1" base/worlds/isles1.params \
    size=128 edge=24 grain=40 sow=2 years=40 maps_years=1 threads=2 \
    body_sow=15 bodies0=300 big_s=1000 \
    road=1 worth=1 reach=1 bite=1 tear=0 ground=1 crown=1 floor=1 press_work=1 sight=1 cover=1 "${@:2}" 2> "$OUT/$1.err"
