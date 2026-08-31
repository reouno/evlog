# e021 The tall plant takes the light

Date: 2026-09-01

## Purpose

e013 to e020 end the same way: one kind of body, a bar of 6-10 gut cells, wins every run, and
lineages alive stay at 1-2. e020's rain graded that one winner by height (mass at birth rises
valley to ridge) but did not split it: a place law of amounts is not enough. The last world with
several winners at once was e011 (tortoises, hunters, corner bodies; teeth paid ten to one),
and its premise was a cell that holds more than one bite: the crowd around a rich cell is what
made size, armor and teeth worth their cost. A closed world has had no way to such a cell: no
cell grows faster than the sun (0.01 per step, half a bite), so every place is a thin lawn and
the best body is the smallest bar that reaches wet ground. The bites stand 400 to a full cell
(cap 8, bite 0.02), but nothing ever fills.

The real world's way from thin sunlight to a concentrated meal is the tree: a plant that is not
eaten grows tall and takes the light of its neighbors, and the forest gathers hectares of sun
into trunks and fruit. This experiment writes that as a law of the world: the matter standing
on a cell is a column, and a taller column takes its neighbors' light. A cell that escapes
grazing rises above the grazed lawn around it, draws the sun of up to four neighbors, and
stands as a store of up to hundreds of bites; a grazed cell under tall neighbors grows in the
dark. The sun is only moved, never made; the law names no trait, reads no body, and costs one
pass over the cells per step. If it works, the world gets its first rich cells since e011 - and
with them, perhaps, a reason for bodies to crowd, and for crowds to be worth biting into.

