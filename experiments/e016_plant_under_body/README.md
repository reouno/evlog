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

(pending)

## Conclusion

(pending)
