#!/bin/bash
# The eleven local runs of e022 (flat seed 4 ran on the Ubuntu box; the control too).
set -e
cd /Users/leo/src/evlog
for s in 1 2 3 4; do
  EVLOG_THREADS=1 ./target/release/e022_spill 1000000 $s 128 0 0.02 8 64 0.1 high &
  EVLOG_THREADS=1 ./target/release/e022_spill 1000000 $s 128 0 0.02 8 64 0.1 high 0.5 &
done
for s in 1 2 3; do
  EVLOG_THREADS=1 ./target/release/e022_spill 1000000 $s 128 0 0.02 8 64 0.1 flat &
done
wait
echo DONE
