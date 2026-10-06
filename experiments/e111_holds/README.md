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

**Cost**: a run is 1-4 minutes on three threads. `nobody`, `base`, `nolitter` and `decay10` ran on the Mac
(2026-10-07); the other five on Ubuntu, two threads each at once (about 10 core-minutes each).

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `ms_step` > 60 at 201960

## Result

(to be written)

## Conclusion

(to be written)
