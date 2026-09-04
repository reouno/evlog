# e029 Small and large bodies in one world

Date: 2026-09-05

## Purpose

The user's premise (#28): the real world spans mites to whales, and a world where a tiny
grazer and a large body both exist should be possible. Every body so far grew on an 8x8 grid:
64 cells at most. The winners were 6-10 cells for a long time, but the season world (e026)
has bodies of 57 cells among its winners and a mass at the top of 110-135 in every seed, so
the ceiling is near. This experiment raises it and asks whether the world then holds bodies
of different sizes at once, and whether size is set by the world (its costs, its crowd) or by
the grid a body can grow on.

## Hypothesis

1. **The grid alone is a rescale.** With every body on a 16x16 grid (`side` 16), the same
   genomes make the same shapes at four times the cells, and the world settles at a size in
   cells near e026's (8-21 per body, the 90th percentile of mass 20-71): the size is set by
   the world's costs, not by the grid. The alternative is that the bodies stay four times as
   large and the population falls to a quarter: the size is a fraction of the grid.
2. **The side is selected under `grow`.** With the side expressed by the genome (4 to 16
   around 8), the mean over bodies leaves 8 and the spread over bodies grows past the start's.
3. **Small and large bodies coexist.** In a `grow` world the size in cells at the 90th
   percentile is at least three times the 10th in the second half of a run, and lineages with
   a mean side under 7 and over 10 hold places in the top lineages of one run at the same
   time for 100,000 steps or more (#19: several winners).
4. **The world stands** at e026's population within a factor of two (bigger bodies, fewer of
   them, the same matter).

## Method

Code: e028 (`experiments/e028_gut`) as `e029_size`, with the digestion law off by default
(e028 did not keep it) and argument 20 `side`: a number (every body on that grid; 8 is e028
byte for byte, checked on seed 9 for 20,000 steps: every output file identical but the added
columns and the timing) or `grow`.

**The law.** A body grows on a grid of `side` by `side` cells, 16 at most. The development
is e004's: the six morphogen gradients (x, 1 - x, y, 1 - y, r, 1 - r) span the grid whatever
its side, so a pattern scales with the body it is written on: side 8 is e028's field, side 16
samples the same field at twice the resolution. Under `grow` the genome expresses the side
like the density (#25): a sigmoid of a sum over the genes' products, read from the run
without position, as 8 x 2^(2 sigmoid - 1) rounded, 4 to 16; the table's column for it draws
from its own random stream, so the bodies, the terrain and the weather are e026's at side 8.
Nothing in the world's laws changes: the upkeep is per cell, a block weighs by its kind and
density, a child costs its mass, a gut eats from the world cell under it, a body lies over
the world cells under its cells (up to 5x5 now, 3x3 before). A child is placed within a
grid's side of its parent's anchor (the larger of the two sides; eight sub-cells before).
Development costs side^2 network runs per distinct gene list instead of 64 (cached per list
as before).

**The world.** e026's season world (128x128, matter 8 per cell, the sun a sine of 20,000
steps at amplitude 0.5, the weight and flesh laws, the canopy, the spill, rain on every cell
alike), the world where the eye pays and the winner turns over; the control is e026's four
season runs (this code with `side` 8).

**Runs.** Two pilots on seed 9, 100,000 steps, six threads each at once (`side` 16 and
`grow`), to see that the world stands, what the 16 grid does to the size, and whether the
side moves under `grow`; then the batch: `grow` and `side` 16, seeds 1-4, 500,000 steps, one
thread each, eight at once on the Mac, read against e026's season runs.

Measures: the log's `side_mean`, `side_std`, `size_p10`, `size_p50`, `size_p90`, `size_max`
(cells per body), `size_mean`, the mass quantiles; `lineages.csv` `side` per lineage with its
size, mass, muscle, bite and intake; the winners by #19's rule (holders of the top place and
lineages alive), the kills per step, the population.

Run (from the repo root):

    ./target/release/e029_size 100000 9 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5 0 16
    ./target/release/e029_size 100000 9 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5 0 grow
    bash experiments/e029_size/run.sh grow 500000 1 2 3 4
    bash experiments/e029_size/run.sh 16 500000 1 2 3 4

Cost: two pilots (12 cores for 25 minutes together) and the batch (8 cores for 4.5 hours: the
16 grid's development is four times e026's).

## Result

### The pilots: the grid is not the size

