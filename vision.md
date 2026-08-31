# Vision

Where we are heading right now. Unlike `principles.md`, this changes as experiments teach us things.
Last updated: 2026-08-31 (e019).

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
grid is the wall now), e012 (two kinds of place: patches of two widths in one world; each place keeps its regime in every
seed, grazers on the grass and the arms race on the trees; bodies cross and lineages straddle, hunters stay; one lineage
with a different body on each place), e013 (facing and space at the cell level: bodies are readable and reach pays, but
one body to a cell ends the crowd, and with it contact, teeth and the arms race, at every width; the world is a jam of
small grazers), e014 (space at the resolution of the body: bodies hold their own cells, births and the narrow places
fill up again, and still nobody touches anybody; contact is a failed move now, selection keeps reach alone, and the
winning body is four cells at the four corners of its grid), e015 (work is force times distance: a move costs by the mass
moved times the distance and a push that moves nothing costs nothing; pushing is free and nobody pushes, forward 9-27% of
decisions, contacts 0.10-0.37 per body per step, no tooth; the winning body is the same constellation; the world is a lawn
because food regrows under the body that eats it, so the best body stands still and reaches), e016 (a plant under a
body does not grow: a cell held by a body does not regrow, and the lawn is a pasture; moves that happen 11-20% of
decisions against 1-3%, 74-88% of forward actions find room, the winner is a block of 7-9 gut cells over 1.6-2.7 world
cells in place of the constellation over 4.5; the world lives on a third of its regrowth and holds half the bodies;
contact falls to 0.02-0.05 per body per step because a body moving through an empty world meets nobody; the milder
reading, regrowth by the free sub-cells, is a tax that reach pays for and keeps the lawn), e017 (a dead body is food
where it lies: every cell of a dead body lays its matter and its share of the body's energy on the world cell under it,
a child never placed lies under its parent, a broken cell nobody eats lies where it was; the world eats its dead and a
body is worth what it cost, 2.5-3.2% of the food at a cell of 0.02 and 7-11% at 0.1; neighbors and contacts stay e016's
in every run, the same wedge wins, 2-4 lineages; on the trees dead matter is 7-12% of the intake and one small tree
lineage lived 50,000 steps on it at 0.1: the dead matter is where the crowd is, and the ground forgets it in a few
dozen steps), e018 (a closed cycle through the soil: a plant grows out of its own cell's soil at most the sun's rate, what
a body spends falls to the soil under it, the dead rot into it; matter is conserved and the map remembers, the richest
tenth of the cells holding 43-87% of the soil, the trails of the patches and of the bodies visible in the maps; but the
world eats what its bodies spend, 23-26 per step of 164 of sun, a third of the sun falls on empty cells, the trees lose
their bodies, the population swings 2-5x, lineages fall to 1-3 against e017's 4, three scarce worlds of four die, and
under a uniform sun the soil weaves into the walks and the food supply falls through the run; 70% of the matter lies
beyond the patches where no sun is), e019 (matter that flows: a height per cell and soil that runs to lower neighbors,
its own height counting, so that it pools level; the closed world stands for the first time, food eaten steady to 1%
and the population to 1-3% in all twelve uniform-sun runs; the soil pools into a level lake over the low ground that
holds 100% of the soil and 99-100% of the bodies, bare ridges above it, the soil map the terrain upside down; but a
lake is one place, the same bar of 6-10 gut cells wins it as wins the flat lawn, lineages stay at 1-2, and the terrain
costs the world the ridges' share of the sun; over the drawn sun the terrain is fatal, two worlds of four die as the
patches drift off the lake: a rich place in a closed world is where the sun and the soil meet).

Next, in this order (GitHub issue numbers):
1. Environments that differ by place (#14). e019 leaves every cell with a coordinate the real world's places vary
   along: height. The lake is one place and the ridges are a desert nobody enters, because nothing is there for a body;
   the next law says what the high ground has that the lake does not (warm and cold, wet and dry, the plants that grow
   there), as a law about the world, not a stronger sun up there (that is a patch again). The sun is uniform from here
   and the shape of the world comes from the ground.
   Seasons (by time) belong here too. This is the answer to #19's "many pressures": a place selects among the verbs
   the physics has; add verbs first. e012 is the first place law and shows the pattern works: two places, two regimes,
   in one run, at no compute cost. New materials (a cell that stores, for a world where food comes and goes) are added
   when a premise calls for one.
2. A full cell that spills food to its neighbors (fruit falls), so that a tree is not one cell feeding sixteen gut
   cells. Small now: with bodies moving, 0-4 of 164 regrowth per step is lost to the cap (e015: 67-68 with trees).
3. #5 3D bodies (same development, 8x8x8), with the ground half of #16 (friction by the cells that touch the ground, an
   overhang has to be held up): legs and wings need a vertical axis, and the top-view grid has none. The 90th percentile
   of mass is 64 at width 1.
