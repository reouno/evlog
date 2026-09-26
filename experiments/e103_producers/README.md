# e103: producers that evolve, and the small life on their leaves (#116, rung 2)

Date: 2026-09-26

## Purpose

The second rung of the redesign (#116). Rung 1 (e102) made a ground whose places differ by rock, water and
years. This rung puts life on it that can take different forms by place and that changes the ground back:
producers as evolving cohorts in the genome language the bodies will also read, and the small eaters that make
their defence keys matter. The question: **do many producer forms arise, hold by place and keep changing, while the
world stands?** If producers alone do not diversify over this ground, the premise fails early and cheaply.

## The design

Written in full in #116 (the rung 2 comment): the laws, the price of each freedom, the cycles and where they should
settle. In short:

- **Tissue chemistry.** Every organ (leaf, wood, root, store, seed) is dry matter with its own A and B shares, set
  by the genome. B is activity (photosynthesis, uptake) and costs respiration and makes the best food; A is
  toughness (longer life, resists frost, wilting, storms and mouths) and leaves less room for B.
- **The genome.** Genes of 16 bases (4 letters): a target of 256 addresses, a condition on a signal (day length,
  its trend, temperature, soil water, light, size, store, damage), a value. Traits sum their genes' values;
  duplication doubles a dose; conditional genes are plasticity (shedding, induced defence). `genome.rs`.
- **Laws** (`life.rs`): light through the leaves by height (Beer); carbon paid in water from the soil and, for deep
  roots, the groundwater, dearer for tall crowns and in dry air; A and B by active roots; growth in each organ's
  shares; losses to turnover, shedding, frost, wilting, storms; litter that decays by warmth, wetness and its own
  A:B; lightning and fire on dry land with fuel; seeds carried by the wind band, down rivers or nearby into seed
  banks, where a free slot is won by the bank's best; the same cohorts in the sea.
- **Small eaters**: cohorts with detox keys that eat leaves by their quality and are harmed by compounds whose key
  they do not carry; they spread on the wind and mutate their keys.

Every rate is one fixed value set by its units (`main.rs`, the `e103` block of parameters).

## Hypothesis

On c1225 (e102's ground), 256 random producer genomes and 64 random eater genomes sown in year 10, run to year
310. Read by `measure.py` over the censuses (`analysis/groups.py` groups genotypes by their traits):

1. **The ledgers close**: water, A, B (with the living), and the living's matter (fixed against respired, decayed,
   burnt), to 1e-9.
2. **The world stands**: in each of the last 50 years producers hold >= 50% of the land (> 0.01 kg a m2) and >= 20% of
   the sea (> 0.001 kg a m2), and the land's biomass drifts < 1% a year over them.
3. **Forms hold by place**: >= 5 effective groups (the old world had 3 producers, written by hand), and the
   normalised mutual information between a land cell's leading group and its place (e102's places, chemistry
   included) >= 0.2.
4. **They keep changing**: the genotype holding the most biomass changes >= 3 times in the last 100 years, and a
   group whose leader was born after year 160 holds >= 1% of the biomass at the end.
5. **The living change the ground**: the land's evaporation (soil and transpiration) differs from e102's bare
   ground by >= 10%, and the soil's A:B map correlates < 0.8 with e102's.

