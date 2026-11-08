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

## Conclusion
