# e063: bodies on the stage-B world (foundation stage C, first step, #76)

Date: 2026-09-14

## Purpose

#76's agreed first step: port the bodies onto the world that passed stage B and measure what a step
costs before deciding how stage C runs (threads for the bodies, or a window of the world). The cost
turns on a number nobody knows yet: how many bodies this world feeds. `foundation.md` costed stage C
from e058's densities scaled to 512 (9,600 bodies in a thin world, 47,000 in a crowded one), but
e062's grass grows 0.0004-0.0006 a step per land cell, a twentieth of e059's sun. So the prototype
answers three things at once: the cost per step at 512, the bodies the world feeds, and whether the
world stands with them.

This is not a law test. No law about a body is new; what joins the two worlds is the least the port
needs (below), and every material trade-off of `foundation.md` section 2 is still to build.

## Hypothesis

Written before the runs.

1. **Few bodies.** The world feeds 500-3,000 bodies, 3-20 times fewer than the thin world
   `foundation.md` assumed. The grass grows about 55 a step on c1225's land and 67 on c1236's; a
   body of 16 blocks pays 0.064 a step, and eating the dead gives back up to twice the plant (e026).
2. **Cheap.** The world costs about 1 ms a step (e062: 8.9 and about 12 ms an update, every 10
   steps) and a body about 5 µs (e059), so a step costs at most about 16 ms and a run of 300,000
   steps under 1.5 hours on one core: stage C needs neither threads nor a window at this density.
3. **It stands.** The bodies do not die out in 100,000 steps (8 years of c1225, 7.6 of c1236), and
   the world's matter holds to 1e-9.
4. **Warm grass holds them.** The bodies live on the warm moist and wet land, where the grass
   stands; the cold habitats (under 5 C a quarter, where nothing grows) hold under 5% of them.

Decision rule: if a 300,000-step run at the population the pilot settles to costs at most 2 hours on
one core, stage C runs its seeds in parallel, one core each. If not, the split of the cost says
which: threads when the bodies dominate, a window when the world does.

## Method

Code: `experiments/e063_bodies`. The world is e062's (`climate.rs`, `habitat.rs`, `plants.rs`,
unchanged but for the dead), the bodies e059's with every law its season world kept (`body.rs`:
development and a grown side, weight by kind and density, corners hold, space at the body's
resolution, contact and the tooth, work, the motor, the store, strict upkeep, wear, the clock at
0.5, eyes to 8, mutation per base, mating within 6 genes). The laws e059 carried at 0 are gone.

**What joins them** (choices of the port, stated so they can be changed, not tested here):

- A body lives on land: a sub-cell of the sea is a wall.
- A gut takes from the grass on its world cell and the dead lying there (`carrion`) in their
  proportions. Wood, algae and litter are not food yet.
- What a body spends (the upkeep its fat pays, the fat its flesh cannot hold, the work of moving)
  goes to the soil under it (e019). Through e062's air pool it would rain on the sea by the sea's
  share of the rain and drain the land within years.
- The dead rot into their cell's soil at 1% a step (e017), on the producers' 10-step clock.
- Bodies start at e006's density on land (0.0977 per land cell) with random genomes.

**The worlds.** c1225 (warm, very wet) and c1236 (cool) with e062's draw d11, grown exactly as e062
grew them (spin-up, then 17 and 16 years of producers), built once and kept in `results/worlds/`.

**Runs.** One pilot per world, seed of life 9, 100,000 steps, one thread each, on the Mac:
`bash experiments/e063_bodies/run.sh <world> 100000 9` from the repo root. Measured every 1,000
steps (`log.csv`): the bodies, the cost split into the world, the bodies and the lineages, where
the bodies are by temperature and moisture band, what they eat, and the matter's drift.

Both worlds were grown in 236 s (c1225) and 266 s (c1236) on one core; the grass, wood and algae a cell
match e062's last year (c1225 0.51/0.25/0.15, c1236 0.555/0.63/0.08). Both pilots were run twice: the
second time with the body's cells added to `agents.csv` for the report's gallery. Apart from the wall
times, the two runs of each world wrote the same logs, bodies and lineages.

