# e082: fresh under W1 (#95)

Date: 2026-09-19

## Purpose

e081 (#94) put a body's water into the land's: drinking takes from the ground (W1) and what a body loses goes
back (W2). The crowd paid for its water as drawn, but water then bound every land body (0.28 of its water
against 0.58), bodies ended nearer their birth place (travel 5.3 to 3.1) and kinds fell in all three seeds.
A body drinks little anywhere but a pool: wet ground gives `fresh` 0.05 of a pool's drink. #88 (set D) set that
share when a drink was free, so that the shore would not be free. Under W1 the ground pays for the drink, so
set D's reason for a small `fresh` is gone. This experiment raises it (`balance.md` section 17, agreed
2026-09-19).

## The cycle (written before the runs, `balance.md` section 17)

- **Takes** the ground's water where a crowd sits: the lawn's spring ground (0.38 full at unit 9.4) becomes
  something a body can live on. At median ground a block drinks about 0.8 of what it loses to the air at
  `fresh` 0.05, about 3 times at 0.2 and 7 times at 0.5 (e072's table), so at 0.2 and up a body away from
  pools is full unless its crowd has drawn the ground down.
- **Refilled** by the rain and the runoff.
- **Limited** by W1: a crowd that drinks more draws its ground down faster, until the drink falls to what it
  loses. The crowd then sits where the rain keeps the ground over that line, and moves when it falls under.
- **Expected**: the lawn's wet season carries bodies without pools, the tether loosens (bodies follow wet
  ground), and the stand's lead over the lawn falls further in spring.
- **Wrong if** the lawn's share in spring does not rise over e081's, travel does not rise, or kinds fall again.
  A second way to be wrong: the drink stops binding anywhere, the land is food-bound again, and the stand is
  the one home as in e080.

## Hypothesis

At unit 9.4, against e081's run at `fresh` 0.05 (seed 9, 60,000 steps, mid = 20-50 degrees, each hemisphere's
own season):

1. **The land stands.** Land bodies at half e081's control or more; thirst under 60% of deaths.
2. **The lawn's wet season.** Bodies a mid lawn cell over a mid stand cell in spring rise over 0.35.
3. **The tether loosens.** Travel (cells from birth place at death, grown bodies) rises over 2.2.
4. **The measure does not fall.** Kinds at a census not under 6.88, kinds kept to a place not under 3.20.

## Method

e081's crate unchanged (`fresh` and `unit` are already arguments). Seed 9, unit 9.4, `fresh` 0.2 and 0.5,
60,000 steps, a census every 1,000 steps from 36,000. `fresh` 0.05 at unit 9.4 and the control (unit 0) are
e081's search runs (`experiments/e081_drink/results/search`).

    (nohup bash experiments/e082_fresh/batch.sh search 60000 9 0.2 0.5 > experiments/e082_fresh/results/search.log 2>&1 < /dev/null &)

2 runs on 2 cores of the Mac, one thread each, about 30 minutes. Read with

    uv run python experiments/e082_fresh/sweep.py experiments/e082_fresh/results/search \
      experiments/e081_drink/results/search/c1225_life9_u0 experiments/e081_drink/results/search/c1225_life9_u9.4

If one passes 1-4, it on seeds 9-11 at 100,000 steps against e081's ladder (the control and unit 9.4 at
`fresh` 0.05): 3 runs, 3 cores, about an hour.

## Result

Each search run took 28-30 minutes at 60,000 steps, each ladder run 46 minutes at 100,000 (3 cores). The
ledger's largest error is 4.7e-11.

**The search** (seed 9, 60,000 steps, censuses 36,000-60,000; `results/sweep_search.csv`). "Lawn / stand" is
bodies a mid lawn cell over a mid stand cell; "home" the stand over the lawn at the equinoxes.

| run | land bodies | thirst | home | lawn / stand, spring | autumn | stand water, spring | lawn water, summer | largest line | kinds / placed | travel |
|---|---|---|---|---|---|---|---|---|---|---|
| control (unit 0) | 4,138 | 48% | 2.79 | 0.29 | 0.41 | 0.78 | 0.26 | 55% | 7.08 / 4.44 | 4.8 |
| fresh 0.05 (e081) | 3,820 | 52% | 2.51 | 0.35 | 0.42 | 0.35 | 0.14 | 67% | 6.88 / 3.20 | 2.2 |
| fresh 0.2 | 3,793 | 46% | 1.51 | 0.62 | 0.70 | 0.54 | 0.26 | 80% | 6.88 / 3.56 | 12.5 |
| fresh 0.5 | 3,916 | 38% | 1.61 | 0.69 | 0.54 | 0.74 | 0.55 | 91% | 5.20 / 2.04 | 19.8 |

Fresh 0.2 passed 1-4 (kinds exactly at the line), 0.5 failed 4. Fresh 0.2 went to three seeds.

