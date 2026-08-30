# e011 Rich cells: food that a small body cannot take

Date: 2026-08-30

## Purpose

e010 removed every trait rule and every seed went to the smallest grazer: three or four
digestive cells in a corner, 3,500 of them. The reason is in the world, not in the body. At the
center of a food patch a cell regrows 0.10 per step and a digestive cell takes 0.02 per step, so
a gut of five cells takes everything a cell can give; the sixth cell costs 0.002 per step and
returns nothing. Size had no reason to exist.

By principles.md (where new laws come from) we ask the real world why it has large bodies.
Elephants, whales, and the big dinosaurs live on food that is abundant and concentrated (a
tree, a swarm of krill, a forest) and regrows faster than a small mouth can take it; their size
is what lets them take it, and it then protects them. A mouse cannot eat a tree. The simplest
premise we can take from that: **a cell can hold more than one bite.** In e010's world every cell
is grass, spread thin. Here the same total regrowth falls on fewer cells, and a cell holds a
larger store. Nothing about bodies changes; whether a large gut pays is left to selection.
We do not take the other premises (a cost that falls with size, food out of reach of a short
body); they stay as candidates. e010's world is a world of microbes, one size with noise. We want
to know whether one law of the world is enough to make sizes.

## Hypothesis

1. **Gut follows the world.** The best gut is the one that keeps up with a cell: about peak
   regrowth / 0.02 digestive cells. With patch width 8 (e010) that is 5; with width 4 it is 20;
   with width 2 it is 80 (the grid holds 64). The median gut of the population will move with the
   width in that order, and the median mass in the concentrated worlds will be at least three
   times e010's (over 16).
2. **Sizes coexist.** Not one size with noise: the mass spread (standard deviation) stays above 5
   for the whole run, and the 10th and 90th percentiles of mass differ by at least a factor of 2
   in every seed of the concentrated worlds.
3. **The world stands at a bounded cost.** No extinction in 1,000,000 steps, population above
   500, at least 300 steps/s with twelve runs sharing the machine. Fewer, larger bodies should
   make the runs faster, not slower.
4. **Teeth have something to reach.** With large soft bodies in the world, hunter lineages (mean
   bite at least 2, 20,000+ steps, 20% of their food from other bodies) appear in at least a
   third of the concentrated seeds, and deaths by damage per birth rise above 0.01 there
   (e010: 0.001 at most, one hunter lineage in twelve seeds).

## Method

Code: e010 (`experiments/e010_contact`) with two world constants turned into arguments:
`RES_CAP` (what a cell can hold; e010: 1) and `PATCH_SIGMA` (the width of a food patch; e010: 8).
The total regrowth is the same whatever the width (0.01 per cell of the world per step, 164 per
step on 128x128, four patches drifting one cell every 50 steps); a narrower patch puts it on
fewer cells. Peak regrowth per cell: width 8, 0.10; width 4, 0.41; width 2, 1.63 per step.
With the defaults the program reproduces e010 byte for byte (checked on seed 9, 20,000 steps).

Physics, costs, mating, lineages, snapshots and measures: e010's. New in the log: mass at the
10th, 50th, 90th percentile and the maximum, cells with a body and the most bodies in one cell
(crowding), regrowth lost to the cap, and plant intake per digestive cell per step.

Trials (seed 9, 100,000 steps, not kept) pick the cap and widths for the runs; see below.