Read beside them: the keys (defended biomass, how closely eaters' keys follow producers'), burnt area, runoff
ratio, and the two runs against each other (the same terrain, two seeds of the living; #112).

## Method

`base/` copied as the rule is (`CLAUDE.md`); the climate gains two lines (the canopy shades the soil's evaporation,
storms are marked where they pass). Two runs, `life=1` and `life=2`:

    cargo run --release -p e103_producers -- experiments/e103_producers/results/c1225_life1 \
        base/worlds/c1225.params years=310 life=1 threads=5

**Set in the pilots, by their units, before the runs** (three pilots of 4-10 years, `results/` not kept):

- `uptake` 50 -> 2,000 and `root_draw` 100 -> 1,000 a year a kg of root: real roots take up ~100 g of nitrogen a
  kg a year and reach a soil's water within days; at the first values a seedling starved with nutrient in the soil.
- `eat` 20 -> 100 a year: a leaf-eating insect eats its own mass in days; at 20 the eaters' best growth was 2 a
  year and they died out before the leaves came.
- Frost reads the day's mean temperature, not its minimum: e061's day swings ~30 C, so every summer night froze.
- The sowing waits for year 10, so that the soils have gathered their nutrients (at year 1 they held 0.1 g).

The pilot at these values stood: ledgers 1e-13, the land's cover 74% and rising 10 years after sowing, biomass
following rain and warmth (0.68 kg a m2 over 5,000 mm, none under 300 mm), 11 effective groups, wet land short of A.

**Stop early if:**

- `water_err` > 1e-6 at 23760
- `a_err` > 1e-6 at 142560
- `c_err` > 1e-6 at 142560
- `land_cover` < 0.01 at 356400

(steps: a row a year of 11,880 steps; the life ledger from year 12, the cover at year 30.)

**Cost.** A year takes ~13 s of climate and ~7 s of life (8 threads); two runs at once on 5 threads each, about
25 s a year: **~2.2 hours, 10 of the 12 cores**. The life step is the rung's whole price (the climate is as it was).

## Result

Two runs, 310 years each, 6,533 and 6,639 s on 5 threads (~21 s a year). Read by `measure.py`
(`results/measure.csv`, a row a census year in `results/years.csv`, thresholds in `results/provenance.csv`).
`analysis/audit.py` reads the bodies' census and does not apply to this run. The censuses live on disk as `.zst`,
not committed like every census (`zstd -d experiments/e103_producers/results/*.zst` before `measure.py` or
`report.py`); the maps are rebuilt by the runs.

| | run 1 | run 2 | line | verdict |
|---|---|---|---|---|
| H1 ledgers (worst year: water, A, B, matter) | 7e-14, 7e-13, 6e-13, 4e-12 | 2e-13, 7e-13, 7e-13, 7e-12 | 1e-9 | **yes** |
| H2 land / sea held (least of the last 50 years); biomass drift | 90% / 35%; +0.2% a year | 91% / 41%; +0.1% | 50% / 20%; 1% | **yes** |
| H3 effective groups (last 50 years); leading group against place (NMI) | 3.3; 0.27 | 5.5; 0.27 | 5; 0.2 | **run 2 only** |
| H4 changes of the leading genotype (last 100 years); late groups at 1% | 0; 0 | 0; 0 | 3; 1 | **no** |
| H5 land evaporation against bare ground; soil A:B map against e102's | -3.4%; 0.31 | +1.5%; 0.35 | 10%; < 0.8 | **no** (the soil yes, the water no) |

**The producers never evolved.** In both runs, genotypes born after the sowing never hold 1e-7 of the biomass at
any census: the 115-121 genotypes that hold the world at year 310 are all founders. About 116,000 mutants were made in
each run and stayed in the seed banks or died as seedlings. The cause is one law: a stand (cohort) is immortal - its
tissue turns over, but the stand never dies of age - so a cell's slot frees only after drought, frost, fire, storm or
starvation, and when one frees, the parent's own seeds, nine times the mutant's share, win it back.

**The eaters did evolve**, because their cohorts move and replace each other every season: 96% and 93% of their
biomass at the end is genotypes born after the sowing. In run 1 a producer compound lies 1.0 bit (by biomass) from
the nearest eater detox key; in run 2 97% of the eaters carry no key and live on the 68% of producer biomass that is
undefended.

**The founders sort by place.** Groups fall from 16 and 35 at the first census to 4.3 by year 100 and then hold; a land
cell's leading group says 0.27 of its place (e102's 71-72 place types). The leaders are near-average founders: about
1 m tall, growth split evenly, one of them 71% of the biomass in run 1, on land and at sea. Heights reach 9-14 m at
the 99th percentile; nothing like a forest.

**The water and the soil.** Transpiration grows to half of the land's evaporation, but the canopy's shade takes as
much from the soil's own: the total moves -3.4% and +1.5%, and the runoff stays at 10% (e102: 9.7%). The soil's
chemistry is remade: its A:B map correlates 0.31-0.35 with the bare ground's.

**History.** The two runs share 26% of their biomass in groups that match within the grouping's cut: which founders
win is contingent.

## Conclusion

**The world stands with its living, but rung 2's question is not answered: producers sort, they do not evolve.**
H4 failed on a precondition (the mechanism of new forms never engages), not on the premise: a stand that never dies
of age leaves a mutant no way in, and the eaters, the same machinery with turnover, evolve at once.

Next (e104): **generations inside a stand** - its plants die at a lifespan the genome sets (a long life paid in
tough tissue), and the space they leave is recruited from the cell's seed bank by lottery, so mutants and immigrants
enter every generation; the same world and the same five lines. Nothing goes back to `base/` until producers evolve.

`vision.md`: layer B rows (producers now evolve-capable but sorted, soil made by the living) and section 5.
