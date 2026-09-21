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

## Result, step 1 (the ladder)

Seed 9, 40,000 steps, every ledger at most 1e-14. The control column is e096's control run of this
world and seed (`c1225_life9_s0g0`), which step 0's own run reproduces column for column at step 40,000
(the timings apart), so the control's log and its 21 censuses are this ladder's control.

| | control | ring r1 | rays r2 | ring r2 | rays r4 |
|---|---|---|---|---|---|
| bodies | 10,253 | 10,249 | 8,443 | 11,671 | 12,749 |
| blocks a body | 27.6 | 28.8 | 31.1 | 26.0 | 25.9 |
| **births with no room** | 50.3% | 45.5% | 40.0% | 35.6% | 31.7% |
| moves blocked | 52.6% | 58.7% | 52.3% | 64.1% | 57.6% |
| sub-cells a child was placed at | 5.63 | 5.23 | 8.18 | 6.65 | 12.97 |
| cells a body stands on | 11.9% | 11.5% | 10.8% | 11.5% | 12.8% |
| land cells none stands on | 86.6% | 87.4% | 88.6% | 88.2% | 86.2% |
| travel of a grown body | 4.9 | 3.5 | 4.6 | 3.8 | 3.5 |
| intake a gut block | 0.0035 | 0.0031 | 0.0034 | 0.0032 | 0.0028 |
| grass standing | 21,381 | 16,611 | 13,838 | 12,856 | 10,358 |
| gut blocks a body | 16.5 | 18.2 | 19.8 | 16.3 | 17.4 |
| lineages | 12 | 15 | 11 | 16 | 13 |
| ms a step | 29.9 | 39.4 | 29.8 | 44.6 | 47.4 |

The ways of living of the same runs, read off their own censuses (21 each, from 20,000 to 40,000;
`results/provenance.csv`). Step 0's run wrote censuses on the default clock, so its 3 are not read here -
its world is the control's anyway.

| | control | ring r1 | rays r2 | ring r2 | rays r4 |
|---|---|---|---|---|---|
| kinds at a census | 8.14 | 6.10 | 7.43 | 5.52 | 5.71 |
| kinds kept to a place | 4.95 | 3.33 | 3.95 | 3.67 | 3.76 |
| the largest kind's share | 12.6% | 19.4% | 22.0% | 32.8% | 21.7% |
| the largest line's share | 58.9% | 56.6% | 55.6% | 30.4% | 56.5% |
| lines holding 5% | 3 | 1 | 2 | 4 | 1 |

**The jam gives way, in the order step 0 said it would.** Births with no room fall 50.3% -> 45.5% when
only the shape changes, -> 40.0% when only the reach doubles, -> 35.6% when both, -> 31.7% at four
lengths on the rays. Every rung is a step down the curve step 0 measured (35% of failures have room
inside one length, 75% within two, 97% within four), so the birth rule was the binding constraint, and
the crowd was the rule's as much as the world's.

**What it buys is not ways of living.** Kinds at a census fall on every rung (8.14 -> 5.52-7.43, against
a control ladder whose six seeds spread 1.02), kinds kept to a place fall with them (4.95 -> 3.33-3.95),
and the largest kind's share rises (12.6% -> 19.4-32.8%). The largest line's share stays where it was on
three rungs (55.6-56.6% against 58.9%) and falls on one (30.4%, inside the control ladder's own 42-78%
band). The world's plant is what pays: the grass standing falls by a fifth to a half (21,381 ->
10,358-16,611), because the children that used to be laid down as carrion are now bodies that eat.

**Room does not become movement either.** Travel falls (4.9 -> 3.5-4.6) and moves blocked rise on the
ring rungs (52.6% -> 58.7%, 64.1%): a child placed on a diagonal stands nearer its parent than one placed
along a ray (5.23 sub-cells against 5.63), so the ring relieves the birth and tightens the standing crowd.

