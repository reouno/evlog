# e085: the regions over stage A's climates (#98)

Date: 2026-09-19

## Purpose

e084 counted the regions a world holds apart from its producers-only map, and of the six worlds with stage
A/B params c1225, the one stage C runs on, held the most (5.03 effective; the next 2.2). Whether kinds rise
with regions across worlds needs a world with clearly more regions than c1225, and none of the six is one.
Stage A passed 34 climates, and the count needs only the ground's fill and the temperature by quarter, which
stage A's climate makes. This asks the cheapest layer (`foundation.md`): does any of stage A's climates hold
clearly more regions than c1225? (`balance.md` section 20.)

## Hypothesis

1. **The climate alone gives c1225's map.** e061's climate is e062's (the same update; the producers do not
   touch the ground's water), so e061's map of c1225 gives the same regions as e062's producers map, and a
   climate's regions can be counted without its producers.
2. **A few climates hold more regions than c1225.** Dense land breaks into pieces where the ground is
   middling dry and some of it hot all year (e084). Among 34 climates, 1-3 hold effective 8 or more; they
   have a middling yearly dryness (0.5-0.7) and a large land; wet climates hold one piece, dry ones none.
3. **Kinds follow the regions** (only if a climate holds effective 8 or more): today's default world on it
   holds more kinds than on c1225, with its predicted regions held by different lines.

## Method

- **Maps** (`maps.sh`). e061's binary with `maps=1` on the 34 climates that passed all four of stage A's
  lines, with their lines from e061's `candidates.txt` (20 years, the search's run; each row must match the
  search's). 10 at once on the Mac, about 1.6 core-hours. Each map holds the last year by quarter: the
  habitat, the temperature, the ground's fill (at most 1) and the rain.
- **The check.** e061's map of c1225 against e062's (`e062_producers/results/pass/c1225_d11_maps.bin`,
  after 20,000 updates of spin-up and 200,000 steps of producers): each 8 x 8 block's yearly dryness and
  coolest-quarter temperature, and the regions counted on each.
