# Foundation

How the world is built: its laws, what is generated and what must emerge, the material trade-offs, the stages it is
searched in and how each is judged, the scale, and today's default world. Read it before designing a law; change it
when a law or a measure is kept or removed, or the method changes (`CLAUDE.md`). What an experiment found is its README's.

## Why

Sixty experiments added or removed one law at a time and every world held one to three ways of living (e060): a world
with one or two limiting factors cannot show what a third does, and a law added alone meets a world without its
counterweights (e066-e071). So the environment is built whole - laws, generated parts, emergent outcomes - and searched
in stages from the cheapest layer, `principles.md` holding throughout: laws are about materials, never traits.

## 1. Laws, generation, emergence

**Laws** are the same in every world:

- **Conservation** of matter and energy through soil, air and water (e018-e035); the runoff carries soil off the
  land (e072, set G). **The sun**: a day (rotation) and a year (tilt), light by latitude. **Heat**: a cell's
  temperature from light, height and nearby water, spreading to neighbours. **Water**: evaporation by temperature,
  humidity carried by one wind that turns with the season, rain where air rises or cools, flow downhill (e061).
- **Producers as materials**: grass, wood and algae, each growing by light, warmth and water on the climate's
  10-step clock; wood shades what grows under it; fire burns dry standing matter and spreads (e062).
- **Bodies**: a genome of 512 bases develops blocks (hard, muscle, sensor, gut) on a grid of side 4-16 and a linear
  reflex policy (e002-e004); weight and density (e025); contact and force at four sub-cells a cell, a softer face
  broken by the muscle behind a pressing line (e010, e014, e015). A block holds one sub-cell whatever sits around
  it, so the room a body takes is its block count and not its outline: a law that pays per open face buys a body
  faces and no room (e093); moves paid as work and made with chance muscle over
  mass (e048); a store of fat, strict upkeep, wear, connection, a clock that slows heavy bodies (e030-e055); a child
  from a mate within 6 genes. One scale s = 1/16 converts a body's matter to the world's (e064).
- **The material trade-offs** of section 2.

**Generated** from the seed and its parameters: the height map and sea level (land, sea, islands and lakes are
results), the span of latitude, the initial soil and water.

**Emergent**, never written: rivers, lakes, deserts, forests, grassland, climate zones, the fire regime, migration and
every way of living.

## 2. The material trade-offs

Every difference comes with a law about a material that makes one body good there and bad elsewhere; a difference the
bodies can ride out is not an axis (e060). The rows are built and searched as a set, never one at a time.

| difference | law about a material | gains | pays | status |
|---|---|---|---|---|
| water and land | a water cell has a surface layer and a bottom layer; a body lighter than water lives at the surface, a denser one on the bottom, and touches and eats only its layer | light bodies reach the algae; dense ones what sinks | light armor is weak armor; dense bodies cannot reach the surface | kept (e065) |
| dry air | a soft block facing dry air loses water from the body; a hard block does not; nothing is lost in water | armored bodies, bodies near water | soft, spread bodies far from water | kept (e067) |
| breath in water | a block over water uses breath, each open face of a soft block gives it back; a hard block breathes through nothing | open, small bodies in the water | solid or armored bodies in the water | kept (e067) |
| heat | a body holds heat made by its upkeep and passed through its open soft faces; under its band it pays energy to warm, over it water to cool | closed, big, fat bodies in the cold; open, small ones in hot wet places | spread bodies in the cold, closed ones in the heat | kept (e072) |
| fresh water | a body drinks from pools and wet ground, not from the sea; what it drinks is taken from its cell and what it loses goes back (`unit` 9.4) | bodies that reach fresh water, bodies that never leave the sea | land bodies far from fresh water, crowds on one water | kept (e072, e101) |
| fat | fat has weight; the most a body holds per unit of mass is read from its genome | fat where shortfalls come | fat on a body that moves | kept (e072) |
| light | a sensor block sees as far as the light allows | eyes by day | eyes at night and in deep water | kept (e072) |
| wood | a stand drops browse by what it stands (`wood_yield` 3e-5); a gut takes it only with a hard tip and enough force behind it | bodies with a hard front and muscle | guts without a tooth | kept (e072, e073) |
| flesh | a gut that breaks a block off a body takes that share of what the body holds (`flesh_bite` 0.4); a body dies under half its birth blocks (`frail` 0.5) | bodies that break others | soft, big bodies (a meal) | kept (e075) |
| height | moving onto a higher cell costs the mass lifted times the rise | light bodies, strong muscle on hills | heavy bodies crossing relief | kept (e072) |
| fire | a burning cell breaks soft blocks facing it; hard blocks resist; water shelters | armor, speed, life in water | soft, slow bodies on dry grassland | not built |

## 3. Stages, measures and pass lines

Each stage is judged before the next is built on it, so a failure names its layer.

