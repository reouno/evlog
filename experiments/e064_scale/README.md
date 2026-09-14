# e064: a body's scale of matter (foundation stage C, second step, #78)

Date: 2026-09-14

## Purpose

e063 put e059's bodies on e062's world and found compute is not stage C's limit (1.34 ms a step at
512) but the density is: the world feeds about 300 bodies, one per 360-530 land cells, and they
live one way (roaming grass eaters without a tooth, kills 2-5% of the intake). The bodies keep
e059's economy (a 16-block body pays 0.064 a step) while e062's grass grows 0.0004-0.0006 a step a
land cell. No trade-off of `foundation.md` section 2 can be judged in a world this thin (#68 rule 2:
the crowd makes the niches), so the density has to be set first. Agreed in #76: option (a), one
scale on a body's matter. This experiment asks whether that scale buys a crowd, and at what cost.

## Hypothesis

Written before the runs.

1. **The crowd grows, but far less than 1/s.** A body at scale s draws s of what it drew, so the
   world's grass could feed 1/s as many (1,200 at s = 1/4, 5,000 at s = 1/16). But grass grows by
   its own cover, stand / (stand + 0.2), and a gut takes a full bite from a cell that holds s of a
   bite, so smaller bodies can graze the stand lower before a cell stops paying them. If they graze
   it to s of e063's stand, the grass grows 0.47 of e063's at s = 1/4 and 0.15 at s = 1/16 (from
   e063's 0.33 a land cell), and the bodies are 1.9 and 2.4 times e063's. Expected: 500-900 bodies
   at s = 1/4 and 600-2,000 at s = 1/16, the grass standing and growing less as s falls.
2. **Bodies meet more, but the world still lives one way.** Contacts per body a step rise with the
   density; kills stay under 10% of the intake and one way of living holds each lineage.
3. **Still cheap.** A body costs under 2 µs in the crowd, and a run of 300,000 steps at s = 1/16
   under 1 hour on one core.

Decision rule: the s stage C runs at is the largest at which bodies meet (contacts per body clearly
above e063's, a kills' share that moves) at a cost that allows 6 seeds on 2 worlds. If no s gives a
crowd because the grass grows from its own stand, that is the answer: the density is set by the
producers' law, not by the body's scale, and the next step is there.

## Method

Code: `experiments/e064_scale`, e063's crate with one parameter, `scale` (s). A body keeps its
energy, fat, blocks, upkeep, bite, moves and threshold in its own units, and s converts where
matter crosses between a body and the world (`body.rs`, `main.rs`):

- a gut takes BITE x s of the world's grass and dead a step, and gains what it took / s;
- what a body spends (upkeep the fat pays, fat over the store, the work of moving) goes to the soil
  as the spent x s;
- what lies dead (a body, a broken or worn block nobody ate, a child with no room) lies as x s;
- the world's matter counts a body's energy, fat and blocks x s;
- the eye reads the food in the body's units, (grass + dead) / s, so s changes the crowd and not
  what a body sees (#78's open point, taken as recommended).

A block's weight, its wear and the clock are not matter and do not scale. The start is e063's
(0.0977 bodies per land cell, random genomes, 5 of energy in the body's units). A new log column,
`grass_grown`, is the grass grown a step on the whole world.

**Runs.** c1225 with e062's draw d11, from e063's cached settled world, seed of life 9, 100,000
steps, one thread each, three at once on the Mac: s = 1/4 and 1/16, and s = 1 to check the
conversions change nothing (its logs must equal e063's but for the wall times and the new column).
`bash experiments/e064_scale/run.sh c1225 100000 9 1 0.25 0.0625` from the repo root. Controls:
e063's s = 1 run and its world without bodies (`experiments/e063_bodies/results/c1225_*`).

Cost, before the runs: 3 cores, about 2.5 minutes (s = 1), 5-10 (1/4) and 10-40 (1/16), at most
one core-hour.

Read, second half of each run: bodies, land cells per body, contacts per body a step, the kills'
share, ways of living per body and per lineage (e060's census), travel, µs per body, the grass
standing and grown and the land burnt against the control.

## Result

Second half of each run (steps 50,000-100,000), c1225, seed 9. The s = 1 run is e063's, reproduced
exactly: every cell of the log but the wall times, every body, lineage and event match e063's files.
The world without bodies (run again here to log the grass grown) matches e063's control the same way.

| | s = 1 (e063) | s = 1/4 | s = 1/16 |
|---|---|---|---|
| bodies: mean (lowest-highest) | 306 (186-494) | 770 (382-1,228) | 5,652 (4,123-7,806) |
| land cells per body | 362 | 144 | 20 |
| contacts per body a step | 0.067 | 0.103 | 0.289 |
| intake: grass / kills / the dead | 95% / 2% / 3% | 88% / 7.5% / 5% | 72% / 17% / 11% |
| grown bodies with over a fifth of their intake from kills | 2% | 12% | 29% |
| bodies with a tooth | 0.2% | 6.6% | 2.5% |
| ways of living (e060): per body, per lineage | 1-2, 1 | 2-4, 1-3 | 4-5, 2-4 |
| grown bodies living the commonest way | 92% | 59% | 38% |
| lineages alive (top lineage's share) | 2.1 (77%) | 6.8 (33%) | 24.1 (19%) |
| blocks; muscle, gut, hard | 25.5; 11.7, 12.5, 0.04 | 42.8; 21.8, 19.5, 0.98 | 17.4; 6.2, 10.5, 0.50 |
| density (1/2 to 2); grid side; speed | 1.08; 7.3; 0.44 | 1.13; 6.9; 0.47 | 1.95; 4.5; 0.19 |
| moves blocked; children with no room | 29%; 2% | 37%; 24% | 52%; 41% |
| median distance of a grown body from its birthplace | 35 cells | 14 cells | 7.7 cells |
| deaths: hunger / broken | 99% / 1% | 98% / 2% | 89% / 11% |
| grass standing, of the control's | 23% | 13% | 7% |
| grass grown a step (control 62.6) | 26.3 | 16.1 | 13.6 |
| bodies' intake a step, in the world's matter | 12.6 | 9.3 | 12.7 |
| litter / wood standing, of the control's | 28% / 81% | 19% / 99% | 14% / 101% |
| land burnt a year (control 0.94%) | 0.52% | 0.21% | 0.14% |
| a step: world + bodies + lineages | 1.03 + 0.33 + 0.00 ms | 1.09 + 0.80 + 0.00 ms | 1.11 + 9.11 + 0.74 ms |
| a body a step | 1.08 µs | 1.04 µs | 1.61 µs |
| 300,000 steps on one core | 7 min | 9.5 min | 55 min |
| matter drift, largest | 4e-14 | 4e-14 | 4e-14 |

Wall times: 100,000 steps took 2.3 minutes (s = 1), 3.2 (1/4) and 18 (1/16), three runs at once and
the control, one core each.

1. **The crowd grows, far less than 1/s: partly.** s = 1/4 holds 770 bodies, 2.5 times e063's and
   inside the 500-900 expected. s = 1/16 holds 5,652, 18.5 times: more than 1/s, and far above
   600-2,000. The mechanism was half right. The grass stands lower as s falls (23%, 13%, 7% of the
   control) and grows less (26.3, 16.1, 13.6 a step, against 62.6 without bodies). But at s = 1/16
   the bodies take in as much of the world's matter as at s = 1 (12.7 a step): they eat 67% of the
   grass that grows (46% at s = 1) before it dies to litter or burns (the land burns a quarter as
   much), 28% of what they eat is other bodies (5%), and a body is 17 blocks, not 26.
2. **Bodies meet more, and the world still lives one way: no.** Contacts per body rise 1.5 and 4.3
   times, the kills' share from 2% to 7.5% and 17%, and the ways of living from one a lineage to 1-3
   and 2-4. The commonest way holds 38% of the grown bodies at s = 1/16 (92% at s = 1). The kills of
   the crowd are not the tooth's: at s = 1/16, 29% of the grown bodies take over a fifth of their
   intake from kills, and 2% of those carry a tooth. The crowd drives the density to its ceiling (1.95
   of 2): a denser soft face breaks a lighter one when pressed (e025), so in a jam density is armor
   and weapon at once. The bodies pay for it in speed (0.19) and grow small grids (side 4.5).
3. **Still cheap: yes, barely.** A body costs 1.0-1.6 µs. A step at s = 1/16 costs 11 ms, 83% of it
   the bodies; 300,000 steps take 55 minutes on one core. The lineages' detection (0.74 ms a step)
   grows with the square of the gene lists alive and is the part to watch.

The crowd jams. At s = 1/16 half the moves are blocked and 41% of the children find no room; a grown
body stands 7.7 cells from its birthplace. It is also more varied: 24 lineages alive and 2,307 birth
shapes at a census (122 at s = 1).

## Conclusion

**The scale buys a crowd, and the crowd makes ways of living.** At s = 1/16 the world holds 18 times
e063's bodies, the kills' share moves (17%), and each lineage lives 2-4 ways where e063's lived one:
#68's rule 2 (the crowd makes the niches) holds here too. The number of bodies is not set by the
grass's regrowth alone: under the crowd the grass grows a fifth of what it grows alone, but less of
it dies or burns and the bodies eat their dead.

**What the crowd costs.** Half the moves are blocked and two children in five find no room, the jam
e056 measured (60% and 29%). Every body is as dense as a genome can make it, so the density law's
ceiling (2, e025's choice) now binds, and the kills come from density, not teeth. A run of 300,000
steps takes 55 minutes: 12 runs (6 seeds on 2 worlds) take about an hour on 11 cores of the Mac and
the Ubuntu box.

**For stage C.** s = 1/16 is the only scale tried where lineages differ in how they live, at a cost
that still allows 6 seeds on 2 worlds; s = 1/4 is cheap (9.5 minutes) and meets less (kills 7.5%).
The pinned density matters for the next step: `foundation.md`'s first trade-off, the water's two
layers, sets density against reach (a light body lives at the surface), which is a price on the
armor the crowd now buys. The options and a recommendation are in #78.

These answers hold for this world and these choices: c1225 only, one seed, 100,000 steps, e063's join
(bodies on land, grass and the dead as food, what a body spends to the soil under it), the eye
reading food in the body's units, and three scales. Not shown: c1236, other seeds, longer runs, a
scale between 1/4 and 1/16, and what the crowd does with a density range other than 2.
