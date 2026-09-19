# e089: seed behind a tooth, fiber digested over time (#99 S + Fb, stage C)

Date: 2026-09-20

## Purpose

P2 (#99, `vision.md` section 5) asks whether more kinds of plant matter, each needing its own mouth or gut, make
more ways of living. e088 put seed on the producers' side: at `seed_share` 0.2 a steady bank of 0.43 of the grass,
more than the leaf in the winter at 50 degrees. This step adds the bodies' side of both laws (the cycle design is in
#99 and not repeated here):

- **S, seed behind a tooth.** A gut on land takes seed only in a body with a hard tip of force `seed_hard` (2)
  behind it; it takes the grass, the seed and the carrion of its cell in their proportions (and the browse with a
  tooth of 3, as today). A body that can take seed sees it as food.
- **Fb, fiber digested over time.** Each food has a fiber share: grass, browse and wood 0.6, algae 0.3, the
  bottom's litter 0.5, seed, flesh and carrion 0. What a gut takes, less its fiber, is energy at once. The fiber
  joins the body's gut store, which gives `ferment` (0.02) of itself as energy every step and passes `pass` (0.02)
  of itself as dung every turn: litter on the body's cell (in the water, on the bottom). A body taking a turn
  every step digests half its fiber, one at today's median land pace (0.59) 63%, one at 0.1 91%.

## Hypothesis

#99's done-when, on seeds 9-11 at 100,000 steps against e081's control ladder (`c1225_life{9,10,11}_u0`):

1. **More ways of living.** Kinds at a census over each seed's control by 1 or more (controls 7.45 / 8.27 / 7.25),
   and kinds kept to a place not below them (4.75 / 4.65 / 4.47).
2. **The foods part the kinds.** At a census a seed-led kind and a grass-led kind (the food that gives it the most
   of its plant matter) each hold 5% or more of the grown bodies, on every seed.
3. **Size follows the food.** Grass-led kinds weigh 1.3 times the seed-led ones or more (median mass).
4. **No harm.** The world stands 100,000 steps; the ledger holds; the largest line holds no more than its
   control's share.

S alone (seed 9) names what Fb adds.

**Wrong if** the world loses half its bodies with no new kind (as e028's digestion did), every body grows slow and
the spread of sizes does not rise, or no body takes seed.

## Method

e088's crate with the bodies' side (`main.rs`: `seed_hard`, `ferment`, `pass`; `plants.rs`: `take_with_seed`).
With `seed_share` and `ferment` 0 a 2,000-step run on seed 9 reproduces e081's control log (timing aside). The
ledger counts the fiber in the guts; a dead body's fiber lies as litter. Tests: matter is conserved with seed and
fiber on (well over the planned rates), and a unit test of the digested share against the pace.

Measures, no law: the log gains `seed_intake`, `fiber_in`, `fermented`, `dung` (a step, in a body's units) and
`fiber_bodies`; `agents.csv` gains each body's lifetime `seed`, `fermented` and `dunged`. A body's grass is its
land plant intake less its seed and wood.

**Runs** (the default world at `seed_share` 0.2, the settled world e088 built; a census every 1,000 steps from
36,000, as the controls): S+Fb (`ferment` 0.02, `pass` 0.02) on seeds 9, 10, 11 and S alone on seed 9, 100,000
steps.

    (nohup bash experiments/e089_fiber/batch.sh > experiments/e089_fiber/results/batch.log 2>&1 < /dev/null &)

4 runs on 4 cores of the Mac, one thread each, about 50 minutes.

## Result

4 runs, 38-49 minutes each on one core (22-37 ms a step). `sweep.py` prints the numbers below and writes
`results/sweep.csv` and `results/kinds.csv`.

**The check.** With both laws off, e089 reproduces e081's control log at steps 1,000 and 2,000 (timing aside). The
ledger drifts by at most 4e-14 in every run. The world stands 100,000 steps in every run (7,600-9,800 bodies in the
second half; controls 8,900-9,500).

| run | kinds at a census | kept to a place | largest line | seed-led kinds | grass-led mass | land pace | seed in the world's intake | fiber digested |
|---|---|---|---|---|---|---|---|---|
| control 9 | 7.45 | 4.75 | 58% | - | 50 | 0.56 | - | - |
| control 10 | 8.27 | 4.65 | 63% | - | 44 | 0.59 | - | - |
| control 11 | 7.25 | 4.47 | 42% | - | 43 | 0.61 | - | - |
| S 9 | 6.29 | 2.55 | 75% | 0% | 46 | 0.58 | 3% | - |
| S+Fb 9 | 6.96 | 4.80 | 75% | 0% | 57 | 0.53 | 3% | 53% |
| S+Fb 10 | 6.20 | 4.27 | 48% | 0% | 56 | 0.53 | 3% | 54% |
| S+Fb 11 | 7.39 | 4.69 | 53% | 0% | 52 | 0.55 | 3% | 54% |

(Grass-led mass and land pace: the median over the grown bodies of kinds led by grass and held at a census.)

**1. More ways of living: no.** Kinds at a census fall on seeds 9 and 10 (-0.49, -2.08) and rise by 0.14 on 11.
Kinds kept to a place hold on 9 and 11 and fall on 10 (4.27 against 4.65).

**2. The foods part the kinds: no.** No kind on any seed is led by seed. Seed is 3% of what the world's bodies eat.
It goes to the toothed land kinds, which are the hunters and mixed eaters of the control: in them seed is 17-28%
of the plant matter, beside grass 43-67% and kills 34-46%. A gut takes the grass, the seed and the carrion of its
cell in their proportions, so a body that can take seed takes it only as a share of what lies with the grass.

**3. Size follows the food: not testable** (no seed-led kind). What moved is the grass eaters: under Fb the
grass-led kinds weigh 52-57 against the controls' 43-50 (+14-27%) and turn slower (pace 0.53-0.55 against
0.56-0.61). S alone does not do this (46 on seed 9). The bodies digest 53-54% of the fiber they take in, less than
the 63% expected at the median land pace, because the water's bodies, faster, take in much of it (algae, litter).

**4. No harm: no.** The largest line holds 75% of the land's bodies on seed 9 (control 58%) and 53% on 11 (42%);
48% on 10 (63%). S alone on seed 9 is the worst run: kinds 6.29, kept to a place 2.55, the largest line 75%.
What eats changes a little: the bottom's litter rises from 23-25% of the world's intake to 26-27% (the dung sinks
to it) and carrion falls from 15-17% to 11-12%.

## Conclusion

No. Seed behind a tooth and fiber digested over time do not make more ways of living: no body lives on seed,
kinds at a census fall on two seeds of three, and the largest line grows on two. The hypothesis fails at its
first step: seed never becomes the food of a kind, because the tooth that opens it is the hunter's, and a gut
takes seed only mixed with the grass around it. The lesson of e075 holds from the other side: a food is its
mouthful, and a seed that comes in the same mouthful as the grass is not a food of its own.

One part of the design showed: fiber digested over time makes the grass eaters heavier and slower (+14-27% in
mass), as Jarman-Bell says, with no rule about size. It did not open a new way of living by itself.

Under these conditions (c1225, `seed_share` 0.2, a gut that takes a cell's foods in their proportions, fiber
0.6 in grass, ferment and pass 0.02), S and Fb are not kept. This is the first of #99's three stage C
experiments.

`vision.md` rows changed: B (seed exists but is not a food of its own), C size (fiber makes grass eaters heavier),
F (kinds do not rise), and section 4 (a food shared in one mouthful with another does not part the kinds).
