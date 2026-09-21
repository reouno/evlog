# e096: the shade, and the light as one flux (#108, P3 step 3)

Date: 2026-09-21

## Purpose

P3's last candidate (`vision.md` section 5), and the only law in sight that makes **one body's income
fall when another arrives**. Twelve laws in a row have been absorbed since e075: P2's foods and places
were eaten by the bodies already there (e089-e091), and P3's shape-materials built bodies and no ways of
living (e093, e095). The numbers the six seeds agree on are the crowd's - 46-49% of births find no room,
44-51% of moves are blocked (e092) - and a gut block's income is pinned wherever it lives (e038, e057,
e087). Nothing we have added changes who the income falls to when bodies stand together.

e093's own wrong-if says how to change it. Its leaf block's income per face was granted to every face
standing over a cell, so the law **had no middle**: at `light_gain` 0.008 a face earned under a block's
upkeep, at 0.032 the world was a mat of 11-block bodies with half the ways of living. A flux the bodies
on a cell **share** has a middle by construction.

## Hypothesis

With the cell's light one flux, at a rate near a gut block's income:

1. **the crowd thins** - bodies a cell, births with no room and moves blocked all fall below the control
   ladder's distribution. The law is density-dependent by construction, so if this does not move, the
   mechanism does not work;
2. a light-led kind (half or more of its life's matter from the light) holds 5% of the grown bodies on
   most seeds, in a birth form that keeps to it - and where it stands, land or water, is recorded, not
   assumed (every shape law so far has ended in the water, e093 and e095);
3. kinds at a census and ways at 5% in the mean rise over the control ladder's distribution;
4. the world stands, the ledger holds, the largest line is no higher, and the grass is not driven out of
   the cells these bodies stand on.

## The law, as one set

Two laws, both off at 0, where the world is e092's bit for bit.

**The leaf (`light_gain`, e093 as built).** A soft block of a muscle's mass and upkeep; each step it
takes `light_gain` x (its faces open to the air) x (the light it reads) out of its cell's soil. Not kept
on its own (e093); it is what the shade acts on, and it is re-laddered here because sharing the flux
changes what a face earns.

**The shade (`shade`).** A cell's light stops being granted to everything standing over it and becomes
one flux, split where it falls. With `n` the blocks of bodies standing over the cell (every block of
every body, in every layer, counted once - a body is opaque, and a cell is one column of light):

- a block's shadow covers `shade` of the SUB^2 = 16 sub-cells a cell holds, so the bodies darken
  `min(1, shade * n / 16)` of the cell's light;
- **the ground gets what is left**: the grass and the algae of that cell grow at `1 - that` of their
  rate. Nothing is taken from the ledger - the light lost is lost, as a dry cell's and a bare cell's is.
  The wood is not shaded: a stand is taller than a body, and its own shade already falls on the grass;
- **the bodies divide exactly what they darkened**: a block reads `min(shade, 16 / n)` of the light of a
  block's own footprint. At `shade` 1 a block alone on its cell reads e093's whole grant, and a cell
  carrying twice the blocks its face holds halves it. A second body cuts the first; a big body shades
  itself.

The two add up to the cell's light, which a unit test checks.

The cycle. **What it takes**: the light on a cell, which today the grass takes all of, and through it the
soil that grass would have become. Nothing new is made: a leaf block still takes its matter out of its
cell's soil. **What refills it**: the sun, every step; the soil, from the dead, the dung and the litter.
**What limits it**: (a) a body standing on a cell starves the grass under it, and grass is what the guts
eat, so a light-eating crowd eats its own pasture; (b) a leaf block's income falls as 1/n, so no mat can
form - the middle e093 lacked; (c) an open face still pays in water (e067) and heat (e072) and is what a
tooth breaks (e075); (d) a leaf block is not a gut, at a gut's upkeep. **The balance it should settle
into**: spread, still, gut-poor bodies where the sun is good and the grass thin, standing apart from each
other because standing together halves them both; packed grazers where the grass is rich, moving off each
other's shade; and bodies per cell falling where the light-eaters win - the opposite of e093, where they
stood twice as thick as the world.

**Wrong if** the world's plant and its bodies fall in the same proportion while the intake per gut block
does not move: then the law is a subtraction, not a law about who gets the flux - e057's fouling again,
which bought 10% fewer bodies, 12.5% less plant, an unmoved income and no kind. The ladder runs the
shade alone (`light_gain` 0) to read that fingerprint directly.

## Method

**The control costs nothing.** With `shade` 0 and `light_gain` 0 the world is e092's bit for bit (the
leaf's column is drawn from a stream of its own, e059; the shade's arithmetic is skipped), checked by
running e093's crate and this one on the same arguments and diffing every output. The control is the
six-seed ladder as it stands (`foundation.md`): `e081_drink/results/ladder/c1225_life{9,10,11}_u0` and
`e092_yardstick/results/ladder/c1225_life{12,13,14}_ctl`.

