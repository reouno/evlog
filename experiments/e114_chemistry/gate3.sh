#!/bin/bash
# e114's gate, again after its revision (#133): the litter worn soft by its rot. Three runs on
# e111's trial world, two threads each, at once. From the repo root:
#
#     experiments/e114_chemistry/gate3.sh
cd "$(dirname "$0")/../.."
export OUT=gate
R=experiments/e114_chemistry/read.sh
$R off3 lock=0 &
$R worn lock=1 &
$R worn80 lock=1 years=80 &
wait
echo DONE
