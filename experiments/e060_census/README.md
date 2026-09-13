# e060 A census of ways of living

Date: 2026-09-13

Analysis only: no new runs. Closes #71.

## Purpose

On 2026-09-13 the measure changed from shape kinds to ways of living (vision.md). A viewer is bored
when every body lives the same way, not when there are too few shapes. Before any new law, three
things are needed: a definition of a way of living from what bodies do, a count of them in the runs
we already have, and a test of the working hypothesis in vision.md against those runs. A first
count on one seed each suggested that e059's diversity gain was shape bins within one way of life;
this experiment checks that on every seed and corrects e059.

## Hypothesis

Written before the census, from #71 (the competitive exclusion frame): the number of ways of living
that coexist is at most the number of independent limiting factors, each with a trade-off.

1. **The laws that added such a factor hold more ways of living than their controls**: e012 (two
   kinds of place), e025 (flesh with weight), e026 (season, cloud), e032 (winter by height).
2. **The laws that did not hold no more**: the ones that moved the amount, timing or place of the one
   resource (e038, e041, e046, e051, e054, e056, e057, e059), the ones whose new axis overlapped the
   old resource in place (e028, e040), and the one with no trade-off (e039).

If this does not hold, the frame is dropped.

## Method

**A way of living** is three things a body does, read from `agents.csv`. Only bodies aged 300 or
more are counted (a newborn has no diet yet).

| part | column | classes |
|---|---|---|
| diet | `meat / (plant + meat)` over the life | plant below 1/3, flesh above 2/3, mixed between |
| tooth | `bite_any` (before e024: `bite`, the front only) | a hard tip with a force of 2 or more behind it (breaks a soft face of density 1) |
| movement | `travel`, world cells from the birthplace (e048 on) | roams at 8 or more, stays below |

So a way of living is one of 12 (6 before e048, which have no `travel`). A world's **ways of
living** are those holding 5% or more of its grown bodies; the tail is counted by q1 = exp(Shannon)
over all 12. Each number is the mean over the census steps of the second half of a run (the
`agents.csv` dump every 100,000 steps; a 100,000-step run has one).

Gaps in the data, noted and not filled here:

- `meat` is the flesh of broken cells plus, from e017, the dead a body ate. No run splits a kill from
  scavenging per body. Before e017 (e010-e012) `meat` is kills only.
- `deaths.csv` counts deaths by cause, age and size, not by way of living, so what kills a way of
  living cannot be read.
- Runs before e048 have no `travel`; for them a way of living is diet and tooth only.

**The test.** Each law against its control at the same code, on the seeds both have, at the census
steps both have:

| class | law | control | seeds |
|---|---|---|---|
| axis | e012 grass and trees (8,1) | e011 trees alone (width 1); e010 grass alone (width 8) | 1-4 |
| axis | e025 weight 1 | e025 weight 0 | 1-4 |
| axis | e026 season 0.5; cloud 1 | e025 weight 1 | 1-4 |
| axis | e032 winter high 2 | e032 flat 0.75 | 1-3 |
| overlap | e028 gut curve (`digest` 2) | e026 season 0.5 | 1-4 |
| overlap | e040 thirst 0.001, 0.002, 0.005 | e041's control (e040 byte for byte) | 9 |
| no trade-off | e039 reach 1 | e039 same reach for every body | 1-3, 9 |
| amount | e038 sun 2, 4 (at k 1 and 0.6) | e037 at sun 1 | 9 |
| amount | e041 stock 1, 4 | e041 control | 9 |
| amount | e046 plant yield 0.5 | e045 connect | 9-14 |
| amount | e051 stock 1, 4 (with and without the brain) | e048 motor; e050 brain | 9-12 |
| amount | e054 grain 64 | e054 control | 9-12 |
| amount | e056 sun 2; sun 4 | e055 clock 0.5 | 9-14; 9-11 |
| amount | e057 foul 0.03 | e057 control | 9-14 |
| amount | e059 islands | e059 thin uniform | 9-14 |

A law holds **more** ways of living on a seed when its count is higher by 1 or more, **fewer** when
lower by 1 or more, and **the same** otherwise. A pair's verdict is what most of its seeds say
(`split` when no answer has a majority). The frame holds for an axis law that holds more, and for
any other law that does not.

