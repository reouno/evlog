# e004 Genome shape: can the gene network grow a body on a grid?

Date: 2026-08-29

## Purpose

`vision.md`, mechanism 1: shape should come from development, not from a list of parts.
This experiment runs the e002 gene network once per cell of an 8x8 grid, with the position of the
cell fed in as a signal, and lets the settled expression decide whether the cell holds a block and
of which kind (hard, muscle, sensor, digestive). Nothing like a limb or a fang is defined anywhere.

Tested on its own, no world. Out of scope: what the blocks do (e005), selection, 3D.

## Hypothesis

1. **Variety.** Random genomes give varied, mostly connected bodies: not all empty, not all full,
   and the 5,000 random bodies do not collapse onto a few shapes.
2. **Small steps.** One point mutation usually changes the body a little (a few blocks), sometimes
   a lot, often not at all.
3. **Heritability.** A child's body looks like its parent's: the body distance after one mutation is
   much smaller than the distance between two random bodies.
4. **Cost.** Developing one body takes under 1 ms in release mode.

## Method

Genome and gene network exactly as e002/e003: 512 symbols over {0,1,2,3}, promoter `010`, each gene
a 4-symbol tag plus a 4-symbol product, products bind tags on 3 or more matching symbols (weight 0.5 or
1.0, sign from the product's first symbol), levels updated by a sigmoid for 40 steps.

Position enters as **morphogens**: 6 fixed patterns (part of the laws, drawn once per seed) that act on
gene tags like products do, but whose level is set by the cell's position instead of by the network.
The 6 levels are `x`, `1-x`, `y`, `1-y`, `r`, `1-r` (`r` = distance from the center), each stretched
to [-1, 1] so that a signal activates a gene at one side of the body and represses it at the other.
A morphogen binds a tag on 2 or more matching symbols with weight m/4 (a broad signal, easier to bind
than a gene product). Genes bind each other exactly as before.

Read-out: a fixed table (256 products x 5 columns, values in [-1, 1]) gives 5 scores per cell,
one for "empty" and one per block kind, as the level-weighted sum over genes. The highest score wins;
ties go to empty, so a genome with no genes is an empty body.

Choice of the morphogen rule (seed 1, 5,000 random genomes; "uniform" = the same thing in every cell):

| Position signal | Morphogen binds on | Uniform bodies | Distinct bodies |
|---|---|---|---|
| [0, 1] | 3 of 4 (as genes) | 72% | 1,137 |
| [0, 1] | 2 of 4 | 63% | 1,697 |
| [-1, 1] | 3 of 4 | 49% | 2,046 |
| [-1, 1] | 2 of 4 | 22% | 3,811 |

With position in [0, 1] and gene-like binding, most genomes never notice where a cell is. Both changes
are structural (two-sided signal, broad binding), not tuned numbers, and the last row is what the
experiment uses.

Measurements:
- 5,000 random genomes: blocks per body, kinds present, share of cells by kind, empty / full / uniform
  bodies, 4-connectivity of the blocks, number of distinct bodies, development time.
- 2,000 of them: one random point mutation, body distance = number of cells that differ (0-64).
  Also two mutations (what an e003 child gets), for reference.
- 2,000 random pairs: the same distance, as the baseline.
- A gallery for the report: 40 random bodies, 4 parents with 7 one-mutation children each, and a walk
  of 32 successive single mutations from one parent.

Run (from repo root): `cargo run --release -p e004_genome_shape -- <seed> > experiments/e004_genome_shape/results/seed<seed>_summary.txt`
Raw rows go to `results/seed<seed>_{random,mutation,pairs}.csv`, the gallery to `results/seed<seed>_bodies.json`.

## Result

Seeds 1-3, all agree; ranges below cover the three seeds. Genes per genome 7.8-7.9, as e002.

- Development: 216-220 us per body (64 cells x 40 network steps).
- Bodies: uniform 20-22% (empty 3-6%, one kind everywhere 16-17%), full (no empty cell) 48-61%.
  Blocks per body: mean 48-54, p10 9-26, median 62-64. Distinct bodies: 3,808-3,940 of 5,000.
- Of the shaped (non-uniform) bodies, 94-97% are connected. Only 36-46% of all bodies contain both
  empty cells and blocks.
- Kinds present per body: one 32-34%, two 41-43%, three 17-19%, four 2-3%. The share of cells by kind
  depends on the seed's table (e.g. hard 16% in seed 1, 28% in seed 2).
- Position reaches the network in 99.6-99.8% of genomes (at least one morphogen edge). Genomes with 0-2
  morphogen edges are shaped 29-34% of the time, with 12 or more 82-83%.
- One mutation: neutral 83-84%; 1-8 cells changed 6%; 32 or more cells 2.4-2.8%. Among non-neutral
  mutations: median 12-13 cells, p90 34-38, max 64.
  Two mutations: neutral 71-73%, p90 18-20.
- Random pairs: median 56-57 cells, p10 26-29, p90 64.

## Conclusion

1. Variety: partly. Bodies are varied (76-79% distinct, 78-80% shaped, almost all connected), but they
   are dense: the typical random body fills the grid and only 4 in 10 have an outline at all. The
   read-out is the reason: one "empty" column competes with four block columns, so a block wins
   most cells. Whether this matters is e005's question: every block will cost upkeep there, so
   selection will trim bodies if the genome lets it; p10 of 9-26 blocks says sparse bodies exist.
2. Small steps: partly. "Often not at all" holds (83%), and the changes are small next to the distance
   between random bodies. But the typical change is not a few blocks: it is a region of about 13 cells,
   a fifth of the body. A mutation shifts a gene's expression, and expression is shared by a whole
   region of cells. Single-block edits are rare (6%). This is what development does; it is not a bug,
   but it means mutation in the world will move outlines and patches, not pixels.
3. Heritability: yes. Non-neutral median 13 vs random-pair median 57; a child is recognizably its parent.
4. Cost: yes, 0.22 ms, well under 1 ms and cheap enough for development at birth.

What this changes:
- Keep the mechanism: e002 network plus 6 position morphogens plus a table read-out. Shapes come out
  of it, with kinds arranged in patches and stripes, and nothing was drawn by hand.
- The morphogen rule matters more than anything else here (72% to 22% uniform); the gene network on its
  own does not see position. Record it as part of the laws.
- Open: bodies are dense by default. Do not fix it here; let e005's upkeep cost act on it, and revisit
  the read-out only if selection cannot find sparse bodies.
- Open: mutations act on regions. Good for variety of outlines, possibly bad for fine-tuning a
  single block (a fang). Watch in e005 whether small features can be kept.
