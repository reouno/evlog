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

All numbers are medians over the second half of the run unless said otherwise; ranges are over
the four seeds of a world (`results/128_sigma0_r64_f0.1_*`: the uniform sun at relief 64;
`128_sigma0_r256_f0.1_*`: relief 256; `128_sigma0_r0_f0.1_*`: flat; `128_sigma8-1_r64_f0.1_*`:
grass and trees at relief 64). The report (`report.html`) has the charts, the terrain and soil
maps, the bodies that prospered and the viewer with the terrain and the soil as layers. The
twelve uniform-sun runs ran locally (12 at once, one thread each, 40-60 minutes), the four
drawn-sun runs on the Ubuntu box.

- **The flow ends the fall.** Under the uniform sun at relief 64 the food eaten per step is
  56-71, the same in the last quarter as in the third (0.99-1.01; it settles by step 100,000:
  seed 1 goes 75, 72, 71, 71, 71 at 100,000-step marks, the others move under 2%); e018's
  uniform world fell from 110 to 50-105 and was still falling. The sun lost to empty soil is
  flat too (52-75 per step, the ridges). Population 1,126-1,458 with a coefficient of variation
  of 0.01-0.03 and a swing of 1.0-1.1x (e018 at 8 per cell: 2.3-4.2x). At relief 256: 26-31
  eaten (1.00), 478-618 bodies (0.01-0.02). No uniform-sun world died or declined.
