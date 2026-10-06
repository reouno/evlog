# e110: bodies in metres and seconds, and bodies that meet (#123)

Date: 2026-10-06

## Purpose

The largest gaps in `vision.md` are the bodies' (rows C to F), and the bodies had not moved since e106: its step 1
lives on the planet, written in cells and updates, and e107 showed what that costs on a small world - walkers that
overshoot, sitters that never spread, and eaters that strip a land they cross in a season with nothing to hold them.
This is rung 3 as one piece on the islands (`base/`, e108-e109): step 1 rewritten so that no law reads a cell or an
update, with step 2, **bodies that meet**, read from positions, speeds and forms. It is the food web the vision asks
for and the brake on the eaters. The design, its cycles and the calls made are #123's comment of 2026-10-06.

This experiment is the pilot: does that world stand, do meetings happen, what does it cost, and how long may the
step of integration be. No law is judged (decision rule 6: the rung is judged whole after its run).

## The design in short

- **In metres and seconds** (`src/body.rs`): a body has a place and a heading; it senses within a reach (its eyes'
  side x the light, at least its own length, at most 500 m): what is at its place, which way food, carrion and water
  rise and the ground falls, and the nearest 8 bodies. Its controller gives a weight to each of those ways and to
  its last heading; with a unit of chance their sum is its heading. It walks `speed x activity x time`, eats where
  the update ends with its mouth swept over the path, and pays by the second. With no genes it wanders at a tenth of
  its speed.
- **The grain**: a body holds about `big_s` kg of animals at any age. A sown body stands for the whole animals
  nearest to `big_s`; a body carries its clutch until its animals' clutches together hold a tenth of `big_s`, and
  the clutch hatches as one brood at its parent's place; a body over 2 `big_s` parts in two that start at one place.
- **Bodies meet** (one law, no chance drawn): a second evaluator gives each body seen a pull and a press, from six
  readings (one, its size against mine, alike, my fat, how near, whether it is coming). If the strongest pull of all
  is a body's, the body heads straight for it or straight away. A chaser follows the other through the update and
  arrives after `gap (v + u cos a) / (v^2 - u^2)` (pure pursuit), `gap / (v + u)` when each heads for the other.
  On contact the catcher's front puts its mouth's pressure on the face geometry gives (front, back or a side),
  against that face's strength - the leaf's law. Where pressure passes strength, tissue fails at
  `power / strength` m3 a second for the time they stay together: the rest of the update if the pressed is slower
  or held and the presser's front holds, else the time to pass a body length. A tip harder than the catcher's front
  returns the force over its own area. Glue on the front anchors the other, or lets the catcher ride it; in water it
  cuts the held body's breath. The compound in the tissue at a failed contact, on both sides, enters the other body
  and harms by keys. Failed tissue comes off as whole animals while a body stands for more than one.
- **Carrion**: all failed tissue and every dead body lie in a pool of their cell, rotting into the litter at 0.2 a
  day; flesh is eaten as carrion by whoever stands there, and what was killed is counted apart.

## The cycles (written before the run)

| cycle | takes from | refilled by | limited by | should settle into |
|---|---|---|---|---|
| producers -> grazers | leaf, seed, wood, litter under the mouth along the path | growth, the seed bank | toughness, keys, height; the grazer's time (an update spent fleeing is not spent eating); hunters where grazers are thick | grazers below what food alone carries, the land greener than e106's 0.46 kg a m2 |
| grazers -> hunters | the animals a front can catch and break | births | eyes, speed, a tip and muscle behind it, against the prey's speed, hard faces, tips, compounds and size; the gut passes 0.5% of a body's mass an update, so a kill is shared or rots; hunters starve and are flesh themselves | hunters a tenth or less of their prey by weight, both swinging, out of step between islands |
| the dead -> scavengers, rot | the carrion of a cell | every death, every kill's leavings | rot within days, finding it | scavenging beside hunters and after a crash |
| water | wet ground | rain | the reach of a walk | 90% of this land's soil is full: thirst may bind nowhere |

## Hypothesis

For the pilot (`isles1`, life seed 1, bodies sown in year 40, to year 70), fixed before the runs:

