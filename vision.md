# Vision

The ideal, today against it, the bottlenecks, the lessons and the direction. Read it before choosing or designing a
step. What happened lives in the experiments' READMEs and git, and what is to be done and in what order in the
issues (#116), never here. **Keep this under 120 lines**: when a row wants a paragraph, the paragraph belongs in an
experiment's README and the row keeps the one sentence that decides the next step.

Last updated: 2026-11-14 (#135, e118).

## 1. The ideal

Not dots and numbers: creatures with different shapes, eating and being eaten, in lines that appear, spread, split
and die out, none of it scripted (`principles.md`). As a picture, a savanna as a film crew would show it:

- **Many ways of living at once**, no one of them most of the animals.
- **A food web**: plants that need different mouths and guts, animals eating animals, the dead returned to the soil.
- **Places that hold different animals**, some keeping to one, some crossing them.
- **Time that moves animals**: herds follow the rains, some sleep through the bad season, numbers swing.
- **Bodies that differ and whose shape does something**, from mouse to elephant, with a reason for each part.
- **Animals that behave**: look, chase, flee, go to water, return home.
- **History**: no line holds the world for good, **a replay is a different world**, and a disturbance (a fire, a
  drought, an invader) moves the optimum and the web rebuilds otherwise - none of it written, all of it allowed.

**The measure is ways of living, not shapes** - what a body eats, whether it can break another, whether it stays
or roams, where it lives - counted by birth form (e068) at a census and as kinds kept to a place, judged on six
seeds against the control ladder's distribution, **and beside it how much two replays of one world agree**
(`analysis/replay.py`): read over the ways that hold the line, never over every way seen, which saturates. **The working
hypothesis** (competitive exclusion): the ways that coexist are at most the independent things they live on,
each with a trade-off no body escapes, laid out at scales the bodies feel. Untested: no world has had more than a few foods.

## 2. Today against the ideal

Today is the last whole world (stage C on c1225, e101) and, where a row says so, the new one being built (`base/`,
#116). One line a row; the gap is how much of the rest it holds back.

| layer | ideal | today | gap |
|---|---|---|---|
| A places, time, water, heat | many wide places, a day, a year, weather, rivers and rain shadows, cold and hot | the map at an animal's size (e117, bare): 49 km2 in four islands on 16 km, drawn at 5 m with ponds and 15 km of streams; lowlands 17.0 C in the south to 5.6 C in the north; fronts from a storm track that moves with the season - the south 517 mm with a rainless summer (7% of its rain, a third of its brooks dry), the north 901 mm in every season and four months of snow; 2.2 m of rain on the heights, a lee a half to an eighth of its windward side; a year's rain differs twofold. Before it `base/` on isles1 (e108, e109): eight islands, where under stands 7-10% of the soil leaves the full band and fire burns the driest third | medium: plants are parted on it by warmth and fire and not yet by water (e118), animals not at all; soil and water are 125 m cells that show as straight edges of woods; a lee is dry only close behind a height, streams run straight |
| B plant foods | several, each needing its own mouth and gut | at metres (e118, 120 years, nothing grazing): a thicket - the field's stands under 0.5 m on 13% of the ground, 0.5-2 m on 37%, 2-5 m on 27%, over 5 m on 18% - with 168,813 trees as things on a tenth of the 5 m cells, 5-9 m tall, their crowns over 5.7% of the ground and spreading; litter 3.3 kg a m2; a quarter of the ground burnt in a decade. Leaves, wood, roots, stores, seed and litter are there to eat; no fruit, and the sown lines sort at a seed's pace: two of 256 genomes are 94% of the trees, 1.3% of the mass is new. At 125 m before it (e105, e109): producers evolve for a millennium and no form is replaced; 45% of the living is in the ground (e112) | **large**: no animal has met these foods; a tree's height is its genome's limit, so no line is taller than 9 m with wood for 17 |
| B response to eating | regrowth, defence, fruit offered | new world: compounds with keys; small eaters evolve and come within 1 bit of the producers' keys, or live on the undefended (e103); a tissue's lock that a gut's keys must fit is born and pays a little but never spreads (under 2e-5 of the producers' mass): the bodies hardly eat the living (e114); a tissue holds water by its working part and a mouthful brings it - thirst eases, the leaf stays about 1% of the diet, since the living are behind height and the crown, not behind water (e115) | **large**: a defence pays only where the living are eaten |
| B plants as places | a forest is home, cover and food | e118: a tree is a thing with a place, a height and a crown, a thicket stands to 8 m, a wood reads as a wood from a walker's height; woods lie where it is warm and unburnt (11% of the ground under crowns over 15 C, 0.6% under 9 C; a tree line at 1,400 m and 59 N), not where it is wet, and under crowns of a leaf area of 1-2 no floor is dark | medium: whether a wood is cover or home is rung 3's to show; wood and open ground are not yet parted by water |
| C parts | worth depending on where they sit and how they move | 4 block kinds, 2D grid of side 4-16; every block pays best packed, so bodies fill their grids (e047) | **large** |
| C size | a thousandfold range, each size with its place | 21-35 blocks; winners differ 1.3-2.2x (e055, e075); new world: adult mass is free over ten decades; which founder comes through the first years' bottleneck sets the size for sixty years after - e111's sowing a 0.1 kg sack, a third armour by year 140, the same world sown again (twice) an 18 kg litter eater holding 95-100% of the matter (e112); after a century, two sizes over 5% of the matter stand 13-32x apart, not by island, the same make at another size, and over the next the small one (0.57 kg) takes 91% of the matter from the 18 kg one, most of it at sea (e113); nothing but distance gets cheaper with size | large: two sizes at most |
| C life history | lives spanning seasons; fat and dormancy selected | breeding values fixed; fat from the genome (e069, e072) | medium |
| D behaviour | look, chase, flee, go to water, go home; some stay, some travel far | a linear reflex, 16 readings to 4 actions, no memory (e050); eyes not bought (2-4% look out, e070); a grown body ends 3-28 cells from its birth | **large**; cause is E |
| E life vs year, vs day | many animals live through several seasons, and many days | a grown life is 500-570 steps, 1/20 of a year and about 7 days; half the dead die by 75 steps; the day's swing is wider than the bands (e071, e087) | **large**: bound by the crowd |
| E travel vs places | a migrant crosses places within a year | a few cells of 512; a place fed in a lean month is 9-15 cells away (e086) | **large** |
| F ways of living | many; the user asked for about 20 | 7.14 kinds at a census, 4.34 kept to a place, 8 ways at 5% in the mean (e101); new world, by the bodies' open measure (`analysis/ways.py`): 1.2-1.4 ways for 30 years and 2-3 after, parted by armour, range, land or sea and at most two sizes, on one food (e112); 2.3-3.2 with a hunter's way among them, litter still 99%; 2.7-4.5 over the next century, falling as one small litter eater takes the matter (e113) | **large** |
| F dominance | no line above a fifth of the animals | the largest line holds 39-70% of the land's bodies (e101); new world: one founder's line of 256 holds every island with bodies, on land and sea alike, walking 550 km a year (e110, e111), and still holds them a hundred years on (e112) | large |
| F food web | three or more levels, hunters of several kinds | kills are 27% of what bodies eat; pure flesh kinds 2-4% (e075); new world: bodies meet and break each other by one law of contact, but flesh is under 1% of the diet and no line lives on it; with a food worth its working part and a gut's leavings sent to the soil the land stands (61-71% of the world without bodies over a hundred years, not falling) and the bodies live on litter, 99.9% of the diet, flesh 0.01%; a designed hunter emptied the world in a year while its front tore what it did not swallow; with a front that breaks only what its gut takes in it bounds its kill, and starves, since a press works its front's muscle for the whole hold; with the ground and crowns as places where the caught is not, flesh is still nothing after sixty years (e111, e112); with a press paid for what it breaks a hunter evolves in one history of two and settles beside its prey to year 200, about 1,000 t, one founder's line, but does not follow its prey up as they multiply fourfold: flesh 0.55% of the diet at year 100, 0.18% at year 200; a designed one still empties the small world in a year, and on the islands strikes every island within two years and starves (e113); the litter they live on was soft by rule: worn soft by its own rot it feeds three quarters as many, the living plants still under 1% of the diet (e114); with water in food, 15-39% of what the bodies take in, still (e115) | **large** |
| F crowding | numbers limited by food, hunters and seasons | limited by the birth rule: 47% of births find no room though a spot that fits is within two body lengths for 75% of them and off the four rays it searches; widening it thins the jam to 33% and costs 2.5 kinds (e097) | **large**, and not to be lifted by giving room |
| F history (a replay) | the same world run again fills other roles with other bodies | between two seeds the ways holding 5% agree 0.66 and their shares 0.77, the largest way is the same in 4 of 6 seeds, the birth forms agree 0.038 (e101, `analysis/replay.py`); new world: the same laws and ground sown in year 40 or 41 fill with 0.1 kg or 18 kg bodies, the land at 65% or 81% of the bare world at year 100 (e112) | medium: contingent already; one pilot reads one history |
| F cycles over time | predator and prey swing | the land's bodies swing twofold over a year; forms do not follow (e070) | medium |
| G matter, water, heat | matter closes between land and sea; a body drinks and gives back; places exchange heat | matter conserved, the land gaining 6.5-7.3% over 90,000 steps with nothing back from the sea (e072, e090); a body's water is the land's and conserved, and ties it to where it drinks (e101); a body holds heat but does not warm its cell (e072) | small, but matter prices every law that moves it |

## 3. Where the bottlenecks are

1. **A life is too short and too local for the world we built** (E, and through it D and part of F). To a body the
   world is the same everywhere and always; places and seasons are felt only by lines over generations. Hence no
   eye bought, no refuge, no migrant.
2. **Few kinds of food, and a label with only 64 boxes to put a way of living in** (B, and through it F). A gut eats
   any plant and there are three producers; each food with the right mouthful added a way of living (e073, e075),
   three tried since have not (e089-e091). A way is a diet (4) x a tooth (2) x roaming (2) x a medium (4), and about
   43 of those 64 are filled in every run, so the coarse reading of a replay saturates whatever the world does.
3. **Parts whose worth does not depend on shape** (C). Forms differ by what they hold, not by how they are built.
   Three materials priced by shape have been tried and none made a way of living (e093, e095, e096).
4. **The crowd absorbs what is added to it** (F, and through it B and C), and it is not an income: half of all
   births fail for room in cells that are half empty, because a rigid grid must land on contiguous free sub-cells
   reached by 24 spots on four rays (e096, e097). It is not a lid to be lifted: relieving it costs ways of living
   (e097), because the narrow rule is what keeps a lineage where its parent stood. What is missing is not room but
   something that parts the world - a food, a place, a trade-off.

## 4. Lessons that hold across experiments

Each holds under the conditions it was found in.

- A difference a body can ride out is not an axis: a law must differ over more ground than a body covers in a life
  (e057, e060) and change on a life's scale if behaviour is to follow it (e049).
- A law that moves the amount, time or place of the one food changes the number of bodies, not the ways (e060), and
  a law can transfer a resource in full and change nothing: take food away and you buy number, not a way (e057, e096).
- A food is its mouthful (e075), and it feeds a new kind only when reaching it needs something a body is born with:
  browse needed a tooth and made a kind (e073); seed parted by a mouthful then by a tool half the world carried, and
  a crown whose door is a mass that moves within a life, fed none (e089-e091).
- A material whose worth is set by shape builds bodies, not ways of living (e093, e095): shape follows a food or a
  place, it does not lead.
- Every shape law so far ends in the water: on land a face open to the air is a water bill (e066, e067, e093, e095).
- A law added alone meets a world without its counterweights; a set searched together can hold (e066-e071, e072) -
  and laws each unreadable alone can harm together (e100). A law must multiply the term that binds: designing a
  cycle does not excuse reading the arithmetic it plugs into (e095).
- A law whose income does not fall as the crowd grows has no middle (e093); one priced by how thick the bodies stand
  has nothing to price, since that thickness is a constant (e096).
- What ends a grown life is the crowd's income, wherever it lives, not the season (e037, e038, e087). A body that
  can wait lives through a winter and then does not move; a winter is a third of its year at any year length (e086).
- Heat is paid in water and water sets where land bodies live (e078); lines are kept apart by places a leader does
  not cross (e083), and by how far a child may be laid from its parent - give a child room and the winner spreads
  fastest (e097), tie a body to its water and nothing readable is lost (e101); regions show in a climate (e084, e085).
- A law that carries matter one way over a world with a sea drains the land (e090). A way that needs a part the
  population has lost is a question of reach: test it by injection beside a control (e074, e076).
- Measures: a distribution against a distribution, harm a fixed 1.02 kinds below the control (e092, e101); never
  judge on a conjunction over censuses (e094); a measure of place breaks when bodies change place within a life (e091);
  a spread is read by what it is made of - one collapsed seed is not a various world (e100).
- A law written in cells and updates holds at one scale only (e107), and a scale sets the clock: with seeds that
  cross metres, 300 years after a sowing is a transient (e109), and 120 years of trees is two founders' lines (e118). Read a trend before a level.
- What holds eaters of the dead is what the dead are worth (e111). A front that breaks only what it swallows bounds
  its kill. A layer is a place when a body can live a life in it; a world's first years set its size, for a century (e112, e113). A designed
  body is no test of what evolution can reach; a body is a cohort, so read animals beside bodies and matter (e113).
- A rule standing in for a process can be what a world stands on: replace it by the matter's state (e114). A price on a food moves the diet only where the bodies reach it: water in the leaf eased thirst and opened no door (e115).

## 5. The direction

**The redesign (#116)**, agreed 2026-09-26: every bottleneck above has one root - the world and its bodies can be too
few things, so the optimum is simple and single and the world converges to it. The premise changed (`principles.md`):
the freedom of the environment, the bodies, their behaviour and their interactions is raised together and by a jump,
every form priced by the world's physics; producers evolve and the living make each other's niches; a small genome
develops into a large space of forms; the world is judged whole, over long runs, by an open measure.

**The gap being filled** was the bodies' at 125 m and 44-minute steps (e110-e115): the land stands, the living stay behind
doors and, watched (2026-11-08), no animal is anywhere - a body is a crowd of 300,000. **The world is rebuilt at the
size of an animal** (#135, agreed 2026-11-11): one body one animal, plants as things at metres, the mind with it, since
what is watched is behaviour. Its map stands (e117), plants stand on it as a thicket with young trees (e118); animals next.
