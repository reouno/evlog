# Foundation

How the world is built: its laws, what is generated and what must emerge, the material trade-offs, the stages it is
searched in and how each is judged, and today's default world. Read it before designing or building a law; change it
when a law or a measure is kept or removed, or the method changes (`CLAUDE.md`, Documents). What each experiment found
is in its README.

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
| fresh water | a body drinks from pools and wet ground, not from the sea | bodies that reach fresh water, bodies that never leave the sea | land bodies far from fresh water | kept (e072) |
| fat | fat has weight; the most a body holds per unit of mass is read from its genome | fat where shortfalls come | fat on a body that moves | kept (e072) |
| light | a sensor block sees as far as the light allows | eyes by day | eyes at night and in deep water | kept (e072) |
| wood | a stand drops browse by what it stands (`wood_yield` 3e-5); a gut takes it only with a hard tip and enough force behind it | bodies with a hard front and muscle | guts without a tooth | kept (e072, e073) |
| flesh | a gut that breaks a block off a body takes that share of what the body holds (`flesh_bite` 0.4); a body dies under half its birth blocks (`frail` 0.5) | bodies that break others | soft, big bodies (a meal) | kept (e075) |
| height | moving onto a higher cell costs the mass lifted times the rise | light bodies, strong muscle on hills | heavy bodies crossing relief | kept (e072) |
| fire | a burning cell breaks soft blocks facing it; hard blocks resist; water shelters | armor, speed, life in water | soft, slow bodies on dry grassland | not built |

## 3. Stages, measures and pass lines

Each stage is judged before the next is built on it, so a failure names its layer.

**Stage A, the environment alone** (terrain, sun, heat, water). A cell's habitat is its medium x temperature band x
moisture band, by quarter. Pass: 5 habitats of 2% of the cells; 3 of them in patches wider than three lives of travel;
10-50% of the cells change habitat in a year; year 20's map agrees with year 10's on 90%. e061: 34 of 300 candidates
pass, 30 of them at 512x512, the size from here; the tilt sets the change; a world is spun up about 20,000 climate
updates before it is judged or lived on. A climate costs 1-8 minutes at 512 on one core. Its regions (pieces of land a
line can hold against another) can be counted from its map alone (e084, e085).

**Stage B, producers** (grass, wood, algae, fire). Pass: each producer holds 5% of the standing matter and is the
larger part of a habitat; none dies out in 10 years; fire burns 1-20% of the land a year; matter is conserved. e062: 9
of 96 candidates pass, and no draw of the rates passes on more than two worlds. Stage C takes draw d11 (grass 0.009983,
wood 0.0017, algae 0.009112, ignite 1.613e-6) on c1225. A candidate costs about 8 minutes at 512.

**Stage C, bodies.** Judged by kinds of living by birth form (e068) at a census and kept to a place, on **six seeds
(9-14)**. A birth form counts a body's blocks of every kind; a group that took half its life's matter from one food
that is not a plant or flesh lives by that food (`census.LIGHT`, e093). Read as a distribution against the control
ladder's - median and spread - never as "+1 kind on every seed": the ladder itself spreads 1.02 kinds (median 7.53) and 1.24 kinds kept to a place (median 4.35), so an effect
of one kind is not readable at all (e092); a spread is read by what it is made of, since one collapsed seed is not a
various world (e100). The categorical done-whens - a kind led by the new food, a form keeping to the new place - are
not noise-limited and decide as before. A piece meant to replace the world (e072's shape) is judged on its own measures
and becomes the new control if it passes. Stability: a kind left out or halved returns, tested by paired injection
beside a control (#72, e074, e076).

**How much a replay agrees** is read beside the count (`analysis/replay.py`, #112). A way's label has 64 boxes and
43 are filled in every run, so the agreement over every way seen saturates (0.91) and is not read; what is read is
the ways **holding 5%** (e092: 0.60), their shares (0.77), whether the largest way is the same one (2 of 6 seeds)
and the birth forms (0.035).

**No measure may be a conjunction over the censuses** (e094): a way's share swings by 61% of its own size, so an AND
over 51 censuses counts 1 where the world holds 8 ways in the mean and drives none out. `kinds_held` is dropped. A
step is judged on **kinds at a census** (median 7.26) and on **ways at 5% of the grown bodies in the mean** (8.0);
"held" survives only as "at the line in 90% of the censuses" (3.0), and #76's pass line (4 kinds on 4 of 6 seeds,
each at 5% for 5 years) is read the same way - the world stands at 3 of the 4, not at 1. The gaps are in `vision.md`.

**Today's default world** (stage C, c1225 with d11, s = 1/16): the trade-offs marked kept in section 2 at the rates
#88 set, with `wood_food` 0, `wood_yield` 3e-5 and the flesh line; the command line is
`experiments/e082_fresh/run.sh` with `unit` 0 and `fresh` 0.05. The controls are the six-seed ladder (e092):
`e081_drink/results/ladder/c1225_life{9,10,11}_u0` and `e092_yardstick/results/ladder/c1225_life{12,13,14}_ctl`,
100,000 steps, 52-73 minutes a run with four at once; `e092_yardstick` is the crate that reproduces them. e100 put
three rejected laws back in and lost 1.8 kinds on every seed, so the world stays as it is (#112).

## 4. Compute

| stage | one candidate | what it buys |
|---|---|---|
| A | 1-8 minutes at 512 on one core (20 years, e061, e085) | 300 candidates in about an hour on 10 cores |
| B | about 8 minutes at 512 (spin-up and 10 years of producers) | about 100 an hour |
| C | about 30 ms a step with about 10,000 bodies; 100,000 steps in about an hour (2.8-3.2x that in 3D, e098) | a handful of worlds, six seeds each (1.2-2.2 hours a batch on 6 cores) |

Stage C cannot be searched widely: it takes the few worlds A and B pass, and a step is judged on six seeds.

## 5. Search, and what this does not promise

Search ratios, not raw constants; sample first (Latin hypercube), keep the passes, refine around them, no optimizer
until sampling shows where the passing region is. Every candidate writes one row of measures, so the table of all
candidates is the result. No parameters may pass all three stages: if A passes and B fails the producers' laws are
wrong, if B passes and C fails the materials of the bodies are. The staged search is chosen so a failure says which.
