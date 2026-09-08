# e037 The cost of a body

Date: 2026-09-08

## Purpose

Since e015 a body pays `UPKEEP` 0.002 per living cell per step plus `UPKEEP_BODY` 0.032 per body,
and a gut block takes at most `BITE` 0.02 a step from the cell under it. e029 found that size is
the sun's (the winner is 11-16 cells in every world tried), e030 that size does not pay and density
does, and e036 sharpened the arithmetic from the other side: a body's income is a rate ceiling
(gut blocks x 0.02, in practice far less over a grazed lawn) while its cost grows with every cell.
The premise this world lacks (issue #39) is the real world's: metabolism does not scale one for
one with mass (about mass^0.75), and large animals exist because the cost per unit of mass falls
with size. This experiment gives the upkeep that slope and asks whether size can pay.

The world already has a sub-linear cost of a kind: the per-body 0.032 is paid once whatever the
size, so a body of 8 cells pays 6.0 per 1,000 per cell and one of 64 pays 2.5. The law here
steepens that slope on top; the table under Method says by how much.

## Hypothesis

1. **Size spreads.** Under a sub-linear upkeep the median size rises above e036's 11-16 cells and
   the spread (`size_p10` to `size_p90`) widens, more so the smaller `k`, because a body that
   covers more cells has more gut blocks over more lawn and now pays less per cell for them.
2. **Fewer, bigger bodies.** The population is bounded by regrowth over the per-body cost, so
   bigger bodies mean fewer of them: the summer peaks and the winter floors fall with `k`, and
   what the world eats a step stays near the control's 116 (the sun is the same).
3. **The crowd and the tooth survive.** The season world's states (a valley refuge, migration as
   a wave, a hunter state in some runs) do not depend on the size of a body, so the floors stay
   in the valley and the biters' share stays in its range (0-30% across e035/e036's pilots).
4. **Or size is not the upkeep's.** If the size distribution does not move even at `k` 0.6, where
   a body of 64 cells pays 34% less than today, then what keeps bodies at 11-16 cells is
   somewhere else: the move cost (mass x distance, e025), the sun per cell, or the development
   (the side grid, e029).

## Method

Code: e036 (`experiments/e036_ground`) as `e037_upkeep` with one law about the world, off by
default (`k` 1 is e036 byte for byte; checked on seed 9 for 10,000 steps: `log.csv`, `pop.csv`,
`agents.csv` and `lineages.csv` identical by md5):

- **The cost of a body** (argument 32, `k`). The upkeep a body of `size` living cells pays a
  step is `UPKEEP x S0 x (size / S0)^k + UPKEEP_BODY`, with S0 = 16 fixed (the size the winners
  have held since e016). A body of 16 cells pays what it pays today under every `k`; only the
  slope changes. Nothing else moves: the bite, the move cost, the weight law and the per-body cost.

What a body pays a step, by size and `k` (the per-body 0.032 included):

| cells | k 1 (today) | k 0.85 | k 0.75 | k 0.6 |
|---|---|---|---|---|
| 8 | 0.048 | 0.050 | 0.051 | 0.053 |
| 16 | 0.064 | 0.064 | 0.064 | 0.064 |
| 32 | 0.096 | 0.090 | 0.086 | 0.081 |
| 64 | 0.160 | 0.136 | 0.123 | 0.106 |

The cost is one `powf` per living body per step: nothing measurable.

**Runs.** Seed 9, 100,000 steps (five winters), one thread each, four at once on the Mac (4 of
12 cores), in e035's season world (`winter high` 2, water 0.1, leach 0.01, depth 0.01, mix 0.2,
flow 0, rain flat, store 5, grow, no ground store): `k` 1 (the control), 0.85, 0.75 and 0.6.
Wall time: 19 minutes for the four. A batch on seeds 1-3 only if a `k` moves the size distribution:
it did, so `k` 0.6 ran on seeds 1-3 for 300,000 steps (two threads each, three at once on the Mac)
and `k` 0.75 on seeds 1-3 for 200,000 steps (two threads each, on the Ubuntu box), against e035's
batch (the same code at `k` 1, seeds 1-3, 300,000 steps).

Run from the repo root: `bash experiments/e037_upkeep/run.sh <k> <threads> <steps> <seeds>`.

**Measures.** The size distribution already in the log (`size_p10`, `size_p50`, `size_p90`,
`size_max`, `mass_p50`, one point per 10,000 steps), the winners' shapes (`lineages.csv`,
`bodies.jsonl`), the population and its winter floors and where they stand (`pop.csv`), what the
world eats a step (`plant_intake` + `meat_intake`), and the biters' share (`biters_any_share`).

## Result

### The pilot (seed 9, 100,000 steps)

Means over the second half (steps 50,000-100,000) unless said otherwise; the floors are the
five winter troughs in order; "at the end" is every body alive at step 100,000.

