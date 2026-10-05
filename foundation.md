# Foundation

How the world is built: its laws, what is generated and what must emerge, the trade-offs, the rungs it is built in and
how each is judged, the scale, and today's world. Read it before designing or building a law; change it when a law or
a measure is kept or removed, or the method changes (`CLAUDE.md`). What an experiment found is its README's.

## Why

A hundred experiments added laws to a world of hand-written categories - three producers, five kinds of block, a
linear reflex - and it held one to seven ways of living: with few things a world and a body can be, the optimum is
single and the world converges to it (e060, e101). So the world was redesigned (#116): the freedom of every side
raised together, each form priced by physics, built as a ladder of rungs with each judged before the next stands on
it. The older world, its trade-offs and its stages A-C are e001-e101 and this file's history in git.

## 1. Laws, generation, emergence

**Laws** are the same in every world, and each closes its ledger (water, A, B, the living's matter) to 1e-9:

- **Sun, heat, air** (e061, e102): a day and a year (the axis's tilt); a cell's temperature goes towards what its
  light and height (6.5 C a km) give, the sea slowly, and spreads to its neighbours; the air takes up water by its
  deficit, is carried by the wind and rains what it cannot hold. A year draws its own anomaly of warmth and rain and
  keeps half of the last one's; storms multiply the rain where they pass.
- **Ground** (e102): five rocks in provinces set what a soil holds and gives. Water over a soil's holding runs down
  a drainage network to the sea, fills basins as lakes, and sinks to groundwater that seeps back into the rivers.
  Rock weathers into nutrients **A** (mobile; structure) and **B** (bound; activity); water leaving a cell takes
  each by its mobility, rivers drop them on flat land and in lakes, the sea buries them.
- **One genome language** for all that lives (`genome.rs`): four letters, genes of 16 bases - a target (one of 256
  addresses, each a physical quantity), a condition (a signal above or below a level) and a value. A trait is its
  genes' sum squashed into its physical range; mutation is a point change, a duplication or a deletion of a gene.
- **Producers** (e103, e104) are cohorts: up to 4 stands a cell, each one genotype's leaf, wood, root, store and
  seed with their A and B, a height and an age. Light falls through the leaves by height; carbon fixed is paid in
  water drawn from the soil and the groundwater; roots take A and B; tissue is lost to turnover, frost, wilting,
  storms and fire, and returns as litter. A stand dies at the lifespan its wood sets, and a free slot is won by
  lottery from the cell's seed bank (seeds come from the cell, on the wind and down the rivers). In the sea the
  same genome floats and takes A and B from the water.
- **Small eaters** (e103), life below a body's scale: up to 2 cohorts a cell eat leaves by their mass and B, less by
  their toughness, and are harmed by a compound whose 8-bit key is far from every detox key they carry.
- **Bodies** (e106: step 1 of three stands, in its crate and not yet in `base/`) are individuals at continuous
  positions. A form is an 8x8x8 grid of tissue developed from the genome by a voxel's place and the body's stage,
  each voxel a mix of frame, muscle, gut, nerve, fat and glue with its A and B; size is separate. Physics reads a
  summary of the form: a mouth takes what its pressure breaks and a gut keeps what its share holds; compounds harm
  by keys; water is drunk from wet ground and lost through soft skin; heat is made by upkeep and lost through open
  skin; breath in water comes through soft skin; speed is muscle over drag and friction. A body grows from egg to
  adult, lays eggs from its fat and dies of hunger, thirst, heat, cold, breath, poison or age; a one-layer map from
  20 readings chooses its direction, activity and breeding. Designed and not built: bodies that meet, press, break,
  hold and eat each other from one law of contact (#123); soil and canopy, hidden units and learning (#125).

**Generated** from the seed and its parameters: the height map and sea level (land, sea, islands and lakes are
results), the rock provinces, the drainage network, the latitudes, and the genomes sown.

**Emergent**, never written: rivers, lakes, deserts, forests, climate zones, the fire regime, which producer holds
which place, and every form, diet, hunt, migration and way of living.

## 2. The trade-offs

Every freedom is a law about a material with a price no form escapes. They are built and judged as a set.

| freedom | law | gains | pays | status |
|---|---|---|---|---|
| a tissue's B | activity (fixing, uptake, digesting) follows its B share | fast growth | respiration; it is the best food; B is scarce where the rock gives little | `base/` |
| a tissue's A | toughness follows its A share | long life; less lost to drought, frost, storms and mouths | less room for B; A washes out of wet soils | `base/` |
| height | light is taken from the top down | the light | wood by height, water lifted, storms | `base/` |
| roots | water and nutrients by root mass and activity; deep roots reach the groundwater | dry seasons, poor soils | roots are C, A and B | `base/` |
| temperature | enzymes work on a curve around an optimum, the area under it fixed | a broad curve: many places and seasons | a lower peak | `base/` |
| seed | mass against number; a wing and a float carry it | a start in shade and drought, or reach | fewer seeds; wing and float are mass | `base/` |
| lifespan | a stand's from its wood's toughness and share, a body's from its frame's | holding a place, living through bad years | A, and wood or frame | `base/`, e106 |
| compound and key | a compound harms an eater that carries no near key | fewer eaters | B to make it; each detox key costs the eater | `base/` |
| fuel | dry litter and low leaves burn, and fire spreads by fuel | open land kept from tall forms | producers burn their own | `base/` |
| size | the same form at any mass | cheap travel a kg, slow change of heat | surface falls behind mass (square-cube): skin, mouth and gut a kg | e106 |
| mouth and gut | a mouth takes what its tip and muscle break; the gut's share sets how much bulk it keeps | tough leaves, wood, seed | frame and muscle; a heavy, B-rich gut | e106 |
| skin | soft open surface passes water, heat and breath | breath in water, cooling | water lost to dry air, warmth lost in the cold | e106 |
| speed | muscle over drag (the front) and friction (the mass); a climb is paid by mass x rise | reach | muscle's upkeep, work by the path | e106 |
| eggs | many small or few large, from the parent's fat | number, or a start | the parent's A and B | e106 |
| contact | a tissue fails under pressure or strain over its toughness; glue holds; a tip's compound harms by keys | flesh | tip, muscle and glue; a large body is food for many | designed (#123) |
| strata, mind | soil by a hard front, canopy by glue and a light body; hidden units and plastic weights by nerve | refuge, crowns, learning | dark and slow; nerve is the costliest tissue | designed (#125) |

## 3. Rungs, pass lines and measures

A rung asks only "does the world stand, and is its new freedom used", on lines written before the run; a law is
judged with its world over long runs, not alone (decision rule 6). A new rate is set from its units in a pilot and
is not searched to hit a result. If a rung fails on a ground that passed, the fault is that rung's laws.

- **Rung 1, the ground** (e102): ledgers; rivers reach the sea and the land's water is steady; the soil's A:B and
  A + B each span x4; years differ without drifting; more places than climate alone makes. On the planet: A:B x14,
  A + B x19, 15.4 places against 6.4, but rivers thin (runoff 10% of the rain) and years mild (12%).
- **Rung 2, producers** (e103-e105): ledgers; producers on >= 50% of the land and >= 20% of the sea; >= 5 effective
  groups held by place (NMI >= 0.2); they keep changing; the living change the ground. On the planet: 7.6-11.9
  groups, mutants 41-51% of the biomass after a millennium, and no form ever replaced.
- **Rung 3, bodies** (e106): ledgers; bodies on >= 10% of the land's cells and producers on >= 50% for 50 years;
  bodies eat >= 10% of what producers fix and producers turn over; the freedoms are used (adult masses x100, two
  strata, flesh 10% of the diet, plastic weights, a group that travels); >= 5 effective groups of bodies by place.

**The open measure** (`analysis/groups.py`): no boxes fixed in advance. Each genotype's traits are a vector scaled
by fixed physical ranges; groups come from average-linkage clustering cut at a fixed distance and are read as an
effective number (Hill 1 by biomass), as held by place (NMI of a cell's leading group against its place), as change
(when the biomass and its groups were founded) and as history (the biomass two replays of one world hold in matching
groups, `analysis/replay.py`). It reads producers; the bodies' is still to be built. Every threshold is written to
`provenance.csv` (`CLAUDE.md`, Measuring). The old world's measures - kinds by birth form, the 64-box label of a
way, the six-seed control ladder at 7.14 kinds (e068, e094, e101) - judge that world only.

## 4. Scale and compute

**Today's world** is `base/` on the planet c1225 (`cargo run --release -p base -- <prefix> base/worlds/c1225.params`):
512 x 512 cells of 63 km, climate by latitude, an update 3.2 hours, a year 159 days; e106's bodies stand for
millions of animals each there. It moves, rung by rung, to **the scale chosen**: 64 km on a side, 512 x 512 cells of
125 m, a tenth of it land (400-500 km2) in 3-5 islands up to 2 km high; climate from height, the windward and lee
sides and the season, not latitude. A body's laws are in metres and seconds - the cell is the ground's grain, the
update the step of integration (19 minutes, lengthened while the readings hold). A body holds about S kg of animals
at any age, S near a large adult's mass (300-1,000 kg, set for ~3 x 10^4 bodies): a grown large body is one animal, a
small kind a flock, a clutch one brood that splits as it grows. The watcher sees a place, later at real size through
a window that plays what the world decided. **Open on this scale**: what parts the lines. On the planet places a
leading line did not cross did (e083), and a small cell was once set aside because a grazer would cross every
climate in days (#117); here the sea between islands and what height asks of a body must do it - read with bodies.

**Compute**: the ground costs by its cells, 12-20 s a year at 512 with producers (e105, e106); bodies 2 us a body an
update on a thread, so 3 x 10^4 at 19 minutes are ~110 s a year on six threads.
