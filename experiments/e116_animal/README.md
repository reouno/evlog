# e116: the speed of a world at the size of an animal - a prototype (#135)

Date: 2026-11-09

## Purpose

Watched on 2026-11-08, e115's world has no animal in it: a body is some 300,000 animals of 3-5 cm, a step is 44
minutes, and the screen mixes three scales (#116). The user chose to rebuild at the size of an animal (#135): one body
one animal from about 1 kg, smaller life a field, an island the size of an open-world game's map, time continuous.
What that costs is not known, and it sets the island's size and the count. This crate is no world: it measures the
cost of animals at their own size, and it shows on the screen what that size looks like.

## Hypothesis

1. **Time continuous, decisions paced by events**, costs about 1e4-1e5 decisions an animal a year (one when the
   animal arrives, its patch runs low, another comes near, or ten minutes pass), at a few microseconds each, so that
   1e4 animals run a year in well under an hour of one core.
2. **The cost grows with the animals near each other**, not with the world's area: at a fixed density the cost an
   animal-year is flat in N.
3. **On the screen**, animals at their own size over ground at 5 m read as animals moving over a landscape, and
   their paths are smooth.

## Method

One crate, no climate, no water, no chemistry. Nothing in it is a law of the world to be kept; the controller is a
placeholder for #131's mind.

- **Ground**: an island in a sea, cells of 5 m, a hill from smooth noise; trees stand where a second noise says, and
  shade the grass under them. Grass on each cell grows back toward its cap, worked out when the cell is read (no
  per-step cost).
- **Animals**: a position, a velocity set at its last decision, a mass (genome, 1-200 kg), energy, a linear controller
  (genome) from what it senses: the grass under it and its slope, the nearest larger and smaller animal within sight,
  its energy. Outputs: a velocity and a bite. Metabolism by Kleiber (3.4 W kg^-0.75), movement by its cost of transport,
  grazing up to 0.1 kg^0.75 of dry grass a day at 9 MJ a kg. A bite at contact on an animal under 2/3 of its mass kills
  and eats it. Births at twice the energy of a newborn, deaths by hunger or age (five years).
- **Time**: each animal has its own next decision in one queue: when it has gone 20 m, when its patch runs low, when
  another enters its sight (worked out from both paths when either decides), or after ten minutes; two seconds while
  another is within ten body lengths. Positions between decisions are on straight lines.
- **Meeting**: a grid of 50 m buckets, each animal in the bucket of its last decision; a query widens by the 20 m an
  animal can have gone since.

**Runs** (Ubuntu, one thread each, at once; under an hour, under 6 core-hours):

| run | world | animals | asks |
|---|---|---|---|
| `bench1k`, `bench10k`, `bench30k` | 7 km (about 25 km2 of land) at the density of `bench10k`, the land scaled to N | fixed (no births or deaths), 30 days | decisions an animal-day, microseconds a decision, animal-years a core-hour |
| `live` | 4 km, an island of about 6 km2 | 300 founders, births and deaths, 2 years | does a population hold, does the queue stay paced with chases in it |
| `look` | `live` recorded: a day at a frame a second, and 30 days at a frame a minute | | the screen |

**Stop early if:** - (no log column decides it: a bench either finishes or not.)

## Result

Ubuntu, one thread each, seed 1, 2026-11-09. `bench10k` and `bench30k` were stopped after 6 days and 1 day of 60
(they would have run for 6 and 19 hours).

| run | animals | decisions an animal-day | us a decision | notices a decision | animal-years a core-hour |
|---|---|---|---|---|---|
| `bench1k` | 993 | 23,340 | 1.65 | 0.3 | 256 |
| `bench10k` (days 1-6) | 9,983 | 29,800 | 3.5-5.2 | 0.9-1.7 | about 70 |
| `bench30k` (day 1) | 30,049 | 28,200 | 5.5 | 1.6 | about 50 |
| `live`, 2 years | 300 founders, 1,000-1,580 | 2,366 | 1.07 | 0.07 | 3,891 |

- **The benches measured a world of endless chases.** With bites off in a bench, a hunter that sees a smaller
  animal chases it for 60 days at a decision a second, and its prey flees at the same pace: a third to a half of
  all decisions are "close". No bench number is the cost of a living world.
- **The cost of a decision grows with N** at a fixed density, 1.5 to 5.5 us from 1k to 30k, with the notices a
  decision sends (0.3 to 1.6): hypothesis 2 does not hold as built.
- **`live`**: the population rises from 300 to 1,580 in four months and holds at 1,000-1,340 (100-140 a km2) for
  the rest of two years. Hunters fall from 16 to 1-2 by day 300. Mean mass rises from 15 to 83 kg. 2,366 decisions
  an animal-day is 8.6e5 an animal-year, ten times hypothesis 1, at 1 us each: 1e4 animals for a year cost about
  2.6 core-hours.
- **On the screen** (`look_close`, `look_lapse`): the ground reads at 5 m and a 34 kg animal reads as an animal
  standing on it. Two things hide it: grass is drawn as tufts of blades taller than the animal, and only within a
  disk around the eye, so from 200 m away the animals are lost in the tufts.

**Second look** (2026-11-11, `runs2.sh`, after the user watched): grass is drawn 8-55 cm tall within 60 m of the
eye, a body 0.4 m kg^-1/3 long (a 40 kg animal 1.4 m), a mouth crops while the animal stands or walks at its
cropping pace and less from a short sward, gaits (stand, walk, run), a larger body is fled only while it comes
nearer, and the shore is turned along instead of walked into (the first look's animals looped at the shore,
put back at their last decision when they reached the sea, and 728 of 745 stood for ten minutes on a patch eaten
bare, which a slope read over 20 m around cannot see).

- Over 10 hours at a frame a minute, the median grazer walks 63 m, the top 0.6-1.2 km, grazing 20-100 minutes then
  walking about 20 m, within 100-200 m; some shuttle between two spots. No animal runs: a hunter grazes like the
  rest and does not search, so no chase is seen. No loop at the shore.
- A population of about 200 holds for 140 days (after 300 founders fall to 230 in ten days); hunters fall from 11
  to 2-3. Walking in short legs costs 9,000 decisions an animal-day against 2,366.

## Conclusion

1. **No (cost a decision yes, count no).** A decision costs 1 us, but the placeholder mind decides ten times more
   often than hoped, mostly a second at a time beside a threat. At 2.6 core-hours a year for 1e4 animals, 300 years
   of a 50 km2 island is about 800 core-hours on one thread: the world needs either decisions paced by the time a
   threat takes to close (not a fixed second) or several threads, and likely both.
2. **No as built**: the notices a decision sends grow with N. To be found before the next crate (probably the
   meeting test on 50 m buckets at 400 a km2).
3. **Half**: animals at their own size read as animals over a 5 m ground; the drawing of grass must change before
   they can be seen from afar.
