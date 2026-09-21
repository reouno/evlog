#!/bin/bash
# e098 (#110), the rest of the spike: what one development costs, what the development is of a step,
# and what six runs at once cost each other - the batch's own shape (six seeds, one core each).
#   bash experiments/e098_cost3d/run2.sh > experiments/e098_cost3d/results/spike2.txt 2>&1
set -e
bin=./target/release/e098_cost3d
common="steps=200 warm=20 fill=0.85"
echo "# one development, 400 random genomes"
$bin arm=2d off=develop_only steps=400 seed=1
$bin arm=3d sz=8 off=develop_only steps=400 seed=1
$bin arm=3d sz=6 off=develop_only steps=400 seed=1
$bin arm=3d sz=4 off=develop_only steps=400 seed=1
echo "# the development left out of the step"
$bin arm=2d bodies=10000 seed=1 off=develop $common
$bin arm=3d sz=8 height=4 bodies=10000 seed=1 off=develop $common
echo "# six at once, the batch's shape"
for s in 1 2 3 4 5 6; do $bin arm=2d bodies=10000 seed=$s $common & done; wait
for s in 1 2 3 4 5 6; do $bin arm=3d sz=8 height=4 bodies=10000 seed=$s $common & done; wait
echo DONE
