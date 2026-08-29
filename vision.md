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
3. **Species are born, then detected.** Lineages are groups of living agents linked by gene-list
   distance (the same rule that would let genes flow between them); births, splits, merges, and
   extinctions of lineages are logged as events. e006 found that the boundaries come from mutation and
   drift, not from mating: sexual reproduction under the compatibility limit is in the code but does
   not shape the lineages.

## Order of work

Done: e004 (shape from the genome), e005 (shape to function, predation), e006 (lineages, event log),
#9 (viewer: a white dot on agents that can bite, block legend, teeth and armor per lineage label).

Next, in this order (GitHub issue numbers):
1. #10 e007: a bigger world (256x256) with patchy food. Do eyes get a reason to exist? The
   environment half of #8.
2. #7 Make prey worth eating (energy stored in a body that grows). No pure carnivores so far.
3. #8 Neighbor perception in the policy (prey vs threat as inputs), once e007 says whether
   sensors appear at all.
4. #4 Learning, growth, aging, health as a layer on top of birth traits.
5. #5 3D bodies (same development, 8x8x8).

## Kept from earlier experiments

- e001: the minimal loop (food grid, energy, split, die) is stable and cheap. Keep.
- e002: the genome map (promoter, tag + product, binding, settle, fixed table) is climbable and unreadable. Keep.
- e003: traits need two-sided trade-offs; pleiotropy is real; snapshots plus a replay viewer are enough to watch.
- e004: the e002 network grows bodies once position enters as morphogens (6 gradients in [-1, 1], binding on 2 of 4). Keep that rule as part of the laws. Bodies are dense by default and mutations move regions; let e005's upkeep act on both before changing the read-out.
- e005: attack = min(front hard, muscle) is the rule that made a food web; with hard alone one immune body won in 10,000 steps. Two body types recur (armored grazer, omnivore with teeth) and the world keeps moving. Costs scale the population; trade-offs decide what evolves. Open: no pure carnivores (prey is worth little), sensors unused.
- e005, after the run: development is batched (all 65 network runs of one body settle together) and a child whose
  gene list equals its parent's reuses the parent's body (60% of births). Results bit-identical, 8,000-40,000 steps/s
  instead of 1,000-6,000. A cheaper sigmoid was tried and rejected: 11% faster, results diverge.
- e006: lineages are groups linked by gene-list distance (at most 6 genes apart, single linkage, at least 5 agents, kept
  once they last 5,000 steps). This gives an event log a person can read (birth, split, merge, extinct; about one
  event per 5,000 steps) and lineages of 60-100 generations with different bodies. Keep the detector, the log, and
  the lineage-colored viewer. Sex under the compatibility limit changed nothing: a mate is in reach at 16-23% of
  births and is a near-clone when found. Species boundaries here come from mutation, drift, and clonal sweeps; the
  limit only names them. Mating stays in the code but is not a mechanism until it has a reason to exist.
