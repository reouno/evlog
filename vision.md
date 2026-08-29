# Vision

Where we are heading right now. Unlike `principles.md`, this changes as experiments teach us things.
Last updated: 2026-08-29.

## What the viewer should see

Not dots and numbers. Creatures with different shapes, eating and being eaten, splitting into
lineages that appear, spread, and go extinct. Nothing in that sentence is scripted: shape, diet,
predation, and species all come out of the genome and the world's rules.

## Three mechanisms, none of them predefined

1. **Shape comes from development.** The gene network of e002 is run on a small grid with the
   position of each cell as input. Settled expression decides whether a cell holds a block and what kind
   (hard, muscle, sensor, digestive). Limbs, fangs, and armor are not defined; they are arrangements
   of blocks that happen to work. Performance is derived from shape: mass from block count,
   speed from muscle over mass, attack from hard blocks at the front, defense from hard blocks overall,
   diet from the digestive blocks. Every block costs upkeep, so every trait has a two-sided trade-off
   for free (the lesson of e003).
2. **Predation comes from one rule.** "You can eat what your attack beats and your digestion accepts."
   Herbivores, carnivores, and escape artists are outcomes, not roles. The predator-prey arms race
   is also the best-known way to keep a world from settling (the problem seen in e001).
3. **Species are born, then detected.** Sexual reproduction with a compatibility limit (only similar
   genomes can mate) makes real species boundaries. For display, lineages are clustered by genome
   distance and named; births, splits, and extinctions of lineages are logged as events.

## Order of work

- e004 (done): shape from the genome, on its own.
- e005 (done): shape to function, plus predation, in the world.
- e006: species: sexual reproduction, lineage detection, event log.
- Later: learning, growth, aging, health as a layer on top of birth traits. Then 3D bodies (same development, 8x8x8).

## Kept from earlier experiments

- e001: the minimal loop (food grid, energy, split, die) is stable and cheap. Keep.
- e002: the genome map (promoter, tag + product, binding, settle, fixed table) is climbable and unreadable. Keep.
- e003: traits need two-sided trade-offs; pleiotropy is real; snapshots plus a replay viewer are enough to watch.
- e004: the e002 network grows bodies once position enters as morphogens (6 gradients in [-1, 1], binding on 2 of 4). Keep that rule as part of the laws. Bodies are dense by default and mutations move regions; let e005's upkeep act on both before changing the read-out.
- e005: attack = min(front hard, muscle) is the rule that made a food web; with hard alone one immune body won in 10,000 steps. Two body types recur (armored grazer, omnivore with teeth) and the world keeps moving. Costs scale the population; trade-offs decide what evolves. Open: no pure carnivores (prey is worth little), sensors unused, development at birth makes the run slow (fix before e006's long runs).