**Stage A, the environment alone** (terrain, sun, heat, water). e061's habitat is medium x temperature band x moisture
band, by quarter; pass: 5 habitats of 2%, 3 of them wider than three lives of travel, 10-50% changing in a year, year
20 agreeing with year 10 on 90%. e061: 34 of 300 candidates pass, at 512x512; a world is spun up about 20,000 climate
updates; 1-8 minutes at 512 on one core; its regions can be counted from its map (e084, e085). **The redesign's
ground** (e102, `base/`): rock provinces, soils, drainage, groundwater, nutrients A and B, winds by band, varying
years; places by medium, temperature, moisture, A:B, fertility. Producers (e104): cohorts dying at their wood's
lifespan.

**Stage B, producers** (grass, wood, algae, fire). Pass: each producer holds 5% of the standing matter and is the
larger part of a habitat; none dies out in 10 years; fire burns 1-20% of the land a year; matter is conserved. e062: 9
of 96 pass, no draw on more than two worlds; stage C takes d11 (grass 0.009983, wood 0.0017, algae 0.009112, ignite
1.613e-6) on c1225, 8 minutes at 512. They are grouped by traits, `analysis/groups.py`.

**Stage C, bodies.** Judged by kinds of living by birth form (e068) at a census and kept to a place, on **six seeds
(9-14)**. A birth form counts a body's blocks of every kind; a group that took half its life's matter from one food
that is not a plant or flesh lives by that food (`census.LIGHT`, e093). Read as a distribution against the control
ladder's - median and spread - never as "+1 kind on every seed": the control ladder (e101) sits at 7.14 kinds and
4.34 kept to a place, six seeds of one world spreading 1.02-1.63 (e092, e101); a spread is read by what it is made
of, one collapsed seed is not a various world (e100). A law is judged with its world over long runs, not alone
(decision rule 6); the redesign (#116) replaces this measure with an open one. The categorical
done-whens (a kind led by the new food, a form keeping to the new place) are not noise-limited and decide as before. A piece
meant to replace the world (e072's shape) is judged on its own measures and becomes the new control if it passes.
Stability: a kind left out or halved returns, tested by paired injection beside a control (#72, e074, e076).

**How much a replay agrees** is read beside the count (`analysis/replay.py`, #112). A way's label has 64 boxes and
43 are filled in every run, so the agreement over every way seen saturates (0.91) and is not read; what is read is
the ways **holding 5%** (e101: 0.66), their shares (0.77), whether the largest way is the same one (4 of 6 seeds)
and the birth forms (0.038).

**No measure may be a conjunction over the censuses** (e094): a way's share swings by 61% of its own size, so an AND
over 51 censuses counts 1 where the world holds 8 ways in the mean and drives none out. `kinds_held` is dropped. A
step is judged on **kinds at a census** (median 7.26) and on **ways at 5% of the grown bodies in the mean** (8.0);
"held" survives only as "at the line in 90% of the censuses" (3.0), and #76's pass line (4 kinds on 4 of 6 seeds,
each at 5% for 5 years) is read the same way - the world stands at 3 of the 4, not at 1. The gaps are in `vision.md`.

**The old default world** (stage C, c1225 with d11, s = 1/16): section 2's kept trade-offs at #88's rates, run by
`experiments/e100_base/run.sh` with `shade_heat`, `shade_dry`, `crown_wet`, `wood_rest` at 0; controls: e101's six-seed
ladder (`e101_unit/results/ladder/`). The world now is `base/` (#116), on its way to section 4's scale.

## 4. Scale and compute

**The scale** (#126, chosen 2026-10-05; `base/` is the planet c1225 until rungs 1-2 stand on it, #127, #128): 64 km
on a side, 512 x 512 cells of 125 m, a tenth of it land (400-500 km2) in 3-5 islands up to 2 km high; climate from
height, the windward and lee sides and the season, not latitude. A body's laws are in metres and seconds - the cell
is the ground's grain, the update the step of integration (19 minutes, lengthened while the readings hold). A body
holds about S kg of animals at any age, S near a large adult's mass (300-1,000 kg, set for ~3 x 10^4 bodies): a grown
large body is one animal, a small kind a flock, a clutch one brood that splits as it grows. The watcher sees a place,
later at real size through a window that plays what the world decided.

**Compute**: the ground costs by its cells, 12-20 s a year at 512 with producers (e105, e106); bodies 2 us a body an
update on a thread, so 3 x 10^4 at 19 minutes are ~110 s a year on six threads. The old stages (A 1-8 minutes a
candidate, B 8, C an hour for 100,000 steps of 10,000 bodies) took the few worlds A and B passed, six seeds a step.

## 5. Search, and what this does not promise

Search ratios, not raw constants; sample first (Latin hypercube), keep the passes, refine around them, no optimizer
until sampling shows where the passing region is. Every candidate writes one row of measures, so the table of all
candidates is the result. No parameters may pass all three stages: if A passes and B fails the producers' laws are
wrong, if B passes and C fails the materials of the bodies are. The staged search is chosen so a failure says which.
