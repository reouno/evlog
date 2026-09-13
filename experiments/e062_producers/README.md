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

**Runs made.** Pilots on the Mac, 3 at once (about 6.5 minutes each). The search: 66 candidates on
the Mac, 9 at once (the first 66 lines of `candidates.txt`), and 30 on the Ubuntu PC, 6 at once (the
last 30), 22:12-23:39 on 2026-09-13; about 17 core-hours. c1225_d11 rerun with maps into
`results/pass/` (its row matches the search's). The maps (`*_maps.bin`, 24 MB) are not committed.

## Result

**Pilots at the defaults** (grass 0.006, wood 0.0024, algae 0.01, ignite 1e-6):

| world | grass / wood / algae share | larger part in habitats (g / w / a) | burnt a year | land matter kept | pass |
|---|---|---|---|---|---|
| c1221 mild | 0.30 / 0.33 / 0.37 | 4 / 1 / 4 | 1.2% | 98.5% | all |
| c1182 hot, wet | 0.09 / 0.75 / 0.17 | 0 / 2 / 3 | 9.4% (largest fire 10,812 cells) | 92.3% | fails larger |
| c1173 hot, dry | 0.09 / 0.001 / 0.91 | 1 / 0 / 4 | 0.3% | 99.8% | wood dies out |

**The search** (96 candidates; each world 16):

| pass line | c1182 hot wet | c1173 hot dry | c1225 very wet | c1221 mild | c1236 cool | c1208 cold | all |
|---|---|---|---|---|---|---|---|
| each holds 5% | 10 | 2 | 10 | 11 | 8 | 8 | 49 |
| each the larger part of a habitat | 2 | 1 | 8 | 2 | 8 | 4 | 25 |
| none under 1% at a year's end | 15 | 2 | 14 | 13 | 14 | 12 | 70 |
| fire burns 1-20% | 14 | 3 | 5 | 7 | 9 | 0 | 38 |
| matter conserved (1e-9) | 16 | 16 | 16 | 16 | 16 | 16 | 96 |
| all | 1 | 0 | 3 | 2 | 3 | 0 | **9** |

No draw passes on more than two worlds (d03: c1225, c1236; d04: c1225, c1221; d11: c1225, c1236; d01,
d13, d14 one each). The passing candidates:

| candidate | grass / wood / algae | larger (g / w / a) | burnt | land matter | wood end / middle year |
|---|---|---|---|---|---|
| c1182_d14 | 0.29 / 0.54 / 0.17 | 1 / 2 / 3 | 6.4% | 93.8% | 1.10 |
| c1221_d04 | 0.44 / 0.32 / 0.24 | 4 / 1 / 4 | 2.8% | 97.5% | 0.83 |
| c1221_d13 | 0.39 / 0.45 / 0.16 | 3 / 2 / 4 | 1.9% | 96.2% | 1.33 |
| c1225_d03 | 0.43 / 0.37 / 0.20 | 4 / 1 / 4 | 4.4% | 96.1% | 1.30 |
| c1225_d04 | 0.28 / 0.64 / 0.08 | 2 / 2 / 3 | 1.5% | 99.3% | 1.03 |
| c1225_d11 | 0.55 / 0.29 / 0.17 | 5 / 1 / 3 | 1.5% | 98.9% | 1.03 |
| c1236_d01 | 0.24 / 0.67 / 0.09 | 2 / 4 / 3 | 2.1% | 98.4% | 1.10 |
| c1236_d03 | 0.34 / 0.58 / 0.08 | 2 / 2 / 2 | 3.4% | 95.5% | 1.14 |
| c1236_d11 | 0.42 / 0.52 / 0.07 | 3 / 2 / 2 | 2.7% | 96.7% | 1.06 |

What decides each line:

- **Who holds the land: the ratio of needs.** A producer stands where light x warmth x water is over
  half / (rate x life). Grass's part of the land's standing matter follows wood's need over grass's
  (rank correlation 0.90 over 96). Both win a habitat in 25 candidates, all with wood needing 2.6-12.3
  times the ground grass needs. Algae are the larger part of a water habitat in all 96.
- **Where it fails, by world.** Hot and dry (c1173): wood falls under 1% in 12 of 16 draws. Hot and wet
  (c1182): wood holds the wet land and grass is the larger part of no habitat with enough plant matter
  in 12 of 16 (the dry land is nearly bare). Cold (c1208): it burns at most 0.7% of its land a year in
  every draw. Grass wins a habitat in 10 of 16 on every other world.
- **Fire burns too little, never too much.** All 58 fire failures burn under 1%; the most any candidate
  burns is 11% a year. The fires counted follow the strike chance (0.97). The land burnt follows it
  in proportion (log-log slope 0.83-1.00) on four worlds, where each fire stays a patch of hundreds of
  cells, and with slopes 0.24 (c1182) and 0.34 (c1236) where dry fuel is continuous in the dry season
  and one fire burns up to 27,128 (c1182) or 10,465 (c1236) cells.
- **The smoke drains the land.** 84 of 96 keep 95% of their land matter; the loss follows the land
  burnt (rank -0.92), median 0.02% and at most 1.24% a year. Half of what burns goes to the air, and the
  air falls mostly on the sea, where more rain falls.
- **Wood is not always settled.** Between the middle and the last year wood changed by under 20% in 62
  of 96 runs; in 31 it fell by more (16 of them the hot dry world, where it dies out), and in 3 it rose
  by more (two of them passing runs, 30-33%).
- **Cost.** On the Mac, 9 at once: a median candidate took 8.1 minutes (spin-up 144 s, producers 344 s,
  16.5 ms an update with the climate; at most 10.3 minutes). On the Ubuntu PC, 6 at once: 16.7 minutes
  (33.9 ms an update). 3 at once on the Mac (the pilots): 13.2-13.8 ms an update. Alone on the Mac
(the c1225_d11 rerun): 8.9 ms an update, 4.3 minutes a candidate.

## Conclusion

1. **Hypothesis 1, no.** Three producers hold places of their own on 4 of 6 worlds, in 9 of 96
   candidates, and no draw of the rates passes on more than 2 worlds (1 of 3 pilots at the defaults).
   Algae always hold the water; grass and wood split the land only when wood needs about 3-12 times
   the ground grass needs, and the split that works on a wet world fails on a drier one.
2. **Hypothesis 2, partly.** Only where dry fuel is continuous (the hot wet and the cool world) do fires
   spread until the fuel runs out; elsewhere the land burnt follows the strikes in proportion. No world
   burns more than 11% a year under these laws, and the cold world never reaches 1%.
3. **Hypothesis 3, mostly.** 84 of 96 keep 95% of their land matter. The rest lose it to the smoke in
   proportion to the fire, up to 1.2% a year, with nothing to bring it back from the sea.
4. **Hypothesis 4, yes.** 8 minutes a candidate on the Mac at 9 at once.

What changes for the project: stage B gives stage C (#76) a small set. Laws are the same in every
world, so stage C takes one draw and the worlds it passes, not the best draw for each world. The
recommendation is draw d11 (grass 0.009983, wood 0.0017, algae 0.009112, ignite 1.613e-6) on c1225
(warm, very wet) and c1236 (cool), where wood is settled (1.03 and 1.06) and the land keeps 98.9% and
96.7% of its matter. Before runs longer than stage C's, the land needs a way to get its matter back
from the sea.

These hold for our choices: one growth form for all three producers with cover halves 0.2 / 4 / 0.1
and lives 2,000 / 20,000 / 500 steps; warmth from 5 to 20 C; water as the ground's fill; seed only from
the four neighbors; fire only on ground under a third full and warmer than 5 C, spreading to four
neighbors with chance fuel / (fuel + 1); half the smoke to an air that falls with the rain; producers
that change neither the water nor the air; 10 years and 200,000 steps after a 20,000-update spin-up;
six worlds; and the pass lines, including the tenth of the mean plant matter a habitat must hold and a
fire line that rejects a cold world that never burns.
