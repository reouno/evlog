# e020 The breath rises and the rain falls on the mountains

Date: 2026-08-31

## Purpose

e019 made the closed world stand: soil runs downhill and pools level, so every wet cell grows at
the sun's rate and the food supply stops falling. But it left the world with one place. At the
end of e019's runs 97% of the matter lies idle in the soil of the lake (19-25 per cell; the sun
draws 0.01 of it per step), the plants on the lake are grazed to the ground (0.03-0.05 per
cell), the ridges hold no soil, no plant and no body, and the same bar of gut cells wins every
run. The ridges are a desert because matter reaches a cell only through the soil, and soil runs
off the high ground. Nothing a body can find is up there, so no law about the high ground (cold,
slope, the plants there) can act yet: the first law of #14 has to give the high ground an income
that does not come from the soil.

The real world has one: what a body burns leaves it as breath, not as dung; the air is
everywhere; and the rain falls on the mountains and runs back down. e018 and e019 sent
everything a body spends to the soil under it. This experiment sends what a body burns (its
upkeep and the work of its moving) to the air, one pool for the whole world, and lets the air
rain on the ground: on every cell at most the sun's worth per step (0.01) times the cell's
height over the relief, so that the peaks get the sun's rate and the lake floor almost nothing;
what the air holds beyond what can fall stays in the air. Rain lands in the soil of the cell,
where the sun draws it into the plant or the flow carries it downhill. The dead still lie where
they fell. A control lets the same air rain on every cell alike (`flat`); e019 is the reference
(`soil`: nothing goes to the air). It is a law about the world (the air, the rain, the
mountains), not about a body; it costs one f64 and one pass over the cells per step.

Two things this could give. The high ground gets a pasture of its own, thinner than the lake
(the rain at a cell is at most the sun and usually less), so bodies live at every height and a
body that lives on thin, spread food may not be the body that wins the lake. And the world's
idle store moves from the lake's soil to the air: the lake drains through the bodies into the
air and comes back as rain on the peaks, and runs down the slopes as soil, so the matter
circulates through the whole terrain instead of pooling in one place. What it cannot give: a
rich cell. No cell grows faster than the sun, so the crowd of e011 has no place to form here
either; this law is the prerequisite for the laws that need life on the high ground, and #14 is
judged by whether the bodies at different heights differ, not yet by whether contact returns.

## Hypothesis

1. **The high ground lives.** With rain on the mountains at relief 64 the ridges (the highest
   third of the cells) hold 400-700 bodies at the end (e019: 0-14) and eat 25-35 per step
   (e019: 0.4); the slopes 20-30 and the valleys 15-25, so that the food eaten falls with
   height the way the rain does, and bodies stand at every height (the soil under bodies is
   no longer 1.6-2 times the soil elsewhere).
2. **The store moves to the air.** The lake's soil drains: the soil holds under 40,000 of the
   world's 139,700 by step 200,000 (e019: 135,000 at the end), the air holds 60,000-100,000,
   and the rain falls at its cap (the air never empties) over the second half. Matter is
   conserved to 0.01% (the soil and the air are f64).
3. **The world stands, with the air as its store.** Food eaten and population steady over the
   second half (quarter medians within 10%, coefficient of variation under 0.10), no
   extinction, in all four seeds; the world eats 75-95 per step (e019 at relief 64: 56-71;
   the rain's caps add up to 82 per step and the lake adds what the dead and the runoff give
   it) and holds 1,500-2,000 bodies.
4. **The relief stops setting the world's income.** At relief 256 the world eats within 15% of
   what it eats at relief 64 (e019: 26-31 against 56-71), because the rain field is the same
   shape at every relief and only the lake's size changes; the lake is smaller and the ridges
   hold as many bodies as at 64.
5. **Rain on every cell alike has no store and swings.** The flat control drains the lake too,
   but no cell's income exceeds the sun, so the air empties every step and the matter has
   nowhere to sit but in plants and bodies: the population overshoots and falls 2x or more
   (coefficient of variation over 0.20) or the world dies in at least one seed of four.
6. **The same body wins at every height.** Judged by #19 the law by itself does not make more
   winners: a bar of 6-10 gut cells is the top body in every band, lineages alive 1-2,
   contacts under 0.1 per body per step, no bite. If a band's top body differs from the lake's
   (in mass, muscle or extent) in three seeds of four, that is the first place effect under the
   uniform sun and worth the next law.

## Method

Code: e019 (`experiments/e019_terrain`, with the f64 soil) with the air added:

- an air pool (`air`, one f64) that receives what a body burns: its upkeep (`UPKEEP * mass +
  UPKEEP_BODY`, or what it has left) and the energy it pays for moving, at the two places where
  e019 called `Food::spend`; with `rain soil` those still fall to the soil under the body;
