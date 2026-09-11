# e047 Corners hold

Date: 2026-09-11

## Purpose

Since e045 (#48) a body is the largest part its blocks make through their sides; a block that
touches the rest only at a corner is not built, or falls off. A body in pieces was wrong, but the
user (2026-09-11) finds the bodies all squares and rectangles, and asks that a corner hold too
(#50). The rectangles came before the law (e044's winners filled 4x4 grids or an 8x8 band), and the
law cut few births (0.6-4.4% on five seeds, 12% on seed 11), so this experiment asks what the
joining rule does to the shapes at all.

## Hypothesis

1. **The cut at birth nearly vanishes.** Under 1% of the births are cut on at least five seeds.
2. **Shapes hardly change.** Every block's work pays best packed (a gut eats the cell under it,
   muscle pushes by the line, hard is harder when contiguous, a body pays 0.032 a step for being
   one), so nothing pays for a shape that reaches out: under 5% of the living bodies are joined
   through a corner anywhere, and the winners still fill their grids.
3. **The world stands.** Bodies and winter floors within 15% of the control's; the hunter world on
   3-5 of 6 seeds (4 in the control).

## Method

Code: e046 (`experiments/e046_yield`) as `e047_corner`, `plant_yield` 1 (e046 did not keep it), and
one choice more for an existing argument, off by default:

- **`connect`** (argument 42) **2**: blocks that touch at a corner join too (8 neighbors). At birth
  only the largest part so joined is built; after a break or a worn block a body keeps its largest
  part so joined and the rest falls as dead matter, as under `connect` 1 (e045). `connect` 1 stays
  the default (e046 byte for byte but a new log column).
- **Log**: `cornered`, the share of the living bodies that are one part through their corners but
  more than one through their sides (0 under `connect` 1). `split` and `outside` count parts under
  the joining rule in force.
- **Checked**: `connect` 1 repeats e045's connect run on seed 9 in every output but the new column,
  the timing column and the parameter line. A unit test: a block touching the rest at a corner is
  kept under `connect` 2 and cut under 1.

**Runs.** e045's season world, 100,000 steps (five winters), one thread each, seven at once on the
Mac (7 of 12 cores, about 16 minutes):

| run | connect | seeds | question |
|---|---|---|---|
| control (e045's connect runs, already run) | 1 | 9-14 | the baseline |
| check | 1 | 9 | byte for byte with e045 |
| corners | 2 | 9-14 | the cut (1), the shapes (2), the world (3) |

Six seeds because the seed picks the world's state (e045) and a winner changes with the state.

Run from the repo root: `bash experiments/e047_corner/run.sh <connect> <threads> <steps> <seeds>`.

**Measures** (over the second half). The births cut and the blocks not built; `cornered`; the
winners of the last third and their shapes; bodies, winter floors; the kills' share of the intake
(the state); diversity (#42).

**Compute.** The walk over a body's grid (at most 256 cells) looks at 8 neighbors instead of 4:
well under a percent of a step's cost.

## Result

**The runs.** Seeds 9-14, 100,000 steps, seven runs at once on the Mac (7 of 12 cores), about 16
minutes. `connect` 1 on seed 9 is e045's connect run byte for byte: every output file identical but
the new column, the timing column of the log and the `"plant_yield":1` of the parameter line.

Means over the second half (steps 50,000-100,000); each pair is sides (e045) / corners hold:

| seed | births cut | cornered | state | kills' share | bodies | lowest floor | diversity | top lineage of the last third, corners |
|---|---|---|---|---|---|---|---|---|
| 9 | 3.4% / 4.9% | 6.8% | hunter / hunter | 35% / 31% | 2,114 / 2,464 | 425 / 505 | 3 / 2 | 63: 11 cells, 1 muscle, 10 gut, 13% flesh; 57% |
| 10 | 0.9% / 0.6% | 7.3% | grazer / grazer | 16% / 13% | 2,089 / 2,131 | 493 / 537 | 2 / 1 | 4: 14 cells, gut only, 9% flesh; 19% |
| 11 | 12.1% / 41.1% | 6.1% | hunter / hunter | 30% / 32% | 2,563 / 1,976 | 590 / 512 | 2 / 2 | 169: 25 cells, 10 muscle, 8 gut, 66% flesh; 53% |
| 12 | 0.6% / 4.1% | 1.9% | hunter / hunter | 37% / 40% | 2,272 / 2,392 | 345 / 420 | 2 / 2 | 36: 15 cells, gut only, 11% flesh; 48% |
| 13 | 4.4% / 2.0% | 4.2% | grazer / grazer | 17% / 30% | 2,249 / 2,489 | 447 / 478 | 2 / 2 | 1: 11 cells, gut only, 6% flesh; 51% |
| 14 | 3.5% / 10.4% | 4.1% | hunter / hunter | 36% / 39% | 2,185 / 3,069 | 555 / 597 | 2 / 3 | 236: 11 cells, gut only, 10% flesh; 44% |

(The state by the blocks broken per body per step, over 0.03 a hunter world; under the law seed 9
is at 0.036 and seed 13 at 0.029, both with kills near 30% of the intake.)

- **No leading body uses a corner.** The usual grown body of each of the top five lineages on every
  seed (30 lineages) is joined through its sides. 1.9-7.3% of the living bodies hold together
  through a corner somewhere: rarer bodies, or bodies that lost a block and stayed in one piece.
- **The cut at birth follows the winner.** 0.6-10.4% of the births on five seeds and 41% on seed 11
  (1.4 blocks not built per birth), against 0.6-4.4% and 12% under the sides rule. Blocks not built
  cost the parent nothing, so a genome that writes blocks apart is not selected against under
  either rule.
- **The states do not move.** Hunter worlds on the same four seeds (9, 11, 12, 14). Bodies change
  by -23% to +40% with the winner (2,420 on average against 2,246; seed 14's winner is a gut of
  11 blocks, size p50 8.6, 3,069 bodies). The lowest winter floor is 420.
- **Shapes stay compact.** The winners: a wall of hard over two rows of muscle (seed 11, 66% flesh),
  bands of gut two rows deep, blocks of gut in a corner of the grid. Muscle-free lineages hold
  21-55% of the bodies against 21-47%. Diversity 1-3 against 2-3.

## Conclusion

1. **The cut at birth nearly vanishes: no.** It follows the winning genome (0.6-41%), not the rule.
2. **Shapes hardly change: partly.** 2-7% of the living bodies use a corner (over 5% on three
   seeds), but no leading body does, and the winners are as compact as before.
3. **The world stands: partly.** On six seeds (lowest floor 420), the hunter world on the same four,
   but bodies change by -23% to +40%, outside 15% on three seeds (with the winner, not the rule).

**Kept**: blocks that touch at a corner join from here (`connect` 2 is the next experiment's
default). It is the physics the user asked for and it changes nothing measured.

What this changes:

- **The rectangles are what pays, not the joining rule.** Every block's work pays best packed (a
  gut eats the cell under it, muscle pushes by the line behind a face, hard is harder when
  contiguous, a body pays 0.032 a step for being one). A block that reaches out has no work to do.
  Shapes need blocks whose work depends on where they sit (#52).
- **Compute**: the same as e046 (16 minutes for seven runs at once).
- **Next**: #51 (moving takes a motor), then #14 (a band of rain that crosses the world), #52, #5.
