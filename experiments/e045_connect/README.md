# e045 A body is what holds together

Date: 2026-09-11

## Purpose

A body grows on a grid of side 4-16, and every block its genome writes is part of it, touching or
not: two groups of blocks at the two ends of the grid move, eat and pay as one body. At step
100,000 of e044's wear runs 4-7% of the living bodies are not connected through the sides of their
blocks, and 1% of all blocks lie outside a body's largest connected part. A body whose parts do
not touch is wrong (the user, 2026-09-11). #48 asks for the material's law instead: a block holds
only to the blocks beside it.

## Hypothesis

1. **Little is cut at birth.** Under 10% of the births are cut down, and they lose under 2% of the
   blocks their genomes write.
2. **Fights cut, wear hardly.** The blocks cut off after a break are at least a tenth of the blocks
   broken (29 a step on seed 9, 135 on seed 10, in the control), and more than those cut off after
   wear.
3. **The world stands.** Bodies and winter floors within 15% of the control, the same plan on top (a
   grazer on seed 9, a gut without muscle on seed 10), and the hunted share of the intake within 5
   points of the control's (17% and 36%).

## Method

Code: e044 (`experiments/e044_wear`) as `e045_connect`, with `wear` 3,000 by default and one
argument more, off by default:

- **`connect`** (argument 42). 1: a body is the largest part its blocks make through their sides
  (a corner holds nothing).
  - At birth only that part is built. The rest is not made, and the parent does not pay for it.
  - When a block breaks (a push) or fails (wear) and the body falls into parts, the largest part
    stays the body; every block of the other parts falls as dead matter on the world cell under
    it, with its share of the body's energy and fat, as a broken block that no gut eats does. The
    breaker eats the block it broke (as today), not what falls off.
  - Two parts of the same size: the heavier stays, then the one first in the body's grid order (no
    draw).
- The cut after a push is made once the push's breaks are all done, and after wear once the step's
  failed blocks are all gone.
- **Log**: `split` (the share of the living bodies in more than one part) and `outside` (the share of
  the living blocks outside their body's largest part), both 0 under the law; `born_cut` (the share
  of the births cut down), `not_built` (blocks not built per birth); `cut_break`, `cut_wear` (blocks
  cut off per step after a break and after wear) and `cut_bodies` (bodies cut per step).
- **Checked**: `connect` 0 is e044's wear run byte for byte (seeds 9 and 10). A unit test: a body
  born in two parts keeps the larger, and a break through a bridge drops the part behind it on the
  ground with its matter, energy and fat in full.

**Runs.** e044's season world with `wear` 3,000, seeds 9 and 10, 100,000 steps (five winters), one
thread each, four at once on the Mac (4 of 12 cores, about 15 minutes):