- **Count** (`regions.py`, e084's rule and calibration unchanged: c1225's control density by dryness and
  coolest-quarter class; a block is dense at 0.03 bodies a land cell, 0.025 and 0.035 as a check; a region is
  a 4-connected piece of 10 or more dense blocks; the effective number is exp(entropy) of the rooms' shares).
- **Bodies**, only if a climate holds effective 8 or more: its producers with draw d11 (e062, about 5
  minutes), the regions recounted on that map, then today's default world (e082's binary, `unit` 0, `fresh`
  0.05) on seeds 9-11 at 100,000 steps against e081's control ladder on c1225; judged by kinds and by the
  regions held (the leader's share in a region under a fifth).

**Wrong if** the climate's map of c1225 gives different regions from the producers' map (then counting from
stage A's maps is not the same count), or, for step 3, if the predicted regions are not held apart by
different lines or kinds do not rise with them.

**Runs made** (all on the Mac): the 34 climate maps, 10 at once, 18:40-18:51 on 2026-09-19 (1.5 core-hours;
17-437 s each; every row matches the search's). Because none held 8 effective regions, the bodies step was not
run. One check beyond the plan, to inform the next step: c1288's producers with draw d11 (`maps=1`, 5 minutes on
one core; `results/producers/`, its params in `results/worlds/c1288.params`, written as e062's `search.py` writes
them):

    ./target/release/e062_producers experiments/e085_climate_regions/results/producers/c1288_d11 \
      experiments/e085_climate_regions/results/worlds/c1288.params \
      grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06 maps=1

## Result

`regions.py` runs in about a minute; its printout is `results/regions.txt`.

**The check** (c1225, 1,728 blocks at least half land, the same blocks on both maps). The climate's map and the
producers' map agree block by block: yearly dryness at a correlation of 0.999 (mean 0.613 against 0.614, largest
gap 0.10), the coolest quarter at 0.9999 (9.90 C against 9.91 C), and 99.8% of the blocks on the same side of the
dense line. The regions are the same:

| c1225 | dense 0.025 | dense 0.03 | dense 0.035 |
|---|---|---|---|
| climate map (e061, 20 years) | 5 regions, 3.66 | 8 regions, 5.03 | 8 regions, 4.70 |
| producers map (e062 d11) | 5 regions, 3.66 | 8 regions, 5.03 | 8 regions, 4.70 |

**The 34 climates** (effective regions at the dense line 0.03; the ten with the most, then the other worlds e062
ran; all 34 in `results/regions.csv`):

| climate | size | land share | land temp | rain on land (mm) | dryness | coolest quarter | predicted bodies | regions (5%+) | effective (0.025 / 0.03 / 0.035) | largest | land masses (effective) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c1288 | 512 | 0.21 | 3.7 C | 693 | 0.43 | -6.3 C | 2,125 | 11 (6) | 7.50 / **7.53** / 7.53 | 29% | 5 (3.25) |
| c1251 | 512 | 0.32 | 8.2 C | 497 | 0.46 | -5.8 C | 3,382 | 9 (5) | 5.00 / **5.22** / 5.22 | 48% | 2 (1.60) |
| c1225 | 512 | 0.42 | 21.2 C | 3,693 | 0.61 | 9.9 C | 3,680 | 8 (4) | 3.66 / **5.03** / 4.70 | 47% | 2 (1.21) |
| c1151 | 512 | 0.46 | -1.1 C | 82 | 0.72 | -12.3 C | 1,511 | 7 (7) | 6.36 / **4.39** / 4.46 | 55% | 1 (1.00) |
| c1255 | 512 | 0.33 | 2.2 C | 29 | 0.79 | -13.2 C | 734 | 4 (4) | 3.68 / **3.70** / 2.77 | 43% | 2 (1.63) |
| c1269 | 512 | 0.28 | 2.2 C | 106 | 0.65 | -7.6 C | 1,568 | 5 (4) | 3.74 / **3.63** / 3.61 | 42% | 2 (1.17) |
| c1072 | 512 | 0.33 | 30.9 C | 1,743 | 0.61 | 19.4 C | 3,083 | 8 (3) | 3.51 / **3.37** / 6.02 | 59% | 6 (3.22) |
| c1044 | 512 | 0.25 | 21.8 C | 145 | 0.79 | -0.8 C | 771 | 4 (4) | 5.67 / **3.34** / 2.61 | 47% | 2 (1.86) |
| c1192 | 512 | 0.34 | 17.5 C | 131 | 0.74 | -9.4 C | 1,419 | 4 (4) | 3.32 / **3.27** / 3.24 | 47% | 2 (2.00) |
| c1252 | 512 | 0.32 | 14.5 C | 1,129 | 0.63 | -14.0 C | 2,037 | 7 (3) | 1.81 / **3.25** / 3.27 | 64% | 1 (1.00) |
| c1208 | 512 | 0.56 | -4.2 C | 128 | 0.48 | -6.8 C | 4,614 | 5 (2) | 2.17 / **2.21** / 2.20 | 78% | 1 (1.00) |
| c1221 | 512 | 0.41 | 13.4 C | 769 | 0.74 | 5.9 C | 2,146 | 3 (2) | 1.54 / **1.44** / 1.47 | 91% | 2 (1.14) |
| c1236 | 512 | 0.64 | 3.3 C | 389 | 0.38 | -1.2 C | 7,380 | 3 (1) | 1.23 / **1.23** / 1.23 | 95% | 1 (1.00) |
| c1182 | 512 | 0.50 | 28.9 C | 1,928 | 0.59 | 16.7 C | 4,571 | 2 (1) | 1.05 / **1.04** / 1.00 | 99% | 1 (1.00) |
| c1173 | 512 | 0.68 | 30.8 C | 490 | 0.92 | 15.0 C | 551 | 0 | 0 | - | 0 |

(The six worlds e062 ran give the same numbers from the climate's map as e084 gave from the producers' map,
within 0.01.) Over the 34: none at 8 or more, 3 at 5 or more, 9 at 3-5, 18 at 1-3, 4 deserts with none; the median
is 2.0. "Land masses" are the 4-connected pieces of blocks holding any land that hold the regions: 8 of c1288's 11
regions share a land mass with another, and its two largest masses (42% of the room each) hold 3 and 5 regions,
so c1288 is broken both by the sea and on land.

**What holds more regions** (rank correlation with the effective number over the 30 climates at 512): a smaller
land share (-0.57) and a colder coolest quarter (-0.45), a higher relief (+0.36) and a wider latitude span
(+0.37). Not the mean dryness (-0.06) or the rain (-0.09): a climate breaks into pieces where its land is small
and cold, not where it is middling dry.

**c1288's producers** (d11, 10 years after e062's 20,000-update spin-up): grass 47%, wood 42% and algae 10% of the
standing matter, 3.4% of the land burnt a year, matter conserved (1.8e-14). It fails one of stage B's lines: wood
is the larger part of no habitat (grass of 3, algae of 1). Its regions on the producers' map are the climate's
(11, effective 7.90 / 7.53 / 7.53).

**The hypotheses:**

1. The climate alone gives c1225's map: **yes** (5.03 effective regions from either map; dryness 0.999).
2. A few climates hold more regions than c1225, with middling dryness and a large land: **no**. None holds 8;
   the most, c1288, holds 7.53 (1.5 times c1225's), and c1225 is third of 34. The ones that hold more have a
   small, cold land, and the dryness does not predict the count.
3. Kinds follow the regions: **not run**, the pre-set condition (effective 8 or more) was not met.

## Conclusion

Stage A made no climate with clearly more regions than c1225: of 34, only c1288 (7.5) and c1251 (5.2) hold more,
and c1225 is third. So among the worlds stage A can offer, c1225 is near the top for the regions a line can hold
apart, and a world that raises kinds by holding many more regions is not among them. The count itself is now
cheap and needs no producers: a climate's map from stage A gives the same regions as its producers' map.

What it changes: my picture of what divides a land was wrong. e084 found the dividing strips on c1225 were dry
and hot all year, and I expected middling dryness to make many regions; across climates it is a small and cold
land that does (land share -0.57, coolest quarter -0.45), and part of c1288's division is the sea. If regions do
raise kinds, a stage A search aimed at them would turn the land share down and the cold up. Whether they do is
still untested; the choice of the next step is a proposal (`balance.md` section 21).

Conditions: the calibration is c1225's, under today's default world (fresh 0.05, the heat band 15-30 C, land
bodies only); a region held apart by the sea counts as held, though stage C's bodies also live in water and may
cross it; the 34 are stage A's passing climates at its 20 years, and 4 of them are 256 cells wide.
