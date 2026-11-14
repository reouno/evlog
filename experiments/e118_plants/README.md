# e118: plants at metres - rung 2 again (#135)

Date: 2026-11-14

## Purpose

The map at an animal's size stands (e117): islands with a dry-summer south, a snowy north, wet heights and lees. What
is watched will be animals, and an animal lives among plants of its own size: a tree is a thing it stands under, grass
a field it eats. `base/`'s producers are cohorts on cells of 125 m; here they are rebuilt at metres (design agreed
2026-11-14, comment on #135). Nothing eats them yet.

## Hypothesis

The base's producer law, run on fine cells of 5 m with trees as things, light through crowns, one soil a 125 m cell,
fire at 5 m and the year's water, makes a land whose wood and open ground are placed by the climate:

1. it stands 100 years with every ledger closed;
2. crowns cover 20-70% of the land, and at least three times more wood stands on the wet windward ground than in the
   lee and on the south's lowlands;
3. there is a tree line;
4. leaves differ between north and south (toughness or shedding);
5. the trees standing at year 100 are not the sown ones: lives turn over.

Not a failure of this rung: wood closing wherever water allows - nothing grazes yet (rung 3).

## Method

The cycles (what takes from whom, what refills it, what limits it, the balance expected):

1. **Light**: a tree takes it from the field and from shorter crowns under it; refilled by a death or a fire; limited
   by the wood a height costs and the life wood gives. Expected: a closed wood with a dark floor and little grass,
   seedlings waiting under it for a gap.
2. **Water**: every plant rooted in a 125 m cell draws on its one soil by its roots; the fronts refill it; the south's
   rainless summer empties it. Expected there: deep roots, plants that pass the summer as seed or store, and green
   strips beside streams and ponds, where the groundwater is within any root's reach.
3. **Fire**: lightning lights dry fuel the sun reaches; grass and litter are the fuel, and a flame kills what stands
   under it. Grass refills its fuel in a year, a wood's shaded floor dries slowly. Expected: open land that stays
   open where it is dry, an edge of wood and grass set by fire, not by a line on the map.
4. **Cold and snow**: frost takes tender leaves; under lying snow the field has no light and no frost. Expected: a
   short season in the north and on the heights, tough leaves kept or leaves shed, no trees above some height.

The crate (`src/plants.rs`; the ground, air and water are `base/`'s):

- **the field**: a fine cell of 5 m with soil (not water; not steeper than 50 degrees) holds up to three cohorts, a
  litter and a seed bank, by `base/src/life.rs`'s law for a cohort;
- **a stand thins into a tree** (the third pilot's finding): a stand of the field is stems. Each stands as high as its
  wood lets one stem stand - 4.2 m at a kg by the mass's fourth root (`h_stem`: wood of 500 kg a m3 in a stem as
  slender as trees are, 50 d^(2/3), half the height at which it buckles; 20 m at half a tonne) - and their crowns,
  0.35 of the height in radius (`crown_h`), fill the ground: so a stand is as tall as h_stem^2 crown_h sqrt(pi w)
  for w kg of wood a m2, many stems while low and fewer as it grows. Thinned to one stem a cell (8 m on cells of
  5 m) it is one plant rooted there, the whole of it, with a place, a height and a crown 0.35 of its height in
  radius - the stand's own crowns, so nothing changes the day it is counted a tree; the disc beyond its own cell is
  shared among the cells about it, the nearer the more. Light falls through the crowns over a cell, the tallest
  first, then through the cell's field. A tree with no leaf and no store left (under a thousandth of its mass,
  `bare`) is dead and falls. (The base's height is a ratio of wood to leaf: a seedling of a gram was 4 m tall. The
  pilots made a tree of a stand at 3 m with the part its crown held: one whip a cell, a twelfth of its light, that
  did not grow in thirty years. The first long run, `dense`, packed a new tree's leaves into a crown at a leaf
  area of 4: see Result.)
- **water** as above (`wet_reach` 10 m, `wet_rise` 2 m);
- **rot frees A and B to the roots in the same step** (after the first pilot): the base lets them lie a step in the
  soil, under the rain, before roots take them;
- **humus** (after the second pilot): 0.3 of the A and B that rot frees stays in the soil's organic matter
  (`humify`) and comes free at 0.05 a year at 20 C in a full soil (`humus`: a residence of 20 years there, 40 at
  10 C); the land starts with an old soil's humus, 300 years of its rock's giving at a soil of mean depth
  (`old_soil`: about 180 g of A and 210 g of B a m2). On bare rock the land's whole capital a century on is what
  its rock gave in that century (0.4 g a m2 a year, a third to two thirds of it washed out): scrub. A real soil
  holds thousands of years of it;
