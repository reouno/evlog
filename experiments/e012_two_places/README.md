# e012 Two kinds of place: wide and narrow food patches in one world

Date: 2026-08-30

## Purpose

e011 showed that the width of a food patch decides what lives on it. Width 8 (e010) makes
five-cell grazers; width 1 makes tortoises, hunters and corner bodies (the arms race); width 2
is the edge (two seeds of four). Each run had one kind of place, so each run had one regime,
with one holder per island at a time and 1-13 lineages alive.

The real world has grass and trees side by side, and a grazer can walk from one into the other.
The simplest premise: **the patches of one world need not all have the same width.** One law of
the world, nothing about bodies, no compute added. Then both kinds of body can exist in one run,
a lineage can move between places (a grazer wandering into a crowd, a tortoise leaving one), and
the viewer sees two kinds of island on one screen.

## Hypothesis

1. **Each place keeps its regime.** On the wide patches bodies stay small and soft, as in e010
   (mass under 10, hard under 1 per body, under 1% of bodies with a bite); on the narrow patches
   the arms race runs, as in e011 width 1 (hard above 5, over 10% with a bite, meat over 5% of
   the intake there). In every seed, over the second half of the run; neither place empties
   (population on each kind of place at least half of what the single-kind world had per patch:
   e010 about 850 per wide patch, e011 about 330 per narrow one).
2. **Lineages cross between places.** At least 1% of living bodies stand in the other kind of
   place from the one they were born in, and in every seed at least one lineage has members in
   both kinds of place at once for 20,000+ steps.
3. **Two niches make more lineages.** Lineages alive (median) in the mixed world are at least
   e011 width 1's (5-13), and the lineage lifetime is not shorter.
4. **The world stands at a bounded cost.** No extinction, population above 500, at least 300
   steps/s with twelve runs sharing the machine.
5. **A grass neighbor pushes the edge over.** With width 2 next to width 8, the arms race starts
   on the narrow patches in more than two seeds of four (e011: two of four alone), because the
   wide place supplies soft bodies to bite.

## Method

Code: e011 (`experiments/e011_rich_cells`) with one change in the food law: patch k has the width
`sigmas[k % sigmas.len()]`, where `sigmas` is an argument ("8,1": every other patch wide, the
rest narrow). Every patch carries the same total regrowth whatever its width (0.01 per cell of
the world per step; 41 per patch per step). What a cell can hold is a constant 8 now (e011: no
effect at any width; e010 lost 0.3% of its regrowth to a cap of 1). With one width the program
reproduces e011 byte for byte (checked at width 1, seed 9, 20,000 steps: lineages, events,
agents, distances and the log identical but for the timing column).

Measures added. Each cell of the world belongs to a place: the patch that gives it the most
regrowth (its kind is the width), or none beyond every patch. Per place every 10,000 steps
(`places.csv`): population, body means (mass, hard, muscle, sensor, digestive, bite, shell,
bodies with a bite), the most crowded cell, plant and meat intake eaten there, lineages present,
and movers (bodies born in the other kind of place). Each agent remembers the place it was born
in; the log adds `crossers` (share of living bodies standing in a kind of place other than
their birth place) and `pop_none`. `lineages.csv` adds the members per kind of place (`p0`,
`p1`, `pnone`); `agents.csv` adds `place` and `born_place`. Snapshots carry the patch centers
and widths, and write food on a square-root scale so that a wide patch is visible.

