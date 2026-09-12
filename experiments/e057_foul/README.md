# e057 A worsening that falls on the one who stays (fouling)

Date: 2026-09-12

## Purpose

Issue #56. Animals foul the ground they stay on: dung and waste pile up where a herd rests and
parasites gather where a crowd stays, so a camp is left before its food runs out. Our world has
no such thing. Two findings ask for it.

- **The crowd binds** (e056, #65). The world is jammed: 56% of forward moves are blocked and 30%
  of births are denied for want of room. Extra sun buys more bodies, not bigger ones, so the way
  out is not a richer world but a thinner crowd, or a world whose places differ.
- **Leaving never pays** (e041 `stock`, e051, e054). Every law that made a grazed cell come back
  slowly lowered every grazed cell alike - a commons, a tax that moves nothing. e054 laid the
  food in patches and the bodies travelled *less*: what makes a body cross is the size of a good
  place against a life's grazing, not the spacing of places against a life's walk.

Fouling is a way to make a place small in that sense without touching the soil budget, because
what it takes away it takes away **where the bodies are**: the ground the crowd has trampled is
poor, the ground it has not is rich, and the loss shrinks by itself as the crowd thins.

**Why it must fall on the growth and not on the bite.** A cell is eaten down to what it grows
(e054: the world stands at its regrowth limit, 46 a step eaten against 45 grown). Under a bite
limited by what stands, a multiplier on the take is void: the plant the gut leaves standing is
there next step, the cell builds up until the smaller share of a bigger stock is the regrowth
again, and the long-run intake is unchanged. The growth is the only channel that moves a body's
income. That is also why this is not e041's `stock` again: `stock` divided the growth of every
grazed cell in the world, fouling divides the growth of the cells the crowd is standing on.

## The law

One law about the ground, off by default, none about the bodies.

- Every world cell holds `foul[c]`, waste, a field of the world and not matter (like the water,
  e035: nothing is taken from the ledger to make it).
- A body lying on a cell lays `foul` (argument 49) of waste a step for a whole cell covered, and
  the part of a cell it covers in proportion (the world counts the sub-cells a body holds).
- The waste rots away by FOUL_ROT = 0.01 a step, the dead matter's rate.
- What a cell holds divides the light it can use: the growth is multiplied by 1 / (1 + foul[c]),
  and the light lost is lost (`fouled` in the log), as the dry cell's and the bare cell's are.

**The time constant, written down before the runs** (the issue asks for it). A cell a body
covers settles at `foul` / FOUL_ROT, reached with a time constant of 100 steps; at 1 it grows at
half the rate. A cell the crowd leaves is half clean in 69 steps and clean in a few hundred. A
body lives 200-400 steps. So a spot worsens, and a spot recovers, within a life - not slower
(e041's tax that moved nothing) and not faster than a body can act on it.

## Hypothesis

Written before the runs.

1. **The crowd thins and lets go of the ground.** Under fouling the share of the world's cells a
   body covers falls, and with it the blocked moves (56% in e056) and the denied births (30%).
2. **The ground stops being uniform.** e054 found the food "eaten to its regrowth limit but
   perfectly uniform". The standing plant's spread from cell to cell (`plant_std`) rises: the
   trampled ground is poor and the ground the crowd has left alone is rich.
3. **Leaving pays.** A body travels further in its life (`travel` in `agents.csv`) and the food
   on the cells its guts leave (`gud_rest`) rises: it gives up on a spot sooner.
4. **Predation.** With room in the world, the hunter state (e045: 4 of 6 seeds) is at least as
   common and the kills' share of the intake does not fall.
5. **The world stands**: every winter floor above 50 bodies, and the world's food not halved
   (e046's yield law everywhere cost half the world; this one must not, because it only takes
   from cells the crowd is on).

**What we expect.** (1) and (2) yes: the law is density-dependent by construction, and it is
self-limiting - fewer bodies, less waste, more food. (3) is the real question, and the honest
prior is no: e049, e050, e051 and e054 all failed to make a body walk, and a crowd that is 56%
blocked may thin its way out of the pressure by dying instead of by moving. (4) is a watch, not
a prediction.

## Method

Code: e056 (`experiments/e056_sun`, which is e055 byte for byte with `clock` 0.5 as the default)
as `e057_foul`, plus the law above. With `foul` 0 the crate is e056 byte for byte, which the
first pilot checks against e056's own seed 9.

**Runs.** From the repo root: `bash experiments/e057_foul/run.sh <foul> <threads> <steps> <seeds>`.

| run | foul | seeds, steps | question |
|---|---|---|---|
| pilots, 4 cores | 0, 0.003, 0.01, 0.03 | 9, 20,000 | does `foul` 0 reproduce e056; does the waste build to a level that moves anything; does the world stand |
| batch, 6 cores | 0.03 | 9-14, 100,000 | (1)-(5) |

**The pilot** (done first). `foul` 0 reproduced e056's seed 9 number for number (3,067 bodies,
regrowth 41.69, 53.4% blocked, 442,346 of plant eaten), so the law off is the old world. The
waste built as the arithmetic said it would and the level sorted the world:

| foul | waste per cell | on a free cell | cells a body is on | light lost a step | standing plant | stays put |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 54.4% | 0 | 1.75 | 15.9% |
| 0.003 | 0.08 | 0.04 | 53.0% | 1.2 | 1.34 | 10.0% |
| 0.01 | 0.26 | 0.13 | 50.5% | 3.7 | 1.43 | 8.1% |
| 0.03 | 0.46 | 0.22 | 38.9% | 7.7 | 2.83 | 6.9% |

A free cell carries about half the waste of the world's mean at every level, so the ground the
crowd is on really is worse than the ground it is not - the contrast is there, and the level
decides how much it is worth. **0.03 is the batch's level**: it is where the share of the world
under a body moves at all (-29%), where the p90 cell stands at 1.25 of waste (44% of its growth)
and where the standing plant rises by half. It costs the world 14% of its light, which e046's
flat cut (a yield law everywhere, the world at half) says is the size we can afford. The control
is e055's own batch of seeds 9-14 - the same code with the law off - so the batch is six runs.

**The control runs are not made twice.** `foul` 0 is e056 is e055, and the pilot checked it, so
the control is `experiments/e055_span/results` (seeds 9-14, 100,000 steps).

**Measures** (over the second half). New in the log: `covered` (the share of the world's cells a
body is on), `foul_mean`, `foul_p90` and `foul_free` (the waste on a cell: all cells, the p90,
and the cells no body is on - the ground the crowd comes back to), `fouled` (the light lost to
the waste a step) and `plant_std` (the spread of the standing plant from cell to cell). Already
there: `blocked` and `births_no_room`; `travel` and `drift` per body (`agents.csv`); `gud_rest`
and `left_rest` (e051's giving-up density); the kills' share and the world state (e045); the
bodies, the winter floors, the regrowth and the intake; mass and size p90; diversity (#42).

**Judged state by state and over six seeds**, as e055 asks: the hunter/grazer state moves the
body measures more than a law does, so pairs are compared within a state.

**Compute.** One multiply and one add per cell per step, on a loop the world already runs: under
1% of the step. The pilots cost 4 cores for 4 minutes on the Mac; the batch 6 runs of 100,000
steps at once, about half an hour.

## Result

`report.html` has the charts. Means over the second half (steps 50,000-100,000), six seeds.

| measure | no fouling | fouling 0.03 | change |
|---|---|---|---|
| cells with a body on them | 56.1% | 50.1% | -10.6% |
| births refused for want of room | 31.0% | 25.8% | -16.8% |
| forward moves blocked | 60.2% | 56.2% | -6.6% |
| spread of the standing plant, cell to cell | 2.63 | 2.59 | -1.5% |
| waste on a cell (mean / p90 / where no body lies) | 0 | 0.69 / 1.71 / 0.32 | - |
| light lost to the waste, a step | 0 | 14.8 | - |
| plant grown, a step | 65.7 | 57.5 | -12.5% |
| bodies | 2,677 | 2,352 | -12.1% |
| intake per gut block, a step | 0.0019 | 0.0018 | -5.4% |
| travel in a life (world cells) | 3.09 | 2.52 | -18.3% |
| kills' share of the intake | 22.4% | 17.8% | -20.5% |
| lowest winter floor | 524-838 | 398-582 | -24.3% |
| mean age | 795 | 994 | +25.0% |
| diversity (#42) | 1.5 | 1.7 | - |

**Per hypothesis.**

1. **The crowd lets go of the ground: yes.** Cells under a body 56% -> 50%, births refused
   31% -> 26%, blocked moves 60% -> 56%; in five of six seeds each.
2. **The ground stops being uniform: no.** The standing plant's spread is 2.63 without the law
   and 2.59 with it, although the waste's own p90 (1.71) is five times what a free cell holds
   (0.32). The unevenness is in the waste and never reaches the plant.
3. **Leaving pays: no.** Travel falls 3.09 -> 2.52 cells a life. Three seeds changed world
   state (9 and 12 hunter -> grazer, 14 grazer -> hunter) and hunters travel further, which is
   the whole of the fall: in the three seeds whose state held, travel moves +2%, +3% and +13%.
   The travel-by-age curve is at or below the control's in every age bin.
4. **Predation holds: yes.** In those same three seeds the kills' share rises: 23->26%, 8->8%,
   30->32%.
5. **The world stands: yes.** Floors 398-582, no run died, every floor far above 50.

**The arithmetic of the loss.** The waste takes 14.8 of the light a step; the thinner crowd
hands 5.2 of it back by shading fewer cells (44.8 -> 39.6), so the plant grown falls 8.2 a step
(-12.5%). The bodies fall 12.1%, and a gut block still takes 0.0018 a step. The crowd thinned
to exactly the food that was removed and each mouth earns what it did before - e038's pinned
income from the other side (e038: more sun, more bodies, same income).

**The control was run twice.** `foul` 0 on seeds 9-14 reproduces e055's kept batch column for
column over all six runs; only `steps_per_sec` differs. It was run here anyway so that the
columns this experiment added (`covered`, `plant_std`, the waste) exist for both arms.

## Conclusion

**Not kept.** The season world keeps `foul` 0.

The mechanism worked exactly as designed - the waste builds where the crowd lies, is five times
heavier there than on free ground, and rots inside a life - and it still changed nothing that
matters. What fails is the link from the ground to a body. A cell under a body does not grow at
all (e016), the crowd covers half the world, and grazing follows growth so closely that the
plant left standing is the same on fouled and clean ground alike. Good ground and bad are never
more than a cell or two apart, which is inside a body's own range, so there is nothing for it to
walk to.

**What this changes for the project.** Four laws have now tried to make leaving pay (e041 #43,
e049 #14, e051 #54, e057 #56) and all four were answered in births rather than in steps. The
rule to carry: *a law that differs by place must differ over more ground than a body covers in a
life, or the crowd averages it away.* e054 measured a body's whole life's travel at 2.5-6.8
cells; a law whose good and bad ground alternate at that scale is a flat tax with extra steps.
The room that fouling did buy (a tenth of the ground, a sixth of the refused births) was bought
with an eighth of the world's food, which is the same trade a weaker sun offers.

**Conditions.** This holds under our world: 128x128, uniform sun, the canopy with `sat` 1 and
`hold` 1, `clock` 0.5, bodies whose range is a few cells and whose lineages move by birth. A
world where a body could travel far in a life, or where a cell under a body still grew, might
answer differently.

**Next:** #58, the brain in a world where the food runs out under the body - whether a body that
can learn reads a worsening that its reflexes cannot. The open question this experiment leaves
for it: under fouling a body's own cell really does get worse while it stays, so the signal #58
needs is present in this world for the first time.
