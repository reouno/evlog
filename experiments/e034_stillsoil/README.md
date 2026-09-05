# e034 The soil barely moves

Date: 2026-09-05

## Purpose

What runs downhill in the real world is water, not soil. The soil is roughly uniform, and where
it is rich follows where the animals and plants die and defecate; a little of it leaches with
the water, but that is not the main cycle. e019's law moves the nutrient stock itself, a tenth
of the drop per step (`flow` 0.1), 10-100 times what any plant can use (e019: 0.01, 0.1 and 1
gave the same world). The lake in the valley, the barren ridge, and e033's negative (the rain
on the ridge runs off before the plant can use it) are all products of that shortcut. e018
(flow 0, no terrain) fell because the soil bound where bodies died: trails one cell wide,
51-72% of the cells bare, the food eaten falling every year. Since then the world has the
crowd, the net (the world eats its dead), the store, and a winter that moves the bodies as a
wave across the terrain twice a year. This experiment replaces the shortcut by the honest
version of the premise, the soil barely moves, and asks again whether the rain's place can be
the soil's place (issue #35). It comes before #29 (water as the carrier) so that #29 is
designed from what a still soil does.

## Hypothesis

1. **The fall does not return.** With the soil still (`flow` 0) the world stands at e032's
   floors (673-1,230 at the batch, 542-825 on the pilot seed): the bodies move with the
   season and lay their dead where they live, so the soil does not bind to trails as in e018.
   The measures of the fall (the sun lost for want of soil, `barren`, rising year on year; the
   food eaten falling) stay flat.
