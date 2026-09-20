# e090: a mouthful of its own for the seed (#100 D + B + Fb', stage C)

Date: 2026-09-20

## Purpose

e089 put seed behind a tooth and fiber in the gut and no kind lived on seed: it was 3% of what the bodies eat
and went to the toothed land kinds, which are the control's hunters. The reason was in the laws, not in the
rates: a gut takes a cell's grass, seed and carrion in their proportions, so seed always comes in one mouthful
with the grass, and the hard tip that opens seed is the tooth that opens bodies, so the seed eater and the
hunter are the same body. #100 gives seed a place of its own, a tool of its own and a worth of its own, as one
cycle (the design is in #100 and not repeated here):

- **D, seed drifts with the wind.** Every producers' update a share `seed_drift` of a cell's seed moves one
  cell downwind on the climate's wind (one wind, turning with the season), by the air's own bilinear shift, so
  nothing is made or lost. Seed that lands on water sinks and lies as the bottom's litter. The seed leaves the
  grass that set it and piles up where it cannot sprout: ground too dry, too cold or burnt.
- **B, a beak opens seed.** `seed_hard` 1: a hard tip with any force behind it takes seed, so the seed eater
  is no longer the hunter (the tooth of 2 that breaks a body is not needed).
- **Fb', grass is a poor food for a fast body.** The fiber of grass, browse and wood is 0.8 (e089: 0.6) and
  `ferment` 0.005 a step (0.02), `pass` 0.02 a turn. A body taking a turn every step digests 20% of its fiber
  and gets 0.36 of the grass's matter; at pace 0.5, 47%; at 0.1, 77%. Seed gives all of itself to any body.

## Hypothesis

#99's done-when, on seeds 9-11 at 100,000 steps against e081's control ladder (`c1225_life{9,10,11}_u0`),
with #100's one fix: a kind's leading food is read by **energy**, not by matter (a food's energy is its matter
x (1 - fiber) + fiber x the body's digested share, `fermented / (fermented + dunged + fiber)` from its census
row).

1. **More ways of living.** Kinds at a census over each control by 1 or more (7.45 / 8.27 / 7.25); kinds kept
   to a place not below 4.75 / 4.65 / 4.47.
2. **The foods part the kinds.** A seed-led and a grass-led kind each hold 5% or more of the grown bodies at
   a census, on every seed.
3. **Size follows the food.** Grass-led kinds weigh 1.3 times the seed-led ones or more.
4. **No harm.** The world stands; the ledger holds; the largest line no higher than its control's share.

**Stopping rule** (agreed in #100): if no seed-led kind holds 5% on any seed, P2's seed track ends and the
next piece is chosen from `vision.md`'s gap table.

## Method

e089's crate with the three laws (`plants.rs`: the drift, on `World::wind_to`, the wind the climate just blew;
`main.rs`: `seed_drift`, FIBER_LEAF 0.8). With `seed_share`, `seed_drift` and `ferment` 0 a 2,000-step run on
seed 9 reproduces e081's control log exactly (timing aside). Tests: matter is conserved with the drift on (well
over the rates run), and a unit test of the shift (a quarter of a cell's seed a cell downwind, nothing made or
lost, and what lands on water sinks as litter).

