# e006 Species: does sex under a compatibility limit make lineages that are born, split, and die?

Date: 2026-08-29

## Purpose

`vision.md`, mechanism 3. e005 gave a world with bodies, predation, and no settling. Here we add the
last mechanism: sexual reproduction that only works between similar genomes, so that a species
boundary is a real thing in the world (gene flow inside, none across) and not a label. Living
genomes are then clustered by the same rule to detect lineages, and the births, splits, and
extinctions of lineages are written to an event log: the first evolution log of the project.

Two questions. Do lineages form, split, and go extinct, or does the world stay one mating pool or a
dust of singletons? And is any of this different from what kinship alone produces in the asexual
world (the control)?

Out of scope: a cost or benefit of sex, mate choice, learning, tuning for beauty.

## Hypothesis

1. **Lineages form.** In the sexual world, the detector finds 2 or more lineages for most of the run
   (more than half of the detections), and one lineage is not the whole population.
2. **Lineages split and die.** The event log has both splits and extinctions, not one lineage that
   lasts forever and not a stream of one-detection lineages: the median lifetime of a lineage is at
   least 10,000 steps.
3. **Sex holds a lineage together.** Gene flow makes a lineage more uniform than an asexual family:
   the share of the population inside the largest lineage is higher in the sexual world than in the
   asexual control, and the event rate (splits plus extinctions per 1,000 steps) is lower.
4. **Cost.** The world stays above 5,000 steps/s with mating and detection on.

## Method

World, bodies, costs, predation, and policy exactly as e005 (64x64 torus, 8x8 bodies from the gene
network, 2 point mutations per child, split at energy 2 + 0.1 * mass). e005's `develop()` with the
batched settle and the parent's body reused (issue #6). The only change is how a child is made.

**Distance between two genomes** = number of genes in one gene list but not in the other (a gene
is its 8 symbols, tag plus product; the symmetric difference of the two lists). A point mutation
inside a gene moves this by 2, a promoter created or destroyed by 1, a mutation outside the genes
by 0. Not the Hamming distance over the 512 symbols: at 2 mutations per child, symbols outside the
genes drift so fast that two members of one family are 50-150 symbols apart within 100,000 steps,
while their gene lists differ by 0-4 (measured below).

**Mating.** When an agent's energy reaches its split threshold, it looks at its own cell and the 4
neighbor cells (Manhattan radius 1; a run with radius 3, 25 cells, is the check on this choice) for a
living agent whose distance is at most **D = 6** (first one found). If there is one, the child's
genome is a one-point crossover: a random cut, the parent's symbols before it, the mate's after it.
If there is none, the child is a copy of the parent, as in e005. Then 2 point mutations, and the
parent gives half its energy, as before. The mate pays nothing. Mode `asexual` skips the search and
is e005 exactly (checked: same log, byte for byte).

**Lineages.** Every 1,000 steps, living agents are grouped by single linkage at distance D: two
agents are in one group if a chain of agents at most D apart connects them, that is, if genes can
flow between them. A group of at least 5 is a candidate. Each agent carries a lineage id inherited
from its mother; a group keeps the id most of its members carry, unless a bigger group already took
it, in which case it gets a new provisional id and its members are relabeled. A provisional id
becomes a **lineage** once its group has existed at 5 detections in a row (5,000 steps); the log then
records a **split** from the id it wanted, or a **birth** if its members carried none. Without this
confirmation, groups that fall apart and rejoin within a few detections (a connecting agent dies)
flood the log: a first version logged one event per 1,000 steps and a median lineage life of one
detection. Members of a group that shrinks below 5 keep their id, so a lineage that recovers is the
same lineage. A lineage whose carriers were all relabeled into another group has **merged** into it
(two pieces that rejoined); one whose carriers all died is **extinct**. When a group carries both a
confirmed id and a provisional one, the confirmed id wins whatever the counts, so that a piece that
rejoins its lineage dissolves into it instead of renaming it. The same detection runs in the asexual
mode, where the groups are kin clusters.

