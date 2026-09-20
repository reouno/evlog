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

(to come)

## Conclusion

(to come)