Seed 9, 100,000 steps; ranges over the log steps (every 10,000). The control is e026's season
pilot on seed 9 (this code with `side` 8). Mass is cells by kind times density (a hard cell
weighs 2, a sensor 1/2); "full" is the share of bodies filling their whole grid.

| | e026 (control, side 8) | `grow` | `side` 16 |
|---|---|---|---|
| Bodies | 2,660-4,850 | 2,790-3,130 | 3,310-7,310 |
| Side at the end, mean and spread | 8 | 5.4, 1.2 | 16 |
| Cells per body | 11-20 | 12-16 | 10-17 |
| Mass p10 / p50 / p90 / largest | 4-6 / 12-16 / 23-96 / 128-221 | 5-8 / 16-26 / 32-50 / 96-206 | 4-8 / 8-16 / 12-36 / 81-196 |
| Full grids | 0-5% | 16-44% | 0% |
| Bodies killed a step | 0.9-6.4 | 1.9-3.1 | 0.0-4.3 |
| Bodies with a bite | 0-8% | 0-0.2% | 0-0.1% |
| Bodies with a sensor | 0-1.7% | 0.2-1.3% | 0-7% |
| Lineages alive | 2-8 | 2-15 | 1-9 |
| Wall time, 6 threads | - | 25 min | 25 min |

On the 16 grid the same genomes make bodies of 10-17 cells, the control's size, on a grid of
256: the size is the world's, not the grid's. Under `grow` the side falls from 8 to 5.4 in
10,000 steps and stays, and at 100,000 steps two kinds of body share the world: 1,170 bodies
on side 4 (15 cells filling the grid, density 2, mass 30, 6.7 muscle, speed 0.22) and 1,600 on
side 6-7 (13 cells, 12 of them gut, 0.5 muscle, speed 0.02). Neither is large.

### The batch: four seeds each, 500,000 steps

Medians over the second half unless said; the largest body is the most over the second
half. Wall time per run, one thread: `grow` 1.7-4.2 hours, `side` 16 4.0-4.5, control 1.3-2.5
(development is side^2 network runs per distinct gene list: 256 on the 16 grid).

| | bodies; fewest | side at the end | cells per body; p10 / p50 / p90 / largest | mass p10 / p50 / p90 / largest | full | muscle | killed a step | with a bite | lineages; winners from 250k, longest hold |
|---|---|---|---|---|---|---|---|---|---|
| `grow` seed 1 | 3,980; 3,470 | 8.1, 0.8 | 11.5; 4 / 11 / 17 / 81 | 7 / 17 / 29 / 165 | 0% | 2.5 | 1.11 | 49% | 3; 2, 185,000 |
| `grow` seed 2 | 2,620; 2,230 | 14.3, 2.4 | 14.2; 7 / 13 / 22 / 127 | 10 / 26 / 42 / 254 | 0% | 0.2 | 0.01 | 0% | 16; 7, 19,000 |
| `grow` seed 3 | 2,930; 2,470 | 4.4, 0.8 | 15.0; 10 / 16 / 16 / 100 | 12 / 32 / 32 / 200 | 71% | 3.6 | 1.63 | 0% | 19; 21, 18,000 |
| `grow` seed 4 | 2,480; 2,190 | 5.2, 2.0 | 16.3; 9 / 16 / 24 / 111 | 16 / 32 / 38 / 222 | 51% | 3.8 | 0.80 | 0.4% | 34; 7, 91,000 |
| `side` 16 seed 1 | 3,410; 2,630 | 16 | 14.0; 7 / 14 / 20 / 127 | 12 / 26 / 39 / 153 | 0% | 1.6 | 0.26 | 0% | 3; 2, 19,000 |
| `side` 16 seed 2 | 2,860; 2,170 | 16 | 12.9; 8 / 12 / 18 / 240 | 16 / 24 / 35 / 480 | 0% | 0.6 | 0.03 | 0% | 22; 9, 109,000 |
| `side` 16 seed 3 | 3,970; 2,480 | 16 | 12.5; 5 / 11 / 22 / 135 | 8 / 18 / 34 / 178 | 0% | 1.8 | 0.69 | 46% | 2; 6, 15,000 |
| `side` 16 seed 4 | 2,800; 1,730 | 16 | 14.2; 6 / 14 / 21 / 132 | 12 / 26 / 42 / 222 | 0% | 1.2 | 0.17 | 0% | 8; 13, 134,000 |
| control seed 1 | 4,760; 3,050 | 8 | 8.2; - | 5 / 14 / 20 / 196 | 0% | 1.4 | 1.52 | 37% | 3; 6, 29,000 |
| control seed 2 | 3,880; 3,040 | 8 | 13.4; - | 8 / 22 / 37 / 185 | 0% | 1.7 | 1.31 | 0% | 8; 14, 17,000 |
| control seed 3 | 2,620; 2,230 | 8 | 21.5; - | 5 / 17 / 71 / 145 | 8% | 4.3 | 4.58 | 18% | 2; 1, 251,000 |
| control seed 4 | 2,850; 2,520 | 8 | 12.6; - | 7 / 21 / 32 / 167 | 0% | 2.9 | 1.46 | 45% | 2; 2, 204,000 |