Run (from repo root): `cargo run --release -p e011_rich_cells -- <steps> <seed> <64|128|256> <uniform|patchy> [cap] [sigma]`
Outputs: `results/<size>_<food>_cap<cap>_sigma<sigma>_seed<seed>_{log,agents,events,lineages,dist}.csv`
and `_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

**Trials** (seed 9, 100,000 steps, one run per world, not kept). Median over the second half:

| cap / width | population | mass mean (std) | mass p10 / p50 / p90 | digestive | hard | muscle | lineages |
|---|---|---|---|---|---|---|---|
| 1 / 8 (e010) | 3,453 | 5.7 (3.8) | 3 / 5 / 8 | 5.3 | 0.05 | 0.03 | 13 |
| 1 / 4 | 2,844 | 9.1 (6.3) | 4 / 7 / 16 | 8.5 | 0.24 | 0.26 | 8 |
| 4 / 4 | 3,120 | 8.0 (6.6) | 4 / 6 / 14 | 7.4 | 0.14 | 0.20 | 5 |
| 4 / 2 | 2,213 | 15.9 (10.2) | 6 / 15 / 29 | 14.6 | 0.46 | 0.55 | 4 |
| 16 / 2 | 2,260 | 16.5 (10.1) | 7 / 13 / 28 | 13.8 | 0.52 | 0.39 | 2 |
| 8 / 1 | 1,407 | 31.9 (15.6) | 14 / 30 / 52 | 28.1 | 0.62 | 0.41 | 2 |

The width is the lever; the cap is not (a crowded cell is emptied every step, so a store never
builds up: regrowth lost to the cap is 0-1.2 of 164 per step in every trial). Mass is stable from
20,000 steps on. The runs therefore vary the width and fix the cap at 8 (above the peak regrowth
of width 1, so that no regrowth is lost to it).

**Runs**: width 4, 2 and 1, cap 8, seeds 1-4 each, 1,000,000 steps, 128 patchy; twelve at once on
one 12-core machine, one thread each. Reference: e010's runs (width 8, cap 1, seeds 1-12).

## Result

12 runs, 1,000,000 steps each (`results/128_patchy_cap8_sigma{4,2,1}_seed{1..4}`), twelve at once on
one 12-core machine, one thread each. Ranges are over the four seeds of a world (medians over
the second half of the run; the report's table uses the whole run, so its numbers differ a
little); e010's numbers are its twelve seeds. Report: `report.html`.

| | width 8 (e010) | width 4 | width 2 | width 1 |
|---|---|---|---|---|
| regrowth per cell per step, peak | 0.10 | 0.41 | 1.63 | 6.5 |
| population, median | 3,360-3,512 | 2,890-3,272 | 2,107-2,374 | 1,138-1,998 |
| mass per body, median of means | 5.2-5.9 | 6.9-9.6 | 14.5-16.3 | 17.6-43.4 |
| spread of mass, minimum of std | 2.9-3.9 | 3.7-5.4 | 5.7-8.8 | 13.9-18.5 |
| mass p10 / p50 / p90 at 1,000,000 | 3 / 5 / 8 | 3-4 / 6-8 / 10-17 | 2-7 / 7-13 / 25-56 | 3-8 / 12-56 / 48-64 |
| digestive cells per body | 5.0-5.5 | 6.3-8.7 | 9.6-14.1 | 10.5-15.6 |
| hard cells per body | 0.04-0.14 | 0.05-0.27 | 0.57-5.5 | 5.6-25.6 |
| most bodies in one cell | 6 | 12 | 27-28 | 45-77 |
| intake per digestive cell per step | - | 0.0064-0.0078 | 0.0051-0.0079 | 0.0076-0.0093 |
| shell (mean tip hardness) | 1.00-1.06 | 1.02-1.09 | 1.17-2.38 | 2.29-8.13 |
| bodies with a bite | 0-0.3% | 0.1-0.3% | 0.3-12% | 12-24% |
| meat share of intake | 0.01-0.2% | 0.01-0.04% | 0.02-12% | 9-19% |
| cells broken per step | 0.1-1.7 | 0.1-0.9 | 0.6-260 | 260-553 |
| deaths by damage per birth | 0.0000-0.0012 | 0.0000-0.0002 | 0.0000-0.018 | 0.0015-0.016 |
| hunter lineages (bite >= 2, 20,000+ steps) | 0 (one of 12,000 steps) | 0 | 0, 44, 0, 4 | 26-50 |
| longest hunter lineage (steps) | 12,000 | - | 0-310,000 | 156,000-483,000 |
| lineages alive, median | 8-17 | 4-8 | 1-6 | 5-13 |
| steps per second, median | 389-666 | 376-656 | 650-806 | 585-846 |

- **The gut follows the world, the crowd more.** Digestive cells 5, 7, 13, 14 as regrowth per cell
  goes 0.10, 0.41, 1.63, 6.5 (the gut that would take one cell alone: 5, 20, 80, 330). The rich
  cells are shared by 12, 28, 45-77 bodies, emptied every step, and each digestive cell gets
  0.005-0.009 per step in every world. Mass rises more than the gut (8, 15, 18-43): at width 1
  a body is mostly armor.
- **Sizes coexist** at width 2 and 1 (spread of mass never below 5.7 and 13.9; p90 at least 2.0
  times p10 at every log step in all twelve runs). At width 1 the size distribution has two
  humps: 3-27% of bodies have at most 4 cells, 3-28% have 60 or more. The most common bodies
  (width 1, seed 4, step 1,000,000): a full square with a two-cell wall of hard around a 4x4 gut
  (28 hard, 16 digestive; 186 agents), and 2-4 digestive cells sitting only in the corners of the
  grid (65 agents). A hunter's muscle is in the middle rows, so its force is in lines 2-5; a cell
  in line 0 or 7 is never in a line where a tooth has force. The corner is a shape that cannot be
  bitten; nobody wrote it.
- **The arms race starts.** At width 1 in every seed, hard is above 1 per body from step 10,000;
  12-24% of bodies have a bite; 260-550 cells break per step; meat is 9-19% of all energy eaten.
  Hunter lineages: 26-50 per seed, the longest 156,000-483,000 steps, with 26-34% of their food
  from other bodies as a rule; width 1 seed 3 has three lineages at 83-85% meat (mass 41-59, hard
  30-44, muscle 6-12, digestive 3). Armor answers: shell 2.3-8.1 (a two-cell wall is 6); in seed 4
  hard goes from 8 to 25-32 per body between 200,000 and 500,000 steps while the meat share
  halves (18% to 8-10%). Width 2 is the edge: seeds 2 and 4 flip into this regime (at 280,000
  and 600,000 steps; seed 2 went from hard 0.4 to 12.3 in one 100,000-step window), seeds 1 and 3
  never do (hard at most 1.4). Width 4: nothing (hard 0.05-0.27, meat 0.01-0.04%).
- **The world stands**, no extinction, population never below 950; fewer, larger bodies run
  faster (width 1: 585-846 steps/s). The contact loop at 6,000-13,000 pushes per step does not
  slow it. The cap: 0-7 of 164 per step lost to it; it did nothing in the trials.

## Conclusion

1. Gut follows the world: partly. Right order, wrong proportion: the bodies crowd and share the
   cell, so the gut goes 5 to 10-16, not to 20-330. Mass passes 16 only at width 1.
2. Sizes coexist: yes at width 2 and 1. Specks, tortoises and hunters on one island.
3. The world stands at a bounded cost: yes.
4. Teeth have something to reach: partly. Hunter lineages in 6 of 8 concentrated seeds (all four
   at width 1), lasting up to 483,000 steps; deaths by damage per birth above 0.01 in only two,
   because a bite mostly takes one cell of a tortoise.

What this changes:
- One law of the world (the same regrowth on fewer cells) gives size a reason and starts the
  arms race that no trait rule reached in e005-e010. The reason for size is not the gut but
  armor; the reason for armor is the crowd; the reason for the crowd is the concentration of
  food. The three things a hunter needed at once (a tooth, a policy that moves into occupied
  cells, kin it does not hurt) are all cheap in a crowd: every move is a push, and an armored
  parent has armored children.
- The metaphor gave the premise (a cell holds more than one bite) and the world gave its own
  answer (tortoises, not elephants). That is the intended use of principles.md, "where new laws
  come from": take the premise, not the outcome.
- Keep the patch width as a law of the world: 1 for the arms race in every seed, 2 for the edge
  (half the seeds). Drop the cap (no effect: a crowded cell never fills).
- The 8x8 grid is the wall now: the 90th percentile of mass is 64 at width 1. That is the
  argument for #5 (3D bodies or a larger grid), stated by the population, not by us.
- Open: what decides the flip at width 2 (one lineage finding the tortoise and the tooth close
  together?); lineages are fewer (1-13 alive) than in e010 (8-17), one holder per island at a
  time; the crowd is partly the drift rule (bodies following a patch one cell wide).
- Next: a world with both kinds of place in one run (wide patches and narrow ones, grass and
  trees), so that e010's grazers and these tortoises are neighbors and lineages can move between
  them; then #5, then #4.
