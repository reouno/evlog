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
| `notear` | `all` with `tear=0` | the hunters' control (added: `tear` changes the sown bodies' meetings too) |
| `notear_hunter` | `notear` with `inject_year=20 inject_kind=1` | hypothesis 3 |
| `notear_hunter3` | `notear` with `inject_year=20 inject_kind=3` | hypothesis 3 |

One run each, one seed: a reading says which way the design must go, not how large an effect is.

**Cost and where**: five runs on Ubuntu (2026-10-14), two threads each, four at once beside e111's pilot: 4-9
minutes a run, under 2 core-hours. Read by `read.py` (`results/read.csv`, `layers.csv`, `designed.csv`,
`provenance.csv`).

**The control of the pilot** is e111's own pilot (`pilot.sh all`, `isles1`, bodies sown in year 40) run on to year
140 on Ubuntu, six threads, 3.5 hours; read by `control.py` by decade against e109's world without bodies, the
bodies by `analysis/ways.py` (#119).

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `ms_step` > 60 at 201960

### Result

All numbers from `results/read.csv`, `layers.csv` and `designed.csv`; what was read and by which thresholds is in
`results/provenance.csv`. Ledgers close to 2e-13.

#### What the land holds (kg a m2 of land, means of years 26-30; B as the run ends)

| pool | `nobody` | `all` | its B share |
|---|---|---|---|
| leaf | 0.037 | 0.035 | 1.6% |
| wood | 0.428 | 0.400 | 0.28% |
| hanging seed | 0.002 | 0.002 | 1.3% |
| **root** | 0.108 | 0.099 | 1.1% |
| **store** | 0.227 | 0.212 | 0.10% |
| **seed bank** | 0.044 | 0.040 | 2.0% |
| litter | 0.391 | 0.315 | 1.5% (`all`: 0.9%) |

1. **The ground holds food no body reaches: yes, and it is most of what there is.** Roots, stores and the bank are
   45% of the living producers' matter and 56% of the B built into them, ten times the leaves. The largest pool is
   the store, sugar with next to no A and B: by e111's worth law 3% of it is working part. The richest tissue on
   the land is the seed in the ground.
2. **The crown is already a closed door: nearly, not as I wrote it.** A grown body of `all` stands 6.8 cm tall (the
   mean animal 3.7 cm). The stands are lower than I assumed - 1.30 m at the median by their leaves, a tenth under
   0.21 m, a tenth over 1.70 m - so a grown body reaches 12% of the leaves and hanging seed, not under a tenth. A
   body 0.3 m tall would reach 37%, one of 1 m 75%.
   - The stands are thin: the median stand (by its leaves) holds 0.13 kg of wood a m2, a tenth of them over 0.76.
   - The soil is full: 99% of the land's cells are over two thirds full as the year ends.
3. **A front that tears nothing but what it swallows: the kill is bounded, and the hunter still does not live.**

   | year | bodies, `notear` | `notear_hunter` | tissue failed, t | of it down a gut | the designed line |
   |---|---|---|---|---|---|
   | 20 (put in) | 867 | 867 | 1.6 | | 50 bodies, 50 t |
   | 21 | 935 | 647 | 388 | 100% | 5 bodies, 1.2 t, flesh 98% of its diet |
   | 22 | 1,027 | 1,011 | 22 | 100% | none at the census |
   | 23 to 30 | 1,109 to 2,481 | 1,222 to 1,346 | 0 | | none |

   The hunter eats all it breaks (in e111's `all_hunter` a twelfth: 60 t of 744), and the world is not emptied: the
   other bodies are a third fewer for a year and back the next. I had the kill unbounded still; it is bounded by
   the gut. The hunter's line ends all the same, in two years: its last bodies are young at a third of their egg's
   weight. Cause not separated (the log has deaths by cause, not by line); by `bench` this body pays 15% of its
   weight a day to run as it does, all day, where a gut kept full all day passes 34% and keeps about half of it.
   The hunter that hunts when hungry (`notear_hunter3`) does the same (315 t eaten, gone in two years).
   With `tear=0` and no designed body (`notear`) the sown bodies stop pressing by year 22, as in `all`, and the land
   stands as it does there (91% of `nobody` against 93%, inside what two realisations differ by).
4. **`all` is e111's `all` to the digit: yes** (92 columns of the log over 30 years).

## The design (part 2)

(on #125, to be agreed before code)

## Conclusion

(to be written)
