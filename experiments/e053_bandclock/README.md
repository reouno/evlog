# e053 The band under the clock

Date: 2026-09-12

## Purpose

e049 laid a band of rain across the world and moved it west. The crowd followed it, but by
**births**, not by walking: a body lives about 200 steps and the band stays over a cell 1,600, so
the lineage meets the change and the body never has to. e052's clock (a body's own time scaling
with its mass) gave lives of 874-1,432 steps against 278-739 without it - long enough for a body
to see the rain come and go within its life. #59 asks what the band does to such bodies: do they
walk with it themselves, and does a brain pay where a body now lives long enough to use what it
learns?

Walking pays when the food moves (A, the band) and a body outlives the change (B, the clock): the
two conditions together, in the world where both already act.

## Hypothesis

Written before the runs.

**How fast the band may go.** e049 set the band's speed to what a body moves now in all directions
together (e048: 0.059-0.089 sub-cells a step), which gave `band` 50 = 0.08. Under the clock every
body takes 0.78-0.88 of a turn a step and moves 0.035-0.052, so the same reasoning gives `band`
100 = 0.04 sub-cells a step. A life of 1,300 steps then meets 13 cells of the band's way, 40% of
the band's width (32 cells): a body born in the middle of the rain ends its life at the band's
back edge unless it walks, and walking west at half of what it now moves keeps it under the rain.
At `band` 50 the band covers 26 cells in such a life, more than a body of this world can walk, so
the crowd would be left behind as in e049. The pilot runs both and the batch takes the one where
the band binds and the world stands.

1. **The body walks, not only the lineage.** Over the second half, `west` (sub-cells a body moves
   west by its own actions, less those east, per step) is at least a quarter of the band's speed
   (0.02 at `band` 50) and above the control's (the same band at `clock` 0) on at least 3 of 4
   seeds. e049's crowd walked at 2-6% of the band without thirst.
2. **The long-lived walk, and they are the crowd now.** The bodies aged 1,000 steps or more at the
   run's end drift west at least half as fast as the band (median drift over age, 0.01 cells a
   step at `band` 50), and they are a large part of the living (e049 under thirst: 2-17 bodies a run; under the clock, lives of
   874-1,432 should make them common).
3. **The world stands.** The lowest winter floor stays above 50 in every run. e049's band halved
   the world and one run of eight died; the clock holds 8-37% more bodies and raises every floor,
   so the combination is the test of whether a moving rain is runnable at all.
4. **The brain pays where a life is long** (second batch, only if (1) or (2) holds): under the
   band and the clock, learners are a larger share than at `clock` 0 under the same band (e050:
   learning used in 26-62% of the decisions but not selected), and the winning lineages of the
   last third carry it.

## Method

Code: e052 (`experiments/e052_clock`) as `e053_bandclock`, byte for byte - no new law. e049's
`band` (argument 45), e050's `brain` (46) and e052's `clock` (47) are arguments of that code and
are combined here for the first time. e048's world otherwise (no thirst, no stock).

**Runs.** From the repo root:
`bash experiments/e053_bandclock/run.sh <band> <clock> <brain> <threads> <steps> <seeds>`.

| run | band | clock | brain | seeds, steps | question |
|---|---|---|---|---|---|
| pilots, 3 threads | 100, 50 | 0.25 | 0 | 9, 20,000 | does the band bind under the clock (`in_band`, `west`), does the world stand |
| pilot, 3 threads | 100 | 0 | 0 | 9, 20,000 | the same band without the clock, for the pilot's pair |
| batch | 50 | 0.25 | 0 | 9-12, 100,000 | (1)-(3) |
| control | 50 | 0 | 0 | 9-12, 100,000 | the band without the clock, on the same seeds |
| brain (only if (1) or (2) holds) | 50 | 0.25 | 1 | 9-12, 100,000 | (4) |

**Measures** (over the second half, as in e049): `west`, `in_band`; the median drift and drift over
age of the bodies aged 1,000 steps or more at the last agents row; `moved`, speed and muscle per
body; `pace`; bodies, winter floors, the kills' share of the intake; where hunger kills behind the
band's front (`dist.csv`); the age at death; the winners of the last third; diversity (#42).

