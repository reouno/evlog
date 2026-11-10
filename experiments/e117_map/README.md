# e117: the map at an animal's size - rung 1 again (#135)

Date: 2026-11-11

## Purpose

#135 (design agreed 2026-11-11) rebuilds the world at the size of an animal, and its first rung is the map: an
open-world game's map whose places differ by latitude, the wind's side, height and island, with a day, drawn at 5 m
where an animal walks. `base/`'s ground and climate are kept; what changes is the scale (16 km, cells of 125 m), a band
of latitude folded north to south, a real year, and the ground at 5 m. Nothing lives on it yet.

## Hypothesis

1. `base/`'s ground and climate, given a band of latitude and the westerlies, make places that differ as designed:
   at least 10 C north to south at sea level, rain five times wetter on the windward side than the lee, a snow line.
2. A 5 m ground drawn once from the coarse one (detail by slope, hollows filled to ponds, streams where a year's
   runoff gathers) reads on the screen as a landscape an animal could walk, from the eye of a walker to the whole map.

## Method

- `worlds/isles16.params` over `base/worlds/isles1.params`: 128 x 128 cells of 125 m, a fifth land, terrain seed 23
  (of forty surveyed with `survey=40`: 21.9 km2 to 1,500 m, 12.4, 9.2 and 4.4 km2, two islets), heights to the power
  1.8 (`relief_pow`), latitudes 44-64 N run once south to north (`lat_span`), wind from the west-south-west, a year of
  365 days (isles1's update of 3.2 hours kept), `lifted` 0.02.
- Laws changed in the crate: on a band of latitude the sea air's warmth over each row is that row's sea (its water
  stays the world's one value: by row, air flowing north rains a southern row's excess once a crossing, the update's
  500 crossings over - tried, 45 m of rain a year).
- `ground5.rs` (`fine=25`): the 5 m ground, generated once at the end of a run from the kept years' rain.
- The viewer's map mode (`viewer map <prefix>`, `viewer/web/src/map.ts`): tiles of 320 m drawn coarser with distance,
  the sun of a day and an hour, snow and the green the climate allows by the day's temperature (no plants exist).
- Runs (Ubuntu, 40-50 s each): ten bare years (`sow=1000`), maps of the last three.

**Stop early if:** - (no log column: a run of the bare climate takes a minute.)

## Result

`map` (10 bare years, the last three's maps):

- Lowland (under 300 m) mean temperature by latitude: 19.0 C at 44-49 N, 15.5, 11.9, 7.6 C at 59-64 N; the season's
  swing (quarter means) 11-13 C. Summits 5.5 C a year.
- Lowland rain 1,011 mm in the south, 677, 342 and 347 mm in the north; 560 mm under 200 m, 2.9 m over 1,400 m. The
  lowlands' west third against their east third: 672 against 514 mm (x1.3).
- The 5 m ground: 48 km2 of land, ponds 1.0 km2, streams of 5 l/s and more 17 km.
- On the screen: from a walker's height a stream winds from a pond down a green valley to a beach; the whole map
  reads as islands in a sea; winter browns the lowlands and whitens the northern summits.

## Conclusion

(Open.) Hypothesis 1 holds for temperature (11 C north to south) and not for rain: the north is drier than the south,
the opposite of the design, and the lee only 1.3 times drier - `base/`'s rain comes from height alone, with one sea
air for the whole map. Hypothesis 2 holds as far as watched: streams still run straight down smooth slopes.
