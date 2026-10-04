# e107: the world's scale (#126)

Date: 2026-10-05

## Purpose

Watching e106 (#124) showed what a planet costs: a cell is 63 km, a body stands for millions of animals and is drawn
50,000 times its size, and a meeting can only be a chance inside a cell. A planet is not wanted (user, #126): climate,
seasons, land masses and height are, the size is not. Before the small world is designed, this pilot asks the
cheapest question: **what do e106's bodies do when the same world is declared smaller?** No law changes and no
crate: e106's binary, with a cell's side and S as arguments.

## Hypothesis

With the cell's side cut from 63 km to 1 km and to 250 m, and S cut with the cell's area (so every cell holds the
same animals a m2 at the sowing as in e106's pilot 3):

1. **The world stands**: bodies live to year 80 and the ledgers close.
2. **Bodies roam the whole world**: they cross 63 and 252 times as many cells a year, so they hold far more of the
   land than pilot 3's 17.5% of its cells, and eat it down sooner.
3. **Lines do not part by distance**: one founder's line holds all (as in pilot 3), over every land.
4. **Thirst kills fewer**: water is a few cells away instead of out of reach.

## Method

    target/release/e106_bodies experiments/e107_scale/results/<run> base/worlds/c1225.params years=80 body_sow=50 threads=6 \
        cell_km=<km> big_s=<S> sow_s=<S/100>

| run | `cell_km` | world's side | `big_s` (kg) | `sow_s` (kg) | a 400 kg adult's body stands for |
|---|---|---|---|---|---|
| pilot 3 (e106) | 63 | 32,000 km | 3e9 | 3e7 | 7.4 million |
| `km1` | 1 | 512 km | 755858 | 7559 | 1,900 |
| `km025` | 0.25 | 128 km | 47241 | 472.4 | 120 |

Everything else is pilot 3's: the same terrain, climate (its latitude bands kept), producers and life seed, so the
world is the same to the digit until the bodies are sown in year 50. What differs afterwards is only what reads the
cell's side: how many cells a body's path crosses, how far its eyes reach in cells, and what it stands for.

What is known to be wrong in these runs, and is the design's to mend: an update stays 3.2 hours, in which a body
walking 15 km a day crosses 2 cells of 1 km or 8 of 250 m and eats only where it lands; the slopes are the planet's
map shrunk (2 km of height over 128 km); the producers' seed and wind distances stay in cells; a sown body whose adult
mass is over `sow_s` stands for less than one animal.

Local (the Ubuntu box was unreachable), two runs side by side, 4 threads each (`threads=4`), about an hour; each also writes the viewer's lapse
(`EVLOG_VIEW=rec:from=582120,len=368280,stride=1190,layers=5`, years 49-80, not committed).

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `bodies` < 100 at 712800
- `ms_step` > 10 at 712800

## Result

`uv run python experiments/e107_scale/read.py` (it reads pilot 3 beside the two runs). Both ran to year 80 with every
ledger closed (worst 4e-12): `km1` in 2,111 s, `km025` in 1,188 s, local, 4 threads each.

| | pilot 3 (63 km) | `km1` (1 km) | `km025` (250 m) |
|---|---|---|---|
| a body stands for (mean, year 80) | 4.1 million animals | 112 | 234 |
| cells a body crosses, year 51 | 22 | 261 | 169 |
| bodies, year 60 | 39,135 | 2,068 | 3,006 |
| cells crossed a body a year, year 60 | 9.9 | 0.0 | 0.2 |
| bodies, the peak | 142,050 (year 71) | 588,497 (year 77) | 7,726 (year 55) |
| land cells held, year 80 | 17.5% | 16.7% (40.6% in year 77) | 0.01% |
| the land's producers, kg a m2, year 80 | 0.46 | 0.075 | 0.90 |
| first cause of death, year 80 | hunger | heat | age |
| founders' lines, year 80 (share of the first) | 2 (0.98) | 2 (1.00) | 2 (0.94) |

- **The walkers die in the first year.** A sown body's path of an update (3.2 hours) is a few hundredths of a 63 km
  cell and 2 to 8 of the small ones: the bodies cross 169-261 cells in year 51 against pilot 3's 22, walk off the land
  and die of thirst, cold and heat (`km1`: 4,524 left of 16,309 sown, 52% of them at sea).
- **What is left sits.** From year 54 the survivors cross no cell at all, and a clutch hatches where its parent
  stands, so 1,000-8,000 bodies hold some tens of cells and the land grows untouched (0.75 -> 0.88-0.93 kg a m2).
  In `km025` nothing else happens in 30 years.
- **In `km1` a line that moves arises in year 63 and nothing rations it.** 5,709 bodies become 207,102 in five years
  and 588,497 by year 77, on 40.6% of the land; the producers' fixing falls from 1.14e5 to 3.5e4 and the land from
  0.88 to 0.075 kg a m2 - pilot 3's bodies took 30 years to bring it to 0.46. Then heat is the first death (691,649
  in year 77) and the bodies fall to 109,976 by year 80, still falling. A year costs 176 s at the peak.
- **One founder's line holds all** in each world, as in pilot 3.

Against the hypotheses: 1 holds for the ledgers and the bodies, but `km1` ends inside a collapse; 2 fails - a body
that roams dies, the ones left hold a ten-thousandth of the land, and the one line that spreads takes it all and
strips it; 3 holds; 4 holds only in the first year (thirst 49-53% of deaths against 70%).

## Conclusion

Holds for e106's laws as they are, with only the cell's side and S changed (the update, the map's slopes, the
producers' distances and the climate's bands are the planet's).

- **A body's behaviour is tied to the cell and the update.** Sensing the next cell, choosing a side and hatching in
  place make a home range of a 63 km cell; in a small one they make a walker that overshoots or a sitter that never
  spreads. The small world needs an update in which a body's path is about a cell (15 km a day is one 250 m cell in
  24 minutes, or one 1 km cell in 1.6 hours) and young that leave by a distance, not by a cell.
- **Distance was the brake on the eaters.** On the planet the land was eaten as fast as bodies could walk to it; in a
  world they cross in a season, the eaters reach all of it at once, overshoot and strip it. A small world needs its
  brake in the living - what eats the eaters (step 2, #123) and what the producers do against being eaten - so the
  scale and step 2 are designed as one set of cycles, not one after the other.
- **What a body stands for falls as designed** (4 million -> 112-234 animals), and the cost of a year does not
  change with the cell's side, only with the number of bodies.

`vision.md`: section 5 (the next piece is the scale, #126, with step 2). Open: which size (the collapse is faster
the smaller the world), and how many bodies evolution needs.