**Control.** After the pilots, each world was run without bodies (`start=0`, seed 9, 100,000 steps, 97
and 102 s), to tell what the bodies do to the grass, the wood and the fire from what the world does
alone over the same steps. The first reading compared with e062's last year instead: it put the fire
at a fifth to a third of the world's without bodies (it is half) and could not say whether the wood's
fall was the bodies' or the code's (it is the bodies').

## Result

Second half of each run (steps 50,000-100,000). `report.html` has the charts.

| | c1225 (warm, very wet) | c1236 (cool) |
|---|---|---|
| bodies: mean (lowest-highest) | 306 (186-494) | 314 (156-878) |
| land cells per body | 362 | 534 |
| grown bodies (age 300+) | 197 | 155 |
| lineages alive (top lineage's share) | 2.1 (77%) | 2.7 (58%) |
| a step: world + bodies + lineages | 1.02 + 0.32 + 0.00 ms | 1.09 + 0.25 + 0.00 ms |
| a step of the world alone (control) | 0.96 ms | 1.01 ms |
| a body a step | 1.05 µs | 0.81 µs |
| 100,000 steps, wall | 143 s | 153 s |
| intake: grass / kills / the dead | 95% / 2% / 3% | 92% / 5% / 3% |
| ways of living (e060): per body, per lineage | 1-2, 1 | 2, 1 |
| grown bodies: plant, no tooth, roams | 92% | 90% |
| median distance of a grown body from its birthplace | 35 cells | 28 cells |
| median mass; mean muscle, gut, hard blocks | 26; 11.7, 12.5, 0.04 | 20; 9.9, 11.9, 0.15 |
| bodies with a tooth | 0.2% | 2.3% |
| bodies in cold / mild / hot habitats | 10% / 13% / 78% | 7% / 62% / 31% |
| bodies on dry / moist / wet land | 25% / 41% / 33% | 5% / 15% / 80% |
| age at death, median / p90 | 312 / 1,704 | 216 / 1,026 |
| grass / litter / wood standing, of the control's | 23% / 28% / 81% | 18% / 39% / 84% |
| land burnt a year: control → with bodies | 0.9% → 0.5% | 1.3% → 0.6% |
| matter drift, largest | 4e-14 | 5e-14 |

1. **Few bodies: no.** 306 and 314 on average, 3-20 times fewer than the 500-3,000 expected and 30 times
   fewer than the 9,600 `foundation.md` costed stage C at. The random start (8,438 and 14,072 bodies)
   crashes within 1,000 steps.
2. **Cheap: yes.** 1.34 and 1.35 ms a step, of which the world's update is 76% and 81%; 300,000 steps
   take 7 minutes on one core. A body costs 0.8-1.05 µs, a fifth of e059's 5.1 µs (that slope was measured
   between 600 and 3,000 bodies at 128, twelve runs sharing the machine; here two ran at once).
3. **It stands: yes.** No world falls under 156 bodies; matter drifts by 5e-14 at most.
4. **Warm grass holds them: no.** The cold habitats hold 10% and 7% of the bodies, not under 5%. Most
   bodies live on the hot land of c1225 (78%) and the mild wet land of c1236 (80% wet).

What the bodies do to the world, few as they are, against the control over the same steps: the grass
stands at 18-23% (grass grows by its own cover, so a stand bitten down grows back slowly), the litter at
28-39%, and the land burns half as much (0.5% against 0.9% a year on c1225, 0.6% against 1.3% on
c1236). The soil on land holds 1.6-2.7 times the control's: the matter of the grass and litter. The
wood, which no body eats, stands 16-19% lower and is still falling at the end (30% and 22% under the
control); these logs do not show the route. The random start adds its bodies' energy to the world
(2.0% and 3.4% of its matter); from there the matter holds to 5e-14.

The bodies live one way. On both worlds 90-92% of the grown bodies eat grass, carry no tooth and roam
(e060: 8 cells from the birthplace or more); counted per lineage there is one way. They are half muscle
and half gut, with almost no armor or sensor, and walk: the median grown body stands 28-35 cells from
where it was born (e058's thin world: 13.8). Kills are 2-5% of the intake.

## Conclusion

**Threads or a window: neither.** At 512 the world costs about a millisecond a step and the bodies this
world feeds add a third of that. Stage C runs one core a seed, 300,000 steps in minutes. This holds at
this density; at a crowd the bodies' share will grow (e059's 5.1 µs a body was measured in a crowd), and
a density of tens of thousands of bodies would bring back the question.

**The open number is the density.** The bodies keep e059's economy (a 16-block body pays 0.064 a step)
while e062's grass grows 0.0004-0.0006 a step a land cell, a twentieth of e059's sun: a body lives on
360-530 land cells, far thinner than e058's thin world, which already had lost most of its ways of
living for want of a crowd (#68 rule 2). At this density one way of living holds each world, and no
trade-off of `foundation.md` section 2 could be judged.

**Stage B's balance moves under grazers.** Against the world without them, 300 bodies hold the grass at a
fifth, halve the fire, and lower the wood, which nothing eats.
The fire line of stage B (1-20% of the land a year) was met without anything eating the fuel; with
bodies both worlds burn 0.5-0.6%.

These answers hold for this world and these choices: one seed a world, 100,000 steps, e059's body economy
unchanged, bodies on land only, grass and the dead as the only food, what a body spends to the soil under
it. None of the three choices of the join was varied.

**Next.** Before the trade-offs are built, the ratio of what a body draws to what the plants grow has to
become a parameter of stage C and be set where the world holds a crowd, and the cost measured there. The
options and a recommendation are in #76.