| k | winter floors | valley share at the floors | summer peaks | size p10 / p50 / p90 / max | at the end: p10 / p50 / p90 / max | grown bodies (age > 200): median / p90 | median mass | density | eaten per step | of it meat | births per step | biters | lineages at the end |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 (today) | 626, 696, 724, 743, 775 | 71-76% | 3,089-6,398 | 3 / 9 / 22 / 115 | 3 / 10 / 23 / 111 | 8 / 20 | 10.3 | 1.43 | 116 | 46 | 11.2 | 2% | 3 |
| 0.85 | 561, 685, 492, 400, 599 | 73-82% | 2,838-4,098 | 5 / 18 / 41 / 88 | 4 / 12 / 28 / 81 | 11 / 28 | 26.3 | 1.48 | 108 | 40 | 4.5 | 6% | 14 |
| 0.75 | 448, 537, 556, 696, 745 | 74-82% | 2,843-4,124 | 4 / 13 / 22 / 95 | 4 / 15 / 25 / 111 | 14 / 25 | 16.0 | 1.42 | 118 | 51 | 7.2 | 1% | 3 |
| 0.6 | 487, 501, 524, 651, 566 | 72-82% | 2,854-3,187 | 6 / 22 / 53 / 86 | 6 / 22 / 57 / 81 | 24 / 56 | 27.1 | 1.05 | 98 | 31 | 3.5 | 33% | 6 |

- **Size pays at k 0.6.** The median body is 22 cells against 9, the 90th percentile 53 against
  22, and among grown bodies (older than 200 steps) the median is 24 against 8. At the end a fifth
  of the bodies have 40 cells or more (3% today). k 0.75 barely moves the median (13); k 0.85
  moves it in waves (10-23) as one large lineage rises and falls.
- **The largest body is 81-121 cells in every run**: the ceiling was never the law. What changes
  is who lives at it.
- **Big and light.** Median mass rises less than median size (27 against 10, size 22 against 9)
  because the k 0.6 bodies are made of light cells: density 1.05 against 1.43. The cheap cells go
  into armor and a mouth, not into weight.
- **Fewer bodies, less eaten.** The summer peaks halve (2,854-3,187 against 3,089-6,398), the
  floors hold (487-651 against 626-775) and stay in the valley (72-82%). The world eats 16% less
  (98 against 116 a step) because births fall from 11.2 to 3.5 a step and the world eats its dead
  (e024): the meat cycle is 31 a step against 46.
- **A hunter's world with two kinds.** At k 0.6 a third of the bodies bite from step 30,000 on
  (2% today). The lineages that held the most body-steps: a 16-cell all-gut grazer (lineage 128,
  the whole run, no tooth) and three armored hunters in succession, each larger than the last:
  37 cells (10 hard, 8 muscle, 18 gut, bite 1.6, steps 23,000-61,000), 36 cells (14 hard, bite 2.3,
  55,000-85,000), 44 cells (19 hard, 10 muscle, 14 gut, bite 2.6, 80,000-100,000). All at density
  0.78-0.87. The lineages at k 0.6 are varied inside (a 49-cell all-gut body and a full 8x8 of
  armor, muscle and gut in the same lineage at once), where today's lineages are one body each.
- **Today's winners are unchanged at k 1**: the 10-cell gut bar (lineage 1, the whole run) and
  e025's dense mover (13 cells, density 2.0).

### The batch (seeds 1-3)

`k` 0.6 for 300,000 steps and `k` 0.75 for 200,000, against e035's batch at `k` 1 (300,000).
Means after step 100,000; the floors are the winter troughs; "at the end" is the last dump.

| run | winter floors | valley share | summer peaks | size p10 / p50 / p90 | largest | at the end: p10 / p50 / p90 / max | median mass | eaten per step | biters | lineages at the end |
|---|---|---|---|---|---|---|---|---|---|---|
| k 1, seed 1 | 624-921 | 69-79% | 2,923-5,523 | 4 / 15 / 18 | 78 | 3 / 14 / 16 / 84 | 26.2 | 133 | 1% | 2 |
| k 1, seed 2 | 691-874 | 74-81% | 3,263-6,159 | 4 / 13 / 28 | 191 | 4 / 12 / 27 / 256 | 18.2 | 106 | 2% | 2 |
| k 1, seed 3 | 328-736 | 76-86% | 2,610-3,430 | 8 / 16 / 16 | 69 | 8 / 16 / 16 / 64 | 32.0 | 129 | 15% | 14 |
| k 0.75, seed 1 | 705-856 | 73-79% | 2,954-4,402 | 5 / 16 / 18 | 102 | 4 / 16 / 21 / 100 | 30.5 | 125 | 1% | 2 |
| k 0.75, seed 2 | 484-764 | 78-88% | 2,926-6,190 | 4 / 8 / 18 | 119 | 3 / 8 / 19 / 143 | 13.2 | 117 | 0% | 6 |
| k 0.75, seed 3 | 523-875 | 74-85% | 2,806-3,968 | 6 / 16 / 22 | 75 | 3 / 15 / 21 / 79 | 29.3 | 125 | 3% | 11 |
| k 0.6, seed 1 | 684-882 | 75-82% | 2,940-4,137 | 5 / 16 / 21 | 83 | 4 / 16 / 23 / 95 | 28.9 | 125 | 1% | 9 |
| k 0.6, seed 2 | 496-817 | 75-83% | 2,972-4,747 | 5 / 15 / 25 | 86 | 5 / 16 / 24 / 64 | 22.3 | 119 | 1% | 5 |
| k 0.6, seed 3 | 527-722 | 75-83% | 2,685-3,999 | 14 / 16 / 24 | 92 | 16 / 16 / 16 / 66 | 32.0 | 130 | 0% | 14 |

