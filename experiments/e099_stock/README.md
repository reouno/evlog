# e099: the rejected laws, re-read by today's measure (#112)

Date: 2026-09-21

**No runs.** This reads censuses already on disk, with the classifier every reading since e068 goes
through (`analysis/`, `e060_census/census.py`, `e068_kinds/kinds.py`).

## Purpose

Thirteen single laws in a row were rejected and only a set was ever kept (e072). The user's premise:
diversity presupposes a world in which **many optima exist and many combinations of traits reach a
similar one**, so stacking only laws whose effect is already visible cannot get there. That makes the
default wrong: a law that did no harm should stay in, because it widens the space the next law meets.

Two facts make this more than a preference. **e094 (#106) threw away the measure several of those
verdicts used** (`kinds held at every census`, an artefact of a 65-fold AND). And **the control ladder
of six seeds of one world spreads 1.02 kinds at a census and 1.24 kinds kept to a place** (e092), so a
difference inside that spread was never readable, whatever the verdict said. There is a precedent:
e066's dry air was "not kept" and `dry` is 0.004 in the default world to this day, because e067 needed
it.

## Hypothesis

Several rejections are inside the ladder's spread - unreadable, not harmful - and a few of them were
rejected in the same breath as a law that did harm.

## Method

`read.py` (from the repo root: `uv run python experiments/e099_stock/read.py`; three minutes on one
core). For each law: its own experiment's control run and its run, over the second half of each run's
censuses, read for **kinds at a census**, **kinds kept to a place** and the largest kind's share. The
censuses on disk are compressed, so they are unpacked into a scratch directory first. What each
reading used is in `results/provenance.csv`; every number below is from `results/stock.csv`.

Where the numbers reproduce a published table they agree to the digit (e080: 7.00 -> 5.84, 4.32 ->
3.72). e069's censuses predate e072's `wood` column, which is why the reader calls `kinds.py`
directly instead of e075's `read_run`.

## Result

Read against each law's own control, seed by seed. **The line is the ladder's spread**: 1.02 kinds at
a census, 1.24 kept to a place.

| law | parameter today | kinds at a census, by seed | kept to a place | reading |
|---|---|---|---|---|
| e078 the crown's shade (2.5/2.5) | `shade_heat` `shade_dry` | +0.04 | -0.40 | **unreadable** |
| e078 the same at 5/5 | | +0.20 | -0.04 | **unreadable** |
| e079 the crown's ground, wood's rest | `crown_wet` `wood_rest` | -0.08 | -0.12 | **unreadable** |
| e093 the light block | not carried | -0.51 (6 seeds) | -0.62 | **unreadable** ("no harm", its README) |
| e095 the spike and the leg | not carried | -0.24 (6 seeds) | -0.32 | **unreadable** |
| e081 the body's water in the land's | `unit` | -0.12, **-2.06**, -0.31 | -1.02, -0.20, -0.24 | one seed beyond |
| e082 fresh water at 0.2 | `fresh` | -0.43, -0.06, **-1.14** | +0.29, **-1.24**, **-1.29** | one seed beyond, both measures |
| e087 the year and torpor | not carried | +0.61, **-1.04**, -0.55 | -0.88, -0.78, **-2.57** | one seed beyond |
| e096 the shade, its best rung | not carried | -0.71 (6 seeds) | -1.14 | at the line |
| e069 life history from the genome | `history` | **-1.83**, **-1.67**, +0.50 | -1.00, -1.17, +0.33 | **harm** (2 of 3 seeds) |
| e080 the crown's cooling | `crown_cool` | **-1.16** | -0.60 | **harm** |
| e097 the birth rule widened | `reach` `ring` | **-2.04** (6 seeds) | -1.62 | **harm** |

**Three laws were thrown out with a fourth that did the harm.** e079's `crown_wet` and `wood_rest`
move the measure by -0.08 and -0.12 - nothing - and were rejected as part of "S1-S3" because
`crown_cool` (S3) costs 1.16 kinds. e078's shade, tested at four rates, never moves it either.

**The verdicts that used the discarded measure survive their re-reading, except e069's.** e069's
`history` costs 1.7-1.8 kinds on two seeds of three: the old verdict was right for a new reason.

**What "unreadable" does not mean.** e081's water changes the world plainly (a body's water is
conserved with the land's, travel falls, the lawn gains in spring) while moving the measure by less
than the seed does. A law can be a real addition to the world and still be unreadable by a count of
kinds - which is the whole of the user's point.

## Conclusion

**Five laws were rejected for a difference smaller than the difference between two seeds of the same
world**: e078's shade (both rates), e079's crown ground and wood rest, e093's light block, e095's
spike and leg. Three harmed the measure and stay out: e069's life history, e080's crown cooling,
e097's widened birth rule. Four are borderline on one seed of three: e081's water, e082's fresh
water, e087's torpor, e096's shade.

What this changes: the rule in `principles.md` (a law that does no harm is kept), the default world in
`foundation.md`, and the control ladder, which has to be re-run on whatever the new default world is
because every later judgement is read against it. The list itself is the user's decision (#112) - this
document only sorts the evidence.

Open: the borderline four cannot be settled by three seeds against a six-seed spread. Each is better
decided by what it adds to the world than by a count it cannot move - the same reasoning that put
`dry` 0.004 in the world after e066 rejected it.
