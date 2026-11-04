#!/bin/bash
# e114's gate (#133): three runs on e111's trial world, two threads each, at once. From the repo root:
#
#     experiments/e114_chemistry/gate.sh
#
# Writes experiments/e114_chemistry/results/gate/<run>_*; prints DONE when all have ended.
cd "$(dirname "$0")/../.."
export OUT=gate
R=experiments/e114_chemistry/read.sh
$R off lock=0 &
$R lock lock=1 &
$R lock80 lock=1 years=80 &
wait
echo DONE
