# e036 A store in the ground

Date: 2026-09-06

## Purpose

Since e032 the world has a winter by height: the ridge is dark half the year, and it is emptied
every autumn and filled every summer from below (72-98% of its winter bodies are born in another
band). No lineage is the ridge's, because a cell's plant is gone in a few steps of grazing and
the dark grows nothing. The user's premise (issue #36): in the real world a dark place still
feeds animals through the winter, out of what the summer left in the ground - seeds, roots,
tubers, bark. Today a cell's surplus (the growth past the plant's cap of 8) falls as fruit
around it (e022) and rots into the soil at 1% a step, and soil in the dark is worth nothing.
This experiment gives the ground a store of plant matter that stands where it grew and is dug
out slowly, and asks whether the ridge becomes a place a body holds through the winter.

## Hypothesis

1. **The store fills and stands.** In summer the world makes 164 of fruit a step, so a ground
   store of a few per cell fills in a few hundred steps of surplus, and it is still there at
   the autumn equinox because the crowd can only dig a share of a bite out of the cells it
   stands on.
2. **The ridge is held through the winter** where the store is deep enough and gives fast
   enough to pay a body's upkeep: a body of mass 21 pays 0.074 a step, and 8 gut blocks digging
   half a bite take 0.08 a step, so at `dig` 0.5 a body can live on the store alone and at 0.1
   it cannot. The measure is the ridge's winter bodies and the share of them born there
   (`pop.csv` `pop2`, `cross2`).
3. **The two rates are in tension.** The store is fed by what the crowd does not eat and drained
   by the crowd; a store fast enough to winter on is also eaten in summer, so the ridge's store
   at the equinox falls as `dig` rises, and the world's floors rise only if the store survives
   the summer.
4. **A store is matter out of the cycle.** The world holds 131,000 of matter and turns it over
   as fruit every few hundred steps, so a store of `root` per cell locks up to root x 16,384:
   at root 4 half the world's matter, which the soil has to give up. The world's floors fall
   with the locked matter unless the ridge's winter pays for it.

## Method

Code: e035 (`experiments/e035_water`) as `e036_ground` with one law about the world, off by
default (`root` 0 is e035 byte for byte; checked on seed 9 for 2,000 steps: `agents.csv`, `lineages.csv`,
`events.csv` and `dist.csv` byte for byte, and `pop.csv`, `places.csv` and `log.csv` equal on
every column they share):

- **The ground store** (argument 29, `root`: what a cell's ground holds, in the plant's units -
  the plant's cap is 8). The growth past the plant's cap, which falls as fruit since e022, goes
  into the ground up to `root`; what the ground cannot hold falls as before. What lies in the
  ground does not rot, is not shaded and is not eaten by a bite: it stands until it is dug up.
  Where it is laid is argument 31, `rootat`: in the ground of the cell it grew on (`grew`,
  round 1) or of the cell the fruit falls on (`fell`, round 2, the ring of 8 of e022's fall).
- **Digging** (argument 30, `dig`: a share of a bite). A gut block over a cell digs `dig` x BITE
  out of the cell's ground per step, besides its bite from what lies on the cell. What is dug is
  plant matter and is digested as plant. `dig` 1 doubles what a body can eat in a step.

A cap per cell, not a share of the fruit: the fruit is the world's whole matter every few
hundred steps, so a store that took a share of it and never gave it back would swallow the
world; a cap locks at most root x cells and refills in a few hundred steps of surplus.

The cost is one f64 field of the grid and two comparisons per cell per step: nothing measurable.

**Runs.** All on seed 9, 100,000 steps (five winters), one thread each, at once on the Mac (4 of
12 cores for round 1 and 3 for round 2, 25 minutes each round), in e035's season world (`winter high` 2, water 0.1, leach
0.01, depth 0.01, mix 0.2, flow 0, rain flat, store 5, grow). The pilot brackets the two rates:

| run | root | dig | asks |
|---|---|---|---|
| deep and fast | 4 | 0.5 | the store as designed: a body can live on it |
| shallow and fast | 1 | 0.5 | how much has to be locked up |
| deep and slow | 4 | 0.1 | the rate knocked out: the store fills but cannot pay a body's upkeep |
| deep and open | 4 | 1 | the store as ordinary food: does the season go away |

Round 2 asks the one thing round 1's failure pointed at (the surplus is made on a few hundred
cells under the crowns, so a store laid where it grew is a larder the crowd stands on): the same
law with the store laid where the fruit falls - root 4 with dig 0.5 and 0.1, and root 8 with
dig 0.5. Control for both rounds: e035's pilot on seed 9 (mix 0.2, no store). A batch on seeds
1-3 for 300,000 steps (3 cores, about 45 minutes) only if a pilot shows bodies wintering on the
ridge.

