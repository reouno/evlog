# e087: a year of 1,200 steps and a flesh whose pace follows its warmth (#93, Y+Q)

Date: 2026-09-19

## Purpose

P1 (#93, `vision.md` section 5): a grown body lives about 1/20 of a year and a few cells, so no body meets a
season; the places and seasons stages A and B made are felt only by lines over generations. #93's design
(agreed 2026-09-19) makes the winter a spell a body can live through and gives it a way to do so:

- **Y, the year: 1,200 steps** (e086). The seasonal land (31% of the land) is lean for about 400 steps a year
  (p90 1,000); the land always fed (62%) is 15 cells away at the median.
- **Q, the flesh's pace follows its warmth.** A body takes `clock x q10^((T - warm_lo) / 10)` turns a step,
  at most its clock and at least a tenth of it (q10 2.5, warm_lo 15 C). It exchanges heat with its cells every
  step and makes heat only in its turns, so a slowed body makes less and cools further (torpor), and a closed,
  busy body keeps itself warm. Set A's paid warming (`heat_spend`) and death by cold go; sweating over 30 C
  stays. A torpid body's bites, moves, breeding, water loss, upkeep and wear all slow with its turns, so its fat
  lasts up to ten times as many steps.

The cycle (what Q takes, what refills it, what limits it, the balance expected, how it is wrong) is written
in #93 and not repeated here.

## Hypothesis

On seeds 9-11 at 100,000 steps, Y+Q meets #93's done-when:

1. **A winter lived through.** On seasonal land, 25% or more of the grown bodies (300 steps or older) standing
   on a cell whose winter starts are alive when that winter ends.
2. **A year lived.** The p90 of a grown body's age at death is 1,200 steps or more.
3. **The season changes what a body does.** In winter on seasonal land 30% or more of the body-steps are
   torpid (at most half its clock, under about 7.4 C), or grown bodies that live through it travel 15 cells or
   more toward fed land.
4. **No harm.** Kinds at a census and kinds kept to a place not below the lowest of e081's control seeds
   (7.25 and 4.47); the world stands 100,000 steps; the ledger holds.

Y alone (set A kept, seed 9) names what Q adds: its winter survival should be near 0 and its torpid share
low (bodies pay to stay warm or die of cold).

**Wrong if** torpid body-steps are rare on seasonal land in winter (a body's own heat keeps it out of the
cold), or torpid grown bodies still starve before spring (then F, the store filling from the surplus, in
e088).

## Method

- **Code.** e082's crate as `e087_torpor` with one law and one measure module:
  - `q10` (0 = e082 exactly; checked on 3,000 steps of seed 9: the log equal but for the timings, the census
    byte for byte), `q_floor`
    0.1. Under Q the heat exchange moves from the turn to the step (the same share of the way), the heat
    made stays in the turn; at a pace of one turn a step this is set A's update.
  - `places.rs` (no law): e086's map at the same year (`places.py` writes `results/places_y<year>.bin`: each
    cell sea, always fed, seasonal or never fed, and its lean months at the bar 0.25). A seasonal cell's winter
    is its longest run of lean months. Every month (100 steps) `_months.csv` gets a row: body-steps and torpid
    body-steps by class, the same on seasonal land in its winter (all and grown), births, deaths, deaths by 75
    steps and grown deaths by class, and the winter cohorts: grown bodies entering (on a seasonal cell whose
    winter starts that month) with their fat in steps of fasting, and, as each winter ends, how many lived,
    how far they went and how many stand on land fed that month. `_grown.csv` has a row per grown body's
    death (age, cause, class, travel). "Torpid" is a pace of at most half the clock, read at q10 2.5 in the
    run without Q too.
- **World.** Stage C's default world as e082 ran it (`run.sh`: c1225, d11, e072's sets, e073's crown yield,
  e075's tear and frail line, `fresh` 0.05, `unit` 0), with `year=1200`; the settled world at that year is
  built once (200,000 steps of producers).
- **Pilot.** Y+Q, seed 9, 30,000 steps: does the world stand.
- **Batch.** Y+Q on seeds 9-11 and Y alone on seed 9, 100,000 steps, a census every 1,000 steps from 36,000.
  Four runs on four cores of the Mac, about 50 minutes. Controls: e081's ladder (year 11,880, unit 0,
  `experiments/e081_drink/results/ladder/c1225_life{9,10,11}_u0`).
- **Reading** (`read.py`): the four criteria over steps 36,000-100,000, and kinds at a census and kept to a
  place by e075's `read_run`, as e081 and e082 read them.

## Result

A first pilot (seed 9, 30,000 steps) ran with a bug: under Q the sweat branch was skipped, so no body cooled
(thirst fell to 3% of deaths). It was stopped, the test `a_cold_body_slows_and_does_not_pay_to_warm` now
checks that a body over the band sweats under Q, and its files were deleted. The batch below ran with the fix;
its first 30,000 steps stood in for the pilot. Each run took 45-55 minutes at 100,000 steps (4 cores of the
Mac, 20-29 ms a step); the settled world at a year of 1,200 took 4.7 minutes to build. The ledger's largest
error is 5.6e-14.

Steps 36,000-100,000 (`results/read_batch.csv`, `uv run python experiments/e087_torpor/read.py
experiments/e087_torpor/results/batch <e081 ladder prefixes>`):

