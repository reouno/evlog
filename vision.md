# Vision

The ideal, today against it, the bottlenecks and the next piece. Read it before choosing or designing a step.
What happened lives in the experiments' READMEs, the issues and git, never here. **Keep this under 120 lines**:
when a row wants a paragraph, the paragraph belongs in an experiment's README and the row keeps the one sentence
that decides the next step.

Last updated: 2026-09-26, e103 (#116 rung 2).

## 1. The ideal

Not dots and numbers: creatures with different shapes, eating and being eaten, in lines that appear, spread, split
and die out, none of it scripted (`principles.md`). As a picture, a savanna as a film crew would show it:

- **Many ways of living at once**, no one of them most of the animals.
- **A food web**: plants that need different mouths and guts, animals eating animals, the dead returned to the soil.
- **Places that hold different animals**, some keeping to one, some crossing them.
- **Time that moves animals**: herds follow the rains, some sleep through the bad season, numbers swing.
- **Bodies that differ and whose shape does something**, from mouse to elephant, with a reason for each part.
- **Animals that behave**: look, chase, flee, go to water, return home.
- **History**: no line holds the world for good, and **a replay is a different world** - the same laws and
  terrain run again fill their roles with other bodies, and need not fill the same roles at all.

**The measure is ways of living, not shapes** - what a body eats, whether it can break another, whether it stays
or roams, where it lives - counted by birth form (e068) at a census and as kinds kept to a place, judged on six
seeds against the control ladder's distribution, **and beside it how much two replays of one world agree**
(`analysis/replay.py`): read over the ways that hold the line, never over every way seen, which saturates. **The working
hypothesis** (competitive exclusion): the ways that coexist are at most the independent things they live on,
each with a trade-off no body escapes, laid out at scales the bodies feel. Untested: no world has had more than a few foods.

## 2. Today against the ideal

Today is stage C's default world on c1225 (`foundation.md`). One line a row; the gap is how much of the rest it
holds back.

| layer | ideal | today | gap |
|---|---|---|---|
| A places, time, water, heat | many wide places, a day, a year, weather, rivers and rain shadows, cold and hot | new ground (`base/`, e102): 5 rocks in 48 provinces, nutrients A and B (A:B spans x14, A + B x19), a drainage network, winds by band, years that differ by place (12% of rain, half kept the next year); 15.4 places on the land against 6.4 by the old bands | small; rivers thin (10% of rain runs off), years milder than Earth's |
| B plant foods | several, each needing its own mouth and gut | old world: grass, algae, browse, carrion, litter; new world (e103): producers with a genome and tissue chemistry sort into 3-6 groups held by place (NMI 0.27), but do not evolve - a stand never dies of age, so no mutant finds room | **large**: no producer evolution yet |
| B response to eating | regrowth, defence, fruit offered | new world: compounds with keys; small eaters evolve and come within 1 bit of the producers' keys, or live on the undefended (e103) | medium |
| B plants as places | a forest is home, cover and food | a stand is a home only through its wet ground (e078) | medium |
| C parts | worth depending on where they sit and how they move | 4 block kinds, 2D grid of side 4-16; every block pays best packed, so bodies fill their grids (e047) | **large** |
| C size | a thousandfold range, each size with its place | 21-35 blocks; winners differ 1.3-2.2x (e055, e075) | large |
| C life history | lives spanning seasons; fat and dormancy selected | breeding values fixed; fat from the genome (e069, e072) | medium |
| D behaviour | look, chase, flee, go to water, go home; some stay, some travel far | a linear reflex, 16 readings to 4 actions, no memory (e050); eyes not bought (2-4% look out, e070); a grown body ends 3-28 cells from its birth | **large**; cause is E |
| E life vs year, vs day | many animals live through several seasons, and many days | a grown life is 500-570 steps, 1/20 of a year and about 7 days; half the dead die by 75 steps; the day's swing is wider than the bands (e071, e087) | **large**: bound by the crowd |
| E travel vs places | a migrant crosses places within a year | a few cells of 512; a place fed in a lean month is 9-15 cells away (e086) | **large** |
| F ways of living | many; the user asked for about 20 | 7.14 kinds at a census, 4.34 kept to a place, 8 ways at 5% in the mean (e101) | **large** |
| F dominance | no line above a fifth of the animals | the largest line holds 39-70% of the land's bodies (e101) | large |
| F food web | three or more levels, hunters of several kinds | kills are 27% of what bodies eat; pure flesh kinds 2-4% (e075) | medium |
| F crowding | numbers limited by food, hunters and seasons | limited by the birth rule: 47% of births find no room though a spot that fits is within two body lengths for 75% of them and off the four rays it searches; widening it thins the jam to 33% and costs 2.5 kinds (e097) | **large**, and not to be lifted by giving room |
| F history (a replay) | the same world run again fills other roles with other bodies | between two seeds the ways holding 5% agree 0.66 and their shares 0.77, the largest way is the same in 4 of 6 seeds, the birth forms agree 0.038 (e101, `analysis/replay.py`) | medium: contingent already; the measure's own 64 boxes cap what can be said |
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

## 5. Next

**The redesign (#116)**, agreed 2026-09-26. About 25 experiments since e075 added laws one at a time and kept two;
every bottleneck above has the same root: the world and its bodies can be too few things, so the optimum is simple
and single and the world converges to it. The premise changes (`principles.md`): the freedom of the environment,
the bodies, their behaviour and their interactions is raised together and by a jump, every form priced by the
world's physics; producers evolve and the living make each other's niches; a small genome develops into a large
space of forms; the world is judged whole, over long runs, by an open measure instead of the 64-box label.

**The order**: the design is agreed in #116 (inventory, the island with the physics that prices each freedom, the
open measure, the ladder). Rung 1, the ground, stands and is `base/` (e102). Rung 2, producers as evolving cohorts,
stands but does not evolve (e103): the founders sort by place and the soil becomes the living's, while the water
cycle hardly moves (runoff still 10%). **Next is generations inside a stand** (e104): plants die at a lifespan the
genome sets and the seed bank recruits into their room, so that mutants enter. Then rung 3, the bodies. The 3D step (#114) is folded into rung 3; e098's price and e101's water ledger carry over.