**Choice of D.** Measured on the asexual run (seed 1, every 50,000 steps, all pairs of living
agents): when several families coexist, within-family gene distances are 0-4 and between-family
15-22, with a valley at 5-8. Inside one old family, distances spread up to 11. D = 6 sits in the
valley, and inside an old family it is the place where sex either holds the group together or not.
Seed 1 is also run with D = 3 and D = 10 to see how much the answer depends on it.

Runs: seeds 1-3, both modes, 1,000,000 steps, D = 6, radius 1; seed 1 sexual with D = 3, D = 10,
and radius 3. Four or five runs at a time on one machine. Logged:
- every 10,000 steps: e005's log plus births with a living agent in reach, sexual births, number of
  lineages, share of the population in the largest lineage, share outside any lineage, steps/s;
- every 1,000 steps: one row per lineage (size, mean blocks by kind, mean attack, distinct bodies);
- events (`step,event,lineage,parent,size`);
- every 50,000 steps: histograms of pairwise distance over all living pairs, three measures
  (gene list, Hamming over 512 symbols, body cells that differ);
- snapshots as e005 with the lineage id per agent (every 5,000 steps; every step for 400 steps at
  600,000), and one row per agent every 100,000 steps.

Run (from repo root): `cargo run --release -p e006_species -- <steps> <seed> [sexual|asexual] [D] [radius]`
Outputs: `results/<mode>_d<D>_r<radius>_seed<seed>_{log,agents,events,lineages,dist}.csv` and
`_{long,clip,bodies}.jsonl` (not committed; re-run to regenerate before building the report).

## Result

Seeds 1-3, both modes, 1,000,000 steps, D = 6, radius 1 (`results/{sexual,asexual}_d6_r1_seed*`), plus
seed 1 sexual with D = 3, D = 10, and radius 3. Four or five runs shared the machine. Numbers below
are sexual / asexual per seed unless noted. A generation is short here: 1.5-2.5 births per step for a
population of 220-270, so an agent lives about 100-170 steps on average and 10,000 steps are 60-100
generations.

- Population: median 257 / 264, 220 / 242, 252 / 230. The world is e005's world.
- Mating: 16-23% of children have a mate (23 / 16 / 19% by seed). A living agent is in reach at only
  25-36% of births; when one is, it is compatible 61-63% of the time. Radius 3 (25 cells): a neighbor
  at 83% of births, a mate at 58%.
- Lineages alive (median over detections): 3 / 2, 2 / 2, 2 / 2; two or more at 94 / 86%, 98 / 72%,
  71 / 82% of detections. Largest lineage, median share of the population: 49 / 53%, 74 / 74%,
  76 / 79%; above 90% in 6 / 18%, 0 / 29%, 24 / 23% of the log windows. Agents in no lineage: median
  10 / 12%, 0 / 6%, 3 / 0%.
- Lineages over the run: 98 / 124, 36 / 94, 85 / 61; of these 56 / 54, 13 / 39, 37 / 40 reached 100
  agents. Lifetime from first sighting (5,000 steps of which are the confirmation): median 11,000 /
  12,000, 11,000 / 11,500, 11,000 / 13,000; p90 97,000 / 54,000, 126,000 / 69,000, 85,000 / 82,000;
  longest 306,000 / 263,000, 856,000 / 386,000, 223,000 / 522,000.
- Events per seed (birth / split / merge / extinct): sexual 1 / 97 / 2 / 92, 2 / 34 / 6 / 28,
  1 / 84 / 2 / 80; asexual 1 / 123 / 10 / 111, 1 / 93 / 5 / 87, 1 / 60 / 2 / 57. Events per 1,000
  steps: 0.19 / 0.24, 0.07 / 0.19, 0.17 / 0.12. Almost every lineage is born by splitting; the
  only "birth" events are the first lineage of the run and one or two later ones.
- Lineages have different bodies. Seed 1 sexual, steps 18,000-132,000: lineage 1 (armored grazer,
  hard 28-36, muscle 0, attack 0, 200-280 agents) and lineage 13 (omnivore, hard 20, muscle 19,
  attack 17, 20-60 agents) coexist; 13 lives 114,000 steps and spawns 5 lineages of its own.
