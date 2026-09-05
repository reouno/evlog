# e035 Water that flows

Date: 2026-09-05

## Purpose

The world's carrier of matter on the ground has been the soil itself since e019: a number per
cell that plants grow out of and that runs downhill at a tenth of the drop per step. The
user's premise (issue #29): what flows is water. Rain becomes water, water runs downhill,
pools in the low ground and evaporates; the soil stays where the dead and the dung lie and
moves only a little, with the water; a plant needs both. e034 (the still soil) showed what the
carrier must do in this world: the dead are eaten and the matter returns through the air,
which rains alike on every cell, so a soil that does not move piles where nothing eats (the
ridge) and the valley's crowd starves; a carrier at the plant's own rate (0.001 of a lake cell
per step) re-forms the lake. This experiment replaces the carrier: water as a field of the
world, and the soil leached by it at that order. Wet and dry become places: with the winter
by height, the ridge is dry and dark in winter, the valley wet with the winter sun.

## Hypothesis

1. **The world stands** at e032's floors (542-825 on the pilot seed) with the soil lying where
   it is laid and the water leaching it: the leaching at the plant's rate brings the matter
   back to the valley as e034's flow 0.001 did (floors 428-670), and the wet valley grows in
   full.
2. **Wet and dry are places.** The ridge's plants grow at about half the sun (its water is
   half the wet level), the valley's in full; the ridge holds soil it cannot use for want of
   water, and its summer share of the bodies falls from e034's 30-38% toward e032's 17-19%
   or below.
3. **The carrier matters, not the wetness alone.** Water on the old carrier (flow 0.1, no
   leaching) is e032's world with a drier ridge: the same floors and shares, the ridge's
   barren sun turned into dry sun.
4. **A drier world is a smaller world**, in proportion to the sun it loses: at water 0.2 the
   world's plants get 57% of the sun and the floors fall by about that.

## Method

Code: e034 (`experiments/e034_stillsoil`) as `e035_water` with two laws about the world, both
off by default (`water` 0 is e034 byte for byte; checked on seed 9 for 10,000 steps):

- **Water** (argument 25, `water`: the share of a cell's water that runs to its lower
  neighbors per step, by the drop of the terrain's height). The sky gives every cell 1 of
  water per step and a cell loses 1% of its water per step to the air; a cell alone settles
  at 100 (the wet level). A plant grows under its sun times min(1, water / 100); the sun lost
  this way is `dry`. On the pilot seed's terrain the steady water gives the plants of the
  valley, the slope and the ridge 91%, 73% and 51% of their sun at water 0.1 (the world 72%),
  and 82%, 55%, 34% at 0.2 (the world 57%); at 0.02 the ridge still gets 85%. The water is a
  field of the world like the height, not matter.
- **Leaching** (argument 26, `leach`): the water that leaves a cell takes `leach` of the soil
  it stood in, in proportion: the soil moved per step is leach x water x soil, so at water 0.1
  a `leach` of 0.01 moves 0.001 of the soil per step, e034's rate. With `flow` 0 (argument 8)
  the soil moves by leaching only.

- **The surface** (argument 27, `depth`: height per unit of water, 0 by default). With 0 the water
  runs by the terrain's height alone and piles in the pits (round 1); with 0.01 (a wet cell is
  1 of height) the drop is that of the water's surface, at most an eighth of it per step (e019's
  LEVEL), so a pool spreads level and the leached soil spreads with the water that fills it
  (round 2). On the pilot seed's terrain at water 0.1 the steady water then gives the bands 96%,
  76% and 53% of their sun (the world 75%), the valley 76% wet cells, the deepest pool 4 of
  height (with `depth` 0 one pit holds 38,000 of water).

- **The mixing** (argument 28, `mix`, 0 by default; round 3): the soil dissolved in standing
  water mixes. Every pair of neighbors exchanges `mix` of the difference of their soil per step,
  times the wetness of the drier of the two (its water over 100, at most 1): a lake shares its
  soil, a dry slope at half. e019's soil flow was two laws in one, the carrier downhill and this
  mixing; round 2 showed the second is the one the crowd lives on.

The cost is one field and two passes per step (the water, the mixing) against the one soil
flow they replace; a run of 100,000 steps at one thread took 13 minutes against e034's 17.

