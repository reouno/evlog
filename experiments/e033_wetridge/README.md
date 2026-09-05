# e033 The wet ridge

Date: 2026-09-05

## Purpose

e032 made the winter a place: the season's amplitude by height, the valley the refuge, the
ridge emptied every autumn and refilled every summer from below. No body holds the ridge
through the winter and no lineage is a place's, because the valley is the best place at every
season but the summer: the ridge has nothing the valley lacks. e020's rain on the mountains
(`rain high`: the air rains on a cell by its height, the bottom of the valley gets none, the
soil runs downhill) turned e019's world upside down - the ridges held 45% of the bodies, the
valleys 20% - and was set aside for the rain on every cell alike from e021 on. Under the
winter by height the two laws together make the places a trade-off: the rain on the ridge
where the sun goes out, the winter sun in the valley where no rain falls. No law is new; the
question is what the bodies do with two places that each lack something.

## Hypothesis

1. **The ridge is worth holding.** With the rain on the ridge its summer is richer than the
   valley's: the ridge's share of the bodies at the summer peak rises over e032's 16-24%, and
   its summer bodies are more its own (born there).
2. **The winter still empties it, but less.** The ridge's midwinter bodies rise over e032's
   17-124 (with its soil the plant stands through the dark for whoever stays), and the valley's
   share at the floor falls below e032's 68-90%.
3. **Two places, two winners.** A lineage that lives on the ridge's soil and one on the
   valley's sun: the ridge's bodies and the valley's differ more than in e032, and more than
   one winner holds through the second half in more seeds than e032's one of three.
4. **The world stands** at e032's floors (673-1,230 at amplitude 2) or above.

## Method

Code: e032 (`experiments/e032_winter`) as `e033_wetridge`, unchanged but for `pop.csv`,
which gets the soil per height band every 1,000 steps (`soil0..2`). `rain` is argument 9
(high or flat, since e020) and `winter` argument 24 (e032). `rain flat` `winter high` is
e032 byte for byte (checked on seed 9 for 20,000 steps at amplitude 2).