1. **Ledgers** close (water, A, B, the living's matter with the carrion) to 1e-9.
2. **The world stands**: bodies are alive in year 70, and producers still hold >= 50% of the land.
3. **Meetings happen**: catches, failed faces and animals killed in every year after the sowing; flesh (carrion and
   kills) is eaten. How much is reported, not judged.
4. **The grain holds**: a body holds 0.2-2 `big_s` of matter in the mean, so the number of bodies follows the
   animals' weight.
5. **The update may be lengthened**: at `body_tick` 3 and 10 the last ten years' bodies' matter, what they eat of the
   producers' fixing, and the flesh in the diet stay within a factor 1.5 of `body_tick` 1, and the first cause of
   death is the same. The longest that holds is kept.

Read and reported, as #116's turn points: the land's biomass against e109's (the same world without bodies: 1.25 kg
a m2 in year 40, 1.80 in year 70), and founders' lines by island.

## Method

`base/` copied (`e110_meet`); `src/form.rs` (what a genome develops into; e106's, with the three faces and the
compound) and `src/body.rs` are new, `src/view.rs` is e106's, `main.rs` sows the bodies, updates them every
`body_tick` steps inside a climate update, and adds them and the carrion to the ledgers, the log, a census
(`_bodies.csv`, a row a body genotype a year) and `_lines.csv` (a row a founder's line on an island a year).

    cargo run --release -p e110_meet -- <prefix> base/worlds/isles1.params [key=value ...]

New rates, each from its units and none searched: `carrion_rot` 0.2 a day (a carcass lasts days), `glue_stress` 1e4
Pa (a wet adhesive), `sense_max` 500 m and `brood_s` 0.1 (compute rules), `big_s` 400 kg (#126: near a large adult's
mass). e106's rates an update of 3.2 h are the same rates a day (harm without breath 1.5, over its heat 2.25, frost
1.5% of the tissue a degree). e106's body rates are otherwise unchanged.

**Local trials** (a 16 km world of 128 cells, `size=128 edge=24 grain=40 sow=2 body_sow=5`, a minute each; results
not kept): the world runs, the ledgers close to 1e-13, and the log, the census and the lines are the same on 1 and 7
threads. The first trial hatched every laying as a body: 10,192 bodies in four years, each a few kg of animals - so
a clutch is carried until it holds a tenth of the grain (`brood_s`), and the bodies then hold 140-270 kg each.

**The first pilot** (Ubuntu, 2026-10-06 02:17; `results/pilot1`): `tick1` (6 threads), `tick3` and `tick10` (3
threads each) with `years=70 body_sow=40`, `big_s` 400 and 20,000 bodies sown. Stopped by hand in its second year
with bodies, before the step its cost rule was written for: a year took 2.7 to 6.7 hours (Result).

**The second pilot** (the same three runs, at once): `big_s` 4000 and `bodies0` 2000 (the same 8,000 t sown), with
the two faults the first one showed mended (Result).

| run | arguments | asks | cost |
|---|---|---|---|
| `tick1` | `years=70 body_sow=40 big_s=4000 bodies0=2000 threads=6` | hypotheses 1-4, the cost | about 3 h |
| `tick3` | `... body_tick=3.3333 threads=3` | hypothesis 5 | about 2 h |
| `tick10` | `... body_tick=10 threads=3` | hypothesis 5 | about 1.5 h |

`body_tick` must divide the climate's 10 steps: 3.3333 is three updates of the bodies in one of the climate.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `ms_step` > 60 at 487080
- `bodies` > 200000 at 487080
- `bodies` < 100 at 594000

## Result

### The first pilot: stopped in its second year (`results/pilot1`, read by `pilot.py`)

