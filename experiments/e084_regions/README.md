# e084: the regions a generated world holds apart (#97)

Date: 2026-09-19

## Purpose

e083 found that the region other lines hold on c1225 is held by a barrier: a thin strip on the upper
continent's equator, between two dense lands, which lets few of the leader's bodies through. Where the lines
meet they breed alike. So kinds on this land follow, in part, the regions the generated land holds apart. This
asks the generated layer, with no law changed (`foundation.md`: search from the cheapest layer): how many
such regions do the worlds we have hold, and does a world with a different number hold a different number of
kinds? (`balance.md` section 19.)

## Hypothesis

1. **A map without bodies says where bodies will be thin.** On c1225 the producers-only map (e062) predicts
   the control's land bodies a cell block by block, and the regions it draws are the ones e083 saw held.
2. **Worlds differ in their regions.** The six worlds with stage A/B params hold different numbers of regions.
3. **Kinds follow the regions** (only if a world differs clearly from c1225 and can hold today's default
   world): more held regions, more kinds; fewer, fewer.

## Method

- **Maps.** e062's producers with draw d11 and `maps=1` on c1173, c1182, c1208, c1221 and c1236 (`maps.sh`,
  about 6 minutes on 5 cores; the maps, 24 MB each, are not committed); c1225's is e062's (`e062_producers/results/pass/c1225_d11_maps.bin`). Each map holds
  the producers' last year by quarter: the ground's fill, the temperature, grass and wood.
- **Calibration** (`regions.py`). Blocks of 8 x 8 cells. On c1225, the land bodies a land cell a census of
  e081's control (seeds 9-11, censuses 36,000-100,000) against the block's yearly ground dryness and its coolest
  quarter's temperature: the mean density of each class is the prediction for any world.
- **Regions.** A block is dense when its predicted density is 0.03 or more (about half of a dense land's); a
  region is a 4-connected piece of 10 or more dense blocks on the torus. Its room is its predicted bodies; the
  world's effective number of regions is exp(entropy) of the rooms' shares. The rule is first run on c1225's
  measured densities.
- **Bodies**, if step 3 applies: today's default world (e082's binary at `unit` 0, `fresh` 0.05) on the
  other world, seeds 9-11 at 100,000 steps, against e081's control ladder on c1225; kinds with e082's
  `sweep.py`, and the leader's share in each region.

## Result

The five maps took 5.3-6 minutes each on 5 cores. `regions.py` runs in about 20 seconds.

**The calibration** (c1225, 1,728 blocks at least half land). The control's land bodies a land cell follow the
ground's yearly dryness (correlation -0.93): 0.075 under 0.4, 0.045 at 0.5-0.55, 0.028 at 0.65-0.7, 0.013 at
0.75-0.8, none over 0.9. Within a dryness, the coolest quarter's temperature sets the rest: at 0.6-0.65, 0.018
where the coolest quarter is under 0 C, 0.044 at 20-25 C and 0.027 at 33 C or more. Both cold winters and a
year with no cool quarter thin the bodies. The two together predict the blocks' density at a correlation of 0.97.

**The rule on c1225.** Its first form (dryness alone, dense under 0.7, gaps of up to 4 blocks crossed) found one
region, and so did the same rule on the measured densities with any gap crossed. The thin strip e083 found is
only 1-2 blocks (8-16 cells) wide on the upper continent's west side, where a corridor of middling dryness
(0.61) is hot in every quarter (34.9-37.9 C, against a coolest quarter of 14.5 C on either side) and holds 0.027
bodies a cell against 0.051. The rule was changed before the other worlds were read: regions are 4-connected
pieces of dense blocks with no gap crossed, and the temperature is the coolest quarter's. Then:

| c1225 | regions of 10+ blocks | sizes (blocks) |
|---|---|---|
| on the measured densities | 7 | 332, 168, 129, 96, 52, 38, 27 |
| on the map's prediction | 8 | 321, 169, 133, 67, 55, 54, 50, 31 |

The predicted regions are the ones held apart in the control (seed 9's leader share in each): the lower
continent (97%), the upper south where the leader is still spreading (58%) and a piece of the lower east (44%);
the upper north (7%), the upper east's three pieces (7-10%) and an island (2%) are held by other lines.

**The six worlds** (dense at 0.03 bodies a cell; in brackets at 0.025 and 0.035):

| world | land cells | predicted bodies | yearly dryness | coolest quarter | regions (5%+ of the room) | effective regions | largest |
|---|---|---|---|---|---|---|---|
| c1225 (very wet) | 110,625 | 3,686 | 0.61 | 9.9 C | 4 | 5.03 (3.66 / 4.70) | 47% |
| c1208 (cold) | 138,178 | 4,616 | 0.45 | -7.6 C | 2 | 2.21 (2.17 / 2.20) | 78% |
| c1221 (mild) | 107,217 | 2,148 | 0.74 | 6.0 C | 2 | 1.44 (1.56 / 1.48) | 91% |
| c1236 (cool) | 168,004 | 7,430 | 0.37 | -1.3 C | 1 | 1.24 (1.24 / 1.24) | 95% |
| c1182 (hot wet) | 131,063 | 4,572 | 0.59 | 16.7 C | 1 | 1.04 (1.05 / 1.00) | 99% |
| c1173 (hot dry) | 176,948 | 513 | 0.93 | 14.9 C | 0 | 0 | - |

(The names are e062's; "very wet" is c1225's rain on land.) c1225 holds the most regions at every threshold. A
wet world (c1236) is one dense land; a dry one (c1173) has none; c1182, as dry as c1225 on the mean, puts its
dense land in one piece.

**The hypotheses:**

1. A map without bodies says where bodies will be thin: **yes** (correlation 0.97 on c1225), with the coolest
   quarter's temperature as well as the dryness; and its regions are the ones held apart in the control.
2. Worlds differ in their regions: **yes** (effective 0 to 5.03).
3. Kinds follow the regions: **not run**. No world holds more regions than c1225, which was the condition for
   the bodies step (`balance.md` section 19).

## Conclusion

A world's regions can be read from its producers-only map, at no cost in bodies: dense land breaks into pieces
where the ground is dry enough and some of it is hot all year, and the pieces are the regions a line holds
against another. Of the six worlds stage A and B left, c1225, the one stage C runs on, holds the most (5.0
effective; the next 2.2). So c1225's kinds are not held down by a poor land among these six, and among them
there is no better one to move to.

What it changes: the generated layer has a measure it lacked, the regions a land holds apart, cheap enough for
stage A's search (it needs the ground's fill and the temperature by quarter, which stage A's climate makes).
Whether kinds follow the regions across worlds is still untested; it needs a world with more regions than
c1225, which none of these six is.

Conditions: the calibration is c1225's, under today's default world (fresh 0.05, the heat band 15-30 C); a
world much colder or hotter than c1225 is read through classes c1225 has few blocks in.
