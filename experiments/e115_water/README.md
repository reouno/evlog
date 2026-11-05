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

## Conclusion
