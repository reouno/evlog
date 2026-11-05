# e115: water in matter - a tissue holds water by its make, a mouthful brings it (#134)

Date: 2026-11-05

## Purpose

In e114's pilot the living are 93% of the food on land and the bodies take 97.8% of their diet from litter, so no
defence is paid for (#133). The plan check of 2026-11-05 (#116) read why from the laws' own arithmetic. Every way to
the living has a price a body cannot pay. Leaves above a body's height are out of reach, and the crowns have nothing
to drink. The ground starves a digger. The dead lie at every body's feet. No mouthful carries water, yet thirst is the first
cause of death on land (44% of the deaths in year 60). The general part missing is that **matter carries no water**.
The design is #134, agreed by the user on 2026-11-05. The crate is e114's, copied; every run has e114's law on
(`lock=1`) and e113's `all` (`road worth reach bite ground crown floor press_work sight cover`, `tear=0`).

## Hypothesis

Written before the runs (#134):

1. **The world stands with it**: plants that hold water in their tissue do not dry the land's soil, and the bodies live.
2. **The living are eaten**: the leaf's share of the bodies' diet rises above e114's (1.3% at the pilot's year 60),
   most where the ground is dry.
3. **Thirst eases**: thirst deaths fall in share against e114's.
4. **The doors open** (pilot): bodies live in the crowns (`body_crown` > 0), and producer locks rise above e114's
   share where the living are eaten.

## Method

One law behind one switch, `water` (0: e114's world), with one constant, `water_ref` = 4 kg of water a kg of dry
tissue that is all working part (a leaf is about 80% water).

- **A tissue holds water by its working part** (`life::hold`): `water_ref * min(1, B share / b_work)` kg a kg of dry
  matter. No organ is named. At e114's makes a leaf holds about 2.2 kg a kg, a root 1.5, wood 0.3 and a store 0.13.
- **The plants draw it** (`Life::pw`, a cell's store): each step the living tissue of a cell is filled to what it
  holds, from the ground and then the groundwater, as fast as its roots draw (`root_draw`, shallow and deep roots as
  for transpiration). What the tissue no longer holds (shed, burnt, eaten by the small eaters, dead) goes to the
  ground. The water ledger counts it.
- **A mouthful brings its water**: of a living tissue, its own share of the cell's store (as full as the plants keep
  it); of litter, what its make holds at the ground's wetness, out of the ground. A body keeps what it can hold (its
  target, as when it drinks) and the rest goes to the ground. At sea nothing changes.

**Decided while building, against the plan check's text** (noted on #134): the plan check gave each litter slot its own
water, drying to the air, and made the rot follow it. Here litter's water is the ground's wetness times its make, with
no store of its own, and the rot still follows the soil's fill. In balance the two are the same, and one store a slot
would be a second water ledger for that lag alone. A cell's plants share one store. Their tissue fills and empties
together, which leaves out a plant that keeps water through a drought while its neighbour dries. Carrion and the seed
bank bring no water (0.5% and 0% of the diet in e114).

**Gate**, on e111's trial world (16 km, 128 cells, bodies sown in year 15; `gate.sh`), Ubuntu, two threads each,
three runs at once, under an hour, under 6 core-hours:

| run | arguments on top of e114's `lock=1` | asks |
|---|---|---|
| `off` | `water=0`, to year 40 | is it e114's gate `worn` to the digit (every log column but timing and e115's own) |
| `water` | `water=1`, to year 40 | does the world stand, does water come in food |
| `water80` | `water=1`, to year 80 | the diet and thirst, given time |

**Passed if** `off` is e114's `worn` to the digit; ledgers under 1e-9; with `water` the land at year 30 is at least
half of e112's `nobody` and bodies live at year 40. Then the thirsty are read by place (where they die, by the
ground's wetness): if they do not die where it is dry (the drink rate, not dry ground), the piece opens only the crown,
and that is written here before the pilot.

