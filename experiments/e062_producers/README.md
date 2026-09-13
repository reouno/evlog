# e062: the producers (foundation stage B, #75)

Date: 2026-09-13

## Purpose

Stage B of `foundation.md`. A consumer can only specialise on foods that differ, so before any body
lives on the world, find out whether several producers hold different places of a stage-A world and
last: grass, wood and algae as materials with their own growth, and fire. It is the second cheapest
layer, searched around stage A's passing worlds.

## Hypothesis

1. With one growth law for all three and a material difference between them (a stand of grass is all
   leaf, most of a tree is trunk; algae live in water), each producer holds 5% of the standing plant
   matter and is the larger part of at least one habitat on most of six worlds: grass on dry and cold
   land, wood on warm wet land, algae in the shallow sea.
2. Fire burns 1-20% of the land a year in a band of the ignition chance, and the band is wide: once
   a fire catches in dense grass it spreads until the fuel runs out, so the burnt share follows how
   fast the grass grows back more than how often lightning strikes.
3. Matter moves from the land to the sea only through the smoke, which falls with the rain; the land
   keeps at least 95% of its matter over a run.
4. A producer update costs at most 10 ms at 512 on one core, so a candidate (spin-up and 200,000 steps)
   takes under 10 minutes.

## Method

**The world.** e061's climate, ported as it is (`src/climate.rs`, `src/habitat.rs`), on six of e061's
30 passing worlds at 512, chosen to span the land's climates (`search.py`, `results/worlds/`):

| world | land temperature | rain on land | year (steps) | why |
|---|---|---|---|---|
| c1182 | 28.9 C | 1,928 mm | 18,960 | hot and wet |
| c1173 | 30.8 C | 490 mm | 5,400 | hot and dry (99% of the land dry) |
| c1225 | 21.2 C | 3,693 mm | 11,880 | warm and very wet |
| c1221 | 13.4 C | 769 mm | 6,320 | mild (e061's report world) |
| c1236 | 3.3 C | 389 mm | 13,120 | cool, 13 habitats |
| c1208 | -4.2 C | 128 mm | 16,040 | cold |

The climate runs alone for 20,000 updates (whole years), then the producers start on every cell (grass
0.5 and wood 1 on land, algae 0.1 in water) and run on the climate's clock (every 10 steps) for at
least 10 years and 200,000 steps. Laws (`src/plants.rs`):

- **Matter.** Every cell starts with 10 in its soil and producers. A producer grows out of its cell's
  soil, what dies of it lies as litter (algae sink into the water's soil), litter rots into the soil,
  and fire sends half of what it burns to the air and the rest to the soil as ash. The air falls on
  the cells by their share of the rain. Nothing else moves matter.
- **Growth.** rate x light x warmth x water x cover a step. The light is the climate's (1 with the sun
  overhead); the warmth goes from 0 at 5 C to 1 at 20 C (e061's bands); the water is the ground's fill
  on land; the cover is s / (s + half), the share of the light a stand of s takes. Grass's half is
  0.2, wood's 4: wood needs better ground to stand, and standing it shades the grass by its own cover.
  Algae grow in the sea and in pools of 500 mm, at 1 / (1 + depth / 200 m) of the rate.
- **Death.** Grass loses its stand over 2,000 steps, wood over 20,000, algae over 500. With the default
  rates (0.006, 0.0024, 0.01) a producer stands where light x warmth x water is above half / (rate x
  life): 0.017 for grass, 0.083 for wood, 0.02 for algae in shallow water.
- **Rot.** Litter rots at 1/2,000 a step times warmth times water, so it piles up in cold or dry ground.
- **Seed.** A cell gets a producer only from its four neighbors (s counts a tenth of their mean), so a
  producer gone from a place comes back from its edges.
- **Fire.** A land cell can burn when its ground is under a third full, it is warmer than 5 C and it
  holds grass or litter (fuel). A strike hits each cell with chance `ignite` an update; a fire spreads
  from each cell that caught in the last update to its four neighbors. A cell catches with chance
  fuel / (fuel + 1) and loses its fuel and the share fuel / (fuel + wood) of its wood.

Wood's hardness is not searched: nothing bites in stage B, so it changes nothing here. It is stage C's.

**Pass lines** (#75), on the last year: each producer holds 5% of the world's standing plant matter;
each is at least half of the standing matter of a habitat that holds 2% of the cells and a tenth of
the world's mean plant matter a cell (so an empty habitat cannot be won by a trace); none falls under
1% at the end of any year; fire burns 1-20% of the land a year (mean over the second half of the
years); matter is conserved to 1e-9.

**Runs.** Pilots at the defaults on c1221 (with maps), c1182 and c1173, then the same Latin hypercube
of 16 draws on all six worlds (96 candidates) over grass, wood and algae rates (a decade around each
default, log) and the ignition chance (1e-8 to 1e-5, log).

    cargo run --release -p e062_producers -- experiments/e062_producers/results/pilot/c1221 experiments/e062_producers/results/worlds/c1221.params maps=1
    uv run python experiments/e062_producers/search.py 16      # results/search/candidates.txt
    xargs -P 10 -L 1 ./target/release/e062_producers < experiments/e062_producers/results/search/candidates.txt

**The viewer.** `EVLOG_VIEW=rec:stride=200,layers=1` records the producers' years. The header adds
`plant` (grass and wood standing), `soil`, `grass`, `wood`, `algae`, `litter` and `fire` to e061's
layers.

## Result

(pending)

## Conclusion

(pending)
