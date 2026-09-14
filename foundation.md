# Foundation (draft)

Status: agreed 2026-09-13, with option (a) for every decision in section 7. It replaces the method
of testing one law at a time (#73, withdrawn) with a whole environment built first and searched in
stages: #74 (A), #75 (B), #76 (C). Stage A is done (e061, 2026-09-13): the world is 512x512.

## Why

- **e060**: sixty experiments added or removed one law at a time, and every world still holds one
  to three kinds of living. Counted per kind, none of the laws read as new axes (places, season,
  cloud, weight, winter by height) added a way of living.
- **A world with one or two limiting factors cannot show what a third one does.** A single new law
  is averaged away by the crowd or absorbed by the hunter/grazer lottery. The real world stands on
  many differences at once, and changing one of them alone mostly breaks the balance.
- **So**: build the environment whole, split into what is a law, what is generated, and what must
  emerge. Then search its parameters in stages, from the cheapest layer to the dearest, and judge by
  kinds of living (e060's census per kind).

What does not change (principles.md): laws are about materials and the world, never traits;
diversity comes out of an environment that differs; compute is bounded; the real world is a source
of premises, not a target.

## 1. Laws, generation, emergence

**Laws** are the same in every world:

| law | status |
|---|---|
| conservation of matter and energy: soil, air, water (e018-e035) | kept |
| contact and force, space at the body's resolution, work (e010, e014, e015) | kept |
| bodies: genome and development, weight and density, store, strict upkeep, wear, connection, motor, clock (e004-e055) | kept |
| the sun: a day (rotation) and a year (tilt), light by latitude | new; replaces season by height (e032) and patches of sun (e007, e011) |
| heat: a cell's temperature from light, height and nearby water, spreading to neighbours | new |
| water: evaporation by temperature, humidity carried by a prevailing wind, rain where air rises or cools, flow downhill (e035) | partly new; replaces rain by height (e020) and the cloud (e026) |
| producers as materials: grass, wood and algae, each with its own growth | new; wood keeps the canopy (e021-e043) |
| fire: dry standing plant matter burns when hot and spreads to dry neighbours; its matter goes to the air and the soil | new |
| the material trade-offs of section 2 | new |

**Generated** at random from the seed, with parameters:

- a height map and a sea level: land, sea, islands and lakes are results;
- the span of latitude the map covers;
- the initial soil and water.

**Emergent**, never written: rivers, lakes, deserts in rain shadows, forests, grassland, climate
zones, the fire regime, succession after fire, migration, and every way of living.

**Later, not in the first version**: terrain that erodes, plants as evolving organisms, 3D bodies
(#5), several kinds of matter (#34).

## 2. What makes each difference usable

e060's lesson: a difference the bodies can ride out is not an axis (season, cloud, two kinds of
place added no way of living). So every difference comes with a law about a material that makes one
body good there and bad elsewhere.

| difference | law about a material | gains | pays |
|---|---|---|---|
| water and land | a water cell has a surface layer and a bottom layer; a body lighter than water (density under 1, e025) lives in the surface layer, a denser one on the bottom, and touches and eats only its layer | light bodies reach the algae and the light; dense bodies reach what sinks | light armor is weak armor (hardness times density); dense bodies cannot reach the surface |
| dry air | a soft block (gut, muscle, sensor) facing dry air loses water each step, paid from the body's water (e040); a hard block does not; nothing is lost in water | armored bodies, and bodies near water | soft, spread bodies far from water |
| breath in water | a block over water uses breath, and each face of a soft block open to the water gives it back; a block over land breathes freely; a hard block breathes through nothing (e067) | open, small bodies in the water | solid or armored bodies in the water |
| cold | a block facing a colder cell loses energy by the difference; hard blocks and fat insulate | compact, armored or fat bodies in cold places and winters (a big body loses less per unit of mass by geometry) | spread, soft bodies |
| light: day, depth, shade | producers grow by light; a sensor sees as far as the light allows | eyes by day, producers near the surface | eyes at night and in deep water |
| wood | a wood cell has a hardness, and a bite breaks it only with more force behind a hard tip than that (e010's rule, applied to a plant) | bodies with a hard front and muscle | guts without a tooth, which eat grass and fallen fruit |
| fire | a burning cell breaks soft blocks facing it with a chance; hard blocks resist; water shelters | armor, speed, life in water | soft, slow bodies on dry grassland |
| height | moving onto a higher cell costs the mass lifted times the rise, on top of e015's work; going down pays nothing back | light bodies and strong muscle on hills | heavy bodies that must cross relief to reach food or water |

Every row reuses a law that exists (density, thirst, the contact rule, the canopy, the store, work). No
row names a trait. The height row was added after e061 (the user): the highest land is drawn about 18
cells tall, a hill 10-20 bodies high, and without it a body feels height only as cold and walks over a
ridge as if it were flat.

## 3. Stages, measures and pass lines

Each stage is run and judged before the next is built on it. A failure names its layer.

**Stage A: the environment alone** (terrain, sun, heat, water; no producers, no bodies).

- A cell's habitat is its medium (land, shallow water, deep water) x temperature band (3) x moisture
  band (3), read at each season.
- Pass: at least 5 habitats each holding 2% of the cells; at least 3 of them in patches wider than
  three lifetimes of travel (a body travels 3-14 cells in a life today, e058); 10-50% of the cells
  change habitat over a year; year 20's habitat map agrees with year 10's on 90% of the cells (it
  stands, it does not drift).
- Result (e061): 34 of 300 candidates pass all four lines, 30 of them at 512x512. Width is bought by
  the size and by the terrain's grain (continents of about 128 cells or more); the wide land habitats
  are dry, and wet land comes as coasts and belts. The tilt sets the change (10-30 degrees). Nothing
  drifts: a world fails to stand only while its sea and ground water settle (about 20,000 climate
  updates), so a world is spun up that long before it is judged or lived on. The lines accept hot,
  cold and desert worlds alike.

**Stage B: producers** (grass, wood, algae and fire on a stage-A world; no bodies).

- Pass: each producer holds 5% of the world's standing plant matter and is the larger part (50%) in
  at least one habitat; none dies out in 10 years; fire burns 1-20% of the land a year (not never,
  not all); matter is conserved.
- Result (e062): 9 of 96 candidates (16 draws of the growth rates and the strike chance on six of
  stage A's worlds) pass every line, on 4 of the 6 worlds, and no draw passes on more than 2. Grass,
  wood and algae share one growth law; wood needs forty times grass's stand to take half the light
  (most of a tree is trunk) and shades the grass under it. Algae always hold the water; grass and wood
  split the land only when wood needs about 3-12 times the ground grass needs. The hot dry world loses
  its wood and the cold world never burns 1% of its land. Fire burns too little, never too much (at
  most 11% a year), and its smoke drains the land to the sea (up to 1.2% a year) with nothing bringing
  it back. A candidate costs 8 minutes at 512 on one core. Stage C takes one draw and the worlds it
  passes: d11 on c1225 (warm, very wet) and c1236 (cool).

**Stage C: bodies** (kinds of living counted by birth form, e068: e060's census read over the bodies
a genome develops, with new columns: the tooth a body was born with, its kills apart from what it
scavenged, the length of its path, its layer, its temperature band).

- Pass: at least 4 kinds of living by birth form on at least 4 seeds of 6, each holding 5% of the
  grown bodies at every census for 5 years or more (reported beside the count by lineage and the count
  with what bodies do shuffled inside lineages); no season's floor reaches zero; two kinds taken from
  the run invade each other while rare (#72's injection, the check that the world holds them and not
  the seed's luck).
- First step (e063, 2026-09-14): e059's bodies with every kept law and no new one, on c1225 and c1236
  with d11; bodies live on land, eat grass and the dead, and spend into the soil under them. A step
  costs 1.34-1.35 ms at 512 on one core, three quarters of it the world's update and about 1 µs a
  body, so stage C needs neither threads nor a window. But the world feeds about 300 bodies (one per
  360-530 land cells), 30 times fewer than section 4 assumed, and they live one way: roaming grass
  eaters without a tooth, kills 2-5% of the intake. Against the same worlds without bodies they hold
  the grass at a fifth and halve the fire (0.5-0.6% of the land a year, under stage B's line, which was
  judged with nothing eating the fuel). The ratio of what a body draws to what the plants grow is the
  first number stage C has to set.
- Second step (e064, 2026-09-14): one scale s on every matter quantity of a body (a body keeps its
  own units; s converts where matter crosses to the world). On c1225, seed 9: s = 1/4 holds 770
  bodies, s = 1/16 holds 5,652, one per 20 land cells. At 1/16 contacts per body are 4.3 times
  e063's, kills 17% of the intake, and each lineage lives 2-4 ways (e063: one). The grass grows a
  fifth of what it grows alone, but the crowd wastes less of it (the land burns 0.14% a year) and
  eats its dead. The crowd jams (52% of moves blocked, 41% of children without room) and every body's
  density sits at the ceiling of 2: a denser soft face breaks a lighter one, so density is the crowd's
  weapon and armor, and the water's two layers (section 2) are a price on it.
- Third step (e065, 2026-09-14): the water's two layers, section 2's first row. Each layer has its own
  occupancy; a surface gut eats algae, a bottom gut eats the carrion and the algae's dead, which now
  lie on the bottom as litter; all water is open and pools stay land. On c1225, seed 9, s = 1/16:
  5,561 bodies (41% on land, 40% at the surface, 19% on the bottom), mean density 1.18 (e064 1.95),
  34% of moves blocked and 21% of children without room. The layers are kept. They make two groups
  by density, not kinds by medium: lineages at 1.00, the hardest a surface body can be, stand in
  all three media (8-23% of grown bodies are in lineages that keep 90% to one), and the dense ones
  keep to land and the bottom. Every producer is grazed to 1-4% of its stand without bodies and grows
  about a tenth as much, so stage B's lines, judged without grazers, say little about a world with them.
- Fourth step (e066, 2026-09-14): dry air, section 2's second row. A soft block over ground that is not
  water loses `dry` x the dryness there per face open to the air, a hard block and a block in water lose
  nothing, and a block in water drinks; a body dries to death at 0. The dryness is 1 minus the ground's
  fill: over a year a cell's mean of the air's humidity spreads a third as wide over the land. On c1225,
  seed 9, at dry 0.004 (a body of e065 dries out in about 270 turns on the driest land): 19% of deaths by
  thirst, the land's share of the bodies 31% (e065 41%). The bodies close up with the blocks they have,
  not with armor: they fill their grids and grow (open soft faces per block 0.86 to 0.63-0.73, 27 blocks
  to 34-43), in every medium, while the hard share stays under 5%. Lineages that keep 90% to one medium
  fall to 1-11%. Not kept as the default: the trade-off is priced on land only, a solid body loses
  nothing in water, and the lineages that span the shore carry the land's answer into the water.
- Fifth step (e067, 2026-09-14): breath in water, a row added to section 2, run with e066's dry air at
  0.004. A block over water uses `breath` and each face of a soft block open to the water gives it
  back; a block over land breathes freely; a body suffocates at 0. On c1225, seed 9, at breath 0.01 (a
  solid 6x6 body wholly in water suffocates in about 300 turns): the water's bodies open up (open soft
  faces per block 1.25 at the surface and 1.11 on the bottom against 0.78 on land; e066 0.73, 0.71,
  0.63) and shrink to 23-25 blocks, and suffocation takes only 1.5% of the deaths (thirst 27%). Shapes
  part by medium: 64% of the grown bodies in common birth forms keep 90% to one medium (e066 33%; e067
  first read 85% from the bodies after breaks, corrected by e068). Lineages do not (16%, back in e065's
  range): each large lineage holds an open water form and a more closed land form, joined by mates at
  the shore. Kept, with the dry air, as stage C's default. A kind counted by lineage cannot see forms
  inside one, which bears on section 3's census of kinds.
- Sixth step (e068, 2026-09-14, no runs): kinds counted below the lineage. A body's birth form is the
  body its genes develop (the grid's side, and its blocks of each kind, bite and density at birth), and
  its way of living is read over all the grown bodies of its form: e060's diet, tooth and roaming, and
  the medium where 90% of them stand, else the shore. On e065, e066 and e067 at breath 0.003 and 0.01:
  2.5, 4.5, 6.2 and 6.2 kinds (1.5-2.7 by lineage), and 2.2, 4.6, 4.3 and 5.1 with the medium shuffled
  inside lineages. Breath adds kinds by medium: the largest lineage's open algae eaters at the surface
  and litter eaters on the bottom. The closed land forms are not kinds (3-4% each). Counted per body
  with the medium, every run reads 5-7 kinds, at its shuffle. Stage C is counted by birth form from here.
- Seventh step (e069, 2026-09-15): life history from the genome (#83). The energy to breed per unit of
  mass, the child's share and the fat per unit of mass are read from the gene table, x0.5 to x2 around
  the constants (0.1, 0.5, 5); random genomes start within x0.81-1.25. On e067's world, c1225, seed 9,
  100,000 steps, they move little: medians 0.099, 0.48 and 6.0, the store rising while the start's
  bodies starve, and fat fills 5-12% of a store. Inside a lineage the water and the land differ by 2-3%
  (shuffled 0.7%); the dense land bodies hold more fat (7.8 against 6.0). Kinds by birth form held at
  every census fall to 2 (e067 4), with one lineage at 52% of the grown bodies in every medium. Seeds 10
  and 11 repeat it: 2, 2 and 3 kinds held with the values from the genome against 4, 3 and 5 with the
  constants, while the values still move little (medians x0.89-1.19) and part nothing. The values stay constants.
  With the constants stage C holds 3-5 kinds over seeds, so a step judged on kinds takes three seeds.

## 4. Compute

Measured from e059's batch (128x128, one core per run, 12 runs at once on the Mac): the world alone
costs 3.0 ms a step (337 steps/s), and each body adds 5.1 µs (165 steps/s at 600 bodies, 55 at
3,000).

| stage | one candidate | local (11 cores) + Ubuntu (6) | what it buys |
|---|---|---|---|
| A | measured (e061): 20 years of a 20,000-step year in 47 s at 256 and about 3 minutes at 512 on one core (1.2 and 4.5 ms a climate update, every 10 steps) | 300 candidates (half at 512) in 65 minutes on 10 cores | a wide search |
| B | 10 years = 200,000 steps at 512: per cell per step that is 48 ms a step and 2.7 hours, so the producers go on the climate's 10-step clock, target 10 minutes a candidate | about 100 an hour, if the target holds | a search around A's passes |
| C | measured (e063): 1.34-1.35 ms a step at 512 on one core with the ~300 bodies the world feeds (the world's update about 1 ms, a body about 1 µs), 300,000 steps in 7 minutes. Measured (e064): at s = 1/16, 11 ms a step with 5,652 bodies (a body 1.6 µs, the lineages' detection 0.74 ms and growing with the square of the gene lists), 300,000 steps in 55 minutes. Planned before e063: 5.1 µs a body (e059, in a crowd), about 4 hours a run at 9,600 bodies and 20 at 47,000 | about 90 runs an hour on 11 cores at e063's density, 12 in about an hour at e064's s = 1/16 | a handful of worlds, 6 seeds each; no threads or window at e064's crowd either |

Stage C cannot be searched widely. It takes the few worlds A and B pass. The size of the world was
decided in stage A (e061): 512x512, since at 256 the continents are too small for land habitats wider
than three lifetimes of travel (#68 rule 1). At 512 a world updated per cell per step costs about 48 ms
a step (e059's 3.0 ms at 128), so stage B puts the producers on a slow clock, as the climate is.

## 5. Search

- Search ratios, not raw constants. A: land share, relief, latitude span, day length over lifespan,
  year length over lifespan, the temperature spread (equator to pole, day to night, season), rain
  and wind strength. B: growth of grass : wood : algae, wood's hardness over a body's typical force,
  the chance of ignition. C: the costs of drying and of cold relative to upkeep, bodies per habitat.
- Sample first (Latin hypercube, about 300 candidates in A), keep the passes, refine around them. No
  optimizer until plain sampling shows where the passing region is.
- Every candidate writes one row of measures, so the table of all candidates is the result.

## 6. Building it

- A new crate for the foundation, not e059 grown further (5,900 lines, 49 positional arguments).
  Named parameters in a file replace the positional arguments.
- Stage A first: terrain generation, sun, heat, water with wind, the stage-A measures, and viewer
  layers for temperature, humidity and habitat.
- Port what has survived many experiments instead of rewriting it: the genome and development
  (e002-e004), body physics (e010-e055), the soil and water carrier (e035), the census (e060).
- Stage B adds producers and fire; stage C ports the bodies with the trade-offs of section 2, the new
  census columns and #72's injection. Each stage is an experiment with a README and a report.
- The build is weeks of work, and the search runs cost the machine as stated in section 4.

## 7. Decisions (agreed 2026-09-13: option (a) in every case)

1. **Weather.** (a) Humidity carried by one prevailing wind that turns with the season, rain where
   air rises or cools: rain shadows and wet coasts emerge, and it is cheap. (b) Pressure and wind from
   temperature differences: more emerges, at several times the cost.
2. **Fire.** (a) In the first version. (b) After stage C works without it.
3. **Size of the world.** (a) Decided in stage A by rule 1. (b) Fixed at 128x128.
4. **Producers.** (a) Three plant materials as fields. (b) Plants as evolving organisms from the
   start: a second genome and far more compute.
5. **The day.** A search axis, starting near a fifth of a lifespan (a body lives several days).
6. **What a body can sense.** (a) Add light, temperature and its own water as inputs to today's
   reflex brain, so a body can tell night and cold. (b) Keep today's inputs.

## What this does not promise

No parameters may pass all three stages. If A passes and B fails, the producers' laws are wrong; if
B passes and C fails, the materials of the bodies are. The staged search is chosen so that a failure
says which.
