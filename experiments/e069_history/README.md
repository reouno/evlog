# e069: life history from the genome (foundation stage C, seventh step, #83)

Date: 2026-09-15

## Purpose

Principle 2: a trait should come out of blocks and values the genome expresses, which a child inherits
with variation, so that what a body can become stays open. Three values that decide how a body lives
are still constants we wrote, the same for every body whatever its shape or place: the energy at which
it breeds (2 + 0.1 per unit of mass), the share of its energy a child gets (half), and the fat its flesh
holds (5 per unit of mass).

e067 and e068 found each large lineage holding an open, small form in the water and a closed, larger
form on land, and counted the water forms as kinds of living. Those forms can part in shape but not in
how they breed or store, because we fixed that. This step reads the three values from the genome, with
no law changed (agreed on #83).

## Hypothesis

Written before the runs. The conditions are named together: **a life history can pay differently in
the water and on land when the media already hold different forms and each has its own food.** Both
hold in e067's world at breath 0.01: the water's bodies are open and small (23-25 blocks) and the land's
closed and larger (34), and the land eats grass, the surface algae, the bottom what sinks (e065).

1. **The media part in life history.** Inside groups of one lineage and one side of density 1 with
   grown bodies both on land and in the water, the water's median of at least one of the three values
   differs from the land's by 15% or more (weighted by the groups' grown bodies), and by more than the
   largest of five shuffles of the medium inside the groups.
2. **The store runs to its ceiling.** Fat costs nothing to hold here: it adds no mass and no upkeep,
   and only a breaker or death takes it. So the grown bodies' median store is 8 or more (x1.6) in the
   second half.
3. **The world keeps its kinds.** Kinds by birth form held at every census of the second half (e068's
   count): 3 or more (e067 at breath 0.01: 4).

No line is set for the breeding energy or the share. The world is jammed (47% of moves blocked, 39% of
children without room, e067): that could favour fewer children with more energy, or more children that
cost less. It is measured, not predicted.

Decision rule, set before the runs: the values are kept in the genome for stage C if the world stands
through 100,000 steps and hypothesis 3 holds. They are kept for principle 2's reason, not for a gain. A
value whose median sits within 10% of an end of its range names a missing price. That price is the next
step, not a wider range.

## Method

Code: `experiments/e069_history`, e067's crate with `breath = 0.01` as its default and one parameter,
`history` (0: e067 at breath 0.01).

- **The values** (`body.rs`, `develop_genes`). Three new columns of the law table, each drawn from its
  own stream, are read from the run without position as the density is: a value is its centre times
  2^(2 sigmoid(s) - 1), so x0.5 to x2. The energy to breed per unit of mass has centre 0.1 (a body breeds
  at 2 + that times its mass), the child's share centre 0.5, and the fat per unit of mass centre 5.
- **Breeding** (`main.rs`). The parent gives the child its share of its energy and pays for the child's
  blocks from what it keeps, as before. With a share near 1 the parent cannot pay, and the child is not
  made: what it was given lies down, as for a child without room.
- **What stays.** The mate distance (6 genes; lineage detection uses the same rule) and the mutation
  rate (2 in 512 per base). What a block is made of, upkeep and wear stay laws of the world. The body's
  energy input is read against its own threshold.
- **The start.** Random genomes under seed 9's law table hold values near today's constants: over 5,000
  of them each value's 10th-90th percentile is x0.81-x1.25 of its constant, and none lies within 10% of
  an end of the range (the density reads the same; `start_spread`, an ignored test, prints it). A value
  far from its constant later is not the start's spread.
- **What else is logged.** `agents.csv` gets `breed`, `share`, `store` and `kids` (children placed);
  `log.csv` the three values' means by medium and `fat_fill`, the mean fat over the body's store.

