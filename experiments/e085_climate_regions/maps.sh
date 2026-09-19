#!/bin/bash
# The climate maps of e085 (#98): e061's binary with maps=1 on stage A's 34 passing climates (their lines from
# e061's candidates.txt, longest first), 10 at once, about 10 minutes. From the repo root:
#   cargo build --release -p e061_climate && bash experiments/e085_climate_regions/maps.sh
# The maps (4-14 MB each) are not committed.
set -e
mkdir -p experiments/e085_climate_regions/results/maps
xargs -P 10 -L 1 ./target/release/e061_climate < experiments/e085_climate_regions/candidates.txt \
  > experiments/e085_climate_regions/results/maps/all.log 2>&1