**Measures.** `pop.csv` every 1,000 steps: the bodies per band (`pop0-2`), of those the ones born
in another band (`cross0-2`), the soil per band and the store per band (`root0-2`) - the winter
floors, the ridge's winter bodies and where they were born, and whether the store stands through
the winter. `log.csv`: `root_stock` (in the ground now), `stored` and `dug` (per step), against
`fruit`, `fruit_eaten` and the food eaten. `places.csv` at the equinoxes: `root` and
`root_intake` per band, beside the bodies, the barren and dry sun and the soil. The winners from
`lineages.csv`; the maps of the store in `soil.jsonl`.

## Result

### Round 1: the store where the surplus grew

From `pop.csv` (the floors and peaks of each season window, the ridge's bodies and the share of
them born in another band, the store per band) and `log.csv` (second half, per step).

| root, dig | winter floors, in order | ridge at the floors (born below) | summer peaks | ridge store at the floor / at the peak | stored / dug per step | store standing | trees | fruit | barren |
|---|---|---|---|---|---|---|---|---|---|
| 4, 0.5 | 735, 727, 676, 674, 598 | 54-91 (89-100%) | 3,096-4,887 | 4-14 / 448-774 | 22.63 / 22.64 | 1,459 | 108 | 56.9 | 18.9 |
| 1, 0.5 | 723, 711, 720, 647, 565 | 37-79 (96-100%) | 2,854-5,298 | 0-3 / 97-164 | 16.79 / 16.79 | 394 | 134 | 75.1 | 10.6 |
| 4, 0.1 | 298, 590, 584, 625, 705 | 16-72 (94-100%) | 2,875-3,925 | 462-1,113 / 939-2,153 | 9.17 / 9.20 | 2,999 | 52 | 54.9 | 20.1 |
| 4, 1 | 618, 664, 696, 757, 816 | 24-56 (88-98%) | 4,013-5,747 | 1-51 / 283-648 | 23.98 / 23.98 | 744 | 90 | 47.6 | 16.4 |
| e035 (no store) | 626, 696, 724, 743, 775 | 36-63 (72-92%) | 3,089-6,398 | - | - | - | 239 | 95.7 | 8.8 |

- **What is laid is dug the same step.** In every run the store's fill and the digging are the
  same number to two decimals (22.63 and 22.64, 16.79 and 16.79, 23.98 and 23.98, 9.17 and 9.20),
  and the standing store is 394-2,999 of the 16,384 (root 1) or 65,536 (root 4) the ground could
  hold: 1-5% full. The store is not a store, it is a pipe.
- **The ridge is not held.** Its bodies at the winter floors are 16-91 against the control's
  36-63, and 88-100% of them were born in another band against 72-92%. No lineage is the ridge's
  in any run.
- **The store fills only under the crowns.** 72% of the surplus still falls as fruit (56.9 a step
  against 22.6 stored) while the ground is 2% full, so the cells that make the surplus - the
  hundred-odd crowns, where the canopy's light lands past the cap - are the only ones with a
  full store, and the crowd stands on them.
- **It costs the world sun.** The store takes the fruit out of the fall, which used to spread it
  over the ring of 8 and rot into the soil the mixing shares, so the sun lost for want of soil
  rises from 8.8 a step to 10.6-20.1 and the trees fall from 239 to 52-134.

### Round 2: the store where the fruit falls

