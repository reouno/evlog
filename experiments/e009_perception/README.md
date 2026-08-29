# e009 Perception: does an eye pay once it can tell prey from threat?

Date: 2026-08-29

## Purpose

Sensor blocks stayed for the first time in e007 (one lineage on 256 patchy for 880,000 steps),
but the eye was not shown to pay: grazers with sensors took in no more food than grazers without,
and two sensor blocks cost 2% of a grazer's intake, cheap enough to ride along. e008 found that
what limits carnivory is access, not the value of a kill: an agent cannot tell who is next to it,
so there is no hunting and no fleeing. Issue #8 asks to let sense decide what a neighbor input
carries. We give the policy inputs that say whether a neighbor can eat you and whether you can eat
it, paid for by sensor blocks, and we knock sense out in the same world to tell an eye that pays
from one that rides along. No flee rule, no hunt rule: only richer inputs.

## Hypothesis

1. **Eyes pay when they can see who.** In mode `who`, agents with sensors are eaten less often per
   capita than agents without (ratio of per-capita predation death rates below 0.8, over the
   second half of the run), or make more kills per capita; and sensor blocks are selected: the
   population mean is above 1 for at least 100,000 steps in at least two of four seeds, against
   one of three seeds in e007's 128 patchy (which `counts` reruns).
2. **e007's eyes were passengers.** In mode `blind` (sense forced to 0 for everyone), sensor
   blocks appear at the same rate as in `counts`: the steps with the mean above 1 and the number
   of sensor lineages are within the seed spread of `counts`. If they are lower in `blind`, the
   distance-2 inputs were paying after all.
3. **Behavior changes.** In `who`, escapes per encounter (escapes / (escapes + kills)) rise and
   predation deaths per birth fall against `counts`, and the `who` inputs change the move in more
   than 10% of the decisions where they are non-zero. Cost: steps per second within 20% of
   `counts`.

## Method

