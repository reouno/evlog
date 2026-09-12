# e054 The grain of the food

Date: 2026-09-12

## Purpose

Measured in e048's world on 2026-09-12 (#64): the world is eaten to the limit of its regrowth
(plants regrow 75 a step, the crowd eats 76) and a body is always short - it pays 0.10 a step and
takes 0.032 from the ground under it, a seventh of a full bite. But **every place is equally thin**:
no bare cells anywhere, the standing plant 0.9-1.7 of a cap of 8 everywhere, and the three height
bands differ in how many bodies stand there and not in what a body is. A body walks 2.5-5 cells in
its life; the world is 128 across. Nothing asks it to go anywhere.

The mechanism for a place difference in the food has been in the code since e011: the world's
regrowth is laid down as Gaussian patches (`sigma`, argument 4), one per `PATCH_AREA` cells. It has
been off since e019 (`sigma` 0, the uniform sun), and where it was on, `PATCH_AREA` 4,096 put four
patches 64 cells apart on a 128x128 world - **a grain no body of this world could ever cross**. So
the food has only ever been uniform or far too coarse to walk between.

Here the grain becomes an argument and the food is run at a grain a body can cross within a life.
Nothing about crowding or moving is written as a law: a body that stays still empties its patch
(the cell under a body does not grow) and the patch comes back only at the world's own rate.

## Hypothesis

Written before the runs.

Walking pays when the food comes in patches a body can cross within its life (A) and eating a patch
empties it (B, already true in this world).

1. **Bodies travel.** The median travel of the bodies aged 200-500 steps is above the flat world's
   2.5-5 cells on at least 3 of 4 seeds.
2. **The crowd is uneven, and the thin land is where hunger kills.** The standing plant on the rich
   land stands above the thin land's, and the starvations per step fall on the thin land in a
   larger share than its share of the bodies.
3. **The world stands**: every winter floor above 50.
4. **Watch**: whether hunters travel too, once the prey is spread out.

## Method

Code: e053 (`experiments/e053_bandclock`) as `e054_grain`, byte for byte but for the new law, two
columns of `places.csv` and six of the log.

**The law.** `patch` (argument 48): the cells of the world per food patch. The peak of each patch
is set so that the sum over the world is the same whatever the grain (`RES_GROWTH * patch / 2 pi
sigma^2`), so **the world grows exactly as much food as before**; only where it lands changes. A
patch center takes a random step of one cell every 50 steps, as since e011. The world is cut in
two for the measures: a cell is **rich** where its regrowth is at or above the world's own rate
(what every cell got under the uniform sun) and **thin** below it.

| grain | `sigma` | `patch` | patches on 128x128 | apart | food of N cells laid on |
|---|---|---|---|---|---|
| flat (e019-e053) | 0 | - | - | - | every cell alike |
| 8 cells | 2 | 64 | 256 | ~8 cells | 64 cells' food on ~25 |
| 16 cells | 4 | 256 | 64 | ~16 cells | 256 cells' food on ~100 |
| e011's grain | 8 | 4,096 | 4 | ~64 cells | 4,096 cells' food on ~400 |

**Runs.** From the repo root:
`bash experiments/e054_grain/run.sh <sigma> <patch> <threads> <steps> <seeds>`.

| run | sigma | patch | seeds, steps | question |
|---|---|---|---|---|
| pilots, 3 threads | 0, 2, 4 | -, 64, 256 | 9, 20,000 | does the world stand at each grain, and is the land uneven |
| batch | the grain that stands | | 9-12, 100,000 | (1)-(3) |
| control | 0 | - | 9-12, 100,000 | the flat world on the same seeds |

