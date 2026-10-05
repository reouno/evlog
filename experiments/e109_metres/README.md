# e109: rung 2 on the small world - the producers' distances in metres (#128)

Date: 2026-10-05

## Purpose

Rung 2's producers (e103-e105, in `base/`) stand, sort by place and evolve on the planet, where a cell is 63 km and
every distance they cross is counted in cells: a winged seed goes 20 cells, a fire crosses to a neighbour with a
chance, an eater moves up to five cells. On the small world (#126; the ground stands on it, e108) a cell is 125 m
and a cohort a stand of 1.6 ha, so those rules say something else. This experiment writes every distance the living
cross in metres and asks rung 2's question again on the islands: **do producers stand, sort by place and keep
changing?** It also reads what e108 left open: whether the islands' rain (x15), height (10 C) and light (x2.3) are
places to the living, and whether the soil's fill differs once stands draw on it.

## The cycles (written before the run)

The laws stay (e103, e104). A cell is only where a thing lands: it leaves from anywhere in its cell, goes its
distance in metres and lands in the cell under it, so a distance shorter than a cell crosses an edge by its share.
Each rate is set from its units and none is searched.

- **Seed on the wind.** A seed falls from its stand's height at its own speed and the wind (the air's own, 5.5 m/s,
  its direction the day's) carries it all the while: distance = height x wind / fall. A bare seed falls as a ball of
  water's density, 7.9 m/s at 0.01 g and by its mass to the 1/6; a wing is a membrane of 30 g a m2 whose drag adds to
  the ball's, so a seed that is 30% wing falls at 0.64 m/s whatever its mass (a maple's key: ~1). A 30 m stand
  throws such a seed 260 m in the mean, a grass of 0.5 m throws it 4 m; each of a release's three packets meets a
  gust of its own (an exponential draw about the mean), so a few go ten times as far. *Takes* seed mass from the
  reserve (a wing is not reserve) and wood for the height; *limited* by the fall: nothing low goes far.
- **Seed that falls near** lands within about its stand's height: the share `height / (pi x 125 m)` crosses each
  edge of its cell (5% for a 20 m stand, 0.1% for a grass). The planet's rule gave 7.5% an edge to any stand.
- **Seed down a river** floats 2 km a unit of `float` in the mean (a stream runs 1 km in an hour; the float buys the
  time before it strands), down the drainage network, or to the sea.
- **Seed in the sea** is scattered by the sea's own mixing, the one that mixes its nutrients (`sea_mix`): 0.86 km
  along each axis between two releases (16 days). No new rate.
- **Fire** runs a length: 2 km in the mean (0.1 m/s for an afternoon; a draw about it) through dry, ample fuel
  before the weather ends it, and less far by the fuel's dampness and thinness (the cost of a cell is its 125 m
  over `dry x fuel / (fuel + fuel_half)`). The planet's rule - a chance to cross to a neighbour - burns everything
  dry that touches at 125 m. Lightning is a rate an area: 0.1 strikes a km2 a year that would light dry fuel (of ~3
  flashes; most come with rain), 41 a year on this land. *Takes* litter and low leaves, *refilled* by growth,
  *limited* by its own ash: burnt ground has no fuel.
- **Small eaters** leave at the same rate (`eater_disp`); what leaves flies 300 m in the mean any way and the wind
  carries it as far again. The planet's rule moved it one to five cells.

**The balance expected.** Tall winged forms take open ground first; low forms spread a cell a few years. A stand's
neighbours are its own seed's, so forms hold ground in patches and meet at fronts; the sea between islands (2.3-32.5
km) is crossed by wind almost never, so each island keeps what was sown on it and what arises there. Where stands
draw the soil down (the lee lowlands, 53-250 mm of rain a year) the fill falls, fuel dries, and fire opens ground
there and not on the wet heights.

**What a planet's run would do with these laws**: the same code runs c1225, where a seed's metres never cross a 63
km cell - rung 2 on the planet (e103-e105) is read from its own crates, not from this one.

## Hypothesis

e104's five lines, unchanged, on `isles1` (256 producer genomes and 64 eater genomes sown in year 10, run to year
310, `life` 1 and 2), read by `measure.py` (e104's, copied):

1. **The ledgers close**: water, A, B and the living's matter, to 1e-9.
2. **The world stands**: producers hold >= 50% of the land and >= 20% of the sea in each of the last 50 years, and
   the land's biomass drifts < 1% a year.
3. **Forms hold by place**: >= 5 effective groups, and the NMI of a land cell's leading group against its place >=
   0.2 - against e102's label (the planet's line, for comparison) and against **the islands' own label**: the
   terciles over the land of the year's rain, temperature and light (27 places).
