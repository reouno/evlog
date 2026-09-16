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
browser), and the community without each of them (`minusA`, `minusB`).

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
  must be a fifth or more;
- **A, the grazer**: the largest kind of the land or the shore with no tooth and under a tenth of its
  food from wood.

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

**Cost, before the runs.** The donor runs are 3 x 100,000 steps on 3 local cores, about 50 minutes
(a step is 17-24 ms on this world). The invasion runs are 12 x 40,000 steps on 11 cores, about 35
minutes in two waves. Around 6 core-hours on the Mac, nothing on the Ubuntu box.

## Result

(to come)

## Conclusion

(to come)
