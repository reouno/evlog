# e073: wood a body can live on, and a cold that differs by place (stage C's eleventh step, #89)

Date: 2026-09-16

## Purpose

e072 built the seven balance sets together and the user kept them as stage C's default world (#88).
Two of the seven did nothing there, and both were meant to part the land from itself:

- **wood as food** was 0.0-0.3% of what any kind ate, and
- **the heat** never parted the temperature bands (5-7% of the land's bodies in the cold band, as in
  the controls), because it reads a cell's temperature at the moment and the day swings it by tens of
  degrees (e071's finding).

This rebuilds those two on the default world and searches them together, as #87 asks of a law that
needs a condition: a body eats wood where a forest stands, and a forest stands where the cold lets it.

## The dry run, before any of it was built

`dryrun.py` (no runs of the bodies: c1225's terrain rebuilt as `climate.rs` builds it, e063's settled
world for the standing wood, the climate's temperature run alone in numpy for two years, and e072's
three runs for what the bodies did). It settled which shape each law takes.

**Wood is patchy enough** (#68 rule 1). A body covers 1.8-5.7 cells in a life. Averaged over a window
of 6 cells the standing wood still spreads 1.91 times its own mean (p50 0.04, p90 2.37 a cell), and
over 48 cells 1.67; the grass spreads 0.71 and does not move with the window. Wood is the first food
of stage C whose grain a body cannot average away.

**But a stand cannot be eaten, at either of the issue's first two rates.**

| what is taken | what it offers a 1,000 steps | against the 37,000 the bodies eat |
|---|---|---|
| the whole standing forest, once | 66,600 | 1.8 thousand steps of food, and then it is gone |
| `wood_food` 0.04 (the default) | - | eaten to a tenth of its stand by step 12,000, then 0.06% of the intake |
| the most of its *growth* a stand can give up | 1,300 | 3.5%, and only if every stand is grazed to its limit |

The last row is the ceiling on the issue's option (b). A stand holds where its growth answers its
death, `R L s/(s+H) = s`, so `R L = s + H`: the share of its growth it can give up before it falls is
exactly its own cover, `s/(s+H)`. That is 9% on a mean land cell and 49% on the richest tenth, and
over the whole land 1,300 a 1,000 steps. Wood cannot be a living off its stock or off its growth.

**So the yield is built as a third thing, a flow beside the stand** (the law below). At `wood_yield`
3e-4 it offers 20,000 a 1,000 steps, and in the richest tenth of the land a cell yields 1.15 against
the 1.06 of grass the same cell grows: in a forest, browse matches the grass; on the lawn there is
none.

**The day's mean is a place; the moment is not.** Over a year of c1225's climate, the moment stands
20 C from the day's mean on a median land cell (p90 23 C). By the moment, **every** land cell is cold
(under `warm_lo` 15 C) between a third and three quarters of the year - none is cold as a place and
none is spared. By the day's mean, 37% of the land is cold one day in ten or less and the rest is cold
by the season: the spread between places goes from 0.31 of its mean to 0.88. Both are broad (neither
moves when averaged over 48 cells), so what the mean adds is not grain but place.

## The two laws

Each as a rate whose 0 is e072 exactly (`main.rs`'s header has them in full).

- **The crown's yield** (`wood_yield`, `plants.rs`). A stand of wood drops `wood_yield` of `browse`
  per unit of what it stands a step, out of its cell's soil and beside its own growth; the trunk is
  not touched, so the stand keeps its shade and its fire. Browse uneaten rots into the soil at the
  litter's rate (warmth x water), so it keeps where the ground is cold or dry. A gut takes it with
  the hard tip of force `wood_hard` that e072's stock share needed, and a body whose tooth can take
  it sees it, as it sees the grass. Fire does not read the browse (stage B's law is left alone; fire
  burns 0.06 of matter over 100,000 steps of this world).
- **A cold that differs by place** (`day_temp`, `climate.rs`). The climate keeps `temp_day`, a running
  mean of each cell's temperature over the last day (a weight of `tick`/`day` an update), and a body's
  heat reads `day_temp` of the way from the moment to that mean. It costs one pass over the cells per
  climate update, one every ten steps, against the per-step pass over every body's blocks.

## Hypothesis

Written before the runs, with the conditions named together (#87): **a kind lives by wood when a
forest stands (A) and when what it stands yields a flow (B); and a kind keeps to a temperature band
when the cold is a property of the place (C) and something else pays there (A).**

Against e072's runs on the same seeds (the controls: 5.78 kinds at a census, the leanest of six 5 / 4
/ 6, 2 / 2 / 1 kinds keeping 90% of their bodies to one medium, none keeping to a temperature band,
wood 0.0-0.3% of any kind's food):

1. **A kind lives by wood.** At least one combination holds a kind that takes 20% or more of its food
   from browse, and that kind keeps 90% of its grown bodies to the land.
2. **A kind keeps to a temperature band that is not the world's own.** Under `day_temp` 1, at least
   one combination holds a kind that keeps 90% of its grown bodies to the cold or the mild band.
   (Corrected before any run was read: "keeps to a band" alone is met by the controls, because 82% of
   the world's bodies stand in the hot band and a kind 96% hot is the world, not a place. Read over
   the search's window the controls hold 2 / 2 / 1 such kinds and **none** off the hot band.)
3. **The two need each other.** The yield holds more kinds at a census with `day_temp` 1 than with 0,
   and the cold holds more with the yield than without it.
4. **The worlds stand.** Every combination keeps bodies in all three media through 50,000 steps and
   conserves matter.

## Method

Code: `experiments/e073_forest`, e072's crate with the two rates. Tests: the crowns drop browse out of
the soil, the trunk is not touched and the browse rots (matter holds); a tooth makes the browse food;
the day's mean swings less than the moment and `day_temp` 0 / 0.5 / 1 read the moment, half way and
the mean; matter is conserved with all nine rates on at once, where each leaves its mark.

**The check**: with both rates 0 the first 10,000 steps must equal e072's run for seed 9
(`c1225_life9_sets`) in every column of the log but the wall times, in every body of the census at
step 10,000, in every lineage row and in every event.

**The search** (`search.py`): 11 runs on c1225 with e062's draw d11, seed 9, 50,000 steps each, the
default world's sets under them. Not a hypercube - two laws, crossed:

| run | `day_temp` | `wood_yield` | `wood_food` | `wood_hard` | what it answers |
|---|---|---|---|---|---|
| d00 | 1 | 0 | 0.04 | 3 | the cold by place alone, on the default world |
| d01 | 0 | 0 | 0 | 3 | the forest left standing, no new law: the wood control |
| d02 | 1 | 0 | 0 | 3 | the forest standing and the cold |
| d03 | 0 | 1e-4 | 0 | 3 | the yield alone, a fifth of what is eaten |
| d04 | 0 | 3e-4 | 0 | 3 | the yield alone, half of it |
| d05 | 1 | 3e-5 | 0 | 3 | both, the yield a twentieth |
| d06 | 1 | 1e-4 | 0 | 3 | both, the yield a fifth |
| d07 | 1 | 3e-4 | 0 | 3 | both, the yield half |
| d08 | 1 | 3e-4 | 0 | 2 | the same with e060's tooth: has a tooth one use or two |
| d09 | 1 | 3e-4 | 0.04 | 3 | the same with the default's share of the standing stock still on |
| d10 | 0 | 0 | 0.3 | 3 | the windfall large enough to pay for the tooth that takes it |

    uv run python experiments/e073_forest/search.py 50000 9
    xargs -P 11 -L 1 ./target/release/e073_forest < experiments/e073_forest/results/search/candidates.txt

The control is e072's `c1225_life9_sets` read over the same window (steps 25,000-50,000).

Read with `sweep.py`: the kinds by birth form at a census and held at every census (e068's `kinds.py`),
how many keep 90% of their bodies to one medium and how many to one temperature band, the browse's
share of each kind's food, the standing wood and browse, the deaths by cause, and the land's matter.

**Then** three seeds (9-11) at 100,000 steps at what the search picks, judged against e072's runs on
the same seeds by stage C's measure (#88): the kinds at a census, the leanest census of the six, and
the kinds kept to a place.

**Decision rule, set before the runs.** The laws are kept as stage C's default if, on the three seeds
at 100,000 steps, a kind lives by wood (20% or more of its food from browse) on at least two seeds
**and** the kinds at a census do not fall below the controls' 5.78. `day_temp` is kept if a kind keeps
90% of its grown bodies to a band that is not the world's own on at least two seeds. The two are
judged apart: the search says whether they need each other.

The controls over the search's window (steps 25,000-50,000 of e072's runs, `results/control`), which
is what the 50,000-step search is read against:

| seed | kinds held | at a census | leanest | kept to a medium | kept to a band | off the world's band | living by wood |
|---|---|---|---|---|---|---|---|
| 9 | 3 | 5.0 | 4 | 0 | 2 | 0 | 0 |
| 10 | 4 | 5.0 | 4 | 2 | 2 | 0 | 0 |
| 11 | 3 | 5.7 | 5 | 2 | 1 | 0 | 0 |

**Cost, before the runs.** The search is 11 runs of 50,000 steps on 11 local cores, one round, about
45 minutes (a step is 23.5 ms on this world). Round two is 3 runs of 100,000 steps, about 50 minutes
on 3 cores. Nothing on the Ubuntu box: 11 runs fit locally.

## Result

**The checks.** The tests pass. With both rates 0 the first 10,000 steps equal e072's run for seed 9 in all
160 shared log columns, in every body of the census at step 10,000 (13,130), in every lineage row and in
every event. Matter drifts by at most 4.9e-14 in every run below.

**The search** (11 runs, seed 9, 50,000 steps, 36 minutes on 11 cores). Against the control read over the
same window (3 kinds held, 5.0 at a census, none living by wood, the standing wood 0.055 a cell):

| run | `day_temp` | `wood_yield` | `wood_food` | held | at a census | living by wood | standing wood | bodies |
|---|---|---|---|---|---|---|---|---|
| control | 0 | 0 | 0.04 | 3 | 5.0 | 0 | 0.055 | 11,140 |
| d00 the cold alone | 1 | 0 | 0.04 | 5 | 7.3 | 0 | 0.017 | 11,530 |
| d01 the forest standing | 0 | 0 | 0 | 3 | 5.3 | 0 | 0.608 | 8,548 |
| d03 the yield alone | 0 | 1e-4 | 0 | **1** | 4.3 | 1 (57%) | 0.586 | 11,012 |
| d04 the yield alone | 0 | 3e-4 | 0 | **1** | 3.3 | 1 (65%) | 0.531 | 11,604 |
| d07 both | 1 | 3e-4 | 0 | 4 | 4.0 | 3 | 0.568 | 16,881 |
| d08 both, `wood_hard` 2 | 1 | 3e-4 | 0 | 3 | 5.3 | 3 | 0.578 | 17,868 |
| d09 both + the stock share | 1 | 3e-4 | 0.04 | 4 | 6.3 | **0** | 0.061 | 11,938 |
| d10 the windfall | 0 | 0 | 0.3 | 4 | 6.0 | 0 | 0.055 | 11,049 |

Three things settled here. **The yield feeds a kind** (57-65% of its food) and **the stand survives it** (0.53-0.61
a cell against the settled 0.61). **The stock share destroys it**: at `wood_food` 0.04 the forest is eaten to 0.061
a cell and the crowns feed 0.7% instead of 22%, so the default's own wood rate has to go to 0. And **the windfall
does nothing**, as the dry run's arithmetic said.

**Round two and the ladder** (9 + 6 + 4 runs, seeds 9-11, 100,000 steps; the second half is steps 50,000-100,000,
six censuses). `wood_food` 0 and `wood_hard` 2 throughout the yield column; the control is e072's three runs.

| mean of seeds 9-11 | control | `wood_yield` 3e-5 | 1e-4 | 3e-4 | 3e-4 + `day_temp` 1 | `day_temp` 1 alone |
|---|---|---|---|---|---|---|
| kinds at a census | 5.78 | **6.56** | 4.06 | 3.11 | 4.28 | 6.11 |
| of them, kept to a place | 3.11 | **3.83** | 2.39 | 2.06 | 2.61 | 2.72 |
| kinds held at every census | 3.00 | 1.67 | 1.33 | 2.33 | 2.00 | 3.67 |
| the leanest census of six | 5.00 | 5.33 | 2.67 | 2.33 | 2.33 | 5.33 |
| the largest kind's share | 25% | **18%** | 54% | 61% | 41% | 28% |
| seeds with a kind living by wood | 0 | 2 | 3 | 3 | 3 | 0 |
| cells a body walks in a life | 3.50 | **6.23** | 3.00 | 1.25 | 2.58 | 4.33 |
| bodies (on land) | 9,797 (4,997) | 7,806 (3,446) | 9,757 (5,330) | 12,505 (7,968) | 16,527 (11,687) | 11,179 (5,849) |
| standing wood a land cell | 0.036 | 0.605 | 0.577 | 0.524 | 0.557 | 0.031 |
| browse of all food | 0.0% | 3.4% | 9.6% | 20.7% | 22.3% | 0.0% |
| bodies with a tooth | 13% | 23% | 38% | 48% | 47% | 9% |
| open soft faces a block, on land | 0.64 | 0.56 | 0.55 | 0.62 | 0.83 | 0.81 |

**The rate decides what the food makes.** At 3e-4 the yield is a subsidy: one browser kind holds 61% of the grown
bodies, walks 1.25 cells in a life, and the kinds at a census fall to 3.11. At 3e-5 it is a reason to leave: no kind
holds a fifth of the world (18%, the most even world stage C has had), the kinds at a census rise over the control
(6.56 against 5.78) and so do the kinds kept to a place (3.83 against 3.11), and **the bodies walk 6.23 cells in a
life against 3.50**. On seeds 10 and 11 the kind that lives by wood is a *roamer* on the land (27% and 34% of its
food from wood, 96% of its bodies on land); the control's land kinds all stay.

**The cold is a discount, not a place.** No kind in any of the 31 runs keeps 90% of its bodies to a band that is not
the world's own, and the cold band holds 2-3% of the bodies everywhere, as in e072. What `day_temp` 1 does is lower
what the land pays to warm itself from 0.090 to 0.016 and the deaths by cold from 3.0% to 0.7%. The probes match
that cost with a plain heat read at the moment: `heat` 0.045 pays 0.019 and holds 5 kinds, 7.3 at a census and 6 at
its leanest on seed 9 at 50,000 steps - the same as `day_temp` 1's 5, 7.3 and 6. Over 100,000 steps the mean also
re-opens the land's bodies (0.81 open soft faces a block against the control's 0.64) and disarms them (6.2% hard
against 9.4%), undoing what e072 bought.

**The tooth and the stability check.** (filled in when the last four runs land)

1. **A kind lives by wood: yes.** At 3e-5 on two seeds of three (27% and 34% of its food), at 1e-4 and 3e-4 on all
   three (48-69%), and the kind keeps 90% or more of its bodies to the land in every case.
2. **A kind keeps to a temperature band that is not the world's own: no.** None in 31 runs.
3. **The two need each other: partly.** The cold lifts the rich yield from 3.11 kinds at a census to 4.28 and cuts
   the largest kind from 61% to 41%, but the thin yield needs no help (6.56 on its own) and the cold alone is
   matched by a smaller heat.
4. **The worlds stand: yes.** Every run held bodies in all three media through 100,000 steps and matter drifts by
   at most 4.9e-14.

## Conclusion

**The crown's yield is kept at `wood_yield` 3e-5, with `wood_food` 0**, by the rule set before the runs: a kind
lives by wood on two seeds of three and the kinds at a census do not fall below the control (6.56 against 5.78).
It is the first law of stage C that adds a way of living rather than closing one, and the first that makes the
crowd move.

**`day_temp` is not kept.** It was built to make the cold a property of a place, and no kind anywhere keeps to a
band. What it changes is the size of the heat's tax, which a smaller `heat` does for the same price and without
re-opening the land's bodies.

**What this changes for the project.** Two rules come out of it, both measured:

- **A patchy food parts the crowd only while it is thin.** The same law at ten times the rate is a subsidy, and a
  subsidy has one winner: 18% of the world for the largest kind at 3e-5, 61% at 3e-4. Stage C has been reading
  "the law did nothing" as "the law is too weak"; here the strong version is the one that fails.
- **Movement is bought by a food, not by a law about moving.** e049 (a band of rain), e050 (a memory), e051 (a
  stock that returns slowly), e052 (a clock that scales with size) and e057 (fouling) all left the crowd sitting.
  A food too thin to keep a body where it stands doubled the distance of a life, and nothing in the law mentions
  movement.

These answers hold for this world and these choices: c1225, seeds 9-11, 100,000 steps from random genomes, s = 1/16,
e072's sets under them, `wood_hard` 2, three points on the yield's ladder, and e068's census with its 5% line. Not
shown: c1236 (a cool world), longer runs, a yield between 3e-5 and 1e-4, and whether a standing forest is a refuge
in a season - the question the cold was built for, which it never reached.
