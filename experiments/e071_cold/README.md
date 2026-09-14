# e071: cold (foundation stage C, ninth step, #86)

Date: 2026-09-15

## Purpose

Section 2 of `foundation.md` gives every difference of the world a law about a material that makes one body
good there and bad elsewhere. Water and land (e065), dry air (e066) and breath (e067) are built. The next row is
cold: a block facing a colder cell loses energy by the difference, and hard blocks and fat insulate. It should
favour compact, armored or fat bodies in cold places and winters, and cost spread, soft bodies.

The world it lands in is e070's: c1225 with senses through sensor blocks. c1225 is hot, but its land swings.
Over the second half of e070's censuses the grown bodies on land stand at -6 C (p10), 18 C (median) and 65 C
(p90), and the land's mean goes from 8 C to 37 C over a year. The water holds 17-38 C. In e070 every seed ends
with the same three kinds, all at the shore.

## Design

#86's open questions, settled before the runs (the options not taken in parentheses):

- **The difference from what:** a fixed body temperature, `warm` = 20 C, where e061's hot band starts. (A
  temperature the body holds as a state needs a heat capacity, one more parameter; the warmest cell under the
  body stands for nothing physical.) At 20 C cold is a law of the land in winter and at the far rows.
- **Which faces lose:** every face of a soft block open to the air or the water (no block of its body beside
  it, e066's open faces), over the block's own cell, in the water too, at one rate. (The land only.)
- **Hard blocks and fat:** a hard face loses nothing, as under dry air. Fat insulates by the share of the
  body's store it fills: the loss is times 1 minus that share. (A hard face losing a fraction; fat by amount.)
- **Paid how:** as the moves are paid, from the energy, then the fat, into the soil under the body. A body that
  pays its upkeep but not its cold dies of cold, a cause of its own.
- **The scale:** `cold` = 0.000125 energy a face a degree a turn, set with no runs on e070's censuses
  (`dryrun.py`, second half, seeds 9-11): the median land body (22 open soft faces, upkeep 0.074 a turn) at the
  land's p10 (-6.4 C) loses as much again as its upkeep. Over those bodies the law would take 30% of the land's
  upkeep (53% of the land's bodies pay some) and 3-4% of the water's.
- **A reading:** none. A body does not sense the temperature; it answers with its blocks, or does not.

## Hypothesis

Written before the runs. The conditions are named together: **insulation pays where the cold differs by place
and season (A) and a body cannot leave it within its life (B).** Both hold on c1225's land: at one census it
spans -6 to 65 C and its mean swings 29 C over a year, and a grown body of e070 ends 22-28 cells from its birth.

1. **The land closes up or fattens.** On at least 2 of 3 seeds the grown bodies on land have at least 0.1 fewer
   open soft faces per block than the controls' 0.87, or a median fat fill at least 1.5 times the controls' 0.069.
2. **Forms part by medium.** On at least 2 of 3 seeds at least one kind keeps 90% of its grown bodies to one
   medium (the controls: no kind on any seed).
3. **The world keeps its kinds.** Kinds by birth form held at every census of the second half, averaged over
   seeds 9-11, are at least the controls' 3.0.

Decision rule, set before the runs: cold becomes stage C's default if every world stands through 100,000 steps
and hypothesis 3 holds.

## Method

Code: `experiments/e071_cold`, e070's crate with `senses = 1` as its default and two parameters, `cold` and
`warm`.

- **The law** (`body.rs`, `cold_turn`). For each block of the body, its open faces (`Agent::open`, soft blocks
  only) times `warm` minus the temperature of the world cell under the block, where that is positive; the sum
  times `cold` times 1 minus the fat's fill of the store (`fat / (store x mass)`).
- **The payment** (`main.rs`, after the breath). From the energy, then the fat, into the soil under the body. A
  body that paid its upkeep and whose fat cannot pay the rest dies of cold.
- **What else is logged.** `log.csv` gets `deaths_cold`; `cold_land`, `cold_surface`, `cold_bottom`, the energy
  lost to cold over the upkeep due, by medium; `fat_land`, `fat_surface`, `fat_bottom`, the fat's mean fill of
  the store, by medium. `agents.csv` gets `chilled`, the energy a body has lost to cold.

Checks: the tests pass (a body loses by its open soft faces and the difference over colder cells only, half with
a half-full store, nothing with a full one or walled in by hard blocks; matter is conserved with cold on). With
`cold = 0` the first 10,000 steps must equal e070's run for seed 9 (`c1225_life9_senses`): every column of its
log but the wall times, every body of the census at step 10,000, every lineage row and every event.

**Runs**, from the repo root, one core each, all at once:

- the pilots: c1225, seeds of life 9, 10 and 11, 100,000 steps, `cold = 0.000125`
  (`bash experiments/e071_cold/run.sh c1225 100000 <seed> cold cold=0.000125`);
- the check: seed 9, 10,000 steps, `cold = 0` (`run.sh c1225 10000 9 check`).

Controls, reused: e070's `c1225_life{9,10,11}_senses`, the same world, seeds and laws without cold.

Cost, before the runs: 4 local cores, about 40 minutes for the pilots and 7 for the check. The law adds one pass
over a body's blocks a turn, as dry air and breath do, since a block loses heat to the cell under it.

Read, second half of each run: kinds by birth form with e068's `kinds.py` (held, at a census, with the medium
shuffled, by lineage) and the medium each keeps; open soft faces per block, the hard share, the fat's fill and
the blocks of the grown bodies by medium and by temperature band (e061's cold, mild and hot, of the cell under
them); the energy lost to cold; bodies, deaths by cause, moves blocked, children with no room, the kills' share;
the sensor blocks; the step's cost.

Analysis: `uv run python experiments/e071_cold/cold.py`, then `report.py`.

## Result

**The checks.** The tests pass. With `cold = 0` the first 10,000 steps equal e070's run for seed 9 in all 141 of its
log columns but the wall times, in every body of the census at step 10,000 (9,316 bodies, 52 columns), in every
lineage row (70) and in every event (40). The check ran in 362 s with four runs at once.

Wall time: 1,910-2,250 s a pilot (32-38 minutes), four runs at once on the Mac. Matter drifts by 6e-14 at most.
Every world stood: 6,117-7,023 bodies at the lowest.

Second half of each run (steps 50,000-100,000), c1225, s = 1/16, dry air 0.004, breath 0.01, senses through sensor
blocks. "Control" is e070's run, "cold" is `cold = 0.000125`.

| | seed 9 control | seed 9 cold | seed 10 control | seed 10 cold | seed 11 control | seed 11 cold |
|---|---|---|---|---|---|---|
| bodies: mean (lowest) | 8,102 (6,395) | 8,472 (7,008) | 8,673 (7,241) | 8,703 (7,023) | 8,100 (6,609) | 7,404 (6,117) |
| cold's share of the upkeep due: land / surface / bottom | - | 24% / 1.8% / 2.4% | - | 23% / 1.7% / 2.6% | - | 22% / 1.6% / 2.1% |
| grown land bodies, cold's share of their upkeep: cold / mild / hot band | - | 23% / 16% / 16% | - | 17% / 14% / 15% | - | 15% / 16% / 15% |
| deaths: hunger / thirst / suffocation / cold | 69% / 26% / 1.2% / - | 68% / 20% / 1.6% / 5.2% | 72% / 23% / 1.6% / - | 66% / 22% / 1.4% / 5.3% | 70% / 21% / 3.5% / - | 67% / 20% / 2.6% / 5.3% |
| grown land bodies: open soft faces per block | 0.87 | 0.75 | 0.83 | 0.79 | 0.91 | 0.78 |
| grown land bodies: hard share; blocks | 5.4%; 27.0 | 6.8%; 33.5 | 3.9%; 25.4 | 5.2%; 27.9 | 1.8%; 26.5 | 4.7%; 27.7 |
| grown land bodies: median fat fill | 0.070 | 0.056 | 0.070 | 0.071 | 0.068 | 0.067 |
| grown land bodies in the cold / mild / hot band | 6% / 11% / 83% | 7% / 10% / 82% | 6% / 9% / 85% | 6% / 14% / 80% | 10% / 13% / 78% | 9% / 15% / 76% |
| kinds by birth form held at every census | 3 | 2 | 3 | 2 | 3 | 3 |
| kinds at a census: mean (lowest-highest) | 3.2 (3-4) | 4.3 (3-5) | 3.2 (3-4) | 2.8 (2-3) | 4.0 (3-5) | 3.2 (3-4) |
| the same with the medium shuffled | 3.2 | 4.0 | 3.2 | 3.0 | 3.2 | 3.2 |
| kinds per lineage (e060) | 1.7 | 2.2 | 2.0 | 1.7 | 2.7 | 1.3 |
| lineages alive (top lineage's share) | 9.6 (73%) | 20.2 (55%) | 13.9 (76%) | 8.1 (79%) | 18.6 (67%) | 3.8 (91%) |
| moves blocked; children with no room | 33%; 29% | 41%; 33% | 35%; 24% | 33%; 24% | 45%; 33% | 33%; 27% |
| births per body per 1,000 steps | 4.38 | 4.31 | 4.57 | 4.52 | 3.95 | 5.13 |
| kills' share of intake | 10% | 12% | 10% | 10% | 13% | 10% |
| a step on one core | 17.1 ms | 19.1 ms | 17.9 ms | 17.3 ms | 17.7 ms | 16.0 ms |

Over the three seeds, control against cold: kinds held 3.00 against 2.33; at a census 3.44 against 3.44; with the
medium shuffled 3.17 against 3.39; per lineage 2.11 against 1.72; grown land bodies' open soft faces per block 0.87
against 0.77 and fat fill 0.069 against 0.065.

**Cold is paid on all the land alike.** Over the second half cold takes 22-24% of the upkeep due on land and 2-3% in
the water, and 5.2-5.3% of the deaths are by cold. Counted over their lives, the grown land bodies pay 15-23% of their
upkeep to cold in the cold band and 14-16% in the mild and hot bands. In the controls half the grown land bodies of
every band (50-64%) stand on a cell under 20 C at a census, and the coldest tenth of every band at -4 to -8 C: at a
body's scale a cell's temperature is set by the hour of the day more than by its band. The share of the land's bodies
in each band does not move. On seeds 9 and 10 the grown land bodies stand on warmer cells at a census (medians 25 and
21 C against 17 C); a reading, not shown, is that cold kills the bodies caught on cold cells first.

**The land closes up a little, and does not fatten.** The grown land bodies open 0.04-0.13 fewer soft faces per block
than their controls and their hard share rises by 1-3 points; on seed 9 they also grow (33.5 blocks against 27.0). The
closing is the same in every band: open soft faces per block in the cold, mild and hot bands 0.79, 0.85 and 0.73 on
seed 9, 0.82, 0.78 and 0.79 on seed 10, 0.70, 0.75 and 0.79 on seed 11. The fat fills 6-7% of the store with or
without cold. The water's bodies do not close up (open soft faces per block at the surface 1.11-1.41, the controls
1.13-1.35).

**The same kinds, one fewer held on two seeds.** Every seed ends with e070's kinds, all at the shore: a roaming plant
eater of density 1 (34-72% of the grown bodies), a plant eater that stays (7-30%) and a dense roaming mixed eater
(10-12%). On seed 9 the mixed roamer holds 5% at five censuses of six, and on seed 10 the sitter does, so the kinds held
fall to 2, 2 and 3; at a census both arms average 3.44. On seed 9 more kinds come and go (4.3 at a census): a solid land
sitter of 64 gut blocks at three censuses, an algae roamer at the surface at three and a dense land roamer at two. No
kind held at every census keeps 90% of its bodies to one medium. One lineage holds 55%, 79% and 91% of the grown bodies
(73%, 76% and 67% without cold).

1. **The land closes up or fattens (on 2 of 3 seeds): no.** Open soft faces per block 0.75, 0.79 and 0.78 against the
   line of 0.77 (1 of 3); median fat fill 0.056, 0.071 and 0.067 against 0.104.
2. **Forms part by medium (on 2 of 3 seeds): no.** No kind held at every census keeps 90% of its bodies to one medium,
   on any seed.
3. **The world keeps its kinds (mean held over seeds 9-11 of 3.0 or more): no.** 2, 2 and 3 (mean 2.33) against 3, 3
   and 3.

## Conclusion

**Not kept as stage C's default, by the rule set before the runs**: every world stood, but the kinds held at every
census average 2.33, under the controls' 3.0. The loss is one kind near the 5% line missing one census on two seeds;
the count at a census does not move (3.44). e070's runs stay stage C's controls.

**In this world the cold is a nightly tax on the land, not a place.** Section 2 expected cold to favour compact, armored
or fat bodies in cold places and winters. At 20 C the land's cells fall under the body's temperature every night in
every band, since the day (60 steps) is a fifth of a life and swings a land cell by tens of degrees. So every body on
land pays about the same share, and the answer is the one dry air got in e066: a body a little more closed, everywhere
on land. The fat cannot answer: a body fills its store only with the upkeep it pays from its energy, 6-7% of it here,
which takes about 7% off the loss.

These answers hold for this world and these choices: c1225, seeds 9-11, 100,000 steps from random genomes, s = 1/16,
dry air 0.004, breath 0.01, senses through sensor blocks, a fixed body temperature of 20 C, cold 0.000125 read against a
cell's temperature at the moment, the loss by open soft faces with hard faces closed and the fat's fill insulating, no
reading of the temperature, a 60-step day, and e068's census. Not shown: c1236 (a cool world), a cold that differs by
place, other body temperatures and scales, and longer runs.

Next, proposed (not yet agreed): (a) the same law read against each cell's temperature averaged over the last day (a
running mean on the climate's clock, as the dry air reads the ground's slow fill and not the air's daily swing),
rescaled with a dry run, so the cold differs by place and season as section 2 meant; judged on seeds 9-11 against
e070. (b) A body's heat as a state that follows the cells under it more slowly the heavier the body is, so a big body
carries the day's heat through the night; one more quantity and one more parameter. (c) Leave cold and build section
2's other rows (wood, fire, height) on e070's world. Recommended: (a), the smallest change that makes the cold a
difference of place.
