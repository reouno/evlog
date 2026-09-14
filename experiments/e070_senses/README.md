# e070: senses from sensor blocks (foundation stage C, eighth step, #84)

Date: 2026-09-15

## Purpose

Principle 2: a trait comes out of the blocks a genome builds and the values it expresses; we do not write
what a body can do. What a body senses is still written. Every body, whatever its blocks, sees one cell
ahead, behind, left and right (the food, the bodies and the water there, e023 and e066) and reads its
energy, its thirst and its breath (e066, e067). A sensor block only makes the eye reach further, and each
law so far added one more input by hand.

In e067's world the bodies have dropped the sensor block. Over the second half of the controls (e067's run
for seed 9, e069's constants runs for seeds 10 and 11), 83-93% of the grown bodies hold none (a mean of
0.5-0.9 blocks a body). The start's random bodies hold 2.9-3.7 and lose most of them by step 5,000. A
sensor block is soft, so it dries on land and breathes in the water, and it costs upkeep, while the senses
it adds to are free.

This step makes the senses the sensor blocks' (agreed on #84): a body senses what its sensor blocks
register, and nothing else. No input is added and no price is set.

## Hypothesis

Written before the runs. The conditions are named together: **seeing pays where what lies around a body
differs by direction within its reach, and the body can move only forward.** Both hold in e067's world:
the crowd blocks 47% of moves, the shore has water on one side, and a body steps only to its front.

1. **The sensor blocks come back.** In the second half at least half of the grown bodies have a sensor
   block looking out in at least one direction (the controls: 6-13%), on at least two of the three seeds.
2. **They look ahead.** The grown bodies' mean number of sensor blocks looking out to the front is at least
   1.5 times that to the back (the controls: front 0.03-0.11, back 0.09-0.20), on at least two of the
   three seeds.
3. **The world keeps its kinds.** Kinds by birth form held at every census of the second half (e068's
   count), averaged over seeds 9-11, lie within 1 of the controls' 4.00 (3.0 or more).

Decision rule, set before the runs: the senses of the sensor blocks become stage C's default if every world
stands through 100,000 steps and hypothesis 3 holds. They are kept for principle 2's reason, not for a
gain. Hypotheses 1 and 2 read whether the senses are selected.

## Method

Code: `experiments/e070_senses`, e069's crate with one parameter, `senses` (0: e069 at `history = 0`, which
is e067 at breath 0.01).

