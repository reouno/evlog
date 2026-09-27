# e106: bodies (#116 rung 3)

Date: 2026-09-27 (started)

## Purpose

Rungs 1-2 made the ground and producers that diversify and hold by place but never turn over (e105): nothing in the
world moves enough to overturn the best form of a place. Rung 3 puts bodies on it - the consumers the vision is
about, and the moving pressure rung 2 lacks. The design is agreed in #117 (v2): every body is an individual; distances
and speeds are real (a cell is ~63 km, an update 3.2 hours); a body's matter counts for `s` animals in the cell's
ledger; a form is an 8x8x8 grid of tissues from the shared genome, with a separate, continuous size.

The rung is built in three steps in this crate and judged whole after the run:

1. **Bodies that grow, eat producers and move** (#122): form and tissues, eating and digesting with keys, water,
   heat, growth, breeding, death, moving on the ground and in the water, a one-layer controller, the ledgers.
2. **Bodies meet**: encounters and contact (press, strain, glue, breath, venom), flesh and carrion.
3. **Strata and the mind**: soil and canopy, hidden units and plasticity.

## Hypothesis

For the run (c1225, bodies sown in year 50, 300 years after, two life seeds; lines fixed before the run, #117):

1. **Ledgers** close (water, A, B, the living's matter) to 1e-9.
2. **The world stands**: bodies in >= 10% of the land's cells in each of the last 50 years; producers hold >= 50% of
   the land; neither's biomass drifts > 1% a year.
3. **Bodies move the world**: they eat >= 10% of what the land's producers fix, and producers turn over (the
   biomass's median birth year after the run's midpoint; e105's H4, failed there).
4. **The freedoms are used**: adult masses span >= 100x (p10-p90 by matter); >= 2 strata each hold >= 5% of the
   bodies' matter; flesh >= 10% of what bodies eat; plastic weights in >= 20% of the matter; a group whose bodies
   travel >= 10 cells a year.
5. **Ways of living**: >= 5 effective groups of bodies by the open measure (#119), held by place (NMI >= 0.2).

## Method

`base/` copied; `src/body.rs` is new, `main.rs` sows the bodies and adds them to the ledgers, the log and a census
(`_bodies.csv`, a row a body genotype a year).

    cargo run --release -p e106_bodies -- <prefix> base/worlds/c1225.params [key=value ...]

**How a body lives** (an update, 3.2 hours): its heat goes towards the balance of its upkeep against what its open
skin loses (less through fat), at a pace set by its mass, and water carries away what is over its range; it senses
its cell and, when near an edge, the next; a linear map from 20 readings gives its direction, activity and whether
it breeds; it reaches leaves and seeds below its height, wood, litter and the seed bank (in water: the floating
producers if it floats, the bottom's litter if it sinks), bites what its mouth's pressure breaks, takes what its
food evaluator accepts up to its gut's rate, and keeps the soft part and as much of the tough part as its gut's share
holds; compounds harm it by their keys' distance from its detox keys; it drinks from wet ground and pools, loses
water through soft skin, and in water breathes through soft skin; it pays upkeep by the B in its tissue and work by
its path; it grows towards its adult mass from its fat with A and B at its tissue's shares, lays eggs from its fat,
and dies of hunger, thirst, heat, cold, breath, poison, or age (its frame's toughness sets its lifespan). Moving:
propulsion from the legs against friction and the ground's roughness over its height on land, from all muscle
against drag in water; climbing is paid.

**Set in step 1's trials, by their units** (a 128-cell world, `results/` not kept): leaves hang from the ground to a
stand's height, so a short body reaches its share of them (it reached none); `bite_ref` 5e3 Pa (1e5 left the default
body no leaf); with no genes a body accepts all food and breeds when it can (random evaluators refused all food); a
body's heat has inertia (the land's noon reaches 55-62 C and small bodies cooked); frost takes 0.2% of the tissue an
update a degree under -2 C; the first bodies' A and B come from the whole world's soil. Results are the same on 1 and
2 threads.

**Set by the first 512 pilot** (Ubuntu, years 50-60, stopped at 1,430 s a year): at `big_s` 3e7 kg the bodies grew
from 22,000 to 9.3 million in seven years and stripped the land - its biomass fell from 0.80 to 0.31 kg a m2 and the
producers' fixing halved - before they fell back (3.4 million at year 60). A body then stood for S/11 on average (most
were young), and the land fed ~0.02 kg a m2 of them. For 3-5 x 10^4 bodies, `big_s` 3e9 and `bodies0` 2,000
(20,000 would start above what the land feeds). What it cost: 2 us a body an update on one thread.

**The second 512 pilot** (years 50-67) sowed only 350 bodies (the rest would have taken more than a tenth of the
world's A), one a genotype, and they died out by year 64; it also found a ledger fault (A and B taken for bodies
that were then not sown, 3e-4). So what a sown body stands for is its own number (`sow_s` 3e7 kg, 20,000 bodies), and
a clutch makes as many bodies as would each weigh `big_s` grown (at least one, at most `clutch_max`): the number of
bodies follows the matter the food holds, over S, whatever the start.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 23760
- `bodies` < 100 at 712800
- `ms_step` > 10 at 712800

## Result

Step 1 pilot: to come.

## Conclusion

To come.
