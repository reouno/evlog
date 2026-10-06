#!/bin/bash
# e111's pilot (#130) on `isles1`: e110's `tick1` (bodies sown in year 40, read to year 70) with the design's four
# cycles on. From the repo root:
#
#     experiments/e111_holds/pilot.sh <name> [key=value ...]
#
# Writes experiments/e111_holds/results/pilot/<name>_*.
set -e
cd "$(dirname "$0")/../.."
OUT=experiments/e111_holds/results/pilot
mkdir -p "$OUT"
exec ./target/release/e111_holds "$OUT/$1" base/worlds/isles1.params \
    years=70 body_sow=40 big_s=4000 bodies0=2000 threads=6 \
    road=1 worth=1 reach=1 bite=1 "${@:2}" 2> "$OUT/$1.err"
