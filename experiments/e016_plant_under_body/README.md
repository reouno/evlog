# e016 A plant under a body does not grow

Date: 2026-08-31

## Purpose

e015 made a push free and nobody pushed: forward is 9-27% of decisions, contacts 0.10-0.37
per body per step, no tooth, no armor, and the same winning body as e014, eight digestive
cells at the corners of its grid that lies over 4.5 world cells and hardly moves. The reading
was that the price of a push was never what stopped it. What a forward action costs a body is
the move: when it finds room it takes the body off the cells its corners eat from, into a
world grazed down to its regrowth everywhere, and pays for the distance. Food regrows in
place, under the body that eats it, so the best body stands still and reaches. That is a
lawn, and a lawn has no herd.

The real world's herds move because a plant under a standing animal does not grow, and the
grass a herd leaves recovers: standing still exhausts the spot. This experiment adds that
premise as a law about the world (issue #18, vision "Next" 1): **a cell held by a body does
not regrow.** Food is per world cell and a world cell is 4x4 sub-cells that bodies hold; the
law is read as "a cell regrows only while no body holds any of its sub-cells" (`shade` = any,
the default). The other reading, "a cell regrows by its free sub-cells" (`shade` = free,
regrowth times the free share), is kept as an argument and piloted; a body of eight cells
over 4.5 world cells shades 8 of 72 sub-cells, so that reading takes about a tenth of the
regrowth from a standing body and is expected to leave the lawn a lawn.

The law names no trait and costs nothing per step (the crowd per cell is kept already,
`Occ.crowd`). It takes food from the world: regrowth on cells that bodies stand on is lost
(a new column, `shaded`, counts it, next to `wasted`, the regrowth lost to the cap). Whether
what moves is a herd, a jostling crowd, or a world that starves is for the run to show.

## Hypothesis

1. **Bodies move.** Forward is more than 30% of decisions (e015: 9-27%) and moves that happen
   (forward actions that found room) are more than 10% of decisions (e015: 1-3%), second half
   of the run, in at least three seeds of four in at least one of the three worlds.
2. **The winning body moves.** The most common body at the end has muscle (e015: 0.00-0.10
   per body) or lies over fewer world cells than e015's constellation (e015: 4.5; a body that
   walks gains nothing from reach), in at least half the runs.
3. **Contact returns with the moving.** Contacts are above 1 per body per step (e015:
   0.10-0.37; e012: 2-4 with trees) on at least one world, second half, in at least two seeds
   of four. Whether a tooth or armor follows is watched, not predicted (e015: 0% bites, hard
   0.00-0.06).
