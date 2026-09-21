#!/bin/bash
# e097 step 1 (#109): the ladder over what step 0 named - the shape of the search and its reach.
# Four rungs at once, one core each, seed 9, 40,000 steps, a census every 1,000 from 20,000 (the
# shape e096's ladder read). The control is e096's own control run of this world and seed
# (results/c1225_life9_s0g0_*), which reproduced e081's seed-9 run to the body, and this
# experiment's step-0 run (results/c1225_life9_probe_*), which is the same world again.
#   (nohup bash experiments/e097_room/ladder.sh > experiments/e097_room/results/ladder.log 2>&1 < /dev/null &)
set -e
for rung in ring1:1:1 r2:2:0 ring2:2:1 r4:4:0; do
  name=${rung%%:*}; rest=${rung#*:}; far=${rest%%:*}; ring=${rest##*:}
  nohup bash experiments/e097_room/run.sh c1225 40000 9 $name reach=$far ring=$ring \
    census=1000 census_from=20000 > experiments/e097_room/results/c1225_life9_$name.log 2>&1 < /dev/null &
done
wait
echo LADDER_DONE
