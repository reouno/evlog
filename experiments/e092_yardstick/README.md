# e092: the yardstick (#102)

Date: 2026-09-20

## Purpose

Ten laws have been proposed since e075 and none was kept (e077-e082, e087, e089, e090, e091). Each was read on
three seeds against e081's control ladder, with a done-when of "+1 kind at a census on every seed" - and the
control's own count spreads 1.02 kinds over those three seeds, while the effects we reject spread more than
that (e091: -0.61, -1.69, +0.04). So "the law did nothing" and "the measure cannot see it" read the same.

This experiment widens the control ladder to six seeds and fixes what a stage C step is read against. It adds
no law: the crate is e091's, run with `crown_at` 0, which is the default world of `foundation.md`.

## Hypothesis

1. This crate at `crown_at` 0 reproduces e081's control exactly (seed 9, column for column).
2. The control's own spread over six seeds is wide enough to explain the effects rejected since e075 - that is,
   a single seed's count is worth about a kind either way, so a step must be read as a distribution.

## Method

Four runs at once, one thread each, 100,000 steps, a census every 1,000 steps from 36,000, c1225 with e062's
draw d11 and the trade-offs `foundation.md` marks kept (e072's sets at #88's rates, `wood_yield` 3e-5,
`wood_hard` 3, `flesh_bite` 0.4, `frail` 0.5, `fresh` 0.05, `unit` 0, `day_temp` 0):

- **seeds 12, 13, 14**: the three runs that widen the ladder from three seeds to six;
- **seed 9**: the check of hypothesis 1 against `experiments/e081_drink/results/ladder/c1225_life9_u0`.

    cargo build --release -p e092_yardstick
    (nohup bash experiments/e092_yardstick/batch.sh > experiments/e092_yardstick/results/batch.log 2>&1 < /dev/null &)

Read with `uv run python experiments/e092_yardstick/sweep.py`: for each of the six control runs, kinds at a
census, kinds kept to a place (e068's census by birth form, e075's `read_run`), the largest line's share of the
land's bodies, the kills' share of what bodies eat (the world state, e025/e045/e076), bodies and travel. Then
the median and spread of each over the six seeds, and the same numbers for the effects rejected since e075.

Cost: 4 cores for about 1.5 hours on the Mac, once.

## Result

The four runs took 3,131-4,379 s each (52-73 minutes, four at once on the Mac). The ladder, one row a run,
over the second half of each (`results/ladder.csv`, read by `sweep.py`):

| seed | kinds at a census | kept to a place | held at every census | largest kind | largest line | kills | bodies | travel | blocked | no room |
|---|---|---|---|---|---|---|---|---|---|---|
| 9 | 7.45 | 4.75 | 1 | 15% | 58% | 28% | 9,442 | 5.8 | 49% | 49% |
| 10 | 8.27 | 4.65 | 1 | 15% | 63% | 25% | 8,860 | 4.2 | 51% | 49% |
| 11 | 7.25 | 4.47 | 1 | 17% | 42% | 28% | 8,995 | 6.0 | 49% | 47% |
| 12 | 7.76 | 4.24 | 0 | 14% | 52% | 30% | 7,831 | 4.8 | 45% | 47% |
| 13 | 7.27 | 3.75 | 2 | 16% | 78% | 27% | 8,757 | 5.8 | 44% | 47% |
| 14 | 7.61 | 3.51 | 0 | 13% | 45% | 27% | 8,280 | 4.0 | 45% | 46% |
| **median** | **7.53** | **4.35** | 1 | 15% | 55% | 28% | 8,809 | 5.2 | 47% | 47% |
| **spread** | **1.02** | **1.24** | 2 | 4 pt | 35 pt | 5 pt | 1,611 | 2.0 | 7 pt | 3 pt |

1. **Reproduction.** e092's seed 9 and e081's `u0` agree on all 182 shared log columns over all 100 rows; the
   only columns that differ are the clocks (`ms_*`). e092's crate logs 30 columns e081's has not. The two
   halves of the ladder are one ladder.
2. **The spread.** The count spreads 1.02 kinds over six seeds around a median of 7.53. The three new seeds all
   fall inside the range the first three gave, so 1.02 is the world's own spread, not a shortage of runs. Half
   of a run's own censuses lie 1.0 kinds apart.
3. **The rejected effects.** Of the nine (law - its control) pairs of e089, e090 and e091, five are smaller than
   half the control's spread. Every large one - 2.08, 1.69, 1.51 - is seed 10, the seed whose control counts
   highest of the six. Each law's own three runs spread 0.49-1.20, about as wide as the control's six, so
   pairing by seed adds one draw to the other instead of cancelling it. None of the nine is positive beyond
   0.14, so the direction (down, or nothing) is consistent even where the size is not readable.
4. **The other measures.** Kinds kept to a place spreads 1.24 over six seeds where three suggested 0.27;
   e091's fall of 1.6 clears even that on all three of its seeds. Kinds held at *every* census is 0-2 and
   carries nothing. The largest line's share spreads 35 points (42-78%) and cannot carry an effect either.
5. **What does not move with the seed.** 44-51% of moves blocked and 46-49% of children born with no room -
   nearly half of every birth, against the 24-33% e070 recorded; the kills' share holds within 5 points
   (25-30%).

## Conclusion

Both hypotheses hold. The ladder is six seeds wide, it is kept at
`results/ladder/c1225_life{12,13,14}_ctl` beside e081's `c1225_life{9,10,11}_u0`, and this crate is the one
that reproduces it. The judging changes as #102 asked: a stage C candidate runs on the same six seeds and is
read as a distribution against the control's (median and spread), never as "+1 kind on every seed"; the
effect's spread across seeds is recorded beside the effect; the categorical done-whens (is there a kind led
by the new food, does a form keep to the new place) stay as they are; and a piece meant to replace the world
is judged on its own measures and becomes the new control if it passes.

Changes in `vision.md`: section 3's last paragraph (the judging question is now answered with numbers), the
crowding row of section 2F (nearly half of all births fail for want of room, not 24-33%), and section 5
(#102 done, next is #103). In `foundation.md`, section 3's stage C paragraph and today's default world (the
six-seed ladder and the judging rule), and section 4's compute row.

What this does not settle: whether any of the ten rejected laws would pass on six seeds. #104 re-tests P2's
foods once the crowd is thinner; the others stay rejected under the conditions they were run in.
