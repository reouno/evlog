# e008 Prey worth eating: do carnivores appear once an old body is a prize?

Date: 2026-08-29

## Purpose

No pure carnivore has appeared in any world so far. Meat is 2-4% of all energy eaten while
predation is 30-50% of deaths (e005-e007). The reason is measurable: a kill is worth about the
same whatever the prey, half its energy (about 2) plus 0.02 per block (about 1.3), and three
quarters of the kills are of newborns. A body that has grazed for 800 steps has paid 100 in
upkeep and is worth 3.3 when eaten, the same as one born ten steps ago. Issue #7 asks to make a
grown body worth what it cost, and to watch whether carnivores follow. We change what a kill is
worth and nothing else. We do not add a role.

## Hypothesis

1. **Meat pays.** With the prize growing with the prey's age, the meat share of intake rises
   with `keep` and reaches at least 10% (from 3-4%) at `keep` = 0.3 or above, in every seed.
2. **Carnivores appear.** At least one confirmed lineage whose members got most of their
   lifetime food from prey (meat > plant, mean over the lineage) lives for at least 20,000
   steps, in at least one seed at `keep` = 0.3 or 1.0. Its body has attack above 5 and fewer
   digestive blocks than the grazers around it.
3. **The world stands.** Population within a factor of two of the control (`keep` = 0) and no
   extinction in 1,000,000 steps at every `keep`. At `keep` = 1.0 a kill of an old body is worth
   ten reproductions; we expect booms of kin after such kills, and watch whether they settle.

## Method

World, bodies, costs, predation, policy, mating, lineages, food law: exactly e007 (`128
patchy`: 128x128, four drifting patches, sexual mode D = 6, radius 1). One change, in what the
eater receives when it kills prey `p`:

    gain = 0.5 * p.energy + p.mass * (0.02 + keep * UPKEEP * p.age)

e007 is `keep` = 0. `UPKEEP * p.age` is the upkeep the prey has paid per block over its life
(0.002 per block per step), so `keep` is the share of the prey's lifetime maintenance the eater
recovers. It is not conserved energy (the prey spent it), and that is the point: the body is
treated as stored tissue. The prize at the median age (170) for a 64-block body is +2.2 / +6.5 /
+22 at `keep` 0.1 / 0.3 / 1.0, on top of the 3.3 of e007; at the 90th percentile age (850) it is
+11 / +33 / +109. A grazer takes in about 0.16 per step and pays 0.13 in upkeep.

Measured, every 10,000 steps, on top of e007's log: mean age of the prey killed, mean gain per
kill, share of kills of prey younger than 50 steps, and the share of agents that have taken in
more meat than plants over their life (`meat_majority`). Per lineage (every 1,000 steps) the
mean age, lifetime plant intake and lifetime meat intake of the members, so that a carnivore
lineage can be found as one with meat > plant.

Runs: `keep` 0, 0.1, 0.3, 1.0, seeds 1-3, 1,000,000 steps, 128 patchy; twelve runs at once on
one 12-core machine, one thread each. `keep` = 0 is e007 `128 patchy` byte for byte (checked:
seed 1, 20,000 steps; snapshots, bodies, lineage rows, events identical) and is rerun for the new
columns. 128 is used because the question is about bodies and behavior on an island (the e007
calibration).

