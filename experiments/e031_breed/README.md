# e031 The child of the flesh, and breeding as a decision

Date: 2026-09-05

## Purpose

e030 gave a body a store, and the season at amplitude 1 (the sun out at midwinter) went from
death in the first winter to a lottery of 7-25 bodies each winter. The winter's arithmetic:
the world's matter is 131,000, the bodies' fat 20-43,000, and 3,000 bodies through 3,000 dark
steps would need 500,000. So a few hundred bodies at most can live through such a winter on
fat, and the world reaches 7-25 because its fat is spread over thousands of young bodies with
little each (fat per body 7-17, 125-300 steps of upkeep): every body breeds the moment its
energy reaches the threshold, and a child is born with no fat. The real world's answers are
that a child is provisioned from its mother's body, and that breeding is timed. This
experiment writes both as laws of the flesh and of the body's decisions, not of a trait.

## Hypothesis

1. **The yolk keeps the fat in the lineage.** With a child made of half its parent's fat, the
   fat per body rises and newborns live longer without food; but the store is only shared,
   not concentrated, so the winter floor rises little alone.
2. **Breeding as a decision concentrates the store.** Given a fifth output, selection finds
   bodies that do not breed when the food is low, so that autumn's bodies enter the winter
   fat and few: the winter floor rises from 7-25 toward the hundreds the matter allows.
3. **Together the lineage lives through the dark.** Both laws at once give the highest floors
   and more than one lineage on them.
4. **The summer world stands** at e030's numbers (1,700-3,100 bodies at 0.75; 2,000-4,000
   at 1).

## Method

