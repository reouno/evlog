# e072: the balance sets, built together (foundation stage C, tenth step, #88)

Date: 2026-09-16

## Purpose

Stage C has added `foundation.md` section 2's rows one at a time and kept or rejected each by the kinds
held on three seeds. `balance.md` (#87) looks at the whole instead: for every axis a body can vary along,
where it wins and where it loses. Four axes are one-sided or not axes at all (hard blocks, the fat, sight,
the shore), and the balanced ones are balanced by medium only, so nothing parts the land from itself and
every land law so far has pushed the land's bodies one way (e066's dry air closed them, e071's cold closed
them again).

The answer agreed in #87 is to build the counterweights **together** and search them as a combination. No
law is kept or rejected alone.

## Design

The seven sets, each as a rate whose 0 is e070 exactly (`main.rs`'s header has the laws in full):

- **A. Heat** (`heat`), replacing e071's cold. A body holds heat. Each face of a block open to the cell
  under it passes heat by the difference, a hard face at `heat_hard` (0.25) of that, and the fat stops
  `heat_fat` (0.75) of it when it fills the store; the change is over the body's mass, so a heavy body
  follows the day slowly. Its blocks make heat as they burn their upkeep, enough for it to sit
  `heat_make` x upkeep / its faces over its cell: a closed body runs hot. Under `warm_lo` (15 C) it pays
  energy to warm itself back to the band, over `warm_hi` (30 C) it pays water to cool, and the sweat
  leaves by its open soft faces, so a closed body pays more for every degree. A body that cannot pay the
  warming dies of cold; one whose water runs out dies of thirst.
- **B. Wood as food** (`wood_food`). A gut takes that share of a cell's wood, with the grass and the
  carrion in their proportions, in a body with a hard tip of force `wood_hard` (3, over e060's tooth of 2)
  behind it.
- **C. The fat weighs** (`fat_weight`, `store_gene`). The fat adds mass, which the clock, the work of a
  move and a shove read; and the fat the flesh holds per unit of mass is read from the genome (e069's
  `store` alone, its two other values left constants, as #83's result asked).
- **D. The sea does not quench** (`fresh`). A block drinks all of `drink` over a pool, `fresh` of it over
  ground at full fill, and nothing over the sea, which still gives its breath.
- **E. Light** (`light`). A sensor block's reach follows the light where the body stands: the sun's
  height, less in deep water and under a stand of wood. At `light` 1 a body sees nothing at night.
- **F. Height** (`climb`). A body that moves onto a higher cell pays per unit of mass per metre it rises.
- **G. The runoff carries soil** (`carry`). Water running off a land cell takes a share of its soil into
  the cell it runs to, the sea included. It runs with the bodies: the settled world is the one they start
  from, so the law answers the bodies' pump and not the world's own spin-up.

**The scales, with no runs** (`dryrun.py`, on e070's censuses, c1225's terrain rebuilt as `climate.rs`
builds it, and e063's settled world). Every rate is put where its law starts to bite:

| set | the range searched | what it costs there |
|---|---|---|
| A heat | 0.03-0.3 | the warming takes 0.14-1.4 of the land's upkeep, the cooling 0.2-2.2 of what the dry air takes; a twentieth of that in the water |
| B wood | 0.02-0.5 | the wood offers a fifth to five times the grazed grass (1.3% of the grown bodies have the tooth today) |
| C fat | 0.02-0.3 | a full store weighs a tenth of the body to one and a half times it |
| D fresh | 0.02-0.5 | a block over median ground (fill 0.37) drinks a third to seven times what the body loses to the air; pools are 0.24% of the land |
| E light | 0.1-1.0 | the shade of the wood cuts a cell's light by 1-41%, the sea's depth to 0.35, the night to nothing |
| F climb | 1e-5 to 3e-4 | the median rise between two land cells (11.6 m) costs a tenth to four times a sub-cell of moving |
| G carry | 0.003-0.3 | 150-15,000 of soil moved a 1,000 steps, against the 318,000 the land's soil holds and the 1,700 a 1,000 steps the bodies pump onto it |

The heat's shape constants are set there too: `heat_make` 1000 (the median land body sits 3.4 C over its
cell, a body of 6 open faces 12.3 C), `heat_spend` 0.0035 and `heat_sweat` 0.003. At `heat` 0.1, on a cell
at -5 C an open body of 22 faces pays 1.73 of its upkeep to warm and a closed one of 6 faces 0.22; on a
cell at 45 C the open body pays 1.4 times what the dry air takes and the closed one 2.1. That is the land
parted in two, which no single law of stage C has managed.

## Hypothesis

Written before the runs. The conditions are named together: **a body's axes take two sides when the world
differs by place in more than one thing at once (A) and every side of an axis has somewhere that pays (B).**
Both are what the sets are built for: heat parts the land by band and by hour, fresh water and wood part it
by place, and the light and the height part it by time and by relief.

Against e070's controls read over the same window (seed 9, censuses 30,000-50,000: 3 kinds held at every
census, 3.0 at a census, none keeping 90% of its bodies to one medium; over seeds 9-11, 3, 4 and 3 held):

1. **The world holds more kinds.** At least one combination of the 22 holds more than 3 kinds at every
   census of its second half.
2. **A kind keeps to a place.** At least one combination has a kind held at every census that keeps 90% of
   its grown bodies to one medium (the controls: one of three seeds, and none on seed 9).
3. **The worlds stand.** Every combination keeps bodies in all three media through 50,000 steps.

Decision rule, set before the runs: the set becomes stage C's default if, on the three seeds at 100,000
steps, the kinds held at every census average more than the controls' 3.00 and at least two seeds hold a
kind that keeps to a place. The sets are kept or dropped together, never one by one.

## Method

Code: `experiments/e072_balance`, e070's crate (`senses = 1`) with the seven rates and their shape
constants. Tests: the heat crosses the open faces and the fat stops it; the fat weighs and slows the clock;
a body drinks what the cell gives; a sensor block sees as far as the light; a tooth makes the wood food;
the runoff carries soil downhill and into the sea, and nothing at `carry` 0; matter is conserved with all
seven sets on at once, where each one leaves its mark.

**The check**: with every rate 0 the first 10,000 steps must equal e070's run for seed 9
(`c1225_life9_senses`) in every column of the log but the wall times, in every body of the census at step
10,000, in every lineage row and in every event.

**The search** (`search.py`): a Latin hypercube of 22 combinations over the seven rates (log-uniform in
the ranges above), `store_gene` on throughout, on c1225 with e062's draw d11, seed 9, 50,000 steps each.

    uv run python experiments/e072_balance/search.py 22 50000 9
    xargs -P 11 -L 1 ./target/release/e072_balance < experiments/e072_balance/results/search/candidates.txt

Read with `sweep.py`: kinds by birth form held at every census of the second half and at a census (e068's
`kinds.py`), how many of them keep 90% of their bodies to one medium, what each set cost (the warming over
the upkeep, the cooling against the dry air, the wood's share of the intake, the soil carried), the bodies
by medium, the deaths by cause, and the land's and the sea's matter.

**Then** three seeds at 100,000 steps around the region the search picks, judged against e070's runs on the
same seeds, and the stability check of #88 (a kind halved at step 50,000 and watched for 20,000 steps).

Cost, before the runs: the search is 22 runs of 50,000 steps on 11 local cores, two rounds, about an hour
(a step is 20-24 ms with the sets on against e070's 17 ms, one pass over a body's blocks more for the
heat). The second round is 3 runs of 100,000 steps, about 40 minutes on 3 cores.

## Result

**The checks.** The tests pass. With every rate 0 the first 10,000 steps equal e070's run for seed 9 in all
141 shared log columns, in every body of the census at step 10,000 (9,316), in every lineage row (70) and
in every event (40). Matter drifts by at most 6e-15. The cut run equals the sets run for seed 9 in every log
column up to step 49,000.

**The search** (22 combinations, seed 9, 50,000 steps, 43 minutes on 10 cores a round). Every world stood
(lowest 3,195-11,799 bodies). Against e070 read over the same window (3 kinds held, 3.0 at a census, none
keeping to a medium):

- kinds held at every census: **2-6**; 14 of 22 hold 4 or more, 7 hold 5 or more.
- kinds that keep 90% of their bodies to one medium: **0-4**; 21 of 22 hold at least one.
- The rate that places a kind is the heat (rank correlation +0.68 with the kinds kept to a medium, +0.74
  with the deaths by thirst, -0.78 with the open faces of the land's bodies, -0.79 with the bodies the world
  holds). No rate raises the kinds held on its own; `wood_food` lowers it (-0.34).

The four best (d09 6/4, d16 6/3, d12 6/3, d17 5/4) put round two at their centre: `heat` 0.09,
`wood_food` 0.04, `fat_weight` 0.06, `store_gene` 1, `fresh` 0.05, `light` 0.7, `climb` 6e-5, `carry` 0.03.

**Round two**, c1225, seeds 9-11, 100,000 steps (47 minutes each, four runs at once), against e070's runs on
the same seeds. The second half is steps 50,000-100,000, six censuses.

| | control (e070) | the sets |
|---|---|---|
| kinds held at every census (9 / 10 / 11) | 3 / 3 / 3 | 4 / 3 / 2 |
| kinds at a census | 3.2 / 3.2 / 4.0 | 6.0 / 4.7 / 6.7 |
| the leanest census of the six | 3 / 3 / 3 | 5 / 4 / 6 |
| the same with the medium shuffled | 3.17 | 5.17 |
| kinds keeping 90% of their bodies to one medium | 0 / 0 / 0 | 2 / 2 / 1 |
| the largest kind's share of the grown bodies | 55-65% | 19-32% |
| the largest lineage's share | 72% | 43% |
| bodies: mean (lowest) | 8,290 (6,395) | 9,790 (5,955) |
| bodies on land / at the surface / on the bottom | 2,740 / 2,960 / 2,590 | 5,010 / 1,630 / 3,160 |
| land bodies: open soft faces per block | 0.87 | 0.64 |
| land bodies: hard share; blocks | 3.7%; 26.3 | 11.9%; 32.4 |
| land bodies: the store the genome reads; the tooth | 5.00 (fixed); 3.0% | 6.82; 15% |
| water bodies (surface): open soft faces per block; hard share | 1.23; 0.2% | 1.24; 1.5% |
| deaths: hunger / thirst / broken / suffocation / cold | 70% / 24% / 4.0% / 2.1% / - | 28% / 60% / 4.4% / 5.6% / 2.4% |
| moves blocked; kills' share of intake | 38%; 11.1% | 57%; 10.4% |
| the land's matter over steps 10,000-100,000 | +13-14% (`balance.md`) | +6.5 to +7.3% |
| a step on one core | 17.6 ms | 23.5 ms |

**The land and the water hold different bodies now.** In the controls a land body and a surface body differ
by a third in their open soft faces per block (0.87 against 1.23) and by nothing else that shows. Under the
sets the land's bodies close (0.64), arm (11.9% hard against 3.7%), grow (32.4 blocks against 26.3), read a
larger store from their genome (6.82 against the constant 5.00) and carry a tooth (15% against 3%), while
the surface's bodies are as open as before (1.24) and stay soft (1.5% hard). The open-or-closed axis has two
sides for the first time in stage C, and so do hard-or-soft and the fat.

**The ways of living.** Every seed holds a kind that keeps to the land: a plant eater that stays, closed
(0.44-0.61 open faces per block), 29-45 blocks, on 96-99% land. On seeds 10 and 11 that kind carries a
tooth (hard 28-36%, half to two thirds of its bodies armed) and takes 13-17% of its food from kills: land
predation, which no stage-C run had. The water keeps its own: a plant roamer at the surface (1.25 open faces
per block, 5% of its bodies on land) on seed 11, a stayer on the bottom on seed 9. The shore's roamer, which
held 55-65% of the controls' grown bodies, holds 24% under the sets.

**What each set did.** The heat is paid: the land's bodies spend 6-8% of their upkeep warming and 2.4% of
the deaths are by cold, while a body sits at 26-28 C on cells of 15-18 C (its own upkeep keeps it there; a
closed body keeps more of it). The sea giving no drink makes thirst 60% of the deaths and moves the crowd
onto land (the surface loses 45% of its bodies, the land gains 83%). **Wood is not eaten**: 0.0-0.3% of any
kind's food, so the tooth that appears is for other bodies, not for trees. The runoff halves the pump: the
land gains 6.5-7.3% of its matter over steps 10,000-100,000 where e070 gained 13-14%, and the sea loses 4.3
-5.0% where e070's soil lost 10%. The bodies do not spread into the cold band (5-7% of the land's bodies,
as in the controls): the heat parts land from water, not band from band, as e071's day still swamps the
bands.

**The stability check.** At step 50,000 the largest lineage (5,142 bodies, 46% of the world) lost half its
bodies. The world's bodies went from 11,185 to 9,101 and were back at 11,961 by step 52,000, inside the same
band (9,500-12,600) for the 48,000 steps that follow, with 9-19 lineages alive; the world's own swing is as
wide, so the population alone does not settle it. The lineage itself does: 3,257 bodies before the cut,
2,021 after it, **5,377 by step 54,000** against the uncut run's 3,957, and by step 61,000 it has split into
three lineages of 1,320, 787 and 463 bodies (the parent label ends at step 70,000, its bodies in the
splits). The cut is answered inside 4,000 steps, a fifth of the window #88 allowed.

1. **The world holds more kinds at every census: no.** 4, 3 and 2 held against the controls' 3, 3 and 3,
   both averaging 3.00. The count at a census rises (5.78 against 3.44) and the leanest census of the six
   holds 5, 4 and 6 kinds against 3, 3 and 3, but the kinds held are not the same ones at every census: on
   seed 9 five more kinds sit at 4-5% of the grown bodies, just under e060's 5% line.
2. **A kind keeps to a place: yes.** 2, 2 and 1 kinds keep 90% of their grown bodies to one medium, on all
   three seeds, against none on any control seed.
3. **The worlds stand: yes.** All three ran 100,000 steps at 5,955 bodies or more, matter drifts by 1e-14,
   and the halved lineage is back over its uncut size within 4,000 steps.

## Conclusion

**Not kept as stage C's default by the rule set before the runs**, which asked for more kinds held at every
census *and* a kind that keeps to a place: the second holds on all three seeds, the first does not move
(3.00 against 3.00).

**But the rule's measure is the only one that did not move.** The sets make a world with more kinds at every
census (5, 4 and 6 at its leanest against 3), no kind holding a third of it (19-32% against 55-65%), no
lineage holding two thirds (43% against 72%), a land that keeps its own closed, armed, bigger-chested bodies
against an open soft water, land predation on two seeds of three, and a matter pump halved. What the "held
at every census" measure counts is the *identity* of the kinds over six censuses, and an even world with
nine kinds near the 5% line loses that intersection exactly because it is even. The measure was built (e060,
e068) for worlds where one kind held two thirds.

**What this changes.** The balance table's reading is confirmed where it could be tested: laws built as a
set give the body's axes two sides, which nine experiments of one law at a time did not. The counterweight
that does the work is the heat (it places the kinds) with the sea that does not quench (it fills the land);
wood as food did nothing at this rate, and the runoff's soil is a slow brake on the pump, not a cure.

These answers hold for this world and these choices: c1225, seeds 9-11, 100,000 steps from random genomes,
s = 1/16, e070's laws under them, the seven rates at the centre of the search's four best, a band of 15-30 C
for a body's heat, `wood_hard` 3, a settled world that never ran the runoff's soil, and e068's census with
its 5% line. Not shown: c1236 (a cool world), longer runs, the rates apart, and the invasion test of #72.

**Decided by the user, 2026-09-16: (a) and (b).** The sets are stage C's default world at the rates above,
these three runs are the controls from here, and stage C is judged by the kinds at a census and the kinds
that keep 90% of their bodies to one place; the kinds held at every census stay in the tables as a number,
not as the line, because they count the identity of the kinds over six censuses and an even world loses that
for being even. The next experiment (#89) takes the two counterweights that did nothing here: wood at a rate
a body can live on, and a cold that differs by place - the heat reading each cell's temperature averaged
over a day, as e071 proposed. `vision.md` and `balance.md` section 9 hold the decision.