**Cost.** The rays are free (29.8 ms a step at `reach` 2 against the control's 29.9); the ring is not
(39.4 and 44.6), since it walks up to 4`r`(`r`+1) spots where the rays walk 4`r`.

**The batch.** The ladder moved both the jam and who wins, so the rung that relieves the jam most within
two body lengths - `ring` 1, `reach` 2 - goes to the six-seed batch (100,000 steps, a census every 1,000
from 36,000, the control ladder's own shape): 6 runs at once, about 1.5-2.5 hours on 6 of 12 cores. One
seed cannot tell a fall of 2.6 kinds from the seed it was run on.

## Result, the batch

`ring` 1 with `reach` 2 on the six seeds of the control ladder, 100,000 steps, against the control
ladder itself (e081's seeds 9-11, e092's 12-14). Both sides are read the same way: 51 censuses from
50,000 to 100,000 and the log's second half (`results/provenance.csv`; the runs write a census every
1,000 from 36,000 and the reader takes the second half by step, which is 51 of the 65).

| measure | control | ring r2 | effect | control's spread |
|---|---|---|---|---|
| kinds at a census | 7.53 | 5.01 | **-2.52** | 1.02 |
| kinds kept to a place | 4.35 | 2.96 | **-1.39** | 1.24 |
| the largest kind's share | 14.8% | 32.9% | **+18.1%** | 3.8% |
| the largest line's share | 54.9% | 60.6% | +5.7% | 35.5% |
| lines over 5% | 1 | 2 | +1 | 2 |
| kills' share of intake | 27.8% | 32.7% | +4.9% | 4.7% |
| **births with no room** | 46.8% | 33.2% | **-13.6%** | 2.7% |
| moves blocked | 50.5% | 60.7% | +10.2% | 7.6% |
| sub-cells a child was placed at | - | 6.90 | - | - |
| bodies | 8,809 | 10,734 | +1,925 | 1,611 |
| travel of a grown body | 5.2 | 2.4 | -2.9 | 2.0 |

Every effect that matters is far outside the control ladder's own spread, and in the same direction on
every seed: the jam gives way on all six (32.0-34.1% against 46.5-49.2%), kinds at a census fall on all
six (4.12-6.69 against 7.25-8.27), and the largest kind's share rises on five of six. The largest line's
share does not move out of the control's band (35.5 points wide), so **what changes is not which line
holds the world but how many ways of living it is parted into**.

## Conclusion

**Not kept.** Step 0 answered #109's question: the jam is the birth rule's, not the world's. Every spot
the rule tries is held by another body, never by a wall; a spot with room is within the rule's own reach
for 35% of the failures, within two body lengths for 75%, within four for 97%, and beyond eight for
0.02%; and 98% of the spots with room at the nearest distance lie off the four rays the rule searches. A
body stands on 10.8% of the world's cells. Half of all births fail in a world that is nine tenths empty
because a rigid grid has to land on contiguous free sub-cells reached by 24 spots on four rays.

Step 1 relieved it - 46.8% of births with no room to 33.2% over six seeds - and **the relief costs ways
of living**: kinds at a census 7.53 -> 5.01 and kinds kept to a place 4.35 -> 2.96 against a control
spread of 1.02 and 1.24, with the largest kind's share 14.8% -> 32.9%. The same fall showed on all four
rungs of the ladder, at every shape and reach. So the crowd's jam was not a lid on the ways of living: it
was part of what held them apart. A child that can only be laid within one body length on four rays
leaves its lineage where its parent stood; a child that can be laid anywhere within two lengths spreads
it, and the winner spreads fastest - dominance rises, travel falls (5.2 -> 2.4, the crowd is nearer), and
the grass standing falls by a fifth to a half because the children that used to be laid down as carrion
are now bodies that eat.

**The conditions this holds under**: stage C's default world on c1225 at a body's scale of 1/16, bodies
that are rigid rectangles on a 4-16 grid placed as a whole, and the measures of e094. It says nothing
about a world whose bodies bend, grow into a space, or choose where their children go.

What it changes in `vision.md`: section 2's crowding row (the jam is the birth rule's, measured, and
relieving it lowers the ways of living), section 3 item 4 (the crowd is not a lid to be lifted - it is a
dispersal limit that keeps lines apart, as e083 found places to be), and section 5 (#109 is answered;
**room is not an axis of the 3D set (#5) but its background**, and the set is designed for the food at
height alone). #104 (re-testing P2's foods in a thinner crowd) now has a knob that thins the crowd, but
the world under it holds fewer ways of living, so a re-test would be read against a poorer control: it
stays shut until something thins the crowd without costing kinds.

Open question, for the 3D set to answer if it can: dispersal is now known to be one of the few things
that moves the ways of living in this world at all (2.5 kinds), and it moved them the wrong way. Whether
a body that **chooses** how far its children go - a trait, not a law of the world, so not this piece's
business - would part the world instead of levelling it is untested.
