# e074: the invasion test (stage C's twelfth step, #72)

Date: 2026-09-16

## Purpose

Every experiment of the series asks two questions in one run: **can this world hold two ways of
living** (ecology) and **will evolution find them from a random start** (evolution). The hunter/grazer
seed lottery of e024, e045 and e055 is the symptom, and e060 found it in 12 of 21 pairs. e010's teeth
were worth ten to one and appeared once in twelve million births: a reachability answer that read like
an ecological one.

Ecology's test of the first question is **mutual invasion while rare**: two ways of living coexist
when each can grow from rare in a world the other holds. #72 asks for it, and until e073 there was
nothing to attempt it with, because stage C's worlds held one way of living on the land. e073's kept
law (`wood_yield` 3e-5) gave the land a browser with a tooth that takes a quarter of its food from
the crowns, beside the shore's grazer. This tests that pair.

## The instruments (no law is added)

`main.rs`, three parameters and two files; with none of them a run is e073's kept run exactly.

- **The genomes of a census** (`genomes`): at the last census every body's genome goes to
  `<prefix>_genomes.csv` with its lineage and the medium it stood in.
- **A world seeded from a pool** (`EVLOG_POOL`, `seed_n`): the start draws `seed_n` genomes from the
  pool instead of making random ones, and places each where its donor stood. A pool of the community
  with one kind's forms taken out is *a world held by the others*.
- **An injection** (`EVLOG_INJECT`, `inject_at`, `inject_n`, `inject_seed`): at `inject_at`,
  `inject_n` bodies of each pool are put in at free spots of their donor's medium, marked with the
  pool they came from. Every descendant carries the mark, so a line is followed whatever the lineage
  detector does with it, and the draw and the placement run on a stream of their own. **Two pools go
  in at once**, so the invader and the resident's own genomes meet the same crowd, the same weather
  and the same luck: the neutral control is beside the test in one world, not in another run. The
  matter the bodies bring is added to the ledger the audit reads.

`pick.py` names the two kinds of a donor run and writes four pools: `A` (the grazer), `B` (the
browser), and the community without each **way of living** (`minusA`, `minusB`). A way, not a kind:
in every seed several forms browse (11 of 64 forms on seed 9, 40 of 118 on seed 10), so a world that
keeps one of them is not a world without browsing.

## Hypothesis

