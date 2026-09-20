# Vision

The ideal world, today's world against it, and the next piece of work. Read it before choosing or designing a step;
update it after every experiment (`CLAUDE.md`, Documents). History is not kept here: it is in each experiment's
README and in git.

Last updated: 2026-09-21 (after e094: the ways of living flicker across the 5% line, they are not driven out;
`kinds_held` dropped as a measure).

## 1. The ideal

Not dots and numbers: creatures with different shapes, eating and being eaten, in lines that appear, spread, split
and die out. Nothing in that is scripted (`principles.md`). As a picture, a savanna with its rivers, woodlands and
coast, as a film crew would show it:

- **Many ways of living at once.** Grass eaters, leaf and bark eaters, fruit and seed eaters, hunters of several sizes
  and styles, scavengers, filter and bottom feeders in the water. No one of them is most of the animals.
- **A food web.** Plants of several kinds, each needing its own mouth and gut; animals eating animals; the dead eaten
  and returned to the soil.
- **Places that hold different animals.** Woodland, open grass, marsh, desert, shore, cold highland, each with its own
  residents; some animals keep to one place, some cross them.
- **Time that moves animals.** Herds follow the rains, animals breed in a season, some sleep through the bad one,
  predator and prey numbers swing against each other.
- **Bodies that differ and whose shape does something.** Sizes from mouse to elephant; legs, jaws, horns, shells,
  fins, and a reason for each.
- **Animals that behave.** They look, chase, flee, go to water, return home.
- **History.** No line holds the world for good.

**The measure is ways of living, not shapes.** A way of living is what a body does: what it eats, whether it can
break another body, whether it stays or roams, where it lives. Stage C counts kinds by birth form (e068): the body a
genome develops, read over all the grown bodies of that form, at a census and as kinds kept to a place. A step is
judged on six seeds against the control ladder's distribution (`foundation.md`; the ladder spreads 1.02 kinds and
1.24 placed kinds on its own, e092). Shape kinds and the leading line's share are second numbers.

**The working hypothesis** (competitive exclusion): the ways of living that coexist are at most the independent
things they live on, each with a trade-off no single body escapes, laid out at scales the bodies feel. It is
neither refuted nor tested: no world has yet had more than a few foods.

## 2. Today against the ideal

Today is stage C's default world on c1225 (`foundation.md`). Gap: how far today is from the ideal and how much of the
rest it holds back.

### A. The physical world

| element | ideal | today | gap |
|---|---|---|---|
| places | many wide places, each with its own residents | 512x512 torus; c1225 holds 12 habitats of 2% and 5.0 effective regions, third of stage A's 34 climates (e084, e085) | small |
| time | a day, a year, weather | a day of 75 steps, a year of 11,880, one wind (e061) | small in itself; see E |
| water and heat | rivers, lakes, rain shadows, cold and hot places | emerge from the climate (e061); the ground's water is what land bodies live on (e078) | small |

### B. Producers