4. **They keep changing**: the leading genotype changes >= 3 times in the last 100 years, and a group whose leader
   was born after year 160 holds >= 1% of the biomass at the end. (e104 failed this line as written while mutants
   reached 12% of the biomass; read beside it: the mutants' share over time.)
5. **The living change the ground**: land evaporation with transpiration differs from e108's bare ground by >= 10%,
   and the soil's A:B map correlates < 0.8 with e108's.

**The plan's turn (#116)** is read from H3's second label: if the leading group does not follow the islands' rain,
temperature and light (NMI < 0.2), the islands do not make places and the remedy is the climate's.

Read beside them, named before the run:

- the NMI against each of rain, temperature, light, A:B and fertility alone (terciles), and against the island;
- over the land's cells, the correlation of the leading genotype's temperature optimum with the cell's temperature,
  and of its standing height with the cell's rain;
- the land's share in e102's dry, middle and wet bands of the soil's fill (bare: 0.5%, 1.5%, 98%) and e102's
  effective places with the living on it (bare: 4.5);
- the share of the land burnt a year; the runoff's share of the rain (bare: 96%) and the transpiration.

## Method

`base/` copied; `src/life.rs` (the seeds, the fire, the eaters, where a thing lands), `src/climate.rs` (the wind as
m/s for the living) and `src/main.rs` (the parameters) changed.

    cargo run --release -p e109_metres -- experiments/e109_metres/results/isles1_life1 \
        experiments/e109_metres/worlds/isles1.params years=310 life=1 threads=6

A pilot first (one run to year 40, not kept): the ledgers close, the land fills, seeds cross cells, fires stay
fires. Then two runs, `life` 1 and 2. All runs on Ubuntu (`ssh leo`).

**The pilot** (`results/pilot/`, not kept; 922 s): the first ten years are e108's to the digit, the ledgers close
(4e-12), the land is 93% covered at year 40, the leading genotypes gain cells (one from 1,657 to 5,349 leading cells
in 30 years), mutants hold 0.3% of the biomass, and 0.4% of the land burns a year (1.1% of the driest third, none of
the wettest). No rate was changed after it. **Seen before the batch, and left as it is**: the sea's producers hold
the islands' waters only - 98% of the sea within 0.5 km of land, 26% of it 2-8 km out, none beyond 8 km, where the
water holds a fiftieth of the nutrients - so the sea's cover falls (0.45 to 0.25 in 30 years) and H2's 20% of the
sea may fail. That is the ground's, not a distance: this sea is nine times the land and fed by its rivers alone.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `air_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 142560
- `land_cover` < 0.01 at 356400
- `mutant_share` < 0.0001 at 1188000

(a row a year of 11,880 steps; the last rule at year 100: the mechanism never engages.)

**Cost.** The pilot: one run, 6 threads, about 15 minutes. The batch: two runs at once on Ubuntu's 6 cores, about
25 s a year (the air's pass is 9 s of it on one thread), **~2.5 hours**. What it buys: whether rung 3 can be
designed on this ground.

## Result

Two runs, 310 years each, 10,703 and 10,587 s on 5 threads on Ubuntu (34 s a year with both running; alone, 26 s).
Read by `measure.py` (`results/measure.csv`, a row a census year in `results/years.csv`, a row a large island in
`results/islands.csv`; thresholds in `results/provenance.csv`). The censuses live on disk as `.zst`, the maps are
rebuilt by the runs.

| | run 1 | run 2 | line | verdict |
|---|---|---|---|---|
| H1 ledgers (worst year: water, A, B, matter) | 7e-13, 1e-12, 8e-13, 5e-12 | 5e-13, 7e-13, 7e-13, 6e-12 | 1e-9 | **yes** |
| H2 land / sea held (least of the last 50 years); biomass drift | 96% / 46%; +0.05% a year | 98% / 47%; -0.17% | 50% / 20%; 1% | **yes** |
| H3 effective groups (last 50 years); leading group against place (NMI): the planet's bands, the islands' own | 8.1; 0.12, 0.09 | 7.4; 0.13, 0.09 | 5; 0.2 | **no** |
| H4 changes of the leading genotype (last 100 years); late groups at 1% | 0; 0 | 1; 0 | 3; 1 | **no** |
| H5 land evaporation with transpiration against bare ground; soil A:B map against e108's | +170% (198 against 73 mm); 0.35 | +126% (166 mm); 0.44 | 10%; < 0.8 | **yes** |

**The world stands.** The land fills in forty years (2.5 and 1.4 kg a m2 at the end, stands to 21 m at the 99th
percentile). The sea did not fail as the pilot suggested: its cover falls to 23% and 25% in years 54 and 53 and climbs to
50% and 53% at year 310 (the sea's biomass is 11 and 8 times year 60's).

**It is not settled.** The groups are still falling at year 310 - 17.8 and 27.8 at year 20, 11.8 and 7.7 at year
140, 7.7 and 6.8 at the end - where the planet's fell to 6 by year 110 and climbed again. The same count as the
planet's (7.8 and 7.6 at year 310, e104) is a world on its way down, not at rest.

**The land is a mosaic of what was sown.** 384 and 166 genotypes still lead a land cell at year 310, the twenty
largest holding 90% and 96% of the land. Read every 30 years (`sorting.py`, added after the batch was read;
`results/trend.csv`): neighbouring cells share a leader in 19% of pairs at year 20 and 66-69% at year 310, and the
leading group's NMI against the planet's bands rises without a pause, 0.06 to 0.12 and 0.07 to 0.13 - half of the
planet's 0.28 and 0.23. Against the islands' own label it is 0.09 in both; alone, rain gives 0.06, temperature 0.06-
0.07, light 0.02-0.03, the soil's A:B 0.08-0.13, fertility 0.08-0.13, and the island a cell lies on 0.16 and 0.12.
The leader's temperature optimum follows the cell's temperature at r 0.13 and 0.17, its height the rain at 0.19 and
0.21. One group leads four of the five large islands in run 1 and all five in run 2.

**Do places exist for these producers?** (`results/leaders.csv`, read after the batch.) Among the twenty leaders,
over the nine places of rain x temperature, the median leader has 36% and 40% of its ground in one place. Of the
difference in standing biomass between (leader, place) pairs, the leader alone gives 31% and 58%, the place alone
40% and 10%, and 35% and 20% is neither's alone; the better of two leaders changes with the place for 24 of 122
pairs in run 1 and 6 of 85 in run 2.

**They evolve, slowly.** Genotypes born after the sowing hold 1.4% of the biomass in run 1 (1.5% at year 110 and
flat since) and 5.8% in run 2 (rising 0.9% every 30 years), against the planet's 12%. The heaviest genotype is a
founder throughout; it changes once in run 2's last century. The two runs share 41% of their biomass in matching
groups (the planet: 32%), and differ by x1.8 in the land's biomass.

**The ground under the living.** 5% and 4% of the land's soil is under a third full and as much between one and two
thirds (bare: 0.5% and 1.5%), and the planet's bands count 9.9 and 8.1 places on the land (bare: 4.5; the planet:
15.4). Fire follows the dry ground: 1.3% and 0.5% of the land burns a year, 3.7% and 1.4% of its driest third and
0.006% and 0.003% of its wettest; the largest island burns 3.3% a year in run 1. Transpiration is 153 and 115 mm a
year; 88% and 90% of the rain still runs off (bare: 96%). The small eaters take 13% and 11% of what is fixed at the
end (5-6% at year 60) and are 89-92% new genotypes.

## Conclusion

Holds for this one world (isles1), two seeds of the living, 300 years after a sowing that put two random genomes of
256 in every cell.

- **Producers stand on the small world with their distances in metres** (H1, H2, H5): every ledger closes, the land
  and half the sea are held, and the living remake the ground more than on the planet - the soil dries where stands
  draw on it and fire lives on that ground only. The rewritten distances go into `base/`.
- **They have not sorted by place in 300 years** (H3 no): NMI 0.12-0.13 against the line's 0.2 and the planet's
  0.23-0.28. By the letter of the plan (#116) that is the islands not making places, and its remedy the climate's.
  **The runs do not support that reading, and the turn is not taken on them**: the sorting rises through all 300
  years, the mosaic coarsens, the groups still fall - the world is read in its transient. On the planet a seed
  crossed 20 cells of 63 km in one release, so every form reached every place within years; here a form reaches its
  place a few cells a decade, and what grows where is still mostly what was sown there.
- **Places exist for producers, weakly**: leaders concentrate in a place and the better form changes with the
  place for a fifth of pairs in one run and a fourteenth in the other. Whether that carries the NMI past 0.2 is not
  known; nor is how much of the sorting on the planet was its climate and how much its seeds' reach.
- **They evolve at a seed's pace** (H4 no): a mutant's seeds stay near, and 1.4-5.8% of the biomass is new after
  300 years.
- **What a small world cannot hold, so far**: a carrier. Nothing takes a seed a kilometre but a rare gust; the sea
  between islands is crossed by none that shows (one group leads nearly every island because all were sown alike,
  not because it arrived). In the island's design the carriers are bodies (fruit, seed eaten and dropped) - not built.
- **Open for the plan (#116), before bodies**: where the sorting ends. One run of a millennium on this ground (7-8
  hours on Ubuntu) would say whether the NMI passes the line and whether the groups level; the climate's remedy
  (the sea air's share of a cell's temperature, the latitude) is judged after that, not on this transient.
- **Cost**: 26 s a year alone (the air's pass 8.5 s on one thread, the cells 8 s, the eaters' flight 2.5 s).

`vision.md`: rows A and B, a lesson (a law's distance against the cell). `foundation.md`: the producers' and small
eaters' laws, rung 2's reading, today's world, compute.
