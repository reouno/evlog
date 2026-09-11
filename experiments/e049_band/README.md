# e049 The band of rain

Date: 2026-09-11

## Purpose

Under the motor (e048) every body keeps muscle, but every body moves about a third as far as
before: the food renews evenly, the crowd grazes everywhere, and nothing asks a body to go far.
Four laws applied everywhere (e038 more sun, e040 thirst, e041 growth that follows the stock, e046
plant matter harder to digest) were absorbed by the crowd's density. Only e032's winter by height
made bodies travel: a place whose worth changes in time. So #14's first pilot is a place
difference that moves: a band of rain that crosses the world at a speed a body can follow within
its life. The real-world picture is the rains that the savanna's herds follow.

Speed pays when the food moves (the band) and a step needs muscle (the motor, e048's law): the two
conditions together.

## Hypothesis

Written before the runs, for a band that crosses a cell in 50 steps:

1. **Bodies follow the rain.** Bodies move west by their own actions (`west` above 0 on all six
   seeds), and the grown bodies stand west of their birthplace by at least half of what the band
   moved in their lives (median drift over age at least 0.01 cells a step) on at least four seeds.
2. **Speed is selected.** Speed (muscle over mass) rises above e048's on the same seed on at least
   five of six, and bodies move farther: `moved` above e048's 0.059-0.089 on at least five seeds.
3. **The world stands, poorer, and hunger kills behind the band.** The lowest winter floor stays
   above 100; bodies are fewer than e048's on every seed; the deaths by hunger peak in the cells
   the band has left, not under it.

The pilots settled (1) for that band within 20,000 steps (see Result): the crowd stays under the
rain by being born there and walks west at 2% of the band's speed. A body lives about 200 steps
(the median age at death) and the band stays over a cell 1,600, so a body need not move. The batch
asks again where births cannot keep up (25 steps a cell: in the pilot the crowd lags the band) and
where a body must also drink the water that moves (e040's thirst, 0.005: a full body is dry in 200
steps; its eyes see the pools):

4. **Bodies walk with the band when they must drink.** Under thirst, `west` over the second half is
   at least a quarter of the band's speed (0.04 sub-cells a step) on at least three of four seeds,
   and the grown bodies' median drift at least a quarter of what the band moved in their lives;
   without thirst, less.
5. **Speed is selected under the band.** Speed above e048's on the same seed on at least three of
   four seeds, in both conditions.
6. **The world stands.** The lowest winter floor stays above 50 in every run; bodies are fewer than
   e048's.

## Method

Code: e048 (`experiments/e048_motor`) as `e049_band`, with `motor` 1 by default (e048 kept it) and
one law about the sky, off by default:

- **`band`** (argument 45) N: the sky's rain falls on a band a quarter of the world's width (32 of
  128 columns), four times WATER_RAIN a cell, none outside: the world gets as much water as before,
  in one place. The band is a straight north-south strip that moves west one column every N steps,
  round the torus. The water is otherwise e035's: it runs downhill, evaporates 1% a step, and a
  plant grows at min(1, water / WET) of its light. A cell under the band fills to about 4 WET in a
  few hundred steps; when the band has left, it falls below WET in about 140 steps and the plant
  slows.
- **Speed.** The design was N = 50: 0.08 sub-cells a step, what a body moves now in all directions
  together (e048: 0.059-0.089), a lap in 6,400 steps, 1,600 steps over a cell. The batch runs
  N = 25 (0.16 sub-cells a step, a lap in 3,200 steps, 800 steps over a cell).
- **Thirst** (argument 36, e040's law, not kept there because its water stood still): a body's
  fill (1 when full) falls by `thirst` a step; on a cell whose water is above WET (a pool: under
  the band, every cell) it drinks 0.1 times the pool's depth in WET (at most 1) a step; a body
  whose fill reaches 0 dies. Its eyes see the pools in the four directions as they see food, and it
  reads its own thirst: five inputs to the same four outputs.
- **Log**: `in_band`, the share of the body-steps under the band; `west`, sub-cells a body moved
  west by its own actions less those it moved east, per body per step. `agents.csv` gets `drift`,
  how far west of its birthplace the body stands (world cells, signed). `dist.csv` gets, every log
  interval, by the columns behind the band's front (0-31: under the band; 127: next to be rained
  on): the body-steps (`band_bodies`) and deaths by hunger (`band_hunger`) over the interval, and
  the food standing (`band_food`).
- **Checked**: `band` 0 repeats e048's motor run on seed 9 in the first 20,000 steps of every CSV
  but the new columns, the timing column and the parameter line. A unit test: the band's front,
  its rain (the same total as before), and drift across the torus's seam.

**Runs.** e048's season world under the motor, one thread each unless said:

| run | band | thirst | seeds, steps | question |
|---|---|---|---|---|
| control (e048's motor runs, already run) | 0 | 0 | 9-12, 100,000 | the baseline |
| check | 0 | 0 | 9, 20,000 | byte for byte with e048's motor run |
| pilots, 5 threads | 50, 25, 12 | 0 | 9, 20,000 | (1); how fast the crowd follows by births |
| pilots, 5 threads | 25 | 0.002, 0.005 | 9, 20,000 | does a body that must drink walk; does the world stand |
| band | 25 | 0 | 9-12, 100,000 | (4)-(6) without thirst |
| band + thirst | 25 | 0.005 | 9-12, 100,000 | (4)-(6) |

Four seeds a condition: the question is walking (`west`, `drift`), not the world's state. Run from
the repo root: `bash experiments/e049_band/run.sh <band> <thirst> <threads> <steps> <seeds>`. The
pilots' and the check's outputs are in `results/pilot/`.

**Measures** (over the second half). `west`, `in_band`; the median drift and drift over age of the
bodies aged 1,000 steps or more at step 100,000; `moved`, speed and muscle per body; bodies, winter
floors, the kills' share of the intake (the state), deaths by hunger and by thirst, and where they
fall; the winners of the last third; diversity (#42).

**Compute.** One pass over the 128 columns and one over the bodies per step: well under a percent
of a step's cost. The runs: the check and five pilots, 5 threads each, 2.5 minutes a run, two at a
time; the batch, 8 of the Mac's 12 cores for about 20 minutes.

## Result

**Check.** `band` 0 on seed 9 for 20,000 steps is e048's motor run: every row of every CSV
identical but the new columns (`in_band`, `west`, `drift`) and `steps_per_sec`; `terrain.json`
identical but the parameters `band` and `band_part`.

**Pilots.** Seed 9, 20,000 steps (the first winter; log rows at 10,000 and 20,000). Where hunger
kills: the columns behind the band's front with the most deaths by hunger.

| band | thirst | under the band | `west` (the band's speed) | speed | hunger kills most | bodies at 20,000 (winter low) |
|---|---|---|---|---|---|---|
| none (check) | 0 | - | - | 0.24, 0.28 | - | 2,542 (422) |
| 50 | 0 | 63%, 60% | 0.0018, 0.0012 (0.08) | 0.24 | 16-31, under it | 739 (163) |
| 25 | 0 | 48%, 42% | 0.0056, 0.0059 (0.16) | 0.28, 0.27 | 32-47, just left | 1,183 (249) |
| 12 | 0 | 27%, 12% | 0.0077, 0.0076 (0.33) | 0.30, 0.29 | 48-79 | 1,156 (201) |
| 25 | 0.002 | 53%, 54% | 0.0099, 0.0088 (0.16) | 0.28, 0.27 | 32-47 | 931 (95) |
| 25 | 0.005 | 63%, 56% | 0.0064, 0.0133 (0.16) | 0.25, 0.19 | 32-47 | 554 (130) |

- **At 50 the crowd rides the band by births.** 60-63% of the body-steps are under the band (a
  quarter of the world) and bodies walk west at 2% of its speed. The median age at death is 195-212
  steps (e048: 180-194); the band stays over a cell 1,600: a body is born and dies under the rain.
  Deaths by hunger fall where the bodies stand, under the band.
- **Faster, the crowd lags.** At 25 the most bodies stand 16-47 columns behind the front, at 12 they
  stand 32-79 behind and hunger kills behind the band. `west` rises with the band's speed but stays
  2-4% of it: bodies do not walk after the rain.
- **Thirst holds the crowd under the band**, by killing the ones left behind (deaths by thirst
  22-30% of the deaths at 0.005), and `west` doubles by step 20,000 at 0.005 (0.013), 8% of the
  band's speed.

**Batch.** Seeds 9-12, 100,000 steps, eight runs at once on the Mac (8 of 12 cores), 29 minutes
(the runs under thirst the slowest). Means over the second half (steps 50,000-100,000); pairs are
band / band + thirst, triples e048 / band / band + thirst. Drift: the median drift over age of the
bodies aged 1,000 steps or more at step 100,000, in cells a step (the band moves 0.04), and how
many there are. Seed 11 under thirst died at step 76,214 (in the fourth winter's trough); its
means are over steps 50,000-76,000.

| seed | walking west | under the band | drift (bodies) | speed | bodies | lowest floor | thirst's share of deaths | kills' share | diversity |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 0.0059 / 0.0102 | 39% / 61% | 0.0071 (37) / 0.0218 (11) | 0.25 / 0.24 / 0.23 | 1,937 / 834 / 879 | 422 / 104 / 82 | 21% | 32% / 30% / 29% | 2 / 1 / 1 |
| 10 | 0.0057 / 0.0079 | 43% / 61% | 0.0057 (28) / 0.0200 (2) | 0.16 / 0.27 / 0.28 | 2,085 / 940 / 714 | 558 / 16 / 89 | 25% | 4% / 29% / 28% | 2 / 1 / 2 |
| 11 | 0.0093 / 0.0122 | 34% / 61% | 0.0041 (141) / - | 0.16 / 0.22 / 0.28 | 2,693 / 1,164 / 694 | 742 / 119 / died | 29% | 10% / 24% / 30% | 1 / 1 / 2 |
| 12 | 0.0033 / 0.0077 | 35% / 63% | 0.0037 (179) / 0.0284 (17) | 0.24 / 0.19 / 0.23 | 2,004 / 918 / 864 | 347 / 122 / 25 | 23% | 34% / 17% / 30% | 1 / 1 / 1 |

- **The crowd lags the band and does not walk after it.** Without thirst, 34-43% of the body-steps
  are under the band; the most bodies stand 16-47 columns behind its front and hunger kills most at
  32-47 (the columns the band has just left). Bodies walk west at 0.003-0.009 sub-cells a step, 2-6%
  of the band's 0.16. The grown bodies stand 5-10 cells west of their birthplace (median), 9-18% of
  the band's way.
- **Under thirst the long-lived walk.** The crowd is held under the band (60-63% of the body-steps;
  the most bodies at 16-31 columns, the band's back half) and walks west at 0.008-0.012, 5-8% of the
  band's speed. But the bodies aged 1,000 steps or more stand 22-35 cells west of their birthplace:
  0.020-0.028 cells a step, half to 70% of the band's speed. They are 2-17 a run: the rest died of
  thirst (21-29% of the deaths) or of hunger before that age. Bodies aged 500-999 steps drift 9
  cells (all seeds together; 1.8 without thirst).
- **Speed is not selected.** Above e048's on seeds 10 and 11 in both conditions, below on 9 and 12
  (0.19-0.28 against 0.16-0.25).
- **A poorer world that nearly dies in winter.** Bodies 54-74% fewer. Winter lows fall to 16 (band,
  seed 10, the first winter) and 25 (thirst, seed 12); seed 11 under thirst dies. The mean age of
  the living falls under thirst (213-314 against 286-504 without and 278-1,329 in e048). Under thirst
  the food of the dry land stands uneaten (11-12% of it in every 16 columns behind the band, against
  5-7% without thirst).
- **The crowd packed in the band hunts.** The hunter world on all four seeds under thirst (kills
  28-30% of the intake) and on two without (e048: two, seeds 9 and 12); the grazer seeds' kills rise
  from 4% and 10% to 24-30% under the band. Contact was not measured.
- **Winners.** Without thirst: gut-front hunters of 23 blocks (seed 9), grazers of 14-26 blocks with
  muscle across the front (seeds 11, 12). Under thirst: smaller bodies of 14-16 blocks on seeds 9 and
  12, one with 11 of 16 blocks muscle (seed 12, speed 0.29), a 32-block body with a hard corner
  (seed 10). Diversity 1-2, as in e048.

## Conclusion

1. **Bodies follow the rain by walking (band 50): no.** The crowd stays under the band by being born
   there and walks west at 2% of its speed. (2) and (3) were not run at 50: the batch moved to 25,
   where (5) and (6) ask the same.
4. **Bodies walk with the band when they must drink: partly.** The crowd does not (5-8% of the
   band's speed, under the 25% asked), but the few bodies that live 1,000 steps do (half the band's
   speed, over the quarter asked, on the three seeds that lived).
5. **Speed is selected under the band: no.** Two seeds of four in both conditions.
6. **The world stands: no.** Bodies are fewer, as expected, but one world of eight dies and two fall
   to 16 and 25 bodies.

**Not kept**: the band does not make bodies walk, halves the world and nearly kills it in winter. It
stays as the argument `band` (45), to combine with a law that gives it a reason.

What this changes:

- **What moves is the lineage, not the body.** A body lives about 200 steps (the median age at death)
  and the crowd is replaced every few hundred steps, so a place that changes slower than a life is
  followed by births (the band at 50), and one that changes faster outruns the crowd before any body
  needs to walk (the band at 25 and 12). The complaint that bodies do not move is a matter of how long
  they live against how fast their world changes.
- **Walking pays to the long-lived, and they are few.** Under thirst the bodies that reach 1,000
  steps walk with the band; most bodies die young of hunger in the crowd whatever they do, so
  selection on walking works on a few percent of the bodies. A body cannot see where the rain is
  going either: it sees food and pools, and under the band both are even.
- **Next**: #52 (materials whose worth depends on shape), as planned. Open for #14: a band under
  bodies that live longer, or that sense the rain; why the band raises hunting (density, contact not
  measured); a milder winter for a band world.
- **Compute**: 29 minutes for eight runs at once; the runs under thirst are the slowest (the pool
  inputs).
