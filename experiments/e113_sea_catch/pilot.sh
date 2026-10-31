#!/bin/bash
# e113's pilot (#132) on `isles1`: e111's pilot (bodies sown in year 40, its four cycles on), read to year 70 unless
# `years=` says more; e113's arguments are in its README. From the repo root:
#
#     experiments/e113_sea_catch/pilot.sh <name> [key=value ...]
#
# Writes experiments/e113_sea_catch/results/pilot/<name>_*.
set -e
cd "$(dirname "$0")/../.."
OUT=experiments/e113_sea_catch/results/pilot
mkdir -p "$OUT"
exec ./target/release/e113_sea_catch "$OUT/$1" base/worlds/isles1.params \
    years=70 body_sow=40 big_s=4000 bodies0=2000 threads=6 \
    road=1 worth=1 reach=1 bite=1 "${@:2}" 2> "$OUT/$1.err"
