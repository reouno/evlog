# Gaps

Status: first draft 2026-09-19 (after e085), to be agreed with the user. It is how the next step is chosen from here.

## How this file is used

- **The next step comes from the largest gap here**, not from the last experiment's "Next". A chain of steps that
  each fix the last result adds one or two laws at a time, and a world whose balance rests on many things at once
  does not hold together that way (e028-e040, e066-e071, e077-e085 all went so).
- **Every result updates this file.** The runs are why we experiment, so a result is read against the rows it
  touches: the "today" column, the size of the gap, the ranking, and, when a result says so, the ideal or the plan
  itself. An experiment's Conclusion names the rows it changed; the change log at the bottom says what and why. A
  result that changes nothing here is a sign the experiment asked the wrong question.
- **A step fills a piece**, not a law. A piece is a missing part of the world large enough to change what can live
  in it; looked at closely it is several laws, or a cycle redesigned. It is designed as cycles before it is built
  (what it takes from whom, what refills it, what limits it, the balance it should settle into: who wins where and
  when), searched in stages from the cheapest layer (`foundation.md`), and measured cycle by cycle, so that a piece
  that fails still says which part failed.
- **The ideal is taken from the real world**, as a source of premises, not a target (`principles.md`).

## 1. The ideal, as a picture

A savanna with its rivers, woodlands and coast, as a film crew would show it:

- **Many ways of living at once.** Grass eaters, leaf and bark eaters, fruit and seed eaters, hunters of several
  sizes and styles (ambush, chase, pack), scavengers, filter feeders and bottom feeders in the water. No one of them
  is most of the animals.
- **A food web.** Plants of several kinds, each needing its own mouth and gut (soft grass, hard browse, rich seasonal
  fruit); animals eating animals; the dead eaten and returned to the soil.
- **Places that hold different animals.** Woodland, open grass, marsh, desert, shore, cold highland, each with its own
  residents and borders between them; some animals keep to one place, some cross them.
- **Time that moves animals.** Herds follow the rains; animals breed in a season; some sleep through the bad season;
  predator and prey numbers swing against each other.
- **Bodies that differ and whose shape does something.** Sizes from mouse to elephant; legs, jaws, horns, shells,
  fins, and a reason for each.
- **Animals that behave.** They look, chase, flee, go to water, return home, gather.
- **History.** Lines appear, spread, split and die out over long runs, and no line holds the world for good.

## 2. The table

Size: how far today is from the ideal, and how much of the rest it holds back (large, medium, small).

### A. The physical world (stage A)

| element | ideal | today | gap |
|---|---|---|---|
| places | many wide places, each with its own residents, borders between | 512x512 torus; c1225 holds 12 habitats of 2%, 5.0 effective regions (e084), third of stage A's 34 climates (e085) | small |
| time | a day, a year, weather | a day of 75 steps, a year of 11,880, one wind (e061) | small in itself; see E |
| water and heat | rivers, lakes, rain shadows, cold and hot places | emerge from the climate (e061); the ground's water is what land bodies live on (e078) | small |

### B. Producers (stage B)

| element | ideal | today | gap |
|---|---|---|---|
| kinds of plant food | several, each needing its own mouth and gut; some seasonal | grass (any gut), algae (a surface gut), wood's browse at 3e-5 (needs a hard tip, e073); carrion and litter | **large**: few ways to eat |
| response to eating | grazed plants regrow, defended plants resist, fruit is offered | every producer grows by its stand and is grazed to 1-4% of it (e065) | medium |
| plants as places | a forest is a home, a cover and a food | the stand is a home only through its wet ground (e078) | medium |

### C. Bodies and genome

| element | ideal | today | gap |
|---|---|---|---|
| parts | parts whose worth depends on where they sit and how they move (legs, jaws, fins, shells) | 4 block kinds on a 2D grid of side 4-16; every block's work pays best packed, so bodies fill their grids (#52, e047) | **large** |
| size | a thousandfold range, each size with its place | 21-35 blocks; winners differ 1.3-2.2x (e055, e075) | large |
| life history | lives that span seasons; clutch sizes, fat, dormancy chosen by selection | breeding values fixed (e069 from the genome cost kinds); fat from the genome (e072) | medium |

### D. Behaviour

| element | ideal | today | gap |
|---|---|---|---|
| senses | eyes and noses that pay | sight through sensor blocks is not bought (2-4% look out, e070) | large, but the cause is probably E |
| decisions | chase, flee, go to water, go home | a linear reflex, about 16 readings to 4 actions; no memory; learning not selected (e050) | large, same |
| movement | some stay, some travel far | a grown body ends 3-28 cells from its birth, depending on the laws (e070-e082); 33-45% of moves blocked (e070) | large, same |

