# e019 Matter that flows: a terrain the soil runs down

Date: 2026-08-31

## Purpose

e018 closed the cycle of matter: every unit is in the soil of a cell, in the plant on it, lying
dead on it, or in a body, and a plant grows only out of its own cell's soil. The world kept its
total and the map got a memory, but the world got poorer: the sun became a pump that empties each
cell once, after which the world eats what its bodies spend (23-26 per step of 164 of sun), a
third of the sun fell on empty cells, the trees lost their bodies, the population swung 2-5x,
lineages fell to 1-3, and under a uniform sun the soil wove itself into the trails of the walking
bodies while the food supply fell through the run. Seventy percent of the matter lay where no sun
was. Matter moved only inside a body.

The real world's ground moves matter on its own: water carries it downhill, a delta is rich
because a continent drains into it, and the sun shines everywhere. This experiment adds that as
a law about the world (issue #22, vision "Next" 1): **the ground has a height, and soil runs
downhill.** Every cell has a height (a terrain: smooth noise drawn from the seed, with a relief
from the lowest cell to the highest measured in soil, one unit of soil raising a cell's surface
by one). The surface of a cell is its height plus its soil. Each step a cell gives a share of its
soil (`flow`) to the neighbors whose surface is lower, split by the drop to each and never more
than an eighth of a drop, so that soil pools level where it collects and does not slosh. Plants
are rooted and the dead lie where they fell; only soil moves. The sun is uniform (e018's width 0,
0.01 on every cell): the places are the valleys, drawn by the flow, not by a patch. It costs one
f32 per cell and one pass over the cells per step.

What this could give: the matter e018 locked in trails and behind the drifting patches runs to
the low ground and pools there as a lake of soil, flat and productive over its whole area, so
that the sun on the lowland is used in full and the food supply stops falling; a map with a
lowland and an upland, made by the water, that bodies may sort themselves by. What it cannot
give under a uniform sun: a rich cell. No cell grows faster than the sun (0.01 per step), so a
valley is a wide place, not a fast one, and e011's trees cannot come back this way; with the
drawn sun a tree patch over a lake may be refilled by the flow.

## Hypothesis

1. **The flow ends the fall.** Under the uniform sun at relief 64 the food eaten per step is
   steady over the second half of the run (the medians of the third and fourth quarters within
   10% of each other; e018's uniform world fell from 110 to 50-105 and was still falling) and
   so is the sun lost to empty soil; the population is 1,400-1,800 with a coefficient of
   variation under 0.10 over the second half.
2. **The places are the valleys.** At relief 64 the lowest two thirds of the cells (valley and
   slope bands) hold over 95% of the soil and over 90% of the bodies, and the ridges are bare
   (soil under 0.1 per cell); at relief 256 the lake covers about a third of the world and
   holds 500-700 bodies, the rest is bare. The soil map is the terrain upside down: the
   richest tenth of the cells holds about 30% of the soil at relief 64 (the lake is flat, so
   the map is a step, not a peak) and about 60% at relief 256.
3. **A lake is not a tree.** No cell grows faster than the sun, so no valley cell becomes a
   rich cell: the bodies on the lake are e018's small movers (mass 6-9, a bar or a block of
   gut cells), contacts under 0.05 per body per step, and 1-2 lineages alive per run (e018's
   uniform world: 1). Judged by #19, the terrain alone under a uniform sun does not make more
   winners; it makes the world stand.
4. **The flow gives the grass back but not the trees.** With the drawn sun (widths 8 and 1)
   at relief 64 the grass eats 28-34 per step (e018: 23-26, e017: 36) and holds 500-650
   bodies, because the lake refills what the sun draws out of a grass cell (0.1 per step);
   the trees stay empty (0-10 bodies) because a tree cell's 6.5 of sun empties a cell faster
   than its neighbors' soil runs in.
5. **Leveling alone makes a lawn.** With no terrain (relief 0) and the same flow the soil
   spreads flat: over 95% of the cells hold soil, the world eats 100-120 per step and holds
   1,800-2,200 bodies, one lineage; e018's trails do not form.
6. **The world holds.** Matter is conserved to 0.1% (f32 rounding), and the flow costs under
   10% of the step time.

## Method

Code: e018 (`experiments/e018_closed_cycle`) with a terrain and the flow added:

- the terrain (`Terrain`): white noise from the seed's own stream, blurred by a Gaussian of
  16 cells (`RELIEF_GRAIN`; a 128x128 world gets a handful of basins, as it has four patches)
  on the torus, scaled to [0, `relief`]; under the uniform sun the place of a cell is its
  height band (0: the lowest third of the cells, the valleys; 1: the middle third, the
  slopes; 2: the highest third, the ridges), so that the per-place log reads by height;
  with the drawn sun the places are the patches, as before;
- the flow (`Food::flow`), once per step after regrowth: for every cell, the drop of its
  surface (height plus soil) to each of its four neighbors; it gives `flow` of its soil to
  the lower ones in proportion to the drops, never more than an eighth of a drop
  (`LEVEL`); all cells move at once from the surfaces at the start of the step.

Two new arguments: `relief` (0: flat) and `flow` (0: e018). New columns: `flow` (soil moved
per step), `soil_cells` (share of the cells with at least a step of sun's worth of soil, 0.01),
`deep` (share with a full plant's worth, 8); `height` on each agent and lineage (the terrain
under the body). The terrain is written once per run (`terrain.json`: height and band of every
cell). Everything else is e018 (matter 8 per cell at the start as plants, a cell of 0.02).

Pilot (seed 9, 100,000 steps, 128x128, two threads each, five at once; the files were not
kept): under the uniform sun the flow rate hardly matters (at 0.01, 0.1 and 1 the world at
step 100,000 is the same to a few percent: 1,450-1,600 bodies, 74-77 eaten per step, 71% of
the cells holding soil, the richest tenth 31%; at 0.01 it is still settling, from 85 at step
40,000), so it is fixed at 0.1 and the relief is what is varied. At relief 64 the soil pools
over the valley and slope bands (19.0 and 5.9 per cell, the ridges 0.05), the ridges get 47
of the 164 of sun on empty soil, bodies stand on cells for another 42, and the food eaten is
flat at 77 from step 40,000 on; one lineage. At relief 256 the lake is 32% of the cells (25
per cell, the richest tenth 60% of the soil), 600 bodies eat 35 per step, 110 of sun is
barren; one lineage. With the drawn sun at relief 64, 569 bodies on the grass eat 31 per step
with 4 of the grass's 82 of sun barren (e018: 17-26), the trees hold 0 bodies with 27 of
their 41 barren. Matter 139,700 to within 0.1% in every run; 700-750 steps per second with
five runs sharing the machine.

Runs (1,000,000 steps, 128x128, seeds 1-4, flow 0.1): the uniform sun at relief 64
(`results/128_sigma0_r64_f0.1_*`), at relief 256 (`128_sigma0_r256_f0.1_*`) and with no
terrain (`128_sigma0_r0_f0.1_*`, the flow as leveling alone), twelve runs locally at one
thread each (`run.sh uniform 1 2 3 4`); grass and trees at relief 64
(`128_sigma8-1_r64_f0.1_*`), four runs on the Ubuntu box (`run.sh drawn 1 2 3 4`). Reference:
e018's uniform sun at 8 per cell and grass and trees at 8 per cell, seeds 1-4
(`../e018_closed_cycle/results/128_sigma0_*`, `128_sigma8-1_*`).

    cargo run --release -p e019_terrain -- <steps> <seed> <size> <widths> [cell_energy] [matter] [relief] [flow]
    uv run python experiments/e019_terrain/report.py

## Result

(pending)

## Conclusion

(pending)
