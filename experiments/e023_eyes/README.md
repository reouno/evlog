# e023 Eyes that see far

Date: 2026-09-02

## Purpose

e022's spill put the world's food in piles on the rings around the trees, and its start showed
what that costs a body that sees two cells: the lawn under the crowns goes dark in the first
hundred steps, the production lies clumped on the rings, and the bodies wander the dark lawn
and starve - one world in five dies before step 4,000, the rest pass through bottlenecks of
7-431 bodies. In the standing world the same limit holds: a body finds a pile by walking into
it. Nothing sees farther than two cells, and a sensor block only sharpens the second (e009
found eyes do not pay when there is nothing to see; there is something to see now).

The issue (#26) writes the eye as a law about a material: a sensor block sees a distance. A
body's range grows with its sensor blocks, the cost stays the upkeep per block, and range is
paid for. This is one of the pieces a hunter needs (see the prey before being on it), with
speed (an outcome already) and a body worth eating (#27) as the others.

## Hypothesis

1. **Eyes pay now.** In the crowd state (the flat world, fruit 44-77% of the intake in e022)
   the sensor share of the population rises above e022's (1-4% in the flat runs at the end,
   sensor mean 0.08-0.29 per body) and sensor lineages last: at least one lineage with a mean
   of one sensor or more lives 100,000 steps in at least two seeds of four.
2. **The knockout says the eye is used.** `sense_used` (decisions a body with sensors takes
   differently from the same body seeing one cell) exceeds e022's 0.06-0.11 in the runs where
   sensor lineages last.
3. **The start survives.** In the survey of the start (seeds 1-8 of the three worlds, 10,000
   steps) fewer than e022's 5 of 24 die, and the bottlenecks are shallower than 7-431: a body
   that sees a pile eight cells away walks to it.
4. **The world stands and keeps its crowd.** Population cv under 0.10 over the second half,
   matter conserved to 0.05%, fruit still the harvest (over a third of the intake), contacts
   at or above e022's 0.22-0.76.
5. **The tooth stays unpaid.** No biter lineage lasts (biters' share under 0.01 at the end): an
   eye alone does not make a hunter; that needs #27 (flesh worth eating), and this experiment
   removes one of the reasons a hunter could not exist.

## Method

Code: e022 (`experiments/e022_spill`) with one law changed; `eyes 0` is e022 byte for byte
(checked on flat seed 9 over 10,000 steps: every CSV identical but `steps_per_sec`).

- `Body::range`: 1 + sensor blocks, capped at `eyes` (8). The inputs in each of the four
  directions sum the food and the crowd in the row of cells j cells away, for j from 1 to the
  range, each at 1/j (the light reaching the eye falls with the distance). A body with no
  sensor sees one cell (e022's saw two). `look` (the row k cells ahead, as wide as the body)
  is the same closure at any k.
- The knockout (e009): `sense_used` compares each decision of a body with sensors to the
  same body seeing one cell.
- Argument 14 `eyes` (8 by default; 0 is e022's law), in the results prefix as `_eyes8`.
- Compute: a body with s sensors looks at 4(1 + s) rows a step instead of 8; the cost grows
  with the sensors selected, and is capped at 36 rows. A sensorless body is cheaper than in
  e022.

The control is e022's runs (`experiments/e022_spill/results`, flat seeds 1-4): the same code
at `eyes 0`, so nothing is rerun.

Cost of the runs: the pilot (flat seed 9, 100,000 steps, 6 threads, minutes); the start survey
(24 runs of 10,000 steps, one thread each, six at a time, about 5 minutes); the batch: flat
seeds 1-4 at 1,000,000 steps, one thread each, 4 cores for about an hour. The mountain worlds
(high, half) are run only if the flat result calls for it.

Run (from the repo root):

    bash experiments/e023_eyes/run.sh 1 2 3 4

Arguments: `<steps> <seed> <size> <widths> <cell_energy> <matter> <relief> <flow> <rain> <breath> <shade> <spill> <mutation> <eyes>`;
the batch uses `1000000 <seed> 128 0 0.02 8 64 0.1 flat` (the defaults: breath 1, shade 2,
spill 1, mutation 2/512, eyes 8).

## Result

Four runs (flat seeds 1-4, 1,000,000 steps, 2 threads each, 4 at once: 107 minutes, 145-250
steps per second) against e022's flat seeds 1-4. Report: `report.html`.

| | seed 1 | seed 2 | seed 3 | seed 4 | e022 flat 1-4 |
|---|---|---|---|---|---|
| Bodies with a sensor (median 2nd half / peak) | 2.8% / 23% | 16% / 84% | 0.7% / 23% | 74% / 85% | 1-7% / 7-25% |
| Sensor blocks per body (2nd half) | 0.21 | 1.27 (last quarter 4.3) | 0.04 | 2.97 | 0.08-0.41 |
| Decisions the eye changed (knockout) | 16% | 17% | 21% | 10% | 11-14% |
| Longest lineage with a sensor per body | 14,000 steps | 261,000 | 39,000 | 695,000 | 10,000-23,000 |
| Population (cv) | 1,340 (0.11) | 1,116 (0.12) | 2,193 (0.05) | 1,051 (0.04) | 912-1,610 (0.04-0.11) |
| Food eaten per step | 96 | 102 | 114 | 109 | 97-134 |
| Fruit, share of the intake | 53% | 54% (last quarter 77%) | 21% | 75% | 44-76% |
| Dead matter, share | 14% | 14% | 5% | 18% | 10-26% |
| Contacts per body per step | 0.39 | 0.32 | 0.11 | 0.69 | 0.22-0.73 |
| Mass | 11.4 | 16.7 | 7.6 | 21.8 | 8.9-23.7 |
| Lineages alive | 2 | 2 | 1 | 1 | 1-3 |
| Biters (median / peak) | 0 / 0.007 | 0 / 0.009 | 0 / 0.011 | 0 / 0.003 | 0-0.006 / 0.003-0.026 |
| Matter, end over start | 0.9999 | 0.9999 | 0.9999 | 0.9997 | 0.9997-1.0011 |

The winners. Seed 4: one lineage the whole run, a frame of 22 cells open at the back (7x7 world
cells), hard 0, muscle 4, sensor 3.1, gut 14 at the end, a sensor per body for 695,000 steps,
forward 66% of its decisions, in the crowd state (fruit 75%, contacts 0.69). Seed 2: one
lineage the whole run, a body of 11 cells with 0.3 sensor until step 750,000, then a frame of 22
cells with 7 sensors and 2 muscle, and the run enters the crowd state with it (fruit 48% to
77%, mass 13 to 21). Seed 1: e022's blind bar (10 gut cells, 2.5x6.5) in the mixed state. Seed
3: fell out of the crowd state at step 500,000 to a lawn (2,200 bodies of 7.6 cells in a single
row, fruit 21%, contacts 0.11), a state none of e022's flat runs entered. e022's frames had
1-4 hard cells at the corners and 0.1-0.3 muscle; the frame that sees has 0.2 hard, 2-4 muscle
and 3-7 sensors. The knockout is flat at 10-21% in every run: the eye is not read more often
than e022's second cell, it is read farther.

The start survey (`results/start_survey.csv`, 24 runs of 10,000 steps, seeds 1-8 of the three
worlds): 2 deaths (flat 6 at step 4,804, half 8 at 5,346) against e022's 5 (high 4 and 8, half
6 and 7, flat 8); bottlenecks of 33-418 bodies in the survivors against 7-431; every world
booms to 4,000-4,700 bodies by step 100 and crashes by step 1,000 as before.

Pilot (flat seed 9, 100,000 steps): sensor share 25% at step 10,000, under 1% from 30,000;
the world stands (1,300-1,500 bodies).

## Conclusion

1. Eyes pay now: yes, in two seeds of four. The winners of seeds 2 and 4 carry a sensor per
   body for 261,000 and 695,000 steps (e022's longest: 23,000), 3-7 blocks per body; seeds 1
   and 3 stay at 0.7-3%.
2. The knockout says the eye is used: partly. 16-21% in seeds 1-3 against e022's 11-14%, 10% in
   seed 4 where nearly every body has three sensors; the share does not rise with the range.
3. The start survives: partly. 2 deaths in 24 against 5, different seeds; the bottlenecks are
   the same (33-418 against 7-431). The eye decides who finds the rings after the crash, not
   the crash.
4. The world stands and keeps its crowd: three of four. No death, matter conserved, cv
   0.04-0.12 (two runs just over 0.10); seed 3 fell to the lawn.
5. The tooth stays unpaid: yes. Biters 0 on median, peaks 0.3-1.1%, no biter lineage.

What it changes: the eye is kept as a law about a material (a sensor block sees one more cell,
seen at 1/distance, `eyes` 8). It pays where the food lies in piles a few cells apart - the crowd
state - and nowhere else, the other half of e009's finding, and it is the first block since e011
whose worth depends on the state of the world. The crowd's body is now the frame that sees: no
armor, four muscle, three eyes; it traded e022's corner armor for sight and legs. Open: whether
the crowd state is the eye's doing or its cause (seed 2 gained both at 750,000, seed 3 lost both
at 500,000), and the start's lottery, which is the boom's, not the eye's. The mountain worlds
were not run: the flat result was clear enough. Next is #27, what flesh is worth: a body that
can see prey exists now, a body worth eating does not.
