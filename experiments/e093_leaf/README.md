# e093: a block that eats the light (#103, P3 step 1)

Date: 2026-09-20

## Purpose

P3's first piece (`vision.md` section 5). Light is the one material whose worth is set by the shape a
genome develops and by nothing a body can change while it lives: it falls on a body's exposed faces, so
a packed body cannot use it however much of it stands over the cell. That is what P2's law asks for (a
food feeds a new kind only when what it takes to reach it is something a body is born with, e089-e091),
and every counterweight is already in the world: an open face loses water to dry air (e067), passes heat
(e072) and is what a tooth breaks (e075).

It is also the crowd's side. Nearly half of all births fail for want of room and 44-51% of moves are
blocked, in every one of six seeds (e092), and the crowd is a cause, not a consequence (`vision.md`
section 3, item 4). A body that lives by its faces takes more room per unit of income than one that
lives by a gut. Both are judged here.

## Hypothesis

At a rate near a gut block's income, a leaf block pays where the light is good and the crowd is thin,
and it pays best on a body that spreads. Then:

1. a kind whose grown bodies take most of their matter from the light holds 5% of the grown bodies on
   most of the six seeds, and it is a birth form that keeps to it (e091's test: the form, not the body);
2. the light-led kinds are measurably less packed than the world's (open faces per block) - the first
   shapes in this world that are not rectangles (e047);
3. bodies per cell falls where they win, and the share of children with no room and of moves blocked
   falls with it;
4. kinds at a census and kinds kept to a place rise over the control ladder's distribution;
5. the world stands, the ledger holds, the largest line is no higher, and the grass is not driven out of
   the cells these bodies stand on.

## The law

A fifth block kind, `leaf`, soft, of the same mass and upkeep as a muscle or a gut. Each step, every leaf
block takes `light_gain` x (its faces open to the air) x (the light on the cell it stands over) out of
**that cell's soil**, and gets what is there when the soil is short. The light is the sun's height less
the water's depth and the wood's shade - the quantity `vis` damps for the eyes (e072 set E) - read here
undamped.

The cycle: **it takes** matter from the soil, the same store a producer grows out of, so the ledger closes
and the body competes with the grass under it. **What refills it** is the world's cycle as it stands (the
dead, the dung and the litter rot back into the soil). **What limits it**: (a) the cell's soil, which the
grass draws on too; (b) the faces themselves - a face open to the light is open to the dry air, to the cold
and to a tooth; (c) the grid - a leaf block is not a gut, a muscle, a hard block or a sensor, and it pays
the same upkeep; (d) the room a spread body needs to stand at all. **The balance it should settle into**:
in lit, warm, wet places, spread, slow, gut-poor bodies that do not move much and are easy meat, and fewer
bodies per cell there; in dry places, the cold and deep water, packed bodies as today; and a hunter on top
of the spread ones.

**Wrong if** a flat mat wins everywhere (the counterweights do not bind); or nothing grows the block
because its gain is small beside a gut's (the rate is wrong); or the spread bodies win and the crowd does
not thin (then it is a food law, not a crowd law).

Left out of this build, and named so that the next step can take them: bodies do not shade each other or
the cell under them; a leaf block does not need water of its own (heat is already paid in water).

## Method

**The control costs nothing.** The leaf's column in the law table is drawn from a stream of its own, as the
density and the side are (e059), so the four older kinds and the policy keep the columns they always had.
With `light_gain` 0 no cell of any body develops a leaf block and the world is e092's bit for bit, which is
checked by running both crates on the same arguments and diffing the log. So the control is the six-seed
ladder as it stands (`foundation.md`): `e081_drink/results/ladder/c1225_life{9,10,11}_u0` and
`e092_yardstick/results/ladder/c1225_life{12,13,14}_ctl`.

**Tests.** Matter is conserved over 3,000 steps with every law of stage C on at once, the light among them
at `light_gain` 0.02, and leaf blocks develop and feed under it. A unit test checks the gain itself: what
one body's leaf blocks take in a turn is exactly `light_gain` x faces x light, the soil gives only what it
has, and with the light off no body has a leaf block.

**Stage B is not run.** The producers' laws do not change; only who else takes from the soil.

