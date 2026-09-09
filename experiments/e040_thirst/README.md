# e040 A body that needs water

Date: 2026-09-09

## Purpose

Since e035 the world has water: it pools in the valley and the ridge is dry, and the plants
live on it (a plant grows under its sun times min(1, water / WET)). The bodies do not: a body
lives wherever its food is, and the only reason it has ever had to change place is the winter
(e032: the valley is the refuge, the migration a wave). This experiment gives the body the
animal's second need (#37): it must drink, and water stands in one place. The question is
whether the bodies move between the wet valley and the dry ridge for a reason other than food,
and whether that gives the ridge's summer bodies a route back down.

Read it as a law about the body's material (a body loses water as it burns, and takes it where
it stands), not a trait: what the policy can learn is when to go, not whether it needs to.

## Hypothesis

1. **Trips.** With a thirst the ridge is a place visited from the water, so the ridge's bodies
   in summer are born in the valley (`cross2`, the ridge's bodies born in another band, above
   the control's 24-38%), the bodies' fill is lowest on the ridge and highest in the valley,
   the deaths by thirst are few after the start (the policy reads the thirst and the pools),
   and the valley holds more of the summer bodies than in the control (46-49% at 100,000 steps).
2. **Or the ridge empties.** A body cannot learn the trip (the pools are 20-40 cells from the
   ridge, a body moves a quarter of a cell a step), so the ridge's summer bodies die of thirst
   and the world lives in the valley and on the slope's pools: the ridge's share falls toward
   0, the deaths by thirst stay high, and the world is smaller (fewer cells fed on).

## Method

Code: e039 (`experiments/e039_reach`) as `e040_thirst` with one argument more, off by default
(`thirst` 0 is e039 at `reach` 0 byte for byte, that is e035's world; checked on seed 9 for
10,000 steps).

- **The fill** (argument 36, `thirst`). A body holds water as its fill, 1 full, 0 dry. It
  dries by `thirst` a step, whatever it does. On a cell whose water stands above WET (100, what
  the sky gives a cell alone; what stands above it came down from higher cells and is a pool)
  it fills by DRINK (0.1) times the pool's depth in units of WET, at most 1, a step: a body on
  the valley's median cell (137) fills by 0.037 a step, from dry to full in 27 steps. The water
  is not consumed (the field is not matter; a plant does not consume it either). A body whose
  fill reaches 0 dies (`deaths_thirst`), as one whose energy and fat are gone does. A child is
  born with its mother's fill.
- **Why a pool and not the wetness.** The plants live on the wetness and the ridge is at
  0.5-0.7 of it, so a body that drank the wetness would drink anywhere and the law would do
  nothing. Standing water is what came down from above: in e035's runs three cells of four in
  the valley hold it, one in five on the slope, one in twenty-five on the ridge.
- **The eye sees water.** The body's policy gets five more inputs: the pools seen ahead,
  behind, left and right (as the food is seen, #26: as far as the eye's range, what lies j
  cells away at 1/j) and its own thirst (1 - fill). Their weights are one more column of the
  law table from its own stream (as the density, the digestion axis, the side and the breed
  output are), so every body of e039 is the same body here, and the column is read only when
  the law is on.

**Runs.** Seed 9, 100,000 steps (five winters), one thread each, three at once on the Mac, in
e039's season world (`winter high` 2, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, rain
flat, store 5, grow, no ground store, k 1, sun 1, reach 0): `thirst` 0.001 (a full body lasts
1,000 steps, a third of the longest life), 0.002 (500 steps) and 0.005 (200 steps), against the
control at `thirst` 0 (e037's pilot on this seed, byte for byte through e038 `sun` 1 and e039
`reach` 0). A batch on seeds 1-3 at 300,000 steps only if the pilot shows trips.

Run from the repo root: `bash experiments/e040_thirst/run.sh <thirst> <threads> <steps> <seeds>`.

