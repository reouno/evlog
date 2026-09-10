# e043 What a crown takes

Date: 2026-09-10

## Purpose

Since e022 the season world's food is a rain onto points. In e042's strict run (seed 9, steps
50,000-100,000) the canopy moves 132 of the light a step into the tall columns, 94 of it falls
back as fruit, and the cells' own plants grow by 12. In e041's control the fruit lay on 7-15% of
the cells, a third to a half of it on the richest 1%. Every law since e022 that needed a body to
move (e023 eyes, e037 size, e039 reach, e040 thirst, e041 stock) was tested in this world.

When e022 added the fall (what a column cannot hold falls as fruit on the ring of 8), it changed
the canopy in two more ways (#45): it dropped e021's saturation (a full crown intercepts nothing),
and it let a column under a body claim (#44). e021's canopy moved 5-18 of sun a step. This
experiment puts each back under the fall and asks which of the two makes the rain.

## Hypothesis

1. **The rain is the saturation's.** With `sat` the canopy moves under 30 a step and the fruit
   made falls by more than half; the light stays on the cells (their own growth rises above 40
   a step) and the food spreads (the share of it on the richest 1% of cells falls). `hold` alone
   moves the canopy's take by less than a quarter: the full crowns nobody stands on still take at
   the full rate.
2. **The world stands** in all four runs (e021's saturating canopy stood; with the fall it is a
   world nobody has run): bodies within a third of the control, no winter floor below half of it.
3. **A mover wins when the food is spread and a body pays what it owes.** Under `strict` (e042)
   and `sat` a held cell does not grow and the food no longer falls at a body's feet, so the work
   of moving per body rises, the mean muscle rises, and the sitters' share of the bodies at the end
   falls below the control's.

## Method

Code: e042 (`experiments/e042_strict`) as `e043_crown` with two arguments more, both off by
default, and `strict` 1 by default.

- **`sat`** (argument 39): under the fall too, a column claims `rate * (cap - res) / cap` (e021's
  law): a full crown claims nothing, a bitten one hardest. Off: e022's law, `rate` whatever its
  height.
- **`hold`** (argument 40, #44): a column under a body claims nothing (e021's law). Off: e022's
  law, it claims, and all of it falls as fruit around the body.
- **Log** (`pop.csv`, every 1,000 steps): `fruit_cells` (the share of cells holding at least 0.01
  of fruit, one step of a cell's sun), `fruit_top` (the share of the fruit lying on the richest 1%
  of the cells, 164 of 16,384), and `food_cells`, `food_top`, the same for all a gut eats on a
  cell (the plant standing, the dead, the fruit).
- **Checked**: `sat` 0 and `hold` 0 is e042's strict run byte for byte (the pilot's control against
  e042's strict seed 9).

**Runs.** Seed 9, 100,000 steps (five winters), one thread each, four at once on the Mac (4 of 12
cores, about 30 minutes), in e042's season world with `strict` 1:

| run | sat | hold | question |
|---|---|---|---|
| control (e042 strict, byte for byte) | 0 | 0 | the baseline, with the new columns |
| sat | 1 | 0 | is the rain the saturation's (1); does a mover win (3) |
| hold | 0 | 1 | is the rain the held column's (1) |
| both | 1 | 1 | e021's canopy under the fall: does the world stand (2) |

A batch on seeds 1-3 only if a variant changes who wins.

Run from the repo root: `bash experiments/e043_crown/run.sh <sat> <hold> <threads> <steps> <seeds>`.

**Measures.** The light: the canopy's take (`shade`), the fruit made (`fruit`), the cells' own
growth (`regrowth`), light lost to dryness and for want of soil. Where the food lies: the four
new columns. The world: bodies, the winter floors, trees, eaten a step and the share of it that
is flesh. The bodies: the work of moving per body, muscle, size, the sitters' share at the end,
the top lineage of the last third, the diversity number (#42).

**Compute.** `sat` and `hold` only skip claims (a full or held column's loop is not run): no
cost, if anything less. The new columns: two copies and two selections of 16,384 numbers every
1,000 steps.

## Result

**The pilot.** Seed 9, 100,000 steps, four runs at once on the Mac, 11-16 minutes each (sat +
hold 11, hold 13, control 15, sat 16: a full crown that claims nothing is a loop not run). Means
over the second half (steps 50,000-100,000): the bodies, their age and where the food lies from
`pop.csv` (every 1,000 steps), the rest from the log (every 10,000). The control is e042's strict
seed 9 byte for byte: every output file identical but the four new columns of `pop.csv` and the
parameter line.

The light (146 a step reaches the cells in every run: the fruit made, the own growth, the light
lost under bodies, to dryness and for want of soil add up to it) and where the food lies:

| run | canopy's take | fruit made | own growth | lost under bodies | dry | no soil | fruit lying | cells with fruit | fruit on the top 1% | cells with food | food on the top 1% | trees | eaten | flesh |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control | 132 | 94 | 12 | 3 | 27 | 11 | 4,094 | 7.8% | 61% | 37% | 48% | 217 | 109 | 36% |
| sat | 95 | 49 | 50 | 17 | 31 | 0.3 | 1,031 | 20.5% | 39% | 63% | 21% | 1,439 | 137 | 40% |
| hold | 125 | 80 | 24 | 5 | 32 | 5 | 3,960 | 8.4% | 55% | 41% | 34% | 689 | 105 | 34% |
| sat + hold | 43 | 0.5 | 78 | 40 | 27 | 1 | 13 | 2.3% | 75% | 68% | 27% | 769 | 102 | 24% |

The bodies ("decisions that move": the share of decisions that step forward and find room;
"sitters": the bodies in lineages whose mean body has under one muscle block, averaged over the
last third, because one sample swings by 30 points - 28-61% at step 100,000):

| run | winter floors | bodies | births a step | mean age | median size | mass | muscle | decisions that move | move cost a body | sitters | top lineage of the last third | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control | 605, 549, 698, 644, 612 | 2,020 | 7.0 | 647 | 12.4 | 19.9 | 4.33 | 23% | 0.0028 | 49% | 465: 14 cells, 7 muscle, 43% flesh; 47% | 2 |
| sat | 529, 664, 628, 589, 679 | 3,053 | 10.4 | 506 | 14.4 | 22.1 | 4.69 | 27% | 0.0045 | 42% | 276: 14 cells, 7 muscle, 53% flesh; 59% | 2 |
| hold | 500, 619, 621, 539, 598 | 2,149 | 8.5 | 520 | 15.4 | 22.8 | 4.97 | 31% | 0.0053 | 48% | 81: 11.5 cells, no muscle, 7% flesh; 35% | 2 |
| sat + hold | 685, 588, 535, 573, 491 | 1,996 | 3.2 | 921 | 16.0 | 29.0 | 3.52 | 46% | 0.0114 | 47% | 253: 16 cells, 5 muscle, 10 gut, 29% flesh; 61% | 3 |

**The fountain has two taps, and each law closes one.** With `hold` alone the canopy still moves
125 a step and 80 falls as fruit (the control 132 and 94): the full crowns nobody stands on take
at the full rate. With `sat` alone it moves 95 and 49 falls: the full crowns claim nothing, and
the columns that claim hardest are now the bitten ones - a column under a body is bitten and
cannot grow, so everything it claims falls around the body (the reading; the fruit is not logged
by whether its column is held). Only with both does the rain stop: 0.5 a step, 13 lying on the
whole world against 4,094.

**With both, the lawn is back.** The light stays on the cells (78 a step grown on them against
12), food lies on 68% of the cells against 37%, and 27% of it on the richest 1% against 48%. The
trees stand (769 against 217). The price is e016's: 40 of the 146 is lost under bodies (a plant
under a body does not grow) against 3. The world eats 102 a step against 109 and holds as many
bodies (1,996 against 2,020), with winter floors as deep (491-685 against 549-698).

**The bodies graze.** Under both, 46% of the decisions move the body against 23%: more of them
step forward (81% against 70%) and fewer are blocked (43% against 68%, the crowd is spread). The
bodies are heavier (mass 29 against 20), pay 4.1 times as much for moving, and live longer (a mean
age of 921 against 647, with 3.2 births a step against 7.0). The top lineage of the last third is
a 16-cell body on a 4x4 grid with 5 muscle and 10 gut blocks (61% of the body-steps), beside two
sitting guts of 9 and 16 cells: diversity 3, the control's 2.

**`sat` alone is the richest world on seed 9.** Fruit lies on 20.5% of the cells (7.8% in the control) and
food on 63%; the world eats 137 a step with 3,053 bodies (+51%) and 1,439 trees, and turns over
faster (10.4 births a step, a mean age of 506). The mover is on top, as in the control (59%).

**The sitters do not go.** Muscle-free lineages hold 42-49% of the bodies over the last third in
all four runs. What the canopy changes is how much the bodies move, not whether a sitting gut
exists: one is in every world, at 6-16 cells. A gut without muscle is not still: a forward
decision moves any body one sub-cell if the way is clear, and muscle only adds a second one with
probability `speed`.

**Round 2: a second seed and the start.** The pilot answers which half makes the rain; keeping
both as the season world also needs the world to stand on other seeds, and e022's fall began as a
lottery at the start (one world in five died in its first winter). So: `sat` and both on seed 10
at 100,000 steps (the control is e042's strict seed 10, the same world byte for byte), and both
on seeds 11-16 through the first winter (20,000 steps); eight runs at once, 15 minutes.

| run, seed 10 | fruit made | own growth | lost under bodies | food on the top 1% | winter floors | bodies | eaten | flesh | decisions that move | move cost a body | muscle | median size | sitters | top lineage of the last third | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control (e042) | 96 | 12.5 | 3 | - | 699, 757, 707, 663, 771 | 2,764 | 115 | 36% | 24% | 0.0029 | 3.01 | 10.0 | 53% | 178: 10 cells, 6 muscle, 48% flesh; 51% | 2 |
| sat | 31 | 59 | 27 | 29% | 676, 693, 652, 664, 683 | 2,475 | 115 | 29% | 38% | 0.0072 | 3.60 | 15.8 | 34% | 506: 15 cells, 3 muscle, 30% flesh; 22% | 2 |
| sat + hold | 2.2 | 78 | 44 | 23% | 446, 539, 482, 435, 509 | 2,418 | 144 | 46% | 40% | 0.0075 | 4.67 | 15.8 | 74% | 801: 16 gut cells, no muscle, mass 10, 13% flesh; 69% | 3 |

**The rain stops on seed 10 too.** Under both, 2.2 of fruit a step against 96, 78 grown on the
cells against 12.5, food on 65% of the cells and 23% of it on the richest 1%.

**The world stands, lower.** Seed 10's floors under both are 435-539 against the control's
663-771, a third lower (seed 9: 491-685 against 549-698, 8% lower), with 13% fewer bodies (2,418
against 2,764) that eat 25% more (144 a step against 115, 46% of it flesh).

**Who wins turns on the seed.** On seed 10 the top lineage under both is a light gut of 16 cells
and no muscle (lineage 801, mass 10 on an 11x11 grid), 69% of the last third, and muscle-free
lineages hold 74% of the bodies (the control 53%); a hunter of 8 muscle and 2 gut (89% flesh) held
the world for 8,000 steps (lineage 675, 62,000-70,000). The bodies move on 40% of their decisions
against 24%, and diversity is 3 again (the control 2).

**The start is not a lottery.** Under both, seeds 11-16 fall to 409-796 bodies in their first
winter (steps 15,000-16,000) and are back at 2,077-3,287 by step 20,000; seed 9's first trough was
685 (its control 605). No world died.

**`sat` alone on seed 10** leaves 31 of fruit a step (a third of the control's), holds the floors
within 8% (652-693), feeds 10% fewer bodies on the same food (115 a step), and splits the last
third among five lineages of 7-22% each (diversity 2). It is not seed 9's rich world.

## Conclusion

1. **The rain is the saturation's: partly.** Each law closes one of two taps. The saturation alone
   cuts the fruit by half to two thirds (94 to 49 on seed 9, 96 to 31 on seed 10), the held
   column's rest alone by 14%; only both stop it (0.5 and 2.2 a step). Under the saturation alone
   the bitten columns under bodies claim hardest and drop all of it (the reading, not measured).
2. **The world stands: yes.** All four on seed 9; both on eight seeds, six of them through the
   first winter only, with no lottery at the start. Under both the winter floors are 8% and 33%
   under the controls'.
3. **A mover wins when the food is spread and a body pays what it owes: partly.** The bodies move
   more in every variant (under both 40-46% of the decisions against 23-24%), but muscle-free
   lineages keep 42-49% of the bodies on seed 9, and 74% under both on seed 10, where a light gut
   of 16 cells wins. A gut without muscle still steps a sub-cell at a time.

**Kept**: the season world is `sat` 1 and `hold` 1 from here (the next experiment's defaults; both
default to 0 in this binary, e042 byte for byte). Why both and not the saturation alone: only both
stop the rain on both seeds, and only both give diversity 3 (the controls and `sat` alone: 2).
Both are e021's own premises, which e022 dropped when it added the fall, untested. The cost is
the winter floors, 8% and 33% lower.

No batch on seeds 1-3. The Method's rule was a batch if a variant changed who wins, and on seed 10
both put a gut without muscle on top where the control had a mover. Keeping the canopy does not
depend on who wins (it is the world's light, not a body's trait); the next experiment's control
runs in this world at its own length and shows what the lawn selects.

What this changes:

- **For the laws since e022.** The eye (e023), size (e037, e038), the reach (e039), the thirst
  (e040) and a growth that follows the stock (e041) were tested in a world whose food rained onto
  a few hundred cells. Now 65-68% of the cells hold food and a body eats by moving on. The laws
  that were not kept stay as arguments and can be tried again here.
- **For who wins.** It turns on the seed (a grazer on seed 9, a light gut on seed 10), and so does
  the mean age (921 and 425 under both, against 647 and 429).
- **Compute.** A full crown's claim is a loop not run: the run is a quarter faster (11 minutes
  against 15 on seed 9, four runs at once).
- **Next**: #47 (ageing), then #38, #5.
