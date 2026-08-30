# e013 Bodies face a direction and take up space

Date: 2026-08-30

## Purpose

e011's physics has four verbs a shape can address (eat: digestive cells; push: muscle per
line; resist: a hard tip; be untouchable: which lines hold cells), and four body kinds came out,
one per verb (grazer, hunter, tortoise, corner body). More kinds of shape need more verbs in the
world, written as laws of materials and the world (principles.md, 2), never as traits. Two are
the cheapest and the ones that make a shape readable: a body has no front, so a tooth cannot be
seen to point anywhere, and a body has no size in the world, so 45-77 bodies stand in one cell
and no body ever blocks another or reaches further than another.

Two laws of the world (issue #15):

- **A body faces a direction.** Its 8x8 grid is rotated with it: the front row of the grid is
  the side that points where the body faces. Moving is along the facing; turning (left, right)
  is an action that takes a step. Only the front pushes, so a hard tip with muscle behind it is a
  tooth only when it points forward. The policy sees the world from the body (food and bodies
  ahead, behind, left, right).
- **A body takes up space.** A world cell is 4x4 body cells, so the grid covers up to 2x2 world
  cells: each quarter of the grid that holds a cell covers one world cell (a corner body covers
  one cell, a full body four). No two bodies cover the same cell. Moving into a covered cell is a
  push (e010's contact rule, line by line, where the lines meet in the world) and the move
  happens only if the way is clear afterwards: the other body lost the cells in the way, or was
  shoved one cell (a push whose muscle exceeds the other's mass moves it, if it has room). Each
  digestive cell eats from the world cell under it, so a body that covers more cells reaches
  more food, and a wide body blocks a passage. A child is born where there is room next to its
  parent; without room it is lost (as a child born without cells).

## Hypothesis

1. **Fronts appear.** Where bodies bite, the tooth is on the front: on the narrow place, over
   the second half of the run, the share of bodies with a bite on the front is at least half the
   share with a bite on any side, and armor is not the same on every side (the mean hardness of
   the back differs from the front by 20% or more).
2. **Reach pays.** On the grass, bodies cover more than one world cell (mean 1.2 or more)
   although e010's five-cell grazer fits in one quarter of its grid.
3. **The crowd becomes a queue and the arms race survives it.** On at least one narrow width
   (1, 2 or 4) the arms race stands: hard above 5 per body and over 10% of bodies with a bite
   on the narrow place, second half, in at least two seeds of four.
4. **The world stands at a bounded cost.** No extinction, population above 500, at least 300
   steps/s with twelve runs sharing the machine.

What to watch besides: whether the crowd of e011 (45-77 bodies to a cell) turns into a queue and
what that does to the arms race, and whether the viewer can now read a body: where its front
is, what it eats, what it can bite.

## Method

Code: e012 (`experiments/e012_two_places`) with the two laws above and nothing else changed
(costs, materials, the contact rule, the patches of two widths, mating, lineages). What changes
in the code: the agent keeps a facing and its body in the world frame (cells rotated, tips per
world side, the quarters it covers, the digestive cells per quarter); an occupancy grid (one
body index per cell) replaces the per-cell lists; the policy has four actions (stay, forward,
turn left, turn right) instead of five and its ten inputs are seen from the body (food under it;
food and bodies one cell ahead, behind, left, right, two cells weighted by sense; energy); the
move is a push into every body holding a cell the footprint enters, resolved with e010's rule in
the lines that meet in the world (line c of the pusher meets line c + 4 dx of the other, and
every line where both have a cell is a contact, as in e010's shared cell; a first version
touched only where the tips would overlap after the move, and then three in four blocked
moves pressed on nothing, so it was dropped before the runs), then a shove if the muscle
pressing on a body exceeds its mass, then the move if the way is clear (a second cell with
probability speed if that way is clear too); the pusher pays the move whether or not it moves.
A turn rotates the grid about its center and happens if the quarters it would newly cover are
free. A child is placed at the first anchor with room for its footprint one or two cells from
the parent's anchor in the four directions (from a random one); without room it is lost. The
initial bodies get a random facing and a random free anchor.

Not byte-identical to e012 (the policy has four outputs, so the fixed table differs).

Measures added: `bite` is now the largest force behind a hard tip on the front; `bite_any` is
e012's bite (any side); `shell_front`, `shell_back`, `shell_side` (mean hardness of the
touchable tips of that side of the body grid); `foot` (world cells covered, 1-4), `long`
(covers a quarter ahead and one behind), `wide` (two quarters across); `cover` (share of the
cells of a place, or of the world, under a body; replaces the most crowded cell, which is 1
now); `blocked` (forward actions that did not move the body, per forward action), `shoves`,
`turns_blocked`, `births_no_room` (children lost for want of room, per child). Snapshots carry
the facing; the viewer draws each body over the 2x2 block it can cover, turned the way it
faces, with a white edge on its front.

Run (from repo root): `cargo run --release -p e013_facing_space -- <steps> <seed> <size> <sigmas>`
Outputs: `results/<size>_sigma<a-b>_seed<seed>_{log,agents,events,lineages,dist,places}.csv`
and `_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

**Trials** (seed 9, not kept; 20,000-30,000 steps at 128, "8,1"): the world stands and runs at
1,850-2,000 steps/s (e012: 600-800 at this stage; births are limited by room, so fewer newborn
die). The grass keeps 5-cell grazers, now spread over two world cells; the trees hold 20-55
bodies in a queue instead of 620-1,046 in a crowd, and half the world's regrowth is wasted
there (a cell holds 8 and one body eats at most 0.32 from it per step). 90% of forward moves
are blocked and 60-80% of turns. The first trial refunded the parent when a child had no room:
23% of the bodies then tried every step and most of the compute went to developing children
that were never born, so a child without room is lost instead.

**Runs**: at 128 (two patches of each kind) "8,1" (grass and trees, e012's main world), "8,2"
(grass and the edge) and "8,4" (grass and shrubs: with one body to a cell, the width that keeps
an arms race is open again), seeds 1-4 each, twelve at once on the 12-core machine, one thread
each (`run.sh`); at 256 (eight patches of each kind, the world people watch) "8,1" seeds 1-4
and "8,2" seeds 1-2, six at once on the 6-core Ubuntu machine (`run_256.sh`). 1,000,000 steps.
Reference: e012's "8,1" and "8,2" runs at 128 (the same worlds without the two laws).

## Result

18 runs, 1,000,000 steps each (`results/128_sigma8-{1,2,4}_seed{1..4}`, `256_sigma8-1_seed{1..4}`,
`256_sigma8-2_seed{1,2}`). Ranges are over the seeds of a world, medians over the second half of
the run unless said otherwise; "grass / narrow" gives the two places of a world. Reference: e012
(the same worlds without the two laws). Report: `report.html`.

| | grass and trees (8,1), 128 | grass and edge (8,2), 128 | grass and shrubs (8,4), 128 | grass and trees (8,1), 256 | e012 (8,1), 128 | e012 (8,2), 128 |
|---|---|---|---|---|---|---|
| population | 1,170-1,410 | 1,320-1,460 | 1,510-1,600 | 4,690-5,370 | 2,350-2,740 | 1,740-2,940 |
| population by place | 1,110-1,320 / 41-65 | 1,160-1,230 / 148-216 | 1,100-1,150 / 424-442 | 4,450-5,030 / 154-230 | 1,620-1,680 / 622-1,050 | 860-1,720 / 693-1,180 |
| cover by place (share of cells under a body) | 43-53% / 89-92% | 43-53% / 77-86% | 52-55% / 74-76% | 44-56% / 87-91% | - | - |
| world cells per body by place | 1.4-2.1 / 1.4-1.9 | 1.5-2.1 / 1.2-1.9 | 2.0-2.1 / 1.9-2.1 | 1.5-2.0 / 1.4-2.3 | - | - |
| mass per body by place | 3.6-5.0 / 5.7-7.8 | 4.4-5.1 / 5.6-7.3 | 4.2-4.7 / 5.9-6.6 | 4.3-4.5 / 6.8-9.8 | 5.7-6.2 / 15.5-31.5 | 5.4-17.5 / 14.0-31.3 |
| hard cells per body by place | 0.02-0.06 / 0.00-0.05 | 0.00-0.06 / 0.00-0.10 | 0.00-0.03 / 0.00-0.02 | 0.01-0.07 / 0.07-0.17 | 0.1-0.2 / 4.4-15.1 | 0.0-3.4 / 0.3-12.7 |
| bodies with a bite (front) by place | 0% / 0% | 0% / 0% | 0% / 0% | 0% / 0% | 0.1-0.2% / 12-34% (any side) | 0.1-11% / 0.2-13% |
| meat share of intake, whole world | under 0.001% | under 0.001% | under 0.001% | 0.001% | 8-10% | 0.5-11% |
| hardness of the front / back, narrow place | 1.00 / 1.00-1.02 | 1.00-1.03 / 1.00-1.04 | 1.00-1.01 / 1.00-1.01 | 1.02-1.06 / 1.01-1.07 | - | - |
| forward moves blocked | 78-93% | 81-94% | 89-94% | 85-94% | - | - |
| turns blocked | 65-84% | 68-84% | 68-81% | 78-82% | - | - |
| children lost for want of room | 81-86% | 84-86% | 88-90% | 83-86% | - | - |
| shoves | 0 | 0 | 0 | 0 | - | - |
| contacts per body per step | 0.08-0.20 | 0.09-0.30 | 0.14-0.32 | 0.22-0.32 | 2.0-3.7 | 0.03-0.57 |
| births per 10,000 steps | 29,000-35,000 | 33,000-40,000 | 36,000-39,000 | 108,000-145,000 | 232,000-336,000 | 200,000-392,000 |
| regrowth wasted (of 164 per step at 128) | 83-88 | 69-79 | 49-55 | 331-350 (of 655) | 0.7-5 | 0.0-0.2 |
| crossers | 0.0-0.8% | 0.1-1.0% | 0.5-2.3% | 0.6-0.9% | 0.1-0.7% | 0.6-2.9% |
| lineages alive, median | 2-7 | 1-8 | 3-7 | 9-21 | 9-15 | 6-12 |
| hunter lineages (front bite >= 2, 20,000+ steps) | 0 | 0 | 0 | 0 | 9-29 (any side) | 1-23 |
| steps per second, median | 770-1,530 | 710-1,550 | 720-890 | 360-440 (3 threads each) | 480-540 | 400-870 |

- **No arms race anywhere.** On every place of every run, hard cells per body stay under 0.1,
  no body has a bite (front or any side; at most 0.1% at any log step), meat is under 0.001%
  of the intake, and no hunter lineage exists (e012: 9-29 per seed on the trees). The trees hold
  41-65 bodies instead of 620-1,050 (cover 89-92%), the edge 148-216, the shrubs 424-442. The
  only hard bodies are the initial random ones (hard 8.5-9.0 on the trees at step 10,000, gone
  by 20,000) and single bodies later (hard 1-5 on a place of 20-50 bodies, no bite).
- **Reach pays: the grazer spreads over the grid.** On the grass a body covers 1.4-2.1 world
  cells with 3.6-5.0 cells (e012: 5.7-6.2 cells in one corner). The most common body at the
  end of the runs is 3-4 digestive cells at the center of the grid, one in each quarter, so
  that it eats from three or four world cells at once; corner bodies of three (one cell) and
  edge lines of four (two cells) come next. Intake per digestive cell is 0.013-0.015 per step
  against e012's 0.008: the cell's regrowth, not the gut, is the limit on the grass, so four
  cells in four quarters beat four cells in one.
- **The world is a jam.** 78-94% of forward actions do not move the body (the way stays
  taken), 65-84% of turns do not happen, 81-90% of children find no free spot and are lost,
  and no body is ever shoved (no body has muscle). Bodies stay 1-18% of the time (e012:
  38-78%): with nothing to lose by pushing, the policy pushes. A body moves once in 20-40
  steps. Half the cells of a grass place are covered, in one disc of two or three lineages per patch
  (the viewer); 1-8 lineages are alive (e012: 6-15).
- **Contact is rare and a tooth does not pay.** A body touches another 0.08-0.32 times per
  step (e012: 2.0-3.7 on the trees' crowd), and a broken cell of a grazer is worth 0.06-0.33
  energy (windows with 50+ breaks). A tooth is a hard cell with two muscle cells behind it:
  three cells that do not eat, 0.045 per step of gut intake forgone; at one touch in five
  steps it breaks even at best, and there are 8 times fewer births to find it with (29,000-
  40,000 per 10,000 steps against 200,000-392,000, since a child needs room).
- **Half the regrowth is wasted with trees.** A cell holds 8 and one body eats at most 0.32
  per step from it (16 digestive cells in one quarter), so the 6.5 per step of a tree cell
  feeds one body and the rest is lost: 83-88 of the 164 regrowth per step at 128 with trees,
  69-79 with the edge, 49-55 with shrubs (e012: 0-5). The population is 1,170-1,600 (e012:
  2,350-2,940).
- **The world stands.** No extinction, population never below 970; 710-1,550 steps/s at 128
  with twelve runs on one machine (faster than e012: fewer births).
- **256 (eight patches of each kind).** The same world eight times over: population 4,690-5,370 (e012: 7,570-11,060), grass 4,450-5,030 in eight discs, trees 154-230 (19-29 per patch), no bite anywhere (hard 0.07-0.17 on the trees, 0.01-0.07 on the grass), meat 0.001% of the intake, no hunter lineage, 85-94% of moves blocked, 331-350 of the 655 regrowth per step wasted. Lineages alive 9-21 (e012: 19-50). With the edge (8,2; seeds 1-2): population 5,140-5,500, the edge 618-741 bodies over eight patches (cover 82-83%, mass 5.9-6.2, hard 0.04, no bite, no hunter lineage), 89-92% of moves blocked, 298-314 of the regrowth wasted, 7-16 lineages alive, 144-174 steps/s on the slower machine.

## Conclusion

1. Fronts appear: no. Nothing bites, so nothing points: 0% of bodies with a bite on any side
   on every place, and the front and the back of a body are equally soft (1.00-1.04).
2. Reach pays: yes. Grass bodies cover 1.4-2.1 world cells; the winning shape is 3-4 digestive
   cells at the center of the grid, one per quarter, eating from 3-4 cells at once.
3. The arms race survives the queue: no, at every width (1, 2, 4), in every seed. Hard under
   0.1, meat under 0.001%, no hunter lineage.
4. The world stands at a bounded cost: yes (population 970+, 710-1,550 steps/s at 128).

What it changes: the crowd was the premise of the arms race, not an accident of it. e011's
"a cell holds more than one bite" worked because many bodies could stand in one cell, so every
move was a push into dozens of bodies and meat was everywhere; space at the resolution of a
world cell (4x4 body cells) took the crowd away, and with it contact (15 times rarer), meat,
teeth, armor, hunters, tortoises and corner bodies. What is left is one kind of body, the
smallest gut spread over the most cells, jammed in a disc of two or three lineages on each patch, with the trees
feeding one body per cell and wasting the rest. Facing by itself did nothing, since nothing
bites; it stays (one number per body, and the viewer reads a front now).

Space at the cell level is too coarse: a 3-cell body blocks a whole world cell, three in four
blocked moves press on a body whose cells are not even in the way, and nothing can pass. The
recommendation is not to give space up but to give it the resolution of the body: bodies
occupy their own cells on a world drawn at body-cell resolution (16 sub-cells per world cell;
occupancy is 16 times more cells, still cheap), so that a small body is small in the world,
bodies pass each other, and contact is the overlap of real cells. That is a world where the
crowd can come back where food is dense without two bodies ever sharing a spot. The other
lever is the food: a full cell that spills to its neighbors (fruit falls) would spread a tree
over more cells; it does not by itself bring contact back. Ground and friction (#16) waits
until the world has contact again: with nothing to bite, a leg has nothing to run from or
after.
