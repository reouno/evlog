# e028 What a gut digests

Date: 2026-09-04

## Purpose

The user's premise after e025 (#32): guts differ. A cow's takes grass, a cat's takes meat. In
the world so far every gut block takes 0.02 a step from the cell under it, plant, fruit and
dead matter alike, and a broken cell of another body is eaten whole by any body with a gut;
nothing in the material says what a gut is good at, so the split between grazers and hunters
is decided by the tooth alone (e024, e025). This experiment gives the gut material one
heritable number, like e025's density, that says what it digests well, and asks whether the
world then holds a plant lineage and a flesh lineage as distinct winners (#19).

## Hypothesis

1. **The axis is selected.** Without the law the axis is neutral and drifts; with it, the
   bodies leave the middle: the spread of `digest` over bodies grows past the control's, and
   lineages sit near 0 or near 1.
2. **Two kinds of winner.** A lineage on the plant side and one on the flesh side hold places
   in the top lineages of one run for 100,000 steps or more (e024's second winner held
   286,000), against e026's one winner per run.
3. **The world stands** at the same population within 25% of e026's (the middle of the axis
   yields three quarters of everything; the ends the whole of one food).
4. **The tooth follows the gut.** Lineages on the flesh side carry more bite than those on the
   plant side; kills per step are e026's or more.

## Method

Code: e026 (`experiments/e026_weather`, which e027 ran unchanged) as `e028_gut`, with one law
about the gut material and argument 19 `digest` (1: the law; 0: e026 byte for byte, checked on
seed 9 for 20,000 steps: every output file identical but the timing column).

**The law.** The genome expresses a digestion axis d in [0, 1] per body, read from the gene
network like the density (a sigmoid of a sum; the table's column for it draws from its own
random stream, so the bodies, the terrain and the weather are e026's). A gut takes what lies
under it as before; it digests plant matter (the standing plant and the fruit) at 1 - d / 2
and flesh (the dead matter on the ground; a broken cell of another body with its share of
energy and fat) at 1/2 + d / 2. So d 0 digests all of the plant and half of the flesh, d 1 the
reverse, and the middle three quarters of both: no d is best at both, and for a body that eats
a mix the yield is linear in d, so any diet that is not half and half favors an end. What is
taken and not digested is dung: it goes to the soil under the cell it was taken from (the
soil under the eater for a kill), so the ledger holds (checked with `EVLOG_AUDIT=1`: the
world's matter moves by at most 1e-6 a step). The axis touches nothing else: not the tooth,
the eye or the weight. d is inherited with the genome and mutates with it.

That is `digest` 1, the line, the issue's example. `digest` 2 is the sharp curve the issue
allowed for: plant at 1 - sqrt(d) / 2, flesh at 1 - sqrt(1 - d) / 2, the same ends and the
middle at 0.65 of both, so that a gut for both is worse than the mean of the two guts (the
line makes it exactly the mean, so on a diet of half and half every d yields the same). Not
taken: leaving the undigested part of a kill on the ground as flesh for others (a second
rule; it would also turn dead plant matter into flesh for the flesh gut).

**The world.** e026's season world (128x128, matter 8 per cell, the sun a sine of 20,000
steps at amplitude 0.5, the weight and flesh laws, the canopy, the spill, rain on every cell
alike), the world where the eye pays and the winner turns over; the control is e026's four
season runs, which are this code with `digest` 0.

**Runs.** A pilot per curve on flat seed 9, 100,000 steps, all threads (10-12 minutes each)
to see that the world stands and whether the axis moves; then, if it does, the batch: `digest` 1, seeds
1-4, 500,000 steps, one thread each, four at once on the Mac (about 2 hours at e026's rate),
read against e026's season runs (no new control runs: the code path is identical).

Measures: the log's `digest_mean`, `digest_std`, `flesh_guts` (the share of bodies with d
over 1/2) and `dung` (matter taken and not digested, per step); `lineages.csv` `digest` per
lineage, with its bite, guts, plant and meat intake; the winners by #19's rule (holders of the
top place and lineages alive), the kills per step, the population.

Run (from the repo root):

    ./target/release/e028_gut 100000 9 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5 1
    ./target/release/e028_gut 100000 9 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5 2
    bash experiments/e028_gut/run.sh 1 500000 1 2 3 4

Cost of the whole: two pilots (12 cores for 11 minutes each) and the batch (4 cores for 1 hour).

## Result

### The pilots: the line is neutral, the sharp curve selects the plant gut

Seed 9, 100,000 steps; ranges over the log steps (every 10,000). The control is e026's
season pilot on seed 9 (this code with `digest` 0).

| | e026 (control) | the line (`digest` 1) | the sharp curve (`digest` 2) |
|---|---|---|---|
| Bodies | 2,660-4,850 | 1,250-1,920 | 1,090-1,450 |
| Intake a step (the sun is 164) | 235-415 | 80-180 | 57-131 |
| Flesh share of the intake | 69-74% | 43-49% | 33-36% |
| Dung a step | 0 | 27-60 | 30-71 |
| Matter in the soil (of 140k) | 56-103k | 98-112k | 111-117k |
| Dead matter lying | 6.7-9.1k | 3.2-4.9k | 3.2-4.9k |
| d, mean over bodies | - | 0.46-0.52 | 0.42 at 10,000, 0.27-0.29 from 60,000 |
| d, spread (std) | - | 0.07-0.09 | 0.10 at 10,000, 0.04-0.05 from 60,000 |
| Bodies on the flesh side (d over 0.5) | - | 19-65% | 21% at 10,000, 0% from 50,000 |
| Bodies killed a step | 0.9-6.4 | 0.00-0.34 | 0.00-0.08 |
| Bodies with a bite | 0-8% | 0-0.7% | 0-0.3% |
| Bodies with a sensor | 0-1.7% | 0.6-6.1% | 1.2-11.9% (9.7-11.9% from 80,000) |
| Lineages alive; the longest | 2-8; - | 2-9; 92,000 (d 0.49) | 2-9; 89,000 (d 0.28) |

