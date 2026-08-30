# e015 Work is force times distance

Date: 2026-08-30

## Purpose

e014 gave space the resolution of the body and contact still did not come back: 0.06-0.22
touches per body per step at every patch width, no tooth, no armor, and a winning body of four
digestive cells at the four corners of its grid that hardly moves. The reading was that the
problem is not room but motive. In e011 and e012 a move always succeeded and a push into fifty
bodies was its free by-product, so a random tooth was paid on its first step. Once bodies take
up space, a push is a move that failed, and e014 charged it as if the body had moved
(`MOVE_COST` per cell of mass, one sub-cell): a body without a tooth gains nothing from
pressing on another and pays 0.008 per attempt (a sixth of its upkeep), so the policies that
win stay and turn (turning is free), and forward is 7-15% of decisions.

This experiment changes the cost law of moving to the honest one (issue #16, vision "Next"
1): **work is force times distance.** A move costs by what was moved and how far: the mover
pays `MOVE_COST` (0.001) per cell of mass per sub-cell it moved, and the same for every body it
shoved. A forward action that moves nothing costs nothing: the faces meet, the softer breaks if
the muscle behind the other exceeds its hardness, and that is all. This is a law about the
world (what a move costs), not about what a body can do; nothing names a push, a tooth or a
hunter. The question is whether contact can again be a by-product of moving, e011's engine,
in a world with space.

The other half of #16, friction by the cells that touch the ground, needs a vertical axis:
the body grid is a top view here (it is what a body holds in the world, e014), so every cell
touches the ground and the friction of a body is its mass, which is the law already. Legs
wait for #5 (3D bodies), where a side exists; the issue says as much.

Compute: nothing changes per step. A push already ran the contact rule; only the charge moves.
If pushing becomes common the contact rule runs more often (up to 64 sub-cells per push);
steps per second are a measure.

## Hypothesis

1. **Pushing returns.** Forward is more than 30% of decisions (e014: 7-15%) and a body presses
   on another more than once per step on average (e014: 0.06-0.22; e012: 2-4 on the trees) on
   the narrow place, second half of the run, in at least three seeds of four at width 1.
2. **Teeth and armor return with contact, and point forward.** On at least one narrow width
   (1, 2 or 4) the arms race stands: hard above 5 per body and over 10% of bodies with a bite
   on the narrow place, second half, in at least two seeds of four (e014: 0.00-0.14 hard, 0%
   bite); and among bodies with a bite on any side, at least half have it on the front.
3. **The winning body moves.** The most common body at the end has muscle (e014: 0.00-0.05
   per body) or the share of moves that happen rises above 50% (e014: 8-38%), in at least
   half the runs.
4. **The world stands at a bounded cost.** No extinction, population above 500, at least 200
   steps/s with twelve runs sharing the machine (e014: 290-430).

What to watch besides: whether the constellation (four cells at the four corners) survives a
world where pushing is free, what a body spends on moving (`move_spent`), and whether the
viewer sees bodies pressing on bodies.

## Method

Code: e014 (`experiments/e014_body_space`) with the cost of a move rewritten and nothing else
changed (the world, materials, the contact rule, facing, mating, lineages, measures). In the
code: a forward action computes `work`, the mass of the mover times the sub-cells it moved
(0, 1 or 2) plus the mass of each body it shoved (one sub-cell each), and charges
`MOVE_COST * work`. Two counters are added to the log: `pushes` (forward actions that pressed
on at least one body, per forward action) and `move_spent` (energy paid for moving per body
per step).

Not byte-identical to e014 (the cost law is different).

Runs (1,000,000 steps): 128x128 with widths "8,1", "8,2", "8,4" (grass and trees, edge,
shrubs), seeds 1-4, twelve at once on one 12-core machine with one thread each (`run.sh`,
74 minutes). The 256 runs (the world people watch, six at once, 2.8 hours) are not run
by default: in e014 they were the 128 world eight times over and added nothing to the answer;
they are run only if the 128 result shows something a viewer should see at that size.
Reference: e014, e013 and e012, the same worlds and seeds. The report compares them.

    cargo run --release -p e015_move_work -- <steps> <seed> <size> <widths>
    uv run python experiments/e015_move_work/report.py

## Result

All numbers are medians over the second half of the run unless said otherwise; ranges are over
the twelve runs (`results/128_*`). The report (`report.html`) has the charts, the per-run
tables, the bodies that prospered and the viewer.

