# e117: the map at an animal's size - rung 1 again (#135)

Date: 2026-11-11 to 2026-11-14

## Purpose

#135 (design agreed 2026-11-11) rebuilds the world at the size of an animal, and its first rung is the map: an
open-world game's map whose places differ by latitude, the wind's side, height and island, with a day and a year,
drawn at 5 m where an animal walks. `base/`'s ground and climate are kept; what changes is the scale (16 km, cells of
125 m), a band of latitude folded north to south, a real year, the year's water (fronts, a dry season, snow) and the
ground at 5 m. Nothing lives on it yet.

## Hypothesis

1. `base/`'s ground and climate, given a band of latitude and the westerlies, make places that differ as designed:
   at least 10 C north to south at sea level, rain five times wetter on the windward side than the lee, a snow line.
2. A 5 m ground drawn once from the coarse one (detail by slope, hollows filled to ponds, streams where a year's
   runoff gathers) reads on the screen as a landscape an animal could walk, from the eye of a walker to the whole map.
3. (Added 2026-11-14, after the first look: "the season changes and I cannot tell what differs".) The year is seen on
   the map: a place looks different in January and in August, and differently in the north and the south.

## Method

- `worlds/isles16.params` over `base/worlds/isles1.params`: 128 x 128 cells of 125 m, a fifth land, terrain seed 23
  mirrored west for east (of forty surveyed with `survey=40`: 21.9 km2 to 1,500 m, 12.4, 9.2 and 4.4 km2, two
  islets; mirrored, the high island's summit stands on its west coast and its lowlands lie in the lee), heights to the
  power 1.8 (`relief_pow`), latitudes 44-64 N run once south to north (`lat_span`), wind from the west-south-west
  wandering 25 degrees, a year of 365 days (isles1's update of 3.2 hours kept).
- Laws changed in the crate, all in the air followed across the map (`climate.rs`, the sweep), all off unless asked
  (with `base/`'s parameters the crate gives `base/`'s log, maps and census to the digit, checked on a 128 world):
  - **each row's sea air is its own**: as warm as its row's sea and as wet as that sea keeps it; air crossing to the
    next row arrives as wet a share of that row's sea air as it left (the rows lie 17 km of latitude apart and are
    drawn 125 m apart; carried as it is, a southern row's water rained 45 m a year on the next);
  - **fronts** (`track`): a front lasts 1.5 days and 2.5 clear days follow, in the mean; each reaches south to its
    own latitude about the storm track's edge, which lies at 48 N, 8 degrees further north at midsummer and south at
    midwinter. The rows it reaches have the sea's wet air and gain water from beyond the map (900 mm a year where
    every front reaches); the rest lie under air sunk from aloft, a fifth short of the sea's, where it rains nowhere;
  - **the rain-out of a slope** (`rain_tau` 200 s for isles1's 1,000 s, `lifted` 0.012): these islands' slopes are
    crossed in 200-400 s, so the lifted air rains on the way up and comes down short;
  - **snow** (`snow_melt` 3 mm a day a degree): rain on freezing land lies, melts by the degrees above freezing and
    reaches the ground as water then; a pack over 3 m of water creeps to the cell below.
- `ground5.rs` (`fine=25`): the 5 m ground, generated once at the end of a run from the kept years' rain.
- The run writes the kept years' twelve mean months (`_season.bin`: temperature, rain, the soil's fill, snow lying,
  run-off). The viewer's map mode (`viewer map <prefix>`, `viewer/web/src/map.ts`) draws tiles of 320 m coarser with
  distance under the sun of a day and an hour, and from the months: snow where it lies, green where the month is warm
  and its soil wet (no plants exist: it is what the climate would let grow), straw where it is not, a stream as a dry
  bed in a month that leaves it under a litre a second.
- Runs (Ubuntu, six threads): `map`, twenty bare years (`sow=1000`), the last ten kept, 95 s (4.4 s a year for air
  and water); trials of eight years (41 s) chose `track_lat`, `rain_tau` and `lifted`. Read by `read.py`
  (`results/map_reading.csv`, `results/provenance.csv`).

**Stop early if:** - (no log column: a run of the bare climate takes two minutes.)

## Result

`map` (years 11-20; lowlands are land under 300 m, quarters run from the spring equinox):

| lowlands at | mean C | winter / summer C | rain mm | spring, summer, autumn, winter | soil's fill, summer / winter | months of snow |
|---|---|---|---|---|---|---|
| 44-49 N | 17.0 | 11.6 / 22.5 | 517 | 38, 36, 231, 213 | 0.28 / 0.95 | 0 |
| 49-54 N | 13.5 | 7.8 / 19.3 | 529 | 55, 50, 219, 206 | 0.48 / 0.95 | 0.1 |
| 54-59 N | 9.9 | 3.7 / 16.3 | 717 | 97, 89, 282, 249 | 0.68 / 0.97 | 0.4 |
| 59-64 N | 5.6 | -0.7 / 12.2 | 901 | 180, 174, 292, 255 | 0.87 / 0.97 | 4.1 |

- By height: 1,058 mm at 300-800 m, 1,626 mm at 800-1,200 m, 2,176 mm over 1,200 m, where snow lies 5.0 months.
- By side (lowlands west against east of an island's summit): 896 against 426 mm on the high island (x2.1), 662
  against 89 mm on the 9.2 km2 one (x7.5), x1.9 and x1.8 on the next two; within an island rain runs from 28 to
  2,734 mm (the high one) and from 7 to 1,894 mm.
- The land's run-off by month, from the spring equinox: 8, 6, 5, 3, 3, 6, 11, 14, 14, 12, 10, 9% of the year's.
- Years differ: the land's rain 437 to 1,045 mm and its mean 10.2 to 12.5 C over the ten.
- The 5 m ground: 49 km2 of land, ponds 1.0 km2, streams of 5 l/s and more about 15 km. On the map page 476 of
  2,980 stream cells are dry beds in mid August (424 of the 1,360 south of 51 N), 175 in January, none in April or
  October.
- Before the year's water (10 bare years, first reading): the south's lowlands 1,011 mm and the north's 347, no dry
  season, the lee x1.3; on the page a quarter of the land changed colour between January and July, and that faintly.
- On the screen: the whole map reads as islands in a sea; in January the northern islands and the summits are white
  and the south green, in August the south's lowlands are straw with dry stream beds and the north green; from a
  walker's height a stream winds from a pond down a valley to a beach.

## Conclusion

1. **Places differ as designed, the lee less than asked**: 11.4 C north to south at sea level (asked 10); snow on the
   north's lowlands four months and on the summits five, none in the south; the windward lowlands twice the lee's on
   three islands and 7.5 times on one (asked x5), since a lee is dry only close behind a height: the air a slope has
   wrung is refilled by the fronts within a few km.
2. **The 5 m ground reads as a landscape**, as far as watched (the user, 2026-11-14: "the terrain looks good").
   Streams still run straight down smooth slopes.
3. **The year is on the map**: the south has a rainless summer (7% of its rain, the soil at 0.28 of its fill, a third
   of its streams' length dry) and a green winter; the north rain in every season and four months of snow. Whether it is seen is
   the user's to say.

Holds under: bare ground (plants will draw the soil down further, and shade it), one terrain seed, ten years.
Not built: weather on the screen (a front is a day and a half of rain in the run, the page draws months), snow that
cools its ground, erosion, the sun's tilt on the page (the run's is 17.8 degrees).
Noticed in `base/`'s law, not changed: a year's warmth anomaly reaches a land cell twice, through the sea air and
again on its own, so the land's years differ by up to 1.85 times the sea's.

`vision.md`: row A (places, time, water, heat) rewritten for this map. `foundation.md`: the air's laws and rung 1's
reading. The crate's laws go to `base/` (the next rung, plants at metres, copies it).
