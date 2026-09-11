# e052 A time that scales with size

Date: 2026-09-12

## Purpose

What follows a change in this world is the lineage, not the body. A body lives about 200 steps
(the median age at death), so a place that changes slower than a life is followed by births
(e049), and learning, where it is kept at all, rides on hunters and not on a body that outlives a
change (e050, e051). A body matters, and can learn, only if it lives long enough to meet the
change itself. This is the behavior track's third step (#55), and the direction agreed with the
user on 2026-09-12: start from a time that scales with size.

In the real world every clock of a body runs at about mass^-1/4 (heartbeat, breath, generation,
lifespan): a large body lives long and acts slowly, a small one fast and briefly. Our world has no
such axis. Every body, whatever it weighs, eats, pays, ages, decides and acts once a step, and
e037 scaled one of those (the upkeep) alone and was not kept.

**What the bodies are now (checked first, decision rule 6).** In e048's world (seeds 9-14, the
second half): the living weigh 32-47 at the median (p10 12-24, p90 32-69); the median age at
death is 175-225 steps; 90-93% of the deaths are hunger, 0-8% wear, 2-10% a break; and the age at
death does not follow the size at birth (125-275 steps in every bin). So a law that lengthens the
life of the old alone (the wear's clock) would touch 0-8% of the deaths: what decides a life here
is what a body pays and takes each step.

## Hypothesis

Written before the runs.

**The law.** `clock` (argument 47) is the exponent of a body's own time. A body of mass m takes
(CLOCK_MASS / m)^clock turns per world step, never more than one: the world's step is the shortest
turn, so a body of CLOCK_MASS (16) or less takes one every step. Everything the body does happens
on its turns and nothing happens to it between them (it eats, pays its upkeep, ages by wear,
decides, acts, breeds); the world's clocks do not scale (the sun, the regrowth, the season, the
rain, the rot), and another body can still push, break or eat it between its turns. At `clock`
0.25 a body of mass 32 takes 0.84 turns a step, one of 64 takes 0.71, one of 256 takes 0.50.

Nothing about lives or children is written as a rule: the upkeep of a body comes to about m^3/4 a
step (Kleiber), its life to about m^1/4 steps, and the time from birth to a child to about m^1/4,
because all three are counted in turns.

**The payoff (written before the runs).** A gut takes min(res, 0.02) from the cell under it per
turn and a cell under a body does not grow, so where the food stands thick (a tree, res of 1 to 8)
the bite decides the intake and a slow body is a fast one in slow motion: it gains and pays r
times as much a step, and needs 1/r times as long to reach the threshold of a child. Where the
food is thin (the ground between the trees, the winter, intake per gut 0.003 a step against a bite
of 0.02) the world's regrowth decides the intake, not the bite: the slow body takes what the fast
one takes and pays r times as much for it. Its store (5 per unit of mass) then carries it 1/r
times as many steps of a winter.

So: **big bodies prosper beside small ones when a body's time runs slower the more it weighs (B)
and the world has places or seasons where the food is thin (A)**. A, the winter by height, is
already in e048's world.

1. **The law acts.** The life in world steps grows with the mass at birth: under the clock, bodies
   born at mass 48 or more die older than bodies born under 24, on at least 3 of 4 seeds. In the
   control there is no such difference (175-275 steps in every bin).
2. **Size pays.** The mass of the living over the second half is above the control's on the same
   seed (`mass_p90`) on at least 3 of 4 seeds.