- **Pushing is free, and nobody pushes.** Forward is 9-27% of decisions (e014: 7-15%),
  78-95% of forward actions press on a body and 78-95% are blocked, and contacts are 0.10-0.37
  per body per step (e014: 0.06-0.22; e012: 2.1-3.7 with trees); with trees 0.10-0.37, the
  most in any run 0.37 (seed 4). Moves that happen are 1.0-2.8% of decisions (e014:
  1.1-3.2%); shoves 0. Turns 66-87% (38-87% blocked), stays 0-15%. A body spends
  0.0001-0.0003 per step on moving, 0.2-0.6% of its upkeep (about 0.05).
- **No tooth, no armor, anywhere.** Hard cells per body 0.00-0.06 (on the narrow places
  0.00-0.03; at most 0.4-4.5 in any window), muscle 0.00-0.10, bodies with a bite 0% on the
  front and 0% on any side (at most 0.1-1.0% in any window), meat at most 0.001% of the
  intake, no hunter lineage, front and back equally soft (1.00-1.03). Cells broken 0-29 per
  10,000 steps (seed 3 with trees 109: a passing body with muscle, as in e014).
- **The world stands.** Population 1,420-1,520 with trees, 1,820-1,940 with the edge,
  2,320-2,450 with shrubs (e014: 1,380-2,510), never below 1,290; 276-496 steps/s with twelve
  runs on one machine (slowest window 169). The narrow places hold what e014 held: trees
  180-194 bodies at 62% cover, the edge 552-706 at 53%, the shrubs 1,140-1,200 at 33%;
  regrowth lost to the cap 67-68 of 164 per step with trees, 41-42 with the edge, 4 with
  shrubs. Births 125,000-193,000 per 10,000 steps.
- **The same winner.** Mass 7-9 per body, 3.5-5.0 world cells under a body, 1-4 lineages
  alive (peaks 6-17), 10-265 splits per run. The most common body at the end of every run is
  e014's constellation: 8 digestive cells at three or four corners of the grid over 4.5 world
  cells, no muscle (viewer run: lineage 205, born at step 74,000, alive at 1,000,000, 1,581
  bodies at its peak, 81% of its forward actions blocked). On the trees: a 2x2 block, a bar,
  a column, four dots at the corners.
- **The world is grazed down.** 0.3-0.6% of cells hold more than half of what a cell can
  hold; the mean cell holds 0.05-0.09 of 8; intake per digestive cell 0.008-0.009 per step
  (the bite is 0.02).

## Conclusion

1. Pushing returns: no. Forward 9-27%, contacts 0.10-0.37 per body per step.
2. Teeth and armor return and point forward: no. Nothing bites, nothing is hard, at any width.
3. The winning body moves: no. No muscle; moves that happen 1-3% of decisions.
4. The world stands at a bounded cost: yes. Population 1,420-2,450, 276-496 steps/s.

What it changes: the cost of a push was not the lever. Pressing on a body is free to try and
the policies that win still do not press, or move; the whole effect of the law is a few
more forward actions that end against a neighbor and break nothing. What a forward action
costs a body is the move, not the push: when it finds room it takes the body off the cells
its corners eat from, into a world grazed down to its regrowth everywhere (a full cell feeds a
gut cell no faster than a regrowing one, 0.02 per step), and pays for the distance; a lineage
spreads over a patch by births faster than by walking. Selection keeps reach and the body
that reaches the most from where it stands wins. This is a lawn: food regrows in place, under
the body that eats it, so the best body stands still. e011 and e012 had contact because a
body without size paid nothing for being in a crowd, not because moving paid.

The cost law stays (it is the honest one and it costs nothing). The missing premise is the
one that makes a herd: a plant under a standing animal does not grow, and the grass a herd
leaves recovers, so standing still exhausts the spot. As a law about the world: a cell
regrows by its free sub-cells (or not at all while a body holds any of them). It costs
nothing (the crowd per cell is already kept), it names no trait, and whether what moves is a
herd, a jostling crowd, or a world that starves is for the run to show. That is the
recommended next experiment. Also on the table: matter that does not vanish (a dead body is
food where it lies: a crowd is a place worth going to, and a body gains from another without
a tooth), and the spill for the trees' waste. The ground half of #16 (friction by the cells
that touch the ground) waits for 3D bodies (#5), where a side exists.
