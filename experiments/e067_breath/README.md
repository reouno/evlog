# e067: breath in water (foundation stage C, fifth step, #81)

Date: 2026-09-14

**Correction (e068, 2026-09-14).** The "common shapes" below were read from `cells`, the body after
breaks and wear, not the body at birth: half the grown bodies have lost blocks, and read that way e065
scores 58%. Read from the birth signature (the grid's side, and the blocks of each kind, bite and density
at birth), the grown bodies in common forms keeping 90% to one medium are 64% at breath 0.01, 44% at
0.003 and 33% in e066 (e065 17%); with the medium shuffled inside lineages 28%, 13% and 4%. The shapes
still part by medium, less than the table says. Counted by birth form, the water forms of lineage 908
are kinds of living and the land's closed forms are not (e068).

## Purpose

e066 priced openness on land: a soft block over dry ground loses water through every face it opens to
the air. At `dry = 0.004` thirst took 19% of the deaths and the land fell from 41% to 31% of the bodies,
but the bodies answered with shape, not armor, and in every medium: open soft faces per block fell from
0.86 to 0.63 on land and to 0.73 and 0.71 in the water, and bodies grew from 27 blocks to 34-43. Only
1-11% of the grown bodies were in lineages that keep 90% of them to one medium (e065 8-23%). A solid
body loses nothing in the water, so the lineages that span the shore carried the land's answer there.

A kind kept to a medium needs a trade-off priced in both. This experiment prices the closed body in
the water with the same count of blocks: a soft face open to the water takes from it what the body
burns (gills, against lungs). A closed body suffocates in the water, an open one dries on land (agreed
in #80, filed as #81).

## Hypothesis

Written before the pilots. The conditions are named together: **an open body pays in the water when
the air dries it on land, and each medium has food the other does not.** The second holds in e066 (the
surface eats the algae, the bottom what sinks, the land the grass). The first is e066's dry air at
0.004, kept on. The rate of breath sets how hard the water presses: e066's grown bodies in the water
open 0.68-0.71 soft faces per block (median), so wholly in water at `breath = 0.01` they would run out
of breath in about 330 turns, within a grown life (their median age is 670-980 steps at 0.6-0.65 turns
a step, 400-640 turns); at `breath = 0.003` in about 1,100 turns, beyond most. e065's open bodies (0.86
per block) would last about 700 turns at 0.01. The predictions are for 0.01; 0.003 should fall between
e066 and 0.01.

1. **The media part their shapes.** Open soft faces per block at the surface and on the bottom exceed
   the land's by 0.20 or more (e066: 0.10 and 0.08; e065: 0.02 and 0.00).
2. **Kinds by medium.** The grown bodies in lineages that keep 90% of them to one medium rise to 30%
   or more (e065 8-23%, e066 1-11%).
3. **The largest lineage leaves the shore.** The lineage with the most grown bodies over the second
   half's censuses keeps 90% of them to one medium (e066's stood in all three).
4. **Breath kills in the water.** 5-30% of the deaths are by suffocation.

Decision rule, set before the runs: breath is kept for stage C if hypothesis 1 holds at one of the two
rates, at the rate that keeps more grown bodies to one medium. If neither rate parts the shapes, the
first thing to look at is whether the water's bodies breathe from the shore instead (the share of
their turns with a block over land) or left the water.

## Method

Code: `experiments/e067_breath`, e066's crate with `dry = 0.004` as its default and two parameters,
`breath` (0: e066 at dry 0.004) and `inhale`.

- **The body's breath** (`body.rs`, `breath_turn`). A body holds breath, a second fill beside its
  water, 1 when full. Each turn, each block over water uses `breath`, and each face of a soft block over
  water with no block of the body beside it gives `breath` back: one open face feeds one block. Each
  block over land gives `inhale`. The net, over the body's block count, moves the fill, up to full. A
  hard block breathes through nothing, so a shell pays in the water too. A solid 6x6 body wholly in
  water (24 open faces, 36 blocks) loses breath x 12/36 a turn; a hollow frame or a line gains.
- **Water** is what a body drinks from (e066): the sea, and pools of 500 mm or more. A body at the
  surface breathes through the water as one on the bottom does; a floating body is not given the air.
  A body over the shore breathes by its blocks on land and drinks by its blocks in water.
