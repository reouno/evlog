#!/bin/bash
# e116's second look (#135), after watching on 2026-11-11: grass at real size, bodies at an animal's length, a mouth
# that crops while walking, gaits, a threat only while it comes nearer, no walking into the sea.
set -e
cd "$(dirname "$0")/../.."
B=./target/release/e116_animal
R=experiments/e116_animal/results
mkdir -p "$R"
# does a population still hold, and what it costs: one year
$B $R/live2 side=4000 n=300 days=365 seed=1 2> $R/live2.err &
# recorded: 10 days at a frame a minute from day 15, and an hour at a frame a second on day 20
EVLOG_VIEW=rec:from=21600,len=14400,layers=1440 $B $R/look2_lapse side=4000 n=300 days=26 seed=1 frame=60 2> $R/look2_lapse.err &
EVLOG_VIEW=rec:from=1728000,len=3600,layers=600 $B $R/look2_close side=4000 n=300 days=21 seed=1 frame=1 2> $R/look2_close.err &
wait