- Naming at a split goes to the bigger piece. Seed 1, step 61,000: lineage 1 (255 agents, hard 31)
  splits; the bigger piece (173 agents, hard 1.5) keeps id 1 and dies out by 63,000; the armored
  piece is confirmed as lineage 29 at 65,000 with 230 agents. The log reads "extinct 1, split 29
  from 1"; the armored lineage itself continued.
- Gene distance: 30-49% of all living pairs are within D at a typical moment (mean over the 20
  samples: 30 / 32%, 43 / 43%, 36 / 49%). The histogram is two-humped when several lineages exist
  (within 0-4, between 15-22).
- D: at D = 3, 195 lineages over the run, median 3 alive, 23% of agents in none, 0.39 events per
  1,000 steps; at D = 10, 53 lineages, median 2 alive, the largest above 90% in 38% of windows, 0.10
  events per 1,000 steps. Radius 3 (58% of children with a mate): 96 lineages, largest 64%, 0.19
  events per 1,000 steps, the same picture as radius 1.
- Speed: median 7,600 / 10,600, 15,600 / 10,500, 9,300 / 12,700 steps/s; minimum 3,200 / 6,100,
  6,000 / 6,000, 5,200 / 8,200. Detection is 20-30 ms every 1,000 steps; the rest of the gap to the
  asexual runs is the mate search and the developments it forces (a crossover child is always
  developed).
- Before the confirmation rule, the detector logged one event per 1,000 steps and a median lineage
  life of one detection, in both modes.

## Conclusion

1. Lineages form: yes. Two or more lineages exist for 71-98% of the run, the largest holds half to
   three quarters of the population, and lineages differ in body (an armored lineage and an omnivore
   lineage side by side for 100,000 steps).
2. Lineages split and die: partly. 34-97 splits and 28-92 extinctions per run, a tenth of the
   lineages last 85,000 steps or more, the longest 856,000, and nearly every lineage is born by
   splitting from another. But the median lifetime of 11,000 steps (60-100 generations) clears the
   10,000 mark only because 5,000 of it is the confirmation window: half of the lineages are gone
   within 6,000 steps of being confirmed.
3. Sex holds a lineage together: no. The share of the largest lineage and the event rate are the
   same in the sexual world as in the asexual control (differences within seed-to-seed spread), and
   so are the pair distances. Two reasons, both measured: a mate is found at only 16-23% of births,
   because a neighbor is in reach at 25-36% of them; and when mating happens it is between genomes
   whose gene lists are already within 6 of each other, so the child is close to a copy anyway.
   Radius 3 raises mating to 58% of births and changes nothing else.
4. Cost: partly. 7,600-15,600 steps/s median with four or five runs sharing the machine, but the
   minimum drops to 3,200 in one seed.

What this changes:
- The evolution log exists. Lineage detection by gene distance, with a confirmation window and
  merge / extinct told apart, gives a log a person can read: about one event per 5,000 steps, and
  lineages that last tens of thousands of steps. Keep it, with the lineage-colored viewer.
- Species boundaries in this world come from mutation, drift, and clonal sweeps, not from sex. At 2
  mutations per child the gene lists of separate families are apart within 60-100 generations, and
  the compatibility limit only names what is already there. The mechanism in `vision.md` ("sexual
  reproduction with a compatibility limit makes real species boundaries") is half right: the limit
  defines the boundary; mating adds nothing to it as built.
- Keep mating in the code (it is cheap and does no harm) but do not count on it. If sex is to matter,
  it needs a reason to exist (a cost to asexual reproduction, or an advantage of recombination) and
  mates that are not near-clones; both are questions for later, not tuning for now.
- Lineages are kin groups that turn over in 60-100 generations. For a viewer that is a lot of
  change; whether that is good to watch or too fast is a question for the app phase. The knobs that
  change it are the mutation rate and D, and both are laws, not tuning: D = 3 doubles the event rate,
  D = 10 halves it.
- Open: the naming rule at a split (the bigger piece keeps the name) can hand the name to a piece
  that dies at once. A rule that follows the body instead would read better; not needed yet.
- Open from e005, unchanged: no pure carnivores, sensors unused.
