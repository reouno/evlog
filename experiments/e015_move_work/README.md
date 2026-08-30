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
about 50 minutes). The 256 runs (the world people watch, six at once, 2.8 hours) are not run
by default: in e014 they were the 128 world eight times over and added nothing to the answer;
they are run only if the 128 result shows something a viewer should see at that size.
Reference: e014, e013 and e012, the same worlds and seeds. The report compares them.

    cargo run --release -p e015_move_work -- <steps> <seed> <size> <widths>
    uv run python experiments/e015_move_work/report.py

## Result

(pending)

## Conclusion

(pending)