| run | winter lived | cohort | fat in (steps) | moved | grown p50 / p90 / p99 | torpid in winter | T in winter | kinds | placed | largest line | bodies (land) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Y+Q seed 9 | 84% | 12,659 | 159 | 1.2 | 439 / 919 / 2,264 | 96% | -9.9 C | 8.06 | 3.86 | 61% | 8,128 (4,031) |
| Y+Q seed 10 | 84% | 11,715 | 133 | 1.0 | 437 / 926 / 2,342 | 96% | -9.3 C | 7.24 | 3.86 | 46% | 7,123 (3,390) |
| Y+Q seed 11 | 81% | 8,761 | 165 | 1.9 | 430 / 869 / 2,316 | 96% | -9.9 C | 6.71 | 1.90 | 78% | 8,826 (4,322) |
| Y alone seed 9 | 36% | 16,232 | 162 | 3.7 | 450 / 966 / 2,324 | 0% | 15.6 C | 5.78 | 4.04 | 41% | 8,689 (4,362) |
| control seed 9 (e081) | - | - | - | - | - | - | - | 7.45 | 4.75 | 58% | 9,450 (4,028) |
| control seed 10 | - | - | - | - | - | - | - | 8.27 | 4.65 | 63% | 9,298 (3,735) |
| control seed 11 | - | - | - | - | - | - | - | 7.25 | 4.47 | 42% | 9,147 (3,701) |

"Winter lived": of the grown bodies on a seasonal cell when its winter starts, the share alive when it ends.
"Moved": cells between where a survivor started and ended its winter; 95-97% of the survivors (Y alone 87%)
stand on land fed that month at the end. "Fat in": steps of fasting at full pace at the winter's start.

- **The winter is waited out.** Under Q a body in winter on seasonal land sits near -10 C and 96% of its
  body-steps are torpid; under Y alone bodies sit at 15.6 C (they pay to warm) and 2.6% of all deaths are by
  cold (6% of grown deaths). Nobody travels: the survivors end 1-2 cells from where they began.
- **Q doubles the seasonal land's use**: 12.5-13.3% of all body-steps are on it, against 7.1% under Y alone.
- **A year is not lived.** Grown age at death by where it died (seed 9, Y+Q against Y alone): seasonal land
  p50 608 / p90 1,102 against 478 / 1,118; land always fed 418 / 753 against 466 / 984; sea 429 / 901 against
  422 / 839. Most grown deaths are in the sea (about 45%) and on the land always fed (35%); they die of hunger
  (50-56%), thirst (26-30%) and wounds (12-20%); none of cold.
- 11-14% of body-steps on the land always fed are torpid under Q. The dead by 75 steps are 51-61%
  of the dead (Y alone 48%).
- **The oldest bodies** at the last censuses are 6,600-18,100 steps old (5-15 years): small soft bodies on the
  cold sea bottom at -5 to -8 C, taking a fraction of a turn a step, and on seed 10 hard-shelled land bodies
  (51 and 34 blocks, 59% hard) on seasonal land at 18-20 C.
- **Births on seasonal land** swing 2.4-4x over the year under both (month 4 the lowest).
- **Kinds.** At a census 8.06 / 7.24 / 6.71 against the lowest control 7.25 (seed 9 over its control, 10 at
  the line, 11 under); kept to a place 3.86 / 3.86 / 1.90 against 4.47, under on every seed. Y alone on seed 9:
  5.78 / 4.04. The largest line holds 46-78% of the land's bodies (controls 42-63%).

**The hypotheses (#93's done-when):**

1. A winter lived through: **yes** (81-84% against 25%; Y alone 36%).
2. A year lived: **no** (p90 869-926 against 1,200).
3. The season changes what a body does: **yes** by torpor (96% against 30%); no travel.
4. No harm: **no** (kinds kept to a place under the line on all three seeds, kinds at a census on seed 11).

## Conclusion

Q does what #93 drew for the winter: the cold slows a body instead of taxing it, a grown body on seasonal land
waits the winter out on its fat (it enters with about ten times what a torpid winter takes) and the spring comes
to it. The wrong-ifs of Q did not happen: torpor is common, and torpid bodies do not starve before spring. So F
(the store filling from the surplus) would not change the result, and e088 is not F.

The done-when assumed the winter was what ended a grown life. It is not. Grown bodies die of hunger, thirst
and wounds in the crowd, in the sea and on the land always fed, as before: the p90 of a grown life stays at
870-930 steps, 3/4 of a year. e037 and e038 found that the crowd pins a body's income at the world's regrowth;
a longer grown life needs a world where a grown body is not at that edge. That is the crowd (F's crowding row)
and the one food (P2), not the season.

P1 is not done: 1 and 3 hold, 2 and 4 fail. By the rule agreed in #93, Y and Q do not become the default world.
Kinds kept to a place fall on every seed; Y alone falls too on its one seed, so part of that is the year's, and
this batch cannot split the two. No body migrates: nothing asks one to (a torpid body loses nothing by staying).

Rows of `vision.md` this changes: E (life against the year: a winter is lived through under Q, a grown life is
still 3/4 of a year and bound by the crowd; travel: none, the winter is waited out), C (life history: dormancy
now a law of the flesh), and a lesson in section 4. The next step is chosen from `vision.md`: #93's budget allows
one rewritten design (two stage C experiments left), or P2 first.

Conditions: c1225 with d11, seeds 9-11 at 100,000 steps, a year of 1,200 steps, stage C's default world as e082
ran it, q10 2.5 with a floor of 0.1, grown meaning 300 steps or older, places and winters from e086's map at the
bar 0.25.