Checks: the tests pass (off, every body holds the constants and its threshold is bit-equal to 2 + 0.1 x
mass; on, each value lies within its range, differs between genomes and follows the gene list, and the
body's blocks do not change; matter is conserved with the values on). With `history = 0` the first
10,000 steps must equal e067's run at breath 0.01 exactly: every column of e067's log but the wall times,
every body of the census at step 10,000, every lineage row and every event.

**Runs**, from the repo root, one core each:

- the pilot: c1225, seed of life 9, 100,000 steps, `history = 1`
  (`bash experiments/e069_history/run.sh c1225 100000 9 history history=1`);
- the check: `history = 0`, 10,000 steps (`run.sh c1225 10000 9 check`).

Control: e067's run at breath 0.01 (`experiments/e067_breath/results/c1225_life9_breath0.01_*`), the same
world, seed and laws with the values held at the constants. It is reused, not run again.

Cost, before the runs: 2 cores, about 45 minutes for the pilot (e067's took 42) and 7 for the check. The
change adds three column reads per new gene list at development, a few operations per gene, and nothing
per step.

Read, second half of each run: the three values by medium, over time from the start's spread; the water
against the land inside lineage groups, with the shuffle; kinds by birth form with e068's `kinds.py`
(forms, held kinds, the shuffled counts, the count by lineage) and each kind's values; deaths by cause,
bodies, children placed per grown body, fat's fill, moves blocked and children without room.

Wall time: the pilot 28 minutes (1,706 s) and the check 5 minutes (316 s), one core each, both at once.
Analysis: `uv run python experiments/e069_history/history.py` (a few seconds), then `report.py`.

## Result

**The checks.** The tests pass. With `history = 0` the first 10,000 steps equal e067's run at breath 0.01 in
all 125 of e067's log columns but the wall times, in every body of the census at step 10,000 (9,154 bodies,
48 columns), in every lineage row (85) and in every event (45). The check ran in 316 s (e067's in 424 s, on a
slower night). Matter drifts by 4e-14 at most in the pilot.

Second half of each run (steps 50,000-100,000), c1225, seed 9, s = 1/16, dry air 0.004, breath 0.01.

| | e067 (constants) | e069 (from the genome) |
|---|---|---|
| bodies: mean (lowest-highest) | 8,073 (6,900-9,628) | 7,772 (6,595-10,137) |
| on land / at the surface / on the bottom | 36% / 37% / 27% | 46% / 32% / 23% |
| grown bodies a census; of them on land | 2,862; 779 | 3,171; 1,278 |
| energy to breed per unit of mass, grown: median (10-90%) | 0.1 | 0.099 (0.087-0.122) |
| child's share | 0.5 | 0.48 (0.39-0.61) |
| fat per unit of mass | 5 | 5.97 (4.87-7.93) |
| the three by medium, land / surface / bottom | - | 0.104 / 0.098 / 0.105; 0.48 / 0.48 / 0.45; 6.16 / 5.97 / 6.15 |
| fat over the store, grown: land / surface / bottom | 0.06 / 0.11 / 0.10 | 0.05 / 0.11 / 0.12 |
| water over land inside lineage groups: breed, share, store (shuffled max) | - | 2.4%, 3.3%, 3.2% (0.6%, 0.7%, 0.7%) |
| kinds by birth form: mean (lowest-highest); held at every census | 6.2 (5-8); 4 | 4.2 (4-5); 2 |
| the same with the medium shuffled; with all shuffled | 5.1, held 3; 4.6, held 1.4 | 4.0, held 2; 3.8, held 1.0 |
| kinds per lineage (e060); forms | 2.5; 351 | 2.0; 362 |
| lineages alive (top lineage's share) | 14.8 (43%) | 13.7 (56%) |
| births per body per 1,000 steps; median age at death | 3.74; 160 | 3.43; 167 |
| deaths: hunger / thirst / broken / suffocation | 66% / 27% / 5% / 1.5% | 60% / 35% / 4% / 1.0% |
| moves blocked; children with no room | 47%; 39% | 52%; 50% |
| kills' share of intake | 12% | 9% |
| a step on one core; per body | 20.25 ms; 2.25 µs (the machine 1.47x slower, e067) | 14.50 ms; 1.66 µs |

**The values barely move.** At step 10,000 the bodies' medians are 0.106, 0.49 and 5.55; over the second
half the grown bodies' are 0.099, 0.48 and 5.97. The grown bodies' spread of the breeding energy and the
share is the start's (x0.87-1.22 and x0.79-1.21 of the constants, against x0.86-1.25 and x0.81-1.21 for
random genomes). The store rose 11% by step 10,000, while the start's 17,000 bodies starved to 11,000, and
8% more after. In both runs the grown bodies' fat fills 5-12% of their store: a larger store is rarely used.

**Between lineages, not within.** Dense bodies (density 1.5 or more) on land, 3,858 grown bodies over the
censuses in a few lineages, hold a median store of 7.8, against 5.9 for the light bodies on land and 6.0 in
the water. Lineage 2295 (93% on land, density 2) holds 8.6; lineage 1498 (all on land, density 2) 8.0, with
a share of 0.29 and a breeding energy of 0.143. Inside the 17 lineage groups with 20 grown bodies both on
land and in the water (74% of the grown bodies), the water's medians differ from the land's by 2-3%. The
water's light bodies have placed 3.4 children against 2.4 on land, at median ages 739 and 540: they breed
more often, at the same values.

**One lineage in every medium.** Lineage 957 holds 52% of the grown bodies (23% on land, 49% at the surface,
29% on the bottom) with a breeding energy and a share within 5% of the constants (0.098, 0.48) and the
population's store (5.97). Its roaming form (a kind of
50% of the grown bodies, 59 forms) and its sitting form (15%) are the two held kinds, both at the shore;
e067's held kinds at the surface and on the bottom, lineage 908's water forms, have no counterpart. Two
dense land kinds reach 5% in five of the six censuses: plant eaters that stay (11%, 108 forms, store 6.4)
and mixed eaters that stay (8%, 36 forms, store 7.6, kills 31% of their intake). With the medium shuffled
the count is 4.0 against 4.2: the forms add no kinds by medium (e067 1.1).

