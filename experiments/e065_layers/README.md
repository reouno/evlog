# e065: the water's two layers (foundation stage C, third step, #79)

Date: 2026-09-14

## Purpose

e064 set stage C's density: at scale s = 1/16 the world c1225 holds 5,652 bodies, kills are 17% of
the intake and each lineage lives 2-4 ways. But the crowd lives on land only (the sea is a wall), it
jams (52% of moves blocked, 41% of children without room), and every body's density sits at the
ceiling of 2. In the jam a denser soft face breaks a lighter one, so density is weapon and armor at
once and nothing prices it. `foundation.md` section 2's first row prices it: a water cell has a
surface layer and a bottom layer, a body lighter than water lives at the surface and a denser one on
the bottom, and each touches and eats only its own layer. This is the first of section 2's
trade-offs, tested at stage C's density (agreed in #78, filed as #79).

## Hypothesis

Written before the runs. The two conditions are named together: **a light body pays when the
surface has food of its own (the algae) and the crowd makes density a weapon (s = 1/16)**. Both hold
in this world: without bodies the algae grow about 77 a step on c1225 (their stand, 38,368, over
their life of 500 steps), more than the grass's 62.6.

1. **The water fills, at both layers.** The world holds 2-5 times e064's bodies, most of them in
   the water, and the surface and the bottom each hold at least 10% of the bodies.
2. **Density splits around 1.** At the surface the crowd's arms race runs up to the density of
   water, so surface bodies sit just under 1 (median 0.85 or more), while land and bottom bodies stay
   near the ceiling (1.8 or more). 20-60% of the bodies are lighter than water.
3. **Kinds by medium.** Nine grown bodies in ten belong to lineages that keep 90% of their grown
   bodies in one medium, and counting the medium as a fourth part of a way of living (e060's diet,
   tooth and roaming) gives more ways per lineage than e064's 2-4.
4. **The land does not change much, and it stays cheap.** Moves blocked on land stay within 10
   points of e064's 52%, since the grass sets the land's crowd. A step costs under 50 ms, and the
   lineages' detection under a third of it.

Decision rule: the law is kept for stage C if the surface and the bottom both hold (hypothesis 1)
and density splits (2). If the water fills but at one layer only, the food of the other layer is the
thing to look at before anything else.

## Method

