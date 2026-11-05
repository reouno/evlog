#!/bin/bash
# e115's pilot (#134) on `isles1`: e113's pilot `all` (bodies sown in year 40, to year 100) with water in
# matter (and e114's chemistry, `lock=1`). From the repo root:
#
#     experiments/e115_water/pilot.sh <name> [key=value ...]
#
# Writes experiments/e115_water/results/pilot/<name>_*.
set -e
cd "$(dirname "$0")/../.."
OUT=experiments/e115_water/results/pilot
mkdir -p "$OUT"
exec ./target/release/e115_water "$OUT/$1" base/worlds/isles1.params \
    years=100 body_sow=40 big_s=4000 bodies0=2000 threads=6 \
    road=1 worth=1 reach=1 bite=1 tear=0 ground=1 crown=1 floor=1 press_work=1 sight=1 cover=1 "${@:2}" 2> "$OUT/$1.err"
