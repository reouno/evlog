# e112: the layers (#125)

Date: 2026-10-14

## Purpose

e111 left a land that stands under one way of living: a 0.1 kg sack that eats litter, the same on every island and
on the sea's floor, with flesh 0.1% of the diet and no hunter that lives with its prey. #125 asks for the layers:
the ground and the crowns as places a body enters - foods with a door of their own (the seed bank, roots, stores,
the leaves above a body's height) and a place where the caught is not - and for the bite's open clause (what the
part of a front that is no mouth breaks). As #130 was, it is done in three parts: readings with no new law (part 1,
here), one design as cycles agreed on the issue before code (part 2), the set on the trial world and a pilot on
`isles1` (part 3).

The crate is e111's (`experiments/e111_holds/`), copied. The control of the pilot is e111's own pilot run on to
year 140 (`experiments/e111_holds/results/pilot/all140_*`).

## Readings (part 1)

No law is added. The log gains what the land's producers hold by organ, a run ends by writing every stand and every
land cell, and one switch takes away what a front tears and does not swallow.

### Hypothesis

Written before the runs:

1. **The ground holds food no body reaches.** Roots, stores and the seed bank together are a fifth or more of the
   land's living producers, and more than its leaves (`nobody`, `all`).
2. **The crown is already a closed door.** The bodies of `all` are under 0.2 m tall where the stands are over 2 m:
   less than a tenth of the land's leaves and hanging seed is within their reach.
3. **A front that tears nothing but what it swallows still does not live with its prey.** With `tear=0` the
   designed hunter eats most of what it breaks (over half of the tissue that fails goes down a gut, against a
   twelfth in e111's `all_hunter`), and within ten years one of the two is gone all the same - the hunter's line or
   every other body: the gut slows a kill and nothing bounds it while a slower body is caught wherever it is
   (`notear_hunter`, and `notear_hunter3`, which hunts when its fat is under half).
4. With `tear` at its default (`all`) the world is e111's `all` to the digit: the copy changed nothing.

### Method

e111's crate copied (`e112_layers`). Added:

- log columns `land_leaf`, `land_wood`, `land_root`, `land_store`, `land_seed`, `land_bank` (kg a m2 of land);
- `<prefix>_stands.csv` (every stand on land as the run ends: height, age, each organ's matter, A and B) and
  `<prefix>_cells.csv` (every land cell: its soil's water, A and B, its litter, its seed bank);
- `tear` (default 1: e111's law): at 0, under `bite`, the part of a front that is no mouth tears nothing.

The trial world is e111's (`read.sh`: 16 km of 128 cells, terrain seed 1, life seed 1, producers sown in year 2,
300 bodies of `big_s` 1,000 kg sown in year 15, read to year 30).

    cargo build --release -p e112_layers
    experiments/e112_layers/read.sh <name> [key=value ...]

| run | arguments | asks |
|---|---|---|
| `nobody` | `body_sow=0` | hypothesis 1, and the line the later runs are set against |
| `all` | `road=1 worth=1 reach=1 bite=1` | hypotheses 1, 2 and 4 |
| `notear_hunter` | `all` with `tear=0 inject_year=20 inject_kind=1` | hypothesis 3 |
| `notear_hunter3` | `all` with `tear=0 inject_year=20 inject_kind=3` | hypothesis 3 |

One run each, one seed: a reading says which way the design must go, not how large an effect is.

**Cost and where**: four runs on Ubuntu, two threads each, at once: about 15 minutes, 2 core-hours.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `ms_step` > 60 at 201960

### Result

(to be written)

## The design (part 2)

(on #125, to be agreed before code)

## Conclusion

(to be written)
