# e097: the crowd measured at its cause (#109 step 0)

Date: 2026-09-21

## Purpose

Twelve laws in a row were rejected because "the crowd absorbed it" (P1, P2, P3; `vision.md` section 3,
item 4), and only the twelfth measured the crowd itself: the cells bodies stand on carry 8.5-10.5 blocks
of the 16 a cell holds whatever the population, and 46-50% of births fail for want of room in cells that
are half empty (e096). So the world's carrying capacity is set by the geometry of placing a rigid grid,
not by food, hunters or seasons - and the rule that places a child has never been tested:

> one of the four axis directions at random, 1..=`reach` sub-cells along it, the first spot the child's
> whole rectangle fits in, `reach` being the wider of parent and child (about 5-6 sub-cells).

At most 24 candidate spots, all on four rays, all within one body length of the parent. **This step asks
what a failed birth actually hits**, before a rung of the ladder is spent on it: is the jam a fact about
the world (bodies really have nowhere to go) or a fact about the birth rule (there is room, but not on
those 24 spots)? Step 1 - one ladder over whatever this names - is designed once this is read (#109).

No law is added. With `probe` 0 the run is e092's control bit for bit (checked below).

## Hypothesis

In the default world at its settled crowd, of the births that find no room:

1. **the rule's own spots are held by bodies, not by walls** - the sea and the crownless cells are not
   what a birth hits, so the jam is bodies standing where the child would go;
2. **a spot with room is there to find, within a body length or two**, and nearly all of those spots lie
   off the four rays the rule searches (a ring at distance `r` holds 8`r` spots, of which 4 are on a
   ray), so the rule's shape is what the jam is made of;
3. the parent's own cell and its neighbours are half empty (e096's 8.5-10.5 blocks of 16), so what the
   child cannot find is not free sub-cells but free sub-cells **contiguous in the shape of its grid**;
4. only a small share of failures have no spot within 8 body lengths - if that share is large instead,
   the jam is the world's, and #109's track closes with that sentence.

## Method

**The instrument** (`src/main.rs`, no law). A share `probe` of the births that find no room is measured
where it failed and written to `<prefix>_room.csv`: what held each of the rule's own spots (a body, or a
wall - the sea a land body cannot enter, a cell with no crown), the distance to the nearest spot the
child does fit in (searched ring by ring out to `probe_far` body lengths, the diagonals the rule never
tries among them; -1 if there is none), the spots with room on that ring and how many of them lie on the
four rays, and the free sub-cells of the parent's cell and of its eight neighbours. The log gains
`cells_held` (the share of the world's cells a body stands on), `land_bare` (the share of the land's none
stands on), `place_k` (how far along its ray a placed child had to go) and `probed`; `<prefix>_ground.csv`
holds the occupied cells by habitat and medium at the end of the run.

**The control costs nothing.** The probe draws from a stream of its own and touches neither the world nor
the ledger. Checked: this crate at `probe` 0 and e092's, on the same arguments (c1225, life 99, 2,000
steps), write identical `agents.csv`, `bands.csv`, `events.csv` and `lineages.csv`, and identical log rows
but for the timings; the run with `probe` 0.01 is identical to both in the same files, and its step costs
95.3 ms against 95.4 and 95.0 (the probe is free at this rate).

**The run.** Seed 9 of the default world (`foundation.md`), 40,000 steps - the ladder's own length, so the
numbers read here stand beside e092's and e096's controls.

    (nohup bash experiments/e097_room/run.sh c1225 40000 9 probe probe=0.01 \
      > experiments/e097_room/results/c1225_life9_probe.log 2>&1 < /dev/null &)

**What is read** (`room.py`, over the settled window from step 20,000, the window written to
`results/provenance.csv`): the share of failed births whose tried spots were held by a body and by a wall;
the distribution of the distance to the nearest spot with room, in body lengths; the share of failures
with no spot within 8 body lengths; the share of the nearest ring's spots that lie on the four rays; the
free sub-cells here and around; and, from the log, the ground the bodies leave empty.

**Stop early if:**

- `pop` < 500 at 20000

**Cost.** One run on one core, about 25 minutes on this Mac. Nothing on the Ubuntu box.

## Result, step 0

The run is the control world to the bit: its log at step 40,000 is e096's own control run
(`e096_shade/results/c1225_life9_s0g0`) column for column, but for the timings. 9,224 bodies at the end,
the ledger at 3.0e-15, 1,156 s on one core.

**A birth that found no room** (14,800 of them measured at `probe` 0.01, over steps 20,000-39,998;
`results/provenance.csv`):

