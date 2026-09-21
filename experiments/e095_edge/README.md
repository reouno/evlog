# e095: the spike and the leg (#107, P3 step 2)

Date: 2026-09-21

## Purpose

P3's second piece (`vision.md` section 5, issue #107). Two materials that work **only at a body's edge**,
which only a genome sets, built and searched as one set.

e093 put the first shape-material in the world and it half worked: a block that gains by its faces open to
the air parted a kind on three seeds of six and gave this world its first bodies that are not filled
rectangles. Its kinds were all in the water, because on land an open face is a water bill (e067). The
lesson was not "shape does not pay" but "a body that sticks out must be able to afford sticking out
somewhere". On land it cannot afford it yet: a body that sticks out is easy meat (e075) and slow to place
in a jam where 44-51% of moves are blocked (e092).

So the two are built together. **The spike makes a protruding body dangerous to touch and the leg makes it
quick to leave**, and each pays the other's bill. Everything this project has kept since the staged search
began was a set searched together (e072's seven, e073's two, e075's two); every single law since has been
rejected, eleven of them.

**Not a done-when: the crowd.** e093 settled that a law paying per unit of edge cannot thin it - room is
counted in blocks, so spreading buys faces and no room (`vision.md` section 3, item 4). Bodies per cell and
the jam are recorded beside the result, not judged by it.

## The two laws

Both read the same thing - a block's faces with nothing of the body beside them - and both are off at 0,
where the world is e092's bit for bit.

**The spike (`spike`).** A hard block at the front of the line it presses on, with nothing of the body
ahead of it or to either side across that line, concentrates what is behind it: the line's muscle counts
`1 + spike` times over for the break. Everything else is e010/e014/e015 as it stands - the shove is the
whole body's weight, and the spike's own face is as hard as the run of hard blocks behind it and no harder
(HARDNESS 3 a block). A hard block inside a flat armoured face counts as it does today.

- **What it takes**: the flesh of what it breaks - e075's tear, already in the world. Nothing new is made.
- **What refills it**: the bodies the world grows, as today.
- **What limits it**: (a) a break still needs the pusher's face to be *harder* than the victim's, so a
  spike backed by one hard block (3) cannot open armour two deep (6) however sharp it is - to point at
  armour it must be a deep, narrow, heavy column (a hard block is mass 2, the heaviest there is); (b) the
  blocks beside it are gone, so the soft blocks it leaves exposed pay in water (e067) and heat (e072);
  (c) a grid cell that is not a gut, at a gut's upkeep; (d) the prey's armour, which is the same material
  used flat and costs the prey nothing new.
- **The balance it should settle into**: narrow, pointed hunters that carry less muscle for the same
  break, against flat-faced grazers whose answer is depth - and armour deep enough that a spike must be
  deep too, which is heavy.

**The leg (`leg`).** A sixth block kind, soft, of a muscle's mass and upkeep, drawn from a stream of its
own. It adds `leg` to the body's motor for **each of its faces open to the air** and nothing where it is
walled in, and the sum is divided by the mass as the muscle is (e048, e055): `speed = (muscle + leg x
open faces of leg blocks) / mass`. At `leg` 0 that is e048's own number to the bit.

- **What it takes**: nothing new - it changes what the existing move cost buys (e048's work).
- **What refills it**: nothing to refill; it is a trade of grid cells.
- **What limits it**: (a) a leg pulls only on the boundary, so a body with many of them is spread or
  small, and a spread body is blocked more often in the jam; (b) a boundary block is what a tooth breaks
  (e075) and what loses water (e067); (c) a grid cell that is not a gut; (d) mass - the motor still
  divides by what it moves; (e) the motor is a chance per sub-cell, so it is worth nothing over 1: a body
  that already steps every time gains nothing by adding legs (the ceiling e093's light did not have).
- **The balance it should settle into**: fringed movers where the food is patchy or the jam is thick,
  packed sitters where the food is even. The measured pressures they answer are the 44-51% of moves
  blocked and the 9-15 cells to a place fed in a lean month (e086).

**Wrong if** nothing develops the shapes at all. Bodies pack (#52): in a 3,000-step test world only 1-2%
of the bodies carry a spike and none of 313 breaks came through one. The supply is there but thin, which
is the reason the pair is built together and the first thing the ladder reads.

Left out on purpose: a leg does not add to the force that breaks (the muscle behind the line is what
breaks, e010), and a spike is not a new material - it is the hard block the world already has, in a shape.

## Hypothesis

Written before the runs.

1. **A kind of its own, for each material.** A kind whose grown bodies take most of their flesh through a
   spike, and a kind whose grown bodies travel where the rest do not, each holding 5% of the grown bodies
   at a census on most of the six seeds, and each a birth form that keeps to it.
2. **Shape.** Those kinds' bodies are measurably not rectangles - open faces per block over the world's -
   and their spikes and legs sit where the law pays, not scattered.
3. **Ways of living.** Kinds at a census and ways at 5% in the mean rise over the control ladder's
   distribution (e094's measures; never a conjunction over the censuses).
4. **No harm.** The world stands, the ledger holds, the largest line no higher, the grass not driven out.

**What we expect.** (1) is the real question and the honest prior is that the spike is the likelier of the
two: it needs one block in the right place and the flesh is already 27% of what bodies eat, while the leg
must beat a muscle at a job the muscle already does. (2) follows from (1) by construction. (3) is what the
set is for.

## Method

Code: e093's crate (`e093_leaf`) as `e095_edge`, plus the two laws. e093's light stays in it at
`light_gain` 0 (not kept, e093) so that the control is untouched.

**The control costs nothing.** The leg's column in the law table is drawn from a stream of its own, as the
leaf's, the density's and the side's are (e059, e093), and the spike is a law about a shape and has no
column at all. With `spike` and `leg` 0 no cell develops a leg block, no tip counts for more, and the world
is e092's bit for bit - checked by running e093 and e095 on the same arguments and diffing the log. So the
control is the six-seed ladder as it stands (`foundation.md`):
`e081_drink/results/ladder/c1225_life{9,10,11}_u0` and `e092_yardstick/results/ladder/c1225_life{12,13,14}_ctl`.

**Tests.** Matter is conserved over 3,000 steps with every law of stage C on at once, the spike at 4 and
the leg at 2 among them, and leg blocks develop with faces that pull. Two unit tests: what a spike is (a
tip with nothing beside it; the same block inside a flat face is not one) and that the force behind it
counts `1 + spike` times over, with what a gut takes through it counted apart; and what a leg adds (three
open faces at rate 2 over a mass of 3 is a motor of 2, the same block walled in adds nothing and still
weighs).

**Stage A and B are not run**: nothing about the environment or the producers changes.

**The ladders (the cheapest layer first).** One seed (9), 40,000 steps, each law alone, against the
control's row at 40,000. The spike's rates are read against the world's own numbers: a face of soft flesh
resists 1, one hard block 3, two 6, and a pressing line carries 8.4 muscle blocks over a side of 5.9, so a
line brings 1-3. The leg's are read against a muscle: a leg block with two open faces at `leg` 0.5 is worth
one muscle block, at 2 four of them.

    for r in 0.5 1 2 4; do ... spike=$r ... done      # x1.5, x2, x3, x5 on the force behind a tip
    for r in 0.25 0.5 1 2; do ... leg=$r ... done     # per open face, in muscle blocks

What is read: `spike_mean`, `spiked`, `sharp_share`, `sharp_broke` (does the shape appear, and does
anything come in through it), `leg_mean`, `leg_open`, `leg_led`, `speed_mean`, `travel_p50`, `blocked`
(does the leg buy movement), and `open_mean`, `per_cell`, `no_room` beside them.

**The batch.** The pair at the two rates the ladders pick, on seeds 9-14, 100,000 steps, a census every
1,000 steps from 36,000 - the control ladder's own shape - read as a distribution against the control's,
with the categorical done-whens deciding (`foundation.md`, e092, e094).

**Stop early if:**

- `pop` < 500 at 20000

**Cost.** The two ladders: 8 runs at once on one core each, about 1 hour 20 minutes on this Mac. The batch:
6 runs at once, about 1.5 hours. Roughly a core-day in all, nothing on the Ubuntu box.

## Result

(to come)

## Conclusion

(to come)
