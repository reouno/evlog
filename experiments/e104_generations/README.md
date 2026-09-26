# e104: generations inside a stand (#116, rung 2)

Date: 2026-09-26

## Purpose

e103 built rung 2 - producers as evolving cohorts, small eaters with keys - and the world stood and sorted its
founders by place, but no producer evolved: a stand never died of age, so a slot freed only after a disaster and the
parent's own seeds won it back (0% of the biomass born after the sowing, 116,000 mutants made and lost). This
experiment changes that one law and asks rung 2's question again: **do many producer forms arise, hold by place and
keep changing, while the world stands?**

## The change (design in #116, the e104 comment)

- **A cohort is an age class**: the plants of one genotype that established together. It ages and dies whole when
  its age passes its **lifespan**, set by its own wood: `1 + life_max x toughness(wood's A share) x wood's share of
  its mass`, `life_max` 300 years. A stand with no wood is an annual; a tree of tough wood lives decades to centuries.
  A long life is paid in A and in wood.
- **A free slot is won by lottery** among the seed bank's genotypes, each by its seeds' number x their survival in the
  cell's shade and dryness (e103: the best took it). A mutant (10% of one release) gets about a tenth of its parent's
  chance; an immigrant its share. A full cell is still entered only by seedlings heavier than its lightest stand.

**The cycle**: slots take from the bank, the bank is refilled by the stands' seeds and by wind and rivers, and the
lifespan limits how long a genotype holds a slot without winning it again. Expected balance: long-lived tough woods
where A suffices; annuals and short lives where fire, frost, drought or eaters kill early, since their seeds refill
the bank faster.

Everything else is e103's: its crate copied (its producers are not in `base/` yet), its laws, rates and seeds.

## Hypothesis

e103's five lines, unchanged, on the same world (c1225, 256 random producer genomes and 64 eater genomes sown in year
10, run to year 310, `life` 1 and 2), read by e103's `measure.py`:

1. **The ledgers close**: water, A, B and the living's matter, to 1e-9.
2. **The world stands**: producers hold >= 50% of the land and >= 20% of the sea in each of the last 50 years, and
   the land's biomass drifts < 1% a year.
3. **Forms hold by place**: >= 5 effective groups, and the NMI of a land cell's leading group against its place >= 0.2.
4. **They keep changing**: the leading genotype changes >= 3 times in the last 100 years, and a group whose leader was
   born after year 160 holds >= 1% of the biomass at the end.
5. **The living change the ground**: land evaporation differs from e102's bare ground by >= 10%, and the soil's A:B
   map correlates < 0.8 with e102's.

And the mechanism engages: genotypes born after the sowing hold a growing share of the producers' biomass.

## Method

    cargo run --release -p e104_generations -- experiments/e104_generations/results/c1225_life1 \
        base/worlds/c1225.params years=310 life=1 threads=5

A pilot to year 25 (not kept): the ledgers close, the land fills as in e103, and the founders' lifespans run 29-83
years (quartiles) with a mass-weighted age of 9 at year 25, so the first generations turn over from about year 40.

**First batch stopped by the rule at year 100** (`mutant_share` 7.5e-7 against 1e-4; not kept). Stands did turn
over (mass-weighted age 25 against a lifespan of 51), but the slots went back to the parents' genotypes: e103's
mutation - 1 release in 500 giving a tenth of itself to a mutant, deposited only in its own cell - makes 2 seeds in
10,000 new, and those small packets are the first a full seed bank evicts. **Changed** (a precondition, before any
measure was read): a mutant is a whole release, carried by wind and rivers like any other, `p_mut` 0.01 (1 seed in
100; a genome of ~300 bases). The genotype table is boxed so that ~40,000 new genotypes a year fit in memory. A
pilot to year 60 (not kept): mutants hold 0.1% of the biomass from year 15 on and lead cells (369 leading genotypes
against 256 founders), a share that holds rather than grows over 50 years.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `c_err` > 1e-6 at 142560
- `land_cover` < 0.01 at 356400
- `mutant_share` < 0.0001 at 1188000

