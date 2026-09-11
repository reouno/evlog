# e051 A place that gets worse the longer a body stays

Date: 2026-09-12

## Purpose

In e050 the brain (#53) was used but not selected: learning changed 26-62% of a learner's
decisions, yet learners were kept only on two seeds of e048's world, riding on fast muscle
blocks. What a brain is worth depends on what the world asks of it, so the world comes first.
e050's toy showed where a learner should gain: with the baseline it leaves a declining patch
sooner than the reflex (25 steps against 40). This experiment builds that world.

**What the bodies live on (checked first, decision rule 6).** In e048's world (seeds 9-12,
second half) 146 of light reaches the cells a step. The crowns take 73-89 of it, and the plant
grows 74-78. Of what the guts take, 77-81% comes from cells that stand at 1 or more (trees). The
fruit rain is gone (3-13 made a step, 2-6 eaten). A tree's growth already follows its height:
its crown claims light as far as it is tall, so a column of 5 gathers up to about 26 cells' sun
and one of 0.5 about 2. A tree under a body does not grow (`hold`). So a place already worsens
while a body stays, at the scale of a tree, and recovers fast once the body leaves, unless the
tree was felled.

e041's `stock` law (argument 37, untested since e043 ended the fruit rain) makes the damage
outlast the grazer. A cell uses min(1, res / stock) of its light, never less than a tenth. At
`stock` 1 standing trees are untouched; a bare cell stands at 1 again in about 330 steps at full
sun, against 100 without the law. That is longer than a median life (about 200 steps). At 4 the
law also slows every bitten tree (trees stand at 4-6).

Leaving pays when the grazed spot comes back slowly (A) and the body can learn (B): the two
conditions together, with the brain on and off.

## Hypothesis

Written before the runs. The payoff: a gut eats min(r, 0.02) a step from the cell under it, and
a held cell does not grow, so a still body eats down what stands under it and then nothing.
Moving costs 0.001 per block of mass per sub-cell, and a world cell is four sub-cells: a body of
20 blocks pays 0.08 to cross one, about four steps of what its 8 guts take in now (0.0027 per gut
a step). Without `stock`, a cell just left regrows at its full light, so the cells around a body
are as good as any farther off. With it, a cell left bare comes back at a tenth of its light, so
the cells a body and its neighbors grazed are poorer than those farther away, and the gain is in
going farther.

1. **Bodies go farther under the law.** With `stock` and the old brain (brain 0), over the second
   half, `moved` is above e048's on the same seed on at least three of four seeds, and grown
   bodies (aged 1,000 steps or more, at step 100,000) stand farther from their birthplace than
   e048's (13.1, 10.1, 13.5 and 29.2 world cells on seeds 9-12) on at least three.
2. **Learning is selected where the place worsens.** With `stock` and the brain, learners over
   the second half are above half on at least three of four seeds, and above e050's brain run in
   e048's world on the same seed (7%, 31%, 95%, 59%) on at least three.
3. **Learners leave sooner.** Under `stock` and the brain, the learners' giving-up density
   (`gud_learn`) is above the rest's (`gud_rest`) over the second half, on at least three of the
   seeds where both groups hold at least 5% of the bodies.
4. **The world stands.** The lowest winter floor stays above 50 in every run.

## Method

Code: e050 (`experiments/e050_brain`) as `e051_leave`. No law is new or changed; `stock`
(argument 37) and `brain` (argument 46) are e041's and e050's.

- **One new measure, the giving-up density** (the food a forager leaves in a patch when it
  moves on, the classic measure of when an animal leaves). As a body acts, the log counts the
  world cells under its digestive blocks and the food on them (`under_learn`, `under_rest`). When
  the body's own step or turn takes every gut off a cell it was on, it counts the food left there
  (`gud_learn`, `gud_rest`) and how often it happens per body-step (`left_learn`, `left_rest`).
  The food is all a gut can eat on the cell: plant, dead matter and fruit. Learners are the
  bodies with eta above 0 under the brain; under the old brain every body is in "the rest". A
  shove by another body is not a leaving. The measure tells "learners leave a declining place
  sooner" apart from "learners are the fast bodies" (e050).
- **Checked**: `stock` 0 with the brain repeats e050's brain run in e048's world on seed 9 for
  the first 20,000 steps of every CSV but the new columns and the timing column.

**Runs.** e048's world (the season world under the motor, no band, no thirst), one thread each
unless said:

| run | stock | brain | seeds, steps | question |
|---|---|---|---|---|
| controls (e048's motor runs, e050's brain runs in e048's world; already run) | 0 | 0 and 1 | 9-12, 100,000 | neither law; the brain alone |
| check, 3 threads | 0 | 1 | 9, 20,000 | byte for byte with e050 |
| pilot, 3 threads | 1 and 4 | 1 | 9, 20,000 | does the world stand, does the law bind (`bare`, `grazed`); the batch's value |
| batch | from the pilot | 0 and 1 | 9-12, 100,000 | (1)-(4) |
| batch at 4 (added after the batch at 1) | 4 | 0 and 1 | 9-12, 100,000 | (1)-(4) where the law slows the trees too |

The batch takes the value at which the world stands and the law binds, 1 if both do. The batch at
4 was added when the batch at 1 moved nothing and the pilot at 4 was the one run where bodies moved
more and learned (8 of 12 cores, about 15 minutes). Run from the repo root:
`bash experiments/e051_leave/run.sh <stock> <brain> <threads> <steps> <seeds>`.

**Measures** (over the second half): `moved`, `stalled`, the travel of grown bodies; `learners`,
`eta`, `learned`, `memory`; `under`, `gud`, `left` by group; `bare` (light lost to the law),
`grazed` (the share of cells below the knee), trees, the intake from trees, regrowth; bodies,
winter floors, the kills' share of the intake; the winners of the last third; diversity (#42).

**Compute.** The measure reads the cells under a body's guts twice a step (at most 25 cells); no
measurable cost is expected, and the pilot compares steps per second with the check. Check and
pilot: 3 runs of 3 threads, about 5 minutes. Batch: 8 of the Mac's 12 cores, about 35 minutes.

## Result

**Check.** `stock` 0 with the brain on seed 9 for 20,000 steps is e050's brain run in e048's
world: every row of every CSV identical but the six new columns and `steps_per_sec`; the long and
bodies frames a prefix of e050's; the terrain identical.

**Pilots.** Seed 9, the brain, 20,000 steps, 3 threads each. Pairs are the two log rows (steps
10,000 and 20,000: a summer half, then a winter half). Kept in `results/pilot/`.

| stock | bodies | lowest | light lost to the law | cells below the knee | moved | speed | learners |
|---|---|---|---|---|---|---|---|
| 0 (the check) | 2,190 / 2,552 | 494 | 0 / 0 | - | 0.099 / 0.064 | 0.30 / 0.24 | 46% / 9% |
| 1 | 1,205 / 1,604 | 250 | 28 / 17 | 84% / 77% | 0.119 / 0.055 | 0.21 / 0.23 | 11% / 24% |
| 4 | 573 / 700 | 53 | 79 / 37 | 89% / 89% | 0.236 / 0.108 | 0.39 / 0.43 | 72% / 82% |

- At 1 the law binds on 77-84% of the cells and takes 17-28 of the light a step (regrowth 108 to 79
  in the summer half). Bodies are 37-45% fewer, the winter low 250 against 494, and the bodies move
  about as much as in the check.
- At 4 the world falls to a quarter and its first winter to 53 bodies (the line is 50). The bodies
  move 1.7-2.4 times as much, carry more muscle (11.9 against 9.6 and 6.6), and learners are 72-82%
  of them; the crowd is thinner (moves blocked 34-48% of the time against 45-55%).
- The batch uses 1, by the rule set before the pilots: the world stands and the law binds at both
  values, 4 only just (one seed, its first winter at 53). The pilot at 4 is kept as a result.

**Batch at 1.** Seeds 9-12, 100,000 steps, eight runs at once on the Mac (8 of 12 cores), 15
minutes (e050's batch: 33; the world is smaller). Means over the second half (steps
50,000-100,000). Pairs are without / with the law on the same seed and brain: the old brain's
runs without it are e048's motor runs, the brain's are e050's brain runs in e048's world. Food
left is the giving-up density under both laws, learners / the rest, over the log rows where each
holds 5% of the bodies or more (4-5 rows of 5).

| seed | brain | moved | travel of grown bodies | learners | food left | bodies | lowest floor | kills' share | diversity |
|---|---|---|---|---|---|---|---|---|---|
| 9 | old | 0.089 / 0.123 | 13.1 / 20.0 | - | - | 1,937 / 1,082 | 422 / 165 | 32% / 34% | 2 / 2 |
| 10 | old | 0.065 / 0.065 | 10.2 / 10.9 | - | - | 2,085 / 1,484 | 558 / 236 | 4% / 8% | 2 / 1 |
| 11 | old | 0.059 / 0.059 | 13.5 / 9.3 | - | - | 2,693 / 1,768 | 742 / 365 | 10% / 8% | 1 / 1 |
| 12 | old | 0.075 / 0.073 | 29.2 / 10.4 | - | - | 2,004 / 1,750 | 347 / 329 | 34% / 10% | 1 / 1 |
| 9 | brain | 0.093 / 0.084 | 7.8 / 12.0 | 7% / 9% | 1.22 / 1.18 | 2,047 / 1,361 | 494 / 229 | 34% / 28% | 1 / 2 |
| 10 | brain | 0.066 / 0.129 | 13.5 / 17.6 | 31% / 35% | 1.13 / 1.14 | 2,199 / 1,318 | 520 / 133 | 26% / 29% | 2 / 1 |
| 11 | brain | 0.075 / 0.056 | 22.6 / 24.3 | 95% / 67% | 1.47 / 0.98 | 2,620 / 1,528 | 220 / 151 | 27% / 22% | 2 / 2 |
| 12 | brain | 0.067 / 0.062 | 26.6 / 11.3 | 59% / 12% | 1.70 / 1.62 | 2,473 / 1,716 | 304 / 274 | 24% / 11% | 2 / 2 |

- **The law binds and the world is poorer.** It takes 16-27 of the light a step, 70-84% of the
  cells stand below the knee, the plant grows 49-56 a step against 73-78, and the intake from trees
  is 43-49 against 59-65. Bodies are 13-44% fewer under the old brain and 31-42% under the brain;
  winter lows 133-365 against 220-742.
- **Bodies do not go farther.** Under the old brain, moving is up on seed 9 (a hunter world whose
  leading body grew to 33 blocks with 13 muscle) and within 4% elsewhere; the travel of grown
  bodies is up on seeds 9 and 10 and down on 11 and 12.
- **Learning is not selected.** Learners are above half on seed 11 only, and above the brain alone's
  on seeds 9 and 10, by 2-4 points.
- **Learners leave more food, on one seed clearly.** The learners' giving-up density is above the
  rest's on seeds 9, 11 and 12 (by 3%, 50% and 5%), and they leave a cell more often on 9-11. The
  clear gap is seed 11, where the learners are its hunters: the two lineages that learn fastest
  (eta 0.07) take 68-72% of their food from flesh.
- **Learning rides on the hunters.** In e048's world, with and without this law, 5 of the 6
  lineages (50 bodies or more at step 100,000) with eta 0.03 or more take 51-72% of their food from
  flesh (e050's seeds 11 and 12, this batch's seed 11), against 6 of the other 31 lineages. Under
  e050's band + thirst no lineage learns that fast.
- Hunter worlds 1 of 4 under the law with the old brain (e048: 2), 3 of 4 with the brain (e050:
  2). Diversity 1-2, as before.

**Batch at 4.** Seeds 9-12, 100,000 steps, eight runs at once, 12 minutes. The same layout.

| seed | brain | moved | travel of grown bodies | learners | food left | bodies | lowest floor | kills' share | diversity |
|---|---|---|---|---|---|---|---|---|---|
| 9 | old | 0.089 / 0.122 | 13.1 / 18.7 | - | - | 1,937 / 799 | 422 / 47 | 32% / 12% | 2 / 1 |
| 10 | old | 0.065 / 0.075 | 10.2 / 15.3 | - | - | 2,085 / 745 | 558 / 99 | 4% / 10% | 2 / 1 |
| 11 | old | 0.059 / 0.107 | 13.5 / 15.8 | - | - | 2,693 / 1,067 | 742 / 47 | 10% / 26% | 1 / 1 |
| 12 | old | 0.075 / 0.084 | 29.2 / 17.8 | - | - | 2,004 / 913 | 347 / 85 | 34% / 18% | 1 / 1 |
| 9 | brain | 0.093 / 0.117 | 7.8 / 28.0 | 7% / 1% | - | 2,047 / 490 | 494 / 53 | 34% / 29% | 1 / 2 |
| 10 | brain | 0.066 / 0.155 | 13.5 / 20.8 | 31% / 4% | 0.90 / 0.94 | 2,199 / 653 | 520 / 85 | 26% / 28% | 2 / 2 |
| 11 | brain | 0.075 / 0.080 | 22.6 / 16.6 | 95% / 4% | - | 2,620 / 1,006 | 220 / 61 | 27% / 16% | 2 / 1 |
| 12 | brain | 0.067 / 0.144 | 26.6 / 14.2 | 59% / 16% | 1.76 / 1.58 | 2,473 / 908 | 304 / 117 | 24% / 33% | 2 / 1 |

- **The growth falls by 60%.** The law takes 47-59 of the light a step, 83-91% of the cells
  stand below the knee, and the plant grows 28-32 a step against 73-78. Bodies are 36-46% of the
  runs without it under the old brain and 24-38% under the brain. Every world's first winter is
  its lowest: 47-117, two below the line of 50 (seeds 9 and 11, old brain); none dies.
- **Bodies go farther.** Moving is 1.11-1.82 times the run without the law under the old brain
  (1.06-2.35 under the brain), and grown bodies stand farther from their birthplace on three seeds
  of four (15.3-18.7 cells against 10.2-13.5; seed 12: 17.8 against 29.2). Speed is not selected
  (0.17-0.22 against 0.16-0.25), and the crowd is thinner: moves are blocked 29-41% of the time
  against 36-58%.
- **Learning is not selected.** Learners end at 1-16% on every seed (the brain alone: 7-95%). The
  pilot's 72-82% on seed 9 was the start's: the same run falls to 1% in the second half.
- **Food left.** Learners hold 5% of the bodies over enough rows on two seeds only (0.90 against
  0.94; 1.76 against 1.58).
- Hunter worlds 0 of 4 with the old brain, 3 of 4 with the brain. Diversity 1-2.

## Conclusion

The answers hold under the conditions of these runs (see "What these runs can and cannot say").

1. **Bodies go farther under the law: no at 1, yes at 4.** At 1 moving is within 4% of the runs
   without it on three seeds and grown bodies travel farther on two; at 4 moving is 1.11-1.82
   times, and grown bodies travel farther on three, in a world of 24-46% of the bodies.
2. **Learning is selected where the place worsens: no.** Learners are above half on one run of
   eight (knee 1, seed 11), and at 1-16% at knee 4.
3. **Learners leave sooner: narrowly, at 1.** Their giving-up density is above the rest's on three
   seeds of four, by 3%, 50% and 5%; the 50% is seed 11, whose learners are hunters. At 4 learners
   are too few to compare (two seeds, one each way).
4. **The world stands: yes at 1, no at 4.** Lowest winters 133-365 at 1; 47-117 at 4, two below 50
   (none dies).

**Not kept as the default**; `stock` stays as the argument 37. This is a decision about the
default world, not a verdict on the law.

**What these runs can and cannot say.** The answers hang on conditions we chose: the world's food
is its standing trees (77-81% of the plant eaten); the law is a knee on the light a cell uses; the
reward is one step's energy balance; two knees; four seeds of 100,000 steps; and at 4 a thinner
crowd we did not control for. Change any of them and the answers may change. The runs do not show
that a worsening place gives no reason to leave, nor that a brain is not needed.

What this changes:

- **A slow return worsens a place for the next visitor, not for the one who stays.** A body eats
  down the cell under it whatever the law, since a held cell does not grow; the law only sets how
  fast the cell comes back once the body has left. At 1 that is a tax on the ground between the
  trees; at 4 it thins the world until the crowd has room to move. Leaving pays a body when its own
  place worsens and other places do not; a slow return lowers every grazed place alike.
- **Moving follows a thinner crowd.** At 4 bodies move more with no more muscle, where their moves
  are blocked less often. A control with the same number of bodies and no law (a weaker sun, say)
  would separate the two; it was not run.
- **Learning rides on hunters.** Where learning is kept in e048's world (knee 1, seed 11 here;
  e050's seeds 11 and 12), the lineages that learn fastest take 51-72% of their food from flesh. A
  hunter's intake jumps with each kill; a grazer's food barely changes within its life. A brain may
  need a world where the food runs more than one where the grass is slow.
- **Next**: #55, life history, as planned: a body must live long enough to follow a change itself
  (e049). Open from here: a worsening that falls on the stayer (fouling: the waste a body leaves
  spoils its own place), and the density control for the knee at 4.
- **Compute**: the new measure reads a few cells per body a step. The batches took 15 and 12
  minutes (e050's: 33), the worlds being smaller.