**The side goes where the seed's history takes it, and the size stays.** Under `grow` the
four seeds end at side 4.4, 5.2, 8.1 and 14.3, each with a spread of 0.8-2.4 over its bodies,
while the cells per body are 11-16 in every seed, every `side` 16 run (12.5-14.2) and the
control (8-21). The side sorts the bodies of one seed into its two kinds, which are e026's:
a dense mover (density 2, 3-6 muscle, speed 0.12-0.16) and a light sitting gut (density 1,
no muscle, speed 0.003-0.03, the sensors). Seed 3 and 4 put the mover on side 4 (a full 4x4
block of 14-15 cells) and the gut on side 6-7; seed 1 puts the mover on side 8-9 and the gut
on side 7; seed 2 has only guts, a dense one of 17 cells spread over a 14-16 grid and a light
one with eyes on side 9. At the end of seed 4, 58% of the bodies are on side 4 and 15% on
side 7. In no seed does a lineage of 100 bodies at side 6 or less share a log step with one
at side 10 or more (0 of 251,000 steps in each seed).

**Large bodies are born and die.** The largest bodies of the runs, 100-240 cells (the 240:
all gut, density 2, mass 480, `side` 16 seed 2), are newborns of 8-14 steps; bodies of 50
cells or more are 0.3-0.6% of the bodies at any dump, and the 90th percentile of cells is
16-24 in every run. No lineage is large.

**The 16 grid loses the tooth.** On `side` 16 the bite is gone in three seeds of four (0% of
bodies; the control has 18-45% in three seeds) and kills fall to 0.03-0.69 a step (control
1.3-4.6); `grow` keeps it where the side stays 8 (seed 1: 49%, 1.1 kills a step). The eye is
e026's (a sensor on up to 1-54% of bodies).

## Conclusion

1. **The grid alone is a rescale: yes.** On the 16 grid the bodies are 12.5-14.2 cells (control
   8-21) on a grid of 256; the size is the world's.
2. **The side is selected under `grow`: yes,** but by history, not toward a size: 4.4, 5.2,
   8.1 and 14.3 at the end of four seeds, with a spread of 0.8-2.4 in each; the cells per body
   are 11-16 in all four.
3. **Small and large bodies coexist: no.** The cells at the 90th percentile are 16-24 in every
   run and 1.6-4 times the 10th (the control's mass ratio is 4-14); lineages of different sides
   share a seed, but they are the same size and e026's two kinds (mover and sitter), sorted
   onto sides by chance. Nothing over 50 cells lives past its first steps.
4. **The world stands: yes.** 2,480-3,980 bodies against the control's 2,620-4,760.

Not kept as the default: `side` stays 8 (the argument stays, 1-16 or `grow`, for a world where
size pays). What it changes for the project: the ceiling was never the reason bodies are 10-20
cells. A body pays 0.002 a cell and 0.032 a body per step, a gut takes at most 0.02 a step from
the cell under it, and the sun gives every cell 0.01 a step: a body of 16 cells costs the sun of
six cells, and 16,000 cells feed 2,700 such bodies, which is what every world holds. A larger
body costs more cells of sun and gains nothing per cell, since a cell of ground holds what the
sun gives it whatever stands on it; the ceiling of 64 was not binding and 256 changes nothing
but the compute (2x per step on the 16 grid) and the tooth (a bite needs a hard tip with muscle
behind it in one line, and a body of 12 cells on a 16 grid has few lines with two cells in
them). Size will pay when a body can do something with size that a small body cannot: carry a
store through the winter (the fat is its eater's now, vision item 2: a store a body can spend),
or reach food a small body cannot (a place, #14; the canopy's trees). #5 (3D bodies) meets the
same ceiling and should wait for that.

Open: whether a cell that holds more (e011's rich cells took bodies to 64) or a store would move
the size under `grow`, which is the cheap way to ask, now that the side is heritable.
