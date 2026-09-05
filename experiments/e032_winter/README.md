# e032 A winter that differs by place

Date: 2026-09-05

## Purpose

The season at amplitude 1 (the sun out at midwinter) is a lottery of 7-25 bodies each winter
with a store (e030), and no law of the body lifts it (e031: the yolk shares the fat, a decision
to breed is never selected). The arithmetic is the world's: 131,000 of matter cannot carry
3,000 bodies through 3,000 dark steps. The real world's dark winters are somewhere: the
higher a place (and the farther from the equator), the harsher its winter, and the animals
leave, huddle, or carry a store. Every season so far was the same on every cell, so leaving
had nowhere to go. This experiment writes the winter as a law of the place: the season's
amplitude by the cell's height.

## Hypothesis

1. **The world stands through the dark winter.** With the amplitude by height (2: every cell
   above the mean height goes dark at midwinter, the valley bottom keeps its sun) the world
   lives its winters in the hundreds with several lineages, not as a lottery, where the flat
   season at the same world sun at midwinter (0.75) gives floors of 300-1,200 (e030).
2. **The bodies are in the valley at midwinter and on the ridge in summer.** The ridge's
   share of the bodies swings with the season, and the bodies on the ridge in summer are born
   elsewhere (`cross2` rises after each winter): migration as an outcome, not a rule.
3. **More than one winner.** The places with different winters hold different bodies: a
   sitter in the valley, a mover on the slope and the ridge.

## Method

Code: e031 (`experiments/e031_breed`) as `e032_winter`, with one argument added: 24 `winter`
(`flat`: the season's amplitude the same on every cell, the default; `high`: the cell's
amplitude is the season's `a` times its height over the relief, at most 1). `winter flat`
is e031 byte for byte (checked on seed 9 for 20,000 steps at amplitude 1: the log,
`agents.csv` and the lineage log identical but for the speed). Under `high` the amplitude may
exceed 1: it is a slope, not a share.

**The law.** A cell at height h gets the sun RES_GROWTH (1 + min(1, a h / relief) sin(2 pi t /
20,000)). The mean over a season is the same on every cell: the world's matter and the sun a
place gets over the year are e031's; only the winter differs by place. On e031's terrain
(relief 64, heights 0-72, mean 32; the bands are thirds of the cells: valley below 23, slope
to 37, ridge above) the amplitudes by band and the world's sun at midwinter are:

| a | valley (mean amplitude) | slope | ridge | cells dark at midwinter | world sun at midwinter |
|---|---|---|---|---|---|
| 1 | 0.22 | 0.47 | 0.80 | 5% | 0.50 |
| 2 | 0.45 | 0.91 | 1.00 | 44% | 0.21 |
| 3 | 0.67 | 1.00 | 1.00 | 72% | 0.11 |

At a = 2 the world's sun at midwinter is a quarter, the flat season's at 0.75: e030's store-5
batch (flat 0.75, seeds 1-3, 300,000 steps) is the control at the same world sun, with the
winter gathered on the high ground instead of spread over every cell.

**Measures.** `pop.csv` every 1,000 steps: all bodies, and per height band the bodies standing
there (`pop0..2`) and of those the bodies born in another band (`cross0..2`). The winter floor
is the least of each cycle of 20,000; the summer's ridge share and the crossers say whether
the bodies move with the season. The log every 10,000 as before.

**Runs.** Three pilots on seed 9, 100,000 steps (five winters), two threads each, at a = 1, 2
and 3 (12 minutes), against e031's control at flat 1 (the same code, the winter the same
everywhere: floors 8-22). Then the batch at the amplitude the pilots pick, seeds 1-3 for
300,000 steps, against flat 0.75 rerun with this code for `pop.csv` (six runs at one thread,
about 45 minutes).

## Result

### The pilots (grow, store 5, seed 9, 100,000 steps, five winters; three runs at two threads, 12 minutes)

From `pop.csv` (every 1,000 steps, all bodies). The control is e031's rerun of the flat season
at amplitude 1 (this code with `winter flat`).