Also censused for their own sake: e045 (both laws), e055 (clock and flat pace), e058 (sun 1, 0.2,
0.1).

Run from the repo root: `uv run python experiments/e060_census/census.py` (about 15 s on one core),
then `census.py sweep` (the frame test under other thresholds) and `report.py`. The census writes
`results/runs.csv` (one row per run and seed), `results/pairs.csv`, `results/ways.csv` (each way of
living of each run: share, size at birth, speed, age, diet, lineages, where it lives) and
`results/sweep.csv`. `census.py` is the successor to e058's `diversity.py`: later experiments import
`way`, `census`, `census_by_lineage`, `count`, `count_by_place`, `hill`, `rarefied`, `kinds` and
`kills_share` from it.

**Added after the first pass**, when the per-body count turned out to follow the hunter worlds:
the state of each world, read from its log apart from the bodies (the flesh of kills over all the
world ate, second half of the run; a hunter world at 25% or more, between e045's grazer worlds at
16-20% and hunter worlds at 30-41%); a count per lineage (every grown body counted under its
lineage's most common way); a count by place (a way counts if it holds 5% of a place that holds 5%
of the bodies); and the sweep.

## Result

156 runs (46 settings, 1-12 seeds each) in 14 seconds on one core. Report: `report.html`.

**1. The per-body count follows the kills.** Worlds hold 1.0-10.0 ways of living per body. Over the
144 runs whose log records kills (e024 on), the count follows the kills' share of what the world
eats (rank correlation 0.61): 2.4 ways where kills are under 10% of the intake, 5.2 at 30% or more;
3.0 in grazer worlds (89 runs) and 5.1 in hunter worlds (55 runs). The kills' share runs evenly
from 0 to 40% across runs, not in two humps: e045's two states are the two ends of a range.