### E. A life against the world's scales

| element | ideal | today | gap |
|---|---|---|---|
| life against the year | many animals live through several seasons; short-lived ones sleep through the bad one | a grown body lives 500-570 steps, **1/20 of a year**; half the dead die by 75 steps, as children (#93) | **large** |
| travel against the places | a migrant crosses places within a year; a resident's home fits in one place | a grown body travels a few cells in a world of 512; the season is felt by a line over 20 lives, never by a body | **large** |
| the day against a life | a body lives many days and can tell night from day | a grown life is about 7 days; the day's swing is wider than the bands (e071) | medium |

### F. The ecosystem (outcomes, never written)

| element | ideal | today | gap |
|---|---|---|---|
| ways of living | many; the user asked for about 20 (2026-09-11) | 7.66 kinds at a census, 4.62 kept to a place (e081's control) | **large** |
| dominance | no line above a fifth of the animals | the largest line holds 42-63% of the land's bodies (e082) | large |
| food web | three or more levels; hunters of several kinds | kills are 27% of what bodies eat; the largest land kind takes half its food from kills; pure flesh kinds 2-4% (e075) | medium |
| crowding | numbers limited by food, hunters and seasons | numbers limited by room: 24-33% of children have no room (e070); without the hunter the grazers double (e076) | medium |
| cycles over time | predator and prey swing; seasons move numbers | the land's bodies swing twofold over a year; forms do not follow (balance.md section 2) | medium |

### G. Cycles of the world

| element | ideal | today | gap |
|---|---|---|---|
| matter | closes between land and sea | conserved in total; the land gains 6.5-7.3% over 90,000 steps, the runoff halves the pump (e072) | small |
| water | a body drinks from the world and gives back | free to the body in the default world (W1 closes it but was not kept, e081) | small |
| heat | bodies and places exchange heat | a body holds heat and pays to hold its band (e072); it reads its cell and does not warm it | small |

## 3. Where the bottlenecks are

Reading across the table, three roots hold most of the large gaps.

1. **A life is too short and too local for the world we built** (E, and through it D and part of F). A body lives a
   twentieth of a year and travels a few cells in a world of 512, so to a body the world is the same everywhere and
   the same all the time; the places and seasons stages A and B made are felt only by lines over generations. The
   failures that follow from it: sight not bought (e070), the cold a flat tax (e071), no kind by temperature band
   (e072, e073), the refuge (e077-e080), lines held by places rather than bodies moving (e083). Behaviour cannot pay
   while nothing within a life differs. The migrant of `vision.md`'s table is impossible at this ratio.
2. **Few kinds of food** (B, and through it F). A gut eats any plant, and there are three producers. The number of
   ways of living that coexist is bounded by the independent things they live on (`vision.md`'s working
   hypothesis), and each food with the right mouthful added a way: wood's browse (e073), the flesh of kills (e075).
3. **Parts whose worth does not depend on shape** (C). Bodies fill their grids because every block pays best packed;
   a shape that reaches out has no reason (#52). Forms differ by what they hold, not by how they are built.

The crowd and the dominant line may follow from 1 and 2: bodies that neither move nor eat differently pile up and
the best eater of the one food spreads.

## 4. Candidate pieces (to be ranked with the user)

Each is a piece in the sense above, several laws designed together. None is designed yet.

| piece | fills | contains (to be designed) | cost of the first stage |
|---|---|---|---|
| **P1. A life that meets its world** | E, D, part of F | the ratio of a grown life to the year and to the places: a shorter year (a climate parameter; stages A and B again), what shortens lives today (children dying in the crowd), a body that can wait out a bad season on its fat (dormancy as a law of the body), and what makes travel pay | stage A/B checks at a new year: minutes a climate |
| **P2. A food web** | B, F | kinds of plant matter that need different mouths and guts (#32, #34), seasonal rich food (fruit, seed), what returns the dead, each food's mouthful set so that it feeds a way (e073, e075's lesson) | producers alone first (stage B), then bodies |
| **P3. Bodies whose shape does something** | C | parts that work only at a tip or an edge, a leg that walks only where it touches (#52), a wider range of sizes; later 3D (#5) | a body law, bodies only |

My reading, to be checked with the user: P1 is the deepest root, since it decides whether any place or season can
act on a body at all, and P2 is the most direct route to more ways of living. P3 waits until a differing world
asks for shapes (`principles.md`: the space of bodies comes after the environment).

## Change log

- 2026-09-19: first draft, after e085 and the user's direction (choose the next step from the gaps, fill a piece in
  a large step, update the table from every result).