**Measures** (over the second half): travel by age from `agents.csv`; `moved`, `stalled`,
`blocked`; `rich`, `plant_rich`, `plant_thin`, `pop_rich`, `hunger_rich`, `hunger_thin` (new);
`movers` and the per-place table of `places.csv`; bodies and winter floors; the kills' share of the
intake; the age at death; diversity (#42).

**Compute.** No new cost in the step loop: the patch field is rebuilt every 50 steps as before
(256 patches over a 13x13 box each, 43,000 cell writes) and the new measures are one pass over the
world per log row. Pilots: 3 runs of 3 threads (9 of the Mac's 12 cores), 5 minutes. Batch and
control: 8 runs of 1 thread, about 30 minutes on the Mac.

## Result

**The code.** At `patch` 4,096 (the default) e054 is e053 byte for byte: the same seed and world
write identical `deaths.csv`, `lineages.csv` and `events.csv`, and the log differs only in the six
new columns (checked on seed 9, 20,000 steps).

**Pilots.** Seed 9, 20,000 steps (one season), 3 threads each, 4 minutes. Means over the second log
row (steps 10,000-20,000); the floor is the lowest population of the season, from `pop.csv`.

| grain | rich land | standing plant rich / thin | bodies on the rich land | bodies at 20,000 | winter floor | `moved` | covered |
|---|---|---|---|---|---|---|---|
| flat | 100% | 1.66 / - | 100% | 2,542 | 422 | 0.069 | 20% |
| 8 cells | 39% | 2.20 / 1.01 | 54% | 2,043 | 436 | 0.064 | 14% |
| 16 cells | 39% | 2.50 / 1.04 | 68% | 2,270 | 689 | 0.059 | 14% |

- **The world stands at both grains**, and no worse than flat: the winter floor is 436 at grain 8
  and 689 at grain 16 against the flat world's 422 (e049's moving band, by contrast, halved the
  world). The patchy world holds a steadier crowd: its summer peak is 2,469 against 3,304.
- **The land is uneven, as asked.** 39% of the cells are rich (they grow at or above the world's
  own rate) and carry 2.2-2.5 of standing plant against 1.0 on the thin 61%.
- **The crowd gathers on the rich land** without being told to: 54% of the bodies at grain 8 and
  68% at grain 16 stand on 39% of the world. Nothing in the rules mentions density.
- **Starving is a thin-land death.** Per body per step, a body on the thin land starves 1.4 times
  as often as one on the rich land at grain 8 (0.0021 against 0.0015) and 1.2 times at grain 16.
- The batch takes **grain 8**, the grain the hypothesis is about: crossing 8 cells takes 133 steps
  at full speed against a life of 200-300, where 16 cells takes 266 - further than a life's walk.

**Batch.** Seeds 9-12, 100,000 steps, the food at grain 8 and the flat world on the same seeds,
eight runs at once on the Mac, 25 minutes. Means over the second half (steps 50,000-100,000);
pairs are the patchy world / the flat world on the same seed.

| seed | travel (aged 200-500) | `moved` | mean age | intake per gut | bodies | lowest floor | kills' share | state | diversity |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 2.5 / 6.1 | 0.055 / 0.089 | 885 / 317 | 0.0025 / 0.0028 | 1,749 / 1,937 | 414 / 422 | 11% / 32% | grazer / hunter | 1 / 2 |
| 10 | 2.8 / 3.7 | 0.062 / 0.065 | 1,053 / 1,329 | 0.0029 / 0.0024 | 2,227 / 2,085 | 590 / 558 | 8% / 4% | grazer / grazer | 1 / 2 |
| 11 | 6.8 / 4.0 | 0.076 / 0.059 | 483 / 739 | 0.0032 / 0.0027 | 2,255 / 2,693 | 704 / 742 | 20% / 10% | grazer / grazer | 1 / 1 |
| 12 | 2.9 / 8.0 | 0.048 / 0.075 | 668 / 278 | 0.0023 / 0.0028 | 1,765 / 2,004 | 365 / 347 | 16% / 34% | grazer / hunter | 2 / 1 |

The land of the patchy world, over the same rows:

| seed | rich land | standing plant rich / thin | bodies on the rich land | starving thin / rich (per 1,000 body-steps) |
|---|---|---|---|---|
| 9 | 37% | 1.69 / 0.87 | 58% | 1.98 / 1.43 (1.38x) |
| 10 | 37% | 1.24 / 0.55 | 58% | 1.75 / 1.34 (1.30x) |
| 11 | 37% | 2.51 / 1.24 | 54% | 3.07 / 2.57 (1.19x) |
| 12 | 37% | 2.08 / 0.92 | 55% | 2.75 / 2.16 (1.27x) |

- **Bodies travel less, not more.** The median travel of a body aged 200-500 steps is 2.5-6.8 cells
  against the flat world's 3.7-8.0, below it on three seeds of four, and the whole curve is lower:
  all four seeds together, by age, 0.6 / 3.3 / 5.5 / 8.5 cells against 1.3 / 5.3 / 8.3 / 11.6.
  `moved` follows (0.048-0.076 against 0.059-0.089).
- **The land is uneven and the crowd gathers on it.** The rich land is 37% of the world and holds
  about twice the standing plant; 54-58% of the bodies stand on it, half again the even share.
- **The thin land is where hunger kills**, by a little: 1.19-1.38 times as many starvations per
  body-step as on the rich land, on every seed.
- **The world stands**, and no worse: winter floors 365-704 against 347-742, no run died.
- **But the world grows less food.** Regrowth is 61-66 a step against 73.5-77.6. The loss is where
  the concentrated light lands: 7.6 a step is lost for want of soil (`barren`, zero in the flat
  world - a cell's soil is local and a patch draws 2.5 times the rate out of its own cells) and 3.2
  more to the bodies standing on the rich cells. The patchy world holds 8% fewer bodies.
- **The tooth goes.** No hunter world of four, against two of four flat; the kills' share falls on
  the two seeds that hunted (32% to 11%, 34% to 16%) and rises on the two that grazed.
- **Why nothing had to walk.** The rich land is not islands. Rebuilding the regrowth field from the
  patch centers at step 100,000: its 37% of the world falls into 39-46 connected regions, the
  largest 1,000-1,100 cells (7% of the world, about 35 cells across) and the median region 50
  cells. A body that travels 2.5-6.8 cells in a life is born inside one and dies inside it.

## Conclusion

The answers hold under the conditions of these runs (see "What these runs can and cannot say").

1. **Bodies travel: no.** Travel is below the flat world's on three seeds of four and lower at
   every age (0.6-8.5 cells against 1.3-11.6), and a body moves less per step.
2. **The crowd is uneven, and the thin land is where hunger kills: yes.** Twice the standing plant
   on the rich 37%, 54-58% of the bodies on it, and 1.19-1.38 times the starvation per body-step
   on the thin land.
3. **The world stands: yes.** Winter floors 365-704, no run died.
4. **Watch, hunters: they go.** No hunter world of four against two of four flat.

**Not kept**: `patch` stays an argument at 4,096. The law makes the world uneven, which is what it
was for, but it does not buy walking, it costs the world 15% of its regrowth, and diversity is
unchanged (1-2 either way).

What this changes:

- **A grain a body can walk between is still a grain it never has to leave.** Patches 8 cells apart
  and 2 wide overlap into connected ribbons 35 cells across, so being born on the rich land is
  enough. The grain that would make a body cross is the size of a patch against a life's grazing,
  not the spacing against a life's walk.
- **Concentrating the sun costs food, because the soil is local.** A cell can only grow what its
  own soil holds; at 2.5 times the rate a patch runs its cells dry and 10% of the world's sun is
  lost (`barren` 7.6 a step). Any future law that concentrates the light has to move the soil with
  it, or it is a weaker sun (as e046's plant yield was).
- **An uneven world is a grazer's world.** Gathering the crowd on a third of the land did not make
  it hunt; it ended hunting on the two seeds that hunted flat. A body that stands where the food is
  does not need to chase one that stands beside it.

**What these runs can and cannot say.** The answers hang on choices we made: patches of width 2 at
one per 64 cells, drifting a cell every 50 steps, in e048's world with no thirst and no clock, four
seeds of 100,000 steps. They do not say that patchy food cannot make a body walk; they say that at
this grain the patches merge into land a body is born inside, and that the cost of concentrating
the light is paid in the soil.