Run (from repo root): `cargo run --release -p e012_two_places -- <steps> <seed> <size> <sigmas>`
Outputs: `results/<size>_sigma<a-b>_seed<seed>_{log,agents,events,lineages,dist,places}.csv`
and `_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

**Trials** (seed 9, not kept; 100,000 steps at 128, 20,000 at 256): both regimes are in place
by 100,000 steps. Grass (width 8): 1,643 bodies, mass 6.2, hard 0.0; trees (width 1): 700
bodies, mass 32, hard 1.3, 42 bodies in the most crowded cell; 51-75 bodies beyond every patch.
Speed 1,270 steps/s at 128 and 330 at 256 (four threads each, three runs at once).

**Runs**: `8,1` at 128 (two wide patches, two narrow; the main world), `8,2` at 128 (the edge
width next to grass), `8,1` at 256 (eight and eight; the world people watch, and lineages across
islands, e007's calibration), seeds 1-4 each, 1,000,000 steps; twelve at once on one 12-core
machine, one thread each (`run.sh`). References: e010's width-8 runs and e011's width-1 and
width-2 runs (128, seeds 1-4).

## Result

12 runs, 1,000,000 steps each (`results/128_sigma8-1_seed{1..4}`, `128_sigma8-2_seed{1..4}`,
`256_sigma8-1_seed{1..4}`), twelve at once on one 12-core machine, one thread each. Ranges are
over the four seeds of a world, medians over the second half of the run unless said otherwise;
"grass / narrow" gives the two places of a world. References: e010 (width 8 alone) and e011
(width 1 and 2 alone), seeds 1-4. Report: `report.html`.

| | grass and trees (8,1), 128 | grass and edge (8,2), 128 | grass and trees (8,1), 256 | width 8 alone | width 1 alone |
|---|---|---|---|---|---|
| population | 2,370-2,776 | 2,420-2,848 | 7,568-11,060 | 3,489 | 1,294 |
| population by place | 1,620-1,675 / 622-1,046 | 860-1,718 / 693-1,177 | 4,560-6,810 / 2,389-4,187 | 1,745 per two patches | 647 per two patches |
| mass per body by place | 5.7-6.2 / 15.5-31.5 | 5.4-17.5 / 14.0-31.3 | 5.5-11.6 / 15.5-36.9 | 5.3 | 31.2 |
| hard cells per body by place | 0.1-0.2 / 4.4-15.1 | 0.0-3.4 / 0.3-12.7 | 0.1-2.1 / 4.4-21.2 | 0.1 | 14.8 |
| bodies with a bite by place | 0.1-0.2% / 12-34% | 0.1-11% / 0.2-13% | 0.3-6.7% / 12-14% | 0.1% | 19% |
| meat share of intake by place | 0.2-0.6% / 14-18% | 0.0-11% / 0.9-9.8% | 0.5-11% / 11-20% | 0.1% | 9-19% |
| most bodies in one cell, narrow place | 53-74 | 20-26 | 59-89 | 6 | 45-77 |
| bodies beyond every patch | 45-86 | 45-86 | 208-268 | - | - |
| crossers (in the other kind of place from birth), median / max | 0.1-0.7% / 3.8-5.9% | 0.6-2.9% / 5.5-14% | 0.6-1.6% / 2.0-5.7% | - | - |
| lineages alive, median | 9-13 | 9-11 | 19-50 | 7-14 | 4-10 |
| lineage lifetime, median (steps) | 11,000-13,000 | 10,000-13,000 | 10,000-12,000 | 10,000-12,000 | 11,000-15,000 |
| lineages shared by both places (20,000+ steps) | 2-4 | 10-22 | 2-13 | - | - |
| lineages that moved home | 1-3 | 2-15 | 1-5 | - | - |
| hunter lineages (bite >= 2, 20,000+ steps) | 9-29 | 1-23 | 91-126 | 0 | 26-50 |
| steps per second, median | 526-588 | 372-550 | 151-232 | 400-588 | 574-749 |

- **Each place keeps its regime, in every seed.** Grass: e010's grazer (5.7-6.2 cells, hard
  0.1-0.2, 0.1-0.2% with a bite). Trees: e011's crowd (53-74 bodies in the most crowded cell)
  and arms race (hard 4.4-15.1, 12-34% with a bite, meat 14-18% of what is eaten there, 9-29
  hunter lineages per seed of mass 33-59 and hard 20-46, 14-74% meat). The population of each
  place is what the single-kind world had per patch. Hard cells per body on the grass never
  pass 1.4: the trees' hunters do not take the grass.
- **Bodies cross, lineages straddle, hunters stay.** 0.1-0.7% of bodies stand in the other kind
  of place from their birth place (up to 3.8-5.9%), 2-3% beyond every patch. Into the trees
  walk small grazers (3-8 cells, no armor); out of the trees walk tortoises (64 cells, 48 hard),
  1% of the grass at the end of seeds 1 and 2; hunters never leave. 2-4 lineages per seed hold
  10%+ of their members in both places for 20,000+ steps; 1-3 move home. Lineage 101 of seed 2
  (steps 27,000-1,000,000, 2,353 agents at its peak) had half its members on each place for the
  whole run with a different body on each: 4 cells and an age of 500-700 steps on the grass,
  8-12 cells and an age of 30-60 on the trees (26-41% of what stands on the trees is a small
  body: e011's corner bodies).
- **Lineages: e010's number, not the sum.** 9-13 alive against 4-10 (trees alone) and 7-14
  (grass alone); lifetime 11,000-13,000 in all three.
- **The edge next to grass does not flip more often, but it pushed into the grass once.** Seed
  4 flipped for good at 100,000 steps (edge hard 17-25 from 400,000), and from 450,000 to 850,000
  its hunters held the grass too (grass hard 5-7, 18-26% with a bite, meat 11% of the grass
  intake, grass population halved to 860) through lineages of mass 32-43 with 12-23 hard cells
  and 30-70% of their members on the grass; by 900,000 the grass was clear. Seed 1 flipped in
  bouts (hard 11 at 100,000 and 400,000, 6-7 at 550,000-700,000, then under 1), seed 3 late and
  weakly (5 at 850,000), seed 2 never (at most 4.3). Alone: two of four for good. The edge is
  four cells wide (26 bodies to a cell), so lineages that live on both sides of its border are
  common: 10-22 shared per seed.
- **At 256 (eight islands of each kind) the trees are the same, and the hunters raid the grass.**
  Trees: mass 15.5-36.9, hard 4.4-21.2, 12-14% with a bite, meat 11-20%, 91-126 hunter lineages
  per seed. Grass: in three seeds of four, hunter lineages of mass 49-56 with 24-30 hard cells, a
  ring of 10-15 muscle cells and a bite of 3-5 (0-4% of their members in the trees) hold a grass island for 40,000-170,000 steps each, 9-11 such lineages per seed, and
  get 13-24 energy per agent from other bodies against 8-30 from plants: grass hard 1-4 per body
  and 3-12% with a bite for 800,000 steps in seed 2 (then the grass clears), from 600,000 to the
  end in seed 1 (grass population from 7,000 down to 4,300-5,200), in two bouts in seed 3; seed 4
  never (hard 0.1). Crossers 0.6-1.6%; 2-13 shared lineages per seed; the largest lineage of seed
  1 (2397: one digestive cell in each corner, 6,246 agents at its peak, 361,000 steps) lived 60%
  on the grass and 40% in the trees. Lineages alive 19-50 (e007's 256 world: 12-21).
- **The world stands**: no extinction, population never below 1,601 at 128 and 6,525 at 256;
  372-588 steps/s at 128 and 151-232 at 256 (7,600-11,100 bodies; the cost is linear in bodies
  as before) with twelve runs on one machine.

## Conclusion

1. Each place keeps its regime: yes at 128 in every seed; at 256 the trees are the same but
   hunters take grass islands for 100,000-800,000 steps in three seeds of four.
2. Lineages cross between places: partly. Bodies cross at 0.1-0.7% (128) and 0.6-1.6% (256),
   under the 1% asked for; lineages straddle in every seed (2-13 for 20,000+ steps), one for
   978,000 steps with a different body on each place.
3. Two niches make more lineages: yes, as many as e010 alone (9-13 against 7-14 and 4-10); not
   the sum. 19-50 at 256.
4. The world stands at a bounded cost: yes at 128 (372-588 steps/s); 151-232 at 256 with four
   times the bodies.
5. A grass neighbor pushes the edge over: no. One seed for good and one in bouts, against two of
   four alone. The edge pushed into the grass instead, once, for 400,000 steps.

What this changes:
- Patch widths as a list are a law of the world from here on. 128 with two patches of each kind
  is the world for questions about places; 256 with eight and eight is the world people watch
  (two kinds of island on one screen, a raid on a grass island, a lineage on both).
- The place of a cell is a measure only, and nothing about bodies changed; the sorting of bodies
  by place (one gene pool with a 4-cell body on the grass and a 12-cell body on the trees) and
  the hunters on the grass came from the world.
- Open: why hunters take the grass at 256 and not at 128 (a rate with more islands, or a
  barrier at two? a longer 128 run would tell); why the grass clears again (the grazers thin out
  and the hunter starves?).
- Next: #15 (bodies face a direction and take up space), then #16 (ground and friction).
