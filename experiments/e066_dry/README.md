# e066: dry air (foundation stage C, fourth step, #80)

Date: 2026-09-14

## Purpose

e065 opened the water to bodies: a body lighter than water lives at the surface, a denser one on the
bottom. Both layers filled (40% and 19% of the bodies) and density came off its ceiling (mean 1.18,
e064 1.95). But no kinds kept to a medium appeared. The two largest lineages (66% of the grown bodies)
sit at density 1.00 and live on land, at the surface and on the bottom. 1.00 is the hardest a surface
body can be, and one small mutation puts a child on either side of it. Only 8-23% of the grown bodies
are in lineages that keep 90% of their bodies to one medium.

A kind kept to a medium needs a trade-off that asks for different blocks, not a different number.
`foundation.md` section 2's second row is one: a soft block facing dry air loses water, a hard block
does not, and nothing is lost in water. This experiment builds it on e065's world (agreed in #79, filed
as #80).

## Hypothesis

Written before the pilots. The two conditions are named together: **a hard or compact body pays on
land when the land is dry enough that an open soft body loses its water within a life away from water,
and the land has food the water does not.** The second holds in e065 (58% of the land's grown bodies'
intake was grass). The first is set by the rate: at `dry = 0.004` a median body of e065 (25 blocks, 24
open soft faces, almost no hard block) dries out in about 410 turns at the land's median dryness and
270 in its driest tenth; at `dry = 0.001` in 1,650 and 1,100 turns, longer than most lives. The
predictions are for 0.004; 0.001 should fall between e065 and 0.004.

1. **The land's bodies change their blocks, the water's do not.** On land, hard blocks rise from 1.6%
   of the blocks to 10% or more, or open soft faces per block fall from 0.86 to 0.60 or fewer (both counted over
   all the land's blocks at the censuses). At the
   surface and on the bottom both stay within 0.05 of e065's.
2. **Kinds by medium.** The grown bodies in lineages that keep 90% of them to one medium rise from
   8-23% to 50% or more.
3. **Thirst thins the land.** The land's share of the bodies falls from 41% to 15-35%, and 5-30% of
   deaths are by thirst.
4. **Two ways of living on land.** Among grown land bodies, those with a block in water in under a tenth
   of their turns carry at least twice the hard share of those with a block in water in over half.

Decision rule, set before the runs: dry air is kept for stage C if hypothesis 1 holds at one of the two
rates, at the rate that keeps more grown bodies to one medium. If neither rate changes the land's blocks,
the first thing to look at is whether the land still pays (its food and its crowd) under thirst.

## Method

Code: `experiments/e066_dry`, e065's crate with two parameters, `dry` (0: e065) and `drink`.

- **The body's water** (`body.rs`, `dry_turn`). A body holds water, its fill, 1 when full. Each turn,
  each soft block (muscle, sensor, gut) over ground that is not water loses `dry` x the dryness there
  (below) for each face with no block of the body beside it. A hard block loses nothing. A block over
  water loses nothing and drinks `drink`. The loss and the drink are counted in blocks of water, so the
  fill moves by their sum over the body's block count. A compact or armored body has fewer open soft
  faces per block and loses less for its size.
- **Water** for a body is the sea and a pool of standing water on land (500 mm or more, as the algae
  and the habitats count one). The water is a field, not matter: drinking takes nothing from the world.
- **Dryness** is 1 minus the ground's fill (e061's moisture, which the grass also grows by), 0 over
  water. #80 proposed the air's (1 minus its relative humidity) unless its spread over land was much
  narrower than the ground's, so both were measured first, over a year of c1225 without bodies (13 s).
  The air's swings with the day: at one moment the land's median is 0 at night and 0.75-0.83 by day.
  A cell's mean over the year spreads 0.32-0.50 (p10-p90 over the land) for the air and 0.21-0.96 for
  the ground, three times wider, and the two agree (correlation 0.86 over blocks of 4x4 cells). So the
  ground's. Pools are 0.25% of the land cells: on land a body drinks at the sea's edge.
- **Death.** A body whose fill reaches 0 dies of thirst (a fourth cause) and lies as carrion, as any
  dead body does.