**Runs.** All on seed 9, 100,000 steps (five winters), one thread each, at once on the Mac, in
the season world (`winter high` 2, store 5, grow, `rain flat`). Round 1 (`depth` 0; 4 cores, 20
minutes): water 0.1 with leach 0.01 and flow 0 (the premise); water 0.1 with leach 0.03 (the
leaching three times faster); water 0.2 with leach 0.01 (the drier world); water 0.1 with leach 0
and flow 0.1 (the wetness alone, on the old carrier). Round 2 (`depth` 0.01; 3 cores, 20
minutes): water 0.1 with leach 0.01 and 0.03, water 0.2 with leach 0.01, flow 0. Round 3 (`depth`
0.01, water 0.1, leach 0.01, flow 0; 2 cores, 13 minutes): `mix` 0.05 and 0.2. Controls: e032's
pilot (flow 0.1, no water) and e034's pilots at flow 0.001 and 0. Then the batch: seeds 1-3 for
300,000 steps (15 winters) at water 0.1, leach 0.01, depth 0.01, mix 0.2 (3 cores, 45 minutes),
against e032's batch (flow 0.1, no water, the same seeds and length).

**Measures.** `pop.csv`: bodies and soil per band every 1,000 steps (floors, the valley's share,
the ridge's summer share). `places.csv`: per band at the equinoxes the water (mean per cell),
the sun lost to dryness (`dry`) and for want of soil (`barren`), the rain, the bodies. `log.csv`:
`dry`, `water`, `leached` (soil moved per step), the food eaten, the soil. The winners from
`lineages.csv`; the soil and water maps in `soil.jsonl`.

## Result

### Round 1: the water on the terrain alone (`depth` 0)

From `pop.csv`, `places.csv` (second half, medians), `log.csv` (second half) and the last soil
and water maps. Controls: e032's pilot (flow 0.1, no water) and e034's at flow 0.001.

| water, leach, flow | winter floors, in order | valley share at the floors | summer peaks | ridge share at the peaks | eaten per step | sun lost: dry / barren, per step | soil per band at the end |
|---|---|---|---|---|---|---|---|
| 0.1, 0.01, 0 | 344, 428, 426, 361, 355 | 54-72% | 1,876-2,481 | 28-32% | 36 | 33 / 60 | 58,500 / 43,000 / 26,000 |
| 0.1, 0.03, 0 | 349, 302, 237, 232, 148 | 48-79% | 1,078-2,512 | 26-33% | 21 | 34 / 75 | 122,200 / 9,600 / 700 |
| 0.2, 0.01, 0 | 318, 224, 195, 107, 156 | 61-74% | 1,056-2,445 | 29-33% | 18 | 52 / 59 | 125,600 / 1,900 / 3,100 |
| 0.1, 0, 0.1 | 383, 595, 607, 661, 661 | 71-82% | 2,157-3,439 | 14-19% | 61 | 29 / 18 | 83,900 / 15,200 / 500 |
| none, -, 0.1 (e032) | 542, 819, 825, 680, 695 | 73-85% | 2,700-4,192 | 17-32% | 67 | 0 / 39 | 82,700 / 14,000 / 300 |
| none, -, 0.001 (e034) | 428, 642, 670, 575, 495 | 63-69% | 1,723-2,476 | 30-34% | 38 | 0 / 96 | 65,700 / 42,000 / 16,600 |

Per band: the water per cell (wet: 100) and the sun lost to dryness per step (the same in every
water-0.1 run: 166 / 82 / 52 of water, 4 / 12 / 21 of dry sun; at 0.2: 203 / 63 / 34, 8 / 20 / 31),
and where the soil sits at the end:

| water, leach, flow | band | soil | bare cells | richest 1% of the cells hold | richest cell | barren |
|---|---|---|---|---|---|---|
| 0.1, 0.01, 0 | valley | 58,500 | 27% | 81% | 14,010 | 28.4 |
| | slope | 43,000 | 4% | 20% | 6,346 | 24.8 |
| | ridge | 26,000 | 2% | 3% | 31 | 13.6 |
| 0.1, 0.03, 0 | valley | 122,200 | 36% | 96% | 40,511 | 36.3 |
| | slope | 9,600 | 53% | 84% | 7,584 | 27.1 |
| | ridge | 700 | 57% | 10% | 2 | 16.6 |
| 0.2, 0.01, 0 | valley | 125,600 | 62% | 98% | 34,824 | 34.2 |
| | slope | 1,900 | 54% | 9% | 5 | 19.1 |
| | ridge | 3,100 | 27% | 4% | 4 | 9.4 |
| 0.1, 0, 0.1 | valley | 83,900 | 0% | 2% | 33 | 0.1 |
| | slope | 15,200 | 2% | 3% | 11 | 8.1 |
| | ridge | 500 | 18% | 6% | 1 | 10.9 |

- **The water makes wet and dry places.** The ridge's plants get half their sun (52 of water,
  21 of dry sun a step), the valley's nearly all (166; 4). On the old carrier (flow 0.1, no
  leaching) the world is e032's at 80%: floors 595-661 after the first winter against 680-825,
  the valley 71-82% of the bodies, the ridge's summer share 14-19%; the ridge's barren sun
  falls from 27.6 to 10.9 because it has less sun to lose.
