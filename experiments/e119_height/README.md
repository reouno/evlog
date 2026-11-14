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

(pending)

## Conclusion

(pending)
