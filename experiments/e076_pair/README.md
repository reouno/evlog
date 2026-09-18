# e076: the invasion test on the hunter and the grazer (stage C's fourteenth step, #92)

Date: 2026-09-18

## Purpose

e074 built the paired invasion test (#72) and could only run it on e073's browser and grazer, a pair a
few percent of bodies apart: whatever way of living was left out of a world came back in 2,000-4,000
steps, because the grazer already carried the browser's tooth in one body in twenty. What evolution
found was what the world held, and the strict test could not run.

e075 (#90) made a pair further apart. At the last census of its kept runs:

| seed | the hunter (`mixed/tooth/roams/land`) | the grazer (`plant/no tooth/stays/shore`) |
|---|---|---|
| 9 | 320 bodies, kills 49%, a tooth in 94%, 14.5 cells travelled | 107 bodies, kills 8%, a tooth in 0%, 0.0 cells |
| 10 | 130 bodies, kills 53%, tooth 98%, 24.2 cells | 256 bodies, kills 6%, tooth 13%, 0.2 cells |
| 11 | 269 bodies, kills 45%, tooth 90%, 19.5 cells | 212 bodies, kills 12%, tooth 0%, 0.2 cells |

The hunter needs more than a tooth the grazer already carries: on two seeds of three no grazer has
one, and the hunter also walks a hundred times as far. This asks whether the gap between **what the
world holds** and **what evolution finds** opens for such a pair. If the hunter re-forms out of the
grazer's genomes within ten lives, a seed's outcome is never a reachability answer in this world.

## Hypothesis

Written before the runs, with the conditions named together (#87): **the hunter pays when a strike is
a meal (e075's tear and frail line) and soft prey stand dense (a world of grazers); it is reached only
when a body has a tooth to start from.** Losing a way is quick and building one is slow, so the gap
opens in one direction only.

1. **The gap, in the grazer's world** (seeded with the grazer alone, before any injection). Killing
   needs no tooth (a soft face breaks under any push), so the kills' share of the world's food is back
   at half the donor's 27% or more by step 10,000 on 3 seeds of 3. But the hunter's way - a land kind
   with a tooth taking 40% or more of its food from kills - is **not** among the kinds of the census at
   step 10,000 on at least 2 seeds of 3.
2. **No gap the other way.** In the hunter's world the grazer's way (a plant eater with no tooth, of the
   land or the shore) is among the kinds at step 10,000 on 3 seeds of 3.
3. **The hunter invades the grazer's world.** Its line ends larger than the grazer's own genomes
   injected beside it (paired means over the two founder draws, e074's rule) on 2 seeds of 3, and its
   marked bodies keep the way at the last census: a tooth in most, a third or more of their food from
   kills.
4. **The world stands.** Matter conserved, bodies in all three media, and after the injection the crowd
   within a fifth of e075's kept runs (9,099).

The grazer invading the hunter's world is read the same way (#72 asks both directions), with no pass
line: hypothesis 2 expects the grazer's way to be back before the injection, as in e074.

What would refute it: the toothed land hunter back at step 10,000 on 2 seeds or more (the gap is closed
even for this pair), or the hunter's line no larger than its control (the world does not hold it when
it is rare).

## Method

No law and no instrument is added: e076 runs e075's binary (`run.sh`), which carries e074's
instruments, on stage C's default world (e075's kept set, `flesh_bite` 0.4, `frail` 0.5). The crate is
a stub, as e068's is.

**The donor runs** (3 runs, seeds 9-11, 100,000 steps): e075's kept runs again with `genomes=1`, which
writes every body's genome at the last census. `experiments/e075_hunt/check.py` must find each donor
equal to e075's kept run (`ladder/c1225_life{9,10,11}_both`) in every shared log column, every body of
the last census, every lineage row and every event.

    (EVLOG_OUT=experiments/e076_pair/results/donor nohup bash experiments/e076_pair/run.sh \
      c1225 100000 9 donor genomes=1 > experiments/e076_pair/results/donor/c1225_life9_donor.log 2>&1 &)

**The pools** (`pick.py`, no runs): at the last census of each donor, **B, the hunter** is the land
kind holding e060's 5% with the largest share of its food from kills (40% or more), and **A, the
grazer** is the largest way of the land or the shore with a plant diet and no tooth (it need not hold
5%: 4.6% on seed 9). Their genomes are the two pools.

**Why one-kind worlds, not e074's `minus` worlds.** e074 also seeded worlds with a whole way of living
taken out, form by form. In e075's world killing is not one way among others: 56-70% of the grown
bodies are in forms that take a quarter or more of their food from kills, so a world without it would be
a remnant, not a community. The one-kind worlds are #72's own wording, and in e074 they gave the clearest
reading.

**The invasion runs** (12 runs, seeds 9-11, 40,000 steps): 2 worlds x 2 draws of the injection. Each
world is seeded with 9,000 genomes of one kind (e075's kept runs hold 9,099) and settles for 10,000
steps; at step 10,000 **both** lines go in, a hundred bodies each (1.1% of the world apiece), and are
followed for 30,000 steps, about a hundred lives.

| run | seeded with | mark 1 (the grazer's genomes) | mark 2 (the hunter's) |
|---|---|---|---|
| `oA_s1`, `oA_s2` | the grazer alone | the neutral control | **the invader** |
| `oB_s1`, `oB_s2` | the hunter alone | **the invader** | the neutral control |

The injection draws on a stream of its own, so the two draws of a world are the same run up to step
10,000: hypotheses 1 and 2 are read once a seed and world, and the two draws check each other.

    bash experiments/e076_pair/batch.sh 40000 9 10   # then 11

Read with `invade.py`: each line's count and way, the kills' share by step, the kinds of the census at
step 10,000 (e068's census on that census alone) and over the second half, with the share of each kind
that carries a mark.

**Cost**, stated before the runs: 3 donor runs of 100,000 steps on 3 cores (a step of e075's world
takes 26 ms, so about 45 minutes), then 12 invasion runs of 40,000 steps in two waves of 8 and 4
(about 20 minutes a wave). About 7 core-hours on the Mac, nothing on the Ubuntu box.

## Result

**The checks.** The three donor runs equal e075's kept runs over all 100,000 steps on seeds 9-11 in
every shared log column (173), every body of the last census, every lineage row and every event. The
two draws of each world are the same run up to step 10,000 in every log column (6 pairs of 6). Matter
drifts by at most 4.7e-14 in the 12 invasion runs.

**The pools** (`pick.py`). The two kinds are the same shapes on every seed. The grazer's most common
birth body is all gut on seeds 9 and 11 (40 and 16 gut blocks, no muscle, no hard block: it cannot
move) and 23 gut with 10 muscle on seed 10; the hunter's is a hard front row (its tooth) over muscle
and gut, 23-36 blocks. The pools hold 107 / 256 / 212 grazer genomes and 320 / 130 / 269 hunter
genomes.

| seed | world | kills at 10k | the other way a kind at 10k | residents living it, 10k -> end | the invader's line | the control's line | bodies, 2nd half |
|---|---|---|---|---|---|---|---|
| 9 | the grazer's | 16% | no | 0.0% -> 0.0% | 5,530 / 5,080 | 974 / 0 | 10,184 |
| 9 | the hunter's | 26% | yes (197) | 13.7% -> 8.0% | 2,009 / 4,666 | 252 / 50 | 9,755 |
| 10 | the grazer's | 23% | no | 6.8% -> 10.0% | 0 / 0 | 1,405 / 1,032 | 8,596 |
| 10 | the hunter's | 23% | yes (95) | 14.3% -> 14.7% | 689 / 1,344 | 243 / 681 | 8,232 |
| 11 | the grazer's | 16% | no | 0.0% -> 0.0% | 5,520 / 5,760 | 0 / 0 | 10,117 |
| 11 | the hunter's | 26% | yes (111) | 13.1% -> 13.4% | 0 / 2,478 | 372 / 0 | 8,673 |

"Kills" is the flesh of the living as a share of all the food, over steps 8,000-10,000 (the donor
world 27.4%). "Residents living it" counts the unmarked grown bodies living the other kind's way one
body at a time (the hunter's: a tooth, roaming, a third of the food flesh, on the land; the donor
worlds 10.2-11.8%; the grazer's: a plant eater with no tooth that stays, out of the surface; donors
20.4-24.9%). The lines are the mean over the last 5,000 steps, draw 1 / draw 2.

### 1. Killing comes back at once; the hunter comes back only where a tooth was there

In the grazer's world killing is 16-23% of the food by step 10,000, on every seed: a soft face breaks
under any push, so bodies that sit in a crowd eat each other with no tooth (on seeds 9 and 11 it is
17-20% by step 1,000). But no seed has the hunter's way among the kinds at step 10,000, and how far it
got depends on one thing: **whether the grazer's genomes already carried a tooth**.

- Seed 10's grazer has muscle and a tooth in 13% of its bodies (the world starts at 15%). The
  hunter's way is 6.8% of the residents by step 10,000 and at the donor's level (10.2%) by step 20,000,
  and a resident kind `mixed/tooth/roams/land` (45% kills, a tooth in all of it, no mark) holds the
  census at the end of one draw. That is e074's result: a way a few percent of bodies away is found
  within tens of thousands of steps.
- Seeds 9 and 11's grazer has no muscle and no tooth. The residents carry a tooth in 0.0-1.6% of their
  bodies at every census, and **the hunter's way is at most 0.1% of the grown residents at any census,
  from step 10,000 to step 40,000**, on either seed, in either draw (0.0% at step 10,000).

The other direction has no gap. The hunter's world has the grazer's way among its kinds by step 10,000
on 3 seeds of 3 (95-197 bodies), and its teeth fall from 66-71% of the bodies at step 1,000 to 34-36%.
**Losing a part is quick; building one the population does not carry is not.**

### 2. Where the world had no hunter, the injected hunter takes it

The grazer's world with no tooth is not a stable place for a grazer: its crowd doubles (17,788 and
20,030 bodies at step 10,000, against the kept world's 9,099). A hundred hunters injected into it are
3,987-7,169 bodies 2,000 steps later, the crowd falls to about 10,000 - the kept world's level - and
the hunter's line holds half the world to the end: 5,080-5,760 bodies in all four runs, against 0-974
for the grazer's own genomes beside it. The lines keep the way loosely: a tooth in 48-71% of their
grown bodies, 28-37% of their food from kills, and they drift from the land to the shore (46-61% on
the land).

On seed 10, where the residents already had teeth, the injected hunter booms to 1,417-1,662 and is gone
by step 20,000 and 32,000, while the residents' own hunters rise. A hunter from outside meets a
world that already hunts.

### 3. The grazer beats the hunter's own genomes in the hunter's world

In the hunter's world the grazer's line ends above the control on 3 seeds of 3 by the paired means
(3,337 against 151, 1,016 against 462, 1,239 against 186; 5 runs of 6). The hunter's own genomes shrink
in the world they came from (0-681 bodies). The grazer's lines learn to kill without a tooth on seeds
9 and 11 (25-31% of their food from kills, `mixed/no tooth/stays`), and stay plant eaters on seed 10.

Read across the two worlds, each kind does better rare in the other's world than in its own on 4
comparisons of 6: the hunter's line ends at 5,305 and 5,640 in the grazer's worlds of seeds 9 and 11
against 151 and 186 in its own, the grazer's at 3,337 and 1,239 against 487 and 0. Both exceptions are
seed 10 (the hunter 0 against 462, the grazer 1,016 against 1,218), the one world whose grazer pool
already carried the tooth.

### The hypotheses

1. **The gap, in the grazer's world: yes.** Killing is back at half the donor's share or more on 3
   seeds of 3 (16-23%); the hunter's way is not a kind at step 10,000 on 3 of 3. On the two seeds
   whose grazer carries no tooth it is not there at all, one body at a time, in 40,000 steps.
2. **No gap the other way: yes.** The grazer's way is a kind at step 10,000 on 3 seeds of 3.
3. **The hunter invades the grazer's world: yes on 2 seeds of 3** (5,305 against 487, 5,640 against 0;
   seed 10 0 against 1,218), and it keeps its way loosely: a tooth in most of its bodies in 3 lines of
   4, a third of the food from kills in 3 of 4.
4. **The world stands: yes.** Matter to 4.7e-14, bodies in all three media in every run (at least
   1,426 at the surface), and 8,077-10,521 bodies over the second half, within a fifth of 9,099.

## Conclusion

**For this pair the gap between what the world holds and what evolution finds opens, and it opens in
one direction.** A world of grazers that carry no tooth does not make a hunter in 10,000 steps, nor its
residents in 40,000, though the same world, given a hundred hunters, lets them take half of it and
brings its doubled crowd back to the kept level. A world of hunters makes grazers in under 10,000
steps. Where the grazer's genomes carry a tooth in one body in eight (seed 10), the hunter is found in
20,000 steps, as e074's browser was.

**What sets reachability in this world is the standing variation, not the value of the way.** A way
that needs a part some bodies already have is found in 20,000 steps; a way that needs parts no body
has (a tooth, and muscle to use it) is not found in 40,000, even when it would take half the world.

**What this changes for the project.**

- **A seed's outcome can be a reachability answer after all**, when the way it lacks needs a part the
  population has lost. e074's rule ("do not read a seed as reachability") holds for close pairs only.
  A world that has passed through a state with no teeth - a bottleneck, a seeded start, a long spell
  of grazing - can stay without hunters although it would hold them.
- **The hunter holds the crowd.** Without it the grazer's world doubles (18,000-20,000 bodies); with it
  the world is back at about 10,000 within 2,000 steps. The jam that five experiments fought
  (`crowd binds`) is partly a world without a predator.
- **The injection is the instrument that tells ecology from reachability.** Stage C should use it
  before rejecting a law on "no kind of that way appeared": seed the world with the kinds the law is
  meant to favour and watch whether they hold.

These answers hold for this world and these choices: c1225, seeds 9-11, stage C's default world (e075's
set), donors at step 100,000, 9,000 seeded genomes of one kind, a hundred of each line injected at step
10,000, two founder draws, 40,000 steps, and e068's census with its 5% line. Not shown: whether the
toothless grazer's world makes a hunter with no injection over a longer run (only 10,000 steps were
free of the injected hunter), how rare a tooth must be before it is not found, and whether a
mutation rate other than the one this world has changes either.

**Cost, as run.** The donors took 43-48 minutes on 3 cores; the 12 invasion runs went in two
overlapping waves on 8-11 cores, 16-25 minutes a run in a world of 9,000 and 34-38 minutes in the
doubled grazer's worlds of seeds 9 and 11. 7.3 core-hours on the Mac, nothing on the Ubuntu box.
