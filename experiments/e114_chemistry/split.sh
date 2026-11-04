#!/bin/bash
# e114's gate failed (the land falls before the bodies are sown, the bodies die out by year 35, no lock appears):
# readings that part the design's two other clauses, on the trial world to year 40. From the repo root:
#
#     experiments/e114_chemistry/split.sh
cd "$(dirname "$0")/../.."
export OUT=gate
R=experiments/e114_chemistry/read.sh
$R no_lit_eat lock=1 lit_eat=0 &
$R no_lit_keep lock=1 lit_keep=0 &
$R neither lock=1 lit_eat=0 lit_keep=0 &
wait
echo DONE