**The ladder** (seeds 9-11, 100,000 steps, censuses 36,000-100,000; `results/sweep_ladder.csv`; the control and
fresh 0.05 are e081's ladder):

| seed | run | land bodies | thirst | home | lawn / stand, spring | autumn | stand water, spring | largest line | kinds | placed | travel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | control | 4,035 | 48% | 2.77 | 0.30 | 0.41 | 0.81 | 58% | 7.45 | 4.75 | 5.8 |
| 9 | fresh 0.05 | 3,782 | 52% | 2.52 | 0.37 | 0.41 | 0.39 | 69% | 7.33 | 3.73 | 3.0 |
| 9 | fresh 0.2 | 3,540 | 44% | 1.58 | 0.62 | 0.64 | 0.54 | 84% | 6.90 | 4.02 | 14.0 |
| 10 | control | 3,640 | 50% | 2.70 | 0.28 | 0.47 | 0.80 | 63% | 8.27 | 4.65 | 4.2 |
| 10 | fresh 0.05 | 3,443 | 52% | 2.60 | 0.41 | 0.37 | 0.38 | 39% | 6.22 | 4.45 | 2.2 |
| 10 | fresh 0.2 | 3,442 | 47% | 1.50 | 0.68 | 0.65 | 0.58 | 82% | 6.16 | 3.22 | 13.5 |
| 11 | control | 3,676 | 46% | 2.91 | 0.27 | 0.41 | 0.79 | 42% | 7.25 | 4.47 | 6.0 |
| 11 | fresh 0.05 | 3,217 | 52% | 2.13 | 0.51 | 0.45 | 0.32 | 61% | 6.94 | 4.24 | 4.2 |
| 11 | fresh 0.2 | 3,834 | 43% | 1.44 | 0.72 | 0.67 | 0.60 | 72% | 5.80 | 2.94 | 17.0 |

- **The land stands.** 95% of the control's land bodies on average (e081 92%); thirst 45% of deaths (52%).
- **The tether loosens.** Grown bodies end 14.8 cells from their birth place against 3.1 (control 5.3), in
  every seed.
- **The lawn takes the crowd in both wet seasons.** Its bodies a cell over the stand's: spring 0.43 to 0.67,
  autumn 0.41 to 0.65 (the autumn section 16 expected), in every seed. The stand's lead at the equinoxes
  falls from 2.42 to 1.51 (control 2.79). Summer lawn bodies hold 0.28 of their water against 0.15.
- **Bodies drink twice as much.** About 3,900 mm a step over the world against 1,700; 2,900 of it goes back
  to the air as sweat. A mid stand's ground is lower in every season (spring 0.52 against 0.62); the mid
  lawn's about the same. 18-19% of children are born short of their parent's fill (7%).
- **One line takes the land.** The largest lineage holds 72-84% of the land's bodies (e081 39-69%, control
  42-63%). It is a large mover that eats half meat (seed 9: 39 blocks, 15 of them muscle, 54% meat). In the
  control and at 0.05 the line that leads the tropics holds only 4-20% of the bodies at 40-50 degrees north,
  where other lines live; at 0.2 it holds 45-74% there, and about the same share in every 10-degree band.
- **The measure falls in every seed.** Kinds at a census 6.83 to 6.29 (control 7.66), in all three seeds
  (-0.43, -0.06, -1.14); kinds kept to a place 4.14 to 3.39 (up in seed 9, down in 10 and 11).

**The hypotheses:**

1. The land stands: **yes** (95% of the control's bodies, thirst 45%).
2. The lawn's wet season: **yes** (spring 0.43 to 0.67, and autumn 0.41 to 0.65).
3. The tether loosens: **yes** (travel 3.1 to 14.8).
4. The measure does not fall: **no** (kinds 6.83 to 6.29 in all three seeds; the largest line 56% to 79%).

## Conclusion

Under W1 a larger `fresh` does what section 17 drew: the lawn carries the crowd in both wet seasons, the
stand's lead falls, and bodies go five times as far. It does not make kinds. The more a body moves, the
more one line spreads over every place: the line that leads the tropics now also holds the north's
mid-latitudes, which other lines held while bodies ended 3-5 cells from their birth place. e081's tether and
e082's loosening both lower kinds against the control, from opposite sides.

What it changes: `fresh` stays 0.05 and `unit` 0 in stage C's default world. For #91: water by place and
season can move the crowd between the stand and the lawn, but no setting here holds a line in a place that
another line cannot reach. What keeps lines apart on this land is distance against a line's spread (#68's
first rule), and the north's lines are the kinds a faster spread erases.

Conditions: c1225, seeds 9-11 at 100,000 steps, a body's water unit of a sub-cell's full ground (9.4 mm),
wet ground giving a fifth of a pool's drink at full fill, the heat band 15-30 C, a grown body living about
1/20 of a year.
