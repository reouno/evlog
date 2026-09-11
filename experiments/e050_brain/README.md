# e050 A brain that remembers and learns

Date: 2026-09-11

## Purpose

After e049 the user asked for smarter bodies: bodies that look for food and go to it, hunt, flee,
and move to better water. The brain today is a reflex. Ten inputs (five more under thirst) go to
four actions (stay, forward, turn left, turn right) through one weighted sum each, and the largest
wins. The weights are fixed at birth. There is no memory, no learning and no noise, and a body
cannot tell a predator from a neighbor: it sees how many sub-cells other bodies hold, nothing more.

e049 found that the crowd follows a moving rain by births, not by walking. A body that walks with
the band needs to remember where it was or sense where the rain goes. A brain pays only where the
world changes within a life (e009's inputs and e040's pools were read as noise where nothing
changed), so the new brain is tested in e049's band with thirst as well as in e048's world.

Walking with the band pays when the water moves (the band, e049) and the body can remember and
learn (this law): the two conditions together.

## Hypothesis

Written before the runs:

1. **Learning is selected where the world changes within a life.** Half of the random genomes
   start with a learning rate of 0. Over the second half the share of learners is above half on
   at least three of four seeds under band + thirst, and above e048's world's on the same seed on
   at least three.
2. **Memory is kept.** The share of bodies with a sensor (hidden units) over the second half is
   above the old brain's on the same seed (e048's world 18% of the bodies, band + thirst 12%,
   pooled over seeds 9-12) on at least three of four seeds under band + thirst.
3. **The brain is used.** The learned weights change at least 5% of the learners' decisions
   (`learned`), and the hidden state changes at least 5% of the decisions of bodies that have one
   (`memory`), in both worlds.
4. **Bodies walk with the band.** Under band + thirst, `west` over the second half is at least
   twice e049's on the same seed, and deaths by thirst are a smaller share of the deaths than
   e049's (21-29%), on at least three of four seeds.
5. **The world stands.** The lowest winter floor stays above 50 in every run.

## Method

Code: e049 (`experiments/e049_band`) as `e050_brain`, with one law about the body, off by default:

