# e046 Plant matter is harder to digest than flesh

Date: 2026-09-11

## Purpose

Every gut digests all it takes, plant or flesh. In e045's connect runs (seeds 9-14, steps
50,000-100,000) the bodies eat 72-84 of plant a step, 17-54 of the flesh of kills and 10-14 of the
dead, and lineages without muscle hold 21-47% of the bodies. The user (2026-09-11): too many bodies
live by just sitting; real plant eaters digest poorly and flesh eaters well, and a kill should last
until the next meal. #49 asks for the matter's law: plant matter yields less than flesh, to every gut.

## Hypothesis

Hunting pays when plant matter yields little and a kill is a big meal (flesh digested whole): a
block of flesh then carries twice the plant it was made of.

1. **The world stands.** Six seeds through five winters (no winter floor under 100 bodies), with
   20-50% fewer bodies than the control (the plant pays half).
2. **More hunter worlds.** At least 5 of 6 seeds settle as a hunter world, against 4 of 6. The
   state is read from the blocks broken per body per step over the second half, which does not
   depend on the yield (e045: 0.045-0.079 in a hunter world, 0.012-0.018 in a grazer world; the
   line at 0.03).
3. **Fewer sitters.** Muscle-free lineages hold fewer of the bodies than in the control, within
   each state.

Against 2 and 3: a kill is worth twice a bite, but with half the bodies a hunter meets fewer prey.
In e045 a body touches another 0.43-0.69 times a step in both states; if the contacts per body fall
with the density, the kill income falls with them and the odds do not move.

## Method

Code: e045 (`experiments/e045_connect`) as `e046_yield`, with `connect` 1 by default and one
argument more, off by default:

- **`plant_yield`** (argument 43): the share of the plant matter a gut takes (the standing plant,
  the fruit, the ground store) that it digests, the same for every gut. The flesh (the dead, a
  broken block) is digested whole. The rest is dung, to the soil of the cell it was taken from
  (e028's dung; the issue's first design point: the soil first, and the runs say whether the world
  stands). Under the digestion axis (`digest` 1, 2; not used here) the axis's plant yield is
  multiplied by it.
- No new log column: the log's `dung` is the plant taken and not digested (under `digest` 0 flesh
  leaves none), so the plant taken is `plant_intake + dung`.
- **Checked**: `plant_yield` 1 is e045's connect run byte for byte (seed 9, the whole run).

**Runs.** e045's season world with `connect` 1, 100,000 steps (five winters), one thread each,
seven at once on the Mac (7 of 12 cores, about 16 minutes):

