#!/bin/bash
# e115's gate (#134): three runs on e111's trial world with e114's law on, two threads each, at once. From the
# repo root:
#
#     experiments/e115_water/gate.sh
cd "$(dirname "$0")/../.."
export OUT=gate
R=experiments/e115_water/read.sh
$R off lock=1 water=0 &
$R water lock=1 water=1 &
$R water80 lock=1 water=1 years=80 &
wait
echo DONE
