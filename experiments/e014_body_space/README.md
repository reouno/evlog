# e014 Space at the resolution of the body

Date: 2026-08-30

## Purpose

e013 gave bodies a front and a size in the world, at the level of a world cell: each 4x4 quarter
of the 8x8 grid that holds a cell covers one world cell, and no two bodies cover the same cell.
Bodies became readable and reach paid, but the world became a jam: a 3-cell body blocks a whole
cell, 78-94% of moves and 81-90% of children were blocked for want of room, three in four
blocked moves pressed on a body whose cells were not even in the way, and contact fell from
2-4 to 0.1-0.3 touches per body per step. With it went meat, teeth, armor, hunters and the
arms race, at every patch width and in every seed. The crowd was the premise of the arms race,
not an accident of it.

Space at the cell level is too coarse. This experiment keeps space and facing and gives space
the resolution of the body (issue #17):

- **Bodies occupy their own cells.** The world is drawn at the resolution of the body cell: a
  world cell is 4x4 sub-cells, and a body occupies exactly the sub-cells its grid fills, turned
  to its facing. No two bodies share a sub-cell. A move is one sub-cell along the facing (a
  second with probability speed). Where a cell of the mover would enter a cell of another
  body, the two faces meet, with e010's rule in that line: the softer face breaks if the mover's
  muscle in the line exceeds its hardness (the hardness of a face is 3 per contiguous hard cell
  behind it, else 1). The move happens only if the way is clear afterwards: the other lost the
  cells in the way, or was shoved one sub-cell by a push whose muscle exceeds its mass. Food
  stays per world cell: a digestive cell eats from the world cell under it, so reach stays. A
  child is born where its cells find room next to its parent.
- Facing stays as in e013.

This is a change to what the world is (its resolution), not to what a body can do. Compute:
occupancy is 16 times more cells (128x128x16 = 262,144, one index each), a move touches at most
64 sub-cells, a look at most 9 world cells.

One thing the resolution cannot give back: at most 16 body cells fit in a world cell, so a cell
feeds at most 16 digestive cells (0.32 per step), whatever the bodies. e011's crowd of 45-77
bodies at one tree cell (6.5 regrowth per step) is not possible in a world where bodies have
size, and the tree's regrowth stays wasted here as in e013. What can come back is a packed crowd
of small bodies on the grass and around the trees, where contact is the overlap of real cells.
The other lever, a full cell that spills to its neighbors (fruit falls), is left for later.

## Hypothesis

1. **Contact comes back.** On the narrow place, second half of the run, bodies touch another
   body more than once per step on average (e012: 2-4 on the trees; e013: 0.1-0.3), in at least
   three seeds of four at width 1.
2. **The jam clears.** Blocked moves below 50% of forward actions and births without room below
   50% of births (e013: 78-94% and 81-90%), in every world.
3. **Teeth and armor return with contact, and point forward.** On at least one narrow width (1,
   2 or 4) the arms race stands: hard above 5 per body and over 10% of bodies with a bite on the
   narrow place, second half, in at least two seeds of four; and among bodies with a bite on any
   side, at least half have it on the front.
4. **The world stands at a bounded cost.** No extinction, population above 500, at least 300
   steps/s with twelve runs sharing the machine.

What to watch besides: whether the viewer still reads a body (a small body is small now),
what shapes the free space makes (bodies were 3-4 cells in four quarters in e013: does the gut
spread or gather?), and whether bodies pass each other.

## Method

Code: e013 (`experiments/e013_facing_space`) with the space law rewritten and nothing else
changed (costs, materials, the contact rule, the patches of two widths, facing, mating,
lineages). What changes in the code: the occupancy grid has 4x4 sub-cells per world cell and
holds one body index per sub-cell, with a per-world-cell count of held sub-cells (the crowd; what
a body sees ahead); a body's position is the sub-cell under the north-west corner of its grid;
the agent keeps the list of the grid cells it holds and their bounding box; a move is one
sub-cell; a push is resolved per cell of the mover whose next sub-cell is held by another body
(face against face, e010's rule, the mover's muscle in that line as the force), then a shove of
one sub-cell if the force on a body exceeds its mass and it has room, then the move if every
cell of the mover finds its next sub-cell free (a second sub-cell with probability speed); a
turn happens if the rotated grid's cells find free sub-cells; a child is placed at the first
anchor one to eight sub-cells from the parent's in the four directions (from a random one) where
its cells find free sub-cells, else lost; the policy's ten inputs are the food under the body's
bounding box, and for each of the four directions the food and the crowd (held sub-cells, in
world cells) in the world cells the box would newly lie over one and two world cells away; the
mate search looks at the sub-cells within two of the body's box. Moving costs `MOVE_COST`
(0.001) per block per body cell moved, as the law says; a world cell is four of them now. The
place of a body is the world cell under the middle of its box.

Not byte-identical to e013 (the space law is different).

Measures: e013's. `foot` is now the number of world cells under the body's cells; `len_fwd`
and `len_side` (cells the body spans along and across the facing) replace `long` and `wide`;
`occupied_cells` and `cover` count sub-cells; `contacts` counts bodies pressed per move.

Runs (1,000,000 steps): 128x128 with widths "8,1", "8,2", "8,4" (grass and trees, edge, shrubs),
seeds 1-4, twelve at once on one 12-core machine with one thread each (`run.sh`); 256x256 with
"8,1" seeds 1-4 and "8,2" seeds 1-2 on the 6-core machine (`run_256.sh`). Reference: e013 and
e012, the same worlds and seeds. The report compares the three.

    cargo run --release -p e014_body_space -- <steps> <seed> <size> <widths>
    uv run python experiments/e014_body_space/report.py

## Result

(after the runs)

## Conclusion

(after the runs)
