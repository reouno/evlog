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

`report.html` has the charts. Every run stood its steps and the ledger drifts by at most 3e-14.

### The two ladders (seed 9, 40,000 steps, means over the second half; the control's own row beside them)

The ladders were extended to 8 and to 4 while the first four ran, to find each law's top.

| spike | 0 (ctl) | 0.5 | 1 | 2 | 4 | 8 |
|---|---|---|---|---|---|---|
| flesh taken through a spike | 0% | 1.0% | 1.8% | **2.0%** | 1.1% | 0.8% |
| blocks broken by a spike | 0% | 0.5% | 1.0% | 1.1% | 0.6% | 0.4% |
| grown bodies carrying a spike | - | 10.0% | 11.6% | 9.7% | 11.3% | 14.7% |
| kills' share of what is eaten | 44.6% | 42.8% | 43.5% | 42.5% | 42.0% | 42.5% |
| hard blocks a body | 3.31 | 3.16 | 2.87 | 2.78 | 2.53 | 3.81 |

| leg | 0 (ctl) | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| leg blocks a body | 0 | 0.46 | 0.85 | 1.76 | 1.90 | 3.02 |
| their faces open to the air | 0 | 0.45 | 0.86 | 1.93 | 2.00 | 3.14 |
| muscle blocks a body | 7.50 | 7.62 | 7.80 | 8.19 | 6.88 | **4.57** |
| motor (chance a sub-cell) | 0.209 | 0.223 | 0.215 | 0.242 | 0.313 | 0.504 |
| travel in a life (cells) | 4.89 | 4.62 | 5.54 | 5.63 | **6.48** | 4.15 |
| moves blocked | 52.6% | 54.0% | 54.9% | 55.1% | 55.2% | **61.6%** |
| kinds at 5% over the censuses | - | - | - | 10 | 9 | 8 |
| a kind the legs move (5% line) | - | - | - | **6.8%** | none | 5.3% |

**The spike does not depend on its rate.** From 0.5 to 8 - a force counted 1.5 to 9 times over - the flesh
that comes in through a spike stays at 1-2% and the blocks broken through one at 0.4-1.1%, and no kind of
any run takes as much as 2.0% of its flesh that way. Raising the rate raises the *shape* (spikes a grown
body 0.08 to 0.19) and not what it earns. The reason is in the break rule it was built on: a break needs
the pusher's face to be **harder** than the victim's and only then more force than that face resists, and
in this world the prey are soft (a soft face resists 1, a pressing line brings 1-3 muscle). The force was
not what limited a break, so multiplying it bought nothing. The spike multiplies a term that does not bind.

**The leg works, and it has a top between 2 and 4.** The leg blocks a body develops sit almost exactly on
its boundary (1.76 blocks with 1.93 open faces at rate 1): where the law pays, and not scattered. Up to
rate 2 the motor and the travel rise together (0.209 to 0.313, 4.89 to 6.48 cells a life). At rate 4 the
law turns over: legs replace muscle (7.50 to 4.57 blocks), the motor reaches 0.504 - and the travel
**falls below the control's** (4.15) while 61.6% of moves are blocked, because what the legs buy is spent
on a body too spread to place in the jam. Rate 1 is the one that parts a kind (one kind of 6.8% of the
grown bodies whose motor is 54% legs, travelling 15.25 cells against the run's median of 5.5, with 1.33
open faces a block against the world's 0.91) and it keeps the most ways of living (10 kinds at the 5%
line, against 9 at rate 2 and 8 at rate 4). **The batch is the pair at `spike` 2 and `leg` 1.**

### The batch (spike 2 + leg 1, seeds 9-14, 100,000 steps)

Read over 51 censuses every 1,000 steps from 50,000 (`results/provenance.csv`), against the control ladder's
six runs of the same worlds.

| measure | control | the pair | effect | control spread | pair spread |
|---|---|---|---|---|---|
| kinds at a census | 7.53 | 7.29 | -0.24 | 1.02 | 1.04 |
| kinds kept to a place | 4.35 | 4.03 | -0.32 | 1.24 | 1.18 |
| kinds led by the spike | 0 | **0** | 0 | 0 | 0 |
| kinds the legs move | 0 | **0** | 0 | 0 | 0 |
| flesh taken through a spike | 0% | 0.5% | +0.5% | 0% | 2.7% |
| the legs' share of the motor | 0% | 9.2% | +9.2% | 0% | 14.1% |
| leg faces that pull, a body | 0 | 0.87 | +0.87 | 0 | 1.70 |
| spikes a grown body | 0.09 | 0.08 | -0.01 | 0.12 | 0.09 |
| open faces a block | 0.94 | 0.91 | -0.03 | 0.15 | 0.20 |
| bodies a cell held | 1.04 | 1.05 | +0.00 | 0.02 | 0.03 |
| births with no room | 46.8% | 47.2% | +0.3% | 2.7% | 5.9% |
| moves blocked | 47.2% | 48.3% | +1.1% | 6.9% | 11.0% |
| travel of a grown body | 5.2 | 4.8 | -0.5 | 2.0 | 2.5 |
| the largest line's share | 54.9% | 51.3% | -3.6% | 35.5% | 46.5% |
| bodies | 8,809 | 8,471 | -338 | 1,611 | 2,200 |
| grass a land cell | 0.176 | 0.179 | +0.003 | 0.027 | 0.039 |

