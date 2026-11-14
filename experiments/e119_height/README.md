# e119: a height is what the wood can stand - rung 2 corrected (#135)

Date: 2026-11-15

## Purpose

e118 put plants at metres on the map and the land stayed a thicket: after 500 years crowns stood over a tenth of
the ground and no line of trees stood over 10 m, though old trees held wood for 16 m. A plant's height was the least
of three things, and one of them was a number in its genome (`height`, sown about 1.6 m): it stopped the height
while the wood went on. Animals will live among these plants (rung 3): before they stand on the land, a height is
made what the wood can stand (agreed 2026-11-15).

## Hypothesis

With a height that is what the wood holds up and can stand, and nothing else changed (the same map, the same 256
sown genomes), the land parts into wood and open ground in 120 years:

1. it stands with every ledger closed;
2. crowns stand over 20-70% of the land with soil (e118: 5.7%);
3. old trees are tall: half of the trees that have stood over 50 years are over 12 m, the tallest over 20 m;
4. a wood's floor is dark: where crowns stand over half of a 125 m cell the field holds under half of what it does
   where they stand over less than 5%;
5. open ground remains, by fire and cold: a fifth or more of the land's cells have crowns over less than 5% of them,
   and they burn more than the wooded ones or are colder;
6. water places wood: the lowlands' wettest third holds 1.5 times the driest third's wood or more (e118: x1.0).

Not a failure of this rung: wood closing wherever water allows - nothing grazes yet.

## Method

The one law changed (`src/plants.rs`, `tree_height` and `stand_height`): a plant's height is the lesser of what its
wood holds up over its leaves (`sigma`: 1.3 kg of wood a kg of leaf a m) and what its wood can stand as stems
(`h_stem`: 4.2 m at a kg, by the fourth root). e118 also took the least with the genome's `height`. That trait is
kept in the genome so that the sowing is e118's to the gene, and nothing reads it.

