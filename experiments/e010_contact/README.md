# e010 Contact physics: what can a body do when nothing is defined but its materials?

Date: 2026-08-30

## Purpose

Every experiment since e005 hit the same wall: attack = min(hard in the front three rows,
muscle) is at most 24, defense = hard / 2 goes to 32, and every body is a full 8x8 square. e008
could not raise meat with a prize, e009 could not with perception. The wall was one of our own
rules, and it was written at the wrong level: attack, defense, gut, the escape roll, and "kin do
not eat kin" are traits, not materials (principles.md, 2). This experiment removes every trait
read-out and keeps only what a block is and what the world is. Whatever a body can do (bite,
armor, hide, hurt its kin) has to come from its shape, its materials, and the way it moves. We
do not tune for any outcome; we watch what the physics allows.

## Hypothesis

1. **The world stands at a bounded cost.** No extinction in 1,000,000 steps; population between
   1,000 and 5,000 (the per-body cost bounds it at regrowth / UPKEEP_BODY, about 5,000 on
   128x128); at least 400 steps/s per run with twelve runs sharing the machine.
2. **Shape is free and used.** Bodies leave the square: full 8x8 bodies are under 10% of the
   population, the median mass is under 32, and the mass spread (standard deviation) is above 3
   for the whole run in every seed.
3. **Teeth come from shape, and armor answers.** A hunter is a hard tip with muscle behind it
   in the line it moves along; the smallest one is four cells. Its arithmetic beats grazing (a
   broken cell of a grazer holds about 0.3, a step of grazing about 0.05), so selection should
   find it: in at least half of the twelve seeds, a lineage with mean bite at least 2 (a hard
   tip with two muscle cells behind it, enough to break a soft tip) lasts 20,000 steps or more
   and takes at least 20% of its food from other bodies, and deaths by damage per birth rise
   above 0.05 in those seeds. Where teeth appear, shells follow: the mean tip hardness of the
   population rises above 1.2 within 100,000 steps of the first hunter lineage.

## Method

