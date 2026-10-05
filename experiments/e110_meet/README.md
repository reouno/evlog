# e110: bodies in metres and seconds, and bodies that meet (#123)

Date: 2026-10-06 (started)

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

**The pilot** (Ubuntu, 6 cores; all three at once):

| run | arguments | asks | cost |
|---|---|---|---|
| `tick1` | `years=70 body_sow=40 threads=6` | hypotheses 1-4, the cost | about 3 h |
| `tick3` | `... body_tick=3.3333 threads=3` | hypothesis 5 | about 2 h |
| `tick10` | `... body_tick=10 threads=3` | hypothesis 5 | about 1.5 h |

`body_tick` must divide the climate's 10 steps: 3.3333 is three updates of the bodies in one of the climate.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `bodies` < 100 at 594000
- `ms_step` > 60 at 594000

## Result

To come.

## Conclusion

To come.
