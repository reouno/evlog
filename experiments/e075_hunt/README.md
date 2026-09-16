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

**The checks.** A run with both rates 0 equals e073's kept run for seed 9 over 10,000 steps in all 163
shared log columns, in every body of the census (7,624), in every lineage row and in every event.
Matter drifts by at most 6.0e-14 over the 12 runs of 100,000 steps, and every run holds bodies on the
land, at the surface and on the bottom.

**The search** (11 runs, seed 9, 50,000 steps). The tear buys the flesh and the frail line does not:
the kills' share goes from the control's 11.7% to 13.7% / 21.1% / 26.4% at a tear of 0.05 / 0.15 /
0.4, while the frail line alone *lowers* it to 8.5% at 0.5 and 5.1% at 0.75 - a prey dies before it
is eaten and its store lies in the cell for whoever stands there. But the frail line is what keeps
kinds to a medium (3.7 in the control against 5.3-5.7 with it). The thicker crowd (the crown's yield
off) was worse on both counts: its flesh kinds are gone and the kinds kept to a place fall to 3.7.

Two centres came out of it and neither passed both lines set before the runs, so the search's own
compromise was run as well. Three worlds, three seeds each, 100,000 steps, against e073's kept runs:

| world | gain a break | kills | of it, the tear | kinds at a census | kept to a place | hunter kinds (of 3 seeds) | bodies | blocks | hard |
|---|---|---|---|---|---|---|---|---|---|
| control (e073) | 0.30 | 9.6% | - | 6.61 | 3.89 | 0 | 8,433 | 34.9 | 7.3% |
| the tear 0.4 | 0.88 | 28.1% | 88% | 7.28 | 3.56 | 3 | 8,652 | 27.6 | 9.5% |
| the set 0.15 / frail 0.75 | 0.82 | 19.0% | 80% | 7.17 | 4.00 | 1 | 7,801 | 33.7 | 9.5% |
| **both: tear 0.4 / frail 0.5** | **1.01** | **27.4%** | **88%** | **7.67** | **4.78** | **2** | **9,099** | **28.1** | **9.9%** |

### 1. The tear is what makes flesh a food, and the frail line is what places the kinds

Alone, each law moves one measure and not the other: the tear puts the kills' share over e060's line
for a hunter world (25%) and leaves the kinds kept to a place at 3.56, below the control's 3.89; the
frail line holds the place (4.00) and leaves the kills at 19%. Together both rise - 27.4% of the
intake and 4.78 kinds kept to a place, above the control on every seed (5.2, 4.7, 4.5 against 3.5,
4.0, 4.2). That is #87's rule in one table: neither law is worth keeping alone.

### 2. The land's browser becomes a hunter

Under the control the biggest land kind is `plant/tooth/roams/land`: a tooth, 24-34% of its food from
the crowns, 9-19% from kills. Under the set the same shape is `mixed/tooth/roams/land`, 8.6-13.7% of
the grown bodies, **46-52% of its food from kills** and 15-24% from wood, with a hard face on a
quarter of its blocks, walking 14-20 cells in a life. Pure flesh kinds (over two thirds from kills)
appear too, at the shore and on the bottom, but they stay small: 2-4% of the grown bodies.

So the hunter of this world is a browser that hunts, not a carnivore. A kind holding 5% of a census
and taking more than half its food from kills is there on 2 seeds of 3 (the third reaches 46%).

### 3. What the set costs the world

Bodies are smaller (28.1 blocks against 34.9) and shorter-lived (a median death at 78 steps against
91), the bottom's crowd grows by a third, and 12.7% of the deaths are wounds. The crowd is larger,
not smaller (9,099 against 8,433). A step costs 26.0 ms against 19.0: the laws add no pass over the
bodies - the tear is a line inside the contact physics and the frail line a comparison in the death
loop - the extra time is the larger crowd and the blocks it breaks.

### The hypotheses

1. **A kind that lives by killing: yes at 0.4 / 0.5** (2 seeds of 3, and 46% on the third), and yes
   for the tear alone on 3 of 3. No, for the tear at 0.15 with the frail line at 0.75 (1 of 3).
2. **Stage C's measure does not fall: yes for the set** (7.67 and 4.78 against 6.61 and 3.89), no for
   the tear alone (3.56 kinds kept to a place).
3. **The world stands: yes.** Matter to 6.0e-14, bodies in all three media in all 12 runs, 8,860-9,442
   bodies against the control's 8,203-8,652.

## Conclusion

**Kept, as a set: `flesh_bite` 0.4 with `frail` 0.5 is stage C's default world from here**, and the
controls are `experiments/e075_hunt/results/ladder/c1225_life{9,10,11}_both`.

The answer to #90 is not the one the issue asked for. The world already ate the living (8-13% of the
intake); what it had no way to do was **take a meal**. A break gave a hunter 2.9% of its prey, about
one turn of grazing, so flesh was a by-product of walking into things. The tear makes one strike
worth a meal (a break gives 1.01 against 0.30) and the frail line means the prey dies of it. Then a
quarter of everything the world eats is the flesh of the living, and the biggest land kind lives half
by hunting and half by browsing.

Two lessons for the series beyond the law. **A measure that nobody re-derives is a law about the
world**: "kills are 0.0%" was one column read wrong, and it set the question for a whole issue.
And **a food is defined by its mouthful, not by its price**: five experiments looked for what made
hunting too expensive, and the cost was never the barrier.

These answers hold for this world and these choices: c1225, seeds 9-11, e073's kept world at
`wood_yield` 3e-5, 100,000 steps, e068's census with its 5% line, and the two rates searched at 0.05
to 0.4 and 0.5 to 0.75. Not shown: the rates between 0.15 and 0.4, a longer run, whether the hunter
and the grazer invade each other (#72's instrument is in this crate for exactly that), and whether a
pure flesh kind can hold more than 4% of a world this crowded.