Code: e030 (`experiments/e030_store`) as `e031_breed`, with `store` 5 by default (e030 kept
it) and two arguments: 22 `yolk` (the share of the parent's fat a child is made of, 0 by
default) and 23 `breed` (0: a body breeds at the threshold, 1: the policy's fifth output).
`yolk` 0 `breed` 0 is e030 byte for byte (checked on seed 9 for 10,000 steps at amplitude 1:
the log and the lineage log identical). The ledger holds (`EVLOG_AUDIT=1`, `yolk` 0.5
`breed` 1: drift 0 over 10,000 steps).

**The laws.** The yolk: at conception the child gets half the parent's energy, as before, and
the share `yolk` of its fat; a child never placed lays both where the parent stands. Breeding
as a decision: the policy has a fifth output, weights on the ten inputs and a bias read from
the gene table like the four moves (its column drawn from its own random stream, so the
bodies and the moves are e030's); when it wins the step's decision the body stays and breeds
if its energy is at the threshold (2 + 0.1 mass), else nothing happens. The threshold and the
cost of a child do not change. The policy sees what it saw: the food under it, the food and
the bodies in four directions, its energy; not its fat, not the season.

**The world.** e030's season world (the store at 5, `grow`) at amplitude 1: the sun a sine of
20,000 steps that goes out at midwinter, under a quarter for 4,600 steps. The control is
e030's pilot at amplitude 1 (this code with both laws off).

**Runs.** Three pilots on seed 9, 100,000 steps (five winters), one thread each: `yolk` 0.5,
`breed` 1, and both. Then the batch on the form that lifts the floor. `pop.csv` counts the
bodies every 1,000 steps (the lineage log counts only lineages of 5 or more, which misses
a floor of 25).

## Result

### The pilots at amplitude 1 (grow, store 5, seed 9, 100,000 steps)

Bodies from `pop.csv` (every 1,000 steps, all bodies); the control is this code with both laws
off (e030's world: its floors in e030 were counted in lineages of 5 or more).

| run | winter floors (bodies), in order | lineages at the floors | summer bodies at the log steps | fat per body | births per 10,000 | decisions to breed; of those, denied |
|---|---|---|---|---|---|---|
| control | see the table below (rerun for `pop.csv`) | 1-2 | 2,074-3,961 | 7-18 | 25,000-140,000 | - |
| yolk 0.5 | 26, 23, 8, 14, 26 | 0-2 | 2,419-3,586 | 4.5-6.1 | 23,000-133,000 | - |
| breed 1 | 9, then dead in the second winter (step 37,000) | 0 | 1,696-2,479 | 12-27 | 12,000-62,000 | 24-30%; 98-99% |
| yolk 0.5 + breed 1 | 5, then dead in the second winter (step 36,000) | 0-1 | 1,500-2,260 | 8-16 | 9,000-38,000 | 26-38%; 97-98% |

Neither law lifts the floor at amplitude 1. The yolk alone is the control: the floors are
8-26 and one or no lineage stands on them (the fat is shared among the same crowd, 4.5-6.1
per body). Breeding as a decision kills the world in its second winter, alone or with the
yolk: the start's random policies want to breed in a quarter to a third of their decisions
whatever their energy (97-99% of those decisions are below the threshold), the summer world
is smaller (1,500-2,500 bodies) and fatter (12-27 per body), and the winter floor is 4-9. A
first form of the law, where a body that decided to breed stood still whether it could or
not, died in its first winter (step 18,021: a third of all decisions were a wasted stand).
In two winters nothing is selected: the share of decisions to breed and the share denied do
not move, because a floor of 5-25 bodies is a lottery that erases selection.

So the question "can selection time the breeding" cannot be asked at amplitude 1, where the
world dies before it evolves. The batch asks it at 0.75, where the world stands (e030: floors
327-1,186): does `breed` fall below the start's 25-35%, does `denied` fall, and does the
winter floor rise over e030's, with the yolk or without it.

### The batch at amplitude 0.75 (grow, store 5, seeds 1-3, 300,000 steps, 15 winters; six runs at one thread, 44 minutes)

Second half unless said. The floors are counted in lineages of 5 or more for every world,
because the control (e030's store-5 runs) has no `pop.csv`; that count is 17-35% under the
bodies alive at the same steps (measured in this batch's runs), which applies to e030's
floors too.

| run | bodies | lowest winter floor | median floor | lineages at the floors | summer peak | fat per body | on their fat | decisions to breed; denied | side at the end | mass p50 | most with a sensor | longest lineage | winners; longest hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| breed, seed 1 | 2,166 | 710 | 947 (all bodies) | 11 | 2,527 | 18 | 45% | 47%; 99% | 5.2 +- 2.1 | 22 | 26% | 233,000 | 4; 50,000 |
| breed, seed 2 | 3,128 | 554 | 1,056 | 5 | 4,192 | 10 | 56% | 39%; 99% | 9.8 +- 3.8 | 12 | 25% | 122,000 | 9; 73,000 |
| breed, seed 3 | 2,007 | 498 | 885 | 16 | 1,807 | 20 | 51% | 29%; 98% | 4.7 +- 0.8 | 32 | 18% | 123,000 | 12; 15,000 |
| yolk + breed, seed 1 | 2,341 | 728 | 873 | 7 | 3,004 | 10 | 47% | 48%; 99% | 5.9 +- 2.0 | 30 | 47% | 157,000 | 5; 32,000 |
| yolk + breed, seed 2 | 3,408 | 524 | 943 | 4 | 5,284 | 5 | 52% | 38%; 99% | 10.6 +- 2.3 | 11 | 13% | 251,000 | 3; 134,000 |
| yolk + breed, seed 3 | 2,090 | 467 | 887 | 12 | 2,151 | 12 | 42% | 36%; 99% | 5.1 +- 2.4 | 32 | 27% | 257,000 | 5; 51,000 |
| control (e030), seed 1 | 3,078 | 908 | 1,072 (lineages) | 8 | 3,881 | 13 | 47% | - | 5.6 +- 1.5 | 14 | 65% | 300,000 | 1; 151,000 |
| control (e030), seed 2 | 1,854 | 530 | 669 | 12 | 1,529 | 28 | 46% | - | 4.0 +- 0.1 | 32 | 34% | 143,000 | 7; 60,000 |
| control (e030), seed 3 | 1,702 | 495 | 662 | 17 | 1,702 | 25 | 45% | - | 4.5 +- 1.1 | 32 | 21% | 158,000 | 11; 19,000 |

- **Nothing is selected about when to breed.** The share of decisions that are to breed
  moves between 23% and 62% over a run with no trend (the second half: 29-48%), and the share
  of those made below the threshold is 98-99% from the first log step to the last in all six
  runs. A denied decision costs nothing (the body takes its best move), and a body at the
  threshold breeds within two or three steps whether the output is a coin or a clock.
- **The winter is the control's.** Lowest floors 498-710 (breed) and 467-728 (both) against
  495-908; lineages at the floors 4-16 against 8-17; bodies 2,000-3,400 against 1,700-3,100.
  The fat per body is lower with the laws (5-20 against 13-28): bodies that breed a little
  later hold more energy and fix no more fat.
- **The bodies are e030's:** the light sitting gut (6-10 guts, side 7-10, density 0.8-1.1) and
  the dense block (a full 4x4 at density 2, mass 27-33), one of each in most seeds; breed
  seed 2 adds a net with an eye over a 15x15 grid (mass 33), breed seed 3 an armored mover
  (six hard blocks in front of ten muscle, mass 43, 64% flesh in its intake: the heaviest
  winner of the series).

## Conclusion

1. **The yolk keeps the fat in the lineage: no effect.** The fat per body falls (5-6 against
   7-18 at amplitude 1); the floors are the control's.
2. **Breeding as a decision concentrates the store: no.** The decision is never selected
   toward a time: 98-99% of the decisions to breed are below the threshold in every run to
   the end, and at amplitude 1 the world dies in its second winter.
3. **Together the lineage lives through the dark: no.** Both laws die in the second winter at
   1; at 0.75 the floors are the control's.
4. **The summer world stands: yes.**

Not kept: `yolk` and `breed` stay as arguments (0 by default), the world is e030's. The dark
winter is beyond the bodies: the world's 131,000 of matter cannot carry 3,000 bodies of
0.056 upkeep through 3,000 dark steps however the fat is divided, and a decision to breed
has nothing hanging on it when the autumn's children die anyway and the winter's floor is a
lottery. The real world lives its dark winters by leaving (a season that differs by place),
by a store in the ground (seeds, roots, a wood nobody eats down), or by paying less while it
waits. The first two are laws about the world: next, the season's amplitude by height (mild
in the valley, dark on the ridge), so that leaving is an outcome a body can reach.
