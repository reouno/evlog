# e055 A clock that reaches further

Date: 2026-09-12

## Purpose

e052 (#55) gave every body its own time: a body of mass m takes (16 / m)^`clock` turns a world
step. At `clock` 0.25 and the reference mass 16, the bodies of e048's world (mass 12-69) all ran
at 0.78-0.88 of a turn a step - a range far too narrow for size to sort in, and the 90th percentile
of the mass rose above the control's on one seed of four. #60 asks the same question with a clock
whose range actually spans the sizes of this world: at exponent 0.5 a body of 64 runs at half the
pace of one of 16 (the span here is 0.48-1.0), at 1.0 at a quarter (0.23-1.0).

Nothing is added to the code: `clock` is already an argument, and this is e054 byte for byte.

## Hypothesis

Written before the runs.

**Against it, from e053.** The world's own clocks do not scale: the sun, the regrowth, the rot and
the other bodies run per step. A slowed body reaches the ground less often while its neighbours
graze it, and e053 measured the cost at pace 0.8 - the intake per gut fell 20-30%. A clock that
reaches further taxes the heavy hardest, which is the opposite of what a size axis needs. So the
expected answer is no, and the run is worth making because the way it fails is the answer to the
size question: if the heavy starve as they slow, what stops a size axis in this world is income
(e037, e038, e052, e054 all point there), not time.

1. **Size sorts.** The 90th percentile of the mass is above the flat-pace control's (the same mean
   pace, no scaling by size) on at least three seeds of four. e052 at 0.25: one of four.
2. **Or the heavy are taxed**: mass p90 below the control's, and the intake per gut falling with
   the pace of the heavy bodies.
