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

(to come)

## Conclusion

(to come)