- **A child** is born with its parent's fill, and the parent keeps its own (e040's rule). #80 proposed
  a child born full with the parent paying its water. A child born full would give a lineage a free
  refill at every birth, and a parent paying a whole body of water would die on dry land at its first
  birth, so the rule of e040 is kept.
- **The senses** (`foundation.md` decision 6, option (a)). A body sees the water in its four directions
  as it sees the food (the cells of water it would newly lie over, what lies j cells away at 1/j), and
  reads its own thirst, 1 minus its fill. The five inputs are weighed by a new column of the law table,
  drawn from its own stream (e040's way), and read only when `dry` is above 0.
- **What else is logged**: deaths by thirst; the fill, the share of turns with a block in water, the
  open soft faces per block and the share of hard blocks, by medium; the air's and the ground's dryness
  over land; `agents.csv` gets `water`, `drank` (turns with a block in water) and `open_soft`.

Checks: the tests (a soft pair dries by its open faces, a walled-in gut and a hard block lose nothing,
blocks in water drink up to full; the world's matter is conserved under dry air, where some bodies die
of thirst) pass; `dry = 0` must reproduce e065's water run exactly for its first 10,000 steps (every log
column e065 has, but the wall times; every body of the census, every lineage and every event).

**Runs**, from the repo root, one core each:

- the pilots: c1225, seed of life 9, 100,000 steps, `dry = 0.004` and `dry = 0.001`, `drink = 0.1`
  (a body wholly in water refills in ten turns)
  (`bash experiments/e066_dry/run.sh c1225 100000 9 dry0.004 dry=0.004`);
- the check: `dry = 0`, 10,000 steps, against e065's water run;
- the year without bodies for the dryness (`start=0`, 11,880 steps).

Control: e065's water run (`experiments/e065_layers/results/c1225_life9_water_*`), the same world,
seed, scale and layers without the dry air.

Cost, before the runs: 3 cores for about 25 minutes (e065's pilot took 22 minutes; a turn in the air
walks the blocks once more, as the gut does), the check about 5 minutes, the year alone 13 s.

Read, second half of each run: deaths by thirst; hard blocks and open soft faces per block by medium;
the bodies by medium; the share of grown bodies in lineages that keep 90% to one medium; ways of living
per lineage with the medium counted; density; the fill and the share of turns with a block in water,
by medium; and, per grown land body, its hard share against its turns in water.

Wall time: 25 minutes for the pilot at 0.004, 39 minutes at 0.001 (its crowd rose to 16,700 bodies at
30,000 steps), 5 minutes for the check, 13 s for the year alone; one core each, three at once.

## Result

Second half of each run (steps 50,000-100,000), c1225, seed 9, s = 1/16.

**The checks.** The tests pass. With `dry = 0` the first 10,000 steps equal e065's water run in every log
column but the wall times, and in every body of the census, every lineage and every event (checked on
the final binary). Matter drifts by 3e-14 at most.

