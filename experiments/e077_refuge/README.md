# e077: does the season take the lawn away? (#91 step 0)

Date: 2026-09-19

## Purpose

#91 asks whether a standing forest can be a refuge a lawn cannot hold: a place worth less than its
surroundings most of the year and more when the season turns. Named together (#87): **a refuge pays
when the season takes the lawn away (A) and the stand keeps what the lawn loses (B).** (B) is not in
the world yet. Before building it, this step measures (A) in stage C's default world (e075's kept
runs): if the lawn loses little in its low season, no (B) can make a refuge, and #91 turns to the
season itself.

## Hypothesis

Written after the dry run (its numbers are in the result) and before the instrumented runs.

1. **World-wide the season takes little from the lawn.** The bodies live in the warm lands (7,000-8,300
   of 10,000 on a hot habitat at a census), where the sun's year swings least, so the grass grown on
   the lawn differs by less than a third between its best and worst quarter.
2. **Only poleward it takes much**: the lawn's growth in its worst quarter falls under half of its best
   only past 40 degrees of latitude, where few bodies live.
3. **Nobody moves with the season**: the share of the land's bodies standing in a stand (wood of 1 or
   more on the cell) moves by less than 5 points over the year.

## Method

No law. Two parts:

- **Dry run on e075's kept runs** (`dryrun.py`, `profile.py`, `census.py`; no runs). The bodies start on
  a whole year of the climate (update counts are whole years), so a step's phase in the year is
  step / 11,880 on c1225. The log (every 1,000 steps) is binned by phase, seeds 9-11 pooled, steps
  20,000-100,000.
- **One instrumented run a seed** (`run.sh`, the e075 binary copied with measures only): its log is
  byte-identical to e075's kept run (checked on the first 2,000 steps of seed 9, timing columns aside).
  Added: `_bands.csv` every 1,000 steps, the land by 10-degree band of latitude and by the wood on a
  cell (lawn < 0.1, thin 0.1-1, stand >= 1): cells, grass grown since the last row, grass and wood
  standing, mean temperature, the land's bodies; `_agents.csv` gains the cell under a body and the wood
  on it (`cell`, `crown`), with a census every 1,000 steps from 36,000 (two years).

      (nohup bash experiments/e077_refuge/run.sh c1225 60000 9 year census=1000 census_from=36000 \
        > experiments/e077_refuge/results/c1225_life9_year.log 2>&1 < /dev/null &)

Seeds 9, 10, 11 (life=9-11 on c1225, d11), 60,000 steps, one thread each: 3 cores for about 25 minutes
on the Mac.

## Result

**Dry run (e075's kept runs, seeds 9-11 pooled, 20,000-100,000, the log in twelve bins of the year).**
World-wide the land's grass grows 19-25 a step by season (worst/best 0.76) and the land's mean
temperature moves 18-24.5 C. But the land's bodies rise and fall **twice a year**: 2,870-3,030 at phases
0.21 and 0.71 (the solstices), 5,000-5,040 at 0.46 and 0.96 (the equinoxes), with standing grass highest
(23,000-24,700) when the land holds fewest bodies. Water and surface bodies barely move.

**The instrumented runs** (3 seeds x 60,000 steps; `analyze.py`; rows after the first year, pooled;
a quarter centred on phase 0, 0.25, 0.5, 0.75; the north's summer is phase 0.25):

| latitude | lawn growth, worst/best quarter | lawn temperature by quarter (C) | lawn bodies by quarter | stand bodies by quarter |
|---|---|---|---|---|
| -60 to -30 | 0.01-0.33 | -14 to 43 | 3-358 | 0-60 |
| -20 to +10 | 0.35-0.75 | 25 to 42 | 4-163 | 188-481 |
| +20 to +40 | 0.15-0.40 | -6 to 40 | 16-298 | 2-123 |
| +50 and up | 0.00-0.01 | -31 to 30 | 0-51 | 0-2 |

- **Where the stands are.** Wood of 1 or more a cell grows only between -30 and +20 degrees, the
  tropics; the seasonal lawns lie next to them, from 20 degrees poleward. 10 degrees is about 17 cells,
  under a body's 22-28 cells of travel in a life.
- **The whole land by class**: lawn growth worst/best 0.78, thin wood 0.88, stand 0.91. Bodies on the
  lawn by quarter 65,000 / 25,500 / 56,800 / 30,100 (row sums), in the stands 59,200 / 55,800 / 55,500 /
  54,300. **The twice-a-year swing is the lawn's alone; the stand's bodies do not move with the season.**
- **The lawn is taken twice, for two reasons.** In winter it stops growing (at 30-40 N the quarter's
  growth is 0.02-0.07 of a cell's best, the temperature -6 to 4 C). In summer it grows best and stands
  highest (0.14-0.22 a cell at 30-40 N, three times the winter's) but its bodies are gone (27 and 53 at
  30 and 40 N against 298 and 219 in the autumn) at 35-38 C: over 30 C a body pays water to cool
  (`warm_hi`), so the summer lawn is lost to heat, not to hunger. (Temperatures are the cells' at the
  log's rows, whose hour of the day drifts, so they are close to a day's mean.)
- **The census** (every 1,000 steps from 36,000): the share of the land's bodies in a stand goes from
  0.24-0.31 at the equinoxes to 0.49-0.59 at the solstices on every seed, only because the lawn's
  crowd comes and goes (land bodies 2,670-5,620). The mid-latitude lawn's crowd swings 5-8 times
  (260-2,390); 23-83% of it belongs to lineages with ten or more bodies in a stand at the same census,
  with no pattern by season. At step 60,000 the largest line in the stands is also the largest on the
  mid-latitude lawn on seeds 9 and 11 (a hunter, kills 32-55% of its food); on seed 10 the lawn's is a
  grazer (47 gut blocks of 49).
- Lives against the year (11,880 steps; e075's kept runs, steps 20,000-100,000): half the dead die by
  about 75 steps, most as children in the crowd; a grown body (300 steps or more) lives to a median of
  500-570, about 1/20 of a year, and the oldest to about 4,400, a third of one. No body dies of wear.
  So almost nothing can migrate with the season as a body. A refuge would work across generations: a line held in the stand through the
  bad quarter and spread back onto the lawn.

## Conclusion

1. **Yes**: world-wide the lawn's growth moves by 22% (worst/best 0.78), under a third.
2. **Partly**: the lawn's worst quarter falls under half of its best from **20** degrees poleward, not
   40, and bodies do live there (the mid-latitude lawn holds up to 2,400 bodies in the equinoxes).
3. **No**: the share in stands moves by 30 points, not 5. But it moves because the lawn empties twice
   a year, not because bodies go into the stands (their number holds within 9%).

**(A) is there**, in the conditions of this world (c1225, a 75-step day, a heat law with a comfort band of
15-30 C, a grown body living about 1/20 of a year): the season takes the mid-latitude lawn twice a year, in winter by
food and in summer by heat, and the stands are within a life's travel of it. What is missing is (B): a
stand today is as hot as the lawn next to it (within 1-5 C in the hot quarter), so it gives nothing the
lawn lost. For #91 step 1 this puts **the heat buffered under crowns** first: the summer's loss is
heat, and a crown that takes the top off a hot day is the one thing a stand could hold that the lawn
cannot. The migrant it could make is a line, not a body.