- **The places are the valleys.** At relief 64 the lowest two thirds of the cells hold 100% of
  the soil at the end (valleys 19.2-21.5 per cell, slopes 3.5-5.6, ridges 0.0) and 99-100% of
  the bodies (698-733 in the valleys, 431-711 on the slopes, 0-14 on the ridges); 54-66% of the
  cells hold soil, the richest tenth holds 32-35% of it (10% if flat), the soil under the bodies
  is 1.6-2.0 times the soil elsewhere. At relief 256 the lake is 25-30% of the cells at 25.4-25.5
  per cell, holds every body (478-613 in the valleys, 0-4 on the slopes), the richest tenth holds
  63-70% of the soil and the soil under bodies is 3.7-4.5 times the soil elsewhere. The soil maps
  are the terrain upside down: a level lake filling the basins to one height, with a sharp shore
  (the report's Figure 3.2). The flow moves 66-77 per step at relief 64, 28-37 at 256, 110-131
  on the flat world: what bodies spend, spreading.
- **A lake is not a tree.** The winner of every uniform world is a bar of 6-10 digestive cells,
  1-2 rows deep and 5-8 wide, mass 6.8-9.1, over 2.6-3.5 world cells, walking forward 28-48%
  of its decisions; no hard cell, no muscle, no bite. Contacts 0.006-0.089 per body per step
  (e018: 0.03). Lineages alive 1 at relief 64, 1-2 at 256, 1 on the flat world; the second
  lineage of relief 256 seed 1 lived 324,000 steps at 127 agents with the same body, its members
  standing higher (height 71 against 59). The ridges hold nobody: 0-14 bodies on 5,461 cells.
- **The flat world is a lawn.** With no terrain the soil levels to 8.1-8.2 on every cell (the
  richest tenth holds 10%, no cell under 0.01), the world eats 101-106 per step, steady
  (0.99-1.00), and holds 1,954-2,149 bodies (cv 0.01) in one lineage, a bar of 7 gut cells 1-2
  by 6-8; the sun is lost only to bodies standing on cells (35-39%). e018's trails do not form:
  leveling alone is the cure for the fall.
- **The terrain takes the soil away from the drawn sun.** Two of the four grass and trees worlds
  died (steps 53,181 and 257,596) and the other two swung 5x and more (cv 0.26-0.91; 333 and 293
  bodies, lows of 58 and 25). The grass eats 13-17 per step (e018: 22-26; e017: 36) with 255-308
  bodies (e018: 393-453) and 35-46 of its 82 of sun falling on empty soil (e018: 17-26); the
  trees hold 8-18 bodies (e018: 0-20) and eat 1.0-1.3 per step. The patches drift over the
  terrain: on the lake the grass holds 500 bodies (seed 1 at step 250,000, barren 27), on the
  ridges 99 (step 750,000, barren 116). The dead worlds are the seeds whose patches started on
  high ground (seed 3: 119 bodies at step 10,000). The trees stand at 27-40 bodies only when a
  tree patch lies on the lake (seeds 1 and 4 at the end), 0 otherwise.
- **The world holds, with a rounding drift.** Matter at the end over the start is 0.9905-0.9964
  at relief 64, 1.0021-1.0059 at 256, 0.9822-0.9896 on the flat world and 0.9996-1.0000 with the
  drawn sun: an f32 soil that receives and gives 0.001-sized amounts a million times drifts by up
  to 1.8% (e018's uniform world: 0.8%), the drawn world, with few bodies, hardly at all. The
  soil should be an f64 from here (one array; see the note below). 624-696 steps per second at
  relief 64 with twelve runs on one machine (e018's uniform world: 616-1,000 with six to ten),
  424-510 on the flat world with 2,000 bodies, 1,020-1,248 at relief 256.

Note on the drift: a copy of the code with the soil as an f64 (everything else the same; not
committed) run 50,000 steps on the flat world and at relief 64 (seed 1) holds matter to within
0.4 of 139,737 (0.0003%) where the f32 runs lose 115 and 62 over the same steps. The runs above
are the f32 code as committed with them; the soil is an f64 in the code from the commit after.

## Conclusion

1. The flow ends the fall: yes. Food eaten steady at 56-71 per step over the second half
   (0.99-1.01 between quarters), the population 1,126-1,458 with a coefficient of variation of
   0.01-0.03 (asked 1,400-1,800 and under 0.10). The first closed world that stands: no
   extinction, no decline and no swing in any of the twelve uniform-sun runs.
2. The places are the valleys: yes. 100% of the soil and 99-100% of the bodies in the lowest
   two thirds at relief 64, bare ridges; a lake of a third of the world at relief 256; the
   richest tenth 32-35% and 63-70%; the map is the terrain upside down.
3. A lake is not a tree: yes. A bar of gut cells of mass 7-9 wins every uniform world, contacts
   0.006-0.089, lineages 1-2. The terrain alone under a uniform sun makes the world stand, not
   more winners.
4. The flow gives the grass back but not the trees: no, the reverse. The terrain takes the soil
   away from the drawn sun: the grass eats 13-17 per step (e018: 22-26), two worlds of four die,
   the other two swing 5x as the patches drift on and off the lake; the trees hold bodies only
   while a tree patch lies on the lake.
5. Leveling alone makes a lawn: yes. 100% of the cells hold soil at 8.1-8.2, the world eats
   101-106 per step, steady, 1,954-2,149 bodies, one lineage, no trails.
6. The world holds: partly. Matter drifts by up to 1.8% over the run, f32 rounding of the soil
   (an f64 soil holds it to 0.0003%); the cost of the flow is one pass over the cells and the
   step rate is in e018's range at the same population.

What it changes: soil that levels (its own height counts) is the law that makes the closed
cycle stand. e018's fall came from matter locking in the bodies' trails while the cells between
them wasted the sun; with the flow every cell that has soil grows, and the world's income is
the sun on the wet cells minus the cells bodies stand on: 101-106 per step on the flat world,
56-71 at relief 64 (the ridges' share of the sun is lost), 26-31 at relief 256. The flow stays,
with or without a terrain, and the soil becomes an f64.

The terrain gives the world a shape without a patch: the lake, level, with a shore, filling the
basins to one height, and bodies live in it and nowhere else. That is a map worth watching (the
viewer's terrain and soil layers show it) and it is only one place: inside the lake every cell is
the same, and the same bar of gut cells wins as on the flat lawn (#19: 1-2 lineages, as e018).
The ridges are a desert nobody enters because nothing is there for a body: matter moves only
downhill and in bodies, and a body gets nothing for carrying it up.

The drawn sun over a terrain fails, and the failure says what a rich place is in a closed world:
the meeting of the sun and the soil. Our patches put the sun where they drift; the water puts
the soil where the ground is low; where the two part, nothing grows, and a world whose patches
climb out of the lake dies. From here the sun is uniform and the shape of the world comes from
the ground. The next law (#14, places that differ) can be written on the height the terrain
gives every cell, the coordinate along which the real world's places differ (warm and cold, wet
and dry, the plants that grow there), and it is a place law about the world, not a sun law: the
question it has to answer is what a body can find on the high ground that it cannot find in the
lake.
