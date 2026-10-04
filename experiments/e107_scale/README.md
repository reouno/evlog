# e107: the world's scale (#126)

Date: 2026-10-05 (started)

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

Ubuntu, two runs side by side, 6 threads each, about an hour; each also writes the viewer's lapse
(`EVLOG_VIEW=rec:from=582120,len=368280,stride=1190,layers=5`, years 49-80, not committed).

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `bodies` < 100 at 712800
- `ms_step` > 10 at 712800

## Result

To come.

## Conclusion

To come.
