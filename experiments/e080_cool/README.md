# e080: a crown that takes its share of the sun (#91 step 3)

Date: 2026-09-19

## Purpose

#91 asks whether a stand of wood is a refuge a lawn cannot hold. e079 built the plants' half of the design
(`balance.md` sections 13-14): wood that rests in the cold puts stands beside the seasonal lawns, and a crown
that keeps its ground wet lifts a mid-latitude stand's summer floor from 0.43 to 0.58, and no further
without taking the land's rain. By e078's budget a body's summer water closes on a floor of 0.58 only if
the crown also halves what the body pays to cool. This step adds that third part, S3, and puts bodies on
e079's world at `crown_wet` 1 and `wood_rest` 0.5 (agreed 2026-09-19).

## The cycle (written before the runs)

- **S3, the crown's share of the sun's heat** (`crown_cool`, c3). What a body's heat reads under a crown is
  lowered by `min(1, c3 x shade) x (T_day - T_dark)`: the day's sun heat on the cell (its running mean over
  a day less what it goes toward with no sun) times the crown's share. It lowers the mean and leaves the
  day's swing (e078's damper did the reverse).
- **What it takes and from whom.** Nothing from the world: it is what a body reads. In summer it takes
  cooling water off a body in a stand; in winter the sun's heat is smaller and so is the cut, but a stand is
  still colder than the lawn beside it, so a body there pays more energy to warm.
- **What limits it.** The winter's warming; the stand's thin browse (3e-5, and the grass under a crown gets
  less light), so with water no longer binding in a stand its food does; the hunters, which already lead the
  stands and follow a crowd.
- **The balance expected at 20-50 degrees.** Spring and autumn: the lawn grows and its water closes, lawn
  lines grow, the stands hold at their browse. Summer: the lawn runs dry as today; a stand's floor (0.58) and
  a cooler mean close a body's water there, so the lawn lines' children fill the stands and the hunters
  follow. Winter: the lawn stops growing; the stand is colder but has browse and a wet floor. The stands fill
  in summer and empty in spring and autumn.
- **What would show it wrong.** The stands hold more bodies a cell than the lawn at the equinoxes (a home,
  not a refuge); a stand's bodies hold under 0.4 of their water in summer; the stands' bodies in summer over
  the equinoxes stay within e078's 0.96-1.04; or the winter's warming empties the stands.

## Hypothesis

