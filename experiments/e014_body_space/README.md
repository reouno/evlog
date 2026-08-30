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
"8,1" seeds 1-4 and "8,2" seeds 1-2, six at once on the same machine once the 128 runs were done
(`run_256.sh`; the 6-core machine managed 50 steps/s and was stopped). Reference: e013 and e012,
the same worlds and seeds. The report compares the three.

    cargo run --release -p e014_body_space -- <steps> <seed> <size> <widths>
    uv run python experiments/e014_body_space/report.py

## Result

All numbers are medians over the second half of the run unless said otherwise; ranges are
over seeds. 128x128, twelve runs (`results/128_*`), and 256x256, six runs (`results/256_*`).
The report (`report.html`) has the charts, the per-run tables and the viewer.

- **Contact did not come back.** A body presses on another 0.06-0.22 times per step (e013:
  0.08-0.33; e012: 2.1-3.7 on the trees). Nearly every forward action is a push (62-92% of
  them do not move the body), but a forward action is 7-15% of all decisions: bodies stay
  (1-55%) and turn (30-90%; turning is free and 46-92% of turns do not happen either). Contact
  is what a failed move looks like, and a body without a tooth has nothing to gain from it.
- **The jam did not clear, but births did.** 62-92% of forward actions are blocked (e013:
  78-94%), 47-63% of children find no room and are lost (e013: 81-90%), and no body is ever
  shoved (nobody has muscle). Births are 134,000-202,000 per 10,000 steps (e013: 29,000-40,000;
  e012: 200,000-392,000): a small child finds a spot four times as often as a 2x2 block did.
- **No tooth, no armor, anywhere.** Bodies with a bite: 0% on the front and 0-0.3% on any
  side, on every place of every run; hard cells per body 0.00-0.14 (at most 0.7 in any window
  on any narrow place); meat 0.000% of the intake; no hunter lineage; cells broken 0-24 per
  10,000 steps (one run: 221, seed 3 with trees, a passing body with muscle); the front and the
  back of a body are equally soft (1.00-1.06). Not at width 1, 2 or 4, not in any seed.
- **The world stands.** Population 1,380-2,510 at 128 (e013: 1,170-1,600; e012: 2,350-2,940),
  never below 1,250; 290-430 steps/s with twelve runs on one machine (e013: 710-1,550: the
  sub-cell physics costs about twice per body, and there are more bodies).
- **The body that wins is a constellation.** In all twelve runs the most common body at the
  end is 4-8 digestive cells at the four corners of the 8x8 grid (`4......4` in the first and
  last rows, sometimes `44....44` with a second cell beside or below each corner): a body that
  spans 7x7 body cells with 4-8 of them, so that each corner lies in a different world cell and
  the body eats from 3.9-5.2 world cells (e013's winner: 3-4 cells at the center of the grid,
  one per quarter, 1.4-2.1 cells). Its box is 41-57 sub-cells for a mass of 6-9; 1-24% of the
  bodies stand wholly inside another body's box. Intake per digestive cell is 0.008-0.010 per
  step (e013: 0.013-0.015; e012: 0.008): reach no longer pays per cell, since a corner cell
  shares its world cell with the corners of its neighbors, but it pays per body. Mass 6-9 (10th
  to 90th percentile 2-12), sensor 0.00-0.05, muscle 0.00-0.05.
- **The narrow places hold three to four times e013's bodies and waste less.** Trees 169-192
  (e013: 41-65; e012: 622-1,050) at cover 59-62% of their sub-cells; the edge 540-636 (e013:
  148-216; e012: 693-1,180); shrubs 1,100-1,212 (e013: 424-442). Regrowth lost to the cap: 67-68
  of 164 per step with trees (e013: 83-88), 41-42 with the edge (e013: 69-79), 4 with shrubs
  (e013: 49-55). The grass holds 1,212-1,408 (e013: 1,100-1,320) at cover 14-15%.
- **Fewer lineages than ever.** 1-3 alive (e013: 1-8; e012: 6-15), peaks of 7-17; 20-200 splits
  and as many extinctions per run: one shape sweeps, splits into near-clones, and they replace
  each other. Crossers 0.0-1.2%.
- **256 (eight patches of each kind).** The same world eight times over. Grass and trees
  (seeds 1-4): population 5,550-6,370 (e013: 4,690-5,370; e012: 7,570-11,060), never below
  4,840; contacts 0.08-0.16 per body per step; blocked 78-80%; children lost 48-53%; births
  541,000-574,000 per 10,000 steps; hard 0.01-0.06, no bite (0% on the front, 0-0.1% on any
  side), meat 0.000%, no hunter lineage; the trees hold 718-784 bodies over eight patches
  (90-98 each; e013: 19-29) at cover 61%, mass 4.8-5.2; the grass 4,830-5,230, mass 7.7-8.6;
  271 of the 655 regrowth per step wasted (e013: 331-350); 2-7 lineages alive (peaks 25-43;
  e013: 9-21); 106-147 steps/s with six runs on one machine, one thread each. Grass and the
  edge (seeds 1-2): population 7,560-7,920, the edge 2,360-2,440 bodies (e013: 618-741) at cover
  52-53%, mass 4.4-4.5, hard 0.01, no bite; 169-172 of the regrowth wasted; 4 lineages alive.
  The most common body of the run people watch (seed 1) is the constellation: six digestive
  cells at the four corners, born at step 14,000, alive at 1,000,000, 5,839 bodies at its peak.

## Conclusion

1. Contact comes back: no. 0.06-0.22 touches per body per step at every width, in every seed.
2. The jam clears: no. 62-92% of moves blocked; children lost 47-63% (better than e013's
   81-90%, and births are four times e013's, but not below half).
3. Teeth and armor return and point forward: no. Nothing bites, nothing is hard, nothing points.
4. The world stands at a bounded cost: yes. Population 1,380-2,510, 290-430 steps/s.

What it changes: the resolution was not the problem. At the resolution of the body, a small
body is small, bodies nest inside each other, births are back and the narrow places hold three
to four times the bodies, and still nobody touches anybody: contact is 0.1-0.2 per body per
step as in e013, not 2-4 as in e012. The reason is not room but motive. In e011 and e012 a
move always succeeded and a push into fifty bodies was its free by-product, so a random tooth
was paid on its first step. Once bodies take up space, a push is a move that failed and cost
the mover; a body without a tooth gains nothing from it, so the policies that win stay and
turn (7-15% forward actions), and a tooth, which needs a hard tip, two muscle cells behind it
and a policy that pushes into bodies, all at once, is never paid for on the way there. Space
and the arms race are in tension: contact must now be sought, and nothing in the world
rewards seeking it before the tooth exists. The selection that remains is reach, and reach
alone makes plants: the winning body is four cells at the four corners of its grid, a
constellation over four world cells that hardly moves (80% of its moves are blocked) and
hardly needs to. The world is at the stage of a lawn of sessile grazers with far-flung mouths.

The next lever is not food (the spill would spread the trees, not the contact) but the cost
law of moving: a push that moves nothing costs the mover 0.001 per cell as if it had moved,
which is what makes pushing a losing action and turning (free) a substitute for it. In the
real world work is force times distance; a body pressing on another spends little until
something gives. Charging the move by the distance moved (and, with #16, by the cells that
touch the ground) is a law about the world, would make pushing into a body free to try, and
would test whether contact as a by-product of moving, e011's engine, can exist in a world with
space. That is the recommended next experiment, folded into #16 (ground and friction). The
spill (a full cell that feeds its neighbors) stays on the table for the trees' waste.