- **Death.** A body whose breath reaches 0 dies of suffocation (a fifth cause) and lies as carrion.
- **A child** starts at its parent's breath, as at its water (e066).
- **The senses.** A body reads its breath (1 - fill) as one more input, weighed by a new column of the
  law table drawn from its own stream (e040's way), read only when `breath` is above 0. It already sees
  the water in its four directions.
- **What else is logged**: deaths by suffocation; the breath fill and the share of turns with a block
  over land, by medium; `agents.csv` gets `breath` and `inhaled` (turns with a block over land).

Checks: the tests (a solid body loses breath in the water by its closed blocks, an open one refills
there, a shell loses at the full rate, blocks on land give `inhale`; the world's matter is conserved
under breath, where some bodies suffocate) pass; `breath = 0` must reproduce e066's run at `dry = 0.004`
exactly for its first 10,000 steps (every log column e066 has, but the wall times; every body of the
census, every lineage and every event).

**Runs**, from the repo root, one core each:

- the pilots: c1225, seed of life 9, 100,000 steps, `breath = 0.01` and `breath = 0.003`, `inhale =
  0.1` (a body wholly on land refills in ten turns)
  (`bash experiments/e067_breath/run.sh c1225 100000 9 breath0.01 breath=0.01`);
- the check: `breath = 0`, 10,000 steps, against e066's run at 0.004.

Control: e066's run at `dry = 0.004` (`experiments/e066_dry/results/c1225_life9_dry0.004_*`), the same
world, seed, scale, layers and dry air without breath. It is reused, not run again.

Cost, before the runs: 3 cores for about 25-40 minutes (e066's pilots took 25 and 39 minutes; the
breath turn walks the blocks once more, as the dry air's does).

Read, second half of each run: open soft faces per block and the hard share by medium; the bodies by
medium; the share of grown bodies in lineages that keep 90% to one medium; ways of living per lineage
with the medium counted; deaths by suffocation and by thirst; the breath fill and the share of turns
with a block over land, by medium; and whether the largest lineages still span the shore.

Wall time: 42 minutes of computing for each pilot (the Mac slept for about 11 minutes during them, which
the step clock does not count), 7 minutes for the check; one core each, three at once. The machine ran
slower than for e066: the check, the same work as e066's first 10,000 steps, took 23.8 ms a step at
step 10,000 against e066's 17.0 (a system process held about 1.6 cores). Corrected by that factor
(1.47 per body), a body costs what it cost in e066 (1.5-1.6 µs); the pilots' 20 ms a step is the machine
and 29% more bodies.

## Result

Second half of each run (steps 50,000-100,000), c1225, seed 9, s = 1/16, dry air at 0.004.

**The checks.** The tests pass. With `breath = 0` the first 10,000 steps equal e066's run at dry 0.004
in every log column but the wall times, and in every body of the census, every lineage and every event
(checked on the final binary). Matter drifts by 3e-14 at most.

| | e066 (no breath) | breath 0.003 | breath 0.01 |
|---|---|---|---|
| bodies: mean (lowest-highest) | 6,273 (4,689-8,724) | 7,864 (5,714-10,011) | 8,073 (6,900-9,628) |
| on land / at the surface / on the bottom | 31% / 40% / 29% | 41% / 32% / 27% | 36% / 37% / 27% |
| deaths by thirst; by suffocation | 19.2%; - | 31.3%; 0.5% | 27.4%; 1.5% |
| open soft faces per block: land / surface / bottom | 0.63 / 0.73 / 0.71 | 0.72 / 1.05 / 1.02 | 0.78 / 1.25 / 1.11 |
| grown bodies with an open face per block or more: land / surface / bottom | 10% / 23% / 23% | 31% / 82% / 75% | 42% / 96% / 86% |
| hard share of blocks: land / surface / bottom | 2.8% / 4.6% / 2.5% | 4.5% / 1.8% / 3.0% | 3.3% / 1.3% / 1.5% |
| mean blocks: land / surface / bottom | 43 / 34 / 36 | 37 / 31 / 26 | 34 / 23 / 25 |
| breath: land / surface / bottom | - | 1.00 / 0.94 / 0.91 | 1.00 / 0.96 / 0.92 |
| the water's bodies: turns with a block over land, surface / bottom | - | 5% / 5% | 3% / 4% |
| grown bodies in lineages keeping 90% to one medium: mean (censuses) | 5% (1-11%) | 15% (3-27%) | 16% (8-24%) |
| grown bodies in common shapes keeping 90% to one medium | 32% | 86% | 85% |
| largest lineage: its share of grown bodies; its commonest medium | 78%; 34% surface | 41%; 46% bottom | 39%; 43% bottom |
| ways of living per lineage; with the medium | 1-2; 1-4 | 2-4; 2-5 | 2-3; 3-6 |
| mean density: land / surface / bottom | 1.06 / 0.98 / 1.17 | 1.46 / 0.98 / 1.26 | 1.27 / 0.99 / 1.20 |
| lineages alive (top lineage's share) | 10.3 (70%) | 12.1 (47%) | 14.8 (43%) |
| kills' share of intake | 13% | 12% | 12% |
| moves blocked; children with no room | 43%; 37% | 50%; 46% | 47%; 39% |
| grass standing | 4,161 | 9,233 | 8,164 |
| a step on one core (the machine 1.47x slower, above) | 11.61 ms | 20.55 ms | 20.25 ms |

"Common shapes" are the birth bodies (side and cells) with 20 grown bodies or more over the second half's
censuses: 19%, 16% and 21% of the grown bodies.

**Inside a lineage the water's bodies are the open ones.** Each of the six largest lineages at 0.01 has
grown bodies in all three media, and in each the water's open more faces per block than the land's. The
largest, 908 (39% of the grown bodies: 14% on land, 43% at the surface, 43% on the bottom), opens 1.15 per
block on land and 1.51 and 1.37 in the water, with 25 blocks on land against 15 and 20. Lineage 1640
opens 0.83 on land (38 blocks) and 1.19 and 1.24 in the water (23 and 24). At 0.003 the largest, 1, opens
0.98 on land (36 blocks) and 1.30 and 1.54 in the water (23 and 18). Three dense lineages there (density
1.9-2.0) keep 85-92% of their grown bodies to land and the rest on the bottom.

**The land opened too.** Grown land bodies' median open faces per block rose from 0.64 to 0.85 at 0.01,
and thirst took 27% of the deaths (e066 19%). Their breath is full (inhale gives a block 0.1 a turn), and
the water's bodies have a block over land in 3-5% of their turns: the water's bodies do not breathe from
the shore. Bodies wholly in the water (96% of the surface's grown bodies and 86% of the bottom's) open a
face per block or more and do not run short (breath 0.92-0.96).

1. **The media part their shapes: yes**, at both rates. The surface and the bottom open 0.48 and 0.33 more
   faces per block than the land at 0.01, 0.33 and 0.30 at 0.003 (the line was 0.20; e066 0.10 and 0.08).
2. **Kinds by medium: no.** 16% of the grown bodies at 0.01 (8-24% over the censuses) and 15% at 0.003
   (3-27%) are in lineages keeping 90% to one medium: back to e065's 8-23%, from e066's 5%, not 30%.
3. **The largest lineage leaves the shore: no.** At 0.01 it stands 43% on the bottom, 43% at the surface
   and 14% on land, though it holds 39% of the grown bodies against e066's 78%.
4. **Breath kills in the water: no.** 1.5% of the deaths at 0.01 and 0.5% at 0.003 are by suffocation (the
   line was 5%): the water's bodies opened before breath could kill them.

## Conclusion

**Breath is kept for stage C, at 0.01 together with e066's dry air at 0.004**, by the rule set before the
runs: hypothesis 1 held at both rates, and 0.01 keeps a little more of the grown bodies to one medium
(16% against 15%, well within the spread over the censuses). The pair is kept as it was run; breath
without the dry air was not run.

**A trade-off priced in both media parts the bodies, not the lineages.** The same count of open soft faces,
dear on land and needed in the water, sorted the shapes: 85% of the grown bodies in common shapes keep to
one medium (e066 32%). The lineages still span the shore, and inside each the water's bodies are open and
small and the land's closed and large. A lineage here is a group joined by mates within 6 genes, a few
genes change a shape, and bodies of the land and the water meet and mate at the shore, where the land
holds both layers. So what the census counts as one lineage now holds a form for each medium, and the
lineage measure of kinds by medium (hypotheses 2 and 3) cannot see them.

**The price is paid in shape, not in deaths.** Suffocation took 1.5% of the deaths: the water's bodies are
open lattices and hooks of gut and muscle that breathe more than they burn. The land's bodies, in the same
lineages, came out more open than in e066, and thirst took more (27%). Openness is now priced on both sides
and each medium pulls the lineages its way, where in e066 the land's answer went unopposed. The world holds
more bodies (8,073) in more lineages (14.8, the top at 43%, e066 70%), with 3-6 ways of living per lineage
counted with the medium.

These answers hold for this world and these choices: c1225 only, one seed, 100,000 steps, s = 1/16, dry air
at 0.004, breath per block with one open face feeding one block, a body at the surface breathing through
the water as one on the bottom does, `inhale` 0.1 on land, a child with its parent's breath, two rates, and
lineages joined by mates within 6 genes. Not shown: breath without the dry air, other seeds and c1236,
longer runs, a floating body that breathes the air, and whether the forms inside a lineage would part if
the shore did not join them.
