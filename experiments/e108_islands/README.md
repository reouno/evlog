# e108: the ground on the small world - islands in a sea, climate from height, wind and season (#127)

Date: 2026-10-05

## Purpose

The scale is chosen (#126, `foundation.md` 4): a world 64 km on a side, 512 x 512 cells of 125 m, a tenth of it land
in a few islands, where a grown body can be one animal. `base/`'s ground is a planet: its climate comes from
latitude and several of its laws read the planet's size. This rung puts the same ground - rock, soil, drainage,
nutrients A and B, years that differ - on the small world with nothing living on it, and asks e102's question
again: **does it stand, and does it make places?** It also reads the two faults e102 carried (#118, folded in here):
the land rained its own water back (runoff 10% of the rain) and the years were mild (rain varied 12%).

## The cycles (written before the run)

The laws stay. What read the planet's size is rewritten, each rate from its units and none searched:

- **Ground.** The same noise, with a tenth of it above the sea and the last 6 km before the border sunk: the world
  is land in a sea and does not wrap. Rock provinces, soils, the drainage network, lakes and groundwater are e102's.
- **Sun.** One latitude (42 degrees: under e061's sun an open sea settles near 21 C there) and one hour for the whole
  world. A slope's light is the sun's mean direction over the update along the ground's normal, so a slope that
  faces the sun is lit more than one that faces away (no shadow is cast by other ground).
- **Air and rain.** At 5.5 m/s the wind crosses 64 km in 3.2 hours, an update, so the air cannot be a store that
  shifts a cell. It enters at the windward border as sea air and is followed across the world in one pass, upwind
  cells first, by e061's two laws: it takes up water by its deficit and rains what it cannot hold. What it can hold
  falls with the height the land lifts it. *Takes* from the sea upwind and the wet ground; *refilled* at the border
  every update; *limited* by what a climb can wring out - the air's water lies mostly above the layer a land lifts
  to its dew, and only that layer's share (`lifted` 0.05) takes part, which is what keeps an island's rain at a
  hundredth of the vapour that passes over it (a real island 1.6 km high takes about 1.5%). The excess falls in
  about 1,000 s (cloud to rain), 5.5 km downwind. Balance: wet windward slopes, rain spilling a few km past a
  crest, a dry lee that stays dry to the border - and a lower island downwind of a higher one in its shadow.
- **Heat.** A land cell's temperature goes towards its own light's equilibrium and the sea air's at its height, by
  the wind: `wind / (wind + 1 m/s)`, 0.85 of it the sea air's at 5.5 m/s (turbulent exchange over rough land against
  the ground's own radiation). So the land is mild by day and by season and cold by height (6.5 C a km), as a
  small island is; on the planet the neighbours' exchange did this, which at 125 m reaches a few cells.
- **The wind's direction** is the season's (it turns 36 degrees between summer and winter, c1225's), turned a
  little by the year (10 degrees) and wandering from day to day (45 degrees, held 3 days): the lee gets the rain of
  the days the wind comes round. A year's anomaly of warmth and rain is one number for the whole world; a storm is
  the whole world's, with a wind of its own and four times the lifted layer, and as rare for a cell as on c1225.
- **Water on the ground and nutrients**: e102's laws. A river's deposition is a share a km, not a cell; a river is
  0.1 m3/s.

## Hypothesis

e102's lines, on the small world:

1. **The ledgers close**: water, A and B to 1e-9, and the air's pass carries out what it took up less what it rained
   (`air_err`) to 1e-9.
2. **Rivers reach the sea**: at least 1% of the land carries a mean of 0.1 m3/s (74 mm an update), and the land's
   water drifts under 1% a year over the last 10 years. Read against #118: the runoff's share of the rain.
3. **The ground differs by chemistry**: the soil's A:B and A + B each span x4 (p10 to p90).
4. **Years differ without drifting**: consecutive years' land rain maps correlate between 0.2 and 0.95, and the
   land's temperature has no trend over 0.1 C a year. Read beside it, as e102 learnt: how much a cell's rain varies
   between years.
5. **Places**: the effective number of places on the land by e102's bands, unchanged (medium, temperature at 5 and
   20 C, moisture, A:B, fertility), is at least the planet's 15.4 - or this README says which of them a small world
   cannot hold. Read beside it: the span over the land of the year's mean temperature, rain and light; how the
   islands differ from each other; the narrowest sea between them (what could part the lines, #117).

## Method

`base/` copied; `src/climate.rs` (the pass, the heat, the wind, the light), `src/terrain.rs` (the border, the
ground's tilt), `src/noise.rs` (a normal draw) and `src/main.rs` (parameters, two log columns, the year's light as a
map) changed. With the new parameters at their defaults the crate is `base/` to the digit (checked on c1225).

    cargo run --release -p e108_islands -- <prefix> experiments/e108_islands/worlds/small.params seed=<N> sow=1000

Life is off (`sow` after the run). Terrain candidates first (`years=0`, seconds each): the seed is chosen by
`terrain.py` for 3-5 islands of 1 km2 or more, one about 2 km high and the others lower. Then one world, 30 years,
the last 10 read by `measure.py`. All runs on Ubuntu (`ssh leo`).

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `a_err` > 1e-6 at 23760
- `air_err` > 1e-6 at 23760
- `land_rain` < 100 at 118800

(steps: two years, ten years; the log has a row a year.)

**Cost.** One world, one core: 30 years of the ground alone, about 5-10 minutes.

## Result

### The terrain

Sixteen seeds were drawn three ways (`terrain.py`, seconds each on Ubuntu; `results/terrain/`, not committed). With
the border sunk over 6 km, as first written, the islands lay against it and were cut straight; over 16 km the land
drew into one island of 300-400 km2; over 12 km (`edge` 96) three of sixteen seeds hold three or more islands of 20
km2. Seed 1 is taken (`worlds/small.params seed=1`): 410 km2 of land in eight islands, five of them over 20 km2 -
149 km2 (1,197 m high), 71 (1,524 m), 64 (1,142 m), 63 (2,002 m) and 24 (964 m) - and the sea between those five
2.3 to 32.5 km wide. (The line written before - "3-5 islands of 1 km2 or more" - fits almost no seed: the noise
always leaves a few islets. It is read as islands of 20 km2.) The ground is steep, as a high island is: the median
slope is 0.41 and a tenth of the land is steeper than 0.78. No rate was changed after the first trial (3 years).

### The run

`results/isles1`, Ubuntu, 4 threads, 30 years in 411 s (13.6 s a year: the air's pass 9.2 s on one thread, the water
3.1 s); the last 10 read by `measure.py` (`results/measure.csv`, thresholds in `results/provenance.csv`). A year is
159 days, so a year's rain is 0.44 of what the same weather gives in 365.

| | reading | line | verdict |
|---|---|---|---|
| H1 ledgers | water 3e-13, A 4e-14, B 4e-14, the air's pass 1e-13 (worst year) | 1e-9 | **yes** |
| H2 rivers | 6.8% of the land carries 0.1 m3/s (0.39% carries 1 m3/s, the largest 1.7); the land's water drifts -0.6% a year | 1%; 1% a year | **yes** |
| H3 chemistry | A:B spans x9 (p10 0.03, p90 0.32), A + B x68 | x4, x4 | **yes** |
| H4 years | consecutive years' rain maps correlate 0.99; the land's temperature trends +0.18 C a year over the ten | 0.2-0.95; 0.1 | **no** as written |
| H5 places | 4.5 effective places on the land by e102's bands | 15.4 | **no** |

**The water (#118).** 1,741 mm a year rains on the land and 1,670 mm reaches the sea: 96% runs off, against 10% on
the planet. The land no longer rains its own water back - what it gives the air leaves with the wind - but it gives
little: 73 mm a year, because the air over a small island is the sea's, mild and humid, where the planet's noon
ground stood at 55-62 C. So streams are everywhere (500 lake cells, a stream on 6.8% of the land) and the bare soil
is full: 98% of the land is in e102's wet band and 0.5% in its dry one.

**Rain is where the land is high.** It correlates 0.91 with height: 53-607 mm a year under 100 m (p10-p90), 2,892-
5,304 mm over 1,000 m, against 293 mm on the open sea. Across the land the year's rain spans x15 (251 to 3,776 mm).
Height is not all of it: land of one height differs x11 under 100 m and x5 from 100 to 300 m, and on the five large
islands the windward half of the lowland gets 2.1 times the lee half's rain (the median; 1.7 to 3.5). The wet side
is weaker than was written before the run: the excess falls 5.5 km downwind, about an island's half-width, so the
rain sits on the crest and just beyond it, and the wind wanders 45 degrees.

**Heat and light.** The sea settles at 20.8 C. The land's year means run from 10.7 to 21.1 C (p5-p95; 4.0 C on the
highest ground), by height, and a cell's quarters differ by 6.6 C. A slope's light spans x2.3 (0.13 to 0.30) by the
way it faces.

**The years.** H4 again read the fixed pattern (e102 did): a year's rain map is mostly the map. Read as departures,
a cell's rain varies 17% between years (the planet's 12%), a year keeps 0.33 of the last one's departure, and 10% of
cell-years get under 80% of their mean. The trend is not a drift: a year's anomaly is now the whole world's, so the
land's mean temperature moves between 15.1 and 17.9 C from year to year and ten years of it have a slope. No storm
came in 30 years (one is due in 70).

**The chemistry holds.** A:B and fertility span more than on the planet (x9 and x68 against x14 and x19); the islands
differ by their rock (the median A:B is 0.04 on three of them, 0.15 on three, 0.32 on two).

**Why 4.5 places and not 15.4.** e102's bands were cut for a planet. Its temperature bands part at 5 and 20 C: this
land has no ground under 5 C (0.02%) and 86% of it between the two. Its moisture bands part the soil's fill in
thirds: the bare soil is full almost everywhere. What is left is the chemistry and the streams. What the land does
differ by is continuous and the count does not see it: 10 C by height, the rain x15, the light x2.3.

## Conclusion

Holds for this one world (seed 1) with nothing living on it.

- **The ground stands on the small world** (H1-H3): every ledger closes, the pass of the air carries out exactly
  what it took up less what it rained, streams reach the sea from every island, and the chemistry parts the land as
  on the planet. It goes into `base/` with its world file.
- **#118 is answered by the scale**: the land rains none of its water back, and the years vary 17%. Runoff is now
  96% and not Earth's 35%, on bare ground; what plants transpire is rung 2's to read.
- **It does not make places by e102's count** (H5: 4.5 against 15.4), and the plan's turn (more land or more
  height, #116) is **not taken**: neither would add what is missing. A cold band needs ground over 2.4 km at this
  latitude, a few per cent of any island; the moisture bands need something that draws the soil down, and on this
  ground only plants can (the drier half of the land under 100 m gets 53-250 mm a year). So whether rain x15, 10 C
  and light x2.3 are places is read at rung 2 (#128), by whether producers sort by them and whether the soil's fill
  then differs; if they do not, the remedies are the climate's (the sea air's share of a cell's temperature, the
  latitude), not the land's size.
- **What could part the lines** (#117's objection): five islands with 2.3 to 32.5 km of sea between them, each with
  its own height (964 to 2,002 m), rain (1,360 to 2,770 mm a year) and rock.
- **Cost**: 13.6 s a year, the air's pass 9.2 s of it on one thread.

`vision.md`: row A. `foundation.md`: the laws of sun, heat and air, rung 1's reading, today's world.
