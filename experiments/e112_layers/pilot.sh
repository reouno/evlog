#!/bin/bash
# e112's pilot (#125) on `isles1`: e111's pilot (bodies sown in year 40, its four cycles on), read to year 70 unless
# `years=` says more. From the repo root:
#
#     experiments/e112_layers/pilot.sh <name> [key=value ...]
#
# Writes experiments/e112_layers/results/pilot/<name>_*.
set -e
cd "$(dirname "$0")/../.."
OUT=experiments/e112_layers/results/pilot
mkdir -p "$OUT"
exec ./target/release/e112_layers "$OUT/$1" base/worlds/isles1.params \
    years=70 body_sow=40 big_s=4000 bodies0=2000 threads=6 \
    road=1 worth=1 reach=1 bite=1 "${@:2}" 2> "$OUT/$1.err"