3. **The world stands**: every winter floor above 50.
4. **Without runs** (the second question of #60): why the diversity number falls to 1 while four to
   six lineages each hold 5% of the last third.

## Method

Code: e054 (`experiments/e054_grain`) as `e055_span`, byte for byte. `clock` (argument 47) is the
exponent; a negative value is the flat-pace control (every body takes |clock| turns a step whatever
it weighs), as in e052.

**Runs.** From the repo root: `bash experiments/e055_span/run.sh <clock> <threads> <steps> <seeds>`.

| run | clock | seeds, steps | question |
|---|---|---|---|
| pilots, 3 threads | 0.5, 1, -0.68 | 9, 20,000 | what the pace spans, whether the world stands, whether mass p90 moves at all |
| batch | the exponent that moves the mass | 9-12, 100,000 | (1)-(3) |
| control | the flat pace at the batch's mean | 9-12, 100,000 | the slowdown without the scaling by size |

**Measures** (over the second half): `pace` and `turned`; the pace of the light and the heavy
apart (from `agents.csv`, which carries `pace` per body); mass p50/p90/max and size p90; intake per
gut; the age at death of the light and the heavy (`deaths.csv` bins the mass at birth); bodies and
winter floors; the kills' share; diversity (#42).

**Compute.** No new cost: the clock is one `powf` a body a step, as in e052. Pilots: 3 runs of 3
threads (9 of the Mac's 12 cores), 5 minutes. Batch and control: 8 runs of 1 thread, about 30
minutes on the Mac.

## Result

**Pilots.** Seed 9, 20,000 steps (one season), 3 threads each, 4 minutes. Means over the second log
row (steps 10,000-20,000); the floor is the lowest population of the season.

| run | pace | mass p50 | mass p90 | intake per gut | bodies at 20,000 | winter floor |
|---|---|---|---|---|---|---|
| `clock` 0.5 | 0.68 | 33.9 | 50.9 | 0.0013 | 3,067 | 684 |
| `clock` 1 | 0.38 | 47.0 | 78.6 | 0.0007 | 3,426 | 1,024 |
| flat pace 0.68 | 0.68 | 36.0 | 72.0 | 0.0021 | 2,736 | 501 |

- **The clock reaches, as designed**: the mean pace is 0.66-0.68 at exponent 0.5 (span 0.48-1.0
  over the masses of this world) and 0.38-0.43 at 1 (span 0.23-1.0), against e052's 0.78-0.88.
- **The world stands at both**, and better than the flat world of e054 (floors 501-1,024 against
  422), because a slower crowd eats the same ground less often: the bodies are 2,700-3,400 against
  1,937.
- **The first sign is the tax, not the sorting.** Against its own flat-pace control, `clock` 0.5
  carries a *smaller* 90th percentile of the mass (50.9 against 72.0) on this seed and season, and
  a fifth less intake per gut (0.0013 against 0.0021).
- The batch takes `clock` 0.5, the exponent #60 asks about, with the flat pace 0.68 as its control.
  Exponent 1 stays a pilot: it is the same question asked harder, and the pilot shows it does not
  break the world.

**The diversity number (question 4), from the runs we already have.** Over e054's eight runs, every
pair of winners was measured: the pairs the number merges are far inside its thresholds (block-mix
distance 0.002-0.14 where the limit is 0.4, size ratio 1.00-1.37 where the limit is 1.5). The
lineages that each hold 5% of the last third really are the same body in different families - e054's
patchy seed 11 has six winners, all of 14 blocks, no two further apart than 0.04. The number counts
forms and the lineage count counts families, so the two are meant to disagree. One weakness showed
up: single linkage chains, and in e054's flat seed 9 two winners 0.469 apart (beyond the limit) land
in one group through an intermediate. It touched 1 of 8 runs and moves the number by at most 1.

**Batch.** `clock` 0.5 against the flat pace 0.68 on the same seeds, 100,000 steps. Seeds 9-12
first (8 runs at once, 25 minutes), then 13 and 14 added because the answer decides a default
(4 runs, 20 minutes). Means over the second half; pairs are the clock / the flat pace.

| seed | state | mass p90 | size p90 (blocks) | winner's body | born mass p50 | life light-heavy | bodies | lowest floor | diversity |
|---|---|---|---|---|---|---|---|---|---|
| 9 | hunter / grazer | 56.0 / 50.0 | 38.8 / 25.0 | 27.9 / 20.6 | 36 / 25 | 75-325 / 225-375 | 2,488 / 2,682 | 675 / 501 | 2 / 1 |
| 10 | grazer / grazer | 50.9 / 43.6 | 39.8 / 24.4 | 29.7 / 14.6 | 36 / 18 | 125-425 / 225-275 | 2,632 / 3,467 | 614 / 777 | 2 / 2 |
| 11 | grazer / grazer | 32.0 / 32.0 | 16.0 / 16.0 | 14.2 / 14.5 | 16 / 16 | 125-275 / 125-275 | 3,178 / 3,446 | 809 / 879 | 1 / 1 |
| 12 | hunter / hunter | 60.1 / 47.6 | 45.4 / 35.2 | 30.0 / 22.8 | 36 / 36 | 175-375 / 175-325 | 2,396 / 2,740 | 525 / 559 | 1 / 1 |
| 13 | hunter / hunter | 70.8 / 38.5 | 52.2 / 31.4 | 36.8 / 16.5 | - | 125-425 / 225-325 | 2,232 / 3,160 | 524 / 600 | 2 / 1 |
| 14 | grazer / hunter | 32.7 / 56.2 | 18.8 / 36.0 | 14.2 / 26.2 | - | 125-325 / 175-325 | 3,133 / 2,396 | 838 / 614 | 1 / 1 |

- **The clock reaches, and size answers.** The pace is a real axis now: by mass bin, 1.00 / 0.89 /
  0.74 / 0.70 / 0.54 / 0.47 turns a step, against a flat 0.68 in the control. The 90th percentile
  of the mass is above the control's on four seeds of six, equal on one, below on one.
- **Where both worlds settled in the same state, the clock is bigger or equal on all four**
  (50.9/43.6, 32.0/32.0, 60.1/47.6, 70.8/38.5). The two seeds that disagree are the two where the
  worlds ended in different states: this world has a hunter state and a grazer state (e045), the
  seed picks it, and a hunter world grows bigger bodies whatever the clock.
- **It is selection, not a census effect.** The winning lineage's body is 1.3-2.2 times bigger under
  the clock in the same-state pairs (29.7 against 14.6 blocks, 36.8 against 16.5), and bodies are
  *born* bigger (born mass p50 36 against 18-25 on seeds 9 and 10).
- **The tax we expected did not show at the world's level**: the intake per gut is 0.0019 in both.
  It lands on the light instead, which now run at a full turn a step: a body born light lives 75-175
  steps against the control's 125-225, while a heavy one lives 275-425 against 275-375. The heavy's
  life is 2.1-4.3 times the light's, against 1.2-1.9 in the control - Kleiber's pattern, from a law
  that says nothing about lifespan. (A life in world steps is partly the clock's own definition: a
  slow body's wear accrues slower. The size of the winners is the evidence that is not.)
- **The world stands**: floors 524-838 against the control's 501-879, no run died. It holds 10%
  fewer bodies (2,677 against 2,982) and the same mean age (795 against 815); the hunter state
  appears in 3 of 6 worlds under both.

## Conclusion

The answers hold under the conditions of these runs (see "What these runs can and cannot say").

1. **Size sorts: yes.** Mass p90 above the flat-pace control on four seeds of six and equal on a
   fifth; in every pair where both worlds settled in the same state, the clock's bodies are bigger
   or equal (4 of 4), and the winning lineages carry 1.3-2.2 times the blocks.
2. **The heavy are taxed: no** - the light are. The intake per gut is the same in both (0.0019),
   and it is the bodies born light whose lives shorten (75-175 steps against 125-225).
3. **The world stands: yes.** Winter floors 524-838, no run died.
4. **The diversity number (no runs needed): it is not a threshold artifact.** Merged winners sit far
   inside the limits (mix distance 0.002-0.14 of 0.4); the lineage count counts families and the
   diversity number counts forms.

**Kept**: the season world's clock is `clock` 0.5. e052 ran the same law at 0.25 and it was not
kept, because at that exponent every body ran at 0.78-0.88 and the law had nothing to sort with.
This changes the default world for the experiments that follow: every body's own time now scales
with its mass.

What this changes:

- **The world has a body-size axis at last.** e029 (size is the sun's), e037 (upkeep by size) and
  e038 (income) all failed to spread the sizes; the clock does it by spreading *time* instead, and
  the spread survives in what wins, not only in what stands.
- **Kleiber for free.** The upkeep of a body comes to about m^0.5 a world step at this exponent and
  its life to 2-4 times the light's, without either being written as a rule.
- **The world state still dominates.** Whether a world hunts or grazes is the seed's, and it moves
  body size more than the clock does. A law about bodies is read against the state it lands in;
  pairs must be compared state by state.

**What these runs can and cannot say.** The answers hang on choices we made: exponent 0.5 with the
reference mass 16, the flat-pace control at 0.68 (the clock's crowd ran at 0.64-0.76, so the control
is 0-11% slower), e048's world with no thirst and flat food, six seeds of 100,000 steps. They do not
say that 0.5 is the best exponent - the pilot at 1 also stands and spans 0.23-1.0, and was not run
as a batch.