**Tests.** Matter is conserved over 3,000 steps with every law of stage C on at once, the shade among
them at `shade` 4 and the light at `light_gain` 0.02. A unit test checks the flux itself: what the blocks
take plus what the ground gets is the cell's light, at every rate and every crowd; half a cell's light
shaded grows half its grass and half its algae; and one body's leaf blocks take exactly
`light_gain` x faces x light x its share, with the sharing binding where the body stands on its own
blocks. e093's own test (the grant with the shade off) still passes unchanged.

**No stage A or B run.** Neither the environment nor the producers change; only who takes the light.

**The ladder (the cheapest layer first).** Seed 9, 40,000 steps, against the control's row at 40,000,
with the control re-run by this crate so the shade's own columns have a control row. `shade` sets two
things at once: where a block's income starts to fall with the crowd (past `16 / shade` blocks on a
cell) and, because a block's shadow covers `shade` of its own footprint, what it earns where the cell
is nearly empty (`shade` x `light_gain`). So the ladder holds the second fixed at e093's kept rate to
read the sharing on its own - (1, 0.016), (2, 0.008), (4, 0.004) - and runs the shade alone
(`light_gain` 0, `shade` 1 and 2) as the e057 read: a subtraction with nobody to take what it took.
Three rungs hold `light_gain` instead - (2, 0.016), (4, 0.016), (1, 0.032) - to ask whether the
sharing holds a rate that made a mat of e093's world.

    for pair in 0:0 1:0 2:0 1:0.016 2:0.008 4:0.004 2:0.016 4:0.016 1:0.032; do
      s=${pair%%:*}; r=${pair##*:}
      (nohup bash experiments/e096_shade/run.sh c1225 40000 9 s${s}g$r shade=$s light_gain=$r \
        census=1000 census_from=20000 > experiments/e096_shade/results/c1225_life9_s${s}g$r.log 2>&1 < /dev/null &)
    done

What is read: `blocks_cell` (blocks over a cell that carries any), `shaded` (the share of its light
they take), `grass_under` and `grass_free` (the grass standing on the land they stand on and on the
land they leave alone), with `per_cell`, `no_room`, `blocked`, `leaf_mean`, `leaf_open`,
`light_intake`, `leaf_led`, `open_mean`, the intake per gut block and the world's plant
(`ladder.py`), and the ways of living of each run from its own censuses (`sweep.py --ladder`).

**The batch.** The pair the ladder picks, on seeds 9-14, 100,000 steps, a census every 1,000 steps from
36,000 - the control ladder's own shape - read as a distribution against the control's, with the
categorical done-whens deciding (`foundation.md`, e092).

**Stop early if:**

- `pop` < 500 at 20000

**Cost.** The ladder: 9 runs at once on one core each, 20-90 minutes each on this Mac (3 cores left
free). The batch: 6 runs at once, about 1.5-2 hours - not run, by the track's own stopping rule
below. Nothing on the Ubuntu box. The law itself costs
no pass over the bodies - the occupancy already counts the blocks over every cell - and one pass over the
cells per producers' update, which is already a pass over the cells.

## Result

Every run's ledger holds (at most 4.8e-14) and a step costs 24-38 ms against the control's 30 with
all nine running at once: the shade is free, as designed (no pass over the bodies).

**The ladder** (seed 9, 40,000 steps; `s<shade>g<light_gain>`; the control re-run by this crate,
which reproduced e081's seed-9 run to the body). The mat rungs were stopped once they had answered,
so their step is given.

| | ctl | s1 g0 | s2 g0 | s1 g0.016 | s2 g0.008 | s4 g0.004 | s2 g0.016 | s4 g0.016 | s1 g0.032 |
|---|---|---|---|---|---|---|---|---|---|
| step | 40,000 | 40,000 | 40,000 | 40,000 | 40,000 | 40,000 | 26,000 | 22,000 | 21,000 |
| bodies | 10,253 | 7,776 | 8,080 | 8,933 | 7,843 | 7,977 | 31,624 | 38,785 | 44,244 |
| blocks a body | 27.6 | 28.8 | 28.5 | 27.3 | 28.8 | 25.1 | 14.3 | 10.8 | 11.1 |
| leaf blocks a body | 0 | 0 | 0 | 1.44 | 1.26 | 0.67 | 5.69 | 3.97 | 3.95 |
| light's share of intake | 0% | 0% | 0% | 6.4% | 4.2% | 1.1% | 73.3% | 77.9% | 76.5% |
| grown bodies led by light | 0% | 0% | 0% | 15.4% | 12.8% | 1.7% | 78.0% | 78.0% | 71.3% |
| **of its light they take** | 0% | 54.0% | 76.7% | 54.9% | 77.0% | 90.5% | 82.1% | 90.5% | 60.7% |
| **blocks over such a cell** | 9.1 | 9.0 | 8.8 | 9.1 | 8.9 | 8.7 | 10.1 | 8.5 | 10.5 |
| bodies a cell held | 1.06 | 1.05 | 1.04 | 1.06 | 1.05 | 1.04 | 1.46 | 1.43 | 1.80 |
| **intake a gut block** | 0.0035 | 0.0035 | 0.0034 | 0.0034 | 0.0036 | 0.0037 | 0.0024 | 0.0027 | 0.0023 |
| births with no room | 50.3% | 47.9% | 47.3% | 46.0% | 47.8% | 48.8% | 51.7% | 35.0% | 47.1% |
| moves blocked | 52.6% | 49.5% | 49.9% | 48.8% | 49.3% | 53.0% | 69.2% | 51.1% | 63.8% |
| plant the world eats a step | 597 | 488 | 472 | 481 | 453 | 470 | 373 | 339 | 404 |
| grass where they stand | 0.141 | 0.118 | 0.129 | 0.127 | 0.116 | 0.134 | 0.085 | 0.078 | 0.093 |
| grass where they do not | 0.202 | 0.186 | 0.212 | 0.170 | 0.189 | 0.223 | 0.187 | 0.203 | 0.213 |

The ways of living of the same runs, read off their own censuses (`sweep.py --ladder`; 21 censuses
from 20,000 to 40,000, the stopped runs 1-9; `analysis/audit.py` found the unfinished last census of each stopped
run - the process was killed while writing it - and those three censuses were dropped before this was read):

| | ctl | s1 g0 | s2 g0 | s1 g0.016 | s2 g0.008 | s4 g0.004 | s2 g0.016 | s4 g0.016 | s1 g0.032 |
|---|---|---|---|---|---|---|---|---|---|
| kinds at a census | 8.14 | 7.43 | 7.52 | 7.24 | 5.86 | 6.81 | 3.44 | 3.00 | 5.00 |
| kinds kept to a place | 4.95 | 3.81 | 4.14 | 4.00 | 3.48 | 3.81 | 2.44 | 1.71 | 3.00 |
| kinds led by the light | 0 | 0 | 0 | 1 | 1 | 0 | 2 | 3 | 3 |
| grown bodies in them | 0% | 0% | 0% | 7.7% | 5.6% | 0% | 67.9% | 74.6% | 66.7% |
| of those, in the water | - | - | - | 99.0% | 98.9% | - | 96.9% | 63.7% | 91.6% |
| bodies a cell, where they stand | - | - | - | 1.64 | 1.85 | - | 3.30 | 1.54 | 1.52 |
| censuses read | 21 | 21 | 21 | 21 | 21 | 21 | 9 | 7 | 1 |

**The law engaged and the crowd did not move.** The bodies take 54-91% of the light of every cell
they stand on, and the grass under them falls with it (0.116-0.134 against 0.170-0.223 where they do
not stand). The world loses 13-24% of its bodies and 19-24% of the plant it eats. But **the intake
per gut block does not move** (0.0034-0.0037 against 0.0035), and neither do the numbers the crowd is
read by: births with no room 46.0-48.8% against 50.3%, moves blocked 48.8-53.0% against 52.6%, bodies
a cell 1.04-1.06 against 1.06. That is e057's fingerprint, declared in advance as this track's
stopping rule, and **the shade alone moves those numbers as far as the pair does**: whatever thinning
there is comes from the subtraction, not from the transfer.

**Why the density term never engaged.** The blocks standing over a cell that carries any are
**8.5-10.5 in every run** - the control's 9.1, the shade alone's 8.8-9.0, and the mat's 8.5-10.5 at
four times the world's bodies. A cell holds 16 sub-cells, so the cells bodies stand on are 53-66%
full of blocks, everywhere, always. The law's own term is that count: at `shade` 2 a block's share of
its cell's flux is `min(2, 16 / n)`, which over the whole ladder's range of `n` varies by a fifth.
The second body never halved the first's income, because the crowd does not answer a lost income by
standing thicker: it stands on other cells, or it is not born. The jam is 46-50% of births failing in
cells that are half empty - a packing of rigid grids, not a density.

**The light is a food, and it feeds the same kind it fed in e093.** A light-led kind holding 5% of
the grown bodies appears on this seed at (1, 0.016) - 7.7% - and at (2, 0.008) - 5.6% - and 99% of
those bodies live in the water, as e093's and e095's did. Where they stand they are 1.6-1.9 bodies a
cell against the world's 1.05: sharing the flux did not make them stand apart. Kinds do not rise on
this seed at any rung (5.86-7.24 against 8.14).

**The mat is not held either.** At a sparse income of 0.032 - e093's breaking rate, reached at (1,
0.032), (2, 0.016) and (4, 0.016) - the world becomes what e093 became: bodies of 11-14 blocks, three
quarters of them led by the light, kinds down to 3.0-5.0 and the largest kind at 43-63%. Sharing does
not stop it for the same reason: the mat's cells carry 8.5-10.5 blocks like everything else, so a
block in the mat reads nearly the same light as a block alone.

## Conclusion

**Not kept, and the track ends here by its own stopping rule** (the batch was not run, saving about
two hours). The shade is a law about who gets the light, and it does transfer: 54-91% of the light
of an occupied cell now goes to the bodies over it, the grass under them falls by a quarter to a
third, and a light-led kind holds 5-8% of the grown bodies. It is still not a law about the crowd.
The world shrinks by a fifth with its plant, the intake per gut block stands where it stood, and the
jam does not move - e057's result again, from the other side.

The reason is a fact about this world that we had not measured: **the blocks over an occupied cell
are 8.5-10.5 whatever happens**, over a fivefold range of population and every rate of this ladder.
Room here is counted in blocks (e093), and a body that cannot fit spreads to the next cell rather
than stacking, so mean density per cell is a constant of this world and a law priced by it has
nothing to bite on. Nearly half of all births fail in cells that are half empty: the jam is the
packing of rigid grids into contiguous free sub-cells, not a density.

What it changes in `vision.md`: section 2's crowding row (the crowd is not reachable by a
density-priced law, with the number that says why), section 2 C's parts row (the light shared is
still a water kind), section 3 item 4 (what will not thin the crowd, now with the mechanism), and
section 5 (P3 is spent: all three of its steps built bodies and none built a way of living or moved
the crowd). The next piece is not another single law but a set that replaces the world, as e072 was:
3D bodies (#5) with a food only a tall body reaches.