**The ladder (the cheapest layer first).** `light_gain` on seed 9, 40,000 steps, against the control's row
at 40,000. A gut block's realised income is 0.003-0.005 a step (e038) and a block's upkeep is 0.002, so the
band where a leaf block is worth a grid cell at all should lie around them. The first five rates (0.0005 to
0.008) were picked against those numbers with the light read at 1; the sun's height averaged over day and
night is about a quarter of that, so a face at `light_gain` 0.008 earns about a block's own upkeep and no
more, and the ladder was extended to 0.016, 0.032 and 0.064 while the first five ran.

What is read: `leaf_mean` (leaf blocks a body holds), `leaf_open` (their open faces),
`light_intake`, `leaf_led` (grown bodies taking most of their life's matter from the light), `open_mean`
(the shape), `per_cell`, `no_room`, `blocked`, and the grass and soil of the land.

    for r in 0.0005 0.001 0.002 0.004 0.008 0.016 0.032 0.064; do
      (nohup bash experiments/e093_leaf/run.sh c1225 40000 9 g$r light_gain=$r \
        census=1000 census_from=20000 > experiments/e093_leaf/results/c1225_life9_g$r.log 2>&1 < /dev/null &)
    done

**The batch.** The rate the ladder picks, on seeds 9-14, 100,000 steps, a census every 1,000 steps from
36,000 - the control ladder's own shape - read as a distribution against the control's, with the categorical
done-whens (is there a light-led kind, does a form keep to it) deciding (`foundation.md`, e092).

**Stop early if:**

- `pop` < 500 at 20000

**Cost.** The ladder: 8 runs at once on one core each, about 1 hour 20 minutes on this Mac. The batch: 6
runs at once, about 1.5 hours. Nothing on the Ubuntu box.

## Result

Every run stood its 100,000 steps and the ledger drifts by at most 4.5e-14. A step costs 20-32 ms
against the control's 24-39: the light is one pass over a body's leaf blocks and is free.

**The rate ladder** (seed 9, 40,000 steps; the control's own row at 40,000 beside it). `light_gain` is
what a face open to the air earns in full light; the sun's height averaged over day and night is about a
quarter of full, so a face earns about a quarter of the rate.

| light_gain | 0 (ctl) | 0.0005 | 0.001 | 0.002 | 0.004 | 0.008 | 0.016 | 0.032 |
|---|---|---|---|---|---|---|---|---|
| bodies | 10,253 | 7,596 | 9,563 | 9,803 | 9,634 | 10,497 | 11,621 | 50,161 |
| blocks a body | 27.6 | 35.1 | 28.7 | 26.6 | 28.3 | 24.6 | 25.1 | 10.8 |
| leaf blocks | 0 | 0.35 | 0.33 | 0.39 | 0.33 | 0.67 | 0.98 | 3.71 |
| light's share of what is eaten | 0% | 0.0% | 0.1% | 0.1% | 0.2% | 1.3% | **4.8%** | 71.4% |
| grown bodies led by the light | 0% | 0% | 0% | 0% | 0% | 1.1% | **10.4%** | 74.3% |
| bodies a cell held | 1.07 | 1.05 | 1.06 | 1.05 | 1.05 | 1.07 | 1.08 | 2.00 |

Under 0.008 a leaf block earns less than its own upkeep and the blocks that appear are mutations nobody
keeps. At 0.032 the light is the world: bodies of 10.8 blocks, three quarters of them led by the light,
two bodies a cell instead of one, and 66% of moves blocked - and the ways of living collapse, 4.0 kinds
at a census and 3 kept to a place against the control's 7.53 and 4.35. That run was stopped after its
first censuses (21,000 steps): it had answered. **0.016 is the rate the ladder picks** and the batch's.

**The batch** (`light_gain` 0.016, seeds 9-14, 100,000 steps, against the control ladder's six):

| measure | control | light | effect | control spread | light spread |
|---|---|---|---|---|---|
| kinds at a census | 7.53 | 7.02 | -0.51 | 1.02 | 1.57 |
| kinds kept to a place | 4.35 | 3.74 | -0.62 | 1.24 | 1.41 |
| kinds led by the light | 0 | 0 | 0 | 0 | 2 |
| grown bodies in them | 0% | 2.9% | +2.9% | 0% | 15.5% |
| open faces a block, in them | - | 0.69 | - | - | 1.62 |
| open faces a block, all | 0.94 | 1.02 | +0.07 | 0.15 | 0.12 |
| bodies a cell held | 1.04 | 1.05 | +0.01 | 0.02 | 0.04 |
| where the light-led stand | - | 0.88 | - | - | 2.18 |
| the largest line's share | 54.9% | 62.6% | +7.7% | 35.5% | 15.0% |
| kills' share of what is eaten | 27.8% | 30.0% | +2.3% | 4.7% | 7.0% |
| bodies | 8,809 | 8,954 | +146 | 1,611 | 2,549 |
| grass a land cell | 0.176 | 0.185 | +0.009 | 0.027 | 0.054 |

Read against the done-whens:

1. **A kind of its own: on three seeds of six.** Seeds 10, 11 and 14 hold light-led kinds at 15.5%, 14.1%
   and 5.9% of their grown bodies; seeds 9, 12 and 13 hold none over the 5% line, though 6-11% of their
   grown bodies are light-led one by one. They are birth forms and they keep to the way, so the
   categorical question is answered - but not on most seeds.
2. **Shape: yes, and it is the first one in this world.** The blocks of the light-led kinds have 1.38-1.62
   faces open to the air each, against 0.94-1.06 for every body of the world and the control's 0.94. Their
   grids are not rectangles: seed 11's leading kind is a hollow frame of leaf blocks round an empty
   middle on a grid of side 7, its guts along one edge and its muscle down another; seed 13's is a bar one
   to two blocks wide down the left of a grid of side 9, two faces open per block. The world's own packing barely moves (0.94 -> 1.02, inside both spreads).
3. **The crowd: no, and the other way.** Bodies a cell is 1.05 against 1.04, and where the light-led kinds
   stand it is **1.76-2.18** - they pack a cell tighter than the world does. Births with no room 46.9%
   against 46.8%, moves blocked 46.7% against 47.2%: nothing moved.
4. **Ways of living: no.** Kinds at a census fall 0.51 and kinds kept to a place 0.62, both inside the
   control's own spread (1.02, 1.24) and inside this batch's (1.57, 1.41).
5. **No harm: yes.** The world stands, the ledger holds, the grass on a land cell is 0.185 against 0.176
   (the light-led bodies do not drive it out), the largest line 62.6% against 54.9%, inside a control
   spread of 35.5%.

**Where the light-led kinds live: in the water.** Every one of them stands 97-99% in one water layer, at
the surface or on the bottom, and none of them on land. They travel 0-1.75 cells in a grown life (the
world's median is 4.2). On land an open face is a water bill - the dry air takes `dry` per face per turn
(e067) - and in the water a face costs nothing and gives breath back. So the counterweights did bind, and
they bound so hard that the light is a water food.

## Conclusion

**Not kept.** The law makes a kind on three seeds of six, not on most; it does not raise the ways of
living; and it does not thin the crowd. Its two done-whens that hold are the shape (the first bodies in
this world that are not rectangles, on the seeds that have a light-led kind) and no harm.

What it changes for the project:

- **A face is not room.** The piece was ranked first because a body living by its exposed faces should take
  more room per unit of income and so thin the crowd (`vision.md` section 3, item 4; section 5). It does
  not, and the reason is in the world's own bookkeeping: a block claims one sub-cell whatever the shape
  around it, so spreading buys faces without buying room. Where the light-led kinds win, the crowd is
  **twice** as thick, because they are small, they sit, and their income does not need a cell of grass.
  The crowd will be thinned by something that takes room, not by something that takes light.
- **A material whose worth is set by shape does part kinds - where its counterweights leave it a place.**
  P2's law (`vision.md` section 4) survives and sharpens: a food feeds a new kind when what it takes to
  reach it is something a body is born with, *and* when the place where that thing pays is a place. Here
  the thing is the open face and the place is the water, because on land an open face is a water bill.
  This is the first time a kind was parted by the shape a genome develops rather than by what it holds.
- **The rate is a knife edge.** Between 0.008 (a leaf block earns under its upkeep and nobody keeps one)
  and 0.032 (the world is a mat of 11-block bodies and the ways of living halve) there is one step of the
  ladder. A law whose income does not fall as the crowd grows has no middle: 0.016 works only because the
  income per face happens to sit near a gut block's.
- `vision.md`: section 2 C (parts) keeps its large gap, with the light read as a part whose worth depends
  on shape that parts kinds in the water only; section 2 F (crowding) is unchanged at 46-49%; section 3
  item 4 gains the reason a face is not room; section 4 gains the two lessons above; section 5 records P3
  step 1 as spent.

Open, for whoever takes P3 further: bodies that shade each other and the cell under them (left out here)
would make the light a per-cell flux the bodies on it share, which is the form of the law that could thin
a crowd - each body's income falling as its neighbours arrive. That is the one change that answers the
"wrong if" this run hit.
