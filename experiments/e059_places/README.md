# e059 Places that differ, in a world a body can cross

Date: 2026-09-13

## Purpose

e058's probes found the first regime in which a law about place can matter: lower the sun and a
body must gather from more cells than it stands on, so it walks. At `sun` 0.2 a body ends its life
13.8 world cells from where it was born (3.0 at `sun` 1), the jam clears (blocked moves 58% ->
24%, births refused for want of room 38% -> 18%) and the world stands. But a thin **uniform** world
costs diversity fourfold (kinds 27.7 -> 13.2, q1 16.9 -> 5.9) and predation with it (kills per body
0.038 -> 0.030): much of the crowded world's diversity was made by the crowd itself (#68, rule 2).

So the thin world is the regime, not the law. The law under test is the one place difference the
world already has - the grain of its food (#64) - laid coarse enough to satisfy rule 1: a law about
place must differ over several times the ground a body covers in a life. e054 ran that law at the
wrong scale (patches 8 cells apart merge into ribbons 35 cells across) in the wrong world (a body
travelled 3 cells), and it bought nothing.

## Hypothesis

Written before the runs. **Diversity pays when the land differs over more ground than a body covers
in a life (A: the food's grain at 43-57 cells against a life's 13.8) and a body must gather from
more cells than it stands on (B: `sun` 0.2, 4.6 cells eaten per cell stood on).**

1. **Diversity rises** above the thin uniform world's: kinds above 13.2 and q1 above 5.9 on at
   least 3 of 4 seeds, and in the pilots it rises with the grain's scale.
2. **Bodies sort by place.** The bodies born on the rich land differ in shape from those born on
   the thin: their mean block mix differs by at least a twentieth of the body in one kind of block,
   or their mean size by a tenth, on at least 3 of 4 seeds.
3. **Predation returns where the crowd gathers.** `pop_rich` above the rich land's share of the
   world (35%), and kills per body above the thin uniform world's 0.030 on at least 3 of 4 seeds.
4. **Travel stays high**: the median travel of the living at least the thin world's 13.8 on at
   least 3 of 4 seeds. (e054's fine grain made bodies travel *less*; a grain they can live inside
   would do it again.)
5. **The world stands and the soil feeds the patches**: every winter floor above 50, and the light
   lost for want of soil (`barren`) below 5% of the world's light. e054 lost 10% of it this way at
   full sun; a thin world asks less of a cell (0.004 a step at a patch's peak against a soil stock
   of 7.5 a cell), so the loss should not appear.

## Method

Code: e058 (`experiments/e058_thin`) as `e059_places`, with no new law and two new measures:
`agents.csv` gets **`rich`** (1 where the cell under the body grows at or above the world's own
rate, 0 on the thin land) and **`born_rich`** (the land the body was born on, recorded at birth).
Hypothesis 2 cannot be read without them. At `sigma` 0 this is e058 byte for byte but for those
two columns (checked: seed 90, 20,000 steps, identical `deaths.csv`, `lineages.csv`, `events.csv`
and `log.csv`).

**The law** (both arguments already in the code since e011 and e054): the world's regrowth is laid
down as Gaussian patches of width `sigma` (argument 4), one per `patch` cells (argument 48), each
carrying the food of `patch` cells. The sum over the world is the same at every grain, so **the
world grows as much food whatever the scale**; only where it lands changes. A patch centre takes a
random step of one cell every 50 steps (so it wanders 3 cells in a life, 10 in ten generations: a
place, not a band). A cell is **rich** where it grows at or above the world's own rate and **thin**
below it.

The scale is the only thing that moves. Holding the concentration at 2.0 (the peak is twice what a
cell got under the uniform sun) and the rich land at 35% of the world, `sigma` sets everything:

| grain | `sigma` | `patch` | patches on 128x128 | apart | rich blob across | vs a life's 13.8 |
|---|---|---|---|---|---|---|
| fine | 6 | 455 | 36 | 21 | 14 | 1.6x |
| middle | 12 | 1,820 | 9 | 43 | 28 | 3.1x |
| coarse | 16 | 3,276 | 5 | 57 | 38 | 4.1x |

**Runs.** `bash experiments/e059_places/run.sh <sigma> <patch> <sun> <threads> <steps> <seeds>`,
from the repo root. Every run is the thin world (`sun` 0.2).

| run | sigma, patch | seeds, steps | question |
|---|---|---|---|
| check | 0, 4096 | 90, 20,000 | e058 byte for byte |
| pilots, 3 threads | 6/455, 12/1,820, 16/3,276 | 9, 100,000 | does the world stand, does `barren` stay near 0, is the land uneven, and do travel and diversity move with the scale |
| pilots, 3 threads | 6/1,820, 8/1,820 (the concentration axis) | 9, 100,000 | at a fixed spacing, which concentration breaks the rich land into islands |
| batch | 8, 1,820 | 9-14, 300,000 | (1)-(5) |
| control | 0, 4096 | 9-14, 300,000 | the thin uniform world on the same seeds (e058's probe is seed 9 at 100,000 only, and `born_rich` is new) |

**Measures** (over the second half): diversity by #66 (`diversity.py`: kinds, rarefied kinds, q1,
q2 on birth shapes, and the same for the born-rich and born-thin bodies apart); the mean birth
shape and size of the two groups; travel by age from `agents.csv`; `rich`, `plant_rich`,
`plant_thin`, `pop_rich`, `hunger_rich`, `hunger_thin`; kills per body and the kills' share of the
intake; `blocked`, `births_no_room`, `moved`; `barren`; bodies and winter floors. Two measures were
added while reading the pilots: the connected regions of the rich land, rebuilt from the patch
centres a snapshot carries, and **lineage segregation** - the chance two bodies of one region share
a lineage over the chance any two bodies do (the uniform runs are cut by the same nine centres).

**Compute.** Pilots: 5 runs of 3 threads (9 of the Mac's 12 cores), about 15 minutes. Batch and
control: 12 runs of 1 thread, about 70 minutes on the Mac (a thin world runs 100,000 steps in about
10 minutes on one core; seeds 13-14 were added after the first four split). No new cost in the step loop: the patch field is rebuilt every 50 steps as
since e011 (5 patches over a 97x97 box is 47,000 cell writes, the same order as e054's 43,000), and
the two new columns are read once per body per census.

## Result

**The code.** At `sigma` 0 e059 is e058 byte for byte: seed 90 at 20,000 steps writes identical
`deaths.csv`, `lineages.csv`, `events.csv`, `places.csv`, `pop.csv`, `dist.csv` and `log.csv` (but
`steps_per_sec`), and `agents.csv` differs only by the two new columns.

**Pilots, the scale axis** (seed 9, 100,000 steps, 3 threads each, 3 minutes). The concentration is
held at 2.0 and only the grain's scale moves. The control is e058's thin uniform probe on the same
seed. Means over the second half; `travel` is the median over the living bodies; the regions are
the rich land rebuilt from the patch centres at step 100,000 (4-neighbour, on the torus).

| grain | rich land | plant rich/thin | bodies on rich | travel | moved | blocked | kills/body | floor | barren | rarefied | q1 | rich regions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uniform (control) | 100% | 0.58 | - | 13.83 | 0.167 | 24% | 0.0296 | 450 | 0% | 13.2 | 5.89 | - |
| sigma 6, 21 apart | 39.9% | 0.94/0.45 | 70% | 5.75 | 0.068 | 35% | 0.0185 | 528 | 0% | 13.8 | 5.29 | 8, largest 58 across |
| sigma 12, 43 apart | 38.6% | 0.92/0.58 | 69% | 4.03 | 0.076 | 31% | 0.0219 | 574 | 0.5% | 13.6 | 6.22 | 2, largest 66 across |
| sigma 16, 57 apart | 41.3% | 1.81/1.11 | 78% | 3.75 | 0.060 | 41% | 0.0085 | 649 | 6.8% | 14.9 | 7.93 | 2, largest 69 across |

- **The land is uneven and the crowd gathers on it**, at every scale: 69-78% of the bodies on about
  40% of the world, which carries 1.6-2.0 times the standing plant.
- **Travel collapses** - 13.8 cells to 3.8-5.8 - and `moved` with it (0.167 to 0.060-0.076). The jam
  comes back (blocked 24% -> 31-41%). This is e054's answer again, at five times the scale.
- **The rich land is a web, not islands, whatever the scale**: two connected regions 66-69 cells
  across. The reason is the shape of the law, not the tuning. For Gaussian patches the share of the
  world that grows at or above the world's own rate is `ln c / c` for a concentration `c`, which is
  at most 1/e = 37%: at a concentration of 2 the rich land is always about 35%, and 35% of randomly
  placed disks is above the percolation threshold of about 33%. e054's "ribbons 35 cells across"
  was this fact at a fifth of the scale.
- **The coarser the grain, the more light the soil cannot feed** (barren 0%, 0.5%, 6.8%). The soil
  does not move sideways in this world (`flow` 0, and `mix` is between a cell and its deep store),
  so a wide patch mines the cells under it while a narrow one drifts onto fresh soil.
- Diversity hardly moves: rarefied 13.2 -> 13.6-14.9.

So the scale was the wrong axis. What separates places is the **concentration**, which sets both
the rich land's share and whether it percolates.

**Pilots, the concentration axis** (seed 9, 100,000 steps; `patch` 1,820 throughout, so the
patches stand 42.5 cells apart and only their width - hence the concentration - moves).

| grain | concentration | rich land | bodies on rich | travel | blocked | kills/body | floor | barren | kinds | rarefied | q1 | q2 | born size | rich regions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uniform (control) | 1.0 | 100% | - | 13.83 | 24% | 0.0296 | 450 | 0% | 22 | 13.2 | 5.89 | 3.76 | 43.9 | - |
| sigma 12 | 2.0 | 38.6% | 69% | 4.03 | 31% | 0.0219 | 574 | 0.5% | 30 | 13.6 | 6.22 | 4.28 | 28.4 | 2, 66 across |
| sigma 8 | 4.5 | 29.6% | 76% | 2.37 | 35% | 0.0142 | 618 | 1.8% | 47 | 21.4 | 9.97 | 5.41 | 24.6 | 5, 36 across |
| sigma 6 | 8.1 | 23.1% | 78% | 2.30 | 44% | 0.0171 | 465 | 2.9% | 31 | 18.1 | 9.92 | 6.77 | 25.8 | 6, 31 across |

- **When the rich land breaks into islands, diversity jumps**: rarefied 13.2 -> 21.4, q1 5.89 ->
  9.97, q2 3.76 -> 5.41 at a concentration of 4.5. The same seed's crowded world (`sun` 1) reads
  27.7 / 16.9 / 9.2, so the islands win back about 60% of what thinning the world cost.
- **And bodies stop walking** (travel 2.3-2.4, a sixth of the uniform thin world's). The diversity
  is not bought by travel. It is bought by the crowd being cut into pieces: half a dozen islands
  30-36 cells across, each with its own crowd, its own jam (blocked 35-44%) and its own winners.
- Predation falls with it (0.030 -> 0.014), and the bodies are half the size (born size 44 -> 25).
- The world stands at every setting (floors 465-649 against the control's 450).

**Batch.** `sigma` 8 / `patch` 1,820 (the island grain) against the thin uniform world, seeds 9-14,
300,000 steps, one thread each. Means over the second half (steps 150,000-300,000).

| | uniform | islands |
|---|---|---|
| bodies | 750 | 630 |
| the world's regrowth per step | 20.6 | 15.5 |
| light lost for want of soil | 0% | 8.5% |
| worst winter floor | 72 | 27 |
| travel in a life (median) | 9.75 | 2.94 |
| `moved` | 0.119 | 0.052 |
| forward moves blocked | 31% | 43% |
| births refused for want of room | 13% | 18% |
| kills per body per step | 0.0172 | 0.0093 |
| the kills' share of the intake | 18% | 11% |
| kinds (birth shapes) | 27 | 33 |
| kinds rarefied to 120 bodies | 13.4 | 17.8 |
| q1 | 5.53 | 10.37 |
| q2 | 3.36 | 6.49 |
| lineages alive | 4.13 | 5.09 |
| lineage segregation | 1.09 | 2.23 |
| birth size | 27.6 | 25.3 |
| mean age at death | 309 | 348 |
| rich land / bodies on it | 100% / - | 31% / 79% |

By seed, kinds rarefied to 120 bodies (uniform / islands): 14.3/6.4, 15.6/25.4, 12.3/28.9,
11.7/14.9, 14.3/13.9, 12.2/17.4. q1: 6.12/3.48, 7.40/12.36, 4.65/20.98, 5.04/8.43, 4.02/6.60,
5.92/10.37.

1. **Diversity rises: yes.** q1 5.53 -> 10.37, higher on five seeds of six; rarefied kinds
   13.4 -> 17.8, higher on four of six. The spread across seeds widens from 11.7-15.6 to
   6.4-28.9: the law raises the ceiling and lowers the floor. At every census the islands hold
   1.3-1.5 times the control's kinds, and both worlds lose kinds as they settle (islands 24.3 ->
   19.3 -> 17.8 at 100k, 200k, 300k; uniform 16.1 -> 13.2 -> 13.4).
2. **Bodies sort by place: no.** The mean birth shape of the bodies born on the thin land differs
   from that of the bodies born on the rich by more than a twentieth of the body on two seeds of
   six (11 and 14, both times more muscle and less gut). On the other four the two lands grow the
   same body. Only 8-10% of the bodies are born on the thin land at all.
3. **Predation returns: no.** Kills per body falls on every seed (0.0172 -> 0.0093), the kills'
   share 18% -> 11%, and the one hunter world of the control (seed 13) grazes under the islands.
4. **Travel stays high: no.** 9.75 -> 2.94 cells a life, lower on every seed and at every age
   (0.3 / 2.5 / 4.3 / 7.6 against 1.5 / 6.2 / 11.8 / 20.7).
5. **The world stands, but the soil does not feed the patches.** No run died, but the worst winter
   floor is 27 against the control's 72, and three of six fall below 50. The light lost for want of
   soil is 8.5% (6-13%), not the under 5% the hypothesis asked: a heap of light sits on the same
   cells and mines them, and `flow` is 0, so no soil comes in from the side. The world grows a
   quarter less food than the uniform one.

**What made the kinds.** The crowd is cut into pieces that keep different lines. Two bodies on the
same island share a lineage 2.23 times as often as two bodies anywhere in that world (six frames of
the second half, the nine patch centres as the regions); the uniform runs, cut by the very same
nine centres, read 1.09 - no clustering at all. The number of lineages alive rises with it (4.13 ->
5.09). The connectivity of the rich land itself does not explain which seed gained: over the second
half every seed's rich land falls into 3 regions on average (range 1-6, the largest holding 60-67%
of it).

## Conclusion

The answers hold under the conditions of these runs (see "What these runs can and cannot say").

1. Diversity rises: **yes** (q1 5.53 -> 10.37, five seeds of six).
2. Bodies sort by place: **no** (two seeds of six, and only 9% of bodies are born on the thin land).
3. Predation returns: **no** (kills per body halves; the one hunter world stops hunting).
4. Travel stays high: **no** (9.75 -> 2.94 cells, lower at every age).
5. The world stands: **yes**, but the soil does not feed the patches (8.5% of the light lost,
   worst floor 27) and the world grows a quarter less food.

**Not kept** as the default world: the season world keeps `sigma` 0. The price is a quarter of the
food, two thirds of the travel, half the hunting and half the winter margin.

What this changes:

- **Diversity in this world comes from cutting the crowd up, not from making it travel.** This is
  the first law in the project to move the diversity number (q1 nearly doubles), and it does it
  while bodies walk *less* than before. What rose with it is the segregation of lineages by place
  (1.09 -> 2.23), not any measure of movement or of local adaptation.
- **Places that differ in how much food they hold do not grow different bodies.** The rich land and
  the thin land of the same world grow the same shape on four seeds of six. A place difference in
  the amount of one food is not a second way of making a living; #14's "kinds of place" needs
  places that differ in *what* they offer, not in how much.
- **A law about place must not pay for the separation in food.** The whole cost here is that a heap
  of light stands on cells whose soil is local: 8.5% of the world's light falls where nothing is
  left to grow it, and the concentration itself moves the crowd onto a third of the land, which
  jams (blocked 31% -> 43%). A separation that costs no food - ground a body cannot cross, or a
  place whose worth differs in kind - would keep the gain and drop the price.
- **The geometry of the Gaussian heap is a hard limit.** The share of the world that grows at or
  above the world's own rate is `ln c / c` for a concentration `c`, at most 1/e = 37% and falling
  slowly; below a concentration of about 3 that share is above the percolation threshold for
  random disks and the rich land is always a web. A patchy sun can make islands only by being
  extreme, and the extreme is what runs the soil dry.

**What these runs can and cannot say.** The answers hang on our choices: nine heaps of width 8 at a
concentration of 4.5, drifting a cell every 50 steps, in the thin world (`sun` 0.2) of e058, six
seeds of 300,000 steps, judged on birth shapes rounded to quarters and rarefied to 120 bodies. They
do not say that places cannot grow different bodies; they say that a place difference in the amount
of one food, at this grain, does not - and that the diversity it does buy comes from the crowd
being broken into pieces.
