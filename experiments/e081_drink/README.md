# e081: drinking takes, losing gives back (#94)

Date: 2026-09-19

## Purpose

e080 closed the crown's path to a refuge (#91): the stand is the land's home in every season, and the
crown can only make it a better home. What the land lacks is on the water's side. It is also `balance.md`
section 3's open cycle, open since #87: **a body's water is a state**. Drinking takes nothing from the
ground and what a body loses goes nowhere, so a crowd sits on its water at no cost. Only food limits the
home, and the home makes one winner. This experiment puts the body's water into the land's water
(`balance.md` section 16, agreed 2026-09-19).

## The cycle (written before the runs, `balance.md` section 16)

- **W1. Drinking takes the water it drinks.** A block that drinks takes it from the cell under it, from the
  ground or a pool's standing water, and a body drinks only up to full (its deficit, not the offer).
  *Takes* from the ground under a crowd; *refilled* by the rain and the runoff; *limited* by the crowd
  itself: the drink falls with the ground's fill, and the crowd thins to what its water keeps.
- **W2. What a body loses goes back.** The dry air's and the sweat's water go to the air over the cell; a
  dead body's water and the water of a lost block (a wear, a bite, a part cut loose) go into its cell's
  ground; a child's water (its parent's fill) comes out of the ground under it, and a child on dry ground
  starts with what the ground gives; the start's bodies the same. In the sea the sea gives and takes.
  The air's, the land's and the bodies' water then move only by the sea's exchanges.
- **The unit** (`unit`): mm of its cell's water a block of a body's water is. The anchor is what a
  sub-cell of full ground holds, 150 mm / 16 = 9.4 mm. At 9.4 today's crowd drinks about 11% of a mid
  stand's yearly rain and a third of its winter rain.
- **Kept as they are**: `fresh` 0.05, the dry air, the sweat, the sea that does not quench. No new rate.
- **The balance expected.** A stand's ground falls where its crowd is dense, most in the low-rain winter and
  in late spring; the stand becomes water- and food-limited at once and holds fewer bodies than its rain
  alone would. With the stand's surplus gone the lawn's share of the crowd in autumn rises. Pools and the
  wettest stands are drunk down in the dry season. A place drunk dry pushes its bodies on. More kinds by
  place and season, because the one home no longer feeds an unlimited sitter.

## Hypothesis