**Runs.** Two pilots on seed 9, 100,000 steps (five winters), two threads each: `rain high`
with `winter high` at 2 (the test), and `rain high` with `winter flat` at 0.75 (the rain alone:
the same world sun at midwinter, the winter the same everywhere). The controls are e032's
pilot on seed 9 (`rain flat`, `winter high` 2) and `rain flat` `flat 0.75` on seed 9 run with this
code (e032's world; e032 ran that form only in its batch). Then the batch on seeds 1-3
for 300,000 steps against e032's batch, on the form the pilots pick.

## Result

### The pilots (grow, store 5, seed 9, 100,000 steps, five winters; three runs at two threads, 12 minutes)

From `pop.csv` (all bodies every 1,000 steps) and `places.csv` (per band at the equinoxes,
median of the second half). e032's pilot at `rain flat`, `winter high` 2 is the control.

| run | winter floors, in order | lineages at the floors | valley share at the floors | ridge bodies at the floors, born elsewhere | summer peaks | ridge share at the peaks | biters |
|---|---|---|---|---|---|---|---|
| rain high, winter high 2 | 553, 751, 764, 744, 679 | 3-10 | 70-79% | 36-84; 82-95% | 2,651-4,120 | 17-20% | 2-6% |
| rain flat, winter high 2 (e032) | 542, 819, 825, 680, 695 | 3-13 | 73-85% | 13-56; 80-92% | 2,700-4,192 | 17-19% | 0-5% |
| rain high, flat 0.75 | 683, 1,131, 1,327, 1,280, 1,318 | 3-12 | 32-41% | 163-437; 42-46% | 2,562-4,277 | 15-24% | 1-11% |
| rain flat, flat 0.75 | 568, 1,195, 1,234, 1,275, 1,280 | 2-9 | 33-44% | 93-405; 43-55% | 2,864-4,468 | 13-17% | 4-25% |

Per band (second half): soil, the sun lost for want of soil (`barren`, per step), the rain
fallen there per step, the regrowth per step, and the bodies at the equinoxes.

| run | band | soil | barren | rain | regrowth | bodies |
|---|---|---|---|---|---|---|
| rain high, winter high 2 | valley | 73,700 | 0.8 | 9.7 | 3.0 | 1,046-1,308 |
| | slope | 15,800 | 13.1 | 17.3 | 4.4 | 881-1,122 |
| | ridge | 2,270 | 27.2 | 24.7 | 8.1 | 559-697 |
| rain flat, winter high 2 (e032) | valley | 83,300 | 0.2 | 16.3 | 3.0 | 1,057-1,199 |
| | slope | 14,300 | 12.7 | 16.3 | 4.4 | 917-1,374 |
| | ridge | 360 | 27.6 | 16.3 | 9.8 | 461-580 |
| rain high, flat 0.75 | valley | 72,100 | 0.8 | 9.9 | 3.3 | 913-1,326 |
| | slope | 13,900 | 12.6 | 17.6 | 5.3 | 873-1,236 |
| | ridge | 1,830 | 22.8 | 25.0 | 11.5 | 570-706 |
| rain flat, flat 0.75 | valley | 83,900 | 0.2 | 17.8 | 3.4 | 916-1,361 |
| | slope | 15,700 | 11.8 | 17.8 | 4.7 | 871-1,208 |
| | ridge | 780 | 27.2 | 17.8 | 10.3 | 396-587 |

- **The rain on the mountains changes nothing the bodies notice.** Under the winter by height
  the floors are 553-764 against 542-825, the valley holds 70-79% of them against 73-85%, the
  ridge's winter bodies are 82-95% born below against 80-92%, and the ridge's summer share is
  17-20% against 17-19%. Under the flat winter the same: floors 1,131-1,327 against
  1,195-1,280, the valley a third in both.
- **The ridge's rain runs off before the plant can use it.** The ridge gets 25 of rain per
  step instead of 16 and holds six times the soil (2,270 against 360) - and loses the same
  sun for want of soil: 27.2 per step against 27.6, half of the ridge's sun. The soil moves
  a tenth of the drop per step (`flow` 0.1) where the plant grows a hundredth per step: what
  falls on the ridge is in the valley within a few steps, and the lake is where it was
  (73,700 against 83,300). The valley loses only 0.8 of its sun to bare soil against 0.2.
- **The regrowth per band is the same** (3.0 / 4.4 / 8.1 against 3.0 / 4.4 / 9.8): the ridge
  grows more per step in both worlds because the valley's cells are shaded by the crowd
  standing on them, not because of its soil.
- **Bodies.** The summer world is e032's (2,300-3,100 bodies, side 5-8, mass p50 13-28); the
  bands hold the same body in every run. The flat-rain flat-0.75 run has 4-25% biters, a
  seed's lottery (e032's batch at that world: 0-3%).

## Conclusion

1. **The ridge is worth holding: no.** The ridge's summer share and its own-born share are
   e032's.
2. **The winter empties it less: no.** 36-84 bodies on the ridge at midwinter against 13-56,
   born below in the same share.
3. **Two places, two winners: no.** The bands hold the same body; no batch was run, the pilot
   settles the mechanism (the soil and the barren sun per band are the same in both worlds).
4. **The world stands: yes,** at e032's floors.

Not kept: the rain stays on every cell alike (`flat`). The reason is a law already in the
world: the soil runs downhill ten times faster than the plant grows, so the rain's place is
not the soil's place - the lake is in the valley whatever the sky does, and the ridge is half
barren whatever the rain. For the ridge to be worth something the soil must stay where it
falls (a slower flow, or soil that a standing plant holds - roots), or the ridge must hold
what the valley cannot use (a store in the ground that stands through the dark). Those are
the next laws; the rain's law alone is not a lever on this terrain.