3. **Different sizes at once.** The diversity number (#42) is above the control's on at least 2
   seeds of 4 and below it on none (the control on seeds 9-12: 2, 2, 1, 1).
4. **The world stands.** The lowest winter floor stays above 50 in every run.

## Method

Code: e051 (`experiments/e051_leave`) as `e052_clock`, with argument 47 `clock`. No other law is
new or changed; `stock` stays 0 (e051 did not keep it) and `brain` 0 (e050 did not).

- **Checked**: `clock` 0 repeats e048's motor run on seed 9 (e051 at `stock` 0, `brain` 0) for the
  first 20,000 steps of every CSV, but for the new columns of the log and of `agents.csv`, and for
  `deaths.csv`, whose rows split by the new mass bin (summed over it, the rows are the same).
- New measures: the log gets `pace` (the turns a living body gets per step, over the body-steps)
  and `turned` (the share of the body-steps whose turn came); `agents.csv` gets `turns` (the turns
  the body has taken) and `pace`; `deaths.csv` gets `mass`, the mass at birth in bins of 4, so
  that the age at death (in world steps) can be read against the size of the body.

**Runs.** e048's world (the season world under the motor, no band, no thirst), one thread each
unless said. Run from the repo root:
`bash experiments/e052_clock/run.sh <clock> <brain> <threads> <steps> <seeds>`.

| run | clock | seeds, steps | question |
|---|---|---|---|
| check, 3 threads | 0 | 9, 20,000 | byte for byte with e048 |
| pilot, 3 threads | 0.25 | 9, 20,000 | does the world stand, does the clock bind (`pace`, `turned`) |
| batch | 0.25 | 9-12, 100,000 | (1)-(4) |
| controls | 0 | 9-12, 100,000 | the world without the law, with the new measures (e048's motor runs byte for byte) |
| the slowdown alone (added after the batch) | -0.84 | 9-12, 100,000 | every body at 0.84 turns a step whatever it weighs: what of the batch is the scaling by size, and what is the slowdown itself |

The last row was added when the batch came back: under the exponent every body of this world runs
at 0.78-0.88, so the same food feeds more of them whatever their size, and the two have to be told
apart. (Its first four runs were lost to a bug of mine: the gate still read `clock > 0`, so a
negative value left every body at a turn a step. Found by the `pace` column reading 1, fixed, and
re-run; a 10,000-step run on seed 99 checked the fix before the batch.)

**Measures** (over the second half): `pace`, `turned`; the mass of the living (p10, p50, p90) and
the size; the age at death by the mass at birth, and by cause; births a step and bodies; the
winter floors; the kills' share of the intake; moving (`moved`, `stalled`); the winners of the
last third; diversity (#42).

**Compute.** The law skips the turns of heavy bodies, so a step costs less as the bodies grow; it
adds one `powf` per living body per step. Check and pilot: 2 runs of 3 threads, about 10 minutes.
Batch: 4 of the Mac's 12 cores, about 25 minutes.

## Result

**Check.** `clock` 0 on seed 9 for 20,000 steps is e048's motor run: every row of `log.csv`,
`pop.csv`, `places.csv`, `lineages.csv` and `events.csv` is identical, `deaths.csv` is identical
once summed over the new mass bin (1,804 keys, 138,241 deaths), and the long frames are identical.
Only `terrain.json` differs, by the `clock` field of the parameter line.

**Pilot.** Seed 9, `clock` 0.25, 20,000 steps, 3 threads: the clock binds (pace 0.81-0.83), the
world stands (2,177 bodies on average against the check's 1,912, lowest 655 against 422), and the
median age at death is 206-253 against 180-194. The batch overwrote its files.

**Batch.** Seeds 9-12, 100,000 steps, the clock and the control at `clock` 0 (e048's motor runs
byte for byte, re-run here for the new measures), eight runs at once on the Mac, 26 minutes. Means
over the second half (steps 50,000-100,000); pairs are without / with the clock on the same seed.

| seed | pace | mass p50 | mass p90 | life at death, born light | born heavy | bodies | lowest floor | kills' share | lineages alive | diversity |
|---|---|---|---|---|---|---|---|---|---|---|
| 9 | 1.00 / 0.85 | 34 / 34 | 52 / 48 | 125 / 125 | 225 / 275 | 1,937 / 2,660 | 422 / 655 | 32% / 6% | 6.5 / 16.5 | 2 / 1 |
| 10 | 1.00 / 0.79 | 41 / 47 | 67 / 60 | 75 / 125 | 325 / 375 | 2,085 / 2,347 | 558 / 622 | 4% / 6% | 7.4 / 9.8 | 2 / 1 |
| 11 | 1.00 / 0.88 | 32 / 32 | 32 / 32 | 125 / 75 | 175 / 175 | 2,693 / 2,908 | 742 / 776 | 10% / 3% | 11.3 / 14.3 | 1 / 1 |
| 12 | 1.00 / 0.78 | 37 / 50 | 54 / 72 | 75 / 125 | 225 / 325 | 2,004 / 2,361 | 347 / 465 | 34% / 16% | 3.4 / 11.2 | 1 / 1 |

- **The clock binds.** Bodies take 0.78-0.88 of a turn a step; `turned` follows `pace` to the third
  decimal. The upkeep, the intake, the wear and the moves all fall with it: moving is 0.035-0.052
  sub-cells a body a step against 0.059-0.089, births 2.9-4.6 a step against 2.5-7.5, and the
  intake per gut 0.0017-0.0023 against 0.0024-0.0028.
- **Bodies live longer, and the world holds more of them.** The mean age of the living rises from
  317, 739 and 278 to 1,328, 1,432 and 874 on seeds 9, 11 and 12 (seed 10: 1,329 to 1,337); the
  90th percentile of the age at death rises from 663, 863 and 580 to 3,288, 3,835 and 1,163. The
  world holds 8-37% more bodies, every winter floor is higher (465-776 against 347-742), and the
  lineages alive rise on all four seeds (3.4-11.3 to 9.8-16.5).
- **Wear acts for the first time.** Deaths by wear a log interval go from 3, 0.6 and 534 to 1,367,
  281 and 1,837 (seed 10: 1,952 to 1,128), and the living bodies carrying a worn block from
  2-16% to 13-28%.
- **Size is not selected.** The 90th percentile of the mass is above the control's on one seed of
  four (seed 12: 72 against 54), the median on two (47 against 41, 50 against 37) and unchanged on
  the other two. The bodies born heavy live longer than the bodies born light under the clock
  (2.2, 3.0, 2.3 and 2.6 times), but they do in the control too (1.8, 4.3, 1.4 and 3.0): the clock
  did not make that difference.
- **The tooth goes.** Hunter worlds 0 of 4 against 2 of 4; the share of the living with a bite
  falls from 40% and 47% to 0.2% and 0.1% on seeds 9 and 12, and the blocks broken by 68-86% on
  three seeds. No winning lineage under the clock carries a hard block (the control's winners on
  seeds 9 and 12 carry 6 and 7).
- **Diversity falls.** The number (#42) is 1 on all four seeds against 2, 2, 1, 1, although there
  are more winners to group (4, 3, 6 and 1 lineages hold 5% of the last third): the winners are
  more alike, a gut with muscle and no armor.

**The slowdown alone.** Seeds 9-12, 100,000 steps at a flat pace of 0.84: every body takes 0.84
of a turn a step whatever it weighs, so the world is as much slower without the scaling by size.
Means over the second half; the three numbers are without the clock / the clock at 0.25 / the flat
pace.

| seed | state | bodies | lowest floor | kills' share | bite in the living | mean age of the living | lineages alive | mass p90 | diversity |
|---|---|---|---|---|---|---|---|---|---|
| 9 | hunter / grazer / hunter | 1,937 / 2,660 / 2,205 | 422 / 655 / 561 | 32% / 6% / 35% | 40% / 0.2% / 46% | 317 / 1,328 / 349 | 6.5 / 16.5 / 4.7 | 52 / 48 / 49 | 2 / 1 / 2 |
| 10 | grazer / grazer / hunter | 2,085 / 2,347 / 2,164 | 558 / 622 / 481 | 4% / 6% / 27% | 0.2% / 0.6% / 46% | 1,329 / 1,337 / 459 | 7.4 / 9.8 / 7.3 | 67 / 60 / 62 | 2 / 1 / 1 |
| 11 | grazer / grazer / grazer | 2,693 / 2,908 / 2,872 | 742 / 776 / 961 | 10% / 3% / 5% | 0.04% / 0% / 0.9% | 739 / 1,432 / 1,598 | 11.3 / 14.3 / 21.6 | 32 / 32 / 32 | 1 / 1 / 1 |
| 12 | hunter / grazer / hunter | 2,004 / 2,361 / 2,113 | 347 / 465 / 400 | 34% / 16% / 32% | 47% / 0.1% / 49% | 278 / 874 / 340 | 3.4 / 11.2 / 3.6 | 54 / 72 / 59 | 1 / 1 / 1 |

- **The hunters are the scaling's doing, not the slowdown's.** Hunter worlds: 2 of 4 without the
  law, 0 of 4 under the clock, 3 of 4 at a flat pace (seed 10 turns hunter, which it was not).
- **Half of the extra bodies are the slowdown.** 2,180 on average without the law, 2,338 at the
  flat pace, 2,569 under the clock.
- **The long lives follow the state, not the pace.** Where the flat pace keeps a hunter world the
  mean age of the living stays at 340-459; on seed 11, a grazer world under all three, it reaches
  1,598 (the clock's 1,432, the control's 739).
- **Size: the flat pace moves the masses as much as the clock does** (median 38 and 37 on seeds 10
  and 12, against the clock's 47 and 50 and the control's 41 and 37), and the bodies born heavy
  outlive the bodies born light under all three (1.0-2.2 times at the flat pace, 2.2-3.0 under the
  clock, 1.4-4.3 without either).

## Conclusion

The answers hold under the conditions of these runs (see "What these runs can and cannot say").

1. **The law acts: yes for the lives, no for sorting them by size.** The clock binds (0.78-0.88 of
   a turn a step), lives lengthen (the mean age of the living 278-739 to 874-1,432 on three seeds;
   the 90th percentile of the age at death 580-863 to 1,163-3,835), and wear kills for the first
   time (281-1,837 deaths a log interval against 0.6-534). But bodies born heavy already outlived
   bodies born light without the law (1.4-4.3 times against the clock's 2.2-3.0): the clock
   lengthens lives, it does not sort them by size.
2. **Size pays: no.** The 90th percentile of the mass is above the control's on one seed of four,
   and the flat-pace control moves the masses as much.
3. **Different sizes at once: no.** The diversity number is 1 on all four seeds against 2, 2, 1, 1,
   although up to six lineages hold 5% of the last third: under the clock they are the same body, a
   gut with muscle and no armor.
4. **The world stands: yes.** Winter floors 465-776 against 347-742, with 8-37% more bodies.

**Not kept as the default**; `clock` stays as argument 47. This is a decision about the default
world, not a verdict on the law.

**What these runs can and cannot say.** The answers hang on choices we made: the mass whose clock
is the world's step (16), the exponent (0.25), so that the bodies of this world run at 0.78-0.88
and none is slow enough to be a different kind of animal; e048's world with no brain; four seeds of
100,000 steps. The runs do not say that a time scaling with size is wrong, and they do not say
long-lived bodies are worthless: they say that at this exponent, in this world, the clock buys
lives and bodies, not sizes.

What this changes:

- **A slower body is a cheaper body, and the world fills up.** The upkeep, the intake, the moves
  and the ageing all fall with the pace, so the same food feeds more bodies (2,569 against 2,180)
  and each lives longer. About half of that is the slowdown itself (the flat pace: 2,338).
- **Scaling time by size is a tax on the hunter.** A grazer's income is set by the world's clock -
  the plant grows per step whatever the body does - while a hunter's income is made of its own
  actions, and the heavier a hunter is (armor, mass) the fewer turns it gets. Under the clock no
  winning lineage carries a hard block and hunter worlds vanish (0 of 4); under the same slowdown
  applied to every body alike they come back (3 of 4). This is the first law of the series that
  removes predation by the way it prices time rather than by what it feeds.
- **Long lives are now available.** What the behavior track asked for - a body that lives long
  enough to meet a change itself - exists under this argument (mean age 874-1,432 against
  278-739), at the price of the hunters.
- **Next**: e049's moving rain under the clock, with and without e050's brain: does a body that
  lives four times as long follow the band itself, instead of being followed by births? Open from
  here: why the diversity number falls when the lineages multiply, and whether an exponent that
  reaches further (a world with bodies of mass 256) sorts sizes where 0.25 did not.
- **Compute**: the clock skips the turns of heavy bodies, so a step is cheaper as bodies grow; it
  adds one `powf` per living body per step. The twelve runs took 26 and 25 minutes in two batches
  (eight and four at once on the Mac), plus a check and a pilot of about 10 minutes.