- **The leaching on a terrain-only water puts the soil in the pits.** The water runs by the
  height alone, so it piles in the local pits (one cell holds 38,210 of water; the valley band
  is 61% wet, the pools one cell wide) and the leached soil piles with it: at leach 0.01 the
  richest 1% of the valley's cells hold 81% of its soil (one cell 14,010), 27% of the valley is
  bare, and the floors are 344-428 (e032's 60%). At leach 0.03 or water 0.2 the richest 1% of
  the cells hold 95% of the world's soil and the world falls year on year (floors 349 to 148,
  318 to 107). A cell uses 0.01 of soil a step whatever it holds; e019's soil flow leveled its
  lake (the drop of height plus soil, an eighth of it per step), which is why the old lake was
  wide and flat (14 per cell over the valley) and this one is a pit.
- **The ridge keeps its soil** (26,000 at leach 0.01 against 300-500 with the old flow) and
  cannot use it: half its sun is dry, and the ridge's share at the summer peaks is the still
  worlds' 28-32%.

### Round 2: the water's surface (`depth` 0.01)

| water, leach | winter floors, in order | valley share at the floors | summer peaks | ridge share at the peaks | eaten per step | sun lost: dry / barren | soil per band at the end | biters |
|---|---|---|---|---|---|---|---|---|
| 0.1, 0.01 | 223, 394, 434, 514, 362 | 56-74% | 1,448-2,532 | 27-34% | 25 | 29 / 77 | 73,200 / 39,100 / 18,100 | 32-42% |
| 0.1, 0.03 | 92, 67, 40, 22, 33 | 66-92% | 174-2,489 | 7-34% | 4 | 30 / 105 | 123,800 / 4,300 / 2,000 | 0% |
| 0.2, 0.01 | 70, 377, 539, 539, 592 | 39-73% | 1,587-2,542 | 25-31% | 28 | 42 / 61 | 69,200 / 35,200 / 20,800 | 0% |

| water, leach | band | water per cell | wet cells | soil | median per cell | richest 1% hold | richest cell | bare cells | barren |
|---|---|---|---|---|---|---|---|---|---|
| 0.1, 0.01 | valley | 165 | 76% | 73,200 | 8.8 | 8% | 249 | 8% | 31.0 |
| | slope | 81 | 20% | 39,100 | 5.2 | 6% | 62 | 8% | 28.9 |
| | ridge | 53 | 2% | 18,100 | 2.2 | 6% | 33 | 6% | 14.9 |
| 0.1, 0.03 | valley | 165 | 76% | 123,800 | 1.3 | 82% | 16,722 | 6% | 44.5 |
| | slope | 81 | 20% | 4,300 | 0.5 | 16% | 29 | 11% | 43.4 |
| | ridge | 53 | 2% | 2,000 | 0.3 | 7% | 7 | 14% | 27.6 |
| 0.2, 0.01 | valley | 194 | 80% | 69,200 | 7.7 | 8% | 394 | 6% | 35.4 |
| | slope | 68 | 19% | 35,200 | 4.9 | 5% | 52 | 0% | 22.4 |
| | ridge | 38 | 3% | 20,800 | 3.3 | 5% | 34 | 0% | 11.3 |

- **The lake spreads.** With the water's surface the deepest pool holds 418 (38,210 before),
  the valley is 76-80% wet cells, and at leach 0.01 the soil spreads with it: the valley's
  median cell holds 7.7-8.8 (0.5 before), its richest 1% hold 8% (81%), 6-8% of its cells are
  bare (27%). At leach 0.03 the soil still piles: at the lake's shore, where the water stops
  moving (the richest 1% hold 82%, one cell 16,722), and the world dies (4 eaten a step).