**Measures.** Per height band and through the season (`pop.csv`): the bodies standing there,
the ones born in another band (`cross0..2`), their mean fill (`fill0..2`) and the ones standing
on a pool (`drink0..2`). In the log: `deaths_thirst`, `fill_mean`, `drinking` (the share of
body-steps on a pool), `pool` (the share of cells holding standing water), the winter floors,
the bodies, what the world eats, `sense_used` (whether the eye decides more), the winners'
shapes (`lineages.csv`, `bodies.jsonl`) and the diversity number (#42, e039's `diversity()`).

**Compute.** The eye looks at the pools as it looks at the food: one more `look` per direction
per cell of range, about a tenth more per step.

## Result

**The pilot.** Seed 9, 100,000 steps, three doses at once, 10-11 minutes a run (148-173 steps a
second; the control 118). Means over the second half (steps 50,000-100,000); the places in the
summer half of each season (the sun above its mean), the lineages those alive at the end; the floors are the five winter troughs in order.

| run | winter floors | bodies | eaten a step | valley / slope / ridge | ridge born elsewhere | fill valley / slope / ridge | on a pool, valley / slope / ridge | deaths dry a step | deaths hungry | eye decides | a gut block earns | size p50 | lineages | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| thirst 0 (control) | 626, 696, 724, 743, 775 | 3,674 | 116 | 39 / 35 / 26% | 18% | - | - | - | 8.87 | 26% | 0.0026 | 9 | 2 | 2 |
| thirst 0.001 | 705, 659, 621, 628, 647 | 2,644 | 123 | 41 / 35 / 24% | 19% | 0.87 / 0.58 / 0.40 | 77 / 28 / 5% | 1.66 | 5.64 | 22% | 0.0031 | 15 | 6 | 2 |
| thirst 0.002 | 498, 572, 651, 596, 670 | 2,459 | 125 | 43 / 35 / 22% | 16% | 0.87 / 0.55 / 0.31 | 80 / 33 / 4% | 3.90 | 5.40 | 19% | 0.0029 | 12 | 4 | 2 |
| thirst 0.005 | 259, 232, 307, 285, 374 | 1,065 | 87 | 56 / 30 / 14% | 15% | 0.88 / 0.56 / 0.37 | 86 / 41 / 12% | 3.78 | 1.48 | 16% | 0.0027 | 26 | 5 | 2 |

The cells holding a pool (water above WET) are 33% of the world: 76% of the valley's, 19% of the
slope's, 4% of the ridge's (e035, and `pool` here, 0.329 in every run).

**No trips.** The ridge's bodies born in another band are 15-19% in summer against the control's
18%, and the time course keeps the control's rhythm at every dose: 15-19% in each summer window,
31-45% in each winter (the winter's wave, e032), with no drift from step 10,000 to 100,000. The
fill on the ridge is 0.31-0.40 and flat; a body that walked down when thirsty would raise it.
The moves that differ from what the same body would do blind (`sense_used`) fall from 26% to 22,
19 and 16%: the five new inputs are read as noise, and selection did not make them a signal.

**The ridge does not empty either.** It holds 24, 22 and 14% of the summer's bodies (control
26%). Bodies on the ridge stand on a pool 5-12% of the time, one to three times what its 4% of
pool cells gives by chance (the slope: 28-41% against 19%); the ridge's lineages live on those
cells and the bodies around them die dry.

**The law kills.** Deaths by thirst are 1.66, 3.90 and 3.78 a step, 23, 42 and 72% of all
deaths; they follow the summer's crowd (6-9 a step at the peaks, 0.5-2 in winter) and take the
bodies that hunger would have taken later (deaths by hunger 8.87 to 5.64, 5.40 and 1.48). The
world loses 28, 33 and 71% of its bodies; at 0.005 it eats 25% less and the valley holds 56% of
the summer's bodies. A gut block earns the same 0.0027-0.0031 a step, and the thinned crowd grows
bigger bodies (median 15, 12 and 26 cells against 9), e038's rule read backwards.

**The winners.** At every dose the top lineage is a gut with no muscle: 11-12 cells of which
10-11 gut at 0.001 and 0.002 (57% and 42% of the body-steps of the last third), 20-24 cells of
which 17-20 gut with 1-2 sensors at 0.005 (45%). The control's winner is the same sitter (ten
gut, 53%). The movers (27 cells, nine muscle, 39% flesh at 0.002) peak and are gone by step
72,000. Diversity (#42) is 2 in every run.

**No batch.** The rule set above was a batch on seeds 1-3 only if the pilot shows trips. It
shows none, at three doses, steady over five winters, so the batch (three runs of 300,000 steps,
about 75 minutes) was not run.

## Conclusion

**Not kept** (`thirst` stays an argument, 0 by default). Hypothesis 1 is answered no: the body
does not learn the trip, and the eye decides less under the law, not more. Hypothesis 2 is half
right: the bodies off the water die dry, but the ridge does not empty, because e035's water
leaves one ridge cell in twenty-five above WET and that is enough for a sitting lineage.

The world's answer to a need for water is the answer it gives to every need: sit where the food
and the water are. A sitter on a valley pool never dries; a sitter on the ridge dies and is
replaced by a child born there; a walker pays the move and gains nothing a sitter lacks. The law
selects places, not trips, and the map of where a body can live already agrees with the food's
(the valley, then the slope).

What this changes:

- **For #37.** Drinking is not a reason to move in this world. A trip needs a body that has to
  move for its food (a grazer that empties a place, or a hunter that follows prey) before a
  second need can shape its route; here a gut sits on a cell that regrows under it.
- **For the places.** The pools are a second map of the world, and the pilot shows it reads:
  the fill is 0.87 / 0.56 / 0.36 by band in every run, and bodies stand on pools above chance
  on the slope and the ridge. A place law that wants the ridge to be a destination must first
  make the ridge worth something the valley is not (#38: its soil).
- **Open.** One seed and 100,000 steps; whether selection would make the water inputs a signal
  over 300,000 steps is not tested, but the sign at 100,000 is down. A ridge with no pool at all
  is a different world (a stronger `water` rate, or a pool threshold above WET) and would be
  emptied by the law, not visited.

Next: #38, the rain on the ridge under e035's carrier.
