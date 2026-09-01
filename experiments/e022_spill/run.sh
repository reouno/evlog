#!/bin/bash
# The 128 runs of e022, one thread each. `run.sh <seeds>` runs the three worlds for each seed at
# relief 64, flow 0.1, shade 2, spill 1 (the ring of 8), mutation 2/512 per base: rain on the
# mountains, half of the breath to the air, and rain on every cell alike. `CONTROL=1 run.sh
# <seeds>` runs instead the control (spill 0: e021's canopy with the per-base mutation) on the
# mountain-rain world. From the repo root:
#   (nohup bash experiments/e022_spill/run.sh 1 2 3 4 > experiments/e022_spill/results/run.log 2>&1 < /dev/null &)
set -e
cargo build --release -p e022_spill 2>&1 | tail -1
for s in "$@"; do
  if [ -n "$CONTROL" ]; then
    EVLOG_THREADS=1 ./target/release/e022_spill 1000000 $s 128 0 0.02 8 64 0.1 high 1 2 0 &
  else
    EVLOG_THREADS=1 ./target/release/e022_spill 1000000 $s 128 0 0.02 8 64 0.1 high &
    EVLOG_THREADS=1 ./target/release/e022_spill 1000000 $s 128 0 0.02 8 64 0.1 high 0.5 &
    EVLOG_THREADS=1 ./target/release/e022_spill 1000000 $s 128 0 0.02 8 64 0.1 flat &
  fi
done
wait
echo DONE "$@"