At the c3 that brings a mid-latitude stand's bodies to 0.4 of their water in summer, against the same world
at c3 0 (seed 9, both hemispheres, "summer" the hemisphere's own):

1. **The body's water (R2).** The mid stands' land bodies hold 0.4 or more of their water in their summer
   (e078's world: 0.20).
2. **The refuge fills.** Bodies a mid stand cell in summer over the equinoxes: 1.25 or more.
3. **A refuge, not a home (R1).** At the equinoxes the mid lawn holds more bodies a cell than the mid stand.
4. **The winter's price.** In the mid stands' winter the warming a body pays a turn rises with c3; cold
   deaths stay under 5% of all deaths.
5. **Stage C's measure does not fall** (one seed, indicative): kinds at a census and kinds kept to a place at
   or over the control's.

## Method

e079's crate with `crown_cool` read on the body's side in `refresh_air`, after e078's damper; 0 is e079
exactly. The world is e079's `crown_wet` 1, `wood_rest` 0.5 (its settled-world file, built by e079).

**Runs** (seed 9, 60,000 steps, a census every 1,000 steps from 36,000, as e078): the control c3 0 and
c3 0.1, 0.2, 0.4. On e079's map of this world a mid stand has a shade of 0.42 and a sun heat of 73 degrees
in its summer (a mean of 40 C against a dark equilibrium near -30 C) and 42 in its winter (8 C), so the
three cut a stand's summer mean by about 3, 6 and 12 C and its winter mean by 2, 3.5 and 7 C. e078's control (the old world, same seed and censuses) is read beside them for what the
plants' half did to the bodies.

    (nohup bash experiments/e080_cool/batch.sh search 60000 9 > experiments/e080_cool/results/search.log 2>&1 < /dev/null &)

4 runs on 4 cores of the Mac, one thread each, about 40 minutes. If a candidate passes 1-3, its c3 on seeds
9-11 at 100,000 steps against the control there (6 runs on 6 cores, about an hour).

The 3-seed run was **not made**: no candidate passed hypotheses 2 and 3.

## Result

**The check.** With `crown_cool` 0 a 2,000-step run of seed 9 on e078's world is byte-identical to e079's
(log timing aside, bands, census). The runs read e079's w1r0.5 world (its file holds the 14,888 mid stand
cells e079's build ended with). Matter drifts by at most 2.0e-14. A unit test: c3 0.2 under a shade of 1/2
takes a tenth of the day's sun heat, at most all of it, and a bare cell is left alone. Each run took 24 minutes.

**The search** (seed 9, 60,000 steps; `sweep.py`; bands after the first year, censuses 36,000-60,000).
"Mid" is 20-50 degrees, seasons the hemisphere's own. e078's control is the old world (no S1/S2).

| run | water, mid stand S/W/E | water, mid lawn S/W/E | bodies a mid stand cell S/W/E | a mid lawn cell S/W/E | stand S/E | stand / lawn at the equinoxes | warm a turn, stand in winter | cold deaths | kinds / placed |
|---|---|---|---|---|---|---|---|---|---|
| e078 control | 0.20/0.89/0.63 | 0.26/0.70/0.44 | 0.027/0.081/0.104 | 0.006/0.017/0.037 | 0.26 | 2.79 | 0.0113 | 1.8% | 7.08 / 4.44 |
| c3 0 | 0.40/0.95/0.72 | 0.26/0.75/0.49 | 0.039/0.051/0.077 | 0.004/0.013/0.024 | 0.50 | 3.22 | 0.0145 | 1.5% | 7.00 / 4.32 |
| c3 0.1 | 0.47/0.95/0.79 | 0.29/0.77/0.49 | 0.054/0.047/0.080 | 0.005/0.012/0.024 | 0.68 | 3.28 | 0.0200 | 2.0% | 5.84 / 3.72 |
| c3 0.2 | 0.52/0.94/0.79 | 0.28/0.73/0.46 | 0.041/0.036/0.055 | 0.006/0.010/0.018 | 0.74 | 3.06 | 0.0298 | 3.6% | 6.20 / 3.40 |
| c3 0.4 | 0.77/0.95/0.89 | 0.33/0.77/0.54 | 0.066/0.039/0.066 | 0.006/0.010/0.022 | 1.01 | 2.96 | 0.0370 | 3.7% | 3.72 / 2.24 |

Land bodies 3,174-4,262 (e078 4,138); thirst 36-44% of deaths (e078 48%); kills 31-34% of the intake.

- **The plants' half alone moves the mid-latitude crowd into the stands for the whole year.** At c3 0, of
  the land bodies censused on a stand or a lawn at 20-50 degrees at the equinoxes, 66% are in stands
  against 16% in the old world (17,532 and 9,174 on stand and lawn against 3,404 and 17,630). A stand's bodies hold 0.40 of their
  water in summer (0.20), and the stands lose half their bodies in summer instead of three quarters.
- **S3 closes the summer and stops there.** The stand's cooling in summer halves at c3 0.4 (0.0048 to 0.0021
  a turn) and its bodies hold 0.77 of their water; the stands' bodies a cell in summer come level with the
  equinoxes (1.01) but do not pass them.
- **The stand is the home in every season.** At the equinoxes a mid stand holds 3.0-3.3 times the bodies a
  mid lawn cell does in every run (2.8 in the old world). The lawn's bodies hold 0.46-0.54 of their water
  at the equinoxes and 0.26-0.33 in summer: water keeps them thin in every season, so the good season never
  comes to the lawn.
- **The winter's price is paid.** Warming in a mid stand in winter rises 2.5-fold at c3 0.4, cold deaths
  from 1.5% to 3.7% of all deaths, and the stands' winter over equinoxes stays at 0.58-0.66.
- **A better home makes fewer kinds.** Kinds at a census fall from 7.00 to 3.72 and kinds kept to a place
  from 4.32 to 2.24 at c3 0.4; at c3 0.1 one lineage holds 73% of the land's bodies. The "line" with a
  summer ratio of 2.56 at c3 0.1 is a lineage seen at one census (the detector's split), not a line.

**The hypotheses:**

1. The body's water: **yes**, and already at c3 0 (0.40; 0.47-0.77 with S3).
2. The refuge fills: **no**. Summer over the equinoxes 0.68-1.01 against 1.25.
3. A refuge, not a home: **no** in every run, the control included (stand over lawn 2.96-3.28).
4. The winter's price: **yes** (warming 0.0145 to 0.0370 a turn; cold deaths 1.5% to 3.7%, under 5%).
5. Stage C's measure: **no**, it falls (7.00 / 4.32 to 3.72 / 2.24 at c3 0.4).

## Conclusion

The crown's three laws do not make a refuge: they make the stand a better home. With the plants' half the
mid-latitude crowd moves into the stands for the whole year, and with S3 the stands stop emptying in summer,
but they never fill, because they are already the crowded place in every season. The payoff that fails is
R1 (and with it R3): section 13 read R1 as food per body (the lawn's 4.0 against the stand's 2.7), which is
high on the lawn only because water keeps bodies off it. Per cell the lawn is the poor place all year;
its bodies hold half their water in the good season. A refuge needs a season in which the open land is
the better place, and on this land that is a question of water, not of the crown.

What it changes: S1-S3 are not kept (the kinds fall and no refuge forms); stage C's default world stays
e075's. #91's crown path ends here. The next design is the land's water in the good season: where a body
drinks on open land when the season is kind (the savanna's pattern: the open land wet in one season, the
permanent water the refuge in the other).

Conditions: c1225, seed 9 at 60,000 steps, the heat band 15-30 C, `fresh` 0.05 (wet ground gives a twentieth
of a pool's drink), a grown body living about 1/20 of a year.