| | e065 (no dry air) | dry 0.001 | dry 0.004 |
|---|---|---|---|
| bodies: mean (lowest-highest) | 5,561 (4,735-7,162) | 9,423 (6,274-14,865) | 6,273 (4,689-8,724) |
| on land / at the surface / on the bottom | 41% / 40% / 19% | 32% / 30% / 38% | 31% / 40% / 29% |
| deaths by thirst | - | 6.6% | 19.2% |
| hard share of blocks: land / surface / bottom | 1.6% / 0.9% / 2.1% | 2.2% / 1.6% / 3.3% | 2.8% / 4.6% / 2.5% |
| open soft faces per block: land / surface / bottom | 0.86 / 0.88 / 0.86 | 0.87 / 1.12 / 0.99 | 0.63 / 0.73 / 0.71 |
| mean blocks: land / surface / bottom | 27 / 27 / 28 | 28 / 39 / 25 | 43 / 34 / 36 |
| share of the grid a body fills: land / surface / bottom | 0.82 / 0.89 / 0.83 | 0.67 / 0.52 / 0.60 | 0.90 / 0.74 / 0.85 |
| land: fill; turns with a block in water | - | 0.56; 6% | 0.46; 7% |
| grown bodies in lineages keeping 90% to one medium | 8-23% | 13-17% | 1-11% |
| ways of living per lineage; with the medium | 1-3; 2-5 | 1-3; 1-4 | 1-2; 1-4 |
| mean density: land / surface / bottom | 1.39 / 0.99 / 1.19 | 1.51 / 0.99 / 1.47 | 1.06 / 0.98 / 1.17 |
| lineages alive (top lineage's share) | 23.5 (55%) | 25.9 (71%) | 10.3 (70%) |
| kills' share of intake | 13% | 13% | 13% |
| moves blocked; children with no room | 34%; 21% | 47%; 33% | 43%; 37% |
| a step on one core | 10.95 ms | 16.55 ms | 11.61 ms |

Grown land bodies at 0.004: those with a block in water in under a tenth of their turns (3,601 at the
censuses) carry 4.2% hard blocks and 0.66 open soft faces per block; those in water in over half (912)
2.4% and 0.86. At 0.001: 3.6% and 0.98 (6,249) against 1.5% and 1.18 (1,304). The ground under the land's
bodies is as dry as before or drier: mean dryness 0.49 at 0.004, 0.41 at 0.001, 0.42 in e065.

At 0.004 open faces per block were already 0.60-0.71 in every medium by 10,000 steps and stayed there;
mean size stayed at 36-40 blocks while e065's fell from 40 to 26. The largest lineage (a 7x7 grid, gut
over muscle, density 1.04) stood in all three media, with a block in water in 80% of its turns. One
lineage kept to land: 124 grown bodies of 66 blocks at density 1.83, 6% hard, a block in water in 9% of
its turns. Hollow frames of 10x10 lived at the surface, in water 98% of their turns. The run ended with
4 lineages, the largest holding 94% of the bodies.

1. **The land's bodies change their blocks, the water's do not: no.** On land open soft faces per block
   fell to 0.63 (the line was 0.60) and hard blocks rose to 2.8% (the line was 10%). The surface and the
   bottom fell as far, to 0.73 and 0.71. At 0.001 the land did not change (0.87).
2. **Kinds by medium: no.** 1-11% of the grown bodies at 0.004 and 13-17% at 0.001 are in lineages that
   keep 90% of them to one medium (e065 8-23%).
3. **Thirst thins the land: yes.** The land holds 31% of the bodies at 0.004 and 32% at 0.001 (e065 41%),
   and 19% and 7% of the deaths are by thirst.
4. **Two ways of living on land: partly.** Land bodies rarely in water carry more hard blocks and fewer
   open faces than those mostly in water (4.2% against 2.4%), but not twice as many.

## Conclusion

**Dry air is not kept as stage C's default**, by the rule set before the runs: at neither rate did the
land's blocks change apart from the water's.

**The bodies answered with shape, not with armor.** The loss is paid per open face, and the cheap way to
have fewer is to fill the grid: a 6x6 square of gut and muscle opens 24 faces for 36 blocks, and every
block still eats or moves. A hard block weighs twice a soft one and does nothing else, so the land's hard
share stayed under 3%. Filling the grid also made size pay, by perimeter over area: bodies at 0.004 are
34-43 blocks against e065's 27.

**A trade-off priced on one side only is answered everywhere.** In e065 each layer priced the other's
answer (a light body is soft armor, a dense one cannot reach the surface). Here only the land pays, a
solid body loses nothing in the water, and the lineages that span the shore carried the land's answer to
the surface and the bottom. Kinds kept to a medium need the water to price the solid body, for example a
soft face that takes from the water what the body burns, so that a closed body starves there while an
open one dries on land.

These answers hold for this world and these choices: c1225 only, one seed, 100,000 steps, s = 1/16, the
dryness read from the ground's fill, drinking in the sea and pools only (0.25% of the land), a child with
its parent's fill and no water paid for it, a hard block of mass 2, the loss per turn, two rates. At 0.001
a body dries out in over a thousand turns and the land's blocks did not change; what differs there from
e065 at the surface, which loses nothing, is not the loss's doing. Not shown: other seeds and c1236,
longer runs, the air's humidity as the dryness, and drinking from wet ground.