| | all | land | surface | bottom |
|---|---|---|---|---|
| failed births measured | 14,800 | 4,674 | 2,217 | 7,909 |
| the rule's reach (sub-cells) | 6.76 | 6.69 | 7.32 | 6.64 |
| blocks of the child | 38.6 | 43.5 | 42.0 | 34.7 |
| **its spots held by a body** | 100.0% | 100.0% | 100.0% | 100.0% |
| its spots held by a wall | 0.0% | 0.0% | 0.0% | 0.0% |
| free sub-cells, parent's cell | 27.3% | 24.9% | 29.0% | 28.2% |
| free sub-cells, its neighbours | 30.8% | 27.2% | 33.1% | 32.4% |
| **room within 1 body length** (the rule's own reach) | 35.1% | 35.4% | 36.1% | 34.7% |
| room within 2 | 75.2% | 73.7% | 80.1% | 74.7% |
| room within 4 | 96.8% | 96.0% | 99.0% | 96.6% |
| room within 8 | 100.0% | 100.0% | 100.0% | 99.9% |
| **no room within 8** | 0.0% | 0.0% | 0.0% | 0.1% |
| nearest room, body lengths (p50) | 1.56 | 1.60 | 1.50 | 1.50 |
| the same (p90) | 3.00 | 3.17 | 2.75 | 3.00 |
| of that ring's spots, on the four rays | 2.0% | 2.0% | 2.1% | 2.1% |

**The world around them.** Births with no room 49.9% (e092's 46-49% again), a placed child went 5.63
sub-cells out, **a body stands on 10.8% of the world's cells and on 11.8% of the land's** - 88.2% of the
land carries none. By habitat (`results/*_ground.csv`, the run's end): the thickest land, `land_hot_wet`,
carries a body on 37% of its cells, `land_hot_moist` on 14%, `land_hot_dry` on 5%.

**The answer to step 0 is the third line of the table.** Every spot the rule tries is held by another
body - not once by the sea, a crownless cell or any wall - and **a spot with room is always there**: for
35% of the failures inside the rule's own reach, for 75% within two body lengths, for 97% within four,
and for all but 0.02% within eight. What the rule misses is not distance alone but shape: a ring at
distance `r` holds 8`r` spots and the rule tries the 4 on the axes, so **98% of the spots with room at the
nearest distance are ones it never looks at**. The parent's own cell is 27% free sub-cells and its
neighbours 31%, so what a child cannot find is not free sub-cells but free sub-cells contiguous in the
shape of its rigid grid - e096's finding, now measured from the birth's side.

So the jam is the birth rule's, not the world's: hypotheses 1-4 all hold. The reach and the shape are both
named, and step 1 ladders both.

## Method, step 1 (the ladder)

Two knobs, both off at their control value, neither heritable (a law of the world, never a trait;
`principles.md` principle 2):

- **the reach** (`reach`, body lengths, 1 being today's rule): a child looks `reach` x max(parent side,
  child side) sub-cells out instead of one body length;
- **the shape** (`ring`, 0 being today's four rays): the search walks **every** spot at a distance - the
  8`r` of the ring, the diagonals among them - before it goes further out, in a walk rotated by the same
  single draw the four rays are rotated by today.

The cycle (#109). **What it takes**: nothing material - the child's matter and its parent's cost are
unchanged, and a failed birth already lays its matter down as carrion. What it takes from a lineage is the
monopoly of its parent's neighbourhood. **What refills it**: nothing needs to. **What limits it**: a child
born further off lands where the food, the water and the medium may be worse, and it still has to fit; a
body that spreads its children thin loses the place its parent proved. **The balance it should settle
into**: lineages spread over ground they do not hold today, local saturation falls, and either the same
body wins everywhere it now reaches or the pressure moves to the places children now reach.

**The rungs** (seed 9, 40,000 steps, a census every 1,000 from 20,000 - the shape e096's ladder read;
`probe` 0, so the jam is read from the log):

| rung | `reach` | `ring` | the question it answers |
|---|---|---|---|
| ring r1 | 1 | 1 | does the shape alone do it - the 35% with room inside today's reach, off the rays? |
| rays r2 | 2 | 0 | does the reach alone - the 75% within two body lengths? |
| ring r2 | 2 | 1 | both, the rung that should leave the least room unfound |
| rays r4 | 4 | 0 | how far the reach must go on the rays alone (97% within four) |

The control is e096's control run of this world and seed (21 censuses from 20,000), which this crate
reproduces bit for bit, and step 0's own run beside it.

**Tests.** The ring walks every spot at its distance, each once, the four rays' own among them
(`the_ring_holds_every_spot_at_its_distance`). With `reach` 1 and `ring` 0 the run is e092's to the bit,
re-checked after the search was rewritten (identical `agents.csv`, `bands.csv`, `events.csv`,
`lineages.csv` on c1225, life 99, 2,000 steps).

**Read by** `ladder.py`: bodies, blocks a body, the jam (births with no room, moves blocked), how far out a
child was placed, the cells a body stands on and the land none stands on, travel, the intake per gut block
(e057's fingerprint), the largest line's share, and the ways of living of each run from its own censuses
(kinds at a census, kinds kept to a place, the largest kind's share). What each reading used is in
`results/provenance.csv`.

**Stop early if:** `pop` < 500 at 20000 (per run, a precondition).

**Cost.** Four rungs at once, one core each, 40,000 steps: 20-40 minutes on this Mac, 8 cores left free.
The ring costs more per birth than the rays (at most 4`r`(`r`+1) spots against 4`r`), and what it actually
cost is in the table's `ms a step`.

## Result, step 1

(to be written)

## Conclusion

(to be written)