| root, dig | winter floors, in order | ridge at the floors (born below) | summer peaks | ridge store at the floor / at the peak | stored / dug per step | store standing | fruit | barren |
|---|---|---|---|---|---|---|---|---|
| 4, 0.5 | 682, 698, 684, 667, 647 | 55-80 (95-100%) | 3,071-5,846 | 8-30 / 1,230-2,173 | 49.46 / 49.48 | 3,990 | 27.4 | 19.9 |
| 8, 0.5 | 799, 828, 741, 700, 805 | 54-76 (74-100%) | 3,061-5,270 | 48-566 / 2,021-4,683 | 53.00 / 52.99 | 8,461 | 22.9 | 20.1 |
| 4, 0.1 | 528, 648, 738, 770, 750 | 33-73 (90-100%) | 2,729-4,272 | 1,570-2,561 / 4,222-6,069 | 22.08 / 22.18 | 10,972 | 73.0 | 11.1 |
| e035 (no store) | 626, 696, 724, 743, 775 | 36-63 (72-92%) | 3,089-6,398 | - | - | - | 95.7 | 8.8 |

- **The fall spreads the store** over the ring of 8 of every crown: the ground holds 3,990-10,972
  against round 1's 394-2,999, and the ridge's summer store is 1,230-6,069 against 448-2,153.
- **It is dug out before the dark ends.** Through one winter (root 4, dig 0.5) the ridge's store
  runs 1,243 at step 68,000, 752 at 70,000, 352 at 72,000, 70 at 74,000 and 4 at 76,000, the
  bottom of the winter, while its bodies run 931, 690, 435, 117, 90. The store carries the
  ridge's crowd for two or three thousand steps of the eight thousand dark ones and is then gone.
- **The ridge's winter is what it was.** 33-80 bodies at the floors, 74-100% of them born below,
  against the control's 36-63 and 72-92%: within the spread of one seed, unchanged. So are the
  world's floors (647-828 against 626-775).
- **A store that stands is a store nobody can live on.** At dig 0.1 the ground holds 1,570-2,561
  on the ridge right through the winter - and 8 gut blocks digging a tenth of a bite take 0.016 a
  step against a body's upkeep of 0.074. The store stands because it is worthless.
- **The arithmetic.** At the autumn (step 70,000) the ridge holds 752-1,502 of store and carries
  690-695 bodies that pay 51 a step between them: fifteen to thirty steps of their upkeep. To
  winter even 100 bodies through the 8,000 dark steps costs 59,000 - 42% of the 140,186 of matter
  in the whole world.
- **Only a full bite makes a sitter.** The bodies are the control's kinds in six of the seven
  runs (mass 20.6-23.2 against 17.6, muscle 3.9-5.5 against 2.95, gut 7.1-8.7 against 7.1 - a
  little larger, because the digging adds to the bite). At dig 1, where the ground gives a whole
  bite of its own, the median body halves: mass 10.5 with 1.2 muscle. A body that is fed by the
  ground under it does not need to walk.

## Conclusion

**Not kept, and no batch was run.** A store in the ground does not make the ridge a place a body
holds through the winter, at any of the six rates tried and either way of laying it. The two
rates the law needs are in conflict, and the pilot puts a number on it: a store fast enough to
pay a body's upkeep (dig 0.5: 0.08 a step against 0.074) is dug out as fast as it is laid, and a
store slow enough to stand through the summer (dig 0.1: 0.016 a step) cannot keep a body alive.

Behind that is the world's arithmetic, e031's lesson again: the dark on the ridge is 8,000 steps
long and a body pays 0.074 a step, so a hundred bodies wintering there would eat 42% of the
world's matter. The ground of 5,461 cells cannot hold that, and if it did the world would have
nothing left to circulate: the store already costs the crowd, taking the fruit out of the fall
that spread it and rotted into the soil (the sun lost for want of soil doubles, 8.8 to 20 a step,
and the trees fall from 239 to 52-134).

What this changes for the project: **wintering in place is not a question of the ground, it is a
question of how long a body can carry.** A body's own store (e030, `store` 5) holds 5 per unit of
mass - 105 for a body of mass 21, or 1,400 steps of upkeep, a sixth of the dark. The next thing
to try for a lineage of the ridge is a body that can carry the winter (a much deeper fat, or a
body that spends less while it waits), not a richer ground. Issue #36 is answered and closed;
`root` and `dig` stay in the code as arguments, 0 by default.
