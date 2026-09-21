#!/bin/bash
# e098 (#110): the spike's measurements. One core, sequential - a clock is not measured beside
# another run. From the repo root:
#   bash experiments/e098_cost3d/run.sh > experiments/e098_cost3d/results/spike.txt 2>&1
set -e
bin=./target/release/e098_cost3d
common="steps=200 warm=20 fill=0.85"
# The arms at the control's population, three seeds each.
for seed in 1 2 3; do
  $bin arm=2d bodies=10000 seed=$seed $common
  $bin arm=3d sz=8 height=4 bodies=10000 seed=$seed $common
  $bin arm=3d sz=4 height=4 bodies=10000 seed=$seed $common
done
# The same matter instead of the same population: the bodies a world of today's blocks would hold.
for seed in 1 2 3; do
  $bin arm=3d sz=8 height=4 bodies=1940 seed=$seed $common
  $bin arm=3d sz=4 height=4 bodies=3850 seed=$seed $common
done
# What each part costs, by what leaving it out saves (one seed, the two arms at 10,000 bodies).
for off in wear eat faces sense move births; do
  $bin arm=2d bodies=10000 seed=1 off=$off $common
  $bin arm=3d sz=8 height=4 bodies=10000 seed=1 off=$off $common
done
# The memory of a shallower world.
$bin arm=3d sz=8 height=2 bodies=10000 seed=1 $common
