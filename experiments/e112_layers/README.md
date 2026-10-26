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
- `tear` (default 1: e111's law): at 0, under `bite`, the part of a front that is no mouth tears nothing;
- `<prefix>_fates.csv` (the bodies that died in a year by founder's line and cause) and `<prefix>_where.csv` (every
  tenth year, each genotype's bodies by island) - added after the first reading, changing no number of a run.

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
140 on Ubuntu, six threads, 5.0 hours; read by `control.py` (`results/control.csv`, `control_ways.csv`) by decade
against e109's world without bodies, the bodies by `analysis/ways.py` (#119).

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
   weight. It starves: of the line's bodies 70 died of hunger in the first year and 5 in the second, 5 of poison
   and 1 of cold (`notear_hunter_fates.csv`: the dead by line and cause, added to the crate after the first
   reading and the run made again, its log the same to the digit). By `bench` this body pays 15% of its weight a
   day to run as it does, all day, where a gut kept full all day passes 34% and keeps about half of it.
   The hunter that hunts when hungry (`notear_hunter3`) does the same (315 t eaten, gone in two years).
   With `tear=0` and no designed body (`notear`) the sown bodies stop pressing by year 22, as in `all`, and the land
   stands as it does there (91% of `nobody` against 93%, inside what two realisations differ by).
4. **`all` is e111's `all` to the digit: yes** (92 columns of the log over 30 years).

#### The control: e111's pilot run on to year 140 (`results/control.csv`)

Means of a decade; the land's producers against e109's world without bodies over the same years; the ways from
the body census of the decade's last year. Ledgers close to 5e-12 over the 140 years.

| years | land, of bare | bodies | their matter, kt | at sea | flesh in the diet | died of thirst a year | frame, of the body | ways | s a year |
|---|---|---|---|---|---|---|---|---|---|
| 41-50 | 99% | 1,328 | 1.5 | 35% | 0.50% | 198 | 0.08 | 1.4 | 41 |
| 51-60 | 89% | 13,201 | 13.1 | 20% | 0.34% | 1,481 | 0.08 | 1.2 | 91 |
| 61-70 | 78% | 11,175 | 15.6 | 18% | 0.13% | 3,068 | 0.11 | 1.3 | 88 |
| 71-80 | 69% | 13,140 | 19.6 | 19% | 0.09% | 3,308 | 0.17 | 2.6 | 104 |
| 81-90 | 68% | 14,075 | 23.7 | 26% | 0.03% | 4,284 | 0.22 | 3.1 | 115 |
| 91-100 | 65% | 17,876 | 31.2 | 28% | 0.02% | 5,157 | 0.27 | 2.9 | 137 |
| 101-110 | 61% | 31,704 | 46.5 | 28% | 0.02% | 5,773 | 0.29 | 2.6 | 236 |
| 111-120 | 67% | 29,187 | 48.0 | 32% | 0.01% | 5,692 | 0.31 | 2.9 | 213 |
| 121-130 | 70% | 43,644 | 70.0 | 31% | 0.02% | 6,161 | 0.32 | 2.9 | 331 |
| 131-140 | 71% | 50,044 | 79.7 | 33% | 0.01% | 5,405 | 0.32 | 2.0 | 346 |

- **The land stands, and is not falling.** It fell to 61% of the world without bodies over years 101-110 and is
  back at 71%; its cover is 94% throughout and what it fixes is the bare world's (0.91-1.07 of it). #116's turn
  (a land falling past half) is not met.
- **The bodies keep growing in number and matter**, five times the matter of year 70: 195 t a km2 of land. The B
  in the soil rises with them, 0.46 to 16.5 g a m2, and in the plants 23 to 49.
- **One food, one size, one line, no flesh.** Litter is 99.4-99.9% of the diet from year 51; no genotype holding
  1% of the matter is over 1 kg; one founder's line holds the world from year 51; flesh falls to 0.01% of the diet
  and the bodies that die broken from 3,059 a year to 47.
- **What changed is the make and the range.** The frame went from 8% of the body to 32% (armour; the deaths by
  poison fall with the breaks, 12,713 to 664 a year) and muscle from 14% to 5%. From year 80 the measure reads
  2.0-3.1 ways where it read 1.2-1.4 before, parted by make, place and range and by nothing else (diet and size
  read 1.0). In year 140: an armoured stayer on land (75% of the matter; 107 km a year, 3% at sea), the first soft
  sack, now mostly at sea (21%; 80% at sea, 1,147 km a year), and the armoured form at sea (3%). 79% of the matter
  is in ways the census of year 50 has no match for; between censuses ten years apart nothing is new (under 2%):
  the change is a drift, not a founding.
- **A year costs what its bodies cost**: 41 s with 1,300 bodies, 346 s with 50,000 (six threads on Ubuntu). A run
  of 300 years at this `big_s` is 17 hours or more, not the 7.5 hours e111 wrote.

## The design (part 2)

Written on #125 (https://github.com/reouno/evlog/issues/125#issuecomment-6152160545) and agreed on 2026-10-26 as
recommended: the three laws as one set, a store digested whole, `tear=0` as the bite's clause, and the bodies'
measure with its five blocks and cuts (#119). Built behind switches in `src/body.rs`, all 0 = e111's world to the
digit:

- `ground`: a land cell's ground is a layer a body enters when its front presses (muscle stress x its bite) as hard
  as the soil - `soil_hard` 1e5 Pa full, twice that dry. Inside, it moves at its front's power over the soil's
  strength times its frontal area, senses to its own length in the dark, loses no water through its skin and takes
  the soil's heat (the air's, followed over `soil_days` 10). It eats the stands' roots and stores and the seed
  bank; a store is digested whole, as a body's fat is.
- `crown`: a land cell's crowns are a layer a body enters when the glue under it holds its weight and the wood
  under its own length bears it (`bear` 10 kg a kg of wood), paying weight x the tallest stand's height. Inside, it
  eats all the leaves, hanging seed and wood, whatever its height, and finds no water; it falls back to the surface
  where the crowns no longer hold it.
- `tear=0`: a front breaks what its own gut takes in, and nothing more.
- In every layer a body senses and meets only the bodies of its layer, reaches only its layer's foods and changes
  layer by the eighth output of its controller (past +1 up, past -1 down, one layer an update; a random first genome
  draws only the seven outputs e111 had, so the founders are e111's and the eighth is found by mutation). Dung and
  the dead go to the cell's pools from any layer. At sea a body is on the surface.
- The census gains `ate_root`, `ate_store`, `ate_bank`, `glue_under` and the shares of a genotype's animals by place
  (`at_sea`, `at_surface`, `at_ground`, `at_crown`), so `analysis/ways.py` reads the layers as places and the new
  foods as diet; the log gains `ate_root` .. `ate_bank` and `body_ground`, `body_crown` (shares of the bodies'
  matter).

The designed bodies (`form::designed`, `inject_kind`), by `bench`'s arithmetic as grown:

| kind | body | front's pressure | the ground's door | digs a day at full activity | glue holds it | wood it needs under it |
|---|---|---|---|---|---|---|
| no genes | 0.1 kg | 2.2e4 Pa | shut | - | yes | 6.7 kg a m2 |
| 5, the walking hunter | 10 kg, e111's hunter without the genes that make it run (activity 0.23, not 0.86) | 2.0e5 Pa | open | - | no | - |
| 6, the digger | 0.1 kg, a hard front with active muscle behind it, gut and fat behind, goes down | 5.4e5 Pa | open, dry or full | 635 m | no | - |
| 7, the climber | 10 mg, glue on its bottom, goes up | 2.2e4 Pa | shut | - | yes | 0.31 kg a m2 |

The climber is 10 mg, not the gram the design named: by `bear` 10 a gram needs about 1 kg of wood a m2 under it, a
stand only the heaviest tenth of the trial world's have.

## The set (part 3)

### Hypothesis

Written before the runs:

1. **Each door can be lived in**: the digger's and the climber's lines are alive in year 30 with over half of their
   diet from their layer's foods, and the walking hunter's line is alive in year 30 with over half of its diet flesh.
2. **Evolution has not found a door in fifteen years**: in `layers` under 5% of the bodies' matter is in the ground
   or the crowns at year 30 (the eighth output is a mutation away, and a door a few more).
3. **The land is not eaten from below**: the land's producers in `layers` are within the spread of two
   realisations (0.07 kg a m2) of `notear`'s, and the digger takes under a fifth of the ground's foods.
4. With `ground=0 crown=0` and `tear=1` the world is e111's `all` to the digit.

### Method

The trial world (`read.sh`), `OUT=set`, one run each, against `notear` (part 1: `all` with `tear=0`):

| run | arguments | asks |
|---|---|---|
| `off` | `road=1 worth=1 reach=1 bite=1` | hypothesis 4 |
| `layers` | `off` with `tear=0 ground=1 crown=1` | hypotheses 2 and 3 |
| `no_ground`, `no_crown`, `tear` | `layers` with `ground=0`, `crown=0`, `tear=1` | each law left out |
| `digger`, `climber`, `hunter` | `layers` with `inject_year=20 inject_kind=` 6, 7, 5 | hypothesis 1 |

A designed line is read by its founder's line in `_lines.csv`, `_bodies.csv` and `_fates.csv`.

**Cost and where**: eight runs on Ubuntu, two threads each, six then two at once: about 20 minutes, under 3
core-hours. Then the pilot on `isles1` (`pilot.sh`, bodies sown in year 40, to year 100) with the set as the
results say, against the control (`results/control.csv`): about 2 hours on six threads, more if the layers hold
more bodies.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `ms_step` > 60 at 201960

### Result (the set)

From `results/set.csv` and `set_designed.csv` (what was read: `results/provenance.csv`, rows `set:`). Ledgers close
to 2e-13 in every run. Land: the land's producers, kg a m2, years 26-30; `notear` (part 1) is the line.

| run | land | of `nobody` | against `notear` | the bodies' matter, t | in the ground / crowns | ways (place) |
|---|---|---|---|---|---|---|
| `notear` | 0.728 | 91% | - | 1,734 | - | - |
| `off` | 0.747 | 93% | +0.019 | 1,163 | - | 1.51 (1.09) |
| `layers` | 0.738 | 92% | +0.010 | 1,461 | 0 / 0 | 1.11 (1.07) |
| `no_ground` | 0.738 | 92% | +0.010 | 1,461 | 0 / 0 | 1.11 (1.07) |
| `no_crown` | 0.728 | 91% | +0.000 | 1,734 | 0 / 0 | 1.26 (1.10) |
| `tear` | 0.675 | 84% | -0.053 | 1,646 | 0 / 0 | 1.47 (1.18) |
| `digger` | 0.716 | 89% | -0.012 | 1,432 | 0 / 0 | 1.17 (1.10) |
| `digger2` | 0.666 | 83% | -0.062 | 1,376 | 0 / 0 | 1.13 (1.06) |
| `climber2` | 0.729 | 91% | +0.001 | 1,413 | 0 / 0.03% | 1.16 (1.06) |
| `hunter` | 0.743 | 93% | +0.016 | 1,566 | 0 / 0 | 1.26 (1.12) |

4. **`off` is e111's `all` to the digit: yes** (98 columns over 30 years).
2. **Evolution has not found a door in fifteen years: yes.** No body of `layers` is in the ground or the crowns
   in years 26-30, and `no_ground` is `layers` to the digit: nothing entered the ground. `no_crown` is `notear` to
   the digit, so something entered the crowns for a while; it left no line there. Litter is 99.9% of the diet.
3. **The land is not eaten from below: by the evolved bodies, yes; by a designed digger, no.** `layers` is within
   the spread of `notear` (+0.010). The revised digger took the land to 83% of `nobody` in ten years (-0.062 against
   `notear`, roots -0.007 and stores -0.030 kg a m2) and was gone in six.
1. **Each door can be lived in: no, not by these bodies.** Each door was entered; no designed line lived ten years.

   | designed line | where it lived | what it ate | how it ended |
   |---|---|---|---|
   | `digger` (activity 0.1) | the ground, all of it | roots 27-47%, stores 34-59%, bank 14-18% | hunger in five years (203, 88, 9 bodies a year) |
   | `digger2` (activity 0.45, half the A in its front) | the ground, all of it | roots 23-37%, stores 48-64%, bank 12-17% | 87 t in its first year, then hunger in six |
   | `climber` (always up) | a quarter of its animals in the crowns in its first year, then none | litter 97% | thirst (142, 76 bodies a year) |
   | `climber2` (down to drink at 0.7 of its water) | 20-33% of its animals in the crowns | litter 90-95%, leaf 3-5%, wood 2-5% | thirst (272, 252, 98 bodies a year), gone in eight |
   | `hunter` (walks) | the surface | - | its first year: hunger 45 bodies, poison 9, broken 8 |

   Read from the traces (`EVLOG_BODY_TRACE_G`, `results/trace/`): the first digger ate its cell down with its broods
   and never left it at the activity of no gene (late in its first year an adult took in a hundredth of what its
   gut could pass), and its young grew slowly on a food poor in A (stores carry 0.1%); the walking hunter's gut
   runs full, but a press works its front's muscle for the whole time it holds its prey, 0.013 kg an update against
   the 0.009 its gut passes, and walking alone costs half of what it keeps.

## Conclusion

**Part 1.** The readings say where the unused food is and which way the bite's clause goes; the control says the
plan does not turn.

1. The ground holds food no body reaches: **yes** - 45% of the land's living producers, ten times the leaves.
2. The crown is a closed door: **nearly** - 12% of the leaves and hanging seed is within a grown body's reach;
   the stands are lower and thinner than assumed, so a climber of these crowns is a small body.
3. A front that tears only what it swallows still does not live with its prey: **half wrong** - the kill is
   bounded by the gut and the world is not emptied; the designed hunter starves, which is the hunter's design
   (it runs all day), not the clause.
4. The copy is e111's world to the digit: **yes**.

The control: a land at 61-71% of the bare world and not falling, one line on one food at one size for a hundred
years, its only spread in armour and range.

Rows of `vision.md` changed: the plant foods (the ground's share, unreached), size, dominance, the food web and
the ways of living (today's numbers from the control), and the lesson on the kill.

Parts 2 and 3: to be written.
