# e105: a millennium of evolving producers (#116, rung 2)

Date: 2026-09-27

## Purpose

e104 made producers evolve: stands that die at the lifespan their wood sets, slots won by lottery. In 300 years the
genotypes born after the sowing reached 12% of the biomass, rising faster each century, and the groups doubled - but
300 years is a few generations of stands that live decades, so whether new forms come to replace the old, and whether
defence keys and the eaters that carry detox keys race, was not yet readable. This experiment runs the same world
for a millennium. It changes no law: `base/` as it is (ae663ea, whose climate and water now run on threads, results
independent of the threads).

## Hypothesis

On c1225, 256 random producer genomes and 64 eater genomes sown in year 10, run to year 1010, `life` 1 and 2, read
by `measure.py` (e104's, copied; H4 and H5 rewritten before the run, as e104 concluded: H4 read one genotype while
evolution spreads over hundreds):

1. **The ledgers close**: water, A, B and the living's matter, to 1e-9.
2. **The world stands**: producers hold >= 50% of the land and >= 20% of the sea in each of the last 100 years, and
   the land's biomass drifts < 1% a year over them.
3. **Forms hold by place**: >= 5 effective groups over the last 100 years, and the NMI of a land cell's leading
   group against its place >= 0.2.
4. **New forms replace the old**: at year 1010 half of the producers' biomass is in genotypes born after year 510
   (the biomass-weighted median birth year), and groups whose leader was born after year 510 hold >= 25% of it.
5. **Keys race**: the producers' compound keys, as biomass over the 256 keys, differ between years 510 and 1010 by a
   Bray-Curtis dissimilarity >= 0.5, while the eaters stay within 2 bits of the producers' compounds at the end.

Read beside them: the groups and the mutants' share over time, the lifespans, heights, the land's water, the
replay agreement between the two runs.

## Method

    cargo run --release -p e105_millennium -- experiments/e105_millennium/results/c1225_life1 \
        base/worlds/c1225.params years=1010 life=1 threads=5

The same parameters as e104 (`base/`'s defaults and c1225's file). The first 310 years are not e104's again: the
threaded sums round in another order, and the world's weather then departs cell by cell.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 142560
- `land_cover` < 0.01 at 356400
- `mutant_share` < 0.0001 at 1188000

(a row a year of 11,880 steps.)

**Cost.** A year takes ~4 s of climate on 5-6 threads and ~6-8 s of life; two runs at once on 5 threads each, about
12 s a year: **~3.5 hours on 10 of the 12 cores**. What it buys: 1,000 years of evolution, three times e104's.

## Result

Two runs, 1,010 years each, 15,949 and 15,979 s on 5 threads (15.8 s a year with both running). Read by
`measure.py` (thresholds in `results/provenance.csv`, a row a census year in `results/years.csv`). The censuses live on
disk as `.zst`, the maps are rebuilt by the runs.

| | run 1 | run 2 | line | verdict |
|---|---|---|---|---|
| H1 ledgers (worst year: water, A, B, matter) | 2e-13, 4e-13, 3e-13, 4e-12 | 2e-13, 3e-13, 3e-13, 6e-12 | 1e-9 | **yes** |
| H2 land / sea held (least of the last 100 years); biomass drift | 90% / 64%; -0.04% a year | 90% / 71%; -0.07% | 50% / 20%; 1% | **yes** |
| H3 effective groups (last 100 years); leading group against place (NMI) | 9.1; 0.26 | 11.9; 0.19 | 5; 0.2 | **run 1 only** |
| H4 the biomass's median birth year; groups led by genotypes born after 510 | 10; 2% | 70; 35% | > 510; 25% | **no** |
| H5 keys' change 510-1010 (Bray-Curtis); eaters' distance to compounds | 0.27; 0.8 bits | 0.50; 1.1 bits | 0.5; 2 | **run 2 only** |

**Evolution never stops, but it does not replace.** Genotypes born after the sowing hold 0.8% of the biomass at year
110, 18% and 26% at 510, and 41% and 51% at 1010, gaining 4-5% a century at an even rate in both runs. The groups
climb with them, from 6.6 and 5.9 at year 110 to 9.7 and 11.7 at 1010, and the genotypes' Hill number reaches 50 and
68. But the heaviest genotype is the same founder from year 210 to 1010 in both runs (ids 136 and 26), and the heaviest
group holds 36% and 21% at the end.

**Selection has directions.** Against the founders still standing at year 1010, the mutants' temperature optimum is
8.4 and 7.0 C warmer, and they live 42 against 71 years and 47 against 59. Run 1's mutants carry 2.7 times the
compound and stand twice as tall (2.3 against 1.0 m); run 2's put a third of their growth into leaves and a third into
seed (22% each for the founders) and make seeds 2.7 times heavier.

**The eaters.** They take 6% of what the producers fix in run 1 and 12% in run 2 at the end (2.5% at year 60). The run
with more eating has more groups (11.9 against 9.1), more biomass in late groups (35% against 2%) and keys that change
twice as much (0.50 against 0.27). With two runs, a hint.

**The ground and the sea.** 90% of the land held; the sea's producers spread from 38-42% of the sea (e104, year 310)
to 64-71%. The soil's A:B map correlates 0.16-0.19 with the bare ground's; the runoff stays at 9-11%, the land's
evaporation within 8% of the bare ground's. The two runs share 53% of their biomass in matching groups (e104: 32%).

## Conclusion

**Rung 2 is done.** Its world stands for a millennium with every ledger closed; producers arise from mutation, hold by
place and keep diversifying (H1, H2, H3 on run 1). What it does not do is turn over (H4 no): once the founders have
sorted, the best form of a place keeps it, and evolution fills in around it at the pace of mutation. Nothing in this
world moves enough to overturn an incumbent - the climate repeats its pattern with yearly noise, fires and storms are
local, and eaters that take a few percent tilt it only a little; the run where they take 12% changes most (H5 on run
2). The world diversifies but does not turn over, and the pressure that would turn it - consumers that strip stands,
choose what they eat and cross places within a life - is rung 3's.

`vision.md`: layer B and F rows, section 5 (next: rung 3, the bodies).
