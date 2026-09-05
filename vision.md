# Vision

Where we are heading right now. Unlike `principles.md`, this changes as experiments teach us things.
Last updated: 2026-09-05 (e032).

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
patches drift off the lake: a rich place in a closed world is where the sun and the soil meet), e020 (the breath rises and the rain falls on
the mountains: what a body burns goes to the air, one pool for the world, and the air rains on every cell at most
the sun's rate times height over relief; the high ground lives, 658-670 bodies on ridges that held 0-14, the world
eats 73-94 per step, steady, with its store in the air and rivers of soil running from under the crowds to the
valley floor; the bodies sort by height, mass at birth rising valley to ridge in all four seeds, the small variants
and twice a second lineage holding the thin valleys: the first place effect on bodies under a uniform sun, a
grading, not a split; half the breath to the air is the richest world of the series, both stores, 103-109 eaten,
nothing wasted but shading, and no place differs from another: a closed world trades productivity against
difference; rain everywhere alike rebuilds the flat lawn, because the store sits wherever the draw is capped and
the population's own shading is cap enough), e021 (the tall plant takes the light: the matter standing on a cell is
a column, and a taller column takes, from every cell within its height in cells, a share of that cell's sun equal
to the height difference less the distance, times its own room over the cap - a full crown intercepts nothing, and
a column under a body neither grows nor claims; the world grows standing trees of 50-400 bites where no cell could
hold half of one, and has two states, an orchard of 6-24 trees in nine runs of twelve and a forest of 165-1,405 in
three, entered and left as booms; the forest doubles contact (0.093 per body per step) and harvests 6.5% of the
intake from the trees; the canopy raises the closed world's income to its record (112.9 eaten on the flat lawn,
e020: 100-103) by taking the light the bodies' own shadow was wasting; lineages alive reach 3-5 in four runs and
two lineages coexist 921,000 steps, the deepest coexistence since e012, with the heaviest winner of the series
(mass 10.3) standing in the thickest forest - but no tooth: a tree is silenced by the body that eats it, feeding
one gut at a time), e022 (the spill: a full crown keeps taking the light it stands in, a column under a body keeps
taking it, and what a column cannot hold - growth past the cap, or under a body - falls as fruit on the ring of
eight cells around it; the crowd comes back for the first time since e012, contacts 0.2-0.8 per body per step in
ten runs of eleven, fruit 44-77% of the intake, the dead 10-26% of it, and the crowd state eats 115-134 per step,
the record; the crowd picks a new winner, a hollow frame of 19-24 cells around the rim of the grid, seven world cells wide,
that stands around a tree without holding it and eats the ring, with armor at its corners, three times e021's bar - and it is one winner still, lineages 1-3, the tooth found and lost
(biters up to 0.026); the price is the start: with every neighbor's light taken the lawn under the trees is dark,
every world crashes to a few hundred bodies by step 1,000 and one in five dies there, bodies that see two cells
starving beside piles they cannot see; mutation as a chance per base rides along and changes nothing else),
e023 (eyes that see far: a sensor block sees one more cell, seen at 1/distance, range paid for with the cell; the
eye pays where the crowd is and nowhere else - in two seeds of four the winner carries a sensor per body for
261,000 and 695,000 steps (e022's longest: 23,000), and it is the crowd state's frame with no armor, four muscle
and three to seven eyes where e022's frame had armor at its corners, walking from ring to ring; in the other two
seeds, the mixed state and a lawn, the blind bar wins and the eye is dropped; the start's deaths fall from 5 to 2
in 24 and its bottlenecks do not move; no tooth),
e024 (what flesh is worth: a share `flesh` of the upkeep a body pays is fixed in its flesh instead of breathed, and
goes to whoever breaks a cell of it or to the ground when it dies, matter conserved; a cell is worth 1-2.5 against
0.15, and the world answers by eating its dead: at every share up to 0.7 and in three seeds of four at 1 nothing
bites, the winner is the net - four pads of three gut cells at the corners of the box, eating corpses from four
places at once - and the fat hoards 25-70% of the world's matter, the rain stopping at 1; the tooth comes in one
seed of four at 1 and in every pilot at 0.85 and above: a state entered at the start and kept, 4,500 bodies of nine
cells, half with a bite, four kills a step, a hunter lineage of 488,000 steps beside a gut of 286,000 - two
winners; a cell is worth less in the hunter's world (0.64) than in the net's (2.4), so the worth does not decide
the state, the start does; matter drifts 0.2-1.8% on the f32 ground under fat corpses, #31).

Next, in this order (GitHub issue numbers). The plan was reset on 2026-09-01 after e021 with the user's reading of
the series: one body wins because the environment is still uniform in time and the body has too few axes; the fixes
are fluctuation, the crowd, and materials with more properties - as laws about the world and materials, as ever.
The order was reset again on 2026-09-02 after e022: the crowd is here, and what it exposed comes first - the
bodies' sight (the start's deaths are bodies that cannot see a pile two cells away) and the worth of a body (the
crowd touches, and a tooth still loses to a gut that eats what falls).
Done 2026-09-02: #26 eyes (e023) - kept; the eye pays in the crowd state only, and the crowd's body sees now.
Done 2026-09-03: #27 flesh (e024) - kept at `flesh` 1; a body is worth eating, the world eats its dead, and the
tooth pays in a state the start decides (one seed of four), where it gives two winners and four kills a step.
Done 2026-09-03: #31 (e025) - the drift was not the f32 ground but two leaks of the ledger (a body's deficit filled
by a kill in the same step; f32 rounding of the fat's fixed increment); the ground and the bodies' ledger are f64
now and the matter holds to 1e-6. #25 what a block weighs (e025) - kept, both halves: a block weighs by its kind
(hard 2, sensor 1/2) times a density the genome expresses (1/2 to 2), and hardness is the material's times the
density. It ended the start's lottery: the hunter state in four seeds of four (the control at the same code: the net
state in four of four), hunters denser than their prey, a second winner half a density apart in three seeds, nobody
light (a light body's face breaks under one muscle). Two routes to resistance: density (seeds 1, 2, 4) or hard
blocks on a big body (seed 3).
Done 2026-09-04: #24 weather (e026) - kept, both forms, as laws of the world: the cloud (the air rains where a
field with a memory of 3,000 steps says, drifting east; the ridge's soil follows it, the bodies hardly do: the
winners are e025's) and the season (the sun a sine of 20,000 steps at amplitude 0.5; the bodies halve each winter,
the top place changes hands 6 and 14 times in two seeds of four, and the eye pays for the first time: lineages with
a sensor per body for 72,000-125,000 steps in four runs of eight, 10,000 at most without weather). The season's
ceiling is a fact about the bodies: a body has no store of its own (its fat is its eater's), so amplitude 1 kills
the world in its first winter and 0.75 makes a lottery every winter.
Done 2026-09-04: #33 room (e027, two pilots) - not a lever. Four times the space at the same matter is four times
the sun, so the matter turns over four times faster and the bodies fill the room (1.4x as many, twice as big);
a quarter of the matter halves the bodies and they crowd the valley (21% of its cells under a body, e026's
whole-world figure). Contacts per body are 0.3-0.6 in every world: the bodies make their own crowd where the
food is. Room, if it is to be given, is a matter of spreading the food (terrain, rain), not of the grid; the eye's
test stays the season world. The 256 grid costs 2-3x per step and is kept as an argument only.
Done 2026-09-04: #32 what a gut digests (e028) - not kept. A heritable digestion axis on the gut material (plant
yield 1 - d/2, flesh 1/2 + d/2; the dung to the soil) is neutral as the issue's line: the world's flesh is its own
dead, lying where the bodies are, so every gut eats a mix (the control digests 70% flesh) and the world settles at
the mix where the line has no slope. As a sharp curve (the middle worse than the mean of the ends) it is selected,
one way: four seeds of four go to the plant gut (d 0.15-0.32), no flesh gut, kills stop, the winners drop their
muscle and sit (speed 0.001-0.005). Either form costs the world two thirds of its bodies: a gut that leaves a
quarter of every pass in the soil breaks the cycle of the dead that fed e026 (an intake of 1.5-2.5 times the sun).
A flesh gut needs flesh that lies apart from the plants (a place, #14, or a hunter that carries its prey); the
split between grazers and hunters stays with the tooth and the state of the world.
Done 2026-09-05: #28 small and large bodies (e029) - not kept as the default (`side` stays 8; the argument stays: a
number up to 16, or `grow`, the side the genome expresses from 4 to 16). The grid is not the size: on a 16x16 grid
the bodies are 12.5-14.2 cells (control 8-21), and under `grow` four seeds settle on sides 4.4, 5.2, 8.1 and 14.3
with bodies of 11-16 cells in all four; the side sorts a seed's two kinds (a dense mover, a sitting gut) onto grids
by chance, the giants (up to 240 cells) are newborns that starve, and the 16 grid costs 2x per step and the tooth
(gone in three seeds of four). Size is the sun's: a body of 16 cells costs the sun of six cells, and a cell of
ground holds what the sun gives it whatever stands on it. Size will pay when a body can do with size what a small
body cannot: carry a store through the winter, or reach food a small body cannot.
Done 2026-09-05: a store a body can spend (e030) - kept, at `store` 5. The fat a body fixes from its upkeep is its
own: the flesh holds at most `store` per unit of mass, the fat pays the upkeep when the energy cannot and what it pays
is breathed, the rest is e024's (the eater's share, the ground at death). Half the bodies live on their fat at every
season (the crowded world's bodies wait instead of dying: starvation deaths 17-21 a step to 2-6), and the winter at
0.75 is no longer a lottery: the floors are 327-1,186 bodies with 2-22 lineages over 45 winters of three seeds, where
the control falls to 18-45 with one or two. Size does not pay: the side falls (4.0-5.6 against 4.8-7.2) and the mass
rises by density (32 against 15 in two seeds), because the store is per unit of mass and mass is free of upkeep - a
full 4x4 block at density 2 is the store's body, and the light sitting gut (with an eye in two seeds) holds the other
place, 151,000-300,000 steps in one seed. The cycle moves from the ground to the air: the winners eat 13-49% flesh
against 70-84%, the air rains three times as much. The tooth stays gone under `grow` (the side-8 pilot had it, 1-21%). At amplitude 1 the world lives now (e026's died in
its first winter) but as a lottery of 7-25 bodies each winter (a pilot on seed 9): a store of 1,300 steps of upkeep does
not span a winter of 6,700 steps under a quarter of the sun.
Done 2026-09-05: the child of the flesh, and breeding as a decision (e031) - not kept, both stay as arguments. A child
made of half its parent's fat (`yolk`) shares the store among the same crowd: the fat per body falls and the floors at
amplitude 1 are the control's (8-26 bodies). Breeding as the policy's fifth output (`breed`) is never selected toward a
time: 98-99% of the decisions to breed are below the threshold from the first log step to the last in six runs of
300,000 steps at 0.75, because a denied decision costs nothing and a body at the threshold breeds within a few steps
either way; at amplitude 1 the world dies in its second winter, alone or with the yolk. At 0.75 the floors (498-728 in
lineages of 5 or more) and the lineages (4-16) are the control's. The dark winter is the world's arithmetic: 131,000 of
matter cannot carry 3,000 bodies of 0.056 upkeep through 3,000 dark steps however the fat is divided. (The lineage
count of the floors is 17-35% under the bodies alive; e030's floors are that much undercounted too.)
Done 2026-09-05: a winter that differs by place (e032) - kept: the season world is `winter high` at amplitude 2
from here (the cell's amplitude is a times its height over the relief, at most 1; the argument's default stays
`flat`, e031 byte for byte). The dark winter is a place now and the world stands: floors of 673-1,230 bodies with
2-10 lineages at amplitude 2 (44% of the cells dark at midwinter) and 364-476 at 3 (72% dark), where the flat season
at 1 is a lottery of 8-22; the floor is the valley's capacity and returns within 5% every winter. The valley holds
68-90% of the bodies at every floor, the ridge's winter bodies are 58-100% born below, and the ridge is refilled to
16-24% of the peak every summer: migration as an outcome, as a wave of the whole world (no lineage is a place's).
The crowd the winter makes in the valley brought the tooth back in one seed of three (24-37% of the bodies for
150,000 steps: a flesh column at density 2 beside a light gut, two kinds 260,000 steps together). Not reached: no
body holds the ridge through the winter, because the valley is the best place at every season but the summer.
1. The ridge worth something: e020's rain on the mountains (`rain high`, an argument already) under the winter by
   height, so that the soil is where the sun goes out and the two places are a trade-off; a body that carries its
   store uphill in spring is an outcome to watch for. The other world law for the dark: a store in the ground that
   stands through it (seeds, roots, a wood nobody eats down).
   Also: whether size can pay at all under a per-cell upkeep (a store per cell instead of per mass would make the
   4x4 block and the 16x16 net equal; a cost that falls with size is the real-world premise still missing).
2. #5 3D bodies (the vertical axis for legs and wings), after size pays: 12-16 cells in 3D is a blob. An arm is an
   outcome to watch for there, not a rule.
3. Later: #34 kinds of matter (several conserved substances - water, plant stuff, animal stuff of different
   hardness - and blocks as mixtures, so that organs are outcomes of the mix; starts with #29 water that flows:
   rivers, lakes, deserts as outcomes, a rewrite of the closed cycle's carrier, when a question needs wet and dry
   as places), #4 learning, growth, aging, health as a layer on top of birth traits.
Also open on the weight: whether the net state can be entered at all under the law (e025's pilot on seed 9 came
close: no tooth, but kills), and why a seed takes density or hard blocks as its route to resistance. On the flesh:
which side of the switch (between 0.7 and 0.85) a run takes was a lottery of the start without the weight law.
Also open on the spill: a start with soil in the ground (the lottery may be the all-plants start meeting the dark
lawn), and whether the crowd state is entered by chance or by history (half seed 2 flipped at 400,000, half seed 1
at 900,000, half seed 4 fell back; e023 flat seed 2 entered it at 750,000 with its eyes, flat seed 3 left it at
500,000 and lost them: the eye and the crowd select each other, and which comes first is open).
Other laws still open on the height axis under #14: cold by height (huddling as an outcome), slope grip.

How we judge whether a law worked (#19): count the winners. e013-e021 end with one body winning every run and 1-5
lineages alive (e018's closed cycle: 1-3, fewer than the open world's 4, so a law can also lose by this rule; e019's
terrain: 1-2; e020's rain: 1-2, but graded by height for the first time, with second lineages holding the low ground
for 300,000-520,000 steps; e021's canopy: 1-5, with two lineages coexisting 921,000 steps and the winners sorted by
state as well as height - kin of one winner still, not other kinds; e022's spill: 1-3, with a new winner, the frame,
where the crowd is, the middle body where it is half there, and the bar where it never came - a different winner,
not a second one; e023's eye: 1-2, the frame that sees where the crowd is, the blind bar elsewhere - the first
block whose worth depends on the state of the world; e024's flesh: 1-3, the net everywhere but in the hunter
state, where the tooth and a gut hold together 286,000 steps - the first second winner that is another kind of
body, not kin on other ground); a world with one optimum is
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
- e020: the breath to the air with the rain by height is a law of the world from here on: what a body burns rises
  to one pool of air, and the air rains on every cell at most the sun's worth per step times height over relief.
  It is the high ground's income (soil runs off it), the closed world's second store, and the first place effect
  on bodies under a uniform sun. Half the breath is the richest world and has no places: productivity trades
  against difference.
- e021: the canopy is a law of the world from here on, at rate 2: a taller column takes a shorter one's light, as
  far as it is tall (the height difference less the distance, over the cap), times its own room over the cap
  (saturation - a full crown intercepts nothing; without it the hoarded light of full columns starves the world
  dead, and without the reach a tree gathers less than one body's upkeep and nothing changes). A column under a
  body neither grows nor claims. It gives standing stores of 50-400 bites, a second state (orchard and forest,
  entered and left as booms), the closed world's record income (the canopy takes back light the bodies' shadow
  wasted), and the deepest coexistence since e012 - at half the speed (178-212 steps/s against 429-492). The
  terrain's mean height is normalized to half the relief from here on (geography, not a law): every seed's rain
  then adds up to the same income, and e020's 73-94 spread collapses to 83.2-83.8.
- e007 calibration: 128x128 (4 islands) matches 256x256 per island for what happens on an island (population,
  food, predation, body composition, rate of sensor lineages) but not between islands (lineages per island and
  lifetime move with the number of islands). Use 128 with more seeds for questions about bodies and behavior;
  use 256 for lineages across islands and for the world people watch. 1,000,000 steps: the uniform world's
  statistics are stationary after 100,000 steps; the patchy world's are not (late sweeps and sensor lineages
  after 500,000), so do not shorten runs on the patchy world without checking the conclusion at the cutoff.
