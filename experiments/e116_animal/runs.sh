#!/bin/bash
# e116's runs (#135), from the repo root on Ubuntu. Writes experiments/e116_animal/results/<run>_*.
set -e
cd "$(dirname "$0")/../.."
B=./target/release/e116_animal
R=experiments/e116_animal/results
mkdir -p "$R"
# the bench: fixed animals at 400 a km2 of land, the world's side scaled to N, 60 days
$B $R/bench1k  side=2040  density=400 bench=1 days=60 seed=1 2> $R/bench1k.err &
$B $R/bench10k side=6450  density=400 bench=1 days=60 seed=1 2> $R/bench10k.err &
$B $R/bench30k side=11200 density=400 bench=1 days=60 seed=1 2> $R/bench30k.err &
# a population: 300 founders on 4 km, two years
$B $R/live side=4000 n=300 days=730 seed=1 2> $R/live.err &
# the same world recorded: 30 days at a frame a minute from day 60, and an hour at a frame a second on day 75
EVLOG_VIEW=rec:from=86400,len=43200,layers=1440 $B $R/look_lapse side=4000 n=300 days=91 seed=1 frame=60 2> $R/look_lapse.err &
EVLOG_VIEW=rec:from=6480000,len=3600,layers=600 $B $R/look_close side=4000 n=300 days=76 seed=1 frame=1 2> $R/look_close.err &
wait