Code: `experiments/e065_layers`, e064's crate with scale 1/16 as the default and one parameter,
`water` (1: open, 0: e064's wall).

- **Layers** (`body.rs`). A body's layer is the surface if its density is under 1, else the bottom;
  a body's density is fixed at birth, so its layer is too. Occupancy is kept per layer: a water
  sub-cell has one slot per layer, a land sub-cell holds its body in both. A body moves, fits,
  presses, is shoved, turns and finds a mate through its own layer's slots, so in the water bodies of
  different layers never meet, and on land every body meets every other. A body over land and water
  at once holds, sub-cell by sub-cell, the land's slot or its layer's.
- **Food** (`plants.rs`, `main.rs`). A gut block over water takes its layer's food: the algae at the
  surface; on the bottom, the algae's dead (litter) and the carrion, in their proportions. A gut
  over land takes the grass and the carrion, as in e063. With the water open the algae's dead lie on
  the bottom as litter, which rots as the land's litter does (warmth x water), instead of going
  straight to the water's soil. What a body spends goes to the soil under it, in the water too, and
  the dead lie as carrion where they are.
- **The eye** reads the food and the crowd of its own layer.
- **Where bodies go.** All water is open, shallow and deep. Pools on land stay land for a body. The
  start places 0.0977 bodies per cell over the whole world (e064: per land cell).
- **The settled world** is e063's cached one, whose algae's dead went to the soil; the bottom's litter
  builds up from the bodies' start (the algae turn over in 500 steps).

Checks: the tests (the layers meet and pass as above, each layer takes its own food, and the matter
of the world is conserved with the water closed and open, to 1e-9) pass; `water = 0` must reproduce
e064's s = 1/16 run exactly for its first 10,000 steps (every log column e064 has, but the wall times).

**Runs**, from the repo root, one core each:

- the pilot: c1225, seed of life 9, 100,000 steps, water open
  (`bash experiments/e065_layers/run.sh c1225 100000 9 water`);
- the world without bodies under the open water's law (`start=0`, 100,000 steps), for the algae and
  the bottom's litter;
- the check: `water=0`, 10,000 steps.

Control: e064's s = 1/16 run (`experiments/e064_scale/results/c1225_life9_s0.0625_*`), the same world,
seed and scale with the sea a wall.

Cost, before the runs: 3 cores, the pilot about 30-90 minutes (a short trial of a few thousand steps
measures it first), the world alone about 2 minutes, the check about 2 minutes.

Read, second half of each run: bodies on land, at the surface and on the bottom; density's spread and
by medium; ways of living per body and per lineage, with and without the medium; the share of each
lineage in its commonest medium; the kills' share by medium; moves blocked and children with no room
by medium; the algae and the bottom's litter against the world without bodies; the cost of a step.

Wall time: 22 minutes for the pilot (three runs at once for its first two minutes), 106 s for the world
alone, 133 s for the check, one core each.

## Result

Second half of the run (steps 50,000-100,000), c1225, seed 9, s = 1/16.

**The checks.** The tests pass. With `water = 0` the first 10,000 steps equal e064's s = 1/16 run in
every log column but the wall times, and in every body of the census, every lineage and every event.
The world without bodies under the open water's law keeps e062's producers (algae 38,368, as in e064's
control) and holds 159,696 of the algae's dead on the bottom, settled by 10,000 steps.

| | sea a wall (e064) | water open (e065) |
|---|---|---|
| bodies: mean (lowest-highest) | 5,652 (4,123-7,806) | 5,561 (4,735-7,162) |
| on land / at the surface / on the bottom | 5,652 / - / - | 2,264 / 2,214 / 1,082 |
| contacts per body a step | 0.289 | 0.199 |
| intake: grass / algae / algae's dead / kills / the dead | 72% / - / - / 17% / 11% | 28% / 40% / 15% / 13% / 5% |
| intake a step, in the world's matter | 12.7 | 14.8 |
| kills' share of intake: land / surface / bottom | 17% / - / - | 21% / 5% / 13% |
| mean density: all; land / surface / bottom | 1.95 | 1.18; 1.38 / 0.99 / 1.17 |
| bodies lighter than water | 4% | 49% |
| grown bodies in lineages keeping 90% of them in one medium | (one medium) | 8-23% |
| ways of living (e060): all grown / per lineage; with the medium counted | 4-5 / 2-4 | 3-4 / 1-3; 5 / 2-5 |
| lineages alive (top lineage's share) | 24.1 (19%) | 23.5 (55%) |
| moves blocked: all; land / surface / bottom | 52% | 34%; 41% / 34% / 22% |
| children with no room: all; land / surface / bottom | 41% | 21%; 29% / 10% / 19% |
| standing, of the world alone: grass / algae / bottom litter | 7.3% / 100% / - | 1.5% / 4.4% / 0.9% |
| grass grown a step (alone 62.6) | 13.6 | 5.0 |
| a step: world + bodies + lineages | 1.11 + 9.11 + 0.74 ms | 1.14 + 9.65 + 0.16 ms |
| 300,000 steps on one core | 55 min | 55 min |
| matter drift, largest | 4e-14 | 4e-14 |

What each medium's grown bodies ate over their lives (the censuses of the second half): on land 58%
grass, 13% algae and 5% the algae's dead (guts over the shore), 19% kills, 5% the dead; at the
surface 94% algae, 4% kills; on the bottom 74% the algae's dead, 13% kills, 8% the dead, 5% grass.

Density at a census: 76% of the surface's bodies lie in 0.87-1.00; 65% of the bottom's in 1.00-1.15;
the land's in two groups, 35% in 1.00-1.15 and 30% in 1.74-2.00. The two largest lineages hold 66% of
the grown bodies, sit at density 1.00 (p10-p90 0.99-1.10) and stand 51-64% at the surface, 17-22% on
the bottom and 19-27% on land. The dense lineages (1.2-1.95) keep to land and the bottom: 1598 is 99%
land at 1.80, 1596 92% land at 1.95, 1690 half land and half bottom at 1.59, 1425 70% bottom at 1.44.

The bodies rose to 21,781 in the start's first 1,000 steps (on land's standing grass), fell to
7,000-8,000 by 10,000 steps, and drifted down from 7,837 at 30,000 steps to 4,735 at 75,000 and
5,333 at 100,000.

1. **The water fills at both layers: partly.** The surface holds 40% of the bodies and the bottom 19%,
   but the world holds 5,561, not 2-5 times e064's 5,652. Every producer grows by its own stand, and
   the crowd grazes all three down: the algae to 4.4% of the world alone, the bottom's litter to 0.9%,
   the grass to 1.5% (7.3% under e064's crowd, which now has fewer bodies on land). The water feeds 55%
   of the intake.
2. **Density splits around 1: partly.** The surface sits just under 1 (mean 0.99) and 49% of the bodies
   are lighter than water. But land and the bottom are at 1.38 and 1.17, not near the ceiling: the
   world's density is no longer pinned (1.18, e064 1.95).
3. **Kinds by medium: no.** 8-23% of the grown bodies are in lineages that keep 90% of them to one
   medium. Counting the medium in a way of living gives 5 ways among all grown bodies and 2-5 per
   lineage, but e060's ways alone fell to 3-4 and 1-3, and the top lineage holds 55% of the bodies (19%).
4. **Land changes little, and it stays cheap: partly.** Land's moves are blocked 41% of the time, 11
   points under e064's 52%. A step costs 10.95 ms, as e064's, and the lineages' detection 0.16 ms.

## Conclusion

**The water's two layers are kept for stage C** by the rule set before the run: both layers fill (40%
and 19% of the bodies) and density is priced, no longer every body's free armor (mean 1.18, e064 1.95).
The crowd is less jammed where it spreads (34% of moves blocked, 21% of children without room).

**They do not make kinds by medium.** A layer picked by a threshold on one number that the genome
expresses makes the threshold the best place to be: a lineage at 1.00 is as hard as a surface body can
be, and its bodies stand in both layers and on land. Only lineages far from 1 keep to land and the
bottom. Kinds kept to a medium need a trade-off one small change cannot cross: a medium that asks for
different blocks, not a different density. `foundation.md`'s next row, dry air (a soft block loses water
out of the water), is one.

**The number of bodies did not grow** with the ground open to them. The producers grow by their
standing matter, and a crowd grazes every pasture it reaches to a few percent of it; opening the water
spread the same grazing over more ground (the world's intake 14.8 a step, e064's 12.7). Stage B judged
its producers without grazers.

These answers hold for this world and these choices: c1225 only, one seed, 100,000 steps (the bodies
were still drifting down at its end), s = 1/16, the layer by density under 1, all water open and pools
as land, a surface that eats only algae and a bottom that eats the algae's dead and the carrion, a body's
medium read at its middle. Not shown: other seeds and c1236, longer runs, and whether the lineage at
1.00 and its 55% share are the law's or this seed's.
