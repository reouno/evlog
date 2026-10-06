# e111: what holds the eaters (#130)

Date: 2026-10-07

## Purpose

e110 put bodies on the islands in metres and seconds and let them meet. The machinery runs; the world does not
stand: the land is eaten bare in ten years, flesh is under 1% of the diet, every body ends at the default 0.1 kg and
two founders' lines hold every island. #130 asks what holds eaters in a world that stands, in three parts: readings
with no new law, one design as cycles agreed before code, a pilot. **This file is the readings so far**; the design
is #130's, and the pilot is added here when the design is agreed.

## Readings (part 1)

No law is added. Each reading is a switch that takes something out of every body's reach, a rate at its extreme, a
designed body put in beside a control, or arithmetic with no world run. All are read on one line: **the land's
producers (kg a m2) in the last five years, against the same world without bodies.**

### Hypothesis

Written before the runs (after the first years of `base` had been seen):

1. **`bench`** (arithmetic): the thinnest food a body can live on is far below what the land holds, and it rises
   with adult mass - on one food the smallest body wins.
2. **Litter is what carries the eaters** (`nolitter`): with litter no food the bodies fall to a small share of
   `base`'s and the land's producers stay within 20% of the world without bodies.
3. **A faster decay alone does not hold them** (`decay10`): the bodies still take the litter before it rots (they
   pass it in days; ten a year is a month).
4. **Wood and the seed bank out of reach protect what regrows** (`noreach`): the bodies stay as many (the litter
   feeds them) and the land's producers stay above half of the world without bodies.
5. **A designed hunter does not live on flesh** (`hunter` against `twin`): it kills, but flesh stays under a tenth
   of its diet and its line does no better than its twin's, the same body with no pull towards another.

### Method

e110's crate copied (`e111_holds`). Added, all off by default (the world is e110's to the digit):

- `eat_litter=0`, `eat_wood=0`, `eat_bank=0`: that food is in no body's reach, and is not sensed.
- `inject_year`, `inject_kind`, `inject_bodies`: grown bodies of one designed genome (`form::designed`, written in
  the genome's own language) put where bodies stand on land - kind 1 the hunter (10 kg grown, a tough front that is
  mouth, frame and muscle; pulled towards a smaller body that is not kin, presses it, rests where flesh lies), kind 2
  its twin without the pull. The world's own chance is not drawn, so the run is its control until that year.
- `e111_holds bench <params>`: what one grown animal earns and pays a day at each adult mass, by `live`'s and
  `speed`'s own arithmetic.

The trial world (`read.sh`): 16 km of 128 cells (`size=128 edge=24 grain=40`), terrain seed 1, life seed 1,
producers sown in year 2, 300 bodies of `big_s` 1,000 kg sown in year 15, read to year 30.

    cargo build --release -p e111_holds
    ./target/release/e111_holds bench base/worlds/isles1.params
    experiments/e111_holds/read.sh <name> [key=value ...]

| run | arguments | asks |
|---|---|---|
| `nobody` | `body_sow=0` | the line every reading is set against |
| `base` | - | does the trial world show e110's outcome |
| `nolitter` | `eat_litter=0` | hypothesis 2 |
| `decay10` | `decay=10` | hypothesis 3 |
| `noreach` | `eat_wood=0 eat_bank=0` | hypothesis 4 |
| `nolitter_noreach` | `eat_litter=0 eat_wood=0 eat_bank=0` | a pair: leaves and hanging seed alone |
| `decay10_noreach` | `decay=10 eat_wood=0 eat_bank=0` | a pair |
| `hunter` | `inject_year=20 inject_kind=1` | hypothesis 5 |
| `twin` | `inject_year=20 inject_kind=2` | hypothesis 5's control |

One run each, one seed: a reading says which lever the outcome hangs on, not how large its effect is.

**Cost and where**: every run on Ubuntu (2026-10-07), 2-3 threads, 4-35 minutes each with four or five at once,
about 8 core-hours in all. `nobody`, `base`, `nolitter` and `decay10` were first run on the Mac; the two machines do
not give the same world to the digit (year 11 without bodies: 0.312 against 0.316 kg a m2), so all nine were run on
one machine and the Mac's four logs are kept in `results/read_mac/` as a second realisation. `nobody`, `base`,
`nolitter` and `noreach` were run again with the land's A and B by pool added to the log (the same world to the
digit). Read by `read.py` (`results/read.csv`, `designed.csv`, `provenance.csv`).

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `ms_step` > 60 at 201960

## Result

### `bench`: a body's day (`results/bench.csv`)

A grown animal of the form with no genes, on land at its best heat, moving at the tenth of its speed it has with no
genes:

| adult mass | goes | its mouth sweeps | its gut can pass | upkeep + work | the thinnest food it lives on |
|---|---|---|---|---|---|
| 1 g | 0.3 km a day | 1,775 m2 a kg a day | 30% of its mass a day | 1.1% a day | 0.008 g a m2 |
| 0.1 kg | 1.5 km | 363 m2 | 30% | 1.1% | 0.038 g a m2 |
| 10 kg | 5.5 km | 63 m2 | 30% | 1.1% | 0.22 g a m2 |
| 1 t | 13.5 km | 7 m2 | 30% | 1.1% | 1.9 g a m2 |

- **A body's economy has no floor the land can stand on.** Its gut passes 27 times what it burns, and its mouth pays
  its day on 0.04 g of food a m2. The trial land holds 800 g of producers and 390 g of litter a m2.