**Read by place** (`_wet.csv`, a reading, no law): on land, a year's animal-days, thirst deaths, leaf, litter and all
food eaten, water in food and water drunk, by the ground's wetness where the body is, in tenths of full.

**Stop early if:**

- `bodies` < 10 at 190080
- `food_water` < 1e-12 at 237600

For the gate (bodies sown in year 15; the steps are the ends of years 16 and 20, at 11,880 steps a year).

## Result

### The gate: passed

Ubuntu, 2026-11-05, under an hour (`gate.py`; `results/gate.csv`, `results/gate_wet.csv`). Ledgers 3.5e-13 at most.

- **`off` is e114's `worn` to the digit**: 109 columns, 40 years, none differ to the digits e114 printed (its four lock
  columns had four places then; the crate prints them in full since).
- **The world stands, with more bodies**: with `water` the land at year 30 is 0.98 of e112's `nobody` (`off` 0.97),
  and 2,878 bodies live at year 40 against `off`'s 834. In `water80` they reach 9,832 at year 80 while the land falls
  from 0.94 (year 50) to 0.73; e114 has no run of its final law to year 80 on this world to set it against.
- **Water comes in food**, 56-75% of what the bodies take in years 25-40 and 19-25% in years 60-80. The diet is still
  99% litter; the leaf is 0.15-0.33% of it (`off` 0.08-0.20%).

By the ground's wetness where the body is (years 21-40 for `water`, 21-80 for `water80`):

| ground's fill | of the animal-days | of the thirst deaths | leaf of what is eaten | food of the water taken in |
|---|---|---|---|---|
| 0-0.1 | 1.5% / 1.2% | 100% / 99% | 0.15% / 0.14% | 1.2% / 0.7% |
| 0.4-0.5 | 0.5% / 0.7% | 0 / 0 | 0.35% / 0.23% | 18% / 6% |
| 0.8-0.9 | 8.9% / 5.4% | 0 / 0 | 0.92% / 0.46% | 46% / 18% |
| 0.9-1 | 85% / 87% | 0 / 0.9% | 0.56% / 0.51% | 72% / 32% |

- **The thirsty die where it is dry**: all but 1% of the thirst deaths are on ground under a tenth full, where 1-2% of
  the animal-days are spent. So, by the rule stated before, the piece is not one for the crown alone.
- **But food brings water where it is wet, not where it is dry**: a litter's water is its make times the ground's
  wetness, so on dry ground it is dry, and the living leaf there is no larger a part of the diet than on wet ground.
  Most bodies live on the wettest ground, where food is the cheaper drink; that is what lets more of them live.

The gate's `wet` column was printed to one decimal, so two bins share a label; `gate.py` takes the bin from the row's
place in its year, and the crate now prints two decimals. `animal_days` is in animals a m2 times years.

### The pilot, written before its run

Plan check's pilot was e114's pilot to year 100. Its control with e114's final law exists only to year 60 (the seeds,
`lock_l2` and `lock_l3`; seed 1 died in the bottleneck), so the pilot is those two: `pilot.sh water_l2 lock=1 water=1
life=2 years=60 threads=3` and the same with `life=3`, Ubuntu, two at once, about 2 hours (6 cores x 2 h). Control:
e114's `lock_l2` and `lock_l3`, the same machine.

- **The world stands**: land at year 60 at least half of the control's, and bodies alive at year 60.
- **Hypothesis 2**: the leaf's share of the diet at year 60 above the control's (1.26% and 0.53%), and higher on dry
  ground than on the wettest (`_wet.csv`, years 45-60).
- **Hypothesis 3**: thirst's share of the deaths at year 60 below the control's (44% and 24%).
- **Hypothesis 4**: `body_crown` above 0 in some year; `p_locked` above the control's at year 60 (4.3e-6 and 2.0e-6).

**Stop early if:**

- `bodies` < 10 at 498960
- `food_water` < 1e-12 at 498960

