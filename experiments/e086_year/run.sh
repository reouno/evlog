#!/bin/bash
# e086 (#93): stage A and B of c1225 with e062's draw d11 at a year of <year> steps, every other rate
# e062's. From the repo root:
#   (nohup bash experiments/e086_year/run.sh 1200 > experiments/e086_year/results/y1200.log 2>&1 < /dev/null &)
set -e
year=$1
out=experiments/e086_year/results/c1225_d11_y$year
./target/release/e086_year $out experiments/e062_producers/results/worlds/c1225.params \
  grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06 maps=1 year=$year
echo DONE $year