World, bodies, costs, predation, mating, lineages, food law: exactly e007 `128 patchy` (e008 with
`keep` = 0; four islands; the diet columns of e008 in the lineage log). One change, in the policy's
inputs. e007's ten inputs stay: food here, food in four directions (distance 1, plus distance 2
times sense), agents in four directions (same), energy over the split threshold. Mode `who` adds
eight: for each direction, the number of neighbors at distance 1 and 2 that can eat me, and the
number I can eat, each times sense. "Can eat" is the predation rule itself (attack above the
prey's defense, prey mass within the gut, not the same body), without the escape roll. Sense is
sensor blocks / 8 as before, so an agent without sensors sees nothing new, and an agent with two
sensor blocks sees a quarter of it. Mode `blind` forces sense to 0 for everyone: the eight inputs
and the distance-2 inputs are 0, sensor blocks still cost upkeep. Mode `counts` is e007.

The weights of the eight new inputs come from their own random stream, so `counts` is e007/e008
`128 patchy` byte for byte (checked: seed 1, 20,000 steps; snapshots, bodies, lineage rows
identical) and `who` at the same seed has the same laws, the same initial population and the same
e007 weights; only the new inputs differ. The new inputs are computed only for agents with sensors
(in `who`), so the cost is paid where the eye is.

Measured, every 10,000 steps, on top of e008's log: prey killed that had sensors, kills made by an
eater with sensors (with the share of agents carrying sensors, these give per-capita rates with
and without eyes); decisions where a `who` input was non-zero and the share of those where the
move differs from the move with the `who` inputs zeroed (the `who` inputs in use). Escapes and
kills as before. Grazer intake with and without sensors is computed from `agents.csv` as in e007.

Runs: `counts`, `who`, `blind`, seeds 1-4, 1,000,000 steps, 128 patchy; twelve runs at once on one
12-core machine, one thread each.

Run (from repo root): `cargo run --release -p e009_perception -- <steps> <seed> <64|128|256> <uniform|patchy> <counts|who|blind>`
Outputs: `results/<size>_<food>_<mode>_seed<seed>_{log,agents,events,lineages,dist}.csv` and
`_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

## Result

12 runs, 1,000,000 steps each (`results/128_patchy_{counts,who,blind}_seed{1,2,3,4}`), twelve at
once on one 12-core machine, one thread each (1,250-2,460 steps/s median). Numbers are per seed
1 / 2 / 3 / 4. Report: `report.html`.

- Sensor blocks per body, median (max): counts 0.11 (0.7) / 0.00 (0.9) / 0.09 (2.0) / 0.47 (1.4);
  who 0.01 (0.6) / 0.02 (0.3) / 0.06 (2.0) / 0.14 (0.6); blind 0.10 (0.4) / 0.00 (0.0) / 0.12
  (0.6) / 0.07 (0.5). Steps with the mean above 1: counts 0 / 0 / 140k / 20k; who 0 / 0 / 30k /
  0; blind 0 everywhere.
- Sensor lineages (mean at least 1 sensor block for 20,000+ steps): counts 8 / 1 / 25 / 9 (43;
  longest 760,000 steps, lineage 233 seed 4); who 1 / 0 / 12 / 3 (16; longest 377,000); blind
  2 / 0 / 4 / 0 (6; longest 375,000). Fewer in blind than in counts in every seed. Almost all are
  armored grazers (hard 37-44, attack 0) with one or two sensor blocks; two are hunters with one.
- The who inputs are non-zero in 1.3 / 1.3 / 1.2 / 0.2% of the decisions made by agents with
  sensors. Where non-zero, they change the move in 19 / 24 / 24 / 20% of cases (median per
  window). Sensors in use (as e007): 17-20% in counts and who.
- Per-capita rate of being eaten, with eyes over without (second half; only where eyes are at
  least 5% of agents): counts seed 4 (22% with eyes) 1.34; who seed 4 (13%) 0.51; blind seed 3
  (7%) 1.34. Elsewhere eyes are 0-3% of agents and the ratio is noise.
- Grazer intake per digestive block per step, with / without eyes (second half, age 50+, no
  muscle): counts 0.0101 / 0.0108, 0.0148 / 0.0118, 0.0049 / 0.0116, 0.0116 / 0.0105; who 0.0094 /
  0.0112, 0.0094 / 0.0106, 0.0113 / 0.0121, 0.0105 / 0.0098; blind 0.0101 / 0.0095, - / 0.0119,
  0.0078 / 0.0091, 0.0097 / 0.0115. No gain in any mode; blind shows the same spread as the
  others, so the spread is body plan, not sight.
- Escapes per encounter: counts 1.3 / 5.5 / 1.3 / 5.9%; who 2.6 / 2.5 / 1.6 / 6.9%; blind 14.6 /
  9.4 / 1.7 / 3.0% (blind seed 1: a muscular grazer lineage). Predation deaths per birth: counts
  0.32 / 0.31 / 0.44 / 0.31; who 0.37 / 0.27 / 0.47 / 0.25; blind 0.29 / 0.30 / 0.52 / 0.42.
- Who gets eaten (instrumented trial, seed 9, counts, 30,000 steps): the prey is younger than the
  eater, so the eater moved first in that step, in 75% of kills; 15% of prey die at age 0, before
  their first move; 55% at age 2-49.
- The world: population 810-1,260, attack 1.7-6.8, hard 25-41, lineages alive 4-9, meat share
  2.6-4.9%, within the seed spread across the three modes. Carnivore lineages (e008's measure):
  counts 1, who 6, blind 0, all with sensor 0.0-0.1 per body.
- Speed: counts 2,462 / 1,840 / 1,814 / 1,748; who 1,962 / 1,869 / 1,674 / 2,030; blind 1,250 /
  1,963 / 1,245 / 1,654 steps/s (median).
- `counts` seed 1 matches e008 `keep 0` (e007 `128 patchy`) byte for byte over 20,000 steps.

## Conclusion

1. Eyes pay when they can see who: no. With the who inputs, sensor blocks are selected less (16
   sensor lineages against 43, 30,000 steps above a mean of 1 against 160,000), grazers with eyes
   take in no more food, and the one seed with enough eyes to compare shows agents with eyes
   eaten half as often without that lineage spreading.
2. e007's eyes were passengers: partly. The population mean is the same blind as not, but
   lineages with a sensor block are fewer blind in every seed and never reach a mean of 1. The
   distance-2 inputs give a lineage a small rebate that shows in nothing we measure.
3. Behavior changes: partly. The who inputs change one move in five where they are non-zero,
   but they are non-zero once in a hundred decisions; escapes and predation are unchanged; speed
   within 20%.

What this changes:
- Perception is not the lever. A neighbor that can eat you, or that you can eat, is next to an
  agent one step in a hundred: bodies are armored grazers among armored kin (immune, and able to
  bite nobody), so there is nothing to see. Predation is decided by the body plan (and by move
  order: the eater moves first in 75% of kills) before any move is made.
- Every experiment since e005 has hit the same wall from a different side: attack is capped at 24
  by the three front rows, defense goes to 32, armor costs the same per block as gut. e008 could
  not raise meat with a prize; e009 cannot raise it with eyes. The next change is to the wall:
  a bite that can grow beyond 24 (attack from more of the body, or muscle multiplying it) or
  armor that costs more per block, then counts and who again on the same world.
- Keep the who inputs in the code (zero cost where sense is 0) and keep e007's law (counts) as
  the world. Keep the knockout as a tool: it is how an eye is tested.
- Open: whether the who inputs would be used if threats and prey were common; whether move order
  (newborns last) should be randomized, since it decides 75% of kills; the sensor share needed
  for a per-capita comparison is 5%+, which only one seed in four reaches.