| run | winter floors (bodies), in order | lineages at the floors | valley share at the floors | bodies on the ridge at the floors | of those, born elsewhere | summer peaks | ridge share at the peaks | biters |
|---|---|---|---|---|---|---|---|---|
| flat 1 (e031) | 8, 9, 9, 22, 13 | 0-2 | - | - | - | 2,734-5,078 | - | 0-11% |
| high 1 | 1,666, 1,950, 2,216, 2,017, 1,992 | 3-12 | 47-49% | 306-412 | 49-64% | 2,719-3,831 | 17-32% | 1-6% |
| high 2 | 542, 819, 825, 680, 695 | 3-13 | 74-85% | 13-56 | 80-92% | 2,700-4,192 | 17-32% | 0-5% |
| high 3 | 300, 303, 310, 305, 296 | 3-7 | 76-83% | 18-26 | 42-91% | 2,734-4,291 | 12-31% | 3-22% |

- **The dark winter is somewhere, and the world stands.** At amplitude 2 (every cell above the
  mean height dark at midwinter, 44% of the cells) the floors are 542-825 bodies with 3-13
  lineages, where the flat season at 1 gives 8-22 with 0-2. At 3 (72% of the cells dark) the
  floor is 296-310 in every winter, within 5%: the valley holds what its sun feeds, and the
  world's floor is a place's capacity, not a lottery.