The line does not move the axis: the mean stays at 0.5 and the spread at 0.07, the
longest lineages sit at d 0.43-0.49. The table says why. In the control 70% of the intake is
flesh: the world eats its dead (e024), and the dead lie where the bodies are, so every gut
eats a mix. Under the line the yield of a mix is linear in d with slope (flesh - plant) / 2,
and the intake settles at 43-49% flesh, where the slope is nothing. The sharp curve has a
slope wherever the diet is not half and half, and with plant the larger part it drives d
down: 0.42 to 0.28 in 60,000 steps, the spread halved, no body on the flesh side after
50,000. Nobody goes to the flesh side; the flesh share of the intake falls to a third as the
plant guts digest half of what flesh they take.

Both laws cost the world two thirds of its bodies. Every pass of matter through a middle gut
leaves a quarter in the soil; the dead-matter cycle that fed the control (intake 1.5-2.5
times the sun) decays, the intake halves, and the matter sits in the soil (110k of 140k
against 56-103k), which the plants draw on only at the sun's rate. Kills fall from 0.9-6.4 a
step to under 0.4, the bite is gone, and the sensor comes: 10-12% of the bodies carry one
over the last 20,000 steps of the sharp pilot (control 0.2%). The line is not run further
(the pilot settles it: neutral); the sharp curve goes to the batch, to see whether a flesh
gut appears once the plant guts have fixed and the dead lie undigested.

### The batch: the sharp curve on seeds 1-4, 500,000 steps

Four runs, one thread each, four at once on the Mac: 1 hour. The control is e026's four
season runs (this code with `digest` 0). Medians over the second half unless said.

| | sharp curve, seeds 1-4 | e026 (control), seeds 1-4 |
|---|---|---|
| Bodies; fewest in the run | 1,060-1,410; 820-905 | 2,610-4,780; 2,230-3,050 |
| Flesh share of the intake | 30-34% | 68-73% |
| d, mean at the end; spread | 0.15-0.32; 0.04-0.07 | - |
| Bodies on the flesh side at the end | 0-5% | - |
| Bodies killed a step | 0.00-0.13 | 0.99-3.67 |
| Bodies with a bite | 0-0.1% | 0-45% |
| Muscle per body; speed | 0.02-0.13 (seed 3: 1.15); 0.001-0.005 (0.026) | 1.4-4.3; 0.06-0.12 |
| Bodies with a sensor; steps with a lineage of a sensor per body | 4-50%; 66,000-293,000 | 1.5-19%; 31,000-185,000 |
| Trees; share of the world under a body | 580-1,000; 7-8% | 260-530; 14-22% |
| Lineages alive; the longest | 1-5; 182,000-460,000 | 2-8; 302,000-500,000 |
| Holders of the top place over the second half; longest hold | 1, 2, 27, 1; 32,000-251,000 | 6, 14, 1, 2; 17,000-251,000 |

Every seed goes to the plant gut: the mean of d falls under 0.35 and stays, the flesh side
is a transient (22% once in seed 1, gone within 10,000 steps), the top lineages sit at d
0.09-0.33. Seed 3 walks furthest (0.24 to 0.09) with 27 holders of the top place and the
density falling from 1.0 to 0.6: the plant end is reached by lighter bodies. Seeds 1, 2 and
4 have one winner for 270,000-460,000 steps. With flesh worth half, nobody breaks anybody,
and with nobody to hunt or flee the winners drop their muscle: the bodies in the gallery of
`report.html` are ten to fifteen guts and nothing else, at speed 0.001-0.005. The eye is
e026's, a little more (seed 2 carries a sensor on half its bodies for 200,000 steps). The
world is a lawn with sitting bodies on it: twice the trees, a third of the bodies, 7-8% of
the cells under one.

## Conclusion

1. **The axis is selected: partly.** The line: no (d 0.46-0.52, spread 0.07, neutral on the
   mixed diet the world settles into). The sharp curve: yes, toward the plant gut only, in
   four seeds of four (d 0.15-0.32 at the end).
2. **Two kinds of winner: no.** No flesh lineage in any run; bodies over d 0.5 are 0-5% at
   the end. The winners are e026's in number (1-27 holders), not in kind.
3. **The world stands: no**, not within 25%: a third of the control's bodies (1,060-1,410
   against 2,610-4,780), because what a gut leaves goes to the soil and the cycle of the dead
   that fed e026 (an intake of 1.5-2.5 times the sun) decays.
4. **The tooth follows the gut: no.** The bite is gone and kills fall to 0.00-0.13 a step.

What it changes. The law is not kept (`digest` 0 stays the world; the argument is kept for
the record). #32's answer: a digestion axis is a working material property, selected and
pulling the density with it, but it has nothing to split in a world whose flesh is its own
dead, lying where the bodies are; and its dung starves the world. A flesh gut needs flesh
that lies apart from the plants, which takes a place (#14) or a hunter that carries its
prey; the split between grazers and hunters stays with the tooth and the state of the
world (e024, e025). Open: the axis with a floor above one half or the dung left as dead
matter (both soften the cost, neither gives the flesh gut a place); the axis in a world
with places.