- **Nothing but distance gets cheaper with size.** Upkeep, work and the gut's rate are the same share of the body at
  every mass; the ground swept a kg falls by 2.2-2.5 a decade of mass. On one food the smallest body wins (hypothesis 1).

### The readings (`results/read.csv`: means of years 26-30; t on the whole trial world, 25.6 km2 of land)

| run | land's producers, kg a m2 | of `nobody` | land covered | bodies' matter | they eat: leaf / wood / seed / litter, t a year |
|---|---|---|---|---|---|
| `nobody` | 0.801 | 100% | 89% | - | - |
| `base` | 0.203 (0.154 in year 30, falling) | 25% | 53% | 1,506 t | 79 / 323 / 165 / 4,323 |
| `nolitter` | 0.785 | 98% | 88% | 16 t | 11 / 30 / 19 / - |
| `decay10` | 0.208 | 26% | 42% | 2,254 t | 172 / 516 / 218 / 6,811 |
| `noreach` | 0.374 (falling) | 47% | 81% | 1,697 t | 37 / - / 4 / 4,938 |
| `nolitter_noreach` | 0.798 | 100% | 88% | none from year 17 | - |
| `decay10_noreach` | 0.436 (falling) | 54% | 82% | 2,320 t | 163 / - / 16 / 7,801 |
| `hunter` | 0.634 (rising) | 79% | 89% | none from year 22 | - |
| `twin` | 0.130 | 16% | 38% | 1,399 t | 103 / 403 / 144 / 4,011 |

Ledgers close to 2e-13 in every run. Two realisations of one run differ by 0.01-0.07 kg a m2 (the Mac's against
Ubuntu's; `twin` against `base`, the same world once the twin's line is gone).

1. **The trial world shows e110's outcome**, more slowly: 25% of the producers left and falling, 85% of the diet
   litter, one founder's line 98% of the matter, 2% of it in bodies over 1 kg.
2. **Litter is what carries the eaters: yes.** With litter no food the bodies fall to a hundredth and the land stands
   at 98%. What is left is another body: one line of 250 kg grown (18 kg in the Mac's realisation), 40% muscle, a
   bite four times the others', living on wood (50%), seed (34%) and leaf (16%).
3. **A faster rot does not hold them: yes.** At ten times the decay the bodies are half as many again; they pass
   litter in days and the rot takes a month.
4. **Wood and the seed bank out of reach keep the cover, not the land: half right.** The cover stays (81% against
   53%) but the producers still fall to 47%, with 37 t of leaf eaten a year of 9,200 t fixed. The cause is the
   nutrients' road (below). Leaves and hanging seed alone feed no sown line (`nolitter_noreach`).
5. **A designed hunter does not live on flesh: wrong, and worse.** Fifty of them (50 t) among 2,653 bodies broke
   2,690 bodies in a year - 285 million animals, 1,840 t - ate 64 t of it, and the last one starved in the next. The
   twin's line was gone by the first census; with every body dead the land grows back (79% and rising).

### Why the land falls when only litter is eaten (`land_b_*` in the logs; g of B a m2 of land, year 30)

| run | soil | producers | litter | bodies on land | litter decayed, t a year |
|---|---|---|---|---|---|
| `nobody` | 0.20 | 16.5 | 5.8 | - | 12,000 |
| `noreach` | 0.24 | 8.0 | 6.8 | 1.2 | 830 |
| `base` | 0.36 | 3.7 | 10.0 | 1.0 | 1,060 |

The bodies hold a fifteenth of the land's B. But what a gut does not keep of a food's A and B goes back into the
litter, while the litter's matter is eaten: in `noreach` the litter is 13 g a m2 of matter holding 6.8 g of B and
2.9 g of A, the decay's own rule reads a litter that rich in A as too tough to rot (a tenth of the rate), and
the producers' B stops growing (8.0 against 16.5). The land also ends with 6-7 g less B than without bodies (not
separated: bodies that feed on land and die at sea, and a land that takes less from its rock).

## Conclusion

Holds for the trial world (16 km, one land of 26 km2, one seed, 15 years with bodies, `big_s` 1,000 kg) and e110's
laws; one run a reading, so each says which way a lever moves the land, not by how much.

- **One lever leaves the land standing: the dead matter.** No other, and no pair without it. #116's turn (the eating
  law redesigned) is not taken; the dead matter's worth and its roads are what the design is about.
- **Why, in three parts.** (1) A body's economy: 0.04 g a m2 pays its day and its gut passes 27 times its need, so
  whatever is free is taken to nothing, and the dead are free - soft, digested whole, everywhere. (2) What the swarm
  takes in passing: the seed in the ground and the young wood (the cover). (3) The road back: A and B a gut does not
  keep return to a litter that no longer has matter and cannot rot, and the producers starve beside it.
- **The live plant is already defended** by height and by the bite it takes: without litter the eaters are a
  hundredth and the land is whole. The body that then lives is large, strong-mouthed and eats wood and seed: a
  size has a place as soon as the free food is gone.
- **Flesh pays, and nothing bounds a kill.** A catch is a whole body of S kg held for the rest of the update: no
  refuge, no escape for the slower, no limit from the catcher's appetite, and 97% of what is killed rots. The
  meeting law is not too weak to be the eaters' brake; it has no brake of its own.
- **Not changed by these readings**: one line on land and sea (a fifth to a half of the bodies are at sea), and the
  scale (the bodies weigh 60-90 t a km2 of land).

The design from these readings is #130's comment of 2026-10-07 (to be agreed before code); its pilot is added here.
`vision.md`: rows C size, F food web, and the lesson on what holds eaters.