- **The bodies are in the valley at midwinter.** At 2 the valley (a third of the cells) holds
  74-85% of the floor's bodies; the ridge holds 13-56, and 80-92% of those were born in the
  valley or on the slope (in summer the ridge's bodies are 78-83% its own). At the summer peak
  the ridge holds 17-19% of 3,200-4,200 bodies (the first peak is the start's 32%): the ridge
  is refilled every summer and emptied every winter.
- **At amplitude 1 the world barely notices:** the ridge's mean amplitude is 0.8, the floors
  1,666-2,216, and the ridge keeps 306-412 bodies through midwinter (the flat season at 0.75
  gives 327-1,186, e030).
- **Bodies.** The summer world is e031's (2,000-3,200 bodies at the log steps, side 5-9, mass
  p50 8-32). At 3 the biters rise to 22% of the bodies in one log step (2 at most 5%, 1 at
  most 6%); whether a tooth pays where the winter crowds the valley is the batch's question.

### The batch (grow, store 5, seeds 1-3, 300,000 steps, 15 winters; nine runs at one thread, 60 minutes)

Second half (eight winters) unless said. All bodies from `pop.csv`. `flat 0.75` is the flat
season at the world sun of `high 2` at midwinter (a quarter), rerun with this code.

| run | bodies | winter floors (lowest, median) | lineages at the floors | valley share at the floors | bodies on the ridge at the floors | of those, born elsewhere | summer peak | ridge share at the peak | biters | flesh in the intake | side at the end | mass p50 | longest lineage | winners; longest hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| high 2, seed 1 | 4,207 | 1,055; 1,092 | 2-6 | 68-76% | 48-124 | 88-97% | 5,600 | 21% | 24-37% | 38% | 10.2 +- 1.7 | 10 | 277,000 | 4; 18,000 |
| high 2, seed 2 | 2,333 | 716; 748 | 3-7 | 71-81% | 37-82 | 79-100% | 2,800 | 21% | 2-6% | 36% | 5.9 +- 1.9 | 28 | 169,000 | 5; 54,000 |
| high 2, seed 3 | 1,935 | 673; 708 | 3-10 | 70-79% | 22-73 | 63-98% | 2,800 | 22% | 0-32% | 34% | 8.1 +- 1.1 | 21 | 300,000 | 4; 111,000 |
| high 3, seed 1 | 2,201 | 412; 444 | 4-7 | 77-85% | 29-52 | 73-100% | 2,700 | 22% | 0-1% | 35% | 5.1 +- 1.5 | 26 | 268,000 | 6; 54,000 |
| high 3, seed 2 | 2,865 | 364; 405 | 2-6 | 81-90% | 17-36 | 58-97% | 4,500 | 16% | 0-3% | 30% | 8.9 +- 3.3 | 13 | 97,000 | 13; 19,000 |
| high 3, seed 3 | 2,264 | 382; 427 | 3-6 | 79-85% | 20-41 | 79-91% | 2,800 | 22% | 5-22% | 39% | 5.2 +- 1.6 | 27 | 189,000 | 7; 14,000 |
| flat 0.75, seed 1 | 3,078 | 1,184; 1,241 | 6-11 | 35-39% | 327-421 | 34-44% | 4,250 | 24% | 1-2% | 35% | 5.6 +- 1.5 | 14 | 300,000 | 1; 151,000 |
| flat 0.75, seed 2 | 1,854 | 813; 875 | 9-16 | 34-39% | 228-273 | 38-46% | 2,140 | 22% | 0-2% | 32% | 4.0 +- 0.1 | 32 | 143,000 | 7; 60,000 |
| flat 0.75, seed 3 | 1,702 | 779; 846 | 12-22 | 33-41% | 220-274 | 36-50% | 2,100 | 20% | 1-3% | 34% | 4.5 +- 1.1 | 32 | 158,000 | 11; 19,000 |

- **The world stands through the dark winter, in the valley.** At 2 the floors are 673-1,230
  bodies with 2-10 lineages, at 3 (72% of the cells dark) 364-476 with 2-7; the flat season at
  1 is 8-22 with 0-2. At the same world sun the flat season holds 779-1,351 with 6-22 lineages
  spread over every band: the winter by height holds as many bodies in a third of the space,
  with fewer lineages on the floor.
- **The bodies move with the season.** The valley (a third of the cells) holds 68-90% of the
  bodies at every floor; the ridge holds 17-124, and 58-100% of them were born in the valley or
  on the slope. Every summer the ridge is refilled to 16-24% of the peak, and its summer bodies
  are 75-80% its own (born there). In the flat world the valley holds 33-41% at the floors and
  the ridge's bodies are 34-50% born elsewhere, the same at every season. The migration is a
  wave of the whole world, not a specialist's: at the equinox every large lineage stands in
  all three bands.
- **The tooth is back where the winter crowds the valley.** In `high 2` seed 1 the bodies that
  can bite are 24-37% of the world through the second half (the flat world: 0-3%; e030 and
  e031 under `grow`: gone): a column of muscle and gut at density 2 (mass 12-14, side 6-10,
  flesh 47-54% of its intake, a third of its members with a hard block) held the top place
  from 40,000 to the end in three kin lineages, beside a light gut wedge (6 guts at density
  1.1, mass 7, 13-16% flesh) that lived 277,000 steps: two kinds of body, 260,000 steps
  together. `high 2` seed 3 is held all 300,000 steps by a bar of 15-17 guts across two rows
  (mass 22, hard blocks in a third of its members) with biters up to 32%; `high 3` seed 3
  has 5-22%. The other seeds are e030's light gut and dense block.
- **The ridge's bodies differ from the valley's in three runs of six.** At the equinox the
  ridge's bodies carry more hard and muscle than the valley's (`high 2` seed 3: hard 7.5
  against 3.6, muscle 7.8 against 5.4, biters 29% against 14%; `high 3` seed 2: mass 26
  against 20); in the flat world the bands hold the same body.
- **Bodies, side, mass.** Bodies 1,935-4,207 (flat 1,702-3,078); side 5-10 (flat 4.0-5.6);
  mass p50 10-28 (flat 14-32). The fat per body is 5-17 (flat 13-28).

## Conclusion

1. **The world stands through the dark winter: yes.** Floors of 673-1,230 bodies at amplitude
   2 and 364-476 at 3 with 2-10 lineages, where the flat season at 1 gives 8-22 with 0-2. The
   floor is a place's capacity (296-310 in five winters of the pilot at 3), not a lottery.
2. **The bodies are in the valley at midwinter and on the ridge in summer: yes.** The valley
   holds 68-90% of the floor's bodies, the ridge's winter bodies are 58-100% born below, and
   the ridge is refilled every summer.
3. **More than one winner: in one seed of three,** two kinds 260,000 steps together (a flesh
   column with a tooth, a light gut), and the tooth back at 24-37% of the bodies; elsewhere
   e030's two bodies, and the lineages spread over every band.

Kept: the season world from here is `winter high` at amplitude 2 (the argument's default
stays `flat`, e031 byte for byte). What the law changed: the dark winter is somewhere, the
bodies leave it, and the crowd it makes in the valley brought the tooth back once. What it
did not: no body lives on the ridge through the winter (the ridge is refilled from below,
not held), and no lineage is a place's. The valley is the best place in every season but the
summer; the next law makes the ridge worth something: e020's rain on the mountains (`rain
high`, already an argument) under this winter, so that the wet ground is where the sun goes
out - a trade-off between places, and a body that carries a store up in spring.