| element | ideal | today | gap |
|---|---|---|---|
| kinds of plant food | several, each needing its own mouth and gut; some seasonal | grass (any gut), algae (a surface gut), wood's browse at 3e-5 (a hard tip, e073); carrion and litter. Seed (#99 S, not in the default world): at `seed_share` 0.2 a steady bank of 0.43 of the grass on the land, more than the leaf in the winter at 50 degrees (e088). Behind a tooth of 2 it feeds no kind of its own: it is 3% of what bodies eat, a side dish of the toothed hunters, since a gut takes it mixed with the grass (e089). Given a place (the wind moves it), a tool (any hard tip) and a worth of its own (grass 0.8 fiber) it reaches 4.5% of what bodies eat and two fifths of the leading land kind's plant energy, and still leads no kind (e090). Fruit held in a crown, out of reach of the floor (#101, not in the default world): 3-5% of the grown bodies live up there and take a third of their food from it, and no kind does (e091) | **large**: few ways to eat |
| response to eating | grazed plants regrow, defended plants resist, fruit is offered | every producer grows by its stand and is grazed to a few percent of it (e065) | medium |
| plants as places | a forest is a home, a cover and a food | a stand is a home only through its wet ground (e078). Made a place of its own - a crown a body stands in, with a food no body below reaches - it holds a crowd with its own hunters and the only bodies in this world that travel (20-26 cells against 4-7), and still no kind (e091) | medium |

### C. Bodies and genome

| element | ideal | today | gap |
|---|---|---|---|
| parts | parts whose worth depends on where they sit and how they move | 4 block kinds on a 2D grid of side 4-16; every block pays best packed, so bodies fill their grids (#52, e047). A fifth that gains by its faces open to the air (#103, `light_gain` 0.016, not in the default world) parts a kind on three seeds of six, and its bodies are the first in this world that are not filled rectangles - a hollow frame, a bar one block wide, 1.38-1.62 open faces a block against 0.94. They live only in the water: on land an open face is a water bill (e093) | **large** |
| size | a thousandfold range, each size with its place | 21-35 blocks; winners differ 1.3-2.2x (e055, e075). Fiber digested over time (Fb, not kept) makes grass eaters 14-27% heavier and slower, with no new kind (e089); at a harsher rate (0.8 fiber, ferment 0.005) they do not grow at all - grass falls to a fifth of what is eaten and the bodies leave it (e090) | large |
| life history | lives that span seasons; fat and dormancy chosen by selection | breeding values fixed (from the genome they cost kinds, e069); fat from the genome (e072); a cold body can go torpid (Q, not in the default world, e087) | medium |

### D. Behaviour

| element | ideal | today | gap |
|---|---|---|---|
| senses | eyes that pay | sight through sensor blocks is not bought (2-4% look out, e070) | large; the cause is probably E |
| decisions | chase, flee, go to water, go home | a linear reflex, about 16 readings to 4 actions; no memory; learning not selected (e050) | large; same |
| movement | some stay, some travel far | a grown body ends 3-28 cells from its birth, by the laws (e070-e082); 33-45% of moves blocked (e070) | large; same |

### E. A life against the world's scales

| element | ideal | today | gap |
|---|---|---|---|
| life against the year | many animals live through several seasons; short-lived ones sleep through the bad one | a grown body lives 500-570 steps, **1/20 of a year**; half the dead die by 75 steps, as children (#93). At a year of 1,200 with Q, 81-84% of grown bodies on seasonal land live through a winter, torpid, but a grown life is still 3/4 of a year at the p90, ended by hunger, thirst and wounds in the crowd (e087) | **large**: bound by the crowd, not the season |
| travel against the places | a migrant crosses places within a year; a resident's home fits in one place | a grown body travels a few cells of 512; a place fed in a lean month is 9-15 cells away over land, beyond the eye (e086); under Q the winter is waited out where it falls (1-2 cells), nothing asks a body to leave (e087) | **large** |
| the day against a life | a body lives many days and can tell night from day | a grown life is about 7 days; the day's swing is wider than the bands (e071) | medium |

### F. The ecosystem (outcomes, never written)

| element | ideal | today | gap |
|---|---|---|---|
| ways of living | many; the user asked for about 20 (2026-09-11) | 7.53 kinds at a census, 4.35 kept to a place, over the six-seed ladder (e092); no plant law since has raised the count on any seed (e088-e091). Read over a run instead of at a census: 8 ways hold 5% of the grown bodies **in the mean**, 17 reach the line at some point, 3 hold it in 90% of the run's 51 censuses, and 1 at every one - because a way's share swings by 61% of its own size and 84% of the dips come back (e094) | **large** |
| dominance | no line above a fifth of the animals | the largest line holds 42-78% of the land's bodies, by the seed (e092) | large |
| food web | three or more levels; hunters of several kinds | kills are 27% of what bodies eat; the largest land kind takes half its food from kills; pure flesh kinds 2-4% (e075) | medium |
| crowding | numbers limited by food, hunters and seasons | numbers limited by room: **46-49% of children have no room and 44-51% of moves are blocked, in every one of six seeds** (e092; e070 read 24-33% in its world); without the hunter the grazers double (e076). Room is counted in blocks, not in outline, so a law that pays per open face does not thin it: under the light the crowd is 1.05 bodies a cell against 1.04, and 1.76-2.18 where the light-led kinds stand (e093) | **large** |
| cycles over time | predator and prey swing; seasons move numbers | the land's bodies swing twofold over a year; forms do not follow (e070) | medium |

### G. Cycles of the world

| element | ideal | today | gap |
|---|---|---|---|
| matter | closes between land and sea | conserved in total; the land gains 6.5-7.3% over 90,000 steps, the runoff halves the pump (e072). Nothing carries matter back from the sea, so a law that moves matter downwind drains the land: seed drifting at 0.02 sends a tenth of what the grass sets into the sea and costs the land a fifth of its grass, at 0.2 the wood dies out (e090) | small, but it prices every law that moves matter |
| water | a body drinks from the world and gives back | free to the body in the default world (W1 closes it, not kept, e081) | small |
| heat | bodies and places exchange heat | a body holds heat and pays to hold its band (e072); it does not warm its cell | small |

## 3. Where the bottlenecks are

1. **A life is too short and too local for the world we built** (E, and through it D and part of F). To a body the
   world is the same everywhere and all the time; places and seasons are felt only by lines over generations. What
   follows from it: sight not bought (e070), cold a flat tax (e071), no kind by temperature band (e072, e073), no
   refuge (e077-e080), lines held by places, not by bodies moving (e083). The migrant is impossible at this ratio.
2. **Few kinds of food** (B, and through it F). A gut eats any plant, and there are three producers. Each food with
   the right mouthful added a way of living: wood's browse (e073), the flesh of kills (e075).
3. **Parts whose worth does not depend on shape** (C). Forms differ by what they hold, not by how they are built.
4. **The crowd sits at its income edge, and absorbs what is added to it** (F, and through it B and C). It was
   listed as a consequence of 1 and 2 until P1 and P2 argued otherwise: what ends a grown life is the crowd's
   income, wherever it lives (e087), and the three foods of P2 each died of the same thing - the bodies already
   there ate the new food (e089, e090) or filled the new place with the light tail of their own forms (e091).
   Nearly half of all births fail for want of room (46-49%) and 44-51% of moves are blocked, and those are the
   numbers the six seeds agree on (e092). A new axis has to thin the crowd, or make a place differ over more
   ground than a body covers, or it is averaged away. **What will not thin it**: a law that pays a body per unit
   of its outline. Room here is counted in blocks - one block, one sub-cell, whatever sits around it - so
   spreading buys faces and no room, and the light's own kinds stand twice as thick as the world (e093). A law
   that thins the crowd has to make one body's income fall when another arrives on its cell.

The dominant line may still follow from 1 and 2: the best eater of the one food spreads. **Judged how**: the ten
laws rejected since e075 were read on three seeds against a line (+1 kind) no larger than the spread the seeds make
on their own - 1.02 kinds over six runs of the same world, and every large "effect" among the last three belongs to
the seed whose control counts highest (e092). The ladder is six seeds wide now and the rule is in `foundation.md`:
a distribution against a distribution, with the categorical done-whens deciding as before. None of the three laws
raised the count on any seed, so what was unreadable was the size of the fall, not its direction.

## 4. Lessons that hold across experiments

Each holds under the conditions it was found in.

- A difference a body can ride out is not an axis (e060). A law must differ over more ground than a body covers in a
  life, or the crowd averages it away (e057), and change close to a life's length if behaviour is to follow it (e049).
- A law that moves the amount, time or place of the one food changes the number of bodies, not the ways (e060).
- A food is its mouthful: what a bite gives is the law, not what it costs (e075). A thin patchy food buys movement; a
  rich one buys one winner (e073).
- The crowd makes hunters and the thin land makes movers (#68). Without the hunter the crowd doubles (e076).
- A way that needs a part the population has lost is a question of reach, not of ecology: test it by injection
  beside a control (e074, e076).
- Heat is paid in water, and water sets where land bodies live (e078). Lines are kept apart by places a leader does
  not cross (e083), and a world's regions can be read from its climate alone (e084, e085).
- A law added alone meets a world without its counterweights (e066-e071); a set searched together can hold (e072).
- A store the producers fill and empty by the growth's own factors (warmth x water) sits at the same level all
  year: it outlasts the leaf in the cold but does not pile up or flush with the season (e088).
- A food that comes in one mouthful with another does not part the kinds: seed taken with the grass of its cell, by
  the hunter's tooth, fed no seed eater (e089). A food is its mouthful (e075) from the other side. Raising its worth
  moves the share, not the kinds: at two fifths of a kind's plant energy seed still led none (e090).
- A food feeds a new kind only when what it takes to reach it is something a body is born with. Browse needed a
  tooth and made one (e073); the water's layers need a density and hold theirs. Seed was parted by a mouthful (e089)
  and by a tool half the world already carried (e090); a crown by a mass that damage and fat move within a life, so
  its bodies are the broken ones of forms that live below, and no form is bound to it (e091).
- A measure of place breaks when bodies change place within a life: kinds kept to a place fell 1.6 with the crown on,
  and two thirds of that came back when the crown was read as the land (e091).
- A law that carries matter one way over a world with a sea drains the land, and the drain is the price of the
  distance: what moves a food off the lawn moves a tenth of it into the sea (e090).
- A seasonal place's winter is a third of its year at any year length: the year sets whether a body meets it, the
  terrain how far the refuge is (e086).
- A body that can wait lives through a winter it meets, and then does not move (e087). What ends a grown life is
  the crowd's income, wherever it lives, not the season (e037, e038, e087).
- A measure that is a conjunction over the censuses says nothing about the world. Asking a kind to hold 5% of the
  grown bodies at every one of a run's 51 censuses counts 1 where the world holds 8 in the mean and drives none of them out,
  because a way's share swings by 61% of its own size (the year explains a tenth of it) and 84% of the dips come
  back (e094). Judge on a census and on the mean, never on an AND.
- A material whose worth is set by the shape a genome develops does part kinds - where its counterweights leave
  it somewhere to live. The light parted a kind on three seeds of six and only in the water, because on land an
  open face is a water bill (e093). It is P2's law from the other side: the thing a body must be born with was
  the open face, and the place where it pays was the water.
- A law whose income does not fall as the crowd grows has no middle. One step of the ladder separates a light
  that earns less than a block's upkeep from a light that makes the whole world a mat of 11-block bodies and
  halves the ways of living (e093).
- The seed re-draws the world, so a law's effect on one seed carries the control's draw as well as its own: six runs
  of the same world spread 1.02 kinds and 1.24 placed kinds, and each law's own three spread as widely (e092). Read
  a distribution against a distribution, and keep the categorical questions for the deciding.

## 5. Next

The next piece fills the largest gap of section 2; it is designed as cycles before it is built (`CLAUDE.md`).
**P1 (#93) closed 2026-09-20 after e087**, by the user's choice, with two of its three experiments unspent. A year of
1,200 steps with Q lets a grown body wait a winter out (81-84% live through it, torpid), so the season can now reach
a body. But a grown life stays at 3/4 of a year: it ends in the crowd, of hunger, thirst and wounds, wherever the
body lives, and kinds kept to a place fall. The gap left is the crowd's income, which P2 addresses more directly
than a redesign of P1 would. Y and Q stay out of the default world; Q is a law ready for a piece that needs it.

**Chosen 2026-09-20: P2, as #99. Its seed track ended the same day.** Stage B (e088): seed at `seed_share` 0.2
passes. Stage C, first (e089): S+Fb not kept, no seed-led kind, since a gut takes seed mixed with the grass and the
tooth that opens it is the hunter's. Stage C, second (e090, #100): seed given a place (the wind), a tool (any hard
tip) and a worth (grass 0.8 fiber) of its own - still no seed-led kind on any seed, kinds do not rise, the largest
line grows on two; and the drift that moves seed off the lawn drains the land into the sea, so stage B caps it at
0.02. By #100's stopping rule the seed track ends with one stage C slot unspent.

**P2 ended 2026-09-20 with e091 (#101), by its own stopping rule.** The crown over a stand was built as a place:
a layer of its own, holding half the stand's yield as fruit that nothing on the floor reaches, and holding only bodies
under ten times their cell's wood. It is lived in - 3-5% of the grown bodies, a third of their food fruit, their own
hunters, and travel of 20-26 cells where the floor's bodies manage 4-7 - and no kind lives there, on any seed. The door
is the reason: mass is moved within a life by damage and fat, so the crown holds the broken bodies of forms that live
below (born at 44-48, counted at 36-37, nine blocks lost), and nothing about it is inherited. Kinds fall on two seeds.

**P3 step 1 spent 2026-09-20 with e093 (#103): a block that eats the light, not kept.** A fifth block kind gains
matter for each of its faces open to the air, times the light on its cell, out of that cell's soil. At the one rate
the ladder leaves (`light_gain` 0.016; 0.008 earns under a block's upkeep, 0.032 makes the world a mat of 11-block
bodies and halves the kinds) it parts a light-led kind on three seeds of six and gives this world its first bodies
that are not filled rectangles - a hollow frame, a bar one block wide, 1.38-1.62 open faces a block against 0.94.
Every one of those kinds lives in the water, because on land an open face is a water bill (e067). Kinds do not rise
(7.02 against 7.53, inside the spread) and **the crowd does not thin**: 1.05 bodies a cell against 1.04, and
1.76-2.18 where the light-led kinds stand. That was the piece's own wrong-if, and it says why the crowd is not
broken this way (section 3, item 4). **#102 is done (e092)** and **#105 is done**: the ladder is six seeds wide, the
judging is in `foundation.md`, and a long batch is watchable from outside.

**Before that, e094 (#106) re-read the twelve censuses we had, with no runs.** The ways of living were never being
driven out: `kinds_held` was an AND over 51 censuses of a share that swings by 61% of itself. It is dropped
(`foundation.md`), stage C is judged on kinds at a census and ways at 5% in the mean, and on 90% of the censuses the
world stands at 3 of #76's 4 kinds instead of 1. The size of the gap is unchanged - 8 ways against an ideal near 20,
the largest line 42-78%, half of all births with no room - but one of the two numbers we read it with was broken.

**The next step of P3, not yet designed as a cycle:** the one law left out of e093 on purpose - bodies that shade
each other and the cell under them, which turns the light from an income each face draws into a flux the bodies on
a cell share, so that one body's income falls when another arrives. It is the only form of the light that could
thin the crowd, and it is also the first law of this world in which a body is a place for another body. #104
(re-testing P2's foods in a thinner crowd) still waits on a crowd that has moved.

| piece | fills | contains |
|---|---|---|
| **P1. A life that meets its world** | E, D, part of F | the ratio of a grown life to the year and to the places: a shorter year (stages A and B again), what kills the young today, a body that waits out a bad season on its fat, what makes travel pay (#93) |
| **P2. A food web** | B, F | kinds of plant matter that need different mouths and guts (#34), seasonal rich food, each food's mouthful set so that it feeds a way. Spent (#99, #100, #101): parted by a mouthful, by a tool and by a place, no plant food has fed a kind |
| **P3. Bodies whose shape does something** | C | parts that work only at a tip or an edge, a leg that walks only where it touches (#52); later 3D (#5) |

P1 was called the deepest root and P2 the most direct route; both are spent without a law kept, and both pointed
at the crowd instead (section 3, item 4). P3 is taken now because it is the one piece that works on the crowd and on
the ways of living at once. What is left of P1 (what kills the young, what makes travel pay) waits.
