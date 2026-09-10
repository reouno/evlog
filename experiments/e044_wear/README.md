# e044 Wear

Date: 2026-09-11

## Purpose

`MAX_AGE` is 3,000: a body dies in the step it passes 3,000, and nothing about it changes before
that. In e043's world (`sat` 1, `hold` 1) this wall matters more than it did: on seed 9, 11% of
the deaths are by age (2% in e042's control), all of them at age 3,001, and the mean age is 921
against 647. Ageing is here for turnover (principle 4). A clock is a law of the world; #47 asks
for a law of the material instead, and its design comment (2026-09-11) settles the law tested
here.

## Hypothesis

1. **The age at death spreads.** Under wear no 50-step bin of age holds more than 2% of the
   deaths of bodies that lived (under the fixed age, 11% die on the one step 3,001, seed 9).
2. **A decline comes before death.** Under wear most deaths past age 2,000 follow a lost block,
   and most of those are by hunger, not by wear: a body that has lost guts cannot pay for what is
   left long before its last block fails.
3. **The world stands and turns over faster.** Bodies and winter floors within 15% of the fixed
   age; more births a step and a lower mean age; the lineages alive and the diversity number at
   least the fixed age's.

## Method

Code: e043 (`experiments/e043_crown`) as `e044_wear`, with `sat` 1 and `hold` 1 by default and
one argument more, off by default:

- **`wear`** (argument 41): a block's median life in steps. Every step each block of a living
  body fails with the chance h(a) = h0 · 2^(a/s), where a is the body's age (every block is made
  at birth), s = wear / 10 (the chance doubles every tenth of the median life, as human
  mortality does) and h0 = (ln 2)² / (s (2^10 − 1)), so that half the blocks of age `wear` have
  failed. A failed block leaves the body and lies on the world cell under it as dead matter, with
  its share of the body's energy and fat, as a broken block no gut eats does: matter is
  conserved. A body dies of wear when no block is left, or of hunger when it cannot pay for what
  is left (`strict`). With `wear` on, `MAX_AGE` does not apply.
- Not heritable (a longer life costs nothing, so selection would only lengthen it), and nothing
  about size is written: a body of more blocks has more to lose.
- At `wear` 3,000 the chance per block per step is 1.6e-6 at birth, 1.6e-4 at age 2,000 and
  1.6e-3 at 3,000. A body of 16 blocks expects its first lost block near age 2,000; a block's
  chance to pass 4,000 is 0.1%.
- Its own random stream, drawn in the order of the bodies. `wear` 0 draws nothing.
- **Log**: `deaths_wear`, `worn` (blocks lost per step), `worn_bodies` (the share of the living
  that have lost a block to wear), `worn_deaths` (the share of the deaths of bodies that lived
  that followed a lost block), `age_p10`, `age_p50`, `age_p90` (the age at death of bodies that
  lived). `agents.csv` gets `worn`. A new `deaths.csv`: every 10,000 steps, the deaths of bodies
  that lived by cause, age (bins of 50 steps) and size at birth (bins of 4 blocks), and how many
  of them had lost a block to wear.
- **Checked**: `wear` 0 is e043's sat + hold run byte for byte (the controls against e043's
  seeds 9 and 10). A unit test: a block lives to the median life with a chance of one half, and a
  worn-out body's matter, energy and fat lie on the ground in full.

**Runs.** e043's season world with `sat` 1 and `hold` 1, seeds 9 and 10, 100,000 steps (five
winters), one thread each, four at once on the Mac (4 of 12 cores, about 15 minutes):