Run (from repo root): `cargo run --release -p e008_prey_worth -- <steps> <seed> <64|128|256> <uniform|patchy> <keep>`
Outputs: `results/<size>_<food>_keep<keep>_seed<seed>_{log,agents,events,lineages,dist}.csv` and
`_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

## Result

12 runs, 1,000,000 steps each (`results/128_patchy_keep{0,0.1,0.3,1}_seed{1,2,3}`), twelve at once
on one 12-core machine, one thread each (1,300-3,400 steps/s; 6-9 minutes per run). Numbers are
per seed 1 / 2 / 3. Report: `report.html`.

- Meat share of intake, whole run: keep 0 2.6 / 3.6 / 3.9%; keep 0.1 4.5 / 3.1 / 3.6%; keep 0.3
  5.2 / 3.8 / 3.5%; keep 1 5.1 / 4.7 / 5.2%. Second half at keep 1: 3.5 / 4.3 / 5.1%.
- Energy per kill (median of window means): keep 0 2.6 / 3.4 / 1.9; keep 1 5.3 / 5.4 / 6.2. Kills
  fall as the prize rises: predation deaths per birth 0.32 / 0.31 / 0.44 at keep 0, 0.28 / 0.24 /
  0.24 at keep 1.
- Who gets eaten: prey younger than 50 steps are 76 / 93 / 70% of kills at keep 0 and 94 / 93 /
  89% at keep 1; the mean age of the prey killed is 58 / 22 / 56 at keep 0 and 13 / 15 / 22 at
  keep 1. Old bodies are not better armored (hard blocks 40-48 at every age in `agents.csv`); a
  catchable body next to a predator is eaten within a few dozen steps of appearing, and the ones
  appearing are newborns.
- Carnivore lineages (mean meat > plant over the members, held for at least 20,000 steps): keep 0
  0 / 0 / 1 (lineage 339, 157,000 steps, meat 56%); keep 0.1 1 / 0 / 0 (428,000 steps); keep 0.3
  0 / 0 / 0; keep 1 4 / 2 / 4, longest 279,000 / 417,000 / 340,000 steps, meat 52-89%. Body:
  23-30 hard (24 in the front rows), 18-25 muscle, 15-18 digestive, attack 15-23. Mean age of the
  members 21-100 steps. They come as booms: 100-1,220 agents in a few thousand steps (lineage 207,
  keep 1 seed 2, takes the world at step 990,000: meat intake per window triples, mean attack 3
  to 10), then shrink. Agents fed mostly on meat: median 0.2-0.6% at keep 0, 1.0-1.7% at keep 1,
  spikes to 13 / 5 / 29%.
- The population answers with armor: hard blocks (median) 37 / 38 / 32 at keep 0, 46 / 41 / 42 at
  keep 1 (45 / 45 at keep 0.1 seeds 2-3); attack per body 3.2 / 4.0 / 2.5 to 2.3 / 2.7 / 1.9. At
  keep 1 seed 1, 84% of agents have 46 or more hard blocks, which no attack (at most 24) beats.
  Digestive blocks 13-19 everywhere.
- The world stands: population median 913 / 876 / 1,066 at keep 0, 848 / 828 / 858 at keep 1,
  minimum 468 (keep 1 seed 1, step 10,000), maximum 1,779 (keep 1 seed 3, a boom). No extinction.
  Lineages alive 5-7 at keep 0, 3-8 at keep 1.
- keep 0 reproduces e007 `128 patchy` byte for byte (snapshots, bodies, lineage rows, events;
  seed 1, 20,000 steps).

## Conclusion

1. Meat pays: no. The prize doubles what a kill is worth, and meat stays at 3-5% of intake,
   because kills get fewer and stay on newborns. The bodies the prize is for are the ones nobody
   catches: age at death is set by the predators themselves, so only the uncatchable grow old.
2. Carnivores appear: yes, at keep 1, and they were already there. Ten hunter lineages in three
   seeds at keep 1 (one in the control, one at keep 0.1, none at keep 0.3), living on meat for
   52-89% of their food for up to 430,000 steps, with maximal attack (24 front hard, 20-25 muscle).
   They do not have fewer digestive blocks: the gut is needed for prey mass, so every hunter also
   grazes. A pure carnivore in the diet-class sense (meat only) cannot exist on a patch.
3. The world stands: yes. Population within 20% of the control, booms settle within 20,000 steps.

What this changes:
- The value of a kill is not the lever; access is. Attack is capped at 24 by the body plan while
  defense goes to 32, and an agent cannot see what its neighbor is, so there is no hunting and no
  fleeing. Both are issue #8. keep stays 0 (e007's law); a prize is not adopted. If one is ever
  wanted, keep 0.1-0.3 gives the same picture with smaller booms; at keep 1 a kill of an old body
  creates a hundred units from nothing.
- The lineage log now records diet (mean age, lifetime plant and meat per member). Keep it: a
  carnivore lineage is a thing that can be found and named, and the control had one we had never
  seen.
- The predator-prey cycle exists as hunter booms that armor ends. It needs no prize. It is the
  mechanism `vision.md` counts on for a world that does not settle.
- Open: whether the booms are tamer on 256 (16 islands); whether a bite that can grow beyond 24 or
  armor that costs more is needed once predators can see.
- Next in order: #8 (neighbor inputs carry attack and defense relative to one's own, paid for by
  sensor blocks) with the sensor knockout, on 128 with three seeds.