(a row a year of 11,880 steps; the last rule at year 100: the mechanism never engages.)

**Cost.** As e103: ~21 s a year, two runs at once on 5 threads each, **~2 hours, 10 of the 12 cores**.

## Result

Two runs, 310 years each, 8,248 and 8,214 s on 5 threads (~26 s a year). Read by `measure.py` (e103's, copied, with
the mutants' share and the lifespan added to `results/years.csv`; thresholds in `results/provenance.csv`). The
censuses live on disk as `.zst`, the maps are rebuilt by the runs.

| | run 1 | run 2 | line | verdict |
|---|---|---|---|---|
| H1 ledgers (worst year: water, A, B, matter) | 7e-14, 3e-13, 3e-13, 4e-12 | 1e-13, 3e-13, 3e-13, 6e-12 | 1e-9 | **yes** |
| H2 land / sea held (least of the last 50 years); biomass drift | 90% / 38%; +0.1% a year | 90% / 42%; +0.04% | 50% / 20%; 1% | **yes** |
| H3 effective groups (last 50 years); leading group against place (NMI) | 7.8; 0.28 | 7.6; 0.23 | 5; 0.2 | **yes** |
| H4 changes of the leading genotype (last 100 years); late groups at 1% | 0; 1 (3.8%) | 0; 0 | 3; 1 | **no** |
| H5 land evaporation against bare ground; soil A:B map against e102's | -4.3%; 0.29 | -1.7%; 0.33 | 10%; < 0.8 | **no** (the soil yes, the water no) |

**The producers evolve.** Genotypes born after the sowing hold 0.1% of the biomass at year 60, 1% at year 120 and
12% at year 300 in both runs, rising faster each century (0.012, 0.049, 0.119 at years 120, 210, 300 in run 1). They
are 553 and 539 of the 618 and 588 genotypes in the last census. The groups fall from the founders' 16-35 to 5.8-6.7
by year 110 and climb again to 8.0 by year 310 as mutants found new ones (e103: 3.3 and 5.5, flat).

**What the mutants changed**, by biomass at year 310, against the surviving founders: in both runs twice the defence
compound (0.75% against 0.37% of leaf mass; 1.23% against 0.61%), seeds 1.7-2.2 times heavier, a temperature optimum
2.4-6.6 C warmer. Beyond that the runs part: run 1's mutants live 24 years against 59 (less, softer wood), run 2's
put 33% of growth into leaves and 33% into seed against 21% and 22%, and 11% into store against 24%.

**H4 fails by its own measure.** The heaviest single genotype is one founder throughout in both runs, because the
new forms are spread over hundreds of small genotypes. One group founded after year 160 holds 3.8% in run 1; none
holds 1% in run 2.

**The ground.** 90% of the land held, the tallest stands at 33 m (run 1, 99th percentile; e103: 9 m). Transpiration is
44-51% of the land's evaporation, the total within 4% of the bare ground's and the runoff at 10%; the soil's A:B map
correlates 0.29-0.33 with the bare ground's. **The eaters** are 94-99% new genotypes; producers' compounds lie
1.1-1.8 bits from the nearest eater key. **History**: the two runs share 32% of their biomass in matching groups.

## Conclusion

**With generations inside a stand the producers evolve, and the world holds twice e103's groups, each by place**
(H1-H3 yes). H4 fails as written: the leading genotype does not change within 300 years, and the line reads one
genotype while evolution here spreads over many - a later reading of change should follow groups and when they were
founded. H5 fails on the water: the living remake the soil but not the land's water balance, and the thin rivers
(runoff 10%) are the climate's, not the producers'.

The law is kept: the world stands with it and its new freedom is used (decision rule 6). **e104's producers go into
`base/`** (their own commit). The rate of evolution is set by the generation (decades), so 12% after 300 years is a
beginning; seeing forms replace each other, and keys and eaters race, needs runs of a millennium, and a year costs
26 s today (13 of them the climate's, on one thread).

`vision.md`: layer B rows and section 5.
