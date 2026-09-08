# e038 Does the income bind size?

Date: 2026-09-09

## Purpose

e037 (#39) moved the cost side of a body (the upkeep of the cells as (size / 16)^k) and the
steady state did not move: after 60,000 steps the world is the control's on every seed (median
15-16 cells, 90th percentile 21-25). The reading of e037's numbers was that the income binds: a
gut block earns `intake_per_gut` 0.0017-0.0037 a step, a fifth of its bite of 0.02 or less, and
less the wider the body stands, because intake is the regrowth under the footprint and regrowth
per cell is the sun's, 0.01 a cell a step. That was an interpretation from one measure. This
experiment tests it (issue #40) before the tree law (#41), which only makes sense if food is the
lever.

## Hypothesis

1. **The income is the lever.** With twice the sun per cell, `intake_per_gut` rises (toward
   0.004-0.007 a step) and the size distribution after the start's transient (step 40,000 on)
   moves up: median above 16, 90th percentile above 25. Most clearly at `k` 0.6, where the
   marginal cell is cheap. At four times the sun, further.
2. **Or the constraint is elsewhere.** If `intake_per_gut` rises and size does not, or if the
   extra sun goes into more bodies of the same size (e027's reading at four times the space:
   1.4x as many bodies, twice as big), then what keeps a body at 16 cells is not the food: the
   weight law's move cost, the winter's fat, or the side grid. Then the next size law should not
   be about food.

## Method

Code: e037 (`experiments/e037_upkeep`) as `e038_income` with one argument more, off by default
(`sun` 1 is e037 byte for byte; checked on seed 9 for 10,000 steps: `log.csv`, `pop.csv`,
`agents.csv` and `lineages.csv` identical by md5):

- **The sun's rate** (argument 33, `sun`). Every cell's regrowth is `RES_GROWTH` 0.01 times
  `sun` a step, before the season, the canopy and the water act on it as before. The rain's cap
  (the most the air rains back on a cell a step, the sun's worth by e020's law) scales with it,
  so that a world that burns twice as much can rain it back and the matter does not pile up in
  the air. The matter per cell stays 8: the soil holds about 6 per cell in e037's runs against a
  sun of 0.01, so it does not bind at 2 or 4 (the issue's "soil to match" is not needed; the log's
  `soil` and `soil_cells` will say).

**Runs.** Seed 9, 100,000 steps (five winters), one thread each, four at once on the Mac (4 of 12
cores), in e035's season world (`winter high` 2, water 0.1, leach 0.01, depth 0.01, mix 0.2,
flow 0, rain flat, store 5, grow, no ground store): `sun` 2 and 4, each at `k` 1 and `k` 0.6.
The controls at `sun` 1 are e037's pilot runs (seed 9, `k` 1 and 0.6, the same code). The `sun` 4
runs are the dose: a graded response says the lever is the food; they also compare with e027
(four times the sun by four times the space). Wall time: e037's 100,000 took 17-25 minutes; a
world with more bodies is slower per step, so 40-50 minutes for `sun` 2 and 70-100 for `sun` 4
were expected. A batch on seeds 1-3 at 300,000 steps only if size moves in the pilot.

Run from the repo root: `bash experiments/e038_income/run.sh <k> <sun> <threads> <steps> <seeds>`.

