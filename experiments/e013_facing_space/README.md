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
the lines that meet in the world (line c of the pusher meets line c + 4 dx of the other; two
tips touch if depth + depth + 4 (cells between the anchors) <= 7), then a shove if the muscle
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

TODO

## Conclusion

TODO