4. #4 Learning, growth, aging, health as a layer on top of birth traits.

How we judge whether a law worked (#19): count the winners. e013-e019 end with one body winning every run and 1-5
lineages alive (e018's closed cycle: 1-3, fewer than the open world's 4, so a law can also lose by this rule; e019's
terrain: 1-2, level with e018, while being the first closed world to pass principle 4); a world with one optimum is
reached fast and is dull to watch. A wider genome or more parts would only
make the one optimum slower to reach; what makes several winners is more pressures (places, seasons, matter that
cycles), so every law is judged by how many different bodies prosper at once, not by how many are possible.

What we want the viewer to be able to do: look at a body and guess what it does, the way a fang, four legs, or a wing
is read at a glance. That needs the physics the reader already knows (a front, ground, air), written as laws of
materials and the world.

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
- e012: the patches of one world can have different widths (patch k has the k-th width of a list, cycling), a law of the
  world from here on; the cap on what a cell holds is a constant 8. Grass (width 8) and trees (width 1) in one world
  keep their regimes in every seed: 6-cell grazers with no armor on the grass, bodies of 16-32 cells with 4-15 hard
  cells, 12-34% with a bite and meat 14-18% of the intake on the trees, each place at the population its single-kind
  world had per patch. Bodies cross (0.1-0.7% stand in the other kind of place, up to 6%): small grazers walk into the
  trees, tortoises walk out onto the grass, hunters never leave; 2-4 lineages per seed straddle both places for 20,000+
  steps, and one lived 978,000 steps with half its members on each place and a different body on each (4 cells on the
  grass, 8-12 on the trees). Lineages alive 9-13, e010's number, not the sum. The edge width (2) next to grass does not
  flip more often than alone, but once the edge's hunters held the grass for 400,000 steps and lost it. Use 128 with
  two patches of each kind for questions about places; 256 (eight and eight) is the world people watch.
- e013: a body faces a direction (one number per body; the grid turns with it, only the front pushes, the policy sees
  the world from the body: keep, it costs nothing and the viewer reads a front) and takes up space at the cell level
  (one world cell per 4x4 quarter of the grid that holds a cell, no two bodies in one cell, a push into a taken cell
  that succeeds only if the way clears, a child that needs room). The world stands and runs at 700-1,500 steps/s, and
  reach pays: the winning grass body is 3-4 digestive cells at the center of the grid, one per quarter, eating from
  four cells at once. But the arms race is gone at every patch width (1, 2, 4) in every seed: no bite, hard under
  0.1, meat under 0.001%, no hunter lineage. The crowd was the premise of e011's arms race: with one body to a cell,
  contact fell from 2-4 to 0.1-0.3 touches per body per step, a tooth breaks even at best, births fell 8-fold (a
  child needs room), the trees feed one body per rich cell and half the regrowth is wasted, and 80-94% of moves are
  blocked: each patch is a jammed disc of two or three lineages. Cell-level space is too coarse (a 3-cell body blocks a whole
  cell, three in four blocked moves press on nothing); the next step is space at the resolution of the body.
- e014: space at the resolution of the body (occupancy per sub-cell, 4x4 per world cell; a body holds exactly the
  sub-cells its grid fills; a move is one sub-cell; a push meets face to face with e010's rule; a child needs room for its
  cells). Keep it: it costs 16 times the cells and about twice the time per body, a small body is small, bodies pass and
  nest, births are four times e013's and the narrow places hold three to four times e013's bodies. What it showed:
  contact does not come back with room (0.06-0.22 touches per body per step at every width in every seed, no tooth, no
  armor, 1-3 lineages). Contact is a failed move now, and a body without a tooth has no reason to fail one: forward is
  7-15% of decisions, turning (free, mostly blocked) takes the rest, and a push costs the mover as if it had moved.
  Selection keeps reach alone, and reach alone makes plants: the winning body everywhere is four to eight digestive
  cells at the four corners of its grid, a constellation lying over four world cells that hardly moves; other bodies
  stand between its cells. Space and the arms race are in tension until pushing into a body is free to try.
- e016: a cell held by a body does not regrow (the strict reading: no regrowth while any of its 16 sub-cells is held), a
  law of the world from here on. It makes bodies move (moves that happen 11-20% of decisions, 74-88% of forward actions
  find room) and brings the mouths together (a block or wedge of 7-9 gut cells over 1.6-2.7 world cells wins every
  run); the price is two thirds of the regrowth and half the bodies. The free reading (regrowth by the free sub-cells)
  is a tax that reach pays for and keeps e015's lawn. Contact does not return: 0.02-0.05 per body per step.
- e017: what a body is made of does not vanish when it dies (every cell lays CELL_ENERGY plus its share of the body's
  energy on the world cell under it; a child never placed lies under its parent; a broken cell nobody eats lies where it
  was; added in full, the cap bounds only what a plant grows to), a law of the world from here on, at a cell of 0.02.
  The dead matter of a cell is kept next to its food as a measure (`carrion`), so what a body ate of the dead is known
  (`meat`). It is free and honest, and it changes nothing by itself: a body is worth what it cost (2.5-3.2% of the food
  at 0.02, 7-11% at 0.1, where the winning body is a cell smaller because a cell is dearer to build), it is eaten within
  a few dozen steps where it fell, neighbors per body (from the snapshots, a measure to keep) and contacts are e016's
  in all sixteen runs, and the same wedge wins. The dead are where the crowd is: 7-12% of the intake on the trees, one
  small tree lineage living on the dead for 50,000 steps at 0.1. A crowd will not form around 2% of the food; a place
  that keeps what falls on it (the closed cycle, #20) is the version of the premise with a memory.
- e018: the soil (one f32 per cell: what was spent and died on the cell, drawn out by the sun into the plant) is kept as
  the world's memory and as a layer in the viewer; the maps of it are the history of a run. The closed cycle as e018 ran
  it (a plant grows only out of its own cell's soil, nothing moves matter but a body) is not kept as it stands: the world
  eats what its bodies spend (regrowth = spent, 23-26 per step of 164 of sun), the trees lose their bodies (a tree cell's
  6.5 of sun empties its soil in a step), the population swings 2-5x, lineages fall to 1-3, three scarce worlds of four
  die, and under a uniform sun the soil weaves into the bodies' trails (one cell wide) and the food supply falls through
  the run. Two lessons: a cell in a closed world can be rich only if matter flows into it from elsewhere, so rich places
  need a flow law (water, #22), not a sun law; and a closed loop with a delay (rot at 1% per step, the sun's rate) and no
  reserve swings, so principle 4 has to be checked by the population's swing, not only by extinction. Matter is
  conserved to 0.01% (f32 rounding at 0.8% with 2,000 bodies); the leak (a parent paying for a child's cells with energy
  it does not have) is under 0.02%.
- e019: the flow (the surface of a cell is its height plus its soil; each step a cell gives a tenth of its soil to the
  neighbors whose surface is lower, split by the drop, never more than an eighth of a drop) is a law of the world from
  here on, with or without a terrain: it is what makes the closed cycle stand (every cell with soil grows, a trail
  spreads as fast as it is laid; food eaten steady to 1%, population to 1-3%, over a million steps in twelve runs of
  twelve). The rate hardly matters (0.01, 0.1 and 1 give the same world; the volume of soil and the shape of the ground
  set the lake). The terrain (smooth noise from the seed, a relief in soil units) is kept as the source of the world's
  shape: a level lake in the low ground, a shore, a desert above; the viewer gets it as a layer. The sun is uniform from
  here: drawn patches over a terrain put the sun where the soil is not, and the world dies of it. The soil is an f64 (an
  f32 soil drifted up to 1.8% of the matter over a million steps; f64 holds 0.0003%). Places under the uniform sun are
  read by height band (thirds of the cells): keep that in the per-place log.
- e007 calibration: 128x128 (4 islands) matches 256x256 per island for what happens on an island (population,
  food, predation, body composition, rate of sensor lineages) but not between islands (lineages per island and
  lifetime move with the number of islands). Use 128 with more seeds for questions about bodies and behavior;
  use 256 for lineages across islands and for the world people watch. 1,000,000 steps: the uniform world's
  statistics are stationary after 100,000 steps; the patchy world's are not (late sweeps and sensor lineages
  after 500,000), so do not shorten runs on the patchy world without checking the conclusion at the cutoff.
