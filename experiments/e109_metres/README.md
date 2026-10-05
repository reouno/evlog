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

(to be written)

## Conclusion

(to be written)