- **The lake does not share its soil.** A level lake does not flow, and the leaching moves
  only with the flow, so a cell the crowd strips is refilled by the rain alone (0.0006 a step)
  and not by the lake around it: the valley loses 31-35 of its sun a step for want of soil
  with a median cell of 8 (e032's valley: 0.2, with 14). The world eats 25-28 a step against
  67, and the floors are 394-514 at water 0.1 (60% of e032's after the first winter) and
  377-592 at 0.2, rising. e019's soil flow was two laws in one: the carrier downhill and the
  mixing of the lake.
- **The tooth is back** at water 0.1, leach 0.01: 32-42% of the bodies bite, a hunter of mass
  25-28 with 9-11 hard cells and 6-8 muscle in every band; a state of the poorer, crowded
  world (one seed).

### Round 3: the lake mixes (`mix` 0.05 and 0.2; water 0.1, leach 0.01, depth 0.01, flow 0)

| mix | winter floors, in order | valley share at the floors | summer peaks | ridge share at the peaks | eaten per step | sun lost: dry / barren | soil per band at the end | soil moved per step: leached / mixed | biters |
|---|---|---|---|---|---|---|---|---|---|
| 0.05 | 652, 547, 594, 608, 558 | 64-79% | 2,599-3,489 | 27-34% | 55 | 30 / 39 | 25,300 / 36,300 / 45,900 | 98 / 183 | 0% |
| 0.2 | 626, 696, 724, 743, 775 | 71-76% | 3,089-6,398 | 25-29% | 70 | 30 / 9 | 26,900 / 34,900 / 43,800 | 93 / 397 | 1-4% |
| e032 (flow 0.1) | 542, 819, 825, 680, 695 | 73-85% | 2,700-4,192 | 17-32% | 67 | 0 / 39 | 82,700 / 14,000 / 300 | - | 0-5% |

Per band at mix 0.2: the soil's median cell is 5.0 / 6.5 / 8.0 and its richest cell 7 / 8 / 10, no
cell bare; barren 2.2 / 3.4 / 1.4 a step; the bodies 1,323-1,639 / 1,094-1,408 / 759-979 at the
equinoxes (e032's 1,057-1,199 / 917-1,374 / 461-580). At mix 0.05: median 3.8 / 6.2 / 8.3, richest
15, no cell bare, barren 16.8 / 14.2 / 7.8.

- **The mixing feeds the crowd.** A stripped cell is refilled from its neighbors, so the sun
  lost for want of soil falls from 77 a step (round 2) to 39 at mix 0.05 and 9 at 0.2 (e032: 39),
  and the world eats 55 and 70 a step (e032: 67) while still losing 30 a step to dryness. The
  floors are 547-652 and 626-775 (e032's 542-825 on this seed), the peaks at mix 0.2 are
  5,765-6,398 against 2,700-4,192.
- **The soil is uniform, and uphill.** With the mixing the soil is 5-8 per cell in every band,
  no cell richer than 15, none bare; the ridge holds the most (44,000-46,000) and the valley
  the least (25,000-27,000), because the valley's crowd eats its soil and the mixing brings it
  back from where nothing eats. No lake: the water pools in the valley (165 per cell, 76% wet)
  and the soil does not. A soil spread thin over every cell feeds more sun than a lake: a cell
  uses 0.01 a step whatever it holds, so e032's 14 per cell in the valley and 0.06 on the ridge
  (barren 27.6 a step there) is worse than 5-8 everywhere.
- **The ridge is used more in summer** (25-34% of the bodies at the peaks against 17-19%) and
  emptied in winter as before (born below 72-98%): the ridge is dry and dark, the valley wet and
  lit.
- **The bodies** at mix 0.2: a light sitting gut (mass 8, 8-9 gut cells, 2,374 bodies at the
  end, from step 5,000) and a dense 4x4 mover (mass 32, 9 muscle, 55% flesh); no tooth (1-4%).

### The batch (seeds 1-3, 300,000 steps; water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0; against e032's batch)

Second half (winters 8-15). The floors from `pop.csv` every 1,000 steps; lineages of 5 or more at
the floors; the log's means over the second half; the top lineage at each lineage-log step from
150,000 (holders).

| world, seed | floors (winters 8-15) | lineages at the floors | valley share at the floors | summer peaks | ridge share at the peaks | eaten per step | sun lost: barren / dry | soil | fat in bodies | biters (max) | bodies with an eye (max) | holders |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| water, seed 1 | 745-814 | 2-5 | 69-76% | 3,314-3,991 | 31-34% | 79 | 11 / 26 | 86,700 | 41,500 | 2% | 29% | 4 |
| water, seed 2 | 720-874 | 2-3 | 74-81% | 4,880-5,236 | 29-33% | 73 | 9 / 25 | 96,000 | 32,600 | 4% | 35% | 4 |
| water, seed 3 | 659-736 | 4-16 | 80-86% | 3,064-3,430 | 31-34% | 78 | 24 / 25 | 75,900 | 52,900 | 23% | 13% | 13 |
| e032, seed 1 | 1,055-1,230 | 2-6 | 68-76% | 5,380-5,975 | 20-24% | 74 | 40 / 0 | 107,000 | 23,600 | 37% | 10% | 4 |
| e032, seed 2 | 716-792 | 3-7 | 71-81% | 2,624-3,391 | 19-23% | 65 | 52 / 0 | 90,400 | 39,300 | 6% | 20% | 5 |
| e032, seed 3 | 673-738 | 3-10 | 70-79% | 2,167-3,001 | 21-25% | 63 | 52 / 0 | 95,600 | 35,100 | 32% | 24% | 4 |

The soil per band at the end: 22,500 / 32,600 / 40,400, 22,400 / 36,300 / 45,600 and 11,400 /
31,200 / 45,400 (valley / slope / ridge): uphill in every seed.

- **The floors are e032's** in seeds 2 and 3 (720-874 against 716-792, 659-736 against 673-738)
  and 70% of them in seed 1 (745-814 against 1,055-1,230), where e032's seed held a hunter
  state of 1,100 at the floor (biters 37%) and the water seed did not (2%). The world eats
  73-79 a step against 63-74: it loses 25 to dryness and gets 30-40 back from the soil that is
  everywhere (barren 9-24 against 40-52).
- **The ridge is used in summer:** 29-34% of the bodies at the peaks against 19-25%; the
  valley's share at the floors is the same (69-86% against 68-81%).
- **The winners are e032's kinds** in every seed: a light sitting gut (mass 11-12, side 8-10)
  and a dense 4x4 mover (mass 28-31, 8 muscle, half flesh). Seed 2's mover grows to a 15-grid
  body of 51 mass with two sensors; seed 3 ends with 4-16 lineages at the floors, 13 holders of
  the top place, and a biter rising at 279,000 (bite 1.8, two hard cells; 23% biters). Bodies
  with an eye reach 29-35% in two seeds (e032: 10-24%).

## Conclusion

1. **The world stands: yes,** with the carrier whole (the water, the leaching, the surface, the
   mixing): e032's floors in two seeds of three, 70% in the third, and 10% more eaten. The
   leaching alone runs the world at 60% (the soil in the pits, then on the lake's shore).
2. **Wet and dry are places: partly.** The ridge gets half its sun and is emptied every winter
   as before; its summer share rises (29-34% against 19-25%) instead of falling, because its
   soil is the most, not the least. The bands hold the same bodies.
3. **The carrier matters: yes.** The wetness on the old flow gives 80% of the floors; the
   leaching alone 60%; the mixing 100%. e019's flow was two laws, the carrier downhill and the
   lake's mixing, and the crowd lived on the second.
4. **A drier world is a smaller world: not settled.** Water 0.2 without the mixing gave rising
   floors (377-592); not run with it.

Kept: the season world is water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0 from here (the
defaults stay 0: `water` 0 is e034 byte for byte). The premise stands in the code: what flows is
water; the soil is laid where the dead rot and the breath rains, leaches a little with the water,
and mixes where it is wet. The soil is uniform and uphill (5-8 per cell, the ridge holding the
most), and no lake of matter. Open: a body that needs water (a reason to move between places),
the rain on the ridge again (e033's question, with a carrier that keeps the soil there), a drier
world with the mixing, and the mixing's rate (0.05 gave 80%, 0.2 e032's floors; no real-world
anchor beyond a lake that mixes faster than a plant grows). The ridge is still not a place a
body holds through the winter; the ground store (vision item 2) is the next law for that.