The cycle it changes - **light** (e118's first):

- *takes from whom*: a plant that sends matter to wood rises over its neighbours and takes their light, the tallest
  first; now every plant with wood does, for as long as it lives;
- *what it costs*: wood is a share of the income not sent to leaf, root or seed; its B breathes; a height doubles
  for sixteen times the wood of one stem; crowns as wide as 0.35 of the height meet and shade each other; storms
  fell the tall (`h_storm`);
- *what refills the light*: a death (a life is as long as its wood is tough and its body woody, `life_max`), a
  storm, a fire;
- *what limits it*: where income is small - a dry summer, a short season, a soil poor in A and B - wood is lost as
  fast as it is made at a lower height; a fire takes a stand back to seed;
- *the balance expected*: tall closed woods on wet, warm, unburnt ground with a thin field under them; lower and
  more open wood where summer is dry; grass and shrubs where it burns and in the cold north and on the tops. A
  plant with little wood lives a year or two and stays low: the forms are the wood's share and its toughness, not
  a number. A genome can still stop its height, by sending its matter elsewhere when it is large (a conditional
  gene on its size).

Cost: every stand with wood now grows to a tree, so trees as things may be several times e118's 170,000 and a year
several times its 44 s (stated before the run, which measures it).

World: `base/worlds/isles1.params base/worlds/isles16.params experiments/e119_height/worlds/plants16.params`
(e118's). Runs, on Ubuntu with six threads:

- `main`: 10 bare years, 120 with plants, read at year 130 against e118's `main` by `read.py` (e118's, with the
  land by the share of its cells under crowns added). No pilot apart from it: a pilot is this run's first years,
  so the run is watched by the rules below and its cost read from its log.

**Stop early if:**

- `c_err` > 1e-6 at 20 (the living's ledger does not close)
- `field` < 0.001 at 20 (nothing grows)

## Result

`main` (10 bare years, 120 with plants, 100 minutes on Ubuntu; read at year 130, maps the mean of years 121-130;
`read.py`, `results/main_reading.csv`, `results/provenance.csv`; e118's `main` beside it in brackets):

- **It stands.** Ledgers: water 6e-13, A 1e-12, B 6e-13, matter 1e-10 at worst. A year of plants takes 49 s on six
  threads (44): the cost feared did not come, with 280,049 trees (168,813).
- **Trees are tall, and the wood is three times e118's within 30 years.** Trees' wood 1.03 kg a m2 (0.34), and
  it has not moved since year 40: 0.93, 0.96, 1.01, 0.94, 1.01, 1.03 at years 40, 50, 70, 90, 110, 130. The tallest
  tree is 57.0 m (16.9) and still rising (33 m at year 40, 48 at 70). Half of the trees are under 9.0 m, a tenth
  over 14.4 m, 1% over 26.4 m; the 3.6% over 20 m hold half of the wood. Of the 21,391 that have stood 50 years or
  more, 61% are over 12 m, half over 13.4 m, a tenth over 27.8 m, and their 128 kg of wood (the median) could stand
  14.1 m as a stem: a height follows its wood now.
- **The land parted into wood and open ground.** Crowns stand over 23.5% of the land with soil (5.7%) and take
  11.4% of its light (3.4%). Of the 125 m cells 19% are closed woods (crowns over half of them or more; 80% on the
  mean), 16% have crowns over 20-50%, 18% over 5-20%, and 46% are open (under 5%; 0.9% on the mean). The field
  holds 1.30 kg a m2 (1.90), litter 3.26.
- **A wood's floor is dimmer, not dark.** The field holds 0.87 kg a m2 under closed woods against 1.38 on open
  ground (x0.63). Crowns over 80% of a closed wood's ground take 25% of its light: a tree of 9 m carries 3 kg of
  leaf on a crown of 31 m2.
- **Open ground is the cold, then the burnt and the dry.** Open cells are 10.8 C on the year's mean, wooded ones
  14.0 C; they burn alike (1.94 and 1.90% of the ground a year). Of the cells under 9 C 79% are open (38% of the
  open ground); of those that burn 2% a year or more and are not cold 45% (19%); of the rest 34% (42%) - and
  those are drier and on thinner soil than the wooded rest: 600 mm of rain against 713, a soil holding 92 mm
  against 134, 127 m up against 218. Where 2% or more burns a year the wood is 0.70 kg a m2, where nothing burns
  2.26.
- **Rain does not place the wood across the lowlands.** Their wettest third (over 699 mm) holds 1.23 kg of wood a
  m2, their driest (under 482 mm) 1.68: x0.7, since the wet lowlands are the cold north. Band by band, wettest
  third over driest: x0.6 at 44-49 N (both burn 6% a year), x0.8 at 49-54 N, x1.4 at 54-59 N, x3.4 at 59-64 N.
- **No tree line by height; the north has trees.** The bands at 600-1,000 m hold the most wood (5.9-8.3 kg a m2);
  crowns stand over 12% of the ground above 1,400 m, with a tree of 35 m. The lowlands at 59-64 N are 8.4% under
  crowns (0.1%), those at 44-54 N 26-28%.
- **Lives turn over; the lines are the sown ones, in two forms.** 31,672 trees fall a year (11.3%; 8% over the last
  fifty years); half of the trees have been trees for under 10 years, 1% since year 30. Four sown genomes are 80%
  of the trees (31, 24, 14, 11%; in e118 two were 94%), 766 genotypes hold a tree (138), and what was born after the
  sowing is 2.4% of the living mass (1.3%). Two of the four are tall - medians 11 m, 1% of each over 26 and 35 m -
  and hold 69% of the wood with 35% of the trees; the other two stay low (99% of their trees under 12.1 m) and hold 15% of it with
  44% of the trees; half of their trees have stood under 3 and under 8 years.
- **Leaves hardly differ north and south**, as in e118: the field's optimum 12.8 and 11.8 C, shedding 0.42 and 0.44.
- On the screen (`shots/`): large trees stand over small ones with a stream between them - a wood in layers, where
  e118's was one height. Young trees stand in rows, on the 5 m grid they were born on, and the woods' edges are
  still straight where the soil's cells differ.

## Conclusion

1. **Stands, with every ledger closed**: yes.
2. **Crowns over 20-70% of the land**: yes, at its low end - 23.5%, settled since year 40.
3. **Old trees are tall**: yes - 61% of the trees that have stood 50 years are over 12 m, the tallest is 57 m.
4. **A wood's floor is dark**: no - the field under closed woods holds x0.63 of the open ground's, asked under
   half. Crowns there take a quarter of the light.
5. **Open ground remains, by fire and cold**: yes - 46% of the cells, 3.2 C colder than the wooded ones. They do
   not burn more; fire lowers the wood where it burns but leaves over half of the burnt cells wooded.
6. **Water places wood**: no - x0.7 across the lowlands. Rain places it only inside one climate (x1.4 and x3.4 in
   the two northern bands) and by the soil's holding; across the map warmth comes first.

The genome's limit was what bound e118's wood: without it the same sowing makes three times the wood in 30 years
and a land of woods and open ground. What bounds it now is a tree's life and its leaves. A tenth of the trees fall
a year, so few grow old, and the wood stays at 3 kg a m2 where trees stand. A crown carries little leaf, so the
floor keeps its light and a field lives under the trees. Neither is a fault for the next rung: an animal finds
open ground with 1.4 kg of field a m2 on nearly half of the land, closed woods on a fifth, and food under both.

Holds under: one sowing of 256 genomes, one terrain seed, 120 years, nothing grazing. Not built: soil and water
finer than 125 m (the woods' straight edges), a fire front that is round, trees born off the 5 m grid, small
eaters, the sea's producers.

`vision.md`: rows B (plant foods, plants as places). `foundation.md`: the height law, rung 2's reading, the cost.
Kept for rung 3 as it is, in this crate: the laws go to `base/` when animals stand on them.
