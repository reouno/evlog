#!/bin/bash
# e114's pilot (#133) on `isles1`: e113's pilot `all` (bodies sown in year 40, to year 100) with the chemistry of
# matter. From the repo root:
#
#     experiments/e114_chemistry/pilot.sh <name> [key=value ...]
#
# Writes experiments/e114_chemistry/results/pilot/<name>_*.
set -e
cd "$(dirname "$0")/../.."
OUT=experiments/e114_chemistry/results/pilot
mkdir -p "$OUT"
exec ./target/release/e114_chemistry "$OUT/$1" base/worlds/isles1.params \
    years=100 body_sow=40 big_s=4000 bodies0=2000 threads=6 \
    road=1 worth=1 reach=1 bite=1 tear=0 ground=1 crown=1 floor=1 press_work=1 sight=1 cover=1 "${@:2}" 2> "$OUT/$1.err"
