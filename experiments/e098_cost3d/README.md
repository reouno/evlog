# e098: what 3D costs (#110, a spike)

Date: 2026-09-21

## Purpose

The next piece is the 3D set (#5), and its design cannot be priced until the clock is measured
(`CLAUDE.md`: when a change adds compute cost, state why and how much). Stage C runs at 30.5 ms a
step with about 8,600 bodies, which is what makes a step of this project take a day. A 3D body grid
touches every hot loop: the grid goes from 16x16 to 8x8x8, a block gets 6 faces, a world cell holds
64 sub-cells instead of 16, and how a body is classified has to follow.

**This is a spike, not an experiment**: no law, no batch, no ladder, nothing kept. The only question
is the clock, and the decision it feeds (#110): a six-seed batch at 100,000 steps under about 5 hours
(180 ms a step) means the 3D set is designed on 8x8x8; over that, the grid is cut until it fits.

## Hypothesis

3D costs between 3x and 8x a step at the same population - the grid's cells double at the cap and
the blocks a body actually grows rise with the cube of its side - and the gene-list cache still
absorbs the development, since what it caches is a list of genes and not a geometry.

## Method

A throwaway crate with the loops 3D touches and nothing else, in two arms of the same harness:

- **2d**: today's geometry - a grid of side 4-16 stored row by row, a world cell of 4x4 sub-cells
  with three layers (e065, e091), 4 faces a block, 4 directions, 10 readings to 4 actions;
- **3d**: a grid of side 4-8 across and `sz` cells up (8 for the full grid, 4 for the cut one), a
  world cell of 4x4x4 sub-cells with no layers (height is real), 6 faces a block, 6 directions, 14
  readings to 6 actions. Development, the parts of a grid (26 neighbours now), the tips, the open
  faces, the occupancy, `fits`, the contact physics and the placement of a child all follow.

**What both arms do a step is driven at e097's control rates**, so only the geometry differs: 0.65
turns a body, the action mix (stay 5.4%, forward 86.1%, turn 8.5%), 0.0122 children a body of which
0.0054 need a development the gene-list cache cannot answer, one body out for one child placed. The
pool of bodies is drawn to the control's side (5-7), and the ground is cut to whole tiles until the
crowd is the control's.

**The calibration** (the 2D arm against e097's control, 10,000 bodies): blocks a body 25.7 against
27.6, the sub-cells bodies hold where they stand 53% against e096's 53-66%, births with no room 20%
against 34%, moves blocked 39% of those tried against 58.5%. The arm is a little looser than the
world it copies, so the crowd's share of the cost is if anything understated in both arms.

**What is left out**, because 3D does not touch it: the climate and the producers (2.55 ms a step),
the lineages (0.66 ms), the matter ledger, the censuses, the water and heat ledgers. The 2D arm
therefore costs 1.7 us a body against the control's 3.2 - it covers 54% of the cost a body - and the
projection below is given as a range because of it.

    cargo build --release -p e098_cost3d
    bash experiments/e098_cost3d/run.sh  > experiments/e098_cost3d/results/spike.txt  2>&1
    bash experiments/e098_cost3d/run2.sh > experiments/e098_cost3d/results/spike2.txt 2>&1
    uv run python experiments/e098_cost3d/read.py

**Cost.** One core, about 20 minutes on this Mac (the six-at-once runs use six for a minute). No batch.

## Result

The arms at the control's population (10,000 bodies, 512x512, three seeds, one run at a time;
`results/spike.txt`, read by `read.py`):

| | 2d 16x16 | 3d 8x8x8 | 3d 8x8x4 |
|---|---|---|---|
| ms a step | 14.4 (13.6-15.6) | 47.2 (41.4-51.7) | 35.1 (28.7-38.3) |
| us a body | 1.49 | 4.74 | 3.52 |
| **against 2D** | 1 | **3.18x** | **2.37x** |
| blocks a body | 25.7 | 126.5 | 75.4 |
| us a block | 0.058 | 0.037 | 0.047 |
| the occupancy grid | 51.9 MB | 270.5 MB | 270.5 MB |
| a body in memory | 1,888 B | 5,152 B | 5,152 B |

**Six at once - the batch's own shape** (six seeds, one core each): 2D 17.3 ms a step (16.0-18.4),
3D 49.0 (44.0-52.4), so **3D costs 2.83x** there. 3D is the less crowded of the two by memory: six
2D runs cost each other 20%, six 3D runs 4%.

**A cost a block, not a cost a cell.** A 3D body is 4.9x the blocks of a 2D one at the same side
(6.7), and costs 3.2x a step - less than its blocks, because the parts that are per body and not per
block (the decision, the clock, the mate) do not grow. One development is linear in the grid's cells
in both arms: 1.32 us a cell in 2D (90.7 us over 68.9 cells), 0.99 in 3D (452 us over 458.6), 1.04
in the cut grid (247 us over 236.6). **The cache is untouched by any of this**: what it keys on is a
list of genes, so it still answers 56% of children, and the development stays 36% of the step in
both arms (the same share, three times the milliseconds).

What each part costs, by what leaving it out saves (seed 1, 10,000 bodies; a run with a part off
draws a different stream, so anything under the spread between runs - 0.8 ms in 2D, 2.5 in 3D - is
noise, not a cost):

| part | 2D ms | share | 3D ms | share |
|---|---|---|---|---|
| the senses (`look` over the box of cells, per direction, per range) | 6.35 | 41% | 15.85 | 33% |
| the births (mate, development, placement) | 4.52 | 29% | 18.96 | 39% |
| of which the development alone | 5.66 | 36% | 17.56 | 36% |
| the move (`push`, `fits`, claim and release) | 2.78 | 18% | 6.84 | 14% |
| the wear, the eating, the faces | 0.88 | 6% | <noise | - |
| the step | 15.64 | | 48.45 | |

**The same matter instead of the same population.** A 3D body of the same side holds 4.9x the
blocks, so a world of today's matter holds about 1,940 of them, not 10,000 - and that world costs
9.0 ms a step against the 2D arm's 14.4. **3D at today's matter is cheaper than today.** The two
rows bracket the answer: whichever way the 3D set prices a block, the clock lands between 0.6x and
3.2x of today's.

**The projection onto the control** (`results/provenance.csv`): the control is e092's control ladder
at 100,000 steps, six at once - 30.5 ms a step, of which world 2.55, bodies 27.3, lineages 0.66. The
world and the lineages do not change; the bodies' time is multiplied by the 2.83 measured six at
once, either in full (the upper line) or only over the 54% of the cost a body this harness covers
(the lower line):

**3D at the control's population costs 58-80 ms a step against the control's 30.5, and a six-seed
batch of 100,000 steps takes 1.6-2.2 hours against today's 1.0-1.2.** The line was 5 hours.

**Memory**: the occupancy grid is 270 MB at a world 4 cells tall and 135 MB at 2 (against 52 MB in
2D, where the third layer is the crown), the bodies 52 MB at 10,000 (against 19 MB). A run is about
350 MB, six at once 2.1 GB - nothing on either machine.

**What the classification would have to become** (`analysis/`, `e060_census/census.py`,
`e068_kinds/kinds.py`): its shape does not change, only its size. A birth form is
`(side, born_<kind> for each kind of block, born_bite, density)` and the block columns are already
read off the census's own header (e094), so a body's form gains exactly one column - the grid's
height beside its side - which is one line in `schema.USED` and one in `kinds.signature`. Two things
are named lists and would follow the crate: `MEDIA` in `kinds.py` (land, surface, bottom, and e091's
crown), which becomes whatever media a world with a real height has, and `census.way`'s diet, which
is untouched unless the 3D set adds a food. Nothing is rewritten; the third axis is a column.

## Conclusion

**The hypothesis holds at its lower edge, and the answer to #110 is the first of its three lines:
the 3D set is designed on 8x8x8.** At the control's population 3D costs 2.8-3.2x a step, which puts
a six-seed batch of 100,000 steps at 1.6-2.2 hours - a third of the 5 hours the decision allowed. At
the control's *matter* it costs less than today, because a world of today's blocks holds a fifth of
the bodies. The grid does not have to be cut: 8x8x4 buys 25% of the clock and would be spent for a
reason of its own, not for the machine.

Three things the design should carry from this, none of them a law:

- **A body's blocks, not its cells, are what is paid**: 0.037-0.058 us a block in both arms, so what
  the set must price is how many blocks a 3D body grows. At the same side that is 4.9x today's, and
  every per-block law (upkeep, matter, the faces) meets that multiplier before the clock does.
- **The senses and the development are two thirds of the step in both geometries.** If the 3D set
  ever needs more than it can afford, those are where it is, not in the occupancy grid.
- The measures need one column (the grid's height) and one list (`MEDIA`); `analysis/` changes size,
  not shape.

`vision.md` section 5 item 1 is settled: #110 is answered and the 3D set is priced. No row of section
2 changes - this spike ran no world and measured no way of living.

No `report.html`: a spike with no law and no batch has one table and a decision, and they are above.
