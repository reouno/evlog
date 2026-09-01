# e022 The spill

Date: 2026-09-01

## Purpose

e021's canopy gave the closed world its first standing stores of food (trees of 50-400 bites,
an orchard in nine runs and a forest in three), its record income, and the longest coexistence
of two lineages since e012 - and still no tooth, and still one kind of body. The report named
the reason: a body eating a tree stands on it, a held cell neither grows nor claims light, so a
tree feeds one gut at a time and the crowd disperses between gulps. e011, the only world where
teeth paid, had rich cells that kept producing while 45-77 bodies ate them at once.

The real world's trees do not stop catching light when a deer stands under them, and what a full
crown cannot hold falls: fruit, mast, leaves, on the ground around the trunk, where the animals
gather without touching the tree. This experiment writes that as a law of the world: a full crown
keeps taking the light it stands in (e021's saturation is dropped) and what a column cannot hold -
the growth past the cap, or under a body - falls as fruit on the ring of cells around it, plant
matter lying on the ground that any gut can eat and that rots into the soil if nobody does. e021's
second pilot showed this flow as a famine, because the hoarded light was destroyed; sent to the
forest floor it should be a rich place with a radius: e011's rich cell, closed.

Riding along (#30): mutation becomes a chance per base (2/512 per copy, the same mean as e021's
exactly two per child), so that most children copy their parent to the base and a few carry
several changes - the rate a property of the genome, not a rule per child.

## Hypothesis

1. **The world stands without saturation.** No extinction, population cv under 0.10 over the
   second half, matter conserved to 0.05%, in all twelve runs: light a full crown takes is
   fruit now, not a blight (e021's pilot 2 killed every world in 700-3,200 steps).
2. **Fruit is the harvest.** Intake from fruit is at least a third of the food eaten in every
   run, and the standing trees are eaten less than in e021's forest (the tree is the source,
   its ring the table).
3. **A crowd forms.** Contacts per body per step exceed e021's forest ceiling (0.093) in every
   run, and the neighbors-per-body distribution grows a tail: bodies gathered on the rings.
4. **The crowd pays for a second kind of body.** By #19: in at least two seeds of four, a
   lineage with a different body coexists with the winner for over 100,000 steps, or the
   biters' share exceeds 0.01 (the first tooth since e012), and dead matter is a larger share of
   the intake than e021's 1% (a body dying in a crowd is eaten).
5. **The canopy pays the world more.** Food eaten per step exceeds e021's in every world (high
   83.2-83.8, half 100-109, flat 105-113): a full crown reclaims the light the bodies' shadow
   wasted (29-35% of the sun in e021).
6. **The ring, not the wide fall.** With the fruit spread over the 24 cells within distance 2
   (pilot only) the crowd is weaker and more of the sun is lost: the fall's radius is a
   design choice with a right answer, not a dial.
7. **Mutation per base changes the distribution, not the world.** The share of children born
   without a mutation is about e^-2 = 13.5%, and the control (e021's law with the per-base
   mutation, four seeds) has e021's winners, lineage counts and income.

## Method

Code: e021 (`experiments/e021_canopy`) with the canopy's saturation dropped and the spill
added; the control at `spill 0` is e021's law exactly (saturation, a held column claims
nothing), so the mutation law is the only difference between it and e021's runs.

