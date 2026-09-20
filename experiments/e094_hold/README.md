# e094: why no way of living lasts (#106)

Date: 2026-09-21

**No runs.** This reads the twelve censuses we already have: the six-seed control ladder (e081's seeds 9-11,
e092's 12-14) and e093's six at `light_gain` 0.016.

## Purpose

Stage C's pass line (#76) asks for four kinds holding 5% of the grown bodies for five years on four of six
seeds. The six-seed ladder reads **7.53 kinds at a census** and **0-2 held at every census** (median 1). Every
piece since e073 has been judged on the first number and none moved it; the second is the number the pass line
is written against. Before spending another batch we should know which of three things the 1 means, because
each asks for a different kind of work:

- the ways of living **turn over** - a kind is driven out and another takes its place (a law is missing);
- the ways of living **flicker** - the same forms cross the 5% line and come back (the line is the problem);
- the count is **noise** - too few bodies to read a 5% share (the census is the problem).

## Hypothesis

Most stretches end without an extinction: the forms that made the kind are still in the world at the next
census, and the kind comes back. The count at a census is not noise. The 1 is a conjunction over 65 censuses,
not a statement about stability.

## Method

e068's reading is kept exactly, so the numbers are comparable with every experiment since: a grown body's form
is (lineage, birth signature); a form's way of living is read over all its grown bodies in the run, so a way's
label never moves; a kind is a way holding 5% of the grown bodies at a census. Over the second half of each run
(censuses every 1,000 steps from 36,000 to 100,000, 65 of them, 5.4 years at a year of 11,880):

- **How long a way holds the line**: the maximal stretches of consecutive censuses, in censuses, steps, years
  and grown lifetimes (535 steps, e087). The same for a single birth form.
- **What ends a stretch**: at the census after it, how many of the way's forms are still in the world and how
  many of their bodies are left. `forms gone` when under a fifth is left, `under the line` otherwise. And
  whether the way comes back later.
- **How far a share swings**: the standard deviation of a way's share over its mean, and how much of that
  swing lies between the four quarters of the year (is the swing the season?).
- **The null**: each census's grown bodies resampled from its own composition, 20 draws, recounted. This is
  what the measure makes on its own when the world does not change.
- **Other lines**: the same counts at 3% and 10%, and "held in 90% of the censuses" instead of every one.
- **Against the largest lineage**: how often it changes, and how many stretch-ends fall on a change.

`uv run python experiments/e094_hold/hold.py` (about ten minutes on one core; the censuses are restored from
`tidy.py`'s archives first and compressed again afterwards). Writes `results/holds.csv` (a row a run),
`results/census.csv`, `results/spells.csv` and `results/events.csv`.

**Stop early if:** not applicable - no runs.

## Result

Medians over the twelve runs (control and light read alike; they differ nowhere that matters here):

| measure | control | light | all |
|---|---|---|---|
| kinds at a census | 7.53 | 7.02 | 7.26 |
| held at every census | 1.0 | 1.0 | **1.0** |
| ways that ever hold the line | 16 | 19 | 16 |
| ways at 5% of the grown bodies **in the mean** | 9.0 | 7.0 | **8.0** |
| censuses a way holds the line (median / p90) | 2 / 12 | 2 / 12 | **2 / 12** |
| censuses a form holds it (median) | 1 | 1 | 1 |
| kinds at a census, resampled (the null) | 7.51 | 7.03 | 7.26 |
| held at every census, resampled | 1.2 | 0.9 | **1.0** |
| kinds at a census / held, line 3% | 10.10 / 3.0 | 9.89 / 3.0 | 9.91 / 3.0 |
| kinds at a census / held, line 10% | 3.23 / 0.0 | 2.81 / 0.0 | 3.01 / 0.0 |
| held in 90% of the censuses, line 5% / 3% | 3.0 / 5.5 | 3.5 / 5.0 | **3.0 / 5.0** |
| a way's share: sd over mean | 0.59 | 0.65 | **0.61** |
| of that swing, what the year explains | 0.09 | 0.14 | **0.10** |
| changes of the largest lineage over 65 censuses | 13 | 10 | 10 |

**It flickers.** Over the twelve runs a stretch at the line ends 751 times. **609 of them (81%) end with the
way's forms still in the world** and only their share under 5%; 142 (19%) lose their forms. **632 (84%) come
back to the line later.** Only 187 (25%) fall on a census where the largest lineage changed.

**A stretch is short**: 2,000 steps at the median - 0.17 of a year, four grown lifetimes - with a p90 of 12
censuses. A single birth form holds the line for one census at the median. Per run, 17 ways cross the line, in
3.5 stretches each, and a way stands over it for 17.5 of the 65 censuses at the median (p90 50). **In no run is
any way over the line in as many as 59 of the 65 censuses**, which is what "held" asks for at every one.

**The count is not noise.** Resampling each census's grown bodies from its own composition gives 7.26 kinds at
a census and 1.0 held, the same numbers. The 5% share is read off 2,000-4,000 grown bodies; the swing is in the
world, not in the sample.

**The swing is not the season either.** A way's share swings by 61% of its own size, and the four quarters of
the year explain a tenth of it.

**The line and the conjunction are what make the 1.** The world holds **8 ways at 5% in the mean** and 16-19
ever reach it. Asking for 5% at *every one of 65* censuses leaves 1. Asking for 5% in 90% of them leaves 3; at
a 3% line, 5. At a 10% line nothing is held at all and only 3.0 kinds stand at a census.

## Conclusion

**The ways of living do not turn over; the measure turns them off.** `kinds_held` is a conjunction over 65
censuses of a share that swings by 61% of its own size, so it reports 1 for a world that holds 8 ways in the
mean and never loses them - four fifths of the losses are a share dipping under the line, and five sixths come
back. It is a measure, not a property, and no law will move it.

What this changes:

- **The pass line (#76) has to be re-read.** "Four kinds at 5% for five years" was scored as every census. The
  same world scores 3 at "in 90% of the censuses" and 5 at a 3% line. Stage C is at or near its first pass line
  already; it was not, on the number we were quoting.
- **`foundation.md`'s stage C measures**: `kinds_held` is dropped and replaced by the two that are not
  conjunctions - kinds at a census (7.26 today, the number every piece since e073 was judged on, which stands)
  and **ways at 5% of the grown bodies in the mean** (8.0 today). "Held" survives only as "in 90% of the
  censuses" (3.0).
- **`vision.md` section 2F**: the ways-of-living row gains the mean count and the flicker; the ideal of about
  20 ways is unchanged and still far away.
- **P3's remaining set (#52)**: judged on kinds at a census and on ways in the mean, never on a conjunction.

What it does not change: the world still holds 7.26 ways at a census against an ideal near 20, the largest line
still holds 42-78% of the land's bodies, and nearly half of all births still fail for want of room. The gap is
the same size; one of the two numbers we were reading it with was broken.

Open, and cheap to ask next: a way's share swinging by 61% with the season explaining a tenth of it is either
drift in a finite population or a cycle of its own (predator and prey against each other, `vision.md` 2F).
Nothing here separates them.
