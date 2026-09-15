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

To come.

## Conclusion

To come.
