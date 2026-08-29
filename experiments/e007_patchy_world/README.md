# e007 Patchy world: does a bigger world with patchy food give eyes a reason to exist?

Date: 2026-08-29

## Purpose

Sensor blocks never evolve. In e005 and e006 the population mean is below 0.1 sensor blocks per
body, and the reason is measurable: food is eaten down uniformly (mean 0.15 of 1.0, under 6% of
cells above 0.5), agents fill 5% of the cells and move almost every step, and food regrows +0.01
everywhere. Nothing at distance 2 tells an agent what distance 1 does not, and a full eye costs 8
blocks of upkeep. This experiment changes the environment, not the agents: a world where food and
other agents are far apart, and where food has a shape in space, so that seeing two cells further
could pay. We watch whether sensor blocks appear. We do not tune for it.

This is the environment half of issue #8; the policy half (what a neighbor input carries) stays
there.

## Hypothesis

1. **Density alone does not do it.** A 256x256 world with the same laws (16x the cells, uniform
   regrowth) has fewer predation deaths per birth than 64x64, and sensor blocks stay where they
   are: population mean below 0.5 in every seed.
2. **Patchy food does.** With regrowth concentrated in drifting patches, sensor blocks rise above
   the e005/e006 level in at least one seed: population mean above 1 for at least 100,000 steps,
   and the sensors are used (the move differs from the sense-less choice in more than 10% of the
   decisions of agents that have them).
3. **Cost.** The step scales with the number of cells and agents (16x); the 256x256 world stays
   above 500 steps/s, so 1,000,000 steps fit in an hour.

## Method

World, bodies, costs, predation, policy, mating (sexual, D = 6, radius 1), and lineage detection
exactly as e006. Two things are new.

**World size** is an argument (64 or 256). The initial population scales with the area (400 per
64x64, so 6,400 on 256x256). No population cap exists in this world; food per cell is the same law,
so the 256 world should carry about 16x the agents.

**Food law**, `uniform` or `patchy`. Uniform is e006: every cell regrows +0.01 per step up to 1.0.
Patchy: one patch per 4,096 cells (1 on 64x64, 16 on 256x256), each a Gaussian of width sigma = 8
cells around a center; the centers take a random step of one cell every 50 steps (a patch crosses
its own width in about 800 steps, five agent lifetimes, and the spacing between patches in about
50,000 steps). The peak regrowth is set so that the regrowth summed over the world equals the
uniform law's: 0.01 * 4096 / (2 pi sigma^2) = 0.102 per step at a center, under 0.001 beyond 3
sigma. The cap at 1.0 wastes more of it (a center cell fills in 10 steps), so the food actually
added is logged too. Simplest law with a real gradient; a noise field was the alternative.

`64 uniform` is the control and reproduces e006 sexual (checked: seed 1, same snapshots and lineage
rows for 20,000 steps).

Measured, every 10,000 steps, on top of e006's log: share of agents with at least one sensor block;
decisions made by agents with sensors and the share of those where the chosen move differs from the
move the same policy picks with sense = 0 (the sensor "in use"); standard deviation of food over
the cells and share of cells above 0.5; food actually added per step. Lineages and events as e006.
Lineage detection links one representative per distinct gene list, then attaches the copies
(same groups as all pairs, needed at 4,000 agents).

Runs: 64 and 256, uniform and patchy, seeds 1-3, 1,000,000 steps; 12 runs sharing one 12-core
machine. `64 patchy` separates the patch effect from the size effect.