- **fire** from fine cell to fine cell, a fuel's drying in full shade a fifth of the open ground's (`fire_shade`);
- **snow**: a field cohort shorter than the lying snow (a mm of its water is 3.3 mm of snow) has no light, no frost;
- **seeds** fall near or go with the wind from their plant's height, in metres; a tree's from under its crown;
- **the sowing**: 256 random genomes; for five years a founder's seed falls on every cell with soil at each release,
  so that a place is filled by what suits it of all that was sown (e109's mosaic of what was sown took centuries).
- A plant step is 5 days (`life_every` 37) and seeds leave every 60 days (`seed_every` 12): a step a day took 150 s
  a year for 1.6 million cells, mostly memory.
- Left out on purpose: the small eaters of leaves (they return as the 125 m field of small life with rung 3), the
  sea's producers, seeds carried by rivers.

World: `base/worlds/isles1.params base/worlds/isles16.params experiments/e118_plants/worlds/plants16.params`.
Runs, all on Ubuntu with six threads:

- `pilot` (10 bare years, 20 with plants; daily steps first, then 5 days): 54 s a year; every ledger closed; 0.40 kg
  a m2 of field and 0.02 of trees after twenty years, the soil's A at 0.02 g a m2 - starved.
- `pilot2` (rot's A and B to the roots at once; stopped at year 14): the land takes in 0.4 g of A a m2 a year and
  loses 0.12-0.34; its living hold 1 g after four years.
- `pilot3`, `pilot4` (humus and an old soil; the stand that thins; 10 bare years and 18 to 50 with plants): stands
  reach 8 m in five to seven years and the first trees 14.5 m fifteen years after the sowing.
- `dense` (10 bare years, 120 with plants; 90 minutes): the first long run, a tree's crown as wide as its leaves
  need at a leaf area of 4.
- `main` (the same, a tree's crown its height's): the run read below.

**Stop early if:**

- `c_err` > 1e-6 at 20 (the living's ledger does not close)
- `field` < 0.001 at 20 (nothing grows)

## Result

`main` (10 bare years, 120 with plants, 90 minutes; read at year 130, maps the mean of years 121-130; `read.py`,
`results/main_reading.csv`, `results/provenance.csv`):

- **It stands.** Ledgers: water 6e-13, A 1e-12, B 6e-13, matter 1e-10 at worst. A year of plants takes 44 s on six
  threads (growth 28, seeds 13), ten times the bare map's.
- **The land is a thicket with young trees in it.** Field 1.90 kg a m2 (1.71 half way), litter 3.27, trees' wood
  0.34 (0.17 half way: still rising). Of the fine cells with soil the field's stands are under 0.5 m on 13%, 0.5-2 m
  on 37%, 2-5 m on 27%, over 5 m on 18%, and 6% have no leaf. 168,813 trees stand on 10.3% of them; their crowns
  stand over 5.7% of the ground and take 3.4% of the light; 11% of the 125 m cells are a fifth or more under
  crowns. Heights: half are 5.2 m, a tenth over 8.5 m, the tallest 16.9 m.
- **Trees are placed by warmth and fire, not by water.** Under crowns: 11.0% of the ground where the year's mean is
  over 15 C, 4.8-6.0% at 11-15 C, 0.6% under 9 C; lowlands at 44-49 N 7.3%, 49-54 N 6.4%, 54-59 N 3.2%, 59-64 N
  0.1%. The lowlands' wettest third 4.5% and 0.28 kg of wood a m2, the driest third 5.9% and 0.28 (x1.0). Where
  2% of the ground or more burns a year (690 cells) 2.1%, where none does 6.7%.
- **A tree line**: 4.4-12.2% of the ground is under crowns in the bands of height up to 1,400 m and 1.0% above
  (6.9 C at 1,200-1,400 m, 4.7 C above); 0.1% on the northern lowlands (6.9 C in these years).
- **Leaves hardly differ north and south.** Field at 44-54 N against 54-64 N: leaf A 0.72 and 0.68%, shed 0.44 and
  0.45 a year, optimum 12.8 and 11.9 C. Trees: shed 0.23 and 0.28, optimum 13.6 and 12.7 C.
- **Lives turn over, lines do not.** 0.6% of the trees of year 130 were trees by year 30; 13,013 fall a year (7.7%);
  their mean age is 33. But two of the 256 sown genomes are 94% of the trees (74% and 20%), and what was born
  after the sowing is 1.3% of the living mass.
- **A tree's wood grows and its height does not.** Trees for 5-20 years hold 29 kg of wood at 5.2 m, for 20-50
  years 89 kg at 8.5 m, for over 50 years 304 kg at 8.5 m - a stem of 304 kg could stand 17.5 m. The height is the
  genome's limit (the two lines' are 5.2 and 8.5 m as they stand); wood goes on by the genome's share for it.
- **`dense`**, the first long run (a new tree's leaves packed into a crown at a leaf area of 4, a seventh of its
  cell): 252,065 trees whose crowns stood over 0.9% of the ground; 44% of them had a leaf at the winter's end, the
  median tree over 40 years old none. Counted a tree, a stand's light halved. In `main` 98% have leaves.
- On the screen (`shots/`): a wood reads as a wood from a walker's height and from above, a thicket as a thicket;
  the woods' edges are straight lines 125 m apart where the soil's cells differ, and fire scars are diamonds.

## Conclusion

1. **Stands, with every ledger closed**: yes.
2. **Crowns over 20-70% of the land, three times the wood on wet ground**: no. Crowns stand over 5.7% after 120
   years and are still spreading (trees' wood doubled in the last 60), and water does not place them: wet and dry
   lowlands hold the same wood. Warmth and fire do.
3. **A tree line**: yes, by cold - at 1,400 m and at about 59 N.
4. **Leaves differ north and south**: no - an optimum 1 C apart, shedding the same.
5. **The trees at year 100 are not the sown ones**: as lives yes, as lines no - the trees are two founders' lines.

What bounds the wood is not the climate but what was sown and how a height is made: a tree's height is its genome's
limit, the two lines that became trees stop at 5.2 and 8.5 m, and 120 years is a few tree lives - too short for a
taller line to be born and spread (1.3% of the mass is new). Under crowns as thin as theirs (a leaf area of 1-2)
the field keeps most of its light, so no floor goes dark and no wood closes.

Holds under: one sowing of 256 genomes, one terrain seed, 120 years (a transient: `long`, 500 years of the same
world, is running), nothing grazing. Not built: soil and water finer than 125 m (the woods' straight edges), a
fire front that is round, small eaters, the sea's producers.

`vision.md`: rows B (plant foods, plants as places). `foundation.md`: producers at metres and rung 2's reading.
Kept for the next rung as it is, in this crate: the laws go to `base/` when animals stand on them.
