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
- **a tree**: a cohort that grows past 3 m (`h_thing`: a crown about 2 m wide) becomes one plant rooted in its cell,
  with the part of the stand its crown holds; the rest stays in the field under it, no taller than 3 m, and takes the
  place when it dies. A crown is as wide as its leaves need at a leaf area of 4 (`lai_crown`), at most 0.35 of its
  height (`crown_h`), and lies over the fine cells within it. Light falls through the crowns over a cell, the tallest
  first, then through the cell's field;
- **a stem** (added after the first pilot): a plant is no taller than its wood can stand as one stem, 4.2 m at a kg
  by the mass's fourth root (`h_stem`: wood of 500 kg a m3 in a stem as slender as trees are, 50 d^(2/3), half the
  height at which it buckles - 20 m at half a tonne; the pilots ran at 2.9, a stout 30 d^(2/3), which asks 2.3 t for
  20 m). The base's height is a ratio of wood to leaf, so a seedling of a gram was 4 m tall and 27,000 "trees" stood
  a year after the sowing;
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
- `pilot3` (humus and an old soil; 10 bare years and 50 with plants): whether a wood grows in decades.

**Stop early if:**

- `c_err` > 1e-6 at 20 (the living's ledger does not close)
- `field` < 0.001 at 20 (nothing grows)

## Result

(pilot running)

## Conclusion

(open)