- the rain (`Food::rain`), once per step before regrowth: every cell gets at most its cap
  (`RES_GROWTH * height / relief` with `high`; `RES_GROWTH` with `flat`; 0 with `soil`), the
  same share of its cap for every cell when the air holds less than the caps add up to; rain
  lands in the soil; what does not fall stays in the air. The dead, a child never placed and a
  broken cell nobody eats still lie on the ground where they were (e017).

Two new arguments, `rain` (high, flat or soil; the default is high) and `breath` (the share of
what a body burns that goes to the air, 1 by default; the rest falls to the soil under the body
as in e019). New columns: `air` (matter in the air), `rain` (rain fallen per step); `rain` per
place in `places.csv`; the rain mode and the breath share in `terrain.json`. Everything else is
e019 (uniform sun, relief 64 by default, flow 0.1, matter 8 per cell at the start as plants, a
cell of 0.02).

Pilot (seed 9, 100,000 steps, 128x128, three threads each, four at once; the files were not
kept): the answer comes fast and changes the plan. With rain on the mountains the lake drains
into the air within 10,000 steps (soil 588 of 139,700 at step 10,000, the air 135,650) and the
world is steady from step 20,000: the rain falls at its caps (76.4 per step; the caps add up to
0.01 times the mean of height over relief, 0.466, times 16,384 cells), the world eats 78.2 per
step and holds 1,490 bodies, 673 of them on the ridges, 513 on the slopes and 301 in the valleys,
e019 upside down (e019's soil law, run as a check: 75.8 eaten, 1,530 bodies, 106 on the ridges).
46 of the sun falls on empty soil, now in the valleys (31 of their 54.6). The body is the same
in every band (mass 8.0, 8.2, 8.0). At relief 256 the world is the same to 0.1% (78.3 eaten,
1,547 bodies, 690 on the ridges): the rain field has the same shape at every relief, and the
lake, which the relief used to set, is gone. Hypothesis 4 is answered by the pilot and the
relief 256 runs are dropped. Rain on every cell alike does not drain the lake: every cell gets
0.0064 per step from the air, the lake's cells draw the rest from their pile, and the population
grows (2,118) until the cells bodies stand on cap the draw at what the rain brings; the world is
e019's flat lawn (104 eaten, 725 / 708 / 685 bodies by band, 2 barren) with the terrain moot and
the air empty every step, so hypothesis 5 is wrong before the runs. That makes the store the
question: all of the breath to the air loses the lake, none of it loses the ridges. So the third
world sends half of what a body burns to the air and half to the soil under it (`breath 0.5`; a
grazer's intake is about half dung and half breath): the lake stays (17.7 per cell in the
valleys, 6.3 on the slopes, and 0.79 on the ridges, where e019 had 0.0), 99% of the cells hold
soil, 0.5 of the sun is lost to empty soil, the world eats 107.8 per step (the sun less the
cells bodies stand on) and holds 2,379 bodies spread evenly (819 / 773 / 787), the soil runs
downhill at 333 per step (e019: 87), and the body is smaller (mass 5.3 against 7.2).

Runs (1,000,000 steps, 128x128, relief 64, flow 0.1, seeds 1-4, twelve at once locally, one
thread each, `run.sh 1 2 3 4`): rain on the mountains with all of the breath to the air
(`results/128_sigma0_r64_f0.1_high_*`), with half of it (`128_sigma0_r64_f0.1_high-b0.5_*`),
and rain on every cell alike (`128_sigma0_r64_f0.1_flat_*`). Reference: e019's uniform sun at
relief 64 and 256, seeds 1-4 (`../e019_terrain/results/128_sigma0_r64_f0.1_*`,
`128_sigma0_r256_f0.1_*`).

    cargo run --release -p e020_rain -- <steps> <seed> <size> <widths> [cell_energy] [matter] [relief] [flow] [rain] [breath]
    uv run python experiments/e020_rain/report.py

## Result

All numbers are medians over the second half unless said otherwise; ranges are over the four
seeds of a world (`results/128_sigma0_r64_f0.1_high_*`: all of the breath to the air, the rain
by height; `128_sigma0_r64_f0.1_high-b0.5_*`: half of it; `128_sigma0_r64_f0.1_flat_*`: rain on
every cell alike). The report (`report.html`) has the charts, the maps, the bodies and the
viewer.

- **The high ground lives.** With the breath in the air the ridges hold 658-670 bodies at the
  end (e019: 0-14) and eat 34-36 per step, the slopes 507-653 and 26-35, the valleys 268-484
  and 13-25: the food eaten falls with height the way the rain does. The world eats 72.8-94.3
  per step (e019: 56.2-71.1), holds 1,442-1,778 bodies at a coefficient of variation of
  0.009-0.019, last quarter over third 0.998-1.000, no extinction. The seeds spread with their
  terrains: the rain cap is 164 times the mean of height over relief, and a seed whose ground
  averages 0.56 of the relief (seed 2) eats 94.3 where one at 0.44 (seed 1) eats 72.8.
- **The store moves to the air.** The lake drains through the bodies into the air within about
  10,000 steps and stays there: soil 2,239-7,262 at the end (e019: 135,550-136,970), air
  129,319-134,672, rain at its cap (72.4-92.5 per step) every step of the second half. The
  ground keeps rivers instead of a lake: rain landing where a body stands is not drawn (a held
  cell does not grow) and runs downhill, 221-536 of soil moved per step (e019: 66-77), and the
  final soil maps show veins running from under the crowds to a remnant pool on the valley
  floor. Sun lost to empty soil falls from e019's 34-46% to 10-29%, all of it in the valleys.
  Matter holds to 0.02%. At relief 256 the pilot's world is the same as 64 to 0.1% (the rain
  field has the same shape at every relief): the relief no longer sets the world's income.
