# e061: the climate (foundation stage A, #74)

Date: 2026-09-13

## Purpose

Stage A of `foundation.md`. Before anything lives on it, find out whether the laws of the physical
world make enough habitats, at scales a body feels, that change with the seasons and do not drift.
It is the cheapest layer, so it is searched widely, and it decides the size of the world.

## Hypothesis

1. At ratios near Earth's (a third of the cells land, a tilt of 23 degrees, a wind of Earth's speed
   for the size of a cell), the laws make at least 5 habitats of 2% of the cells each without
   tuning: cold and hot by latitude and height, dry and wet by the wind and the mountains.
2. The width line decides the size: at 256 cells few habitats lie in patches 42 cells wide (three
   lives of travel), because the moisture bands cut the land into narrower pieces; 512 passes.
3. The change line (10-50% of the cells change habitat in a year) is set mostly by the tilt.
4. The stand line (year 20's map agrees with year 10's on 90% of the cells) passes, except where
   lakes are still filling basins at year 10.

## Method

**The world.** A torus. Generated from the seed: a height map (octaves of smooth noise, the widest
`grain` cells across) cut by a sea level so that `land` of the cells are above it. The rows run from
latitude `lat_lo` to `lat_hi` and back, so a walk along y passes every latitude twice and there is no
edge. Laws, updated every `tick` = 10 steps of the bodies' clock:

- **Sun.** The declination follows the year (`tilt` x sin), the hour angle the day and the longitude
  (x), so day and night sweep across the map. A cell's light is the cosine of the sun's height.
- **Heat.** A cell goes `land_rate` (land) or `sea_rate` (sea) of the way to `night + gain x light -
  lapse x height` each update, and exchanges heat with its neighbors by the difference of potential
  temperature, divided by its capacity (the sea's is `land_rate / sea_rate` times the land's).
- **Water.** A cell's air takes up `evap` of its deficit (the saturation at its temperature, 25 mm at
  20 C, 6.5% more a degree), from the sea in full and from the ground by how full the ground is. Air
  above 80% of saturation rains `rain` of the excess, so it rains where the air has risen (a colder
  cell) or cooled (night, winter). One wind moves the air `wind` cells an update toward `wind_dir`,
  turning `wind_turn` degrees with the season. The ground holds `soil` mm; water above that stands,
  and `flow` of it runs to lower neighbors by the drop of the surface (e035), into the sea at the coast.

**Habitat.** Each quarter of a year a cell's medium (land; shallow water: sea under 200 m or a pool
of 500 mm standing more than half the quarter; deep water), its temperature band (the quarter's mean:
under 5 C, 5-20 C, 20 C and over) and on land its moisture band (the quarter's mean fill of the
ground: under 1/3, 1/3-2/3, over 2/3). 15 habitats.