1. **The media part in life history: no.** Inside lineage groups the water's medians differ from the land's
   by 2.4%, 3.3% and 3.2% (the line was 15%), above the largest shuffle (0.6-0.7%).
2. **The store runs to its ceiling: no.** The grown bodies' median store is 5.97, x1.19 (the line was 8).
3. **The world keeps its kinds: no.** 2 kinds held at every census (the line was 3; e067 4).

The world stood (7,623 bodies at step 100,000). No value's median lies within 10% of an end of its range;
the dense land lineages' store, 8.0-8.6, is the closest.

## Conclusion

**Not kept as stage C's default for now**, by the rule set before the run: the world stood, but 2 kinds were
held at every census, under the line of 3. The rule guarded against a loss of kinds; the run does not show
that the values caused it.

**The values barely moved and did not part the media.** Over 100,000 steps selection moved the store 19% and
left the breeding energy and the share at the start's spread. In this world the crowd limits a life before
these values do: half the children find no room, and fat fills a tenth of a store. Inside lineages the water
and the land live alike (2-3%); only the dense land lineages hold more fat.

**The kinds fell with a different winner.** Reading the values from the genome changed every body at the
start and so the whole course of the run: lineage 957 took 52% of the grown bodies with the constants'
breeding energy and share and the population's store, and its water forms stayed shore kinds. One seed cannot separate that from an effect of the values,
and stage C has run one seed at every step so far.

These answers hold for this world and these choices: c1225 only, seed 9, 100,000 steps, s = 1/16, dry air at
0.004, breath at 0.01, ranges x0.5-x2 around the constants, fat with no weight and no upkeep, the mate
distance at 6 genes, mutation at 2 in 512, and e068's census. Not shown: other seeds and c1236, longer runs,
a price on fat, and the mate distance and the mutation rate from the genome.

Next, proposed on #83 (not yet agreed): (a) the same pair, `history` 0 and 1, on seeds 10 and 11 for 100,000
steps (4 runs, 4 local cores for about 30 minutes): whether reading the values loses kinds, and how far e067's
4 held kinds spread over seeds (stage C's pass line asks for 4 seeds of 6); (b) #84, senses from sensor
blocks, with the values kept constant; (c) a price on fat (weight or upkeep). Recommended: (a), then (b).
