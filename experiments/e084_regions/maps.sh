#!/bin/bash
# The producers-only maps of e084 (#97): e062's binary with draw d11 and maps=1 on the five worlds other than
# c1225 (whose map is e062's), one core each, all at once, about 6 minutes. From the repo root:
#   cargo build --release -p e062_producers && bash experiments/e084_regions/maps.sh
set -e
out=experiments/e084_regions/results/maps
mkdir -p $out
for w in c1173 c1182 c1208 c1221 c1236; do
  nohup ./target/release/e062_producers $out/${w}_d11 experiments/e062_producers/results/worlds/$w.params \
    grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06 maps=1 > $out/${w}_d11.log 2>&1 < /dev/null &
done
wait