- `Food::shade` with `spill`: a column claims at `shade` (2) times (the difference of the
  columns less the distance walked) over the cap, whatever its own height - a full crown as
  hard as a bitten one - and a column under a body claims too. What it takes is the crown's
  light, above the body; only the cell's own sun falls in the body's shadow (e016). The sun is
  still only moved: claims past a cell's whole sun share it in proportion. A full tree alone on
  a bare lawn takes the whole sun of the cells within five of it and a part out to eight, 200
  suns per step at rate 2 (e021's full crown took nothing; a half tree took ten suns).
- `Food::regrow` with `spill`: a cell grows out of its soil by at most its light (own sun plus
  the crown's); the growth that would pass the cap, or that a held cell cannot make, is fruit,
  taken from the cell's soil and returned by `Food::spill` in equal shares to the eight cells
  of the ring (`spill 1`; radius 2 is the 24 cells within two). Fruit is a third kind of matter
  lying on a cell beside the plant and the dead (`fruit`, at most `res`): it counts in the
  column, a gut takes it in the cell's proportion, it rots into the soil at DECAY (1% per
  step), and a body's diet counts it as plant. A column with no soil takes light and wastes it,
  as ever (`barren`).
- Mutation: each base of a child's genome flips with probability `mutation` (2/512) instead
  of exactly two bases at random; `mutation 0` is e021's rule.
- `trees`, `tree_res` and `tree_eaten` count the standing plant (the column less the dead and
  the fruit on it), so that a pile of fruit is not a tree.

Pilot (seed 9, 100,000 steps, six runs at once): the three worlds at spill 1, and on the
mountain-rain world spill 2, shade 1, and the control. All six stood (matter held to 0.005%).
At spill 1 the mountain world ate 102-115 per step (e021: 83), 80-120 of fruit fell per step
and 45-70 of it was eaten, 450-1,500 trees stood, contacts were 0.3-0.5 per body per step
(e021's forest: 0.093), dead matter 16% of the intake (e021: 1%), and a tooth appeared once
(biters 0.008 at step 30,000). Spill 2 dispersed it: 19-25 of fruit per step, 13-16 eaten,
31-34% of the sun barren, contacts 0.13. Shade 1 stood but weaker (fruit eaten 26-56, barren
19-25%). The control reproduced e021 (7-133 trees, no fruit, contacts 0.04, clones 13.3%,
2.00 mutations per child). The half-breath world swung (372-1,654 bodies, one crash at step
70,000 as trees boomed to 2,664). Spill 1 and shade 2 are the defaults; the pilot files were not
kept.

The batch showed what the pilot's one seed could not: the start is a lottery. High seed 4 died
at step 3,324, and a trace of the start (`EVLOG_TRACE=1`, every 100 steps) showed why. The run
starts with every cell at the cap and no soil; with fruit falling from the first step the
population booms to 4,052 by step 100 and eats 45% of the world's plants in those 100 steps;
when the stock is gone the grazed cells cannot regrow, because every full column around them
takes their whole sun (regrowth 7-12 per step against e021's 90 at the same point), so all of
the world's production (130-140 of fruit per step, most of the sun) lies on the rings of the
surviving trees, clumped, while the bodies - which see two cells - wander the dark lawn and
starve. Every seed crashes to a few hundred bodies by step 500-1,000; most recover as the far
lawn regrows and the crowds find the trees. A survey of the start (24 runs of 10,000 steps on
the Ubuntu box: seeds 1-8 of the three worlds; files not kept) counted 5 deaths in 24 (high
seeds 4 and 8, half 6 and 7, flat 8, at steps 2,149-3,723) and bottlenecks of 7-431 bodies in
the survivors (half seed 1 passed through 11). Under e021's law the same seed 4 never falls
below 750. The runs were left as they were: the law is reported with its start, and the dead
run counts.

The spill also changes the speed: 150-190 steps per second with twelve runs on the machine
(e021: 178-212), the fruit pass and the crowd's contacts.

Arguments `spill` (12th; the radius of the fall, 1 by default, 0 is e021's law) and `mutation`
(13th; per base, 2/512 by default, 0 is two per child). New columns: `fruit` (fallen per step),
`fruit_stock` (lying now), `fruit_eaten` (intake from fruit per step), `clones` (share of the
children conceived without a mutation), `mutations` (mean per child); `fruit` and
`fruit_intake` per place in `places.csv`; `spill` and `mutation` in `terrain.json`.

Worlds, sixteen 1,000,000-step runs at 128x128, seeds 1-4: rain on the mountains (`high`),
half the breath (`high 0.5`) and rain everywhere alike (`flat`) at spill 1, one thread each on
the Mac (eleven of them; flat seed 4 moved to the Ubuntu box to free a core); and the control
(`high`, spill 0) on the Ubuntu box. The reference
is e021's twelve runs (`../e021_canopy/results/`; the same terrains, seed for seed).

    cargo run --release -p e022_spill -- <steps> <seed> <size> <widths> [cell_energy] [matter] [relief] [flow] [rain] [breath] [shade] [spill] [mutation]
    bash experiments/e022_spill/run.sh 1 2 3 4
    CONTROL=1 bash experiments/e022_spill/run.sh 1 2 3 4
    uv run python experiments/e022_spill/report.py

## Result

All numbers are medians over the second half unless said otherwise; ranges are over the seeds
of a world (`high`: rain on the mountains; `half`: half of the breath; `flat`: rain everywhere
alike; `control`: e021's canopy with the per-base mutation, on `high`). The report
(`report.html`) has the charts, the maps, the bodies and the viewer.

- **The start is a lottery; after it the world stands.** High seed 4 died at step 3,324 and the
  survey counted 5 deaths in 24 starts (Method). The eleven survivors stand: population cv
  0.03-0.11 (flat seed 3 at 0.109), food eaten last quarter over third 0.96-1.07, matter held
  to 0.11% at worst (flat seed 1; the columns are f32 and stand 30-40 tall), 0.03% elsewhere.
- **Fruit is the harvest, and the world has two states again.** Fruit is 44-77% of the food
  eaten in ten runs of eleven (68-128 falling per step, of the sun's 164) and 7.7% in high seed
  1, which stayed in e021's state (158 trees, contacts 0.03, e021's bar). The ten split by the
  fruit share: the crowd state at 70-77% (flat 1 and 4, high 2, half 2 from step 400,000, half
  1 from 900,000; half 4 held it for 300,000 steps and fell back) and the mixed state at
  44-62%. Trees stand 290-660 to a run (e021's forest made permanent, its orchard gone) and are
  eaten 2-9% of the intake, about e021's forest. In the mountain worlds the fruit falls where
  the soil is, not where the rain is: high seed 2 drops 48 per step in the valleys against 20
  on the ridges, and holds 474 bodies in the valleys against 254 on the ridges - e020's height
  sorting turned over, the crowd on the lake.
- **A crowd forms and eats its dead.** Contacts per body per step are 0.22-0.76 in the ten
  runs (e021: 0.008-0.093, control: 0.03-0.05), 0.029 in high seed 1; they track the fruit
  share run for run. Dead matter is 10-26% of the intake (e021 and the control: 1%).
- **A new winner, still one, and no tooth.** In the crowd state the winner is a frame: 19-24
  cells around the rim of the 8x8 grid and none inside, 6.5-7 world cells wide, 17-20 digestive
  and 1-4 hard at the corners - a hollow square that stands around a tree without holding it,
  its guts on the ring where the fruit lands -
  mass three times e021's bar (flat 1: 23.8 with 3.9 hard, one lineage all 1,000,000 steps;
  flat 4: 20.4, one lineage all run; high 2: 19.3, 877,000 steps; half 2: 18.4 with 3.3 hard,
  567,000 steps beside a bar of 11.2 for 326,000 of them). The mixed state has a middle body
  of 10-15 cells on 3 world cells; high seed 1 has e021's bar of 7.5. A giant of 37 cells (9.6
  hard) held a valley of high seed 3 for 16,000 steps. Lineages alive stay at 1-3 (peaks 8-9).
  The biters' share rises above zero for the first time since e012 - 0.006 on median in flat
  seed 1, peaks of 0.008-0.026 in seven runs - and falls back every time; every top lineage
  has bite 0. Hard cells pay as armor (flat 1: 3.9 per body) on a body touched 0.5-0.8 times a
  step.
- **The crowd state is the richest closed world so far.** It eats 115 (high), 120 (half) and
  105-134 (flat) per step against e021's 83, 100-109 and 105-113 - the record 134 in flat
  seed 4 - because the bodies' shadow falls from e021's 29-38% of the sun to 0.5-0.7% (a body
  in a crowd stands on a tree whose crown takes light above it). The mixed state eats 97-111,
  e021's level or under it; high seed 1 eats 84.2, e021's mountain income. Sun lost to empty
  soil is 15-34% (control 20-26%).
- **The ring, not the wide fall** (pilot): at radius 2 the mountain world dropped 19-25 of
  fruit per step against 80-120, ate 13-16 of it against 45-70, lost 31-34% of the sun to empty
  soil, and had contacts 0.13 against 0.3-0.5.
- **Mutation per base changes the distribution, not the world.** 13.5% of the children are
  clones in every run (e^-2), at 2.00 mutations per child; the control reproduces e021's
  mountain world: 81-84 eaten (e021: 83.2-83.8), a bar of 7-8, lineages 1-2, contacts
  0.03-0.05, trees 7-42, dead matter 1%.
- 103-177 steps per second with twelve runs on the Mac (e021: 178-212).

## Conclusion

1. The world stands without saturation: no - one run of twelve died at the start and the
   survey says one in five does; the survivors stand (cv 0.03-0.11, steady to 4%). The blight
   is gone (the light a full crown takes is fruit), and a new failure takes its place: a dark
   lawn under the trees at the start, and bodies that cannot see the piles two cells away.
2. Fruit is the harvest: yes in ten runs of eleven (44-77% of the intake); the trees are eaten
   as much as e021's forest, not less.
3. A crowd forms: yes in ten of eleven, at two to eight times e021's forest ceiling, and it
   eats its dead (10-26% of the intake).
4. A second kind of body: a new winner, not a second one. The crowd picks the frame (19-24 cells
   around a tree, 7 world cells wide, armor at the corners) where e021 picked the bar, the middle body in the
   mixed state, and the bar where the crowd never came; each sweeps its run, lineages stay at
   1-3, and the tooth appears (biters up to 0.026) and never pays.
5. The canopy pays more: yes in the crowd state (115-134, the record), no in the mixed state
   (97-111).
6. The ring, not the wide fall: yes (pilot).
7. Mutation per base: yes; the control is e021 in every measure.

What it changes: the spill at radius 1 is kept as a law of the world, with its start marked as
the open wound (a fifth of the worlds die in their first 4,000 steps). The closed world has its
crowd back for the first time since e012, the scavenging e017 was written for, its richest
state, and a winning body that is not a bar - and it has the same shape of answer as ever: one
winner per run. Mutation per base is kept. The next steps follow from what the crowd exposed:
#26 eyes that see far (the start kills bodies that cannot see a pile two cells away), then #27
what flesh is worth (a body of 20 cells is worth 0.4 plus its energy, a few steps of fruit, so
a tooth loses to a gut that eats what falls) and #25 what a block weighs; #24 weather after
them, with a crowd for it to work on.
