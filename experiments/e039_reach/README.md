# e039 A food only a big body reaches

Date: 2026-09-09

## Purpose

Every winner since e016 is 11-16 cells. e037 (#39) made a big body cheaper and the steady state
did not move; e038 (#40) gave the world two and four times the sun and a gut block still earned
0.003-0.005 a step, the extra sun becoming more bodies of the same size or smaller. The income
per block is pinned by the crowd, not by the sun, so a law that gives the world more food is
eaten by more small bodies. What escapes the pinning is an income the crowd cannot dilute: a
food only a big body reaches (#41).

The world already has the food. Since e021 a cell's plant is a column that stands, shades as far
as it is tall, and spills what it cannot hold as fruit; the trees hold 1,349 of matter on 338
cells (a mean height of 4) in the control. But a bite is the same bite whatever stands there: a
4-cell body eats a tree as well as a 40-cell one does. This experiment gives the bite a reach.

Read it as the first law of the third axis of an environment (principles 7): an environment
differs by place, by time, and by the size of the body looking at it. The tree's height is an
environment only a tall body sees.

## Hypothesis

1. **Size pays.** With the reach, the standing column is worth more to a long body than to a
   short one, so the size distribution after the start's transient (step 40,000 on) moves up
   (median above 16, 90th percentile above 25, `len_fwd` above the control's 4.2 sub-cells), the
   intake from the trees goes to the longer bodies (`tree_len` above `len_fwd`), and a browser
   lineage holds beside the grazer: two winners, and the diversity number (#42) above 1.
2. **Or the world pays and nothing moves.** The trees are 5% of the intake (5.6 a step of 116),
   so the reach may only lock that away: the trees grow past every mouth, the crowd lives on the
   fruit they spill, the bodies stay at 11-16 cells and the floors fall.

## Method

Code: e038 (`experiments/e038_income`) as `e039_reach` with one argument more, off by default
(`reach` 0 is e038 byte for byte; checked on seed 9 for 10,000 steps: `log.csv` without the new
column, `pop.csv`, `agents.csv`, `lineages.csv`, `events.csv`, `places.csv` and `dist.csv`
identical by md5, `steps_per_sec` apart).

- **The reach of a bite** (argument 34, `reach`). A column of `h` matter stands `h` cells tall
  (the canopy's own reading since e021). What a gut block takes from the standing plant in a
  step is its bite times `min(1, reach_h / h)`, where the body's reach `reach_h` is `reach`
  world cells of height per world cell of its length front to back (SUB 4 sub-cells to a world
  cell): a body 4 sub-cells long reaches `reach`, the longest body (16) reaches 4 `reach`. What
  lies above the reach stands, shades and falls as fruit as before. The fruit and the dead lie
  on the ground: every mouth takes those whole.
- **Why the rate and not the stock.** A bite is 0.02 per gut block (0.32 for the largest body)
  and a tree holds 1 to 8 (50 to 400 bites), so a cap on the stock within reach - min(h, reach) -
  would bind on no column a body ever stands on. What a reach decides is how much of a plant a
  mouth can work on at once.
- **Why the length front to back.** The world has no up axis (#5 would give one), so a body's
  height is read from its length: a long body is one that rears. `len_fwd` is 4.2 sub-cells in
  the control (about one world cell), `side` 4 to 16 under `grow`.

**Runs.** Seed 9, 100,000 steps (five winters), one thread each, four at once on the Mac (4 of
12 cores), in e038's season world (`winter high` 2, water 0.1, leach 0.01, depth 0.01, mix 0.2,
flow 0, rain flat, store 5, grow, no ground store, k 1, sun 1): `reach` 0.5, 1 and 2, against
the control at `reach` 0 (e037's pilot run again, byte for byte). At `reach` 1 a body of the
control's length reaches 1.06 and takes a quarter of its bite from a tree of height 4, where the
longest body takes all of it: the same fourfold gradient at every dose, set higher or lower
against the trees the world grows. A batch on seeds 1-3 at 300,000 steps only if the pilot moves.

Run from the repo root: `bash experiments/e039_reach/run.sh <reach> <reachfix> <threads> <steps> <seeds>`.

**Measures.** The size distribution (`size_p10`, `size_p50`, `size_p90`, `size_max`) and
`len_fwd` after step 40,000; `tree_len` (the length front to back of the bodies eating from the
trees, weighted by what they take) against `len_fwd` (all bodies): whose food the standing plant
is; `tree_eaten`, `trees`, `tree_res`, `res_max`, `fruit`, `fruit_eaten` (where the world's
matter goes); `intake_per_gut`; the winter floors and the valley's share (`pop.csv`); the
winners' shapes (`lineages.csv`, `bodies.jsonl`); the biters (`biters_any_share`); and the
diversity number (#42).

**The diversity number (#42).** One number, the same in every experiment from here on, beside
the lineage count: the winners are the lineages holding at least 5% of the body-steps of a
window (the last third of the run); two winners are the same body when their sizes are within a
factor of 1.5 and the mixes of their blocks (each kind's count over the size) differ by at most
0.4 in sum; the winners are grouped by single linkage on that relation (e006's rule for
lineages, applied to shapes) and the number of groups is the diversity. Counted for the whole
world and per height band (valley, slope, ridge). Written in `report.py` here and copied from
here on.

## Result

**The pilot.** Seed 9, 100,000 steps, means over the second half (steps 50,000-100,000); the floors
are the five winter troughs in order. Wall time 13-17 minutes a run, four at once.

| run | winter floors | bodies | size p10 / p50 / p90 | size mean | length front to back | the trees pay per step | standing plant (cells) | a gut block earns | biters | lineages at the end | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| reach 0 (today) | 626, 696, 724, 743, 775 | 3,591 | 3 / 9 / 22 | 11.0 | 4.23 | 5.6 | 1,349 (338) | 0.0030 | 2% | 2 | 2 |
| reach 0.5 | 57, 435, 421, 533, 586 | 2,730 | 5 / 15 / 31 | 16.7 | 4.70 | 10.3 | 2,727 (610) | 0.0024 | 3% | 9 | 2 |
| reach 1 | 358, 587, 662, 334, 341 | 2,796 | 5 / 15 / 31 | 16.6 | 4.89 | 9.4 | 2,288 (543) | 0.0025 | 7% | 4 | 3 |
| reach 2 | 594, 624, 686, 650, 580 | 2,733 | 4 / 14 / 43 | 18.2 | 4.28 | 4.4 | 889 (221) | 0.0027 | 21% | 2 | 2 |

Size moves on this seed, at every dose: the median body goes from 9 cells to 14-15, the mean from
11.0 to 16.6-18.2, the 90th percentile from 22 to 31-43. No law in the series has moved it before
(e029 the grid, e037 the upkeep's slope, e038 the sun: all left it at 11-16). The knockout and
the other seeds below take this back.

The world pays a quarter of its bodies (3,591 to 2,730-2,796) and eats 8-12% less (128 a step to
113-119). At `reach` 0.5 the first winter is a near miss (57 bodies).

The trees answer as the law says they should: what the crowd cannot take grows. The standing
plant doubles at `reach` 0.5 and 1 (2,727 and 2,288 on 610 and 543 cells, against 1,349 on 338),
and, because there is more of it, it pays out more in total than in the control (10.3 and 9.4 a
step against 5.6) although every bite from it is cut to a quarter or a half. At `reach` 2 the
trees are eaten down instead (889 on 221 cells): the bodies reach most columns.

The winner changes. The control's top lineage is a bar of ten gut cells lying across its facing,
2.1 sub-cells long and 6.6 wide - the shortest mouth the world can grow, and the body the law
punishes most. Under `reach` 1 the winners are 4.4 to 5.8 long: a 21-cell body with nine muscle
and eleven gut (60% of the body-steps of the last third), a 17-cell biter beside it. Under
`reach` 2 the world enters the hunter state at step 40,000 and holds it: 21% of bodies bite, and
a 35-cell hunter with sixteen hard blocks and a bite of 2.7 (57% flesh) stands beside a 12-cell
gut bar.

**The knockout (the gradient against the tax).** The seed-9 pilot cannot say whether the bodies
answered the reach or the loss: the law takes a share of every bite from a tall column, so the
standing plant is worth less to everyone. `reachfix` (argument 35, e009's rule for testing an
eye) gives every body the same reach in cells whatever its length: the same loss, no gradient.
Run at 1.0 (the reach of a body of the control's length, 4.2 sub-cells) and at 1.25 on seed 9,
and at 1.0 on seeds 1-3, against `reach` 1 and the control on the same seeds (the controls on
seeds 1-3 are e035's runs of this world, the same code). Means over steps 50,000-100,000:

| seed | control: mean body / length / bodies | reach 1 | fix 1 |
|---|---|---|---|
| 9 | 11.0 / 4.22 / 3,591 | 16.6 / 4.89 / 2,796 | 17.4 / 4.85 / 2,909 |
| 1 | 11.9 / 3.38 / 3,182 | 13.4 / 3.95 / 3,033 | 21.9 / 4.86 / 2,072 |
| 2 | 16.2 / 5.14 / 3,432 | 18.7 / 7.32 / 2,408 | 16.7 / 4.02 / 2,966 |
| 3 | 16.4 / 4.06 / 2,178 | 15.5 / 4.40 / 2,413 | 14.4 / 3.67 / 2,577 |

The length rises under the reach in four seeds of four (+0.34, +0.56, +0.66, +2.18 sub-cells) and
does not under the knockout (+1.48, +0.62, -0.38, -1.12): the law selects the property it prices.
The size in cells does not follow it. The control's own mean body is 11.0-16.4 by seed, `reach` 1
is +1.6, +2.5, +5.6 and -1.0 against its seed, and the knockout moves it as much (+10.0, +6.3,
+0.5, -2.0): the seed-9 pilot's step from 11 to 17 cells is inside the spread of the seeds and is
not the reach's. Both the law and the knockout grow the forest (the standing plant 1.5 to 7.7
times the control's), because both make the standing plant cost more to take.

**The batch.** Seeds 1-3, 300,000 steps at `reach` 1 (about 65 minutes a run, three at once),
against e035's runs of this world on the same seeds. Means over the last half (steps 150,000-300,000); the floors
are the last five winter troughs.

| run | last five winter floors | bodies | size p50 / mean / p90 | length | standing plant (cells) | a gut block earns | biters | lineages at the end | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|
| seed 1 control | 785, 814, 799, 745, 768 | 2,644 | 16 / 13.6 / 17 | 3.64 | 677 (202) | 0.0036 | 1% | 2 | 2 |
| seed 1, reach 1 | 720, 710, 685, 601, 810 | 2,532 | 15 / 14.6 / 22 | 3.91 | 1,476 (382) | 0.0034 | 1% | 7 | 2 |
| seed 2 control | 720, 733, 803, 802, 874 | 3,465 | 13 / 16.2 / 29 | 5.09 | 977 (254) | 0.0024 | 2% | 2 | 2 |
| seed 2, reach 1 | 354, 358, 181, 304, 240 | 2,557 | 12 / 15.3 / 27 | 13.39 | 6,214 (1,228) | 0.0023 | 0% | 6 | 1 |
| seed 3 control | 659, 676, 736, 689, 702 | 2,572 | 16 / 13.9 / 16 | 3.89 | 675 (248) | 0.0033 | 19% | 14 | 1 |
| seed 3, reach 1 | 547, 598, 519, 550, 570 | 2,059 | 16 / 15.8 / 19 | 3.98 | 287 (86) | 0.0033 | 0% | 8 | 2 |

The mean body is +1.0, -0.9 and +1.9 cells against its seed: size does not move at 300,000 steps
either. What moves is the length, and only where the world takes the law's offer: seed 2 stands
at 13.4 sub-cells against the control's 5.1, and its winner is a body 14.7 long and 2.8 wide - a
pole of 12.7 cells over four world cells, nine gut blocks, no bite - holding 75% of the
body-steps of the last third. Its forest is six times the control's (6,214 standing on 1,228
cells). Seeds 1 and 3 stay at 3.9-4.0 long; seed 3's forest is a third of its control's, because
the law also ended its hunter state (biters 19% to 0.1%) and its bodies graze the lawn down.

The world pays for it: bodies fall 4%, 26% and 20%, and in seed 2 the winter floors fall from
691-874 to 144-551. The diversity number falls in seed 2, from two winners (a wide bar of 9.4
cells and a mover of 24.8) to one (the pole and its two near-kin); it is 2 against 2 in seed 1
and 1 against 2 in seed 3. No browser stands beside a grazer anywhere.

## Conclusion

**Not kept** (`reach` stays an argument, 0 by default). The law does exactly what it says and the
world answers it exactly: what the reach prices is the body's length front to back, and the
length is what grows - in four seeds of four at 100,000 steps, and to 13.4 sub-cells in one seed
of three at 300,000. Hypothesis 1 is answered no all the same, because length is not size. The
body that took the trees of seed 2 is a pole of 12.7 cells, 14.7 long and 2.8 wide: it reaches
the crown of a four-cell column with less matter than the control's winner carries. Nothing in
the world makes a long body cost more than a short one of the same cells, so a food out of reach
buys a shape, not a mass.

What the world pays is real: 4-26% of its bodies, the winter floors of seed 2 more than halved,
and, where the law bites hardest, a winner lost (diversity 2 to 1). The knockout says the rest of
what the pilot showed - a bigger mean body, a doubled forest - is not the reach's but the loss's:
a tax on taking the standing plant does the same without any gradient.

What this changes:

- **For #41 and for size.** A reach must be priced on mass. In a world with no up axis, a body's
  height is a shape it can have for free, and the crowd will grow it cheaply rather than grow
  large. This is the first concrete argument for #5 (3D bodies) beyond legs and wings: the third
  axis of an environment (principles 7) needs a body axis that costs matter to stand up in. The
  other route, in this world as it stands, is a reach that costs - a column a mouth must climb,
  or a body that must hold itself up - which is a law about the body, not about the material,
  and so is against the project's rule.
- **For the trees.** A tax on the standing plant is mostly a subsidy to it: the forest grows 1.5
  to 7.7 times at 100,000 steps under the law and under the knockout alike. It is not a rule: at
  300,000 steps seed 3's forest is a third of its control's, because the law ended that seed's
  hunter state and its grazers ate the lawn and the trees down.
- **For the diversity number (#42).** It is written and reported here (winners above 5% of the
  body-steps of the last third, grouped by single linkage on size within a factor of 1.5 and
  block mixes within 0.4). It reads 1-3 in this experiment, where the lineage count reads 2-14: it is the tighter measure the issue asked for. Two cautions from its first use: it
  is sensitive at the margin (a window a few thousand steps wider turned a 3 into a 2 on one
  run), and a lineage's blocks are logged as its mean over the world, so a lineage with a
  different body on each place counts once.

Next: #37 (a body that needs water) and #38 (the rain on the ridge), then #5 with the reach in
mind. Open from here: whether the pole of seed 2 is a body the viewer would enjoy (it is the
first body in the series that is a line four world cells long), and why seeds 1 and 3 did not
take the law's offer at all - the forest of seed 2 is six times theirs, so the offer's size is
the world's own state, not the law's dose.