Alongside it one piece of geography: the terrain's mean height is normalized to half the relief
(e020's seeds spread 73-94 in income because the rain caps sum to 164 times the seed's mean
height over relief, 0.44-0.56; normalized, every seed's caps sum to 81.9). This is generation,
not a law: the shape of each seed's terrain is unchanged.

## Hypothesis

1. **Trees stand.** Cells holding at least 1.0 of matter (50 bites; the grazed lawn stands at
   0.03-0.05) persist through the second half of every run - tens to hundreds of them per
   world (e020: none after the start's stock is eaten) - and some reach the cap. They stand
   where soil meets few bodies: in the mountain-rain world, on the valley floors and rivers,
   where 10-29% of the sun fell on empty or unlit ground in e020.
2. **The trees are eaten.** Intake from tree cells (`tree_eaten`) is at least 5% of the world's
   intake in the mountain-rain world: the trees are not a dead store but a harvest, and the
   world eats within 15% of e020's income (the normalized caps sum to 81.9 per step).
3. **A crowd forms at the trees.** Contacts per body per step rise above e020's 0.009-0.042
   somewhere in every run, and the neighbors-per-body distribution grows a tail (bodies
   waiting at a tree the way e011's crowds shared a rich cell).
4. **A second kind of body lives on the trees.** By #19: in at least two seeds of four, a
   lineage whose intake is mostly from tree cells coexists with the lawn bar for over 100,000
   steps, with a different body (larger, or toothed - `biters_share` > 0.01 would be the first
   tooth since e012). This is the hypothesis the law is for; it failed in every world since
   e013.
5. **The world stands.** No extinction, population cv under 0.10 over the second half, matter
   conserved to 0.05%, in all twelve runs. The canopy moves sun, it does not destroy it; a
   world of trees can starve the lawn locally but the trees themselves are food.
6. **The rate is not a dial.** Doubling the shade rate (pilot only) changes how sharp the
   canopy is, not what kind of world forms (as e019's flow rate and e020's relief stopped
   mattering).

## Method

Code: e020 (`experiments/e020_rain`) with the canopy added and the terrain normalized:

- `Food::shade`, once per step between the rain and the regrowth: a column of standing matter
  (`res`, the plant plus what lies dead on it) claims, from every cell within Chebyshev
  distance `d` of it, `shade * (res[t] - res[n] - (d - 1)) / cap * (cap - res[t]) / cap` of
  that cell's sun - the slanting sun (the shadow weakens by one cap-worth per cell walked and
  reaches at most the cap, 8, in cells) times the column's own room over the cap (saturation:
  a full crown intercepts nothing, a tree bitten deep pulls hardest, and a column never
  gathers much more light than it can grow by). A column under a body claims nothing (the
  plant neither grows nor gathers there, e016), though its own sun, already dark, can be
  claimed. Claims on a cell past its whole sun share it in proportion. All columns shade at
  once from the state at the start of the step, and the moved light lands in the taker's
  regrowth budget. The sun is conserved: what the canopy takes, the canopy gets, and a bitten
  tree refills at up to tens of suns while the lawn around it grows in the dark.

  The law took three pilots (seed 9, 100,000 steps, four runs each: the three worlds and
  `high` at a doubled rate; the files were not kept) to find this form, and each wrong form
  taught something:
  1. Stopping the shadow at the four neighbors (a share per neighbor of the difference over
     the cap) cannot reach the premise: a full tree gathers at most five suns, 0.05 per step,
     less than one winning body's upkeep (0.048), so no cell can hold a crowd. Trees were
     7-27 cells, their harvest 0.2-0.5% of the intake, and doubling the rate doubled
     everything - the truncation, not the rate, was the wall.
  2. The full slant without saturation kills every world in 700-3,200 steps. The run starts
     with every cell at the cap; the first bite makes a hollow that every full column around
     it shades, and a column at the cap throws what it takes away (no room to grow), so
     nothing regrows anywhere: the world eats its stock and starves. Light hoarded by a
     column that cannot use it is not a canopy but a blight; interception must saturate.
  3. With saturation the world stands (cv 0.007-0.031, no extinction) and the rate has a
     threshold, not a slope: at rate 1 the trees lose the race against the grazing (8-12
     standing, harvest 0.3%, no larder full), at rate 2 they win it (204 standing, 116 on the
     ridges, harvest 6.4%, larders at the cap, mass rising valley 7.6 to ridge 8.7, contacts
     0.06). Saturation halves the slant's strength; rate 2 restores it. The default is 2.
- `Terrain::new` scales the heights so their mean is half the relief (the peaks may stand
  above the relief; bands, being ranks, are unchanged).

One new argument, `shade` (the rate of the canopy law; 2 by default, 0 is e020). New columns:
`shade` (sun moved per step), `trees` (cells at 1.0 or more), `tree_res` (matter standing in
them), `res_max`, `tree_eaten` (intake from cells at 1.0 or more at the bite); `trees` per
place in `places.csv`; the shade rate in `terrain.json`. Everything else is e020 (uniform sun,
relief 64, flow 0.1, breath to the air with rain by height as the kept law, matter 8 per cell
at the start, a cell of 0.02).

Worlds, twelve 1,000,000-step runs at 128x128, seeds 1-4, local, one thread each: rain on the
mountains (`high`, the kept law), half the breath (`high 0.5`, the richest world, whose places
the rain erased - does the canopy differentiate it?), and rain everywhere alike (`flat`, the
uniform lawn with the terrain moot - do trees rise from an undifferentiated world?). The
control at shade 0 is e020's twelve runs (`../e020_rain/results/`), read as ranges (the
normalization rescales each seed's heights, so seeds do not match one to one).

    cargo run --release -p e021_canopy -- <steps> <seed> <size> <widths> [cell_energy] [matter] [relief] [flow] [rain] [breath] [shade]
    bash experiments/e021_canopy/run.sh 1 2 3 4
    uv run python experiments/e021_canopy/report.py

## Result

All numbers are medians over the second half unless said otherwise; ranges are over the four
seeds of a world (`high`: the breath in the air, the rain by height; `high-b0.5`: half of it;
`flat`: rain everywhere alike; all at shade 2). The report (`report.html`) has the charts, the
maps, the bodies and the viewer.

- **Trees stand in every run, and the world has two states.** Every run keeps cells at 1.0 or
  more through the whole run, and the tallest cell reaches the cap in 8 runs of 12; but the
  count is bimodal. Most runs hold a sparse orchard: 6-24 trees, 0.2-0.8% of the intake. Three
  runs live in a forest: high seed 3 holds 165-1,405 tree cells over the run (a boom - 1,405
  at step 400,000 grazed down to 165 by 600,000 - then a steady 200-250), flat seed 3 holds
  217-458, and half seed 3 flips late, 4-10 trees until step 800,000 and 300-477 after; high
  seed 2 touches 172 at 700,000 and falls back. The forest is a state the world enters and
  leaves, the first bistability of the series. Where: in the mountain worlds the trees stand
  where the rain is, ridges and slopes (high seed 3 at the end: 37 / 94 / 125 by band), not
  the valleys as guessed; on the flat lawn they stand on the lake (44 / 39 / 2).
- **The trees are a harvest only in the forest.** Intake from tree cells is 5.47 and 7.40 per
  step - 6.5% of the intake - in the two full-run forests (guessed at least 5% everywhere),
  0.2-0.8% in the orchard runs. And the canopy pays the world: the flat worlds eat 105.4-112.9
  per step against e020's 100.4-103.3, because a tree overtopping a grazed or held cell takes
  light that would have been shaded or gone begging - the bodies' own shadow falls from 36-38%
  of the sun to 29-35%. The forest seed eats 112.9, the most of any closed world so far. The
  high worlds eat 83.2-83.8: the normalization works (e020: 72.8-94.3 with the seed's terrain),
  and the canopy holds the income while moving 5-18 of sun per step between cells.
- **A crowd only in the forest.** Contacts per body per step are 0.008-0.093: the orchard runs
  sit inside e020's 0.009-0.042, the forests above it (high seed 3: 0.093, twice e020's
  ceiling; flat seed 3: 0.042; half seed 3 after the flip: 0.027 from 0.014).
- **No new kind of body, but the deepest coexistence since e012.** No tooth anywhere (biters
  0.000 in all twelve; hard 0.0-0.2), every winner a gut bar, mass still rising with height in
  all four high seeds (7.0-7.8 valleys to 7.3-8.4 ridges at the end). But lineages alive reach
  3 (median) in high seeds 1 and 3 and 5 in half seed 4 (e020: 1-2), and the coexistences are
  long: flat seed 3 holds two lineages for 921,000 steps (mass 9.1 against 7.6); high seed 3
  holds three, the third (lineage 81, 395,000 steps) the heaviest winner of the series at mass
  10.3, standing highest (39.5) where the forest is; half seed 4 turns over four long-lived
  lineages of two different bar shapes (2.2 x 7.7 and 3.0 x 4.3).
- **The world stands in all twelve runs.** Population cv 0.007-0.028, food eaten last quarter
  over third 0.990-1.011, no extinction. Matter holds to 0.01% in the orchard runs and
  0.04-0.08% in the forests (the plants are f32, and rounding grows with the standing heights).
- 178-212 steps per second with twelve runs on the machine (e020: 429-492): the canopy pass
  costs about half the speed, the price of every column checking its reach.

## Conclusion

1. Trees stand: yes, in every run - but "tens to hundreds" is really two states, orchard and
   forest, chosen by seed and epoch. The forest is a boom the grazers mow back; twice it
   arrived after step 700,000, so a million steps reads the orchard runs only as "not yet".
2. The trees are eaten: only the forest reaches the 5% asked (6.5%). The surprise is the
   income: the canopy raises what the closed world eats (flat +3-10%) by taking the light
   that the bodies' own standing shadow was wasting. A law written to concentrate food also
   made more of it.
3. A crowd forms: no as stated - only the forest runs push contacts above e020's ceiling, to
   0.093 at most. A crowd needs the forest, and the forest is episodic.
4. A second kind of body: no. No tooth, no majority-tree lineage; the coexistences are longer
   than anything since e012 (921,000 steps) and the heaviest winners yet stand where the
   trees are, but they are all still gut bars sorted by size and height - kin of the winner,
   not another kind.
5. The world stands: yes, twelve of twelve, and the law's two failed forms (the report's
   Method) mark the boundaries: reach without saturation is a blight; saturation without
   reach is marginal.
6. The rate is a threshold, not a dial (by the pilot): at 1 the trees lose the race against
   the grazing, at 2 they win it.

What it changes: the canopy (slant, reach, saturation, at rate 2) is kept as a law of the
world - it gives the closed world standing stores of food, a second state, its first income
above the lawn's, and the longest coexistence in nine experiments, at the price of half the
speed. What it did not give is the crowd that pays for teeth, and the reason is visible in the
law itself: a body eating a tree stands on it, and a held cell neither grows nor claims, so a
tree is eaten in gulps and the forest feeds nobody while it is being eaten. The next law on
this axis is the spill (vision, next step 2): let a full crown keep catching the light it
stands in and drop what it cannot hold as fruit on the cells around it - pilot 2's fatal
hoarding turned into food on the forest floor. Then a tree becomes a place where a crowd eats
without silencing the tree, which is e011's rich cell, closed.
