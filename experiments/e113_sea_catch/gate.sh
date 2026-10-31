#!/bin/bash
# e113's gate (#132): six runs on e112's trial world, to year 40, two threads each, at once. From the repo root:
#
#     experiments/e113_sea_catch/gate.sh
#
# Writes experiments/e113_sea_catch/results/gate/<run>_*; prints DONE when all have ended.
cd "$(dirname "$0")/../.."
export OUT=gate
R=experiments/e113_sea_catch/read.sh
BASE="road=1 worth=1 reach=1 bite=1 tear=0 ground=1 crown=1 years=40 threads=2"
ALL="floor=1 press_work=1 sight=1 cover=1"
HUNT="inject_year=20 inject_kind=${HUNTER:-5}"
$R off $BASE &
$R all $BASE $ALL &
$R hunter $BASE $ALL $HUNT &
$R hunter_press $BASE press_work=1 $HUNT &
$R hunter_nosight $BASE press_work=1 floor=1 $HUNT &
$R no_floor $BASE press_work=1 sight=1 cover=1 &
wait
echo DONE