Measures, no law: the log gains `seed_wet` (the seed that sank, a step); `agents.csv` gains `fiber` (the fiber
in a body's gut now), which reads its digested share; `cells.bin` gains the seed on a cell.

**Runs.** Stage B check first (`alone.sh`): the producers alone on c1225, two years after the settled world,
at `seed_drift` 0, 0.01, 0.02, 0.05 and 0.2, with e088's `seed_share` 0.2 - where the seed lands, and whether
stage B still passes (#100 planned two rates; the first pair showed the land draining, so the ladder was run
down to 0.01). Then stage C (`batch.sh`): D+B+Fb' on seeds 9-11, 100,000 steps, a census every 1,000 from
36,000, at the drift the check chose.

    (nohup bash experiments/e090_drift/alone.sh > experiments/e090_drift/results/alone.log 2>&1 < /dev/null &)
    (nohup DRIFT=<rate> bash experiments/e090_drift/batch.sh > experiments/e090_drift/results/batch.log 2>&1 < /dev/null &)

5 cores for about 10 minutes, then 3 cores for about 50 minutes, on the Mac. One field moves a cell an update.

## Result

### The stage B check: the drift rate

5 runs of the producers alone, 1-7 minutes each (the settled world 5.5 of them; `seed_drift` 0 read e089's).
A land cell's means over the two years; `alone.py` prints them and writes `results/alone.csv` and
`results/alone_bands.csv`. "Thin ground" is a cell whose grass is under a tenth of the land's mean: ground too
dry, too cold or too lately burnt for grass.

| drift | grass a cell | seed a cell | seed sunk in the sea | grass / wood / algae of the standing matter | fire a year | seed on thin ground | seed a thin cell |
|---|---|---|---|---|---|---|---|
| 0 (e088) | 1.121 | 0.479 | 0% | 64 / 22 / 14% | 1.0% | 3.1% | 0.08 |
| 0.01 | 0.999 | 0.425 | 5.0% | 64 / 20 / 16% | 1.4% | 6.8% | 0.15 |
| 0.02 | 0.881 | 0.366 | 9.9% | 64 / 19 / 18% | 1.1% | 8.8% | 0.16 |
| 0.05 | 0.602 | 0.225 | 23.7% | 61 / 13 / 26% | 0.9% | 12.3% | 0.13 |
| 0.2 | 0.183 | 0.042 | 60.1% | 39 / 1 / 60% | 0.4% | 20.4% | 0.05 |

**The drift does what it was meant to do, and takes the land with it.** Seed does leave the grass that set it:
the share of the land's seed lying on thin ground rises from 3.1% to 8.8% at 0.02 and 12.3% at 0.05, and a thin
cell's bank doubles (0.08 to 0.16). But the wind also blows it into the sea: 5% of all seed set at 0.01, 10% at
0.02, 24% at 0.05, 60% at 0.2. The sea keeps it (it sinks as the bottom's litter, which rots into the sea's
soil), and nothing carries it back, so the land thins: grass falls to 0.89 / 0.79 / 0.54 / 0.16 of the drift-free
land and wood with it.

**Stage B** (`foundation.md`: each producer 5% of the standing matter, none dies out, fire 1-20% of the land a
year) passes at 0.01 and 0.02, fails at 0.05 on fire (0.9%) and at 0.2 on wood (1.3% of the standing matter,
805 against 59,793). D's own "wrong if" - the land loses its bank - is met from 0.05 on.

**Stage C runs at `seed_drift` 0.02**: the largest rate that passes stage B, and the one where a thin cell's
bank is largest (0.16, twice the drift-free land's), with a fifth of the land holding more seed than grass.

### Stage C: the kinds

3 runs, 35-36 minutes each on one core (15-24 ms a step). `sweep.py` prints the numbers and writes
`results/sweep.csv`, `results/kinds.csv` and `results/bodies.csv`. "Led by" is read by energy (#100): a food's
energy is its matter x (1 - fiber) + fiber x the body's digested share.

| run | kinds at a census | kept to a place | largest line | seed-led kinds | grass-led mass | land pace | seed of what is eaten | bodies (land) |
|---|---|---|---|---|---|---|---|---|
| control 9 | 7.45 | 4.75 | 58% | - | 50 | 0.56 | - | 9,470 (4,060) |
| control 10 | 8.27 | 4.65 | 63% | - | 44 | 0.59 | - | 8,902 (3,653) |
| control 11 | 7.25 | 4.47 | 42% | - | 43 | 0.61 | - | 9,012 (3,693) |
| D+B+Fb' 9 | 7.16 | 5.22 | 64% | 0% | 46 | 0.59 | 4.5% | 8,963 (3,511) |
| D+B+Fb' 10 | 6.76 | 4.06 | 62% | 0% | 44 | 0.59 | 4.4% | 8,255 (3,048) |
| D+B+Fb' 11 | 7.25 | 5.18 | 78% | 0% | 45 | 0.59 | 4.6% | 8,353 (3,282) |

The world stands 100,000 steps in every run and the ledger drifts by at most 4.4e-14.

**1. More ways of living: no.** Kinds at a census fall on seeds 9 and 10 (-0.29, -1.51) and hold on 11. Kinds kept
to a place rise on 9 and 11 (5.22, 5.18 against 4.75, 4.47) and fall on 10 (4.06 against 4.65).

**2. The foods part the kinds: no.** No kind on any seed is led by seed, though seed comes closer than in e089:
it is 4.5% of what the world's bodies eat (e089 3%), and in the largest toothed land kind (10-11% of the grown
bodies on every seed) it is a quarter of the plant matter and **40-42% of the plant energy**, against grass's
51-52%. The kinds that take it are the same toothed land kinds as in e089. The beak did not part the tool: a
tooth of force 2 or more is carried by 26-40% of the grown bodies anyway (controls 18-30%), so every body that
would grow a beak already has the hunter's tooth.

**3. Size follows the food: not testable** (no seed-led kind). Fb' did not repeat e089's heavier grass eater:
the grass-led kinds weigh 44-46 against the controls' 43-50, and turn at 0.59 against 0.57-0.61. At `ferment`
0.005 grass is poor enough that the bodies leave it rather than grow into it.

**4. No harm: no.** The largest line holds 64% of the land's bodies on seed 9 (control 58%) and 78% on 11 (42%);
62% on 10 (63%). Land bodies fall 9-16%. What the world eats moves off the land: the bottom's litter rises from
23-25% to 29-32% (the dung and the sunk seed both land there) and carrion falls from 15-17% to 9-10%.

**The bank the bodies leave.** Grazed, the seed on a land cell is 0.09-0.12 against 0.37 with no bodies, and the
grass 0.23-0.30 against 0.88: the bodies hold both to a third. Of the seed set, 6% still sinks in the sea (10%
with no bodies). The wood the drift already cost stands at 48,500-50,500 against the controls' 67,200.

## Conclusion

No. Seed with a place, a tool and a worth of its own still feeds no kind of its own. Under D+B+Fb' no kind on any
seed is led by seed, kinds at a census do not rise on any seed, and the largest line grows on two of three. By
#100's stopping rule, **P2's seed track ends**.

Two things are worth keeping from the attempt. First, what the drift buys and what it costs are the same law: the
wind that carries seed off the lawn onto ground the grass does not hold (the bank on thin ground doubles at 0.02)
also carries 10% of it into the sea, where the world has no way back to the land, so the rate that would make
seed the larger food empties the land (at 0.05 the grass halves, at 0.2 the wood dies out). Second, raising a
food's worth moves the share, not the kinds: read by energy, seed went from a fifth of the leading land kind's
plant matter (e089) to two fifths of its plant energy, and still did not lead it. A food that is taken in the
same mouthful, by the same body, as another is a share of a diet, not a way of living - even when it is worth
more per gram.

Under these conditions (c1225, `seed_share` 0.2, `seed_drift` 0.02, `seed_hard` 1, fiber 0.8 at `ferment` 0.005,
a gut that takes a cell's foods in their proportions), D, B and Fb' are not kept.

`vision.md` rows changed: B (seed is not a food of its own even with its own place, tool and worth), C size (a
harsher fiber does not make grass eaters heavier), F (kinds do not rise; the largest line grows), G (a law that
moves matter downwind drains the land into the sea), section 4 (two lessons above) and section 5 (P2's seed track
ends; the next piece is chosen from the gap table).