| run | plant_yield | seeds | question |
|---|---|---|---|
| control (e045's connect runs, already run) | 1 | 9-14 | the baseline |
| check | 1 | 9 | byte for byte with e045 |
| law | 0.5 | 9-14 | does the world stand (1); how many hunter worlds (2); fewer sitters (3) |

`plant_yield` 0.3 only if 0.5 stands (the issue's plan).

Run from the repo root: `bash experiments/e046_yield/run.sh <plant_yield> <threads> <steps> <seeds>`.

**Measures** (over the second half). The blocks broken per body per step (the state) and the
contacts per body per step; per step the plant taken and digested, the flesh of kills, the dead
scavenged, and the kills' share of what is digested and of what is taken; the share of the bodies
in muscle-free lineages (mean muscle under 0.5); bodies, winter floors, births a step; the top
lineage of the last third; the diversity number (#42).

**Compute.** One multiplication per gut cell per step: nothing measurable.

## Result

**The runs.** Seeds 9-14, 100,000 steps, seven runs at once on the Mac (7 of 12 cores): the check
10.5 minutes, the law's runs 16.5-18.5 (see Compute below). `plant_yield` 1 on seed 9 is
e045's connect run byte for byte: every output file identical but the timing column of the log
and the `"plant_yield":1` of the parameter line.

Means over the second half (steps 50,000-100,000); each cell is control / `plant_yield` 0.5:

| seed | state | blocks broken per body per step | kills' share of the digested | of the taken | muscle-free | gut blocks per body | bodies | winter floors, law | top lineage of the last third, law |
|---|---|---|---|---|---|---|---|---|---|
| 9 | hunter / hunter | 0.059 / 0.073 | 35% / 36% | 35% / 23% | 47% / 64% | 11.2 / 16.1 | 2,114 / 1,044 | 150, 177, 125, 206, 206 | 31: 24 cells, no muscle, 22 gut, 8% flesh; 60% |
| 10 | grazer / hunter | 0.018 / 0.048 | 16% / 31% | 16% / 19% | 21% / 40% | 10.2 / 11.8 | 2,089 / 1,292 | 257, 280, 291, 301, 233 | 1: 25 cells, no muscle, 24 gut, 5% flesh; 41% |
| 11 | hunter / grazer | 0.045 / 0.024 | 30% / 17% | 30% / 10% | 32% / 16% | 9.7 / 14.0 | 2,563 / 1,280 | 231, 212, 286, 298, 287 | 377: 14 cells, 3 muscle, 11 gut, 26% flesh; 60% |
| 12 | hunter / hunter | 0.079 / 0.050 | 37% / 28% | 37% / 17% | 24% / 35% | 11.6 / 14.6 | 2,272 / 1,281 | 169, 253, 214, 250, 228 | 487: 14 cells, 7 muscle, 8 gut, 48% flesh; 26% |
| 13 | grazer / hunter | 0.012 / 0.085 | 17% / 36% | 17% / 23% | 21% / 56% | 7.5 / 18.7 | 2,249 / 939 | 157, 188, 144, 156, 174 | 121: 29 cells, no muscle, 25 gut, 7% flesh; 70% |
| 14 | hunter / hunter | 0.053 / 0.067 | 36% / 33% | 36% / 21% | 45% / 34% | 9.6 / 14.1 | 2,185 / 1,147 | 177, 199, 246, 175, 234 | 238: 15 cells, 7 muscle, 7 gut, 63% flesh; 43% |

What the bodies eat (per step: plant taken, plant digested, the flesh of kills, the dead
scavenged) and how they live:

| seed | plant taken | plant digested | kills | dead | contacts per body per step | births a step | mean age |
|---|---|---|---|---|---|---|---|
| 9 | 72 / 90 | 72 / 45 | 46 / 29 | 12 / 5 | 0.48 / 0.49 | 8.5 / 3.9 | 403 / 422 |
| 10 | 77 / 93 | 77 / 46 | 17 / 23 | 11 / 5 | 0.44 / 0.54 | 3.8 / 4.4 | 961 / 474 |
| 11 | 84 / 93 | 84 / 46 | 41 / 11 | 11 / 6 | 0.61 / 0.49 | 10.1 / 2.5 | 473 / 917 |
| 12 | 79 / 91 | 79 / 45 | 54 / 20 | 14 / 5 | 0.69 / 0.56 | 10.7 / 4.0 | 233 / 536 |
| 13 | 73 / 89 | 73 / 44 | 17 / 29 | 13 / 7 | 0.48 / 0.36 | 3.5 / 3.6 | 1,006 / 569 |
| 14 | 74 / 89 | 74 / 44 | 48 / 25 | 10 / 5 | 0.47 / 0.51 | 8.3 / 4.3 | 377 / 425 |

- **The world stands at half.** 1,164 bodies on average against 2,246 (38-58% fewer; seeds 9 and
  13 lose more than half), winter floors 125-233 against 345-590 (51-71% lower). The bodies digest
  73 a step against 126: half of every bite goes back to the soil, and the bodies take 89-93 of
  plant a step against 72-84.
- **The uneaten plant stands as forest.** Trees (cells holding at least 1 of standing matter)
  cover 4,460-5,069 cells against 436-2,569 (27-31% of the world against 3-16%) and hold
  26,800-31,800 of matter against 1,300-14,200; the fruit on the ground is 11-16 against 0.6-6.2.
- **The seed still picks the state.** Hunter worlds on 5 of 6 seeds against 4: seeds 10 and 13
  become hunter worlds, seed 11 a grazer world (0.024 broken per body per step, 17% kills, mean age
  917, 2.5 births a step: the grazer world's marks). e045 swapped two seeds under a law that changed
  nothing about hunting.
- **Within a state the balance holds.** In the hunter worlds the kills are 28-36% of what the bodies
  digest (control 30-37%) and 17-23% of what they take. A body gets as much from kills as before,
  0.015-0.031 a step against 0.016-0.024, and meets others about as often (0.36-0.56 contacts a step
  against 0.44-0.69). What a body digests in all is 0.049-0.085 a step against 0.046-0.065.
- **The sitter grows its gut.** A body takes 2.1-2.6 times the plant it took (0.071-0.095 a step
  against 0.032-0.037), with more gut blocks on all six seeds (11.8-18.7 against 7.5-11.6). On seeds
  9, 10 and 13 the top lineage is a gut of 22-25 blocks on a 7- to 9-wide grid without muscle, beside
  4x4 hunters of 12-15 blocks (70-85% flesh). Muscle-free lineages hold 34-64% of the bodies in the
  hunter worlds against 24-47%, and 16% in seed 11's grazer world against 21% in the control's two.
- Diversity 2-3 in every run (law 2, 2, 2, 2, 3, 2; control 3, 2, 2, 2, 2, 2).

## Conclusion

1. **The world stands: partly.** On all six seeds (lowest floor 125), with 38-58% fewer bodies;
   two seeds lose more than the 50% the hypothesis allowed.
2. **More hunter worlds: partly.** 5 of 6 against 4 of 6, but three seeds swap states and one more
   in six is what the seed alone does. Within a state the kills' share of what is digested does not
   move (28-36% against 30-37% in the hunter worlds).
3. **Fewer sitters: no.** Muscle-free lineages hold more of the bodies in the hunter worlds (34-64%
   against 24-47%), and on three seeds the winner is a big gut without muscle.

**Not kept**: `plant_yield` stays 1; the argument stays in the binary for later combinations.

What this changes:

- **A law that lowers what food yields everywhere acts as a weaker sun.** The crowd sets what a
  bite brings (e038): with half the yield the bodies thin until a gut breaks even again, and a
  grazer lives as it did. A kill is worth what it was (flesh digested whole) and a hunter meets
  others as often, so its income is unchanged too. Fewer bodies of the same kinds.
- **Poor food grows the gut.** A body pays UPKEEP_BODY (0.032 a step, the upkeep of 16 blocks) for
  being one. When a gut block earns less, more of them are needed to carry that cost, and a big gut
  without muscle becomes the cheaper answer: the Jarman-Bell principle of real grazers, out of the
  costs.
- **0.3 was not run** (the issue's plan ran it only if 0.5 stood). The world stands at 0.5, but the
  balance within a state did not move, and the reading above says a lower yield thins the world
  again (floors near 100) with bigger guts still: a run for completeness.
- **Where hunting could pay**: in a world whose places differ, so that the crowd cannot even out
  what a bite brings (#14).
- **Compute**: nothing from the law itself (one multiplication per gut cell), but the world it
  makes is slower: the check ran at 176 steps a second and the law's runs at 92-110, seven at once
  (10.5 minutes against 16.5-18.5). The speed follows the trees (the canopy's claims grow with the
  columns' height): e045's two most wooded seeds (11 and 12, 14-16% of the cells) were its slowest.
- **Next**: #14 (the regions, designed in the issue first, with #38 as its first pilot), then #5.