**Pass lines** (#74): at least 5 habitats of 2% (mean over the last year's quarters); at least 3 of
those with an area-weighted median patch width of 42 cells or more (width: the side of the largest
square inside the patch); 10-50% of the cells change habitat over the last year; the last year's
four maps agree with the middle year's on 90% of the cells.

**Runs.** Pilots at the defaults on sizes 128, 256 and 512 (speed, maps), then a Latin hypercube over
land share, relief, latitude span, day and year over a life of 300 steps, the sun's gain, the tilt,
the land's response rate, the wind and the rain, one row of measures per candidate.

    cargo run --release -p e061_climate -- experiments/e061_climate/results/pilot/default size=256 maps=1
    uv run python experiments/e061_climate/search.py 300 1000      # results/search/candidates.txt
    xargs -P 10 -L 1 ./target/release/e061_climate < experiments/e061_climate/results/search/candidates.txt

The search axes (Latin hypercube, `search.py`): size 256 or 512, grain 32-256 cells, land 0.2-0.7,
relief 500-6,000 m, a latitude span of 30-180 degrees placed anywhere between the poles, a day of
0.1-1 life, a year of 10-100 lives (3,000-30,000 steps), gain 120-240 C, tilt 0-45, land rate
0.02-0.3, wind 0.1-2 cells an update, wind turn 0-90 degrees, rain 0.02-0.5. Fixed: evap 0.05, sea
rate 0.0005, spread 0.2, lapse 6.5, night -30, soil 150 mm, flow 0.25. The seed of candidate i is i.

The maps (`*_maps.bin`, 4-16 MB) are not committed. The report draws them from
`results/pilot/default` (the command above) and `results/pass/c1221` (its line from
`candidates.txt` with `results/pass/` as the prefix and `maps=1`).

**Runs made.** The default world at 256 (20 years, 90 s with the search running beside it); the
search, 300 candidates of 20 years on 10 local cores (65 min, 10.1 core-hours); 7 candidates that
failed the stand line rerun for 80 years (`results/spinup`); two passing worlds with maps
(`results/pass`: c1182, the most wide land habitats, and c1221, the report's). All on the Mac.

**The viewer.** `EVLOG_VIEW=rec:stride=200,layers=1` records the climate (46 MB a year at 256).
The header carries `water` (the sea and the pools), `temperature` (C + 50), `moisture`, `humidity`,
`rain`, `light` and `habitat`, and the browser's new "地面の色" menu colours the ground and the water
by any of them (`?ground=habitat` opens on one). The sea floor is drawn at most 3 units deep. Checked:
the header, the wire tests and the minimap; two tries at a headless screenshot of the 3D view did
not produce one, so the colouring is still to be looked at in a browser.

## Result

**The default world** (256, seed 1, 20 years; 1.18 ms an update alone, 47 s):

| measure | value |
|---|---|
| habitats of 2% | 12 of 15 |
| in patches 42 wide | 1 (deep hot, 55); land habitats 3-17 wide |
| change in a year | 53% (temperature band 52%, moisture band 16%, medium 0.02%) |
| stand (year 20 against year 10) | 99.6% |
| land / sea mean temperature | 10.6 C / 16.9 C |
| warmest row minus coldest row | 28.7 C |
| day swing / season swing on land | 14.2 C / 22.5 C |
| rain on land | 394 mm a year; lakes 0.55% of the cells |
| land dry / moist / wet | 37% / 17% / 45% |
| water ledger error | 3e-16 |

It fails only the width line. The ground fills or empties: wet windward coasts and dry lee sides,
with a thin moist band between (its patches 3-5 wide).

**The search** (300 candidates, 20 years each):

| pass line | 256 (150) | 512 (150) | all |
|---|---|---|---|
| 5 habitats of 2% | 146 | 148 | 294 |
| 3 of them 42 cells wide | 24 | 90 | 114 |
| 10-50% change in a year | 87 | 88 | 175 |
| year 20 agrees with year 10 on 90% | 125 | 126 | 251 |
| all four | 4 | 30 | 34 |

What decides each line (rank correlation over the 300; no other axis above 0.3 on a pass line):

- **Width: the size and the grain.** Wide habitats rise with the size (0.51) and the grain of the
  terrain (0.52). At 512 with a grain of 128 or more, 47 of 53 pass the width line and 16 pass all
  four; at 256 with a grain of 100 or more, 18 of 66 and 3. The wide habitats are the deep sea
  (cold, mild, hot: 114-152 candidates each) and the dry land (cold 98, hot 91, mild 53); a wet or
  moist land habitat is wide in 2-8 candidates of 300, because the rain falls on coasts and belts.
- **Change: the tilt.** Change rises with the tilt (0.66; its temperature part 0.74) and the land
  share (0.39). It fails by too much far more than by too little (100 above 50%, 25 under 10%). A
  tilt of 10-30 degrees passes in 95 of 134. The moisture part follows the gain (0.62) and the wind (0.32).
- **Stand: updates, not years.** Stand follows the year's length (0.76). With 1,000 updates a year
  or more 141 of 144 pass; under 600, 51 of 90. The 7 failures rerun for 80 years all pass
  (0.767-0.893 at 20 years, 0.905-0.989 at 80), with the same habitats and change: the sea and the
  ground water need about 10,000-20,000 updates to settle, and a short year counts too few of them
  by year 10.
- **Hardly matter** for any line: the day's length, the rain rate, the wind speed, the relief and the
  gain (each 0.13 or less).

Passing worlds hold 5-15 habitats (median 8); 30 of the 34 have at least one wide land habitat. The
most (c1182: 512, grain 193, half land, tilt 18, latitude -63 to 0) has four: a wet equatorial belt
between dry subtropics, with cold dry land at the far rows in winter. It is a hot world (land 28.8
C): the lines do not ask for a temperate one. Passing worlds run from -6 C to 31 C on land and from
26 to 3,700 mm of rain a year on it.

## Conclusion

1. **Hypothesis 1, yes.** The laws make 5 or more habitats of 2% in 294 candidates of 300 and 12 at
   the defaults, with no tuning.
2. **Hypothesis 2, yes, and the grain as much as the size.** 30 of the 34 passing worlds are 512; at
   256 the continents are too small for land habitats 42 cells wide. The size of the world for stage
   B is 512, with a grain of about 128 or more.
3. **Hypothesis 3, yes.** The tilt sets the change; 10-30 degrees is the band.
4. **Hypothesis 4, no.** Nothing drifts: what fails the stand line is the climate still settling when
   the year is short. A world must be spun up for about 20,000 updates (200,000 steps) before it is
   judged or before anything lives on it.

These hold for our choices: bands at 5 and 20 C and at a third and two thirds of the ground's fill,
habitats from quarter means, shallow water under 200 m with the sea's depth on the land's scale (a
low relief makes a shallow sea: c1182's is 30% of the world), a body's travel of 14 cells, one
uniform wind, no ice or snow, and terrain that does not erode.

For stage B (#75): a 512 world costs 4.5 ms a climate update alone (8.4 ms with 10 runs beside it),
so the climate is 0.45 ms a step. The producers cannot be updated per cell per step at 512: e059's
world alone cost 3.0 ms a step at 128, which is 48 ms a step at 512 and 2.7 hours for 10 years. Stage
B has to put the producers on a slow clock too, as the climate is, before a search of 100 is possible.