World, food law, mating, lineages, snapshots: e007 `128 patchy` (four drifting patches, sexual
mode D = 6, the diet columns of e008 in the lineage log). Bodies grow from the genome as in
e004 (8x8 grid, 5 kinds). Removed: attack, defense, gut, the escape roll, the kin exclusion, the
kill rule, and the `who` inputs of e009 (the policy sees e007's ten inputs). Added, as material
and world laws only:

- **A cell costs what it holds.** Building a child's body costs the parent CELL_ENERGY = 0.02
  per cell, on top of the halving; eating a broken cell yields the same 0.02 plus the cell's share
  of its body's energy (energy / mass). Energy is conserved through a bite, except when the
  pusher has no digestive cells (then it is lost).
- **A body costs something besides its cells.** UPKEEP_BODY = 0.032 per step (the upkeep of 16
  cells) on top of UPKEEP = 0.002 per cell. Added after the first trials (below).
- **Force acts the way a body moves.** When a body moves toward a cell that holds other bodies,
  it pushes into each of them along the facing side, line by line (8 lines). In a line where both
  have a cell, the tips are the outermost cells; the pusher's force in that line is its muscle
  cells in the line; a hard tip has hardness 3 per contiguous hard cell behind it, any other tip
  has hardness 1. The softer tip breaks if the force exceeds its hardness (a soft tip crushes
  against armor; armor breaks under a strong push); equal hardness, nothing. A stationary body
  pushes nobody.
- **A broken cell is gone.** The body's cells, mass, counts and tips are recomputed; upkeep
  drops with mass; the split threshold (2 + 0.1 mass) drops too. A body with no cells left dies
  (`deaths_broken`). A child gets the birth body of its gene list, not the parent's damaged one.

Measured, every 10,000 steps: cells broken, contacts (pushes into an occupied cell), deaths by
damage and their age, energy per broken cell, meat share of intake, agents fed mostly on other
bodies; shape: mass mean and spread, full squares, damaged bodies, open lines per body (lines
with no cell to touch, of 32), **bite** (largest force behind a hard tip; a rule-free measure, no
rule reads it), **shell** (mean hardness of the touchable tips), share of bodies with a bite.
Per lineage: mass, bite, shell, open lines, diet.

**Trials before the runs** (seed 9, 20,000-40,000 steps, not kept):
1. Contact every step between every adjacent pair, cells free to build: a cannibal soup. 85
   births and 4,700 broken cells per step, meat 4.5x plants, bodies of 25 cells that were mostly
   muscle. Breeding bodies to eat them was an energy source (0.02 per cell from nothing).
2. Cells cost energy to build; force only in the direction of movement: the soup is gone, and
   the smallest body wins. 14,000 bodies of 4-5 cells, 421 steps/s. Plant intake is capped by
   the food in one cell whatever the body, and upkeep is per cell, so a 4-cell body is the best
   grazer; in e005-e009 only the defense rule made bodies large.
3. With UPKEEP_BODY: 3,300 bodies of 6 cells, 1,400 steps/s with 8 threads. Kept.

Runs: seeds 1-12, 1,000,000 steps, 128 patchy; twelve at once on one 12-core machine, one thread
each. Reference: e009 `counts` (e007's law on the same world).

Run (from repo root): `cargo run --release -p e010_contact -- <steps> <seed> <64|128|256> <uniform|patchy>`
Outputs: `results/<size>_<food>_seed<seed>_{log,agents,events,lineages,dist}.csv` and
`_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

## Result

12 runs, 1,000,000 steps each (`results/128_patchy_seed{1..12}`), twelve at once on one 12-core
machine, one thread each (390-670 steps/s median; 35-45 minutes per run). Ranges are over the
twelve seeds unless noted. Report: `report.html`.

- The world stands: no extinction; population median 3,360-3,512 (minimum 2,676, maximum 3,669),
  two thirds of the bound regrowth / UPKEEP_BODY. e007's law carried 900-1,100 on the same food.
  Births equal deaths by starvation at 25 per step; median age 320 steps; median energy 1.3.
- Shape: mass per body 5.2-5.9 (median of means), spread 2.9-3.9; full squares at most 0.1-0.3%;
  20-22 of 32 lines open (nothing to touch). Hard 0.04-0.14, muscle 0.02-0.20, sensor 0.03-0.19,
  digestive 5.0-5.5 per body. The most common bodies (seed 1, step 1,000,000) are 3, 4 and 5
  digestive cells packed into the bottom-left corner of the grid, 20% of the population between
  them, among 514 distinct bodies. Mass falls from about 30 (random start) to 5-6 within 20,000
  steps in every seed.
- Teeth: bite per body 0.00-0.01 median, 0.01-0.34 maximum; bodies with a bite 0.3-8.9% at their
  peak; hunter lineages (mean bite at least 2 for 20,000+ steps) 0 in all twelve seeds; lineages
  with a mean bite of 1 or more at any detection 0-5 per seed, all short. Shell 1.00-1.06 median,
  1.06-1.62 maximum. Cells broken 0.12-1.73 per step, pushes 163-404 per step, deaths by damage
  per birth 0.0000-0.0012, meat 0.01-0.2% of intake, agents fed mostly on other bodies 0.1-8.2%
  at their peak.
- The one hunter: seed 1, lineage 1136, confirmed at 985,000: mass 18-22, hard 4-6, muscle 6-8,
  digestive 6-12, bite 2.4-2.9, 58% of its food from other bodies at its peak; 181,000 cells
  broken and 3,267 bodies killed in the window 980,000-990,000 (bodies with a bite: 3 at
  985,000, 69 at 990,000, 16 at 995,000, 1 at 1,000,000); the lineage went from 45 to 7 agents
  in 5,000 steps. Its arithmetic is good (a grazer's cell holds about 0.3, ten steps of grazing);
  the likely cost is that a body that pushes with a tooth also breaks its own children, which
  are born next to it.
- Speed: 389-666 steps/s median per run, set by the number of bodies.
- Lineages alive 8-17 (e007's law: 4-9); median lifetime 11,000-20,000 steps.

**Extension.** Seed 1 rerun to 2,000,000 steps (`results/128_patchy_seed1_2M_{log,lineages,events}.csv`;
the first million is the same run byte for byte). In the second million: population 3,542, mass
5.2, bite 0.00 at every log step, no body with a bite above 0.1% of the population, meat 0.0000%
of intake, 0.01 cells broken per step. The hunter of step 985,000 did not return, and no other
appeared: over the whole 2,000,000 steps, two lineages ever had a mean bite of 2 (lineage 78 at
26,000-32,000, mass 11, meat 15%; lineage 1136 at 992,000-997,000), 10,000-11,000 steps each.

## Conclusion

1. The world stands at a bounded cost: yes. 3,400-3,500 bodies, 390-670 steps/s, no extinction.
2. Shape is free and used: yes, in one direction. Every seed went to the smallest grazer, three
   or four digestive cells in a corner. Not diversity of size: one size with noise.
3. Teeth come from shape and armor answers: no. Teeth are profitable and appeared once in twelve
   million births; the one hunter lineage lasted 12,000 steps; shells never rose.

What this changes:
- The trait rules were also holding the world up. Bodies were full squares because defense
  counted hard blocks; take that away and the two laws that remain (food capped per cell, cost
  per cell) make the smallest body the best, in every seed. The freedom of shape exists now and
  is used, but there is nothing in the world for a large body to be better at.
- Emergence has a reachability problem here, not a profitability problem. A hunter must have
  three things at once (a hard tip with muscle behind it in the line it moves along, a policy
  that moves into occupied cells, and a way not to hurt its own kind); the old rules gave the
  third for free ("kin do not eat kin"). Under the physics it costs armor on every side or a
  policy that turns away.
- Keep: the contact physics (a cell costs what it holds; force acts the way a body moves; the
  softer tip breaks; a broken cell is gone), the per-body cost as a world law, and the measures
  (bite, shell, open lines, damaged bodies). Drop nothing back.
- Next, by principles.md 2: change the world, not the body. Give size a reason in the world:
  food that a small body cannot take (a cell holding more than one bite, so that intake scales
  with digestive cells again), or places a small body cannot cross. Then watch whether bodies
  grow because the world rewards it, and whether teeth then have something to reach. Runs longer
  than 1,000,000 steps did not help here (seed 1 to 2,000,000: no second hunter); the world has to
  change first.
