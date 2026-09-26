# e102: the ground of the island - rock, rivers, nutrients and years that differ (#116, rung 1)

Date: 2026-09-26

## Purpose

The first rung of the redesign (#116). The new world gives every form a price in chemistry and every place a
different supply, so its ground must differ by more than temperature and water: by **rock**, by the **nutrients**
the rock gives and the water takes away, by **rivers** that carry them, and by **years that are not the same year
again**. This rung builds that ground with nothing living on it and asks whether it stands. It is also the first
code of `base/`, written fresh; the sun, heat and air are e061's, ported.

## The cycles (written before the run)

- **Water.** The air takes it up from the sea and the wet ground and rains it where it cools (e061). New: the soil
  holds what its **rock and depth** allow (thin on slopes, deep in valleys); what is left over stands, sinks slowly
  into **groundwater**, or runs down a **drainage network** (every land cell drains along a path to the sea, found
  once from the terrain; depressions are lakes that must fill before they spill). Groundwater seeps back into the
  rivers, so they run between rains. *Takes* from the air; *refilled* by the sea's evaporation; *limited* by the
  sea taking back what the rivers bring. Balance: wet uplands, rivers that grow downstream, lakes in basins, dry
  interiors where the air arrives empty.
- **Nutrients A and B.** Each rock province gives A and B at its own rates, faster when warm and wet
  (weathering). Water leaving a cell takes some of each - A is mobile, B is not (leaching) - and the rivers carry
  them down, dropping part where the land is flat and most in lakes (deposition), the rest into the sea, where they
  spread and are buried slowly. *Takes* from the rock; *refilled* by weathering; *limited* by leaching, which grows
  with the water that passes. Balance: a soil's A:B is set by its rock and how much water crosses it - wet uplands
  lose A and are poor, dry places keep it, floodplains and deltas are rich, coasts at river mouths are rich seas.
- **Winds by latitude.** Easterlies under 25 degrees, westerlies from 35 to 55, polar easterlies beyond 65, the
  bands following the sun with the season, and the air mixing a little across its edges. Rain shadows then fall
  on different sides of a range at different latitudes.
- **Years that differ.** Each year draws a new field of temperature and rain anomaly (smooth, 128 cells across),
  keeping half of last year's; within the year the world moves toward it. Droughts are runs of dry anomaly, not a
  law. **Storms** (12 a year, 10 cells across, 3 updates) multiply the rain where they pass, and the rivers carry
  the flood. *Limited* by the vapor: a storm rains only what the air holds.

## Hypothesis

On c1225's terrain and climate (e061), with every new rate at a value set from its units, not searched:

1. **The ledgers close**: water (air + soil + groundwater, the sea as the open edge) and each nutrient
   (soil + sea, against weathering in and burial out), to 1e-9 of the totals.
2. **Rivers reach the sea**: at least 1% of the land carries a mean discharge of 100 mm an update or more, and the
   land's water (soil, lakes, groundwater) is steady over the last 10 years (a drift under 1% a year), so what the
   rivers bring to the sea is what the land sheds. *(Rewritten before any result was read: the first wording,
   "90% of the water leaving the land as runoff", had no measure - water leaves the land by the air as well.)*
3. **The ground differs by chemistry**: across the land the soil's A:B spans at least a factor of 4 between the
   10th and 90th percentile, and the fertility (A + B) at least a factor of 4.
4. **Years differ without drifting**: consecutive years' land rain maps correlate between 0.2 and 0.95, and the
   land's mean temperature over the last 10 years has no trend larger than 0.1 C a year.
5. **More places**: counted by bands of medium, temperature, moisture, A:B and fertility, the effective number of
   places (Hill number of order 1 over their areas) is larger than the same count without the chemistry bands, which
   is today's classification.

## Method

`base/` (the new world's code), copied into this folder as the rule is (`CLAUDE.md`). One world: c1225's
parameters (`base/worlds/c1225.params`), 30 years, the last 10 read. `measure.py` reads the annual maps.

    cargo run --release -p e102_ground -- experiments/e102_ground/results/c1225 base/worlds/c1225.params

**Set in the pilot, by their units, before the run** (four 2-4-year trials, `results/` not kept): with e061's
laws as ported, 97-99% of the rain on the land went back to the air and 13-31 mm a year reached the sea. Four
changes, none searched:

- `wind` 0.1 -> 1: a cell is about 63 km (0.57 degrees) and an update about 3.2 hours, so e061's wind was about
  0.5 m/s; 1 cell an update is 5.5 m/s, a mean surface wind. (0.5 and 2 were tried to see the direction: runoff
  96 and 253 mm a year at year 4.)
- `soil_evap` 0.3: a soil gives up less than open water; water standing on it gives up as open water does.
- `beta` 2: the share of a rain that runs straight off is the soil's fill squared (a cell is not one bucket).
- `lake_depth` 2 m: a pit of the noise terrain (7% of the land, median 13 m deep) is filled to 2 m under its spill
  level, as sediment fills real ones; without it the rivers ended in sinks that never spilled.

What stays: the land still rains mostly its own water back (the day heats the ground, the night rains on it), so
the runoff ratio is low; the climate's own rain law is e061's and is not changed here.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `a_err` > 1e-6 at 23760

(steps: two years; the log has a row a year.)

**Cost.** One world at 512, one core: e061 took 1-8 minutes for 20 years; this adds a routing pass and two
nutrients, so about 5-15 minutes. A few more worlds (terrain seeds) only if the first is unclear.

## Result

One world (c1225), 30 years in 407 s on one core (13-14 s a year); the last 10 read by `measure.py`
(`results/measure.csv`, thresholds in `results/provenance.csv`).

| | reading | line | verdict |
|---|---|---|---|
| H1 ledgers | water 4e-14, A 4e-14, B 8e-14 (worst year) | 1e-9 | **yes** |
| H2 rivers | 0.14% of the land carries 100 mm an update (0.47% at 50, 1.7% at 20); the land's water drifts -0.4% a year | 1%; 1% a year | **no** (the rivers are there, small) |
| H3 chemistry | A:B spans x14 (p10 0.04, p90 0.52), A + B spans x19 | x4, x4 | **yes** |
| H4 years | consecutive years' rain maps correlate 0.98; land temperature trend -0.02 C a year | 0.2-0.95; 0.1 | **no** as written |
| H5 places | 15.9 effective places against 10.9 by e061's bands on the same world; on the land alone 15.4 against 6.4 | more | **yes** |

**The water.** 1,948 mm a year rains on the land and 189 mm reaches the sea: a runoff ratio of 10%, against about
35% on Earth. The rest goes back to the air, mostly on the day it fell (the ground heats by day and the night rains
on it). So the rivers are real - a network that grows downstream to the coasts, 366-408 lakes - but thin: 1.7% of
the land carries 20 mm an update. H2's line was set for a wetter land.

**The years.** H4 read the wrong thing: a year's rain map is mostly the fixed pattern (74 to 2,800 mm across the
land), so any two years correlate near 1. Read as departures from the mean, a year keeps 0.46 of the last one's
(the law's 0.5), a cell's rain varies 12% between years, and 10% of cell-years get under 80% of their mean. The
years differ, at about half of Earth's 15-30%.

**The chemistry is the largest change.** Rock sets the supply and water sets the loss (medians of the last year's
soil): A:B is 0.40 on the granite-like rock and 0.05 on the basalt- and limestone-like, and A + B is 4.1 on the
shale-like and 0.5 on the sandstone-like; land that gets under 300 mm of rain keeps its mobile A (A:B 0.52) where
land over 1,000 mm loses it (0.09-0.13); what the rivers drop gathers where they slow - A + B is 12.0 in the filled
basins against 1.7 elsewhere, 7.0 on flat land against 1.1 on steep. On the land alone the ground holds 2.4 times as
many places once A:B and fertility are read. A is still gathering at 1.4% a year at year 30 (the soils are not at
their balance yet).

## Conclusion

**The ground stands and its new freedom is used**: the ledgers close, the chemistry parts the land by rock and
water into 2.4 times as many places, and years differ by persistent, place-by-place anomalies. It is kept as
`base/`'s first rung.

Two things it does not yet give, carried to the next rungs rather than tuned now:

- **Thin rivers.** The climate's rain law recycles most of the land's rain within a day (runoff 10%). Producers
  will change the land's water (they transpire and shade), so the water cycle is read again at rung 2 before any
  rate is changed.
- **Mild years.** Rain varies 12% between years; `var_rain` 0.3 was set without a target, and Earth's is larger.

`vision.md`: layer A's row (rock, chemistry, rivers, years that differ) and section 5's next rung.