Written before the runs, with the conditions named together (#87): **the browse is a second axis on
the land, so the browser and the grazer coexist by it - each grows from rare (A) in a world the other
holds (B), above what the resident's own genomes do in the same place.**

1. **Mutual invasion.** In both directions, on at least 2 of the 3 seeds, the invading line is larger
   over the last 5,000 steps than the control line beside it (the resident's own genomes, injected the
   same way into the same world) and is still in the world at step 40,000.
2. **The invader keeps its way.** At the last census the marked bodies of a browser injection take a
   fifth or more of their food from wood, and those of a grazer injection less than a tenth. A
   line that grew as something else is not the kind invading.
3. **The world stands.** Matter is conserved (the injected matter in the ledger), bodies live in all
   three media, and the seeded world holds in the population band of e073's kept runs.
4. **Reachability, measured, not a pass line.** Whether the kind taken out comes back on its own out
   of the resident genomes, at the injection step and at the end, counted over the unmarked bodies.

## Method

Code: `experiments/e074_invade`, e073's crate with the instruments above. Tests: a pool taken from a
run seeds a new world, every body of it out of the pool and in the medium its donor stood in; an
injected body is marked, its children carry the mark, and matter is conserved with the injected matter
in the ledger. **The check**: a run with no pool must equal e073's kept run for seed 9 over its first
10,000 steps in every shared column of the log, in every body of the census at 10,000, in every
lineage row and in every event (`check.py`).

**The donor runs** (3 runs, seeds 9-11, 100,000 steps): e073's kept world with `genomes=1`. They are
e073's ladder runs re-run, so the check above is what says they hold.

    (nohup bash experiments/e074_invade/run.sh c1225 100000 9 donor genomes=1 &)

**The pools** (`pick.py`, no runs). At the last census of each donor run, of the kinds holding e060's
5% of the grown bodies:

- **B, the browser**: the land kind with the largest share of its food from the crowns' yield, which
  must be a fifth or more (35%, 36% and 26% on seeds 9-11; a tooth, and it roams);
- **A, the grazer**: the largest kind of the land or the shore with no tooth and under a tenth of its
  food from wood (3%, 1% and 0%).

The seeded worlds take out a whole way of living, form by form:

- **`minusB`**, a land of grass eaters: every form that takes a tenth or more of its food from wood
  is left out (1,626, 1,422 and 1,806 genomes remain of 2,527, 2,499 and 2,819);
- **`minusA`**, a land of browsers: every form of the land or the shore that does not is left out
  (1,180, 1,596 and 1,914 remain). The water's forms stay in both: neither kind lives there.

**The invasion runs** (12 runs, seeds 9-11, 40,000 steps): 2 worlds x 2 draws of the injection a seed.
Each world is seeded with 8,000 genomes (e073's kept runs hold 7,806 on average) and settles for
10,000 steps; at step 10,000 **both** lines go in, a hundred bodies each (1.2% of the world apiece,
one to a thousand land cells), and are followed for 30,000 steps, about a hundred lives.

| run | seeded with | mark 1 (the grazer's genomes) | mark 2 (the browser's) |
|---|---|---|---|
| `mB_s1`, `mB_s2` | the community without the browser | the neutral control | **the invader** |
| `mA_s1`, `mA_s2` | the community without the grazer | **the invader** | the neutral control |

The two draws (`inject_seed` 1 and 2) are two independent founder groups in the same world, since a
line of a hundred in eight thousand can be lost to luck alone.

Read with `invade.py`: the marked line's count over the run, its way of living at the census, the
kinds of the resident world at each census, and the world's own numbers.

**Round two, added after the first twelve runs** (the rule of the house: add runs when the first
result is unclear). The `minus` worlds were meant to hold one way of living and did not - both ways
were back before the injection - and the twelve runs split 5 wins, 3 losses and 4 draws. So #72's own
wording was run as well: a world seeded with **one kind alone** (`only`), 12 more runs, the same 2
draws x 3 seeds, at the same steps.

    bash experiments/e074_invade/batch.sh 40000 minus 9 10   # then 11
    bash experiments/e074_invade/batch.sh 40000 only 9 10    # then 11

**Cost.** Stated before the runs: 3 donor runs of 100,000 steps on 3 cores (~50 minutes) and 12
invasion runs of 40,000 steps on 11 cores (~35 minutes), about 6 core-hours. What it came to: the
donors took 31-36 minutes each, a 12,000-step pilot checked that a seeded world stands, and the
invasion runs were 24, in four waves of 8 and 4, 15-19 minutes a wave. About 11 core-hours on the Mac
over two hours, nothing on the Ubuntu box.

## Result

**The checks.** A run with no pool equals e073's kept run for seed 9 over 10,000 steps in all 163
shared log columns, in every body of the census (7,624), in every lineage row and in every event; and
the three donor runs equal e073's ladder runs over the whole 100,000 steps on seeds 9-11. Matter
drifts by at most 5.0e-14 in the 24 invasion runs.

**The kinds** (at the donor runs' last census, 2,527 / 2,499 / 2,819 grown bodies):

| seed | the browser (B) | the grazer (A) |
|---|---|---|
| 9 | plant/tooth/roams/land, 635 bodies, wood 35%, a tooth in 98% | plant/no tooth/stays/shore, 644, wood 3%, a tooth in 5.0% |
| 10 | plant/tooth/roams/land, 354, wood 36%, tooth 93% | plant/no tooth/stays/shore, 529, wood 1%, tooth 5.3% |
| 11 | plant/tooth/roams/land, 219, wood 26%, tooth 78% | plant/no tooth/stays/shore, 230, wood 0%, tooth 3.9% |

### 1. A world cannot be held at one way of living: the other is back in 2,000-4,000 steps

The seeded worlds were built to hold one way. None of them did. Before a single body was injected:

| world | seeded with | the browse pays half the donor's share at step | browse of all food at 10,000 | bodies with a tooth, 1,000 -> 10,000 | living by wood at 10,000 |
|---|---|---|---|---|---|
| `minusB` | no form that browses | 2,000-3,000 | 3.0-3.7% | 0.10 -> 0.19 | 23.1% |
| `minusA` | no land or shore grass eater | 2,000 | 2.4-3.7% | 0.53 -> 0.24 | 24.2% |
| `oA` | the grazer kind alone | 3,000-4,000 | 2.8-4.2% | 0.05 -> 0.22 | 23.9% |
| `oB` | the browser kind alone | 2,000 | 2.6-3.2% | 0.57 -> 0.26 | 25.3% |

e073's kept runs eat 3.4% of their food as browse and hold about a quarter of their grown bodies
living by wood. **Every world is back at both numbers by step 10,000**, the grazer's world included,
and the land of the browser's world is 48% grass eaters by then (53% in the grazer's own). The return
is 7-13 lives: a body lives about 300 steps.

It is a return out of standing variation, not an invention. The grazer kind carries a tooth in 3.9-5.3%
of its bodies (the browser in 78-98%), so a world of grazers alone starts with one body in twenty able
to bite wood, and the crowns pay for the rest: by step 10,000 one body in five has a tooth.

### 2. The injected line grows above its control, on average, in all four worlds

Every run has both lines in it: a hundred bodies of each kind at step 10,000, 1.2% of the world apiece.

| world | the invader | its line at 40,000 (mean of 6) | the control line | runs won / lost / both gone | lines still alive |
|---|---|---|---|---|---|
| `minusB` | the browser | 1,282 | 410 | 3 / 2 / 1 | 5 of 6 against 3 of 6 |
| `minusA` | the grazer | 555 | 192 | 2 / 1 / 3 | 2 of 6 against 3 of 6 |
| `oA` (the grazer's world) | the browser | 1,105 | 0 | 5 / 0 / 1 | 5 of 6 against 0 of 6 |
| `oB` (the browser's world) | the grazer | 717 | 567 | 2 / 2 / 2 | 3 of 6 against 3 of 6 |

Over the 24 runs the invading line is the larger one in 12, the smaller in 5, and both lines are gone
in 7. The same genomes read across the two one-kind worlds show the frequency dependence coexistence
asks for: **the browser's line ends at 1,105 when rare in the grazer's world and 567 in its own; the
grazer's at 717 in the browser's world and 0 in its own** (alive in 5 of 6 against 3 of 6, and 3 of 6
against 0 of 6).

A line of a hundred is a lottery ticket all the same. Seven runs of 24 end with both lines gone, and
the two founder draws of one world often disagree (`oB` on seed 9: 819 and 2,748; on seed 11: 0 and
735). The world itself swings between 6,895 and 9,215 bodies and turns its lineages over, and a line
of a hundred rides that noise. Without the control beside it in the same world, a single injection
says nothing.

### 3. What grew, and what the world stayed

The grazer's lines that grew are grass eaters to the end (0% of their food from wood, no tooth). The
browser's keep the tooth and the wood on seeds 9 and 10 (6-26% of their food, `plant/tooth/roams`),
and lose it on seed 11, where the line grows to 1,220-2,042 bodies as a shore grazer. In `minusB` on
seed 9 the injected browsers take the browsing over: the residents' share living by wood falls from
26.5% at the injection to 0-2% at the end while the marked line grows to 2,869-4,483.

Every world stands: 6,895-9,215 bodies (e073's kept runs 7,806), bodies in all three media in every
run, 6.74 kinds at a census against the donor world's 6.61, and the browse at 2.9-3.7% of the food.

### The hypotheses

1. **Mutual invasion: partly.** In the one-kind worlds the browser's line beats the control beside it
   on 3 seeds of 3, the grazer's on 1 of 3, so the rule set before the runs (2 of 3 in both
   directions) is not met; the means favour the invader in all four worlds.
2. **The invader keeps its way: partly.** The grazer's lines stay grass eaters; the browser's keep
   tooth and wood on 2 seeds of 3 and drop both on the third.
3. **The world stands: yes.** Matter to 5.0e-14, all three media, the kinds and the browse of e073's
   world.
4. **Reachability, measured:** the way taken out is back at the donor world's level in 2,000-4,000
   steps, in every world, out of 4-5% of the bodies of the kind that was left.

## Conclusion

**The instrument works and the question it was built for is answered, but not the way the test
intended.** The browser and the grazer of e073's world are not a lottery: **each way of living
re-forms from the other's genomes within ten lives**, so what evolution finds here is what the world
holds. e010's teeth - worth ten to one and found once in twelve million births - have no counterpart
in this pair; the browse is a food that the standing variation of any kind can reach, because one body
in twenty already carries the tooth that takes it.

That is also why a world held at one way of living could not be built. The mutual-invasion test in its
strict form (a resident at equilibrium, an invader from rare) needs a world that stays put while the
invader is watched; this world re-invents the missing way in a third of the time it takes to run the
test. What the runs can still say is the weaker, paired version: **the invading line ends larger than
the resident's own genomes injected beside it in all four worlds, and each kind does better rare in
the other's world than in its own**. That is the signature of coexistence, at the strength this world's
noise allows.

**What this changes for the project.**

- **Do not read a seed's outcome as a reachability answer.** The hunter/grazer lottery of e024, e045
  and e055 is not "evolution did not find it" for a pair as close as this one. A way of living that
  sits a few percent of bodies away from the resident kind is found in ten lives, on every seed.
- **A rare line needs its control beside it.** Seven of 24 injections lost both lines to noise. The
  paired injection (two marks in one world) is the form to keep; a single injection compared with
  another run would have read as a result either way.
- **#72's pass line does not fit this world.** Stage C should judge a pair by the paired means over
  several founder draws, not by "grows from rare in most replicates" on single runs.

These answers hold for this world and these choices: c1225, seeds 9-11, e073's kept world at
`wood_yield` 3e-5, 8,000 seeded bodies, an injection of a hundred at step 10,000 and 30,000 steps of
watching, two founder draws per world, and e068's census with its 5% line. Not shown: longer watching,
larger founder groups, a pair further apart than these two (a hunter and a grazer), and whether a
world seeded with one kind would hold if the mutation rate were lower.