- **`brain`** (argument 46) 1: the policy becomes a brain.
  - **Inputs.** e049's ten inputs, the five of the water (0 without thirst), two for the body
    ahead, and a bias. The body ahead is the nearest other body in the facing direction within the
    eye's range, seen at 1/j like the rest: its size over both sizes, and its share of hard blocks
    less the body's own.
  - **Memory.** Up to 8 hidden units that read the inputs and each other's state before the step
    (tanh). The two sums are each divided by the square root of their count, so that a unit of
    random weights reads its inputs and its past at the same scale (added after the first pilot:
    unscaled, the 18 inputs drowned the past). A body has one hidden unit per sensor block: the
    nerve tissue is the sensor's, and pays its upkeep (0.002 a step) and its weight (0.5). The
    hidden units' weights come from the genome and stay for life.
  - **Learning.** The outputs read the inputs (the reflex, starting at the policy's weights) and
    the hidden units. At each decision, the weights into the output chosen at the last one move by
    eta x the value at their other end x R, within -1..1. The reward of the interval is the body's
    energy balance: what it took in (eaten and killed) less what it paid (upkeep and moves), over
    both (-1 to 1). R is the reward less its running mean (the baseline, kept at the rate beta).
    eta (0 to 0.1) and beta (0 to 1) come from the genome, as max(0, 2 sigmoid - 1): half of the
    random genomes start at 0. A child starts from its genome's weights.
  - **No noise.** The largest output wins, as before. A loss weakens the action that led to it, so
    the next best gets its turn.
  - The genome's brain column (250 weights per gene product) comes from its own random stream, so
    that everything else is e049's.
- **Why the baseline.** A toy of a body grazing its cell bare (the explainer page of this
  experiment): with R the plain balance, the good steps build up the weight of staying and the body
  leaves later than the reflex (42 steps against 40); with the baseline it leaves when the balance
  falls below what it has been (25 steps), the classic answer to when an animal leaves a patch.
- **The start.** Measured with a scratch copy of e049 that stopped after making the first
  bodies (seeds 9-12, 5,795 bodies): random bodies have no sensor (58%) or 8 or more (34%); 1-7
  only 8%. Under the old brain the bodies with a sensor fall to 7-47% by step 5,000, and in the
  second half the ones left carry 1-2 sensors in e048's world (85% of them).
- **Log**: `learners` (the share of the living with eta above 0), `eta`, `base_share`, `beta`,
  `hidden` (hidden units per body), `eyed` (the share with any); from knockouts every 10 steps,
  `learned` (the share of the learners' decisions that differ with their birth weights) and
  `memory` (the share of the decisions of bodies with hidden units that differ with the state
  before the step at 0), `units` (the share of those that differ without the hidden units at all)
  and `sat` (the hidden units' mean |state|, 1 at their bounds); `wchange` (the mean distance of
  the learners' weights from their birth weights). `agents.csv` gets `hidden`, `eta`, `beta`, `wchange`.
- **Checked**: `brain` 0 repeats e049's band + thirst run on seed 9 in the first 20,000 steps of
  every CSV but the new columns and the timing column. A unit test: with no hidden units and
  nothing ahead the brain decides as the policy does; the hidden units read the state before the
  step; learning moves only the weights into the chosen output and stops at 1.

**Runs.** e049's world (e048's season world under the motor), one thread each unless said:

| run | brain | band, thirst | seeds, steps | question |
|---|---|---|---|---|
| controls (e048's motor runs, e049's band + thirst batch, already run) | 0 | 0, 0 and 25, 0.005 | 9-12, 100,000 | the old brain |
| check, 5 threads | 0 | 25, 0.005 | 9, 20,000 | byte for byte with e049 |
| pilot, 5 threads | 1 | 25, 0.005 | 9, 20,000 | does the world stand; are learners and eyes kept past the start; the cost |
| brain | 1 | 0, 0 | 9-12, 100,000 | (1)-(3), (5) in e048's world |
| brain + band + thirst | 1 | 25, 0.005 | 9-12, 100,000 | (1)-(5) |

Four seeds a condition, as e049. Run from the repo root:
`bash experiments/e050_brain/run.sh <brain> <band> <thirst> <threads> <steps> <seeds>`.

**Measures** (over the second half): `learners`, `eta`, `base_share`, `eyed`, `hidden`, `learned`,
`memory`, `wchange`; `west`, `in_band`, the drift of the bodies aged 1,000 steps or more, `moved`;
bodies, winter floors, the kills' share of the intake, deaths by hunger and by thirst; the winners
of the last third; diversity (#42).

**Compute.** The brain costs about 350 multiply-adds per body per step (the hidden units 18 x 8 +
8 x 8, the outputs 26 x 4, learning 26), the knockouts three more decisions every 10 steps; the
pilot measures it against e049's steps per second. The batch: 8 of the Mac's 12 cores for about 35
minutes.

## Result

**Check.** `brain` 0 on seed 9 under band 25 + thirst 0.005 for 20,000 steps is e049's run: every row of
every CSV identical but the new columns and `steps_per_sec`; the long and bodies frames a prefix of
e049's. Checked twice (before and after the scaling).

**Pilots.** Seed 9, band 25 + thirst 0.005, 20,000 steps, 5 threads (log rows at 10,000 and 20,000).
The old brain is e049's run on the same seed.

| run | bodies | learners | with a sensor | learned | memory | units | sat |
|---|---|---|---|---|---|---|---|
| old brain (e049) | 944, 554 | - | 0.8%, 2.7% | - | - | - | - |
| pilot 1, unscaled | 650, 655 | 85%, 34% | 41%, 28% | 53%, 49% | 2.0%, 1.5% | - | - |
| pilot 2, scaled | 824, 933 | 5%, 10% | 0.2%, 1.9% | 50%, 32% | 4.0%, 1.7% | 16%, 6% | 0.75, 0.86 |

- Pilot 1 kept sensors and learners, but the carried state changed 2% of the decisions: the units'
  sum of 18 inputs drowned their past. The scaling was added; pilot 2 lost both sensors and learners
  on the same seed. One seed each: the lineage that won the start differs, and the batch was the test.
- Cost: the brain runs 46-72 steps a second against 49-58 for the check running beside it (5
  threads each): within the noise of the population.

**Batch.** Seeds 9-12, 100,000 steps, eight runs at once on the Mac (8 of 12 cores), 33 minutes.
Means over the second half (steps 50,000-100,000); pairs are the old brain / the brain on the same
world and seed. The old brain's runs are e048's motor runs and e049's band + thirst batch.

| seed | world | learners | learned | with a sensor | memory | walking west | thirst's share | bodies | lowest floor | kills' share | diversity |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | e048's | 7% | 31% | 2% / 5% | 0.7% | - | - | 1,937 / 2,047 | 422 / 494 | 32% / 34% | 2 / 1 |
| 9 | band + thirst | 8% | 26% | 6% / 1% | 1.5% | 0.010 / 0.013 | 21% / 22% | 879 / 926 | 82 / 86 | 29% / 21% | 1 / 1 |
| 10 | e048's | 31% | 50% | 72% / 8% | 2.6% | - | - | 2,085 / 2,199 | 558 / 520 | 4% / 26% | 2 / 2 |
| 10 | band + thirst | 8% | 45% | 20% / 10% | 1.4% | 0.008 / 0.011 | 25% / 25% | 714 / 861 | 89 / 107 | 28% / 27% | 2 / 1 |
| 11 | e048's | 95% | 53% | 4% / 2% | 5.2% | - | - | 2,693 / 2,620 | 742 / 220 | 10% / 27% | 1 / 2 |
| 11 | band + thirst | 1% | 30% | 42% / 8% | 0.7% | 0.012 / 0.012 | 29% / 23% | 694 / 943 | died / 37 | 30% / 26% | 2 / 1 |
| 12 | e048's | 59% | 62% | 3% / 2% | 0.6% | - | - | 2,004 / 2,473 | 347 / 304 | 34% / 24% | 1 / 2 |
| 12 | band + thirst | 27% | 41% | 3% / 9% | 2.6% | 0.008 / 0.008 | 23% / 29% | 864 / 616 | 25 / 1 | 30% / 30% | 1 / 2 |

- **Learning is used, and follows the winner.** By step 10,000 learners are above half on six
  runs of eight (65-99%; half of the random genomes learn). After that the share follows the lineage
  that wins: under band + thirst it falls to 0-15% by step 100,000 on every seed; in e048's world it
  stays at 58-96% on seeds 11 and 12 and falls to 6-18% on 9 and 10. Where it runs, 26-62% of the
  learners' decisions differ from their birth weights (weights 0.03-0.33 away, mean).
- **The learners are the fast muscle blocks.** In e048's world seeds 11 and 12 end with two winners
  each: a 4x4 block of muscle with its gut at one end that learns (eta 0.05 and 0.09, speed
  0.30-0.32) and a gut-heavy sitter that does not (eta 0.009 and 0.0001; speed 0.19-0.23). The winners under
  band + thirst do not learn (lineage 303 of seed 10: 1% of its bodies).
- **Memory is hardly used.** Sensors are not kept above the old brain's (1-10% under band + thirst,
  2-8% in e048's world; seed 10 of e048's world lost its crowd of eyes, 72% to 8%). The carried state
  changes 0.6-5.2% of the decisions of bodies with units, removing the units 3-17%; the units' mean
  |state| is 0.49-0.62 (e048's world) and 0.83-0.89 (band + thirst).
- **No walking with the band.** Walking west 0.008-0.013 sub-cells a step (old brain 0.008-0.012);
  bodies aged 1,000 steps or more drift west at 0.022-0.034 cells a step (old brain 0.020-0.028);
  deaths by thirst 22-29% of the deaths (21-29%).
- **The world.** Bodies about the old brain's. In e048's world the two grazer seeds turn to hunting
  (kills 4% to 26% and 10% to 27% of the intake; hunter worlds 2 of 4 by blocks broken, as before)
  and bodies are faster (speed 0.25-0.30 against 0.16-0.25). Under band + thirst the winters reach 37
  and 1 body (seeds 11, 12); no world dies (e049: seed 11 died). Diversity 1-2, as before.

## Conclusion

1. **Learning is selected where the world changes within a life: no.** Under band + thirst learners
   end at 1-27%, below half on every seed and below e048's world on three.
2. **Memory is kept: no.** Sensors above the old brain's on one seed of four.
3. **The brain is used: partly.** Learning changes 26-62% of the learners' decisions; the carried
   state 0.6-5.2%, 5% or more on one run of eight.
4. **Bodies walk with the band: no.** Walking west 0.98-1.35 times the old brain's; thirst's share
   lower on one seed.
5. **The world stands: no.** Two winters under band + thirst fall to 37 and 1 body (none dies).

**Not kept as the default**; it stays as the argument `brain` (46), to combine with a law that gives
it something to learn.

What this changes:

- **A brain alone gives no motive to move.** Learning works (it rewrites a quarter to three fifths
  of a learner's decisions), but a step's energy balance says little in this world: a sitter's food
  regrows under it, and the band's water decides who dies of thirst, which the reward does not
  count. Where it is kept, it rides on the fast bodies, not on the sitters.
- **Memory needs something slow to remember.** The units are set by the present inputs; the past
  changes a few percent of decisions even with the sums scaled.
- **Next**: #54, a place that gets worse the longer a body stays (e041's `stock` first), with the
  brain on and off: the case the toy illustrated, where leaving a place in decline pays and the
  baseline makes a learner leave. Open: thirst or damage in the reward; a nerve block that is not
  also an eye.
- **Compute**: no measurable cost at this population; the batch took 33 minutes (e049's: 29).