| | `tick1` | `tick3` | `tick10` |
|---|---|---|---|
| bodies, year 41 / 42 | 27,556 / 556,066 | 23,978 / 581,822 | 291,957 / 563,629 |
| their matter, year 42 | 84,055 t | 117,498 t | 90,730 t |
| a body holds, year 42 | 151 kg | 202 kg | 161 kg |
| eaten of the producers' fixing, year 42 | 100% | 126% | 263% |
| the land's producers, kg a m2 (e109: 1.35) | 1.21 | 0.99 | 0.42 |
| flesh in the diet, year 42 | 0.4% | 0.7% | 2.9% |
| catches / faces failed, year 42 | 7.0 million / 11,568 | 7.1 million / 39,252 | 1.9 million / 133,005 |
| a year, year 41 / 42 | 96 s / 6.7 h | 97 s / 2.8 h | 322 s / 4.8 h |
| worst ledger | 9e-13 | 1e-12 | 2e-12 |

- **Ledgers close** and **the grain holds** (hypotheses 1 and 4): a body holds 0.4-0.5 `big_s`. Meetings happen
  from the first year (hypothesis 3), and the flesh eaten is under 3% of the diet.
- **The animals weigh ten to twenty times what the scale was chosen for.** #126 took 8.8-20 t a km2 of land from
  e106's planet; here the bodies' matter is 84,000-117,000 t in the second year, 200-290 t a km2 of land. They eat
  the litter (86-99% of the leading lines' diet): the world holds 280,000 t of it and 416,000 t a year is fixed, and
  nothing but a slow decay (1 a year) competes for it. Nine tenths of the matter is in swarms of the default adult
  mass, 0.1 kg. At `big_s` 400 that is 556,000-582,000 bodies against the 30,000 a run can pay for.
- **The cost of choosing grew with the crowd.** A body searched every cell within its reach (up to 81 cells) and
  with 20 bodies a cell that was 91% of a year's 6.7 hours.
- **A law still read the update.** The unit of chance was drawn afresh every update, so a wanderer's spread grew
  with the update's length: at `tick10` the bodies held 86% of the land's cells after one year, against 24% and 16%,
  and weighed ten times as much.
- Not read: whether the world stands, whether hunters hold the eaters, lines by island (two years).

**Mended before the second pilot** (trials: the log and the census the same on 1 and 7 threads): a body's reach is
searched ring by ring and stops when no farther cell can hold a nearer body; chance is an angle that wanders,
keeping its way for `turn_s` 3,600 s whatever the update. **Not mended, because it is the scale's question**: the
animals' weight. The second pilot follows #126's rule - the bodies are held near 30,000 and `big_s` follows - with
`big_s` 4,000 kg, ten times the agreed 300-1,000: a 400 kg adult's body is then a herd of ten, and only a kind of
4 t is one animal a body. What the weight settles at after the first years' overshoot is read there.

### The second pilot (`results/pilot`, read by `pilot.py`; thresholds in `results/provenance.csv`)

All three ran to year 70, in 80-90 minutes each. Levels are the last ten years' means (years 61-70).

| | `tick1` | `tick3` | `tick10` |
|---|---|---|---|
| bodies: the peak (year) / the last ten years | 29,786 (44) / 4,467 | 43,623 (43) / 6,050 | 52,542 (42) / 7,158 |
| their matter: the peak / the last ten years | 75,300 t / 6,360 t | 99,100 t / 10,070 t | 128,300 t / 19,887 t |
| a body holds | 1,428 kg | 1,667 kg | 2,831 kg |
| the land's producers, kg a m2 (e109 without bodies: 1.75-1.83) | 0.013 | 0.021 | 0.072 |
| the land they cover | 21% | 37% | 52% |
| the producers' fixing, year 40 -> year 70 | 416,000 -> 57,000 t | -> 57,000 t | -> 149,000 t |
| eaten of that fixing | 76% | 76% | 66% |
| flesh in the diet (of it killed) | 0.8% (0.2%) | 0.4% (0.0%) | 0.5% (0.1%) |
| faces failed a year, year 45 / year 70 | 10,788 / 1,520 | 5,715 / 0 | 2,441 / 504 |
| founders' lines, year 41 / year 70 | 28 / 2 | 25 / 2 | 25 / 2 |
| matter in bodies over 1 kg grown, year 43 / year 50 on | 38% / 0% | 3% / 0% | 0.3% / 0% |
| a year: the dearest / the last ten years | 353 s / 90 s | 339 s / 78 s | 161 s / 96 s |
| worst ledger | 2.2e-12 | 2.4e-12 | 2.0e-12 |

Against the hypotheses:

1. **Ledgers: yes.** Water, A, B and the living's matter with the carrion close to 2.4e-12.
2. **The world stands: no.** Bodies live to year 70, but the land is eaten bare within ten years and stays so: its
   producers are 0.7-4% of the world without bodies, they cover 21% and 37% of the land in two runs of three, and what
   they fix falls by 64-86%. In `tick1` the litter goes first (280,000 t to 47,000 t in five years, 285,000-378,000 t
   eaten a year), then the wood (42,000-53,000 t a year at the peak) and the seed with its bank.
3. **Meetings happen: yes, and they feed no one.** Catches every year, and failed faces in every year of `tick1`
   and `tick10`; in `tick3` the bodies that press die out and no face fails after year 62. Flesh is 0.4-0.8% of the
   diet, and bodies with flesh over a tenth of their diet never hold more than 0.7% of the matter.
4. **The grain holds: yes.** A body holds 0.36-0.71 `big_s`.
5. **The update may not be lengthened on this reading**: against `tick1` the bodies' matter is 1.6 times at
   `tick3` and 3.1 times at `tick10` (the line was 1.5), the flesh in the diet half. One run each: a difference
   between two replays of one update was not measured, so this says only that nothing shows the longer update to be
   safe. `body_tick` stays 1; the bodies then cost 36 s of a year's 90 s at 4,500 bodies and 303 s of 353 s at 25,000.

#116's turn points, read:

- **The eaters strip the land with bodies that break each other present.** Nothing holds them but their food.
- **One world of bodies on every island.** Two founders' lines of 256 are left from year 50, both on all eight
  islands and in the sea; a body ends 5-13 km from where it hatched and walks 450-1,900 km a year.
- **One way of living.** From year 50 every body is of the default adult mass, 0.1 kg, a swarm of 40,000 animals a
  body; 86-94% of what the bodies eat is litter.

## Conclusion

Holds for this world as built: `isles1` 40 years after the producers were sown and one seed, e106's body rates,
`big_s` 4,000 kg, bodies whose default form eats and digests anything soft, and 30 years.

- **The mechanics stand.** A body's laws in metres and seconds, the grain, pursuit in closed form, one law of
  contact and the carrion pool run with closed ledgers, the same on any number of threads, at a cost a 300-year run
  can pay if the bodies stay near 5,000 (7.5 hours) and not if they stay near 30,000 (a day and more).
- **The world does not stand with them.** The meeting law is not the brake on the eaters it was built to be: in 30
  years no line comes to live on flesh, and the eaters take three quarters of what the producers fix from a land
  they have eaten to a hundredth. This is the turn #116 wrote before the pilot - the producers' side of the cycle -
  and it is taken there, not mended here.
- **What the runs show of why** (read from the code and the outcome, not tested one by one): a body's food is found
  by sweeping a path, so no density of it is safe; dead matter is as digestible as its toughness allows and nothing
  else takes it at the bodies' pace (decay is 1 a year); wood and the seed bank lie within reach of a body of any
  size; and the world ends at one size - bodies over 1 kg grown held up to 38% of the matter in the first years
  and none from year 50.
- **The scale's numbers hold only for a land eaten out.** The bodies' matter over the land's area is 180-310 t a
  km2 at the overshoot's peak and 16-48 t once the land is bare, against #126's 8.8-20 (e106's planet, eaten to
  half). At `big_s` 400 kg that is some 470,000 bodies at the peak and 40,000 on the bare land; what a land that
  stands would hold is not known. What a body should stand for is asked after the eaters are held, not before: the
  weight depends on what holds them.
- Nothing goes to `base/`: e110's crate is the bodies' code until a world stands with them.

`vision.md`: rows C size, F dominance and F food web (the new world's part), and a lesson (a food found by sweeping
has no safe density). `foundation.md`: the bodies' paragraph, the contact row and the scale. The next step is #130 (what holds the eaters),
with the plan check on #116.