4. **The world stands at a bounded cost, with less food.** No extinction, a population that
   holds over the second half of the run (the last quarter's median within 20% of the third
   quarter's; the pilot gave 380-455 with trees, e015 1,420-2,450), at least 200 steps/s with
   six runs sharing a machine. Regrowth lost to standing bodies (`shaded`) is below half of
   the regrowth on every world.

What to watch besides: how much of the world is covered by bodies (e015: 33-62% of the narrow
place), whether the narrow place (the trees) empties or is held by bodies that circle it,
births (e015: 125,000-193,000 per 10,000 steps), and the free-sub-cells reading next to the
strict one on the trees world: how much shading it takes to make a lawn move.

## Method

Code: e015 (`experiments/e015_move_work`) with the regrowth loop changed and nothing else
(the world, materials, the cost law, the contact rule, facing, mating, lineages, measures).
In the code: before adding a cell's regrowth, the crowd of the cell (sub-cells held by bodies)
is read; with `shade` = any a held cell adds nothing, with `shade` = free it adds regrowth
times (16 - held) / 16. The difference is summed into `shaded` and written to the log per
step. One argument is added after the widths: `any` (default) or `free`.

Not byte-identical to e015 (the regrowth is different).

Pilot (seed 9, 100,000 steps, 128x128 "8,1", grass and trees, both readings; `results/*seed9*`):
the world stands under both. With `any`, 380-455 bodies (e015 about 1,470), forward 44-50% of
decisions and 30-35% of decisions a move that happened, mass 14-18 per body, and 113-127 of
the 164 regrowth per step lost to standing bodies (the trees' regrowth sits on a few cells,
and bodies sit on them). With `free`, 1,090-1,190 bodies, forward 20-28%, moves that happened
5-7%, mass 8-9, the same lawn as e015, and still 86 of 164 lost. So the batch runs both: the
strict reading on the three worlds, and the free reading on the trees world next to it. The
population level of hypothesis 4 was set after the pilot (a level of 500 was written first).

Runs (1,000,000 steps): 128x128 with widths "8,1", "8,2", "8,4" (grass and trees, edge,
shrubs), seeds 1-4, `shade` = any (twelve runs), and "8,1" seeds 1-4 with `shade` = free (four
runs, `results/128_sigma8-1-free_*`); six at a time on each of two machines with one thread
each (`run.sh any 1 2 && run.sh free 1 2` and the same with seeds 3 4; outputs are
byte-identical across machines). The 256 runs are not run: in e014 they were the 128 world
eight times over. Reference: e015 and e014, the same worlds and seeds. The report compares
them.

    cargo run --release -p e016_plant_under_body -- <steps> <seed> <size> <widths> [any|free]
    uv run python experiments/e016_plant_under_body/report.py

## Result

All numbers are medians over the second half of the run unless said otherwise; ranges are over
the twelve strict runs (`results/128_sigma8-{1,2,4}_seed{1-4}`), the free reading apart
(`results/128_sigma8-1-free_seed{1-4}`). The report (`report.html`) has the charts, the per-run
tables, the bodies that prospered and the viewer.

- **Bodies move.** Moves that happen (forward actions that found room) are 11-20% of decisions
  (e015: 1.0-2.8%) in all twelve runs; forward is 14-24% (e015: 9-27%), so the 30% asked for is
  not reached; 74-88% of forward actions find room (e015: 5-22%). Turns 76-86%, stays 0-1%.
  A body spends 0.0009-0.0018 per step on moving (e015: 0.0001-0.0003), 2-4% of its upkeep.
- **The block replaces the constellation.** The most common body at the end of every run is
  7-9 digestive cells in one block, a 3x3 square or a wedge (three, three, two; or three, two,
  two, one), in a corner of its grid, over 1.6-2.7 world cells (e015's constellation: 4.5),
  with no muscle. Over all bodies: mass 7.8-10.6, 1.8-2.7 world cells under a body (e015:
  3.5-5.0), muscle 0.00-0.17, hard 0.00-0.13. Lineages alive 1-5 (7-18 kept over a run).
- **Nobody meets anybody.** Contacts 0.02-0.05 per body per step (e015: 0.10-0.37; e012:
  2-4). Cover 2-3% of the world: 7-8% of the grass, 27-28% of the trees, 20-26% of the edge,
  15-18% of the shrubs (e015: 62%, 53%, 33% of the narrow places). Bodies with a bite 0% on
  the front and on any side (single windows on the trees reach 6%: a body or two among 32-40,
  passing), meat 0% of the intake, cells broken 0-74 per 10,000 steps, no hunter lineage.
- **The world stands on a third of its food.** No extinction; population 630-750 with trees,
  713-830 with the edge, 848-1,093 with shrubs (e015: 1,420-2,450), never below 318, the
  last quarter 0.94-1.06 of the third. Regrowth lost to standing bodies 66-78% of the 164 per
  step (75-78% with trees, 74-77% with the edge, 66-71% with shrubs); the world lives on 33-55
  per step, and 0-4 is lost to the cap (e015: 67-68 with trees). Cells above half full 0.0-0.1%,
  mean cell 0.03-0.06 of 8, intake per gut cell 0.0054-0.0066 (e015: 0.008-0.009), births
  26,000-51,000 per 10,000 steps (e015: 125,000-193,000). 541-1,892 steps/s with six runs on a
  machine (8-16 minutes per run). The narrow places hold 32-40 bodies on the trees, 110-150 on
  the edge, 268-370 on the shrubs (e015: 180-194, 552-706, 1,140-1,200).
- **The free reading is e015.** Grass and trees, `shade` = free: population 1,028-1,333,
  forward 14-21%, moves that happen 4-6%, 62-81% of forward actions blocked, contacts 0.11-0.25,
  regrowth lost to standing bodies 51-53%, cover 10-13% of the grass and 51-52% of the trees, and the
  winner 6-12 digestive cells at two to four corners of its grid over 3.9-6.0 world cells
  (e015's constellation: 4.5). 23-40 minutes per run.

## Conclusion

1. Bodies move: half. Moves that happen 11-20% of decisions (above 10% in all twelve runs);
   forward 14-24%, not 30%.
2. The winning body moves: yes. A block of 7-9 gut cells over 1.6-2.7 world cells in every run,
   in place of a constellation over 4.5; no muscle.
3. Contact returns with the moving: no. 0.02-0.05 per body per step, less than e015.
4. The world stands at a bounded cost, with less food: stands, on a third. No extinction,
   the population holds, 541-1,892 steps/s; regrowth lost to standing bodies 66-78%, over the
   half asked for.

What it changes: one law about the world, and the lawn is a pasture. A body that stands still
eats what is under it in a few steps and then nothing, so the policies that win step off the
exhausted cell into one that has recovered, and the body that wins brings its mouths together
(reach is worth nothing when standing exhausts every cell under the body alike; what pays is
bringing every mouth onto the cell just entered). Nothing in the law names a move or a shape.
The free reading, the same law at a sixteenth of the strength per sub-cell, does not do it:
it is a tax on standing that reach pays for, and the corners stay. The strict reading
stays; the price is a third of the food and half the bodies.

What did not come: contact. Bodies move through a world that is 2-3% covered and press on
nothing; a body gains nothing from another body here but its place, and places are free. The
missing premise is the one "a crowd is a place worth going to" needs: matter that does not
vanish. A dead body is food where it lies, so a body gains from another without a tooth and a
place where bodies die is a place to walk to (vision "Next" 2). That is the recommended next
experiment. The spill (a full cell feeds its neighbors) waits behind it: with bodies moving,
only 0-4 of 164 regrowth is lost to the cap.