Run (from repo root): `cargo run --release -p e007_patchy_world -- <steps> <seed> <64|256> <uniform|patchy>`
`EVLOG_THREADS=n` sets the threads used for development (default: all cores). Development is 75% of
the step on the 256 world (profiled: `develop_genes` plus its `expf`), so the children born in one
step are developed together on several threads, in birth order, with the same result. One run goes
from 26.7 s to 14.3 s per 20,000 steps (1 vs 12 threads; about 10 developments per step is the
ceiling). It shortens one run only: runs sharing a machine should split the cores between them.
A body cache by gene list also skips children whose list a living agent already has (13% fewer
developments than parent-reuse alone). Both were added after the runs above; outputs are
byte-identical (checked on seed 9, 20,000 steps).
Outputs: `results/<size>_<food>_seed<seed>_{log,agents,events,lineages,dist}.csv` and
`_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

## Calibration: is 128x128 (4 islands) a scale model of 256x256 (16 islands)?

Added after the runs above, to decide whether later experiments can use the 4x cheaper world.

**Purpose.** e007 found that the number of islands, not the area, does the work. If quantities that
live on one island are the same per island at 4 and at 16 islands, questions about bodies and
behavior can run on 128x128 with more seeds for the same compute, and 256x256 is kept for
questions about lineages across islands.

**Hypothesis.** Per-island quantities that live on an island match 256 patchy within the seed
spread: population per island, body composition (hard, muscle, attack), predation deaths per
birth, food actually added per island. Quantities that live between islands are lower at 4
islands: lineages alive per island and events per 1,000 steps per island (64 patchy, one island,
already showed 2-4 lineages and long lifetimes). Sensor lineages: the rate per island-step is the
same, so 4 islands give a quarter of the chance per run.

**Method.** `128 patchy`, seeds 1-3, 1,000,000 steps (4 patches, initial population 1,600). Same
measures as above, divided by the number of islands (1, 4, 16 for 64, 128, 256 patchy), compared
with the 64 and 256 patchy runs. Run: `cargo run --release -p e007_patchy_world -- 1000000 <seed> 128 patchy`.

**Result** (`results/128_patchy_seed{1,2,3}`; per island = divided by 1 / 4 / 16 for 64 / 128 / 256;
seeds 1 / 2 / 3):
- On an island, 128 matches 256. Population per island 228 / 219 / 266 vs 217 / 228 / 242. Predation
  deaths per birth 0.32 / 0.31 / 0.44 vs 0.31 / 0.39 / 0.44. Meat share 2.6-3.9% vs 2.9-4.3%. Food added
  per step per island 40.5 both; food per cell 0.062-0.068 vs 0.056-0.065. Body: hard 32-38 vs 37-40,
  attack 2.5-4.0 vs 2.0-2.7 (64: 2.3-4.5); within the spread, a little more attack at 128.
- Between islands, the count matters. Lineages alive per island 1.6 / 1.3 / 1.8 at 4 islands vs
  1.3 / 0.9 / 0.8 at 16 (and 4 / 3 / 2 at one island); median lifetime 19,000 / 14,500 / 15,500 vs
  12,000 / 11,000 / 10,000 (one island: 13,000-34,000). Fewer islands, more isolation: each island
  keeps its own lineage longer, and sweeps across islands are rarer. Events per 1,000 steps per
  island 0.06-0.11 vs 0.04-0.09.
- Sensor lineages per island are of the same order: 128 seed 3 has 2 (0.5 per island, sensor mean
  above 1 for 140,000 steps); 256 has 0.5 and 2.3 per island in seeds 1 and 3. A quarter of the
  islands, a quarter of the chances per run, as expected.
- Speed: 3,100-4,200 steps/s with 4 threads each, three runs at once; 1,000,000 steps in 4-5 minutes.

**Conclusion.** 128 is a scale model of 256 for what happens on an island (population, food,
predation, body composition, the rate at which sensor lineages appear). It is not one for what
happens between islands: lineages per island and lineage lifetime move with the number of islands.
Use 128 with more seeds for questions about bodies and behavior (#7, the sensor knockout, #8);
use 256 for questions about lineages across islands and for the world people watch.

## Result

12 runs, 1,000,000 steps each (`results/{64,256}_{uniform,patchy}_seed{1,2,3}`), all twelve sharing a
12-core machine. Numbers are per seed 1 / 2 / 3 unless noted. Report: `report.html`.

- Population, median: 64 uniform 257 / 220 / 252; 64 patchy 204 / 196 / 210; 256 uniform 3,742 /
  3,808 / 3,762; 256 patchy 3,478 / 3,645 / 3,868. Agents fill 5.7-6.3% of the cells in every
  variant: food per cell is the same law, so the 256 world is the 64 world sixteen times over, not
  a sparser one.
- Sensor blocks per body, median (max), and steps with the mean above 1: 64 uniform 0.04 (1.9) 20k,
  0.00 (0.3) 0, 0.29 (2.2) 220k; 64 patchy 0.00 (2.9) 40k, 0.01 (2.4) 90k, 0.31 (4.3) 320k (the
  initial random bodies, gone by step 300,000); 256 uniform 0.06 (0.3) 0, 0.04 (0.1) 0, 0.24 (1.1)
  20k; 256 patchy 0.22 (0.9) 0, 0.02 (0.2) 0, **1.12 (2.0) 820k**. Agents with at least one sensor,
  median share: 256 patchy 12 / 0 / 42%; 256 uniform 2 / 0 / 11%.
- The 256 patchy seed 3 plateau is one lineage: lineage 508, confirmed at step 121,000, alive at
  1,000,000, mean sensor blocks at least 2 for 878,000 steps, up to 601 agents. Body: armored grazer
  (46 hard, 15 digestive, 0 muscle, attack 0) with 2-3 sensor cells inside the shell (sense =
  sensors / 8, so a quarter of an eye). Seed 1 grows a similar lineage (2041, sensor 2.1, up to 995
  agents) from step 558,000. Every sensor lineage in any run is a grazer.
- Sensors in use (share of moves by agents with sensors that differ from the blind choice), median:
  64 uniform 15 / 12 / 11%; 64 patchy 23 / 17 / 19%; 256 uniform 10 / 13 / 8%; 256 patchy 15 / 15 /
  20%. Patchy food makes the distance-2 input change the choice more often, at any world size.
- Does the eye pay? Grazers (0 muscle, age at least 50, second half of the run), plant intake per
  digestive block per step, with sensors vs without: 256 patchy seed 3 0.0131 vs 0.0137; seed 1
  0.0119 vs 0.0125; 256 uniform seed 3 0.0129 vs 0.0128. No measurable gain. Two sensor blocks cost
  0.004 per step against an intake of about 0.2 per step: within 2% of free.
- Food: added per step (after the cap) 41 / 41 / 41 vs 40 / 38 / 40 on 64, 655 / 655 / 655 vs 650 /
  643 / 650 on 256: the patches are eaten as they regrow. Mean food per cell 0.15 uniform vs 0.06
  patchy (256); cells above half 1-2% in both.
- Predation deaths per birth: 64 uniform 0.70 / 0.38 / 0.59; 64 patchy 0.26 / 0.30 / 0.27; 256
  uniform 0.62 / 0.71 / 0.71; 256 patchy 0.31 / 0.39 / 0.44. Meat share of intake 5-6% uniform,
  3-4% patchy (256). Mean attack per body 3.7-5.0 uniform, 2.0-2.7 patchy (256).
- Lineages alive, median: 64 uniform 3 / 2 / 2; 64 patchy 4 / 3 / 2; 256 uniform 4 / 6 / 6; 256
  patchy 21 / 13 / 12. Lineages over the run: 256 uniform 282 / 149 / 281; 256 patchy 754 / 334 /
  420. Splits: 256 uniform 277 / 143 / 274; 256 patchy 750 / 327 / 414. Median lifetime 7,000-9,000
  steps on 256 uniform, 10,000-12,000 on 256 patchy, 13,000-34,000 on 64 patchy (one island).
- Speed, median (min) steps/s: 64 worlds 4,800-9,900 (all above 2,000); 256 uniform 586 (438), 730
  (525), 566 (246); 256 patchy 445 (348), 512 (295), 387 (293). A 256 run took 25-45 minutes.
- `64 uniform` seed 1 matches e006 `sexual_d6_r1_seed1` byte for byte (snapshots and lineage rows,
  checked for 20,000 steps).

## Conclusion

1. Density alone does not do it: partly. Sensors stay at a median 0.04-0.24 per body on 256
   uniform, as predicted. But the premise was wrong: a bigger world with uniform food is not a
   sparser world. Food per cell sets the density, so predation deaths per birth are the same
   (0.62-0.71) as on 64 (0.38-0.70), and the world is e006 sixteen times over.
2. Patchy food does: yes, in one seed fully and one seed late. 256 patchy seed 3 holds a sensor
   mean above 1 for 820,000 steps with 42% of agents carrying sensors and the sensor changing 20%
   of their moves; seed 1 reaches 0.8 in its last 300,000 steps; seed 2 has none. This is the first
   environment in the project where sensor blocks stayed.
3. Cost: partly. 390-730 steps/s median on 256 with twelve runs sharing the machine, four of six
   above 500; minimum 250.

What this changes:
- Patchy food becomes a law of the world. Beyond the sensors, it cuts predation in half and
  multiplies lineages by three: each patch is an island with its own kin group, and the patches
  drift, touch, and merge. That is closer to `vision.md`'s "lineages that appear, spread, and go
  extinct" than one mixed population, and it is what the viewer shows: green islands, each with
  its colors, and a desert between them.
- Eyes are present but not proven to pay. Grazers with sensors take in no more food per digestive
  block than grazers without, and two sensor blocks cost 2% of a grazer's intake, so a good body
  plan can carry them for free. Two cheap tests settle it: a knockout (same world, sense forced to
  0 for everyone; if lineage 508 still wins, the eyes were passengers), and inputs that reward
  seeing (issue #8). Do both before building anything on sensors.
- The 256 world is the world for the next experiments: the viewer needs its islands, and the cost
  is linear in agents (per-agent cost unchanged). The 64 patchy world with a single patch was not
  different from uniform; it is the number of islands that does the work, not the patchiness of
  one.
- Open: one patch width, drift speed, and density were run, chosen for gradients and not tuned.
  Pace is a question again: 12-21 lineages turning over every 10,000-12,000 steps is a lot of
  change for a viewer.
- Next in order: #7 (prey worth eating), then #8 with the knockout.