The median size every 20,000 steps (log.csv, `size_p50`), `k` 0.6:

| seed | 20k | 40k | 60k | 80k | 100k | ... | 300k | p90 in the first 40k | p90 after 100k | biters after 100k |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 23 | 13 | 13 | 15 | 16 | 15-16 | 16 | 58, 25 | 18-25 | 0-1% |
| 2 | 34 | 16 | 17 | 15 | 15 | 14-18 | 16 | 64, 46 | 21-33 | 0-5% |
| 3 | 13 | 16 | 16 | 16 | 16 | 16 | 16 | 25, 19 | 16-25 | 0% |

- **The world returns to 16 cells.** After step 100,000 the median is 15-16 at `k` 0.6 and 8-16 at
  `k` 0.75, the 90th percentile 21-25 and 18-22, against the control's 13-16 and 16-28. Seed 3 at
  `k` 0.6 is 16 at every percentile with density 2.0: e025's dense block. The floors, the peaks,
  the valley's share and what the world eats are the control's.
- **The pilot's world is the start's transient.** Every seed at `k` 0.6 opens like seed 9: a
  median of 21-34 cells and a 90th percentile of 46-64 in its first 40,000 steps, then 16 by
  60,000. Seed 9 held it through 100,000 steps; whether a seed can keep it is open.
- **The tooth is at 0-1%** at `k` 0.6 after 100,000, where the control holds a hunter state in
  seed 3 (15-21% from step 140,000 on, with 16-cell bodies).
- **Where the ceiling is.** A gut block earns `intake_per_gut` 0.0024-0.0036 a step in every
  run, an eighth of its bite, and less the wider the body stands: 0.0023 at a footprint of 4.6
  cells in the pilot's `k` 0.6 world, 0.0036 at 2.4 in the control's seed 1. A body strips the
  lawn under itself, so more gut over the same lawn shares the same regrowth. At `k` 0.6 the
  32nd cell costs 0.0009 a step (0.002 today) and still does not pay.
- **Compute.** The cost of a step is per cell: seeds 1 and 3 took 72 minutes for 300,000 steps at
  two threads each (the pilot: 17 minutes per 100,000 at one), 40% slower per step while the bodies
  were large. Seed 2 finished at 00:53 the next day; the Mac may have slept in between, so its wall
  time is not known.

## Conclusion

**Not kept.** `k` stays an argument, 1 by default; the season world is e035's. An upkeep that
scales as (size / 16)^k does not make size pay: on three seeds at `k` 0.6 the world is the
control's after 60,000 steps (median 15-16 cells, 90th percentile 21-25, 0-1% biters), and `k`
0.75 is the control too. Hypotheses 1-3 fail at 300,000 steps and hypothesis 4 holds: size is not
the upkeep's.

**What the pilot showed is real but not selected.** On seed 9 at `k` 0.6 a 16-cell grazer and
armored hunters of 37-44 cells (density 0.8, a bite of 1.6-2.6) held 100,000 steps together, the
first size axis in the arms race. Seeds 1-3 pass through the same world in their first 40,000
steps and lose it. It is the start's world: an ungrazed lawn on which a wide body earns over
every cell it covers. Once the crowd has grazed the world down to 0.003 a step per gut block, a
body cannot earn more by being wider, at any price per cell.

**What this changes for the project.** The ceiling on size is the income side, not the bill:
intake is regrowth under the footprint, and regrowth per cell is the sun's and the soil's. The
real world's large animals eat what small ones cannot (tall trees, tough grass, large prey) or go
where food is. The premise still missing is a food a big body reaches and a small one does not;
the canopy's trees (e021, eaten today by any gut) are the candidate already in the world. Open:
whether seed 9's hunter world outlasts 100,000 steps (seeds 1-3 lost theirs by 60,000), and what
the weight law (mass x distance) costs a big body.
