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

To come.

## Conclusion

To come.
