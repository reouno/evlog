#!/bin/bash
# The runs of e052 (#55): `run.sh <clock> <brain> <threads> <steps> <seeds>` runs e048's world
# (the season world under the motor: relief 64, winter high 2, shade 2, spill 1, mutation 2/512,
# eyes 8, flesh 1, weight 1, side grow, rain flat, water 0.1, leach 0.01, depth 0.01, mix 0.2,
# flow 0, no ground store, k 1, sun 1, reach 0, no thirst, store 5, strict 1, sat 1, hold 1, wear
# 3,000, corners hold, plant yield 1, motor 1, no band, no stock) with <clock> (the exponent of a
# body's own time: a body of mass m takes (16 / m)^clock turns a step, at most one; 0: every body
# takes a turn every step, e051 byte for byte) and <brain> (e050: 0 the policy, 1 the brain that
# remembers and learns).
# From the repo root:
#   (nohup bash experiments/e052_clock/run.sh 0.25 0 1 100000 9 10 11 12 > experiments/e052_clock/results/batch.log 2>&1 < /dev/null &)
set -e
clock=$1; brain=$2; threads=$3; steps=$4; shift 4
for s in "$@"; do
  EVLOG_THREADS=$threads ./target/release/e052_clock $steps $s 128 0 0.02 8 64 0 flat 1 2 1 0.00390625 8 1 1 season 2 0 grow 5 0 0 high 0.1 0.01 0.01 0.2 0 0 grew 1 1 0 0 0 0 1 1 1 3000 2 1 1 0 $brain $clock &
done
wait
echo DONE clock $clock brain $brain steps $steps seeds "$@"