| run | connect | question |
|---|---|---|
| control (e044's wear run, byte for byte) | 0 | the baseline, and the check |
| connect | 1 | how much is cut at birth (1) and in fights (2); does the world stand (3) |

A batch only if the law changes who wins.

Run from the repo root: `bash experiments/e045_connect/run.sh <connect> <threads> <steps> <seeds>`.

**Measures.** The births cut and the blocks not built; the blocks cut off after breaks and after
wear against the blocks broken and worn; what the bodies eat (plant, the flesh of kills, the dead
scavenged); the bodies and the winter floors; births a step; the lineages alive; the top lineage of
the last third; the diversity number (#42); the shape of the winners (cells, extent).

**Compute.** A walk over a body's grid (at most 256 cells) when a new gene list develops, after a
push that breaks a block, after a step in which a block wears out, and once per log for each living
body: well under a percent of a step's cost.

## Result

**The runs.** Seeds 9 and 10, 100,000 steps, four runs at once on the Mac, 15 minutes each.
`connect` 0 is e044's wear run byte for byte on both seeds: every output file identical but the
new log columns, the timing column and the `"connect":0` of the parameter line.

The cut (means over the second half, steps 50,000-100,000; blocks per step; the births are those
with a block):

| run | births cut | blocks written not built | bodies in pieces | blocks outside the largest part | broken | cut off after a break | worn | cut off after wear | bodies cut |
|---|---|---|---|---|---|---|---|---|---|
| control, seed 9 | - | - | 9.9% | 1.6% | 29 | - | 4.71 | - | - |
| connect, seed 9 | 3.4% | 0.37% | 0 | 0 | 124 | 7.65 (6.2% of broken) | 0.27 | 0.11 | 3.20 |
| control, seed 10 | - | - | 5.9% | 0.9% | 135 | - | 0.72 | - | - |
| connect, seed 10 | 0.9% | 0.19% | 0 | 0 | 37 | 1.69 (4.6% of broken) | 3.08 | 1.29 | 1.56 |

The world (bodies and births from `pop.csv` every 1,000 steps, the rest from the log every
10,000; means over the second half; eaten per step: plant, the flesh of kills (the blocks the
eaters broke), the dead scavenged):

| run | winter floors | bodies | births a step | mean age | lineages alive | eaten | kills' share | top lineage of the last third | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|
| control, seed 9 | 475, 547, 564, 587, 613 | 2,376 | 4.1 | 942 | 13.3 | 76, 17, 14 | 16% | 705: 15 cells, 5 muscle, 9 gut, 34% flesh; 32% | 2 of 4 |
| connect, seed 9 | 468, 523, 522, 524, 425 | 2,114 | 8.5 | 403 | 4.2 | 72, 46, 12 | 35% | 865: 23 cells, 8 muscle, 8 gut (7 hard at its peak), 64% flesh; 42% | 3 of 5 |
| control, seed 10 | 446, 540, 642, 641, 668 | 2,425 | 11.6 | 307 | 4.6 | 77, 47, 11 | 35% | 575: 13 cells, no muscle, 13 gut, 9% flesh; 38% | 2 of 5 |
| connect, seed 10 | 592, 521, 493, 540, 552 | 2,089 | 3.8 | 961 | 8.3 | 77, 17, 11 | 16% | 964: 14 cells, 3 muscle, 11 gut, 22% flesh; 42% | 2 of 5 |

**Little is cut at birth.** 3.4% and 0.9% of the births are cut down, and 0.2-0.4% of the blocks
the genomes write are not built. Without the law 6-10% of the living bodies are in pieces (4-15%
at single log steps) and 0.9-1.6% of the blocks lie outside the largest part: most of the pieces
come from damage, not from birth.

**A break rarely cuts; a worn block often does.** A break drops 3.5-8% more blocks than it breaks
at every log step (6.2% and 4.6% over the second half): the blocks a push breaks are on the
surface, and a surface block is rarely the only link between two parts. A worn block can be any
block: wear drops 0.1-0.56 more blocks per block worn (0.42 at every log step of seed 10's second
half, where the bodies get old).

**The two seeds swap states.** All four runs begin in the hunter state (the flesh of kills 29-43%
of the intake over the first 30,000 steps: the ungrazed start, e037). Control seed 9 and connect
seed 10 leave it by step 50,000 and settle as a grazer world (kills 16%, bodies live 940-960 steps
on average, few blocks broken); control seed 10 and connect seed 9 stay in it to the end (kills
35%, 120-135 blocks broken a step, a mean age of 300-400, 8.5-11.6 births a step). The two levels
are the same under both laws (16% and 35%); the law changed which seed takes which.

**Six seeds.** The law changed who wins on both seeds (the Method's rule for a batch), so seeds
11-14 ran under both laws: eight runs at once on the Mac (8 of 12 cores), 16.5 minutes. The
second half:

| seed | kills' share, control / connect | bodies | lowest winter floor | births cut | blocks written not built | cut off per block broken | per block worn | top lineage of the last third, control | connect |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 16% / 35% | 2,376 / 2,114 | 475 / 425 | 3.4% | 0.37% | 6.2% | 0.41 | 705: 15 cells, 5 muscle, 9 gut, 34% flesh; 32% | 865: 23 cells, 8 muscle, 8 gut, 64% flesh; 42% |
| 10 | 35% / 16% | 2,425 / 2,089 | 446 / 493 | 0.9% | 0.19% | 4.6% | 0.42 | 575: 13 cells, 13 gut, 9% flesh; 38% | 964: 14 cells, 3 muscle, 11 gut, 22% flesh; 42% |
| 11 | 38% / 30% | 2,684 / 2,563 | 598 / 590 | 12.1% | 5.21% | 5.8% | 0.34 | 638: 14 cells, 7 muscle, 7 gut, 63% flesh; 35% | 1: 17 cells, 16 gut, 7% flesh; 32% |
| 12 | 41% / 37% | 2,764 / 2,272 | 480 / 345 | 0.6% | 0.13% | 3.0% | 0.11 | 1: 15 cells, 6 muscle, 6 gut, 69% flesh; 64% | 12: 18 cells, 5 muscle, 8 gut, 54% flesh; 79% |
| 13 | 20% / 17% | 2,456 / 2,249 | 480 / 447 | 4.4% | 0.79% | 6.4% | 0.43 | 490: 8 cells, 8 gut, 4% flesh; 31% | 676: 14 cells, 7 muscle, 7 gut, 33% flesh; 48% |
| 14 | 34% / 36% | 2,526 / 2,185 | 481 / 555 | 3.5% | 0.45% | 6.0% | 0.26 | 346: 12 cells, 11 gut, 6% flesh; 48% | 323: 11 cells, 10 gut, 9% flesh; 54% |

- **Two states, picked by the seed.** A hunter world (kills 30-41% of the intake, 110-180 blocks
  broken a step, 8-15 births a step) or a grazer world (kills 16-20%, 27-37 broken, 3.5-4.2
  births). The hunter world holds on 4 of 6 seeds under both laws: seeds 11, 12 and 14 keep it, 13
  stays a grazer world, and only 9 and 10 swap.
- **Fewer bodies on every seed**, 4-18% (2,245 against 2,539 on average, 11%), the four seeds that
  keep their state included.
- **Seed 11's winner writes parts.** Lineage 1, alive from the start, is cut at birth in 12% of
  the births and loses 5.2% of the blocks its genome writes; it still wins under the law.
- Bodies in pieces without the law: 4.3-14.5% of the living. Diversity 2 in every run but connect
  seed 9 (3).

## Conclusion

1. **Little is cut at birth: partly.** On five seeds 0.6-4.4% of the births are cut, losing
   0.1-0.8% of the blocks written; on seed 11, 12.1% and 5.2% (its winner's genome writes parts).
2. **Fights cut, wear hardly: no.** A break drops 3.0-6.4% more blocks than it breaks, not a tenth:
   a push breaks surface blocks, which rarely hold two parts together. A worn block drops 0.11-0.43
   more. The cut after breaks is still the larger on all six seeds (close in the grazer worlds: 1.7
   against 1.3-1.5 a step).
3. **The world stands: partly.** It stands on six seeds (lowest floor 345, seed 12) with 4-18%
   fewer bodies (18% on seed 12, outside the 15%). The hunter world comes on 4 of 6 seeds under both
   laws; the plan on top is the same kind on seeds 12 and 14 and changes on the other four.

**Kept**: a body is what holds together from here, `connect` 1 (the next experiment's default; it
defaults to 0 in this binary, e044's wear run byte for byte). The law is the material's, the world
stands, and the odds of the hunter world do not move.

What this changes:

- **The season world has two states** after the ungrazed start, and the seed picks one (4 of 6 a
  hunter world). A law meant to change predation (#49) has to be judged by how many of six seeds
  settle as a hunter world and by the kills' share within each state, not by one seed.
- **e045's connect runs on seeds 9-14 are the next experiment's control.**
- **Open**: why the law costs 4-18% of the bodies (one reading: a body in pieces spread its gut over
  more ground; not measured).
- **Compute**: the runs of seeds 9 and 10 took about 15 minutes with or without the law.
- **Next**: #49 (plant matter harder to digest than flesh), then #14 (the regions, with #38 as its
  first pilot), then #5.
