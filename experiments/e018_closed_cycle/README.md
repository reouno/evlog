# e018 A closed cycle through the soil

Date: 2026-08-31

## Purpose

e017 showed the premise "matter that does not vanish" without a memory: a dead body is food
where it lies, it is worth what it cost (2-3% of the food), and it is eaten within a few dozen
steps by whoever stands there next. Nothing in the crowd, the contacts or the winners moved,
because the ground forgets a death as soon as it is eaten and the sun regrows every cell at the
same rate whatever happened on it. The real world's ground is not like that: what is not eaten
returns to the soil of the place, and a plant grows out of that soil, so a place where much
lived and died is rich and a place that was grazed bare stays bare until matter comes back.
The total matter of a closed world is fixed; the sun sets only how fast it moves.

This experiment adds that as a law about matter (issue #20, vision "Next" 1): **matter does
not vanish.** Every unit of it is in one of four places, the soil of a cell, the plant on a
cell, dead matter lying on a cell, or a body (its cells and its energy). A plant grows out of
the soil of its cell, at most the sun's rate per step (today's regrowth field), never above the
cap, and not while a body stands on the cell (e016). What a body spends, its upkeep and the
work of moving, falls to the soil of the cell under it. Dead matter that nobody eats rots into
the soil of its cell at 1% per step. Nothing is created and nothing is lost: the world holds
what it started with. The sun bounds the speed, the soil bounds the amount.

What this could give: the map remembers (a cell holds what was spent and died on it, and
grows only out of that), so a place where many lived is rich for as long as it takes to eat
it back out through plants, and a place grazed bare stays bare; boom and bust in place of a
fixed carrying capacity, when the matter in circulation is scarce; and, with no patches drawn
at all, places may emerge from where matter piles up. What it risks: matter spreading flat, or
matter locked where no sun reaches (the soil left behind a patch that drifted away). It costs
one f32 per cell and nothing per body.

## Hypothesis

1. **The soil binds where the sun is strong.** With the drawn sun (grass and trees) at
   e017's total (8 per cell), 20-40% of the sun is barren (it shines on a cell whose soil is
   empty) over the second half, most of it on the trees: a tree cell gets 6.5 of sun per step
   and its soil holds a few steps of that, refilled only by what the bodies on it spend. The
   trees hold 5-15 bodies (e017: 33-42), the world eats 20-30 per step (e017: 35-54) and
   holds 400-600 bodies (e017: 652-795).