(sown in year 40; the step is the end of year 41.)

### The pilot: thirst eases, the living are not eaten more

Ubuntu, 2026-11-05, about 2 hours, both to year 60 (`pilot.py`; `results/pilot.csv`, `results/pilot_wet.csv`).
Ledgers 5.5e-12 at most. `analysis/audit.py` does not read this crate's output (as in e113-e114). Against e114's seeds:

| life seed | run | bodies, year 45 / 50 / 60 | land, year 60 | leaf of the diet, 60 | thirst of the deaths, 60 | food of the water, 60 | producers' locked share, 60 |
|---|---|---|---|---|---|---|---|
| 2 | e114 `lock_l2` | 7,967 / 7,299 / 7,786 | 0.96 | 1.26% | 44% | 0 | 4.3e-6 |
| 2 | `water_l2` | 7,412 / 8,080 / 9,393 | 1.03 | 1.02% | 36% | 15% | 3e-12 |
| 3 | e114 `lock_l3` | 2,004 / 3,717 / 5,911 | 1.20 | 0.53% | 24% | 0 | 2.0e-6 |
| 3 | `water_l3` | 329 / 4,572 / 4,441 | 1.24 | 0.49% | 4% | 39% | 7e-9 |

- **The world stands**: yes, in both, with more land than the control and 1.2x and 0.75x its bodies.
- **Hypothesis 2, the living are eaten: no.** The leaf's share at year 60 is under the control's in both seeds
  (1.02% against 1.26%, 0.49% against 0.53%). By place (years 46-60) it is a little higher on the driest tenth than on
  the wettest (1.57% against 1.11% in seed 2, 0.89% against 0.77% in seed 3); e114 wrote no reading by place to
  compare with.
- **Hypothesis 3, thirst eases: yes**, 36% against 44% and 4% against 24% of the deaths at year 60. In seed 3 the
  control's share swings between 7% and 24% from year 45 to 60, so one year is a weak reading there.
- **Hypothesis 4, the doors open: no.** No body lives in the crowns (`body_crown` 0 in every year), and the producers'
  locked share is 1,000 times or more under the control's.

By place, the thirsty still die where it is dry in seed 2 (95% of the thirst deaths on the driest tenth, 2.1% of the
animal-days), where food brings 2% of the water taken in (27% on the wettest). In seed 3, where thirst is rare, 76% of
its deaths are on the wettest tenth, where 88% of the animal-days are: a crowd's drink rate, not dry ground.

## Conclusion

Under this world's conditions (isles1 and the trial world, two life seeds to year 60, one run to year 80):

1. **The world stands with it: yes.** Plants that hold water in their tissue leave the land as it was (1.03 and 1.24
   against 0.96 and 1.20), and the bodies live.
2. **The living are eaten: no.** Water makes every mouthful also a drink, but most of what is drunk this way comes
   where it is wet: a litter's water follows the ground's wetness, and 87-88% of the bodies' time is on the wettest
   tenth. On dry ground, where the thirsty die, the leaf is 1-1.6% of what is eaten, too little to bring water.
3. **Thirst eases: yes**, in both seeds; food brings 15-39% of the water at year 60.
4. **The doors open: no.** No body enters the crowns, and locks hold less than in e114.

The finding: water in matter prices food on a second axis, as designed, but the axis does not reach the doors. The
living stay behind height and the crown. A body reaches 14% of the leaves (#116, plan check), and none climbs to
where the rest are. Water was the price a climber could not pay in e112; no body went up here to find out whether
it can pay it now. The next gap is the door itself: height as a continuous axis around a plant, set aside in the plan
check.

Kept in the crate, on (`water=1`): it is a property of matter and harms nothing read here. Like e110-e114, nothing
goes to `base/` (it holds the world without bodies, e109). Rows changed in `vision.md`: B water in matter, F food
web, the lessons and the direction.
