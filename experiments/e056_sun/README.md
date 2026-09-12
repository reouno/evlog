# e056 More sun under the clock

Date: 2026-09-12

## Purpose

e038 (#40) measured the ceiling on body size and found it was income: under 1, 2 and 4 suns the
crowd pinned a gut block's intake at 0.003-0.005 a step, and the extra sun bought **more bodies of
the same size**, not bigger ones. That was measured in a world where a body's upkeep is proportional
to its mass every step.

e055 (#60) changed exactly that. Under `clock` 0.5 a body of mass m takes (16 / m)^0.5 turns a world
step, so its upkeep comes to about m^0.5 a step, and body size sorted for the first time (mass p90
above the flat-pace control on four seeds of six, the winners carrying 1.3-2.2 times the blocks).
The cost side of e038's arithmetic has moved, so #65 asks its question again: with the cost of being
big now sublinear, does a richer sun buy **size** instead of **number**?

Nothing is added to the code: `sun` is already an argument, and this is e055 byte for byte with
`clock` 0.5 as the crate's default (the law e055 kept; e055's own default stays 0 so its runs
reproduce).

## Hypothesis

Written before the runs.

1. **Size rises with the sun.** The winning lineage's blocks and mass p90 rise from sun 1 to sun 2
   to sun 4, comparing pairs that settled in the same world state.
2. **Or it is still number.** The bodies rise about in proportion to the sun and the size does not
   move: the ceiling is the income after all, and the clock did not lift it.
3. **The world stands**: every winter floor above 50.

**What we expect.** Number, mostly: e038's crowd ate every extra ration, and under the clock the
income per gut is still set by how often a body reaches an eaten cell, not by what a cell can hold.
But the clock makes a heavy body cheap per unit of mass for the first time, so a part of the extra
sun can be taken as mass without the upkeep eating it. A rise in the size that is smaller than the
rise in the sun is the answer we expect, and the pilot has to show it moves at all.

## Method

Code: e055 (`experiments/e055_span`) byte for byte, as `e056_sun`, with the crate's default `clock`
0.5. `sun` is argument 33: the factor on every cell's regrowth and on the rain's cap with it, so a
world that burns twice as much can rain it back (e038's law, unchanged).

**Runs.** From the repo root: `bash experiments/e056_sun/run.sh <sun> <threads> <steps> <seeds>`.

| run | sun | seeds, steps | question |
|---|---|---|---|
| pilots, 3 threads | 1, 2, 4 | 9, 20,000 | does mass p90 or the winner's body move at all, and does the world stand |
| batch | 1 and the sun that moves it | 9-14, 100,000 | (1)-(3) |

**Measures** (over the second half): mass p50/p90/max and size p90; the winning lineage's blocks and
born mass; intake per gut (e038's 0.003-0.005); the pace by mass; bodies and winter floors; the
kills' share and the world state (hunter or grazer, e045); diversity (#42).

**Judged state by state.** e055 found the hunter/grazer state moves body size more than a law does,
and two seeds of six disagreed only because their worlds ended in different states. Pairs are
compared within a state, and the control for all of this is the clock world at sun 1 - every control
number from e043-e054 was measured without the clock.

**Compute.** No new cost: the sun is a factor on a multiply the world already does. Pilots: 3 runs
of 3 threads (9 of the Mac's 12 cores), about 5 minutes. Batch: 12 runs of 1 thread, about 45
minutes.

## Result

**Pilots.** Seed 9, 20,000 steps (one season), 3 threads each, 4 minutes. The sun 1 pilot reproduced
e055's `clock` 0.5 pilot number for number (pace 0.68, mass p50 33.9, p90 50.9, intake 0.0013,
3,067 bodies, floor 684), which is the check that this crate is e055's world: **the sun 1 control was
not run again**, and every sun 1 number below is e055's kept batch.

| run | mass p50 | mass p90 | size p50 | intake per gut | bodies | winter floor | regrowth | soil |
|---|---|---|---|---|---|---|---|---|
| sun 1 | 33.9 | 50.9 | 23 | 0.0013 | 3,067 | 684 | 41.7 | 82,503 |
| sun 2 | 32.0 | 32.0 | 16 | 0.0022 | 5,611 | 1,629 | 69.5 | 42,549 |
| sun 4 | 33.0 | 50.9 | 18 | 0.0021 | 5,614 | 1,740 | 80.7 | 34,188 |

The size did not move, the bodies did - and stopped moving between sun 2 and sun 4 (5,611 and
5,614) while the soil fell by half. The batch took sun 2 on all six seeds and sun 4 on three, to
see whether that is the transient or the world.

**Batch.** 100,000 steps, 9 runs at once (9 of the Mac's 12 cores), 30 minutes. Means over the
second half. The state is e045's: a hunter world breaks more than 0.03 blocks per body per step.

| seed | state 1 / 2 / 4 | mass p90 | size p90 | winner's blocks | bodies | lowest floor | kills' share | diversity |
|---|---|---|---|---|---|---|---|---|
| 9 | hunter / grazer / grazer | 56.0 / 42.0 / 49.2 | 38.8 / 21.0 / 24.6 | 27.9 / 14.7 / 15.0 | 2,488 / 4,091 / 3,763 | 675 / 1,533 / 1,740 | 33% / 7% / 4% | 2 / 1 / 1 |
| 10 | grazer / hunter / grazer | 50.9 / 33.7 / 32.0 | 39.8 / 32.0 / 16.0 | 29.7 / 18.5 / 14.0 | 2,632 / 4,127 / 5,341 | 614 / 974 / 1,470 | 23% / 36% / 19% | 2 / 2 / 1 |
| 11 | grazer / grazer / grazer | 32.0 / 56.8 / 32.0 | 16.0 / 28.4 / 16.0 | 14.2 / 23.1 / 13.8 | 3,178 / 3,740 / 4,515 | 809 / 1,521 / 2,201 | 8% / 18% / 4% | 1 / 1 / 1 |
| 12 | hunter / grazer | 60.1 / 42.8 | 45.4 / 21.4 | 30.0 / 18.4 | 2,396 / 4,197 | 525 / 1,022 | 31% / 14% | 1 / 1 |
| 13 | hunter / grazer | 70.8 / 50.0 | 52.2 / 25.0 | 36.8 / 21.8 | 2,232 / 2,987 | 524 / 886 | 30% / 4% | 2 / 1 |
| 14 | grazer / hunter | 32.7 / 41.5 | 18.8 / 32.4 | 14.2 / 20.3 | 3,133 / 3,777 | 838 / 1,219 | 11% / 31% | 1 / 2 |

- **The size does not rise with the sun.** Over the three seeds run at all three suns, mass p90 is
  46.3 / 44.2 / 37.7 and size p90 31.5 / 27.1 / 18.9. Judged state by state it does not move either:
  the grazer worlds' winners carry 19.4 blocks at sun 1 (3 worlds), 19.5 at sun 2 (4) and 14.3 at
  sun 4 (3); the hunter worlds' carry 31.6 at sun 1 (3) and 19.4 at sun 2 (2). The swings within one
  sun (14.2 to 36.8 blocks) are the seed's, not the sun's.
- **The number rises, and far less than the sun does.** Bodies 2,766 / 3,986 / 4,540 on the shared
  seeds: twice the light buys 44% more bodies, four times buys 64%.
- **The crowd pins the income, as in e038.** The intake per gut block is 0.0019 / 0.0020 / 0.0022 a
  step under 1, 2 and 4 suns - flat, as e038 measured it flat at 0.003-0.005 without the clock.
- **What binds is the matter, not the light.** The matter is conserved (140,139 in every run), and
  the light offered per step is 114 / 228 / 453. What is actually grown is 67.0 / 87.8 / 88.5 - four
  times the light grows 1.3 times the plant. The rest is lost to the canopy's shade (39% / 45% /
  31%) and, more and more, to **ground with no soil left to grow from**: `barren` takes 2% of the
  light at sun 1, 16% at sun 2 and **50% at sun 4**.
- **Where the soil went: into the bodies' fat.** The free soil falls from 70,186 (50% of all the
  matter) to 42,440 (30%) to 10,639 (**7.6%**), and the crowd's fat store rises 39,694 to 59,135 to
  96,591 over the same runs - 96% of the soil that went missing, with the fruit lying on the ground
  and the carrion making up most of the rest. A richer sun does not grow a bigger
  body; it moves the world's matter out of the ground and into more bodies and their stores, until
  the ground has nothing left to grow from.
- **The world stands, and more safely.** Winter floors 524-838 (sun 1), 886-1,533 (sun 2),
  1,470-2,201 (sun 4); no run died, and the mean age rises 795 / 1,055 / 1,420.
- **The tooth fades and diversity does not come.** Hunter worlds are 3 of 6 at sun 1, 2 of 6 at
  sun 2 and 0 of 3 at sun 4 (three seeds cannot settle that), and the diversity number (#42) is
  1-2 everywhere: a richer world is not a world of more kinds.

## Conclusion

The answers hold under the conditions of these runs (see "What these runs can and cannot say").

1. **Size rises with the sun: no.** Mass p90 46.3 / 44.2 / 37.7 and the winners' blocks flat or
   falling within each state. The clock lifted the *cost* of being big (e055), but the ceiling that
   e038 measured is the income, and the sun does not raise the income.
2. **It is still number: yes, and the number saturates too.** 44% more bodies for twice the light,
   64% for four times, with the intake per gut block pinned at 0.0019-0.0022.
3. **The world stands: yes.** Floors 886-2,201 against the control's 524-838.

**Not kept**: the season world's sun stays 1. Nothing here asks for a richer sun - it buys a
denser, smaller-bodied, less hunted world, and past sun 2 it mostly buys barren ground.

What this changes:

- **The sun is not the world's income; the matter is.** The light is a rate on a stock that the
  crowd holds: at sun 4 half the light falls on cells with nothing to grow from, and 92% of the
  world's matter is standing in plants, bodies and fat. e038 said the ceiling on a body is its
  income; e056 says the income has a ceiling of its own, and it is not the sun's to lift.
- **A law that needs a richer world cannot get it this way.** Anything we want to test in a world
  of plenty (a longer life, a bigger body, a costlier brain) has to come from more matter or a
  faster turnover of it - deeper soil, a faster rot, a cheaper body - not from turning up the sun.
- **Bigger bodies still need a reason, not a ration.** Two laws have now failed to make the world
  grow one by making it richer (e038, e056); the one thing that moved size was the clock, which
  changed what a body pays, and the hunter state, which changes what it eats.

**What these runs can and cannot say.** The answers hang on choices we made: e055's world at
`clock` 0.5, the sun as a factor on every cell's regrowth and on the rain's cap with it (e038's
law), six seeds of 100,000 steps at sun 2 and three at sun 4, and the state read off the blocks
broken per body. They do not say that no richer world grows a bigger body - they say this way of
making one richer does not, because the matter, not the light, is what the crowd is short of. The
three sun 4 seeds are too few to call the fading of the hunter state.
