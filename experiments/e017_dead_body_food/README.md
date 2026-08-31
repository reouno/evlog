# e017 A dead body is food where it lies

Date: 2026-08-31

## Purpose

e016 made bodies move (a cell held by a body does not regrow) and they find only grass:
contacts fell to 0.02-0.05 per body per step, no tooth, no meat, one block of 7-9 gut cells
winning every run with 1-5 lineages alive. A body gains nothing from another body in that
world but its place, and places are free. The sentence "a crowd is a place worth going to"
needs a premise the world does not have yet: matter that does not vanish.

Today a body that dies is gone with everything it was made of. Its cells cost the parent
0.02 each to build (`CELL_ENERGY`, e010's "a cell costs what it holds") and the energy it
still held is dropped; a child that finds no room, or is born without cells, takes half the
parent's energy with it into nothing; a cell broken by a push that no gut takes vanishes.
This experiment adds the premise as a law about matter (issue #21, vision "Next" 1): **what a
body is made of does not vanish when it dies.** Every cell of a dead body is `CELL_ENERGY`
of food on the world cell under it, and the energy the body still held is split over its
cells and lies with them; a child never placed lies where its parent stands; a broken cell
nobody eats lies where it was. It is the same food the gut cells eat: whoever stands there
next eats it. Upkeep and the work of moving are heat and vanish, as before.

The law names no trait and costs nothing per step. What it is worth is set by the world's
own numbers, and they are small: in e016, 3-5 bodies of 8-10 cells die per step, nearly all
with no energy left (deaths by energy are 99% of deaths), so the dead lay 0.5-1.0 of matter
per step, and the children never placed 0.15-0.6 more, against 33-55 of food eaten per step.
A body is worth two to four per cent of what the world eats. The real world's scavengers
live on a carcass because it is concentrated, not because it is large next to the sun; here
the same holds, so the experiment asks whether two to four per cent, laid where bodies are,
changes where bodies go. To see how the answer depends on the amount, four runs make a cell
of five times the matter (`CELL_ENERGY` = 0.1, an argument now): a child then costs five
times more to build and a dead body is worth five times more, the two sides of the same law.
Part 2, the closed cycle through the soil, is #20 (e018).

## Hypothesis

1. **The dead are eaten, and the world remembers little.** Dead matter laid on the ground is
   2-4% of the food eaten (median over the second half) in the twelve runs at 0.02, and
   10-20% at 0.1. It is eaten: the dead matter lying uneaten (`carrion`) levels off (the last
   quarter's median within 20% of the third quarter's) below 1,000 in every run (a thousand
   steps' worth at the rate it falls), because bodies die where bodies are.
2. **No scavenger.** No lineage lives 20,000 steps or more on dead matter for more than half
   of its intake, at either value, and bodies with more dead matter than plant in their
   lifetime intake are under 1% of the population. Whether one appears at 0.1 is watched.
3. **A crowd is not yet a place worth going to.** Contacts stay under 0.1 per body per step
   (e016: 0.02-0.05) and the crowding of bodies (neighbors: other bodies within the 3x3
   world cells around a body's place, computed from the snapshots for e016 too) is within
   20% of e016's on the same world and seed in at least nine of the twelve runs at 0.02.
   At 0.1 this is the open question: if a crowd follows death anywhere, it is there
   (contacts above 0.1 or neighbors above e016's by half in at least two seeds of four).
4. **The winners.** Judged by #19's rule (principles.md "Pressures, not parts"): lineages
   alive (e016: 1-5) and the winning body (e016: a block of 7-9 gut cells over 1.6-2.7
   world cells) are unchanged at 0.02; at 0.1 the population falls (a child costs five times
   more) and the winning body is watched, not predicted. The world stands: no extinction,
   population holding over the second half (last quarter within 20% of the third), at least
   200 steps per second with six runs sharing a machine.

## Method

Code: e016 (`experiments/e016_plant_under_body`, strict reading of the shade law only) with
the food of the world split into what it holds (`res`) and how much of that is dead matter
(`carrion`, a measure: no rule reads it), and matter laid on the ground at three points:

- a body that dies (energy at or below zero, age above 3,000, or a body pushed to nothing)
  leaves its sub-cells and lays, on the world cell under each of its cells, `CELL_ENERGY`
  plus its share of the energy the body still held (`lay_body`); a body with no cells lays
  its energy on the cell under its anchor;
- a child never placed (no room next to the parent, or born without cells) lays the energy
  the parent gave it on the cell under the parent's anchor;
- a cell broken by a push whose pusher has no gut lays `CELL_ENERGY` plus its share of the
  victim's energy where it was (a pusher with a gut eats it, as before).

Dead matter is added in full: the cap (8) bounds what a plant grows to, not what lies on the
ground, and a cell above the cap does not regrow until it is eaten down. A gut takes from
the cell under it as before (0.02 per gut cell per step), plant and dead matter in the
cell's proportion; the dead matter taken is counted as `meat` (with broken cells, as in
e010-e016), so the diet columns, `meat_majority` and the lineage log's `meat` read
scavenging. New columns: `dead` (matter laid per step) and `carrion` (dead matter lying
uneaten at the log step) in the log and per place. One argument after the widths:
`CELL_ENERGY` (0.02 by default).

Not byte-identical to e016 (the food is different from the first death).

Neighbors (hypothesis 3) are computed by the report from the snapshots (`long.jsonl`, every
5,000 steps: position, body, facing): for each body, the other bodies holding a sub-cell in
the 3x3 world cells around the cell under the middle of its box; mean over bodies, median
over the second half; the same for e016's runs.

Pilot (seed 9, 100,000 steps, 128x128 "8,1", grass and trees, at 0.02 and 0.1;
`results/*seed9*`, medians over the second half): the world stands under both. At 0.02, 563
bodies, dead matter laid 1.25 per step, 3.7% of the 34 eaten; contacts 0.078 per body per
step (e016: 0.02-0.05), forward 37% of decisions, bodies with more dead matter than plant
0.3%; 2,274 steps/s with six threads. At 0.1, 687 bodies of mass 8 (12 at 0.02), 3.1 laid
per step, 8.3% of the 37 eaten (less than five times: a dearer cell makes a smaller body);
contacts 0.039. Under both, the start is a burden: the 1,600 random bodies of step 0 die
with their 5 of energy each and lay about 8,000 of matter where nobody goes; the stock
(`carrion`) is 5,000 at step 10,000 and 2,000 at 100,000, half of it beyond the patches,
falling. Hypothesis 1's level is judged from step 500,000 on for that reason.

Runs (1,000,000 steps): 128x128 with widths "8,1", "8,2", "8,4" (grass and trees, edge,
shrubs), seeds 1-4, at 0.02 (twelve runs), and "8,1" seeds 1-4 at 0.1 (four runs,
`results/128_sigma8-1-cell0.1_*`); six at a time on each of two machines with one thread
each (`run.sh law 1 2 && run.sh cell 1 2` and the same with seeds 3 4; outputs are
byte-identical across machines). Reference: e016, the same worlds and seeds.

    cargo run --release -p e017_dead_body_food -- <steps> <seed> <size> <widths> [cell_energy]
    uv run python experiments/e017_dead_body_food/report.py

## Result

(after the runs)

## Conclusion

(after the runs)