- **The readings** (`body.rs`, `sense`). The inputs and the weights that read them are e069's: the food
  under the body; the food, the bodies and the water in each of four directions, what lies j cells away at
  1/j; the energy over the threshold, the thirst and the breath short of full. With `senses = 1`:
  - the food under the body is read on the world cells under its sensor blocks only;
  - a sensor block looks out of the body in a direction when no block of the body lies beyond it that way
    (`sight_of`). A direction is seen as far as one cell and one more per sensor block looking out that
    way, up to 8 more (`Body::reach`, e023's numbers per direction); a direction with none reads 0;
  - the energy, the thirst and the breath are read only by a body with a sensor block.
- **Unchanged.** A sensor block weighs 1/2, costs a block's upkeep and matter, and dries and breathes as a
  soft block. The policy, the strip a look covers (the body's whole width), the knockout of `sense_used`
  (the eye cut to one cell) and the values of a life (constants).
- **Today's configuration.** With `senses = 0` the same function reads every direction as far as one cell
  and one more per sensor block of the body, the food under the whole body, and every body's fills: e069.
- **What else is logged.** `log.csv` gets `feeling` (bodies with a sensor block), `sighted` (with one
  looking out) and `sight_front`, `sight_back`, `sight_left`, `sight_right` (sensor blocks looking out, per
  body). The census reads the same from `cells`.

Checks: the tests pass (a sensor block looks out only where nothing of its body lies beyond it; with
`senses` on a body without a sensor block reads nothing, and one with a sensor block in its front row reads
the front, the left, the right and its fills as with `senses` off and nothing behind, facing north and
east; matter is conserved with `senses` on). With `senses = 0` the first 10,000 steps must equal e069's
check run (`c1225_life9_check`, itself equal to e067's run): every column of its log but the wall times,
every body of the census at step 10,000, every lineage row and every event.

**Runs**, from the repo root, one core each, all at once:

- the pilots: c1225, seeds of life 9, 10 and 11, 100,000 steps, `senses = 1`
  (`bash experiments/e070_senses/run.sh c1225 100000 <seed> senses senses=1`);
- the check: seed 9, 10,000 steps, `senses = 0` (`run.sh c1225 10000 9 check`).

Controls, reused: e067's run at breath 0.01 for seed 9 and e069's `c1225_life{10,11}_constants`, the same
world, seeds and laws with the senses given to every body.

Cost, before the runs: 4 local cores, about 35-40 minutes for the pilots and 5 for the check. The change
walks each sensor block's four lines to the grid's edge when a body's blocks change (at development and
after a break), and a decision reads no more than in e069 (a dark direction is skipped).

Read, second half of each run: the sensor blocks (bodies with one, bodies with one looking out, per
direction, by medium) against the controls; kinds by birth form with e068's `kinds.py` (held, at a census,
with the medium shuffled, by lineage); bodies, deaths by cause, actions, moves blocked, children without
room, kills' share, `sense_used` and the step's cost.

Analysis: `uv run python experiments/e070_senses/senses.py` (8 seconds), then `report.py`.

## Result

**The checks.** The tests pass. With `senses = 0` the first 10,000 steps equal e069's check run in all 135 of its
log columns but the wall times, in every body of the census at step 10,000 (9,154 bodies, 52 columns), in every
lineage row (85) and in every event (45). The check ran in 421 s with four runs at once (e069's in 316 s with two).

Wall time: 2,019-2,131 s a pilot (34-36 minutes), four runs at once on the Mac. Matter drifts by 4e-14 at most.
Every world stood: 6,729-8,664 bodies at step 100,000.

Second half of each run (steps 50,000-100,000), c1225, s = 1/16, dry air 0.004, breath 0.01. "Given" is the
control (seed 9: e067's run; seeds 10 and 11: e069's constants runs), "sensors" is `senses = 1`.

| | seed 9 given | seed 9 sensors | seed 10 given | seed 10 sensors | seed 11 given | seed 11 sensors |
|---|---|---|---|---|---|---|
| bodies: mean (lowest) | 8,073 (6,900) | 8,102 (6,395) | 9,780 (8,108) | 8,673 (7,241) | 7,484 (6,009) | 8,100 (6,609) |
| grown bodies with a sensor block; with one looking out | 7.1%; 6.1% | 4.4%; 4.3% | 10.7%; 9.1% | 2.9%; 2.2% | 17.1%; 13.1% | 3.1%; 2.2% |
| sensor blocks looking out per grown body: front / back / left / right | 0.03 / 0.09 / 0.09 / 0.03 | 0.10 / 0.08 / 0.05 / 0.11 | 0.07 / 0.20 / 0.20 / 0.06 | 0.03 / 0.04 / 0.01 / 0.05 | 0.11 / 0.19 / 0.13 / 0.13 | 0.03 / 0.02 / 0.03 / 0.02 |
| kinds by birth form held at every census | 4 | 3 | 3 | 3 | 5 | 3 |
| kinds at a census: mean (lowest-highest) | 6.2 (5-8) | 3.2 (3-4) | 6.2 (5-7) | 3.2 (3-4) | 6.0 (5-7) | 4.0 (3-5) |
| the same with the medium shuffled | 5.1 | 3.2 | 5.5 | 3.2 | 5.0 | 3.2 |
| kinds per lineage (e060) | 2.5 | 1.7 | 2.5 | 2.0 | 3.2 | 2.7 |
| lineages alive (top lineage's share) | 14.8 (43%) | 9.6 (73%) | 34.3 (53%) | 13.9 (76%) | 26.6 (59%) | 18.6 (67%) |
| decisions: stay / forward / turn | 6% / 78% / 17% | 4% / 85% / 10% | 6% / 78% / 16% | 3% / 87% / 10% | 6% / 78% / 16% | 2% / 90% / 8% |
| grown bodies: median distance from birth; mean path (cells) | 9.3; 35.1 | 28.4; 37.1 | 8.2; 34.7 | 27.6; 36.6 | 9.5; 31.7 | 21.6; 31.3 |
| moves blocked; children with no room | 47%; 39% | 33%; 29% | 47%; 38% | 35%; 24% | 46%; 42% | 45%; 33% |
| births per body per 1,000 steps | 3.74 | 4.38 | 4.19 | 4.57 | 3.07 | 3.95 |
| deaths: hunger / thirst / suffocation | 66% / 27% / 1.5% | 69% / 26% / 1.2% | 65% / 23% / 1.2% | 72% / 23% / 1.6% | 63% / 27% / 3.9% | 70% / 21% / 3.5% |
| kills' share of intake | 12% | 10% | 16% | 10% | 13% | 13% |
| blocks a body (mean) | 28 | 23 | 24 | 21 | 37 | 26 |
| a step on one core | 20.3 ms | 17.1 ms | 20.6 ms | 17.9 ms | 17.0 ms | 17.7 ms |

Over the three seeds, given against sensors: kinds held 4.00 against 3.00; at a census 6.11 against 3.44; with the
medium shuffled 5.20 against 3.17 (a gain of 0.91 against 0.28); per lineage 2.72 against 2.11; the top lineage 52%
against 72%; bodies 8,446 against 8,291.

**The sensor blocks do not come back.** At every census of the runs with senses from sensor blocks, 1-6% of the
grown bodies have a sensor block looking out (the controls 3-12%). The start's random bodies hold 2.5-3.8 sensor
blocks at step 1,000, and by step 3,000 the bodies hold about 0.5, as in the controls.

**The few that see sit.** In those runs the grown bodies with a sensor block looking out lie a median of 0 cells from
where they were born and place 1.7-2.5 children per 1,000 steps of age, against 3.8-4.5 for the blind. In the
controls of seeds 10 and 11, where every body sees, the same split is 2.7-3.0 against 3.0-3.2 (e067 did not log
children).

**The blind walk straight.** Turns fall from 16-17% of the decisions to 8-10%, and the grown bodies end 22-28 cells
from where they were born, against 8-10, over about the same path. Fewer moves are blocked on seeds 9 and 10 (33-35%
against 47%) and fewer children find no room (24-33% against 38-42%).

**Every seed ends with the same three kinds, all at the shore**: a roaming plant eater of density 1 (55-65% of the
grown bodies, a median 28-34 cells from birth), a dense roaming mixed eater (13-21%) and a plant eater that stays
(8-11%, the kind with the most sensor blocks). No kind keeps 90% of its bodies to one medium, so the medium adds
almost nothing over the shuffle. The controls' roamers of the surface and of the bottom and their sitters of the
bottom and of the land are gone.

1. **The sensor blocks come back (half the grown bodies look out, on 2 of 3 seeds): no.** 4.3%, 2.2% and 2.2%, under
   the controls' 6-13%.
2. **They look ahead (front at least 1.5 times back, on 2 of 3 seeds): no.** 0.10 against 0.08, 0.03 against 0.04,
   0.03 against 0.02.
3. **The world keeps its kinds (mean held over seeds 9-11 of 3.0 or more): yes, at the line.** 3, 3 and 3 against 4,
   3 and 5.

## Conclusion

**Kept as stage C's default, by the rule set before the runs**: every world stood and the kinds held at every
census average 3.00, the line. The rule is met at its edge, and the finer counts fall on every seed: 3.2-4.0 kinds at
a census against 6.0-6.2, none kept to one medium, one lineage holding 67-76% of the grown bodies. From here a body
senses through its sensor blocks, and these three runs are the controls of the next step.

**In this world the bodies do not buy sight.** A sensor block is not selected when every sense depends on it. The
bodies that keep one sit and place about half the children of the blind; the blind walk straight, three times as
far from their birth. The controls' kinds of one medium came with senses every body was given; without them one
roaming form holds most of the world. Why a sensor block does not pay is not shown: its readings reach the actions
through weights the same genes set at random, and the grazed food is even (#64).

These answers hold for this world and these choices: c1225, seeds 9-11, 100,000 steps from random genomes, s = 1/16,
dry air 0.004, breath 0.01, e069's policy (a linear map from 16 readings to four actions), a sensor block at e023's
weight, cost and reach, a look as wide as the body, the readings of the old menu, and e068's census. Not shown: c1236,
longer runs, a start from bodies that already see, and a world where walking straight costs more.

Next, proposed (not yet agreed): (a) follow the rule and go on with section 2 on this world (cold, the next row),
judged on seeds 9-11 against these runs, with the sensor blocks counted there too; (b) set the rule aside, since it
is met at its edge, and keep the given senses for stage C until a law makes walking blind cost; (c) first ask whether
sight can pay here at all, by putting the controls' sighted forms into this world (#72's injection, still to build).
Recommended: (a). Agreed 2026-09-15: (a), filed as #86.