Read against the done-whens:

1. **A kind of its own: no, for either material, on any seed.** No kind takes most of its flesh through a
   spike (the best is 13% of one kind's flesh, on seed 13), and no kind passes the leg rule - most of its
   motor from its legs *and* twice the run's median travel *and* 5% of the grown bodies. **What does exist
   is the body.** On three seeds of six there are kinds whose motor is 40-60% legs, holding 3.0%, 3.6% and
   4.98% of the grown bodies (seed 13 holds three of them, 12.2% between them); the nearest miss is seed
   13's `plant / no tooth / roams / surface` at 4.98%, its motor 50.3% legs, travelling 22.5 cells.
2. **Shape: yes for the leg, where it is used, and no for the world.** The five leg-built kinds carry 1.29
   open faces a block against 0.90 for the other 63 kinds of the batch, and they travel 17.0 cells against
   4.2. Their legs are on the boundary by construction, and seed 13's bottom kind is a hollow frame of gut
   with a column of legs down its left face. The world's own packing does not move (0.91 against 0.94,
   inside both spreads).
3. **Ways of living: no.** Kinds at a census fall 0.24 and kinds kept to a place 0.32, both well inside the
   control's own spread (1.02, 1.24).
4. **No harm: yes.** Every run stood 100,000 steps, the ledger drifts by at most 3e-14, the grass on a land
   cell is 0.179 against 0.176, and the largest line's 51.3% is under the control's 54.9%.

**Where the leg-built bodies live: in the water.** 90% of the bodies of those five kinds stand in a water
layer, and every one of the five is a plant eater with no tooth that roams. It is e093's finding again from
another law: on land a face open to the air is a water bill (e067), so a body that sticks out lives in the
water, where a face costs nothing and gives breath back.

**Both materials swing and neither settles.** Over seed 13's run the legs a body carries go 1.8 -> 2.3 ->
1.1 -> 2.6 -> 1.8 blocks and the flesh taken through a spike 3.7% -> 17.1% -> 3.2% -> 5.7%; on seed 9 the
legs fall to 0.7 by 50,000 and come back to 2.1 at 90,000. Both are used, by a tenth to a quarter of the
bodies, and neither is ever the thing a kind is built on - e094's flicker, at the level of a material.

## Conclusion

**Not kept, neither law.** Neither parts a kind on any of six seeds, the ways of living do not rise, and the
crowd does not move (it was not asked to). Both rates stay out of the default world. What the piece leaves:

- **A law must multiply the term that binds.** The spike was designed to make a protruding body dangerous,
  and it multiplies the force behind a tip. In this world force is not what limits a break: the rule asks
  first that the pusher's face be harder than the victim's, and the prey are soft, so 1-3 muscle on a line
  is already enough. From `spike` 0.5 to 8 - a force counted 1.5 to 9 times over - what comes in through a
  spike stays at 1-2%. Designing a law as a cycle is not enough; the arithmetic of the mechanism it plugs
  into has to be read first.
- **The leg builds a body but not a way of living.** It is the second material (after e093's light) whose
  worth is set by the shape a genome develops, and the second to build recognisable bodies - open, roaming,
  water plant eaters with a column of legs on one face, 1.29 open faces a block against 0.90. They sit at
  3-5% of the grown bodies on half the seeds and never hold the line. A material can change what a body
  looks like without changing what it lives on, and it is what a body lives on that the kinds are counted by.
- **The third law in a row whose shapes live in the water.** The light (e093), the leg, and the open bodies
  of e066-e067 all end in the water, because on land an open face is a water bill. Any further shape law is
  a water law until something pays for an open face on land.
- **A law with a ceiling has a top, and the top is the jam.** Unlike the light, the leg's income stops
  mattering above a motor of 1, and the ladder found its turnover: at `leg` 4 legs replace muscle, the motor
  reaches 0.504 and the travel falls *below* the control's while 62% of moves are blocked. What a law buys
  can be spent by the crowd.

For `vision.md`: section 2 C (parts) keeps its large gap, with the leg read as a part whose worth depends on
shape that builds bodies and no kinds; section 2 F is unchanged; section 4 gains the two lessons above;
section 5 records P3 step 2 as spent, which leaves the shade (bodies that shade each other and the cell
under them) as P3's one remaining candidate and the only one that could thin the crowd.