At a unit that passes, against the same world at unit 0 (seed 9, both hemispheres, 20-50 degrees, each
hemisphere's own season):

1. **The land stands.** Land bodies at half the control's or more; thirst under 60% of deaths.
2. **The home pays for its crowd.** A mid stand's bodies hold under 0.7 of their water, and the stand over
   the lawn in bodies a cell at the equinoxes falls from the control's.
3. **The lawn in autumn.** The lawn over the stand in bodies a cell in autumn rises above the control's.
4. **The ground under the crowd.** A mid stand's ground fill falls under the control's (the producers
   alone), most in winter and spring.
5. **Stage C's measure** (one seed, indicative): the largest lineage's share falls and kinds kept to a place
   rise.
6. **The ledger closes**: the water of the air, the land and the bodies stays within 1e-9 of what the sea's
   exchanges leave it.

## Method

e080's crate with W1 and W2 behind one rate, `unit` (0: e080 exactly). W1 is `dry_turn_w` (`body.rs`):
the turn's offer is cut to what brings the body to full, then each block takes its share out of its cell's
ground, as much as the ground holds; what the soft faces lose goes to the air over each face's cell. W2 is
`settle`, `give_back` and `water_from_ground` (`main.rs`): each body books the water it holds (`held`,
blocks), and what a lost block held goes into the ground at the body's next turn. The log gains the flows
(`water_drunk`, `water_air`, `water_sweat`, `water_dead`, `water_born`, `water_spill`, mm a step), the
children born short of their parent's fill (`born_dry`), and the ledger's error (`water_err`).

**Runs** (the default world, S1-S3 at 0; seed 9, 60,000 steps, a census every 1,000 steps from 36,000):
unit 0 (the control), 4.7, 9.4 and 28 mm (half, one and three times the anchor).

    (nohup bash experiments/e081_drink/batch.sh search 60000 9 > experiments/e081_drink/results/search.log 2>&1 < /dev/null &)

4 runs on 4 cores of the Mac, one thread each, about 30 minutes. Read with
`uv run python experiments/e081_drink/sweep.py experiments/e081_drink/results/search`. If a unit passes 1-3,
it on seeds 9-11 at 100,000 steps against the control (6 cores, about an hour).

## Result

**The check.** At `unit` 0 a 2,000-step run of seed 9 on e079's world is byte-identical to e080's (log,
censuses, bands, events, lineages; timing aside). Two unit tests: a body drinks out of the ground only up to
full, dries into the air and draws a thin cell to empty with the ledger unmoved; and on a small world with
dry air, heat, `fresh`, the tear and the frail line, the air's, the land's and the bodies' water stays
within 1e-10 of what the sea's exchanges leave it over 3,000 steps while the matter is conserved. In the
runs the ledger's largest error is 1.8e-11. Each run took 25-30 minutes at 60,000 steps (the control 24).

**The search** (seed 9, 60,000 steps, censuses 36,000-60,000; `sweep.py`). Mid is 20-50 degrees, seasons
the hemisphere's own. "Lawn / stand" is bodies a mid lawn cell over a mid stand cell; "home" the stand over
the lawn at the equinoxes (spring and autumn together).

| unit | land bodies | thirst | home | lawn / stand, spring | lawn / stand, autumn | stand body water Sp/S/A/W | stand ground, winter | lawn ground, winter | largest line | kinds / placed | travel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,138 | 48% | 2.79 | 0.29 | 0.41 | 0.78/0.20/0.46/0.89 | 0.87 | 0.37 | 55% | 7.08 / 4.44 | 4.8 |
| 4.7 | 3,690 | 50% | 2.10 | 0.45 | 0.49 | 0.45/0.21/0.28/0.67 | 0.80 | 0.41 | 56% | 7.56 / 4.72 | 2.8 |
| 9.4 | 3,820 | 52% | 2.51 | 0.35 | 0.42 | 0.35/0.17/0.23/0.60 | 0.78 | 0.43 | 67% | 6.88 / 3.20 | 2.2 |
| 28 | 3,909 | 57% | 2.14 | 0.47 | 0.47 | 0.30/0.17/0.17/0.38 | 0.65 | 0.45 | 29% | 5.80 / 4.52 | 2.0 |

The control is e078's control exactly (4,138 land bodies, kinds 7.08 / 4.44). Every unit passed 1 and 2 and,
on this seed, 3 (at 9.4 by 0.01). The mechanism moved the same way at all three, and the lines and kinds did
not move one way, so the anchor 9.4 went to three seeds.

**The ladder** (seeds 9-11, 100,000 steps, censuses 36,000-100,000; `results/ladder`):

| seed | unit | land bodies | thirst | home | lawn / stand, spring | autumn | stand water, spring | largest line | kinds | placed | travel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | 0 | 4,035 | 48% | 2.77 | 0.30 | 0.41 | 0.81 | 58% | 7.45 | 4.75 | 5.8 |
| 9 | 9.4 | 3,782 | 52% | 2.52 | 0.37 | 0.41 | 0.39 | 69% | 7.33 | 3.73 | 3.0 |
| 10 | 0 | 3,640 | 50% | 2.70 | 0.28 | 0.47 | 0.80 | 63% | 8.27 | 4.65 | 4.2 |
| 10 | 9.4 | 3,443 | 52% | 2.60 | 0.41 | 0.37 | 0.38 | 39% | 6.22 | 4.45 | 2.2 |
| 11 | 0 | 3,676 | 46% | 2.91 | 0.27 | 0.41 | 0.79 | 42% | 7.25 | 4.47 | 6.0 |
| 11 | 9.4 | 3,217 | 52% | 2.13 | 0.51 | 0.45 | 0.32 | 61% | 6.94 | 4.24 | 4.2 |

- **The land stands.** 88-95% of the control's land bodies; thirst 52% of deaths (46-50%).
- **The home pays.** A mid stand's bodies hold 0.32-0.39 of their water in spring (0.79-0.81) and 0.50-0.60
  in winter (0.89-0.91). The stand over the lawn falls in every seed, 2.79 to 2.42 on average.
- **The lawn gains in spring, not in autumn.** Its bodies a cell over the stand's rise from 0.28 to 0.43 in
  spring in every seed; in autumn they move 0.43 to 0.41 (down, up, flat).
- **The crowd moves water from the stands to the lawn.** A mid stand's ground in winter falls from 0.88 to
  0.75-0.79; the mid lawn's rises from 0.37 to 0.44-0.45. Bodies drink about 1,700 mm a step over the world
  and sweat about 1,450 of it back into the air, where the wind takes it; the pools fall by 15-23% of their
  cells (0.26% of the land to 0.20-0.23%).
- **Every land body is drier, and goes less far.** The land's bodies hold 0.25-0.30 of their water against
  0.57-0.59: a crowd draws down the ground it stands on, so what the ground gives it falls. Grown bodies end
  2.2-4.2 cells from their birth against 4.2-6.0, walking as much.
- **The measure falls in every seed.** Kinds at a census 7.66 to 6.83 on average, kinds kept to a place 4.62
  to 4.14; the largest line moves -24, +11 and +19 points.
- 7% of the children are born short of their parent's fill (a child of 30 blocks at full needs 280 mm, more
  than a full cell's ground holds).

**The hypotheses:**

1. The land stands: **yes** (88-95% of the bodies, thirst 52%).
2. The home pays for its crowd: **yes** (stand water 0.32-0.39 in spring; home 2.79 to 2.42).
3. The lawn in autumn: **no** (0.43 to 0.41); the lawn gains in spring instead (0.28 to 0.43).
4. The ground under the crowd: **yes** (a stand's winter ground 0.88 to 0.77), and the lawn's rises.
5. Stage C's measure: **no**, it falls in all three seeds (kinds 7.66 to 6.83, placed 4.62 to 4.14).
6. The ledger closes: **yes** (1.8e-11 at most).

## Conclusion

The body's water is now part of the land's, and the cycle does what section 16 drew: a crowd draws down
the ground it stands on, the stand pays for its crowd and holds fewer of the land's bodies against the lawn,
and the lawn gains in spring. It does not make more kinds. Water now binds every land body (they hold half
of what they held) instead of the lawn's alone, and a body that binds on water everywhere goes less far: the
crowd's commute did not come, a tether did. The lawn's good season is spring, when the stand's ground is
drawn down (0.61-0.63 full) and the lawn's is wetter than it was (0.38 against 0.31); in autumn, the
season the design expected, the lawn's ground is at 0.31-0.32 against the stand's 0.57-0.62.

What it changes: W1/W2 are not kept as stage C's default world (the measure falls on three seeds by the
rule set at e072). The code is right physics and stays as the base of the next water step: under it the
land's water is conserved, and the refuge question moves from "a better stand" to "a season in which the
open land has water to drink". Next is a proposal, not agreed (balance.md section 17).

Conditions: c1225, seeds 9-11 at 100,000 steps, `fresh` 0.05 (wet ground gives a twentieth of a pool's
drink), a body's water unit of a sub-cell's full ground, the heat band 15-30 C, a grown body living about
1/20 of a year.
