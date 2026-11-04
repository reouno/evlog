#!/bin/bash
# e114's gate, again after its revision (#133): the litter kept by its make, the small eaters off it. Three runs on
# e111's trial world, two threads each, at once. From the repo root:
#
#     experiments/e114_chemistry/gate2.sh
cd "$(dirname "$0")/../.."
export OUT=gate
R=experiments/e114_chemistry/read.sh
$R off2 lock=0 &
$R make lock=1 &
$R make80 lock=1 years=80 &
wait
echo DONE