- **The bodies sort by height, a little.** Mass at birth rises from the valleys to the ridges
  in all four runs (7.29/7.48/8.19, 8.04/8.97/9.05, 7.07/7.38/7.67, 8.03/7.98/8.17): the small
  variants of the winning bar (6 cells) hold a third of the thin valleys, the full 8-9-cell
  bars nearly all of the ridges, and twice a second lineage stands lower for 309,000-520,000
  steps (seed 1: lineage 76 at height 30 under the main line's 34; seed 2: lineage 86 with 121
  of 126 agents in the valleys at height 21 under a main line at 38). Every winner is still a
  gut bar: no muscle, no tooth, contacts 0.009-0.042 per body per step, lineages alive 1-2.
- **Half the breath is the best world and erases the places.** With half of what a body burns
  falling under it, both stores hold (soil 135,866-136,299, the air emptying every step),
  99-100% of the cells are wet, the ridges get 25-28 of rain per step, and the world eats
  102.9-109.1 per step - the whole sun less the 33-38% shaded by bodies - with 2,002-2,268
  bodies (cv 0.006-0.008). Nothing but shading is wasted in a closed world for the first time.
  But the three bands hold the same 666-757 bodies each, eat the same 35.5-37.9, grow the same
  body, and lineages alive are 1 (seed 1 turns over through 4).
- **Rain everywhere alike rebuilds the lawn (hypothesis 5 wrong).** No swing, no death: 100.4-
  103.3 eaten, 1,928-2,226 bodies, cv 0.008-0.019. Every cell gets 0.0061 per step from the
  air and draws the rest from its soil, so the lake drains only until the population's own
  shading caps the draw at what the rain returns; the lake then sits untouched (136,019-
  136,511) and the world is e019's flat lawn with the terrain moot (bands within 1-4%).
- 429-492 steps per second with twelve runs on the machine (the last two runs alone: 550-600);
  the rain is one pass over the cells.

## Conclusion

1. The high ground lives: yes. 658-670 bodies and 34-36 eaten per step on ridges that held
   0-14 and 0.0-0.5; the map of life is the map of the rain, e019 inverted.
2. The store moves to the air: yes, in 10,000 steps, and the world still stands (cv under
   0.02 for a million steps): the closed world's store can sit in an invisible pool and the
   soil's job becomes transport - rivers, not a lake.
3. The world stands: yes. 72.8-94.3 eaten, no extinction, no swing; the seeds now spread with
   their terrains' mean height, which is geography, not noise.
4. The relief stops setting the income: yes (by the pilot; relief 256 = relief 64 to 0.1%).
5. Rain everywhere alike swings: no. It rebuilds the flat lawn; the store sits wherever the
   draw is capped, and the population's own shading is cap enough to preserve the lake.
6. The same body wins at every height: no - the bodies sort. Born mass rises with height in
   all four seeds, the thin valleys keep the small variants and twice a second lineage; but
   every winner is a gut bar and lineages stay 1-2, so by #19 the law grades the one winner
   rather than multiplying winners.

What it changes: the closed cycle has two pools from here, the soil and the air, and the route
of what a body burns decides which holds the store. Kept as the world's law: the breath to the
air with the rain by height (the high ground's income; e019's lake was one place, and a world
whose matter all falls back under the bodies has no second one). The half-breath world shows
the trade exactly: richness against difference - it eats the most and has no places; the
mountain-rain world eats a fifth less and is the first world where a place shaped a body. A
place law made of amounts (more rain here, less there) grades bodies; the next law on the
height axis (#14) should make the high ground differ in kind - what grows there, what standing
there costs - not only in how much falls.