2. **The lake is the bodies' now.** Without the flow the soil lies where the bodies die: the
   valley still holds most of it (it is the winter refuge, most deaths are there), but the
   ridge holds thousands instead of e033's 360, and the ridge's barren sun falls below e033's
   27 a step (half the ridge's sun).
3. **A tiny flow (0.001) is a still soil.** The world and the soil per band are the flow-0
   world's, not e033's: the lake does not re-form.
4. **The ridge's rain is the ridge's soil.** With `rain high` under the still soil the ridge
   holds more soil than the valley (its rain is 25 a step against the valley's 10) and loses
   less sun than the valley for want of it; the ridge's summer share rises over e033's
   17-20%, and the winter still empties it (the dark is the dark).

## Method

Code: e033 (`experiments/e033_wetridge`) as `e034_stillsoil`, unchanged (only the results path).
The flow rate is argument 8 (`flow`, a share of a cell's soil per step, 0.1 since e019, capped
at an eighth of the drop); `rain` is argument 9 (`flat`: on every cell alike; `high`: by
height, e020) and `winter` argument 24 (`high` at 2: e032's season world). `flow` 0.1 `rain flat`
is e033's control byte for byte.

**Runs.** Five pilots on seed 9, 100,000 steps (five winters), one thread each, at once on the
Mac (5 cores, about 20 minutes): `flow` 0, 0.001 and 0.0001 with `rain flat` (the still soil, the
leaching soil, and the bracket between them), and `flow` 0 and 0.001 with `rain high` (the
rain's place under a still soil: e033's question for real). The controls are e033's pilots on
seed 9 (`flow` 0.1 with `rain flat` and `rain high`). A batch on seeds 1-3 only if a pilot says
yes and the question needs it (the mechanism is a matter of the soil per band, which a pilot
settles).

**Measures.** `pop.csv` every 1,000 steps: the bodies per band, the ones born elsewhere, the soil
per band (the winter floors, the valley's share, the ridge's refilling). `places.csv` at the
equinoxes: the soil, the sun lost for want of soil (`barren`), the rain, the regrowth per band.
`log.csv`: the food eaten, the soil cells (cells with a step of sun's worth of soil), the
matter. The winners from `lineages.csv`.

## Result

### The pilots (seed 9, 100,000 steps, five winters; five runs at one thread each, 17 minutes)

From `pop.csv` (every 1,000 steps), `places.csv` (per band at the equinoxes, second half),
`log.csv` (second half) and the last `soil.jsonl` frame. The controls are the flow-0.1 pilots
of e032 (`rain flat`) and e033 (`rain high`).

| flow, rain | winter floors, in order | lineages of 5+ at the floors | valley share at the floors | summer peaks | ridge share at the peaks | eaten per step | sun lost for want of soil, per step | soil / fat in bodies |
|---|---|---|---|---|---|---|---|---|
| 0, flat | 178, 368, 239, 242, 246 | 0-4 | 43-59% | 1,656-2,526 | 31-35% | 32 | 101 | 128,600 / 7,300 |
| 0.0001, flat | 314, 361, 462, 349, 326 | 1-6 | 46-69% | 1,307-3,283 | 32-36% | 44 | 85 | 123,100 / 12,000 |
| 0.001, flat | 428, 642, 670, 575, 495 | 1-6 | 63-69% | 1,723-2,476 | 30-34% | 38 | 96 | 124,700 / 10,900 |
| 0.1, flat (e032) | 542, 819, 825, 680, 695 | 3-13 | 73-85% | 2,700-4,192 | 17-32% | 67 | 39 | 90,500 / 38,500 |
| 0, high | 54, 80, 38, 22, 24 | 1-3 | 21-61% | 1,496-2,416 | 32-56% | 28 | 104 | 126,800 / 9,200 |
| 0.001, high | 164, 311, 293, 350, 313 | 1-4 | 48-56% | 1,572-2,525 | 32-38% | 30 | 104 | 129,200 / 6,300 |
| 0.1, high (e033) | 553, 751, 764, 744, 679 | 3-10 | 70-79% | 2,651-4,120 | 17-30% | 67 | 37 | 91,100 / 37,400 |

The world's sun is 164 per step on average (0.01 per cell). Where the soil is, per band, at the
end (step 100,000): the soil, the share of the band's cells with less than a step of sun's
worth of soil (0.01, `bare`), the share of the band's soil in its richest tenth of cells (`top
10%`); and at the equinoxes of the second half the sun lost for want of soil per step
(`barren`), the rain per step, the bodies.

| flow, rain | band | soil | bare cells | top 10% holds | barren | rain | bodies |
|---|---|---|---|---|---|---|---|
| 0, flat | valley | 18,300 | 41% | 61% | 33.6 | 10.3 | 326-461 |
| | slope | 52,200 | 9% | 38% | 41.1 | 10.3 | 357-496 |
| | ridge | 61,000 | 7% | 34% | 40.2 | 10.3 | 372-535 |
| 0.0001, flat | valley | 4,500 | 56% | 80% | 27.8 | 14.2 | 428-819 |
| | slope | 50,800 | 13% | 23% | 34.1 | 14.2 | 515-986 |
| | ridge | 71,900 | 3% | 17% | 34.7 | 14.2 | 542-970 |
| 0.001, flat | valley | 65,700 | 0% | 16% | 35.3 | 12.6 | 474-567 |
| | slope | 42,000 | 1% | 17% | 39.2 | 12.6 | 441-534 |
| | ridge | 16,600 | 16% | 26% | 34.1 | 12.6 | 384-571 |
| 0.1, flat (e032) | valley | 82,700 | 0% | 18% | 0.2 | 16.3 | 1,057-1,199 |
| | slope | 14,000 | 6% | 31% | 12.7 | 16.3 | 917-1,374 |
| | ridge | 300 | 44% | 46% | 27.6 | 16.3 | 461-580 |
| 0, high | valley | 20 | 93% | 100% | 42.0 | 5.5 | 178-299 |
| | slope | 11,800 | 51% | 78% | 37.5 | 9.7 | 216-497 |
| | ridge | 104,400 | 5% | 39% | 38.8 | 13.8 | 369-735 |
| 0.001, high | valley | 13,800 | 55% | 54% | 38.0 | 5.7 | 299-389 |
| | slope | 56,000 | 3% | 17% | 41.1 | 10.2 | 359-590 |
| | ridge | 59,700 | 0% | 17% | 37.5 | 14.6 | 495-663 |
| 0.1, high (e033) | valley | 78,900 | 0% | 18% | 0.8 | 9.7 | 1,046-1,308 |
| | slope | 18,100 | 3% | 29% | 13.1 | 17.3 | 881-1,122 |
| | ridge | 2,000 | 12% | 47% | 27.2 | 24.7 | 559-697 |

- **The soil climbs.** Without the flow the soil leaves the valley and piles on the slope and the
  ridge: 18,300 / 52,200 / 61,000 at flow 0 against the control's 82,700 / 14,000 / 300, and
  4,500 / 50,800 / 71,900 at 0.0001. The valley, the winter refuge, is 41-56% bare cells at the
  end, and its soil is heaped (the richest tenth of its cells hold 61-80% of it); the ridge's
  soil is even (median 8-14 per cell, 3-7% bare). The road is the air: the crowd eats in the
  valley, breathes, and the air rains on every cell alike (10-14 per step over the world, a
  third of it on the valley); the soil comes back down only by the flow. Where nothing eats
  (the ridge: dark in winter, its plants full at the cap in summer) the rain and the dead pile up.
- **The world stands at half, and the refuge starves.** Floors 178-368 at flow 0 and 314-462 at
  0.0001 against 542-825; peaks 1,300-3,300 against 2,700-4,200; the world eats 32-44 per step
  against 67 and loses 85-101 of the sun's 164 for want of soil against 39. The matter sits in
  the soil (123,000-129,000 of 140,000; the control 90,500), not in the bodies (fat 7,000-12,000
  against 38,500). The food eaten drifts down over the five years at flow 0 (56, 42, 39, 49, 37
  per step in the summers). e018's fall, in a milder form: the soil binds where the bodies do
  not eat, and the rain alone (0.0006-0.0009 per cell per step) cannot feed a valley cell that
  the crowd strips at 0.01.
- **0.001 is not a still soil.** A cell of 8 soil gives 0.008 a step at that rate, the plant's
  own order; the lake re-forms (65,700 in the valley, 0% bare) and the ridge keeps 16,600
  (e032's 300). The floors are 428-670, 80% of the control's, the peaks 60%: the soil that stays
  on the slope and the ridge (58,600 against 14,300) is idle matter. The ridge's summer share
  is 30-34% against 17-19%: the bodies use the ridge's soil when it is there.
- **The rain's place is the soil's place under a still soil, and it kills the valley.** `rain
  high` at flow 0 puts 104,400 of the 131,000 of soil on the ridge (the valley 20, 93% bare)
  and the world is a lottery of 22-80 bodies each winter: the refuge has no soil, the ridge
  has no winter sun. At 0.001 the valley gets 13,800 back and the floors are 164-350.
- **The ridge is used more, held no more.** The ridge's summer share is 31-38% in every still
  world (17-19% at flow 0.1), and its winter bodies are born below in the same share
  (81-98%). The bodies are the same in every world: a light sitting gut (mass 9-11, side 6-10)
  and a dense 4x4 mover with 7-17 muscle eating 50-82% flesh.

## Conclusion

1. **The fall does not return: partly.** No world dies (but `rain high` at flow 0 is a lottery),
   and the soil does not bind to trails: it binds to the high ground, where nothing eats. The
   world stands at half the bodies, with 52-63% of the sun lost for want of soil.
2. **The lake is the bodies': no.** The soil goes where the bodies are not. The dead do not lie
   (the world eats them, e024): the matter returns through the air, and the air rains alike on
   every cell, so a still soil ends up uniform where nothing eats and stripped where the crowd
   eats. The lake in the valley was the flow's and the valley's crowd needs it.
3. **A tiny flow is a still soil: no.** 0.0001 is; 0.001 is the plant's own rate and re-forms
   the lake at 80% of the control's floors.
4. **The ridge's rain is the ridge's soil: yes, and it is worth nothing.** The soil where the
   sun is out in winter and the plants are full in summer is idle; the valley starves without it.

Not kept: the flow stays 0.1 (the default). What the pilots settle for #29 (water as the
carrier): the return road in this world is the air, not the ground (the dead are eaten), and
the carrier's job is to bring the matter back to the sunlit crowd; the rate that matters is
the plant's, 0.01 per cell per step (flow 0.001 of a lake cell), a hundredth of what the flow
does now. A water that flows downhill and carries the soil at that order keeps the lake and
leaves the ridge a soil the bodies use in summer (30-34% of them); the ridge is worth holding
through the winter only when a body can live there on what its soil holds, which is a store in
the ground (roots, seeds, wood) or a body's own store larger than e030's. The batch was not run:
no still world stands at the control's floors, and the mechanism (where the soil goes) is a
matter of the ledger, not of the seed.
