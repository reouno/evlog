# Vision

Where we are heading right now. Unlike `principles.md`, this changes as experiments teach us things.
Last updated: 2026-08-30 (e011).

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
#9 (viewer: a white dot on agents that can bite, block legend, teeth and armor per lineage label),
e007 (256x256 world with drifting food patches: islands, half the predation, three times the
lineages, and the first sensor lineage that lasted), e008 (prey worth eating: a prize for old bodies does not make meat pay; hunter lineages exist anyway, as
booms; the lineage log now records diet), e009 (perception: inputs that say who can eat whom are non-zero once in a
hundred decisions; eyes do not pay because there is nothing to see; the knockout shows e007's eyes were a passenger
with a slight tailwind), e010 (contact physics: every trait rule removed; the world stands, shape goes to the
smallest corner of gut, teeth are profitable and were found once in twelve million births), e011 (rich cells: the same
regrowth on fewer cells gives size a reason and starts the arms race; tortoises, hunters and corner bodies coexist; the 8x8
grid is the wall now).

Next, in this order (GitHub issue numbers):
1. A world with both kinds of place in one run: wide patches (e010's grass, where the smallest grazer wins) and narrow
   ones (e011's trees, where the crowd makes tortoises and hunters), so that both kinds of body exist in one world and
   lineages can move between places. One law, no compute added. (#13)
2. #5 3D bodies (same development, 8x8x8), or a larger grid: the 90th percentile of mass is 64 at width 1; the
   population is pressed against a limit we drew.
3. #4 Learning, growth, aging, health as a layer on top of birth traits.

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
- e007: patchy food (one Gaussian patch of width 8 per 64x64 cells, drifting one cell every 50 steps, same total
  regrowth as uniform) is a law of the world from here on. A bigger world with uniform food is the same world
  sixteen times over (food per cell sets the density). Patches make islands: 12-21 lineages alive instead of 4-6,
  three times the splits, predation deaths per birth halved. Sensor blocks stayed for the first time (one seed:
  a grazer lineage with 2-3 sensor cells for 880,000 steps, its sensor changing one move in five), but the eye
  is not shown to pay: intake per digestive block is the same with and without, and two sensor blocks cost 2%
  of a grazer's intake. Cost is linear in agents (400-700 steps/s at 256).
- e008: what a kill is worth is not the lever. A prize of up to 30x for an old body (keep x the upkeep it paid)
  doubles the energy per kill and leaves meat at 3-5% of intake: kills get fewer and stay on newborns (nine in ten),
  because a catchable body next to a predator is eaten within a few dozen steps of appearing, so only the
  uncatchable grow old. The population answers with armor (hard 32-38 to 41-48; attack is capped at 24 by the
  body plan, defense goes to 32). Carnivore lineages (mean meat > plant) exist even in the control, and ten
  appear at keep 1: hunters with 24 front hard and 20-25 muscle, 52-89% meat, up to 430,000 steps, as booms of
  100-1,200 agents that armor ends. Every hunter also grazes (the gut for prey mass is the same organ). keep
  stays 0. Keep the diet columns in the lineage log. Access (a bite that beats armor, seeing who is next to
  you) is what limits carnivory, not the prize.
- e009: perception is not the lever. Given inputs that say, per direction, how many neighbors can eat me and
  how many I can eat (the predation rule itself, times sense), those inputs are non-zero in 1% of the decisions
  of agents with sensors: an armored grazer among armored kin is immune and bites nobody. Sensor blocks are
  selected less with the inputs than without (16 sensor lineages vs 43 in four seeds), escapes and predation
  are unchanged, grazers with eyes take in no more food. The knockout (sense forced to 0): the population mean
  is the same, but sensor lineages drop to 6 and never reach a mean of 1, fewer in every seed; e007's eyes were
  a passenger with a slight tailwind. Predation is decided by the body plan and by move order (the eater moves
  first in 75% of kills; 15% of prey die before their first move). The who inputs stay in the code at zero
  cost; the world stays e007's (counts). The knockout is how an eye is tested from now on.
- e010: the laws are now about materials and the world only. A cell costs what it holds (0.02 to build, 0.02
  when eaten plus its share of the body's energy); a body pays 0.032 per step besides its cells (a world law, for
  the population bound: regrowth / 0.032); force acts the way a body moves: a body moving into an occupied cell
  pushes into the bodies there line by line, and the softer tip breaks if the pusher's muscle in that line exceeds
  the tip's hardness (3 per contiguous hard cell, else 1). No attack, defense, gut, escape roll, kin exclusion,
  or kill rule. Keep these laws and the measures (bite, shell, open lines). What they showed: bodies were full
  squares only because defense counted hard blocks; without that, every seed goes to 3-4 digestive cells in a
  corner (intake is capped by the food in one cell, cost is per cell). Teeth pay ten to one and appeared once in
  twelve million births (seed 1, step 985,000; gone in 12,000 steps: a body that pushes with a tooth also breaks
  its own children). Emergence here is a reachability problem: a hunter needs a tooth, a policy that moves into
  occupied cells, and a way not to hurt kin, all at once.
- e011: the width of a food patch is a law of the world from here on (the total regrowth is fixed, so a narrower patch
  puts the same food on fewer cells). Width 8 (e010) makes five-cell grazers; width 4 seven-cell ones; width 2 is the
  edge (two seeds of four go to the arms race); width 1 (6.5 regrowth per cell per step, 45-77 bodies to a cell) goes
  there in every seed: hard 6-26 per body, 12-24% of bodies with a bite, meat 9-19% of intake, 26-50 hunter lineages
  per seed lasting up to 483,000 steps, shell 2.3-8. Three body kinds coexist: the tortoise (a full square, a two-cell
  wall of hard around a 4x4 gut, no muscle), the hunter (hard tip, muscle behind it, 26-85% meat), and the corner body (2-12
  digestive cells in the corners of the grid only, where the middle-row muscle of a hunter has no force: hiding as a
  shape). The gut is not the reason for size (it stays at 10-16 cells: bodies crowd and share the cell, 0.005-0.009
  per digestive cell per step in every world); armor is. What a cell can hold (the cap) does nothing: a crowded cell
  never fills. Lineages are fewer (1-13 alive) with one holder per island at a time. Fewer, larger bodies run faster
  (585-846 steps/s at width 1).
- e007 calibration: 128x128 (4 islands) matches 256x256 per island for what happens on an island (population,
  food, predation, body composition, rate of sensor lineages) but not between islands (lineages per island and
  lifetime move with the number of islands). Use 128 with more seeds for questions about bodies and behavior;
  use 256 for lineages across islands and for the world people watch. 1,000,000 steps: the uniform world's
  statistics are stationary after 100,000 steps; the patchy world's are not (late sweeps and sensor lineages
  after 500,000), so do not shorten runs on the patchy world without checking the conclusion at the cutoff.
