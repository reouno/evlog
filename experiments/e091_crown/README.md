# e091: the crown as a place (#101 C1 + C2 + C3, stage C)

Date: 2026-09-20

## Purpose

e088-e090 spent three stage C slots on a food parted by **what is mixed into a mouthful** (seed lying with the
grass, opened by a tooth, carried by the wind, worth more per gram). It never led a kind: a gut takes a cell's
foods in their proportions, so the seed eater was always also the grass eater. What parts kinds in this world
is **where a body must be** - three of the four media hold kinds of their own, and the two plant foods with
kinds of their own are reached by being in a place, not by carrying a tool.

#101 gives the land a second place. A stand of wood is 17% of the land's cells and its floor carries no more
grass than the lawn (0.151 against 0.154 a cell, e081's control); the crown over it is a place with a food in
it and no grass at all. The three laws go in together (the design is in #101 and not repeated here):

- **C1, the crown is a place.** A land cell whose wood is `crown_at` (1) or more carries a crown, a layer of
  the occupancy as the water's surface and bottom are (e065). A body in a crown holds the crown and nothing of
  the floor: it reaches the crown's food and not the floor's grass, litter or carrion, and a body on the floor
  cannot reach it (nor it them: a hunter below cannot touch what stands above). Where no crown stands the layer
  is a wall, so nothing in a crown hangs over the lawn.
- **C2, the crown keeps its yield, and the floor gets what falls.** `wood_yield` (3e-5 a step per unit of
  standing wood, e073) drops into the cell's crown as `fruit`, soft: a gut up there takes it with no tooth.
  A share `fruit_fall` (0.5) of every drop falls to the floor instead and is today's browse there, behind a
  tooth of `wood_hard` (3). A cell under `crown_at` drops all of it as browse, as in e073. Fruit rots as
  browse does (warmth x water).
- **C3, a branch holds only so much.** A body stands in a crown only while its mass is at most `hold` (10) x
  the cell's wood; a heavier one stands on the floor. No new gene and no new output: the world decides, as the
  water's density does, so a body light enough climbs when it walks under a stand and comes down when it grows
  too heavy or the stand falls.

## Hypothesis

#101's done-when, on seeds 9-11 at 100,000 steps against e081's control ladder (`c1225_life{9,10,11}_u0`),
censuses every 1,000 from 36,000:

1. **More ways of living.** Kinds at a census over each control by 1 or more (7.45 / 8.27 / 7.25); kinds kept
   to a place not below 4.75 / 4.65 / 4.47.
2. **The foods part the kinds.** A fruit-led and a grass-led kind each hold 5% or more of the grown bodies at
   a census, on every seed (a kind's leading food is the one that gives its grown bodies the most matter;
   there is no fiber law here, so matter is energy).
3. **Size follows the food.** Grass-led kinds weigh 1.3 times the fruit-led ones or more.
4. **No harm.** The world stands; the ledger holds; the largest line no higher than its control's share; the
   floor's kinds are not lost (the shore and bottom kinds hold their shares).

**Stopping rule** (agreed in #101): if no fruit-led kind holds 5% on any seed, **P2 ends** - three stage C
slots will have said that a plant food does not make a way of living in this world - and the next piece is
chosen from `vision.md`'s gap table.

## Method

e090's crate with the three laws and its seed and fiber laws off (`seed_share`, `seed_drift`, `ferment` 0).
`body.rs` holds C1 and C3: the occupancy gains a third layer (`CROWN`), `Occ::set_crowns` opens it where the
wood stands and walls it where the wood goes (after every producers' update, one pass over the cells every
ten steps), and `Occ::layer_for` says which layer a body belongs in wherever it would stand, which `fits` tests
before a move and the body settles into after it. `plants.rs` holds C2 (`fruit`, `take_fruit`).

**The rates, before the pilot.** `hold` 10 was read off the control's own census: over the second half of
`c1225_life9_u0`, 37% of the land's bodies stand on a cell with wood 1 or more, and at `hold` 10 14.5% of
those are light enough for its crown (5.4% of the land's bodies), with a median mass of 36.8 against 50.4 for
the bodies on stands. So the ceiling binds at both ends, which is what C3's "wrong if" asks. `fruit_fall` 0.5
is #101's first value.

**Checks.** At `crown_at` 0 a 2,000-step run on seed 9 reproduces e081's control log column for column (the
new columns are the only difference, and they are 0). Tests: the crown's occupancy (a light body and a heavy
one hold the same sub-cells without meeting, a crown's layer is a wall over the lawn, and a crown that goes
leaves the body to come down when the floor is free); the split of the drop and the rot of the fruit; and
matter conserved over 3,000 steps with every law of stage C on at once, the crown among them, with the
occupancy's invariant checked at the end.

**Measures, no law.** The log gains `fruit` (what the crowns hold), `fruit_intake` (what guts took from them,
a body's units a step) and `climbs` (times a body changed layer), and every per-medium column gains its
`_crown` twin (the medium is now land, surface, bottom, crown); `agents.csv` gains `fruit`, a body's lifetime
intake from the crowns, and its `medium` reads 3 in a crown; `bands.csv` counts a crown's body on its cell as
the floor's. The viewer gains the `fruit` layer.

**Runs.** No stage B run: the producers' matter flow is unchanged, only where the yield lands, which the ledger
test and the split's unit test cover. A pilot on seed 9, 40,000 steps (does anything stand in the crowns, and
what does it eat), then the batch, seeds 9-11, 100,000 steps.

    (nohup bash experiments/e091_crown/run.sh c1225 40000 9 pilot census=10000 census_from=20000 \
      crown_at=1 hold=10 fruit_fall=0.5 > experiments/e091_crown/results/c1225_life9_pilot.log 2>&1 < /dev/null &)
    (nohup bash experiments/e091_crown/batch.sh > experiments/e091_crown/results/batch.log 2>&1 < /dev/null &)

1 core for about 20 minutes, then 3 cores for about 40 minutes a run, on the Mac.

## Result

3 runs, 100 minutes each, three at once on the Mac (one core each). `sweep.py` prints the numbers and writes
`results/sweep.csv`, `results/kinds.csv` and `results/bodies.csv`; the pilot's files are `c1225_life9_pilot_*`.
The world stands 100,000 steps in every run and the ledger drifts by at most 4.8e-14.

| run | kinds at a census | kept to a place | largest line | fruit-led kinds | crown bodies | fruit of what is eaten | browse of it | bodies |
|---|---|---|---|---|---|---|---|---|
| control 9 | 7.45 | 4.75 | 58% | - | - | - | 2.6% | 9,470 |
| control 10 | 8.27 | 4.65 | 63% | - | - | - | 2.9% | 8,902 |
| control 11 | 7.26 | 4.47 | 42% | - | - | - | 2.7% | 9,012 |
| crown 9 | 6.84 | 3.02 | 55% | 0% | 4.3% | 0.95% | 1.4% | 10,578 |
| crown 10 | 6.59 | 2.80 | 62% | 0% | 4.7% | 0.99% | 1.5% | 9,034 |
| crown 11 | 7.29 | 3.33 | 43% | 0% | 2.9% | 1.17% | 1.6% | 7,643 |

**The crowns are lived in.** 220-315 bodies stand in them at any time, 2.9-4.7% of the grown bodies, and they live
on what the crowns hold: fruit is 26-33% of their food, grass 11-15%, kills 38-47%. They are lighter than the
bodies below them (mass 36-37 against 47-50), they carry a tooth far more often (70-81% against 41-47%), and they
end their lives 20-26 cells from where they were born against the floor's 4-7. The ceiling binds at both ends, as
C3 asked: the crown's bodies sit at 72-99% of `hold` x their cell's wood (median 0.91), and the stands they stand
in carry wood 4.2 against the land's 0.36 under a floor body.

**1. More ways of living: no.** Kinds at a census fall on two seeds (6.84, 6.59 against 7.45, 8.27) and hold on the
third (7.29 against 7.26). Kinds kept to a place fall on all three, well under the line: 3.02 / 2.80 / 3.33 against
4.75 / 4.65 / 4.47.

Two thirds of that fall is the measure, not the world. Read again with the crown counted as land (the same censuses,
`medium` 3 mapped to 0), kinds kept to a place come back to 4.02 / 4.06 / 3.88 and kinds at a census do not move
(6.84 / 6.75 / 7.24). A kind keeps to a place when 90% of its bodies stand in one medium (e067's line); a body that
climbs and comes down within its life breaks that for its whole form. The land's kinds are where it shows: they fall
from 21-31% of the grown bodies to 11-16%, and the kinds that keep to no medium rise from 38-42% to 53-54%. The
water's kinds hold (bottom 24-29% against 23-31%, surface 5-8% against 6-8%).

**2. The foods part the kinds: no.** No kind on any seed is led by fruit, on any censuses. The kind that eats the
most of it - a toothed roamer holding 9-16% of the grown bodies - takes 16-20% of its plant matter from the crowns
and is still led by grass (45-61%).

**No birth form keeps to the crown.** Of the forms with 50 grown bodies or more, none stands 90% of its bodies in a
crown, and the most crown-bound (50-68%) hold 0.2-0.5% of the grown bodies between them. The reason is in what the
door is made of: a crown's body is born at mass 44-48 and weighs 36-37 when it is counted, having **lost 9.1 blocks**
(the floor's bodies have lost none). Bodies do not climb because they are born light; they climb because something
broke them, or because their fat is low. `hold` prices a quantity that moves within a life, so it sorts a stage of a
life, not a kind, and nothing it sorts is inherited.

**3. Size follows the food: no kind to compare**, but the places do sort by size: the crown's bodies weigh 0.73-0.77
of the floor's (36-37 against 47-50), which is the 1.3x the done-when asked for, in the wrong unit.

**4. No harm: partly.** The world stands and the ledger holds (4e-14). The largest line is no higher than its
control's (55 / 62 / 43% against 58 / 63 / 42%), and the water's kinds hold their shares. But the land's kinds
halve (above), and seed 11 keeps 15% fewer bodies (7,643 against 9,012) while seeds 9 and 10 keep 3-12% more.

**What the crown did to the food.** The crowns drop 2.01 of the world's matter a step in both worlds (the wood is
the same). In the control all of it is browse on the floor and the bodies eat 78-84% of it. Split, they eat 70-76%:
0.57-0.64 as fruit and 0.84-0.90 as browse. So the world's bodies ate slightly less of the crowns' yield than
before, and the half locked above the floor fed 3-5% of them. The crown is a place, but the food in it was 2.6% of
what the world eats, and half of that is not a living.

**Cost.** The world's update goes from 2.40 to 2.44 ms (+1.7%, one pass over the cells every ten steps for the
crowns that come and go); the bodies' time per body-step is within the noise between two runs (6.5-7.4 us). The
occupancy's third layer is half as much memory again.

## Conclusion

**Not kept.** The three laws each did what they say: the crown is a place, its fruit is a food only reached from
there, and the branch prices mass. Bodies live there. But no kind does, on any seed, so #101's stopping rule is met.

**By that rule P2 ends**, three stage C slots spent (e089, e090, e091). Its own conclusion is narrower than "a plant
food does not make a way of living": e073's browse did make one. What the three say together is that **a new food
feeds a new kind only when what it takes to reach it is something a body is born with**. Seed was parted by a
mouthful (e089) and by a tool half the world already carried (e090); the crown is parted by a mass that damage and
fat move within a life. In every case the eater was a body already there, in a stage or a side of a distribution,
and no form was bound to the food.

For `vision.md`: B's "plants as places" row (a crown holds bodies now, and it is still not a home), F's "ways of
living" row (no plant law since e081 has raised the count), section 4's lessons (the new one above), and section 5
(P2 ends; the next piece is P3 (#52) or what is left of P1).

Two things this leaves for whatever comes next, neither of them tested here:

- **The crown made movers.** Its bodies end 20-26 cells from their birth against the floor's 4-7, in a world where
  "nothing asks a body to go far" has held since e049. It is the first place in this world that a body crosses.
- **A door on a birth trait.** The same three laws with a ceiling on a body's *birth* mass (or on a part it is born
  with, as #52 would give it) would test the sentence above directly, and cheaply: the crate is built.
