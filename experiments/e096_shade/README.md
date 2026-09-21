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

**The ladder (the cheapest layer first).** Seed 9, 40,000 steps, against the control's row at 40,000.
`shade` at e093's kept rate and at the rate that broke it (0.032 made a mat of the world - if the shade
has the middle it is built for, it holds that rate), and the shade alone as the e057 read:

    for s in 0.5 1 2 4; do for r in 0.016 0.032; do
      (nohup bash experiments/e096_shade/run.sh c1225 40000 9 s${s}g$r shade=$s light_gain=$r \
        census=1000 census_from=20000 > experiments/e096_shade/results/c1225_life9_s${s}g$r.log 2>&1 < /dev/null &)
    done; done
    for s in 1 2; do
      (nohup bash experiments/e096_shade/run.sh c1225 40000 9 s${s}g0 shade=$s \
        census=1000 census_from=20000 > experiments/e096_shade/results/c1225_life9_s${s}g0.log 2>&1 < /dev/null &)
    done

What is read: `blocks_cell` (blocks over a cell that carries any), `shaded` (the share of its light they
take), `grass_under` and `grass_free` (the grass standing on the land they stand on and on the land they
leave alone), with `per_cell`, `no_room`, `blocked`, `leaf_mean`, `leaf_open`, `light_intake`, `leaf_led`,
`open_mean`, the intake per gut block and the world's plant.

**The batch.** The pair the ladder picks, on seeds 9-14, 100,000 steps, a census every 1,000 steps from
36,000 - the control ladder's own shape - read as a distribution against the control's, with the
categorical done-whens deciding (`foundation.md`, e092).

**Stop early if:**

- `pop` < 500 at 20000

**Cost.** The ladder: 10 runs at once on one core each, about 1 hour 20 minutes on this Mac (2 cores
left free). The batch: 6 runs at once, about 1.5-2 hours. Nothing on the Ubuntu box. The law itself costs
no pass over the bodies - the occupancy already counts the blocks over every cell - and one pass over the
cells per producers' update, which is already a pass over the cells.

## Result

(to come)

## Conclusion

(to come)