**2. Per lineage every world holds 1-3.** With each grown body counted under its lineage's most
common way, every run holds 1.0-3.0 ways (grazer worlds 1.6, hunter worlds 2.0; rank correlation
with the kills 0.37). The per-body count is 1.95 higher on average. Three things make the gap, seen
in e055 seed 9 (read through e058's sun-1 run on seed 9, the same run with the birth shape), the
world with the most ways per body (10):

- Lineage 593 holds 68% of the grown bodies and the largest share of every one of the 10 ways. Its
  members' flesh share runs 0.22-0.65 between quartiles: one diet, cut three ways by the thresholds.
- Its 307 toothless members were born with 14.9 muscle blocks and hold 3.9 (no worn blocks); its
  toothed members were born with 17.4 and hold 11.3. The muscle behind the hard tip was broken
  off: a tooth read from the current body is partly a record of damage.
- Over all runs, roamers are 1.74 times older than stayers of the same diet and tooth (1.02-3.41):
  the distance from the birthplace grows with age.

A way of living with a tooth is nearly always one lineage (its leading lineage's median share 96%;
77 of 117 at 80% or more); one without a tooth, 52% and 11 lineages.

The per-lineage count is a lower bound. Lineages are single linkage on gene lists and can join
different builds: e032 winter high seed 3 holds a 70-block hunter (speed 0.43) and a 17-block gut
(speed 0) in lineage 1, which holds 94% of the grown bodies; e045 connect seed 12 is one lineage.

**3. The frame test.**

| law vs control | class | seeds | per body | per lineage | seeds into / out of a hunter world |
|---|---|---|---|---|---|
| e012 grass and trees vs trees alone; vs grass alone | axis | 1-4 | fewer; same | same; same | no kill log |
| e025 weight 1 vs weight 0 | axis | 1-4 | more | same | 4 / 0 |
| e026 season 0.5; cloud 1 vs e025 weight 1 | axis | 1-4 | split; same | split; split | 0 / 3 |
| e032 winter high 2 vs flat 0.75 | axis | 1-3 | more | same | 1 / 0 |
| e028 gut curve vs e026 season 0.5 | overlap | 1-4 | fewer | same | 0 / 3 |
| e040 thirst 0.001; 0.002; 0.005 vs control | overlap | 9 | same x3 | same; more; same | 0 / 0 |
| e039 reach 1 vs the same reach for all | no trade-off | 1-3, 9 | same | split | 0 / 1 |
| e038 sun 2; 4; at k 0.6 sun 2; 4 | amount | 9 | same; same; same; fewer | more; same; same; fewer | 0 / 0 |
| e041 stock 1; 4 | amount | 9 | same; same | same; fewer | 0 / 0 |
| e046 plant yield 0.5 | amount | 9-14 | split | split | 2 / 1 |
| e051 stock 1; 4; each with the brain | amount | 9-12 | split; split; fewer; fewer | split; fewer; split; split | 2 / 5 |
| e054 grain 64 | amount | 9-12 | split | fewer | 0 / 2 |
| e056 sun 2; sun 4 vs e055 | amount | 9-14; 9-11 | split; fewer | same; fewer | 2 / 4 |
| e057 foul 0.03 | amount | 9-14 | split | split | 1 / 2 |
| e059 islands vs thin uniform | amount | 9-14 | split | same | 0 / 2 |

- The axis laws hold more ways in 2 of 6 pairs per body (e025 and e032, both by bringing kills: all
  four e025 seeds become hunter worlds, one e032 seed does) and in 0 of 6 per lineage.
- The other laws hold no more in 21 of 21 pairs per body and 19 of 21 per lineage (e038 sun 2 and
  e040 thirst 0.002, each by one way on one seed). They are not neutral: 12 of the 21 moved seeds
  into or out of hunter worlds, in both directions, and those counts split.
- Moving the thresholds (`census.py sweep`: roam 4 and 16 cells, diet cuts 0.2/0.8, tooth force 1
  and 3, grown 100 and 1,000, share 2% and 10%) keeps the frame holding on 21-24 of 27 pairs per
  body. e025 reads "more" under 8 of 10 settings, e032 under 9, e012 against grass alone under 1
  (share 2%), the season and the cloud under none.

**4. e059 corrected.** Islands against the thin uniform world, seeds 9-14, steps 200,000 and
300,000: 2.0-5.0 ways per body (mean 3.0) against 2.0-3.5 (2.7); 1.0-2.0 per lineage (1.6) against
1.0-2.0 (1.3). Plant eaters without a tooth are 66-95% of the grown bodies against 64-92%; the share
that stays is 38-71% against 10-32%; hunter worlds 0 of 6 against 2 of 6. The correction is at the
top of e059's README and report, and on #69.

## Conclusion

1. **The laws read as new axes hold more ways of living: no.** 2 of 6 pairs per body, both by
   bringing kills; 0 of 6 per lineage.
2. **The other laws hold no more: yes.** 21 of 21 pairs per body, 19 of 21 per lineage; 12 of them
   move seeds between hunter and grazer worlds.

By the rule set before the census, the frame's **reading of the series is dropped**: the laws it
called successes did not add ways of living. The bound itself (ways at most the independent
limiting factors) is neither refuted nor tested: no world held more than three kinds, and none had
more than two foods (the plant, and the flesh of kills).

What this changes:

- **Count ways of living per kind, not per body.** Per body the number is mostly the spread of one
  kind: its diet by what lay near, a tooth lost to a break, its range by its age. The per-body count
  still says how varied a world's bodies look, and it follows the kills. Report both; judge a law
  per kind.
- **Every world so far holds one to three kinds of living**, whatever law was added. #42's "one
  winner" was not an artifact of its measure.
- **The flesh of kills is the only second food that has made a second way of living**, and a
  world's share of it is a degree that the seed and the laws move. The question for #72: can a world
  hold a hunter kind and a grazer kind when both are put there, apart from whether evolution finds
  them.
- **Columns to add before #72** (not added here): the tooth a body was born with, its kills apart
  from what it scavenged, and the length of the path it walked. A kind also needs a better unit than
  single-linkage lineages; the birth shape (#66) within a lineage is the candidate.

**What this cannot say.** The census rests on our thresholds (checked under 10 settings), on the
runs that were kept (1-6 seeds of 100,000-1,000,000 steps per pair), and on per-body columns that
mix kills with scavenging and read the tooth from the damaged body. It does not say that places or
seasons cannot make ways of living; it says the ones we ran did not.