**Compute.** No new cost: the band is one pass over the 128 columns a step, the clock one `powf` a
body. Pilots: 3 runs of 3 threads (9 of the Mac's 12 cores), 4 minutes. Batch and control: 8
runs of 1 thread, 20 minutes on the Mac. The brain batch was not run (see the Conclusion).

## Result

**Pilots.** Seed 9, 20,000 steps (the first winter), 3 threads each, 4 minutes. The band's speed in
sub-cells a step is 4 / `band` (0.08 at 50, 0.04 at 100); `west` is the same unit.

| band | clock | under the band | `west` (the band's speed) | pace | `moved` | bodies at 20,000 (winter low) | age at death p50 / p90 |
|---|---|---|---|---|---|---|---|
| 100 | 0.25 | 63-68% | 0.0002 (0.04) | 0.73-0.80 | 0.042-0.054 | 772 (163) | 300 / 1,055 |
| 50 | 0.25 | 55-58% | 0.0013 (0.08) | 0.75-0.80 | 0.049 | 861 (113) | 282 / 916 |
| 100 | 0 | 64-68% | 0.0003 (0.04) | 1.00 | 0.061-0.064 | 830 (167) | 215 / 756 |

- **The world stands under both bands**, at half of e048's numbers as e049's band was: 772-1,019
  bodies against 1,937, winter lows 113-167 against 422.
- **The slower band is the one nobody walks after.** At `band` 100 the crowd sits under the rain
  (63-68% of the body-steps, a quarter of the world) and walks west at 0.5% of the band's speed -
  with the clock and without it alike. At `band` 50 `west` is six times higher (1.6%), still far
  under e049's 2-6% at `band` 25.
- **The clock costs moving**: 0.042-0.054 sub-cells a step against the control's 0.061-0.064, in
  proportion to the pace (0.73-0.80).
- The batch takes `band` 50: within a life of 1,300 steps (e052's mean age of the living) the band
  covers 26 of the 32 cells of its own width there, so a body that does not walk meets the rain's
  going; at 100 it covers 13 and the pilot shows the crowd has no reason to move.

**Batch.** Seeds 9-12, 100,000 steps, `band` 50 with and without the clock, eight runs at once on
the Mac, 20 minutes. Means over the second half (steps 50,000-100,000); pairs are the band alone /
the band under the clock on the same seed. The band moves 0.08 sub-cells a step (`west`'s unit) and
0.02 world cells a step (the drift rate's).

| seed | `west` | under the band | drift rate | bodies | lowest floor | mean age of the living | mass p50 | intake per gut | kills' share | state | diversity |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | 0.0019 / 0.0025 | 61% / 58% | 0.0037 / 0.0029 | 974 / 946 | 131 / 113 | 368 / 440 | 34 / 50 | 0.0032 / 0.0021 | 30% / 29% | hunter / hunter | 1 / 2 |
| 10 | 0.0019 / 0.0030 | 61% / 55% | 0.0028 / 0.0032 | 886 / 1,165 | 88 / 131 | 368 / 818 | 34 / 37 | 0.0028 / 0.0026 | 27% / 14% | hunter / grazer | 2 / 1 |
| 11 | 0.0019 / 0.0042 | 61% / 58% | 0.0039 / 0.0068 | 1,177 / 1,031 | 190 / 91 | 683 / 380 | 32 / 33 | 0.0033 / 0.0025 | 20% / 29% | grazer / hunter | 1 / 3 |
| 12 | 0.0025 / 0.0030 | 61% / 58% | 0.0030 / 0 | 992 / 1,081 | 120 / 102 | 619 / 381 | 36 / 33 | 0.0028 / 0.0022 | 18% / 30% | grazer / hunter | 1 / 1 |

- **The clock moves the crowd west, a little.** `west` is above the control's on all four seeds
  (0.0025-0.0042 against 0.0019-0.0025), but it is 3-5% of the band's speed, where e049 found 2-6%
  at `band` 25 without thirst. The crowd is also further behind the band than without the clock
  (55-58% of the body-steps under it against 61%), because it moves less: 0.056-0.078 sub-cells a
  step in all directions against 0.062-0.094, in proportion to the pace (0.78-0.86).
- **The long-lived do not walk farther under the clock.** All seeds together, the bodies alive at
  step 100,000 stand, by age bin: 3.8 cells west of their birthplace at 1,000-1,999 steps and 12.5
  at 2,000 or more without the clock (395 and 138 bodies), against 2.8 and 9.2 with it (441 and
  175). The band moves 0.02 cells a step, so 1,500 steps of it is 30 cells.
- **The clock does not buy long lives here.** The mean age of the living is 380-818 under the clock
  against 368-683 without it - it rises on two seeds and falls on two. In e052's world, the same
  law on the same seeds raised it from 278-739 to 874-1,432.
- **Because the deaths are hunger, and the clock makes hunger worse.** Deaths are 2.0-3.1 by hunger
  a log interval against 0.26-0.68 by a break, and **none** by wear (e052: 281-1,837 by wear). The
  intake per gut falls from 0.0028-0.0033 to 0.0021-0.0026: a body that takes its turn 0.8 of the
  time takes 0.8 of the food from a ground the crowd has already thinned.
- **The world stands, and better than e049's band world.** Winter floors 91-179 under the clock and
  88-190 without, no run died; e049's `band` 25 fell to 16-122 and one of eight worlds died.
- **The clock turns the band's world to hunting**, the opposite of what it did without the band:
  hunter worlds 3 of 4 against 2 of 4 here (e052, no band: 0 of 4 against 2 of 4). Seeds 11 and 12
  turn hunter under the clock; seed 10 turns grazer.

## Conclusion

The answers hold under the conditions of these runs (see "What these runs can and cannot say").

1. **The body walks, not only the lineage: no.** Walking west rises on all four seeds under the
   clock, but to 3-5% of the band's speed, where a quarter was asked; and the bodies that live
   longest drift less than the control's, not more (2.8 cells against 3.8 at 1,000-1,999 steps).
2. **The long-lived are the crowd now: no, and the reason is the point.** Under the band the clock
   does not lengthen lives at all (mean age of the living 380-818 against the control's 368-683),
   where in e052's world it doubled to quadrupled them. What kills here is hunger (2.0-3.1 deaths a
   log interval against none by wear), and the clock makes hunger worse: a body takes its turn 0.8
   of the time and its intake per gut falls by 20-30%.
3. **The world stands: yes.** Winter floors 91-179, no run died - a better-standing world than
   e049's band alone (16-122, one world of eight died).
4. **The brain where a life is long: not run.** The condition it needs (a life long enough to use
   what it learns) does not appear in this world, so the question cannot be asked here.

**Not kept**: nothing new was added, and the combination does not make bodies walk. `band`, `clock`
and `brain` stay arguments.

What this changes:

- **A long life is a rich world's, not a law's.** e052's clock bought lives because that world fed
  its bodies; the band takes the same sun and pours it on a quarter of the world, and there the
  same law buys nothing. Before a law can use "bodies live long" as its condition, the world has
  to be one where they do.
- **The two conditions destroy each other.** We wanted the food to move (A) and the body to outlive
  the change (B). A is what makes B impossible here: the moving band is what keeps the world poor
  and the deaths at hunger. A world with both needs the band to be gentler than a quarter of the
  world's width, or the world to be richer than e048's.
- **The band packs the crowd, and the clock makes it hunt.** Hunter worlds 3 of 4 under the clock
  against 2 of 4 without, the opposite of e052's no-band result (0 of 4). The band is a density
  law as much as a water law.
- **Next**: the open end of #59 is a world where lives are long AND the food moves. The cheapest
  test is the band over a richer world (more sun, or a band over half the world instead of a
  quarter) - one pilot says whether lives lengthen there at all, and only then is walking worth
  asking about again.

**What these runs can and cannot say.** The answers hang on choices we made: `band` 50 (the pilot's
other speed, 100, showed a crowd with no reason to move at all), `clock` 0.25 with the reference
mass 16, e048's world, no thirst, four seeds of 100,000 steps. They do not say that a body cannot
be made to follow a moving food; they say that in this world the clock's long lives and the band's
moving rain cannot be had at the same time.
