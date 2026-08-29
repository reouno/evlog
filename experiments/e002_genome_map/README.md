# e002 Genome map: can a DNA-like string produce traits that are varied, robust, and not readable by hand?

Date: 2026-08-29

## Purpose

We want each individual to be born from a genome: a string over 4 symbols, long enough that
the space cannot be explored by trying (4^N with N in the hundreds). The hard part is not the
string but the map from string to traits. A direct map (position 1 = speed, position 2 = size)
is readable and boring. Real biology is not readable because the map is indirect: genes act on
each other, one gene affects several traits, and traits come out of a process, not a lookup.

This experiment tests one cheap way to get that: an artificial genome with a gene regulatory
network (after Reil 1999). It is tested on its own, without a world.

Out of scope: the world, selection, trade-offs between traits, lifetime changes (learning, aging).
The output of this map is "traits at birth"; state that changes during life is a separate layer, added later.

## Hypothesis

1. **Variety.** Random genomes give varied traits: across 5,000 random genomes, no trait is stuck
   at one value, and the trait vectors do not collapse onto a few points.
2. **Small steps, rare jumps, and neutrality.** A single-symbol mutation usually changes traits a little,
   sometimes a lot, and often not at all. Concretely: the distribution of trait distance after one
   mutation has a large mass at zero (neutral), a median well below the distance between two random
   genomes, and a tail reaching that distance.
3. **Cost.** Decoding one genome takes under 100 microseconds in release mode.

If 1 and 2 hold, the map is usable as the base for individuals. If 2 fails as "always zero" the map is
dead; if it fails as "always a jump" the map is chaotic and evolution cannot climb it.

## Method

Genome: a string of N = 256 symbols from {0,1,2,3}.

Decoding (the "development"):
- A fixed promoter pattern (4 symbols) marks the start of a gene. Each gene is the next L = 8 symbols.
- Each gene has two parts: a regulatory tag (first 4 symbols) and a product (last 4 symbols).
- Gene expression is a vector of levels in [0,1]. Each step, gene i's input is the sum over genes j of
  match(product_j, tag_i) * level_j * sign_j, where match counts equal symbols, and sign is +1 or -1
  from the first symbol of the product. Levels update with a sigmoid, for T = 40 steps.
- Traits: K = 8 named values in [0,1]. Trait k reads the final levels through a fixed random
  projection (the same for every genome), squashed to [0,1]. The projection is part of the "laws",
  not of the genome.

Measurements:
- 5,000 random genomes: per-trait mean, std, min, max; number of genes per genome; how many genomes
  have zero genes.
- For 2,000 of them, apply one random point mutation and measure the Euclidean distance between
  trait vectors before and after. Report the fraction at exactly zero, median, 90th percentile, max.
- Baseline: distance between trait vectors of 2,000 random pairs.
- Decoding time: mean over the 5,000 decodes.

Run (from repo root): `cargo run --release -p e002_genome_map > experiments/e002_genome_map/results/summary.txt`
Raw rows go to `results/*.csv`.

## Result

Seeds 1-3 (each seed draws a different fixed table). All three agree; numbers below are seed 1 unless a range is given.
Raw rows in `results/seed*_{random,mutation,pairs}.csv`, summaries in `results/seed*_summary.txt`.

- Decode time: 3.7 us per genome.
- Genes per genome: mean 7.9, range 0-20. Zero-gene genomes: 1-4 out of 5,000. 88% of genomes have at least one binding edge (mean 3.7 edges).
- Traits: every trait has mean ~0.50, std ~0.11, range about 0.08-0.97. Distance between two random genomes: median 0.41 (p10 0.27, p90 0.60). No collapse.
- One point mutation: 83% neutral (trait vector unchanged). Among the 17% that change something: q25 0.07, median 0.11, p90 0.18, max 0.34-0.42.
  Mutations that add or remove a gene (about half) and mutations inside a gene have the same median effect (~0.11).
- Pleiotropy: a non-neutral mutation moves 6.1 of the 8 traits by more than 0.01 on average; 91% move at least 4 traits, only 1-2% move exactly one.
- Trait extremity grows with gene count: mean |trait - 0.5| is 0.045 at 2 genes, 0.09 at 8, 0.13 at 14.

## Conclusion

Hypotheses 1-3 hold.

1. Variety: traits are spread, not stuck, not clustered.
2. Small steps, rare jumps, neutrality: 83% of mutations do nothing, the typical non-neutral step is a quarter of the distance between two random genomes, and the tail reaches that distance.
3. Cost: 3.7 us per decode; development is free for our purposes.

What this changes: this map is good enough to become the base for individuals. Keep the structure (promoter, tag + product, binding by match, settle, read through a fixed table).

Two things to watch when it goes into a world, noted but not tuned here:
- Pleiotropy is near total: almost every gene touches almost every trait, so selection on one trait drags all the others. If that blocks adaptation, make the fixed table sparse (each product touches 1-3 traits).
- More genes means more extreme traits. Selection for any extreme trait will also select for longer coding regions. Not wrong, but it is a hidden bias.

Traits sit mostly in 0.3-0.7; whether that range is enough depends on how the world uses them, which is the next experiment's problem.