**Measures.** `intake_per_gut` and the size distribution (`size_p10`, `size_p50`, `size_p90`,
`size_max`) after step 40,000 (the start's transient is in every run, e037), the population and
its winter floors (`pop.csv`), what the world eats a step, the biters' share
(`biters_any_share`), the soil (`soil`, `soil_cells`: does it bind), and the winners' shapes
(`lineages.csv`, `bodies.jsonl`).

## Result

Seed 9, 100,000 steps. Means over the second half (steps 50,000-100,000) unless said otherwise; the
floors are the five winter troughs in order; "at the end" is every body alive at step 100,000. The
`sun` 1 rows are e037's pilots (the same code). Wall time: 16-18 minutes for the `sun` 2 runs,
24-26 for `sun` 4 (more bodies, 1.5x slower per step).

| run | winter floors | valley share | summer peaks | a gut block earns: summer / winter | size p10 / p50 / p90 | largest | at the end: p10 / p50 / p90 / max | eaten per step | soil per cell | biters | lineages at the end |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sun 1, k 1 (today) | 626, 696, 724, 743, 775 | 71-76% | 3,089-6,398 | 0.0042 / 0.0016 | 3 / 9 / 22 | 115 | 3 / 10 / 23 / 111 | 116 | 6.2 | 2% | 2 |
| sun 2, k 1 | 1,037, 1,347, 1,195, 1,182, 1,169 | 78-84% | 3,861-8,844 | 0.0046 / 0.0030 | 2 / 11 / 16 | 66 | 2 / 10 / 16 / 57 | 175 | 4.0 | 0% | 14 |
| sun 4, k 1 | 1,438, 1,865, 1,838, 1,393, 1,447 | 70-83% | 5,390-11,822 | 0.0037 / 0.0029 | 5 / 15 / 19 | 75 | 4 / 14 / 21 / 65 | 209 | 2.2 | 3% | 20 |
| sun 1, k 0.6 | 487, 501, 524, 651, 566 | 72-82% | 2,854-3,187 | 0.0033 / 0.0016 | 6 / 22 / 53 | 86 | 6 / 22 / 57 / 81 | 98 | 5.5 | 33% | 6 |
| sun 2, k 0.6 | 846, 862, 838, 919, 952 | 78-86% | 3,495-5,048 | 0.0031 / 0.0017 | 5 / 23 / 37 | 94 | 4 / 20 / 36 / 91 | 153 | 3.4 | 29% | 13 |
| sun 4, k 0.6 | 1,289, 1,435, 1,585, 1,440, 1,318 | 79-83% | 4,679-7,172 | 0.0033 / 0.0029 | 6 / 18 / 30 | 115 | 8 / 20 / 25 / 169 | 220 | 1.9 | 6% | 25 |

Means after step 40,000 (the start's transient excluded):

| run | bodies | births per step | density | footprint (cells under a body) | size mean |
|---|---|---|---|---|---|
| sun 1, k 1 | 3,591 | 12.2 | 1.49 | 2.98 | 11.0 |
| sun 2, k 1 | 4,587 | 15.4 | 1.59 | 2.15 | 10.7 |
| sun 4, k 1 | 5,307 | 17.9 | 1.71 | 2.21 | 13.1 |
| sun 1, k 0.6 | 2,248 | 3.6 | 1.05 | 4.64 | 27.5 |
| sun 2, k 0.6 | 3,422 | 4.6 | 1.41 | 4.16 | 22.9 |
| sun 4, k 0.6 | 4,430 | 8.3 | 1.71 | 3.35 | 18.9 |

- **A gut block earns the same under every sun.** In summer 0.0037-0.0046 a step at `k` 1 and
  0.0031-0.0033 at `k` 0.6, whatever the sun. The winter income doubles once (0.0016 to 0.0030,
  from `sun` 1 to 2) and does not move again at 4.
- **The sun becomes bodies.** The winter floors go 626-775, 1,037-1,347, 1,393-1,865 at `k` 1;
  bodies after step 40,000 1.3x and 1.5x the control's, births 12 to 18 a step (3.6 to 8.3 at
  `k` 0.6). What the world eats rises 1.5x and 1.8x (116, 175, 209), less than the sun (2x, 4x):
  the rest stands as lawn and trees (200-330 trees today, 500-1,400 under four suns) or rots.
- **Size does not follow the food.** At `k` 1 the median is 9, 11, 15 cells by sun, the 90th
  percentile 22, 16, 19; the lineage with the most body-steps under four suns is a 6-cell gut bar
  (lineage 223, 171,000 body-samples, peak 8,671 bodies). At `k` 0.6 the median holds at 18-23
  while the 90th percentile falls 53, 37, 30 and the biters 33%, 29%, 6%: the armored hunters
  (37 cells at `sun` 1, 29 at `sun` 2, 33 at `sun` 4) give way to dense movers of 12-19 cells
  under four suns.
- **Denser, on less lawn.** Density rises 1.49 to 1.71 and the footprint falls 2.98 to 2.21 cells
  at `k` 1: e025's dense block wins where the food is thick.
- **The soil falls but never binds.** 6.2 to 2.2 per cell as the matter moves into the standing
  plant and the bodies; at `sun` 4 the soil is still 55 times the sun's rate and `soil_cells` is
  0.996-0.999. The issue's "soil to match" was not needed.
- **The reading of e037 was half right.** A gut block does earn about the regrowth under its
  footprint (footprint 2.2 cells x 0.02 a step = 0.044 a body under two suns, against an intake
  of 0.046 a body: 10 gut blocks x 0.0046), but the regrowth under a footprint is the sun's
  divided by the bodies sharing the lawn, and the bodies multiply until a block earns what it
  earns today. The income per block is pinned by the crowd, not by the sun.
- One seed, 100,000 steps: the k 0.6 rows are the start's transient (e037: seeds 1-3 lose the
  hunter world by 60,000). The `k` 1 rows are read after step 40,000.

## Conclusion

**No: more food per cell does not lift a gut block's income, and size does not follow the food.**
Hypothesis 1 fails (the summer income is flat across a fourfold sun; the median body is 9-15 cells
at `k` 1 under every sun); hypothesis 2 holds, in e027's form: the world converts sun into bodies
at the size it has, 1.3-1.5x as many and denser, and the hunter world of `k` 0.6 thins rather
than grows. `sun` stays an argument, 1 by default; no batch was run (the pilot did not move size).

**What this changes for the project.** The income per gut block is pinned by the crowd
(0.003-0.005 a step in summer), so a size law that gives the world *more* food will be eaten by
more small bodies. What escapes the pinning is an income the crowd cannot dilute: a food only a
big body reaches. That is #41's premise (the tree as a column, a bite up to a reach the body has by
its shape), and this result is the reason for it, not against it. The other candidate, the move
cost of a big body (mass x distance, e025), stays untested. Then #37 (a body that needs water) and
#38 (the rain on the ridge).
