# e024 What flesh is worth

Date: 2026-09-02

## Purpose

The crowd is here (e022: bodies touch 0.2-0.8 times a step on the rings around the trees) and
the eye is here (e023: the crowd's body sees prey three to seven cells off and walks to it).
The tooth appears in every run and never pays: biters peak at 0.3-1.1% and no biter lineage
lasts. What a tooth wins is a cell of another body, and a cell is worth what it cost: 0.02 of
matter plus the cell's share of the body's energy, 0.10-0.15 in all, five to seven bites of
grass, for a push that must beat armor first. e008 put a prize on old bodies (up to 30x) and
e017 made a cell dearer (0.1) and both found the worth was not the lever - without a crowd
and without eyes. Now that a hunter could exist, the missing piece is a body worth eating.

The issue (#27) asks for the worth of flesh as a law about a material, with matter conserved.
The real world's premise: flesh is dense because an animal is the concentrate of what it ate
and burned; a kilogram of meat holds what many kilograms of grass held. The law here: a share
of what a body burns is fixed in its flesh instead of breathed. A body that has lived long is
worth more than the plant it stands on, by what it lived through; the matter comes from the
breath (so less rain), and returns through the eater or the soil. Nothing names a trait: the
body's own economy is unchanged (it pays the same upkeep and cannot spend the fat), only what
its cells are worth to others changes.

## Hypothesis

1. **A body is worth eating.** The worth of a cell (`worth`: cell matter plus the cell's share
   of energy and fat, mean over bodies) is at least twice e023's 0.10-0.15, and old bodies
   are worth many times a bite (fat grows with age at 0.3 x upkeep, 0.02 a step for a body of
   15 cells).
2. **Meat pays.** The energy eaters gain per cell broken (`kill_gain`) is at least twice
   e023's, and the meat share of the intake (kills and the dead) rises above e023's 5-18%.
3. **A hunter lineage lasts.** In at least one seed of four a lineage with a bite of 2 or more
   holds 100,000 steps or more, or the biters' share of the population stays above 1% over the
   last quarter (e023: 0 on median, peaks 0.3-1.1%, longest biter lineage under 20,000 steps).
4. **The world stands.** No death, matter conserved to 0.05%, population cv under 0.10 over
   the second half; the fat locked in bodies is a few percent of the world's matter and the
   rain falls as before.
5. **#19.** Lineages alive at the end at or above e023's 1-2; a hunter, if one comes, is a
   second winner beside the frame, not the same body.

## Method

Code: e023 (`experiments/e023_eyes`) with one law changed; `flesh 0` is e023 byte for byte
(checked on flat seed 9 over 30,000 steps: every CSV and JSONL identical but `steps_per_sec`
and the new columns).

- The flesh law: of the upkeep a body pays each step, a share `flesh` (1 by default, set after the runs; the code was run at 1 and 0.7) goes
  to the body's `fat` and the rest to the air (or the soil, by `breath`) as before. The body
  cannot spend its fat. A cell broken by a push yields, to a digesting pusher or to the
  ground, its matter (`cell_energy`) plus its share of the body's energy plus its share of
  the fat (`fat / mass`). A dead body lays its fat with its cells and energy. Matter: the fat
  is counted in the bodies' stock (`matter` in the log).
- New log columns: `fat_mean` (fat per body), `fat_stock` (fat in all bodies), `worth` (what
  a cell of a body would yield to its eater, mean over bodies), `kill_gain` (what eaters
  gained per cell broken). `agents.csv` gets `fat`.
- Argument 15 `flesh` (1 by default; 0 is e023's law), in the results prefix as `_flesh1`.
- Compute: none added (one multiply per body per step).

The control is e023's runs (`experiments/e023_eyes/results`, flat seeds 1-4): the same code
at `flesh 0`, so nothing is rerun.

Pilot, the dose series (flat seed 9, 200,000 steps, one run per share, 15-20 minutes each,
3 at once): `flesh` 0.1, 0.3, 0.5, 0.7, 0.85, 0.95 and 1, to see where the tooth begins to
pay and whether the world stands. The batch (two worlds, from the pilot): `flesh` 1 and
`flesh` 0.7, flat seeds 1-4 each, 500,000 steps, one thread each, 8 runs at once on the Mac
(12 cores; the shape and the winners settle by 300,000-500,000 steps, and a run at `flesh` 1
breaks 300 cells a step and goes at 100-130 steps per second, so 500,000 steps is 1.5-2
hours). The control, e023's runs, is compared over its first 500,000 steps.

Run (from the repo root):

    bash experiments/e024_flesh/run.sh 1 1 2 3 4
    bash experiments/e024_flesh/run.sh 0.7 1 2 3 4

Arguments: `<steps> <seed> <size> <widths> <cell_energy> <matter> <relief> <flow> <rain> <breath> <shade> <spill> <mutation> <eyes> <flesh>`;
the batch uses `500000 <seed> 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 <flesh>` (breath 1, shade 2,
spill 1, mutation 2/512, eyes 8).

## Result

### The dose (pilot, flat seed 9, 200,000 steps, medians over the second half)

| flesh | worth of a cell | intake from bodies | from fruit | biters | bodies killed per step | fat, share of the matter | air | bodies | mass | lineages |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (e023) | 0.13-0.18 | 5-18% | 21-75% | 0.0% | 0.00 | 0% | 73-110 | 1,050-2,200 | 8-22 | 1-2 |
| 0.1 | 0.31 | 23% | 58% | 0.0% | 0.00 | 2% | 81 | 1,492 | 13 | 1 |
| 0.3 | 0.58 | 32% | 50% | 0.0% | 0.00 | 6% | 89 | 2,172 | 12 | 1 |
| 0.5 | 0.87 | 44% | 45% | 0.0% | 0.00 | 15% | 79 | 2,632 | 12 | 2 |
| 0.7 | 0.72 | 56% | 38% | 0.0% | 0.00 | 16% | 71 | 3,760 | 12 | 1 |
| 0.85 | 0.72 | 64% | 30% | 17.0% | 1.74 | 14% | 45 | 2,375 | 23 | 4 |
| 0.95 | 0.60 | 69% | 26% | 25.5% | 2.64 | 12% | 34 | 2,063 | 28 | 1 |
| 1 | 0.68 | 72% | 24% | 24.6% | 4.97 | 14% | 22 | 2,586 | 26 | 2 |

(e023's row is its four flat runs over 1,000,000 steps.) A cell is worth 0.3-0.9 at every share
from 0.1 up - two to seven times e023's - and up to 0.7 nothing bites: the intake from other
bodies rises to 56%, all of it the dead eaten where they lie (bodies killed per step 0.00,
biters 0). Between 0.7 and 0.85 the world switches: biters 17-26% of the bodies, 1.7-5 bodies
killed per step, meat 64-72% of the intake, mass doubles to 23-28, and the worth of a cell is
the same 0.6-0.7 on both sides of the switch. What changes across it is the breath: the air
falls from 71 to 45-22, so the rain and the grass do (fruit 38% to 30-24%).

### The batch (flat seeds 1-4, 500,000 steps; e023 over its first 500,000)

Eight runs, one thread each, eight at once on the Mac: 90 minutes (80-135 steps per second).
Report: `report.html`. Ranges over seeds, medians over the second half unless said.

| | flesh 1, seeds 1, 2, 4 (the net state) | flesh 1, seed 3 (the hunter state) | flesh 0.7 | e023 (flesh 0) |
|---|---|---|---|---|
| Worth of a cell (a bite is 0.02) | 2.2-2.5 | 0.64 | 1.09-1.19 | 0.125-0.181 |
| What a kill paid per cell broken | - (no kills) | 0.45 | 0.14-0.70 (a kill every few thousand steps) | - |
| Fat per body; fat, share of the world's matter | 24-28; 63-70% | 2.7; 9% | 9.5-12.3; 25-29% | 0 |
| Intake from other bodies | 78-79% | 75% | 56-58% | 9-20% |
| Bodies killed per step; cells broken per step | 0.00; 0.00 | 3.95; 310 | 0.00; 0.00-0.13 | 0.00; 0.01-0.13 |
| Bodies with a bite (median / peak) | 0 / 0.001 | 0.46 / 0.50 | 0-0.001 / 0-0.004 | 0 / 0.002-0.008 |
| Longest lineage with a bite of 1 or more | - | 469,000 steps, 81% of its intake other bodies | - | 28,000 (e023 seed 3, meat 8%) |
| Population (cv) | 3,313-3,812 (0.02) | 4,509 (0.05) | 3,329-3,632 (0.02-0.05) | 1,139-1,648 (0.05-0.11) |
| Mass; world cells under a body | 11.7-11.8; 6.9-7.4 | 8.8; 2.5 | 11.2-12.7; 5.3-6.4 | 9.1-19.7; 3.1-6.2 |
| Hard; muscle per body | 0.01-0.02; 0.00-0.03 | 1.35; 2.14 | 0.03-0.07; 0.01-0.11 | 0.03-0.52; 0.08-1.49 |
| Air (the matter in the breath) | 0.4-2 | 20-23 | 59-66 | 73-110 |
| Intake from fruit | 20-22% | 20% | 35-36% | 35-72% |
| Contacts per body per step | 0.16-0.69 | 0.52 | 0.71-1.00 | 0.16-0.65 |
| Lineages alive | 2-3 | 2 | 1-3 | 1-2 |
| Bodies with a sensor | 0.5-6% | 7% | 0.2-1.8% | 2-57% |
| Matter at the end over the start | 0.998 | 0.982 | 0.999 | 1.000 |

The winners (report, Figure 2). At flesh 1 in seeds 1, 2 and 4 and at 0.7 in all four seeds the
winner is one body, the net: four pads of three gut cells at the four corners of the 8x8 box,
nothing between them, no armor, no muscle, no eye, twelve guts on six to seven world cells,
eating the dead from four places at once (78% of its intake the dead at 1, 54-56% at 0.7). At
flesh 1 seed 3 the world entered the hunter state at step 40,000 and kept it: the tooth, eight
cells two wide (two hard at the front, gut behind, three muscle at the back) on 2.5 world
cells, 7,139 agents at its peak, a bite on half its bodies, 81% of its intake other bodies,
the winner for 488,000 steps; beside it a gut of ten cells (lineage 814, 286,000 steps, 1,365
agents, 59% other bodies), the longest a second body has held against a first. The pilot at
flesh 1 (seed 9) also grew a 48-cell body with 9 hard, 13 muscle, a bite of 2 and 71% meat that
held 26,000 steps beside a smaller winner.

The states. The net state: 63-70% of the world's matter sits in living flesh, the air holds
0.4-2 (nothing is breathed; the corpses rot where they fall), the rain has stopped, a cell is
worth 2.2-2.5 because bodies grow old on a ground of corpses. The hunter state: 9% of the
matter in flesh, 300 cells broken and 4 bodies killed a step, prey dead at 124 steps of age, the
air fed by the work of moving (20-23), a cell worth 0.64. Same law, same share.

The matter. 0.998-0.999 at the end over the start in seven runs, 0.982 in the hunter run,
against e023's 1.000: the ground (`res`, `carrion`, `fruit`) is an f32 and corpses of 30-150
lie on it (a fat body of 64 cells at age 2,400 carried 130-160); the loss grows with the cells
broken (about 1.5e-5 per break in seed 3) and is there without breaks (0.2% in the net state).
It is e019's soil drift again (1.8% with an f32 soil, cured by an f64). Filed as an issue for
the ground.

## Conclusion

1. **A body is worth eating: yes.** A cell is worth 1.09-1.19 at 0.7 and 2.2-2.5 in the net
   state at 1, four to nineteen times e023's 0.125-0.181, and 0.64 in the hunter state, where
   nobody grows old.
2. **Meat pays: partly.** Other bodies are 56-80% of the intake (e023: 9-20%) and a cell broken
   by a push pays 0.45 in the hunter state, twenty bites. But in seven runs of eight the bodies
   killed per step are 0.00: the meat is corpses, eaten where they lie by a gut without a tooth.
3. **A hunter lineage lasts: one seed of four at flesh 1, and it holds.** Seed 3: a bite on
   44-50% of the bodies over the whole run, one lineage with a bite for 469,000 steps. Never at
   0.7 or below (the dose series: 0.1-0.7 no tooth, 0.85-1 the hunter state, on seed 9).
4. **The world stands: partly.** No death, population cv 0.02-0.05. The fat is not a few
   percent of the matter but 25-29% at 0.7 and 63-70% in the net state, where the rain has
   stopped. Matter 0.998-0.999, and 0.982 in the hunter run, by rounding on an f32 ground.
5. **#19: partly.** Lineages 1-3 (e023: 1-2); the hunter run holds two for 286,000 steps, the
   tooth and a gut beside it. The other seven runs have the same one winner, the net; e023's
   frame that sees is gone and the eye with it (a sensor on 0.2-7% of the bodies).

What it changes. The flesh law is kept (a share of the upkeep fixed in the flesh, yielded to
whoever breaks a cell, matter conserved; `flesh`, default 1: nothing a body burns is lost but
the work of moving). It answered the question of e008 and e017: the prize on a body was not the
lever, and the reason is that the prize is paid to whoever waits - the dead lie where they fall
and a gut eats them. The tooth pays in a state the world enters at the start (the pilots at
0.85-1, seed 3 at step 40,000) and keeps, where the meat is not left lying; there the world has
two winners and four kills a step, the most there has been to watch. The worth of a cell does
not decide the state (0.64 in the hunter's world, 2.4 in the net's); the start does, as in e022.
Open: why the switch sits between 0.7 and 0.85 (the air falls from 71 to 45 across it), whether
a net world ever tips into the hunter state later, the mountain worlds. Before the next
experiment: an f64 ground. Next: #25, what a block weighs (the armored hunter and the light net
are two bodies that could both be right); then #24, weather, which could move a world between
its two states.