2. **The map remembers.** The soil is rough, not flat: in every run the richest tenth of the
   cells holds over 30% of the soil (10% if flat), and on the grass at least a fifth of the
   cells are bare (soil under 1) while the grass holds 5 or more per cell on average; the
   matter the patches swept is left behind them as soil (the cells beyond the patches hold
   the world's matter, 8 or more per cell, as soil where they held it as plants before).
3. **Boom and bust at a scarce total.** At 1 per cell (an eighth of e017's total, with the
   start's bodies a third of it), the soil binds everywhere (60-90% of the sun barren), the
   population is 100-300, and it swings: the coefficient of variation of the population over
   the second half is above 0.15 and its largest value over its smallest above 2 in at least
   three seeds of four (e017 on the same world: 0.03-0.09 and 1.18-1.60). At 8 per cell the
   swing stays in e017's range.
4. **The soil does not make places.** With a uniform sun (0.01 on every cell, no patch
   drawn) at 8 per cell, matter does not pile up: the richest tenth of the cells holds 30-40%
   of the soil at the end as at step 10,000 (roughness, not places), the soil under bodies is
   within 10% of the soil elsewhere, and the world is a lawn of about 2,000 small movers with
   one or two lineages. If instead the soil concentrates (the richest tenth over 50% by the
   end, bodies on the rich cells), the drawn patches can go and this law draws them.
5. **The winners and the world.** Judged by #19's rule: lineages alive 1-4 (e017: 2-4) and
   e017's wedge of eight gut cells winning the grass at 8 per cell; the bodies of the trees
   are gone with the trees' food. Matter is conserved to within 1% over the run (a parent
   that pays for a child's cells with energy it does not have is the one leak). The world
   stands: no extinction, at least 200 steps per second with six runs sharing a machine.

## Method

Code: e017 (`experiments/e017_dead_body_food`, a cell of 0.02) with the soil added to the
food of the world (`Food::soil`, one f32 per cell) and the cycle closed at three points:

- regrowth (`Food::regrow`): dead matter on the cell rots into its soil (`DECAY` = 0.01 per
  step), then the plant grows out of the soil by at most the sun (the patches' field, as
  before), not above the cap (8), and not at all while a body holds the cell; the sun that
  grew nothing is counted as `shaded` (a body on the cell), `wasted` (the plant at the cap) or
  `barren` (the soil empty);
- a body's upkeep (0.002 per cell and 0.032 per body per step) and the work of moving fall to
  the soil of the cell under the middle of its box (`Food::spend`); a body that has less than
  it owes gives what it has (it dies this step) so that nothing is created;
- the dead lie on the ground as in e017 (a dead body's cells and energy, a child never placed,
  a broken cell nobody eats), and rot from there.

Two arguments set the world: the matter per cell at the start (`matter`, the cap by default:
plants at the cap and empty soil, e017's start; below the cap the plants are that much and the
soil empty) and the patch widths, where a width of 0 alone means a uniform sun (`RES_GROWTH`
= 0.01 on every cell, one kind of place). New columns: `soil` (matter in the soil), `matter`
(the total: soil, plants, dead matter, bodies' energy and cells), `barren`, `rot` (dead
matter returned to the soil per step), `spent` (what bodies returned per step); per place
`soil`, `barren`, `regrowth`, `cells`. The soil and the plants of every cell are written every
100,000 steps (`soil.jsonl`, two decimals) and the soil goes into the long snapshots on a log
scale for the viewer. The leak: a parent pays `CELL_ENERGY` per cell of its child from the
half it kept, and a small parent with a large child can owe more than it has; the deficit is
discarded with its negative energy at death. `matter` measures it.

Not byte-identical to e017 (the food differs from the first step: the start's plants are eaten
down and never regrow where no sun is).

Pilot (seed 9, 100,000 steps, 128x128, six threads; the files were not kept): at 8 per cell
with grass and trees, 411-535 bodies, 24-31 eaten per step (e017's pilot: 34), the sun barren
32-64 per step of 164 (on the trees 29 of 41; the trees hold 12 bodies), matter 139,700 at
every log step (a leak of 1.3 in 100,000 steps); the soil holds 135,000 of it, 7.2 per cell on
the grass, 7 on the trees and 8.7 beyond the patches (where the patches passed, eating the
plants and leaving soil), and the richest tenth of the cells holds 37% of it. At 1 per cell:
88-334 bodies, 6-16 eaten per step, barren 108-145 per step, matter 25,013 (a leak of 0.3).
Uniform sun at 8 per cell: 1,960-2,200 bodies of mass 6 moving forward 70% of the time, 105
regrown per step (a third of the sun shaded, 2.5 barren), matter 139,692 falling to 139,609
(a leak of 84 in 100,000 steps, 0.06%, from 35,000-74,000 births per 10,000 steps), the
richest tenth of the cells 34% of the soil at step 10,000 and at 100,000, the soil under
bodies equal to the soil elsewhere; 800 steps per second.

Runs (1,000,000 steps, 128x128, seeds 1-4): grass and trees ("8,1") at 8 per cell
(`results/128_sigma8-1_*`), grass and trees at 1 per cell (`results/128_sigma8-1-m1_*`), and
the uniform sun at 8 per cell (`results/128_sigma0_*`): twelve runs, six at a time on each of
two machines with one thread each (`run.sh 1 2` locally, `run.sh 3 4` on the Ubuntu box).
Four more runs were added once the first two at 1 per cell had died (steps 304,308 and
803,008): grass and trees at 4 per cell, seeds 1-4, locally (`results/128_sigma8-1-m4_*`), to
see where between 1 and 8 the world stands. Reference: e017, grass and trees, seeds 1-4
(`../e017_dead_body_food/results/128_sigma8-1_*`).

    cargo run --release -p e018_closed_cycle -- <steps> <seed> <size> <widths> [cell_energy] [matter]
    uv run python experiments/e018_closed_cycle/report.py

## Result

All numbers are medians over the second half of the run unless said otherwise; ranges are over
the four seeds of a world (`results/128_sigma8-1_*`: 8 per cell; `128_sigma8-1-m4_*`: 4;
`128_sigma8-1-m1_*`: 1; `128_sigma0_*`: the uniform sun at 8). The report (`report.html`) has
the charts, the soil maps, the bodies that prospered and the viewer with the soil as a layer.
Seeds 1-2 of the three drawn worlds ran locally, seeds 3-4 on the Ubuntu box; the 4 per cell
and the uniform runs locally (the uniform seeds 3-4 were started on both machines and the
local ones, finishing first, are the ones kept).

- **The total holds.** Matter at the end is 0.9999-1.0002 of the start in the drawn worlds
  (the parent's leak, under 0.02%) and 0.9923-1.0017 under the uniform sun, where 1,100-2,200
  bodies add 0.05 to an f32 of 8 or more a million times over (rounding, both ways).
- **The world lives on what its bodies return.** Regrowth equals what was spent, in every run
  of every drawn world: 22-26 per step at 8 per cell (the sun gives 164; e017's world ate
  35.6), 17-22 at 4, 6-9 at 1. The sun falls on empty soil 26-39% of the time at 8 per cell
  (17-26 per step on the grass, 20-42 on the trees, of 82 each), 42-51% at 4, 76-87% at 1;
  on bodies standing on cells 32-59%, 30-42%, 8-16%. Population 414-482 at 8 per cell (e017:
  673), 314-418 at 4, 100-172 at 1. The trees hold 0-20 bodies (e017: 37) and feed 0.5-1.6
  per step (e017: 2.7): a tree cell's 6.5 of sun empties its soil in a step, and what grows
  there after is what its bodies spend.
- **The map remembers.** At the end of the 8 per cell runs the richest tenth of the cells
  holds 43-46% of the soil (36-38% at step 100,000; 10% if flat), 31-48% of the grass cells
  are bare (under 1) while the grass holds 4.9-10.6 per cell, the trees 1.2-10.1, and the
  cells beyond the patches 7.6-9.9 per cell, 70% of the world's matter, left there by the
  patches as they passed (the maps show the trails dark and the patches' present places
  pale). The soil under the bodies is 0.63-2.01 times the soil elsewhere. At 4 per cell:
  50-55%, 58-61% bare, grass 2.6-4.6, beyond 4.3-5.2. At 1: 57-67%, 77-96% bare.
- **The closed world swings, and the scarce one dies.** Population coefficient of variation
  0.17-0.25 at 8 per cell, 0.25-0.34 at 4, 0.37-0.58 at 1 (e017: 0.06); largest over
  smallest 2.3-4.2, 3.1-4.9, 10.5 and more (e017: 1.4). At 1 per cell three worlds of four
  died (steps 304,308, 803,008, 941,817); the fourth ended with 60 bodies. No extinction at
  8 or 4.
- **The uniform sun weaves the soil into trails.** 1,110-2,188 bodies (cv 0.01-0.08), one
  lineage per run, a bar of 6-9 gut cells 2 rows deep and 5-8 wide walking forward 28-42% of
  the time. In three seeds of four the richest tenth of the cells goes from 34-56% of the
  soil at step 100,000 to 60-87% at the end, 51-72% of the cells are bare, the soil under
  bodies is 1.4-2.4 times the soil elsewhere, the sun lost to empty soil rises from 5-10 to
  34-77 per step and the food eaten falls from 110-115 to 50-105 per step, still falling at
  the end; the map is a weave of lines one cell wide, the bodies' trails, with bare cells
  between them. In the fourth seed nothing moves (36%, 1.01, barren 5 per step).
- **Fewer winners.** Lineages alive 2 at 8 per cell, 1-3 at 4, 1 at 1, 1 uniform (e017: 4).
  A block of 9-14 digestive cells wins the grass in every drawn run (the wedge; a slab of 14
  over 3.4 world cells, 372,000 steps; one wall 7 wide with 2.4 hard cells on its side,
  439,000 steps); the survivor at 1 per cell is 6-7 cells; nothing has a bite; the trees hold
  no lineage of their own. 616-4,553 steps per second.

## Conclusion

1. The soil binds where the sun is strong: yes. 26-39% of the sun barren, the world eating
   23-26 per step and holding 414-482, the trees 0-20 bodies.
2. The map remembers: yes. 43-46% in the richest tenth, 31-48% of the grass bare, the swept
   matter (70% of the total) lying beyond the patches as soil.
3. Boom and bust: yes at 1 per cell (cv 0.37-0.58, 10x and more), and the world dies (three
   of four); the swing is 2-5x at 4 and 8 per cell too, not e017's range. Partly.
4. The soil does not make places: no, in neither reading. It makes trails (three seeds of
   four), one cell wide, and the world eats less every year.
5. The winners: fewer (1-3 lineages against e017's 4), the same block on the grass, the trees
   empty. Partly.

What it changes: the closed cycle conserves matter and gives the world a memory, both cheap,
and makes a poorer, swingier, less diverse world. When a plant grows only out of its own
cell's soil, the sun is no longer the world's income but a pump that empties each cell once;
after that the world eats what its bodies spend (regrowth = spent, 23-26 of 164), the rich
places become the places the sun drains fastest (the trees, where bodies met, are empty),
and 70% of the matter lies where no sun is. Principle 4 fails at the scarce total (three
deaths) and under the uniform sun (a food supply still falling at a million steps). Judged
by #19 (count the winners), this law as it stands is a loss: 1-3 lineages against 4.

What is missing is a flow. The real world's matter moves without bodies: water carries it
downhill, a delta is rich because a continent drains into it, and the sun shines everywhere.
Here matter moves only inside a body. The next law (issue #22) is a terrain: a height per
cell and soil that spills downhill at a rate, so that rich places are where matter collects
and the sun can be uniform; the places would be the valleys, drawn by the water. The soil
stays in the code as the world's memory; whether the cycle stays closed is decided by that
experiment. The soil maps and the soil layer in the viewer stay: a map of where the world
has been is something to watch.