| run | wear | question |
|---|---|---|
| fixed age (e043's sat + hold, byte for byte) | 0 | the baseline |
| wear | 3,000 | does the age at death spread (1); a decline before death (2); does the world stand (3) |

A batch only if wear changes who wins.

Run from the repo root: `bash experiments/e044_wear/run.sh <wear> <threads> <steps> <seeds>`.

**Measures.** The age at death (p10, p50, p90, and the share at 3,001), the share of the deaths
that follow a lost block, the deaths by cause, the bodies and the winter floors, births a step
and the mean age, the lineages alive, the diversity number (#42), the top lineage of the last
third; and whether a body of more blocks lives longer (the age at death by size at birth).

**Compute.** One draw per block per step, about 30,000 a step: a percent or two of a step's
cost. The new columns and `deaths.csv` are counts.

## Result

**The runs.** Seeds 9 and 10, 100,000 steps, four runs at once on the Mac: 11.2 and 14.3 minutes
under the fixed age, 13.0 and 14.7 under wear (seed 9's wear run holds 19% more bodies). The fixed
age is e043's sat + hold run byte for byte on both seeds: every output file identical but the new
columns, the timing column and the `"wear":0` of the parameter line.

The deaths of bodies that lived (born with a block), steps 50,000-100,000 (`deaths.csv`; ages in
bins of 50 steps, so a quantile is good to about 25 steps; "oldest" is the top of the last bin):

| run | deaths | age p10 | p50 | p90 | p99 | oldest | fullest bin | fullest bin past 1,000 | hunger | broken | age | wear | after a worn block | past 2,000 | of those, after a worn block |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed, seed 9 | 156,674 | 53 | 211 | 3,004 | 3,045 | 3,050 | 19.0% (50-100) | 10.9% (3,000) | 69% | 20% | 10.9% | - | - | 12.9% | - |
| wear, seed 9 | 205,045 | 54 | 209 | 1,799 | 3,732 | 4,200 | 17.6% (50-100) | 0.8% (3,550) | 78% | 19% | - | 3.1% | 11.1% | 9.3% | 96%: 61% hunger, 35% wear, 4% broken |
| fixed, seed 10 | 545,172 | 36 | 133 | 480 | 1,469 | 3,050 | 25.6% (50-100) | 0.2% (1,000) | 73% | 27% | 0.2% | - | - | 0.5% | - |
| wear, seed 10 | 564,717 | 40 | 133 | 456 | 1,353 | 4,050 | 26.2% (50-100) | 0.2% (1,000) | 72% | 28% | - | 0.03% | 1.5% | 0.5% | 93%: 90% hunger, 7% wear, 3% broken |

The world (bodies, births and the mean age of the living from `pop.csv` every 1,000 steps, the
rest from the log every 10,000; means over the second half; the lineages alive are confirmed
lineages of 5 or more):

| run | winter floors | bodies | births a step | mean age | lineages alive | blocks worn a step | living with a worn block | eaten a step | muscle | top lineage of the last third | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed, seed 9 | 685, 588, 535, 573, 491 | 1,996 | 3.2 | 921 | 4.5 | - | - | 102 | 3.52 | 253: 16 cells, 5 muscle, 10 gut, 29% flesh; 61% | 3 of 3 |
| wear, seed 9 | 475, 547, 564, 587, 613 | 2,376 | 4.1 | 942 | 13.3 | 4.7 | 20% | 106 | 4.17 | 705: 15 cells, 5 muscle, 9 gut, 34% flesh; 32% | 2 of 4 |
| fixed, seed 10 | 446, 539, 482, 435, 509 | 2,418 | 11.1 | 425 | 4.6 | - | - | 144 | 4.67 | 801: 16 gut, no muscle, 8% flesh; 69% | 3 of 3 |
| wear, seed 10 | 446, 540, 642, 641, 668 | 2,425 | 11.6 | 307 | 4.6 | 0.7 | 3.2% | 136 | 4.86 | 575: 13 gut, no muscle, 9% flesh; 38% | 2 of 5 |

**The wall is gone.** Under the fixed age 12.9% of seed 9's bodies reach age 2,000, and those
still alive at 3,000 all die on the next step: 10.9% of the deaths fall in the one bin. Under
wear the old die between 2,000 and 4,200 and no bin past age 1,000 holds more than 0.8%; p90 falls
from 3,004 to 1,799 and p99 rises from 3,045 to 3,732.

**Hypothesis 1 was written badly.** Most deaths are of the newborn: the bin of ages 50-100 holds
18-26% of the deaths in all four runs, so "no bin above 2%" fails under both laws. The criterion
was meant for the pile of the old, and the column "past 1,000" is that.

**The old decline.** At step 100,000, 202 of the 220 bodies of age 2,000 or more on seed 9 (92%)
had lost blocks to wear, 5.0 on average (seed 10: 20 of 25, 6.9). Of the deaths past 2,000, 96%
followed a worn block; 61% of those were by hunger (the body could not pay for what was left), 35%
by wear (the last block failed) and 4% by another body.

**Where the bodies get old, the world turns over faster.** Seed 9's winner is a grazer whose
bodies live past 1,000 steps (the mean age of lineage 253 is 1,225 at its peak). Under wear the
same plan wins in a new lineage (705) with 32% of the last third against 61%; births rise from 3.2
to 4.1 a step and the bodies from 1,996 to 2,376 on as much food (106 a step against 102). The
lineages alive swing with the season: every 5,000 steps 5-34 under wear, peaking at the end of
each summer (21, 25, 34 at steps 50,000, 70,000, 90,000), against 2-10.

**Where they do not, wear is a detail.** On seed 10 the median death comes at 133 steps and the
p90 at 456-480; wear touches 1.5% of the deaths. The two runs differ as two paths of one world do
after the first worn block: the floors of the last three winters are 641-668 against 435-509, and
the same plan (a gut of 13-16 cells without muscle) wins with 38% against 69%, beside a hunter
(lineage 438: 7 muscle, 4-5 sensors, 4 gut, 81% flesh, 30,000-100,000).

**Diversity.** The number of #42 falls from 3 to 2 on both seeds, with more winners (4 and 5
against 3): the lineages that share the winner's place under wear share its shape or the sitter's.

**Size.** Whether a body of more blocks lives longer cannot be read here: on seed 9 the bodies
that reach age 2,000 are the 16-block grazer's (12-17% of the 16-block deaths reach it, 1-8% of
every other size, under both laws), a lineage, not a size.

## Conclusion

1. **The age at death spreads: partly.** As written no (the newborns fill the youngest bins,
   18-26%, in every run). The pile it meant is gone: past age 1,000 no bin holds more than 0.8%
   under wear, against 10.9% at 3,001, and the oldest die at 4,200 instead of 3,001.
2. **A decline comes before death: yes.** 96% of the deaths past 2,000 on seed 9 follow a worn
   block (93% on seed 10), and 61% of those are by hunger, 35% by wear.
3. **The world stands and turns over faster: partly.** The world stands on both seeds (lowest
   floors 475 and 446 against 491 and 435). On seed 9 births rise 31%, the bodies 19% and the
   lineages alive threefold, but the mean age of the living does not fall (942 against 921), and
   the diversity number drops from 3 to 2 on both seeds.

**Kept**: the season world ages by wear from here, `wear` 3,000 (the next experiment's default;
it defaults to 0 in this binary, e043 byte for byte), and `MAX_AGE` no longer applies. A body ages
by losing blocks and dies of what it can no longer pay for; the law is the material's, not a
clock's. No batch: the Method's rule was a batch if wear changes who wins, and on both seeds the
same plan wins (a grazer on seed 9, a gut without muscle on seed 10).

What this changes:

- **Turnover where bodies get old.** On seed 9 the long-lived winner no longer holds the world
  for its whole life: its share of the last third halves and more lineages come and go beside
  it. One seed: a reading, to watch in the next runs.
- **Numbers set against a life of 3,000** (the weather's span, e040's drying rate) still hold: the
  old die between 2,000 and 4,200.
- **Compute.** The wear runs took 3-16% longer, as many more bodies as they held.
- **Open.** Whether size buys a longer life, in a world where more than one plan gets old.
- **Next**: #38 (the rain on the ridge under the water carrier), then #5.
