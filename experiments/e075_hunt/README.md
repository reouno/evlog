# e075: what the flesh of kills needs to pay (stage C's thirteenth step, #90)

Date: 2026-09-16

## Purpose

#90 was written from a measure that was wrong. It said stage C's world has no predation at all -
"kills are 0.0% of what the bodies eat on all three seeds" - and asked what would make flesh pay.
The first thing this experiment did was read that number again, with no runs (`dryrun.py`).

**The world already eats the living.** e073's `sweep.py` divided the log's `kill_gain` column by the
intake, and that column is the gain **per cell broken**, not a total. The run's own `row.csv`, the
log's totals and the census all agree on the real figure:

| seed | log (meat less the dead) | `row.csv` | census | the wrong measure |
|---|---|---|---|---|
| 9 | 10.2% | 10.1% | 10.4% | 0.0006% |
| 10 | 8.1% | 8.2% | 12.9% | 0.0006% |
| 11 | 10.6% | 10.6% | 12.3% | 0.0007% |

13% of the deaths are bodies broken to their last block, and at a census two seeds of three hold a
kind taking 31-35% of its food from kills (`mixed / no tooth / roams / shore`). e072's and e073's
reports had it right; only #90 and `sweep.py` were wrong, and `sweep.py` is corrected in this commit.

What is true is the part of #90 that the measure did not decide: **no kind lives by killing.** The
most a kind takes from kills is a third, no kind is a flesh eater by e060's line (two thirds), and
the kinds held at every census are all plant eaters. This experiment asks why, and what it takes.

## What the dry run found (no runs of the bodies)

- A break gives **0.29** in a body's units, of which the fat is 0.165, the victim's energy 0.045 and
  the block's own matter 0.022. A whole body is worth 9.1 (p90 24): **one break is 2.9% of a prey**.
- A break takes about **17 presses** (0.60 contacts a press, 0.10 breaks a contact), and costs almost
  nothing: a body's moves are 0.001-0.002 a turn against an upkeep of 0.09-0.12.
- So a break is **0.9 turns of a full gut's feeding**, and the bodies that take flesh eat *less* in
  all: a toothed roamer takes 0.024 a turn from kills and 0.087 from plants, where a body that sits
  with no tooth takes 0.167 from plants and 0.047 from the dead.

The cost of hunting is not what stops it. **A bite is too small a mouthful**, and a prey is not a
meal but 35 mouthfuls that walk away between them.

## The set (#87: named together, never one law in a world without its counterweights)

Two laws, each a rate whose 0 is e073's kept world.

- **The tear** (`flesh_bite`): a gut that breaks a block off another body takes with it that share
  of what the body still holds, its energy and its fat. Real world: a predator eats through the
  wound it opens, not the scale it tore off. It is a line inside the contact physics (`push`), so it
  costs no compute.
- **The frail line** (`frail`): a body dies when its blocks fall under that share of the body it was
  born with, and lies where it fell. Real world: an animal dies of its wounds long before it is
  eaten. Today a body lives to its last block, so the only way to take a prey is to eat all of it.

The third condition of #90 - are prey dense enough to be met - is the crowd itself, and it needs no
law: the same runs are repeated with the crown's yield off, which is e072's thicker, less travelled
crowd. The fourth - do the plants nearby pay as well - is measured, not set: a sitter's 0.167 a turn
is what the flesh has to beat.

## Hypothesis

Written before the runs, with the conditions named together: **flesh pays when one tear takes a meal
(A) and a prey dies of its wounds instead of to its last block (B), and then a kind that lives by
killing appears.** The pass lines, set before the runs:

1. **A kind that lives by killing**: a kind holding e060's 5% of a census takes more than half its
   food from kills (the census's `killed`, which is the flesh of the living alone), on 2 seeds of 3.
2. **Stage C's measure does not fall** (#88): kinds at a census and kinds kept to a place at least
   e073's kept runs (6.61 and 3.89) on the same three seeds.
3. **The world stands**: matter conserved, bodies in all three media, and the crowd within e073's
   band (the kept runs hold 8,194-8,681).

What would refute it: the tear feeds every body that walks into another (the crowd grinds itself)
and no kind keeps to killing; or the frail line only feeds the sitters, who eat the fallen where
they lie; or the world falls.

## Method

Code: `experiments/e075_hunt`, e074's crate (its invasion instruments come along for #72's follow-up)
with the two rates above, a seventh cause of death (`wound`), and four columns in the log:
`deaths_wound`, `kill_intake` (the flesh of the living, as a total, which the log never held),
`flesh_intake` (what the tear itself gave) and `blocks_kept`.

Tests: a tear gives the breaker the block plus its share of what the prey holds, takes exactly that
much out of the prey, and gives a gutless breaker nothing; matter is conserved over 3,000 steps with
both rates on top of e072's seven sets and e073's two, no body lives under the frail line, and bodies
die of their wounds. **The check**: a run with both rates 0 must equal e073's kept run for seed 9
over its first 10,000 steps in every shared column of the log, in every body of the census, in every
lineage row and in every event (`check.py`).

**The search** (`search.py`, 11 runs, seed 9, 50,000 steps): the control, the tear alone at 0.05 /
0.15 / 0.4, the frail line alone at 0.5 / 0.75, four pairs of them, and the middle of the set in the
thicker crowd. Read with `sweep.py` (e073's, with the kills' share corrected).

**The batch**: the centre of the region that passes, on seeds 9-11 at 100,000 steps, against e073's
kept runs as the control.

**Cost**, stated before the runs: 11 runs of 50,000 steps on 11 of the Mac's 12 cores, about 20
minutes (a run of 100,000 steps takes 35 minutes on one core); then 3 runs of 100,000 steps on 3
cores, about 40 minutes. About 6 core-hours in all, nothing on the Ubuntu box.

## Result

(to come)

## Conclusion

(to come)
